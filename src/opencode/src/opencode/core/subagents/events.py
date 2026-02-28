"""
Subagent event system for UI integration.

Provides event types and emitter for tracking subagent execution.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Awaitable
import asyncio
import logging

logger = logging.getLogger(__name__)


class SubAgentEventType(str, Enum):
    """Types of subagent events."""
    START = "start"
    ROUND = "round"
    STREAM_TEXT = "stream_text"
    USAGE = "usage"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    FINISH = "finish"
    ERROR = "error"
    APPROVAL_REQUEST = "approval_request"


@dataclass
class SubAgentEvent:
    """Base event for subagent operations."""
    event_type: SubAgentEventType
    timestamp: datetime = field(default_factory=datetime.now)
    agent_name: str = ""
    session_id: str = ""


@dataclass
class SubAgentStartEvent(SubAgentEvent):
    """Event emitted when a subagent starts execution."""
    event_type: SubAgentEventType = SubAgentEventType.START
    task: str = ""
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SubAgentRoundEvent(SubAgentEvent):
    """Event emitted for each round of subagent execution."""
    event_type: SubAgentEventType = SubAgentEventType.ROUND
    round_number: int = 0
    max_rounds: int = 10


@dataclass
class SubAgentStreamTextEvent(SubAgentEvent):
    """Event emitted for streaming text from subagent."""
    event_type: SubAgentEventType = SubAgentEventType.STREAM_TEXT
    text: str = ""
    is_complete: bool = False


@dataclass
class SubAgentUsageEvent(SubAgentEvent):
    """Event emitted for token usage updates."""
    event_type: SubAgentEventType = SubAgentEventType.USAGE
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


@dataclass
class SubAgentToolCallEvent(SubAgentEvent):
    """Event emitted when a tool is called."""
    event_type: SubAgentEventType = SubAgentEventType.TOOL_CALL
    tool_name: str = ""
    tool_args: Dict[str, Any] = field(default_factory=dict)
    call_id: str = ""


@dataclass
class SubAgentToolResultEvent(SubAgentEvent):
    """Event emitted when a tool returns a result."""
    event_type: SubAgentEventType = SubAgentEventType.TOOL_RESULT
    tool_name: str = ""
    result: Any = None
    error: Optional[str] = None
    call_id: str = ""


@dataclass
class SubAgentFinishEvent(SubAgentEvent):
    """Event emitted when a subagent finishes execution."""
    event_type: SubAgentEventType = SubAgentEventType.FINISH
    success: bool = True
    result: str = ""
    total_rounds: int = 0
    total_tokens: int = 0


@dataclass
class SubAgentErrorEvent(SubAgentEvent):
    """Event emitted when a subagent encounters an error."""
    event_type: SubAgentEventType = SubAgentEventType.ERROR
    error_message: str = ""
    error_type: str = ""
    recoverable: bool = False


@dataclass
class SubAgentApprovalRequestEvent(SubAgentEvent):
    """Event emitted when a tool requires user approval."""
    event_type: SubAgentEventType = SubAgentEventType.APPROVAL_REQUEST
    tool_name: str = ""
    tool_args: Dict[str, Any] = field(default_factory=dict)
    risk_level: str = "medium"  # low, medium, high
    message: str = ""


# Type alias for event handlers
EventHandler = Callable[[SubAgentEvent], Awaitable[None]]


class SubAgentEventEmitter:
    """Event emitter for subagent execution.
    
    Provides a way to subscribe to subagent events and emit them
    during execution.
    """
    
    def __init__(self):
        """Initialize the event emitter."""
        self._handlers: Dict[SubAgentEventType, List[EventHandler]] = {
            event_type: [] for event_type in SubAgentEventType
        }
        self._any_handlers: List[EventHandler] = []
    
    def on(
        self,
        event_type: SubAgentEventType,
        handler: EventHandler
    ) -> None:
        """Subscribe to a specific event type.
        
        Args:
            event_type: Type of event to subscribe to
            handler: Async function to handle the event
        """
        self._handlers[event_type].append(handler)
    
    def on_any(self, handler: EventHandler) -> None:
        """Subscribe to all events.
        
        Args:
            handler: Async function to handle any event
        """
        self._any_handlers.append(handler)
    
    def off(
        self,
        event_type: SubAgentEventType,
        handler: EventHandler
    ) -> None:
        """Unsubscribe from a specific event type.
        
        Args:
            event_type: Type of event to unsubscribe from
            handler: Handler to remove
        """
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
    
    def off_any(self, handler: EventHandler) -> None:
        """Unsubscribe from all events.
        
        Args:
            handler: Handler to remove
        """
        if handler in self._any_handlers:
            self._any_handlers.remove(handler)
    
    async def emit(self, event: SubAgentEvent) -> None:
        """Emit an event to all subscribers.
        
        Args:
            event: Event to emit
        """
        # Emit to specific handlers
        for handler in self._handlers[event.event_type]:
            try:
                await handler(event)
            except Exception as e:
                # Don't let handler errors propagate
                logger.warning(f"Event handler error: {e}")
        
        # Emit to any handlers
        for handler in self._any_handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.warning(f"Any-event handler error: {e}")
    
    def emit_sync(self, event: SubAgentEvent) -> None:
        """Emit an event synchronously (creates a task).
        
        Args:
            event: Event to emit
        """
        asyncio.create_task(self.emit(event))
    
    def clear(self) -> None:
        """Clear all handlers."""
        for event_type in self._handlers:
            self._handlers[event_type] = []
        self._any_handlers = []
