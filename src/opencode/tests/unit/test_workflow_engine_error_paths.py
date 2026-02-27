"""
Extended tests for workflow engine error paths and edge cases.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio

from opencode.workflow.engine import (
    WorkflowEngine,
    WorkflowEngineConfig,
    ExecutionEvent,
)
from opencode.workflow.graph import WorkflowGraph, WorkflowNode, WorkflowEdge, WorkflowMetadata
from opencode.workflow.state import WorkflowState, ExecutionStatus, NodeExecutionState
from opencode.workflow.node import BaseNode, NodePort, NodeSchema, ExecutionResult
from opencode.workflow.registry import NodeRegistry


class TestWorkflowEngineConfig:
    """Tests for WorkflowEngineConfig."""

    @pytest.mark.unit
    def test_default_config(self):
        """Test default configuration values."""
        config = WorkflowEngineConfig()
        
        assert config.max_concurrent_nodes == 10
        assert config.default_timeout_seconds == 300.0
        assert config.retry_failed_nodes is True
        assert config.max_retries == 3
        assert config.continue_on_error is False
        assert config.enable_caching is True

    @pytest.mark.unit
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

    @pytest.mark.unit
    def test_execution_event_creation(self):
        """Test creating an execution event."""
        from datetime import datetime
        
        event = ExecutionEvent(
            event_type="node_started",
            workflow_id="wf-1",
            execution_id="exec-1",
            node_id="node-1",
            data={"key": "value"},
        )
        
        assert event.event_type == "node_started"
        assert event.workflow_id == "wf-1"
        assert event.execution_id == "exec-1"
        assert event.node_id == "node-1"
        assert event.data == {"key": "value"}
        assert isinstance(event.timestamp, datetime)

    @pytest.mark.unit
    def test_execution_event_to_dict(self):
        """Test converting event to dictionary."""
        event = ExecutionEvent(
            event_type="workflow_started",
            workflow_id="wf-1",
            execution_id="exec-1",
            data={"name": "Test"},
        )
        
        result = event.to_dict()
        
        assert result["event_type"] == "workflow_started"
        assert result["workflow_id"] == "wf-1"
        assert result["execution_id"] == "exec-1"
        assert result["node_id"] is None
        assert result["data"] == {"name": "Test"}
        assert "timestamp" in result


class TestWorkflowEngineInit:
    """Tests for WorkflowEngine initialization."""

    @pytest.mark.unit
    def test_engine_creation_default_config(self):
        """Test creating engine with default config."""
        engine = WorkflowEngine()
        
        assert engine.config is not None
        assert engine.state_store is not None
        assert engine._running_executions == set()
        assert engine._cancellation_tokens == {}
        assert engine._event_handlers == []

    @pytest.mark.unit
    def test_engine_creation_custom_config(self):
        """Test creating engine with custom config."""
        config = WorkflowEngineConfig(max_concurrent_nodes=5)
        engine = WorkflowEngine(config=config)
        
        assert engine.config.max_concurrent_nodes == 5


class TestWorkflowEngineEventHandlers:
    """Tests for event handler management."""

    @pytest.mark.unit
    def test_add_event_handler(self):
        """Test adding an event handler."""
        engine = WorkflowEngine()
        
        handler = MagicMock()
        engine.add_event_handler(handler)
        
        assert handler in engine._event_handlers

    @pytest.mark.unit
    def test_remove_event_handler(self):
        """Test removing an event handler."""
        engine = WorkflowEngine()
        
        handler = MagicMock()
        engine.add_event_handler(handler)
        engine.remove_event_handler(handler)
        
        assert handler not in engine._event_handlers

    @pytest.mark.unit
    def test_emit_event(self):
        """Test emitting an event."""
        engine = WorkflowEngine()
        
        handler = MagicMock()
        engine.add_event_handler(handler)
        
        event = ExecutionEvent(
            event_type="test",
            workflow_id="wf-1",
            execution_id="exec-1",
        )
        engine._emit_event(event)
        
        handler.assert_called_once_with(event)


class TestWorkflowEngineCancel:
    """Tests for workflow cancellation."""

    @pytest.mark.unit
    def test_cancel_nonexistent_execution(self):
        """Test canceling a non-existent execution."""
        engine = WorkflowEngine()
        
        result = engine.cancel("non-existent")
        
        assert result is False

    @pytest.mark.unit
    def test_cancel_execution(self):
        """Test canceling a running execution."""
        engine = WorkflowEngine()
        
        # Add a fake running execution
        engine._running_executions.add("exec-1")
        cancel_token = asyncio.Event()
        engine._cancellation_tokens["exec-1"] = cancel_token
        
        result = engine.cancel("exec-1")
        
        assert result is True
        assert cancel_token.is_set()


class TestWorkflowEnginePrepareExecution:
    """Tests for _prepare_execution method."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_prepare_execution_valid_workflow(self):
        """Test preparing execution with valid workflow."""
        engine = WorkflowEngine()
        
        # Create a valid workflow
        workflow = WorkflowGraph()
        node = WorkflowNode(node_type="test_node")
        workflow.add_node(node)
        
        state = await engine._prepare_execution(workflow, {"var": "value"})
        
        assert state.workflow_id == workflow.id
        assert state.variables == {"var": "value"}
        assert len(state.node_states) == 1
        assert state.status == ExecutionStatus.PENDING


