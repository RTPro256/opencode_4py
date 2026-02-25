"""
Local Vector Store for Privacy-First RAG.

Provides local vector storage using Chroma or FAISS with no external dependencies.
"""

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SearchResult(BaseModel):
    """Result from vector store search."""
    
    id: str = Field(..., description="Document ID")
    text: str = Field(..., description="Document text")
    score: float = Field(..., description="Similarity score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "text": self.text,
            "score": self.score,
            "metadata": self.metadata,
        }


class VectorStoreBackend(ABC):
    """Abstract base class for vector store backends."""
    
    @abstractmethod
    async def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        texts: List[str],
        metadata: List[Dict[str, Any]],
    ) -> None:
        """Add documents to the store."""
        pass
    
    @abstractmethod
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Search for similar documents."""
        pass
    
    @abstractmethod
    async def delete(self, ids: List[str]) -> None:
        """Delete documents by ID."""
        pass
    
    @abstractmethod
    async def count(self) -> int:
        """Get document count."""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all documents."""
        pass


class MemoryVectorStore(VectorStoreBackend):
    """
    In-memory vector store using numpy.
    
    Simple and fast, but not persistent.
    """
    
    def __init__(self, dimensions: int = 768):
        """
        Initialize memory vector store.
        
        Args:
            dimensions: Embedding dimensions
        """
        self.dimensions = dimensions
        self.ids: List[str] = []
        self.texts: List[str] = []
        self.metadata: List[Dict[str, Any]] = []
        self.embeddings: Optional[np.ndarray] = None
    
    async def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        texts: List[str],
        metadata: List[Dict[str, Any]],
    ) -> None:
        """Add documents to the store."""
        self.ids.extend(ids)
        self.texts.extend(texts)
        self.metadata.extend(metadata)
        
        embeddings_array = np.array(embeddings)
        if self.embeddings is None:
            self.embeddings = embeddings_array
        else:
            self.embeddings = np.vstack([self.embeddings, embeddings_array])
    
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Search for similar documents using cosine similarity."""
        if self.embeddings is None or len(self.embeddings) == 0:
            return []
        
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
            # Apply filter if provided
            if filter:
                match = all(
                    self.metadata[idx].get(k) == v
                    for k, v in filter.items()
                )
                if not match:
                    continue
            
            results.append(SearchResult(
                id=self.ids[idx],
                text=self.texts[idx],
                score=float(similarities[idx]),
                metadata=self.metadata[idx],
            ))
        
        return results
    
    async def delete(self, ids: List[str]) -> None:
        """Delete documents by ID."""
        id_set = set(ids)
        indices_to_keep = [i for i, id in enumerate(self.ids) if id not in id_set]
        
        self.ids = [self.ids[i] for i in indices_to_keep]
        self.texts = [self.texts[i] for i in indices_to_keep]
        self.metadata = [self.metadata[i] for i in indices_to_keep]
        
        if self.embeddings is not None:
            self.embeddings = self.embeddings[indices_to_keep]
    
    async def count(self) -> int:
        """Get document count."""
        return len(self.ids)
    
    async def clear(self) -> None:
        """Clear all documents."""
        self.ids = []
        self.texts = []
        self.metadata = []
        self.embeddings = None


class FileVectorStore(VectorStoreBackend):
    """
    File-based vector store with persistence.
    
    Stores embeddings and metadata in JSON files.
    """
    
    def __init__(self, path: Path, dimensions: int = 768):
        """
        Initialize file vector store.
        
        Args:
            path: Path to store directory
            dimensions: Embedding dimensions
        """
        self.path = path
        self.dimensions = dimensions
        self.path.mkdir(parents=True, exist_ok=True)
        
        self.data_file = self.path / "data.json"
        self.embeddings_file = self.path / "embeddings.npy"
        
        # Load existing data
        self._load()
    
    def _load(self) -> None:
        """Load data from disk."""
        if self.data_file.exists():
            try:
                with open(self.data_file, "r") as f:
                    data = json.load(f)
                    self.ids = data.get("ids", [])
                    self.texts = data.get("texts", [])
                    self.metadata = data.get("metadata", [])
            except Exception as e:
                logger.warning(f"Failed to load data file: {e}")
                self.ids = []
                self.texts = []
                self.metadata = []
        else:
            self.ids = []
            self.texts = []
            self.metadata = []
        
        if self.embeddings_file.exists():
            try:
                self.embeddings = np.load(str(self.embeddings_file))
            except Exception as e:
                logger.warning(f"Failed to load embeddings file: {e}")
                self.embeddings = None
        else:
            self.embeddings = None
    
    def _save(self) -> None:
        """Save data to disk."""
        with open(self.data_file, "w") as f:
            json.dump({
                "ids": self.ids,
                "texts": self.texts,
                "metadata": self.metadata,
            }, f)
        
        if self.embeddings is not None:
            np.save(str(self.embeddings_file), self.embeddings)
    
    async def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        texts: List[str],
        metadata: List[Dict[str, Any]],
    ) -> None:
        """Add documents to the store."""
        self.ids.extend(ids)
        self.texts.extend(texts)
        self.metadata.extend(metadata)
        
        embeddings_array = np.array(embeddings)
        if self.embeddings is None:
            self.embeddings = embeddings_array
        else:
            self.embeddings = np.vstack([self.embeddings, embeddings_array])
        
        self._save()
    
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Search for similar documents."""
        if self.embeddings is None or len(self.embeddings) == 0:
            return []
        
        # Calculate cosine similarity
        query_vec = np.array(query_embedding)
        query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-8)
        embeddings_norm = self.embeddings / (
            np.linalg.norm(self.embeddings, axis=1, keepdims=True) + 1e-8
        )
        similarities = np.dot(embeddings_norm, query_norm)
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if filter:
                match = all(
                    self.metadata[idx].get(k) == v
                    for k, v in filter.items()
                )
                if not match:
                    continue
            
            results.append(SearchResult(
                id=self.ids[idx],
                text=self.texts[idx],
                score=float(similarities[idx]),
                metadata=self.metadata[idx],
            ))
        
        return results
    
    async def delete(self, ids: List[str]) -> None:
        """Delete documents by ID."""
        id_set = set(ids)
        indices_to_keep = [i for i, id in enumerate(self.ids) if id not in id_set]
        
        self.ids = [self.ids[i] for i in indices_to_keep]
        self.texts = [self.texts[i] for i in indices_to_keep]
        self.metadata = [self.metadata[i] for i in indices_to_keep]
        
        if self.embeddings is not None:
            self.embeddings = self.embeddings[indices_to_keep]
        
        self._save()
    
    async def count(self) -> int:
        """Get document count."""
        return len(self.ids)
    
    async def clear(self) -> None:
        """Clear all documents."""
        self.ids = []
        self.texts = []
        self.metadata = []
        self.embeddings = None
        self._save()


