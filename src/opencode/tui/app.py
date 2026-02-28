"""
Main TUI application for OpenCode.

This is the main entry point for the terminal user interface,
built with Textual for a rich, interactive experience.
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Header, Static

from opencode.core.config import Config
from opencode.core.session import SessionManager
from opencode.mcp.client import MCPClient
from opencode.provider.base import Provider
from opencode.tool.base import ToolRegistry

# Set up logging for TUI debugging
logger = logging.getLogger(__name__)


def _setup_tui_logging(data_dir: Optional[Path] = None):
    """Set up logging for TUI debugging based on environment variables.
    
    Args:
        data_dir: Optional data directory for log storage. If provided and
                  OPENCODE_LOG_FILE is not set, logs will be written to
                  {data_dir}/logs/opencode_{datetime}.log
    """
    log_level = os.environ.get("OPENCODE_LOG_LEVEL", "INFO").upper()
    log_file = os.environ.get("OPENCODE_LOG_FILE", "")
    
    # Map string level to logging constant
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
    }
    level = level_map.get(log_level, logging.INFO)
    
    # Configure root logger for opencode
    opencode_logger = logging.getLogger("opencode")
    opencode_logger.setLevel(level)
    
    # Clear existing handlers
    opencode_logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S"
    )
    
    # Add console handler (stderr)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    opencode_logger.addHandler(console_handler)
    
    # Determine log file location
    if not log_file and data_dir:
        # Use data_dir/logs/ with datetime in filename
        from datetime import datetime
        logs_dir = data_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        dt_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file = str(logs_dir / f"opencode_{dt_str}.log")
    
    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        opencode_logger.addHandler(file_handler)
        logger.info(f"Logging to file: {log_file}")
    
    return opencode_logger


# Initialize logging when module is loaded (basic setup)
# Full logging setup happens in OpenCodeApp.on_mount with data_dir
_setup_tui_logging()


class MessageWidget(Static):
    """Widget for displaying a single message."""
    
    DEFAULT_CSS = """
    MessageWidget {
        margin: 0 1;
        padding: 1;
        background: $surface;
        border: solid $primary;
    }
    
    MessageWidget.user {
        border-left: thick $accent;
    }
    
    MessageWidget.assistant {
        border-left: thick $primary;
    }
    
    MessageWidget.system {
        border-left: thick $warning;
        background: $surface-darken-1;
    }
    
    MessageWidget.error {
        border-left: thick $error;
    }
    """
    
    role: reactive[str] = reactive("user")
    message_content: reactive[str] = reactive("")  # Renamed to avoid conflict with Static.content
    
    def __init__(
        self,
        role: str,
        content: str | list,
        *,
        name: Optional[str] = None,
        id: Optional[str] = None,
    ) -> None:
        super().__init__(name=name, id=id)
        self.role = role
        # Handle ContentBlock list or string
        self.message_content = self._extract_text(content)
    
    def _extract_text(self, content: str | list) -> str:
        """Extract text from string or ContentBlock list."""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text_parts = []
            for block in content:
                if hasattr(block, 'text') and block.text:
                    text_parts.append(block.text)
                elif isinstance(block, dict) and 'text' in block:
                    text_parts.append(block['text'])
            return "\n".join(text_parts)
        return str(content)
    
    def watch_role(self, role: str) -> None:
        self.remove_class("user", "assistant", "system")
        self.add_class(role)
    
    def watch_message_content(self, content: str) -> None:
        """Called when message_content changes - triggers a re-render."""
        self.refresh()
    
    def render(self) -> str:
        role_label = {
            "user": "👤 You",
            "assistant": "🤖 Assistant",
            "system": "⚙️ System",
        }.get(self.role, self.role)
        
        return f"[bold]{role_label}[/bold]\n\n{self.message_content}"


class ChatContainer(Container):
    """Container for chat messages."""
    
    DEFAULT_CSS = """
    ChatContainer {
        height: 1fr;
        overflow-y: auto;
        padding: 1;
    }
    """
    
    def add_message(self, role: str, content: str | list) -> MessageWidget:
        """Add a message to the chat."""
        message = MessageWidget(role=role, content=content)
        self.mount(message)
        self.scroll_end(animate=False)
        return message
    
    def clear_messages(self) -> None:
        """Clear all messages."""
        for child in list(self.children):
            child.remove()


class InputContainer(Container):
    """Container for user input with multi-line support."""
    
    DEFAULT_CSS = """
    InputContainer {
        height: auto;
        max-height: 10;
        dock: bottom;
        background: $surface;
        border-top: solid $primary;
        padding: 1;
    }
    
    InputContainer Horizontal {
        height: auto;
    }
    
    InputContainer #message-input {
        width: 1fr;
        height: auto;
        min-height: 1;
        max-height: 8;
    }
    
    InputContainer #send-button {
        width: 3;
        height: 3;
        margin-left: 1;
        background: $primary;
        border: none;
    }
    
    InputContainer #send-button:hover {
        background: $accent;
    }
    
    InputContainer #send-button:focus {
        background: $accent;
    }
    """
    
    def compose(self) -> ComposeResult:
        from textual.widgets import TextArea, Button
        
        with Horizontal():
            yield TextArea(
                id="message-input",
                placeholder="Type your message... (Enter to send, Shift+Enter for new line)",
                show_line_numbers=False,
            )
            yield Button("➤", id="send-button", variant="primary")


class StatusWidget(Static):
    """Widget for displaying system status."""
    
    DEFAULT_CSS = """
    StatusWidget {
        margin: 0 1;
        padding: 1;
        background: $surface-darken-2;
        border: solid $primary-darken-2;
    }
    
    StatusWidget .status-label {
        color: $text-muted;
        text-style: italic;
    }
    
    StatusWidget .status-value {
        color: $text;
    }
    
    StatusWidget .status-ok {
        color: $success;
    }
    
    StatusWidget .status-error {
        color: $error;
    }
    
    StatusWidget .status-warning {
        color: $warning;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._computer_status = "Detecting..."
        self._network_status = "Detecting..."
        self._ollama_status = "Detecting..."
        self._current_model = "Unknown"
        self._models_count = 0
        self._models_list = []
    
    def update_status(
        self,
        computer: Optional[str] = None,
        network: Optional[str] = None,
        ollama: Optional[str] = None,
        current_model: Optional[str] = None,
        models_count: Optional[int] = None,
        models_list: Optional[list] = None,
    ) -> None:
        """Update status values."""
        if computer is not None:
            self._computer_status = computer
        if network is not None:
            self._network_status = network
        if ollama is not None:
            self._ollama_status = ollama
        if current_model is not None:
            self._current_model = current_model
        if models_count is not None:
            self._models_count = models_count
        if models_list is not None:
            self._models_list = models_list
        self.refresh()
    
    def render(self) -> str:
        # Determine status colors
        computer_color = "status-ok" if "OK" in self._computer_status or "Available" in self._computer_status else "status-warning"
        network_color = "status-ok" if "Connected" in self._network_status else "status-error"
        ollama_color = "status-ok" if "Running" in self._ollama_status or "OK" in self._ollama_status else "status-error"
        
        # Format models list (show first 3, then count)
        if self._models_list:
            models_display = ", ".join(self._models_list[:3])
            if len(self._models_list) > 3:
                models_display += f" (+{len(self._models_list) - 3} more)"
        else:
            models_display = "None"
        
        return f"""[bold]💻 Computer[/bold]
  [{computer_color}]{self._computer_status}[/{computer_color}]

[bold]🌐 Network[/bold]
  [{network_color}]{self._network_status}[/{network_color}]

[bold]🦙 Ollama[/bold]
  [{ollama_color}]{self._ollama_status}[/{ollama_color}]
  Model: [cyan]{self._current_model}[/cyan]
  Total: {self._models_count} models
  {models_display}"""


class SidebarContainer(Container):
    """Container for sidebar with sessions and tools."""
    
    DEFAULT_CSS = """
    SidebarContainer {
        width: 30;
        dock: left;
        background: $surface-darken-1;
        border-right: solid $primary;
        overflow-y: auto;
    }
    
    SidebarContainer .status-section {
        margin: 1;
        padding: 1;
    }
    """
    
    def compose(self) -> ComposeResult:
        yield Static("📁 Sessions", classes="sidebar-header")
        yield Static("🔧 Tools", classes="sidebar-header")
        yield Static("📊 Status", classes="sidebar-header")
        yield StatusWidget(id="status-widget")


class OpenCodeApp(App):
    """
    Main OpenCode TUI application.
    
    Features:
    - Chat interface with message history
    - Session management
    - Tool execution
    - Model selection
    - Keyboard shortcuts
    """
    
    CSS = """
    Screen {
        background: $background;
    }
    
    .sidebar-header {
        padding: 1;
        background: $primary;
        color: $text;
        text-align: center;
        text-style: bold;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+n", "new_session", "New Session"),
        Binding("ctrl+s", "save_session", "Save Session"),
        Binding("ctrl+o", "open_session", "Open Session"),
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+m", "toggle_model", "Change Model"),
        Binding("ctrl+t", "toggle_logging", "Debug Logs"),
        Binding("ctrl+l", "view_logs", "View Logs"),
        Binding("f1", "help", "Help"),
        Binding("escape", "cancel", "Stop/Cancel"),
        Binding("ctrl+c", "cancel", "Stop"),
    ]
    
    TITLE = "OpenCode"
    SUB_TITLE = "AI-Powered Code Assistant"
    
    # Reactive state
    current_session_id: reactive[Optional[str]] = reactive(None)
    current_model: reactive[str] = reactive("")  # Will be set from config in __init__
    is_processing: reactive[bool] = reactive(False)
    logging_enabled: reactive[bool] = reactive(False)
    _cancelled: bool = False  # Flag for cancellation during streaming
    
    def __init__(
        self,
        config: Config,
        session_manager: SessionManager,
        tool_registry: ToolRegistry,
        mcp_client: Optional[MCPClient] = None,
        sandbox_root: Optional[Path] = None,
        *,
        driver_class=None,
        css_path=None,
        watch_css=False,
    ) -> None:
        super().__init__(
            driver_class=driver_class,
            css_path=css_path,
            watch_css=watch_css,
        )
        self.config = config
        self.session_manager = session_manager
        self.tool_registry = tool_registry
        self.mcp_client = mcp_client
        self.sandbox_root = sandbox_root
        self.provider: Optional[Provider] = None
        self._streaming_task: Optional[asyncio.Task] = None
        # Set current_model from config
        self.current_model = config.default_model
    
    def watch_is_processing(self, processing: bool) -> None:
        """Update UI when processing state changes."""
        if processing:
            self.sub_title = "⏳ Processing... (Press Esc or Ctrl+C to stop)"
        else:
            self.sub_title = "AI-Powered Code Assistant"
    
    def compose(self) -> ComposeResult:
        """Compose the main layout."""
        yield Header()
        yield Horizontal(
            SidebarContainer(),
            Vertical(
                ChatContainer(id="chat"),
                InputContainer(),
            ),
        )
        yield Footer()
    
    async def on_mount(self) -> None:
        """Handle app mount."""
        # Set up logging with data_dir from config
        # This ensures logs are saved to the target project's docs/opencode/logs/ folder
        _setup_tui_logging(self.config.data_dir)
        
        # Initialize quick commands project root
        from opencode.tui.quick_commands import set_project_root
        if self.config.data_dir:
            set_project_root(self.config.data_dir.parent)
        
        # Initialize provider
        await self._init_provider()
        
        # Load or create session
        await self._load_or_create_session()
        
        # Update status widget
        await self._update_status()
        
        # Focus input
        self.query_one("#message-input").focus()
    
    async def _update_status(self) -> None:
        """Update the status widget with current system information."""
        try:
            status_widget = self.query_one("#status-widget", StatusWidget)
        except Exception:
            return  # Status widget not found
        
        # Get computer status
        computer_status = await self._get_computer_status()
        
        # Get network status
        network_status = await self._get_network_status()
        
        # Get Ollama status
        ollama_status, models_count, models_list = await self._get_ollama_status()
        
        # Update the widget
        status_widget.update_status(
            computer=computer_status,
            network=network_status,
            ollama=ollama_status,
            current_model=self.current_model,
            models_count=models_count,
            models_list=models_list,
        )
    
    async def _get_computer_status(self) -> str:
        """Get computer/system status."""
        try:
            import platform
            import psutil
            
            # Get CPU and memory info
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_gb = memory.total / (1024**3)
            
            return f"OK | CPU: {cpu_percent:.0f}% | RAM: {memory_percent:.0f}% of {memory_gb:.1f}GB"
        except ImportError:
            import platform
            return f"OK | {platform.system()} {platform.machine()}"
        except Exception as e:
            return f"Error: {e}"
    
    async def _get_network_status(self) -> str:
        """Get network connectivity status."""
        import socket
        
        try:
            # Try to connect to a common DNS server
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            return "Connected"
        except OSError:
            return "Disconnected"
    
    async def _get_ollama_status(self) -> tuple[str, int, list]:
        """Get Ollama status and available models.
        
        Returns:
            Tuple of (status_string, model_count, model_list)
        """
        try:
            # Use the OllamaClient to check status
            from opencode.llmchecker.ollama.client import OllamaClient
            
            client = OllamaClient()
            availability = await client.check_availability()
            
            if not availability.get("available"):
                error = availability.get("error", "Unknown error")
                return f"Not available: {error}", 0, []
            
            # Get list of models
            try:
                models = await client.list_models()
                model_names = [m.name for m in models]
                return f"Running (v{availability.get('version', 'unknown')})", len(model_names), model_names
            except Exception as e:
                return f"Running (model list error: {e})", 0, []
                
        except Exception as e:
            return f"Error: {e}", 0, []
    
    async def _init_provider(self) -> None:
        """Initialize the AI provider."""
        # Determine provider from model config
        model_config = self.config.models.get(self.current_model)
        provider_name = model_config.provider if model_config else "ollama"
        
        logger.info(f"Initializing provider: {provider_name} for model: {self.current_model}")
        
        try:
            if provider_name == "ollama":
                from opencode.provider.ollama import OllamaProvider
                self.provider = OllamaProvider()
                logger.info("OllamaProvider initialized successfully")
            elif provider_name == "anthropic":
                provider_config = self.config.get_provider_config("anthropic")
                from opencode.provider.anthropic import AnthropicProvider
                self.provider = AnthropicProvider(
                    api_key=provider_config.api_key if provider_config else "",
                )
            elif provider_name == "openai":
                provider_config = self.config.get_provider_config("openai")
                from opencode.provider.openai import OpenAIProvider
                self.provider = OpenAIProvider(
                    api_key=provider_config.api_key if provider_config else "",
                )
            elif provider_name == "openrouter":
                provider_config = self.config.get_provider_config("openrouter")
                from opencode.provider.openrouter import OpenRouterProvider
                self.provider = OpenRouterProvider(
                    api_key=provider_config.api_key or "",
                )
            else:
                # Default to Ollama
                logger.warning(f"Unknown provider '{provider_name}', defaulting to Ollama")
                from opencode.provider.ollama import OllamaProvider
                self.provider = OllamaProvider()
        except Exception as e:
            logger.exception(f"Failed to initialize provider: {e}")
            # Fallback to Ollama
            from opencode.provider.ollama import OllamaProvider
            self.provider = OllamaProvider()
            logger.info("Fallback to OllamaProvider")
    
    async def _load_or_create_session(self) -> None:
        """Load the most recent session or create a new one."""
        sessions = await self.session_manager.list_sessions()
        if sessions:
            session = sessions[0]  # Most recent
            self.current_session_id = session.id
            await self._load_session_messages(session.id)
        else:
            # Create new session synchronously
            session = await self.session_manager.create_session(
                directory=str(self.config.project_dir) if hasattr(self.config, 'project_dir') else ".",
                model=self.current_model,
            )
            self.current_session_id = session.id
    
    async def _load_session_messages(self, session_id: str) -> None:
        """Load messages from a session into the chat."""
        chat = self.query_one("#chat", ChatContainer)
        chat.clear_messages()
        
        messages = await self.session_manager.get_messages(session_id)
        for msg in messages:
            chat.add_message(msg.role, msg.content)
    
    async def on_input_submitted(self, _event) -> None:
        """Handle input submission (deprecated - kept for compatibility)."""
        pass
    
    async def on_text_area_key_press(self, event) -> None:
        """Handle key press in TextArea - Enter to send, Shift+Enter for new line."""
        from textual.widgets import TextArea
        
        # Only handle Enter key
        if event.key != "enter":
            return
        
        _text_area = self.query_one("#message-input", TextArea)
        
        # Shift+Enter = new line (default behavior)
        if event.shift:
            return
        
        # Enter = send message
        event.prevent_default()
        await self._send_message()
    
    async def on_button_pressed(self, event) -> None:
        """Handle button press - Send button."""
        if event.button.id == "send-button":
            await self._send_message()
    
    async def _send_message(self) -> None:
        """Send the current message from the input area."""
        from textual.widgets import TextArea
        
        if self.is_processing:
            return
        
        text_area = self.query_one("#message-input", TextArea)
        message = text_area.text.strip()
        if not message:
            return
        
        # Clear input
        text_area.text = ""
        
        # Check for quick commands (import already done at startup)
        from opencode.tui.quick_commands import execute_command
        
        # Try to execute as quick command
        result, is_command = await execute_command(message)
        
        if is_command:
            # Handle special command results
            if result == "__CLEAR__":
                chat = self.query_one("#chat", ChatContainer)
                chat.clear_messages()
                return
            
            if result.startswith("__THEME__"):
                theme = result.replace("__THEME__", "")
                # Theme switching - apply the theme
                from opencode.tui.themes import get_theme, OPENCODE_CSS_VARS
                theme_obj = get_theme(theme)
                
                # Update CSS variables dynamically
                css_vars = f"""
                {OPENCODE_CSS_VARS}
                .theme-{theme} {{
                    background: {theme_obj.colors.get('background', '#1E1E2E')};
                    color: {theme_obj.colors.get('text', '#E4E4E7')};
                }}
                """
                
                # Try to update the app's theme
                try:
                    self.theme = theme
                    chat = self.query_one("#chat", ChatContainer)
                    chat.add_message("system", f"Theme switched to: {theme}")
                except Exception as e:
                    chat = self.query_one("#chat", ChatContainer)
                    chat.add_message("system", f"Theme '{theme}' applied (full theme switching requires restart)")
                return
            
            # Display command result
            chat = self.query_one("#chat", ChatContainer)
            chat.add_message("assistant", result)
            return
        
        # Add user message to chat
        chat = self.query_one("#chat", ChatContainer)
        chat.add_message("user", message)
        
        # Save message
        if self.current_session_id:
            from opencode.core.session import MessageRole
            await self.session_manager.add_message(
                self.current_session_id,
                role=MessageRole.USER,
                content=message,
            )
        
        # Process with AI
        await self._process_message(message)
    
    async def _process_message(self, _message: str) -> None:
        """Process a message with the AI."""
        if not self.provider:
            logger.error("Provider not initialized - cannot process message")
            chat = self.query_one("#chat", ChatContainer)
            error_widget = chat.add_message("assistant", "Error: Provider not initialized. Please restart the application.")
            error_widget.add_class("error")
            return
        
        if not self.current_session_id:
            logger.error("Session not initialized - cannot process message")
            chat = self.query_one("#chat", ChatContainer)
            error_widget = chat.add_message("assistant", "Error: Session not initialized. Please restart the application.")
            error_widget.add_class("error")
            return
        
        logger.info(f"Processing message with model: {self.current_model}")
        self.is_processing = True
        chat = self.query_one("#chat", ChatContainer)
        
        # Create placeholder for response
        response_widget = chat.add_message("assistant", "Thinking...")
        
        # Create a cancellation scope for this processing
        self._cancelled = False
        
        async def do_process():
            """Inner function that can be cancelled."""
            nonlocal response_widget
            
            try:
                # Get conversation history
                logger.debug("Fetching conversation history")
                messages = await self.session_manager.get_messages(self.current_session_id)
                logger.debug(f"Got {len(messages)} messages from history")
                
                # Check for cancellation
                if self._cancelled:
                    logger.info("Processing cancelled before streaming")
                    response_widget.message_content = "[Cancelled]"
                    return
                
                # Convert to provider Message format
                from opencode.provider.base import Message, MessageRole as ProviderMessageRole
                provider_messages = []
                for msg in messages:
                    # Get text content from message
                    if isinstance(msg.content, str):
                        text_content = msg.content
                    elif isinstance(msg.content, list):
                        # Extract text from ContentBlock list
                        text_content = " ".join(
                            block.text for block in msg.content 
                            if hasattr(block, 'text') and block.text
                        )
                    else:
                        text_content = str(msg.content)
                    
                    role = ProviderMessageRole.USER if msg.role == "user" else ProviderMessageRole.ASSISTANT
                    provider_messages.append(Message(role=role, content=text_content))
                
                logger.info(f"Calling provider.complete() with model={self.current_model}, {len(provider_messages)} messages")
                logger.debug(f"Provider type: {type(self.provider).__name__}")
                
                # Stream response using the provider's complete() method
                # Note: complete() is an async generator, so we don't await it
                full_response = ""
                chunk_count = 0
                
                # Get the async iterator from the provider
                # The provider.complete() returns an AsyncIterator[StreamChunk]
                stream_iterator = self.provider.complete(
                    provider_messages, 
                    model=self.current_model,
                )
                
                logger.debug(f"Stream iterator type: {type(stream_iterator)}")
                
                async for chunk in stream_iterator:
                    # Check for cancellation during streaming
                    if self._cancelled:
                        logger.info("Processing cancelled during streaming")
                        response_widget.message_content = full_response + "\n\n[Cancelled]"
                        return
                    
                    chunk_count += 1
                    if chunk.delta:
                        full_response += chunk.delta
                        # Update the reactive property - this triggers watch_message_content
                        response_widget.message_content = full_response
                        # Log every 10 chunks for debugging
                        if chunk_count % 10 == 0:
                            logger.debug(f"Received {chunk_count} chunks, {len(full_response)} chars")
                
                logger.info(f"Streaming complete: {chunk_count} chunks, response length: {len(full_response)}")
                
                # Check for cancellation before saving
                if self._cancelled:
                    return
                
                # Save response
                from opencode.core.session import MessageRole
                await self.session_manager.add_message(
                    self.current_session_id,
                    role=MessageRole.ASSISTANT,
                    content=full_response,
                    model=self.current_model,
                )
                logger.debug("Response saved to session")
            
            except asyncio.CancelledError:
                logger.info("Processing task was cancelled")
                response_widget.message_content = "[Cancelled]"
                raise
            
            except Exception as e:
                logger.exception(f"Error processing message: {e}")
                response_widget.message_content = f"Error: {e}"
                response_widget.add_class("error")
        
        # Create the task and store it for cancellation
        self._streaming_task = asyncio.create_task(do_process())
        
        try:
            await self._streaming_task
        except asyncio.CancelledError:
            logger.info("Streaming task cancelled")
        finally:
            self._streaming_task = None
            self.is_processing = False
    
    def action_new_session(self) -> None:
        """Create a new session."""
        async def create_new():
            session = await self.session_manager.create_session(
                directory=str(self.config.project_root) if hasattr(self.config, 'project_root') else ".",
                model=self.current_model,
            )
            self.current_session_id = session.id
            
            chat = self.query_one("#chat", ChatContainer)
            chat.clear_messages()
        
        asyncio.create_task(create_new())
    
    def action_save_session(self) -> None:
        """Save the current session."""
        # Sessions are auto-saved
        self.notify("Session saved")
    
    def action_open_session(self) -> None:
        """Open a session browser."""
        # TODO: Implement session browser
        self.notify("Session browser coming soon")
    
    def action_toggle_model(self) -> None:
        """Toggle between available models."""
        # Get models from config, or use defaults
        models = list(self.config.models.keys()) if self.config.models else [
            "qwen3-coder:30b",
            "llama3.2:latest",
            "llama3.1:8b",
        ]
        
        if not models:
            self.notify("No models configured")
            return
        
        current_idx = models.index(self.current_model) if self.current_model in models else 0
        next_idx = (current_idx + 1) % len(models)
        self.current_model = models[next_idx]
        
        # Update status widget with new model
        asyncio.create_task(self._update_status())
        
        # Model is passed to complete() at call time, no need to set on provider
        self.notify(f"Model: {self.current_model}")
    
    def action_toggle_tools(self) -> None:
        """Toggle tools panel."""
        # TODO: Implement tools panel
        self.notify("Tools panel coming soon")
    
    def action_toggle_logging(self) -> None:
        """Toggle debug logging on/off."""
        self.logging_enabled = not self.logging_enabled
        
        if self.logging_enabled:
            # Enable logging
            _setup_tui_logging()
            logger.info("Debug logging enabled")
            self.notify("Debug logging ENABLED - logs written to docs folder")
        else:
            # Disable logging by setting level to WARNING
            opencode_logger = logging.getLogger("opencode")
            opencode_logger.setLevel(logging.WARNING)
            self.notify("Debug logging DISABLED")
    
    def action_view_logs(self) -> None:
        """View log files and offer to send to debugging agent."""
        from textual.widgets import Button, Label
        from textual.containers import Vertical
        from textual.screen import ModalScreen
        
        log_file = os.environ.get("OPENCODE_LOG_FILE", "")
        if not log_file:
            # Default location
            log_file = str(Path(__file__).parent.parent / "docs" / "opencode_debug.log")
        
        log_path = Path(log_file)
        
        # Check if log file exists
        if log_path.exists():
            try:
                log_content = log_path.read_text(encoding="utf-8")
                lines = log_content.strip().split("\n")
                last_lines = lines[-50:]  # Last 50 lines
                content = "\n".join(last_lines)
            except Exception as e:
                content = f"Error reading log: {e}"
        else:
            content = "No log file found. Press Ctrl+T to enable logging first."
        
        # Show log in a simple notification for now
        # In a full implementation, this would open a modal dialog
        self.notify(f"Log file: {log_file}")
        logger.info(f"Log file location: {log_file}")
        logger.info(f"Last 10 log entries:\n{content}")
        
        # Print to console for debugging
        print(f"\n{'='*60}")
        print("OPENCODE DEBUG LOG")
        print(f"Location: {log_file}")
        print(f"{'='*60}")
        print(content)
        print(f"{'='*60}")
        print("To debug: Share this log with a debugging agent")
        print(f"{'='*60}\n")
    
    def action_help(self) -> None:
        """Show help."""
        self.notify("Press Ctrl+N for new session, Ctrl+M to change model")
    
    def action_cancel(self) -> None:
        """Cancel current operation."""
        if self.is_processing:
            # Set the cancellation flag for the inner loop to check
            self._cancelled = True
            
            # Also cancel the streaming task if it exists
            if self._streaming_task:
                self._streaming_task.cancel()
                self._streaming_task = None
            
            self.is_processing = False
            self.notify("Cancelled", title="Operation Cancelled")
        else:
            self.notify("No operation in progress")
    
    async def shutdown(self) -> None:
        """Clean shutdown."""
        if self.mcp_client:
            await self.mcp_client.stop()
        
        await super().shutdown()
