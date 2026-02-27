"""
Workflow Engine Module

This module provides the core workflow execution engine that orchestrates
node execution, handles data flow, and manages execution state.
"""

import asyncio
import logging
import traceback
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, AsyncGenerator
import uuid

from opencode.workflow.graph import WorkflowGraph, WorkflowNode, WorkflowEdge
from opencode.workflow.node import (
    BaseNode,
    ExecutionContext,
    ExecutionResult,
    NodeExecutionError,
    NodeValidationError,
)
from opencode.workflow.state import (
    WorkflowState,
    NodeExecutionState,
    ExecutionStatus,
    WorkflowStateStore,
)
from opencode.workflow.registry import NodeRegistry

logger = logging.getLogger(__name__)


class WorkflowEngineConfig:
    """Configuration for the workflow engine."""
    
    def __init__(
        self,
        max_concurrent_nodes: int = 10,
        default_timeout_seconds: float = 300.0,
        retry_failed_nodes: bool = True,
        max_retries: int = 3,
        continue_on_error: bool = False,
        enable_caching: bool = True,
    ):
        self.max_concurrent_nodes = max_concurrent_nodes
        self.default_timeout_seconds = default_timeout_seconds
        self.retry_failed_nodes = retry_failed_nodes
        self.max_retries = max_retries
        self.continue_on_error = continue_on_error
        self.enable_caching = enable_caching


class ExecutionEvent:
    """Event emitted during workflow execution."""
    
    def __init__(
        self,
        event_type: str,
        workflow_id: str,
        execution_id: str,
        node_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ):
        self.event_type = event_type
        self.workflow_id = workflow_id
        self.execution_id = execution_id
        self.node_id = node_id
        self.data = data or {}
        self.timestamp = timestamp or datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "workflow_id": self.workflow_id,
            "execution_id": self.execution_id,
            "node_id": self.node_id,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        }


