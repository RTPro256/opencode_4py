"""
Tests for Source Manager.

Tests source validation, indexing, and management functionality.
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile
import os

from opencode.core.rag.source_manager import (
    SourceValidationError,
    IndexResult,
    SourceInfo,
    SourceManager,
    create_source_manager,
)


class TestSourceValidationError:
    """Tests for SourceValidationError exception."""

    def test_is_exception(self):
        """Test that it's an exception."""
        assert issubclass(SourceValidationError, Exception)

    def test_can_raise(self):
        """Test that it can be raised."""
        with pytest.raises(SourceValidationError):
            raise SourceValidationError("Test error")


class TestIndexResult:
    """Tests for IndexResult model."""

    def test_init_required_fields(self):
        """Test initialization with required fields."""
        result = IndexResult(
            success=True,
            source="/path/to/source",
        )
        assert result.success is True
        assert result.source == "/path/to/source"
        assert result.document_count == 0
        assert result.chunk_count == 0
        assert result.error is None
        assert result.duration_seconds == 0.0

    def test_init_with_all_fields(self):
        """Test initialization with all fields."""
        from datetime import datetime
        
        now = datetime.utcnow()
        result = IndexResult(
            success=True,
            source="/path/to/source",
            document_count=10,
            chunk_count=25,
            error=None,
            duration_seconds=1.5,
            indexed_at=now,
        )
        assert result.document_count == 10
        assert result.chunk_count == 25
        assert result.duration_seconds == 1.5
        assert result.indexed_at == now

    def test_init_with_error(self):
        """Test initialization with error."""
        result = IndexResult(
            success=False,
            source="/path/to/source",
            error="Indexing failed",
        )
        assert result.success is False
        assert result.error == "Indexing failed"


class TestSourceInfo:
    """Tests for SourceInfo dataclass."""

    def test_init_required_fields(self):
        """Test initialization with required fields."""
        info = SourceInfo(path="/path/to/source")
        assert info.path == "/path/to/source"
        assert info.file_count == 0
        assert info.total_size == 0
        assert info.last_indexed is None
        assert info.file_hash is None
        assert info.metadata == {}

    def test_init_with_all_fields(self):
        """Test initialization with all fields."""
        from datetime import datetime
        
        now = datetime.utcnow()
        info = SourceInfo(
            path="/path/to/source",
            file_count=10,
            total_size=1024,
            last_indexed=now,
            file_hash="abc123",
            metadata={"key": "value"},
        )
        assert info.file_count == 10
        assert info.total_size == 1024
        assert info.last_indexed == now
        assert info.file_hash == "abc123"
        assert info.metadata == {"key": "value"}


