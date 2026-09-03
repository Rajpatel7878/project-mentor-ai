'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BookOpen,
  CheckCircle,
  Database,
  FileCode,
  FileText,
  Layers,
  RefreshCw,
  Search,
  Trash2,
  Upload,
  AlertCircle,
} from 'lucide-react';
import {
  fetchDocuments,
  uploadDocument,
  deleteDocument,
  refreshRAG,
  searchRAG,
  type DocumentInfo,
  type RAGSearchResponse,
} from '@/lib/api';

export function KnowledgeManager() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Search Tester State
  const [searchQuery, setSearchQuery] = useState('');
  const [searchMode, setSearchMode] = useState<'hybrid' | 'dense'>('hybrid');
  const [searchResults, setSearchResults] = useState<RAGSearchResponse | null>(null);
  const [isSearching, setIsSearching] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadDocuments = useCallback(async () => {
    try {
      setIsLoading(true);
      const docs = await fetchDocuments();
      setDocuments(docs);
    } catch (err: any) {
      console.error('Failed to load documents', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    const file = files[0];
    setIsUploading(true);
    setStatusMessage(null);

    try {
      const newDoc = await uploadDocument(file);
      setStatusMessage({
        type: 'success',
        text: `Indexed "${newDoc.name}" into ${newDoc.chunk_count} vector chunks.`,
      });
      await loadDocuments();
    } catch (err: any) {
      setStatusMessage({
        type: 'error',
        text: err.message || 'Failed to upload document',
      });
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDelete = async (filename: string) => {
    try {
      await deleteDocument(filename);
      setStatusMessage({
        type: 'success',
        text: `Document "${filename}" and its vector embeddings were removed.`,
      });
      await loadDocuments();
    } catch (err: any) {
      setStatusMessage({
        type: 'error',
        text: err.message || 'Failed to delete document',
      });
    }
  };

  const handleRefresh = async () => {
    try {
      setIsRefreshing(true);
      const res = await refreshRAG();
      setStatusMessage({
        type: 'success',
        text: `Knowledge base re-indexed successfully. Total chunks: ${res.document_count}`,
      });
      await loadDocuments();
    } catch (err: any) {
      setStatusMessage({
        type: 'error',
        text: err.message || 'Re-index failed',
      });
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!searchQuery.trim()) return;

    try {
      setIsSearching(true);
      const results = await searchRAG(searchQuery, searchMode);
      setSearchResults(results);
    } catch (err: any) {
      console.error('Search error', err);
    } finally {
      setIsSearching(false);
    }
  };

  const totalChunks = documents.reduce((acc, d) => acc + d.chunk_count, 0);

  return (
    <div className="flex-1 flex flex-col p-6 overflow-y-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-display text-xl tracking-wider glow-text">
            KNOWLEDGE BASE & RAG PIPELINE
          </h2>
          <p className="text-xs text-white/50 tracking-wider">
            CHROMADB EMBEDDINGS • BM25 SPARSE HYBRID RETRIEVAL • MULTI-FORMAT ETL
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="flex items-center gap-2 px-3 py-1.5 glass-panel rounded-lg hover:bg-white/10 text-xs font-display tracking-wider text-cyan-glow transition-all"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
            RE-INDEX STORE
          </button>
        </div>
      </div>

      {/* Status banner */}
      <AnimatePresence>
        {statusMessage && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className={`p-3 rounded-lg border text-xs flex items-center gap-2 ${
              statusMessage.type === 'success'
                ? 'bg-green-500/10 border-green-500/30 text-green-300'
                : 'bg-red-500/10 border-red-500/30 text-red-300'
            }`}
          >
            {statusMessage.type === 'success' ? (
              <CheckCircle className="w-4 h-4 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 shrink-0" />
            )}
            <span>{statusMessage.text}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Metrics Banner */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="glass-panel rounded-xl p-4 border border-white/10 flex items-center gap-3">
          <div className="p-3 rounded-lg bg-cyan-500/20 text-cyan-glow">
            <BookOpen className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs text-white/50 uppercase tracking-wider block">
              Indexed Documents
            </span>
            <span className="font-display text-xl text-cyan-glow font-bold">
              {documents.length}
            </span>
          </div>
        </div>

        <div className="glass-panel rounded-xl p-4 border border-white/10 flex items-center gap-3">
          <div className="p-3 rounded-lg bg-blue-500/20 text-blue-400">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs text-white/50 uppercase tracking-wider block">
              Embedded Chunks
            </span>
            <span className="font-display text-xl text-blue-400 font-bold">
              {totalChunks}
            </span>
          </div>
        </div>

        <div className="glass-panel rounded-xl p-4 border border-white/10 flex items-center gap-3">
          <div className="p-3 rounded-lg bg-purple-500/20 text-purple-400">
            <Database className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs text-white/50 uppercase tracking-wider block">
              Retrieval Architecture
            </span>
            <span className="font-display text-sm text-purple-300 font-semibold">
              Hybrid (Dense + BM25)
            </span>
          </div>
        </div>
      </div>

      {/* Upload Zone */}
      <div className="glass-panel rounded-xl p-5 border border-dashed border-cyan-glow/30 hover:border-cyan-glow/60 transition-all text-center">
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.md,.txt,.json"
          onChange={handleFileUpload}
          className="hidden"
          id="rag-file-input"
        />
        <label
          htmlFor="rag-file-input"
          className="cursor-pointer flex flex-col items-center justify-center gap-2 py-3"
        >
          <div className="p-3 rounded-full bg-cyan-500/20 text-cyan-glow">
            <Upload className={`w-6 h-6 ${isUploading ? 'animate-bounce' : ''}`} />
          </div>
          <span className="font-display text-sm tracking-wider text-white/90">
            {isUploading ? 'INDEXING DOCUMENT...' : 'DROP OR SELECT DOCUMENT TO INDEX'}
          </span>
          <span className="text-xs text-white/40">
            Supports PDF, Markdown (.md), JSON, and Plain Text (.txt)
          </span>
        </label>
      </div>

      {/* Document Table */}
      <div className="glass-panel rounded-xl p-5 border border-white/10 space-y-4">
        <h3 className="font-display text-xs tracking-widest text-cyan-glow/70 uppercase">
          KNOWLEDGE REPOSITORY ARCHIVE
        </h3>

        {isLoading ? (
          <div className="text-center py-6 text-xs text-white/40 font-mono">
            Scanning vector store...
          </div>
        ) : documents.length === 0 ? (
          <div className="text-center py-6 text-xs text-white/40">
            No documents in the knowledge repository. Upload a file above to begin.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-white/40 border-b border-white/10 uppercase font-mono">
                <tr>
                  <th className="pb-3">Source Name</th>
                  <th className="pb-3">Format</th>
                  <th className="pb-3">File Size</th>
                  <th className="pb-3">Chunks</th>
                  <th className="pb-3">Indexed Date</th>
                  <th className="pb-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {documents.map((doc) => (
                  <tr key={doc.name} className="hover:bg-white/5 transition-colors">
                    <td className="py-3 font-medium text-white/90 flex items-center gap-2">
                      {doc.format === '.pdf' ? (
                        <FileText className="w-4 h-4 text-red-400" />
                      ) : doc.format === '.json' ? (
                        <FileCode className="w-4 h-4 text-yellow-400" />
                      ) : (
                        <FileText className="w-4 h-4 text-cyan-glow" />
                      )}
                      {doc.name}
                    </td>
                    <td className="py-3 font-mono uppercase text-white/60">
                      {doc.format.replace('.', '')}
                    </td>
                    <td className="py-3 font-mono text-white/60">
                      {(doc.size_bytes / 1024).toFixed(1)} KB
                    </td>
                    <td className="py-3 font-mono text-cyan-glow font-semibold">
                      {doc.chunk_count}
                    </td>
                    <td className="py-3 font-mono text-white/40">
                      {new Date(doc.uploaded_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 text-right">
                      <button
                        onClick={() => handleDelete(doc.name)}
                        className="p-1 rounded text-white/40 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                        title="Delete Document"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Hybrid Search Sandbox */}
      <div className="glass-panel rounded-xl p-5 border border-white/10 space-y-4">
        <h3 className="font-display text-xs tracking-widest text-cyan-glow/70 uppercase">
          HYBRID RETRIEVAL BENCHMARK & TESTER
        </h3>

        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 w-4 h-4 text-white/40" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Query project knowledge (e.g. system architecture, API endpoints, roadmap)..."
              className="w-full pl-9 pr-4 py-2 rounded-lg bg-black/40 border border-white/10 text-xs text-white placeholder-white/40 focus:outline-none focus:border-cyan-glow transition-all"
            />
          </div>

          <select
            value={searchMode}
            onChange={(e) => setSearchMode(e.target.value as any)}
            className="px-3 py-2 rounded-lg bg-black/40 border border-white/10 text-xs text-cyan-glow focus:outline-none"
          >
            <option value="hybrid">Hybrid (Dense + BM25)</option>
            <option value="dense">Dense Vector Only</option>
          </select>

          <button
            type="submit"
            disabled={isSearching}
            className="px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-black font-display text-xs font-semibold tracking-wider transition-all"
          >
            {isSearching ? 'SEARCHING...' : 'BENCHMARK'}
          </button>
        </form>

        {/* Results view */}
        {searchResults && (
          <div className="space-y-3 pt-2">
            <span className="text-xs text-white/50 block font-mono">
              Mode: {searchResults.retrieval_mode.toUpperCase()} • Matches:{' '}
              {searchResults.results.length}
            </span>

            <div className="space-y-2">
              {searchResults.results.map((res, i) => (
                <div
                  key={i}
                  className="p-3 rounded-lg bg-black/30 border border-white/5 space-y-1.5"
                >
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-cyan-glow font-medium">[{res.source}]</span>
                    <span className="font-mono text-emerald-400">
                      Score: {res.relevance}%
                    </span>
                  </div>
                  <p className="text-xs text-white/70 leading-relaxed font-mono whitespace-pre-wrap">
                    {res.text}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
