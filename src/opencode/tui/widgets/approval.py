"""
Approval Dialog Widget

Provides approval dialogs for tool execution in the TUI.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import logging

from textual.widget import Widget
from textual.message import Message
from textual.reactive import reactive

logger = logging.getLogger(__name__)


class ApprovalStatus(Enum):
    """Status of an approval request."""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    ALWAYS_APPROVE = "always_approve"
    TIMEOUT = "timeout"


@dataclass
class ApprovalRequest:
    """A request for approval."""
    request_id: str
    title: str
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    risk_level: str = "medium"  # low, medium, high
    timeout_seconds: int = 60
    auto_approve_safe: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "request_id": self.request_id,
            "title": self.title,
            "description": self.description,
            "details": self.details,
            "risk_level": self.risk_level,
            "timeout_seconds": self.timeout_seconds,
        }


@dataclass
class ApprovalResponse:
    """Response to an approval request."""
    request_id: str
    status: ApprovalStatus
    reason: Optional[str] = None
    user_feedback: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "request_id": self.request_id,
            "status": self.status.value,
            "reason": self.reason,
            "user_feedback": self.user_feedback,
        }


class ApprovalDialog(Widget):
    """
    Dialog widget for approving or denying actions.
    
    Shows a modal dialog with details about the action being
    requested and buttons to approve or deny.
    
    Example:
        dialog = ApprovalDialog()
        dialog.show_request(
            ApprovalRequest(
                request_id="123",
                title="Execute Command",
                description="Run: npm install",
                details={"command": "npm install"},
                risk_level="low",
            )
        )
    """
    
    DEFAULT_CSS = """
    ApprovalDialog {
        display: none;
        align: center middle;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
        width: 60;
        height: auto;
    }
    
    ApprovalDialog.visible {
        display: block;
    }
    
    ApprovalDialog .title {
        text-style: bold;
        margin-bottom: 1;
    }
    
    ApprovalDialog .description {
        margin-bottom: 1;
    }
    
    ApprovalDialog .details {
        background: $surface-darken-1;
        padding: 1;
        margin-bottom: 1;
    }
    
    ApprovalDialog .risk-low {
        color: $success;
    }
    
    ApprovalDialog .risk-medium {
        color: $warning;
    }
    
    ApprovalDialog .risk-high {
        color: $error;
    }
    
    ApprovalDialog .buttons {
        align: center;
        margin-top: 1;
    }
    
    ApprovalDialog .button {
        margin: 0 1;
    }
    """
    
    current_request: reactive[Optional[ApprovalRequest]] = reactive(None)
    visible: reactive[bool] = reactive(False)
    timeout_remaining: reactive[int] = reactive(0)
    
    class Approved(Message):
        """Message sent when request is approved."""
        def __init__(self, response: ApprovalResponse):
            self.response = response
            super().__init__()
    
    class Denied(Message):
        """Message sent when request is denied."""
        def __init__(self, response: ApprovalResponse):
            self.response = response
            super().__init__()
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._timeout_timer: Optional[Any] = None
        self._response_callback: Optional[Callable] = None
    
    def show_request(
        self,
        request: ApprovalRequest,
        callback: Optional[Callable] = None,
    ) -> None:
        """
        Show an approval request.
        
        Args:
            request: The approval request
            callback: Optional callback for the response
        """
        self.current_request = request
        self.visible = True
        self.timeout_remaining = request.timeout_seconds
        self._response_callback = callback
        
        # Start timeout timer
        if request.timeout_seconds > 0:
            self._start_timeout_timer()
    
    def hide(self) -> None:
        """Hide the dialog."""
        self.visible = False
        self.current_request = None
        self._stop_timeout_timer()
    
    def approve(self, always: bool = False) -> None:
        """Approve the current request."""
        if not self.current_request:
            return
        
        status = ApprovalStatus.ALWAYS_APPROVE if always else ApprovalStatus.APPROVED
        response = ApprovalResponse(
            request_id=self.current_request.request_id,
            status=status,
        )
        
        self.post_message(self.Approved(response))
        
        if self._response_callback:
            self._response_callback(response)
        
        self.hide()
    
    def deny(self, reason: Optional[str] = None) -> None:
        """Deny the current request."""
        if not self.current_request:
            return
        
        response = ApprovalResponse(
            request_id=self.current_request.request_id,
            status=ApprovalStatus.DENIED,
            reason=reason,
        )
        
        self.post_message(self.Denied(response))
        
        if self._response_callback:
            self._response_callback(response)
        
        self.hide()
    
    def _start_timeout_timer(self) -> None:
        """Start the timeout countdown."""
        self._stop_timeout_timer()
        self._timeout_timer = self.set_interval(1, self._on_timeout_tick)
    
    def _stop_timeout_timer(self) -> None:
        """Stop the timeout timer."""
        if self._timeout_timer:
            self._timeout_timer.stop()
            self._timeout_timer = None
    
    def _on_timeout_tick(self) -> None:
        """Handle timeout tick."""
        if not self.current_request:
            return
        
        self.timeout_remaining -= 1
        
        if self.timeout_remaining <= 0:
            # Timeout - deny automatically
            response = ApprovalResponse(
                request_id=self.current_request.request_id,
                status=ApprovalStatus.TIMEOUT,
                reason="Approval timed out",
            )
            
            self.post_message(self.Denied(response))
            
            if self._response_callback:
                self._response_callback(response)
            
            self.hide()
    
    def render(self) -> str:
        """Render the dialog."""
        if not self.visible or not self.current_request:
            return ""
        
        request = self.current_request
        
        # Build risk indicator
        risk_class = f"risk-{request.risk_level}"
        risk_text = f"[{risk_class}]Risk: {request.risk_level.upper()}[/{risk_class}]"
        
        # Build details section
        details_lines = []
        for key, value in request.details.items():
            details_lines.append(f"  {key}: {value}")
        details_text = "\n".join(details_lines) if details_lines else "  No additional details"
        
        # Build timeout indicator
        timeout_text = f"\n\nTimeout in: {self.timeout_remaining}s" if self.timeout_remaining > 0 else ""
        
        return f"""