class TestSourceManager:
    """Tests for SourceManager class."""

    def test_init_defaults(self):
        """Test initialization with default values."""
        manager = SourceManager()
        assert len(manager.allowed_sources) == 3
        assert len(manager.blocked_patterns) == 6
        assert len(manager.file_patterns) == 5
        assert manager._indexed_sources == {}

    def test_init_custom(self):
        """Test initialization with custom values."""
        manager = SourceManager(
            allowed_sources=["/custom/path"],
            blocked_patterns=["**/secret/**"],
            file_patterns=["*.custom"],
        )
        assert manager.allowed_sources == ["/custom/path"]
        assert manager.blocked_patterns == ["**/secret/**"]
        assert manager.file_patterns == ["*.custom"]

    def test_validate_source_nonexistent(self):
        """Test validation of nonexistent source."""
        manager = SourceManager(allowed_sources=["/docs"])
        
        result = manager.validate_source(Path("/nonexistent/path"))
        
        assert result is False

    def test_validate_source_not_allowed(self):
        """Test validation of source not in allowed list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SourceManager(allowed_sources=["/docs"])
            
            # Create a directory
            test_dir = Path(tmpdir) / "test"
            test_dir.mkdir()
            
            result = manager.validate_source(test_dir)
            
            assert result is False

    def test_validate_source_allowed(self):
        """Test validation of allowed source."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SourceManager(allowed_sources=[tmpdir])
            
            # Create a directory
            test_dir = Path(tmpdir) / "test"
            test_dir.mkdir()
            
            result = manager.validate_source(test_dir)
            
            assert result is True

    def test_validate_source_exact_match(self):
        """Test validation with exact path match."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SourceManager(allowed_sources=[tmpdir])
            
            result = manager.validate_source(Path(tmpdir))
            
            assert result is True

    def test_validate_source_blocked_pattern(self):
        """Test validation of source matching blocked pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a secrets directory
            secrets_dir = Path(tmpdir) / "secrets"
            secrets_dir.mkdir()
            
            manager = SourceManager(
                allowed_sources=[tmpdir],
                blocked_patterns=["**/secrets/**"],
            )
            
            result = manager.validate_source(secrets_dir)
            
            # The blocked pattern check is on the source string
            # This tests the fnmatch pattern matching
            assert result is True  # Directory itself doesn't match pattern

    def test_is_file_allowed_blocked_pattern(self):
        """Test file allowed check with blocked pattern."""
        manager = SourceManager(
            blocked_patterns=["**/secrets/**"],
            file_patterns=["*.txt"],
        )
        
        # File in secrets directory
        result = manager.is_file_allowed(Path("/some/path/secrets/file.txt"))
        
        # fnmatch should match the pattern
        assert result is False

    def test_is_file_allowed_matching_pattern(self):
        """Test file allowed check with matching file pattern."""
        manager = SourceManager(
            file_patterns=["*.txt", "*.md"],
        )
        
        result = manager.is_file_allowed(Path("/some/path/file.txt"))
        
        assert result is True

    def test_is_file_allowed_non_matching_pattern(self):
        """Test file allowed check with non-matching file pattern."""
        manager = SourceManager(
            file_patterns=["*.txt", "*.md"],
        )
        
        result = manager.is_file_allowed(Path("/some/path/file.py"))
        
        assert result is False

    def test_get_files_to_index_invalid_source(self):
        """Test getting files from invalid source."""
        manager = SourceManager(allowed_sources=["/docs"])
        
        files = manager.get_files_to_index(Path("/nonexistent"))
        
        assert files == []

    def test_get_files_to_index_empty_directory(self):
        """Test getting files from empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SourceManager(allowed_sources=[tmpdir])
            
            files = manager.get_files_to_index(Path(tmpdir))
            
            assert files == []

    def test_get_files_to_index_with_files(self):
        """Test getting files from directory with files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SourceManager(
                allowed_sources=[tmpdir],
                file_patterns=["*.txt"],
            )
            
            # Create test files
            (Path(tmpdir) / "file1.txt").write_text("content 1")
            (Path(tmpdir) / "file2.txt").write_text("content 2")
            (Path(tmpdir) / "file3.py").write_text("# python file")
            
            files = manager.get_files_to_index(Path(tmpdir))
            
            assert len(files) == 2
            assert all(f.suffix == ".txt" for f in files)

    def test_get_files_to_index_single_file(self):
        """Test getting a single file to index."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SourceManager(
                allowed_sources=[tmpdir],
                file_patterns=["*.txt"],
            )
            
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("content")
            
            files = manager.get_files_to_index(test_file)
            
            assert len(files) == 1
            assert files[0] == test_file.resolve()

    def test_calculate_hash(self):
        """Test hash calculation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir) / "file1.txt"
            file2 = Path(tmpdir) / "file2.txt"
            file1.write_text("content 1")
            file2.write_text("content 2")
            
            manager = SourceManager()
            
            hash1 = manager.calculate_hash([file1, file2])
            hash2 = manager.calculate_hash([file1, file2])
            
            assert hash1 == hash2
            assert len(hash1) == 16

    def test_calculate_hash_different_files(self):
        """Test hash is different for different files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir) / "file1.txt"
            file2 = Path(tmpdir) / "file2.txt"
            file1.write_text("content 1")
            file2.write_text("content 2")
            
            manager = SourceManager()
            
            hash1 = manager.calculate_hash([file1])
            hash2 = manager.calculate_hash([file2])
            
            assert hash1 != hash2

    def test_has_source_changed_new_source(self):
        """Test change detection for new source."""
        manager = SourceManager()
        
        result = manager.has_source_changed(Path("/new/source"))
        
        assert result is True

    def test_has_source_changed_indexed_source(self):
        """Test change detection for indexed source."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SourceManager(allowed_sources=[tmpdir])
            
            # Index the source
            (Path(tmpdir) / "test.txt").write_text("content")
            manager._indexed_sources[str(Path(tmpdir).resolve())] = SourceInfo(
                path=str(Path(tmpdir).resolve()),
                file_hash="oldhash",
            )
            
            result = manager.has_source_changed(Path(tmpdir))
            
            # Hash should be different
            assert result is True

    @pytest.mark.asyncio
    async def test_index_source_invalid(self):
        """Test indexing invalid source."""
        manager = SourceManager(allowed_sources=["/docs"])
        
        result = await manager.index_source(Path("/nonexistent"))
        
        assert result.success is False
        assert "validation failed" in result.error

    @pytest.mark.asyncio
    async def test_index_source_empty(self):
        """Test indexing empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SourceManager(allowed_sources=[tmpdir])
            
            result = await manager.index_source(Path(tmpdir))
            
            assert result.success is True
            assert result.document_count == 0

    @pytest.mark.asyncio
    async def test_index_source_with_files(self):
        """Test indexing directory with files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SourceManager(
                allowed_sources=[tmpdir],
                file_patterns=["*.txt"],
            )
            
            # Create test files
            (Path(tmpdir) / "file1.txt").write_text("content 1")
            (Path(tmpdir) / "file2.txt").write_text("content 2")
            
            result = await manager.index_source(Path(tmpdir))
            
            assert result.success is True
            assert result.document_count == 2
            assert result.chunk_count == 2

    @pytest.mark.asyncio
    async def test_index_source_with_metadata(self):
        """Test indexing with metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SourceManager(
                allowed_sources=[tmpdir],
                file_patterns=["*.txt"],
            )
            
            # Create a file so the source gets indexed
            (Path(tmpdir) / "test.txt").write_text("content")
            
            result = await manager.index_source(
                Path(tmpdir),
                metadata={"project": "test"},
            )
            
            assert result.success is True
            source_info = manager.get_source_info(Path(tmpdir))
            assert source_info is not None
            assert source_info.metadata == {"project": "test"}

    def test_get_indexed_sources_empty(self):
        """Test getting indexed sources when empty."""
        manager = SourceManager()
        
        sources = manager.get_indexed_sources()
        
        assert sources == []

    @pytest.mark.asyncio
    async def test_get_indexed_sources(self):
        """Test getting indexed sources."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SourceManager(allowed_sources=[tmpdir])
            
            (Path(tmpdir) / "test.txt").write_text("content")
            await manager.index_source(Path(tmpdir))
            
            sources = manager.get_indexed_sources()
            
            assert len(sources) == 1

    def test_get_source_info_not_found(self):
        """Test getting info for non-indexed source."""
        manager = SourceManager()
        
        info = manager.get_source_info(Path("/nonexistent"))
        
        assert info is None

    @pytest.mark.asyncio
    async def test_get_source_info(self):
        """Test getting source info."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SourceManager(allowed_sources=[tmpdir])
            
            (Path(tmpdir) / "test.txt").write_text("content")
            await manager.index_source(Path(tmpdir))
            
            info = manager.get_source_info(Path(tmpdir))
            
            assert info is not None
            assert info.file_count == 1

    def test_remove_source_not_found(self):
        """Test removing non-indexed source."""
        manager = SourceManager()
        
        result = manager.remove_source(Path("/nonexistent"))
        
        assert result is False

    @pytest.mark.asyncio
    async def test_remove_source(self):
        """Test removing indexed source."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SourceManager(allowed_sources=[tmpdir])
            
            (Path(tmpdir) / "test.txt").write_text("content")
            await manager.index_source(Path(tmpdir))
            
            result = manager.remove_source(Path(tmpdir))
            
            assert result is True
            assert len(manager.get_indexed_sources()) == 0

    def test_clear(self):
        """Test clearing all indexed sources."""
        manager = SourceManager()
        manager._indexed_sources["/path1"] = SourceInfo(path="/path1")
        manager._indexed_sources["/path2"] = SourceInfo(path="/path2")
        
        manager.clear()
        
        assert len(manager._indexed_sources) == 0

    def test_get_stats_empty(self):
        """Test getting stats when empty."""
        manager = SourceManager()
        
        stats = manager.get_stats()
        
        assert stats["indexed_source_count"] == 0
        assert stats["total_files"] == 0
        assert stats["total_size_bytes"] == 0

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test getting stats."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SourceManager(allowed_sources=[tmpdir])
            
            (Path(tmpdir) / "test.txt").write_text("content")
            await manager.index_source(Path(tmpdir))
            
            stats = manager.get_stats()
            
            assert stats["indexed_source_count"] == 1
            assert stats["total_files"] == 1
            assert stats["total_size_bytes"] > 0
            assert "total_size_mb" in stats


class TestCreateSourceManager:
    """Tests for create_source_manager factory function."""

    def test_create_defaults(self):
        """Test creating with default values."""
        manager = create_source_manager()
        
        assert isinstance(manager, SourceManager)
        assert len(manager.allowed_sources) == 3

    def test_create_custom(self):
        """Test creating with custom values."""
        manager = create_source_manager(
            allowed_sources=["/custom"],
            blocked_patterns=["**/secret/**"],
            file_patterns=["*.custom"],
        )
        
        assert manager.allowed_sources == ["/custom"]
        assert manager.blocked_patterns == ["**/secret/**"]
        assert manager.file_patterns == ["*.custom"]
