"""
Extended tests for workflow state module.
"""

import pytest
from datetime import datetime
from opencode.workflow.state import (
    ExecutionStatus,
    NodeExecutionState,
    WorkflowState,
    WorkflowStateStore,
)


class TestNodeExecutionStateExtended:
    """Extended tests for NodeExecutionState."""

    @pytest.mark.unit
    def test_node_execution_state_defaults(self):
        """Test NodeExecutionState default values."""
        state = NodeExecutionState(node_id="node-1")
        
        assert state.node_id == "node-1"
        assert state.status == ExecutionStatus.PENDING
        assert state.started_at is None
        assert state.completed_at is None
        assert state.inputs == {}
        assert state.outputs == {}
        assert state.error is None
        assert state.error_traceback is None
        assert state.duration_ms is None
        assert state.attempts == 0
        assert state.max_retries == 3

    @pytest.mark.unit
    def test_start(self):
        """Test start method."""
        state = NodeExecutionState(node_id="node-1")
        state.start()
        
        assert state.status == ExecutionStatus.RUNNING
        assert state.started_at is not None

    @pytest.mark.unit
    def test_complete(self):
        """Test complete method."""
        state = NodeExecutionState(node_id="node-1")
        state.start()
        state.complete({"result": "success"})
        
        assert state.status == ExecutionStatus.COMPLETED
        assert state.outputs == {"result": "success"}
        assert state.completed_at is not None
        assert state.duration_ms is not None

    @pytest.mark.unit
    def test_complete_without_start(self):
        """Test complete method without start."""
        state = NodeExecutionState(node_id="node-1")
        state.complete({"result": "success"})
        
        assert state.status == ExecutionStatus.COMPLETED
        assert state.duration_ms is None  # No start time

    @pytest.mark.unit
    def test_fail(self):
        """Test fail method."""
        state = NodeExecutionState(node_id="node-1")
        state.start()
        state.fail("Something went wrong", "Traceback here")
        
        assert state.status == ExecutionStatus.FAILED
        assert state.error == "Something went wrong"
        assert state.error_traceback == "Traceback here"
        assert state.completed_at is not None
        assert state.duration_ms is not None

    @pytest.mark.unit
    def test_fail_without_start(self):
        """Test fail method without start."""
        state = NodeExecutionState(node_id="node-1")
        state.fail("Error")
        
        assert state.status == ExecutionStatus.FAILED
        assert state.duration_ms is None

    @pytest.mark.unit
    def test_skip(self):
        """Test skip method."""
        state = NodeExecutionState(node_id="node-1")
        state.skip("Not needed")
        
        assert state.status == ExecutionStatus.SKIPPED
        assert state.completed_at is not None

    @pytest.mark.unit
    def test_can_retry(self):
        """Test can_retry method."""
        state = NodeExecutionState(node_id="node-1", max_retries=3)
        
        # Not failed yet
        assert not state.can_retry()
        
        # Failed but under retry limit
        state.fail("Error")
        assert state.can_retry()
        
        # Exhaust retries
        state.attempts = 3
        assert not state.can_retry()

    @pytest.mark.unit
    def test_increment_attempt(self):
        """Test increment_attempt method."""
        state = NodeExecutionState(node_id="node-1")
        
        assert state.attempts == 0
        state.increment_attempt()
        assert state.attempts == 1
        state.increment_attempt()
        assert state.attempts == 2


