"""Enhanced RAG service with multi-format ETL, hybrid search (dense + BM25), and document management."""

import hashlib
import json
import logging
import math
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

logger = logging.getLogger(__name__)

CHUNK_SIZE = 800
CHUNK_OVERLAP = 120
TOP_K = 5


class SimpleBM25:
    """Lightweight in-memory BM25 indexer for hybrid retrieval."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus: list[list[str]] = []
        self.doc_ids: list[str] = []
        self.doc_lens: list[int] = []
        self.avg_doc_len = 0.0
        self.df: dict[str, int] = {}
        self.idf: dict[str, float] = {}

    def _tokenize(self, text: str) -> list[str]:
        return [w.lower() for w in re.findall(r"\b[a-zA-Z0-9_]+\b", text)]

    def index(self, doc_ids: list[str], documents: list[str]):
        self.corpus = [self._tokenize(doc) for doc in documents]
        self.doc_ids = doc_ids
        self.doc_lens = [len(doc) for doc in self.corpus]
        n_docs = len(self.corpus)
        if n_docs == 0:
            return

        self.avg_doc_len = sum(self.doc_lens) / n_docs
        self.df = {}
        for doc in self.corpus:
            unique_terms = set(doc)
            for term in unique_terms:
                self.df[term] = self.df.get(term, 0) + 1

        self.idf = {}
        for term, freq in self.df.items():
            # Standard Lucene/BM25 IDF formula
            self.idf[term] = math.log(1 + (n_docs - freq + 0.5) / (freq + 0.5))

    def score(self, query: str) -> list[tuple[str, float]]:
        query_terms = self._tokenize(query)
        scores = []
        for idx, doc in enumerate(self.corpus):
            doc_len = self.doc_lens[idx]
            score = 0.0
            term_counts: dict[str, int] = {}
            for t in doc:
                term_counts[t] = term_counts.get(t, 0) + 1

            for term in query_terms:
                if term in term_counts:
                    tf = term_counts[term]
                    idf = self.idf.get(term, 0.0)
                    denom = tf + self.k1 * (1 - self.b + self.b * (doc_len / (self.avg_doc_len or 1.0)))
                    score += idf * (tf * (self.k1 + 1)) / (denom or 1.0)

            if score > 0.0:
                scores.append((self.doc_ids[idx], score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores


class RAGService:
    """Enterprise RAG service: Multi-format parsing, hybrid search, document lifecycle."""

    def __init__(self, knowledge_dir: Path, persist_dir: Path):
        self.knowledge_dir = knowledge_dir
        self.persist_dir = persist_dir
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name="project_knowledge",
            metadata={"hnsw:space": "cosine"},
        )
        self.bm25 = SimpleBM25()
        self._sync_knowledge()

    def _extract_text(self, file_path: Path) -> str:
        """Extract text from supported formats: .md, .txt, .json, .pdf."""
        suffix = file_path.suffix.lower()

        if suffix in [".md", ".txt"]:
            return file_path.read_text(encoding="utf-8", errors="replace")

        elif suffix == ".json":
            try:
                data = json.loads(file_path.read_text(encoding="utf-8", errors="replace"))
                return json.dumps(data, indent=2)
            except Exception as e:
                logger.warning("Failed parsing JSON %s: %s", file_path.name, e)
                return file_path.read_text(encoding="utf-8", errors="replace")

        elif suffix == ".pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(str(file_path))
                text_parts = [page.extract_text() or "" for page in reader.pages]
                return "\n\n".join(text_parts).strip()
            except ImportError:
                logger.warning("pypdf not installed. Falling back to raw text read for %s", file_path.name)
                return file_path.read_text(encoding="latin1", errors="replace")
            except Exception as e:
                logger.warning("PDF extraction error for %s: %s", file_path.name, e)
                return ""

        return file_path.read_text(encoding="utf-8", errors="replace")

    def _chunk_text(self, text: str, source: str) -> list[dict[str, str]]:
        """Chunk text with semantic boundary splitting (paragraphs and sentences)."""
        chunks = []
        paragraphs = text.split("\n\n")
        current_chunk = ""

        for p in paragraphs:
            p_clean = p.strip()
            if not p_clean:
                continue

            if len(current_chunk) + len(p_clean) < CHUNK_SIZE:
                current_chunk = f"{current_chunk}\n\n{p_clean}".strip()
            else:
                if current_chunk:
                    chunks.append({"text": current_chunk, "source": source})
                # If paragraph itself exceeds chunk size, split by chunk size
                if len(p_clean) > CHUNK_SIZE:
                    for i in range(0, len(p_clean), CHUNK_SIZE - CHUNK_OVERLAP):
                        slice_p = p_clean[i : i + CHUNK_SIZE].strip()
                        if slice_p:
                            chunks.append({"text": slice_p, "source": source})
                    current_chunk = ""
                else:
                    current_chunk = p_clean

        if current_chunk:
            chunks.append({"text": current_chunk, "source": source})

        return chunks

    def _file_hash(self, path: Path) -> str:
        return hashlib.md5(path.read_bytes()).hexdigest()

    def _sync_knowledge(self) -> None:
        """Scan directory and index new/modified documents into ChromaDB and BM25."""
        supported_exts = ["*.md", "*.txt", "*.json", "*.pdf"]
        files = []
        for ext in supported_exts:
            files.extend(list(self.knowledge_dir.glob(f"**/{ext}")))

        if not files:
            logger.info("No documents found in knowledge directory: %s", self.knowledge_dir)
            return

        existing = self.collection.get(include=["metadatas"])
        indexed_hashes = {meta.get("file_hash") for meta in (existing.get("metadatas") or []) if meta}

        all_doc_ids = []
        all_doc_texts = []

        for f in files:
            try:
                f_hash = self._file_hash(f)
                if f_hash not in indexed_hashes:
                    content = self._extract_text(f)
                    chunks = self._chunk_text(content, f.name)
                    if chunks:
                        ids = [f"{f.stem}_{i}_{f_hash[:8]}" for i in range(len(chunks))]
                        documents = [c["text"] for c in chunks]
                        metadatas = [
                            {
                                "source": c["source"],
                                "file_hash": f_hash,
                                "chunk_index": i,
                                "format": f.suffix.lower(),
                                "file_size": f.stat().st_size,
                            }
                            for i, c in enumerate(chunks)
                        ]
                        self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
                        logger.info("Indexed %d chunks from %s", len(chunks), f.name)
            except Exception as exc:
                logger.error("Failed to process document %s: %s", f.name, exc)

        # Re-index BM25 with all collection entries
        try:
            full_corpus = self.collection.get(include=["documents"])
            c_docs = full_corpus.get("documents") or []
            c_ids = full_corpus.get("ids") or []
            if c_docs and c_ids:
                self.bm25.index(c_ids, c_docs)
        except Exception as e:
            logger.warning("BM25 index update failed: %s", e)

    def refresh(self) -> int:
        """Reset and re-index all documents in the knowledge base."""
        self.client.delete_collection("project_knowledge")
        self.collection = self.client.get_or_create_collection(
            name="project_knowledge", metadata={"hnsw:space": "cosine"}
        )
        self._sync_knowledge()
        return self.collection.count()

    def list_documents(self) -> list[dict[str, Any]]:
        """List all indexed documents with statistics."""
        docs_summary: dict[str, dict[str, Any]] = {}
        try:
            records = self.collection.get(include=["metadatas"])
            for meta in records.get("metadatas") or []:
                src = meta.get("source", "unknown")
                if src not in docs_summary:
                    file_path = self.knowledge_dir / src
                    size = file_path.stat().st_size if file_path.exists() else meta.get("file_size", 0)
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime).isoformat() if file_path.exists() else datetime.utcnow().isoformat()
                    docs_summary[src] = {
                        "name": src,
                        "size_bytes": size,
                        "chunk_count": 0,
                        "format": meta.get("format", Path(src).suffix.lower()),
                        "uploaded_at": mtime,
                    }
                docs_summary[src]["chunk_count"] += 1
        except Exception as e:
            logger.error("Error listing documents: %s", e)

        return list(docs_summary.values())

    def ingest_file(self, filename: str, content_bytes: bytes) -> dict[str, Any]:
        """Save and immediately index an uploaded file."""
        target_path = self.knowledge_dir / filename
        target_path.write_bytes(content_bytes)

        # Sync document
        f_hash = self._file_hash(target_path)
        content = self._extract_text(target_path)
        chunks = self._chunk_text(content, filename)

        if chunks:
            ids = [f"{target_path.stem}_{i}_{f_hash[:8]}" for i in range(len(chunks))]
            documents = [c["text"] for c in chunks]
            metadatas = [
                {
                    "source": filename,
                    "file_hash": f_hash,
                    "chunk_index": i,
                    "format": target_path.suffix.lower(),
                    "file_size": len(content_bytes),
                }
                for i in range(len(chunks))
            ]
            self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

            # Refresh BM25
            full_corpus = self.collection.get(include=["documents"])
            c_docs = full_corpus.get("documents") or []
            c_ids = full_corpus.get("ids") or []
            self.bm25.index(c_ids, c_docs)

        return {
            "name": filename,
            "size_bytes": len(content_bytes),
            "chunk_count": len(chunks),
            "format": target_path.suffix.lower(),
            "uploaded_at": datetime.utcnow().isoformat(),
        }

    def delete_document(self, filename: str) -> bool:
        """Remove a document from disk and purge its chunks from vector store."""
        target_path = self.knowledge_dir / filename
        if target_path.exists():
            target_path.unlink()

        # Delete from ChromaDB
        existing = self.collection.get(where={"source": filename})
        chunk_ids = existing.get("ids") or []
        if chunk_ids:
            self.collection.delete(ids=chunk_ids)

        # Refresh BM25
        full_corpus = self.collection.get(include=["documents"])
        c_docs = full_corpus.get("documents") or []
        c_ids = full_corpus.get("ids") or []
        self.bm25.index(c_ids, c_docs)
        return True

    def retrieve(self, query: str, top_k: int = TOP_K, mode: str = "hybrid") -> list[dict[str, Any]]:
        """Retrieve relevant chunks using hybrid search (Dense Vector + BM25 Keyword)."""
        if self.collection.count() == 0:
            return []

        dense_scores: dict[str, float] = {}
        dense_docs: dict[str, dict[str, Any]] = {}

        # 1. Dense Semantic Query
        try:
            results = self.collection.query(
                query_texts=[query], n_results=min(top_k * 2, self.collection.count())
            )
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            dists = results.get("distances", [[]])[0]
            ids = results.get("ids", [[]])[0]

            for doc_id, doc, meta, dist in zip(ids, docs, metas, dists):
                dense_scores[doc_id] = round(1 - dist, 4)
                dense_docs[doc_id] = {
                    "text": doc,
                    "source": meta.get("source", "unknown"),
                    "format": meta.get("format", ".txt"),
                }
        except Exception as exc:
            logger.error("Chroma query error: %s", exc)

        # 2. Sparse BM25 Keyword Query
        bm25_scores = dict(self.bm25.score(query)[: top_k * 2])

        # If pure dense or no BM25 matches, fallback to dense results
        if mode == "dense" or not bm25_scores:
            sorted_dense = sorted(dense_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
            return [
                {
                    "text": dense_docs[did]["text"],
                    "source": dense_docs[did]["source"],
                    "relevance": score,
                    "format": dense_docs[did]["format"],
                }
                for did, score in sorted_dense
                if did in dense_docs
            ]

        # 3. Reciprocal Rank Fusion (RRF) for Hybrid combination
        # RRF(d) = 0.6 / (60 + dense_rank) + 0.4 / (60 + bm25_rank)
        all_ids = set(dense_scores.keys()).union(set(bm25_scores.keys()))
        dense_ranked = [k for k, _ in sorted(dense_scores.items(), key=lambda x: x[1], reverse=True)]
        bm25_ranked = [k for k, _ in sorted(bm25_scores.items(), key=lambda x: x[1], reverse=True)]

        combined_ranks: list[tuple[str, float]] = []
        for did in all_ids:
            r_dense = dense_ranked.index(did) if did in dense_ranked else 999
            r_bm25 = bm25_ranked.index(did) if did in bm25_ranked else 999
            rrf_score = (0.6 / (60 + r_dense)) + (0.4 / (60 + r_bm25))
            combined_ranks.append((did, rrf_score))

        combined_ranks.sort(key=lambda x: x[1], reverse=True)

        final_results = []
        for did, score in combined_ranks[:top_k]:
            if did in dense_docs:
                final_results.append({
                    "text": dense_docs[did]["text"],
                    "source": dense_docs[did]["source"],
                    "relevance": round(score * 100, 2),  # Scaled score
                    "format": dense_docs[did]["format"],
                })
            else:
                # Fetch doc text from collection
                try:
                    res = self.collection.get(ids=[did], include=["documents", "metadatas"])
                    d_text = (res.get("documents") or [""])[0]
                    d_meta = (res.get("metadatas") or [{}])[0]
                    final_results.append({
                        "text": d_text,
                        "source": d_meta.get("source", "unknown"),
                        "relevance": round(score * 100, 2),
                        "format": d_meta.get("format", ".txt"),
                    })
                except Exception:
                    pass

        return final_results

    def get_context_string(self, query: str) -> str:
        """Generate formatted context string for LLM prompting."""
        chunks = self.retrieve(query, top_k=TOP_K, mode="hybrid")
        if not chunks:
            return ""
        return "\n\n".join(f"[{c['source']}] {c['text']}" for c in chunks)
