"""
Local Embedding Engine for Privacy-First RAG.

Provides local embedding generation using Ollama with caching support.
No external API calls - all embeddings generated locally.
"""

import asyncio
import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from opencode.core.defaults import (
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_EMBEDDING_DIMENSIONS,
    DEFAULT_BATCH_SIZE,
    DEFAULT_EMBEDDING_CACHE_PATH,
    OLLAMA_BASE_URL,
)

logger = logging.getLogger(__name__)


class EmbeddingCache:
    """
    Cache for embeddings to avoid regenerating for same text.
    
    Uses file-based storage for persistence across sessions.
    """
    
    def __init__(self, cache_path: Optional[Path] = None):
        """
        Initialize the embedding cache.
        
        Args:
            cache_path: Path to cache directory
        """
        self.cache_path = cache_path or Path("./RAG/.embedding_cache")
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self._memory_cache: Dict[str, List[float]] = {}
    
    def _get_cache_key(self, text: str, model: str) -> str:
        """Generate cache key from text and model."""
        content = f"{model}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _get_cache_file(self, key: str) -> Path:
        """Get cache file path for key."""
        return self.cache_path / f"{key}.json"
    
    def get(self, text: str, model: str) -> Optional[List[float]]:
        """
        Get cached embedding if available.
        
        Args:
            text: Text to get embedding for
            model: Model name
            
        Returns:
            Cached embedding or None
        """
        key = self._get_cache_key(text, model)
        
        # Check memory cache first
        if key in self._memory_cache:
            return self._memory_cache[key]
        
        # Check file cache
        cache_file = self._get_cache_file(key)
        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    data = json.load(f)
                    embedding = data["embedding"]
                    self._memory_cache[key] = embedding
                    return embedding
            except Exception as e:
                logger.warning(f"Failed to read cache: {e}")
        
        return None
    
    def set(self, text: str, model: str, embedding: List[float]) -> None:
        """
        Cache an embedding.
        
        Args:
            text: Text that was embedded
            model: Model name
            embedding: Embedding vector
        """
        key = self._get_cache_key(text, model)
        
        # Store in memory cache
        self._memory_cache[key] = embedding
        
        # Store in file cache
        cache_file = self._get_cache_file(key)
        try:
            with open(cache_file, "w") as f:
                json.dump({
                    "text_hash": hashlib.sha256(text.encode()).hexdigest(),
                    "model": model,
                    "embedding": embedding,
                }, f)
        except Exception as e:
            logger.warning(f"Failed to write cache: {e}")
    
    def clear(self) -> None:
        """Clear the cache."""
        self._memory_cache.clear()
        for cache_file in self.cache_path.glob("*.json"):
            cache_file.unlink()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        file_count = len(list(self.cache_path.glob("*.json")))
        return {
            "memory_cache_size": len(self._memory_cache),
            "file_cache_count": file_count,
            "cache_path": str(self.cache_path),
        }


class LocalEmbeddingConfig(BaseModel):
    """Configuration for local embedding engine."""
    
    model: str = Field(
        default=DEFAULT_EMBEDDING_MODEL,
        description="Ollama model for embeddings"
    )
    
    base_url: str = Field(
        default=OLLAMA_BASE_URL,
        description="Ollama API URL"
    )
    
    dimensions: int = Field(
        default=DEFAULT_EMBEDDING_DIMENSIONS,
        description="Embedding dimensions"
    )
    
    batch_size: int = Field(
        default=DEFAULT_BATCH_SIZE,
        description="Batch size for embedding"
    )
    
    cache_enabled: bool = Field(
        default=True,
        description="Enable embedding caching"
    )
    
    cache_path: Optional[str] = Field(
        default=DEFAULT_EMBEDDING_CACHE_PATH,
        description="Path to embedding cache"
    )


