"""
RAG Configuration.

Supports privacy-first RAG with local embeddings, content filtering,
and source validation.
"""

from typing import List, Optional
from pydantic import BaseModel, Field

from opencode.core.defaults import (
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_EMBEDDING_DIMENSIONS,
    DEFAULT_BATCH_SIZE,
    DEFAULT_TOP_K,
    DEFAULT_EMBEDDING_CACHE_PATH,
    DEFAULT_VECTOR_STORE_PATH,
)


class RAGEmbeddingConfig(BaseModel):
    """Configuration for embedding generation."""
    
    provider: str = Field(
        default="ollama",
        description="Provider for embeddings (ollama, openai, etc.)"
    )
    
    model: str = Field(
        default=DEFAULT_EMBEDDING_MODEL,
        description="Model to use for embeddings"
    )
    
    dimensions: int = Field(
        default=DEFAULT_EMBEDDING_DIMENSIONS,
        description="Embedding vector dimensions"
    )
    
    batch_size: int = Field(
        default=DEFAULT_BATCH_SIZE,
        description="Batch size for embedding generation"
    )
    
    cache_enabled: bool = Field(
        default=True,
        description="Enable embedding caching"
    )
    
    cache_path: str = Field(
        default=DEFAULT_EMBEDDING_CACHE_PATH,
        description="Path to embedding cache"
    )


class RAGVectorStoreConfig(BaseModel):
    """Configuration for vector store."""
    
    engine: str = Field(
        default="memory",
        description="Vector store engine (memory, chroma, faiss)"
    )
    
    persist: bool = Field(
        default=True,
        description="Whether to persist the index to disk"
    )
    
    path: str = Field(
        default=DEFAULT_VECTOR_STORE_PATH,
        description="Path to store the vector index"
    )


class RAGSearchConfig(BaseModel):
    """Configuration for search."""
    
    hybrid_search: bool = Field(
        default=True,
        description="Enable hybrid search (semantic + keyword)"
    )
    
    semantic_weight: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Weight for semantic search results"
    )
    
    keyword_weight: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Weight for keyword search results"
    )
    
    top_k: int = Field(
        default=DEFAULT_TOP_K,
        ge=1,
        le=100,
        description="Number of documents to retrieve"
    )
    
    min_similarity: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score for retrieval"
    )


class RAGSafetyConfig(BaseModel):
    """Configuration for safety features."""
    
    content_filter: bool = Field(
        default=True,
        description="Enable content filtering for sensitive data"
    )
    
    output_sanitization: bool = Field(
        default=True,
        description="Enable output sanitization"
    )
    
    audit_logging: bool = Field(
        default=True,
        description="Enable audit logging of all queries"
    )
    
    require_citations: bool = Field(
        default=True,
        description="Require citations in responses"
    )


class RAGSourceConfig(BaseModel):
    """Configuration for source management."""
    
    allowed_sources: List[str] = Field(
        default=["./docs", "./src", "./RAG/sources"],
        description="Directories that can be indexed"
    )
    
    blocked_patterns: List[str] = Field(
        default=["**/secrets/**", "**/.env*", "**/credentials/**"],
        description="Patterns to exclude from indexing"
    )
    
    file_patterns: List[str] = Field(
        default=["*.md", "*.py", "*.txt", "*.rst"],
        description="File types to index"
    )


class RAGConfig(BaseModel):
    """Configuration for RAG pipeline.
    
    Attributes:
        embedding_model: Model to use for embeddings
        chunk_size: Maximum tokens per chunk
        chunk_overlap: Overlap between chunks
        top_k: Number of documents to retrieve
        min_similarity: Minimum similarity score
        max_documents: Maximum documents in index
    """
    
    # Privacy settings
    allow_external_apis: bool = Field(
        default=False,
        description="Allow external API calls for embeddings"
    )
    
    allow_web_search: bool = Field(
        default=False,
        description="Allow web search for retrieval"
    )
    
    offline_mode: bool = Field(
        default=True,
        description="Require offline-only operation"
    )
    
    # Embedding settings (legacy support)
    embedding_model: str = Field(
        default="nomic-embed-text",
        description="Model to use for embeddings (Ollama model name)"
    )
    
    embedding_provider: str = Field(
        default="ollama",
        description="Provider for embeddings (ollama, openai, etc.)"
    )
    
    # Chunking settings
    chunk_size: int = Field(
        default=500,
        ge=50,
        le=4000,
        description="Maximum tokens per chunk"
    )
    
    chunk_overlap: int = Field(
        default=50,
        ge=0,
        le=500,
        description="Overlap between chunks in tokens"
    )
    
    # Retrieval settings (legacy support)
    top_k: int = Field(
        default=3,
        ge=1,
        le=20,
        description="Number of documents to retrieve"
    )
    
    min_similarity: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score for retrieval"
    )
    
    max_documents: int = Field(
        default=10000,
        ge=1,
        description="Maximum documents in index"
    )
    
    # Embedding dimensions (model-specific)
    embedding_dimensions: int = Field(
        default=768,
        description="Embedding vector dimensions"
    )
    
    # Storage settings
    persist_index: bool = Field(
        default=True,
        description="Whether to persist the index to disk"
    )
    
    index_path: Optional[str] = Field(
        default=None,
        description="Path to store the index"
    )
    
    # New nested configurations
    embeddings: RAGEmbeddingConfig = Field(
        default_factory=RAGEmbeddingConfig,
        description="Embedding configuration"
    )
    
    vector_store: RAGVectorStoreConfig = Field(
        default_factory=RAGVectorStoreConfig,
        description="Vector store configuration"
    )
    
    search: RAGSearchConfig = Field(
        default_factory=RAGSearchConfig,
        description="Search configuration"
    )
    
    safety: RAGSafetyConfig = Field(
        default_factory=RAGSafetyConfig,
        description="Safety configuration"
    )
    
    sources: RAGSourceConfig = Field(
        default_factory=RAGSourceConfig,
        description="Source configuration"
    )
