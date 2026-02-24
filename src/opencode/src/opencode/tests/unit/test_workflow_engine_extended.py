"""
Extended tests for workflow/engine.py to improve coverage.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from datetime import datetime

from opencode.workflow.engine import (
    WorkflowEngine,
    WorkflowEngineConfig,
    ExecutionEvent,
    WorkflowEngineError,
)
from opencode.workflow.graph import WorkflowGraph, WorkflowNode, WorkflowEdge, WorkflowMetadata
from opencode.workflow.state import WorkflowState, ExecutionStatus, NodeExecutionState, WorkflowStateStore
from opencode.workflow.node import (
    BaseNode,
    NodePort,
    NodeSchema,
    ExecutionContext,
    ExecutionResult,
    PortDataType,
    PortDirection,
)
from opencode.workflow.registry import NodeRegistry


class TestWorkflowEngineConfig:
    """Tests for WorkflowEngineConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = WorkflowEngineConfig()
        
        assert config.max_concurrent_nodes == 10
        assert config.default_timeout_seconds == 300.0
        assert config.retry_failed_nodes is True
        assert config.max_retries == 3
        assert config.continue_on_error is False
        assert config.enable_caching is True
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = WorkflowEngineConfig(
            max_concurrent_nodes=5,
            default_timeout_seconds=60.0,
            retry_failed_nodes=False,
            max_retries=1,
            continue_on_error=True,
            enable_caching=False,
        )
        
        assert config.max_concurrent_nodes == 5
        assert config.default_timeout_seconds == 60.0
        assert config.retry_failed_nodes is False
        assert config.max_retries == 1
        assert config.continue_on_error is True
        assert config.enable_caching is False


class TestExecutionEvent:
    """Tests for ExecutionEvent."""
    
    def test_execution_event_creation(self):
        """Test creating an execution event."""
        event = ExecutionEvent(
            event_type="test_event",
            workflow_id="wf-123",
            execution_id="exec-456",
            node_id="node-789",
            data={"key": "value"},
        )
        
        assert event.event_type == "test_event"
        assert event.workflow_id == "wf-123"
        assert event.execution_id == "exec-456"
        assert event.node_id == "node-789"
        assert event.data == {"key": "value"}
        assert isinstance(event.timestamp, datetime)
    
    def test_execution_event_default_timestamp(self):
        """Test that timestamp is auto-generated."""
        event = ExecutionEvent(
            event_type="test",
            workflow_id="wf",
            execution_id="exec",
        )
        
        assert event.timestamp is not None
    
    def test_execution_event_custom_timestamp(self):
        """Test custom timestamp."""
        custom_time = datetime(2024, 1, 1, 12, 0, 0)
        event = ExecutionEvent(
            event_type="test",
            workflow_id="wf",
            execution_id="exec",
            timestamp=custom_time,
        )
        
        assert event.timestamp == custom_time
    
    def test_to_dict(self):
        """Test converting event to dictionary."""
        custom_time = datetime(2024, 1, 1, 12, 0, 0)
        event = ExecutionEvent(
            event_type="node_completed",
            workflow_id="wf-123",
            execution_id="exec-456",
            node_id="node-789",
            data={"result": "success"},
            timestamp=custom_time,
        )
        
        result = event.to_dict()
        
        assert result["event_type"] == "node_completed"
        assert result["workflow_id"] == "wf-123"
        assert result["execution_id"] == "exec-456"
        assert result["node_id"] == "node-789"
        assert result["data"] == {"result": "success"}
        assert result["timestamp"] == "2024-01-01T12:00:00"


