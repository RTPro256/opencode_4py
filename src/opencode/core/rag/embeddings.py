"""
Embedding engine for RAG pipeline.

Supports multiple embedding providers:
- Ollama (local models like nomic-embed-text)
- OpenAI (text-embedding-ada-002, etc.)
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import asyncio

from opencode.core.defaults import (
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_EMBEDDING_DIMENSIONS,
    OLLAMA_BASE_URL,
    EMBEDDING_TIMEOUT,
)

from .config import RAGConfig


class EmbeddingEngine(ABC):
    """Abstract base class for embedding engines."""
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        pass
    
    @abstractmethod
    def get_dimensions(self) -> int:
        """Get the dimensionality of embeddings.
        
        Returns:
            Number of dimensions
        """
        pass


class OllamaEmbeddingEngine(EmbeddingEngine):
    """Embedding engine using Ollama."""
    
    def __init__(
        self,
        model: str = DEFAULT_EMBEDDING_MODEL,
        base_url: str = OLLAMA_BASE_URL,
        dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS
    ):
        """Initialize Ollama embedding engine.
        
        Args:
            model: Ollama model name
            base_url: Ollama API URL
            dimensions: Embedding dimensions
        """
        self.model = model
        self.base_url = base_url
        self.dimensions = dimensions
    
    async def embed(self, text: str) -> List[float]:
        """Generate embedding using Ollama.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        try:
            import ollama
            
            response = ollama.embed(
                model=self.model,
                input=[text]
            )
            return response.embeddings[0]
        except ImportError:
            # Fallback to HTTP API
            return await self._embed_http(text)
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            import ollama
            
            response = ollama.embed(
                model=self.model,
                input=texts
            )
            return response.embeddings
        except ImportError:
            # Fallback to HTTP API
            return await self._embed_batch_http(texts)
    
    async def _embed_http(self, text: str) -> List[float]:
        """Embed using HTTP API.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text}
            )
            response.raise_for_status()
            data = response.json()
            return data["embedding"]
    
    async def _embed_batch_http(self, texts: List[str]) -> List[List[float]]:
        """Embed batch using HTTP API.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        # Ollama HTTP API doesn't support batch, so embed one by one
        embeddings = []
        for text in texts:
            embedding = await self._embed_http(text)
            embeddings.append(embedding)
        return embeddings
    
    def get_dimensions(self) -> int:
        """Get embedding dimensions."""
        return self.dimensions


class OpenAIEmbeddingEngine(EmbeddingEngine):
    """Embedding engine using OpenAI API."""
    
    def __init__(
        self,
        model: str = "text-embedding-ada-002",
        api_key: Optional[str] = None,
        dimensions: int = 1536
    ):
        """Initialize OpenAI embedding engine.
        
        Args:
            model: OpenAI model name
            api_key: OpenAI API key
            dimensions: Embedding dimensions
        """
        self.model = model
        self.api_key = api_key
        self.dimensions = dimensions
    
    async def embed(self, text: str) -> List[float]:
        """Generate embedding using OpenAI.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        import httpx
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers=headers,
                json={"model": self.model, "input": text}
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        import httpx
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers=headers,
                json={"model": self.model, "input": texts}
            )
            response.raise_for_status()
            data = response.json()
            return [item["embedding"] for item in data["data"]]
    
    def get_dimensions(self) -> int:
        """Get embedding dimensions."""
        return self.dimensions


def create_embedding_engine(config: RAGConfig) -> EmbeddingEngine:
    """Create an embedding engine based on configuration.
    
    Args:
        config: RAG configuration
        
    Returns:
        Embedding engine instance
    """
    provider = config.embedding_provider.lower()
    
    if provider == "ollama":
        return OllamaEmbeddingEngine(
            model=config.embedding_model,
            dimensions=config.embedding_dimensions
        )
    elif provider == "openai":
        import os
        return OpenAIEmbeddingEngine(
            model=config.embedding_model,
            api_key=os.environ.get("OPENAI_API_KEY"),
            dimensions=config.embedding_dimensions
        )
    else:
        raise ValueError(f"Unknown embedding provider: {provider}")
