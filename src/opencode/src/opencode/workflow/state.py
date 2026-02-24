"""
Workflow State Module

This module provides state management for workflow execution,
including execution status tracking and history.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class ExecutionStatus(str, Enum):
    """Status of a workflow or node execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    SKIPPED = "skipped"


class NodeExecutionState(BaseModel):
    """Execution state for a single node."""
    node_id: str = Field(..., description="ID of the node")
    status: ExecutionStatus = Field(default=ExecutionStatus.PENDING, description="Current status")
    started_at: Optional[datetime] = Field(default=None, description="When execution started")
    completed_at: Optional[datetime] = Field(default=None, description="When execution completed")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Input values")
    outputs: Dict[str, Any] = Field(default_factory=dict, description="Output values")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    error_traceback: Optional[str] = Field(default=None, description="Full traceback if available")
    duration_ms: Optional[float] = Field(default=None, description="Execution duration in ms")
    attempts: int = Field(default=0, description="Number of execution attempts")
    max_retries: int = Field(default=3, description="Maximum retry attempts")

    def start(self) -> None:
        """Mark execution as started."""
        self.status = ExecutionStatus.RUNNING
        self.started_at = datetime.utcnow()

    def complete(self, outputs: Dict[str, Any]) -> None:
        """Mark execution as completed successfully."""
        self.status = ExecutionStatus.COMPLETED
        self.outputs = outputs
        self.completed_at = datetime.utcnow()
        if self.started_at:
            self.duration_ms = (self.completed_at - self.started_at).total_seconds() * 1000

    def fail(self, error: str, traceback: Optional[str] = None) -> None:
        """Mark execution as failed."""
        self.status = ExecutionStatus.FAILED
        self.error = error
        self.error_traceback = traceback
        self.completed_at = datetime.utcnow()
        if self.started_at:
            self.duration_ms = (self.completed_at - self.started_at).total_seconds() * 1000

    def skip(self, reason: str = "") -> None:
        """Mark execution as skipped."""
        self.status = ExecutionStatus.SKIPPED
        self.completed_at = datetime.utcnow()

    def can_retry(self) -> bool:
        """Check if the node can be retried."""
        return self.attempts < self.max_retries and self.status == ExecutionStatus.FAILED

    def increment_attempt(self) -> None:
        """Increment the attempt counter."""
        self.attempts += 1


