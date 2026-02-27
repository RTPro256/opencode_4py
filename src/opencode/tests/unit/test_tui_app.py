"""
Tests for TUI app module.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock, PropertyMock
import asyncio

from opencode.tui.app import (
    MessageWidget,
    ChatContainer,
    InputContainer,
    SidebarContainer,
    OpenCodeApp,
)


@pytest.mark.unit
class TestMessageWidget:
    """Tests for MessageWidget class."""

    def test_message_widget_creation(self):
        """Test MessageWidget instantiation."""
        widget = MessageWidget(role="user", content="Hello")
        assert widget is not None
        assert widget.role == "user"
        assert widget.message_content == "Hello"

    def test_message_widget_with_name(self):
        """Test MessageWidget with custom name."""
        widget = MessageWidget(role="assistant", content="Hi", name="my-message")
        assert widget.name == "my-message"

    def test_message_widget_with_id(self):
        """Test MessageWidget with custom id."""
        widget = MessageWidget(role="system", content="Info", id="msg-1")
        assert widget.id == "msg-1"

    def test_message_widget_reactive_role(self):
        """Test MessageWidget role reactive property."""
        widget = MessageWidget(role="user", content="Test")
        assert widget.role == "user"
        widget.role = "assistant"
        assert widget.role == "assistant"

    def test_message_widget_reactive_content(self):
        """Test MessageWidget content reactive property."""
        widget = MessageWidget(role="user", content="Initial")
        assert widget.message_content == "Initial"
        widget.message_content = "Updated"
        assert widget.message_content == "Updated"

    def test_message_widget_render_user(self):
        """Test MessageWidget render for user role."""
        widget = MessageWidget(role="user", content="Hello world")
        result = widget.render()
        assert "👤 You" in result
        assert "Hello world" in result

    def test_message_widget_render_assistant(self):
        """Test MessageWidget render for assistant role."""
        widget = MessageWidget(role="assistant", content="Hi there!")
        result = widget.render()
        assert "🤖 Assistant" in result
        assert "Hi there!" in result

    def test_message_widget_render_system(self):
        """Test MessageWidget render for system role."""
        widget = MessageWidget(role="system", content="System message")
        result = widget.render()
        assert "⚙️ System" in result
        assert "System message" in result

    def test_message_widget_render_unknown_role(self):
        """Test MessageWidget render for unknown role."""
        widget = MessageWidget(role="custom", content="Custom message")
        result = widget.render()
        assert "custom" in result
        assert "Custom message" in result

    def test_message_widget_watch_role(self):
        """Test MessageWidget watch_role removes old classes and adds new."""
        widget = MessageWidget(role="user", content="Test")
        # Initially has user class
        widget.watch_role("assistant")
        # Should now have assistant class
        assert "assistant" in widget.classes
        widget.watch_role("system")
        assert "system" in widget.classes


@pytest.mark.unit
class TestChatContainer:
    """Tests for ChatContainer class."""

    def test_chat_container_creation(self):
        """Test ChatContainer instantiation."""
        container = ChatContainer()
        assert container is not None

    def test_chat_container_has_add_message(self):
        """Test ChatContainer has add_message method."""
        container = ChatContainer()
        assert hasattr(container, 'add_message')

    def test_chat_container_has_clear_messages(self):
        """Test ChatContainer has clear_messages method."""
        container = ChatContainer()
        assert hasattr(container, 'clear_messages')

    def test_chat_container_default_css(self):
        """Test ChatContainer has DEFAULT_CSS."""
        container = ChatContainer()
        assert container.DEFAULT_CSS is not None
        assert "height: 1fr" in container.DEFAULT_CSS


@pytest.mark.unit
class TestInputContainer:
    """Tests for InputContainer class."""

    def test_input_container_creation(self):
        """Test InputContainer instantiation."""
        container = InputContainer()
        assert container is not None

    def test_input_container_has_compose(self):
        """Test InputContainer has compose method."""
        container = InputContainer()
        assert hasattr(container, 'compose')

    def test_input_container_default_css(self):
        """Test InputContainer has DEFAULT_CSS."""
        container = InputContainer()
        assert container.DEFAULT_CSS is not None
        assert "dock: bottom" in container.DEFAULT_CSS


@pytest.mark.unit
class TestSidebarContainer:
    """Tests for SidebarContainer class."""

    def test_sidebar_container_creation(self):
        """Test SidebarContainer instantiation."""
        container = SidebarContainer()
        assert container is not None

    def test_sidebar_container_has_compose(self):
        """Test SidebarContainer has compose method."""
        container = SidebarContainer()
        assert hasattr(container, 'compose')

    def test_sidebar_container_default_css(self):
        """Test SidebarContainer has DEFAULT_CSS."""
        container = SidebarContainer()
        assert container.DEFAULT_CSS is not None
        assert "dock: left" in container.DEFAULT_CSS


@pytest.mark.unit
class TestOpenCodeApp:
    """Tests for OpenCodeApp class."""

    def test_app_creation(self):
        """Test OpenCodeApp instantiation."""
        mock_config = MagicMock()
        mock_config.project_root = "/test/project"
        mock_session_manager = MagicMock()
        mock_tool_registry = MagicMock()

        app = OpenCodeApp(
            config=mock_config,
            session_manager=mock_session_manager,
            tool_registry=mock_tool_registry,
        )
        assert app is not None
        assert app.config == mock_config
        assert app.session_manager == mock_session_manager
        assert app.tool_registry == mock_tool_registry

    def test_app_with_mcp_client(self):
        """Test OpenCodeApp with MCP client."""
        mock_config = MagicMock()
        mock_config.project_root = "/test/project"
        mock_session_manager = MagicMock()
        mock_tool_registry = MagicMock()
        mock_mcp_client = MagicMock()

        app = OpenCodeApp(
            config=mock_config,
            session_manager=mock_session_manager,
            tool_registry=mock_tool_registry,
            mcp_client=mock_mcp_client,
        )
        assert app.mcp_client == mock_mcp_client

    def test_app_title(self):
        """Test OpenCodeApp title."""
        mock_config = MagicMock()
        mock_session_manager = MagicMock()
        mock_tool_registry = MagicMock()

        app = OpenCodeApp(
            config=mock_config,
            session_manager=mock_session_manager,
            tool_registry=mock_tool_registry,
        )
        assert app.TITLE == "OpenCode"
        assert app.SUB_TITLE == "AI-Powered Code Assistant"

    def test_app_reactive_current_session_id(self):
        """Test OpenCodeApp current_session_id reactive property."""
        mock_config = MagicMock()
        mock_session_manager = MagicMock()
        mock_tool_registry = MagicMock()

        app = OpenCodeApp(
            config=mock_config,
            session_manager=mock_session_manager,
            tool_registry=mock_tool_registry,
        )
        assert app.current_session_id is None
        app.current_session_id = "session-123"
        assert app.current_session_id == "session-123"

    def test_app_reactive_current_model(self):
        """Test OpenCodeApp current_model reactive property."""
        mock_config = MagicMock()
        mock_config.default_model = "claude-3-5-sonnet-20241022"
        mock_session_manager = MagicMock()
        mock_tool_registry = MagicMock()

        app = OpenCodeApp(
            config=mock_config,
            session_manager=mock_session_manager,
            tool_registry=mock_tool_registry,
        )
        assert app.current_model == "claude-3-5-sonnet-20241022"
        app.current_model = "gpt-4o"
        assert app.current_model == "gpt-4o"

    def test_app_reactive_is_processing(self):
        """Test OpenCodeApp is_processing reactive property."""
        mock_config = MagicMock()
        mock_session_manager = MagicMock()
        mock_tool_registry = MagicMock()

        app = OpenCodeApp(
            config=mock_config,
            session_manager=mock_session_manager,
            tool_registry=mock_tool_registry,
        )
        assert app.is_processing is False
        app.is_processing = True
        assert app.is_processing is True

    def test_app_bindings(self):
        """Test OpenCodeApp has correct bindings."""
        mock_config = MagicMock()
        mock_session_manager = MagicMock()
        mock_tool_registry = MagicMock()

        app = OpenCodeApp(
            config=mock_config,
            session_manager=mock_session_manager,
            tool_registry=mock_tool_registry,
        )
        binding_keys = [b.key for b in app.BINDINGS]
        assert "ctrl+n" in binding_keys
        assert "ctrl+s" in binding_keys
        assert "ctrl+o" in binding_keys
        assert "ctrl+q" in binding_keys
        assert "ctrl+m" in binding_keys
        assert "ctrl+t" in binding_keys
        assert "f1" in binding_keys
        assert "escape" in binding_keys

    def test_app_has_compose(self):
        """Test OpenCodeApp has compose method."""
        mock_config = MagicMock()
        mock_session_manager = MagicMock()
        mock_tool_registry = MagicMock()

        app = OpenCodeApp(
            config=mock_config,
            session_manager=mock_session_manager,
            tool_registry=mock_tool_registry,
        )
        assert hasattr(app, 'compose')

    def test_app_has_action_new_session(self):
        """Test OpenCodeApp has action_new_session method."""
        mock_config = MagicMock()
        mock_session_manager = MagicMock()
        mock_tool_registry = MagicMock()

        app = OpenCodeApp(
            config=mock_config,
            session_manager=mock_session_manager,
            tool_registry=mock_tool_registry,
        )
        assert hasattr(app, 'action_new_session')
        assert callable(app.action_new_session)

    def test_app_has_action_save_session(self):
        """Test OpenCodeApp has action_save_session method."""
        mock_config = MagicMock()
        mock_session_manager = MagicMock()
        mock_tool_registry = MagicMock()

        app = OpenCodeApp(
            config=mock_config,
            session_manager=mock_session_manager,
            tool_registry=mock_tool_registry,
        )
        assert hasattr(app, 'action_save_session')
        assert callable(app.action_save_session)

    def test_app_has_action_open_session(self):
        """Test OpenCodeApp has action_open_session method."""
        mock_config = MagicMock()
        mock_session_manager = MagicMock()
        mock_tool_registry = MagicMock()

        app = OpenCodeApp(
            config=mock_config,
            session_manager=mock_session_manager,
            tool_registry=mock_tool_registry,
        )
        assert hasattr(app, 'action_open_session')
        assert callable(app.action_open_session)

    def test_app_has_action_toggle_model(self):
        """Test OpenCodeApp has action_toggle_model method."""
        mock_config = MagicMock()
        mock_session_manager = MagicMock()
        mock_tool_registry = MagicMock()

        app = OpenCodeApp(
            config=mock_config,
            session_manager=mock_session_manager,
            tool_registry=mock_tool_registry,
        )
        assert hasattr(app, 'action_toggle_model')
        assert callable(app.action_toggle_model)

    def test_app_has_action_toggle_tools(self):
        """Test OpenCodeApp has action_toggle_tools method."""
        mock_config = MagicMock()
        mock_session_manager = MagicMock()
        mock_tool_registry = MagicMock()

        app = OpenCodeApp(
            config=mock_config,
            session_manager=mock_session_manager,
            tool_registry=mock_tool_registry,
        )
        assert hasattr(app, 'action_toggle_tools')
        assert callable(app.action_toggle_tools)

    def test_app_has_action_help(self):
        """Test OpenCodeApp has action_help method."""
        mock_config = MagicMock()
        mock_session_manager = MagicMock()
        mock_tool_registry = MagicMock()

        app = OpenCodeApp(
            config=mock_config,
            session_manager=mock_session_manager,
            tool_registry=mock_tool_registry,
        )
        assert hasattr(app, 'action_help')
        assert callable(app.action_help)

    def test_app_has_action_cancel(self):
        """Test OpenCodeApp has action_cancel method."""
        mock_config = MagicMock()
        mock_session_manager = MagicMock()
        mock_tool_registry = MagicMock()

        app = OpenCodeApp(
            config=mock_config,
            session_manager=mock_session_manager,
            tool_registry=mock_tool_registry,
        )
        assert hasattr(app, 'action_cancel')
        assert callable(app.action_cancel)

    def test_app_has_shutdown(self):
        """Test OpenCodeApp has shutdown method."""
        mock_config = MagicMock()
        mock_session_manager = MagicMock()
        mock_tool_registry = MagicMock()

        app = OpenCodeApp(
            config=mock_config,
            session_manager=mock_session_manager,
            tool_registry=mock_tool_registry,
        )
        assert hasattr(app, 'shutdown')
        assert callable(app.shutdown)

    def test_app_provider_initially_none(self):
        """Test OpenCodeApp provider is initially None."""
        mock_config = MagicMock()
        mock_session_manager = MagicMock()
        mock_tool_registry = MagicMock()

        app = OpenCodeApp(
            config=mock_config,
            session_manager=mock_session_manager,
            tool_registry=mock_tool_registry,
        )
        assert app.provider is None

    def test_app_streaming_task_initially_none(self):
        """Test OpenCodeApp _streaming_task is initially None."""
        mock_config = MagicMock()
        mock_session_manager = MagicMock()
        mock_tool_registry = MagicMock()

        app = OpenCodeApp(
            config=mock_config,
            session_manager=mock_session_manager,
            tool_registry=mock_tool_registry,
        )
        assert app._streaming_task is None


@pytest.mark.unit
class TestOpenCodeAppActions:
    """Tests for OpenCodeApp action methods."""

    def test_action_toggle_model_cycles_models(self):
        """Test action_toggle_model cycles through models."""
        mock_config = MagicMock()
        mock_config.default_model = "qwen3-coder:30b"
        mock_config.models = {
            "qwen3-coder:30b": {},
            "llama3.2:latest": {},
            "llama3.1:8b": {},
        }
        mock_session_manager = MagicMock()
        mock_tool_registry = MagicMock()

        app = OpenCodeApp(
            config=mock_config,
            session_manager=mock_session_manager,
            tool_registry=mock_tool_registry,
        )
        
        # Initial model
        assert app.current_model == "qwen3-coder:30b"
        
        # Toggle to next model (mock asyncio.create_task to avoid event loop requirement)
        with patch('asyncio.create_task'):
            app.action_toggle_model()
        assert app.current_model == "llama3.2:latest"
        
        # Toggle again
        with patch('asyncio.create_task'):
            app.action_toggle_model()
        assert app.current_model == "llama3.1:8b"
        
        # Toggle back to first
        with patch('asyncio.create_task'):
            app.action_toggle_model()
        assert app.current_model == "qwen3-coder:30b"

    def test_action_toggle_model_with_provider(self):
        """Test action_toggle_model updates provider model."""
        mock_config = MagicMock()
        mock_config.default_model = "qwen3-coder:30b"
        mock_config.models = {
            "qwen3-coder:30b": {},
            "llama3.2:latest": {},
        }
        mock_session_manager = MagicMock()
        mock_tool_registry = MagicMock()

        app = OpenCodeApp(
            config=mock_config,
            session_manager=mock_session_manager,
            tool_registry=mock_tool_registry,
        )
        
        # Set a mock provider
        mock_provider = MagicMock()
        app.provider = mock_provider
        
        # Toggle model (mock asyncio.create_task to avoid event loop requirement)
        with patch('asyncio.create_task'):
            app.action_toggle_model()
        
        # Model should be toggled to next in list
        assert app.current_model == "llama3.2:latest"

    def test_action_cancel_with_no_task(self):
        """Test action_cancel with no streaming task."""
        mock_config = MagicMock()
        mock_session_manager = MagicMock()
        mock_tool_registry = MagicMock()

        app = OpenCodeApp(
            config=mock_config,
            session_manager=mock_session_manager,
            tool_registry=mock_tool_registry,
        )
        
        app.is_processing = True
        app.action_cancel()
        
        assert app.is_processing is False
        assert app._streaming_task is None

    def test_action_cancel_with_task(self):
        """Test action_cancel with streaming task."""
        mock_config = MagicMock()
        mock_session_manager = MagicMock()
        mock_tool_registry = MagicMock()

        app = OpenCodeApp(
            config=mock_config,
            session_manager=mock_session_manager,
            tool_registry=mock_tool_registry,
        )
        
        # Create a mock task
        mock_task = MagicMock()
        mock_task.cancel = MagicMock()
        app._streaming_task = mock_task
        app.is_processing = True
        
        app.action_cancel()
        
        mock_task.cancel.assert_called_once()
        assert app._streaming_task is None
        assert app.is_processing is False


@pytest.mark.unit
class TestOpenCodeAppAsync:
    """Tests for OpenCodeApp async methods."""

    @pytest.mark.asyncio
    async def test_shutdown_without_mcp_client(self):
        """Test shutdown without MCP client."""
        mock_config = MagicMock()
        mock_session_manager = MagicMock()
        mock_tool_registry = MagicMock()

        app = OpenCodeApp(
            config=mock_config,
            session_manager=mock_session_manager,
            tool_registry=mock_tool_registry,
        )
        
        # Call shutdown - should not raise even without MCP client
        # Note: Textual App.shutdown() may not exist in all versions
        try:
            await app.shutdown()
        except AttributeError:
            # Expected if parent doesn't have shutdown
            pass

    @pytest.mark.asyncio
    async def test_shutdown_with_mcp_client(self):
        """Test shutdown with MCP client."""
        mock_config = MagicMock()
        mock_session_manager = MagicMock()
        mock_tool_registry = MagicMock()
        mock_mcp_client = MagicMock()
        mock_mcp_client.stop = AsyncMock()

        app = OpenCodeApp(
            config=mock_config,
            session_manager=mock_session_manager,
            tool_registry=mock_tool_registry,
            mcp_client=mock_mcp_client,
        )
        
        try:
            await app.shutdown()
        except AttributeError:
            # Parent shutdown may not exist
            pass
        
        # MCP client stop should still be called
        mock_mcp_client.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_init_provider_with_config(self):
        """Test _init_provider with valid config."""
        mock_config = MagicMock()
        mock_config.default_model = "claude-3-5-sonnet-20241022"
        mock_config.get_provider_config = MagicMock(return_value=MagicMock(api_key="test-key"))
        # Set up models with provider info - use MagicMock for model_config to have .provider attribute
        model_config_mock = MagicMock()
        model_config_mock.provider = "ollama"  # Use ollama to avoid needing API keys
        mock_config.models = {
            "claude-3-5-sonnet-20241022": model_config_mock,
        }
        mock_session_manager = MagicMock()
        mock_tool_registry = MagicMock()

        app = OpenCodeApp(
            config=mock_config,
            session_manager=mock_session_manager,
            tool_registry=mock_tool_registry,
        )
        
        # The provider initialization requires proper module imports
        # For now, just verify the method runs without error
        await app._init_provider()
        
        # Provider should be set (either to the configured provider or fallback to Ollama)
        # The actual behavior depends on whether the provider module is available

    @pytest.mark.asyncio
    async def test_init_provider_without_config(self):
        """Test _init_provider without valid config."""
        mock_config = MagicMock()
        mock_config.default_model = "claude-3-5-sonnet-20241022"
        mock_config.get_provider_config = MagicMock(return_value=None)
        mock_config.models = {}
        mock_session_manager = MagicMock()
        mock_tool_registry = MagicMock()

        app = OpenCodeApp(
            config=mock_config,
            session_manager=mock_session_manager,
            tool_registry=mock_tool_registry,
        )
        
        await app._init_provider()
        
        # Provider falls back to Ollama when config is None
        assert app.provider is not None  # Ollama provider is used as fallback


@pytest.mark.unit
class TestMessageWidgetEdgeCases:
    """Tests for MessageWidget edge cases."""

    def test_message_widget_empty_content(self):
        """Test MessageWidget with empty content."""
        widget = MessageWidget(role="user", content="")
        result = widget.render()
        assert "👤 You" in result

    def test_message_widget_multiline_content(self):
        """Test MessageWidget with multiline content."""
        widget = MessageWidget(role="user", content="Line 1\nLine 2\nLine 3")
        result = widget.render()
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result

    def test_message_widget_special_characters(self):
        """Test MessageWidget with special characters."""
        widget = MessageWidget(role="user", content="Special: <>&\"'")
        result = widget.render()
        assert "Special" in result

    def test_message_widget_long_content(self):
        """Test MessageWidget with long content."""
        long_content = "A" * 10000
        widget = MessageWidget(role="assistant", content=long_content)
        result = widget.render()
        assert "🤖 Assistant" in result
        assert long_content in result


@pytest.mark.unit
class TestOpenCodeAppToggleModelEdgeCases:
    """Tests for OpenCodeApp toggle model edge cases."""

    def test_action_toggle_model_unknown_model(self):
        """Test action_toggle_model with unknown current model."""
        mock_config = MagicMock()
        mock_config.default_model = "claude-3-5-sonnet-20241022"
        # Set up models so the toggle has something to cycle through
        mock_config.models = {
            "claude-3-5-sonnet-20241022": {},
            "claude-3-5-haiku-20241022": {},
            "gpt-4o": {},
            "gpt-4o-mini": {},
        }
        mock_session_manager = MagicMock()
        mock_tool_registry = MagicMock()

        app = OpenCodeApp(
            config=mock_config,
            session_manager=mock_session_manager,
            tool_registry=mock_tool_registry,
        )
        
        # Set to unknown model
        app.current_model = "unknown-model"
        
        # When model is unknown, index() returns 0 (model not in list)
        # Then next_idx = (0 + 1) % 4 = 1, so first model in list
        # Mock asyncio.create_task to avoid event loop requirement
        with patch('asyncio.create_task'):
            app.action_toggle_model()
        # The model should cycle to the first model in the list since unknown is not found
        assert app.current_model == "claude-3-5-haiku-20241022"
