"""
Citation System for Privacy-First RAG.

Tracks and cites sources used in responses for transparency and accountability.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Citation(BaseModel):
    """A citation for a source used in a RAG response."""
    
    id: str = Field(..., description="Unique citation ID")
    source_id: str = Field(..., description="Source document ID")
    source_path: str = Field(..., description="Path to source file")
    source_type: str = Field(default="file", description="Type of source")
    
    # Content
    snippet: Optional[str] = Field(default=None, description="Relevant snippet from source")
    snippet_start: int = Field(default=0, description="Start position of snippet")
    snippet_end: int = Field(default=0, description="End position of snippet")
    
    # Relevance
    relevance_score: float = Field(default=0.0, description="Relevance score")
    semantic_score: float = Field(default=0.0, description="Semantic similarity score")
    keyword_score: float = Field(default=0.0, description="Keyword match score")
    
    # Metadata
    title: Optional[str] = Field(default=None, description="Document title")
    author: Optional[str] = Field(default=None, description="Document author")
    created_at: Optional[datetime] = Field(default=None, description="Document creation date")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "source_id": self.source_id,
            "source_path": self.source_path,
            "source_type": self.source_type,
            "snippet": self.snippet[:100] + "..." if self.snippet and len(self.snippet) > 100 else self.snippet,
            "relevance_score": self.relevance_score,
            "title": self.title,
        }
    
    def format_inline(self) -> str:
        """Format citation for inline use."""
        if self.title:
            return f"[{self.title}]({self.source_path})"
        return f"[{self.source_path}]"
    
    def format_footnote(self, number: int) -> str:
        """Format citation as footnote."""
        parts = [f"[{number}] {self.source_path}"]
        
        if self.title:
            parts.append(f' "{self.title}"')
        
        if self.relevance_score > 0:
            parts.append(f" (relevance: {self.relevance_score:.2f})")
        
        return "".join(parts)


class CitationStyle:
    """Citation formatting styles."""
    
    INLINE = "inline"
    FOOTNOTE = "footnote"
    ENDNOTE = "endnote"
    ACADEMIC = "academic"


class CitationManager:
    """
    Manages citations for RAG responses.
    
    Features:
    - Builds citations from search results
    - Formats citations in various styles
    - Tracks source usage
    - Generates citation reports
    
    Example:
        ```python
        manager = CitationManager()
        
        # Build citations from search results
        citations = manager.build_citations(search_results)
        
        # Format response with citations
        response = manager.format_response_with_citations(
            response="The API provides...",
            citations=citations,
            style=CitationStyle.FOOTNOTE,
        )
        ```
    """
    
    def __init__(
        self,
        default_style: str = CitationStyle.FOOTNOTE,
        include_snippets: bool = True,
        max_snippet_length: int = 200,
    ):
        """
        Initialize citation manager.
        
        Args:
            default_style: Default citation style
            include_snippets: Whether to include snippets in citations
            max_snippet_length: Maximum snippet length
        """
        self.default_style = default_style
        self.include_snippets = include_snippets
        self.max_snippet_length = max_snippet_length
        
        # Track citation usage
        self._citation_count = 0
        self._source_usage: Dict[str, int] = {}
    
    def build_citations(
        self,
        sources: List[Any],
        min_score: float = 0.0,
    ) -> List[Citation]:
        """
        Build citation list from search results.
        
        Args:
            sources: List of search results
            min_score: Minimum relevance score to include
            
        Returns:
            List of citations
        """
        citations = []
        
        for i, source in enumerate(sources):
            # Get score (handle different result types)
            score = getattr(source, "score", 0.0)
            if hasattr(source, "combined_score"):
                score = source.combined_score
            
            if score < min_score:
                continue
            
            # Get source info
            source_id = getattr(source, "id", str(i))
            source_path = getattr(source, "text", "")[:50]
            
            # Get metadata
            metadata = getattr(source, "metadata", {})
            
            # Get snippet
            snippet = None
            if self.include_snippets:
                text = getattr(source, "text", "")
                if text:
                    snippet = text[:self.max_snippet_length]
                    if len(text) > self.max_snippet_length:
                        snippet += "..."
            
            # Create citation
            citation = Citation(
                id=f"cite_{i+1}",
                source_id=source_id,
                source_path=metadata.get("source", "unknown"),
                source_type=metadata.get("type", "file"),
                snippet=snippet,
                relevance_score=score,
                semantic_score=getattr(source, "semantic_score", 0.0),
                keyword_score=getattr(source, "keyword_score", 0.0),
                title=metadata.get("title"),
                author=metadata.get("author"),
                metadata=metadata,
            )
            
            citations.append(citation)
            
            # Track usage
            self._citation_count += 1
            source_key = citation.source_path
            self._source_usage[source_key] = self._source_usage.get(source_key, 0) + 1
        
        return citations
    
    def format_response_with_citations(
        self,
        response: str,
        citations: List[Citation],
        style: Optional[str] = None,
    ) -> str:
        """
        Append citations to response.
        
        Args:
            response: Response text
            citations: List of citations
            style: Citation style (uses default if not provided)
            
        Returns:
            Response with citations
        """
        if not citations:
            return response
        
        style = style or self.default_style
        
        if style == CitationStyle.INLINE:
            return self._format_inline(response, citations)
        elif style == CitationStyle.FOOTNOTE:
            return self._format_footnote(response, citations)
        elif style == CitationStyle.ENDNOTE:
            return self._format_endnote(response, citations)
        elif style == CitationStyle.ACADEMIC:
            return self._format_academic(response, citations)
        else:
            return self._format_footnote(response, citations)
    
    def _format_inline(
        self,
        response: str,
        citations: List[Citation],
    ) -> str:
        """Format with inline citations."""
        # Add citation markers in text
        lines = response.split("\n")
        
        # Append sources section
        lines.append("\n\n**Sources:**")
        for citation in citations:
            lines.append(f"- {citation.format_inline()}")
        
        return "\n".join(lines)
    
    def _format_footnote(
        self,
        response: str,
        citations: List[Citation],
    ) -> str:
        """Format with footnote citations."""
        lines = [response]
        
        lines.append("\n\n---")
        lines.append("**Sources:**\n")
        
        for i, citation in enumerate(citations, 1):
            lines.append(citation.format_footnote(i))
        
        return "\n".join(lines)
    
    def _format_endnote(
        self,
        response: str,
        citations: List[Citation],
    ) -> str:
        """Format with endnote citations."""
        lines = [response]
        
        lines.append("\n\n**References:**\n")
        
        for i, citation in enumerate(citations, 1):
            ref = f"[{i}] {citation.source_path}"
            if citation.title:
                ref += f' "{citation.title}"'
            if citation.snippet:
                ref += f" - {citation.snippet[:50]}..."
            lines.append(ref)
        
        return "\n".join(lines)
    
    def _format_academic(
        self,
        response: str,
        citations: List[Citation],
    ) -> str:
        """Format with academic-style citations."""
        lines = [response]
        
        lines.append("\n\n**References:**\n")
        
        for i, citation in enumerate(citations, 1):
            # Academic format: Author (Year) Title. Source.
            parts = []
            
            if citation.author:
                parts.append(f"{citation.author}")
            else:
                parts.append("[Author]")
            
            if citation.created_at:
                parts.append(f"({citation.created_at.year})")
            else:
                parts.append("(n.d.)")
            
            if citation.title:
                parts.append(f'"{citation.title}."')
            
            parts.append(citation.source_path)
            
            lines.append(f"[{i}] {' '.join(parts)}")
        
        return "\n".join(lines)
    
    def get_source_usage(self) -> Dict[str, int]:
        """
        Get source usage statistics.
        
        Returns:
            Dictionary of source paths to usage counts
        """
        return self._source_usage.copy()
    
    def get_most_used_sources(self, limit: int = 10) -> List[tuple]:
        """
        Get most frequently cited sources.
        
        Args:
            limit: Maximum number to return
            
        Returns:
            List of (source_path, count) tuples
        """
        sorted_sources = sorted(
            self._source_usage.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        return sorted_sources[:limit]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get citation manager statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            "total_citations": self._citation_count,
            "unique_sources": len(self._source_usage),
            "default_style": self.default_style,
            "include_snippets": self.include_snippets,
            "most_used_sources": self.get_most_used_sources(5),
        }
    
    def reset_stats(self) -> None:
        """Reset usage statistics."""
        self._citation_count = 0
        self._source_usage.clear()


def format_citation_report(
    citations: List[Citation],
    title: str = "Citation Report",
) -> str:
    """
    Generate a citation report.
    
    Args:
        citations: List of citations
        title: Report title
        
    Returns:
        Formatted report string
    """
    lines = [
        f"# {title}",
        f"\nGenerated: {datetime.utcnow().isoformat()}",
        f"Total citations: {len(citations)}\n",
    ]
    
    # Group by source type
    by_type: Dict[str, List[Citation]] = {}
    for citation in citations:
        source_type = citation.source_type
        if source_type not in by_type:
            by_type[source_type] = []
        by_type[source_type].append(citation)
    
    for source_type, type_citations in by_type.items():
        lines.append(f"\n## {source_type.title()} Sources ({len(type_citations)})\n")
        
        for citation in type_citations:
            lines.append(f"- **{citation.source_path}**")
            if citation.title:
                lines.append(f"  - Title: {citation.title}")
            if citation.relevance_score > 0:
                lines.append(f"  - Relevance: {citation.relevance_score:.2f}")
            if citation.snippet:
                lines.append(f"  - Snippet: {citation.snippet[:100]}...")
    
    return "\n".join(lines)
