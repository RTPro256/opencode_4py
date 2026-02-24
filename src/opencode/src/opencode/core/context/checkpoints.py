"""
Checkpoint System

Provides checkpoint/restore functionality for session state.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar, Generic

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class CheckpointMetadata:
    """Metadata for a checkpoint."""
    checkpoint_id: str
    created_at: datetime
    description: str
    tags: List[str] = field(default_factory=list)
    size_bytes: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "checkpoint_id": self.checkpoint_id,
            "created_at": self.created_at.isoformat(),
            "description": self.description,
            "tags": self.tags,
            "size_bytes": self.size_bytes,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CheckpointMetadata":
        """Create from dictionary."""
        return cls(
            checkpoint_id=data["checkpoint_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            description=data["description"],
            tags=data.get("tags", []),
            size_bytes=data.get("size_bytes", 0),
        )


@dataclass
class Checkpoint:
    """A complete checkpoint of session state."""
    metadata: CheckpointMetadata
    state: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metadata": self.metadata.to_dict(),
            "state": self.state,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Checkpoint":
        """Create from dictionary."""
        return cls(
            metadata=CheckpointMetadata.from_dict(data["metadata"]),
            state=data["state"],
        )


class CheckpointManager:
    """
    Manages checkpoints for session state.
    
    Provides functionality to:
    - Create checkpoints
    - Restore from checkpoints
    - List available checkpoints
    - Delete checkpoints
    
    Example:
        manager = CheckpointManager(storage_dir=".checkpoints")
        
        # Create checkpoint
        checkpoint_id = manager.create(
            state={"messages": [...], "context": {...}},
            description="Before refactoring",
            tags=["important", "pre-refactor"],
        )
        
        # Restore checkpoint
        checkpoint = manager.load(checkpoint_id)
        state = checkpoint.state
    """
    
    def __init__(
        self,
        storage_dir: str = ".checkpoints",
        max_checkpoints: int = 100,
        auto_cleanup: bool = True,
    ):
        """
        Initialize checkpoint manager.
        
        Args:
            storage_dir: Directory to store checkpoints
            max_checkpoints: Maximum number of checkpoints to keep
            auto_cleanup: Whether to auto-cleanup old checkpoints
        """
        self.storage_dir = Path(storage_dir)
        self.max_checkpoints = max_checkpoints
        self.auto_cleanup = auto_cleanup
        
        # Create storage directory
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Index file for metadata
        self.index_file = self.storage_dir / "index.json"
        self._index: Dict[str, CheckpointMetadata] = {}
        self._load_index()
    
    def _load_index(self) -> None:
        """Load checkpoint index from disk."""
        if self.index_file.exists():
            try:
                with open(self.index_file, "r") as f:
                    data = json.load(f)
                    self._index = {
                        k: CheckpointMetadata.from_dict(v)
                        for k, v in data.items()
                    }
            except Exception as e:
                logger.warning(f"Failed to load checkpoint index: {e}")
                self._index = {}
    
    def _save_index(self) -> None:
        """Save checkpoint index to disk."""
        try:
            with open(self.index_file, "w") as f:
                json.dump(
                    {k: v.to_dict() for k, v in self._index.items()},
                    f,
                    indent=2,
                )
        except Exception as e:
            logger.error(f"Failed to save checkpoint index: {e}")
    
    def _get_checkpoint_path(self, checkpoint_id: str) -> Path:
        """Get path for a checkpoint file."""
        return self.storage_dir / f"{checkpoint_id}.json"
    
    def create(
        self,
        state: Dict[str, Any],
        description: str = "",
        tags: Optional[List[str]] = None,
    ) -> str:
        """
        Create a new checkpoint.
        
        Args:
            state: State to checkpoint
            description: Description of the checkpoint
            tags: Optional tags for categorization
            
        Returns:
            Checkpoint ID
        """
        import uuid
        
        checkpoint_id = str(uuid.uuid4())[:8]
        created_at = datetime.utcnow()
        
        # Create checkpoint
        checkpoint = Checkpoint(
            metadata=CheckpointMetadata(
                checkpoint_id=checkpoint_id,
                created_at=created_at,
                description=description,
                tags=tags or [],
            ),
            state=state,
        )
        
        # Save to disk
        checkpoint_path = self._get_checkpoint_path(checkpoint_id)
        try:
            with open(checkpoint_path, "w") as f:
                json.dump(checkpoint.to_dict(), f, indent=2)
            
            # Update size
            checkpoint.metadata.size_bytes = checkpoint_path.stat().st_size
            
            # Update index
            self._index[checkpoint_id] = checkpoint.metadata
            self._save_index()
            
            logger.info(f"Created checkpoint {checkpoint_id}: {description}")
            
            # Auto cleanup
            if self.auto_cleanup:
                self._cleanup_old_checkpoints()
            
            return checkpoint_id
            
        except Exception as e:
            logger.error(f"Failed to create checkpoint: {e}")
            raise
    
    def load(self, checkpoint_id: str) -> Checkpoint:
        """
        Load a checkpoint.
        
        Args:
            checkpoint_id: ID of checkpoint to load
            
        Returns:
            Checkpoint object
            
        Raises:
            FileNotFoundError: If checkpoint doesn't exist
        """
        checkpoint_path = self._get_checkpoint_path(checkpoint_id)
        
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_id}")
        
        try:
            with open(checkpoint_path, "r") as f:
                data = json.load(f)
                return Checkpoint.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load checkpoint {checkpoint_id}: {e}")
            raise
    
    def delete(self, checkpoint_id: str) -> bool:
        """
        Delete a checkpoint.
        
        Args:
            checkpoint_id: ID of checkpoint to delete
            
        Returns:
            True if deleted successfully
        """
        checkpoint_path = self._get_checkpoint_path(checkpoint_id)
        
        try:
            if checkpoint_path.exists():
                checkpoint_path.unlink()
            
            if checkpoint_id in self._index:
                del self._index[checkpoint_id]
                self._save_index()
            
            logger.info(f"Deleted checkpoint {checkpoint_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete checkpoint {checkpoint_id}: {e}")
            return False
    
    def list(
        self,
        tags: Optional[List[str]] = None,
        limit: int = 20,
    ) -> List[CheckpointMetadata]:
        """
        List available checkpoints.
        
        Args:
            tags: Filter by tags (any match)
            limit: Maximum number to return
            
        Returns:
            List of checkpoint metadata
        """
        checkpoints = list(self._index.values())
        
        # Filter by tags
        if tags:
            checkpoints = [
                c for c in checkpoints
                if any(tag in c.tags for tag in tags)
            ]
        
        # Sort by creation time (newest first)
        checkpoints.sort(key=lambda c: c.created_at, reverse=True)
        
        return checkpoints[:limit]
    
    def get_latest(self) -> Optional[Checkpoint]:
        """
        Get the most recent checkpoint.
        
        Returns:
            Latest checkpoint or None
        """
        checkpoints = self.list(limit=1)
        
        if checkpoints:
            return self.load(checkpoints[0].checkpoint_id)
        
        return None
    
    def _cleanup_old_checkpoints(self) -> int:
        """
        Remove old checkpoints if over limit.
        
        Returns:
            Number of checkpoints removed
        """
        if len(self._index) <= self.max_checkpoints:
            return 0
        
        # Sort by creation time
        checkpoints = sorted(
            self._index.values(),
            key=lambda c: c.created_at,
        )
        
        # Remove oldest
        to_remove = len(self._index) - self.max_checkpoints
        removed = 0
        
        for checkpoint in checkpoints[:to_remove]:
            if self.delete(checkpoint.checkpoint_id):
                removed += 1
        
        logger.info(f"Cleaned up {removed} old checkpoints")
        return removed
    
    def get_storage_size(self) -> int:
        """
        Get total storage size in bytes.
        
        Returns:
            Total size of all checkpoints
        """
        return sum(c.size_bytes for c in self._index.values())
    
    def clear_all(self) -> int:
        """
        Remove all checkpoints.
        
        Returns:
            Number of checkpoints removed
        """
        removed = 0
        
        for checkpoint_id in list(self._index.keys()):
            if self.delete(checkpoint_id):
                removed += 1
        
        return removed


class SessionCheckpointMixin:
    """
    Mixin for adding checkpoint support to sessions.
    
    Classes using this mixin need to implement:
    - get_state() -> Dict[str, Any]
    - set_state(state: Dict[str, Any]) -> None
    """
    
    _checkpoint_manager: Optional[CheckpointManager] = None
    
    @property
    def checkpoint_manager(self) -> CheckpointManager:
        """Get or create checkpoint manager."""
        if self._checkpoint_manager is None:
            self._checkpoint_manager = CheckpointManager()
        return self._checkpoint_manager
    
    def create_checkpoint(
        self,
        description: str = "",
        tags: Optional[List[str]] = None,
    ) -> str:
        """
        Create a checkpoint of current state.
        
        Args:
            description: Description of the checkpoint
            tags: Optional tags
            
        Returns:
            Checkpoint ID
        """
        state = self.get_state()  # type: ignore
        return self.checkpoint_manager.create(
            state=state,
            description=description,
            tags=tags,
        )
    
    def restore_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Restore state from a checkpoint.
        
        Args:
            checkpoint_id: ID of checkpoint to restore
            
        Returns:
            True if restored successfully
        """
        try:
            checkpoint = self.checkpoint_manager.load(checkpoint_id)
            self.set_state(checkpoint.state)  # type: ignore
            return True
        except Exception as e:
            logger.error(f"Failed to restore checkpoint: {e}")
            return False
    
    def list_checkpoints(
        self,
        tags: Optional[List[str]] = None,
        limit: int = 20,
    ) -> List[CheckpointMetadata]:
        """
        List available checkpoints.
        
        Args:
            tags: Filter by tags
            limit: Maximum number to return
            
        Returns:
            List of checkpoint metadata
        """
        return self.checkpoint_manager.list(tags=tags, limit=limit)
    
    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Delete a checkpoint.
        
        Args:
            checkpoint_id: ID of checkpoint to delete
            
        Returns:
            True if deleted successfully
        """
        return self.checkpoint_manager.delete(checkpoint_id)
