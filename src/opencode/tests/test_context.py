"""
Tests for Context Management Module
"""

import pytest
from datetime import datetime

from opencode.core.context.tracker import ContextTracker, FileContext
from opencode.core.context.truncation import (
    ContextTruncation,
    ContextItem,
    TruncationStrategy,
)
from opencode.core.context.mentions import MentionProcessor, MentionType
from opencode.core.context.checkpoints import CheckpointManager, Checkpoint


class TestContextTracker:
    """Tests for ContextTracker."""
    
    def test_add_file(self):
        """Test adding a file to context."""
        tracker = ContextTracker()
        tracker.add_file("main.py", "read", 1000)
        
        assert len(tracker.get_all_files()) == 1
        assert tracker.get_file("main.py") is not None
        assert tracker.get_file("main.py").tokens == 1000
    
    def test_update_file(self):
        """Test updating a file in context."""
        tracker = ContextTracker()
        tracker.add_file("main.py", "read", 1000)
        tracker.add_file("main.py", "modified", 1500)
        
        file_ctx = tracker.get_file("main.py")
        assert file_ctx.access_type == "modified"
        assert file_ctx.tokens == 1500
        assert file_ctx.access_count == 2
    
    def test_remove_file(self):
        """Test removing a file from context."""
        tracker = ContextTracker()
        tracker.add_file("main.py", "read", 1000)
        
        assert tracker.remove_file("main.py") is True
        assert tracker.get_file("main.py") is None
        assert tracker.remove_file("nonexistent.py") is False
    
    def test_context_summary(self):
        """Test context summary generation."""
        tracker = ContextTracker()
        tracker.add_file("main.py", "read", 1000)
        tracker.add_file("config.py", "modified", 500)
        
        summary = tracker.get_context_summary()
        assert "2 files" in summary
        assert "1,500" in summary
    
    def test_capacity_tracking(self):
        """Test capacity tracking."""
        tracker = ContextTracker(max_context_tokens=1000)
        tracker.add_file("main.py", "read", 800)
        
        assert tracker.is_over_capacity() is False
        assert tracker.get_capacity_percent() == 80.0
        
        tracker.add_file("config.py", "read", 300)
        assert tracker.is_over_capacity() is True
    
    def test_eviction(self):
        """Test file eviction logic."""
        tracker = ContextTracker(max_context_tokens=1000)
        tracker.add_file("old.py", "read", 500)
        tracker.add_file("new.py", "read", 600)
        
        to_evict = tracker.get_files_to_evict(400)
        assert len(to_evict) > 0
    
    def test_serialization(self):
        """Test serialization and deserialization."""
        tracker = ContextTracker()
        tracker.add_file("main.py", "read", 1000)
        
        data = tracker.to_dict()
        restored = ContextTracker.from_dict(data)
        
        assert len(restored.get_all_files()) == 1
        assert restored.get_file("main.py").tokens == 1000


class TestContextTruncation:
    """Tests for ContextTruncation."""
    
    def test_no_truncation_needed(self):
        """Test when no truncation is needed."""
        truncation = ContextTruncation(max_tokens=1000)
        
        items = [
            ContextItem(id="1", content="Hello", tokens=10),
            ContextItem(id="2", content="World", tokens=10),
        ]
        
        result = truncation.truncate(items)
        assert len(result.kept_items) == 2
        assert len(result.removed_items) == 0
    
    def test_oldest_first_truncation(self):
        """Test oldest-first truncation strategy."""
        truncation = ContextTruncation(
            max_tokens=20,
            default_strategy=TruncationStrategy.OLDEST_FIRST,
        )
        
        items = [
            ContextItem(id="1", content="First", tokens=10, age=5),
            ContextItem(id="2", content="Second", tokens=10, age=3),
            ContextItem(id="3", content="Third", tokens=10, age=1),
        ]
        
        result = truncation.truncate(items)
        assert len(result.kept_items) == 2
        assert "1" in result.removed_items  # Oldest removed
    
    def test_priority_truncation(self):
        """Test priority-based truncation."""
        truncation = ContextTruncation(
            max_tokens=20,
            default_strategy=TruncationStrategy.PRIORITY,
        )
        
        items = [
            ContextItem(id="1", content="Low", tokens=10, priority=1),
            ContextItem(id="2", content="High", tokens=10, priority=10),
            ContextItem(id="3", content="Medium", tokens=10, priority=5),
        ]
        
        result = truncation.truncate(items)
        assert "2" in result.kept_items  # High priority kept
    
    def test_smart_truncation(self):
        """Test smart truncation strategy."""
        truncation = ContextTruncation(
            max_tokens=30,
            default_strategy=TruncationStrategy.SMART,
        )
        
        items = [
            ContextItem(id="1", content="System", tokens=10, priority=100, item_type="system"),
            ContextItem(id="2", content="Recent", tokens=10, priority=1, age=0),
            ContextItem(id="3", content="Old", tokens=10, priority=1, age=10),
            ContextItem(id="4", content="Older", tokens=10, priority=1, age=20),
        ]
        
        result = truncation.truncate(items)
        # System message and recent should be kept
        assert "1" in result.kept_items
        assert "2" in result.kept_items