class ChromaVectorStore(VectorStoreBackend):
    """
    Vector store using ChromaDB.
    
    Provides efficient similarity search with metadata filtering.
    """
    
    def __init__(self, path: Path, collection_name: str = "opencode_rag"):
        """
        Initialize Chroma vector store.
        
        Args:
            path: Path to Chroma database
            collection_name: Name of the collection
        """
        self.path = path
        self.collection_name = collection_name
        self._client = None
        self._collection = None
    
    def _get_collection(self):
        """Get or create Chroma collection."""
        if self._collection is None:
            try:
                import chromadb
                
                self._client = chromadb.PersistentClient(path=str(self.path))
                self._collection = self._client.get_or_create_collection(
                    name=self.collection_name
                )
            except ImportError:
                logger.warning("ChromaDB not installed, falling back to file store")
                raise RuntimeError("ChromaDB not installed. Install with: pip install chromadb")
        
        return self._collection
    
    async def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        texts: List[str],
        metadata: List[Dict[str, Any]],
    ) -> None:
        """Add documents to the store."""
        collection = self._get_collection()
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadata,
        )
    
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Search for similar documents."""
        collection = self._get_collection()
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter,
        )
        
        search_results = []
        for i in range(len(results["ids"][0])):
            search_results.append(SearchResult(
                id=results["ids"][0][i],
                text=results["documents"][0][i],
                score=1.0 - results["distances"][0][i],  # Convert distance to similarity
                metadata=results["metadatas"][0][i] if results["metadatas"] else {},
            ))
        
        return search_results
    
    async def delete(self, ids: List[str]) -> None:
        """Delete documents by ID."""
        collection = self._get_collection()
        collection.delete(ids=ids)
    
    async def count(self) -> int:
        """Get document count."""
        collection = self._get_collection()
        return collection.count()
    
    async def clear(self) -> None:
        """Clear all documents."""
        if self._client and self._collection:
            self._client.delete_collection(self.collection_name)
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name
            )


class LocalVectorStore:
    """
    Local vector store with multiple backend options.
    
    Supports:
    - Memory backend (fast, not persistent)
    - File backend (persistent, simple)
    - Chroma backend (efficient, feature-rich)
    
    Example:
        ```python
        # Create with default settings
        store = LocalVectorStore(path="./RAG/.vector_store")
        
        # Add documents
        await store.add(
            ids=["doc1", "doc2"],
            embeddings=[[0.1, ...], [0.2, ...]],
            texts=["Document 1", "Document 2"],
            metadata=[{"source": "file1"}, {"source": "file2"}]
        )
        
        # Search
        results = await store.search(query_embedding, top_k=5)
        ```
    """
    
    def __init__(
        self,
        path: str = "./RAG/.vector_store",
        engine: str = "file",
        dimensions: int = 768,
    ):
        """
        Initialize local vector store.
        
        Args:
            path: Path to store data
            engine: Backend engine (memory, file, chroma)
            dimensions: Embedding dimensions
        """
        self.path = Path(path)
        self.engine = engine
        self.dimensions = dimensions
        self._backend: Optional[VectorStoreBackend] = None
    
    def _get_backend(self) -> VectorStoreBackend:
        """Get or create backend."""
        if self._backend is None:
            if self.engine == "memory":
                self._backend = MemoryVectorStore(dimensions=self.dimensions)
            elif self.engine == "chroma":
                self._backend = ChromaVectorStore(path=self.path)
            else:  # Default to file
                self._backend = FileVectorStore(
                    path=self.path,
                    dimensions=self.dimensions
                )
        return self._backend
    
    async def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        texts: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """
        Add documents to the store.
        
        Args:
            ids: Document IDs
            embeddings: Embedding vectors
            texts: Document texts
            metadata: Optional metadata for each document
        """
        backend = self._get_backend()
        await backend.add(
            ids=ids,
            embeddings=embeddings,
            texts=texts,
            metadata=metadata or [{}] * len(ids),
        )
    
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """
        Search for similar documents.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of search results
        """
        backend = self._get_backend()
        return await backend.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filter=filter,
        )
    
    async def delete(self, ids: List[str]) -> None:
        """
        Delete documents by ID.
        
        Args:
            ids: Document IDs to delete
        """
        backend = self._get_backend()
        await backend.delete(ids)
    
    async def count(self) -> int:
        """Get document count."""
        backend = self._get_backend()
        return await backend.count()
    
    async def clear(self) -> None:
        """Clear all documents."""
        backend = self._get_backend()
        await backend.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get store statistics."""
        return {
            "engine": self.engine,
            "path": str(self.path),
            "dimensions": self.dimensions,
        }
