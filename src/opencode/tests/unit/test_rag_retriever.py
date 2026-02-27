"""
Tests for RAG retriever.
"""

import pytest
import numpy as np
from typing import List, Optional

from opencode.core.rag.retriever import Retriever, RetrievalResult
from opencode.core.rag.config import RAGConfig
from opencode.core.rag.document import Document, DocumentChunk


class TestRetrievalResult:
    """Tests for RetrievalResult."""

    def test_create_retrieval_result(self):
        """Test creating a retrieval result."""
        chunk = DocumentChunk(
            id="chunk-1",
            text="Test chunk content",
            start_index=0,
            end_index=18,
        )
        
        result = RetrievalResult(chunk=chunk, score=0.95)
        
        assert result.chunk == chunk
        assert result.score == 0.95
        assert result.document is None

    def test_create_retrieval_result_with_document(self):
        """Test creating a retrieval result with parent document."""
        chunk = DocumentChunk(
            id="chunk-1",
            text="Test chunk content",
            start_index=0,
            end_index=18,
        )
        doc = Document(id="doc-1", text="Full document", chunks=[chunk])
        
        result = RetrievalResult(chunk=chunk, score=0.95, document=doc)
        
        assert result.document == doc

    def test_to_dict(self):
        """Test converting to dictionary."""
        chunk = DocumentChunk(
            id="chunk-1",
            text="Test chunk content",
            start_index=0,
            end_index=18,
            metadata={"source": "test"},
        )
        
        result = RetrievalResult(chunk=chunk, score=0.95)
        d = result.to_dict()
        
        assert d["text"] == "Test chunk content"
        assert d["score"] == 0.95
        assert d["metadata"] == {"source": "test"}
        assert d["start_index"] == 0
        assert d["end_index"] == 18


