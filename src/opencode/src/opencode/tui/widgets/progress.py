"""
Progress widget for displaying long-running operations.

Provides Rich-powered progress bars and spinners for the TUI.
"""

from __future__ import annotations

from typing import Optional

from textual.widgets import Static
from textual.containers import Container
from textual.reactive import reactive


class ProgressBarWidget(Static):
    """
    A progress bar widget using Rich styling.
    
    Features:
    - Customizable progress percentage
    - Animated fill
    - Status text
    """
    
    DEFAULT_CSS = """
    ProgressBarWidget {
        height: 3;
        margin: 1 0;
    }
    
    ProgressBarWidget .progress-track {
        background: $panel;
        color: $primary;
    }
    
    ProgressBarWidget .progress-fill {
        background: $primary;
    }
    
    ProgressBarWidget .progress-text {
        color: $text;
        text-align: center;
    }
    """
    
    progress: reactive[int] = reactive(0)
    status_text: reactive[str] = reactive("")
    max_value: int = 100
    
    def __init__(
        self,
        progress: int = 0,
        status_text: str = "",
        max_value: int = 100,
        name: Optional[str] = None,
        id: Optional[str] = None,
    ) -> None:
        super().__init__(name=name, id=id)
        self.progress = progress
        self.status_text = status_text
        self.max_value = max_value
    
    def watch_progress(self, progress: int) -> None:
        """Update display when progress changes."""
        self.refresh()
    
    def watch_status_text(self, status_text: str) -> None:
        """Update display when status changes."""
        self.refresh()
    
    def set_progress(self, progress: int) -> None:
        """Set the current progress value."""
        self.progress = max(0, min(progress, self.max_value))
    
    def set_status(self, status_text: str) -> None:
        """Set the status text."""
        self.status_text = status_text
    
    def increment(self, amount: int = 1) -> None:
        """Increment progress by the given amount."""
        self.set_progress(self.progress + amount)
    
    def complete(self) -> None:
        """Set progress to max (complete)."""
        self.set_progress(self.max_value)
    
    def reset(self) -> None:
        """Reset progress to 0."""
        self.progress = 0
        self.status_text = ""
    
    def render(self) -> str:
        """Render the progress bar."""
        filled = int(self.progress * 20 / self.max_value)
        empty = 20 - filled
        bar = "█" * filled + "░" * empty
        percentage = int(self.progress * 100 / self.max_value) if self.max_value > 0 else 0
        
        status = self.status_text if self.status_text else f"{percentage}%"
        
        return f"[primary]{bar}[/primary] {status}"


class SpinnerWidget(Static):
    """
    An animated spinner widget for loading states.
    """
    
    DEFAULT_CSS = """
    SpinnerWidget {
        margin: 1;
    }
    
    SpinnerWidget .spinner-text {
        color: $primary;
    }
    """
    
    is_spinning: reactive[bool] = reactive(True)
    text: reactive[str] = reactive("Loading...")
    
    # Spinner frames
    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    def __init__(
        self,
        text: str = "Loading...",
        is_spinning: bool = True,
        name: Optional[str] = None,
        id: Optional[str] = None,
    ) -> None:
        super().__init__(name=name, id=id)
        self.text = text
        self.is_spinning = is_spinning
        self._frame_index = 0
    
    def watch_is_spinning(self, spinning: bool) -> None:
        """Handle spinning state change."""
        self.refresh()
    
    def watch_text(self, text: str) -> None:
        """Handle text change."""
        self.refresh()
    
    def start(self) -> None:
        """Start the spinner."""
        self.is_spinning = True
    
    def stop(self) -> None:
        """Stop the spinner."""
        self.is_spinning = False
    
    def render(self) -> str:
        """Render the spinner."""
        if not self.is_spinning:
            return f"✓ {self.text}"
        
        frame = self.FRAMES[self._frame_index % len(self.FRAMES)]
        self._frame_index += 1
        
        return f"[primary]{frame}[/primary] {self.text}"


class StatusIndicator(Static):
    """
    A status indicator with colored dots.
    """
    
    DEFAULT_CSS = """
    StatusIndicator {
        margin: 0 1;
    }
    """
    
    status: reactive[str] = reactive("unknown")
    label: reactive[str] = reactive("")
    
    STATUS_COLORS = {
        "ok": "green",
        "success": "green",
        "running": "cyan",
        "active": "cyan",
        "warning": "yellow",
        "warn": "yellow",
        "error": "red",
        "fail": "red",
        "unknown": "white",
        "idle": "white",
    }
    
    STATUS_ICONS = {
        "ok": "●",
        "success": "●",
        "running": "◐",
        "active": "◉",
        "warning": "⚠",
        "warn": "⚠",
        "error": "✕",
        "fail": "✕",
        "unknown": "○",
        "idle": "○",
    }
    
    def __init__(
        self,
        status: str = "unknown",
        label: str = "",
        name: Optional[str] = None,
        id: Optional[str] = None,
    ) -> None:
        super().__init__(name=name, id=id)
        self.status = status
        self.label = label
    
    def watch_status(self, status: str) -> None:
        """Handle status change."""
        self.refresh()
    
    def watch_label(self, label: str) -> None:
        """Handle label change."""
        self.refresh()
    
    def set_status(self, status: str) -> None:
        """Set the status."""
        self.status = status.lower()
    
    def set_label(self, label: str) -> None:
        """Set the label."""
        self.label = label
    
    def render(self) -> str:
        """Render the status indicator."""
        color = self.STATUS_COLORS.get(self.status, "white")
        icon = self.STATUS_ICONS.get(self.status, "○")
        
        if self.label:
            return f"[{color}]{icon}[/{color}] {self.label}"
        return f"[{color}]{icon}[/{color}]"
