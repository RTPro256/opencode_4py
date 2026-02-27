"""
Tests for Checkpoint System.
"""

import pytest
from pathlib import Path
from datetime import datetime
import tempfile
import json
import os

from opencode.core.context.checkpoints import (
    CheckpointMetadata,
    Checkpoint,
    CheckpointManager,
)


class TestCheckpointMetadata:
    """Tests for CheckpointMetadata dataclass."""

    def test_creation(self):
        """Test CheckpointMetadata instantiation."""
        created_at = datetime.utcnow()
        metadata = CheckpointMetadata(
            checkpoint_id="test-123",
            created_at=created_at,
            description="Test checkpoint",
            tags=["test", "unit"],
            size_bytes=1024,
        )
        
        assert metadata.checkpoint_id == "test-123"
        assert metadata.created_at == created_at
        assert metadata.description == "Test checkpoint"
        assert metadata.tags == ["test", "unit"]
        assert metadata.size_bytes == 1024

    def test_defaults(self):
        """Test CheckpointMetadata default values."""
        metadata = CheckpointMetadata(
            checkpoint_id="test",
            created_at=datetime.utcnow(),
            description="test",
        )
        
        assert metadata.tags == []
        assert metadata.size_bytes == 0

    def test_to_dict(self):
        """Test CheckpointMetadata.to_dict()."""
        created_at = datetime.utcnow()
        metadata = CheckpointMetadata(
            checkpoint_id="test-456",
            created_at=created_at,
            description="Test",
            tags=["a", "b"],
            size_bytes=2048,
        )
        
        result = metadata.to_dict()
        
        assert result["checkpoint_id"] == "test-456"
        assert result["created_at"] == created_at.isoformat()
        assert result["description"] == "Test"
        assert result["tags"] == ["a", "b"]
        assert result["size_bytes"] == 2048

    def test_from_dict(self):
        """Test CheckpointMetadata.from_dict()."""
        created_at = datetime.utcnow()
        data = {
            "checkpoint_id": "from-dict",
            "created_at": created_at.isoformat(),
            "description": "From dict test",
            "tags": ["x", "y", "z"],
            "size_bytes": 4096,
        }
        
        metadata = CheckpointMetadata.from_dict(data)
        
        assert metadata.checkpoint_id == "from-dict"
        assert metadata.created_at.isoformat() == created_at.isoformat()
        assert metadata.description == "From dict test"
        assert metadata.tags == ["x", "y", "z"]
        assert metadata.size_bytes == 4096

    def test_from_dict_defaults(self):
        """Test from_dict with missing optional fields."""
        created_at = datetime.utcnow()
        data = {
            "checkpoint_id": "minimal",
            "created_at": created_at.isoformat(),
            "description": "Minimal",
        }
        
        metadata = CheckpointMetadata.from_dict(data)
        
        assert metadata.tags == []
        assert metadata.size_bytes == 0


class TestCheckpoint:
    """Tests for Checkpoint dataclass."""

    def test_creation(self):
        """Test Checkpoint instantiation."""
        metadata = CheckpointMetadata(
            checkpoint_id="test",
            created_at=datetime.utcnow(),
            description="test",
        )
        state = {"messages": ["msg1", "msg2"], "context": {"key": "value"}}
        
        checkpoint = Checkpoint(metadata=metadata, state=state)
        
        assert checkpoint.metadata == metadata
        assert checkpoint.state == state

    def test_to_dict(self):
        """Test Checkpoint.to_dict()."""
        metadata = CheckpointMetadata(
            checkpoint_id="test-789",
            created_at=datetime.utcnow(),
            description="Test checkpoint",
            tags=["test"],
        )
        state = {"messages": ["a", "b"], "count": 42}
        
        checkpoint = Checkpoint(metadata=metadata, state=state)
        result = checkpoint.to_dict()
        
        assert "metadata" in result
        assert "state" in result
        assert result["metadata"]["checkpoint_id"] == "test-789"
        assert result["state"]["messages"] == ["a", "b"]
        assert result["state"]["count"] == 42

    def test_from_dict(self):
        """Test Checkpoint.from_dict()."""
        created_at = datetime.utcnow()
        data = {
            "metadata": {
                "checkpoint_id": "from-dict-cp",
                "created_at": created_at.isoformat(),
                "description": "From dict",
                "tags": ["imported"],
                "size_bytes": 512,
            },
            "state": {
                "messages": ["imported message"],
                "context": {"imported": True},
            },
        }
        
        checkpoint = Checkpoint.from_dict(data)
        
        assert checkpoint.metadata.checkpoint_id == "from-dict-cp"
        assert checkpoint.metadata.description == "From dict"
        assert checkpoint.state["messages"] == ["imported message"]
        assert checkpoint.state["context"]["imported"] is True