class WorkflowState(BaseModel):
    """
    Complete state of a workflow execution.
    
    Tracks the execution status of all nodes and provides
    methods for state management and querying.
    """
    workflow_id: str = Field(..., description="ID of the workflow")
    execution_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique ID for this execution run"
    )
    status: ExecutionStatus = Field(default=ExecutionStatus.PENDING, description="Overall status")
    started_at: Optional[datetime] = Field(default=None, description="When execution started")
    completed_at: Optional[datetime] = Field(default=None, description="When execution completed")
    node_states: Dict[str, NodeExecutionState] = Field(
        default_factory=dict,
        description="Execution states keyed by node ID"
    )
    variables: Dict[str, Any] = Field(default_factory=dict, description="Workflow variables")
    current_layer: int = Field(default=0, description="Current execution layer")
    total_layers: int = Field(default=0, description="Total number of layers")
    error: Optional[str] = Field(default=None, description="Global error message")
    parent_execution_id: Optional[str] = Field(default=None, description="Parent execution for nested workflows")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        arbitrary_types_allowed = True

    def initialize_nodes(self, node_ids: List[str]) -> None:
        """
        Initialize execution states for all nodes.
        
        Args:
            node_ids: List of node IDs to initialize
        """
        for node_id in node_ids:
            if node_id not in self.node_states:
                self.node_states[node_id] = NodeExecutionState(node_id=node_id)

    def get_node_state(self, node_id: str) -> Optional[NodeExecutionState]:
        """Get the execution state for a node."""
        return self.node_states.get(node_id)

    def start_node(self, node_id: str, inputs: Optional[Dict[str, Any]] = None) -> NodeExecutionState:
        """
        Mark a node as started.
        
        Args:
            node_id: ID of the node
            inputs: Optional input values
            
        Returns:
            The node's execution state
        """
        state = self.node_states.get(node_id)
        if not state:
            state = NodeExecutionState(node_id=node_id)
            self.node_states[node_id] = state
        
        if inputs:
            state.inputs = inputs
        state.start()
        return state

    def complete_node(self, node_id: str, outputs: Dict[str, Any]) -> NodeExecutionState:
        """
        Mark a node as completed.
        
        Args:
            node_id: ID of the node
            outputs: Output values from the node
            
        Returns:
            The node's execution state
        """
        state = self.node_states[node_id]
        state.complete(outputs)
        return state

    def fail_node(self, node_id: str, error: str, traceback: Optional[str] = None) -> NodeExecutionState:
        """
        Mark a node as failed.
        
        Args:
            node_id: ID of the node
            error: Error message
            traceback: Optional full traceback
            
        Returns:
            The node's execution state
        """
        state = self.node_states[node_id]
        state.fail(error, traceback)
        return state

    def skip_node(self, node_id: str, reason: str = "") -> NodeExecutionState:
        """
        Mark a node as skipped.
        
        Args:
            node_id: ID of the node
            reason: Optional reason for skipping
            
        Returns:
            The node's execution state
        """
        state = self.node_states[node_id]
        state.skip(reason)
        return state

    def start_execution(self) -> None:
        """Mark the workflow execution as started."""
        self.status = ExecutionStatus.RUNNING
        self.started_at = datetime.utcnow()

    def complete_execution(self) -> None:
        """Mark the workflow execution as completed."""
        self.status = ExecutionStatus.COMPLETED
        self.completed_at = datetime.utcnow()

    def fail_execution(self, error: str) -> None:
        """Mark the workflow execution as failed."""
        self.status = ExecutionStatus.FAILED
        self.error = error
        self.completed_at = datetime.utcnow()

    def cancel_execution(self) -> None:
        """Mark the workflow execution as cancelled."""
        self.status = ExecutionStatus.CANCELLED
        self.completed_at = datetime.utcnow()

    def pause_execution(self) -> None:
        """Mark the workflow execution as paused."""
        self.status = ExecutionStatus.PAUSED

    def resume_execution(self) -> None:
        """Resume a paused execution."""
        self.status = ExecutionStatus.RUNNING

    def is_complete(self) -> bool:
        """Check if the workflow execution is complete."""
        return self.status in (
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.CANCELLED
        )

    def is_successful(self) -> bool:
        """Check if the workflow completed successfully."""
        return self.status == ExecutionStatus.COMPLETED

    def get_progress(self) -> Dict[str, int]:
        """
        Get execution progress statistics.
        
        Returns:
            Dictionary with counts by status
        """
        counts = {status.value: 0 for status in ExecutionStatus}
        for state in self.node_states.values():
            counts[state.status.value] += 1
        return counts

    def get_completed_outputs(self) -> Dict[str, Dict[str, Any]]:
        """
        Get outputs from all completed nodes.
        
        Returns:
            Dictionary mapping node IDs to their outputs
        """
        return {
            node_id: state.outputs
            for node_id, state in self.node_states.items()
            if state.status == ExecutionStatus.COMPLETED
        }

    def get_failed_nodes(self) -> List[str]:
        """Get IDs of all failed nodes."""
        return [
            node_id for node_id, state in self.node_states.items()
            if state.status == ExecutionStatus.FAILED
        ]

    def get_pending_nodes(self) -> List[str]:
        """Get IDs of all pending nodes."""
        return [
            node_id for node_id, state in self.node_states.items()
            if state.status == ExecutionStatus.PENDING
        ]

    def get_running_nodes(self) -> List[str]:
        """Get IDs of all running nodes."""
        return [
            node_id for node_id, state in self.node_states.items()
            if state.status == ExecutionStatus.RUNNING
        ]

    def get_duration_ms(self) -> Optional[float]:
        """Get total execution duration in milliseconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() * 1000
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the state to a dictionary."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowState":
        """Deserialize state from a dictionary."""
        return cls.model_validate(data)


class WorkflowStateStore:
    """
    In-memory store for workflow states.
    
    Provides basic CRUD operations for workflow states.
    In production, this would be backed by a database.
    """
    
    def __init__(self):
        self._states: Dict[str, WorkflowState] = {}
    
    def save(self, state: WorkflowState) -> None:
        """Save a workflow state."""
        self._states[state.execution_id] = state
    
    def get(self, execution_id: str) -> Optional[WorkflowState]:
        """Get a workflow state by execution ID."""
        return self._states.get(execution_id)
    
    def get_by_workflow(self, workflow_id: str) -> List[WorkflowState]:
        """Get all states for a workflow."""
        return [
            state for state in self._states.values()
            if state.workflow_id == workflow_id
        ]
    
    def delete(self, execution_id: str) -> bool:
        """Delete a workflow state."""
        if execution_id in self._states:
            del self._states[execution_id]
            return True
        return False
    
    def list_all(self) -> List[WorkflowState]:
        """List all workflow states."""
        return list(self._states.values())
    
    def clear(self) -> None:
        """Clear all states."""
        self._states.clear()
