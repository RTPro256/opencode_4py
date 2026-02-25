"""
Unit tests for the RAG pipeline.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import numpy as np

from opencode.core.rag import (
    RAGConfig,
    RAGPipeline,
    Document,
    DocumentChunk,
    EmbeddingEngine,
    Retriever,
)
from opencode.core.rag.retriever import RetrievalResult


class TestRAGConfig:
    """Tests for RAGConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = RAGConfig()
        
        assert config.embedding_model == "nomic-embed-text"
        assert config.embedding_provider == "ollama"
        assert config.chunk_size == 500
        assert config.chunk_overlap == 50
        assert config.top_k == 3
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = RAGConfig(
            embedding_model="text-embedding-ada-002",
            embedding_provider="openai",
            chunk_size=1000,
            top_k=5
        )
        
        assert config.embedding_model == "text-embedding-ada-002"
        assert config.embedding_provider == "openai"
        assert config.chunk_size == 1000
        assert config.top_k == 5


class TestDocumentChunk:
    """Tests for DocumentChunk."""
    
    def test_create_chunk(self):
        """Test creating a document chunk."""
        chunk = DocumentChunk(
            text="This is a test chunk.",
            start_index=0,
            end_index=20,
            metadata={"source": "test"}
        )
        
        assert chunk.text == "This is a test chunk."
        assert chunk.length == 20
        assert chunk.has_embedding is False
    
    def test_chunk_with_embedding(self):
        """Test chunk with embedding."""
        chunk = DocumentChunk(
            text="Test",
            embedding=[0.1, 0.2, 0.3]
        )
        
        assert chunk.has_embedding is True
        assert chunk.embedding == [0.1, 0.2, 0.3]


class TestDocument:
    """Tests for Document."""
    
    def test_create_document(self):
        """Test creating a document."""
        doc = Document(
            text="This is a test document.",
            source="test.txt"
        )
        
        assert doc.text == "This is a test document."
        assert doc.source == "test.txt"
        assert doc.chunk_count == 0
    
    def test_document_with_chunks(self):
        """Test document with chunks."""
        chunks = [
            DocumentChunk(text="Chunk 1"),
            DocumentChunk(text="Chunk 2"),
        ]
        
        doc = Document(
            text="Chunk 1 Chunk 2",
            chunks=chunks
        )
        
        assert doc.chunk_count == 2
        assert doc.get_chunk_texts() == ["Chunk 1", "Chunk 2"]
    
    def test_has_embeddings(self):
        """Test has_embeddings property."""
        doc = Document(
            text="Test",
            chunks=[
                DocumentChunk(text="A", embedding=[0.1]),
                DocumentChunk(text="B", embedding=[0.2]),
            ]
        )
        
        assert doc.has_embeddings is True
        
        doc.chunks[0].embedding = None
        assert doc.has_embeddings is False


