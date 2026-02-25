"""
Tests for TUI widgets.
"""

import pytest
from unittest.mock import patch, MagicMock

from opencode.tui.widgets.approval import (
    ApprovalStatus,
    ApprovalRequest,
    ApprovalResponse,
    ApprovalDialog,
)
from opencode.tui.widgets.chat import MessageBubble
from opencode.tui.widgets.input import InputWidget
from opencode.tui.widgets.sidebar import SessionItem, ToolItem
from opencode.tui.widgets.completion import (
    CompletionItem,
    CompletionProvider,
    PathCompletionProvider,
)


class TestApprovalStatus:
    """Tests for ApprovalStatus enum."""
    
    @pytest.mark.unit
    def test_approval_status_pending(self):
        """Test PENDING status."""
        assert ApprovalStatus.PENDING.value == "pending"
    
    @pytest.mark.unit
    def test_approval_status_approved(self):
        """Test APPROVED status."""
        assert ApprovalStatus.APPROVED.value == "approved"
    
    @pytest.mark.unit
    def test_approval_status_denied(self):
        """Test DENIED status."""
        assert ApprovalStatus.DENIED.value == "denied"
    
    @pytest.mark.unit
    def test_approval_status_always_approve(self):
        """Test ALWAYS_APPROVE status."""
        assert ApprovalStatus.ALWAYS_APPROVE.value == "always_approve"
    
    @pytest.mark.unit
    def test_approval_status_timeout(self):
        """Test TIMEOUT status."""
        assert ApprovalStatus.TIMEOUT.value == "timeout"


class TestApprovalRequest:
    """Tests for ApprovalRequest dataclass."""
    
    @pytest.mark.unit
    def test_approval_request_creation(self):
        """Test ApprovalRequest instantiation."""
        request = ApprovalRequest(
            request_id="test-123",
            title="Test Request",
            description="Test description",
        )
        assert request.request_id == "test-123"
        assert request.title == "Test Request"
        assert request.description == "Test description"
    
    @pytest.mark.unit
    def test_approval_request_defaults(self):
        """Test ApprovalRequest default values."""
        request = ApprovalRequest(
            request_id="test-123",
            title="Test",
            description="Test desc",
        )
        assert request.details == {}
        assert request.risk_level == "medium"
        assert request.timeout_seconds == 60
        assert request.auto_approve_safe is False
    
    @pytest.mark.unit
    def test_approval_request_to_dict(self):
        """Test ApprovalRequest.to_dict()."""
        request = ApprovalRequest(
            request_id="test-123",
            title="Test Request",
            description="Test description",
            details={"key": "value"},
            risk_level="high",
        )
        result = request.to_dict()
        assert result["request_id"] == "test-123"
        assert result["title"] == "Test Request"
        assert result["description"] == "Test description"
        assert result["details"] == {"key": "value"}
        assert result["risk_level"] == "high"


class TestApprovalResponse:
    """Tests for ApprovalResponse dataclass."""
    
    @pytest.mark.unit
    def test_approval_response_creation(self):
        """Test ApprovalResponse instantiation."""
        response = ApprovalResponse(
            request_id="test-123",
            status=ApprovalStatus.APPROVED,
        )
        assert response.request_id == "test-123"
        assert response.status == ApprovalStatus.APPROVED
        assert response.reason is None
        assert response.user_feedback is None
    
    @pytest.mark.unit
    def test_approval_response_with_reason(self):
        """Test ApprovalResponse with reason."""
        response = ApprovalResponse(
            request_id="test-123",
            status=ApprovalStatus.DENIED,
            reason="Too risky",
            user_feedback="Please provide more details",
        )
        assert response.reason == "Too risky"
        assert response.user_feedback == "Please provide more details"
    
    @pytest.mark.unit
    def test_approval_response_to_dict(self):
        """Test ApprovalResponse.to_dict()."""
        response = ApprovalResponse(
            request_id="test-123",
            status=ApprovalStatus.APPROVED,
            reason="Looks good",
        )
        result = response.to_dict()
        assert result["request_id"] == "test-123"
        assert result["status"] == "approved"
        assert result["reason"] == "Looks good"