class TestRetriever:
    """Tests for Retriever."""

    @pytest.fixture
    def config(self):
        """Create a RAG config."""
        return RAGConfig(
            top_k=5,
            min_similarity=0.5,
        )

    @pytest.fixture
    def retriever(self, config):
        """Create a retriever instance."""
        return Retriever(config)

    def test_create_retriever(self, config):
        """Test creating a retriever."""
        retriever = Retriever(config)
        
        assert retriever.config == config
        assert retriever.documents == []
        assert retriever.chunks == []
        assert retriever.embeddings is None

    def test_add_document(self, retriever):
        """Test adding a document."""
        chunk = DocumentChunk(
            id="chunk-1",
            text="Test content",
            start_index=0,
            end_index=12,
            embedding=[0.1, 0.2, 0.3],
        )
        doc = Document(id="doc-1", text="Test content", chunks=[chunk])
        
        retriever.add_document(doc)
        
        assert len(retriever.documents) == 1
        assert len(retriever.chunks) == 1
        assert retriever.embeddings is not None
        assert retriever.embeddings.shape == (1, 3)

    def test_add_document_multiple_chunks(self, retriever):
        """Test adding a document with multiple chunks."""
        chunks = [
            DocumentChunk(
                id=f"chunk-{i}",
                text=f"Content {i}",
                start_index=i * 10,
                end_index=(i + 1) * 10,
                embedding=[0.1 * i, 0.2 * i, 0.3 * i],
            )
            for i in range(3)
        ]
        doc = Document(id="doc-1", text="Full content", chunks=chunks)
        
        retriever.add_document(doc)
        
        assert len(retriever.documents) == 1
        assert len(retriever.chunks) == 3
        assert retriever.embeddings.shape == (3, 3)

    def test_add_multiple_documents(self, retriever):
        """Test adding multiple documents."""
        for i in range(3):
            chunk = DocumentChunk(
                id=f"chunk-{i}",
                text=f"Content {i}",
                start_index=0,
                end_index=10,
                embedding=[0.1, 0.2, 0.3],
            )
            doc = Document(id=f"doc-{i}", text=f"Content {i}", chunks=[chunk])
            retriever.add_document(doc)
        
        assert len(retriever.documents) == 3
        assert len(retriever.chunks) == 3
        assert retriever.embeddings.shape == (3, 3)

    def test_add_document_without_embeddings(self, retriever):
        """Test adding a document without embeddings."""
        chunk = DocumentChunk(
            id="chunk-1",
            text="Test content",
            start_index=0,
            end_index=12,
        )
        doc = Document(id="doc-1", text="Test content", chunks=[chunk])
        
        retriever.add_document(doc)
        
        assert len(retriever.documents) == 1
        assert len(retriever.chunks) == 1
        assert retriever.embeddings is None

    def test_remove_document(self, retriever):
        """Test removing a document."""
        chunk = DocumentChunk(
            id="chunk-1",
            text="Test content",
            start_index=0,
            end_index=12,
            embedding=[0.1, 0.2, 0.3],
        )
        doc = Document(id="doc-1", text="Test content", chunks=[chunk])
        retriever.add_document(doc)
        
        retriever.remove_document("doc-1")
        
        assert len(retriever.documents) == 0
        assert len(retriever.chunks) == 0
        assert retriever.embeddings is None

    def test_remove_nonexistent_document(self, retriever):
        """Test removing a non-existent document."""
        chunk = DocumentChunk(
            id="chunk-1",
            text="Test content",
            start_index=0,
            end_index=12,
            embedding=[0.1, 0.2, 0.3],
        )
        doc = Document(id="doc-1", text="Test content", chunks=[chunk])
        retriever.add_document(doc)
        
        retriever.remove_document("nonexistent")
        
        assert len(retriever.documents) == 1
        assert len(retriever.chunks) == 1

    def test_remove_document_rebuilds_embeddings(self, retriever):
        """Test that removing a document rebuilds embeddings."""
        chunks1 = [
            DocumentChunk(
                id="chunk-1",
                text="Content 1",
                start_index=0,
                end_index=10,
                embedding=[0.1, 0.2, 0.3],
            )
        ]
        chunks2 = [
            DocumentChunk(
                id="chunk-2",
                text="Content 2",
                start_index=0,
                end_index=10,
                embedding=[0.4, 0.5, 0.6],
            )
        ]
        doc1 = Document(id="doc-1", text="Content 1", chunks=chunks1)
        doc2 = Document(id="doc-2", text="Content 2", chunks=chunks2)
        
        retriever.add_document(doc1)
        retriever.add_document(doc2)
        
        assert retriever.embeddings.shape == (2, 3)
        
        retriever.remove_document("doc-1")
        
        assert retriever.embeddings.shape == (1, 3)

    @pytest.mark.asyncio
    async def test_retrieve(self, retriever):
        """Test retrieving documents."""
        # Create documents with different embeddings
        chunk1 = DocumentChunk(
            id="chunk-1",
            text="Similar content",
            start_index=0,
            end_index=15,
            embedding=[1.0, 0.0, 0.0],
        )
        chunk2 = DocumentChunk(
            id="chunk-2",
            text="Different content",
            start_index=0,
            end_index=17,
            embedding=[0.0, 1.0, 0.0],
        )
        doc = Document(id="doc-1", text="Full content", chunks=[chunk1, chunk2])
        retriever.add_document(doc)
        
        # Query similar to chunk1
        results = await retriever.retrieve(query_embedding=[1.0, 0.0, 0.0])
        
        assert len(results) >= 1
        assert results[0].chunk.id == "chunk-1"
        assert results[0].score > 0.9

    @pytest.mark.asyncio
    async def test_retrieve_top_k(self, retriever):
        """Test retrieving with top_k limit."""
        chunks = [
            DocumentChunk(
                id=f"chunk-{i}",
                text=f"Content {i}",
                start_index=0,
                end_index=10,
                embedding=[0.1 * i, 0.2 * i, 0.3 * i],
            )
            for i in range(10)
        ]
        doc = Document(id="doc-1", text="Full content", chunks=chunks)
        retriever.add_document(doc)
        
        results = await retriever.retrieve(
            query_embedding=[0.5, 0.5, 0.5],
            top_k=3,
        )
        
        assert len(results) <= 3

    @pytest.mark.asyncio
    async def test_retrieve_min_similarity(self, retriever):
        """Test retrieving with minimum similarity threshold."""
        chunk1 = DocumentChunk(
            id="chunk-1",
            text="Similar content",
            start_index=0,
            end_index=15,
            embedding=[1.0, 0.0, 0.0],
        )
        chunk2 = DocumentChunk(
            id="chunk-2",
            text="Different content",
            start_index=0,
            end_index=17,
            embedding=[0.0, 0.0, 1.0],
        )
        doc = Document(id="doc-1", text="Full content", chunks=[chunk1, chunk2])
        retriever.add_document(doc)
        
        # Query similar to chunk1, high threshold
        results = await retriever.retrieve(
            query_embedding=[1.0, 0.0, 0.0],
            min_similarity=0.99,
        )
        
        # Only chunk1 should match
        for result in results:
            assert result.score >= 0.99

    @pytest.mark.asyncio
    async def test_retrieve_empty_index(self, retriever):
        """Test retrieving from empty index."""
        results = await retriever.retrieve(query_embedding=[0.1, 0.2, 0.3])
        
        assert results == []

    @pytest.mark.asyncio
    async def test_retrieve_no_embeddings(self, retriever):
        """Test retrieving when documents have no embeddings."""
        chunk = DocumentChunk(
            id="chunk-1",
            text="Test content",
            start_index=0,
            end_index=12,
        )
        doc = Document(id="doc-1", text="Test content", chunks=[chunk])
        retriever.add_document(doc)
        
        results = await retriever.retrieve(query_embedding=[0.1, 0.2, 0.3])
        
        assert results == []

    @pytest.mark.asyncio
    async def test_retrieve_finds_parent_document(self, retriever):
        """Test that retrieval finds parent document."""
        chunk = DocumentChunk(
            id="chunk-1",
            text="Test content",
            start_index=0,
            end_index=12,
            embedding=[1.0, 0.0, 0.0],
        )
        doc = Document(id="doc-1", text="Full content", metadata={"author": "test"}, chunks=[chunk])
        retriever.add_document(doc)
        
        results = await retriever.retrieve(query_embedding=[1.0, 0.0, 0.0])
        
        assert len(results) == 1
        assert results[0].document is not None
        assert results[0].document.id == "doc-1"

    def test_get_stats(self, retriever):
        """Test getting retriever statistics."""
        chunk = DocumentChunk(
            id="chunk-1",
            text="Test content",
            start_index=0,
            end_index=12,
            embedding=[0.1, 0.2, 0.3],
        )
        doc = Document(id="doc-1", text="Test content", chunks=[chunk])
        retriever.add_document(doc)
        
        stats = retriever.get_stats()
        
        assert stats["document_count"] == 1
        assert stats["chunk_count"] == 1
        assert stats["embedding_dimensions"] == 3
        assert stats["has_embeddings"] is True

    def test_get_stats_empty(self, retriever):
        """Test getting stats from empty retriever."""
        stats = retriever.get_stats()
        
        assert stats["document_count"] == 0
        assert stats["chunk_count"] == 0
        assert stats["embedding_dimensions"] == 0
        assert stats["has_embeddings"] is False

    def test_clear(self, retriever):
        """Test clearing the retriever."""
        chunk = DocumentChunk(
            id="chunk-1",
            text="Test content",
            start_index=0,
            end_index=12,
            embedding=[0.1, 0.2, 0.3],
        )
        doc = Document(id="doc-1", text="Test content", chunks=[chunk])
        retriever.add_document(doc)
        
        retriever.clear()
        
        assert retriever.documents == []
        assert retriever.chunks == []
        assert retriever.embeddings is None


