"""
Tests for Local Embeddings.

Tests embedding cache and local embedding engine functionality.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import tempfile
import json
import hashlib

from opencode.core.rag.local_embeddings import (
    EmbeddingCache,
    LocalEmbeddingConfig,
    LocalEmbeddingEngine,
    create_local_embedding_engine,
)


class TestEmbeddingCache:
    """Tests for EmbeddingCache class."""

    def test_init_default_path(self):
        """Test initialization with default path."""
        cache = EmbeddingCache()
        assert cache.cache_path is not None
        assert isinstance(cache._memory_cache, dict)

    def test_init_custom_path(self):
        """Test initialization with custom path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "test_cache"
            cache = EmbeddingCache(cache_path)
            assert cache.cache_path == cache_path
            assert cache.cache_path.exists()

    def test_get_cache_key(self):
        """Test cache key generation."""
        cache = EmbeddingCache()
        
        key1 = cache._get_cache_key("hello", "model-a")
        key2 = cache._get_cache_key("hello", "model-b")
        key3 = cache._get_cache_key("hello", "model-a")
        
        # Same text and model should produce same key
        assert key1 == key3
        # Different models should produce different keys
        assert key1 != key2
        # Key should be a hex string
        assert all(c in '0123456789abcdef' for c in key1)

    def test_get_cache_file(self):
        """Test cache file path generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "test_cache"
            cache = EmbeddingCache(cache_path)
            
            file_path = cache._get_cache_file("testkey123")
            assert file_path == cache_path / "testkey123.json"

    def test_set_and_get_memory_cache(self):
        """Test setting and getting from memory cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = EmbeddingCache(Path(tmpdir) / "test_cache")
            
            embedding = [0.1, 0.2, 0.3]
            cache.set("test text", "test-model", embedding)
            
            # Should be in memory cache
            result = cache.get("test text", "test-model")
            assert result == embedding

    def test_set_and_get_file_cache(self):
        """Test setting and getting from file cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "test_cache"
            cache = EmbeddingCache(cache_path)
            
            embedding = [0.1, 0.2, 0.3]
            cache.set("test text", "test-model", embedding)
            
            # Clear memory cache
            cache._memory_cache.clear()
            
            # Should load from file
            result = cache.get("test text", "test-model")
            assert result == embedding

    def test_get_not_found(self):
        """Test getting when not cached."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = EmbeddingCache(Path(tmpdir) / "test_cache")
            
            result = cache.get("nonexistent", "model")
            assert result is None

    def test_get_corrupted_cache_file(self):
        """Test getting with corrupted cache file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "test_cache"
            cache = EmbeddingCache(cache_path)
            
            # Create corrupted cache file
            key = cache._get_cache_key("test", "model")
            cache_file = cache._get_cache_file(key)
            cache_file.write_text("not valid json")
            
            # Should return None and not crash
            result = cache.get("test", "model")
            assert result is None

    def test_clear(self):
        """Test clearing the cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "test_cache"
            cache = EmbeddingCache(cache_path)
            
            cache.set("text1", "model", [0.1])
            cache.set("text2", "model", [0.2])
            
            cache.clear()
            
            assert len(cache._memory_cache) == 0
            assert len(list(cache.cache_path.glob("*.json"))) == 0

    def test_get_stats(self):
        """Test getting cache statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "test_cache"
            cache = EmbeddingCache(cache_path)
            
            cache.set("text1", "model", [0.1])
            cache.set("text2", "model", [0.2])
            
            stats = cache.get_stats()
            
            assert stats["memory_cache_size"] == 2
            assert stats["file_cache_count"] == 2
            assert "cache_path" in stats


class TestLocalEmbeddingConfig:
    """Tests for LocalEmbeddingConfig model."""

    def test_init_defaults(self):
        """Test initialization with default values."""
        config = LocalEmbeddingConfig()
        assert config.model == "nomic-embed-text"
        assert config.base_url == "http://localhost:11434"
        assert config.dimensions == 768
        assert config.batch_size == 32
        assert config.cache_enabled is True
        assert config.cache_path == "./RAG/.embedding_cache"

    def test_init_custom(self):
        """Test initialization with custom values."""
        config = LocalEmbeddingConfig(
            model="custom-model",
            base_url="http://custom:8080",
            dimensions=512,
            batch_size=16,
            cache_enabled=False,
            cache_path="/custom/path",
        )
        assert config.model == "custom-model"
        assert config.base_url == "http://custom:8080"
        assert config.dimensions == 512
        assert config.batch_size == 16
        assert config.cache_enabled is False
        assert config.cache_path == "/custom/path"


class TestLocalEmbeddingEngine:
    """Tests for LocalEmbeddingEngine class."""

    def test_init_defaults(self):
        """Test initialization with default config."""
        engine = LocalEmbeddingEngine()
        assert engine.config is not None
        assert engine.cache is not None
        assert engine._client is None

    def test_init_custom_config(self):
        """Test initialization with custom config."""
        config = LocalEmbeddingConfig(model="custom-model")
        engine = LocalEmbeddingEngine(config)
        assert engine.config.model == "custom-model"

    def test_init_cache_disabled(self):
        """Test initialization with cache disabled."""
        config = LocalEmbeddingConfig(cache_enabled=False)
        engine = LocalEmbeddingEngine(config)
        assert engine.cache is None

    def test_get_dimensions(self):
        """Test getting dimensions."""
        config = LocalEmbeddingConfig(dimensions=512)
        engine = LocalEmbeddingEngine(config)
        assert engine.get_dimensions() == 512

    def test_get_stats(self):
        """Test getting engine statistics."""
        engine = LocalEmbeddingEngine()
        stats = engine.get_stats()
        
        assert "model" in stats
        assert "dimensions" in stats
        assert "batch_size" in stats
        assert "cache_enabled" in stats
        assert "cache" in stats

    def test_get_stats_no_cache(self):
        """Test getting stats without cache."""
        config = LocalEmbeddingConfig(cache_enabled=False)
        engine = LocalEmbeddingEngine(config)
        stats = engine.get_stats()
        
        assert "cache" not in stats

    def test_clear_cache(self):
        """Test clearing cache."""
        engine = LocalEmbeddingEngine()
        assert engine.cache is not None
        engine.cache.set("test", "model", [0.1])
        
        engine.clear_cache()
        
        assert len(engine.cache._memory_cache) == 0

    def test_clear_cache_no_cache(self):
        """Test clearing cache when cache is disabled."""
        config = LocalEmbeddingConfig(cache_enabled=False)
        engine = LocalEmbeddingEngine(config)
        
        # Should not crash
        engine.clear_cache()

    @pytest.mark.asyncio
    async def test_embed_from_cache(self):
        """Test embedding from cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LocalEmbeddingConfig(
                cache_path=tmpdir + "/cache",
                cache_enabled=True,
            )
            engine = LocalEmbeddingEngine(config)
            assert engine.cache is not None
            
            # Pre-populate cache
            embedding = [0.1, 0.2, 0.3]
            engine.cache.set("test text", config.model, embedding)
            
            # Should return cached embedding
            result = await engine.embed("test text")
            assert result == embedding

    @pytest.mark.asyncio
    async def test_embed_with_ollama_client(self):
        """Test embedding with Ollama client."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LocalEmbeddingConfig(
                cache_path=tmpdir + "/cache",
                cache_enabled=False,
            )
            engine = LocalEmbeddingEngine(config)
            
            # Mock the Ollama client
            mock_client = MagicMock()
            mock_client.embed = MagicMock(return_value={
                "embeddings": [[0.1, 0.2, 0.3]]
            })
            engine._client = mock_client
            
            result = await engine.embed("test text")
            
            assert result == [0.1, 0.2, 0.3]
            mock_client.embed.assert_called_once()

    @pytest.mark.asyncio
    async def test_embed_batch_from_cache(self):
        """Test batch embedding from cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LocalEmbeddingConfig(
                cache_path=tmpdir + "/cache",
                cache_enabled=True,
            )
            engine = LocalEmbeddingEngine(config)
            assert engine.cache is not None
            
            # Pre-populate cache
            engine.cache.set("text1", config.model, [0.1])
            engine.cache.set("text2", config.model, [0.2])
            
            results = await engine.embed_batch(["text1", "text2"])
            
            assert len(results) == 2
            assert results[0] == [0.1]
            assert results[1] == [0.2]

    @pytest.mark.asyncio
    async def test_embed_batch_partial_cache(self):
        """Test batch embedding with partial cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LocalEmbeddingConfig(
                cache_path=tmpdir + "/cache",
                cache_enabled=True,
            )
            engine = LocalEmbeddingEngine(config)
            assert engine.cache is not None
            
            # Pre-populate cache for one text
            engine.cache.set("text1", config.model, [0.1])
            
            # Mock client for uncached text
            mock_client = MagicMock()
            mock_client.embed = MagicMock(return_value={
                "embeddings": [[0.2]]
            })
            engine._client = mock_client
            
            results = await engine.embed_batch(["text1", "text2"])
            
            assert len(results) == 2
            assert results[0] == [0.1]  # From cache
            assert results[1] == [0.2]  # From API

    @pytest.mark.asyncio
    async def test_embed_batch_with_client(self):
        """Test batch embedding with Ollama client."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LocalEmbeddingConfig(
                cache_path=tmpdir + "/cache",
                cache_enabled=False,
            )
            engine = LocalEmbeddingEngine(config)
            
            mock_client = MagicMock()
            mock_client.embed = MagicMock(return_value={
                "embeddings": [[0.1], [0.2]]
            })
            engine._client = mock_client
            
            results = await engine.embed_batch(["text1", "text2"])
            
            assert len(results) == 2
            assert results[0] == [0.1]
            assert results[1] == [0.2]

    @pytest.mark.asyncio
    async def test_embed_batch_respects_batch_size(self):
        """Test that batch embedding respects batch size."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LocalEmbeddingConfig(
                cache_path=tmpdir + "/cache",
                cache_enabled=False,
                batch_size=2,
            )
            engine = LocalEmbeddingEngine(config)
            
            mock_client = MagicMock()
            # Return appropriate number of embeddings for each batch
            mock_client.embed = MagicMock(side_effect=[
                {"embeddings": [[0.1], [0.2]]},
                {"embeddings": [[0.3], [0.4]]},
                {"embeddings": [[0.5]]},
            ])
            engine._client = mock_client
            
            results = await engine.embed_batch(["t1", "t2", "t3", "t4", "t5"])
            
            assert len(results) == 5
            assert mock_client.embed.call_count == 3

    def test_get_client_creates_client(self):
        """Test that _get_client creates Ollama client."""
        engine = LocalEmbeddingEngine()
        
        # Mock the import inside the method
        mock_client = MagicMock()
        with patch.dict('sys.modules', {'ollama': MagicMock(Client=MagicMock(return_value=mock_client))}):
            client = engine._get_client()
            
            assert client == mock_client

    def test_get_client_no_ollama_package(self):
        """Test _get_client when ollama package not installed."""
        engine = LocalEmbeddingEngine()
        
        # Simulate ImportError when trying to import ollama
        with patch.dict('sys.modules', {}):
            # Remove ollama from available modules
            with patch('builtins.__import__', side_effect=ImportError("No module named 'ollama'")):
                client = engine._get_client()
                
                assert client is None


class TestCreateLocalEmbeddingEngine:
    """Tests for create_local_embedding_engine factory function."""

    def test_create_defaults(self):
        """Test creating with default values."""
        engine = create_local_embedding_engine()
        
        assert engine.config.model == "nomic-embed-text"
        assert engine.config.cache_enabled is True

    def test_create_custom_model(self):
        """Test creating with custom model."""
        engine = create_local_embedding_engine(model="custom-model")
        
        assert engine.config.model == "custom-model"

    def test_create_cache_disabled(self):
        """Test creating with cache disabled."""
        engine = create_local_embedding_engine(cache_enabled=False)
        
        assert engine.config.cache_enabled is False
        assert engine.cache is None

    def test_create_custom_cache_path(self):
        """Test creating with custom cache path."""
        engine = create_local_embedding_engine(cache_path="/custom/path")
        
        assert engine.config.cache_path == "/custom/path"

    def test_create_with_additional_kwargs(self):
        """Test creating with additional kwargs."""
        engine = create_local_embedding_engine(
            dimensions=512,
            batch_size=16,
        )
        
        assert engine.config.dimensions == 512
        assert engine.config.batch_size == 16