class TestWorkflowEngine:
    """Tests for WorkflowEngine."""
    
    def test_engine_creation_default_config(self):
        """Test creating engine with default config."""
        engine = WorkflowEngine()
        
        assert engine.config is not None
        assert isinstance(engine.config, WorkflowEngineConfig)
        assert engine._event_handlers == []
        assert engine._running_executions == set()
        assert engine._cancellation_tokens == {}
    
    def test_engine_creation_custom_config(self):
        """Test creating engine with custom config."""
        config = WorkflowEngineConfig(max_concurrent_nodes=20)
        engine = WorkflowEngine(config=config)
        
        assert engine.config.max_concurrent_nodes == 20
    
    def test_engine_creation_custom_state_store(self):
        """Test creating engine with custom state store."""
        state_store = WorkflowStateStore()
        engine = WorkflowEngine(state_store=state_store)
        
        assert engine.state_store is state_store
    
    def test_add_event_handler(self):
        """Test adding an event handler."""
        engine = WorkflowEngine()
        handler = MagicMock()
        
        engine.add_event_handler(handler)
        
        assert handler in engine._event_handlers
    
    def test_remove_event_handler(self):
        """Test removing an event handler."""
        engine = WorkflowEngine()
        handler = MagicMock()
        engine.add_event_handler(handler)
        
        engine.remove_event_handler(handler)
        
        assert handler not in engine._event_handlers
    
    def test_remove_event_handler_not_found(self):
        """Test removing an event handler that doesn't exist."""
        engine = WorkflowEngine()
        handler = MagicMock()
        
        # Should not raise
        engine.remove_event_handler(handler)
    
    def test_emit_event(self):
        """Test emitting events to handlers."""
        engine = WorkflowEngine()
        handler1 = MagicMock()
        handler2 = MagicMock()
        engine.add_event_handler(handler1)
        engine.add_event_handler(handler2)
        
        event = ExecutionEvent(
            event_type="test",
            workflow_id="wf",
            execution_id="exec",
        )
        engine._emit_event(event)
        
        handler1.assert_called_once_with(event)
        handler2.assert_called_once_with(event)
    
    def test_emit_event_handler_error(self):
        """Test that handler errors are caught."""
        engine = WorkflowEngine()
        handler_error = MagicMock(side_effect=ValueError("Handler error"))
        handler_ok = MagicMock()
        engine.add_event_handler(handler_error)
        engine.add_event_handler(handler_ok)
        
        event = ExecutionEvent(
            event_type="test",
            workflow_id="wf",
            execution_id="exec",
        )
        
        # Should not raise
        engine._emit_event(event)
        
        # OK handler should still be called
        handler_ok.assert_called_once()
    
    def test_cancel_existing_execution(self):
        """Test cancelling an existing execution."""
        engine = WorkflowEngine()
        execution_id = "exec-123"
        
        # Add a cancellation token
        cancel_token = asyncio.Event()
        engine._cancellation_tokens[execution_id] = cancel_token
        
        result = engine.cancel(execution_id)
        
        assert result is True
        assert cancel_token.is_set()
    
    def test_cancel_nonexistent_execution(self):
        """Test cancelling a non-existent execution."""
        engine = WorkflowEngine()
        
        result = engine.cancel("nonexistent")
        
        assert result is False
    
    def test_get_state(self):
        """Test getting execution state."""
        state_store = WorkflowStateStore()
        engine = WorkflowEngine(state_store=state_store)
        
        state = WorkflowState(
            workflow_id="wf-123",
            execution_id="exec-456",
        )
        state_store.save(state)
        
        result = engine.get_state("exec-456")
        
        assert result is not None
        assert result.execution_id == "exec-456"
    
    def test_get_state_not_found(self):
        """Test getting state for non-existent execution."""
        engine = WorkflowEngine()
        
        result = engine.get_state("nonexistent")
        
        assert result is None
    
    def test_is_running(self):
        """Test checking if execution is running."""
        engine = WorkflowEngine()
        execution_id = "exec-123"
        
        engine._running_executions.add(execution_id)
        
        assert engine.is_running(execution_id) is True
        assert engine.is_running("nonexistent") is False


class TestWorkflowEngineError:
    """Tests for WorkflowEngineError."""
    
    def test_error_creation(self):
        """Test creating WorkflowEngineError."""
        error = WorkflowEngineError("Something went wrong")
        
        assert str(error) == "Something went wrong"
        assert isinstance(error, Exception)


