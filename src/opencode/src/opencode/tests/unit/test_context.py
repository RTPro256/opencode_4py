"""
Unit tests for context tracking functionality.

Tests for ContextTracker, FileContext, and related context management.
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path

from opencode.core.context.tracker import ContextTracker, FileContext


class TestFileContext:
    """Tests for FileContext dataclass."""
    
    def test_file_context_creation(self):
        """Test creating a FileContext instance."""
        ctx = FileContext(
            path="test.py",
            access_type="read",
            tokens=100,
            content_preview="def hello():",
        )
        
        assert ctx.path == "test.py"
        assert ctx.access_type == "read"
        assert ctx.tokens == 100
        assert ctx.content_preview == "def hello():"
        assert ctx.access_count == 1
    
    def test_file_context_to_dict(self):
        """Test serializing FileContext to dictionary."""
        ctx = FileContext(
            path="test.py",
            access_type="modified",
            tokens=200,
            content_preview="# test file",
        )
        
        data = ctx.to_dict()
        
        assert data["path"] == "test.py"
        assert data["access_type"] == "modified"
        assert data["tokens"] == 200
        assert data["content_preview"] == "# test file"
        assert "last_accessed" in data
        assert data["access_count"] == 1
    
    def test_file_context_from_dict(self):
        """Test deserializing FileContext from dictionary."""
        data = {
            "path": "config.py",
            "access_type": "created",
            "tokens": 50,
            "content_preview": "# config",
            "last_accessed": "2024-01-01T12:00:00",
            "access_count": 3,
        }
        
        ctx = FileContext.from_dict(data)
        
        assert ctx.path == "config.py"
        assert ctx.access_type == "created"
        assert ctx.tokens == 50
        assert ctx.content_preview == "# config"
        assert ctx.access_count == 3
    
    def test_file_context_default_values(self):
        """Test default values for FileContext."""
        ctx = FileContext(
            path="test.py",
            access_type="read",
            tokens=100,
        )
        
        assert ctx.content_preview is None
        assert ctx.last_accessed is not None
        assert ctx.access_count == 1


class TestContextTracker:
    """Tests for ContextTracker class."""
    
    def test_tracker_initialization(self):
        """Test ContextTracker initialization."""
        tracker = ContextTracker()
        
        assert tracker._max_context_tokens == 100000
        assert tracker._current_tokens == 0
        assert len(tracker._files) == 0
    
    def test_tracker_custom_max_tokens(self):
        """Test ContextTracker with custom max tokens."""
        tracker = ContextTracker(max_context_tokens=50000)
        
        assert tracker._max_context_tokens == 50000
    
    def test_add_file(self):
        """Test adding a file to context."""
        tracker = ContextTracker()
        
        tracker.add_file(
            path="main.py",
            access_type="read",
            tokens=500,
            content_preview="def main():",
        )
        
        assert "main.py" in tracker._files
        assert tracker._current_tokens == 500
    
    def test_add_multiple_files(self):
        """Test adding multiple files."""
        tracker = ContextTracker()
        
        tracker.add_file("file1.py", "read", 100)
        tracker.add_file("file2.py", "read", 200)
        tracker.add_file("file3.py", "modified", 150)
        
        assert len(tracker._files) == 3
        assert tracker._current_tokens == 450
    
    def test_update_existing_file(self):
        """Test updating an existing file increases access count."""
        tracker = ContextTracker()
        
        tracker.add_file("test.py", "read", 100)
        tracker.add_file("test.py", "modified", 150)
        
        assert len(tracker._files) == 1
        assert tracker._files["test.py"].access_count == 2
        assert tracker._files["test.py"].access_type == "modified"
    
    def test_remove_file(self):
        """Test removing a file from context."""
        tracker = ContextTracker()
        
        tracker.add_file("test.py", "read", 100)
        result = tracker.remove_file("test.py")
        
        assert result is True
        assert "test.py" not in tracker._files
        assert tracker._current_tokens == 0
    
    def test_remove_nonexistent_file(self):
        """Test removing a file that doesn't exist."""
        tracker = ContextTracker()
        
        result = tracker.remove_file("nonexistent.py")
        
        assert result is False
        assert tracker._current_tokens == 0
    
    def test_get_file(self):
        """Test getting a file from context."""
        tracker = ContextTracker()
        
        tracker.add_file("test.py", "read", 100, "content")
        
        file_ctx = tracker.get_file("test.py")
        
        assert file_ctx is not None
        assert file_ctx.path == "test.py"
        assert file_ctx.tokens == 100
    
    def test_get_nonexistent_file(self):
        """Test getting a file that doesn't exist."""
        tracker = ContextTracker()
        
        file_ctx = tracker.get_file("nonexistent.py")
        
        assert file_ctx is None
    
    def test_get_all_files(self):
        """Test getting all files from context."""
        tracker = ContextTracker()
        
        tracker.add_file("file1.py", "read", 100)
        tracker.add_file("file2.py", "read", 200)
        
        files = tracker.get_all_files()
        
        assert len(files) == 2
        assert "file1.py" in files
        assert "file2.py" in files
    
    def test_get_context_summary(self):
        """Test getting context summary."""
        tracker = ContextTracker()
        
        tracker.add_file("file1.py", "read", 100)
        tracker.add_file("file2.py", "modified", 200)
        
        summary = tracker.get_context_summary()
        
        # get_context_summary returns a string
        assert isinstance(summary, str)
        assert "2 files" in summary
        assert "300" in summary  # total tokens
    
    def test_clear_context(self):
        """Test clearing all context."""
        tracker = ContextTracker()
        
        tracker.add_file("file1.py", "read", 100)
        tracker.add_file("file2.py", "read", 200)
        
        tracker.clear()
        
        assert len(tracker._files) == 0
        assert tracker._current_tokens == 0
    
    def test_get_capacity_percent(self):
        """Test getting capacity percentage."""
        tracker = ContextTracker(max_context_tokens=1000)
        
        tracker.add_file("file1.py", "read", 250)
        
        percent = tracker.get_capacity_percent()
        
        assert percent == 25.0
    
    def test_is_over_capacity(self):
        """Test checking if over capacity."""
        tracker = ContextTracker(max_context_tokens=500)
        
        tracker.add_file("file1.py", "read", 300)
        assert tracker.is_over_capacity() is False
        
        tracker.add_file("file2.py", "read", 300)
        assert tracker.is_over_capacity() is True
    
    def test_get_files_to_evict(self):
        """Test getting files to evict."""
        tracker = ContextTracker(max_context_tokens=1000)
        
        tracker.add_file("file1.py", "read", 300)
        tracker.add_file("file2.py", "modified", 200)
        tracker.add_file("file3.py", "read", 400)
        
        # Request to free 300 tokens
        to_evict = tracker.get_files_to_evict(target_tokens=300)
        
        # Should not evict modified files
        assert "file2.py" not in to_evict
        # Should evict read files
        assert len(to_evict) > 0
    
    def test_token_limit_warning(self):
        """Test behavior when approaching token limit."""
        tracker = ContextTracker(max_context_tokens=500)
        
        tracker.add_file("file1.py", "read", 300)
        tracker.add_file("file2.py", "read", 300)
        
        # Should still add but may trigger warning
        assert tracker._current_tokens == 600