class TestWorkflowStateExtended:
    """Extended tests for WorkflowState."""

    @pytest.mark.unit
    def test_workflow_state_defaults(self):
        """Test WorkflowState default values."""
        state = WorkflowState(workflow_id="wf-1")
        
        assert state.workflow_id == "wf-1"
        assert state.execution_id is not None
        assert state.status == ExecutionStatus.PENDING
        assert state.started_at is None
        assert state.completed_at is None
        assert state.node_states == {}
        assert state.variables == {}
        assert state.current_layer == 0
        assert state.total_layers == 0
        assert state.error is None
        assert state.parent_execution_id is None
        assert state.metadata == {}

    @pytest.mark.unit
    def test_initialize_nodes(self):
        """Test initialize_nodes method."""
        state = WorkflowState(workflow_id="wf-1")
        state.initialize_nodes(["node-1", "node-2", "node-3"])
        
        assert len(state.node_states) == 3
        assert "node-1" in state.node_states
        assert state.node_states["node-1"].node_id == "node-1"
        assert state.node_states["node-1"].status == ExecutionStatus.PENDING

    @pytest.mark.unit
    def test_initialize_nodes_idempotent(self):
        """Test initialize_nodes is idempotent."""
        state = WorkflowState(workflow_id="wf-1")
        state.initialize_nodes(["node-1"])
        state.node_states["node-1"].status = ExecutionStatus.RUNNING
        
        # Re-initialize should not overwrite existing state
        state.initialize_nodes(["node-1"])
        assert state.node_states["node-1"].status == ExecutionStatus.RUNNING

    @pytest.mark.unit
    def test_get_node_state(self):
        """Test get_node_state method."""
        state = WorkflowState(workflow_id="wf-1")
        state.initialize_nodes(["node-1"])
        
        result = state.get_node_state("node-1")
        assert result is not None
        assert result.node_id == "node-1"
        
        result = state.get_node_state("non-existent")
        assert result is None

    @pytest.mark.unit
    def test_start_node(self):
        """Test start_node method."""
        state = WorkflowState(workflow_id="wf-1")
        
        node_state = state.start_node("node-1", {"input": "value"})
        
        assert node_state.status == ExecutionStatus.RUNNING
        assert node_state.inputs == {"input": "value"}
        assert node_state.started_at is not None

    @pytest.mark.unit
    def test_complete_node(self):
        """Test complete_node method."""
        state = WorkflowState(workflow_id="wf-1")
        state.start_node("node-1")
        
        node_state = state.complete_node("node-1", {"output": "result"})
        
        assert node_state.status == ExecutionStatus.COMPLETED
        assert node_state.outputs == {"output": "result"}

    @pytest.mark.unit
    def test_fail_node(self):
        """Test fail_node method."""
        state = WorkflowState(workflow_id="wf-1")
        state.start_node("node-1")
        
        node_state = state.fail_node("node-1", "Error occurred", "Traceback")
        
        assert node_state.status == ExecutionStatus.FAILED
        assert node_state.error == "Error occurred"
        assert node_state.error_traceback == "Traceback"

    @pytest.mark.unit
    def test_skip_node(self):
        """Test skip_node method."""
        state = WorkflowState(workflow_id="wf-1")
        state.initialize_nodes(["node-1"])
        
        node_state = state.skip_node("node-1", "Not needed")
        
        assert node_state.status == ExecutionStatus.SKIPPED

    @pytest.mark.unit
    def test_start_execution(self):
        """Test start_execution method."""
        state = WorkflowState(workflow_id="wf-1")
        state.start_execution()
        
        assert state.status == ExecutionStatus.RUNNING
        assert state.started_at is not None

    @pytest.mark.unit
    def test_complete_execution(self):
        """Test complete_execution method."""
        state = WorkflowState(workflow_id="wf-1")
        state.start_execution()
        state.complete_execution()
        
        assert state.status == ExecutionStatus.COMPLETED
        assert state.completed_at is not None

    @pytest.mark.unit
    def test_fail_execution(self):
        """Test fail_execution method."""
        state = WorkflowState(workflow_id="wf-1")
        state.start_execution()
        state.fail_execution("Workflow failed")
        
        assert state.status == ExecutionStatus.FAILED
        assert state.error == "Workflow failed"
        assert state.completed_at is not None

    @pytest.mark.unit
    def test_cancel_execution(self):
        """Test cancel_execution method."""
        state = WorkflowState(workflow_id="wf-1")
        state.start_execution()
        state.cancel_execution()
        
        assert state.status == ExecutionStatus.CANCELLED
        assert state.completed_at is not None

    @pytest.mark.unit
    def test_pause_execution(self):
        """Test pause_execution method."""
        state = WorkflowState(workflow_id="wf-1")
        state.start_execution()
        state.pause_execution()
        
        assert state.status == ExecutionStatus.PAUSED

    @pytest.mark.unit
    def test_resume_execution(self):
        """Test resume_execution method."""
        state = WorkflowState(workflow_id="wf-1")
        state.start_execution()
        state.pause_execution()
        state.resume_execution()
        
        assert state.status == ExecutionStatus.RUNNING

    @pytest.mark.unit
    def test_is_complete(self):
        """Test is_complete method."""
        state = WorkflowState(workflow_id="wf-1")
        
        assert not state.is_complete()
        
        state.status = ExecutionStatus.COMPLETED
        assert state.is_complete()
        
        state.status = ExecutionStatus.FAILED
        assert state.is_complete()
        
        state.status = ExecutionStatus.CANCELLED
        assert state.is_complete()
        
        state.status = ExecutionStatus.RUNNING
        assert not state.is_complete()

    @pytest.mark.unit
    def test_is_successful(self):
        """Test is_successful method."""
        state = WorkflowState(workflow_id="wf-1")
        
        assert not state.is_successful()
        
        state.status = ExecutionStatus.COMPLETED
        assert state.is_successful()
        
        state.status = ExecutionStatus.FAILED
        assert not state.is_successful()

    @pytest.mark.unit
    def test_get_progress(self):
        """Test get_progress method."""
        state = WorkflowState(workflow_id="wf-1")
        state.initialize_nodes(["node-1", "node-2", "node-3"])
        
        state.start_node("node-1")
        state.complete_node("node-1", {})
        state.start_node("node-2")
        state.fail_node("node-2", "Error")
        
        progress = state.get_progress()
        
        assert progress["completed"] == 1
        assert progress["failed"] == 1
        assert progress["pending"] == 1

    @pytest.mark.unit
    def test_get_completed_outputs(self):
        """Test get_completed_outputs method."""
        state = WorkflowState(workflow_id="wf-1")
        state.initialize_nodes(["node-1", "node-2"])
        
        state.start_node("node-1")
        state.complete_node("node-1", {"result": "success"})
        state.start_node("node-2")
        
        outputs = state.get_completed_outputs()
        
        assert "node-1" in outputs
        assert outputs["node-1"] == {"result": "success"}
        assert "node-2" not in outputs

    @pytest.mark.unit
    def test_get_failed_nodes(self):
        """Test get_failed_nodes method."""
        state = WorkflowState(workflow_id="wf-1")
        state.initialize_nodes(["node-1", "node-2"])
        
        state.start_node("node-1")
        state.fail_node("node-1", "Error")
        
        failed = state.get_failed_nodes()
        
        assert failed == ["node-1"]

    @pytest.mark.unit
    def test_get_pending_nodes(self):
        """Test get_pending_nodes method."""
        state = WorkflowState(workflow_id="wf-1")
        state.initialize_nodes(["node-1", "node-2"])
        
        state.start_node("node-1")
        
        pending = state.get_pending_nodes()
        
        assert pending == ["node-2"]

    @pytest.mark.unit
    def test_get_running_nodes(self):
        """Test get_running_nodes method."""
        state = WorkflowState(workflow_id="wf-1")
        state.initialize_nodes(["node-1", "node-2"])
        
        state.start_node("node-1")
        
        running = state.get_running_nodes()
        
        assert running == ["node-1"]

    @pytest.mark.unit
    def test_get_duration_ms(self):
        """Test get_duration_ms method."""
        state = WorkflowState(workflow_id="wf-1")
        
        # No times set
        assert state.get_duration_ms() is None
        
        # Only started
        state.start_execution()
        assert state.get_duration_ms() is None
        
        # Completed
        state.complete_execution()
        assert state.get_duration_ms() is not None
        assert state.get_duration_ms() >= 0

    @pytest.mark.unit
    def test_to_dict(self):
        """Test to_dict method."""
        state = WorkflowState(
            workflow_id="wf-1",
            execution_id="exec-1",
            status=ExecutionStatus.RUNNING,
        )
        
        data = state.to_dict()
        
        assert data["workflow_id"] == "wf-1"
        assert data["execution_id"] == "exec-1"
        assert data["status"] == "running"

    @pytest.mark.unit
    def test_from_dict(self):
        """Test from_dict method."""
        data = {
            "workflow_id": "wf-1",
            "execution_id": "exec-1",
            "status": "running",
            "node_states": {},
            "variables": {"key": "value"},
        }
        
        state = WorkflowState.from_dict(data)
        
        assert state.workflow_id == "wf-1"
        assert state.execution_id == "exec-1"
        assert state.status == ExecutionStatus.RUNNING
        assert state.variables == {"key": "value"}


