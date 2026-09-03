"""ChromaDB RAG service for project knowledge retrieval."""

import hashlib
import logging
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

logger = logging.getLogger(__name__)

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
TOP_K = 5


class RAGService:
    """Load, chunk, embed, and retrieve project knowledge."""

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
        self._sync_knowledge()

    def _chunk_text(self, text: str, source: str) -> list[dict[str, str]]:
        chunks = []
        start = 0
        while start < len(text):
            end = start + CHUNK_SIZE
            chunk = text[start:end]
            if chunk.strip():
                chunks.append({"text": chunk.strip(), "source": source})
            start = end - CHUNK_OVERLAP
        return chunks

    def _file_hash(self, path: Path) -> str:
        return hashlib.md5(path.read_bytes()).hexdigest()

    def _sync_knowledge(self) -> None:
        md_files = list(self.knowledge_dir.glob("**/*.md"))
        if not md_files:
            logger.info("No markdown files found in knowledge directory.")
            return

        existing = self.collection.get(include=["metadatas"])
        indexed_hashes = {meta.get("file_hash") for meta in (existing.get("metadatas") or []) if meta}

        for md_file in md_files:
            file_hash = self._file_hash(md_file)
            if file_hash in indexed_hashes:
                continue

            content = md_file.read_text(encoding="utf-8")
            chunks = self._chunk_text(content, md_file.name)
            if not chunks:
                continue

            ids = [f"{md_file.stem}_{i}_{file_hash[:8]}" for i in range(len(chunks))]
            documents = [c["text"] for c in chunks]
            metadatas = [{"source": c["source"], "file_hash": file_hash, "chunk_index": i} for i, c in enumerate(chunks)]
            self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
            logger.info("Indexed %d chunks from %s", len(chunks), md_file.name)

    def refresh(self) -> int:
        self.client.delete_collection("project_knowledge")
        self.collection = self.client.get_or_create_collection(name="project_knowledge", metadata={"hnsw:space": "cosine"})
        self._sync_knowledge()
        return self.collection.count()

    def retrieve(self, query: str, top_k: int = TOP_K) -> list[dict[str, str]]:
        if self.collection.count() == 0:
            return []
        results = self.collection.query(query_texts=[query], n_results=min(top_k, self.collection.count()))
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        return [{"text": doc, "source": meta.get("source", "unknown"), "relevance": round(1 - dist, 3)} for doc, meta, dist in zip(documents, metadatas, distances)]

    def get_context_string(self, query: str) -> str:
        chunks = self.retrieve(query)
        if not chunks:
            return ""
        return "\n\n".join(f"[{c['source']}] {c['text']}" for c in chunks)