class MockEmbeddingEngine(EmbeddingEngine):
    """Mock embedding engine for testing."""
    
    async def embed(self, text: str) -> list[float]:
        """Return a mock embedding."""
        # Simple hash-based embedding for testing
        return [float(hash(text) % 100) / 100] * 768
    
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Return mock embeddings."""
        return [await self.embed(t) for t in texts]
    
    def get_dimensions(self) -> int:
        """Return embedding dimensions."""
        return 768


class TestRetriever:
    """Tests for Retriever."""
    
    def test_add_document(self):
        """Test adding a document to retriever."""
        config = RAGConfig()
        retriever = Retriever(config)
        
        doc = Document(
            text="Test document",
            chunks=[
                DocumentChunk(text="Chunk 1", embedding=[0.1, 0.2]),
                DocumentChunk(text="Chunk 2", embedding=[0.3, 0.4]),
            ]
        )
        
        retriever.add_document(doc)
        
        assert len(retriever.documents) == 1
        assert len(retriever.chunks) == 2
        assert retriever.embeddings is not None
    
    def test_remove_document(self):
        """Test removing a document."""
        config = RAGConfig()
        retriever = Retriever(config)
        
        doc = Document(
            id="doc-1",
            text="Test",
            chunks=[DocumentChunk(text="Chunk", embedding=[0.1])]
        )
        
        retriever.add_document(doc)
        assert len(retriever.documents) == 1
        
        retriever.remove_document("doc-1")
        assert len(retriever.documents) == 0
    
    @pytest.mark.asyncio
    async def test_retrieve(self):
        """Test retrieval."""
        config = RAGConfig(top_k=2)
        retriever = Retriever(config)
        
        # Add documents with different embeddings
        doc1 = Document(
            text="Document 1",
            chunks=[DocumentChunk(text="Apple fruit", embedding=[1.0, 0.0, 0.0])]
        )
        doc2 = Document(
            text="Document 2",
            chunks=[DocumentChunk(text="Banana fruit", embedding=[0.0, 1.0, 0.0])]
        )
        doc3 = Document(
            text="Document 3",
            chunks=[DocumentChunk(text="Car vehicle", embedding=[0.0, 0.0, 1.0])]
        )
        
        retriever.add_document(doc1)
        retriever.add_document(doc2)
        retriever.add_document(doc3)
        
        # Query similar to "Apple"
        results = await retriever.retrieve([0.9, 0.1, 0.0])
        
        assert len(results) <= 2
        # First result should be most similar to "Apple"
        if results:
            assert results[0].chunk.text == "Apple fruit"
    
    def test_get_stats(self):
        """Test getting retriever stats."""
        config = RAGConfig()
        retriever = Retriever(config)
        
        stats = retriever.get_stats()
        
        assert stats["document_count"] == 0
        assert stats["chunk_count"] == 0


class TestRAGPipeline:
    """Tests for RAGPipeline."""
    
    @pytest.mark.asyncio
    async def test_add_document(self):
        """Test adding a document to the pipeline."""
        pipeline = RAGPipeline()
        
        # Mock the embedding engine
        pipeline.embedding_engine = MockEmbeddingEngine()
        pipeline._initialized = True
        
        doc = await pipeline.add_document(
            text="This is a test document for the RAG pipeline.",
            metadata={"source": "test"},
            chunk=True
        )
        
        assert doc.text == "This is a test document for the RAG pipeline."
        assert doc.chunk_count > 0
        assert doc.has_embeddings is True
    
    @pytest.mark.asyncio
    async def test_query(self):
        """Test querying the pipeline."""
        pipeline = RAGPipeline()
        
        # Mock the embedding engine
        pipeline.embedding_engine = MockEmbeddingEngine()
        pipeline._initialized = True
        
        # Add a document
        await pipeline.add_document(
            text="Python is a programming language.",
            metadata={"topic": "programming"}
        )
        
        # Query
        results = await pipeline.query("What is Python?")
        
        # Should return results
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_build_context(self):
        """Test building context for LLM."""
        pipeline = RAGPipeline()
        
        # Mock the embedding engine
        pipeline.embedding_engine = MockEmbeddingEngine()
        pipeline._initialized = True
        
        # Add documents
        await pipeline.add_document(
            text="Python is a programming language created by Guido van Rossum."
        )
        await pipeline.add_document(
            text="JavaScript is another popular programming language."
        )
        
        # Build context
        context = await pipeline.build_context("programming languages")
        
        assert isinstance(context, str)
        assert len(context) > 0
    
    def test_get_stats(self):
        """Test getting pipeline stats."""
        pipeline = RAGPipeline()
        
        stats = pipeline.get_stats()
        
        assert "config" in stats
        assert "retriever" in stats
        assert stats["initialized"] is False
    
    def test_clear(self):
        """Test clearing the pipeline."""
        pipeline = RAGPipeline()
        
        # Add a document directly to retriever
        doc = Document(text="Test", chunks=[DocumentChunk(text="Chunk")])
        pipeline.retriever.add_document(doc)
        
        assert len(pipeline.retriever.documents) == 1
        
        pipeline.clear()
        
        assert len(pipeline.retriever.documents) == 0


class TestRetrievalResult:
    """Tests for RetrievalResult."""
    
    def test_to_dict(self):
        """Test converting result to dictionary."""
        chunk = DocumentChunk(
            text="Test chunk",
            start_index=0,
            end_index=10,
            metadata={"source": "test"}
        )
        
        result = RetrievalResult(
            chunk=chunk,
            score=0.95
        )
        
        d = result.to_dict()
        
        assert d["text"] == "Test chunk"
        assert d["score"] == 0.95
        assert d["metadata"]["source"] == "test"
