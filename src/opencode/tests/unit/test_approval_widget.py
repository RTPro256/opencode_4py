"""Tests for TUI approval widget."""

import pytest
from unittest.mock import MagicMock, patch

from opencode.tui.widgets.approval import (
    ApprovalStatus,
    ApprovalRequest,
    ApprovalResponse,
)


class TestApprovalStatus:
    """Tests for ApprovalStatus enum."""

    def test_pending_value(self):
        """Test PENDING status value."""
        assert ApprovalStatus.PENDING.value == "pending"

    def test_approved_value(self):
        """Test APPROVED status value."""
        assert ApprovalStatus.APPROVED.value == "approved"

    def test_denied_value(self):
        """Test DENIED status value."""
        assert ApprovalStatus.DENIED.value == "denied"

    def test_always_approve_value(self):
        """Test ALWAYS_APPROVE status value."""
        assert ApprovalStatus.ALWAYS_APPROVE.value == "always_approve"

    def test_timeout_value(self):
        """Test TIMEOUT status value."""
        assert ApprovalStatus.TIMEOUT.value == "timeout"

    def test_all_statuses_exist(self):
        """Test all expected statuses exist."""
        statuses = [s.value for s in ApprovalStatus]
        assert "pending" in statuses
        assert "approved" in statuses
        assert "denied" in statuses
        assert "always_approve" in statuses
        assert "timeout" in statuses


class TestApprovalRequest:
    """Tests for ApprovalRequest dataclass."""

    def test_create_with_required_fields(self):
        """Test creating request with required fields."""
        request = ApprovalRequest(
            request_id="req-123",
            title="Test Request",
            description="Test description",
        )
        
        assert request.request_id == "req-123"
        assert request.title == "Test Request"
        assert request.description == "Test description"

    def test_default_values(self):
        """Test default values."""
        request = ApprovalRequest(
            request_id="req-123",
            title="Test",
            description="Test",
        )
        
        assert request.details == {}
        assert request.risk_level == "medium"
        assert request.timeout_seconds == 60
        assert request.auto_approve_safe is False

    def test_custom_values(self):
        """Test custom values."""
        request = ApprovalRequest(
            request_id="req-456",
            title="Custom Request",
            description="Custom description",
            details={"key": "value"},
            risk_level="high",
            timeout_seconds=120,
            auto_approve_safe=True,
        )
        
        assert request.request_id == "req-456"
        assert request.title == "Custom Request"
        assert request.description == "Custom description"
        assert request.details == {"key": "value"}
        assert request.risk_level == "high"
        assert request.timeout_seconds == 120
        assert request.auto_approve_safe is True

    def test_to_dict(self):
        """Test to_dict method."""
        request = ApprovalRequest(
            request_id="req-789",
            title="Dict Test",
            description="Testing dict conversion",
            details={"command": "ls -la"},
            risk_level="low",
            timeout_seconds=30,
        )
        
        result = request.to_dict()
        
        assert result["request_id"] == "req-789"
        assert result["title"] == "Dict Test"
        assert result["description"] == "Testing dict conversion"
        assert result["details"] == {"command": "ls -la"}
        assert result["risk_level"] == "low"
        assert result["timeout_seconds"] == 30

    def test_to_dict_excludes_auto_approve(self):
        """Test that to_dict excludes auto_approve_safe."""
        request = ApprovalRequest(
            request_id="req-001",
            title="Test",
            description="Test",
            auto_approve_safe=True,
        )
        
        result = request.to_dict()
        
        assert "auto_approve_safe" not in result


class TestApprovalResponse:
    """Tests for ApprovalResponse dataclass."""

    def test_create_approved(self):
        """Test creating approved response."""
        response = ApprovalResponse(
            request_id="req-123",
            status=ApprovalStatus.APPROVED,
        )
        
        assert response.request_id == "req-123"
        assert response.status == ApprovalStatus.APPROVED
        assert response.reason is None
        assert response.user_feedback is None

    def test_create_denied_with_reason(self):
        """Test creating denied response with reason."""
        response = ApprovalResponse(
            request_id="req-456",
            status=ApprovalStatus.DENIED,
            reason="Security concern",
            user_feedback="Please review",
        )
        
        assert response.request_id == "req-456"
        assert response.status == ApprovalStatus.DENIED
        assert response.reason == "Security concern"
        assert response.user_feedback == "Please review"

    def test_create_timeout(self):
        """Test creating timeout response."""
        response = ApprovalResponse(
            request_id="req-789",
            status=ApprovalStatus.TIMEOUT,
        )
        
        assert response.status == ApprovalStatus.TIMEOUT

    def test_create_always_approve(self):
        """Test creating always approve response."""
        response = ApprovalResponse(
            request_id="req-101",
            status=ApprovalStatus.ALWAYS_APPROVE,
        )
        
        assert response.status == ApprovalStatus.ALWAYS_APPROVE

    def test_to_dict(self):
        """Test to_dict method."""
        response = ApprovalResponse(
            request_id="req-202",
            status=ApprovalStatus.DENIED,
            reason="Too risky",
            user_feedback="Need more info",
        )
        
        result = response.to_dict()
        
        assert result["request_id"] == "req-202"
        assert result["status"] == "denied"
        assert result["reason"] == "Too risky"
        assert result["user_feedback"] == "Need more info"

    def test_to_dict_with_none_values(self):
        """Test to_dict with None values."""
        response = ApprovalResponse(
            request_id="req-303",
            status=ApprovalStatus.APPROVED,
        )
        
        result = response.to_dict()
        
        assert result["request_id"] == "req-303"
        assert result["status"] == "approved"
        assert result["reason"] is None
        assert result["user_feedback"] is None
