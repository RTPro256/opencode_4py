"""
Help overlay widget for displaying keyboard shortcuts.

Shows a modal overlay with all available keyboard shortcuts.
"""

from __future__ import annotations

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
    
    def compose(self) -> ComposeResult:
        """Compose the help screen."""
        with Vertical(classes="help-container"):
            yield Static("⌨️ Keyboard Shortcuts", classes="title")
            yield Static("")
            
            # Create table manually since Table widget might not be available
            for key, action in self.SHORTCUTS:
                yield Static(f"  [bold cyan]{key:<15}[/bold cyan]  {action}")
            
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
    return "\n".join(lines)
