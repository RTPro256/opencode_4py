"""
Audit Logger for Privacy-First RAG.

Logs all RAG operations for audit purposes.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AuditEntry:
    """An entry in the audit log."""
    
    timestamp: datetime
    """When the event occurred."""
    
    event_type: str
    """Type of event (query, index, delete, etc.)."""
    
    query: Optional[str] = None
    """The query if applicable."""
    
    sources_used: List[str] = field(default_factory=list)
    """Sources used in the operation."""
    
    response_preview: Optional[str] = None
    """Preview of the response (truncated)."""
    
    document_count: int = 0
    """Number of documents involved."""
    
    user_id: Optional[str] = None
    """User who performed the operation."""
    
    session_id: Optional[str] = None
    """Session ID if applicable."""
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "query": self.query,
            "sources_used": self.sources_used,
            "response_preview": self.response_preview,
            "document_count": self.document_count,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "metadata": self.metadata,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class RAGAuditLogger:
    """
    Logs all RAG operations for audit purposes.
    
    Features:
    - Logs all queries and sources used
    - Logs indexing operations
    - Logs deletions and modifications
    - Supports querying audit history
    - File-based persistence
    
    Example:
        ```python
        audit = RAGAuditLogger(path="./RAG/audit.log")
        
        # Log a query
        await audit.log_query(
            query="What is the API?",
            sources_used=["docs/api.md", "src/api.py"],
            response_preview="The API provides...",
        )
        
        # Log indexing
        await audit.log_indexing(
            source="./docs",
            document_count=42,
            indexed_by="user@example.com",
        )
        
        # Get recent entries
        entries = await audit.get_recent_entries(limit=10)
        ```
    """
    
    def __init__(
        self,
        path: str = "./RAG/audit.log",
        max_file_size_mb: int = 10,
        max_entries: int = 10000,
    ):
        """
        Initialize audit logger.
        
        Args:
            path: Path to audit log file
            max_file_size_mb: Maximum log file size before rotation
            max_entries: Maximum entries to keep in memory
        """
        self.path = Path(path)
        self.max_file_size_mb = max_file_size_mb
        self.max_entries = max_entries
        
        # Ensure directory exists
        self.path.parent.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache of recent entries
        self._entries: List[AuditEntry] = []
        self._load_entries()
    
    def _load_entries(self) -> None:
        """Load existing entries from file."""
        if not self.path.exists():
            return
        
        try:
            with open(self.path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                        entry = AuditEntry(
                            timestamp=datetime.fromisoformat(data["timestamp"]),
                            event_type=data["event_type"],
                            query=data.get("query"),
                            sources_used=data.get("sources_used", []),
                            response_preview=data.get("response_preview"),
                            document_count=data.get("document_count", 0),
                            user_id=data.get("user_id"),
                            session_id=data.get("session_id"),
                            metadata=data.get("metadata", {}),
                        )
                        self._entries.append(entry)
                    except Exception as e:
                        logger.warning(f"Failed to parse audit entry: {e}")
            
            # Trim to max entries
            if len(self._entries) > self.max_entries:
                self._entries = self._entries[-self.max_entries:]
                
        except Exception as e:
            logger.error(f"Failed to load audit log: {e}")
    
    def _append_entry(self, entry: AuditEntry) -> None:
        """Append entry to log file."""
        try:
            # Check file size for rotation
            if self.path.exists():
                size_mb = self.path.stat().st_size / (1024 * 1024)
                if size_mb >= self.max_file_size_mb:
                    self._rotate_log()
            
            # Append to file
            with open(self.path, "a") as f:
                f.write(entry.to_json() + "\n")
            
            # Add to memory cache
            self._entries.append(entry)
            
            # Trim memory cache
            if len(self._entries) > self.max_entries:
                self._entries = self._entries[-self.max_entries:]
                
        except Exception as e:
            logger.error(f"Failed to write audit entry: {e}")
    
    def _rotate_log(self) -> None:
        """Rotate log file when it gets too large."""
        if not self.path.exists():
            return
        
        try:
            # Create backup with timestamp
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_path = self.path.with_suffix(f".{timestamp}.log")
            self.path.rename(backup_path)
            
            logger.info(f"Rotated audit log to {backup_path}")
            
        except Exception as e:
            logger.error(f"Failed to rotate audit log: {e}")
    
    async def log_query(
        self,
        query: str,
        sources_used: List[str],
        response_preview: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log a RAG query.
        
        Args:
            query: The query string
            sources_used: List of sources used
            response_preview: Preview of the response
            user_id: User who made the query
            session_id: Session ID
            metadata: Additional metadata
        """
        # Truncate response preview
        if response_preview and len(response_preview) > 200:
            response_preview = response_preview[:200] + "..."
        
        entry = AuditEntry(
            timestamp=datetime.utcnow(),
            event_type="query",
            query=query,
            sources_used=sources_used,
            response_preview=response_preview,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata or {},
        )
        
        self._append_entry(entry)
        logger.debug(f"Logged query: {query[:50]}...")
    
    async def log_indexing(
        self,
        source: str,
        document_count: int,
        indexed_by: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log an indexing operation.
        
        Args:
            source: Source that was indexed
            document_count: Number of documents indexed
            indexed_by: User who performed indexing
            session_id: Session ID
            metadata: Additional metadata
        """
        entry = AuditEntry(
            timestamp=datetime.utcnow(),
            event_type="indexing",
            sources_used=[source],
            document_count=document_count,
            user_id=indexed_by,
            session_id=session_id,
            metadata=metadata or {},
        )
        
        self._append_entry(entry)
        logger.debug(f"Logged indexing: {source} ({document_count} documents)")
    
    async def log_deletion(
        self,
        source: str,
        document_count: int,
        deleted_by: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log a deletion operation.
        
        Args:
            source: Source that was deleted
            document_count: Number of documents deleted
            deleted_by: User who performed deletion
            session_id: Session ID
            metadata: Additional metadata
        """
        entry = AuditEntry(
            timestamp=datetime.utcnow(),
            event_type="deletion",
            sources_used=[source],
            document_count=document_count,
            user_id=deleted_by,
            session_id=session_id,
            metadata=metadata or {},
        )
        
        self._append_entry(entry)
        logger.debug(f"Logged deletion: {source} ({document_count} documents)")
    
    async def log_event(
        self,
        event_type: str,
        query: Optional[str] = None,
        sources_used: Optional[List[str]] = None,
        response_preview: Optional[str] = None,
        document_count: int = 0,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log a custom event.
        
        Args:
            event_type: Type of event
            query: Query if applicable
            sources_used: Sources used
            response_preview: Response preview
            document_count: Document count
            user_id: User ID
            session_id: Session ID
            metadata: Additional metadata
        """
        entry = AuditEntry(
            timestamp=datetime.utcnow(),
            event_type=event_type,
            query=query,
            sources_used=sources_used or [],
            response_preview=response_preview,
            document_count=document_count,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata or {},
        )
        
        self._append_entry(entry)
    
    async def get_recent_entries(
        self,
        limit: int = 100,
        event_type: Optional[str] = None,
    ) -> List[AuditEntry]:
        """
        Get recent audit entries.
        
        Args:
            limit: Maximum number of entries to return
            event_type: Filter by event type
            
        Returns:
            List of audit entries
        """
        entries = self._entries
        
        if event_type:
            entries = [e for e in entries if e.event_type == event_type]
        
        return entries[-limit:]
    
    async def get_entries_by_date(
        self,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        event_type: Optional[str] = None,
    ) -> List[AuditEntry]:
        """
        Get entries within a date range.
        
        Args:
            start_date: Start date
            end_date: End date (defaults to now)
            event_type: Filter by event type
            
        Returns:
            List of audit entries
        """
        end_date = end_date or datetime.utcnow()
        
        entries = [
            e for e in self._entries
            if start_date <= e.timestamp <= end_date
        ]
        
        if event_type:
            entries = [e for e in entries if e.event_type == event_type]
        
        return entries
    
    async def get_entries_by_query(
        self,
        query_text: str,
        limit: int = 100,
    ) -> List[AuditEntry]:
        """
        Get entries containing query text.
        
        Args:
            query_text: Text to search for
            limit: Maximum entries to return
            
        Returns:
            List of matching entries
        """
        query_lower = query_text.lower()
        
        entries = [
            e for e in self._entries
            if e.query and query_lower in e.query.lower()
        ]
        
        return entries[-limit:]
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get audit log statistics.
        
        Returns:
            Statistics dictionary
        """
        # Count by event type
        event_counts: Dict[str, int] = {}
        for entry in self._entries:
            event_counts[entry.event_type] = event_counts.get(entry.event_type, 0) + 1
        
        # Get file size
        file_size = 0
        if self.path.exists():
            file_size = self.path.stat().st_size
        
        return {
            "total_entries": len(self._entries),
            "event_counts": event_counts,
            "file_path": str(self.path),
            "file_size_bytes": file_size,
            "file_size_kb": file_size / 1024,
            "max_entries": self.max_entries,
            "max_file_size_mb": self.max_file_size_mb,
        }
    
    async def clear(self) -> None:
        """Clear all audit entries."""
        self._entries.clear()
        
        if self.path.exists():
            self.path.unlink()
        
        logger.info("Cleared audit log")
    
    async def export(
        self,
        output_path: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """
        Export audit log to a file.
        
        Args:
            output_path: Path to export file
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Number of entries exported
        """
        entries = self._entries
        
        if start_date:
            entries = [e for e in entries if e.timestamp >= start_date]
        
        if end_date:
            entries = [e for e in entries if e.timestamp <= end_date]
        
        with open(output_path, "w") as f:
            for entry in entries:
                f.write(entry.to_json() + "\n")
        
        logger.info(f"Exported {len(entries)} audit entries to {output_path}")
        return len(entries)