class TestMentionProcessor:
    """Tests for MentionProcessor."""
    
    def test_file_mention(self):
        """Test file mention extraction."""
        processor = MentionProcessor()
        result = processor.process("Read @file:main.py and check it")
        
        assert len(result.file_mentions) == 1
        assert result.file_mentions[0].value == "main.py"
    
    def test_directory_mention(self):
        """Test directory mention extraction."""
        processor = MentionProcessor()
        result = processor.process("Check @dir:src/components")
        
        assert len(result.directory_mentions) == 1
        assert result.directory_mentions[0].value == "src/components"
    
    def test_tool_mention(self):
        """Test tool mention extraction."""
        processor = MentionProcessor()
        result = processor.process("Use @tool:bash to run commands")
        
        assert len(result.tool_mentions) == 1
        assert result.tool_mentions[0].value == "bash"
    
    def test_mode_mention(self):
        """Test mode mention extraction."""
        processor = MentionProcessor()
        result = processor.process("Switch to @mode:architect")
        
        assert len(result.mode_mentions) == 1
        assert result.mode_mentions[0].value == "architect"
    
    def test_multiple_mentions(self):
        """Test multiple mentions in one text."""
        processor = MentionProcessor()
        result = processor.process("Read @file:main.py and @file:config.py")
        
        assert len(result.file_mentions) == 2
    
    def test_person_mention(self):
        """Test generic person mention."""
        processor = MentionProcessor()
        result = processor.process("Ask @john for help")
        
        mentions = [m for m in result.mentions if m.mention_type == MentionType.PERSON]
        assert len(mentions) == 1
        assert mentions[0].value == "john"
    
    def test_file_resolution(self, tmp_path):
        """Test file path resolution."""
        # Create a temp file
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")
        
        processor = MentionProcessor(workspace_root=str(tmp_path))
        result = processor.process("@file:test.py")
        
        assert len(result.file_mentions) == 1
        assert result.file_mentions[0].resolved is True
    
    def test_mention_summary(self):
        """Test mention summary generation."""
        processor = MentionProcessor()
        summary = processor.get_mention_summary("Read @file:main.py and @dir:src")
        
        assert "file" in summary
        assert "directory" in summary


class TestCheckpointManager:
    """Tests for CheckpointManager."""
    
    def test_create_checkpoint(self, tmp_path):
        """Test creating a checkpoint."""
        manager = CheckpointManager(storage_dir=str(tmp_path / "checkpoints"))
        
        state = {"messages": ["hello"], "context": {}}
        checkpoint_id = manager.create(state, "Test checkpoint")
        
        assert checkpoint_id is not None
        assert len(manager.list()) == 1
    
    def test_load_checkpoint(self, tmp_path):
        """Test loading a checkpoint."""
        manager = CheckpointManager(storage_dir=str(tmp_path / "checkpoints"))
        
        state = {"messages": ["hello"], "count": 42}
        checkpoint_id = manager.create(state, "Test checkpoint")
        
        loaded = manager.load(checkpoint_id)
        assert loaded.state["messages"] == ["hello"]
        assert loaded.state["count"] == 42
    
    def test_delete_checkpoint(self, tmp_path):
        """Test deleting a checkpoint."""
        manager = CheckpointManager(storage_dir=str(tmp_path / "checkpoints"))
        
        state = {"messages": []}
        checkpoint_id = manager.create(state, "Test")
        
        assert manager.delete(checkpoint_id) is True
        assert len(manager.list()) == 0
    
    def test_list_checkpoints(self, tmp_path):
        """Test listing checkpoints."""
        manager = CheckpointManager(storage_dir=str(tmp_path / "checkpoints"))
        
        manager.create({"id": 1}, "First")
        manager.create({"id": 2}, "Second")
        manager.create({"id": 3}, "Third")
        
        checkpoints = manager.list()
        assert len(checkpoints) == 3
    
    def test_checkpoint_tags(self, tmp_path):
        """Test checkpoint tagging."""
        manager = CheckpointManager(storage_dir=str(tmp_path / "checkpoints"))
        
        manager.create({"id": 1}, "Important", tags=["important", "pre-refactor"])
        manager.create({"id": 2}, "Normal", tags=["auto"])
        
        important = manager.list(tags=["important"])
        assert len(important) == 1
    
    def test_max_checkpoints(self, tmp_path):
        """Test max checkpoints limit."""
        manager = CheckpointManager(
            storage_dir=str(tmp_path / "checkpoints"),
            max_checkpoints=3,
            auto_cleanup=True,
        )
        
        for i in range(5):
            manager.create({"id": i}, f"Checkpoint {i}")
        
        # Should only have 3 (oldest removed)
        assert len(manager.list()) == 3
    
    def test_get_latest(self, tmp_path):
        """Test getting latest checkpoint."""
        manager = CheckpointManager(storage_dir=str(tmp_path / "checkpoints"))
        
        manager.create({"id": 1}, "First")
        manager.create({"id": 2}, "Second")
        
        latest = manager.get_latest()
        assert latest.state["id"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
