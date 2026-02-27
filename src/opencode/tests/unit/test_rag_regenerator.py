"""
Tests for RAG Regenerator.

Tests regeneration of RAG index after false content removal.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime
from pathlib import Path

from opencode.core.rag.validation.rag_regenerator import (
    RegenerationResult,
    RAGRegenerator,
)


class TestRegenerationResult:
    """Tests for RegenerationResult model."""

    def test_init_required_fields(self):
        """Test initialization with required fields."""
        result = RegenerationResult(
            success=True,
            source_id="source-1",
        )
        assert result.success is True
        assert result.source_id == "source-1"
        assert result.documents_removed == 0
        assert result.documents_reindexed == 0
        assert result.false_content_removed == 0
        assert isinstance(result.started_at, datetime)
        assert result.completed_at is None
        assert result.duration_seconds == 0.0
        assert result.error is None
        assert result.warnings == []

    def test_init_with_all_fields(self):
        """Test initialization with all fields."""
        start = datetime(2025, 1, 1, 10, 0, 0)
        end = datetime(2025, 1, 1, 10, 0, 5)
        
        result = RegenerationResult(
            success=True,
            source_id="source-1",
            documents_removed=5,
            documents_reindexed=10,
            false_content_removed=3,
            started_at=start,
            completed_at=end,
            duration_seconds=5.0,
            error=None,
            warnings=["Warning 1"],
        )
        assert result.success is True
        assert result.source_id == "source-1"
        assert result.documents_removed == 5
        assert result.documents_reindexed == 10
        assert result.false_content_removed == 3
        assert result.started_at == start
        assert result.completed_at == end
        assert result.duration_seconds == 5.0
        assert result.warnings == ["Warning 1"]

    def test_to_dict(self):
        """Test to_dict conversion."""
        result = RegenerationResult(
            success=True,
            source_id="source-1",
            documents_removed=5,
            documents_reindexed=10,
            false_content_removed=3,
            duration_seconds=2.5,
            error=None,
        )
        
        d = result.to_dict()
        assert d["success"] is True
        assert d["source_id"] == "source-1"
        assert d["documents_removed"] == 5
        assert d["documents_reindexed"] == 10
        assert d["false_content_removed"] == 3
        assert d["duration_seconds"] == 2.5
        assert d["error"] is None

    def test_to_dict_with_error(self):
        """Test to_dict with error."""
        result = RegenerationResult(
            success=False,
            source_id="source-1",
            error="Something went wrong",
        )
        
        d = result.to_dict()
        assert d["success"] is False
        assert d["error"] == "Something went wrong"


class TestRAGRegenerator:
    """Tests for RAGRegenerator class."""

    def test_init_defaults(self):
        """Test initialization with default values."""
        regenerator = RAGRegenerator()
        assert regenerator.vector_store is None
        assert regenerator.embedding_engine is None
        assert regenerator.registry is None
        assert regenerator.source_manager is None

    def test_init_with_components(self):
        """Test initialization with components."""
        mock_vector_store = MagicMock()
        mock_embedding = MagicMock()
        mock_registry = MagicMock()
        mock_source_manager = MagicMock()
        
        regenerator = RAGRegenerator(
            vector_store=mock_vector_store,
            embedding_engine=mock_embedding,
            registry=mock_registry,
            source_manager=mock_source_manager,
        )
        assert regenerator.vector_store == mock_vector_store
        assert regenerator.embedding_engine == mock_embedding
        assert regenerator.registry == mock_registry
        assert regenerator.source_manager == mock_source_manager

    @pytest.mark.asyncio
    async def test_regenerate_after_removal_no_components(self):
        """Test regeneration without any components."""
        regenerator = RAGRegenerator()
        
        result = await regenerator.regenerate_after_removal(
            source_id="source-1",
            false_content_ids=["content-1", "content-2"],
        )
        
        assert result.success is True
        assert result.source_id == "source-1"
        assert result.documents_removed == 0
        assert result.documents_reindexed == 0
        assert result.false_content_removed == 0

    @pytest.mark.asyncio
    async def test_regenerate_after_removal_with_vector_store(self):
        """Test regeneration with vector store."""
        mock_vector_store = MagicMock()
        mock_vector_store.delete = AsyncMock()
        
        regenerator = RAGRegenerator(vector_store=mock_vector_store)
        
        result = await regenerator.regenerate_after_removal(
            source_id="source-1",
            false_content_ids=["content-1", "content-2"],
        )
        
        assert result.success is True
        assert result.documents_removed == 2
        mock_vector_store.delete.assert_called_once_with(["content-1", "content-2"])

    @pytest.mark.asyncio
    async def test_regenerate_after_removal_vector_store_error(self):
        """Test regeneration when vector store fails."""
        mock_vector_store = MagicMock()
        mock_vector_store.delete = AsyncMock(side_effect=Exception("Delete failed"))
        
        regenerator = RAGRegenerator(vector_store=mock_vector_store)
        
        result = await regenerator.regenerate_after_removal(
            source_id="source-1",
            false_content_ids=["content-1"],
        )
        
        assert result.success is True
        assert result.documents_removed == 0
        assert len(result.warnings) == 1
        assert "Failed to remove from vector store" in result.warnings[0]

    @pytest.mark.asyncio
    async def test_regenerate_after_removal_with_registry(self):
        """Test regeneration with registry."""
        mock_registry = MagicMock()
        mock_registry.get_record_by_content = AsyncMock(return_value=MagicMock())
        mock_registry.mark_removed = AsyncMock(return_value=True)
        
        regenerator = RAGRegenerator(registry=mock_registry)
        
        result = await regenerator.regenerate_after_removal(
            source_id="source-1",
            false_content_ids=["content-1", "content-2"],
        )
        
        assert result.success is True
        assert result.false_content_removed == 2

    @pytest.mark.asyncio
    async def test_regenerate_after_removal_registry_mark_removed_fails(self):
        """Test regeneration when mark_removed returns False."""
        mock_registry = MagicMock()
        mock_registry.get_record_by_content = AsyncMock(return_value=MagicMock())
        mock_registry.mark_removed = AsyncMock(return_value=False)
        
        regenerator = RAGRegenerator(registry=mock_registry)
        
        result = await regenerator.regenerate_after_removal(
            source_id="source-1",
            false_content_ids=["content-1"],
        )
        
        assert result.success is True
        assert result.false_content_removed == 0

    @pytest.mark.asyncio
    async def test_regenerate_after_removal_with_source_manager(self):
        """Test regeneration with source manager."""
        mock_source_manager = MagicMock()
        mock_result = MagicMock()
        mock_result.document_count = 5
        mock_source_manager.index_source = AsyncMock(return_value=mock_result)
        
        regenerator = RAGRegenerator(source_manager=mock_source_manager)
        
        result = await regenerator.regenerate_after_removal(
            source_id="source-1",
            false_content_ids=["content-1"],
            source_path="/path/to/source",
        )
        
        assert result.success is True
        assert result.documents_reindexed == 5
        mock_source_manager.index_source.assert_called_once_with(Path("/path/to/source"))

    @pytest.mark.asyncio
    async def test_regenerate_after_removal_source_manager_error(self):
        """Test regeneration when source manager fails."""
        mock_source_manager = MagicMock()
        mock_source_manager.index_source = AsyncMock(side_effect=Exception("Index failed"))
        
        regenerator = RAGRegenerator(source_manager=mock_source_manager)
        
        result = await regenerator.regenerate_after_removal(
            source_id="source-1",
            false_content_ids=["content-1"],
            source_path="/path/to/source",
        )
        
        assert result.success is True
        assert result.documents_reindexed == 0
        assert len(result.warnings) == 1
        assert "Failed to re-index source" in result.warnings[0]

    @pytest.mark.asyncio
    async def test_regenerate_after_removal_exception(self):
        """Test regeneration when exception occurs."""
        mock_registry = MagicMock()
        mock_registry.get_record_by_content = AsyncMock(side_effect=Exception("Registry error"))
        
        regenerator = RAGRegenerator(registry=mock_registry)
        
        result = await regenerator.regenerate_after_removal(
            source_id="source-1",
            false_content_ids=["content-1"],
        )
        
        assert result.success is False
        assert result.error == "Registry error"

    @pytest.mark.asyncio
    async def test_regenerate_source_no_components(self):
        """Test source regeneration without components."""
        regenerator = RAGRegenerator()
        
        result = await regenerator.regenerate_source("/path/to/source")
        
        assert result.success is True
        assert result.source_id == "/path/to/source"
        assert result.documents_removed == 0
        assert result.documents_reindexed == 0

    @pytest.mark.asyncio
    async def test_regenerate_source_with_registry(self):
        """Test source regeneration with registry."""
        mock_record = MagicMock()
        mock_record.id = "content-1"
        mock_record.source_path = "/path/to/source"
        
        mock_registry = MagicMock()
        mock_registry.get_false_content_by_path = AsyncMock(return_value=[mock_record])
        mock_registry.mark_removed = AsyncMock(return_value=True)
        
        regenerator = RAGRegenerator(registry=mock_registry)
        
        result = await regenerator.regenerate_source("/path/to/source")
        
        assert result.success is True
        assert result.documents_removed == 1
        assert result.false_content_removed == 1

    @pytest.mark.asyncio
    async def test_regenerate_source_with_vector_store(self):
        """Test source regeneration with vector store."""
        mock_record = MagicMock()
        mock_record.id = "content-1"
        mock_record.source_path = "/path/to/source"
        
        mock_registry = MagicMock()
        mock_registry.get_false_content_by_path = AsyncMock(return_value=[mock_record])
        mock_registry.mark_removed = AsyncMock(return_value=True)
        
        mock_vector_store = MagicMock()
        mock_vector_store.delete = AsyncMock()
        
        regenerator = RAGRegenerator(
            registry=mock_registry,
            vector_store=mock_vector_store,
        )
        
        result = await regenerator.regenerate_source("/path/to/source")
        
        assert result.success is True
        mock_vector_store.delete.assert_called_once_with(["content-1"])

    @pytest.mark.asyncio
    async def test_regenerate_source_with_source_manager(self):
        """Test source regeneration with source manager."""
        mock_source_manager = MagicMock()
        mock_result = MagicMock()
        mock_result.document_count = 10
        mock_source_manager.index_source = AsyncMock(return_value=mock_result)
        
        regenerator = RAGRegenerator(source_manager=mock_source_manager)
        
        result = await regenerator.regenerate_source("/path/to/source")
        
        assert result.success is True
        assert result.documents_reindexed == 10

    @pytest.mark.asyncio
    async def test_regenerate_source_exception(self):
        """Test source regeneration when exception occurs."""
        mock_registry = MagicMock()
        mock_registry.get_false_content_by_path = AsyncMock(side_effect=Exception("Failed"))
        
        regenerator = RAGRegenerator(registry=mock_registry)
        
        result = await regenerator.regenerate_source("/path/to/source")
        
        assert result.success is False
        assert result.error == "Failed"

    @pytest.mark.asyncio
    async def test_regenerate_all_no_registry(self):
        """Test regenerate all without registry."""
        regenerator = RAGRegenerator()
        
        results = await regenerator.regenerate_all()
        
        assert results == []

    @pytest.mark.asyncio
    async def test_regenerate_all_with_records(self):
        """Test regenerate all with records."""
        mock_record1 = MagicMock()
        mock_record1.id = "content-1"
        mock_record1.source_path = "/path/to/source1"
        
        mock_record2 = MagicMock()
        mock_record2.id = "content-2"
        mock_record2.source_path = "/path/to/source2"
        
        mock_registry = MagicMock()
        mock_registry.get_all_records = AsyncMock(return_value=[mock_record1, mock_record2])
        mock_registry.get_false_content_by_path = AsyncMock(return_value=[])
        mock_registry.mark_removed = AsyncMock(return_value=True)
        
        regenerator = RAGRegenerator(registry=mock_registry)
        
        results = await regenerator.regenerate_all()
        
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_regenerate_all_same_source(self):
        """Test regenerate all with multiple records from same source."""
        mock_record1 = MagicMock()
        mock_record1.id = "content-1"
        mock_record1.source_path = "/path/to/source"
        
        mock_record2 = MagicMock()
        mock_record2.id = "content-2"
        mock_record2.source_path = "/path/to/source"
        
        mock_registry = MagicMock()
        mock_registry.get_all_records = AsyncMock(return_value=[mock_record1, mock_record2])
        mock_registry.get_false_content_by_path = AsyncMock(return_value=[mock_record1, mock_record2])
        mock_registry.mark_removed = AsyncMock(return_value=True)
        
        regenerator = RAGRegenerator(registry=mock_registry)
        
        results = await regenerator.regenerate_all()
        
        # Should only regenerate once per unique source path
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_regeneration_status_no_registry(self):
        """Test get status without registry."""
        regenerator = RAGRegenerator()
        
        status = await regenerator.get_regeneration_status()
        
        assert status == {"pending": 0}

    @pytest.mark.asyncio
    async def test_get_regeneration_status_no_records(self):
        """Test get status with no records."""
        mock_registry = MagicMock()
        mock_registry.get_all_records = AsyncMock(return_value=[])
        
        regenerator = RAGRegenerator(registry=mock_registry)
        
        status = await regenerator.get_regeneration_status()
        
        assert status["pending_removal"] == 0
        assert status["sources_affected"] == 0
        assert status["oldest_pending"] is None

    @pytest.mark.asyncio
    async def test_get_regeneration_status_with_records(self):
        """Test get status with records."""
        mock_record1 = MagicMock()
        mock_record1.source_id = "source-1"
        mock_record1.marked_at = datetime(2025, 1, 1, 10, 0, 0)
        
        mock_record2 = MagicMock()
        mock_record2.source_id = "source-2"
        mock_record2.marked_at = datetime(2025, 1, 1, 11, 0, 0)
        
        mock_registry = MagicMock()
        mock_registry.get_all_records = AsyncMock(return_value=[mock_record1, mock_record2])
        
        regenerator = RAGRegenerator(registry=mock_registry)
        
        status = await regenerator.get_regeneration_status()
        
        assert status["pending_removal"] == 2
        assert status["sources_affected"] == 2
        assert status["oldest_pending"] == "2025-01-01T10:00:00"

    @pytest.mark.asyncio
    async def test_get_regeneration_status_with_source_id_filter(self):
        """Test get status with source ID filter."""
        mock_record1 = MagicMock()
        mock_record1.source_id = "source-1"
        mock_record1.marked_at = datetime(2025, 1, 1, 10, 0, 0)
        
        mock_record2 = MagicMock()
        mock_record2.source_id = "source-2"
        mock_record2.marked_at = datetime(2025, 1, 1, 11, 0, 0)
        
        mock_registry = MagicMock()
        mock_registry.get_all_records = AsyncMock(return_value=[mock_record1, mock_record2])
        
        regenerator = RAGRegenerator(registry=mock_registry)
        
        status = await regenerator.get_regeneration_status(source_id="source-1")
        
        assert status["pending_removal"] == 1
        assert status["sources_affected"] == 1

    @pytest.mark.asyncio
    async def test_regenerate_after_removal_full_integration(self):
        """Test full regeneration integration."""
        mock_record = MagicMock()
        mock_record.id = "content-1"
        mock_record.reason = "False information"
        
        mock_registry = MagicMock()
        mock_registry.get_record_by_content = AsyncMock(return_value=mock_record)
        mock_registry.mark_removed = AsyncMock(return_value=True)
        
        mock_vector_store = MagicMock()
        mock_vector_store.delete = AsyncMock()
        
        mock_result = MagicMock()
        mock_result.document_count = 3
        
        mock_source_manager = MagicMock()
        mock_source_manager.index_source = AsyncMock(return_value=mock_result)
        
        regenerator = RAGRegenerator(
            vector_store=mock_vector_store,
            registry=mock_registry,
            source_manager=mock_source_manager,
        )
        
        result = await regenerator.regenerate_after_removal(
            source_id="source-1",
            false_content_ids=["content-1"],
            source_path="/path/to/source",
        )
        
        assert result.success is True
        assert result.documents_removed == 1
        assert result.documents_reindexed == 3
        assert result.false_content_removed == 1
        assert result.duration_seconds >= 0