[bold]{request.title}[/bold]

{request.description}

{risk_text}

[italic]Details:[/italic]
{details_text}
{timeout_text}

[1] Approve  [2] Always Approve  [3] Deny  [Esc] Cancel
"""


class ApprovalManager:
    """
    Manages approval requests and responses.
    
    Provides a centralized way to request approvals for actions
    and track approval history.
    
    Example:
        manager = ApprovalManager()
        
        # Request approval
        response = await manager.request_approval(
            title="Delete File",
            description="Delete: config.yaml",
            risk_level="high",
            details={"file": "config.yaml"},
        )
        
        if response.status == ApprovalStatus.APPROVED:
            # Proceed with action
            pass
    """
    
    def __init__(
        self,
        auto_approve_safe: bool = False,
        default_timeout: int = 60,
    ):
        """
        Initialize the approval manager.
        
        Args:
            auto_approve_safe: Auto-approve low-risk actions
            default_timeout: Default timeout in seconds
        """
        self.auto_approve_safe = auto_approve_safe
        self.default_timeout = default_timeout
        
        self._pending_requests: Dict[str, ApprovalRequest] = {}
        self._history: List[ApprovalResponse] = []
        self._always_approve: Dict[str, bool] = {}  # action_type -> always_approve
        self._request_id_counter = 0
    
    def _generate_request_id(self) -> str:
        """Generate a unique request ID."""
        self._request_id_counter += 1
        return f"approval_{self._request_id_counter}"
    
    async def request_approval(
        self,
        title: str,
        description: str,
        risk_level: str = "medium",
        details: Optional[Dict[str, Any]] = None,
        action_type: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> ApprovalResponse:
        """
        Request approval for an action.
        
        Args:
            title: Dialog title
            description: Action description
            risk_level: Risk level (low, medium, high)
            details: Additional details
            action_type: Type of action (for always-approve tracking)
            timeout: Timeout in seconds
            
        Returns:
            ApprovalResponse
        """
        request_id = self._generate_request_id()
        
        # Check if always-approve is set for this action type
        if action_type and self._always_approve.get(action_type, False):
            return ApprovalResponse(
                request_id=request_id,
                status=ApprovalStatus.ALWAYS_APPROVE,
            )
        
        # Auto-approve safe actions if configured
        if self.auto_approve_safe and risk_level == "low":
            return ApprovalResponse(
                request_id=request_id,
                status=ApprovalStatus.APPROVED,
                reason="Auto-approved (safe action)",
            )
        
        # Create request
        request = ApprovalRequest(
            request_id=request_id,
            title=title,
            description=description,
            details=details or {},
            risk_level=risk_level,
            timeout_seconds=timeout or self.default_timeout,
        )
        
        self._pending_requests[request_id] = request
        
        # In a real implementation, this would show the dialog and wait
        # For now, we return a pending response
        return ApprovalResponse(
            request_id=request_id,
            status=ApprovalStatus.PENDING,
        )
    
    def set_always_approve(self, action_type: str, always: bool) -> None:
        """
        Set always-approve for an action type.
        
        Args:
            action_type: Type of action
            always: Whether to always approve
        """
        self._always_approve[action_type] = always
    
    def record_response(self, response: ApprovalResponse) -> None:
        """Record a response in history."""
        self._history.append(response)
        
        # Remove from pending
        if response.request_id in self._pending_requests:
            del self._pending_requests[response.request_id]
    
    def get_history(self, limit: int = 100) -> List[ApprovalResponse]:
        """Get approval history."""
        return self._history[-limit:]
    
    def get_pending_count(self) -> int:
        """Get number of pending requests."""
        return len(self._pending_requests)
    
    def clear_history(self) -> None:
        """Clear approval history."""
        self._history.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get approval statistics."""
        total = len(self._history)
        approved = len([r for r in self._history if r.status in (
            ApprovalStatus.APPROVED,
            ApprovalStatus.ALWAYS_APPROVE,
        )])
        denied = len([r for r in self._history if r.status == ApprovalStatus.DENIED])
        timeout = len([r for r in self._history if r.status == ApprovalStatus.TIMEOUT])
        
        return {
            "total_requests": total,
            "approved": approved,
            "denied": denied,
            "timeout": timeout,
            "approval_rate": approved / total if total > 0 else 0,
            "pending": len(self._pending_requests),
        }
