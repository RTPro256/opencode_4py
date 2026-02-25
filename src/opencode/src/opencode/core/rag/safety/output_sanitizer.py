"""
Output Sanitizer for Privacy-First RAG.

Sanitizes LLM output before returning to user to prevent data leakage.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from .content_filter import ContentFilter

logger = logging.getLogger(__name__)


@dataclass
class Citation:
    """A citation for a source used in response."""
    
    source_id: str
    """Unique identifier for the source."""
    
    source_path: str
    """Path or name of the source."""
    
    relevance_score: float
    """Relevance score of the source."""
    
    snippet: Optional[str] = None
    """Optional snippet from the source."""
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata."""


@dataclass
class SanitizationContext:
    """Context for sanitization operation."""
    
    query: str
    """The original query."""
    
    sources_used: List[Citation] = field(default_factory=list)
    """Sources used in generating the response."""
    
    allowed_urls: Set[str] = field(default_factory=set)
    """URLs that are allowed to appear in output."""
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional context metadata."""


@dataclass
class SanitizedOutput:
    """Result of output sanitization."""
    
    original_output: str
    """The original output before sanitization."""
    
    sanitized_output: str
    """The sanitized output."""
    
    citations: List[Citation] = field(default_factory=list)
    """Valid citations from the response."""
    
    warnings: List[str] = field(default_factory=list)
    """Warning messages about potential issues."""
    
    removed_urls: List[str] = field(default_factory=list)
    """URLs that were removed from output."""
    
    is_safe: bool = True
    """Whether the output is safe to return."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "sanitized_output": self.sanitized_output,
            "is_safe": self.is_safe,
            "citation_count": len(self.citations),
            "warnings": self.warnings,
            "removed_urls": self.removed_urls,
        }


class OutputSanitizer:
    """
    Sanitizes LLM output before returning to user.
    
    Features:
    - Removes accidentally included secrets
    - Validates citations match sources
    - Removes unauthorized external URLs
    - Ensures no sensitive data leakage
    
    Example:
        ```python
        sanitizer = OutputSanitizer()
        
        context = SanitizationContext(
            query="What is the API?",
            sources_used=[Citation(source_id="1", source_path="docs/api.md", ...)],
        )
        
        result = sanitizer.sanitize(
            "The API key is sk-12345. See https://external.com for more.",
            context
        )
        
        print(result.sanitized_output)
        # "The API key is [REDACTED]. See [URL_REMOVED] for more."
        ```
    """
    
    # Patterns for potentially leaked secrets
    SECRET_PATTERNS = [
        r"sk-[a-zA-Z0-9]{20,}",  # OpenAI-style keys
        r"xox[baprs]-[a-zA-Z0-9-]+",  # Slack tokens
        r"github_pat_[a-zA-Z0-9_]+",  # GitHub PATs
        r"glpat-[a-zA-Z0-9-]+",  # GitLab PATs
        r"Bearer\s+[a-zA-Z0-9_-]+",  # Bearer tokens
    ]
    
    # URL pattern
    URL_PATTERN = r'https?://[^\s<>"{}|\\^`\[\]]+'
    
    def __init__(
        self,
        content_filter: Optional[ContentFilter] = None,
        allow_external_urls: bool = False,
        allowed_url_domains: Optional[List[str]] = None,
    ):
        """
        Initialize output sanitizer.
        
        Args:
            content_filter: Content filter to use for secret detection
            allow_external_urls: Whether to allow external URLs
            allowed_url_domains: List of allowed URL domains
        """
        self.content_filter = content_filter or ContentFilter()
        self.allow_external_urls = allow_external_urls
        self.allowed_url_domains = set(allowed_url_domains or [])
        
        # Compile secret patterns
        self._secret_patterns = [
            re.compile(p) for p in self.SECRET_PATTERNS
        ]
        self._url_pattern = re.compile(self.URL_PATTERN)
    
    def sanitize(
        self,
        output: str,
        context: Optional[SanitizationContext] = None,
    ) -> SanitizedOutput:
        """
        Sanitize LLM output.
        
        Args:
            output: Output to sanitize
            context: Sanitization context
            
        Returns:
            SanitizedOutput with cleaned content
        """
        sanitized = output
        warnings: List[str] = []
        removed_urls: List[str] = []
        citations: List[Citation] = []
        
        # 1. Filter sensitive content
        filter_result = self.content_filter.filter_content(sanitized)
        sanitized = filter_result.filtered_content
        
        if not filter_result.is_safe:
            warnings.append("Sensitive content detected and redacted")
        
        # 2. Check for leaked secrets
        for pattern in self._secret_patterns:
            matches = pattern.findall(sanitized)
            for match in matches:
                sanitized = sanitized.replace(match, "[SECRET_REDACTED]")
                warnings.append(f"Potential secret detected and redacted")
        
        # 3. Handle URLs
        if not self.allow_external_urls:
            urls = self._url_pattern.findall(sanitized)
            for url in urls:
                # Check if URL is allowed
                is_allowed = any(
                    domain in url for domain in self.allowed_url_domains
                )
                
                if not is_allowed:
                    sanitized = sanitized.replace(url, "[URL_REMOVED]")
                    removed_urls.append(url)
                    warnings.append(f"External URL removed: {url[:50]}...")
        
        # 4. Validate citations if context provided
        if context and context.sources_used:
            citations = self._validate_citations(
                sanitized,
                context.sources_used
            )
        
        # 5. Final safety check
        is_safe = (
            len(warnings) == 0 or
            all("redacted" in w.lower() or "removed" in w.lower() for w in warnings)
        )
        
        return SanitizedOutput(
            original_output=output,
            sanitized_output=sanitized,
            citations=citations,
            warnings=warnings,
            removed_urls=removed_urls,
            is_safe=is_safe,
        )
    
    def _validate_citations(
        self,
        output: str,
        sources: List[Citation],
    ) -> List[Citation]:
        """
        Validate that citations in output match provided sources.
        
        Args:
            output: Output text
            sources: List of valid sources
            
        Returns:
            List of valid citations
        """
        valid_citations = []
        
        # Look for citation patterns like [1], [source:doc.md], etc.
        citation_patterns = [
            r'\[(\d+)\]',  # [1], [2], etc.
            r'\[source:([^\]]+)\]',  # [source:doc.md]
            r'\[ref:([^\]]+)\]',  # [ref:doc.md]
        ]
        
        for pattern in citation_patterns:
            matches = re.findall(pattern, output)
            
            for match in matches:
                # Try to find matching source
                for source in sources:
                    if match == source.source_id or match in source.source_path:
                        if source not in valid_citations:
                            valid_citations.append(source)
        
        return valid_citations
    
    def add_allowed_domain(self, domain: str) -> None:
        """
        Add a domain to the allowed list.
        
        Args:
            domain: Domain to allow
        """
        self.allowed_url_domains.add(domain)
    
    def remove_allowed_domain(self, domain: str) -> None:
        """
        Remove a domain from the allowed list.
        
        Args:
            domain: Domain to remove
        """
        self.allowed_url_domains.discard(domain)
    
    def add_secret_pattern(self, pattern: str) -> None:
        """
        Add a custom secret pattern.
        
        Args:
            pattern: Regex pattern to add
        """
        self._secret_patterns.append(re.compile(pattern))
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get sanitizer statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            "allow_external_urls": self.allow_external_urls,
            "allowed_domains": list(self.allowed_url_domains),
            "secret_pattern_count": len(self._secret_patterns),
            "content_filter": self.content_filter.get_stats(),
        }
