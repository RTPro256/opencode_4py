"""
Sidebar widget for sessions, tools, and status.
"""

from __future__ import annotations

from typing import Optional

from textual.containers import Container, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Button, Static, Tree


class SessionItem(Button):
    """A session item in the sidebar."""
    
    DEFAULT_CSS = """
    SessionItem {
        width: 100%;
        height: auto;
        min-height: 3;
        padding: 1;
        background: $surface;
        border: none;
        text-align: left;
    }
    
    SessionItem:hover {
        background: $surface-lighten-1;
    }
    
    SessionItem.active {
        background: $primary-darken-2;
        border-left: thick $accent;
    }
    """
    
    session_id: reactive[str] = reactive("")
    session_title: reactive[str] = reactive("")
    is_active: reactive[bool] = reactive(False)
    
    class Selected(Message):
        """Message sent when a session is selected."""
        
        def __init__(self, session_id: str) -> None:
            self.session_id = session_id
            super().__init__()
    
    def __init__(
        self,
        session_id: str,
        title: str,
        *,
        is_active: bool = False,
        name: Optional[str] = None,
        id: Optional[str] = None,
    ) -> None:
        super().__init__(name=name, id=id)
        self.session_id = session_id
        self.session_title = title
        self.is_active = is_active
    
    def watch_is_active(self, is_active: bool) -> None:
        if is_active:
            self.add_class("active")
        else:
            self.remove_class("active")
    
    def render(self) -> str:
        return f"💬 {self.session_title[:30]}"
    
    def on_click(self) -> None:
        self.post_message(self.Selected(self.session_id))


class ToolItem(Button):
    """A tool item in the sidebar."""
    
    DEFAULT_CSS = """
    ToolItem {
        width: 100%;
        height: auto;
        padding: 1;
        background: transparent;
        border: none;
        text-align: left;
    }
    
    ToolItem:hover {
        background: $surface-lighten-1;
    }
    
    ToolItem.enabled {
        color: $success;
    }
    
    ToolItem.disabled {
        color: $text-muted;
    }
    """
    
    tool_name: reactive[str] = reactive("")
    is_enabled: reactive[bool] = reactive(True)
    
    class Toggled(Message):
        """Message sent when a tool is toggled."""
        
        def __init__(self, tool_name: str, enabled: bool) -> None:
            self.tool_name = tool_name
            self.enabled = enabled
            super().__init__()
    
    def __init__(
        self,
        tool_name: str,
        *,
        is_enabled: bool = True,
        name: Optional[str] = None,
        id: Optional[str] = None,
    ) -> None:
        super().__init__(name=name, id=id)
        self.tool_name = tool_name
        self.is_enabled = is_enabled
    
    def watch_is_enabled(self, is_enabled: bool) -> None:
        if is_enabled:
            self.add_class("enabled")
            self.remove_class("disabled")
        else:
            self.add_class("disabled")
            self.remove_class("enabled")
    
    def render(self) -> str:
        status = "✓" if self.is_enabled else "✗"
        return f"{status} {self.tool_name}"
    
    def on_click(self) -> None:
        self.is_enabled = not self.is_enabled
        self.post_message(self.Toggled(self.tool_name, self.is_enabled))


class SidebarWidget(Container):
    """
    Sidebar widget for navigation and status.
    
    Features:
    - Session list
    - Tool toggles
    - Model selector
    - Status display
    """
    
    DEFAULT_CSS = """
    SidebarWidget {
        width: 28;
        dock: left;
        background: $surface-darken-1;
        border-right: solid $primary;
    }
    
    SidebarWidget .section {
        padding: 1;
        border-bottom: solid $primary;
    }
    
    SidebarWidget .section-header {
        text-style: bold;
        margin-bottom: 1;
        color: $accent;
    }
    
    SidebarWidget .session-list {
        max-height: 15;
        overflow-y: auto;
    }
    
    SidebarWidget .tool-list {
        max-height: 10;
        overflow-y: auto;
    }
    
    SidebarWidget .status {
        padding: 1;
        background: $surface-darken-2;
    }
    """
    
    current_session_id: reactive[Optional[str]] = reactive(None)
    current_model: reactive[str] = reactive("claude-3-5-sonnet")
    is_processing: reactive[bool] = reactive(False)
    
    def __init__(
        self,
        *,
        name: Optional[str] = None,
        id: Optional[str] = None,
    ) -> None:
        super().__init__(name=name, id=id)
        self._session_items: list[SessionItem] = []
        self._tool_items: list[ToolItem] = []
    
    def compose(self) -> None:
        """Compose the sidebar layout."""
        yield Static("📁 Sessions", classes="section-header")
        with Container(classes="section session-list"):
            pass  # Sessions will be added dynamically
        
        yield Static("🔧 Tools", classes="section-header")
        with Container(classes="section tool-list"):
            pass  # Tools will be added dynamically
        
        yield Static("📊 Status", classes="section-header")
        with Container(classes="section status"):
            yield Static(id="model-display")
            yield Static(id="status-display")
    
    def on_mount(self) -> None:
        """Update initial display."""
        self._update_status()
    
    def watch_current_model(self, model: str) -> None:
        self._update_status()
    
    def watch_is_processing(self, processing: bool) -> None:
        self._update_status()
    
    def _update_status(self) -> None:
        """Update the status display."""
        model_display = self.query_one("#model-display", Static)
        model_display.update(f"Model: {self.current_model}")
        
        status_display = self.query_one("#status-display", Static)
        status = "⏳ Processing..." if self.is_processing else "✓ Ready"
        status_display.update(f"Status: {status}")
    
    def add_session(self, session_id: str, title: str) -> None:
        """Add a session to the list."""
        is_active = session_id == self.current_session_id
        item = SessionItem(session_id, title, is_active=is_active)
        self._session_items.append(item)
        
        session_list = self.query(".session-list").first()
        session_list.mount(item)
    
    def set_active_session(self, session_id: str) -> None:
        """Set the active session."""
        self.current_session_id = session_id
        
        for item in self._session_items:
            item.is_active = item.session_id == session_id
    
    def clear_sessions(self) -> None:
        """Clear all sessions from the list."""
        for item in self._session_items:
            item.remove()
        self._session_items.clear()
    
    def add_tool(self, tool_name: str, enabled: bool = True) -> None:
        """Add a tool to the list."""
        item = ToolItem(tool_name, is_enabled=enabled)
        self._tool_items.append(item)
        
        tool_list = self.query(".tool-list").first()
        tool_list.mount(item)
    
    def clear_tools(self) -> None:
        """Clear all tools from the list."""
        for item in self._tool_items:
            item.remove()
        self._tool_items.clear()
    
    def on_session_item_selected(self, event: SessionItem.Selected) -> None:
        """Handle session selection."""
        self.set_active_session(event.session_id)
    
    def on_tool_item_toggled(self, event: ToolItem.Toggled) -> None:
        """Handle tool toggle."""
        # Bubble up to parent
        pass
