"""
Mention Processing

Handles @mentions in messages for referencing files, people, and entities.
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class MentionType(Enum):
    """Types of mentions."""
    FILE = "file"
    DIRECTORY = "directory"
    PERSON = "person"
    TOOL = "tool"
    MODE = "mode"
    SKILL = "skill"
    VARIABLE = "variable"
    URL = "url"


@dataclass
class Mention:
    """A parsed mention."""
    mention_type: MentionType
    value: str
    raw_text: str
    start_pos: int
    end_pos: int
    resolved: bool = False
    resolved_value: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "mention_type": self.mention_type.value,
            "value": self.value,
            "raw_text": self.raw_text,
            "start_pos": self.start_pos,
            "end_pos": self.end_pos,
            "resolved": self.resolved,
            "resolved_value": self.resolved_value,
            "metadata": self.metadata,
        }


@dataclass
class ProcessedMentions:
    """Result of processing mentions in text."""
    original_text: str
    processed_text: str
    mentions: List[Mention]
    
    @property
    def file_mentions(self) -> List[Mention]:
        """Get all file mentions."""
        return [m for m in self.mentions if m.mention_type == MentionType.FILE]
    
    @property
    def directory_mentions(self) -> List[Mention]:
        """Get all directory mentions."""
        return [m for m in self.mentions if m.mention_type == MentionType.DIRECTORY]
    
    @property
    def tool_mentions(self) -> List[Mention]:
        """Get all tool mentions."""
        return [m for m in self.mentions if m.mention_type == MentionType.TOOL]
    
    @property
    def mode_mentions(self) -> List[Mention]:
        """Get all mode mentions."""
        return [m for m in self.mentions if m.mention_type == MentionType.MODE]
    
    @property
    def skill_mentions(self) -> List[Mention]:
        """Get all skill mentions."""
        return [m for m in self.mentions if m.mention_type == MentionType.SKILL]


class MentionProcessor:
    """
    Processes @mentions in text.
    
    Handles various types of mentions:
    - @file:path - File references
    - @dir:path - Directory references
    - @tool:name - Tool references
    - @mode:name - Mode references
    - @skill:name - Skill references
    - @person:name - Person references
    - @variable:name - Variable references
    - @url:url - URL references
    
    Example:
        processor = MentionProcessor(workspace_root="/project")
        result = processor.process("Read @file:src/main.py and check @dir:tests")
        
        for mention in result.file_mentions:
            print(f"File: {mention.value}")
    """
    
    # Regex patterns for different mention types
    PATTERNS = {
        MentionType.FILE: re.compile(r'@file:([^\s]+)'),
        MentionType.DIRECTORY: re.compile(r'@dir:([^\s]+)'),
        MentionType.TOOL: re.compile(r'@tool:([^\s]+)'),
        MentionType.MODE: re.compile(r'@mode:([^\s]+)'),
        MentionType.SKILL: re.compile(r'@skill:([^\s]+)'),
        MentionType.PERSON: re.compile(r'@person:([^\s]+)'),
        MentionType.VARIABLE: re.compile(r'@var:([^\s]+)'),
        MentionType.URL: re.compile(r'@url:([^\s]+)'),
    }
    
    # Generic @mention pattern (for people)
    GENERIC_MENTION = re.compile(r'@([a-zA-Z][a-zA-Z0-9_-]*)')
    
    def __init__(
        self,
        workspace_root: Optional[str] = None,
        resolve_files: bool = True,
        resolve_urls: bool = True,
    ):
        """
        Initialize the mention processor.
        
        Args:
            workspace_root: Root directory for resolving file paths
            resolve_files: Whether to resolve file paths
            resolve_urls: Whether to resolve URLs
        """
        self.workspace_root = Path(workspace_root) if workspace_root else None
        self.resolve_files = resolve_files
        self.resolve_urls = resolve_urls
    
    def process(self, text: str) -> ProcessedMentions:
        """
        Process all mentions in text.
        
        Args:
            text: Text to process
            
        Returns:
            ProcessedMentions with all found mentions
        """
        mentions = self._extract_all_mentions(text)
        
        # Resolve mentions
        for mention in mentions:
            self._resolve_mention(mention)
        
        # Build processed text
        processed_text = self._build_processed_text(text, mentions)
        
        return ProcessedMentions(
            original_text=text,
            processed_text=processed_text,
            mentions=mentions,
        )
    
    def _extract_all_mentions(self, text: str) -> List[Mention]:
        """Extract all mentions from text."""
        mentions: List[Mention] = []
        
        # Extract typed mentions
        for mention_type, pattern in self.PATTERNS.items():
            for match in pattern.finditer(text):
                mentions.append(Mention(
                    mention_type=mention_type,
                    value=match.group(1),
                    raw_text=match.group(0),
                    start_pos=match.start(),
                    end_pos=match.end(),
                ))
        
        # Extract generic mentions (that aren't already typed)
        typed_positions = set()
        for m in mentions:
            typed_positions.update(range(m.start_pos, m.end_pos))
        
        for match in self.GENERIC_MENTION.finditer(text):
            # Skip if overlaps with typed mention
            if any(pos in typed_positions for pos in range(match.start(), match.end())):
                continue
            
            mentions.append(Mention(
                mention_type=MentionType.PERSON,
                value=match.group(1),
                raw_text=match.group(0),
                start_pos=match.start(),
                end_pos=match.end(),
            ))
        
        # Sort by position
        mentions.sort(key=lambda m: m.start_pos)
        
        return mentions
    
    def _resolve_mention(self, mention: Mention) -> None:
        """Resolve a mention to its actual value."""
        if mention.mention_type == MentionType.FILE:
            self._resolve_file_mention(mention)
        elif mention.mention_type == MentionType.DIRECTORY:
            self._resolve_directory_mention(mention)
        elif mention.mention_type == MentionType.URL:
            self._resolve_url_mention(mention)
        # Other types don't need resolution
    
    def _resolve_file_mention(self, mention: Mention) -> None:
        """Resolve a file mention."""
        if not self.resolve_files or not self.workspace_root:
            return
        
        file_path = self.workspace_root / mention.value
        
        if file_path.exists() and file_path.is_file():
            mention.resolved = True
            mention.resolved_value = str(file_path.resolve())
            mention.metadata["exists"] = True
            mention.metadata["size"] = file_path.stat().st_size
        else:
            mention.resolved = False
            mention.metadata["exists"] = False
    
    def _resolve_directory_mention(self, mention: Mention) -> None:
        """Resolve a directory mention."""
        if not self.resolve_files or not self.workspace_root:
            return
        
        dir_path = self.workspace_root / mention.value
        
        if dir_path.exists() and dir_path.is_dir():
            mention.resolved = True
            mention.resolved_value = str(dir_path.resolve())
            mention.metadata["exists"] = True
            # List files in directory
            try:
                files = list(dir_path.iterdir())[:20]  # Limit to 20
                mention.metadata["files"] = [f.name for f in files]
            except PermissionError:
                mention.metadata["files"] = []
        else:
            mention.resolved = False
            mention.metadata["exists"] = False
    
    def _resolve_url_mention(self, mention: Mention) -> None:
        """Resolve a URL mention."""
        if not self.resolve_urls:
            return
        
        # For now, just mark as resolved
        # Could fetch URL content in the future
        mention.resolved = True
        mention.resolved_value = mention.value
    
    def _build_processed_text(self, text: str, mentions: List[Mention]) -> str:
        """Build processed text with resolved mentions."""
        if not mentions:
            return text
        
        # Build text with resolved values
        result = []
        last_end = 0
        
        for mention in mentions:
            # Add text before mention
            result.append(text[last_end:mention.start_pos])
            
            # Add resolved or original mention
            if mention.resolved and mention.resolved_value:
                result.append(mention.resolved_value)
            else:
                result.append(mention.raw_text)
            
            last_end = mention.end_pos
        
        # Add remaining text
        result.append(text[last_end:])
        
        return "".join(result)
    
    def extract_files(self, text: str) -> List[str]:
        """
        Extract file paths from mentions.
        
        Args:
            text: Text to process
            
        Returns:
            List of file paths
        """
        result = self.process(text)
        return [m.value for m in result.file_mentions]
    
    def extract_directories(self, text: str) -> List[str]:
        """
        Extract directory paths from mentions.
        
        Args:
            text: Text to process
            
        Returns:
            List of directory paths
        """
        result = self.process(text)
        return [m.value for m in result.directory_mentions]
    
    def replace_mentions(
        self,
        text: str,
        replacement: str,
        mention_type: Optional[MentionType] = None,
    ) -> str:
        """
        Replace mentions with a string.
        
        Args:
            text: Text to process
            replacement: Replacement string
            mention_type: Only replace this type (all if None)
            
        Returns:
            Text with mentions replaced
        """
        result = self.process(text)
        
        if mention_type:
            mentions = [m for m in result.mentions if m.mention_type == mention_type]
        else:
            mentions = result.mentions
        
        # Sort by position (reverse) to replace from end
        mentions.sort(key=lambda m: m.start_pos, reverse=True)
        
        processed = text
        for mention in mentions:
            processed = (
                processed[:mention.start_pos]
                + replacement
                + processed[mention.end_pos:]
            )
        
        return processed
    
    def get_mention_summary(self, text: str) -> str:
        """
        Get a summary of mentions in text.
        
        Args:
            text: Text to process
            
        Returns:
            Human-readable summary
        """
        result = self.process(text)
        
        if not result.mentions:
            return "No mentions found."
        
        lines = [f"Found {len(result.mentions)} mentions:"]
        
        # Group by type
        by_type: Dict[MentionType, List[Mention]] = {}
        for mention in result.mentions:
            if mention.mention_type not in by_type:
                by_type[mention.mention_type] = []
            by_type[mention.mention_type].append(mention)
        
        for mention_type, mentions in by_type.items():
            lines.append(f"\n{mention_type.value}:")
            for mention in mentions:
                status = "✓" if mention.resolved else "?"
                lines.append(f"  [{status}] {mention.value}")
        
        return "\n".join(lines)