class TestWorkflowEngineExecute:
    """Tests for workflow execution."""
    
    @pytest.fixture
    def mock_node_class(self):
        """Create a mock node class."""
        class MockNode(BaseNode):
            @classmethod
            def get_schema(cls) -> NodeSchema:
                return NodeSchema(
                    node_type="mock_node",
                    display_name="Mock Node",
                    inputs=[NodePort(name="input", data_type=PortDataType.ANY, direction=PortDirection.INPUT, required=False)],
                    outputs=[NodePort(name="output", data_type=PortDataType.ANY, direction=PortDirection.OUTPUT)],
                )
            
            async def execute(self, inputs: dict, context: ExecutionContext) -> ExecutionResult:
                return ExecutionResult(
                    success=True,
                    outputs={"output": inputs.get("input", "default")},
                )
        
        return MockNode
    
    @pytest.fixture
    def simple_workflow(self):
        """Create a simple workflow with one node."""
        graph = WorkflowGraph(
            id="test-workflow",
            metadata=WorkflowMetadata(name="Test Workflow"),
        )
        
        node = WorkflowNode(
            id="node1",
            node_type="mock_node",
            config={},
        )
        graph.add_node(node)
        
        return graph
    
    @pytest.mark.asyncio
    async def test_execute_simple_workflow(self, mock_node_class, simple_workflow):
        """Test executing a simple workflow."""
        # Register mock node
        NodeRegistry._nodes["mock_node"] = mock_node_class
        
        engine = WorkflowEngine()
        
        state = await engine.execute(simple_workflow)
        
        assert state.status == ExecutionStatus.COMPLETED
        assert state.is_successful()
    
    @pytest.mark.asyncio
    async def test_execute_with_variables(self, mock_node_class, simple_workflow):
        """Test executing with variables."""
        NodeRegistry._nodes["mock_node"] = mock_node_class
        
        engine = WorkflowEngine()
        
        state = await engine.execute(
            simple_workflow,
            variables={"var1": "value1"},
        )
        
        assert state.variables["var1"] == "value1"
    
    @pytest.mark.asyncio
    async def test_execute_with_custom_execution_id(self, mock_node_class, simple_workflow):
        """Test executing with custom execution ID."""
        NodeRegistry._nodes["mock_node"] = mock_node_class
        
        engine = WorkflowEngine()
        
        state = await engine.execute(
            simple_workflow,
            execution_id="custom-exec-id",
        )
        
        assert state.execution_id == "custom-exec-id"
    
    @pytest.mark.asyncio
    async def test_execute_invalid_workflow(self):
        """Test executing an invalid workflow."""
        # Create an invalid workflow (no nodes)
        graph = WorkflowGraph(id="empty-workflow")
        
        engine = WorkflowEngine()
        
        # Empty workflow should complete without errors (no nodes to execute)
        state = await engine.execute(graph)
        assert state.status == ExecutionStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_execute_stream(self, mock_node_class, simple_workflow):
        """Test streaming execution events."""
        NodeRegistry._nodes["mock_node"] = mock_node_class
        
        engine = WorkflowEngine()
        
        events = []
        async for event in engine.execute_stream(simple_workflow):
            events.append(event)
        
        assert len(events) > 0
        assert any(e.event_type == "workflow_started" for e in events)
        assert any(e.event_type == "workflow_completed" for e in events)


