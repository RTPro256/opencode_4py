"""
Tests for Validation Pipeline.

Tests validation-aware RAG pipeline functionality.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

from opencode.core.rag.validation.validation_pipeline import (
    FilteredContent,
    ValidatedQueryResult,
    ValidationAwareRAGPipeline,
)


class TestFilteredContent:
    """Tests for FilteredContent model."""

    def test_init_required_fields(self):
        """Test initialization with required fields."""
        filtered = FilteredContent(
            content_id="test-id",
            content_preview="test content...",
            source_id="source-1",
            reason="Marked as false",
        )
        assert filtered.content_id == "test-id"
        assert filtered.content_preview == "test content..."
        assert filtered.source_id == "source-1"
        assert filtered.reason == "Marked as false"
        assert isinstance(filtered.filtered_at, datetime)

    def test_init_with_custom_timestamp(self):
        """Test initialization with custom timestamp."""
        custom_time = datetime(2025, 1, 1, 12, 0, 0)
        filtered = FilteredContent(
            content_id="test-id",
            content_preview="test content",
            source_id="source-1",
            reason="Test reason",
            filtered_at=custom_time,
        )
        assert filtered.filtered_at == custom_time


class TestValidatedQueryResult:
    """Tests for ValidatedQueryResult model."""

    def test_init_defaults(self):
        """Test initialization with default values."""
        result = ValidatedQueryResult(query="test query")
        assert result.query == "test query"
        assert result.results == []
        assert result.total_found == 0
        assert result.filtered_count == 0
        assert result.filtered_content == []
        assert isinstance(result.query_time, datetime)

    def test_init_with_results(self):
        """Test initialization with results."""
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {"text": "result text"}
        
        result = ValidatedQueryResult(
            query="test query",
            results=[mock_result],
            total_found=5,
            filtered_count=2,
        )
        assert result.query == "test query"
        assert len(result.results) == 1
        assert result.total_found == 5
        assert result.filtered_count == 2

    def test_to_dict(self):
        """Test to_dict conversion."""
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {"text": "result text"}
        
        filtered = FilteredContent(
            content_id="filtered-1",
            content_preview="preview",
            source_id="source-1",
            reason="Test",
        )
        
        result = ValidatedQueryResult(
            query="test query",
            results=[mock_result],
            total_found=5,
            filtered_count=1,
            filtered_content=[filtered],
        )
        
        d = result.to_dict()
        assert d["query"] == "test query"
        assert d["total_found"] == 5
        assert d["filtered_count"] == 1
        assert len(d["results"]) == 1
        assert d["results"][0] == {"text": "result text"}

    def test_to_dict_result_without_to_dict(self):
        """Test to_dict with result that doesn't have to_dict."""
        mock_result = MagicMock(spec=object)  # No to_dict method
        mock_result.__str__ = lambda self: "string result"
        
        result = ValidatedQueryResult(
            query="test query",
            results=[mock_result],
            total_found=1,
            filtered_count=0,
        )
        
        d = result.to_dict()
        assert d["results"][0] == "string result"