class TestRetrieverWithMixedEmbeddings:
    """Tests for retriever with mixed embedding scenarios."""

    @pytest.fixture
    def config(self):
        """Create a RAG config."""
        return RAGConfig(top_k=5, min_similarity=0.0)

    @pytest.fixture
    def retriever(self, config):
        """Create a retriever instance."""
        return Retriever(config)

    def test_add_mixed_embeddings(self, retriever):
        """Test adding documents with and without embeddings."""
        chunk1 = DocumentChunk(
            id="chunk-1",
            text="With embedding",
            start_index=0,
            end_index=14,
            embedding=[0.1, 0.2, 0.3],
        )
        chunk2 = DocumentChunk(
            id="chunk-2",
            text="Without embedding",
            start_index=0,
            end_index=17,
        )
        
        doc1 = Document(id="doc-1", text="Content 1", chunks=[chunk1])
        doc2 = Document(id="doc-2", text="Content 2", chunks=[chunk2])
        
        retriever.add_document(doc1)
        retriever.add_document(doc2)
        
        assert len(retriever.chunks) == 2
        assert retriever.embeddings is not None
        assert retriever.embeddings.shape[0] == 1  # Only one with embedding

    @pytest.mark.asyncio
    async def test_retrieve_normalizes_vectors(self, retriever):
        """Test that retrieval normalizes vectors properly."""
        # Create chunk with non-normalized embedding
        chunk = DocumentChunk(
            id="chunk-1",
            text="Test content",
            start_index=0,
            end_index=12,
            embedding=[10.0, 10.0, 10.0],  # Non-normalized
        )
        doc = Document(id="doc-1", text="Test content", chunks=[chunk])
        retriever.add_document(doc)
        
        # Query with different magnitude but same direction
        results = await retriever.retrieve(query_embedding=[1.0, 1.0, 1.0])
        
        # Should still match with high similarity
        assert len(results) == 1
        assert results[0].score > 0.99  # Should be ~1.0 after normalization

    @pytest.mark.asyncio
    async def test_retrieve_zero_query(self, retriever):
        """Test retrieval with zero query vector."""
        chunk = DocumentChunk(
            id="chunk-1",
            text="Test content",
            start_index=0,
            end_index=12,
            embedding=[0.1, 0.2, 0.3],
        )
        doc = Document(id="doc-1", text="Test content", chunks=[chunk])
        retriever.add_document(doc)
        
        # Zero query should not crash
        results = await retriever.retrieve(query_embedding=[0.0, 0.0, 0.0])
        
        # Results may be empty or have low scores
        assert isinstance(results, list)