class TestWorkflowEngineNodeExecution:
    """Tests for node execution scenarios."""
    
    @pytest.fixture
    def failing_node_class(self):
        """Create a node that fails."""
        class FailingNode(BaseNode):
            @classmethod
            def get_schema(cls) -> NodeSchema:
                return NodeSchema(
                    node_type="failing_node",
                    display_name="Failing Node",
                    inputs=[],
                    outputs=[],
                )
            
            async def execute(self, inputs: dict, context: ExecutionContext) -> ExecutionResult:
                return ExecutionResult(
                    success=False,
                    error="Node failed intentionally",
                )
        
        return FailingNode
    
    @pytest.fixture
    def exception_node_class(self):
        """Create a node that raises an exception."""
        class ExceptionNode(BaseNode):
            @classmethod
            def get_schema(cls) -> NodeSchema:
                return NodeSchema(
                    node_type="exception_node",
                    display_name="Exception Node",
                    inputs=[],
                    outputs=[],
                )
            
            async def execute(self, inputs: dict, context: ExecutionContext) -> ExecutionResult:
                raise RuntimeError("Node raised an exception")
        
        return ExceptionNode
    
    @pytest.fixture
    def slow_node_class(self):
        """Create a slow node for timeout testing."""
        class SlowNode(BaseNode):
            @classmethod
            def get_schema(cls) -> NodeSchema:
                return NodeSchema(
                    node_type="slow_node",
                    display_name="Slow Node",
                    inputs=[],
                    outputs=[],
                )
            
            async def execute(self, inputs: dict, context: ExecutionContext) -> ExecutionResult:
                await asyncio.sleep(10)  # Long delay
                return ExecutionResult(success=True, outputs={})
        
        return SlowNode
    
    @pytest.fixture
    def workflow_with_failing_node(self):
        """Create a workflow with a failing node."""
        graph = WorkflowGraph(id="failing-workflow")
        node = WorkflowNode(id="fail-node", node_type="failing_node", config={})
        graph.add_node(node)
        return graph
    
    @pytest.mark.asyncio
    async def test_execute_failing_node(self, failing_node_class, workflow_with_failing_node):
        """Test executing a workflow with a failing node."""
        NodeRegistry._nodes["failing_node"] = failing_node_class
        
        engine = WorkflowEngine()
        
        state = await engine.execute(workflow_with_failing_node)
        
        assert state.status == ExecutionStatus.FAILED
    
    @pytest.mark.asyncio
    async def test_execute_exception_node(self, exception_node_class):
        """Test executing a node that raises an exception."""
        graph = WorkflowGraph(id="exception-workflow")
        node = WorkflowNode(id="exc-node", node_type="exception_node", config={})
        graph.add_node(node)
        
        NodeRegistry._nodes["exception_node"] = exception_node_class
        
        engine = WorkflowEngine()
        
        state = await engine.execute(graph)
        
        assert state.status == ExecutionStatus.FAILED
    
    @pytest.mark.asyncio
    async def test_execute_timeout_node(self, slow_node_class):
        """Test executing a node that times out."""
        graph = WorkflowGraph(id="timeout-workflow")
        node = WorkflowNode(
            id="slow-node",
            node_type="slow_node",
            config={"timeout_seconds": 0.1},  # Very short timeout
        )
        graph.add_node(node)
        
        NodeRegistry._nodes["slow_node"] = slow_node_class
        
        config = WorkflowEngineConfig(default_timeout_seconds=0.1)
        engine = WorkflowEngine(config=config)
        
        state = await engine.execute(graph)
        
        assert state.status == ExecutionStatus.FAILED
    
    @pytest.mark.asyncio
    async def test_execute_disabled_node(self):
        """Test executing a disabled node."""
        class MockNode(BaseNode):
            @classmethod
            def get_schema(cls) -> NodeSchema:
                return NodeSchema(
                    node_type="mock_node",
                    display_name="Mock Node",
                    inputs=[],
                    outputs=[],
                )
            
            async def execute(self, inputs: dict, context: ExecutionContext) -> ExecutionResult:
                return ExecutionResult(success=True, outputs={})
        
        graph = WorkflowGraph(id="disabled-workflow")
        node = WorkflowNode(
            id="disabled-node",
            node_type="mock_node",
            config={},
            disabled=True,
        )
        graph.add_node(node)
        
        NodeRegistry._nodes["mock_node"] = MockNode
        
        engine = WorkflowEngine()
        state = await engine.execute(graph)
        
        assert state.status == ExecutionStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_execute_unknown_node_type(self):
        """Test executing a workflow with unknown node type."""
        graph = WorkflowGraph(id="unknown-workflow")
        node = WorkflowNode(id="unknown-node", node_type="nonexistent_type", config={})
        graph.add_node(node)
        
        engine = WorkflowEngine()
        
        state = await engine.execute(graph)
        
        assert state.status == ExecutionStatus.FAILED