class TestApprovalDialog:
    """Tests for ApprovalDialog widget."""
    
    @pytest.mark.unit
    def test_approval_dialog_creation(self):
        """Test ApprovalDialog instantiation."""
        dialog = ApprovalDialog()
        assert dialog is not None
    
    @pytest.mark.unit
    def test_approval_dialog_has_render(self):
        """Test ApprovalDialog has render method."""
        dialog = ApprovalDialog()
        assert hasattr(dialog, 'render')
    
    @pytest.mark.unit
    def test_approval_dialog_has_compose(self):
        """Test ApprovalDialog has compose method."""
        dialog = ApprovalDialog()
        assert hasattr(dialog, 'compose')
    
    @pytest.mark.unit
    def test_approval_dialog_reactive_current_request(self):
        """Test ApprovalDialog current_request reactive."""
        dialog = ApprovalDialog()
        assert dialog.current_request is None
    
    @pytest.mark.unit
    def test_approval_dialog_reactive_visible(self):
        """Test ApprovalDialog visible reactive."""
        dialog = ApprovalDialog()
        assert dialog.visible is False


class TestMessageBubble:
    """Tests for MessageBubble widget."""
    
    @pytest.mark.unit
    def test_message_bubble_creation(self):
        """Test MessageBubble instantiation."""
        bubble = MessageBubble(role="user", content="Hello")
        assert bubble is not None
    
    @pytest.mark.unit
    def test_message_bubble_role(self):
        """Test MessageBubble role."""
        bubble = MessageBubble(role="assistant", content="Hi there")
        assert bubble.role == "assistant"
    
    @pytest.mark.unit
    def test_message_bubble_content(self):
        """Test MessageBubble content."""
        bubble = MessageBubble(role="user", content="Test message")
        assert bubble.content == "Test message"
    
    @pytest.mark.unit
    def test_message_bubble_streaming(self):
        """Test MessageBubble streaming flag."""
        bubble = MessageBubble(role="assistant", content="...", streaming=True)
        assert bubble.streaming is True
    
    @pytest.mark.unit
    def test_message_bubble_has_render(self):
        """Test MessageBubble has render method."""
        bubble = MessageBubble(role="user", content="Test")
        assert hasattr(bubble, 'render')


class TestInputWidget:
    """Tests for InputWidget."""
    
    @pytest.mark.unit
    def test_input_widget_creation(self):
        """Test InputWidget instantiation."""
        widget = InputWidget()
        assert widget is not None
    
    @pytest.mark.unit
    def test_input_widget_placeholder_default(self):
        """Test InputWidget default placeholder."""
        widget = InputWidget()
        assert "Type your message" in widget.placeholder
    
    @pytest.mark.unit
    def test_input_widget_placeholder_custom(self):
        """Test InputWidget custom placeholder."""
        widget = InputWidget(placeholder="Enter command...")
        assert widget.placeholder == "Enter command..."
    
    @pytest.mark.unit
    def test_input_widget_max_chars(self):
        """Test InputWidget max_chars."""
        widget = InputWidget()
        assert widget.max_chars == 100000
    
    @pytest.mark.unit
    def test_input_widget_has_compose(self):
        """Test InputWidget has compose method."""
        widget = InputWidget()
        assert hasattr(widget, 'compose')


class TestSessionItem:
    """Tests for SessionItem widget."""
    
    @pytest.mark.unit
    def test_session_item_creation(self):
        """Test SessionItem instantiation."""
        item = SessionItem(session_id="sess-123", title="Test Session")
        assert item is not None
    
    @pytest.mark.unit
    def test_session_item_session_id(self):
        """Test SessionItem session_id."""
        item = SessionItem(session_id="sess-456", title="Test")
        assert item.session_id == "sess-456"
    
    @pytest.mark.unit
    def test_session_item_title(self):
        """Test SessionItem title."""
        item = SessionItem(session_id="sess-123", title="My Session")
        assert item.session_title == "My Session"
    
    @pytest.mark.unit
    def test_session_item_is_active_default(self):
        """Test SessionItem is_active default."""
        item = SessionItem(session_id="sess-123", title="Test")
        assert item.is_active is False
    
    @pytest.mark.unit
    def test_session_item_is_active_set(self):
        """Test SessionItem is_active set."""
        item = SessionItem(session_id="sess-123", title="Test", is_active=True)
        assert item.is_active is True
    
    @pytest.mark.unit
    def test_session_item_has_render(self):
        """Test SessionItem has render method."""
        item = SessionItem(session_id="sess-123", title="Test")
        assert hasattr(item, 'render')