class TestValidationAwareRAGPipeline:
    """Tests for ValidationAwareRAGPipeline class."""

    def test_init_defaults(self):
        """Test initialization with default values."""
        pipeline = ValidationAwareRAGPipeline()
        assert pipeline.hybrid_search is None
        assert pipeline.registry is None
        assert pipeline.audit_logger is None
        assert pipeline.auto_filter is True
        assert pipeline.log_filtered is True
        assert pipeline._total_queries == 0
        assert pipeline._total_filtered == 0

    def test_init_custom(self):
        """Test initialization with custom values."""
        mock_search = MagicMock()
        mock_registry = MagicMock()
        mock_logger = MagicMock()
        
        pipeline = ValidationAwareRAGPipeline(
            hybrid_search=mock_search,
            registry=mock_registry,
            audit_logger=mock_logger,
            auto_filter=False,
            log_filtered=False,
        )
        assert pipeline.hybrid_search == mock_search
        assert pipeline.registry == mock_registry
        assert pipeline.audit_logger == mock_logger
        assert pipeline.auto_filter is False
        assert pipeline.log_filtered is False

    @pytest.mark.asyncio
    async def test_query_with_validation_no_hybrid_search(self):
        """Test query without hybrid search."""
        pipeline = ValidationAwareRAGPipeline()
        
        result = await pipeline.query_with_validation(
            query="test query",
            query_embedding=[0.1, 0.2, 0.3],
        )
        
        assert result.query == "test query"
        assert result.results == []
        assert result.total_found == 0
        assert result.filtered_count == 0
        assert pipeline._total_queries == 1

    @pytest.mark.asyncio
    async def test_query_with_validation_no_embedding(self):
        """Test query without embedding."""
        mock_search = MagicMock()
        mock_search.search = AsyncMock(return_value=[])
        
        pipeline = ValidationAwareRAGPipeline(hybrid_search=mock_search)
        
        result = await pipeline.query_with_validation(
            query="test query",
            query_embedding=None,
        )
        
        assert result.query == "test query"
        assert result.results == []
        assert result.total_found == 0
        # Search should not be called without embedding
        mock_search.search.assert_not_called()

    @pytest.mark.asyncio
    async def test_query_with_validation_with_results(self):
        """Test query with results."""
        mock_result = MagicMock()
        mock_result.text = "This is valid content"
        mock_result.id = "result-1"
        mock_result.source_id = "source-1"
        
        mock_search = MagicMock()
        mock_search.search = AsyncMock(return_value=[mock_result])
        
        mock_registry = MagicMock()
        mock_registry.is_content_false = AsyncMock(return_value=False)
        
        pipeline = ValidationAwareRAGPipeline(
            hybrid_search=mock_search,
            registry=mock_registry,
        )
        
        result = await pipeline.query_with_validation(
            query="test query",
            query_embedding=[0.1, 0.2, 0.3],
            top_k=5,
        )
        
        assert result.query == "test query"
        assert len(result.results) == 1
        assert result.total_found == 1
        assert result.filtered_count == 0
        # Should fetch double when auto_filter is enabled
        mock_search.search.assert_called_once_with(
            query="test query",
            query_embedding=[0.1, 0.2, 0.3],
            top_k=10,  # top_k * 2
        )

    @pytest.mark.asyncio
    async def test_query_with_validation_filters_false_content(self):
        """Test query filters false content."""
        mock_result = MagicMock()
        mock_result.text = "This is false content"
        mock_result.id = "result-1"
        mock_result.source_id = "source-1"
        
        mock_search = MagicMock()
        mock_search.search = AsyncMock(return_value=[mock_result])
        
        mock_record = MagicMock()
        mock_record.reason = "Incorrect information"
        
        mock_registry = MagicMock()
        mock_registry.is_content_false = AsyncMock(return_value=True)
        mock_registry.get_record_by_content = AsyncMock(return_value=mock_record)
        
        mock_audit = MagicMock()
        mock_audit.log_event = AsyncMock()
        
        pipeline = ValidationAwareRAGPipeline(
            hybrid_search=mock_search,
            registry=mock_registry,
            audit_logger=mock_audit,
            log_filtered=True,
        )
        
        result = await pipeline.query_with_validation(
            query="test query",
            query_embedding=[0.1, 0.2, 0.3],
        )
        
        assert len(result.results) == 0
        assert result.filtered_count == 1
        assert len(result.filtered_content) == 1
        assert result.filtered_content[0].content_id == "result-1"
        assert result.filtered_content[0].reason == "Incorrect information"
        assert pipeline._total_filtered == 1
        
        # Audit should be called
        mock_audit.log_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_with_validation_auto_filter_disabled(self):
        """Test query with auto_filter disabled."""
        mock_result = MagicMock()
        mock_result.text = "This is false content"
        mock_result.id = "result-1"
        mock_result.source_id = "source-1"
        
        mock_search = MagicMock()
        mock_search.search = AsyncMock(return_value=[mock_result])
        
        mock_registry = MagicMock()
        mock_registry.is_content_false = AsyncMock(return_value=True)
        
        pipeline = ValidationAwareRAGPipeline(
            hybrid_search=mock_search,
            registry=mock_registry,
            auto_filter=False,
        )
        
        result = await pipeline.query_with_validation(
            query="test query",
            query_embedding=[0.1, 0.2, 0.3],
            top_k=5,
        )
        
        # Should not filter when auto_filter is False
        assert len(result.results) == 1
        assert result.filtered_count == 0
        # Should fetch exact top_k when auto_filter is disabled
        mock_search.search.assert_called_once_with(
            query="test query",
            query_embedding=[0.1, 0.2, 0.3],
            top_k=5,
        )

    @pytest.mark.asyncio
    async def test_query_with_validation_no_registry(self):
        """Test query without registry."""
        mock_result = MagicMock()
        mock_result.text = "Some content"
        mock_result.id = "result-1"
        
        mock_search = MagicMock()
        mock_search.search = AsyncMock(return_value=[mock_result])
        
        pipeline = ValidationAwareRAGPipeline(hybrid_search=mock_search)
        
        result = await pipeline.query_with_validation(
            query="test query",
            query_embedding=[0.1, 0.2, 0.3],
        )
        
        # Should not filter without registry
        assert len(result.results) == 1
        assert result.filtered_count == 0

    @pytest.mark.asyncio
    async def test_query_with_validation_result_without_attributes(self):
        """Test query with results lacking standard attributes."""
        # Result without text, id, source_id attributes
        mock_result = MagicMock(spec=object)
        
        mock_search = MagicMock()
        mock_search.search = AsyncMock(return_value=[mock_result])
        
        mock_registry = MagicMock()
        mock_registry.is_content_false = AsyncMock(return_value=False)
        
        pipeline = ValidationAwareRAGPipeline(
            hybrid_search=mock_search,
            registry=mock_registry,
        )
        
        result = await pipeline.query_with_validation(
            query="test query",
            query_embedding=[0.1, 0.2, 0.3],
        )
        
        assert len(result.results) == 1
        # Should use defaults for missing attributes
        assert result.filtered_content == []

    @pytest.mark.asyncio
    async def test_query_with_validation_result_with_metadata_source(self):
        """Test query with result having source in metadata."""
        mock_result = MagicMock()
        mock_result.text = "Some content"
        mock_result.id = "result-1"
        # No source_id attribute, but has metadata with source
        del mock_result.source_id
        mock_result.metadata = {"source": "metadata-source"}
        
        mock_search = MagicMock()
        mock_search.search = AsyncMock(return_value=[mock_result])
        
        mock_record = MagicMock()
        mock_record.reason = "Test reason"
        
        mock_registry = MagicMock()
        mock_registry.is_content_false = AsyncMock(return_value=True)
        mock_registry.get_record_by_content = AsyncMock(return_value=mock_record)
        
        pipeline = ValidationAwareRAGPipeline(
            hybrid_search=mock_search,
            registry=mock_registry,
        )
        
        result = await pipeline.query_with_validation(
            query="test query",
            query_embedding=[0.1, 0.2, 0.3],
        )
        
        assert result.filtered_count == 1
        assert result.filtered_content[0].source_id == "metadata-source"

    @pytest.mark.asyncio
    async def test_query_with_validation_long_content_preview(self):
        """Test that long content is truncated in preview."""
        long_content = "x" * 200
        mock_result = MagicMock()
        mock_result.text = long_content
        mock_result.id = "result-1"
        mock_result.source_id = "source-1"
        
        mock_search = MagicMock()
        mock_search.search = AsyncMock(return_value=[mock_result])
        
        mock_record = MagicMock()
        mock_record.reason = "Test"
        
        mock_registry = MagicMock()
        mock_registry.is_content_false = AsyncMock(return_value=True)
        mock_registry.get_record_by_content = AsyncMock(return_value=mock_record)
        
        pipeline = ValidationAwareRAGPipeline(
            hybrid_search=mock_search,
            registry=mock_registry,
        )
        
        result = await pipeline.query_with_validation(
            query="test query",
            query_embedding=[0.1, 0.2, 0.3],
        )
        
        # Preview should be truncated to 100 chars + "..."
        assert len(result.filtered_content[0].content_preview) == 103
        assert result.filtered_content[0].content_preview.endswith("...")

    @pytest.mark.asyncio
    async def test_query_with_validation_no_record_reason(self):
        """Test filtered content uses default reason when no record."""
        mock_result = MagicMock()
        mock_result.text = "Some content"
        mock_result.id = "result-1"
        mock_result.source_id = "source-1"
        
        mock_search = MagicMock()
        mock_search.search = AsyncMock(return_value=[mock_result])
        
        mock_registry = MagicMock()
        mock_registry.is_content_false = AsyncMock(return_value=True)
        mock_registry.get_record_by_content = AsyncMock(return_value=None)
        
        pipeline = ValidationAwareRAGPipeline(
            hybrid_search=mock_search,
            registry=mock_registry,
        )
        
        result = await pipeline.query_with_validation(
            query="test query",
            query_embedding=[0.1, 0.2, 0.3],
        )
        
        assert result.filtered_content[0].reason == "Marked as false"

    @pytest.mark.asyncio
    async def test_build_context_with_validation(self):
        """Test building context with validation."""
        mock_result = MagicMock()
        mock_result.text = "Context content"
        mock_result.id = "result-1"
        
        mock_search = MagicMock()
        mock_search.search = AsyncMock(return_value=[mock_result])
        
        mock_registry = MagicMock()
        mock_registry.is_content_false = AsyncMock(return_value=False)
        
        pipeline = ValidationAwareRAGPipeline(
            hybrid_search=mock_search,
            registry=mock_registry,
        )
        
        context = await pipeline.build_context_with_validation(
            query="test query",
            query_embedding=[0.1, 0.2, 0.3],
        )
        
        assert context == "Context content"

    @pytest.mark.asyncio
    async def test_build_context_with_multiple_results(self):
        """Test building context with multiple results."""
        mock_result1 = MagicMock()
        mock_result1.text = "First content"
        mock_result1.id = "result-1"
        
        mock_result2 = MagicMock()
        mock_result2.text = "Second content"
        mock_result2.id = "result-2"
        
        mock_search = MagicMock()
        mock_search.search = AsyncMock(return_value=[mock_result1, mock_result2])
        
        mock_registry = MagicMock()
        mock_registry.is_content_false = AsyncMock(return_value=False)
        
        pipeline = ValidationAwareRAGPipeline(
            hybrid_search=mock_search,
            registry=mock_registry,
        )
        
        context = await pipeline.build_context_with_validation(
            query="test query",
            query_embedding=[0.1, 0.2, 0.3],
        )
        
        assert "First content" in context
        assert "Second content" in context
        assert "\n\n" in context

    @pytest.mark.asyncio
    async def test_build_context_respects_max_tokens(self):
        """Test that context building respects max_tokens."""
        mock_result1 = MagicMock()
        mock_result1.text = "A" * 100  # ~25 tokens
        mock_result1.id = "result-1"
        
        mock_result2 = MagicMock()
        mock_result2.text = "B" * 100  # ~25 tokens
        mock_result2.id = "result-2"
        
        mock_search = MagicMock()
        mock_search.search = AsyncMock(return_value=[mock_result1, mock_result2])
        
        mock_registry = MagicMock()
        mock_registry.is_content_false = AsyncMock(return_value=False)
        
        pipeline = ValidationAwareRAGPipeline(
            hybrid_search=mock_search,
            registry=mock_registry,
        )
        
        context = await pipeline.build_context_with_validation(
            query="test query",
            query_embedding=[0.1, 0.2, 0.3],
            max_tokens=30,  # Should only fit first result
        )
        
        assert "A" * 100 in context
        assert "B" * 100 not in context

    @pytest.mark.asyncio
    async def test_build_context_result_without_text(self):
        """Test building context with result without text attribute."""
        mock_result = MagicMock(spec=object)
        mock_result.__str__ = lambda self: "string representation"
        
        mock_search = MagicMock()
        mock_search.search = AsyncMock(return_value=[mock_result])
        
        pipeline = ValidationAwareRAGPipeline(hybrid_search=mock_search)
        
        context = await pipeline.build_context_with_validation(
            query="test query",
            query_embedding=[0.1, 0.2, 0.3],
        )
        
        assert context == "string representation"

    @pytest.mark.asyncio
    async def test_suggest_corrections_no_registry(self):
        """Test suggest_corrections without registry."""
        pipeline = ValidationAwareRAGPipeline()
        
        suggestions = await pipeline.suggest_corrections("test query")
        
        assert suggestions == []

    @pytest.mark.asyncio
    async def test_suggest_corrections_with_matches(self):
        """Test suggest_corrections with matching records."""
        mock_record = MagicMock()
        mock_record.content = "This is test content about authentication"
        mock_record.reason = "Outdated information"
        mock_record.source_path = "/path/to/source"
        mock_record.marked_at = datetime(2025, 1, 1, 12, 0, 0)
        
        mock_registry = MagicMock()
        mock_registry.get_all_records = AsyncMock(return_value=[mock_record])
        
        pipeline = ValidationAwareRAGPipeline(registry=mock_registry)
        
        suggestions = await pipeline.suggest_corrections("test authentication")
        
        assert len(suggestions) == 1
        assert "test content" in suggestions[0]["false_content"]
        assert suggestions[0]["reason"] == "Outdated information"
        assert suggestions[0]["source"] == "/path/to/source"

    @pytest.mark.asyncio
    async def test_suggest_corrections_no_matches(self):
        """Test suggest_corrections with no matching records."""
        mock_record = MagicMock()
        mock_record.content = "This is about something else"
        mock_record.reason = "Test reason"
        mock_record.source_path = "/path"
        mock_record.marked_at = datetime(2025, 1, 1)
        
        mock_registry = MagicMock()
        mock_registry.get_all_records = AsyncMock(return_value=[mock_record])
        
        pipeline = ValidationAwareRAGPipeline(registry=mock_registry)
        
        suggestions = await pipeline.suggest_corrections("authentication")
        
        assert len(suggestions) == 0

    @pytest.mark.asyncio
    async def test_suggest_corrections_limited_to_ten(self):
        """Test that suggest_corrections limits to 10 records."""
        mock_records = []
        for i in range(15):
            record = MagicMock()
            record.content = f"Test content {i}"
            record.reason = f"Reason {i}"
            record.source_path = f"/path/{i}"
            record.marked_at = datetime(2025, 1, 1)
            mock_records.append(record)
        
        mock_registry = MagicMock()
        mock_registry.get_all_records = AsyncMock(return_value=mock_records)
        
        pipeline = ValidationAwareRAGPipeline(registry=mock_registry)
        
        suggestions = await pipeline.suggest_corrections("test")
        
        assert len(suggestions) == 10

    @pytest.mark.asyncio
    async def test_get_validation_stats(self):
        """Test getting validation statistics."""
        mock_registry = MagicMock()
        mock_registry.get_stats = AsyncMock(return_value={"total_records": 5})
        
        pipeline = ValidationAwareRAGPipeline(registry=mock_registry)
        pipeline._total_queries = 10
        pipeline._total_filtered = 3
        
        stats = await pipeline.get_validation_stats()
        
        assert stats["total_queries"] == 10
        assert stats["total_filtered"] == 3
        assert stats["filter_rate"] == 0.3
        assert stats["auto_filter"] is True
        assert stats["log_filtered"] is True
        assert stats["registry"] == {"total_records": 5}

    @pytest.mark.asyncio
    async def test_get_validation_stats_no_queries(self):
        """Test validation stats with no queries."""
        pipeline = ValidationAwareRAGPipeline()
        
        stats = await pipeline.get_validation_stats()
        
        assert stats["filter_rate"] == 0

    @pytest.mark.asyncio
    async def test_get_validation_stats_no_registry(self):
        """Test validation stats without registry."""
        pipeline = ValidationAwareRAGPipeline()
        
        stats = await pipeline.get_validation_stats()
        
        assert "registry" not in stats

    @pytest.mark.asyncio
    async def test_report_false_content(self):
        """Test reporting false content."""
        mock_record = MagicMock()
        mock_record.id = "record-1"
        
        mock_registry = MagicMock()
        mock_registry.add_false_content = AsyncMock(return_value=mock_record)
        
        mock_audit = MagicMock()
        mock_audit.log_event = AsyncMock()
        
        pipeline = ValidationAwareRAGPipeline(
            registry=mock_registry,
            audit_logger=mock_audit,
        )
        
        record = await pipeline.report_false_content(
            content="False content",
            source_id="source-1",
            source_path="/path/to/source",
            reason="Incorrect information",
            evidence="Test evidence",
            reported_by="user-1",
        )
        
        assert record.id == "record-1"
        mock_registry.add_false_content.assert_called_once_with(
            content="False content",
            source_id="source-1",
            source_path="/path/to/source",
            reason="Incorrect information",
            evidence="Test evidence",
            marked_by="user-1",
        )
        mock_audit.log_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_report_false_content_no_registry(self):
        """Test reporting false content without registry."""
        pipeline = ValidationAwareRAGPipeline()
        
        record = await pipeline.report_false_content(
            content="False content",
            source_id="source-1",
            source_path="/path",
            reason="Test",
        )
        
        assert record is None

    @pytest.mark.asyncio
    async def test_report_false_content_no_audit_logger(self):
        """Test reporting false content without audit logger."""
        mock_record = MagicMock()
        mock_record.id = "record-1"
        
        mock_registry = MagicMock()
        mock_registry.add_false_content = AsyncMock(return_value=mock_record)
        
        pipeline = ValidationAwareRAGPipeline(registry=mock_registry)
        
        record = await pipeline.report_false_content(
            content="False content",
            source_id="source-1",
            source_path="/path",
            reason="Test",
        )
        
        assert record.id == "record-1"

    def test_reset_stats(self):
        """Test resetting statistics."""
        pipeline = ValidationAwareRAGPipeline()
        pipeline._total_queries = 100
        pipeline._total_filtered = 25
        
        pipeline.reset_stats()
        
        assert pipeline._total_queries == 0
        assert pipeline._total_filtered == 0

    @pytest.mark.asyncio
    async def test_multiple_queries_increment_stats(self):
        """Test that multiple queries increment statistics."""
        mock_result = MagicMock()
        mock_result.text = "Content"
        mock_result.id = "result-1"
        
        mock_search = MagicMock()
        mock_search.search = AsyncMock(return_value=[mock_result])
        
        pipeline = ValidationAwareRAGPipeline(hybrid_search=mock_search)
        
        await pipeline.query_with_validation("query 1", [0.1, 0.2])
        await pipeline.query_with_validation("query 2", [0.1, 0.2])
        await pipeline.query_with_validation("query 3", [0.1, 0.2])
        
        assert pipeline._total_queries == 3
