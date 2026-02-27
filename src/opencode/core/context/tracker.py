"""
File Context and Context Tracker

Tracks file context for the AI agent.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class FileContext:
    """
    Context information for a tracked file.
    
    Tracks when and how a file was accessed, its token count,
    and a preview of its content.
    """
    path: str
    access_type: str  # read, modified, created, deleted, mentioned
    tokens: int
    content_preview: Optional[str] = None
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "path": self.path,
            "access_type": self.access_type,
            "tokens": self.tokens,
            "content_preview": self.content_preview,
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileContext":
        """Create from dictionary."""
        return cls(
            path=data["path"],
            access_type=data["access_type"],
            tokens=data["tokens"],
            content_preview=data.get("content_preview"),
            last_accessed=datetime.fromisoformat(data["last_accessed"])
            if data.get("last_accessed")
            else datetime.utcnow(),
            access_count=data.get("access_count", 1),
        )


class ContextTracker:
    """
    Tracks file context for the AI agent.
    
    Maintains a record of files that have been read, modified, or are
    relevant to the current task. This helps manage context window usage
    and provides context for the AI.
    
    Example:
        tracker = ContextTracker()
        tracker.add_file("main.py", "read", 1000)
        tracker.add_file("config.py", "modified", 500)
        
        # Get context summary
        summary = tracker.get_context_summary()
    """
    
    def __init__(self, max_context_tokens: int = 100000):
        """
        Initialize the context tracker.
        
        Args:
            max_context_tokens: Maximum tokens for context window
        """
        self._files: Dict[str, FileContext] = {}
        self._max_context_tokens = max_context_tokens
        self._current_tokens = 0
    
    def add_file(
        self,
        path: str,
        access_type: str,
        tokens: int,
        content_preview: Optional[str] = None,
    ) -> None:
        """
        Add or update a file in the context.
        
        Args:
            path: File path
            access_type: Type of access (read, modified, created, deleted)
            tokens: Estimated token count
            content_preview: Optional preview of file content
        """
        if path in self._files:
            # Update existing entry
            existing = self._files[path]
            self._current_tokens -= existing.tokens
            existing.access_type = access_type
            existing.tokens = tokens
            existing.content_preview = content_preview
            existing.last_accessed = datetime.utcnow()
            existing.access_count += 1
        else:
            # Add new entry
            self._files[path] = FileContext(
                path=path,
                access_type=access_type,
                tokens=tokens,
                content_preview=content_preview,
            )
        
        self._current_tokens += tokens
    
    def remove_file(self, path: str) -> bool:
        """
        Remove a file from context.
        
        Args:
            path: File path to remove
            
        Returns:
            True if file was removed
        """
        if path in self._files:
            self._current_tokens -= self._files[path].tokens
            del self._files[path]
            return True
        return False
    
    def get_file(self, path: str) -> Optional[FileContext]:
        """Get context for a specific file."""
        return self._files.get(path)
    
    def get_all_files(self) -> Dict[str, FileContext]:
        """Get all tracked files."""
        return self._files
    
    def get_context_summary(self) -> str:
        """
        Get a summary of the current context.
        
        Returns:
            Human-readable summary
        """
        if not self._files:
            return "No files in context."
        
        lines = [
            f"Context: {len(self._files)} files, ~{self._current_tokens:,} tokens",
            f"Capacity: {self.get_capacity_percent():.1f}% used",
            "",
            "Files:",
        ]
        
        # Sort by last accessed
        sorted_files = sorted(
            self._files.values(),
            key=lambda f: f.last_accessed,
            reverse=True,
        )
        
        for file_ctx in sorted_files[:20]:  # Limit to 20 files
            lines.append(
                f"  [{file_ctx.access_type:8}] {file_ctx.path} "
                f"({file_ctx.tokens:,} tokens, {file_ctx.access_count} accesses)"
            )
        
        if len(self._files) > 20:
            lines.append(f"  ... and {len(self._files) - 20} more files")
        
        return "\n".join(lines)
    
    def get_capacity_percent(self) -> float:
        """Get context capacity usage as percentage."""
        return (self._current_tokens / self._max_context_tokens) * 100
    
    def is_over_capacity(self) -> bool:
        """Check if context is over capacity."""
        return self._current_tokens > self._max_context_tokens
    
    def get_files_to_evict(self, target_tokens: int) -> List[str]:
        """
        Get list of files to evict to free up tokens.
        
        Args:
            target_tokens: Number of tokens to free
            
        Returns:
            List of file paths to evict
        """
        if self._current_tokens <= target_tokens:
            return []
        
        # Sort by priority (oldest access, lowest access count)
        sorted_files = sorted(
            self._files.values(),
            key=lambda f: (f.last_accessed, -f.access_count),
        )
        
        to_evict = []
        freed_tokens = 0
        
        for file_ctx in sorted_files:
            if freed_tokens >= target_tokens:
                break
            
            # Don't evict recently modified files
            if file_ctx.access_type in ("modified", "created"):
                continue
            
            to_evict.append(file_ctx.path)
            freed_tokens += file_ctx.tokens
        
        return to_evict
    
    def clear(self) -> None:
        """Clear all context."""
        self._files.clear()
        self._current_tokens = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "files": {path: ctx.to_dict() for path, ctx in self._files.items()},
            "current_tokens": self._current_tokens,
            "max_context_tokens": self._max_context_tokens,
            "capacity_percent": self.get_capacity_percent(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextTracker":
        """Create from dictionary."""
        tracker = cls(max_context_tokens=data.get("max_context_tokens", 100000))
        for path, file_data in data.get("files", {}).items():
            tracker._files[path] = FileContext.from_dict(file_data)
        tracker._current_tokens = data.get("current_tokens", 0)
        return tracker
