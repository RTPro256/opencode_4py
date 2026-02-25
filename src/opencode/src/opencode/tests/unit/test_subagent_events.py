"""
Unit tests for subagent event system.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from opencode.core.subagents.events import (
    SubAgentEventType,
    SubAgentEvent,
    SubAgentStartEvent,
    SubAgentRoundEvent,
    SubAgentStreamTextEvent,
    SubAgentUsageEvent,
    SubAgentToolCallEvent,
    SubAgentToolResultEvent,
    SubAgentFinishEvent,
    SubAgentErrorEvent,
    SubAgentApprovalRequestEvent,
    SubAgentEventEmitter,
)


class TestSubAgentEventType:
    """Tests for SubAgentEventType enum."""
    
    def test_event_types_exist(self):
        """Test that all event types exist."""
        assert SubAgentEventType.START == "start"
        assert SubAgentEventType.ROUND == "round"
        assert SubAgentEventType.STREAM_TEXT == "stream_text"
        assert SubAgentEventType.USAGE == "usage"
        assert SubAgentEventType.TOOL_CALL == "tool_call"
        assert SubAgentEventType.TOOL_RESULT == "tool_result"
        assert SubAgentEventType.FINISH == "finish"
        assert SubAgentEventType.ERROR == "error"
        assert SubAgentEventType.APPROVAL_REQUEST == "approval_request"
    
    def test_event_type_count(self):
        """Test that we have the expected number of event types."""
        assert len(SubAgentEventType) == 9


class TestSubAgentEvent:
    """Tests for base SubAgentEvent."""
    
    def test_creation(self):
        """Test creating a base event."""
        event = SubAgentEvent(
            event_type=SubAgentEventType.START,
            agent_name="test_agent",
            session_id="session-123",
        )
        
        assert event.event_type == SubAgentEventType.START
        assert event.agent_name == "test_agent"
        assert event.session_id == "session-123"
        assert isinstance(event.timestamp, datetime)
    
    def test_default_values(self):
        """Test default values for base event."""
        event = SubAgentEvent(event_type=SubAgentEventType.ROUND)
        
        assert event.agent_name == ""
        assert event.session_id == ""


class TestSubAgentStartEvent:
    """Tests for SubAgentStartEvent."""
    
    def test_creation(self):
        """Test creating a start event."""
        event = SubAgentStartEvent(
            agent_name="code_agent",
            session_id="session-123",
            task="Fix the bug",
            config={"model": "gpt-4"},
        )
        
        assert event.event_type == SubAgentEventType.START
        assert event.task == "Fix the bug"
        assert event.config == {"model": "gpt-4"}
    
    def test_default_values(self):
        """Test default values for start event."""
        event = SubAgentStartEvent()
        
        assert event.event_type == SubAgentEventType.START
        assert event.task == ""
        assert event.config == {}


class TestSubAgentRoundEvent:
    """Tests for SubAgentRoundEvent."""
    
    def test_creation(self):
        """Test creating a round event."""
        event = SubAgentRoundEvent(
            agent_name="debug_agent",
            round_number=3,
            max_rounds=10,
        )
        
        assert event.event_type == SubAgentEventType.ROUND
        assert event.round_number == 3
        assert event.max_rounds == 10
    
    def test_default_values(self):
        """Test default values for round event."""
        event = SubAgentRoundEvent()
        
        assert event.round_number == 0
        assert event.max_rounds == 10


class TestSubAgentStreamTextEvent:
    """Tests for SubAgentStreamTextEvent."""
    
    def test_creation(self):
        """Test creating a stream text event."""
        event = SubAgentStreamTextEvent(
            text="Hello, world!",
            is_complete=False,
        )
        
        assert event.event_type == SubAgentEventType.STREAM_TEXT
        assert event.text == "Hello, world!"
        assert event.is_complete is False
    
    def test_default_values(self):
        """Test default values for stream text event."""
        event = SubAgentStreamTextEvent()
        
        assert event.text == ""
        assert event.is_complete is False


class TestSubAgentUsageEvent:
    """Tests for SubAgentUsageEvent."""
    
    def test_creation(self):
        """Test creating a usage event."""
        event = SubAgentUsageEvent(
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
        )
        
        assert event.event_type == SubAgentEventType.USAGE
        assert event.input_tokens == 100
        assert event.output_tokens == 50
        assert event.total_tokens == 150
    
    def test_default_values(self):
        """Test default values for usage event."""
        event = SubAgentUsageEvent()
        
        assert event.input_tokens == 0
        assert event.output_tokens == 0
        assert event.total_tokens == 0


class TestSubAgentToolCallEvent:
    """Tests for SubAgentToolCallEvent."""
    
    def test_creation(self):
        """Test creating a tool call event."""
        event = SubAgentToolCallEvent(
            tool_name="file_read",
            tool_args={"path": "/src/main.py"},
            call_id="call-123",
        )
        
        assert event.event_type == SubAgentEventType.TOOL_CALL
        assert event.tool_name == "file_read"
        assert event.tool_args == {"path": "/src/main.py"}
        assert event.call_id == "call-123"
    
    def test_default_values(self):
        """Test default values for tool call event."""
        event = SubAgentToolCallEvent()
        
        assert event.tool_name == ""
        assert event.tool_args == {}
        assert event.call_id == ""


class TestSubAgentToolResultEvent:
    """Tests for SubAgentToolResultEvent."""
    
    def test_creation_success(self):
        """Test creating a tool result event with success."""
        event = SubAgentToolResultEvent(
            tool_name="file_read",
            result="file contents",
            call_id="call-123",
        )
        
        assert event.event_type == SubAgentEventType.TOOL_RESULT
        assert event.tool_name == "file_read"
        assert event.result == "file contents"
        assert event.error is None
    
    def test_creation_error(self):
        """Test creating a tool result event with error."""
        event = SubAgentToolResultEvent(
            tool_name="file_read",
            result=None,
            error="File not found",
            call_id="call-456",
        )
        
        assert event.result is None
        assert event.error == "File not found"


class TestSubAgentFinishEvent:
    """Tests for SubAgentFinishEvent."""
    
    def test_creation_success(self):
        """Test creating a finish event with success."""
        event = SubAgentFinishEvent(
            success=True,
            result="Task completed successfully",
            total_rounds=5,
            total_tokens=500,
        )
        
        assert event.event_type == SubAgentEventType.FINISH
        assert event.success is True
        assert event.result == "Task completed successfully"
        assert event.total_rounds == 5
        assert event.total_tokens == 500
    
    def test_creation_failure(self):
        """Test creating a finish event with failure."""
        event = SubAgentFinishEvent(
            success=False,
            result="Task failed",
        )
        
        assert event.success is False


class TestSubAgentErrorEvent:
    """Tests for SubAgentErrorEvent."""
    
    def test_creation(self):
        """Test creating an error event."""
        event = SubAgentErrorEvent(
            error_message="API rate limit exceeded",
            error_type="RateLimitError",
            recoverable=True,
        )
        
        assert event.event_type == SubAgentEventType.ERROR
        assert event.error_message == "API rate limit exceeded"
        assert event.error_type == "RateLimitError"
        assert event.recoverable is True
    
    def test_default_values(self):
        """Test default values for error event."""
        event = SubAgentErrorEvent()
        
        assert event.error_message == ""
        assert event.error_type == ""
        assert event.recoverable is False


class TestSubAgentApprovalRequestEvent:
    """Tests for SubAgentApprovalRequestEvent."""
    
    def test_creation(self):
        """Test creating an approval request event."""
        event = SubAgentApprovalRequestEvent(
            tool_name="bash",
            tool_args={"command": "rm -rf /"},
            risk_level="high",
            message="This command may be dangerous",
        )
        
        assert event.event_type == SubAgentEventType.APPROVAL_REQUEST
        assert event.tool_name == "bash"
        assert event.tool_args == {"command": "rm -rf /"}
        assert event.risk_level == "high"
        assert event.message == "This command may be dangerous"
    
    def test_default_values(self):
        """Test default values for approval request event."""
        event = SubAgentApprovalRequestEvent()
        
        assert event.tool_name == ""
        assert event.tool_args == {}
        assert event.risk_level == "medium"
        assert event.message == ""


class TestSubAgentEventEmitter:
    """Tests for SubAgentEventEmitter."""
    
    def test_initialization(self):
        """Test emitter initialization."""
        emitter = SubAgentEventEmitter()
        
        # Should have empty handler lists for each event type
        for event_type in SubAgentEventType:
            assert emitter._handlers[event_type] == []
        assert emitter._any_handlers == []
    
    def test_on_subscribe(self):
        """Test subscribing to an event type."""
        emitter = SubAgentEventEmitter()
        
        async def handler(event):
            pass
        
        emitter.on(SubAgentEventType.START, handler)
        
        assert handler in emitter._handlers[SubAgentEventType.START]
    
    def test_on_any_subscribe(self):
        """Test subscribing to all events."""
        emitter = SubAgentEventEmitter()
        
        async def handler(event):
            pass
        
        emitter.on_any(handler)
        
        assert handler in emitter._any_handlers
    
    def test_off_unsubscribe(self):
        """Test unsubscribing from an event type."""
        emitter = SubAgentEventEmitter()
        
        async def handler(event):
            pass
        
        emitter.on(SubAgentEventType.START, handler)
        emitter.off(SubAgentEventType.START, handler)
        
        assert handler not in emitter._handlers[SubAgentEventType.START]
    
    def test_off_nonexistent_handler(self):
        """Test unsubscribing a handler that wasn't subscribed."""
        emitter = SubAgentEventEmitter()
        
        async def handler(event):
            pass
        
        # Should not raise an error
        emitter.off(SubAgentEventType.START, handler)
    
    def test_off_any_unsubscribe(self):
        """Test unsubscribing from all events."""
        emitter = SubAgentEventEmitter()
        
        async def handler(event):
            pass
        
        emitter.on_any(handler)
        emitter.off_any(handler)
        
        assert handler not in emitter._any_handlers
    
    def test_off_any_nonexistent_handler(self):
        """Test unsubscribing a handler that wasn't subscribed to any."""
        emitter = SubAgentEventEmitter()
        
        async def handler(event):
            pass
        
        # Should not raise an error
        emitter.off_any(handler)
    
    @pytest.mark.asyncio
    async def test_emit_to_specific_handlers(self):
        """Test emitting to specific handlers."""
        emitter = SubAgentEventEmitter()
        
        received = []
        
        async def handler1(event):
            received.append(("handler1", event))
        
        async def handler2(event):
            received.append(("handler2", event))
        
        emitter.on(SubAgentEventType.START, handler1)
        emitter.on(SubAgentEventType.START, handler2)
        
        event = SubAgentStartEvent(task="Test task")
        await emitter.emit(event)
        
        assert len(received) == 2
        assert ("handler1", event) in received
        assert ("handler2", event) in received
    
    @pytest.mark.asyncio
    async def test_emit_to_any_handlers(self):
        """Test emitting to any handlers."""
        emitter = SubAgentEventEmitter()
        
        received = []
        
        async def any_handler(event):
            received.append(event)
        
        emitter.on_any(any_handler)
        
        event = SubAgentStartEvent(task="Test task")
        await emitter.emit(event)
        
        assert len(received) == 1
        assert received[0] == event
    
    @pytest.mark.asyncio
    async def test_emit_handler_error_suppressed(self):
        """Test that handler errors are suppressed."""
        emitter = SubAgentEventEmitter()
        
        async def failing_handler(event):
            raise RuntimeError("Handler error")
        
        async def success_handler(event):
            success_handler.called = True
        
        emitter.on(SubAgentEventType.START, failing_handler)
        emitter.on(SubAgentEventType.START, success_handler)
        
        event = SubAgentStartEvent(task="Test task")
        
        # Should not raise an error
        await emitter.emit(event)
        
        # Success handler should still be called
        assert hasattr(success_handler, "called") and success_handler.called
    
    @pytest.mark.asyncio
    async def test_emit_any_handler_error_suppressed(self):
        """Test that any handler errors are suppressed."""
        emitter = SubAgentEventEmitter()
        
        async def failing_any_handler(event):
            raise RuntimeError("Any handler error")
        
        received = []
        
        async def success_any_handler(event):
            received.append(event)
        
        emitter.on_any(failing_any_handler)
        emitter.on_any(success_any_handler)
        
        event = SubAgentStartEvent(task="Test task")
        
        # Should not raise an error
        await emitter.emit(event)
        
        # Success handler should still be called
        assert len(received) == 1
    
    def test_clear(self):
        """Test clearing all handlers."""
        emitter = SubAgentEventEmitter()
        
        async def handler(event):
            pass
        
        # Subscribe to multiple event types
        emitter.on(SubAgentEventType.START, handler)
        emitter.on(SubAgentEventType.FINISH, handler)
        emitter.on_any(handler)
        
        emitter.clear()
        
        # All handlers should be cleared
        for event_type in SubAgentEventType:
            assert emitter._handlers[event_type] == []
        assert emitter._any_handlers == []