class TestToolItem:
    """Tests for ToolItem widget."""
    
    @pytest.mark.unit
    def test_tool_item_creation(self):
        """Test ToolItem instantiation."""
        item = ToolItem(tool_name="test_tool")
        assert item is not None
    
    @pytest.mark.unit
    def test_tool_item_tool_name(self):
        """Test ToolItem tool_name."""
        item = ToolItem(tool_name="my_tool")
        assert item.tool_name == "my_tool"
    
    @pytest.mark.unit
    def test_tool_item_is_enabled_default(self):
        """Test ToolItem is_enabled default."""
        item = ToolItem(tool_name="test_tool")
        assert item.is_enabled is True
    
    @pytest.mark.unit
    def test_tool_item_is_enabled_set(self):
        """Test ToolItem is_enabled set."""
        item = ToolItem(tool_name="test_tool", is_enabled=False)
        assert item.is_enabled is False
    
    @pytest.mark.unit
    def test_tool_item_has_render(self):
        """Test ToolItem has render method."""
        item = ToolItem(tool_name="test_tool")
        assert hasattr(item, 'render')


class TestCompletionItem:
    """Tests for CompletionItem dataclass."""
    
    @pytest.mark.unit
    def test_completion_item_creation(self):
        """Test CompletionItem instantiation."""
        item = CompletionItem(text="test", display="Test")
        assert item.text == "test"
        assert item.display == "Test"
    
    @pytest.mark.unit
    def test_completion_item_defaults(self):
        """Test CompletionItem default values."""
        item = CompletionItem(text="test", display="Test")
        assert item.description is None
        assert item.category == "general"
        assert item.priority == 0
        assert item.insert_text is None
    
    @pytest.mark.unit
    def test_completion_item_with_description(self):
        """Test CompletionItem with description."""
        item = CompletionItem(
            text="test",
            display="Test",
            description="A test item",
        )
        assert item.description == "A test item"
    
    @pytest.mark.unit
    def test_completion_item_comparison(self):
        """Test CompletionItem comparison (sorting)."""
        item1 = CompletionItem(text="a", display="A", priority=1)
        item2 = CompletionItem(text="b", display="B", priority=2)
        # Higher priority should come first
        assert item2 < item1  # item2 has higher priority
    
    @pytest.mark.unit
    def test_completion_item_alphabetical_comparison(self):
        """Test CompletionItem alphabetical comparison for same priority."""
        item1 = CompletionItem(text="a", display="Apple", priority=1)
        item2 = CompletionItem(text="b", display="Banana", priority=1)
        # Same priority, alphabetical order
        assert item1 < item2  # Apple comes before Banana


class TestCompletionProvider:
    """Tests for CompletionProvider base class."""
    
    @pytest.mark.unit
    def test_completion_provider_name(self):
        """Test CompletionProvider name property."""
        provider = CompletionProvider()
        assert provider.name == "base"
    
    @pytest.mark.unit
    def test_completion_provider_get_completions(self):
        """Test CompletionProvider.get_completions returns empty list."""
        provider = CompletionProvider()
        result = provider.get_completions("test", 4, {})
        assert result == []
    
    @pytest.mark.unit
    def test_completion_provider_get_trigger_chars(self):
        """Test CompletionProvider.get_trigger_chars returns empty list."""
        provider = CompletionProvider()
        result = provider.get_trigger_chars()
        assert result == []


class TestPathCompletionProvider:
    """Tests for PathCompletionProvider."""
    
    @pytest.mark.unit
    def test_path_completion_provider_creation(self):
        """Test PathCompletionProvider instantiation."""
        provider = PathCompletionProvider()
        assert provider is not None
    
    @pytest.mark.unit
    def test_path_completion_provider_name(self):
        """Test PathCompletionProvider name property."""
        provider = PathCompletionProvider()
        assert provider.name == "path"
    
    @pytest.mark.unit
    def test_path_completion_provider_trigger_chars(self):
        """Test PathCompletionProvider trigger chars."""
        provider = PathCompletionProvider()
        triggers = provider.get_trigger_chars()
        assert "/" in triggers
        assert "./" in triggers
        assert "~" in triggers
    
    @pytest.mark.unit
    def test_path_completion_provider_with_workspace(self):
        """Test PathCompletionProvider with workspace root."""
        provider = PathCompletionProvider(workspace_root="/project")
        assert provider.workspace_root is not None
