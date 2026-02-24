"""
GraphQL Schema for Workflow API

This module defines the GraphQL schema using strawberry-graphql for
workflow management and execution.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, AsyncGenerator
import uuid

import strawberry
from strawberry.types import Info
from strawberry.fastapi import GraphQLRouter
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL

from opencode.workflow.graph import WorkflowGraph, WorkflowNode, WorkflowEdge, WorkflowMetadata
from opencode.workflow.engine import WorkflowEngine, ExecutionEvent
from opencode.workflow.state import WorkflowState, ExecutionStatus
from opencode.workflow.registry import NodeRegistry

logger = logging.getLogger(__name__)

# In-memory storage (would be database in production)
_workflows: Dict[str, WorkflowGraph] = {}
_engine: Optional[WorkflowEngine] = None


def get_engine() -> WorkflowEngine:
    """Get or create the workflow engine."""
    global _engine
    if _engine is None:
        _engine = WorkflowEngine()
    return _engine


# GraphQL Types
@strawberry.type
class NodePortType:
    """GraphQL type for node port."""
    name: str
    data_type: str
    direction: str
    required: bool
    description: str


@strawberry.type
class NodeSchemaType:
    """GraphQL type for node schema."""
    node_type: str
    display_name: str
    description: str
    category: str
    icon: str
    version: str
    
    @strawberry.field
    def inputs(self) -> List[NodePortType]:
        """Get input ports."""
        return [
            NodePortType(
                name=p.name,
                data_type=p.data_type.value if hasattr(p.data_type, 'value') else str(p.data_type),
                direction=p.direction.value if hasattr(p.direction, 'value') else str(p.direction),
                required=p.required,
                description=p.description,
            )
            for p in NodeRegistry.get(self.node_type).get_schema().inputs
        ] if NodeRegistry.get(self.node_type) else []
    
    @strawberry.field
    def outputs(self) -> List[NodePortType]:
        """Get output ports."""
        return [
            NodePortType(
                name=p.name,
                data_type=p.data_type.value if hasattr(p.data_type, 'value') else str(p.data_type),
                direction=p.direction.value if hasattr(p.direction, 'value') else str(p.direction),
                required=p.required,
                description=p.description,
            )
            for p in NodeRegistry.get(self.node_type).get_schema().outputs
        ] if NodeRegistry.get(self.node_type) else []


@strawberry.type
class WorkflowNodeType:
    """GraphQL type for workflow node."""
    id: str
    node_type: str
    position_x: float
    position_y: float
    config: strawberry.scalars.JSON
    label: Optional[str]
    disabled: bool


@strawberry.type
class WorkflowEdgeType:
    """GraphQL type for workflow edge."""
    id: str
    source_node_id: str
    source_port: str
    target_node_id: str
    target_port: str


@strawberry.type
class WorkflowMetadataType:
    """GraphQL type for workflow metadata."""
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    version: str


@strawberry.type
class WorkflowType:
    """GraphQL type for workflow."""
    id: str
    metadata: WorkflowMetadataType
    variables: strawberry.scalars.JSON
    
    @strawberry.field
    def nodes(self) -> List[WorkflowNodeType]:
        """Get workflow nodes."""
        workflow = _workflows.get(self.id)
        if not workflow:
            return []
        return [
            WorkflowNodeType(
                id=node.id,
                node_type=node.node_type,
                position_x=node.position_x,
                position_y=node.position_y,
                config=node.config,
                label=node.label,
                disabled=node.disabled,
            )
            for node in workflow.nodes.values()
        ]
    
    @strawberry.field
    def edges(self) -> List[WorkflowEdgeType]:
        """Get workflow edges."""
        workflow = _workflows.get(self.id)
        if not workflow:
            return []
        return [
            WorkflowEdgeType(
                id=edge.id,
                source_node_id=edge.source_node_id,
                source_port=edge.source_port,
                target_node_id=edge.target_node_id,
                target_port=edge.target_port,
            )
            for edge in workflow.edges
        ]


@strawberry.type
class NodeExecutionStateType:
    """GraphQL type for node execution state."""
    node_id: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error: Optional[str]
    inputs: Optional[strawberry.scalars.JSON]
    outputs: Optional[strawberry.scalars.JSON]


@strawberry.type
class WorkflowExecutionType:
    """GraphQL type for workflow execution state."""
    workflow_id: str
    execution_id: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error: Optional[str]
    variables: strawberry.scalars.JSON
    
    @strawberry.field
    def node_states(self) -> List[NodeExecutionStateType]:
        """Get node execution states."""
        engine = get_engine()
        state = engine.state_store.get(self.execution_id)
        if not state:
            return []
        return [
            NodeExecutionStateType(
                node_id=node_id,
                status=ns.status.value,
                started_at=ns.started_at,
                completed_at=ns.completed_at,
                error=ns.error,
                inputs=ns.inputs,
                outputs=ns.outputs,
            )
            for node_id, ns in state.node_states.items()
        ]


@strawberry.type
class ExecutionEventType:
    """GraphQL type for execution event."""
    event_type: str
    workflow_id: str
    execution_id: str
    node_id: Optional[str]
    data: strawberry.scalars.JSON
    timestamp: datetime


# Input Types
@strawberry.input
class CreateWorkflowInput:
    """Input for creating a workflow."""
    name: str
    description: str = ""
    variables: strawberry.scalars.JSON = strawberry.field(default_factory=lambda: {})


@strawberry.input
class UpdateWorkflowInput:
    """Input for updating a workflow."""
    name: Optional[str] = None
    description: Optional[str] = None
    variables: Optional[strawberry.scalars.JSON] = None


@strawberry.input
class AddNodeInput:
    """Input for adding a node."""
    workflow_id: str
    node_type: str
    position_x: float = 0
    position_y: float = 0
    config: strawberry.scalars.JSON = strawberry.field(default_factory=lambda: {})
    label: Optional[str] = None


@strawberry.input
class AddEdgeInput:
    """Input for adding an edge."""
    workflow_id: str
    source_node_id: str
    source_port: str
    target_node_id: str
    target_port: str


@strawberry.input
class ExecuteWorkflowInput:
    """Input for executing a workflow."""
    workflow_id: str
    variables: strawberry.scalars.JSON = strawberry.field(default_factory=lambda: {})


# Query Type
@strawberry.type
class Query:
    """GraphQL Query type."""
    
    @strawberry.field
    def workflow(self, id: str) -> Optional[WorkflowType]:
        """Get a workflow by ID."""
        workflow = _workflows.get(id)
        if not workflow:
            return None
        return WorkflowType(
            id=workflow.id,
            metadata=WorkflowMetadataType(
                name=workflow.metadata.name,
                description=workflow.metadata.description,
                created_at=workflow.metadata.created_at,
                updated_at=workflow.metadata.updated_at,
                version=workflow.metadata.version,
            ),
            variables=workflow.variables,
        )
    
    @strawberry.field
    def workflows(self) -> List[WorkflowType]:
        """List all workflows."""
        return [
            WorkflowType(
                id=wf.id,
                metadata=WorkflowMetadataType(
                    name=wf.metadata.name,
                    description=wf.metadata.description,
                    created_at=wf.metadata.created_at,
                    updated_at=wf.metadata.updated_at,
                    version=wf.metadata.version,
                ),
                variables=wf.variables,
            )
            for wf in _workflows.values()
        ]
    
    @strawberry.field
    def node_types(self) -> List[NodeSchemaType]:
        """List all available node types."""
        schemas = NodeRegistry.get_all_schemas()
        return [
            NodeSchemaType(
                node_type=name,
                display_name=schema.display_name,
                description=schema.description,
                category=schema.category,
                icon=schema.icon,
                version=schema.version,
            )
            for name, schema in schemas.items()
        ]
    
    @strawberry.field
    def execution(self, execution_id: str) -> Optional[WorkflowExecutionType]:
        """Get execution state by ID."""
        engine = get_engine()
        state = engine.state_store.get(execution_id)
        if not state:
            return None
        return WorkflowExecutionType(
            workflow_id=state.workflow_id,
            execution_id=state.execution_id,
            status=state.status.value,
            started_at=state.started_at,
            completed_at=state.completed_at,
            error=state.error,
            variables=state.variables,
        )


# Mutation Type
@strawberry.type
class Mutation:
    """GraphQL Mutation type."""
    
    @strawberry.mutation
    def create_workflow(self, input: CreateWorkflowInput) -> WorkflowType:
        """Create a new workflow."""
        workflow = WorkflowGraph(
            metadata=WorkflowMetadata(
                name=input.name,
                description=input.description,
            ),
            variables=input.variables,
        )
        _workflows[workflow.id] = workflow
        return WorkflowType(
            id=workflow.id,
            metadata=WorkflowMetadataType(
                name=workflow.metadata.name,
                description=workflow.metadata.description,
                created_at=workflow.metadata.created_at,
                updated_at=workflow.metadata.updated_at,
                version=workflow.metadata.version,
            ),
            variables=workflow.variables,
        )
    
    @strawberry.mutation
    def update_workflow(self, id: str, input: UpdateWorkflowInput) -> Optional[WorkflowType]:
        """Update a workflow."""
        workflow = _workflows.get(id)
        if not workflow:
            return None
        
        if input.name is not None:
            workflow.metadata.name = input.name
        if input.description is not None:
            workflow.metadata.description = input.description
        if input.variables is not None:
            workflow.variables = input.variables
        
        return WorkflowType(
            id=workflow.id,
            metadata=WorkflowMetadataType(
                name=workflow.metadata.name,
                description=workflow.metadata.description,
                created_at=workflow.metadata.created_at,
                updated_at=workflow.metadata.updated_at,
                version=workflow.metadata.version,
            ),
            variables=workflow.variables,
        )
    
    @strawberry.mutation
    def delete_workflow(self, id: str) -> bool:
        """Delete a workflow."""
        if id in _workflows:
            del _workflows[id]
            return True
        return False
    
    @strawberry.mutation
    def add_node(self, input: AddNodeInput) -> Optional[WorkflowNodeType]:
        """Add a node to a workflow."""
        workflow = _workflows.get(input.workflow_id)
        if not workflow:
            return None
        
        node = WorkflowNode(
            node_type=input.node_type,
            position_x=input.position_x,
            position_y=input.position_y,
            config=input.config,
            label=input.label,
        )
        workflow.add_node(node)
        
        return WorkflowNodeType(
            id=node.id,
            node_type=node.node_type,
            position_x=node.position_x,
            position_y=node.position_y,
            config=node.config,
            label=node.label,
            disabled=node.disabled,
        )
    
    @strawberry.mutation
    def remove_node(self, workflow_id: str, node_id: str) -> bool:
        """Remove a node from a workflow."""
        workflow = _workflows.get(workflow_id)
        if not workflow:
            return False
        return workflow.remove_node(node_id)
    
    @strawberry.mutation
    def add_edge(self, input: AddEdgeInput) -> Optional[WorkflowEdgeType]:
        """Add an edge to a workflow."""
        workflow = _workflows.get(input.workflow_id)
        if not workflow:
            return None
        
        edge = WorkflowEdge(
            source_node_id=input.source_node_id,
            source_port=input.source_port,
            target_node_id=input.target_node_id,
            target_port=input.target_port,
        )
        success, error = workflow.add_edge(edge)
        if not success:
            return None
        
        return WorkflowEdgeType(
            id=edge.id,
            source_node_id=edge.source_node_id,
            source_port=edge.source_port,
            target_node_id=edge.target_node_id,
            target_port=edge.target_port,
        )
    
    @strawberry.mutation
    def remove_edge(self, workflow_id: str, edge_id: str) -> bool:
        """Remove an edge from a workflow."""
        workflow = _workflows.get(workflow_id)
        if not workflow:
            return False
        return workflow.remove_edge(edge_id)
    
    @strawberry.mutation
    async def execute_workflow(self, input: ExecuteWorkflowInput) -> Optional[WorkflowExecutionType]:
        """Execute a workflow."""
        workflow = _workflows.get(input.workflow_id)
        if not workflow:
            return None
        
        engine = get_engine()
        state = await engine.execute(workflow, input.variables)
        
        return WorkflowExecutionType(
            workflow_id=state.workflow_id,
            execution_id=state.execution_id,
            status=state.status.value,
            started_at=state.started_at,
            completed_at=state.completed_at,
            error=state.error,
            variables=state.variables,
        )
    
    @strawberry.mutation
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution."""
        engine = get_engine()
        return engine.cancel(execution_id)


