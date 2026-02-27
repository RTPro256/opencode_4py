"""
Extended tests for tui/widgets/approval.py.

Tests for ApprovalManager class for 100% coverage.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from opencode.tui.widgets.approval import (
    ApprovalStatus,
    ApprovalRequest,
    ApprovalResponse,
    ApprovalManager,
)


class TestApprovalManager:
    """Tests for ApprovalManager class."""

    @pytest.mark.unit
    def test_init_default(self):
        """Test initialization with defaults."""
        manager = ApprovalManager()
        assert manager.auto_approve_safe is False
        assert manager.default_timeout == 60
        assert manager._pending_requests == {}
        assert manager._history == []
        assert manager._always_approve == {}

    @pytest.mark.unit
    def test_init_custom(self):
        """Test initialization with custom values."""
        manager = ApprovalManager(auto_approve_safe=True, default_timeout=120)
        assert manager.auto_approve_safe is True
        assert manager.default_timeout == 120

    @pytest.mark.unit
    def test_generate_request_id(self):
        """Test request ID generation."""
        manager = ApprovalManager()
        id1 = manager._generate_request_id()
        id2 = manager._generate_request_id()
        assert id1 == "approval_1"
        assert id2 == "approval_2"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_request_approval_basic(self):
        """Test basic approval request."""
        manager = ApprovalManager()
        response = await manager.request_approval(
            title="Test Request",
            description="Test description",
        )
        assert response.status == ApprovalStatus.PENDING
        assert "approval_" in response.request_id

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_request_approval_with_details(self):
        """Test approval request with details."""
        manager = ApprovalManager()
        response = await manager.request_approval(
            title="Test",
            description="Test",
            details={"file": "test.py", "action": "delete"},
        )
        assert response.status == ApprovalStatus.PENDING

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_request_approval_auto_approve_safe(self):
        """Test auto-approve for safe actions."""
        manager = ApprovalManager(auto_approve_safe=True)
        response = await manager.request_approval(
            title="Safe Action",
            description="A safe action",
            risk_level="low",
        )
        assert response.status == ApprovalStatus.APPROVED
        assert "Auto-approved" in (response.reason or "")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_request_approval_no_auto_approve_medium_risk(self):
        """Test no auto-approve for medium risk."""
        manager = ApprovalManager(auto_approve_safe=True)
        response = await manager.request_approval(
            title="Medium Risk",
            description="A medium risk action",
            risk_level="medium",
        )
        assert response.status == ApprovalStatus.PENDING

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_request_approval_no_auto_approve_high_risk(self):
        """Test no auto-approve for high risk."""
        manager = ApprovalManager(auto_approve_safe=True)
        response = await manager.request_approval(
            title="High Risk",
            description="A high risk action",
            risk_level="high",
        )
        assert response.status == ApprovalStatus.PENDING

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_request_approval_always_approve_set(self):
        """Test always-approve for action type."""
        manager = ApprovalManager()
        manager.set_always_approve("delete_file", True)
        response = await manager.request_approval(
            title="Delete File",
            description="Delete a file",
            action_type="delete_file",
        )
        assert response.status == ApprovalStatus.ALWAYS_APPROVE

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_request_approval_always_approve_not_set(self):
        """Test always-approve not set for action type."""
        manager = ApprovalManager()
        manager.set_always_approve("delete_file", True)
        response = await manager.request_approval(
            title="Create File",
            description="Create a file",
            action_type="create_file",
        )
        assert response.status == ApprovalStatus.PENDING

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_request_approval_custom_timeout(self):
        """Test approval request with custom timeout."""
        manager = ApprovalManager(default_timeout=60)
        response = await manager.request_approval(
            title="Test",
            description="Test",
            timeout=120,
        )
        assert response.status == ApprovalStatus.PENDING
        # Check that request was stored with correct timeout
        request = manager._pending_requests.get(response.request_id)
        assert request is not None
        assert request.timeout_seconds == 120

    @pytest.mark.unit
    def test_set_always_approve_true(self):
        """Test setting always-approve to true."""
        manager = ApprovalManager()
        manager.set_always_approve("delete_file", True)
        assert manager._always_approve["delete_file"] is True

    @pytest.mark.unit
    def test_set_always_approve_false(self):
        """Test setting always-approve to false."""
        manager = ApprovalManager()
        manager.set_always_approve("delete_file", True)
        manager.set_always_approve("delete_file", False)
        assert manager._always_approve["delete_file"] is False

    @pytest.mark.unit
    def test_record_response(self):
        """Test recording a response."""
        manager = ApprovalManager()
        # Create a pending request first
        manager._pending_requests["approval_1"] = ApprovalRequest(
            request_id="approval_1",
            title="Test",
            description="Test",
        )
        response = ApprovalResponse(
            request_id="approval_1",
            status=ApprovalStatus.APPROVED,
        )
        manager.record_response(response)
        assert response in manager._history
        assert "approval_1" not in manager._pending_requests

    @pytest.mark.unit
    def test_record_response_not_pending(self):
        """Test recording a response not in pending."""
        manager = ApprovalManager()
        response = ApprovalResponse(
            request_id="nonexistent",
            status=ApprovalStatus.APPROVED,
        )
        # Should not raise error
        manager.record_response(response)
        assert response in manager._history

    @pytest.mark.unit
    def test_get_history_empty(self):
        """Test getting empty history."""
        manager = ApprovalManager()
        history = manager.get_history()
        assert history == []

    @pytest.mark.unit
    def test_get_history_with_responses(self):
        """Test getting history with responses."""
        manager = ApprovalManager()
        response1 = ApprovalResponse(request_id="1", status=ApprovalStatus.APPROVED)
        response2 = ApprovalResponse(request_id="2", status=ApprovalStatus.DENIED)
        manager._history = [response1, response2]
        history = manager.get_history()
        assert len(history) == 2

    @pytest.mark.unit
    def test_get_history_with_limit(self):
        """Test getting history with limit."""
        manager = ApprovalManager()
        responses = [
            ApprovalResponse(request_id=str(i), status=ApprovalStatus.APPROVED)
            for i in range(10)
        ]
        manager._history = responses
        history = manager.get_history(limit=5)
        assert len(history) == 5

    @pytest.mark.unit
    def test_get_pending_count_empty(self):
        """Test getting pending count when empty."""
        manager = ApprovalManager()
        assert manager.get_pending_count() == 0

    @pytest.mark.unit
    def test_get_pending_count_with_requests(self):
        """Test getting pending count with requests."""
        manager = ApprovalManager()
        manager._pending_requests["1"] = ApprovalRequest(
            request_id="1", title="Test", description="Test"
        )
        manager._pending_requests["2"] = ApprovalRequest(
            request_id="2", title="Test", description="Test"
        )
        assert manager.get_pending_count() == 2

    @pytest.mark.unit
    def test_clear_history(self):
        """Test clearing history."""
        manager = ApprovalManager()
        manager._history = [
            ApprovalResponse(request_id="1", status=ApprovalStatus.APPROVED)
        ]
        manager.clear_history()
        assert manager._history == []

    @pytest.mark.unit
    def test_get_stats_empty(self):
        """Test getting stats when empty."""
        manager = ApprovalManager()
        stats = manager.get_stats()
        assert stats["total_requests"] == 0
        assert stats["approved"] == 0
        assert stats["denied"] == 0
        assert stats["timeout"] == 0
        assert stats["approval_rate"] == 0
        assert stats["pending"] == 0

    @pytest.mark.unit
    def test_get_stats_with_history(self):
        """Test getting stats with history."""
        manager = ApprovalManager()
        manager._history = [
            ApprovalResponse(request_id="1", status=ApprovalStatus.APPROVED),
            ApprovalResponse(request_id="2", status=ApprovalStatus.APPROVED),
            ApprovalResponse(request_id="3", status=ApprovalStatus.ALWAYS_APPROVE),
            ApprovalResponse(request_id="4", status=ApprovalStatus.DENIED),
            ApprovalResponse(request_id="5", status=ApprovalStatus.TIMEOUT),
        ]
        stats = manager.get_stats()
        assert stats["total_requests"] == 5
        assert stats["approved"] == 3  # APPROVED + ALWAYS_APPROVE
        assert stats["denied"] == 1
        assert stats["timeout"] == 1
        assert stats["approval_rate"] == 0.6  # 3/5

    @pytest.mark.unit
    def test_get_stats_with_pending(self):
        """Test getting stats with pending requests."""
        manager = ApprovalManager()
        manager._pending_requests["1"] = ApprovalRequest(
            request_id="1", title="Test", description="Test"
        )
        stats = manager.get_stats()
        assert stats["pending"] == 1


class TestApprovalRequestExtended:
    """Extended tests for ApprovalRequest."""

    @pytest.mark.unit
    def test_to_dict(self):
        """Test to_dict method."""
        request = ApprovalRequest(
            request_id="test-123",
            title="Test Title",
            description="Test Description",
            details={"key": "value"},
            risk_level="high",
            timeout_seconds=120,
        )
        result = request.to_dict()
        assert result["request_id"] == "test-123"
        assert result["title"] == "Test Title"
        assert result["description"] == "Test Description"
        assert result["details"] == {"key": "value"}
        assert result["risk_level"] == "high"
        assert result["timeout_seconds"] == 120


class TestApprovalResponseExtended:
    """Extended tests for ApprovalResponse."""

    @pytest.mark.unit
    def test_to_dict(self):
        """Test to_dict method."""
        response = ApprovalResponse(
            request_id="test-123",
            status=ApprovalStatus.APPROVED,
            reason="User approved",
            user_feedback="Looks good",
        )
        result = response.to_dict()
        assert result["request_id"] == "test-123"
        assert result["status"] == "approved"
        assert result["reason"] == "User approved"
        assert result["user_feedback"] == "Looks good"

    @pytest.mark.unit
    def test_to_dict_minimal(self):
        """Test to_dict with minimal data."""
        response = ApprovalResponse(
            request_id="test-123",
            status=ApprovalStatus.DENIED,
        )
        result = response.to_dict()
        assert result["request_id"] == "test-123"
        assert result["status"] == "denied"
        assert result["reason"] is None
        assert result["user_feedback"] is None
