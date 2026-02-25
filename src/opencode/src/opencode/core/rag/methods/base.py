"""
Base RAG Method Implementation.

Provides the abstract base class and common utilities for all RAG methods.
Integrated from OpenRAG and RAG_Techniques patterns.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional, Protocol, Union

from pydantic import BaseModel, Field


class RetrievalStrategy(str, Enum):
    """Available retrieval strategies."""
    SEMANTIC = "semantic"  # Vector similarity search
    KEYWORD = "keyword"    # BM25 keyword search
    HYBRID = "hybrid"      # Combined semantic + keyword
    GRAPH = "graph"        # Graph-based retrieval


class ChunkingStrategy(str, Enum):
    """Available chunking strategies."""
    FIXED = "fixed"              # Fixed-size chunks
    RECURSIVE = "recursive"      # Recursive character splitting
    SEMANTIC = "semantic"        # Semantic-aware chunking
    PROPOSITION = "proposition"  # Proposition-based chunking
    HIERARCHICAL = "hierarchical" # Hierarchical summarization


class RAGMethodConfig(BaseModel):
    """Configuration for RAG methods."""
    
    # Retrieval settings
    retrieval_strategy: RetrievalStrategy = Field(
        default=RetrievalStrategy.SEMANTIC,
        description="Strategy for document retrieval"
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Number of documents to retrieve"
    )
    similarity_threshold: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score for retrieval"
    )
    
    # Chunking settings
    chunking_strategy: ChunkingStrategy = Field(
        default=ChunkingStrategy.RECURSIVE,
        description="Strategy for document chunking"
    )
    chunk_size: int = Field(
        default=1000,
        ge=100,
        le=10000,
        description="Size of chunks in characters"
    )
    chunk_overlap: int = Field(
        default=200,
        ge=0,
        le=1000,
        description="Overlap between chunks"
    )
    
    # Model settings
    embedding_model: str = Field(
        default="mxbai-embed-large",
        description="Model for embeddings"
    )
    llm_model: str = Field(
        default="llama3",
        description="Model for generation"
    )
    temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
        description="Generation temperature"
    )
    
    # Advanced settings
    rerank_enabled: bool = Field(
        default=False,
        description="Enable reranking of results"
    )
    rerank_model: Optional[str] = Field(
        default=None,
        description="Model for reranking"
    )
    query_rewriting: bool = Field(
        default=False,
        description="Enable query rewriting"
    )
    self_reflection: bool = Field(
        default=False,
        description="Enable self-reflection checks"
    )
    
    # Performance settings
    max_concurrent_requests: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum concurrent API requests"
    )
    timeout_seconds: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Request timeout in seconds"
    )
    
    class Config:
        use_enum_values = True


@dataclass
class RetrievedDocument:
    """A retrieved document with metadata."""
    content: str
    score: float = 0.0
    source: Optional[str] = None
    title: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "content": self.content,
            "score": self.score,
            "source": self.source,
            "title": self.title,
            "metadata": self.metadata,
        }


@dataclass
class RAGResult:
    """Result from a RAG query."""
    answer: str
    sources: List[RetrievedDocument] = field(default_factory=list)
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # For self-reflective methods
    self_reflection_passed: Optional[bool] = None
    reflection_reason: Optional[str] = None
    
    # For corrective methods
    correction_applied: bool = False
    correction_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "answer": self.answer,
            "sources": [s.to_dict() for s in self.sources],
            "confidence": self.confidence,
            "metadata": self.metadata,
            "self_reflection_passed": self.self_reflection_passed,
            "reflection_reason": self.reflection_reason,
            "correction_applied": self.correction_applied,
            "correction_type": self.correction_type,
        }


class EmbeddingProvider(Protocol):
    """Protocol for embedding providers."""
    
    async def embed_texts(
        self,
        texts: List[str],
        model: Optional[str] = None,
    ) -> List[List[float]]:
        """Generate embeddings for texts."""
        ...
    
    async def embed_query(
        self,
        query: str,
        model: Optional[str] = None,
    ) -> List[float]:
        """Generate embedding for a query."""
        ...


class VectorStore(Protocol):
    """Protocol for vector stores."""
    
    async def add_documents(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Add documents to the store."""
        ...
    
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievedDocument]:
        """Search for similar documents."""
        ...
    
    async def delete(
        self,
        ids: Optional[List[str]] = None,
        filter: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Delete documents from the store."""
        ...


class LLMProvider(Protocol):
    """Protocol for LLM providers."""
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate text from a prompt."""
        ...
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """Generate text stream from a prompt."""
        ...


class BaseRAGMethod(ABC):
    """
    Abstract base class for RAG methods.
    
    All RAG method implementations should inherit from this class
    and implement the required abstract methods.
    
    This design is inspired by OpenRAG's modular architecture and
    RAG_Techniques' comprehensive technique collection.
    """
    
    method_name: str = "base"
    method_description: str = "Base RAG method"
    
    def __init__(
        self,
        config: RAGMethodConfig,
        embedding_provider: Optional[EmbeddingProvider] = None,
        vector_store: Optional[VectorStore] = None,
        llm_provider: Optional[LLMProvider] = None,
    ):
        """
        Initialize the RAG method.
        
        Args:
            config: Configuration for the RAG method
            embedding_provider: Provider for embeddings
            vector_store: Vector store for document storage
            llm_provider: Provider for LLM generation
        """
        self.config = config
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store
        self.llm_provider = llm_provider
    
    @abstractmethod
    async def query(
        self,
        question: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RAGResult:
        """
        Execute a RAG query.
        
        Args:
            question: The question to answer
            context: Optional context for the query
            
        Returns:
            RAGResult containing the answer and sources
        """
        pass
    
    @abstractmethod
    async def index_documents(
        self,
        documents: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> int:
        """
        Index documents for retrieval.
        
        Args:
            documents: List of document texts
            metadata: Optional metadata for each document
            ids: Optional IDs for each document
            
        Returns:
            Number of documents indexed
        """
        pass
    
    async def query_stream(
        self,
        question: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[str]:
        """
        Execute a RAG query with streaming response.
        
        Args:
            question: The question to answer
            context: Optional context for the query
            
        Yields:
            Chunks of the generated answer
        """
        # Default implementation: non-streaming
        result = await self.query(question, context)
        yield result.answer
    
    def get_config(self) -> RAGMethodConfig:
        """Get the current configuration."""
        return self.config
    
    def update_config(self, **kwargs) -> None:
        """
        Update configuration parameters.
        
        Args:
            **kwargs: Configuration parameters to update
        """
        data = self.config.model_dump()
        data.update(kwargs)
        self.config = RAGMethodConfig(**data)
    
    @classmethod
    def get_method_info(cls) -> Dict[str, str]:
        """Get information about this RAG method."""
        return {
            "name": cls.method_name,
            "description": cls.method_description,
        }


class SimpleRAGMethod(BaseRAGMethod):
    """
    Simple RAG implementation for basic use cases.
    
    This is a minimal implementation that can be used as a fallback
    when providers are not fully configured.
    """
    
    method_name = "simple"
    method_description = "Simple RAG with basic retrieval and generation"
    
    def __init__(
        self,
        config: Optional[RAGMethodConfig] = None,
        **kwargs,
    ):
        """Initialize with optional config."""
        super().__init__(config or RAGMethodConfig(), **kwargs)
        self._documents: List[RetrievedDocument] = []
    
    async def query(
        self,
        question: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RAGResult:
        """Execute a simple RAG query."""
        # If we have providers, use them
        if self.vector_store and self.embedding_provider:
            query_embedding = await self.embedding_provider.embed_query(
                question,
                model=self.config.embedding_model,
            )
            sources = await self.vector_store.search(
                query_embedding,
                top_k=self.config.top_k,
            )
        else:
            # Fallback to in-memory search
            sources = self._simple_search(question)
        
        # Build context from sources
        context_text = "\n\n".join(
            f"[{i+1}] {doc.content}"
            for i, doc in enumerate(sources)
        )
        
        # Generate answer
        if self.llm_provider:
            prompt = self._build_prompt(question, context_text)
            answer = await self.llm_provider.generate(
                prompt,
                temperature=self.config.temperature,
            )
        else:
            # Fallback: return context as answer
            answer = f"Based on the retrieved documents:\n\n{context_text}"
        
        return RAGResult(
            answer=answer,
            sources=sources,
            confidence=0.5 if not self.llm_provider else 0.8,
            metadata={"method": self.method_name},
        )
    
    async def index_documents(
        self,
        documents: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> int:
        """Index documents for retrieval."""
        import uuid
        
        for i, doc in enumerate(documents):
            doc_id = ids[i] if ids else str(uuid.uuid4())
            doc_metadata = metadata[i] if metadata else {}
            
            self._documents.append(RetrievedDocument(
                content=doc,
                source=doc_metadata.get("source"),
                title=doc_metadata.get("title"),
                metadata=doc_metadata,
            ))
        
        return len(documents)
    
    def _simple_search(self, query: str) -> List[RetrievedDocument]:
        """Simple keyword-based search fallback."""
        query_terms = set(query.lower().split())
        scored_docs = []
        
        for doc in self._documents:
            doc_terms = set(doc.content.lower().split())
            overlap = len(query_terms & doc_terms)
            if overlap > 0:
                score = overlap / len(query_terms)
                scored_docs.append((score, doc))
        
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored_docs[:self.config.top_k]]
    
    def _build_prompt(self, question: str, context: str) -> str:
        """Build the generation prompt."""
        return f"""Based on the following context, please answer the question.

Context:
{context}

Question: {question}

Please provide a clear and accurate answer based only on the provided context.
If the context doesn't contain enough information, say so.

Answer:"""