class LocalEmbeddingEngine:
    """
    Local embedding generation using Ollama.
    
    No external API calls - all embeddings generated locally.
    
    Features:
    - Uses Ollama for local embedding generation
    - Caching to avoid regenerating embeddings
    - Batch processing for efficiency
    - Offline capable
    
    Example:
        ```python
        config = LocalEmbeddingConfig(model="nomic-embed-text")
        engine = LocalEmbeddingEngine(config)
        
        # Single embedding
        embedding = await engine.embed("Hello world")
        
        # Batch embeddings
        embeddings = await engine.embed_batch(["Hello", "World"])
        ```
    """
    
    def __init__(self, config: Optional[LocalEmbeddingConfig] = None):
        """
        Initialize the local embedding engine.
        
        Args:
            config: Embedding configuration
        """
        self.config = config or LocalEmbeddingConfig()
        self.cache = EmbeddingCache(
            Path(self.config.cache_path) if self.config.cache_path else None
        ) if self.config.cache_enabled else None
        self._client = None
    
    def _get_client(self):
        """Get or create Ollama client."""
        if self._client is None:
            try:
                import ollama
                self._client = ollama.Client(host=self.config.base_url)
            except ImportError:
                logger.warning("Ollama package not installed, using HTTP API")
                self._client = None
        return self._client
    
    async def embed(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        # Check cache first
        if self.cache:
            cached = self.cache.get(text, self.config.model)
            if cached is not None:
                logger.debug(f"Cache hit for text (length={len(text)})")
                return cached
        
        # Generate embedding
        try:
            client = self._get_client()
            if client:
                # Use Ollama Python client
                response = client.embed(
                    model=self.config.model,
                    input=[text]
                )
                embedding = response["embeddings"][0]
            else:
                # Use HTTP API
                embedding = await self._embed_http(text)
            
            # Cache the result
            if self.cache:
                self.cache.set(text, self.config.model, embedding)
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Uses batched requests for efficiency.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        results = []
        uncached_texts = []
        uncached_indices = []
        
        # Check cache for each text
        for i, text in enumerate(texts):
            if self.cache:
                cached = self.cache.get(text, self.config.model)
                if cached is not None:
                    results.append((i, cached))
                    continue
            
            uncached_texts.append(text)
            uncached_indices.append(i)
        
        # Generate embeddings for uncached texts
        if uncached_texts:
            # Process in batches
            batch_size = self.config.batch_size
            new_embeddings = []
            
            for i in range(0, len(uncached_texts), batch_size):
                batch = uncached_texts[i:i + batch_size]
                batch_embeddings = await self._embed_batch_internal(batch)
                new_embeddings.extend(batch_embeddings)
            
            # Cache new embeddings
            for text, embedding in zip(uncached_texts, new_embeddings):
                if self.cache:
                    self.cache.set(text, self.config.model, embedding)
            
            # Add to results
            for idx, embedding in zip(uncached_indices, new_embeddings):
                results.append((idx, embedding))
        
        # Sort by original index and return
        results.sort(key=lambda x: x[0])
        return [embedding for _, embedding in results]
    
    async def _embed_batch_internal(self, texts: List[str]) -> List[List[float]]:
        """
        Internal batch embedding without cache checks.
        
        Args:
            texts: Texts to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            client = self._get_client()
            if client:
                # Use Ollama Python client
                response = client.embed(
                    model=self.config.model,
                    input=texts
                )
                return response["embeddings"]
            else:
                # Use HTTP API (process one by one)
                embeddings = []
                for text in texts:
                    embedding = await self._embed_http(text)
                    embeddings.append(embedding)
                return embeddings
                
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise
    
    async def _embed_http(self, text: str) -> List[float]:
        """
        Embed using HTTP API (fallback when ollama package not installed).
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.config.base_url}/api/embeddings",
                json={"model": self.config.model, "prompt": text},
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()
            return data["embedding"]
    
    def get_dimensions(self) -> int:
        """
        Get embedding dimensions.
        
        Returns:
            Number of dimensions
        """
        return self.config.dimensions
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get engine statistics.
        
        Returns:
            Statistics dictionary
        """
        stats = {
            "model": self.config.model,
            "dimensions": self.config.dimensions,
            "batch_size": self.config.batch_size,
            "cache_enabled": self.config.cache_enabled,
        }
        
        if self.cache:
            stats["cache"] = self.cache.get_stats()
        
        return stats
    
    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        if self.cache:
            self.cache.clear()


def create_local_embedding_engine(
    model: str = "nomic-embed-text",
    cache_enabled: bool = True,
    cache_path: Optional[str] = None,
    **kwargs
) -> LocalEmbeddingEngine:
    """
    Create a local embedding engine with sensible defaults.
    
    Args:
        model: Ollama model name
        cache_enabled: Enable caching
        cache_path: Path to cache directory
        **kwargs: Additional configuration options
        
    Returns:
        LocalEmbeddingEngine instance
    """
    config = LocalEmbeddingConfig(
        model=model,
        cache_enabled=cache_enabled,
        cache_path=cache_path,
        **kwargs
    )
    return LocalEmbeddingEngine(config)
