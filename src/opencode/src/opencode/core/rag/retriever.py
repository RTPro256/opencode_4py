"""
Retriever for RAG pipeline.

Implements similarity search using cosine similarity.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from dataclasses import dataclass

from .document import Document, DocumentChunk
from .config import RAGConfig


@dataclass
class RetrievalResult:
    """Result of a retrieval operation."""
    
    chunk: DocumentChunk
    """The retrieved chunk."""
    
    score: float
    """Similarity score."""
    
    document: Optional[Document] = None
    """Parent document if available."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "text": self.chunk.text,
            "score": self.score,
            "metadata": self.chunk.metadata,
            "start_index": self.chunk.start_index,
            "end_index": self.chunk.end_index,
        }


class Retriever:
    """Retriever for finding relevant documents.
    
    Uses cosine similarity for semantic search.
    """
    
    def __init__(self, config: RAGConfig):
        """Initialize the retriever.
        
        Args:
            config: RAG configuration
        """
        self.config = config
        self.documents: List[Document] = []
        self.chunks: List[DocumentChunk] = []
        self.embeddings: Optional[np.ndarray] = None
    
    def add_document(self, document: Document) -> None:
        """Add a document to the index.
        
        Args:
            document: Document to add
        """
        self.documents.append(document)
        self.chunks.extend(document.chunks)
        
        # Update embeddings matrix
        embeddings = [
            chunk.embedding for chunk in document.chunks
            if chunk.embedding is not None
        ]
        
        if embeddings:
            if self.embeddings is None:
                self.embeddings = np.array(embeddings)
            else:
                self.embeddings = np.vstack([self.embeddings, np.array(embeddings)])
    
    def remove_document(self, document_id: str) -> None:
        """Remove a document from the index.
        
        Args:
            document_id: ID of document to remove
        """
        # Find and remove document
        doc_to_remove = None
        for doc in self.documents:
            if doc.id == document_id:
                doc_to_remove = doc
                break
        
        if doc_to_remove:
            self.documents.remove(doc_to_remove)
            
            # Remove chunks
            chunk_ids = {chunk.id for chunk in doc_to_remove.chunks}
            self.chunks = [c for c in self.chunks if c.id not in chunk_ids]
            
            # Rebuild embeddings matrix
            self._rebuild_embeddings()
    
    def _rebuild_embeddings(self) -> None:
        """Rebuild the embeddings matrix."""
        embeddings = [
            chunk.embedding for chunk in self.chunks
            if chunk.embedding is not None
        ]
        
        if embeddings:
            self.embeddings = np.array(embeddings)
        else:
            self.embeddings = None
    
    async def retrieve(
        self,
        query_embedding: List[float],
        top_k: Optional[int] = None,
        min_similarity: Optional[float] = None
    ) -> List[RetrievalResult]:
        """Retrieve relevant chunks for a query embedding.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of retrieval results
        """
        if self.embeddings is None or len(self.embeddings) == 0:
            return []
        
        top_k = top_k or self.config.top_k
        min_similarity = min_similarity or self.config.min_similarity
        
        # Calculate cosine similarity
        query_vec = np.array(query_embedding)
        
        # Normalize vectors
        query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-8)
        embeddings_norm = self.embeddings / (
            np.linalg.norm(self.embeddings, axis=1, keepdims=True) + 1e-8
        )
        
        # Calculate similarities
        similarities = np.dot(embeddings_norm, query_norm)
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            score = similarities[idx]
            
            if score < min_similarity:
                continue
            
            chunk = self.chunks[idx]
            
            # Find parent document
            parent_doc = None
            for doc in self.documents:
                if chunk.id in {c.id for c in doc.chunks}:
                    parent_doc = doc
                    break
            
            results.append(RetrievalResult(
                chunk=chunk,
                score=float(score),
                document=parent_doc
            ))
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get retriever statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            "document_count": len(self.documents),
            "chunk_count": len(self.chunks),
            "embedding_dimensions": self.embeddings.shape[1] if self.embeddings is not None else 0,
            "has_embeddings": self.embeddings is not None,
        }
    
    def clear(self) -> None:
        """Clear all documents from the index."""
        self.documents = []
        self.chunks = []
        self.embeddings = None
