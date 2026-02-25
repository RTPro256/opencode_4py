"""
Tests for Local Vector Store.

Tests vector store backends and local vector store functionality.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import tempfile
import numpy as np

from opencode.core.rag.local_vector_store import (
    SearchResult,
    VectorStoreBackend,
    MemoryVectorStore,
    FileVectorStore,
    ChromaVectorStore,
    LocalVectorStore,
)


class TestSearchResult:
    """Tests for SearchResult model."""

    def test_init_required_fields(self):
        """Test initialization with required fields."""
        result = SearchResult(
            id="test-id",
            text="test text",
            score=0.95,
        )
        assert result.id == "test-id"
        assert result.text == "test text"
        assert result.score == 0.95
        assert result.metadata == {}

    def test_init_with_metadata(self):
        """Test initialization with metadata."""
        result = SearchResult(
            id="test-id",
            text="test text",
            score=0.95,
            metadata={"source": "test.py", "line": 10},
        )
        assert result.metadata == {"source": "test.py", "line": 10}

    def test_to_dict(self):
        """Test to_dict conversion."""
        result = SearchResult(
            id="test-id",
            text="test text",
            score=0.95,
            metadata={"source": "test"},
        )
        d = result.to_dict()
        assert d["id"] == "test-id"
        assert d["text"] == "test text"
        assert d["score"] == 0.95
        assert d["metadata"] == {"source": "test"}


class TestMemoryVectorStore:
    """Tests for MemoryVectorStore class."""

    def test_init(self):
        """Test initialization."""
        store = MemoryVectorStore(dimensions=512)
        assert store.dimensions == 512
        assert store.ids == []
        assert store.texts == []
        assert store.metadata == []
        assert store.embeddings is None

    @pytest.mark.asyncio
    async def test_add_single(self):
        """Test adding a single document."""
        store = MemoryVectorStore()
        
        await store.add(
            ids=["doc-1"],
            embeddings=[[0.1, 0.2, 0.3]],
            texts=["Test document"],
            metadata=[{"source": "test"}],
        )
        
        assert len(store.ids) == 1
        assert store.ids[0] == "doc-1"
        assert store.texts[0] == "Test document"
        assert store.metadata[0] == {"source": "test"}
        assert store.embeddings is not None
        assert store.embeddings.shape == (1, 3)

    @pytest.mark.asyncio
    async def test_add_multiple(self):
        """Test adding multiple documents."""
        store = MemoryVectorStore()
        
        await store.add(
            ids=["doc-1", "doc-2"],
            embeddings=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
            texts=["Doc 1", "Doc 2"],
            metadata=[{}, {}],
        )
        
        assert len(store.ids) == 2
        assert store.embeddings.shape == (2, 3)

    @pytest.mark.asyncio
    async def test_add_appends(self):
        """Test that add appends to existing data."""
        store = MemoryVectorStore()
        
        await store.add(
            ids=["doc-1"],
            embeddings=[[0.1, 0.2, 0.3]],
            texts=["Doc 1"],
            metadata=[{}],
        )
        
        await store.add(
            ids=["doc-2"],
            embeddings=[[0.4, 0.5, 0.6]],
            texts=["Doc 2"],
            metadata=[{}],
        )
        
        assert len(store.ids) == 2
        assert store.embeddings.shape == (2, 3)

    @pytest.mark.asyncio
    async def test_search_empty(self):
        """Test search on empty store."""
        store = MemoryVectorStore()
        
        results = await store.search([0.1, 0.2, 0.3])
        
        assert results == []

    @pytest.mark.asyncio
    async def test_search_with_results(self):
        """Test search with results."""
        store = MemoryVectorStore()
        
        # Add documents with different embeddings
        await store.add(
            ids=["doc-1", "doc-2"],
            embeddings=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
            texts=["Document 1", "Document 2"],
            metadata=[{"type": "a"}, {"type": "b"}],
        )
        
        # Search with query similar to first document
        results = await store.search([0.9, 0.1, 0.0], top_k=2)
        
        assert len(results) == 2
        # First result should be doc-1 (more similar)
        assert results[0].id == "doc-1"

    @pytest.mark.asyncio
    async def test_search_with_filter(self):
        """Test search with metadata filter."""
        store = MemoryVectorStore()
        
        await store.add(
            ids=["doc-1", "doc-2"],
            embeddings=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
            texts=["Doc 1", "Doc 2"],
            metadata=[{"type": "a"}, {"type": "b"}],
        )
        
        results = await store.search(
            [0.5, 0.5, 0.0],
            top_k=5,
            filter={"type": "a"},
        )
        
        assert len(results) == 1
        assert results[0].id == "doc-1"

    @pytest.mark.asyncio
    async def test_search_filter_no_match(self):
        """Test search with filter that matches nothing."""
        store = MemoryVectorStore()
        
        await store.add(
            ids=["doc-1"],
            embeddings=[[1.0, 0.0, 0.0]],
            texts=["Doc 1"],
            metadata=[{"type": "a"}],
        )
        
        results = await store.search(
            [1.0, 0.0, 0.0],
            filter={"type": "nonexistent"},
        )
        
        assert results == []

    @pytest.mark.asyncio
    async def test_delete(self):
        """Test deleting documents."""
        store = MemoryVectorStore()
        
        await store.add(
            ids=["doc-1", "doc-2", "doc-3"],
            embeddings=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]],
            texts=["Doc 1", "Doc 2", "Doc 3"],
            metadata=[{}, {}, {}],
        )
        
        await store.delete(["doc-2"])
        
        assert len(store.ids) == 2
        assert "doc-2" not in store.ids
        assert store.embeddings.shape == (2, 3)

    @pytest.mark.asyncio
    async def test_count(self):
        """Test counting documents."""
        store = MemoryVectorStore()
        
        assert await store.count() == 0
        
        await store.add(
            ids=["doc-1", "doc-2"],
            embeddings=[[0.1, 0.2], [0.3, 0.4]],
            texts=["Doc 1", "Doc 2"],
            metadata=[{}, {}],
        )
        
        assert await store.count() == 2

    @pytest.mark.asyncio
    async def test_clear(self):
        """Test clearing the store."""
        store = MemoryVectorStore()
        
        await store.add(
            ids=["doc-1"],
            embeddings=[[0.1, 0.2, 0.3]],
            texts=["Doc 1"],
            metadata=[{}],
        )
        
        await store.clear()
        
        assert store.ids == []
        assert store.texts == []
        assert store.metadata == []
        assert store.embeddings is None


class TestFileVectorStore:
    """Tests for FileVectorStore class."""

    def test_init_creates_directory(self):
        """Test that initialization creates directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = Path(tmpdir) / "vector_store"
            store = FileVectorStore(store_path)
            
            assert store_path.exists()

    def test_init_loads_existing_data(self):
        """Test that initialization loads existing data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = Path(tmpdir) / "vector_store"
            
            # Create store and add data
            store1 = FileVectorStore(store_path)
            import asyncio
            asyncio.run(store1.add(
                ids=["doc-1"],
                embeddings=[[0.1, 0.2, 0.3]],
                texts=["Doc 1"],
                metadata=[{"source": "test"}],
            ))
            
            # Create new store instance - should load existing data
            store2 = FileVectorStore(store_path)
            
            assert len(store2.ids) == 1
            assert store2.ids[0] == "doc-1"

    @pytest.mark.asyncio
    async def test_add_persists(self):
        """Test that add persists data to disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = Path(tmpdir) / "vector_store"
            store = FileVectorStore(store_path)
            
            await store.add(
                ids=["doc-1"],
                embeddings=[[0.1, 0.2, 0.3]],
                texts=["Doc 1"],
                metadata=[{}],
            )
            
            # Check files exist
            assert (store_path / "data.json").exists()
            assert (store_path / "embeddings.npy").exists()

    @pytest.mark.asyncio
    async def test_search(self):
        """Test search functionality."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileVectorStore(Path(tmpdir) / "store")
            
            await store.add(
                ids=["doc-1", "doc-2"],
                embeddings=[[1.0, 0.0], [0.0, 1.0]],
                texts=["Doc 1", "Doc 2"],
                metadata=[{}, {}],
            )
            
            results = await store.search([0.9, 0.1], top_k=2)
            
            assert len(results) == 2

    @pytest.mark.asyncio
    async def test_delete_persists(self):
        """Test that delete persists to disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = Path(tmpdir) / "store"
            store = FileVectorStore(store_path)
            
            await store.add(
                ids=["doc-1", "doc-2"],
                embeddings=[[0.1, 0.2], [0.3, 0.4]],
                texts=["Doc 1", "Doc 2"],
                metadata=[{}, {}],
            )
            
            await store.delete(["doc-1"])
            
            # Create new instance to verify persistence
            store2 = FileVectorStore(store_path)
            assert len(store2.ids) == 1
            assert store2.ids[0] == "doc-2"

    @pytest.mark.asyncio
    async def test_clear_persists(self):
        """Test that clear persists to disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = Path(tmpdir) / "store"
            store = FileVectorStore(store_path)
            
            await store.add(
                ids=["doc-1"],
                embeddings=[[0.1, 0.2]],
                texts=["Doc 1"],
                metadata=[{}],
            )
            
            await store.clear()
            
            store2 = FileVectorStore(store_path)
            assert len(store2.ids) == 0

    @pytest.mark.asyncio
    async def test_count(self):
        """Test counting documents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileVectorStore(Path(tmpdir) / "store")
            
            await store.add(
                ids=["doc-1", "doc-2"],
                embeddings=[[0.1, 0.2], [0.3, 0.4]],
                texts=["Doc 1", "Doc 2"],
                metadata=[{}, {}],
            )
            
            assert await store.count() == 2


