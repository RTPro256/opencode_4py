"""
Source Manager for Privacy-First RAG.

Manages curated knowledge sources with validation and indexing.
Only approved sources are indexed for improved accuracy and safety.
"""

import fnmatch
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SourceValidationError(Exception):
    """Raised when a source fails validation."""
    pass


class IndexResult(BaseModel):
    """Result of indexing operation."""
    
    success: bool = Field(..., description="Whether indexing succeeded")
    source: str = Field(..., description="Source path")
    document_count: int = Field(default=0, description="Number of documents indexed")
    chunk_count: int = Field(default=0, description="Number of chunks created")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    duration_seconds: float = Field(default=0.0, description="Time taken to index")
    indexed_at: datetime = Field(default_factory=datetime.utcnow, description="Index timestamp")


@dataclass
class SourceInfo:
    """Information about an indexed source."""
    
    path: str
    file_count: int = 0
    total_size: int = 0
    last_indexed: Optional[datetime] = None
    file_hash: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class SourceManager:
    """
    Manages curated knowledge sources for RAG.
    
    Features:
    - Source validation against allowed directories
    - Blocked pattern exclusion
    - File type filtering
    - Change detection for re-indexing
    - Source tracking and statistics
    
    Example:
        ```python
        config = RAGSourceConfig(
            allowed_sources=["./docs", "./src"],
            blocked_patterns=["**/secrets/**"],
            file_patterns=["*.md", "*.py"],
        )
        
        manager = SourceManager(config)
        
        # Validate a source
        if manager.validate_source(Path("./docs")):
            result = await manager.index_source(Path("./docs"))
            print(f"Indexed {result.document_count} documents")
        ```
    """
    
    def __init__(
        self,
        allowed_sources: Optional[List[str]] = None,
        blocked_patterns: Optional[List[str]] = None,
        file_patterns: Optional[List[str]] = None,
    ):
        """
        Initialize source manager.
        
        Args:
            allowed_sources: List of allowed source directories
            blocked_patterns: Patterns to exclude from indexing
            file_patterns: File types to include
        """
        self.allowed_sources = allowed_sources or ["./docs", "./src", "./RAG/sources"]
        self.blocked_patterns = blocked_patterns or [
            "**/secrets/**",
            "**/.env*",
            "**/credentials/**",
            "**/__pycache__/**",
            "**/node_modules/**",
            "**/.git/**",
        ]
        self.file_patterns = file_patterns or ["*.md", "*.py", "*.txt", "*.rst", "*.json"]
        
        # Track indexed sources
        self._indexed_sources: Dict[str, SourceInfo] = {}
    
    def validate_source(self, source: Path) -> bool:
        """
        Check if a source is allowed to be indexed.
        
        Args:
            source: Source path to validate
            
        Returns:
            True if source is valid
        """
        source = source.resolve()
        
        # Check if source exists
        if not source.exists():
            logger.warning(f"Source does not exist: {source}")
            return False
        
        # Check if source is in allowed list
        source_str = str(source)
        is_allowed = False
        
        for allowed in self.allowed_sources:
            allowed_path = Path(allowed).resolve()
            if source == allowed_path or source.is_relative_to(allowed_path):
                is_allowed = True
                break
        
        if not is_allowed:
            logger.warning(f"Source not in allowed list: {source}")
            return False
        
        # Check against blocked patterns
        for pattern in self.blocked_patterns:
            if fnmatch.fnmatch(source_str, pattern):
                logger.warning(f"Source matches blocked pattern '{pattern}': {source}")
                return False
        
        return True
    
    def is_file_allowed(self, file_path: Path) -> bool:
        """
        Check if a specific file should be indexed.
        
        Args:
            file_path: File path to check
            
        Returns:
            True if file should be indexed
        """
        file_path = file_path.resolve()
        file_str = str(file_path)
        
        # Check blocked patterns
        for pattern in self.blocked_patterns:
            if fnmatch.fnmatch(file_str, pattern):
                return False
        
        # Check file patterns
        for pattern in self.file_patterns:
            if fnmatch.fnmatch(file_path.name, pattern):
                return True
        
        return False
    
    def get_files_to_index(self, source: Path) -> List[Path]:
        """
        Get list of files to index from a source.
        
        Args:
            source: Source directory
            
        Returns:
            List of file paths to index
        """
        if not self.validate_source(source):
            return []
        
        files = []
        source = source.resolve()
        
        if source.is_file():
            if self.is_file_allowed(source):
                files.append(source)
        else:
            for pattern in self.file_patterns:
                for file_path in source.rglob(pattern):
                    if self.is_file_allowed(file_path):
                        files.append(file_path)
        
        return files
    
    def calculate_hash(self, files: List[Path]) -> str:
        """
        Calculate hash of files for change detection.
        
        Args:
            files: List of files
            
        Returns:
            Hash string
        """
        hasher = hashlib.sha256()
        
        for file_path in sorted(files):
            try:
                mtime = file_path.stat().st_mtime
                hasher.update(f"{file_path}:{mtime}".encode())
            except Exception:
                pass
        
        return hasher.hexdigest()[:16]
    
    def has_source_changed(self, source: Path) -> bool:
        """
        Check if source has changed since last indexing.
        
        Args:
            source: Source path
            
        Returns:
            True if source has changed
        """
        source_str = str(source.resolve())
        
        if source_str not in self._indexed_sources:
            return True
        
        files = self.get_files_to_index(source)
        current_hash = self.calculate_hash(files)
        
        return self._indexed_sources[source_str].file_hash != current_hash
    
    async def index_source(
        self,
        source: Path,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> IndexResult:
        """
        Index a source directory or file.
        
        Args:
            source: Source path to index
            metadata: Optional metadata to attach to documents
            
        Returns:
            IndexResult with indexing statistics
        """
        start_time = datetime.utcnow()
        
        if not self.validate_source(source):
            return IndexResult(
                success=False,
                source=str(source),
                error="Source validation failed",
            )
        
        try:
            files = self.get_files_to_index(source)
            
            if not files:
                return IndexResult(
                    success=True,
                    source=str(source),
                    document_count=0,
                    chunk_count=0,
                )
            
            # Calculate hash for change detection
            file_hash = self.calculate_hash(files)
            
            # Track source info
            source_str = str(source.resolve())
            self._indexed_sources[source_str] = SourceInfo(
                path=source_str,
                file_count=len(files),
                total_size=sum(f.stat().st_size for f in files if f.exists()),
                last_indexed=datetime.utcnow(),
                file_hash=file_hash,
                metadata=metadata or {},
            )
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            return IndexResult(
                success=True,
                source=str(source),
                document_count=len(files),
                chunk_count=len(files),  # Simplified; actual chunking happens elsewhere
                duration_seconds=duration,
            )
            
        except Exception as e:
            logger.error(f"Error indexing source {source}: {e}")
            return IndexResult(
                success=False,
                source=str(source),
                error=str(e),
            )
    
    def get_indexed_sources(self) -> List[SourceInfo]:
        """
        Get list of indexed sources.
        
        Returns:
            List of SourceInfo objects
        """
        return list(self._indexed_sources.values())
    
    def get_source_info(self, source: Path) -> Optional[SourceInfo]:
        """
        Get information about an indexed source.
        
        Args:
            source: Source path
            
        Returns:
            SourceInfo if indexed, None otherwise
        """
        source_str = str(source.resolve())
        return self._indexed_sources.get(source_str)
    
    def remove_source(self, source: Path) -> bool:
        """
        Remove a source from tracking.
        
        Args:
            source: Source path to remove
            
        Returns:
            True if source was removed
        """
        source_str = str(source.resolve())
        if source_str in self._indexed_sources:
            del self._indexed_sources[source_str]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all indexed source tracking."""
        self._indexed_sources.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get source manager statistics.
        
        Returns:
            Statistics dictionary
        """
        total_files = sum(s.file_count for s in self._indexed_sources.values())
        total_size = sum(s.total_size for s in self._indexed_sources.values())
        
        return {
            "allowed_sources": self.allowed_sources,
            "blocked_patterns": self.blocked_patterns,
            "file_patterns": self.file_patterns,
            "indexed_source_count": len(self._indexed_sources),
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
        }


def create_source_manager(
    allowed_sources: Optional[List[str]] = None,
    blocked_patterns: Optional[List[str]] = None,
    file_patterns: Optional[List[str]] = None,
) -> SourceManager:
    """
    Create a source manager with configuration.
    
    Args:
        allowed_sources: List of allowed source directories
        blocked_patterns: Patterns to exclude
        file_patterns: File types to include
        
    Returns:
        SourceManager instance
    """
    return SourceManager(
        allowed_sources=allowed_sources,
        blocked_patterns=blocked_patterns,
        file_patterns=file_patterns,
    )