class TestContextTrackerSerialization:
    """Tests for ContextTracker serialization."""
    
    def test_to_dict(self):
        """Test serializing ContextTracker to dictionary."""
        tracker = ContextTracker()
        
        tracker.add_file("file1.py", "read", 100)
        tracker.add_file("file2.py", "modified", 200)
        
        data = tracker.to_dict()
        
        assert data["max_context_tokens"] == 100000
        assert data["current_tokens"] == 300
        assert "files" in data
        assert len(data["files"]) == 2
    
    def test_from_dict(self):
        """Test deserializing ContextTracker from dictionary."""
        data = {
            "max_context_tokens": 50000,
            "current_tokens": 300,
            "files": {
                "test.py": {
                    "path": "test.py",
                    "access_type": "read",
                    "tokens": 100,
                    "content_preview": "# test",
                    "last_accessed": "2024-01-01T12:00:00",
                    "access_count": 1,
                }
            },
        }
        
        tracker = ContextTracker.from_dict(data)
        
        assert tracker._max_context_tokens == 50000
        assert tracker._current_tokens == 300
        assert len(tracker._files) == 1
    
    def test_round_trip_serialization(self):
        """Test that serialization and deserialization preserves data."""
        tracker1 = ContextTracker(max_context_tokens=75000)
        
        tracker1.add_file("file1.py", "read", 100, "content1")
        tracker1.add_file("file2.py", "modified", 200, "content2")
        
        data = tracker1.to_dict()
        tracker2 = ContextTracker.from_dict(data)
        
        assert tracker2._max_context_tokens == tracker1._max_context_tokens
        assert len(tracker2._files) == len(tracker1._files)


class TestContextTrackerEdgeCases:
    """Edge case tests for ContextTracker."""
    
    def test_empty_path(self):
        """Test handling empty path."""
        tracker = ContextTracker()
        
        tracker.add_file("", "read", 100)
        
        assert "" in tracker._files
    
    def test_unicode_path(self):
        """Test handling unicode paths."""
        tracker = ContextTracker()
        
        tracker.add_file("日本語/テスト.py", "read", 100)
        
        assert "日本語/テスト.py" in tracker._files
    
    def test_very_long_path(self):
        """Test handling very long paths."""
        tracker = ContextTracker()
        
        long_path = "a" * 1000 + ".py"
        tracker.add_file(long_path, "read", 100)
        
        assert long_path in tracker._files
    
    def test_zero_tokens(self):
        """Test handling zero token count."""
        tracker = ContextTracker()
        
        tracker.add_file("empty.py", "read", 0)
        
        assert tracker._current_tokens == 0
        assert "empty.py" in tracker._files
    
    def test_special_characters_in_content_preview(self):
        """Test handling special characters in content preview."""
        tracker = ContextTracker()
        
        special_content = "def test():\n\tprint('\"special\" \\ chars')"
        tracker.add_file("test.py", "read", 100, special_content)
        
        assert tracker._files["test.py"].content_preview == special_content
    
    def test_empty_context_summary(self):
        """Test summary when context is empty."""
        tracker = ContextTracker()
        
        summary = tracker.get_context_summary()
        
        assert "No files" in summary
    
    def test_evict_when_under_capacity(self):
        """Test eviction when already under target."""
        tracker = ContextTracker()
        
        tracker.add_file("file1.py", "read", 100)
        
        to_evict = tracker.get_files_to_evict(target_tokens=500)
        
        assert len(to_evict) == 0
