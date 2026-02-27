"""
RAG (Retrieval-Augmented Generation) Pipeline.

Based on youtube_Rag project implementation with Privacy-First extensions.

Provides functionality for:
- Document chunking
- Embedding generation (local and remote)
- Similarity search
- Context retrieval for LLM queries
- Query rewriting and expansion
- RAG evaluation metrics
- Privacy-first features:
  - Local embeddings via Ollama
  - Local vector store (memory, file, Chroma)
  - Hybrid search (semantic + keyword)
  - Content filtering and sanitization
  - Source validation
  - Audit logging
  - Citation tracking
  - Content validation and correction
"""

# Core components
from .config import (
    RAGConfig,
    RAGEmbeddingConfig,
    RAGVectorStoreConfig,
    RAGSearchConfig,
    RAGSafetyConfig,
    RAGSourceConfig,
)
from .pipeline import RAGPipeline
from .document import Document, DocumentChunk
from .embeddings import EmbeddingEngine
from .retriever import Retriever
from .query_rewriter import QueryRewriter, QueryRewriteResult, HyDEGenerator
from .evaluation import RAGEvaluator, RetrievalMetrics, GenerationMetrics

# Privacy-first components
from .local_embeddings import (
    LocalEmbeddingEngine,
    LocalEmbeddingConfig,
    EmbeddingCache,
    create_local_embedding_engine,
)
from .local_vector_store import (
    LocalVectorStore,
    SearchResult,
    VectorStoreBackend,
    MemoryVectorStore,
    FileVectorStore,
)
from .hybrid_search import (
    HybridSearch,
    HybridSearchResult,
    BM25Index,
)
from .source_manager import (
    SourceManager,
    SourceInfo,
    IndexResult,
    SourceValidationError,
    create_source_manager,
)
from .citations import (
    Citation,
    CitationManager,
    CitationStyle,
    format_citation_report,
)

# Validation components
from .validation import (
    ContentValidator,
    ValidationResult,
    FalseContentRegistry,
    FalseContentRecord,
    RAGRegenerator,
    RegenerationResult,
    ValidationAwareRAGPipeline,
    ValidatedQueryResult,
)

__all__ = [
    # Core
    "RAGConfig",
    "RAGEmbeddingConfig",
    "RAGVectorStoreConfig",
    "RAGSearchConfig",
    "RAGSafetyConfig",
    "RAGSourceConfig",
    "RAGPipeline",
    "Document",
    "DocumentChunk",
    "EmbeddingEngine",
    "Retriever",
    "QueryRewriter",
    "QueryRewriteResult",
    "HyDEGenerator",
    "RAGEvaluator",
    "RetrievalMetrics",
    "GenerationMetrics",
    # Privacy-first
    "LocalEmbeddingEngine",
    "LocalEmbeddingConfig",
    "EmbeddingCache",
    "create_local_embedding_engine",
    "LocalVectorStore",
    "SearchResult",
    "VectorStoreBackend",
    "MemoryVectorStore",
    "FileVectorStore",
    "HybridSearch",
    "HybridSearchResult",
    "BM25Index",
    "SourceManager",
    "SourceInfo",
    "IndexResult",
    "SourceValidationError",
    "create_source_manager",
    "Citation",
    "CitationManager",
    "CitationStyle",
    "format_citation_report",
    # Validation
    "ContentValidator",
    "ValidationResult",
    "FalseContentRegistry",
    "FalseContentRecord",
    "RAGRegenerator",
    "RegenerationResult",
    "ValidationAwareRAGPipeline",
    "ValidatedQueryResult",
]
