"""
Tests for RAG Methods Module.

Tests for the integrated RAG method implementations.
"""

import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src" / "opencode" / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from opencode.core.rag.methods import (
    BaseRAGMethod,
    RAGMethodConfig,
    RAGResult,
    RetrievedDocument,
    create_rag_method,
    get_available_methods,
)
from opencode.core.rag.methods.base import (
    RetrievalStrategy,
    ChunkingStrategy,
    SimpleRAGMethod,
)
from opencode.core.rag.methods.naive_rag import NaiveRAG, NaiveRAGConfig
from opencode.core.rag.methods.hyde import HyDeRAG, HyDeConfig
from opencode.core.rag.methods.self_rag import SelfRAG, SelfRAGConfig


class TestRAGMethodConfig:
    """Tests for RAGMethodConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = RAGMethodConfig()
        
        assert config.retrieval_strategy == RetrievalStrategy.SEMANTIC
        assert config.top_k == 5
        assert config.chunk_size == 1000
        assert config.chunk_overlap == 200
        assert config.embedding_model == "mxbai-embed-large"
        assert config.temperature == 0.0
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = RAGMethodConfig(
            top_k=10,
            chunk_size=2000,
            temperature=0.5,
        )
        
        assert config.top_k == 10
        assert config.chunk_size == 2000
        assert config.temperature == 0.5
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Invalid top_k
        with pytest.raises(ValueError):
            RAGMethodConfig(top_k=0)
        
        with pytest.raises(ValueError):
            RAGMethodConfig(top_k=101)
        
        # Invalid temperature
        with pytest.raises(ValueError):
            RAGMethodConfig(temperature=-0.1)
        
        with pytest.raises(ValueError):
            RAGMethodConfig(temperature=2.1)


class TestRetrievedDocument:
    """Tests for RetrievedDocument."""
    
    def test_document_creation(self):
        """Test creating a retrieved document."""
        doc = RetrievedDocument(
            content="Test content",
            score=0.95,
            source="test_source",
            title="Test Title",
        )
        
        assert doc.content == "Test content"
        assert doc.score == 0.95
        assert doc.source == "test_source"
        assert doc.title == "Test Title"
    
    def test_document_to_dict(self):
        """Test converting document to dictionary."""
        doc = RetrievedDocument(
            content="Test content",
            score=0.95,
            metadata={"key": "value"},
        )
        
        result = doc.to_dict()
        
        assert result["content"] == "Test content"
        assert result["score"] == 0.95
        assert result["metadata"] == {"key": "value"}


class TestRAGResult:
    """Tests for RAGResult."""
    
    def test_result_creation(self):
        """Test creating a RAG result."""
        result = RAGResult(
            answer="Test answer",
            sources=[
                RetrievedDocument(content="Source 1"),
                RetrievedDocument(content="Source 2"),
            ],
            confidence=0.8,
        )
        
        assert result.answer == "Test answer"
        assert len(result.sources) == 2
        assert result.confidence == 0.8
    
    def test_result_to_dict(self):
        """Test converting result to dictionary."""
        result = RAGResult(
            answer="Test answer",
            sources=[RetrievedDocument(content="Source")],
            confidence=0.8,
            self_reflection_passed=True,
        )
        
        d = result.to_dict()
        
        assert d["answer"] == "Test answer"
        assert d["confidence"] == 0.8
        assert d["self_reflection_passed"] is True


class TestSimpleRAGMethod:
    """Tests for SimpleRAGMethod."""
    
    @pytest.mark.asyncio
    async def test_simple_query(self):
        """Test simple query without providers."""
        method = SimpleRAGMethod()
        
        # Index some documents
        await method.index_documents([
            "Python is a programming language.",
            "Machine learning uses algorithms.",
        ])
        
        # Query
        result = await method.query("What is Python?")
        
        assert result.answer is not None
        assert len(result.sources) > 0
    
    @pytest.mark.asyncio
    async def test_index_documents(self):
        """Test indexing documents."""
        method = SimpleRAGMethod()
        
        count = await method.index_documents([
            "Document 1",
            "Document 2",
            "Document 3",
        ])
        
        assert count == 3


class TestNaiveRAG:
    """Tests for NaiveRAG."""
    
    def test_method_info(self):
        """Test method info."""
        info = NaiveRAG.get_method_info()
        
        assert info["name"] == "naive"
        assert "simple" in info["description"].lower()
    
    @pytest.mark.asyncio
    async def test_query_without_providers(self):
        """Test query without external providers."""
        config = NaiveRAGConfig(top_k=3)
        method = NaiveRAG(config=config)
        
        # Index documents
        await method.index_documents([
            "The capital of France is Paris.",
            "The capital of Germany is Berlin.",
            "The capital of Italy is Rome.",
        ])
        
        # Query
        result = await method.query("What is the capital of France?")
        
        assert result.answer is not None
        assert result.metadata["method"] == "naive"
    
    def test_chunk_document(self):
        """Test document chunking."""
        method = NaiveRAG()
        
        # Short document
        chunks = method._chunk_document("Short text")
        assert len(chunks) == 1
        
        # Long document
        long_text = " ".join(["word"] * 2000)
        chunks = method._chunk_document(long_text)
        assert len(chunks) > 1


class TestHyDeRAG:
    """Tests for HyDeRAG."""
    
    def test_method_info(self):
        """Test method info."""
        info = HyDeRAG.get_method_info()
        
        assert info["name"] == "hyde"
        assert "hypothetical" in info["description"].lower()
    
    @pytest.mark.asyncio
    async def test_query_without_llm(self):
        """Test query without LLM (fallback behavior)."""
        config = HyDeConfig(top_k=2)
        method = HyDeRAG(config=config)
        
        await method.index_documents([
            "Python is used for web development.",
        ])
        
        result = await method.query("What is Python used for?")
        
        assert result.answer is not None
        assert result.metadata["method"] == "hyde"
    
    def test_embedding_combination(self):
        """Test embedding combination strategies."""
        method = HyDeRAG()
        
        emb1 = [1.0, 2.0, 3.0]
        emb2 = [4.0, 5.0, 6.0]
        
        # Average
        avg = method._average_embeddings([emb1, emb2])
        assert avg == [2.5, 3.5, 4.5]
        
        # Max pool
        max_pooled = method._max_pool_embeddings([emb1, emb2])
        assert max_pooled == [4.0, 5.0, 6.0]


class TestSelfRAG:
    """Tests for SelfRAG."""
    
    def test_method_info(self):
        """Test method info."""
        info = SelfRAG.get_method_info()
        
        assert info["name"] == "self"
        assert "reflective" in info["description"].lower()
    
    @pytest.mark.asyncio
    async def test_query_without_llm(self):
        """Test query without LLM (no reflection checks)."""
        config = SelfRAGConfig(max_iterations=1)
        method = SelfRAG(config=config)
        
        await method.index_documents([
            "The Earth orbits the Sun.",
        ])
        
        result = await method.query("What orbits the Sun?")
        
        assert result.answer is not None
        assert result.metadata["method"] == "self"


class TestRAGMethodRegistry:
    """Tests for RAG method registry."""
    
    def test_get_available_methods(self):
        """Test getting available methods."""
        methods = get_available_methods()
        
        assert "naive" in methods
        assert "hyde" in methods
        assert "self" in methods
        assert len(methods) >= 3
    
    def test_create_rag_method(self):
        """Test creating RAG methods via factory."""
        config = RAGMethodConfig()
        
        # Create naive method
        method = create_rag_method("naive", config)
        assert isinstance(method, NaiveRAG)
        
        # Create hyde method
        method = create_rag_method("hyde", config)
        assert isinstance(method, HyDeRAG)
        
        # Invalid method
        with pytest.raises(ValueError):
            create_rag_method("invalid", config)


class TestWithMockedProviders:
    """Tests with mocked providers."""
    
    @pytest.mark.asyncio
    async def test_naive_rag_with_mocked_embedding(self):
        """Test NaiveRAG with mocked embedding provider."""
        mock_embedding = AsyncMock()
        mock_embedding.embed_query = AsyncMock(return_value=[0.1] * 768)
        mock_embedding.embed_texts = AsyncMock(return_value=[[0.1] * 768])
        
        mock_store = AsyncMock()
        mock_store.search = AsyncMock(return_value=[
            RetrievedDocument(content="Test result", score=0.9),
        ])
        mock_store.add_documents = AsyncMock()
        
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(return_value="Generated answer")
        
        method = NaiveRAG(
            embedding_provider=mock_embedding,
            vector_store=mock_store,
            llm_provider=mock_llm,
        )
        
        result = await method.query("Test question")
        
        assert result.answer == "Generated answer"
        mock_embedding.embed_query.assert_called_once()
        mock_store.search.assert_called_once()
        mock_llm.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_hyde_with_mocked_llm(self):
        """Test HyDeRAG with mocked LLM for hypothetical generation."""
        mock_embedding = AsyncMock()
        mock_embedding.embed_query = AsyncMock(return_value=[0.1] * 768)
        mock_embedding.embed_texts = AsyncMock(return_value=[[0.1] * 768])
        
        mock_store = AsyncMock()
        mock_store.search = AsyncMock(return_value=[
            RetrievedDocument(content="Test result", score=0.9),
        ])
        
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(side_effect=[
            "Hypothetical answer to the question.",
            "Final generated answer.",
        ])
        
        method = HyDeRAG(
            embedding_provider=mock_embedding,
            vector_store=mock_store,
            llm_provider=mock_llm,
        )
        
        result = await method.query("Test question")
        
        assert result.answer == "Final generated answer."
        assert len(result.metadata.get("hypothetical_docs", [])) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
