"""
Auto-completion Widget

Provides auto-completion for paths, commands, and mentions in the TUI.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
import logging
import re

from textual.widget import Widget
from textual.message import Message
from textual.reactive import reactive

logger = logging.getLogger(__name__)


@dataclass
class CompletionItem:
    """A completion suggestion."""
    text: str
    display: str
    description: Optional[str] = None
    category: str = "general"
    priority: int = 0
    insert_text: Optional[str] = None  # Text to insert (if different from display)
    
    def __lt__(self, other: "CompletionItem") -> bool:
        # Higher priority first, then alphabetically
        if self.priority != other.priority:
            return self.priority > other.priority
        return self.display.lower() < other.display.lower()


class CompletionProvider:
    """
    Base class for completion providers.
    
    A completion provider generates suggestions for a specific type
    of completion (paths, commands, mentions, etc.).
    """
    
    @property
    def name(self) -> str:
        """Provider name."""
        return "base"
    
    def get_completions(
        self,
        text: str,
        cursor_position: int,
        context: Dict[str, Any],
    ) -> List[CompletionItem]:
        """
        Get completions for the current input.
        
        Args:
            text: Current input text
            cursor_position: Cursor position in text
            context: Additional context (workspace root, etc.)
            
        Returns:
            List of completion items
        """
        return []
    
    def get_trigger_chars(self) -> List[str]:
        """Characters that trigger this provider."""
        return []


class PathCompletionProvider(CompletionProvider):
    """
    Provides file and directory path completions.
    
    Example:
        provider = PathCompletionProvider(workspace_root="/project")
        completions = provider.get_completions("src/ope", 7, {})
        # Returns completions for paths starting with "src/ope"
    """
    
    @property
    def name(self) -> str:
        return "path"
    
    def __init__(self, workspace_root: Optional[str] = None):
        self.workspace_root = Path(workspace_root) if workspace_root else None
    
    def get_trigger_chars(self) -> List[str]:
        return ["/", "./", "~"]
    
    def get_completions(
        self,
        text: str,
        cursor_position: int,
        context: Dict[str, Any],
    ) -> List[CompletionItem]:
        """Get path completions."""
        workspace = Path(context.get("workspace_root", self.workspace_root or "."))
        
        # Find path being typed
        path_match = self._find_path_at_cursor(text, cursor_position)
        if not path_match:
            return []
        
        path_start, partial_path = path_match
        
        # Resolve the directory and partial name
        if partial_path.startswith("~"):
            base_dir = Path.home()
            partial = partial_path[1:].lstrip("/")
        elif partial_path.startswith("/"):
            base_dir = Path("/")
            partial = partial_path.lstrip("/")
        else:
            base_dir = workspace
            partial = partial_path
        
        # Get directory and prefix
        if "/" in partial:
            dir_part = partial.rsplit("/", 1)[0]
            prefix = partial.rsplit("/", 1)[1]
            search_dir = base_dir / dir_part
        else:
            search_dir = base_dir
            prefix = partial
        
        # List matching items
        completions = []
        try:
            if search_dir.exists() and search_dir.is_dir():
                for item in search_dir.iterdir():
                    if item.name.startswith(prefix):
                        is_dir = item.is_dir()
                        completions.append(CompletionItem(
                            text=str(item.relative_to(workspace)) if not str(item).startswith("/") else str(item),
                            display=item.name + ("/" if is_dir else ""),
                            description="directory" if is_dir else "file",
                            category="path",
                            priority=10 if is_dir else 5,
                        ))
        except PermissionError:
            pass
        
        return sorted(completions)
    
    def _find_path_at_cursor(self, text: str, cursor: int) -> Optional[Tuple[int, str]]:
        """Find path being typed at cursor position."""
        # Look for path pattern before cursor
        before_cursor = text[:cursor]
        
        # Match paths starting with /, ./, ~, or just alphanumeric
        patterns = [
            r'(/[^\s]*)$',       # Absolute path
            r'(\./[^\s]*)$',     # Relative path ./
            r'(~/[^\s]*)$',      # Home path
            r'(\b[a-zA-Z0-9_\-./]+)$',  # Relative path without ./
        ]
        
        for pattern in patterns:
            match = re.search(pattern, before_cursor)
            if match:
                return match.start(1), match.group(1)
        
        return None


class CommandCompletionProvider(CompletionProvider):
    """
    Provides slash command completions.
    """
    
    @property
    def name(self) -> str:
        return "command"
    
    def __init__(self, commands: Optional[Dict[str, Any]] = None):
        self.commands = commands or {}
    
    def get_trigger_chars(self) -> List[str]:
        return ["/"]
    
    def get_completions(
        self,
        text: str,
        cursor_position: int,
        context: Dict[str, Any],
    ) -> List[CompletionItem]:
        """Get command completions."""
        # Check if we're at the start of a command
        before_cursor = text[:cursor_position]
        
        # Match /command pattern
        match = re.search(r'^/(\w*)$', before_cursor)
        if not match:
            # Also match /command in middle of text after newline
            match = re.search(r'\n/(\w*)$', before_cursor)
        
        if not match:
            return []
        
        prefix = match.group(1)
        
        completions = []
        for cmd, info in self.commands.items():
            if cmd.startswith(prefix):
                completions.append(CompletionItem(
                    text=f"/{cmd}",
                    display=f"/{cmd}",
                    description=info.get("description", ""),
                    category="command",
                    priority=10,
                ))
        
        return sorted(completions)


class MentionCompletionProvider(CompletionProvider):
    """
    Provides @mention completions for files, people, etc.
    """
    
    @property
    def name(self) -> str:
        return "mention"
    
    def __init__(self, workspace_root: Optional[str] = None):
        self.workspace_root = Path(workspace_root) if workspace_root else None
        self._file_cache: List[str] = []
    
    def get_trigger_chars(self) -> List[str]:
        return ["@"]
    
    def get_completions(
        self,
        text: str,
        cursor_position: int,
        context: Dict[str, Any],
    ) -> List[CompletionItem]:
        """Get mention completions."""
        before_cursor = text[:cursor_position]
        
        # Match @mention patterns
        patterns = [
            r'@file:([^\s]*)$',    # @file:path
            r'@dir:([^\s]*)$',     # @dir:path
            r'@(\w*)$',            # @person
        ]
        
        completions = []
        
        for pattern in patterns:
            match = re.search(pattern, before_cursor)
            if match:
                prefix = match.group(1)
                mention_type = "file" if "file:" in pattern else ("dir" if "dir:" in pattern else "person")
                
                if mention_type in ("file", "dir"):
                    completions.extend(self._get_path_mentions(prefix, mention_type, context))
                else:
                    completions.extend(self._get_person_mentions(prefix, context))
                
                break
        
        return sorted(completions)
    
    def _get_path_mentions(
        self,
        prefix: str,
        mention_type: str,
        context: Dict[str, Any],
    ) -> List[CompletionItem]:
        """Get path-based mention completions."""
        workspace = Path(context.get("workspace_root", self.workspace_root or "."))
        
        completions = []
        prefix_lower = prefix.lower()
        
        # Search for matching files
        try:
            for file_path in workspace.rglob("*"):
                if prefix_lower in str(file_path.relative_to(workspace)).lower():
                    is_dir = file_path.is_dir()
                    if mention_type == "dir" and not is_dir:
                        continue
                    
                    completions.append(CompletionItem(
                        text=f"@{mention_type}:{file_path.relative_to(workspace)}",
                        display=f"@{mention_type}:{file_path.relative_to(workspace)}",
                        description="directory" if is_dir else "file",
                        category="mention",
                        priority=5,
                    ))
                    
                    if len(completions) >= 20:
                        break
        except Exception:
            pass
        
        return completions
    
    def _get_person_mentions(
        self,
        prefix: str,
        context: Dict[str, Any],
    ) -> List[CompletionItem]:
        """Get person mention completions."""
        # This could be extended to include actual people from git history, etc.
        people = context.get("people", [])
        
        completions = []
        prefix_lower = prefix.lower()
        
        for person in people:
            if prefix_lower in person.lower():
                completions.append(CompletionItem(
                    text=f"@{person}",
                    display=f"@{person}",
                    description="person",
                    category="mention",
                    priority=5,
                ))
        
        return completions
    
    def refresh_file_cache(self, workspace: Path) -> None:
        """Refresh the file cache for faster completions."""
        self._file_cache = []
        try:
            for file_path in workspace.rglob("*"):
                self._file_cache.append(str(file_path.relative_to(workspace)))
        except Exception:
            pass


class CompletionManager:
    """
    Manages multiple completion providers.
    
    Example:
        manager = CompletionManager()
        manager.add_provider(PathCompletionProvider())
        manager.add_provider(CommandCompletionProvider())
        
        completions = manager.get_completions("/src/ope", 8, {})
    """
    
    def __init__(self):
        self._providers: List[CompletionProvider] = []
    
    def add_provider(self, provider: CompletionProvider) -> None:
        """Add a completion provider."""
        self._providers.append(provider)
    
    def remove_provider(self, name: str) -> bool:
        """Remove a provider by name."""
        for i, provider in enumerate(self._providers):
            if provider.name == name:
                del self._providers[i]
                return True
        return False
    
    def get_completions(
        self,
        text: str,
        cursor_position: int,
        context: Dict[str, Any],
    ) -> List[CompletionItem]:
        """
        Get all completions from all providers.
        
        Args:
            text: Current input text
            cursor_position: Cursor position
            context: Additional context
            
        Returns:
            Combined and sorted list of completions
        """
        all_completions = []
        
        for provider in self._providers:
            try:
                completions = provider.get_completions(text, cursor_position, context)
                all_completions.extend(completions)
            except Exception as e:
                logger.error(f"Completion provider {provider.name} error: {e}")
        
        # Sort and deduplicate
        seen = set()
        unique_completions = []
        
        for item in sorted(all_completions):
            if item.text not in seen:
                seen.add(item.text)
                unique_completions.append(item)
        
        return unique_completions[:50]  # Limit to 50 items
    
    def should_trigger(self, char: str) -> bool:
        """Check if a character should trigger completions."""
        for provider in self._providers:
            if char in provider.get_trigger_chars():
                return True
        return False


class CompletionWidget(Widget):
    """
    Textual widget for displaying completions.
    
    Shows a dropdown list of completion suggestions that can be
    navigated with arrow keys and selected with Enter/Tab.
    """
    
    DEFAULT_CSS = """
    CompletionWidget {
        display: none;
        background: $surface;
        border: solid $primary;
        height: auto;
        max-height: 15;
        overflow-y: auto;
    }
    
    CompletionWidget.visible {
        display: block;
    }
    
    CompletionWidget .completion-item {
        padding: 0 1;
    }
    
    CompletionWidget .completion-item.selected {
        background: $primary;
        color: $text-on-primary;
    }
    
    CompletionWidget .completion-description {
        color: $text-muted;
        text-style: italic;
    }
    """
    
    completions: reactive[List[CompletionItem]] = reactive([])
    selected_index: reactive[int] = reactive(0)
    visible: reactive[bool] = reactive(False)
    
    class Selected(Message):
        """Message sent when a completion is selected."""
        def __init__(self, item: CompletionItem):
            self.item = item
            super().__init__()
    
    class Cancelled(Message):
        """Message sent when completion is cancelled."""
        pass
    
    def __init__(
        self,
        manager: Optional[CompletionManager] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.manager = manager or CompletionManager()
    
    def show_completions(
        self,
        text: str,
        cursor_position: int,
        context: Dict[str, Any],
    ) -> None:
        """Show completions for the current input."""
        self.completions = self.manager.get_completions(text, cursor_position, context)
        self.selected_index = 0
        self.visible = len(self.completions) > 0
    
    def hide(self) -> None:
        """Hide the completion widget."""
        self.visible = False
        self.completions = []
    
    def select_next(self) -> None:
        """Select the next completion."""
        if self.completions:
            self.selected_index = (self.selected_index + 1) % len(self.completions)
    
    def select_previous(self) -> None:
        """Select the previous completion."""
        if self.completions:
            self.selected_index = (self.selected_index - 1) % len(self.completions)
    
    def confirm_selection(self) -> Optional[CompletionItem]:
        """Confirm the current selection."""
        if self.visible and self.completions:
            item = self.completions[self.selected_index]
            self.post_message(self.Selected(item))
            self.hide()
            return item
        return None
    
    def cancel(self) -> None:
        """Cancel completion."""
        self.post_message(self.Cancelled())
        self.hide()
    
    def render(self) -> str:
        """Render the completion widget."""
        if not self.visible or not self.completions:
            return ""
        
        lines = []
        for i, item in enumerate(self.completions):
            is_selected = i == self.selected_index
            css_class = "selected" if is_selected else ""
            
            line = f"[{css_class}] {item.display}"
            if item.description:
                line += f" [{item.description}]"
            
            lines.append(line)
        
        return "\n".join(lines)
