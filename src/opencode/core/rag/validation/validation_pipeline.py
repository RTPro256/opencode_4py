"""
Validation-Aware RAG Pipeline for Privacy-First RAG.

RAG pipeline that filters false content from results.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class FilteredContent(BaseModel):
    """Record of content that was filtered."""
    
    content_id: str
    content_preview: str
    source_id: str
    reason: str
    filtered_at: datetime = Field(default_factory=datetime.utcnow)


class ValidatedQueryResult(BaseModel):
    """Result from validation-aware query."""
    
    results: List[Any] = Field(default_factory=list, description="Filtered search results")
    total_found: int = Field(default=0, description="Total results before filtering")
    filtered_count: int = Field(default=0, description="Number of results filtered out")
    
    filtered_content: List[FilteredContent] = Field(
        default_factory=list,
        description="Content that was filtered"
    )
    
    query: str = Field(..., description="Original query")
    query_time: datetime = Field(default_factory=datetime.utcnow, description="When query was executed")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "results": [r.to_dict() if hasattr(r, "to_dict") else str(r) for r in self.results],
            "total_found": self.total_found,
            "filtered_count": self.filtered_count,
            "query": self.query,
            "query_time": self.query_time.isoformat(),
        }


class ValidationAwareRAGPipeline:
    """
    RAG pipeline that filters false content.
    
    Features:
    - Filters false content from search results
    - Logs when false content would have been returned
    - Suggests corrections based on validation history
    - Tracks filtering statistics
    
    Example:
        ```python
        pipeline = ValidationAwareRAGPipeline(
            hybrid_search=hybrid_search,
            registry=false_content_registry,
            audit_logger=audit_logger,
        )
        
        # Query with validation
        result = await pipeline.query_with_validation(
            query="How does authentication work?",
            top_k=5,
        )
        
        print(f"Found {len(result.results)} valid results")
        print(f"Filtered {result.filtered_count} false content items")
        ```
    """
    
    def __init__(
        self,
        hybrid_search: Any = None,
        registry: Any = None,
        audit_logger: Any = None,
        auto_filter: bool = True,
        log_filtered: bool = True,
    ):
        """
        Initialize validation-aware pipeline.
        
        Args:
            hybrid_search: Hybrid search instance
            registry: False content registry
            audit_logger: Audit logger for tracking
            auto_filter: Whether to automatically filter false content
            log_filtered: Whether to log filtered content
        """
        self.hybrid_search = hybrid_search
        self.registry = registry
        self.audit_logger = audit_logger
        self.auto_filter = auto_filter
        self.log_filtered = log_filtered
        
        # Statistics
        self._total_queries = 0
        self._total_filtered = 0
    
    async def query_with_validation(
        self,
        query: str,
        query_embedding: Optional[List[float]] = None,
        top_k: int = 5,
    ) -> ValidatedQueryResult:
        """
        Query RAG with false content filtering.
        
        Args:
            query: Query string
            query_embedding: Optional pre-computed embedding
            top_k: Number of results to return
            
        Returns:
            ValidatedQueryResult with filtered results
        """
        self._total_queries += 1
        
        # Get more results to account for filtering
        fetch_k = top_k * 2 if self.auto_filter else top_k
        
        # Search
        results = []
        if self.hybrid_search:
            if query_embedding:
                results = await self.hybrid_search.search(
                    query=query,
                    query_embedding=query_embedding,
                    top_k=fetch_k,
                )
            else:
                # Need embedding - this would typically be computed elsewhere
                results = []
        
        total_found = len(results)
        filtered_content: List[FilteredContent] = []
        
        # Filter false content
        validated_results = []
        
        for result in results:
            # Get content text
            content_text = getattr(result, "text", str(result))
            content_id = getattr(result, "id", "unknown")
            source_id = getattr(result, "source_id", getattr(result, "metadata", {}).get("source", "unknown"))
            
            # Check if content is false
            is_false = False
            if self.registry and self.auto_filter:
                is_false = await self.registry.is_content_false(content_text)
            
            if is_false:
                # Get reason from registry
                reason = "Marked as false"
                record = await self.registry.get_record_by_content(content_text)
                if record:
                    reason = record.reason
                
                # Record filtered content
                filtered = FilteredContent(
                    content_id=content_id,
                    content_preview=content_text[:100] + "..." if len(content_text) > 100 else content_text,
                    source_id=source_id,
                    reason=reason,
                )
                filtered_content.append(filtered)
                
                # Log if enabled
                if self.log_filtered:
                    logger.info(f"Filtered false content: {content_id} from query")
                    self._total_filtered += 1
                
            else:
                validated_results.append(result)
        
        # Log to audit if available
        if self.audit_logger and filtered_content:
            await self.audit_logger.log_event(
                event_type="content_filtered",
                query=query,
                metadata={
                    "filtered_count": len(filtered_content),
                    "filtered_ids": [f.content_id for f in filtered_content],
                },
            )
        
        return ValidatedQueryResult(
            results=validated_results[:top_k],
            total_found=total_found,
            filtered_count=len(filtered_content),
            filtered_content=filtered_content,
            query=query,
        )
    
    async def build_context_with_validation(
        self,
        query: str,
        query_embedding: Optional[List[float]] = None,
        max_tokens: int = 4000,
        top_k: int = 10,
    ) -> str:
        """
        Build context string with false content filtered.
        
        Args:
            query: Query string
            query_embedding: Optional pre-computed embedding
            max_tokens: Maximum tokens in context
            top_k: Number of results to consider
            
        Returns:
            Context string
        """
        result = await self.query_with_validation(
            query=query,
            query_embedding=query_embedding,
            top_k=top_k,
        )
        
        context_parts = []
        current_tokens = 0
        
        for search_result in result.results:
            text = getattr(search_result, "text", str(search_result))
            chunk_tokens = len(text) // 4  # Rough estimate
            
            if current_tokens + chunk_tokens > max_tokens:
                break
            
            context_parts.append(text)
            current_tokens += chunk_tokens
        
        return "\n\n".join(context_parts)
    
    async def suggest_corrections(
        self,
        query: str,
    ) -> List[Dict[str, Any]]:
        """
        Suggest corrections based on validation history.
        
        Args:
            query: Query string
            
        Returns:
            List of correction suggestions
        """
        suggestions = []
        
        if not self.registry:
            return suggestions
        
        # Get recent false content that might be related
        records = await self.registry.get_all_records(include_removed=False)
        
        for record in records[:10]:  # Limit to recent 10
            # Simple relevance check
            if any(word in record.content.lower() for word in query.lower().split()):
                suggestions.append({
                    "false_content": record.content[:100] + "...",
                    "reason": record.reason,
                    "source": record.source_path,
                    "marked_at": record.marked_at.isoformat(),
                })
        
        return suggestions
    
    async def get_validation_stats(self) -> Dict[str, Any]:
        """
        Get validation statistics.
        
        Returns:
            Statistics dictionary
        """
        stats = {
            "total_queries": self._total_queries,
            "total_filtered": self._total_filtered,
            "filter_rate": self._total_filtered / self._total_queries if self._total_queries > 0 else 0,
            "auto_filter": self.auto_filter,
            "log_filtered": self.log_filtered,
        }
        
        if self.registry:
            registry_stats = await self.registry.get_stats()
            stats["registry"] = registry_stats
        
        return stats
    
    async def report_false_content(
        self,
        content: str,
        source_id: str,
        source_path: str,
        reason: str,
        evidence: Optional[str] = None,
        reported_by: Optional[str] = None,
    ) -> Any:
        """
        Report content as false.
        
        Args:
            content: Content to report
            source_id: Source document ID
            source_path: Path to source
            reason: Reason for reporting
            evidence: Evidence supporting the report
            reported_by: Who reported it
            
        Returns:
            FalseContentRecord
        """
        if not self.registry:
            logger.warning("No registry available to report false content")
            return None
        
        record = await self.registry.add_false_content(
            content=content,
            source_id=source_id,
            source_path=source_path,
            reason=reason,
            evidence=evidence,
            marked_by=reported_by,
        )
        
        # Log to audit
        if self.audit_logger:
            await self.audit_logger.log_event(
                event_type="false_content_reported",
                query=None,
                sources_used=[source_path],
                metadata={
                    "content_id": record.id,
                    "reason": reason,
                    "reported_by": reported_by,
                },
            )
        
        logger.info(f"Reported false content: {record.id}")
        
        return record
    
    def reset_stats(self) -> None:
        """Reset statistics."""
        self._total_queries = 0
        self._total_filtered = 0
