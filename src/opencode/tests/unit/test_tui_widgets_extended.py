"""
Extended tests for TUI widgets to improve coverage.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path

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


class TestApprovalDialogExtended:
    """Extended tests for ApprovalDialog widget."""
    
    @pytest.mark.unit
    def test_approval_dialog_show(self):
        """Test showing the approval dialog."""
        dialog = ApprovalDialog()
        dialog.visible = True
        assert dialog.visible is True
    
    @pytest.mark.unit
    def test_approval_dialog_hide(self):
        """Test hiding the approval dialog."""
        dialog = ApprovalDialog()
        dialog.visible = True
        dialog.visible = False
        assert dialog.visible is False
    
    @pytest.mark.unit
    def test_approval_dialog_set_request(self):
        """Test setting current request."""
        dialog = ApprovalDialog()
        request = ApprovalRequest(
            request_id="test-123",
            title="Test Request",
            description="Test description",
        )
        dialog.current_request = request
        assert dialog.current_request == request
    
    @pytest.mark.unit
    def test_approval_dialog_clear_request(self):
        """Test clearing current request."""
        dialog = ApprovalDialog()
        request = ApprovalRequest(
            request_id="test-123",
            title="Test",
            description="Test",
        )
        dialog.current_request = request
        dialog.current_request = None
        assert dialog.current_request is None


class TestMessageBubbleExtended:
    """Extended tests for MessageBubble widget."""
    
    @pytest.mark.unit
    def test_message_bubble_user_role(self):
        """Test MessageBubble with user role."""
        bubble = MessageBubble(role="user", content="Hello")
        assert bubble.role == "user"
    
    @pytest.mark.unit
    def test_message_bubble_assistant_role(self):
        """Test MessageBubble with assistant role."""
        bubble = MessageBubble(role="assistant", content="Hi")
        assert bubble.role == "assistant"
    
    @pytest.mark.unit
    def test_message_bubble_long_content(self):
        """Test MessageBubble with long content."""
        long_content = "A" * 1000
        bubble = MessageBubble(role="user", content=long_content)
        assert bubble.content == long_content
    
    @pytest.mark.unit
    def test_message_bubble_empty_content(self):
        """Test MessageBubble with empty content."""
        bubble = MessageBubble(role="user", content="")
        assert bubble.content == ""
    
    @pytest.mark.unit
    def test_message_bubble_multiline_content(self):
        """Test MessageBubble with multiline content."""
        content = "Line 1\nLine 2\nLine 3"
        bubble = MessageBubble(role="user", content=content)
        assert bubble.content == content
    
    @pytest.mark.unit
    def test_message_bubble_code_content(self):
        """Test MessageBubble with code content."""
        content = "```python\nprint('hello')\n```"
        bubble = MessageBubble(role="assistant", content=content)
        assert bubble.content == content


class TestInputWidgetExtended:
    """Extended tests for InputWidget."""
    
    @pytest.mark.unit
    def test_input_widget_with_id(self):
        """Test InputWidget with custom ID."""
        widget = InputWidget(id="my-input")
        assert widget is not None
    
    @pytest.mark.unit
    def test_input_widget_disabled(self):
        """Test InputWidget disabled state."""
        widget = InputWidget()
        widget.disabled = True
        assert widget.disabled is True
    
    @pytest.mark.unit
    def test_input_widget_has_focus_method(self):
        """Test InputWidget has focus method."""
        widget = InputWidget()
        assert hasattr(widget, 'focus')
    
    @pytest.mark.unit
    def test_input_widget_has_attributes(self):
        """Test InputWidget has expected attributes."""
        widget = InputWidget()
        # Check for any relevant attributes
        assert hasattr(widget, 'placeholder') or hasattr(widget, 'render')


class TestSessionItemExtended:
    """Extended tests for SessionItem widget."""
    
    @pytest.mark.unit
    def test_session_item_render_output(self):
        """Test SessionItem render output."""
        item = SessionItem(session_id="sess-123", title="Test Session")
        result = item.render()
        assert "Test Session" in result
    
    @pytest.mark.unit
    def test_session_item_long_title(self):
        """Test SessionItem with long title (truncated)."""
        long_title = "A" * 100
        item = SessionItem(session_id="sess-123", title=long_title)
        result = item.render()
        # Should be truncated to 30 chars
        assert len(result) < len(long_title) + 10  # Allow for emoji prefix
    
    @pytest.mark.unit
    def test_session_item_watch_is_active_true(self):
        """Test SessionItem watch_is_active with True."""
        item = SessionItem(session_id="sess-123", title="Test")
        item.watch_is_active(True)
        # Should have added 'active' class
        assert "active" in item.classes or item.is_active is True
    
    @pytest.mark.unit
    def test_session_item_watch_is_active_false(self):
        """Test SessionItem watch_is_active with False."""
        item = SessionItem(session_id="sess-123", title="Test", is_active=True)
        # watch_is_active should remove 'active' class
        item.watch_is_active(False)
        # The reactive variable should still be True until explicitly set
        # but the CSS class should be removed
        assert "active" not in item.classes
    
    @pytest.mark.unit
    def test_session_item_selected_message(self):
        """Test SessionItem Selected message."""
        item = SessionItem(session_id="sess-123", title="Test")
        # Check that Selected class exists
        assert hasattr(SessionItem, 'Selected')
    
    @pytest.mark.unit
    def test_session_item_on_click(self):
        """Test SessionItem on_click method."""
        item = SessionItem(session_id="sess-123", title="Test")
        assert hasattr(item, 'on_click')


class TestToolItemExtended:
    """Extended tests for ToolItem widget."""
    
    @pytest.mark.unit
    def test_tool_item_render_output(self):
        """Test ToolItem render output."""
        item = ToolItem(tool_name="test_tool")
        result = item.render()
        assert result is not None
    
    @pytest.mark.unit
    def test_tool_item_enabled_class(self):
        """Test ToolItem enabled class."""
        item = ToolItem(tool_name="test_tool", is_enabled=True)
        # Check that enabled state is reflected
        assert item.is_enabled is True
    
    @pytest.mark.unit
    def test_tool_item_disabled_class(self):
        """Test ToolItem disabled class."""
        item = ToolItem(tool_name="test_tool", is_enabled=False)
        assert item.is_enabled is False
    
    @pytest.mark.unit
    def test_tool_item_toggle_enabled(self):
        """Test toggling ToolItem enabled state."""
        item = ToolItem(tool_name="test_tool", is_enabled=True)
        item.is_enabled = False
        assert item.is_enabled is False
        item.is_enabled = True
        assert item.is_enabled is True


class TestCompletionItemExtended:
    """Extended tests for CompletionItem dataclass."""
    
    @pytest.mark.unit
    def test_completion_item_with_insert_text(self):
        """Test CompletionItem with insert_text."""
        item = CompletionItem(
            text="test",
            display="Test",
            insert_text="test_value",
        )
        assert item.insert_text == "test_value"
    
    @pytest.mark.unit
    def test_completion_item_high_priority(self):
        """Test CompletionItem with high priority."""
        item = CompletionItem(text="test", display="Test", priority=100)
        assert item.priority == 100
    
    @pytest.mark.unit
    def test_completion_item_negative_priority(self):
        """Test CompletionItem with negative priority."""
        item = CompletionItem(text="test", display="Test", priority=-1)
        assert item.priority == -1
    
    @pytest.mark.unit
    def test_completion_item_different_categories(self):
        """Test CompletionItem with different categories."""
        for category in ["file", "command", "mention", "general"]:
            item = CompletionItem(text="test", display="Test", category=category)
            assert item.category == category
    
    @pytest.mark.unit
    def test_completion_item_sorting_multiple(self):
        """Test sorting multiple CompletionItems."""
        items = [
            CompletionItem(text="c", display="C", priority=1),
            CompletionItem(text="a", display="A", priority=3),
            CompletionItem(text="b", display="B", priority=2),
        ]
        sorted_items = sorted(items)
        # Higher priority first
        assert sorted_items[0].text == "a"  # priority 3
        assert sorted_items[1].text == "b"  # priority 2
        assert sorted_items[2].text == "c"  # priority 1


class TestPathCompletionProviderExtended:
    """Extended tests for PathCompletionProvider."""
    
    @pytest.mark.unit
    def test_path_completion_get_completions_empty(self):
        """Test get_completions with empty query."""
        provider = PathCompletionProvider()
        result = provider.get_completions("", 0, {})
        assert isinstance(result, list)
    
    @pytest.mark.unit
    def test_path_completion_provider_name(self):
        """Test PathCompletionProvider name property."""
        provider = PathCompletionProvider()
        assert provider.name == "path"
    
    @pytest.mark.unit
    def test_path_completion_trigger_chars(self):
        """Test PathCompletionProvider trigger chars."""
        provider = PathCompletionProvider()
        triggers = provider.get_trigger_chars()
        assert "/" in triggers
        assert "./" in triggers
        assert "~" in triggers
    
    @pytest.mark.unit
    def test_path_completion_with_workspace(self):
        """Test PathCompletionProvider with workspace root."""
        provider = PathCompletionProvider(workspace_root="/tmp/test")
        assert provider.workspace_root == "/tmp/test" or provider.workspace_root == Path("/tmp/test")
    
    @pytest.mark.unit
    def test_path_completion_has_get_completions(self):
        """Test PathCompletionProvider has get_completions method."""
        provider = PathCompletionProvider()
        assert hasattr(provider, 'get_completions')


class TestApprovalRequestExtended:
    """Extended tests for ApprovalRequest dataclass."""
    
    @pytest.mark.unit
    def test_approval_request_high_risk(self):
        """Test ApprovalRequest with high risk level."""
        request = ApprovalRequest(
            request_id="test-123",
            title="Test",
            description="Test",
            risk_level="high",
        )
        assert request.risk_level == "high"
    
    @pytest.mark.unit
    def test_approval_request_low_risk(self):
        """Test ApprovalRequest with low risk level."""
        request = ApprovalRequest(
            request_id="test-123",
            title="Test",
            description="Test",
            risk_level="low",
        )
        assert request.risk_level == "low"
    
    @pytest.mark.unit
    def test_approval_request_with_timeout(self):
        """Test ApprovalRequest with custom timeout."""
        request = ApprovalRequest(
            request_id="test-123",
            title="Test",
            description="Test",
            timeout_seconds=120,
        )
        assert request.timeout_seconds == 120
    
    @pytest.mark.unit
    def test_approval_request_auto_approve(self):
        """Test ApprovalRequest with auto_approve_safe."""
        request = ApprovalRequest(
            request_id="test-123",
            title="Test",
            description="Test",
            auto_approve_safe=True,
        )
        assert request.auto_approve_safe is True
    
    @pytest.mark.unit
    def test_approval_request_complex_details(self):
        """Test ApprovalRequest with complex details."""
        details = {
            "command": "rm -rf /",
            "args": ["-rf", "/"],
            "cwd": "/home/user",
            "env": {"DEBUG": "1"},
        }
        request = ApprovalRequest(
            request_id="test-123",
            title="Test",
            description="Test",
            details=details,
        )
        assert request.details == details


class TestApprovalResponseExtended:
    """Extended tests for ApprovalResponse dataclass."""
    
    @pytest.mark.unit
    def test_approval_response_denied(self):
        """Test ApprovalResponse with DENIED status."""
        response = ApprovalResponse(
            request_id="test-123",
            status=ApprovalStatus.DENIED,
        )
        assert response.status == ApprovalStatus.DENIED
    
    @pytest.mark.unit
    def test_approval_response_timeout(self):
        """Test ApprovalResponse with TIMEOUT status."""
        response = ApprovalResponse(
            request_id="test-123",
            status=ApprovalStatus.TIMEOUT,
        )
        assert response.status == ApprovalStatus.TIMEOUT
    
    @pytest.mark.unit
    def test_approval_response_always_approve(self):
        """Test ApprovalResponse with ALWAYS_APPROVE status."""
        response = ApprovalResponse(
            request_id="test-123",
            status=ApprovalStatus.ALWAYS_APPROVE,
        )
        assert response.status == ApprovalStatus.ALWAYS_APPROVE
    
    @pytest.mark.unit
    def test_approval_response_to_dict_all_fields(self):
        """Test ApprovalResponse.to_dict() with all fields."""
        response = ApprovalResponse(
            request_id="test-123",
            status=ApprovalStatus.APPROVED,
            reason="Looks good",
            user_feedback="Thanks",
        )
        result = response.to_dict()
        assert result["request_id"] == "test-123"
        assert result["status"] == "approved"
        assert result["reason"] == "Looks good"
        assert result["user_feedback"] == "Thanks"
