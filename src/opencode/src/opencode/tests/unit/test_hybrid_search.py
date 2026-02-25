"""
Tests for Hybrid Search.

Tests BM25 indexing and hybrid search combining semantic and keyword search.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from typing import List

from opencode.core.rag.hybrid_search import (
    HybridSearchResult,
    BM25Index,
    HybridSearch,
)
from opencode.core.rag.local_vector_store import SearchResult


class TestHybridSearchResult:
    """Tests for HybridSearchResult model."""

    def test_init_defaults(self):
        """Test initialization with default values."""
        result = HybridSearchResult(
            id="test-id",
            text="test text",
            score=0.5,
        )
        assert result.id == "test-id"
        assert result.text == "test text"
        assert result.score == 0.5
        assert result.semantic_score == 0.0
        assert result.keyword_score == 0.0
        assert result.combined_score == 0.0

    def test_init_with_all_scores(self):
        """Test initialization with all scores."""
        result = HybridSearchResult(
            id="test-id",
            text="test text",
            score=0.8,
            metadata={"source": "test"},
            semantic_score=0.7,
            keyword_score=0.3,
            combined_score=0.5,
        )
        assert result.semantic_score == 0.7
        assert result.keyword_score == 0.3
        assert result.combined_score == 0.5
        assert result.metadata == {"source": "test"}


class TestBM25Index:
    """Tests for BM25Index class."""

    def test_init_defaults(self):
        """Test initialization with default parameters."""
        index = BM25Index()
        assert index.k1 == 1.5
        assert index.b == 0.75
        assert index.doc_ids == []
        assert index.doc_texts == []
        assert index.doc_metadata == []
        assert index.doc_lengths == []
        assert index.avg_doc_length == 0.0
        assert index.total_docs == 0

    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        index = BM25Index(k1=2.0, b=0.5)
        assert index.k1 == 2.0
        assert index.b == 0.5

    def test_tokenize(self):
        """Test tokenization."""
        index = BM25Index()
        
        tokens = index._tokenize("Hello World Test")
        assert tokens == ["hello", "world", "test"]
        
        # Underscore is a word character, so "with_special" stays together
        tokens = index._tokenize("Test-with_special.chars!")
        assert "test" in tokens
        assert "with_special" in tokens  # underscore connects words
        assert "chars" in tokens

    def test_tokenize_empty(self):
        """Test tokenization of empty string."""
        index = BM25Index()
        tokens = index._tokenize("")
        assert tokens == []

    def test_add_documents_single(self):
        """Test adding a single document."""
        index = BM25Index()
        
        index.add_documents(
            ids=["doc-1"],
            texts=["Hello world"],
            metadata=[{"source": "test"}],
        )
        
        assert len(index.doc_ids) == 1
        assert index.doc_ids[0] == "doc-1"
        assert index.doc_texts[0] == "Hello world"
        assert index.doc_metadata[0] == {"source": "test"}
        assert index.total_docs == 1
        assert index.avg_doc_length == 2.0

    def test_add_documents_multiple(self):
        """Test adding multiple documents."""
        index = BM25Index()
        
        index.add_documents(
            ids=["doc-1", "doc-2", "doc-3"],
            texts=["Hello world", "Test document", "Another text"],
        )
        
        assert len(index.doc_ids) == 3
        assert index.total_docs == 3
        assert index.avg_doc_length == 2.0  # (2 + 2 + 2) / 3

    def test_add_documents_no_metadata(self):
        """Test adding documents without metadata."""
        index = BM25Index()
        
        index.add_documents(
            ids=["doc-1"],
            texts=["Test"],
        )
        
        assert index.doc_metadata[0] == {}

    def test_add_documents_updates_term_freq(self):
        """Test that adding documents updates term frequencies."""
        index = BM25Index()
        
        index.add_documents(
            ids=["doc-1", "doc-2"],
            texts=["hello world", "hello test"],
        )
        
        # "hello" appears in 2 documents
        assert index.term_doc_freq["hello"] == 2
        # "world" appears in 1 document
        assert index.term_doc_freq["world"] == 1

    def test_search_empty_index(self):
        """Test search on empty index."""
        index = BM25Index()
        
        results = index.search("test query")
        
        assert results == []

    def test_search_no_match(self):
        """Test search with no matching terms."""
        index = BM25Index()
        index.add_documents(
            ids=["doc-1"],
            texts=["Hello world"],
        )
        
        results = index.search("xyz abc")
        
        # No matching terms, so no results
        assert results == []

    def test_search_with_match(self):
        """Test search with matching terms."""
        index = BM25Index()
        index.add_documents(
            ids=["doc-1"],
            texts=["Hello world this is a test"],
            metadata=[{"source": "test"}],
        )
        
        results = index.search("hello test")
        
        assert len(results) == 1
        assert results[0].id == "doc-1"
        assert results[0].score > 0
        assert results[0].metadata == {"source": "test"}

    def test_search_top_k(self):
        """Test search with top_k limit."""
        index = BM25Index()
        index.add_documents(
            ids=["doc-1", "doc-2", "doc-3"],
            texts=["hello world", "hello hello hello", "test test test"],
        )
        
        results = index.search("hello", top_k=2)
        
        assert len(results) == 2

    def test_search_ranking(self):
        """Test that search results are ranked by score."""
        index = BM25Index()
        index.add_documents(
            ids=["doc-1", "doc-2"],
            texts=["hello", "hello hello hello hello hello"],
        )
        
        results = index.search("hello", top_k=2)
        
        # doc-2 has more occurrences, should rank higher
        assert results[0].id == "doc-2"
        assert results[0].score > results[1].score

    def test_bm25_score(self):
        """Test BM25 score calculation."""
        index = BM25Index()
        index.add_documents(
            ids=["doc-1"],
            texts=["hello world hello"],
        )
        
        score = index._bm25_score(0, ["hello"])
        
        assert score > 0

    def test_bm25_score_no_match(self):
        """Test BM25 score with no matching terms."""
        index = BM25Index()
        index.add_documents(
            ids=["doc-1"],
            texts=["hello world"],
        )
        
        score = index._bm25_score(0, ["xyz"])
        
        assert score == 0.0

    def test_clear(self):
        """Test clearing the index."""
        index = BM25Index()
        index.add_documents(
            ids=["doc-1"],
            texts=["Hello world"],
        )
        
        index.clear()
        
        assert index.doc_ids == []
        assert index.doc_texts == []
        assert index.doc_metadata == []
        assert index.doc_lengths == []
        assert index.total_docs == 0
        assert index.avg_doc_length == 0.0

    def test_get_stats(self):
        """Test getting index statistics."""
        index = BM25Index()
        index.add_documents(
            ids=["doc-1", "doc-2"],
            texts=["Hello world", "Test document"],
        )
        
        stats = index.get_stats()
        
        assert stats["total_docs"] == 2
        assert stats["avg_doc_length"] == 2.0
        assert stats["vocabulary_size"] == 4  # hello, world, test, document


class TestHybridSearch:
    """Tests for HybridSearch class."""

    def test_init_defaults(self):
        """Test initialization with default values."""
        hybrid = HybridSearch()
        assert hybrid.vector_store is None
        assert hybrid.semantic_weight == 0.7
        assert hybrid.keyword_weight == 0.3
        assert isinstance(hybrid.keyword_index, BM25Index)

    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        mock_store = MagicMock()
        
        hybrid = HybridSearch(
            vector_store=mock_store,
            semantic_weight=0.5,
            keyword_weight=0.5,
        )
        assert hybrid.vector_store == mock_store
        assert hybrid.semantic_weight == 0.5
        assert hybrid.keyword_weight == 0.5

    @pytest.mark.asyncio
    async def test_index_documents_no_vector_store(self):
        """Test indexing documents without vector store."""
        hybrid = HybridSearch()
        
        await hybrid.index_documents(
            ids=["doc-1"],
            texts=["Hello world"],
            embeddings=[[0.1, 0.2, 0.3]],
        )
        
        assert len(hybrid.keyword_index.doc_ids) == 1

    @pytest.mark.asyncio
    async def test_index_documents_with_vector_store(self):
        """Test indexing documents with vector store."""
        mock_store = MagicMock()
        mock_store.add = AsyncMock()
        
        hybrid = HybridSearch(vector_store=mock_store)
        
        await hybrid.index_documents(
            ids=["doc-1"],
            texts=["Hello world"],
            embeddings=[[0.1, 0.2, 0.3]],
            metadata=[{"source": "test"}],
        )
        
        mock_store.add.assert_called_once_with(
            ids=["doc-1"],
            embeddings=[[0.1, 0.2, 0.3]],
            texts=["Hello world"],
            metadata=[{"source": "test"}],
        )
        assert len(hybrid.keyword_index.doc_ids) == 1

    @pytest.mark.asyncio
    async def test_search_no_vector_store(self):
        """Test search without vector store."""
        hybrid = HybridSearch()
        hybrid.keyword_index.add_documents(
            ids=["doc-1"],
            texts=["Hello world"],
        )
        
        results = await hybrid.search(
            query="hello",
            query_embedding=[0.1, 0.2, 0.3],
            top_k=5,
        )
        
        # Only keyword results
        assert len(results) == 1
        assert results[0].id == "doc-1"
        assert results[0].keyword_score > 0
        assert results[0].semantic_score == 0.0

    @pytest.mark.asyncio
    async def test_search_with_vector_store(self):
        """Test search with vector store."""
        mock_result = SearchResult(
            id="doc-1",
            text="Hello world",
            score=0.9,
            metadata={},
        )
        
        mock_store = MagicMock()
        mock_store.search = AsyncMock(return_value=[mock_result])
        
        hybrid = HybridSearch(vector_store=mock_store)
        hybrid.keyword_index.add_documents(
            ids=["doc-1"],
            texts=["Hello world"],
        )
        
        results = await hybrid.search(
            query="hello",
            query_embedding=[0.1, 0.2, 0.3],
            top_k=5,
        )
        
        mock_store.search.assert_called_once()
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_with_filter(self):
        """Test search with metadata filter."""
        mock_store = MagicMock()
        mock_store.search = AsyncMock(return_value=[])
        
        hybrid = HybridSearch(vector_store=mock_store)
        
        await hybrid.search(
            query="hello",
            query_embedding=[0.1, 0.2, 0.3],
            top_k=5,
            filter={"source": "test"},
        )
        
        mock_store.search.assert_called_once_with(
            query_embedding=[0.1, 0.2, 0.3],
            top_k=10,  # top_k * 2
            filter={"source": "test"},
        )

    @pytest.mark.asyncio
    async def test_search_merges_results(self):
        """Test that search merges semantic and keyword results."""
        # Semantic result
        sem_result = SearchResult(
            id="doc-1",
            text="Hello world",
            score=0.9,
            metadata={"type": "semantic"},
        )
        
        mock_store = MagicMock()
        mock_store.search = AsyncMock(return_value=[sem_result])
        
        hybrid = HybridSearch(vector_store=mock_store)
        hybrid.keyword_index.add_documents(
            ids=["doc-1", "doc-2"],
            texts=["Hello world", "Another document"],
        )
        
        results = await hybrid.search(
            query="hello",
            query_embedding=[0.1, 0.2, 0.3],
            top_k=5,
        )
        
        # Should have merged results
        assert len(results) >= 1
        # doc-1 should have both scores
        doc1_result = next((r for r in results if r.id == "doc-1"), None)
        assert doc1_result is not None

    def test_normalize_scores_empty(self):
        """Test normalizing empty scores."""
        hybrid = HybridSearch()
        
        normalized = hybrid._normalize_scores([])
        
        assert normalized == []

    def test_normalize_scores_single(self):
        """Test normalizing single score."""
        hybrid = HybridSearch()
        
        normalized = hybrid._normalize_scores([0.5])
        
        assert normalized == [1.0]

    def test_normalize_scores_multiple(self):
        """Test normalizing multiple scores."""
        hybrid = HybridSearch()
        
        normalized = hybrid._normalize_scores([0.0, 0.5, 1.0])
        
        assert normalized == [0.0, 0.5, 1.0]

    def test_normalize_scores_same_values(self):
        """Test normalizing scores with same values."""
        hybrid = HybridSearch()
        
        normalized = hybrid._normalize_scores([0.5, 0.5, 0.5])
        
        assert normalized == [1.0, 1.0, 1.0]

    def test_merge_results_empty(self):
        """Test merging empty results."""
        hybrid = HybridSearch()
        
        merged = hybrid._merge_results([], [], top_k=5)
        
        assert merged == []

    def test_merge_results_semantic_only(self):
        """Test merging with only semantic results."""
        hybrid = HybridSearch()
        
        sem_result = SearchResult(
            id="doc-1",
            text="Test",
            score=0.9,
            metadata={},
        )
        
        merged = hybrid._merge_results([sem_result], [], top_k=5)
        
        assert len(merged) == 1
        assert merged[0].id == "doc-1"
        assert merged[0].semantic_score > 0
        assert merged[0].keyword_score == 0.0

    def test_merge_results_keyword_only(self):
        """Test merging with only keyword results."""
        hybrid = HybridSearch()
        
        kw_result = SearchResult(
            id="doc-1",
            text="Test",
            score=2.5,
            metadata={},
        )
        
        merged = hybrid._merge_results([], [kw_result], top_k=5)
        
        assert len(merged) == 1
        assert merged[0].id == "doc-1"
        assert merged[0].semantic_score == 0.0
        assert merged[0].keyword_score > 0

    def test_merge_results_both(self):
        """Test merging both result types."""
        hybrid = HybridSearch(semantic_weight=0.7, keyword_weight=0.3)
        
        sem_result = SearchResult(
            id="doc-1",
            text="Test document",
            score=0.9,
            metadata={"type": "sem"},
        )
        
        kw_result = SearchResult(
            id="doc-1",
            text="Test document",
            score=2.5,
            metadata={"type": "kw"},
        )
        
        merged = hybrid._merge_results([sem_result], [kw_result], top_k=5)
        
        assert len(merged) == 1
        assert merged[0].semantic_score > 0
        assert merged[0].keyword_score > 0
        # Combined score should be weighted sum
        expected = 0.7 * merged[0].semantic_score + 0.3 * merged[0].keyword_score
        assert abs(merged[0].combined_score - expected) < 0.001

    def test_merge_results_respects_top_k(self):
        """Test that merge respects top_k."""
        hybrid = HybridSearch()
        
        results = [
            SearchResult(id=f"doc-{i}", text=f"Text {i}", score=0.9 - i * 0.1, metadata={})
            for i in range(10)
        ]
        
        merged = hybrid._merge_results(results, [], top_k=3)
        
        assert len(merged) == 3

    @pytest.mark.asyncio
    async def test_delete_documents_no_vector_store(self):
        """Test deleting documents without vector store."""
        hybrid = HybridSearch()
        hybrid.keyword_index.add_documents(
            ids=["doc-1", "doc-2", "doc-3"],
            texts=["One", "Two", "Three"],
        )
        
        await hybrid.delete_documents(["doc-2"])
        
        assert "doc-2" not in hybrid.keyword_index.doc_ids
        assert len(hybrid.keyword_index.doc_ids) == 2

    @pytest.mark.asyncio
    async def test_delete_documents_with_vector_store(self):
        """Test deleting documents with vector store."""
        mock_store = MagicMock()
        mock_store.delete = AsyncMock()
        
        hybrid = HybridSearch(vector_store=mock_store)
        hybrid.keyword_index.add_documents(
            ids=["doc-1", "doc-2"],
            texts=["One", "Two"],
        )
        
        await hybrid.delete_documents(["doc-1"])
        
        mock_store.delete.assert_called_once_with(["doc-1"])
        assert "doc-1" not in hybrid.keyword_index.doc_ids

    @pytest.mark.asyncio
    async def test_clear_no_vector_store(self):
        """Test clearing without vector store."""
        hybrid = HybridSearch()
        hybrid.keyword_index.add_documents(
            ids=["doc-1"],
            texts=["Test"],
        )
        
        await hybrid.clear()
        
        assert hybrid.keyword_index.total_docs == 0

    @pytest.mark.asyncio
    async def test_clear_with_vector_store(self):
        """Test clearing with vector store."""
        mock_store = MagicMock()
        mock_store.clear = AsyncMock()
        
        hybrid = HybridSearch(vector_store=mock_store)
        hybrid.keyword_index.add_documents(
            ids=["doc-1"],
            texts=["Test"],
        )
        
        await hybrid.clear()
        
        mock_store.clear.assert_called_once()
        assert hybrid.keyword_index.total_docs == 0

    def test_get_stats_no_vector_store(self):
        """Test getting stats without vector store."""
        hybrid = HybridSearch()
        hybrid.keyword_index.add_documents(
            ids=["doc-1"],
            texts=["Test"],
        )
        
        stats = hybrid.get_stats()
        
        assert stats["semantic_weight"] == 0.7
        assert stats["keyword_weight"] == 0.3
        assert stats["keyword_index"]["total_docs"] == 1
        assert stats["vector_store"] is None

    def test_get_stats_with_vector_store(self):
        """Test getting stats with vector store."""
        mock_store = MagicMock()
        mock_store.get_stats = MagicMock(return_value={"total_vectors": 5})
        
        hybrid = HybridSearch(vector_store=mock_store)
        
        stats = hybrid.get_stats()
        
        assert stats["vector_store"] == {"total_vectors": 5}