class TestChromaVectorStore:
    """Tests for ChromaVectorStore class."""

    def test_init(self):
        """Test initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ChromaVectorStore(Path(tmpdir) / "chroma")
            assert store.path == Path(tmpdir) / "chroma"
            assert store.collection_name == "opencode_rag"
            assert store._client is None
            assert store._collection is None

    @pytest.mark.asyncio
    async def test_search_returns_empty_when_no_data(self):
        """Test search returns empty when no data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ChromaVectorStore(Path(tmpdir) / "chroma")
            
            # Mock chromadb
            mock_collection = MagicMock()
            mock_collection.query.return_value = {
                "ids": [[]],
                "documents": [[]],
                "distances": [[]],
                "metadatas": [[]],
            }
            
            with patch.object(store, '_get_collection', return_value=mock_collection):
                results = await store.search([0.1, 0.2, 0.3])
                
                assert results == []


class TestLocalVectorStore:
    """Tests for LocalVectorStore class."""

    def test_init_defaults(self):
        """Test initialization with default values."""
        store = LocalVectorStore()
        assert store.engine == "file"
        assert store.dimensions == 768
        assert store._backend is None

    def test_init_custom(self):
        """Test initialization with custom values."""
        store = LocalVectorStore(
            path="/custom/path",
            engine="memory",
            dimensions=512,
        )
        assert store.engine == "memory"
        assert store.dimensions == 512

    def test_get_backend_memory(self):
        """Test getting memory backend."""
        store = LocalVectorStore(engine="memory")
        backend = store._get_backend()
        
        assert isinstance(backend, MemoryVectorStore)

    def test_get_backend_file(self):
        """Test getting file backend."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = LocalVectorStore(path=tmpdir, engine="file")
            backend = store._get_backend()
            
            assert isinstance(backend, FileVectorStore)

    def test_get_backend_chroma(self):
        """Test getting chroma backend."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = LocalVectorStore(path=tmpdir, engine="chroma")
            
            # Mock chromadb import
            with patch.dict('sys.modules', {'chromadb': MagicMock()}):
                backend = store._get_backend()
                
                assert isinstance(backend, ChromaVectorStore)

    @pytest.mark.asyncio
    async def test_add(self):
        """Test adding documents."""
        store = LocalVectorStore(engine="memory")
        
        await store.add(
            ids=["doc-1"],
            embeddings=[[0.1, 0.2, 0.3]],
            texts=["Doc 1"],
            metadata=[{"source": "test"}],
        )
        
        backend = store._get_backend()
        assert len(backend.ids) == 1

    @pytest.mark.asyncio
    async def test_add_no_metadata(self):
        """Test adding documents without metadata."""
        store = LocalVectorStore(engine="memory")
        
        await store.add(
            ids=["doc-1"],
            embeddings=[[0.1, 0.2, 0.3]],
            texts=["Doc 1"],
        )
        
        backend = store._get_backend()
        assert backend.metadata[0] == {}

    @pytest.mark.asyncio
    async def test_search(self):
        """Test searching documents."""
        store = LocalVectorStore(engine="memory")
        
        await store.add(
            ids=["doc-1"],
            embeddings=[[1.0, 0.0, 0.0]],
            texts=["Doc 1"],
        )
        
        results = await store.search([0.9, 0.1, 0.0])
        
        assert len(results) == 1
        assert results[0].id == "doc-1"

    @pytest.mark.asyncio
    async def test_delete(self):
        """Test deleting documents."""
        store = LocalVectorStore(engine="memory")
        
        await store.add(
            ids=["doc-1", "doc-2"],
            embeddings=[[0.1, 0.2], [0.3, 0.4]],
            texts=["Doc 1", "Doc 2"],
        )
        
        await store.delete(["doc-1"])
        
        assert await store.count() == 1

    @pytest.mark.asyncio
    async def test_count(self):
        """Test counting documents."""
        store = LocalVectorStore(engine="memory")
        
        await store.add(
            ids=["doc-1", "doc-2"],
            embeddings=[[0.1, 0.2], [0.3, 0.4]],
            texts=["Doc 1", "Doc 2"],
        )
        
        assert await store.count() == 2

    @pytest.mark.asyncio
    async def test_clear(self):
        """Test clearing documents."""
        store = LocalVectorStore(engine="memory")
        
        await store.add(
            ids=["doc-1"],
            embeddings=[[0.1, 0.2]],
            texts=["Doc 1"],
        )
        
        await store.clear()
        
        assert await store.count() == 0

    def test_get_stats(self):
        """Test getting statistics."""
        store = LocalVectorStore(
            path="/test/path",
            engine="memory",
            dimensions=512,
        )
        
        stats = store.get_stats()
        
        assert stats["engine"] == "memory"
        assert "test" in stats["path"]  # Path format varies by OS
        assert stats["dimensions"] == 512
