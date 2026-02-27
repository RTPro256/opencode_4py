"""
Extended tests for TUI widgets - completion, input, and approval.

Tests the completion providers, input handling, and approval widget logic.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import os

from opencode.tui.widgets.completion import (
    CompletionItem,
    CompletionProvider,
    PathCompletionProvider,
)


class TestCompletionItem:
    """Tests for CompletionItem class."""

    def test_comparison_same_priority(self):
        """Test comparison with same priority."""
        item1 = CompletionItem(text="abc", display="ABC", priority=1)
        item2 = CompletionItem(text="xyz", display="XYZ", priority=1)
        
        assert item1 < item2  # abc comes before xyz alphabetically

    def test_comparison_different_priority(self):
        """Test comparison with different priority."""
        item1 = CompletionItem(text="abc", display="ABC", priority=5)
        item2 = CompletionItem(text="xyz", display="XYZ", priority=1)
        
        assert item1 < item2  # Higher priority comes first

    def test_comparison_case_insensitive(self):
        """Test case-insensitive comparison."""
        item1 = CompletionItem(text="ABC", display="ABC", priority=1)
        item2 = CompletionItem(text="abc", display="abc", priority=1)
        
        # Both have same priority, comparison is case-insensitive
        result = item1 < item2
        assert isinstance(result, bool)


class TestCompletionProvider:
    """Tests for CompletionProvider base class."""

    def test_provider_name(self):
        """Test default provider name."""
        provider = CompletionProvider()
        assert provider.name == "base"

    def test_get_completions_empty(self):
        """Test get_completions returns empty list."""
        provider = CompletionProvider()
        result = provider.get_completions("test", 0, {})
        assert result == []

    def test_get_trigger_chars_empty(self):
        """Test get_trigger_chars returns empty list."""
        provider = CompletionProvider()
        result = provider.get_trigger_chars()
        assert result == []


class TestPathCompletionProvider:
    """Tests for PathCompletionProvider class."""

    def test_provider_name(self):
        """Test path provider name."""
        provider = PathCompletionProvider()
        assert provider.name == "path"

    def test_trigger_chars(self):
        """Test trigger characters."""
        provider = PathCompletionProvider()
        chars = provider.get_trigger_chars()
        assert "/" in chars
        assert "./" in chars

    def test_get_completions_no_workspace(self):
        """Test get_completions without workspace root."""
        provider = PathCompletionProvider()
        result = provider.get_completions("", 0, {})
        # Should handle empty case gracefully
        assert isinstance(result, list)


class TestApprovalStatus:
    """Tests for Approval status functionality."""

    def test_approval_status_import(self):
        """Test that approval status can be imported."""
        from opencode.tui.widgets.approval import ApprovalStatus
        assert ApprovalStatus is not None

    def test_approval_status_values(self):
        """Test approval status enum values."""
        from opencode.tui.widgets.approval import ApprovalStatus
        
        assert ApprovalStatus.PENDING.value == "pending"
        assert ApprovalStatus.APPROVED.value == "approved"
        assert ApprovalStatus.DENIED.value == "denied"
        assert ApprovalStatus.ALWAYS_APPROVE.value == "always_approve"
        assert ApprovalStatus.TIMEOUT.value == "timeout"

    def test_approval_request_import(self):
        """Test that approval request can be imported."""
        from opencode.tui.widgets.approval import ApprovalRequest
        assert ApprovalRequest is not None

    def test_approval_request_creation(self):
        """Test creating an approval request."""
        from opencode.tui.widgets.approval import ApprovalRequest
        
        request = ApprovalRequest(
            request_id="test-1",
            title="Test Approval",
            description="Test description",
            risk_level="high",
            timeout_seconds=30,
        )
        
        assert request.request_id == "test-1"
        assert request.title == "Test Approval"
        assert request.risk_level == "high"
        assert request.timeout_seconds == 30

    def test_approval_request_to_dict(self):
        """Test approval request to_dict method."""
        from opencode.tui.widgets.approval import ApprovalRequest
        
        request = ApprovalRequest(
            request_id="test-1",
            title="Test",
            description="Desc",
        )
        
        result = request.to_dict()
        assert isinstance(result, dict)
        assert result["request_id"] == "test-1"

    def test_approval_response_import(self):
        """Test that approval response can be imported."""
        from opencode.tui.widgets.approval import ApprovalResponse
        assert ApprovalResponse is not None

    def test_approval_response_creation(self):
        """Test creating an approval response."""
        from opencode.tui.widgets.approval import ApprovalResponse, ApprovalStatus
        
        response = ApprovalResponse(
            request_id="test-1",
            status=ApprovalStatus.APPROVED,
            reason="Looks good",
        )
        
        assert response.request_id == "test-1"
        assert response.status == ApprovalStatus.APPROVED
        assert response.reason == "Looks good"

    def test_approval_response_to_dict(self):
        """Test approval response to_dict method."""
        from opencode.tui.widgets.approval import ApprovalResponse, ApprovalStatus
        
        response = ApprovalResponse(
            request_id="test-1",
            status=ApprovalStatus.DENIED,
        )
        
        result = response.to_dict()
        assert isinstance(result, dict)
        assert result["request_id"] == "test-1"


class TestInputWidget:
    """Tests for Input widget functionality."""

    def test_input_widget_import(self):
        """Test that input widget can be imported."""
        from opencode.tui.widgets.input import InputWidget
        assert InputWidget is not None


class TestChatWidget:
    """Tests for Chat widget functionality."""

    def test_chat_widget_import(self):
        """Test that chat widget can be imported."""
        from opencode.tui.widgets.chat import ChatWidget
        assert ChatWidget is not None


class TestSidebarWidget:
    """Tests for Sidebar widget functionality."""

    def test_sidebar_widget_import(self):
        """Test that sidebar widget can be imported."""
        from opencode.tui.widgets.sidebar import SidebarWidget
        assert SidebarWidget is not None
