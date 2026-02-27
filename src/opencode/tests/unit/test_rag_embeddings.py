"""Tests for RAG Embeddings module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from opencode.core.rag.embeddings import (
    EmbeddingEngine,
    OllamaEmbeddingEngine,
    OpenAIEmbeddingEngine,
    create_embedding_engine,
)
from opencode.core.rag.config import RAGConfig


class TestEmbeddingEngine:
    """Tests for EmbeddingEngine abstract base class."""

    def test_is_abstract(self):
        """Test that EmbeddingEngine is abstract."""
        with pytest.raises(TypeError):
            EmbeddingEngine()

    def test_abstract_methods(self):
        """Test that abstract methods must be implemented."""
        # OllamaEmbeddingEngine implements all abstract methods
        engine = OllamaEmbeddingEngine()
        assert hasattr(engine, 'embed')
        assert hasattr(engine, 'embed_batch')
        assert hasattr(engine, 'get_dimensions')


class TestOllamaEmbeddingEngine:
    """Tests for OllamaEmbeddingEngine."""

    def test_init_default(self):
        """Test default initialization."""
        engine = OllamaEmbeddingEngine()
        
        assert engine.model == "nomic-embed-text"
        assert engine.base_url == "http://localhost:11434"
        assert engine.dimensions == 768

    def test_init_custom(self):
        """Test custom initialization."""
        engine = OllamaEmbeddingEngine(
            model="custom-model",
            base_url="http://custom:8080",
            dimensions=512
        )
        
        assert engine.model == "custom-model"
        assert engine.base_url == "http://custom:8080"
        assert engine.dimensions == 512

    def test_get_dimensions(self):
        """Test get_dimensions method."""
        engine = OllamaEmbeddingEngine(dimensions=1024)
        
        assert engine.get_dimensions() == 1024

    @pytest.mark.asyncio
    async def test_embed_http(self):
        """Test embed using HTTP API."""
        engine = OllamaEmbeddingEngine()
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"embedding": [0.5, 0.6, 0.7]}
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await engine._embed_http("test text")
            
            assert result == [0.5, 0.6, 0.7]

    @pytest.mark.asyncio
    async def test_embed_batch_http(self):
        """Test embed_batch using HTTP API."""
        engine = OllamaEmbeddingEngine()
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"embedding": [0.5, 0.6]}
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await engine._embed_batch_http(["text1", "text2"])
            
            assert len(result) == 2


class TestOpenAIEmbeddingEngine:
    """Tests for OpenAIEmbeddingEngine."""

    def test_init_default(self):
        """Test default initialization."""
        engine = OpenAIEmbeddingEngine()
        
        assert engine.model == "text-embedding-ada-002"
        assert engine.api_key is None
        assert engine.dimensions == 1536

    def test_init_custom(self):
        """Test custom initialization."""
        engine = OpenAIEmbeddingEngine(
            model="text-embedding-3-small",
            api_key="test-key",
            dimensions=512
        )
        
        assert engine.model == "text-embedding-3-small"
        assert engine.api_key == "test-key"
        assert engine.dimensions == 512

    def test_get_dimensions(self):
        """Test get_dimensions method."""
        engine = OpenAIEmbeddingEngine(dimensions=3072)
        
        assert engine.get_dimensions() == 3072

    @pytest.mark.asyncio
    async def test_embed(self):
        """Test embed method."""
        engine = OpenAIEmbeddingEngine(api_key="test-key")
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [{"embedding": [0.1, 0.2, 0.3]}]
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await engine.embed("test text")
            
            assert result == [0.1, 0.2, 0.3]

    @pytest.mark.asyncio
    async def test_embed_batch(self):
        """Test embed_batch method."""
        engine = OpenAIEmbeddingEngine(api_key="test-key")
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {"embedding": [0.1, 0.2]},
                {"embedding": [0.3, 0.4]}
            ]
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await engine.embed_batch(["text1", "text2"])
            
            assert len(result) == 2
            assert result[0] == [0.1, 0.2]
            assert result[1] == [0.3, 0.4]


class TestCreateEmbeddingEngine:
    """Tests for create_embedding_engine function."""

    def test_create_ollama_engine(self):
        """Test creating Ollama embedding engine."""
        config = RAGConfig(
            embedding_provider="ollama",
            embedding_model="nomic-embed-text",
            embedding_dimensions=768
        )
        
        engine = create_embedding_engine(config)
        
        assert engine.model == "nomic-embed-text"
        assert engine.dimensions == 768

    def test_create_openai_engine(self):
        """Test creating OpenAI embedding engine."""
        config = RAGConfig(
            embedding_provider="openai",
            embedding_model="text-embedding-ada-002",
            embedding_dimensions=1536
        )
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            engine = create_embedding_engine(config)
            
            assert engine.model == "text-embedding-ada-002"
            assert engine.api_key == "test-key"

    def test_create_unknown_provider(self):
        """Test creating engine with unknown provider."""
        config = RAGConfig(
            embedding_provider="unknown",
            embedding_model="model",
            embedding_dimensions=512
        )
        
        with pytest.raises(ValueError, match="Unknown embedding provider"):
            create_embedding_engine(config)

    def test_create_case_insensitive(self):
        """Test provider name is case insensitive."""
        config = RAGConfig(
            embedding_provider="OLLAMA",
            embedding_model="nomic-embed-text",
            embedding_dimensions=768
        )
        
        engine = create_embedding_engine(config)
        
        assert engine.model == "nomic-embed-text"