class TestWorkflowEngineExecuteNode:
    """Tests for _execute_node method."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_node_not_found(self):
        """Test executing a node that doesn't exist."""
        engine = WorkflowEngine()
        workflow = WorkflowGraph()
        state = WorkflowState(workflow_id="wf-1")
        
        result = await engine._execute_node(workflow, state, "non-existent")
        
        assert result == ("non-existent", False)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_node_disabled(self):
        """Test executing a disabled node."""
        engine = WorkflowEngine()
        
        # Create workflow with disabled node
        workflow = WorkflowGraph()
        node = WorkflowNode(node_type="test", disabled=True)
        workflow.add_node(node)
        
        state = WorkflowState(workflow_id=workflow.id)
        state.initialize_nodes([node.id])
        
        result = await engine._execute_node(workflow, state, node.id)
        
        assert result == (node.id, True)
        assert state.node_states[node.id].status == ExecutionStatus.SKIPPED

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_node_unregistered_type(self):
        """Test executing a node with unregistered type."""
        engine = WorkflowEngine()
        
        # Create workflow with node of unregistered type
        workflow = WorkflowGraph()
        node = WorkflowNode(node_type="non_existent_node_type")
        workflow.add_node(node)
        
        state = WorkflowState(workflow_id=workflow.id)
        state.initialize_nodes([node.id])
        
        result = await engine._execute_node(workflow, state, node.id)
        
        assert result == (node.id, False)
        assert state.node_states[node.id].status == ExecutionStatus.FAILED


class TestWorkflowEngineExecuteLayer:
    """Tests for _execute_layer method."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_layer_with_cancellation(self):
        """Test executing layer with cancellation token set."""
        engine = WorkflowEngine()
        workflow = WorkflowGraph()
        state = WorkflowState(workflow_id=workflow.id)
        
        # Create cancellation token that's already set
        cancel_token = asyncio.Event()
        cancel_token.set()
        
        result = await engine._execute_layer(
            workflow, state, ["node-1", "node-2"], cancel_token
        )
        
        assert result["node-1"] is False
        assert result["node-2"] is False


class TestWorkflowEngineGetState:
    """Tests for get_state method."""

    @pytest.mark.unit
    def test_get_state_exists(self):
        """Test getting an existing state."""
        engine = WorkflowEngine()
        state = WorkflowState(workflow_id="wf-1", execution_id="exec-1")
        engine.state_store.save(state)
        
        result = engine.get_state("exec-1")
        
        assert result is not None
        assert result.execution_id == "exec-1"

    @pytest.mark.unit
    def test_get_state_not_exists(self):
        """Test getting a non-existing state."""
        engine = WorkflowEngine()
        
        result = engine.get_state("non-existent")
        
        assert result is None