class TestCheckpointManager:
    """Tests for CheckpointManager class."""

    def test_init(self):
        """Test CheckpointManager initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(
                storage_dir=tmpdir,
                max_checkpoints=50,
                auto_cleanup=False,
            )
            
            assert manager.storage_dir == Path(tmpdir)
            assert manager.max_checkpoints == 50
            assert manager.auto_cleanup is False
            assert manager._index == {}

    def test_init_creates_directory(self):
        """Test that init creates storage directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "checkpoints" / "nested"
            manager = CheckpointManager(storage_dir=str(storage_path))
            
            assert storage_path.exists()

    def test_create_checkpoint(self):
        """Test creating a checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(storage_dir=tmpdir, auto_cleanup=False)
            
            state = {"messages": ["test"], "context": {"key": "value"}}
            checkpoint_id = manager.create(
                state=state,
                description="Test checkpoint",
                tags=["test"],
            )
            
            assert checkpoint_id is not None
            assert len(checkpoint_id) == 8  # UUID[:8]
            assert checkpoint_id in manager._index

    def test_create_and_load_checkpoint(self):
        """Test creating and loading a checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(storage_dir=tmpdir, auto_cleanup=False)
            
            state = {
                "messages": ["msg1", "msg2"],
                "context": {"user": "test", "session": "abc"},
            }
            checkpoint_id = manager.create(
                state=state,
                description="Full test checkpoint",
                tags=["important", "test"],
            )
            
            # Load the checkpoint
            checkpoint = manager.load(checkpoint_id)
            
            assert checkpoint.metadata.checkpoint_id == checkpoint_id
            assert checkpoint.metadata.description == "Full test checkpoint"
            assert checkpoint.metadata.tags == ["important", "test"]
            assert checkpoint.state["messages"] == ["msg1", "msg2"]
            assert checkpoint.state["context"]["user"] == "test"

    def test_load_nonexistent_checkpoint(self):
        """Test loading a non-existent checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(storage_dir=tmpdir)
            
            with pytest.raises(FileNotFoundError):
                manager.load("nonexistent-id")

    def test_delete_checkpoint(self):
        """Test deleting a checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(storage_dir=tmpdir, auto_cleanup=False)
            
            state = {"data": "test"}
            checkpoint_id = manager.create(state=state, description="To delete")
            
            assert checkpoint_id in manager._index
            
            result = manager.delete(checkpoint_id)
            
            assert result is True
            assert checkpoint_id not in manager._index
            
            # File should be deleted
            checkpoint_path = manager._get_checkpoint_path(checkpoint_id)
            assert not checkpoint_path.exists()

    def test_delete_nonexistent_checkpoint(self):
        """Test deleting a non-existent checkpoint returns True (idempotent)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(storage_dir=tmpdir)
            
            # Delete is idempotent - returns True even if checkpoint doesn't exist
            result = manager.delete("nonexistent-id")
            
            assert result is True

    def test_list_checkpoints(self):
        """Test listing checkpoints."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(storage_dir=tmpdir, auto_cleanup=False)
            
            # Create multiple checkpoints
            id1 = manager.create({"data": 1}, description="First")
            id2 = manager.create({"data": 2}, description="Second")
            id3 = manager.create({"data": 3}, description="Third")
            
            checkpoints = manager.list()
            
            assert len(checkpoints) == 3
            ids = [c.checkpoint_id for c in checkpoints]
            assert id1 in ids
            assert id2 in ids
            assert id3 in ids

    def test_list_checkpoints_empty(self):
        """Test listing checkpoints when none exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(storage_dir=tmpdir)
            
            checkpoints = manager.list()
            
            assert checkpoints == []

    def test_list_checkpoints_by_tag(self):
        """Test listing checkpoints filtered by tag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(storage_dir=tmpdir, auto_cleanup=False)
            
            id1 = manager.create({"data": 1}, description="One", tags=["important"])
            id2 = manager.create({"data": 2}, description="Two", tags=["test"])
            id3 = manager.create({"data": 3}, description="Three", tags=["important", "test"])
            
            important = manager.list(tags=["important"])
            
            assert len(important) == 2
            ids = [c.checkpoint_id for c in important]
            assert id1 in ids
            assert id3 in ids
            assert id2 not in ids

    def test_get_latest_checkpoint(self):
        """Test getting the latest checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(storage_dir=tmpdir, auto_cleanup=False)
            
            # Create checkpoints with slight delay
            id1 = manager.create({"data": 1}, description="First")
            id2 = manager.create({"data": 2}, description="Second")
            id3 = manager.create({"data": 3}, description="Third")
            
            latest = manager.get_latest()
            
            assert latest is not None
            assert latest.metadata.checkpoint_id == id3

    def test_get_latest_no_checkpoints(self):
        """Test getting latest when no checkpoints exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(storage_dir=tmpdir)
            
            latest = manager.get_latest()
            
            assert latest is None

    def test_get_checkpoint_metadata(self):
        """Test getting checkpoint metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(storage_dir=tmpdir, auto_cleanup=False)
            
            checkpoint_id = manager.create(
                {"data": "test"},
                description="Metadata test",
                tags=["meta"],
            )
            
            # Get metadata from index
            metadata = manager._index.get(checkpoint_id)
            
            assert metadata is not None
            assert metadata.checkpoint_id == checkpoint_id
            assert metadata.description == "Metadata test"
            assert metadata.tags == ["meta"]

    def test_get_nonexistent_metadata(self):
        """Test getting metadata for non-existent checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(storage_dir=tmpdir)
            
            metadata = manager._index.get("nonexistent")
            
            assert metadata is None

    def test_auto_cleanup(self):
        """Test auto cleanup of old checkpoints."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(
                storage_dir=tmpdir,
                max_checkpoints=3,
                auto_cleanup=True,
            )
            
            # Create more checkpoints than max
            id1 = manager.create({"data": 1}, description="First")
            id2 = manager.create({"data": 2}, description="Second")
            id3 = manager.create({"data": 3}, description="Third")
            id4 = manager.create({"data": 4}, description="Fourth")
            
            # Should only have 3 checkpoints
            checkpoints = manager.list()
            assert len(checkpoints) == 3
            
            # First checkpoint should be deleted
            assert id1 not in [c.checkpoint_id for c in checkpoints]
            assert id4 in [c.checkpoint_id for c in checkpoints]

    def test_clear_all(self):
        """Test clearing all checkpoints."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(storage_dir=tmpdir, auto_cleanup=False)
            
            manager.create({"data": 1}, description="One")
            manager.create({"data": 2}, description="Two")
            manager.create({"data": 3}, description="Three")
            
            assert len(manager.list()) == 3
            
            manager.clear_all()
            
            assert len(manager.list()) == 0
            assert manager._index == {}

    def test_persistence(self):
        """Test that checkpoints persist across manager instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create manager and checkpoint
            manager1 = CheckpointManager(storage_dir=tmpdir, auto_cleanup=False)
            checkpoint_id = manager1.create(
                {"data": "persistent"},
                description="Persistent checkpoint",
            )
            
            # Create new manager instance
            manager2 = CheckpointManager(storage_dir=tmpdir, auto_cleanup=False)
            
            # Should be able to load the checkpoint
            checkpoint = manager2.load(checkpoint_id)
            assert checkpoint.state["data"] == "persistent"

    def test_index_persistence(self):
        """Test that index persists across manager instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create manager and checkpoints
            manager1 = CheckpointManager(storage_dir=tmpdir, auto_cleanup=False)
            id1 = manager1.create({"data": 1}, description="One", tags=["a"])
            id2 = manager1.create({"data": 2}, description="Two", tags=["b"])
            
            # Create new manager instance
            manager2 = CheckpointManager(storage_dir=tmpdir, auto_cleanup=False)
            
            # Index should be loaded
            assert id1 in manager2._index
            assert id2 in manager2._index
            assert manager2._index[id1].description == "One"
            assert manager2._index[id2].tags == ["b"]

    def test_restore_state(self):
        """Test restoring state from checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(storage_dir=tmpdir, auto_cleanup=False)
            
            original_state = {
                "messages": [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi!"},
                ],
                "context": {
                    "working_directory": "/home/user",
                    "session_id": "abc123",
                },
                "counters": {
                    "turns": 5,
                    "tokens": 1000,
                },
            }
            
            checkpoint_id = manager.create(
                state=original_state,
                description="State to restore",
            )
            
            # Simulate modifying state
            modified_state = original_state.copy()
            modified_state["counters"]["turns"] = 10
            
            # Restore from checkpoint
            checkpoint = manager.load(checkpoint_id)
            restored_state = checkpoint.state
            
            # Should have original values
            assert restored_state["counters"]["turns"] == 5
            assert restored_state["context"]["session_id"] == "abc123"

    def test_size_tracking(self):
        """Test that checkpoint size is tracked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(storage_dir=tmpdir, auto_cleanup=False)
            
            # Create checkpoint with larger state
            large_state = {"data": "x" * 10000}
            checkpoint_id = manager.create(state=large_state, description="Large")
            
            metadata = manager._index.get(checkpoint_id)
            
            assert metadata.size_bytes > 0
            assert metadata.size_bytes > 10000  # Should be larger than the data

    def test_get_checkpoint_path(self):
        """Test checkpoint path generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(storage_dir=tmpdir)
            
            path = manager._get_checkpoint_path("abc123")
            
            assert path == Path(tmpdir) / "abc123.json"