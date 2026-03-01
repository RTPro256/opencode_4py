"""
Help overlay widget for displaying keyboard shortcuts.

Shows a modal overlay with all available keyboard shortcuts.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static

try:
    from textual.widgets import Table
except ImportError:
    Table = None


class HelpScreen(ModalScreen):
    """
    A modal screen showing keyboard shortcuts.
    """
    
    DEFAULT_CSS = """
    HelpScreen {
        background: $panel 90%;
    }
    
    HelpScreen .help-container {
        width: 60;
        height: auto;
        max-height: 80%;
        background: $surface;
        border: solid $primary;
        padding: 1 2;
    }
    
    HelpScreen .title {
        text-style: bold;
        text-align: center;
        color: $primary;
        margin-bottom: 1;
    }
    
    HelpScreen Table {
        margin: 1 0;
    }
    
    HelpScreen Table > .table--fixed {
        height: auto;
    }
    
    HelpScreen .close-button {
        align: center middle;
        margin-top: 1;
    }
    """
    
    # Keyboard shortcuts to display
    SHORTCUTS = [
        ("Ctrl+N", "New Session"),
        ("Ctrl+S", "Save Session"),
        ("Ctrl+O", "Open Session"),
        ("Ctrl+Q", "Quit"),
        ("Ctrl+M", "Change Model"),
        ("Ctrl+Shift+M", "Change Mode"),
        ("Ctrl+T", "Toggle Debug Logs"),
        ("Ctrl+L", "View Logs"),
        ("Ctrl+P", "Command Palette"),
        ("F1", "Show Help"),
        ("Escape", "Stop/Cancel"),
        ("Ctrl+C", "Stop Processing"),
        ("?", "Toggle Help"),
        ("/", "Focus Search"),
        ("j/k", "Navigate Up/Down"),
        ("Enter", "Send Message"),
        ("Shift+Enter", "New Line"),
    ]
    
    # Quick commands - slash commands available in chat
    QUICK_COMMANDS = [
        ("/help", "Show this help"),
        ("/index", "Show PROJECT_INDEX.md summary"),
        ("/plans", "Show PLAN_INDEX.md summary"),
        ("/docs", "Show DOCS_INDEX.md summary"),
        ("/files", "Show all Python files with summaries"),
        ("/tools", "Show all available tools"),
        ("/agents", "Show all agents"),
        ("/mode", "Show/change current mode"),
        ("/memory", "Show session memory"),
        ("/clear", "Clear chat history"),
    ]
    
    # Project-specific index files to check
    PROJECT_INDEX_FILES = [
        "COMFYUI_INDEX.md",
        "OPENCODE_4PY_README.md",
        "PROJECT_INDEX.md",
        "INDEX.md",
        "README.md",
    ]
    
    def _get_project_info(self) -> list[str]:
        """
        Get project-specific index file info if available.
        
        Generic - works for any project with index files.
        """
        info = []
        
        # Find project root using generic detection
        project_root = self._find_project_root(Path.cwd())
        
        if not project_root or not project_root.exists():
            return info
        
        # Check for project-specific index files
        for index_file in self.PROJECT_INDEX_FILES:
            index_path = project_root / index_file
            if index_path.exists():
                try:
                    content = index_path.read_text(encoding='utf-8', errors='ignore')
                    # Get first meaningful lines (skip title/headers)
                    lines = content.split('\n')[1:20]  # Skip title, get next 20 lines
                    title = index_path.stem.replace('_', ' ').replace('-', ' ')
                    info.append(f"\n[bold yellow]📁 {title}[/bold yellow]")
                    for line in lines[:5]:
                        line = line.strip()
                        if line and not line.startswith('#') and not line.startswith('---'):
                            # Truncate long lines
                            if len(line) > 50:
                                line = line[:47] + "..."
                            info.append(f"   {line}")
                except Exception:
                    pass
        
        return info
    
    def _find_project_root(self, start_path: Path) -> Optional[Path]:
        """
        Find the project root by looking for common project markers.
        
        Generic method that works for any project type.
        """
        markers = [
            "ComfyUI_windows_portable",
            "opencode.toml",
            "pyproject.toml",
            "package.json",
            ".git",
        ]
        
        # Check if starting path is the root
        for marker in markers:
            if (start_path / marker).exists():
                return start_path
        
        # Check parent directories (max 5 levels up)
        current = start_path
        for _ in range(5):
            for marker in markers:
                if (current / marker).exists():
                    return current
            parent = current.parent
            if parent == current:  # Reached root
                break
            current = parent
        
        # Fall back to starting path
        return start_path if start_path.exists() else None
    
    def _get_comfyui_info(self) -> list[str]:
        """Get ComfyUI-specific help info if running in ComfyUI context."""
        # This is now handled generically by _get_project_info()
        # Keeping for backwards compatibility but it does nothing extra
        return []
    
    def compose(self) -> ComposeResult:
        """Compose the help screen."""
        with Vertical(classes="help-container"):
            yield Static("⌨️ Keyboard Shortcuts", classes="title")
            yield Static("")
            
            # Create table manually since Table widget might not be available
            for key, action in self.SHORTCUTS:
                yield Static(f"  [bold cyan]{key:<15}[/bold cyan]  {action}")
            
            yield Static("")
            yield Static("📝 Quick Commands (type in chat)", classes="title")
            yield Static("")
            
            for cmd, desc in self.QUICK_COMMANDS:
                yield Static(f"  [bold green]{cmd:<12}[/bold green]  {desc}")
            
            # Add project-specific info
            project_info = self._get_project_info()
            for line in project_info:
                yield Static(line)
            
            # Add ComfyUI-specific info
            comfyui_info = self._get_comfyui_info()
            for line in comfyui_info:
                yield Static(line)
            
            yield Static("")
            yield Static("[dim]Press Escape or ? to close[/dim]", classes="close-button")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Close the help screen when button is pressed."""
        self.dismiss()
    
    def on_key(self, event) -> None:
        """Close on Escape or ? key."""
        if event.key in ("escape", "question_mark", "?"):
            self.dismiss()