class TestRetrieverEdgeCases:
    """Tests for edge cases in retriever."""

    @pytest.fixture
    def config(self):
        """Create a RAG config."""
        return RAGConfig(top_k=5, min_similarity=0.0)

    @pytest.fixture
    def retriever(self, config):
        """Create a retriever instance."""
        return Retriever(config)

    @pytest.mark.asyncio
    async def test_retrieve_single_dimension(self, retriever):
        """Test retrieval with single dimension embeddings."""
        chunk = DocumentChunk(
            id="chunk-1",
            text="Test",
            start_index=0,
            end_index=4,
            embedding=[1.0],
        )
        doc = Document(id="doc-1", text="Test", chunks=[chunk])
        retriever.add_document(doc)
        
        results = await retriever.retrieve(query_embedding=[1.0])
        
        assert len(results) == 1
        assert results[0].score == pytest.approx(1.0, abs=0.01)

    def test_add_document_empty_chunks(self, retriever):
        """Test adding document with no chunks."""
        doc = Document(id="doc-1", text="Content", chunks=[])
        
        retriever.add_document(doc)
        
        assert len(retriever.documents) == 1
        assert len(retriever.chunks) == 0
        assert retriever.embeddings is None

    @pytest.mark.asyncio
    async def test_retrieve_large_top_k(self, retriever):
        """Test retrieval with top_k larger than available chunks."""
        chunk = DocumentChunk(
            id="chunk-1",
            text="Test",
            start_index=0,
            end_index=4,
            embedding=[0.1, 0.2, 0.3],
        )
        doc = Document(id="doc-1", text="Test", chunks=[chunk])
        retriever.add_document(doc)
        
        results = await retriever.retrieve(query_embedding=[0.1, 0.2, 0.3], top_k=100)
        
        assert len(results) == 1

    def test_remove_document_empty_chunks(self, retriever):
        """Test removing document with empty chunks list."""
        doc = Document(id="doc-1", text="Content", chunks=[])
        retriever.add_document(doc)
        
        retriever.remove_document("doc-1")
        
        assert len(retriever.documents) == 0
