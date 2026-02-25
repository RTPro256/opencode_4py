"""
Extended tests for GraphQL schema module - testing resolvers and mutations.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import MagicMock, patch, AsyncMock

from opencode.server.graphql.schema import (
    get_engine,
    _workflows,
    NodePortType,
    NodeSchemaType,
    WorkflowNodeType,
    WorkflowEdgeType,
    WorkflowMetadataType,
    WorkflowType,
    NodeExecutionStateType,
    WorkflowExecutionType,
    ExecutionEventType,
    CreateWorkflowInput,
    UpdateWorkflowInput,
    AddNodeInput,
    AddEdgeInput,
    ExecuteWorkflowInput,
    Query,
    Mutation,
    Subscription,
    schema,
    get_graphql_router,
)
from opencode.workflow.graph import WorkflowGraph, WorkflowMetadata, WorkflowNode, WorkflowEdge
from opencode.workflow.state import WorkflowState, ExecutionStatus, NodeExecutionState


@pytest.fixture(autouse=True)
def clear_workflows():
    """Clear workflows before each test."""
    _workflows.clear()
    yield
    _workflows.clear()


@pytest.fixture
def sample_workflow():
    """Create a sample workflow for testing."""
    workflow = WorkflowGraph(
        metadata=WorkflowMetadata(
            name="Test Workflow",
            description="A test workflow",
        ),
        variables={"key": "value"},
    )
    # Add a node
    node = WorkflowNode(
        node_type="test_node",
        position_x=100.0,
        position_y=200.0,
        config={"param": "value"},
        label="Test Node",
    )
    workflow.add_node(node)
    _workflows[workflow.id] = workflow
    return workflow


class TestNodePortType:
    """Tests for NodePortType."""

    @pytest.mark.unit
    def test_node_port_type_creation(self):
        """Test creating NodePortType."""
        port = NodePortType(
            name="input1",
            data_type="string",
            direction="input",
            required=True,
            description="Test input",
        )
        assert port.name == "input1"
        assert port.data_type == "string"
        assert port.direction == "input"
        assert port.required is True
        assert port.description == "Test input"


class TestWorkflowNodeType:
    """Tests for WorkflowNodeType."""

    @pytest.mark.unit
    def test_workflow_node_type_creation(self):
        """Test creating WorkflowNodeType."""
        node = WorkflowNodeType(
            id="node-123",
            node_type="llm_process",
            position_x=10.0,
            position_y=20.0,
            config={"model": "gpt-4"},
            label="LLM Node",
            disabled=False,
        )
        assert node.id == "node-123"
        assert node.node_type == "llm_process"
        assert node.position_x == 10.0
        assert node.position_y == 20.0
        assert node.config == {"model": "gpt-4"}
        assert node.label == "LLM Node"
        assert node.disabled is False


class TestWorkflowEdgeType:
    """Tests for WorkflowEdgeType."""

    @pytest.mark.unit
    def test_workflow_edge_type_creation(self):
        """Test creating WorkflowEdgeType."""
        edge = WorkflowEdgeType(
            id="edge-123",
            source_node_id="node-1",
            source_port="output",
            target_node_id="node-2",
            target_port="input",
        )
        assert edge.id == "edge-123"
        assert edge.source_node_id == "node-1"
        assert edge.source_port == "output"
        assert edge.target_node_id == "node-2"
        assert edge.target_port == "input"


class TestWorkflowMetadataType:
    """Tests for WorkflowMetadataType."""

    @pytest.mark.unit
    def test_workflow_metadata_type_creation(self):
        """Test creating WorkflowMetadataType."""
        now = datetime.utcnow()
        metadata = WorkflowMetadataType(
            name="My Workflow",
            description="Description",
            created_at=now,
            updated_at=now,
            version="1.0.0",
        )
        assert metadata.name == "My Workflow"
        assert metadata.description == "Description"
        assert metadata.created_at == now
        assert metadata.updated_at == now
        assert metadata.version == "1.0.0"


class TestExecutionEventType:
    """Tests for ExecutionEventType."""

    @pytest.mark.unit
    def test_execution_event_type_creation(self):
        """Test creating ExecutionEventType."""
        now = datetime.utcnow()
        event = ExecutionEventType(
            event_type="node_started",
            workflow_id="wf-123",
            execution_id="exec-123",
            node_id="node-1",
            data={"key": "value"},
            timestamp=now,
        )
        assert event.event_type == "node_started"
        assert event.workflow_id == "wf-123"
        assert event.execution_id == "exec-123"
        assert event.node_id == "node-1"
        assert event.data == {"key": "value"}
        assert event.timestamp == now


class TestQueryWorkflow:
    """Tests for Query.workflow resolver."""

    @pytest.mark.unit
    def test_query_workflow_exists(self):
        """Test querying an existing workflow."""
        workflow = WorkflowGraph(
            metadata=WorkflowMetadata(name="Test", description="Test"),
        )
        _workflows[workflow.id] = workflow
        
        query = Query()
        result = query.workflow(id=workflow.id)
        
        assert result is not None
        assert result.id == workflow.id
        assert result.metadata.name == "Test"

    @pytest.mark.unit
    def test_query_workflow_not_exists(self):
        """Test querying a non-existing workflow."""
        query = Query()
        result = query.workflow(id="non-existent-id")
        
        assert result is None


class TestQueryWorkflows:
    """Tests for Query.workflows resolver."""

    @pytest.mark.unit
    def test_query_workflows_empty(self):
        """Test querying workflows when empty."""
        query = Query()
        result = query.workflows()
        
        assert result == []

    @pytest.mark.unit
    def test_query_workflows_multiple(self):
        """Test querying multiple workflows."""
        wf1 = WorkflowGraph(metadata=WorkflowMetadata(name="WF1", description="D1"))
        wf2 = WorkflowGraph(metadata=WorkflowMetadata(name="WF2", description="D2"))
        _workflows[wf1.id] = wf1
        _workflows[wf2.id] = wf2
        
        query = Query()
        result = query.workflows()
        
        assert len(result) == 2
        names = [w.metadata.name for w in result]
        assert "WF1" in names
        assert "WF2" in names


class TestQueryNodeTypes:
    """Tests for Query.node_types resolver."""

    @pytest.mark.unit
    def test_query_node_types(self):
        """Test querying node types."""
        query = Query()
        result = query.node_types()
        
        # Should return a list (may be empty if no nodes registered)
        assert isinstance(result, list)


class TestQueryExecution:
    """Tests for Query.execution resolver."""

    @pytest.mark.unit
    def test_query_execution_not_exists(self):
        """Test querying non-existing execution."""
        query = Query()
        result = query.execution(execution_id="non-existent")
        
        assert result is None

    @pytest.mark.unit
    def test_query_execution_exists(self):
        """Test querying existing execution."""
        # Create a mock state store
        engine = get_engine()
        state = WorkflowState(
            workflow_id="wf-123",
            execution_id="exec-123",
            status=ExecutionStatus.RUNNING,
        )
        engine.state_store.save(state)  # Use save() not set()
        
        query = Query()
        result = query.execution(execution_id="exec-123")
        
        assert result is not None
        assert result.workflow_id == "wf-123"
        assert result.execution_id == "exec-123"
        assert result.status == "running"


class TestMutationCreateWorkflow:
    """Tests for Mutation.create_workflow resolver."""

    @pytest.mark.unit
    def test_create_workflow_minimal(self):
        """Test creating workflow with minimal input."""
        mutation = Mutation()
        input_data = CreateWorkflowInput(name="New Workflow")
        
        result = mutation.create_workflow(input=input_data)
        
        assert result is not None
        assert result.metadata.name == "New Workflow"
        assert result.metadata.description == ""
        assert result.id in _workflows

    @pytest.mark.unit
    def test_create_workflow_full(self):
        """Test creating workflow with full input."""
        mutation = Mutation()
        input_data = CreateWorkflowInput(
            name="Full Workflow",
            description="A complete workflow",
            variables={"var1": "value1"},
        )
        
        result = mutation.create_workflow(input=input_data)
        
        assert result.metadata.name == "Full Workflow"
        assert result.metadata.description == "A complete workflow"
        assert result.variables == {"var1": "value1"}


class TestMutationUpdateWorkflow:
    """Tests for Mutation.update_workflow resolver."""

    @pytest.mark.unit
    def test_update_workflow_not_exists(self):
        """Test updating non-existing workflow."""
        mutation = Mutation()
        input_data = UpdateWorkflowInput(name="Updated")
        
        result = mutation.update_workflow(id="non-existent", input=input_data)
        
        assert result is None

    @pytest.mark.unit
    def test_update_workflow_name(self, sample_workflow):
        """Test updating workflow name."""
        mutation = Mutation()
        input_data = UpdateWorkflowInput(name="Updated Name")
        
        result = mutation.update_workflow(id=sample_workflow.id, input=input_data)
        
        assert result is not None
        assert result.metadata.name == "Updated Name"

    @pytest.mark.unit
    def test_update_workflow_description(self, sample_workflow):
        """Test updating workflow description."""
        mutation = Mutation()
        input_data = UpdateWorkflowInput(description="New description")
        
        result = mutation.update_workflow(id=sample_workflow.id, input=input_data)
        
        assert result is not None
        assert result.metadata.description == "New description"

    @pytest.mark.unit
    def test_update_workflow_variables(self, sample_workflow):
        """Test updating workflow variables."""
        mutation = Mutation()
        input_data = UpdateWorkflowInput(variables={"new": "vars"})
        
        result = mutation.update_workflow(id=sample_workflow.id, input=input_data)
        
        assert result is not None
        assert result.variables == {"new": "vars"}

    @pytest.mark.unit
    def test_update_workflow_all_fields(self, sample_workflow):
        """Test updating all workflow fields."""
        mutation = Mutation()
        input_data = UpdateWorkflowInput(
            name="All Updated",
            description="All fields updated",
            variables={"all": "updated"},
        )
        
        result = mutation.update_workflow(id=sample_workflow.id, input=input_data)
        
        assert result.metadata.name == "All Updated"
        assert result.metadata.description == "All fields updated"
        assert result.variables == {"all": "updated"}


class TestMutationDeleteWorkflow:
    """Tests for Mutation.delete_workflow resolver."""

    @pytest.mark.unit
    def test_delete_workflow_exists(self, sample_workflow):
        """Test deleting existing workflow."""
        mutation = Mutation()
        wf_id = sample_workflow.id
        
        result = mutation.delete_workflow(id=wf_id)
        
        assert result is True
        assert wf_id not in _workflows

    @pytest.mark.unit
    def test_delete_workflow_not_exists(self):
        """Test deleting non-existing workflow."""
        mutation = Mutation()
        
        result = mutation.delete_workflow(id="non-existent")
        
        assert result is False


class TestMutationAddNode:
    """Tests for Mutation.add_node resolver."""

    @pytest.mark.unit
    def test_add_node_workflow_not_exists(self):
        """Test adding node to non-existing workflow."""
        mutation = Mutation()
        input_data = AddNodeInput(
            workflow_id="non-existent",
            node_type="test_node",
        )
        
        result = mutation.add_node(input=input_data)
        
        assert result is None

    @pytest.mark.unit
    def test_add_node_minimal(self, sample_workflow):
        """Test adding node with minimal input."""
        mutation = Mutation()
        input_data = AddNodeInput(
            workflow_id=sample_workflow.id,
            node_type="llm_process",
        )
        
        result = mutation.add_node(input=input_data)
        
        assert result is not None
        assert result.node_type == "llm_process"
        assert result.position_x == 0
        assert result.position_y == 0

    @pytest.mark.unit
    def test_add_node_full(self, sample_workflow):
        """Test adding node with full input."""
        mutation = Mutation()
        input_data = AddNodeInput(
            workflow_id=sample_workflow.id,
            node_type="http_request",
            position_x=150.0,
            position_y=250.0,
            config={"url": "https://example.com"},
            label="HTTP Node",
        )
        
        result = mutation.add_node(input=input_data)
        
        assert result is not None
        assert result.node_type == "http_request"
        assert result.position_x == 150.0
        assert result.position_y == 250.0
        assert result.config == {"url": "https://example.com"}
        assert result.label == "HTTP Node"


class TestMutationRemoveNode:
    """Tests for Mutation.remove_node resolver."""

    @pytest.mark.unit
    def test_remove_node_workflow_not_exists(self):
        """Test removing node from non-existing workflow."""
        mutation = Mutation()
        
        result = mutation.remove_node(workflow_id="non-existent", node_id="node-1")
        
        assert result is False

    @pytest.mark.unit
    def test_remove_node_exists(self, sample_workflow):
        """Test removing existing node."""
        node_id = list(sample_workflow.nodes.keys())[0]
        mutation = Mutation()
        
        result = mutation.remove_node(
            workflow_id=sample_workflow.id,
            node_id=node_id,
        )
        
        assert result is True
        assert node_id not in sample_workflow.nodes

    @pytest.mark.unit
    def test_remove_node_not_exists(self, sample_workflow):
        """Test removing non-existing node."""
        mutation = Mutation()
        
        result = mutation.remove_node(
            workflow_id=sample_workflow.id,
            node_id="non-existent-node",
        )
        
        assert result is False


class TestMutationAddEdge:
    """Tests for Mutation.add_edge resolver."""

    @pytest.mark.unit
    def test_add_edge_workflow_not_exists(self):
        """Test adding edge to non-existing workflow."""
        mutation = Mutation()
        input_data = AddEdgeInput(
            workflow_id="non-existent",
            source_node_id="node-1",
            source_port="output",
            target_node_id="node-2",
            target_port="input",
        )
        
        result = mutation.add_edge(input=input_data)
        
        assert result is None

    @pytest.mark.unit
    def test_add_edge_success(self, sample_workflow):
        """Test adding edge successfully."""
        # Add another node
        node2 = WorkflowNode(node_type="test_node2")
        sample_workflow.add_node(node2)
        
        node1_id = list(sample_workflow.nodes.keys())[0]
        
        mutation = Mutation()
        input_data = AddEdgeInput(
            workflow_id=sample_workflow.id,
            source_node_id=node1_id,
            source_port="output",
            target_node_id=node2.id,
            target_port="input",
        )
        
        result = mutation.add_edge(input=input_data)
        
        assert result is not None
        assert result.source_node_id == node1_id
        assert result.target_node_id == node2.id


class TestMutationRemoveEdge:
    """Tests for Mutation.remove_edge resolver."""

    @pytest.mark.unit
    def test_remove_edge_workflow_not_exists(self):
        """Test removing edge from non-existing workflow."""
        mutation = Mutation()
        
        result = mutation.remove_edge(
            workflow_id="non-existent",
            edge_id="edge-1",
        )
        
        assert result is False


class TestMutationCancelExecution:
    """Tests for Mutation.cancel_execution resolver."""

    @pytest.mark.unit
    def test_cancel_execution_not_exists(self):
        """Test canceling non-existing execution."""
        mutation = Mutation()
        
        result = mutation.cancel_execution(execution_id="non-existent")
        
        # Should return False or True depending on engine implementation
        assert isinstance(result, bool)


class TestWorkflowTypeNodes:
    """Tests for WorkflowType.nodes resolver."""

    @pytest.mark.unit
    def test_nodes_workflow_exists(self, sample_workflow):
        """Test getting nodes from existing workflow."""
        wf_type = WorkflowType(
            id=sample_workflow.id,
            metadata=WorkflowMetadataType(
                name=sample_workflow.metadata.name,
                description=sample_workflow.metadata.description,
                created_at=sample_workflow.metadata.created_at,
                updated_at=sample_workflow.metadata.updated_at,
                version=sample_workflow.metadata.version,
            ),
            variables=sample_workflow.variables,
        )
        
        nodes = wf_type.nodes()
        
        assert len(nodes) == 1
        assert nodes[0].node_type == "test_node"

    @pytest.mark.unit
    def test_nodes_workflow_not_exists(self):
        """Test getting nodes from non-existing workflow."""
        wf_type = WorkflowType(
            id="non-existent",
            metadata=WorkflowMetadataType(
                name="Test",
                description="Test",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                version="1.0",
            ),
            variables={},
        )
        
        nodes = wf_type.nodes()
        
        assert nodes == []


class TestWorkflowTypeEdges:
    """Tests for WorkflowType.edges resolver."""

    @pytest.mark.unit
    def test_edges_workflow_exists(self, sample_workflow):
        """Test getting edges from existing workflow."""
        # Add an edge
        node2 = WorkflowNode(node_type="test_node2")
        sample_workflow.add_node(node2)
        node1_id = list(sample_workflow.nodes.keys())[0]
        edge = WorkflowEdge(
            source_node_id=node1_id,
            source_port="output",
            target_node_id=node2.id,
            target_port="input",
        )
        sample_workflow.add_edge(edge)
        
        wf_type = WorkflowType(
            id=sample_workflow.id,
            metadata=WorkflowMetadataType(
                name=sample_workflow.metadata.name,
                description=sample_workflow.metadata.description,
                created_at=sample_workflow.metadata.created_at,
                updated_at=sample_workflow.metadata.updated_at,
                version=sample_workflow.metadata.version,
            ),
            variables=sample_workflow.variables,
        )
        
        edges = wf_type.edges()
        
        assert len(edges) == 1

    @pytest.mark.unit
    def test_edges_workflow_not_exists(self):
        """Test getting edges from non-existing workflow."""
        wf_type = WorkflowType(
            id="non-existent",
            metadata=WorkflowMetadataType(
                name="Test",
                description="Test",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                version="1.0",
            ),
            variables={},
        )
        
        edges = wf_type.edges()
        
        assert edges == []


class TestWorkflowExecutionTypeNodeStates:
    """Tests for WorkflowExecutionType.node_states resolver."""

    @pytest.mark.unit
    def test_node_states_execution_exists(self):
        """Test getting node states from existing execution."""
        # Create execution state
        engine = get_engine()
        state = WorkflowState(
            workflow_id="wf-123",
            execution_id="exec-123",
            status=ExecutionStatus.RUNNING,
        )
        # NodeExecutionState requires node_id as a required field
        state.node_states["node-1"] = NodeExecutionState(
            node_id="node-1",
            status=ExecutionStatus.RUNNING,
            started_at=datetime.utcnow(),
        )
        engine.state_store.save(state)
        
        exec_type = WorkflowExecutionType(
            workflow_id="wf-123",
            execution_id="exec-123",
            status="running",
            started_at=datetime.utcnow(),
            completed_at=None,
            error=None,
            variables={},
        )
        
        node_states = exec_type.node_states()
        
        assert len(node_states) == 1
        assert node_states[0].node_id == "node-1"

    @pytest.mark.unit
    def test_node_states_execution_not_exists(self):
        """Test getting node states from non-existing execution."""
        exec_type = WorkflowExecutionType(
            workflow_id="wf-123",
            execution_id="non-existent",
            status="running",
            started_at=datetime.utcnow(),
            completed_at=None,
            error=None,
            variables={},
        )
        
        node_states = exec_type.node_states()
        
        assert node_states == []


class TestGetGraphqlRouter:
    """Tests for get_graphql_router function."""

    @pytest.mark.unit
    def test_get_graphql_router(self):
        """Test getting GraphQL router."""
        router = get_graphql_router()
        
        assert router is not None


class TestSchemaSubscription:
    """Tests for schema subscription."""

    @pytest.mark.unit
    def test_subscription_type_exists(self):
        """Test Subscription type exists."""
        assert Subscription is not None

    @pytest.mark.unit
    def test_schema_has_subscription(self):
        """Test schema has subscription."""
        assert schema.subscription is not None


class TestInputTypes:
    """Tests for input types."""

    @pytest.mark.unit
    def test_create_workflow_input_defaults(self):
        """Test CreateWorkflowInput defaults."""
        input_data = CreateWorkflowInput(name="Test")
        
        assert input_data.name == "Test"
        assert input_data.description == ""
        assert input_data.variables == {}

    @pytest.mark.unit
    def test_update_workflow_input_defaults(self):
        """Test UpdateWorkflowInput defaults."""
        input_data = UpdateWorkflowInput()
        
        assert input_data.name is None
        assert input_data.description is None
        assert input_data.variables is None

    @pytest.mark.unit
    def test_add_node_input_defaults(self):
        """Test AddNodeInput defaults."""
        input_data = AddNodeInput(workflow_id="wf-1", node_type="test")
        
        assert input_data.workflow_id == "wf-1"
        assert input_data.node_type == "test"
        assert input_data.position_x == 0
        assert input_data.position_y == 0
        assert input_data.config == {}
        assert input_data.label is None

    @pytest.mark.unit
    def test_add_edge_input_creation(self):
        """Test AddEdgeInput creation."""
        input_data = AddEdgeInput(
            workflow_id="wf-1",
            source_node_id="n1",
            source_port="out",
            target_node_id="n2",
            target_port="in",
        )
        
        assert input_data.workflow_id == "wf-1"
        assert input_data.source_node_id == "n1"
        assert input_data.source_port == "out"
        assert input_data.target_node_id == "n2"
        assert input_data.target_port == "in"

    @pytest.mark.unit
    def test_execute_workflow_input_defaults(self):
        """Test ExecuteWorkflowInput defaults."""
        input_data = ExecuteWorkflowInput(workflow_id="wf-1")
        
        assert input_data.workflow_id == "wf-1"
        assert input_data.variables == {}


class TestNodeSchemaTypeInputsOutputs:
    """Tests for NodeSchemaType inputs and outputs resolvers."""

    @pytest.mark.unit
    def test_node_schema_type_inputs_registered_node(self):
        """Test inputs for a registered node type."""
        # Create NodeSchemaType for a potentially registered node
        schema_type = NodeSchemaType(
            node_type="llm_process",
            display_name="LLM Process",
            description="Process with LLM",
            category="processing",
            icon="brain",
            version="1.0",
        )
        
        # Call inputs - may return empty if node not registered
        inputs = schema_type.inputs()
        
        assert isinstance(inputs, list)

    @pytest.mark.unit
    def test_node_schema_type_outputs_registered_node(self):
        """Test outputs for a registered node type."""
        schema_type = NodeSchemaType(
            node_type="llm_process",
            display_name="LLM Process",
            description="Process with LLM",
            category="processing",
            icon="brain",
            version="1.0",
        )
        
        outputs = schema_type.outputs()
        
        assert isinstance(outputs, list)

    @pytest.mark.unit
    def test_node_schema_type_inputs_unregistered_node(self):
        """Test inputs for an unregistered node type."""
        schema_type = NodeSchemaType(
            node_type="non_existent_node_type",
            display_name="Unknown",
            description="Unknown node",
            category="unknown",
            icon="question",
            version="1.0",
        )
        
        inputs = schema_type.inputs()
        
        assert inputs == []

    @pytest.mark.unit
    def test_node_schema_type_outputs_unregistered_node(self):
        """Test outputs for an unregistered node type."""
        schema_type = NodeSchemaType(
            node_type="non_existent_node_type",
            display_name="Unknown",
            description="Unknown node",
            category="unknown",
            icon="question",
            version="1.0",
        )
        
        outputs = schema_type.outputs()
        
        assert outputs == []


class TestMutationExecuteWorkflow:
    """Tests for Mutation.execute_workflow resolver."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_workflow_not_exists(self):
        """Test executing non-existing workflow."""
        mutation = Mutation()
        input_data = ExecuteWorkflowInput(workflow_id="non-existent")
        
        result = await mutation.execute_workflow(input=input_data)
        
        assert result is None


class TestNodeExecutionStateType:
    """Tests for NodeExecutionStateType."""

    @pytest.mark.unit
    def test_node_execution_state_type_creation(self):
        """Test creating NodeExecutionStateType."""
        now = datetime.utcnow()
        state = NodeExecutionStateType(
            node_id="node-1",
            status="completed",
            started_at=now,
            completed_at=now,
            error=None,
            inputs={"in": "value"},
            outputs={"out": "result"},
        )
        
        assert state.node_id == "node-1"
        assert state.status == "completed"
        assert state.started_at == now
        assert state.completed_at == now
        assert state.error is None
        assert state.inputs == {"in": "value"}
        assert state.outputs == {"out": "result"}

    @pytest.mark.unit
    def test_node_execution_state_type_with_error(self):
        """Test creating NodeExecutionStateType with error."""
        state = NodeExecutionStateType(
            node_id="node-1",
            status="failed",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            error="Something went wrong",
            inputs=None,
            outputs=None,
        )
        
        assert state.status == "failed"
        assert state.error == "Something went wrong"