# Subscription Type
@strawberry.type
class Subscription:
    """GraphQL Subscription type."""
    
    @strawberry.subscription
    async def workflow_execution(
        self,
        workflow_id: str,
        execution_id: Optional[str] = None,
    ) -> AsyncGenerator[ExecutionEventType, None]:
        """
        Subscribe to workflow execution events.
        
        Args:
            workflow_id: ID of the workflow to subscribe to
            execution_id: Optional specific execution ID to filter
            
        Yields:
            ExecutionEventType objects as events occur
        """
        engine = get_engine()
        queue: asyncio.Queue[ExecutionEvent] = asyncio.Queue()
        
        def event_handler(event: ExecutionEvent) -> None:
            """Handle execution events."""
            if event.workflow_id == workflow_id:
                if execution_id is None or event.execution_id == execution_id:
                    try:
                        asyncio.get_event_loop().call_soon_threadsafe(
                            queue.put_nowait, event
                        )
                    except Exception:
                        pass
        
        engine.add_event_handler(event_handler)
        
        try:
            while True:
                try:
                    # Wait for events with timeout
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield ExecutionEventType(
                        event_type=event.event_type,
                        workflow_id=event.workflow_id,
                        execution_id=event.execution_id,
                        node_id=event.node_id,
                        data=event.data,
                        timestamp=event.timestamp,
                    )
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield ExecutionEventType(
                        event_type="keepalive",
                        workflow_id=workflow_id,
                        execution_id=execution_id or "",
                        node_id=None,
                        data={},
                        timestamp=datetime.utcnow(),
                    )
        finally:
            engine.remove_event_handler(event_handler)


# Create the schema
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
)


def get_graphql_router() -> GraphQLRouter:
    """
    Get the GraphQL router for FastAPI.
    
    Returns:
        GraphQLRouter instance
    """
    return GraphQLRouter(
        schema,
        subscription_protocols=[
            GRAPHQL_TRANSPORT_WS_PROTOCOL,
            GRAPHQL_WS_PROTOCOL,
        ],
    )
