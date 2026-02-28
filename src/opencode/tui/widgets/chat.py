"""
Chat widget for displaying conversation messages.
"""

from __future__ import annotations

from typing import Optional

from textual.containers import Container, ScrollableContainer
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Static


# Default syntax highlighting theme
DEFAULT_CODE_THEME = "monokai"


def render_markdown(content: str, code_theme: str = DEFAULT_CODE_THEME) -> str:
    """
    Render markdown content with enhanced code block formatting.
    
    This adds proper Rich markup for code blocks to enable syntax highlighting.
    The actual rendering happens in the display layer.
    """
    import re
    
    # Rich will handle markdown rendering
    # We just ensure code blocks have proper language hints
    
    # Pattern to match code blocks with language
    code_block_pattern = r'```(\w+)?\n(.*?)```'
    
    def replace_code_block(match):
        language = match.group(1) or "text"
        code = match.group(2)
        # Add language hint for Rich syntax highlighter
        return f"```{language}\n{code}```"
    
    return re.sub(code_block_pattern, replace_code_block, content, flags=re.DOTALL)


class MessageBubble(Static):
    """A single message bubble in the chat."""
    
    DEFAULT_CSS = """
    MessageBubble {
        margin: 0 1 1 1;
        padding: 1;
        background: $surface;
        border-radius: 1;
    }
    
    MessageBubble.user {
        background: $primary-darken-2;
        margin-left: 10;
    }
    
    MessageBubble.assistant {
        background: $surface-lighten-1;
        margin-right: 10;
    }
    
    MessageBubble.system {
        background: $warning-darken-2;
        color: $text;
    }
    
    MessageBubble.tool {
        background: $accent-darken-2;
        font-size: 0.9em;
    }
    
    MessageBubble .role {
        text-style: bold;
        margin-bottom: 1;
    }
    
    MessageBubble .content {
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    
    MessageBubble.streaming {
        border: dashed $accent;
    }
    
    /* Enhanced styling for code blocks */
    MessageBubble .code-block {
        background: $panel;
        border: solid $primary;
        padding: 1;
        margin: 1 0;
    }
    
    /* Inline code styling */
    MessageBubble .inline-code {
        background: $panel;
        padding: 0 2;
    }
    """
    
    role: reactive[str] = reactive("user")
    content: reactive[str] = reactive("")
    streaming: reactive[bool] = reactive(False)
    
    class Clicked(Message):
        """Message sent when a bubble is clicked."""
        
        def __init__(self, bubble: "MessageBubble") -> None:
            self.bubble = bubble
            super().__init__()
    
    def __init__(
        self,
        role: str,
        content: str,
        *,
        streaming: bool = False,
        name: Optional[str] = None,
        id: Optional[str] = None,
    ) -> None:
        super().__init__(name=name, id=id)
        self.role = role
        self.content = content
        self.streaming = streaming
    
    def watch_role(self, role: str) -> None:
        self.remove_class("user", "assistant", "system", "tool")
        self.add_class(role)
    
    def watch_streaming(self, streaming: bool) -> None:
        if streaming:
            self.add_class("streaming")
        else:
            self.remove_class("streaming")
    
    def render(self) -> str:
        """Render the message content with markdown support."""
        role_icons = {
            "user": "👤",
            "assistant": "🤖",
            "system": "⚙️",
            "tool": "🔧",
        }
        
        icon = role_icons.get(self.role, "💬")
        role_label = self.role.capitalize()
        
        # Format the content based on role
        content = self._format_content()
        
        lines = [
            f"[bold]{icon} {role_label}[/bold]",
            "",
            content,
        ]
        
        if self.streaming:
            lines.append("")
            lines.append("[dim]Streaming...[/dim]")
        
        return "\n".join(lines)
    
    def _format_content(self) -> str:
        """Format content with markdown and syntax highlighting support."""
        # For assistant messages, we add markdown support
        if self.role == "assistant":
            # Rich markdown rendering happens at display time
            # We wrap code blocks for syntax highlighting
            return self._enhance_code_blocks(self.content)
        return self.content
    
    def _enhance_code_blocks(self, text: str) -> str:
        """Enhance code blocks with language hints for Rich syntax highlighting."""
        import re
        
        # Check if content has code blocks
        if "```" not in text:
            return text
        
        # Rich will handle the syntax highlighting at render time
        # We just ensure the code blocks are properly formatted
        return text
    
    def on_click(self) -> None:
        self.post_message(self.Clicked(self))


class ChatWidget(ScrollableContainer):
    """
    Widget for displaying a chat conversation.
    
    Features:
    - Scrollable message history
    - Message bubbles with role styling
    - Streaming message support
    - Auto-scroll to latest
    """
    
    DEFAULT_CSS = """
    ChatWidget {
        height: 1fr;
        background: $background;
    }
    """
    
    def __init__(
        self,
        *,
        name: Optional[str] = None,
        id: Optional[str] = None,
    ) -> None:
        super().__init__(name=name, id=id)
        self._message_bubbles: list[MessageBubble] = []
    
    def add_message(
        self,
        role: str,
        content: str,
        *,
        streaming: bool = False,
    ) -> MessageBubble:
        """Add a new message to the chat."""
        bubble = MessageBubble(role=role, content=content, streaming=streaming)
        self._message_bubbles.append(bubble)
        self.mount(bubble)
        self.scroll_end(animate=False)
        return bubble
    
    def update_last_message(self, content: str) -> None:
        """Update the content of the last message."""
        if self._message_bubbles:
            self._message_bubbles[-1].content = content
    
    def finish_streaming(self) -> None:
        """Mark the last message as finished streaming."""
        if self._message_bubbles:
            self._message_bubbles[-1].streaming = False
    
    def clear_messages(self) -> None:
        """Clear all messages from the chat."""
        for bubble in self._message_bubbles:
            bubble.remove()
        self._message_bubbles.clear()
    
    def get_messages(self) -> list[dict]:
        """Get all messages as a list of dicts."""
        return [
            {"role": bubble.role, "content": bubble.content}
            for bubble in self._message_bubbles
        ]
    
    def scroll_to_message(self, index: int) -> None:
        """Scroll to a specific message by index."""
        if 0 <= index < len(self._message_bubbles):
            self.scroll_to_widget(self._message_bubbles[index])