class WorkflowEngine:
    """
    Core workflow execution engine.
    
    The engine is responsible for:
    - Loading and validating workflows
    - Determining execution order (topological sort)
    - Executing nodes in parallel where possible
    - Managing execution state
    - Handling errors and retries
    - Emitting events for real-time updates
    
    Example:
        engine = WorkflowEngine()
        
        # Execute a workflow
        state = await engine.execute(workflow_graph)
        
        # Or stream events
        async for event in engine.execute_stream(workflow_graph):
            print(event)
    """
    
    def __init__(
        self,
        config: Optional[WorkflowEngineConfig] = None,
        state_store: Optional[WorkflowStateStore] = None,
    ):
        self.config = config or WorkflowEngineConfig()
        self.state_store = state_store or WorkflowStateStore()
        self._event_handlers: List[Callable[[ExecutionEvent], None]] = []
        self._running_executions: Set[str] = set()
        self._cancellation_tokens: Dict[str, asyncio.Event] = {}
    
    def add_event_handler(self, handler: Callable[[ExecutionEvent], None]) -> None:
        """
        Add a handler for execution events.
        
        Args:
            handler: Function to call for each event
        """
        self._event_handlers.append(handler)
    
    def remove_event_handler(self, handler: Callable[[ExecutionEvent], None]) -> None:
        """Remove an event handler."""
        if handler in self._event_handlers:
            self._event_handlers.remove(handler)
    
    def _emit_event(self, event: ExecutionEvent) -> None:
        """Emit an event to all registered handlers."""
        for handler in self._event_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.warning(f"Event handler error: {e}")
    
    async def execute(
        self,
        workflow: WorkflowGraph,
        variables: Optional[Dict[str, Any]] = None,
        execution_id: Optional[str] = None,
    ) -> WorkflowState:
        """
        Execute a workflow and return the final state.
        
        Args:
            workflow: The workflow graph to execute
            variables: Optional workflow variables
            execution_id: Optional execution ID (generated if not provided)
            
        Returns:
            The final workflow state
        """
        state = await self._prepare_execution(workflow, variables, execution_id)
        
        async for _ in self._execute_workflow(workflow, state):
            pass  # Consume all events
        
        return state
    
    async def execute_stream(
        self,
        workflow: WorkflowGraph,
        variables: Optional[Dict[str, Any]] = None,
        execution_id: Optional[str] = None,
    ) -> AsyncGenerator[ExecutionEvent, None]:
        """
        Execute a workflow and yield events.
        
        Args:
            workflow: The workflow graph to execute
            variables: Optional workflow variables
            execution_id: Optional execution ID
            
        Yields:
            ExecutionEvent objects as the workflow progresses
        """
        state = await self._prepare_execution(workflow, variables, execution_id)
        
        async for event in self._execute_workflow(workflow, state):
            yield event
    
    async def _prepare_execution(
        self,
        workflow: WorkflowGraph,
        variables: Optional[Dict[str, Any]] = None,
        execution_id: Optional[str] = None,
    ) -> WorkflowState:
        """Prepare for workflow execution."""
        # Validate workflow
        errors = workflow.validate_graph()
        if errors:
            raise ValueError(f"Invalid workflow: {errors}")
        
        # Create execution state
        state = WorkflowState(
            workflow_id=workflow.id,
            execution_id=execution_id or str(uuid.uuid4()),
            variables={**workflow.variables, **(variables or {})},
        )
        
        # Initialize node states
        state.initialize_nodes(list(workflow.nodes.keys()))
        
        # Get execution order
        execution_order = workflow.get_execution_order()
        state.total_layers = len(execution_order)
        
        # Store state
        self.state_store.save(state)
        
        return state
    
    async def _execute_workflow(
        self,
        workflow: WorkflowGraph,
        state: WorkflowState,
    ) -> AsyncGenerator[ExecutionEvent, None]:
        """Internal workflow execution logic."""
        execution_id = state.execution_id
        self._running_executions.add(execution_id)
        
        # Create cancellation token
        cancel_token = asyncio.Event()
        self._cancellation_tokens[execution_id] = cancel_token
        
        try:
            # Emit start event
            start_event = ExecutionEvent(
                event_type="workflow_started",
                workflow_id=workflow.id,
                execution_id=execution_id,
                data={"name": workflow.metadata.name},
            )
            self._emit_event(start_event)
            yield start_event
            
            state.start_execution()
            
            # Get execution order
            execution_order = workflow.get_execution_order()
            
            # Execute layer by layer
            for layer_index, layer in enumerate(execution_order):
                if cancel_token.is_set():
                    state.cancel_execution()
                    break
                
                state.current_layer = layer_index
                
                # Emit layer start event
                layer_event = ExecutionEvent(
                    event_type="layer_started",
                    workflow_id=workflow.id,
                    execution_id=execution_id,
                    data={"layer": layer_index, "nodes": layer},
                )
                self._emit_event(layer_event)
                yield layer_event
                
                # Execute nodes in this layer (potentially in parallel)
                layer_results = await self._execute_layer(
                    workflow, state, layer, cancel_token
                )
                
                # Check for failures
                failed_nodes = [nid for nid, success in layer_results.items() if not success]
                if failed_nodes and not self.config.continue_on_error:
                    state.fail_execution(f"Nodes failed: {failed_nodes}")
                    break
                
                # Emit layer complete event
                complete_event = ExecutionEvent(
                    event_type="layer_completed",
                    workflow_id=workflow.id,
                    execution_id=execution_id,
                    data={"layer": layer_index, "results": layer_results},
                )
                self._emit_event(complete_event)
                yield complete_event
            
            # Mark execution complete
            if state.status == ExecutionStatus.RUNNING:
                state.complete_execution()
            
            # Emit completion event
            end_event = ExecutionEvent(
                event_type="workflow_completed" if state.is_successful() else "workflow_failed",
                workflow_id=workflow.id,
                execution_id=execution_id,
                data={
                    "status": state.status.value,
                    "duration_ms": state.get_duration_ms(),
                    "error": state.error,
                },
            )
            self._emit_event(end_event)
            yield end_event
            
        except Exception as e:
            logger.exception(f"Workflow execution error: {e}")
            state.fail_execution(str(e))
            
            error_event = ExecutionEvent(
                event_type="workflow_error",
                workflow_id=workflow.id,
                execution_id=execution_id,
                data={"error": str(e), "traceback": traceback.format_exc()},
            )
            self._emit_event(error_event)
            yield error_event
            
        finally:
            self._running_executions.discard(execution_id)
            self._cancellation_tokens.pop(execution_id, None)
            self.state_store.save(state)
    
    async def _execute_layer(
        self,
        workflow: WorkflowGraph,
        state: WorkflowState,
        layer: List[str],
        cancel_token: asyncio.Event,
    ) -> Dict[str, bool]:
        """
        Execute a layer of nodes (potentially in parallel).
        
        Args:
            workflow: The workflow graph
            state: Current execution state
            layer: List of node IDs in this layer
            cancel_token: Cancellation token
            
        Returns:
            Dictionary mapping node IDs to success status
        """
        semaphore = asyncio.Semaphore(self.config.max_concurrent_nodes)
        
        async def execute_with_semaphore(node_id: str) -> tuple[str, bool]:
            async with semaphore:
                if cancel_token.is_set():
                    return node_id, False
                return await self._execute_node(workflow, state, node_id)
        
        # Execute all nodes in the layer concurrently
        tasks = [execute_with_semaphore(node_id) for node_id in layer]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        layer_results = {}
        for i, result in enumerate(results):
            node_id = layer[i]
            if isinstance(result, Exception):
                logger.error(f"Node {node_id} raised exception: {result}")
                layer_results[node_id] = False
            elif isinstance(result, tuple):
                layer_results[node_id] = result[1]
            else:
                layer_results[node_id] = False
        
        return layer_results
    
    async def _execute_node(
        self,
        workflow: WorkflowGraph,
        state: WorkflowState,
        node_id: str,
    ) -> tuple[str, bool]:
        """
        Execute a single node.
        
        Args:
            workflow: The workflow graph
            state: Current execution state
            node_id: ID of the node to execute
            
        Returns:
            Tuple of (node_id, success)
        """
        workflow_node = workflow.nodes.get(node_id)
        if not workflow_node:
            logger.error(f"Node {node_id} not found in workflow")
            return node_id, False
        
        if workflow_node.disabled:
            state.skip_node(node_id, "Node is disabled")
            return node_id, True
        
        # Get node class from registry
        try:
            node_class = NodeRegistry.get_required(workflow_node.node_type)
        except KeyError as e:
            state.fail_node(node_id, str(e))
            return node_id, False
        
        # Create node instance
        node = node_class(node_id=node_id, config=workflow_node.config)
        
        # Gather inputs from connected nodes
        inputs = await self._gather_inputs(workflow, state, node_id)
        
        # Create execution context
        context = ExecutionContext(
            workflow_id=workflow.id,
            execution_id=state.execution_id,
            node_id=node_id,
            variables=state.variables,
        )
        
        # Validate inputs
        validation_errors = node.validate_inputs(inputs)
        if validation_errors:
            state.fail_node(node_id, f"Validation errors: {validation_errors}")
            return node_id, False
        
        # Emit node start event
        node_start_event = ExecutionEvent(
            event_type="node_started",
            workflow_id=workflow.id,
            execution_id=state.execution_id,
            node_id=node_id,
            data={"node_type": workflow_node.node_type},
        )
        self._emit_event(node_start_event)
        
        # Update state
        node_state = state.start_node(node_id, inputs)
        
        # Get timeout value before try block
        timeout = workflow_node.config.get(
            "timeout_seconds",
            self.config.default_timeout_seconds
        )
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                node.execute(inputs, context),
                timeout=timeout
            )
            
            if result.success:
                state.complete_node(node_id, result.outputs)
                
                # Emit node complete event
                node_complete_event = ExecutionEvent(
                    event_type="node_completed",
                    workflow_id=workflow.id,
                    execution_id=state.execution_id,
                    node_id=node_id,
                    data={"outputs": result.outputs, "duration_ms": result.duration_ms},
                )
                self._emit_event(node_complete_event)
                
                return node_id, True
            else:
                state.fail_node(node_id, result.error or "Unknown error", result.error_traceback)
                
                # Emit node error event
                node_error_event = ExecutionEvent(
                    event_type="node_error",
                    workflow_id=workflow.id,
                    execution_id=state.execution_id,
                    node_id=node_id,
                    data={"error": result.error, "traceback": result.error_traceback},
                )
                self._emit_event(node_error_event)
                
                return node_id, False
                
        except asyncio.TimeoutError:
            error_msg = f"Node execution timed out after {timeout} seconds"
            state.fail_node(node_id, error_msg)
            
            timeout_event = ExecutionEvent(
                event_type="node_timeout",
                workflow_id=workflow.id,
                execution_id=state.execution_id,
                node_id=node_id,
                data={"timeout_seconds": timeout},
            )
            self._emit_event(timeout_event)
            
            return node_id, False
            
        except Exception as e:
            error_msg = str(e)
            tb = traceback.format_exc()
            state.fail_node(node_id, error_msg, tb)
            logger.exception(f"Node {node_id} execution failed: {e}")
            
            error_event = ExecutionEvent(
                event_type="node_error",
                workflow_id=workflow.id,
                execution_id=state.execution_id,
                node_id=node_id,
                data={"error": error_msg, "traceback": tb},
            )
            self._emit_event(error_event)
            
            return node_id, False
    
    async def _gather_inputs(
        self,
        workflow: WorkflowGraph,
        state: WorkflowState,
        node_id: str,
    ) -> Dict[str, Any]:
        """
        Gather inputs for a node from connected upstream nodes.
        
        Args:
            workflow: The workflow graph
            state: Current execution state
            node_id: ID of the target node
            
        Returns:
            Dictionary of input values keyed by port name
        """
        inputs: Dict[str, Any] = {}
        
        # Get incoming edges
        incoming_edges = workflow.get_incoming_edges(node_id)
        
        for edge in incoming_edges:
            if edge.disabled:
                continue
            
            # Get output from source node
            source_state = state.get_node_state(edge.source_node_id)
            if source_state and source_state.status == ExecutionStatus.COMPLETED:
                output_value = source_state.outputs.get(edge.source_port)
                inputs[edge.target_port] = output_value
        
        return inputs
    
    def cancel(self, execution_id: str) -> bool:
        """
        Request cancellation of a running execution.
        
        Args:
            execution_id: ID of the execution to cancel
            
        Returns:
            True if cancellation was requested, False if execution not found
        """
        if execution_id in self._cancellation_tokens:
            self._cancellation_tokens[execution_id].set()
            return True
        return False
    
    def get_state(self, execution_id: str) -> Optional[WorkflowState]:
        """Get the state of an execution."""
        return self.state_store.get(execution_id)
    
    def is_running(self, execution_id: str) -> bool:
        """Check if an execution is currently running."""
        return execution_id in self._running_executions


class WorkflowEngineError(Exception):
    """Raised when there's an error in the workflow engine."""
    pass