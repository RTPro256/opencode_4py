"""
Document and DocumentChunk models for RAG.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import uuid


class DocumentChunk(BaseModel):
    """A chunk of a document with embedding.
    
    Attributes:
        id: Unique identifier for the chunk
        text: The text content
        embedding: Vector embedding (optional, can be None until embedded)
        start_index: Starting character index in original document
        end_index: Ending character index in original document
        metadata: Additional metadata
    """
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    """Unique identifier for the chunk."""
    
    text: str
    """The text content of the chunk."""
    
    embedding: Optional[List[float]] = None
    """Vector embedding of the text."""
    
    start_index: int = 0
    """Starting character index in original document."""
    
    end_index: int = 0
    """Ending character index in original document."""
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    """Additional metadata about the chunk."""
    
    @property
    def length(self) -> int:
        """Get the length of the chunk text."""
        return len(self.text)
    
    @property
    def has_embedding(self) -> bool:
        """Check if the chunk has an embedding."""
        return self.embedding is not None and len(self.embedding) > 0


class Document(BaseModel):
    """A document to be indexed in the RAG system.
    
    Attributes:
        id: Unique identifier for the document
        text: Full text content
        chunks: List of document chunks
        metadata: Additional metadata
        created_at: When the document was created
        source: Source of the document (file, url, etc.)
    """
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    """Unique identifier for the document."""
    
    text: str
    """Full text content of the document."""
    
    chunks: List[DocumentChunk] = Field(default_factory=list)
    """List of document chunks."""
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    """Additional metadata about the document."""
    
    created_at: datetime = Field(default_factory=datetime.now)
    """When the document was created/indexed."""
    
    source: Optional[str] = None
    """Source of the document (file path, URL, etc.)."""
    
    @property
    def length(self) -> int:
        """Get the length of the document text."""
        return len(self.text)
    
    @property
    def chunk_count(self) -> int:
        """Get the number of chunks."""
        return len(self.chunks)
    
    @property
    def has_embeddings(self) -> bool:
        """Check if all chunks have embeddings."""
        return all(chunk.has_embedding for chunk in self.chunks)
    
    def get_chunk_texts(self) -> List[str]:
        """Get all chunk texts.
        
        Returns:
            List of chunk text strings
        """
        return [chunk.text for chunk in self.chunks]
    
    def get_embeddings(self) -> List[List[float]]:
        """Get all chunk embeddings.
        
        Returns:
            List of embedding vectors
        """
        return [chunk.embedding for chunk in self.chunks if chunk.embedding]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization.
        
        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "text": self.text[:500] + "..." if len(self.text) > 500 else self.text,
            "chunk_count": self.chunk_count,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "source": self.source,
        }
