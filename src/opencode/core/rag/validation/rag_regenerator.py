"""
RAG Regenerator for Privacy-First RAG.

Regenerates RAG index after false content removal.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class RegenerationResult(BaseModel):
    """Result of RAG regeneration."""
    
    success: bool = Field(..., description="Whether regeneration succeeded")
    source_id: str = Field(..., description="Source that was regenerated")
    
    documents_removed: int = Field(default=0, description="Documents removed")
    documents_reindexed: int = Field(default=0, description="Documents re-indexed")
    
    false_content_removed: int = Field(default=0, description="False content items removed")
    
    started_at: datetime = Field(default_factory=datetime.utcnow, description="When started")
    completed_at: Optional[datetime] = Field(default=None, description="When completed")
    duration_seconds: float = Field(default=0.0, description="Duration in seconds")
    
    error: Optional[str] = Field(default=None, description="Error message if failed")
    warnings: List[str] = Field(default_factory=list, description="Warning messages")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "source_id": self.source_id,
            "documents_removed": self.documents_removed,
            "documents_reindexed": self.documents_reindexed,
            "false_content_removed": self.false_content_removed,
            "duration_seconds": self.duration_seconds,
            "error": self.error,
        }


class RAGRegenerator:
    """
    Regenerates RAG index after content removal.
    
    Process:
    1. Remove false content from source
    2. Re-index affected documents
    3. Update vector store
    4. Log regeneration
    
    Example:
        ```python
        regenerator = RAGRegenerator(
            vector_store=vector_store,
            embedding_engine=embedding_engine,
            registry=false_content_registry,
        )
        
        # Regenerate after false content removal
        result = await regenerator.regenerate_after_removal(
            source_id="doc_123",
            false_content_ids=["false_abc123"],
        )
        
        print(f"Removed {result.false_content_removed} false content items")
        ```
    """
    
    def __init__(
        self,
        vector_store: Any = None,
        embedding_engine: Any = None,
        registry: Any = None,
        source_manager: Any = None,
    ):
        """
        Initialize RAG regenerator.
        
        Args:
            vector_store: Vector store instance
            embedding_engine: Embedding engine instance
            registry: False content registry instance
            source_manager: Source manager instance
        """
        self.vector_store = vector_store
        self.embedding_engine = embedding_engine
        self.registry = registry
        self.source_manager = source_manager
    
    async def regenerate_after_removal(
        self,
        source_id: str,
        false_content_ids: List[str],
        source_path: Optional[str] = None,
    ) -> RegenerationResult:
        """
        Remove false content and regenerate RAG.
        
        Args:
            source_id: Source document ID
            false_content_ids: IDs of false content to remove
            source_path: Optional path to source file
            
        Returns:
            RegenerationResult
        """
        start_time = datetime.utcnow()
        warnings: List[str] = []
        
        try:
            # Get false content records
            false_records = []
            if self.registry:
                for record_id in false_content_ids:
                    record = await self.registry.get_record_by_content(record_id)
                    if record:
                        false_records.append(record)
            
            # Remove from vector store
            documents_removed = 0
            if self.vector_store:
                try:
                    await self.vector_store.delete(false_content_ids)
                    documents_removed = len(false_content_ids)
                except Exception as e:
                    warnings.append(f"Failed to remove from vector store: {e}")
            
            # Mark as removed in registry
            false_content_removed = 0
            if self.registry:
                for record_id in false_content_ids:
                    if await self.registry.mark_removed(record_id):
                        false_content_removed += 1
            
            # Re-index source if path provided
            documents_reindexed = 0
            if source_path and self.source_manager:
                try:
                    result = await self.source_manager.index_source(Path(source_path))
                    documents_reindexed = result.document_count
                except Exception as e:
                    warnings.append(f"Failed to re-index source: {e}")
            
            completed_at = datetime.utcnow()
            duration = (completed_at - start_time).total_seconds()
            
            return RegenerationResult(
                success=True,
                source_id=source_id,
                documents_removed=documents_removed,
                documents_reindexed=documents_reindexed,
                false_content_removed=false_content_removed,
                started_at=start_time,
                completed_at=completed_at,
                duration_seconds=duration,
                warnings=warnings,
            )
            
        except Exception as e:
            logger.error(f"Regeneration failed for {source_id}: {e}")
            
            completed_at = datetime.utcnow()
            duration = (completed_at - start_time).total_seconds()
            
            return RegenerationResult(
                success=False,
                source_id=source_id,
                error=str(e),
                started_at=start_time,
                completed_at=completed_at,
                duration_seconds=duration,
                warnings=warnings,
            )
    
    async def regenerate_source(
        self,
        source_path: str,
    ) -> RegenerationResult:
        """
        Fully regenerate a source.
        
        Args:
            source_path: Path to source file/directory
            
        Returns:
            RegenerationResult
        """
        start_time = datetime.utcnow()
        
        try:
            # Get false content for this source
            false_records = []
            if self.registry:
                false_records = await self.registry.get_false_content_by_path(source_path)
            
            # Remove false content from vector store
            false_ids = [r.id for r in false_records]
            
            if self.vector_store and false_ids:
                await self.vector_store.delete(false_ids)
            
            # Re-index source
            documents_reindexed = 0
            if self.source_manager:
                result = await self.source_manager.index_source(Path(source_path))
                documents_reindexed = result.document_count
            
            # Mark records as removed
            false_content_removed = 0
            if self.registry:
                for record in false_records:
                    if await self.registry.mark_removed(record.id):
                        false_content_removed += 1
            
            completed_at = datetime.utcnow()
            duration = (completed_at - start_time).total_seconds()
            
            return RegenerationResult(
                success=True,
                source_id=source_path,
                documents_removed=len(false_ids),
                documents_reindexed=documents_reindexed,
                false_content_removed=false_content_removed,
                started_at=start_time,
                completed_at=completed_at,
                duration_seconds=duration,
            )
            
        except Exception as e:
            logger.error(f"Source regeneration failed for {source_path}: {e}")
            
            completed_at = datetime.utcnow()
            duration = (completed_at - start_time).total_seconds()
            
            return RegenerationResult(
                success=False,
                source_id=source_path,
                error=str(e),
                started_at=start_time,
                completed_at=completed_at,
                duration_seconds=duration,
            )
    
    async def regenerate_all(
        self,
    ) -> List[RegenerationResult]:
        """
        Regenerate all sources with false content.
        
        Returns:
            List of regeneration results
        """
        results = []
        
        if not self.registry:
            return results
        
        # Get all unique source paths with false content
        records = await self.registry.get_all_records(include_removed=False)
        source_paths = set(r.source_path for r in records)
        
        for source_path in source_paths:
            result = await self.regenerate_source(source_path)
            results.append(result)
        
        return results
    
    async def get_regeneration_status(
        self,
        source_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get status of pending regenerations.
        
        Args:
            source_id: Optional source ID to check
            
        Returns:
            Status dictionary
        """
        if not self.registry:
            return {"pending": 0}
        
        records = await self.registry.get_all_records(include_removed=False)
        
        if source_id:
            records = [r for r in records if r.source_id == source_id]
        
        return {
            "pending_removal": len(records),
            "sources_affected": len(set(r.source_id for r in records)),
            "oldest_pending": min(r.marked_at for r in records).isoformat() if records else None,
        }