class CommandPalette(ModalScreen):
    """
    A command palette for quick actions.
    """
    
    DEFAULT_CSS = """
    CommandPalette {
        align: center middle;
    }
    
    CommandPalette .palette {
        width: 50;
        height: auto;
        background: $surface;
        border: solid $accent;
    }
    
    CommandPalette Input {
        margin: 1;
    }
    
    CommandPalette .results {
        height: 10;
        margin: 0 1 1 1;
    }
    """
    
    def __init__(self, commands: list[tuple[str, str]] = None, **kwargs):
        super().__init__(**kwargs)
        self.commands = commands or [
            ("New Session", "Create a new chat session"),
            ("Save Session", "Save current session"),
            ("Toggle Theme", "Switch between light/dark theme"),
            ("Clear Chat", "Clear all messages"),
            ("Show Shortcuts", "Display keyboard shortcuts"),
            ("Settings", "Open settings"),
        ]
    
    def compose(self) -> ComposeResult:
        """Compose the command palette."""
        with Container(classes="palette"):
            yield Static("🔍 Command Palette", classes="title")
            yield Static("Type a command...", id="placeholder")
    
    def on_mount(self) -> None:
        """Focus the input on mount."""
        pass  # Input focus would be handled here


def get_shortcuts_text() -> str:
    """Get a text representation of shortcuts for display."""
    lines = ["[bold]Keyboard Shortcuts[/bold]", ""]
    for key, action in HelpScreen.SHORTCUTS:
        lines.append(f"  [cyan]{key:<15}[/cyan]  {action}")
    
    # Add quick commands section
    lines.append("")
    lines.append("[bold]Quick Commands[/bold]")
    lines.append("")
    for cmd, desc in HelpScreen.QUICK_COMMANDS:
        lines.append(f"  [green]{cmd:<12}[/green]  {desc}")
    
    return "\n".join(lines)
