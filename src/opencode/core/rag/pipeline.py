"""
RAG Pipeline - Main pipeline for Retrieval-Augmented Generation.

Combines document chunking, embedding, and retrieval.
"""

from typing import Any, Dict, List, Optional
import asyncio

from .config import RAGConfig
from .document import Document, DocumentChunk
from .embeddings import EmbeddingEngine, create_embedding_engine
from .retriever import Retriever, RetrievalResult


class RAGPipeline:
    """Retrieval-Augmented Generation pipeline.
    
    Provides a complete pipeline for:
    - Adding documents with automatic chunking
    - Creating embeddings
    - Retrieving relevant documents for queries
    
    Example:
        ```python
        pipeline = RAGPipeline()
        
        # Add a document
        await pipeline.add_document(
            text="Long document text...",
            metadata={"source": "video.mp4"}
        )
        
        # Query
        results = await pipeline.query("What is the main topic?")
        for result in results:
            print(f"[{result.score:.2f}] {result.chunk.text}")
        ```
    """
    
    def __init__(self, config: Optional[RAGConfig] = None):
        """Initialize the RAG pipeline.
        
        Args:
            config: Pipeline configuration (uses defaults if not provided)
        """
        self.config = config or RAGConfig()
        self.embedding_engine: Optional[EmbeddingEngine] = None
        self.retriever = Retriever(self.config)
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the pipeline (create embedding engine)."""
        if self._initialized:
            return
        
        self.embedding_engine = create_embedding_engine(self.config)
        self._initialized = True
    
    async def add_document(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
        chunk: bool = True
    ) -> Document:
        """Add a document to the pipeline.
        
        Args:
            text: Document text
            metadata: Optional metadata
            source: Optional source identifier
            chunk: Whether to chunk the document
            
        Returns:
            The created document
        """
        await self.initialize()
        
        # Create document
        document = Document(
            text=text,
            metadata=metadata or {},
            source=source
        )
        
        if chunk:
            # Chunk the document
            chunks = self._chunk_text(text)
            document.chunks = chunks
        
        # Create embeddings
        if self.embedding_engine and document.chunks:
            embeddings = await self.embedding_engine.embed_batch(
                [c.text for c in document.chunks]
            )
            for i, embedding in enumerate(embeddings):
                document.chunks[i].embedding = embedding
        
        # Add to retriever
        self.retriever.add_document(document)
        
        return document
    
    async def add_chunks(
        self,
        chunks: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        """Add pre-chunked content.
        
        Args:
            chunks: List of chunk dictionaries with 'text', 'start', 'duration' keys
            metadata: Optional metadata
            
        Returns:
            The created document
        """
        await self.initialize()
        
        # Create document chunks
        doc_chunks = []
        full_text_parts = []
        current_index = 0
        
        for chunk_data in chunks:
            text = chunk_data.get("text", "")
            start = chunk_data.get("start", 0)
            duration = chunk_data.get("duration", 0)
            
            doc_chunk = DocumentChunk(
                text=text,
                start_index=int(start * 1000),  # Convert to ms
                end_index=int((start + duration) * 1000),
                metadata={
                    "start_seconds": start,
                    "duration_seconds": duration,
                }
            )
            doc_chunks.append(doc_chunk)
            full_text_parts.append(text)
        
        # Create document
        document = Document(
            text=" ".join(full_text_parts),
            chunks=doc_chunks,
            metadata=metadata or {}
        )
        
        # Create embeddings
        if self.embedding_engine and document.chunks:
            embeddings = await self.embedding_engine.embed_batch(
                [c.text for c in document.chunks]
            )
            for i, embedding in enumerate(embeddings):
                document.chunks[i].embedding = embedding
        
        # Add to retriever
        self.retriever.add_document(document)
        
        return document
    
    async def query(
        self,
        query: str,
        top_k: Optional[int] = None,
        min_similarity: Optional[float] = None
    ) -> List[RetrievalResult]:
        """Query the pipeline for relevant documents.
        
        Args:
            query: Query string
            top_k: Number of results to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of retrieval results
        """
        await self.initialize()
        
        if not self.embedding_engine:
            return []
        
        # Create query embedding
        query_embedding = await self.embedding_engine.embed(query)
        
        # Retrieve
        return await self.retriever.retrieve(
            query_embedding,
            top_k=top_k,
            min_similarity=min_similarity
        )
    
    def _chunk_text(self, text: str) -> List[DocumentChunk]:
        """Split text into overlapping chunks.
        
        Args:
            text: Text to chunk
            
        Returns:
            List of document chunks
        """
        # Simple word-based chunking
        words = text.split()
        chunks = []
        
        chunk_size = self.config.chunk_size
        overlap = self.config.chunk_overlap
        
        start = 0
        char_index = 0
        
        while start < len(words):
            # Get chunk words
            end = min(start + chunk_size, len(words))
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words)
            
            # Find character positions
            text_start = text.find(chunk_words[0], char_index)
            text_end = text_start + len(chunk_text)
            
            # Create chunk
            chunk = DocumentChunk(
                text=chunk_text,
                start_index=text_start,
                end_index=text_end,
                metadata={
                    "word_start": start,
                    "word_end": end,
                }
            )
            chunks.append(chunk)
            
            # Move to next chunk with overlap
            start = end - overlap if end < len(words) else end
            char_index = text_end
            
            if end >= len(words):
                break
        
        return chunks
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            "config": self.config.model_dump(),
            "retriever": self.retriever.get_stats(),
            "initialized": self._initialized,
        }
    
    def clear(self) -> None:
        """Clear all documents from the pipeline."""
        self.retriever.clear()
    
    async def build_context(
        self,
        query: str,
        max_tokens: int = 4000,
        include_metadata: bool = True
    ) -> str:
        """Build a context string for an LLM prompt.
        
        Args:
            query: Query string
            max_tokens: Maximum tokens in context
            include_metadata: Whether to include metadata
            
        Returns:
            Context string
        """
        results = await self.query(query)
        
        context_parts = []
        current_tokens = 0
        
        for result in results:
            # Estimate tokens (rough: 4 chars per token)
            chunk_tokens = len(result.chunk.text) // 4
            
            if current_tokens + chunk_tokens > max_tokens:
                break
            
            if include_metadata and result.chunk.metadata:
                # Format with metadata
                start = result.chunk.metadata.get("start_seconds", 0)
                if start:
                    minutes = int(start // 60)
                    seconds = int(start % 60)
                    context_parts.append(f"[{minutes}:{seconds:02d}] {result.chunk.text}")
                else:
                    context_parts.append(result.chunk.text)
            else:
                context_parts.append(result.chunk.text)
            
            current_tokens += chunk_tokens
        
        return "\n\n".join(context_parts)