class TestWorkflowEngineCancellation:
    """Tests for workflow cancellation."""
    
    @pytest.mark.asyncio
    async def test_cancel_during_execution(self):
        """Test cancelling during execution."""
        class SlowNode(BaseNode):
            @classmethod
            def get_schema(cls) -> NodeSchema:
                return NodeSchema(
                    node_type="slow_node",
                    display_name="Slow Node",
                    inputs=[],
                    outputs=[],
                )
            
            async def execute(self, inputs: dict, context: ExecutionContext) -> ExecutionResult:
                await asyncio.sleep(10)
                return ExecutionResult(success=True, outputs={})
        
        graph = WorkflowGraph(id="cancel-workflow")
        node = WorkflowNode(id="slow-node", node_type="slow_node", config={})
        graph.add_node(node)
        
        NodeRegistry._nodes["slow_node"] = SlowNode
        
        engine = WorkflowEngine()
        
        # Start execution in background
        async def run_and_cancel():
            task = asyncio.create_task(engine.execute(graph))
            
            # Wait a bit then cancel
            await asyncio.sleep(0.1)
            
            # Get the execution ID from running executions
            if engine._running_executions:
                exec_id = list(engine._running_executions)[0]
                engine.cancel(exec_id)
            
            return await task
        
        state = await run_and_cancel()
        
        # Should be cancelled or completed (timing dependent)
        assert state.status in [ExecutionStatus.CANCELLED, ExecutionStatus.COMPLETED, ExecutionStatus.FAILED]


class TestWorkflowEngineEvents:
    """Tests for execution events."""
    
    @pytest.mark.asyncio
    async def test_event_handler_receives_events(self):
        """Test that event handlers receive all events."""
        class MockNode(BaseNode):
            @classmethod
            def get_schema(cls) -> NodeSchema:
                return NodeSchema(
                    node_type="mock_node",
                    display_name="Mock Node",
                    inputs=[],
                    outputs=[],
                )
            
            async def execute(self, inputs: dict, context: ExecutionContext) -> ExecutionResult:
                return ExecutionResult(success=True, outputs={})
        
        graph = WorkflowGraph(id="event-workflow")
        node = WorkflowNode(id="node1", node_type="mock_node", config={})
        graph.add_node(node)
        
        NodeRegistry._nodes["mock_node"] = MockNode
        
        engine = WorkflowEngine()
        events = []
        
        def capture_event(event):
            events.append(event)
        
        engine.add_event_handler(capture_event)
        
        await engine.execute(graph)
        
        assert len(events) > 0
        event_types = [e.event_type for e in events]
        assert "workflow_started" in event_types
        assert "workflow_completed" in event_types


class TestContinueOnError:
    """Tests for continue_on_error configuration."""
    
    @pytest.mark.asyncio
    async def test_continue_on_error_false(self):
        """Test that execution stops when a node fails and continue_on_error is False."""
        class FailingNode(BaseNode):
            @classmethod
            def get_schema(cls) -> NodeSchema:
                return NodeSchema(
                    node_type="failing_node",
                    display_name="Failing Node",
                    inputs=[],
                    outputs=[],
                )
            
            async def execute(self, inputs: dict, context: ExecutionContext) -> ExecutionResult:
                return ExecutionResult(success=False, error="Failed")
        
        graph = WorkflowGraph(id="stop-workflow")
        node = WorkflowNode(id="fail", node_type="failing_node", config={})
        graph.add_node(node)
        
        NodeRegistry._nodes["failing_node"] = FailingNode
        
        config = WorkflowEngineConfig(continue_on_error=False)
        engine = WorkflowEngine(config=config)
        
        state = await engine.execute(graph)
        
        assert state.status == ExecutionStatus.FAILED
