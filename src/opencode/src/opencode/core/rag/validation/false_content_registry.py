"""
False Content Registry for Privacy-First RAG.

Registry of content marked as false for tracking and filtering.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class FalseContentRecord(BaseModel):
    """A record of content marked as false."""
    
    id: str = Field(..., description="Unique record ID")
    content: str = Field(..., description="The false content")
    content_hash: str = Field(..., description="Hash of content for quick lookup")
    source_id: str = Field(..., description="Source document ID")
    source_path: str = Field(..., description="Path to source file")
    
    reason: str = Field(..., description="Reason for marking as false")
    evidence: Optional[str] = Field(default=None, description="Evidence supporting the marking")
    
    marked_at: datetime = Field(default_factory=datetime.utcnow, description="When marked")
    marked_by: Optional[str] = Field(default=None, description="Who marked it")
    confirmed_by: Optional[str] = Field(default=None, description="Who confirmed it")
    
    is_removed: bool = Field(default=False, description="Whether content has been removed from source")
    removed_at: Optional[datetime] = Field(default=None, description="When removed")
    
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "content_hash": self.content_hash,
            "source_id": self.source_id,
            "source_path": self.source_path,
            "reason": self.reason,
            "evidence": self.evidence[:200] if self.evidence else None,
            "marked_at": self.marked_at.isoformat(),
            "marked_by": self.marked_by,
            "confirmed_by": self.confirmed_by,
            "is_removed": self.is_removed,
        }


class FalseContentRegistry:
    """
    Registry of content marked as false.
    
    Tracks:
    - Content marked as false
    - Reason for marking
    - Evidence/test results
    - User who confirmed
    - Timestamp
    - Removal status
    
    Example:
        ```python
        registry = FalseContentRegistry(path="./RAG/.false_content_registry.json")
        
        # Add false content
        record = await registry.add_false_content(
            content="The function returns a string",
            source_id="doc_123",
            source_path="docs/api.md",
            reason="Test failure: function returns int",
            evidence="Test test_return_type failed",
            marked_by="test_runner",
        )
        
        # Check if content is false
        is_false = await registry.is_content_false("The function returns a string")
        
        # Get all false content for a source
        records = await registry.get_false_content_for_source("doc_123")
        ```
    """
    
    def __init__(
        self,
        path: str = "./RAG/.false_content_registry.json",
    ):
        """
        Initialize false content registry.
        
        Args:
            path: Path to registry file
        """
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        
        # In-memory storage
        self._records: Dict[str, FalseContentRecord] = {}
        self._content_hashes: Set[str] = set()
        
        # Load existing records
        self._load()
    
    def _load(self) -> None:
        """Load existing records from file."""
        if not self.path.exists():
            return
        
        try:
            with open(self.path, "r") as f:
                data = json.load(f)
            
            for record_data in data.get("records", []):
                record = FalseContentRecord(
                    id=record_data["id"],
                    content=record_data["content"],
                    content_hash=record_data["content_hash"],
                    source_id=record_data["source_id"],
                    source_path=record_data["source_path"],
                    reason=record_data["reason"],
                    evidence=record_data.get("evidence"),
                    marked_at=datetime.fromisoformat(record_data["marked_at"]),
                    marked_by=record_data.get("marked_by"),
                    confirmed_by=record_data.get("confirmed_by"),
                    is_removed=record_data.get("is_removed", False),
                    removed_at=datetime.fromisoformat(record_data["removed_at"]) if record_data.get("removed_at") else None,
                    metadata=record_data.get("metadata", {}),
                )
                self._records[record.id] = record
                self._content_hashes.add(record.content_hash)
            
            logger.info(f"Loaded {len(self._records)} false content records")
            
        except Exception as e:
            logger.error(f"Failed to load false content registry: {e}")
    
    def _save(self) -> None:
        """Save records to file."""
        try:
            data = {
                "version": 1,
                "updated_at": datetime.utcnow().isoformat(),
                "records": [r.model_dump() for r in self._records.values()],
            }
            
            with open(self.path, "w") as f:
                json.dump(data, f, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"Failed to save false content registry: {e}")
    
    def _hash_content(self, content: str) -> str:
        """Generate hash for content."""
        import hashlib
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    async def add_false_content(
        self,
        content: str,
        source_id: str,
        source_path: str,
        reason: str,
        evidence: Optional[str] = None,
        marked_by: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FalseContentRecord:
        """
        Add content to false content registry.
        
        Args:
            content: The false content
            source_id: Source document ID
            source_path: Path to source file
            reason: Reason for marking as false
            evidence: Evidence supporting the marking
            marked_by: Who marked it as false
            metadata: Additional metadata
            
        Returns:
            FalseContentRecord
        """
        content_hash = self._hash_content(content)
        record_id = f"false_{content_hash}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        record = FalseContentRecord(
            id=record_id,
            content=content,
            content_hash=content_hash,
            source_id=source_id,
            source_path=source_path,
            reason=reason,
            evidence=evidence,
            marked_by=marked_by,
            metadata=metadata or {},
        )
        
        self._records[record_id] = record
        self._content_hashes.add(content_hash)
        
        self._save()
        
        logger.info(f"Added false content record: {record_id} (source={source_id})")
        
        return record
    
    async def get_false_content_for_source(
        self,
        source_id: str,
    ) -> List[FalseContentRecord]:
        """
        Get all false content for a source.
        
        Args:
            source_id: Source document ID
            
        Returns:
            List of false content records
        """
        return [
            r for r in self._records.values()
            if r.source_id == source_id
        ]
    
    async def get_false_content_by_path(
        self,
        source_path: str,
    ) -> List[FalseContentRecord]:
        """
        Get all false content for a source path.
        
        Args:
            source_path: Path to source file
            
        Returns:
            List of false content records
        """
        return [
            r for r in self._records.values()
            if r.source_path == source_path
        ]
    
    async def is_content_false(
        self,
        content: str,
    ) -> bool:
        """
        Check if content is in false content registry.
        
        Args:
            content: Content to check
            
        Returns:
            True if content is marked as false
        """
        content_hash = self._hash_content(content)
        return content_hash in self._content_hashes
    
    async def get_record_by_content(
        self,
        content: str,
    ) -> Optional[FalseContentRecord]:
        """
        Get record for specific content.
        
        Args:
            content: Content to look up
            
        Returns:
            FalseContentRecord if found, None otherwise
        """
        content_hash = self._hash_content(content)
        
        for record in self._records.values():
            if record.content_hash == content_hash:
                return record
        
        return None
    
    async def mark_removed(
        self,
        record_id: str,
    ) -> bool:
        """
        Mark a record as removed from source.
        
        Args:
            record_id: Record ID to mark
            
        Returns:
            True if successful
        """
        if record_id not in self._records:
            return False
        
        record = self._records[record_id]
        record.is_removed = True
        record.removed_at = datetime.utcnow()
        
        self._save()
        
        logger.info(f"Marked false content as removed: {record_id}")
        
        return True
    
    async def confirm_record(
        self,
        record_id: str,
        confirmed_by: str,
    ) -> bool:
        """
        Confirm a false content record.
        
        Args:
            record_id: Record ID to confirm
            confirmed_by: Who confirmed it
            
        Returns:
            True if successful
        """
        if record_id not in self._records:
            return False
        
        record = self._records[record_id]
        record.confirmed_by = confirmed_by
        
        self._save()
        
        logger.info(f"Confirmed false content: {record_id} by {confirmed_by}")
        
        return True
    
    async def remove_record(
        self,
        record_id: str,
    ) -> bool:
        """
        Remove a record from the registry.
        
        Args:
            record_id: Record ID to remove
            
        Returns:
            True if successful
        """
        if record_id not in self._records:
            return False
        
        record = self._records.pop(record_id)
        self._content_hashes.discard(record.content_hash)
        
        self._save()
        
        logger.info(f"Removed false content record: {record_id}")
        
        return True
    
    async def get_all_records(
        self,
        include_removed: bool = False,
    ) -> List[FalseContentRecord]:
        """
        Get all records.
        
        Args:
            include_removed: Whether to include removed records
            
        Returns:
            List of all records
        """
        records = list(self._records.values())
        
        if not include_removed:
            records = [r for r in records if not r.is_removed]
        
        return records
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get registry statistics.
        
        Returns:
            Statistics dictionary
        """
        records = list(self._records.values())
        
        return {
            "total_records": len(records),
            "pending_removal": sum(1 for r in records if not r.is_removed),
            "removed": sum(1 for r in records if r.is_removed),
            "confirmed": sum(1 for r in records if r.confirmed_by),
            "unique_sources": len(set(r.source_id for r in records)),
        }
    
    async def clear(self) -> None:
        """Clear all records."""
        self._records.clear()
        self._content_hashes.clear()
        self._save()
        
        logger.info("Cleared false content registry")