class TestWorkflowStateStore:
    """Tests for WorkflowStateStore."""

    @pytest.mark.unit
    def test_save_and_get(self):
        """Test save and get methods."""
        store = WorkflowStateStore()
        state = WorkflowState(workflow_id="wf-1", execution_id="exec-1")
        
        store.save(state)
        
        result = store.get("exec-1")
        assert result is not None
        assert result.workflow_id == "wf-1"
        
        result = store.get("non-existent")
        assert result is None

    @pytest.mark.unit
    def test_get_by_workflow(self):
        """Test get_by_workflow method."""
        store = WorkflowStateStore()
        state1 = WorkflowState(workflow_id="wf-1", execution_id="exec-1")
        state2 = WorkflowState(workflow_id="wf-1", execution_id="exec-2")
        state3 = WorkflowState(workflow_id="wf-2", execution_id="exec-3")
        
        store.save(state1)
        store.save(state2)
        store.save(state3)
        
        results = store.get_by_workflow("wf-1")
        
        assert len(results) == 2
        assert all(r.workflow_id == "wf-1" for r in results)

    @pytest.mark.unit
    def test_delete(self):
        """Test delete method."""
        store = WorkflowStateStore()
        state = WorkflowState(workflow_id="wf-1", execution_id="exec-1")
        store.save(state)
        
        result = store.delete("exec-1")
        assert result is True
        assert store.get("exec-1") is None
        
        result = store.delete("non-existent")
        assert result is False

    @pytest.mark.unit
    def test_list_all(self):
        """Test list_all method."""
        store = WorkflowStateStore()
        state1 = WorkflowState(workflow_id="wf-1", execution_id="exec-1")
        state2 = WorkflowState(workflow_id="wf-2", execution_id="exec-2")
        
        store.save(state1)
        store.save(state2)
        
        results = store.list_all()
        
        assert len(results) == 2

    @pytest.mark.unit
    def test_clear(self):
        """Test clear method."""
        store = WorkflowStateStore()
        state = WorkflowState(workflow_id="wf-1", execution_id="exec-1")
        store.save(state)
        
        store.clear()
        
        assert store.list_all() == []
