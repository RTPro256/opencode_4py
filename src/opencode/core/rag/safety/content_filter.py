"""
Content Filter for Privacy-First RAG.

Filters sensitive content from RAG operations to prevent data leakage.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Redaction:
    """Information about a redaction."""
    
    pattern_name: str
    """Name of the pattern that matched."""
    
    original_length: int
    """Length of the original matched text."""
    
    start_position: int
    """Start position in the original text."""
    
    redacted_text: str
    """The redacted replacement text."""


@dataclass
class FilteredContent:
    """Result of content filtering."""
    
    original_content: str
    """The original content before filtering."""
    
    filtered_content: str
    """The filtered content with redactions."""
    
    redactions: List[Redaction] = field(default_factory=list)
    """List of redactions made."""
    
    is_safe: bool = True
    """Whether the content is safe (no sensitive data detected)."""
    
    warnings: List[str] = field(default_factory=list)
    """Warning messages about potential issues."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "filtered_content": self.filtered_content,
            "is_safe": self.is_safe,
            "redaction_count": len(self.redactions),
            "redactions": [
                {
                    "pattern": r.pattern_name,
                    "position": r.start_position,
                    "length": r.original_length,
                }
                for r in self.redactions
            ],
            "warnings": self.warnings,
        }


class SensitivePattern:
    """A sensitive pattern to detect and redact."""
    
    def __init__(
        self,
        name: str,
        pattern: str,
        description: str = "",
        redact_with: str = "[REDACTED]",
    ):
        """
        Initialize a sensitive pattern.
        
        Args:
            name: Pattern name for identification
            pattern: Regex pattern to match
            description: Human-readable description
            redact_with: Text to replace matches with
        """
        self.name = name
        self.pattern = re.compile(pattern, re.IGNORECASE)
        self.description = description
        self.redact_with = redact_with


# Default sensitive patterns
DEFAULT_SENSITIVE_PATTERNS = [
    SensitivePattern(
        name="password",
        pattern=r"password\s*[:=]\s*\S+",
        description="Password values",
        redact_with="[PASSWORD_REDACTED]",
    ),
    SensitivePattern(
        name="api_key",
        pattern=r"api[_-]?key\s*[:=]\s*\S+",
        description="API key values",
        redact_with="[API_KEY_REDACTED]",
    ),
    SensitivePattern(
        name="secret",
        pattern=r"secret\s*[:=]\s*\S+",
        description="Secret values",
        redact_with="[SECRET_REDACTED]",
    ),
    SensitivePattern(
        name="token",
        pattern=r"token\s*[:=]\s*\S+",
        description="Token values",
        redact_with="[TOKEN_REDACTED]",
    ),
    SensitivePattern(
        name="private_key",
        pattern=r"-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----",
        description="Private key markers",
        redact_with="[PRIVATE_KEY_REDACTED]",
    ),
    SensitivePattern(
        name="credit_card",
        pattern=r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
        description="Credit card numbers",
        redact_with="[CC_REDACTED]",
    ),
    SensitivePattern(
        name="ssn",
        pattern=r"\b\d{3}[\s-]?\d{2}[\s-]?\d{4}\b",
        description="Social Security Numbers",
        redact_with="[SSN_REDACTED]",
    ),
    SensitivePattern(
        name="email",
        pattern=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        description="Email addresses",
        redact_with="[EMAIL_REDACTED]",
    ),
    SensitivePattern(
        name="ip_address",
        pattern=r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        description="IP addresses",
        redact_with="[IP_REDACTED]",
    ),
    SensitivePattern(
        name="aws_key",
        pattern=r"AKIA[0-9A-Z]{16}",
        description="AWS Access Key IDs",
        redact_with="[AWS_KEY_REDACTED]",
    ),
    SensitivePattern(
        name="jwt",
        pattern=r"eyJ[A-Za-z0-9-_]*\.eyJ[A-Za-z0-9-_]*\.[A-Za-z0-9-_]*",
        description="JWT tokens",
        redact_with="[JWT_REDACTED]",
    ),
]


