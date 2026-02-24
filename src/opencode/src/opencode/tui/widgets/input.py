"""
Input widget for user message entry.
"""

from __future__ import annotations

from typing import Optional

from textual.containers import Container, Horizontal
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Button, Static, TextArea


class InputWidget(Container):
    """
    Widget for user message input.
    
    Features:
    - Multi-line text input
    - Send button
    - Keyboard shortcuts
    - File attachment support
    """
    
    DEFAULT_CSS = """
    InputWidget {
        dock: bottom;
        height: auto;
        min-height: 5;
        max-height: 15;
        background: $surface;
        border-top: solid $primary;
        padding: 1;
    }
    
    InputWidget .input-area {
        height: auto;
        min-height: 3;
    }
    
    InputWidget TextArea {
        height: auto;
        min-height: 3;
        max-height: 10;
        background: $background;
        border: solid $primary;
    }
    
    InputWidget .button-bar {
        height: auto;
        align: right;
        margin-top: 1;
    }
    
    InputWidget Button {
        margin-left: 1;
    }
    
    InputWidget .send-button {
        background: $accent;
        color: $text;
    }
    
    InputWidget .attach-button {
        background: $primary;
    }
    
    InputWidget .char-count {
        color: $text-muted;
        text-align: right;
    }
    """
    
    is_processing: reactive[bool] = reactive(False)
    char_count: reactive[int] = reactive(0)
    max_chars: int = 100000
    
    class Submitted(Message):
        """Message sent when input is submitted."""
        
        def __init__(self, text: str, attachments: list[str]) -> None:
            self.text = text
            self.attachments = attachments
            super().__init__()
    
    class Cancelled(Message):
        """Message sent when input is cancelled."""
        pass
    
    def __init__(
        self,
        *,
        placeholder: str = "Type your message... (Enter to send, Shift+Enter for new line)",
        name: Optional[str] = None,
        id: Optional[str] = None,
    ) -> None:
        super().__init__(name=name, id=id)
        self.placeholder = placeholder
        self._attachments: list[str] = []
    
    def compose(self) -> None:
        """Compose the input widget."""
        yield TextArea(
            id="message-input",
            placeholder=self.placeholder,
        )
        with Horizontal(classes="button-bar"):
            yield Static("", id="char-count", classes="char-count")
            yield Button("📎 Attach", id="attach-button", classes="attach-button")
            yield Button("Send ➤", id="send-button", classes="send-button")
    
    def on_mount(self) -> None:
        """Focus the input on mount."""
        self.query_one("#message-input", TextArea).focus()
    
    def watch_is_processing(self, processing: bool) -> None:
        """Update UI when processing state changes."""
        send_button = self.query_one("#send-button", Button)
        send_button.disabled = processing
        send_button.label = "⏳ Processing..." if processing else "Send ➤"
        
        text_area = self.query_one("#message-input", TextArea)
        text_area.disabled = processing
    
    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Update character count when text changes."""
        text = event.text_area.text
        self.char_count = len(text)
        
        char_count_display = self.query_one("#char-count", Static)
        if self.char_count > self.max_chars * 0.9:
            char_count_display.update(f"⚠️ {self.char_count}/{self.max_chars}")
        else:
            char_count_display.update(f"{self.char_count} chars")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "send-button":
            self._submit()
        elif event.button.id == "attach-button":
            self._attach_file()
    
    def on_key(self, event) -> None:
        """Handle keyboard shortcuts."""
        if event.key == "enter" and not event.shift:
            event.prevent_default()
            self._submit()
        elif event.key == "escape":
            self.post_message(self.Cancelled())
    
    def _submit(self) -> None:
        """Submit the current input."""
        if self.is_processing:
            return
        
        text_area = self.query_one("#message-input", TextArea)
        text = text_area.text.strip()
        
        if not text:
            return
        
        # Clear input
        text_area.text = ""
        
        # Post message
        self.post_message(self.Submitted(text, self._attachments.copy()))
        
        # Clear attachments
        self._attachments.clear()
    
    def _attach_file(self) -> None:
        """Attach a file to the message."""
        # TODO: Implement file picker
        pass
    
    def add_attachment(self, file_path: str) -> None:
        """Add an attachment programmatically."""
        self._attachments.append(file_path)
    
    def clear_attachments(self) -> None:
        """Clear all attachments."""
        self._attachments.clear()
    
    def focus(self) -> None:
        """Focus the input."""
        self.query_one("#message-input", TextArea).focus()
    
    def set_text(self, text: str) -> None:
        """Set the input text."""
        text_area = self.query_one("#message-input", TextArea)
        text_area.text = text
    
    def get_text(self) -> str:
        """Get the current input text."""
        text_area = self.query_one("#message-input", TextArea)
        return text_area.text
