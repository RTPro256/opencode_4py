"""
Tests for False Content Registry.

Tests the registry for tracking false content in RAG.
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from opencode.core.rag.validation.false_content_registry import (
    FalseContentRecord,
    FalseContentRegistry,
)


class TestFalseContentRecord:
    """Tests for FalseContentRecord model."""

    def test_record_creation(self):
        """Test creating a FalseContentRecord."""
        record = FalseContentRecord(
            id="false_123",
            content="This is false content",
            content_hash="abc123",
            source_id="doc_456",
            source_path="docs/api.md",
            reason="Test failure",
        )
        assert record.id == "false_123"
        assert record.content == "This is false content"
        assert record.content_hash == "abc123"
        assert record.source_id == "doc_456"
        assert record.source_path == "docs/api.md"
        assert record.reason == "Test failure"
        assert record.is_removed is False

    def test_record_with_all_fields(self):
        """Test creating record with all fields."""
        record = FalseContentRecord(
            id="false_123",
            content="False content",
            content_hash="abc123",
            source_id="doc_456",
            source_path="docs/api.md",
            reason="Incorrect information",
            evidence="Test evidence",
            marked_by="test_runner",
            confirmed_by="admin@example.com",
            is_removed=True,
            metadata={"key": "value"},
        )
        assert record.evidence == "Test evidence"
        assert record.marked_by == "test_runner"
        assert record.confirmed_by == "admin@example.com"
        assert record.is_removed is True
        assert record.metadata == {"key": "value"}

    def test_record_to_dict(self):
        """Test converting record to dictionary."""
        record = FalseContentRecord(
            id="false_123",
            content="False content",
            content_hash="abc123",
            source_id="doc_456",
            source_path="docs/api.md",
            reason="Test reason",
            evidence="Test evidence",
            marked_by="tester",
        )
        data = record.to_dict()
        assert data["id"] == "false_123"
        assert data["content_hash"] == "abc123"
        assert data["source_id"] == "doc_456"
        assert data["reason"] == "Test reason"
        assert "marked_at" in data


class TestFalseContentRegistry:
    """Tests for FalseContentRegistry class."""

    @pytest.fixture
    def temp_registry_path(self, tmp_path):
        """Create a temporary registry file path."""
        return str(tmp_path / "RAG" / ".false_content_registry.json")

    @pytest.fixture
    def registry(self, temp_registry_path):
        """Create a FalseContentRegistry instance with temp path."""
        return FalseContentRegistry(path=temp_registry_path)

    def test_init_creates_directory(self, tmp_path):
        """Test that initialization creates the directory."""
        registry_path = str(tmp_path / "subdir" / "registry.json")
        registry = FalseContentRegistry(path=registry_path)
        assert Path(registry_path).parent.exists()

    def test_init_loads_existing_records(self, temp_registry_path):
        """Test that initialization loads existing records."""
        # Create existing registry file
        Path(temp_registry_path).parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": 1,
            "records": [
                {
                    "id": "false_existing",
                    "content": "Existing false content",
                    "content_hash": "hash123",
                    "source_id": "doc_1",
                    "source_path": "docs/existing.md",
                    "reason": "Existing reason",
                    "marked_at": "2024-01-01T12:00:00",
                }
            ],
        }
        with open(temp_registry_path, "w") as f:
            json.dump(data, f)

        registry = FalseContentRegistry(path=temp_registry_path)
        assert len(registry._records) == 1
        assert "false_existing" in registry._records

    def test_load_invalid_json(self, temp_registry_path):
        """Test loading with invalid JSON doesn't crash."""
        Path(temp_registry_path).parent.mkdir(parents=True, exist_ok=True)
        Path(temp_registry_path).write_text("not valid json")

        registry = FalseContentRegistry(path=temp_registry_path)
        assert len(registry._records) == 0

    @pytest.mark.asyncio
    async def test_add_false_content(self, registry):
        """Test adding false content."""
        record = await registry.add_false_content(
            content="This is incorrect",
            source_id="doc_123",
            source_path="docs/api.md",
            reason="Test failure",
            evidence="Test output",
            marked_by="test_runner",
        )
        
        assert record.id.startswith("false_")
        assert record.content == "This is incorrect"
        assert record.source_id == "doc_123"
        assert record.reason == "Test failure"
        assert len(registry._records) == 1

    @pytest.mark.asyncio
    async def test_add_false_content_with_metadata(self, registry):
        """Test adding false content with metadata."""
        record = await registry.add_false_content(
            content="False content",
            source_id="doc_123",
            source_path="docs/api.md",
            reason="Test",
            metadata={"test_id": "test_1"},
        )
        assert record.metadata == {"test_id": "test_1"}

    @pytest.mark.asyncio
    async def test_get_false_content_for_source(self, registry):
        """Test getting false content for a source."""
        await registry.add_false_content(
            content="Content 1",
            source_id="doc_1",
            source_path="docs/1.md",
            reason="Reason 1",
        )
        await registry.add_false_content(
            content="Content 2",
            source_id="doc_2",
            source_path="docs/2.md",
            reason="Reason 2",
        )
        await registry.add_false_content(
            content="Content 3",
            source_id="doc_1",
            source_path="docs/3.md",
            reason="Reason 3",
        )
        
        records = await registry.get_false_content_for_source("doc_1")
        assert len(records) == 2

    @pytest.mark.asyncio
    async def test_get_false_content_by_path(self, registry):
        """Test getting false content by path."""
        await registry.add_false_content(
            content="Content 1",
            source_id="doc_1",
            source_path="docs/api.md",
            reason="Reason 1",
        )
        await registry.add_false_content(
            content="Content 2",
            source_id="doc_2",
            source_path="docs/other.md",
            reason="Reason 2",
        )
        
        records = await registry.get_false_content_by_path("docs/api.md")
        assert len(records) == 1
        assert records[0].source_path == "docs/api.md"

    @pytest.mark.asyncio
    async def test_is_content_false(self, registry):
        """Test checking if content is false."""
        content = "This is false information"
        await registry.add_false_content(
            content=content,
            source_id="doc_1",
            source_path="docs/1.md",
            reason="Test",
        )
        
        assert await registry.is_content_false(content) is True
        assert await registry.is_content_false("Different content") is False

    @pytest.mark.asyncio
    async def test_get_record_by_content(self, registry):
        """Test getting record by content."""
        content = "Specific false content"
        await registry.add_false_content(
            content=content,
            source_id="doc_1",
            source_path="docs/1.md",
            reason="Test",
        )
        
        record = await registry.get_record_by_content(content)
        assert record is not None
        assert record.content == content
        
        # Non-existent content
        record = await registry.get_record_by_content("Non-existent")
        assert record is None

    @pytest.mark.asyncio
    async def test_mark_removed(self, registry):
        """Test marking a record as removed."""
        record = await registry.add_false_content(
            content="Content to remove",
            source_id="doc_1",
            source_path="docs/1.md",
            reason="Test",
        )
        
        assert record.is_removed is False
        
        result = await registry.mark_removed(record.id)
        assert result is True
        assert registry._records[record.id].is_removed is True
        assert registry._records[record.id].removed_at is not None

    @pytest.mark.asyncio
    async def test_mark_removed_nonexistent(self, registry):
        """Test marking nonexistent record as removed."""
        result = await registry.mark_removed("nonexistent_id")
        assert result is False

    @pytest.mark.asyncio
    async def test_confirm_record(self, registry):
        """Test confirming a record."""
        record = await registry.add_false_content(
            content="Content to confirm",
            source_id="doc_1",
            source_path="docs/1.md",
            reason="Test",
        )
        
        assert record.confirmed_by is None
        
        result = await registry.confirm_record(record.id, "admin@example.com")
        assert result is True
        assert registry._records[record.id].confirmed_by == "admin@example.com"

    @pytest.mark.asyncio
    async def test_confirm_record_nonexistent(self, registry):
        """Test confirming nonexistent record."""
        result = await registry.confirm_record("nonexistent", "admin@example.com")
        assert result is False

    @pytest.mark.asyncio
    async def test_remove_record(self, registry):
        """Test removing a record."""
        record = await registry.add_false_content(
            content="Content to delete",
            source_id="doc_1",
            source_path="docs/1.md",
            reason="Test",
        )
        
        assert len(registry._records) == 1
        
        result = await registry.remove_record(record.id)
        assert result is True
        assert len(registry._records) == 0
        assert record.content_hash not in registry._content_hashes

    @pytest.mark.asyncio
    async def test_remove_record_nonexistent(self, registry):
        """Test removing nonexistent record."""
        result = await registry.remove_record("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_all_records(self, registry):
        """Test getting all records."""
        await registry.add_false_content(
            content="Content 1",
            source_id="doc_1",
            source_path="docs/1.md",
            reason="Test",
        )
        record2 = await registry.add_false_content(
            content="Content 2",
            source_id="doc_2",
            source_path="docs/2.md",
            reason="Test",
        )
        
        # Mark one as removed
        await registry.mark_removed(record2.id)
        
        # Get all without removed
        records = await registry.get_all_records(include_removed=False)
        assert len(records) == 1
        
        # Get all with removed
        records = await registry.get_all_records(include_removed=True)
        assert len(records) == 2

    @pytest.mark.asyncio
    async def test_get_stats(self, registry):
        """Test getting registry statistics."""
        record1 = await registry.add_false_content(
            content="Content 1",
            source_id="doc_1",
            source_path="docs/1.md",
            reason="Test",
        )
        record2 = await registry.add_false_content(
            content="Content 2",
            source_id="doc_2",
            source_path="docs/2.md",
            reason="Test",
        )
        await registry.add_false_content(
            content="Content 3",
            source_id="doc_1",
            source_path="docs/3.md",
            reason="Test",
        )
        
        # Confirm one and mark one as removed
        await registry.confirm_record(record1.id, "admin")
        await registry.mark_removed(record2.id)
        
        stats = await registry.get_stats()
        assert stats["total_records"] == 3
        assert stats["pending_removal"] == 2  # Not removed
        assert stats["removed"] == 1
        assert stats["confirmed"] == 1
        assert stats["unique_sources"] == 2  # doc_1 and doc_2

    @pytest.mark.asyncio
    async def test_clear(self, registry):
        """Test clearing all records."""
        await registry.add_false_content(
            content="Content 1",
            source_id="doc_1",
            source_path="docs/1.md",
            reason="Test",
        )
        await registry.add_false_content(
            content="Content 2",
            source_id="doc_2",
            source_path="docs/2.md",
            reason="Test",
        )
        
        assert len(registry._records) == 2
        
        await registry.clear()
        
        assert len(registry._records) == 0
        assert len(registry._content_hashes) == 0

    def test_hash_content(self, registry):
        """Test content hashing."""
        hash1 = registry._hash_content("test content")
        hash2 = registry._hash_content("test content")
        hash3 = registry._hash_content("different content")
        
        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 16

    @pytest.mark.asyncio
    async def test_persistence(self, temp_registry_path):
        """Test that records persist across registry instances."""
        # Create first instance and add record
        registry1 = FalseContentRegistry(path=temp_registry_path)
        await registry1.add_false_content(
            content="Persistent content",
            source_id="doc_1",
            source_path="docs/1.md",
            reason="Test",
        )
        
        # Create second instance - should load existing records
        registry2 = FalseContentRegistry(path=temp_registry_path)
        assert len(registry2._records) == 1
        assert await registry2.is_content_false("Persistent content") is True