class ContentFilter:
    """
    Filters sensitive content from RAG operations.
    
    Detects and redacts sensitive patterns like passwords, API keys,
    credit card numbers, and other PII.
    
    Example:
        ```python
        filter = ContentFilter()
        
        result = filter.filter_content(
            "My password is: secret123 and my email is user@example.com"
        )
        
        print(result.filtered_content)
        # "My password is: [PASSWORD_REDACTED] and my email is [EMAIL_REDACTED]"
        print(result.is_safe)  # False
        ```
    """
    
    def __init__(
        self,
        patterns: Optional[List[SensitivePattern]] = None,
        custom_patterns: Optional[List[Dict[str, str]]] = None,
    ):
        """
        Initialize content filter.
        
        Args:
            patterns: List of sensitive patterns (uses defaults if not provided)
            custom_patterns: Additional custom patterns to add
        """
        self.patterns = patterns or DEFAULT_SENSITIVE_PATTERNS.copy()
        
        # Add custom patterns
        if custom_patterns:
            for cp in custom_patterns:
                self.patterns.append(SensitivePattern(
                    name=cp.get("name", "custom"),
                    pattern=cp.get("pattern", ""),
                    description=cp.get("description", ""),
                    redact_with=cp.get("redact_with", "[REDACTED]"),
                ))
    
    def filter_content(self, content: str) -> FilteredContent:
        """
        Filter sensitive content from text.
        
        Args:
            content: Content to filter
            
        Returns:
            FilteredContent with redactions
        """
        filtered = content
        redactions: List[Redaction] = []
        warnings: List[str] = []
        
        for pattern in self.patterns:
            try:
                matches = list(pattern.pattern.finditer(content))
                
                for match in matches:
                    original_text = match.group()
                    start_pos = match.start()
                    
                    # Create redaction record
                    redaction = Redaction(
                        pattern_name=pattern.name,
                        original_length=len(original_text),
                        start_position=start_pos,
                        redacted_text=pattern.redact_with,
                    )
                    redactions.append(redaction)
                    
                    # Replace in filtered content
                    filtered = filtered.replace(original_text, pattern.redact_with)
                    
                    logger.debug(
                        f"Redacted {pattern.name} at position {start_pos}"
                    )
                    
            except Exception as e:
                warnings.append(f"Error processing pattern {pattern.name}: {e}")
                logger.warning(f"Error processing pattern {pattern.name}: {e}")
        
        # Sort redactions by position
        redactions.sort(key=lambda r: r.start_position)
        
        return FilteredContent(
            original_content=content,
            filtered_content=filtered,
            redactions=redactions,
            is_safe=len(redactions) == 0,
            warnings=warnings,
        )
    
    def check_content(self, content: str) -> bool:
        """
        Check if content contains sensitive data without filtering.
        
        Args:
            content: Content to check
            
        Returns:
            True if content is safe (no sensitive data)
        """
        for pattern in self.patterns:
            if pattern.pattern.search(content):
                return False
        return True
    
    def get_detected_patterns(self, content: str) -> List[str]:
        """
        Get list of detected pattern names in content.
        
        Args:
            content: Content to analyze
            
        Returns:
            List of pattern names that matched
        """
        detected = []
        
        for pattern in self.patterns:
            if pattern.pattern.search(content):
                detected.append(pattern.name)
        
        return detected
    
    def add_pattern(
        self,
        name: str,
        pattern: str,
        description: str = "",
        redact_with: str = "[REDACTED]",
    ) -> None:
        """
        Add a new sensitive pattern.
        
        Args:
            name: Pattern name
            pattern: Regex pattern
            description: Description
            redact_with: Redaction text
        """
        self.patterns.append(SensitivePattern(
            name=name,
            pattern=pattern,
            description=description,
            redact_with=redact_with,
        ))
    
    def remove_pattern(self, name: str) -> bool:
        """
        Remove a pattern by name.
        
        Args:
            name: Pattern name to remove
            
        Returns:
            True if pattern was removed
        """
        for i, pattern in enumerate(self.patterns):
            if pattern.name == name:
                self.patterns.pop(i)
                return True
        return False
    
    def get_pattern_names(self) -> List[str]:
        """
        Get list of all pattern names.
        
        Returns:
            List of pattern names
        """
        return [p.name for p in self.patterns]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get filter statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            "pattern_count": len(self.patterns),
            "patterns": self.get_pattern_names(),
        }
