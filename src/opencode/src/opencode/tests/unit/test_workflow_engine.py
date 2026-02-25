"""
Tests for workflow engine execution paths.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio

from opencode.workflow.engine import WorkflowEngine
from opencode.workflow.graph import WorkflowGraph, WorkflowNode, WorkflowEdge, WorkflowMetadata
from opencode.workflow.state import WorkflowState, ExecutionStatus, NodeExecutionState
from opencode.workflow.node import BaseNode, NodePort, NodeSchema
from opencode.workflow.registry import NodeRegistry


class TestWorkflowGraph:
    """Tests for WorkflowGraph."""
    
    @pytest.mark.unit
    def test_workflow_graph_creation(self):
        """Test WorkflowGraph instantiation."""
        graph = WorkflowGraph()
        assert graph.nodes == {}
        assert graph.edges == {}
    
    @pytest.mark.unit
    def test_add_node(self):
        """Test adding a node to the graph."""
        graph = WorkflowGraph()
        node = WorkflowNode(id="test_node", node_type="test", config={})
        node_id = graph.add_node(node)
        assert "test_node" in graph.nodes
        assert graph.nodes["test_node"] == node
    
    @pytest.mark.unit
    def test_add_edge(self):
        """Test adding an edge to the graph."""
        graph = WorkflowGraph()
        node1 = WorkflowNode(id="node1", node_type="test", config={})
        node2 = WorkflowNode(id="node2", node_type="test", config={})
        graph.add_node(node1)
        graph.add_node(node2)
        
        edge = WorkflowEdge(
            source_node_id="node1",
            source_port="output",
            target_node_id="node2",
            target_port="input",
        )
        graph.add_edge(edge)
        assert edge.id in graph.edges
    
    @pytest.mark.unit
    def test_remove_node(self):
        """Test removing a node from the graph."""
        graph = WorkflowGraph()
        node = WorkflowNode(id="test_node", node_type="test", config={})
        graph.add_node(node)
        graph.remove_node("test_node")
        assert "test_node" not in graph.nodes
    
    @pytest.mark.unit
    def test_workflow_metadata(self):
        """Test workflow metadata."""
        metadata = WorkflowMetadata(name="Test Workflow")
        graph = WorkflowGraph(metadata=metadata)
        assert graph.metadata.name == "Test Workflow"


class TestWorkflowNode:
    """Tests for WorkflowNode."""
    
    @pytest.mark.unit
    def test_workflow_node_creation(self):
        """Test WorkflowNode instantiation."""
        node = WorkflowNode(id="test", node_type="test_type", config={"key": "value"})
        assert node.id == "test"
        assert node.node_type == "test_type"
        assert node.config == {"key": "value"}
    
    @pytest.mark.unit
    def test_workflow_node_defaults(self):
        """Test WorkflowNode default values."""
        node = WorkflowNode(node_type="test")
        assert node.config == {}
        assert node.position_x == 0
        assert node.position_y == 0
    
    @pytest.mark.unit
    def test_workflow_node_disabled(self):
        """Test WorkflowNode disabled flag."""
        node = WorkflowNode(node_type="test", disabled=True)
        assert node.disabled is True


class TestWorkflowEdge:
    """Tests for WorkflowEdge."""
    
    @pytest.mark.unit
    def test_workflow_edge_creation(self):
        """Test WorkflowEdge instantiation."""
        edge = WorkflowEdge(
            source_node_id="node1",
            source_port="output",
            target_node_id="node2",
            target_port="input",
        )
        assert edge.source_node_id == "node1"
        assert edge.target_node_id == "node2"
        assert edge.source_port == "output"
        assert edge.target_port == "input"
    
    @pytest.mark.unit
    def test_workflow_edge_with_label(self):
        """Test WorkflowEdge with label."""
        edge = WorkflowEdge(
            source_node_id="node1",
            source_port="output",
            target_node_id="node2",
            target_port="input",
            label="data_flow",
        )
        assert edge.label == "data_flow"
    
    @pytest.mark.unit
    def test_workflow_edge_disabled(self):
        """Test WorkflowEdge disabled flag."""
        edge = WorkflowEdge(
            source_node_id="node1",
            source_port="output",
            target_node_id="node2",
            target_port="input",
            disabled=True,
        )
        assert edge.disabled is True


class TestWorkflowMetadata:
    """Tests for WorkflowMetadata."""
    
    @pytest.mark.unit
    def test_metadata_creation(self):
        """Test WorkflowMetadata instantiation."""
        metadata = WorkflowMetadata(name="Test Workflow", description="A test")
        assert metadata.name == "Test Workflow"
        assert metadata.description == "A test"
    
    @pytest.mark.unit
    def test_metadata_defaults(self):
        """Test WorkflowMetadata default values."""
        metadata = WorkflowMetadata()
        assert metadata.name == "Untitled Workflow"
        assert metadata.version == "1.0.0"
        assert metadata.tags == []


class TestNodeExecutionState:
    """Tests for NodeExecutionState."""
    
    @pytest.mark.unit
    def test_node_state_creation(self):
        """Test NodeExecutionState instantiation."""
        state = NodeExecutionState(node_id="test_node")
        assert state.node_id == "test_node"
        assert state.status == ExecutionStatus.PENDING
    
    @pytest.mark.unit
    def test_node_state_start(self):
        """Test NodeExecutionState start method."""
        state = NodeExecutionState(node_id="test")
        state.start()
        assert state.status == ExecutionStatus.RUNNING
        assert state.started_at is not None
    
    @pytest.mark.unit
    def test_node_state_complete(self):
        """Test NodeExecutionState complete method."""
        state = NodeExecutionState(node_id="test")
        state.start()
        state.complete({"result": "ok"})
        assert state.status == ExecutionStatus.COMPLETED
        assert state.outputs == {"result": "ok"}
        assert state.completed_at is not None
    
    @pytest.mark.unit
    def test_node_state_fail(self):
        """Test NodeExecutionState fail method."""
        state = NodeExecutionState(node_id="test")
        state.start()
        state.fail("Something went wrong")
        assert state.status == ExecutionStatus.FAILED
        assert state.error == "Something went wrong"
    
    @pytest.mark.unit
    def test_node_state_skip(self):
        """Test NodeExecutionState skip method."""
        state = NodeExecutionState(node_id="test")
        state.skip("Not needed")
        assert state.status == ExecutionStatus.SKIPPED
    
    @pytest.mark.unit
    def test_node_state_can_retry(self):
        """Test NodeExecutionState can_retry method."""
        state = NodeExecutionState(node_id="test", max_retries=3)
        state.fail("Error")
        assert state.can_retry() is True
        
        # Exhaust retries
        state.attempts = 3
        assert state.can_retry() is False


class TestWorkflowState:
    """Tests for WorkflowState."""
    
    @pytest.mark.unit
    def test_workflow_state_creation(self):
        """Test WorkflowState instantiation."""
        state = WorkflowState(workflow_id="test-workflow")
        assert state.workflow_id == "test-workflow"
        assert state.status == ExecutionStatus.PENDING
    
    @pytest.mark.unit
    def test_workflow_state_defaults(self):
        """Test WorkflowState default values."""
        state = WorkflowState(workflow_id="test")
        assert state.node_states == {}
        assert state.variables == {}
    
    @pytest.mark.unit
    def test_is_complete(self):
        """Test checking if workflow is complete."""
        state = WorkflowState(workflow_id="test")
        assert state.is_complete() is False
        state.status = ExecutionStatus.COMPLETED
        assert state.is_complete() is True
    
    @pytest.mark.unit
    def test_get_node_state(self):
        """Test getting node state."""
        state = WorkflowState(workflow_id="test")
        # Node state doesn't exist until initialized
        node_state = state.get_node_state("node1")
        assert node_state is None
        
        # Initialize nodes first
        state.initialize_nodes(["node1"])
        node_state = state.get_node_state("node1")
        assert node_state is not None
        assert node_state.node_id == "node1"


class TestExecutionStatus:
    """Tests for ExecutionStatus enum."""
    
    @pytest.mark.unit
    def test_execution_status_values(self):
        """Test ExecutionStatus enum values."""
        assert ExecutionStatus.PENDING.value == "pending"
        assert ExecutionStatus.RUNNING.value == "running"
        assert ExecutionStatus.COMPLETED.value == "completed"
        assert ExecutionStatus.FAILED.value == "failed"
        assert ExecutionStatus.CANCELLED.value == "cancelled"
        assert ExecutionStatus.PAUSED.value == "paused"
        assert ExecutionStatus.SKIPPED.value == "skipped"


class TestNodeRegistry:
    """Tests for NodeRegistry."""
    
    @pytest.mark.unit
    def test_registry_creation(self):
        """Test NodeRegistry instantiation."""
        registry = NodeRegistry()
        assert registry is not None
    
    @pytest.mark.unit
    def test_registry_get(self):
        """Test getting node from registry."""
        registry = NodeRegistry()
        # May return None if not registered
        node = registry.get("nonexistent")
        assert node is None
    
    @pytest.mark.unit
    def test_register_decorator(self):
        """Test registering a node using the decorator."""
        from opencode.workflow.node import BaseNode, NodeSchema, NodePort, PortDirection
        
        # Clear registry first
        NodeRegistry.clear()
        
        @NodeRegistry.register("test_node_type")
        class TestNodeForRegistry(BaseNode):
            @classmethod
            def get_schema(cls) -> NodeSchema:
                return NodeSchema(
                    node_type="test_node_type",
                    display_name="Test Node",
                    inputs=[NodePort(name="input", data_type="string", direction=PortDirection.INPUT)],
                    outputs=[NodePort(name="output", data_type="string", direction=PortDirection.OUTPUT)],
                    category="test",
                )
            
            async def execute(self, inputs: dict) -> dict:
                return {"output": inputs.get("input")}
        
        # Verify registration
        assert NodeRegistry.get("test_node_type") == TestNodeForRegistry
        
        # Clean up
        NodeRegistry.unregister("test_node_type")
    
    @pytest.mark.unit
    def test_register_decorator_auto_name(self):
        """Test registering a node with auto-generated name."""
        from opencode.workflow.node import BaseNode, NodeSchema
        
        NodeRegistry.clear()
        
        @NodeRegistry.register()
        class AutoNamedNode(BaseNode):
            @classmethod
            def get_schema(cls) -> NodeSchema:
                return NodeSchema(
                    node_type="auto_named_node",
                    display_name="Auto Named Node",
                    inputs=[],
                    outputs=[],
                    category="test",
                )
            
            async def execute(self, inputs: dict) -> dict:
                return {}
        
        # Should be registered as "auto_named_node"
        assert NodeRegistry.get("auto_named_node") == AutoNamedNode
        
        NodeRegistry.unregister("auto_named_node")
    
    @pytest.mark.unit
    def test_register_node_explicit(self):
        """Test registering a node explicitly."""
        from opencode.workflow.node import BaseNode, NodeSchema
        
        NodeRegistry.clear()
        
        class ExplicitNode(BaseNode):
            @classmethod
            def get_schema(cls) -> NodeSchema:
                return NodeSchema(
                    node_type="explicit",
                    display_name="Explicit Node",
                    inputs=[],
                    outputs=[],
                    category="test",
                )
            
            async def execute(self, inputs: dict) -> dict:
                return {}
        
        NodeRegistry.register_node(ExplicitNode, "explicit_node")
        assert NodeRegistry.get("explicit_node") == ExplicitNode
        
        NodeRegistry.unregister("explicit_node")
    
    @pytest.mark.unit
    def test_register_node_overwrite(self):
        """Test overwriting an existing node registration."""
        from opencode.workflow.node import BaseNode, NodeSchema
        
        NodeRegistry.clear()
        
        class FirstNode(BaseNode):
            @classmethod
            def get_schema(cls) -> NodeSchema:
                return NodeSchema(node_type="first", display_name="First", inputs=[], outputs=[], category="test")
            async def execute(self, inputs: dict) -> dict:
                return {"version": 1}
        
        class SecondNode(BaseNode):
            @classmethod
            def get_schema(cls) -> NodeSchema:
                return NodeSchema(node_type="second", display_name="Second", inputs=[], outputs=[], category="test")
            async def execute(self, inputs: dict) -> dict:
                return {"version": 2}
        
        NodeRegistry.register_node(FirstNode, "overwrite_test")
        NodeRegistry.register_node(SecondNode, "overwrite_test")  # Should log warning
        
        assert NodeRegistry.get("overwrite_test") == SecondNode
        
        NodeRegistry.unregister("overwrite_test")
    
    @pytest.mark.unit
    def test_get_required_existing(self):
        """Test getting a required node that exists."""
        from opencode.workflow.node import BaseNode, NodeSchema
        
        NodeRegistry.clear()
        
        class RequiredNode(BaseNode):
            @classmethod
            def get_schema(cls) -> NodeSchema:
                return NodeSchema(node_type="required", display_name="Required", inputs=[], outputs=[], category="test")
            async def execute(self, inputs: dict) -> dict:
                return {}
        
        NodeRegistry.register_node(RequiredNode, "required_node")
        
        result = NodeRegistry.get_required("required_node")
        assert result == RequiredNode
        
        NodeRegistry.unregister("required_node")
    
    @pytest.mark.unit
    def test_get_required_missing(self):
        """Test getting a required node that doesn't exist."""
        NodeRegistry.clear()
        
        with pytest.raises(KeyError, match="not registered"):
            NodeRegistry.get_required("nonexistent_node")
    
    @pytest.mark.unit
    def test_create_node(self):
        """Test creating a node instance."""
        from opencode.workflow.node import BaseNode, NodeSchema
        
        NodeRegistry.clear()
        
        class CreatableNode(BaseNode):
            @classmethod
            def get_schema(cls) -> NodeSchema:
                return NodeSchema(node_type="creatable", display_name="Creatable", inputs=[], outputs=[], category="test")
            async def execute(self, inputs: dict) -> dict:
                return {}
        
        NodeRegistry.register_node(CreatableNode, "creatable_node")
        
        instance = NodeRegistry.create("creatable_node", "node_123", {"key": "value"})
        
        assert isinstance(instance, CreatableNode)
        assert instance.node_id == "node_123"
        assert instance.config == {"key": "value"}
        
        NodeRegistry.unregister("creatable_node")
    
    @pytest.mark.unit
    def test_list_nodes(self):
        """Test listing all registered nodes."""
        from opencode.workflow.node import BaseNode, NodeSchema
        
        NodeRegistry.clear()
        
        class ListNode1(BaseNode):
            @classmethod
            def get_schema(cls) -> NodeSchema:
                return NodeSchema(node_type="list1", display_name="List 1", inputs=[], outputs=[], category="test")
            async def execute(self, inputs: dict) -> dict:
                return {}
        
        class ListNode2(BaseNode):
            @classmethod
            def get_schema(cls) -> NodeSchema:
                return NodeSchema(node_type="list2", display_name="List 2", inputs=[], outputs=[], category="test")
            async def execute(self, inputs: dict) -> dict:
                return {}
        
        NodeRegistry.register_node(ListNode1, "list_node_1")
        NodeRegistry.register_node(ListNode2, "list_node_2")
        
        nodes = NodeRegistry.list_nodes()
        
        assert "list_node_1" in nodes
        assert "list_node_2" in nodes
        
        NodeRegistry.clear()
    
    @pytest.mark.unit
    def test_list_categories(self):
        """Test listing all categories."""
        from opencode.workflow.node import BaseNode, NodeSchema
        
        NodeRegistry.clear()
        
        class CatNode1(BaseNode):
            @classmethod
            def get_schema(cls) -> NodeSchema:
                return NodeSchema(node_type="cat1", display_name="Cat 1", inputs=[], outputs=[], category="category_a")
            async def execute(self, inputs: dict) -> dict:
                return {}
        
        class CatNode2(BaseNode):
            @classmethod
            def get_schema(cls) -> NodeSchema:
                return NodeSchema(node_type="cat2", display_name="Cat 2", inputs=[], outputs=[], category="category_b")
            async def execute(self, inputs: dict) -> dict:
                return {}
        
        NodeRegistry.register_node(CatNode1, "cat_node_1")
        NodeRegistry.register_node(CatNode2, "cat_node_2")
        
        categories = NodeRegistry.list_categories()
        
        assert "category_a" in categories
        assert "category_b" in categories
        
        NodeRegistry.clear()
    
    @pytest.mark.unit
    def test_get_nodes_by_category(self):
        """Test getting nodes by category."""
        from opencode.workflow.node import BaseNode, NodeSchema
        
        NodeRegistry.clear()
        
        class DataNode1(BaseNode):
            @classmethod
            def get_schema(cls) -> NodeSchema:
                return NodeSchema(node_type="data1", display_name="Data 1", inputs=[], outputs=[], category="data")
            async def execute(self, inputs: dict) -> dict:
                return {}
        
        class DataNode2(BaseNode):
            @classmethod
            def get_schema(cls) -> NodeSchema:
                return NodeSchema(node_type="data2", display_name="Data 2", inputs=[], outputs=[], category="data")
            async def execute(self, inputs: dict) -> dict:
                return {}
        
        class ProcessNode(BaseNode):
            @classmethod
            def get_schema(cls) -> NodeSchema:
                return NodeSchema(node_type="process", display_name="Process", inputs=[], outputs=[], category="process")
            async def execute(self, inputs: dict) -> dict:
                return {}
        
        NodeRegistry.register_node(DataNode1, "data_node_1")
        NodeRegistry.register_node(DataNode2, "data_node_2")
        NodeRegistry.register_node(ProcessNode, "process_node")
        
        data_nodes = NodeRegistry.get_nodes_by_category("data")
        
        assert len(data_nodes) == 2
        assert "data_node_1" in data_nodes
        assert "data_node_2" in data_nodes
        
        NodeRegistry.clear()
    
    @pytest.mark.unit
    def test_get_nodes_by_category_empty(self):
        """Test getting nodes from a nonexistent category."""
        NodeRegistry.clear()
        
        nodes = NodeRegistry.get_nodes_by_category("nonexistent_category")
        assert nodes == []
    
    @pytest.mark.unit
    def test_get_all_schemas(self):
        """Test getting all node schemas."""
        from opencode.workflow.node import BaseNode, NodeSchema
        
        NodeRegistry.clear()
        
        class SchemaNode(BaseNode):
            @classmethod
            def get_schema(cls) -> NodeSchema:
                return NodeSchema(
                    node_type="schema_test",
                    display_name="Schema Test",
                    inputs=[],
                    outputs=[],
                    category="test",
                    description="Test schema node",
                )
            async def execute(self, inputs: dict) -> dict:
                return {}
        
        NodeRegistry.register_node(SchemaNode, "schema_node")
        
        schemas = NodeRegistry.get_all_schemas()
        
        assert "schema_node" in schemas
        assert schemas["schema_node"].node_type == "schema_test"
        
        NodeRegistry.clear()
    
    @pytest.mark.unit
    def test_unregister_existing(self):
        """Test unregistering an existing node."""
        from opencode.workflow.node import BaseNode, NodeSchema
        
        NodeRegistry.clear()
        
        class UnregNode(BaseNode):
            @classmethod
            def get_schema(cls) -> NodeSchema:
                return NodeSchema(node_type="unreg", display_name="Unreg", inputs=[], outputs=[], category="test")
            async def execute(self, inputs: dict) -> dict:
                return {}
        
        NodeRegistry.register_node(UnregNode, "unregister_test")
        
        assert NodeRegistry.get("unregister_test") is not None
        
        result = NodeRegistry.unregister("unregister_test")
        
        assert result is True
        assert NodeRegistry.get("unregister_test") is None
    
    @pytest.mark.unit
    def test_unregister_nonexistent(self):
        """Test unregistering a nonexistent node."""
        NodeRegistry.clear()
        
        result = NodeRegistry.unregister("nonexistent_node")
        assert result is False
    
    @pytest.mark.unit
    def test_clear(self):
        """Test clearing all registered nodes."""
        from opencode.workflow.node import BaseNode, NodeSchema
        
        NodeRegistry.clear()
        
        class ClearNode(BaseNode):
            @classmethod
            def get_schema(cls) -> NodeSchema:
                return NodeSchema(node_type="clear", display_name="Clear", inputs=[], outputs=[], category="test")
            async def execute(self, inputs: dict) -> dict:
                return {}
        
        NodeRegistry.register_node(ClearNode, "clear_node_1")
        NodeRegistry.register_node(ClearNode, "clear_node_2")
        
        assert len(NodeRegistry.list_nodes()) == 2
        
        NodeRegistry.clear()
        
        assert len(NodeRegistry.list_nodes()) == 0
        assert len(NodeRegistry.list_categories()) == 0
    
    @pytest.mark.unit
    def test_to_snake_case(self):
        """Test converting CamelCase to snake_case."""
        assert NodeRegistry._to_snake_case("CamelCase") == "camel_case"
        assert NodeRegistry._to_snake_case("HTTPNode") == "h_t_t_p_node"
        assert NodeRegistry._to_snake_case("Simple") == "simple"
        assert NodeRegistry._to_snake_case("XMLParser") == "x_m_l_parser"


class TestBaseNode:
    """Tests for BaseNode abstract class."""
    
    @pytest.mark.unit
    def test_base_node_is_abstract(self):
        """Test that BaseNode cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseNode(node_id="test", config={})


class TestWorkflowEngine:
    """Tests for WorkflowEngine."""
    
    @pytest.mark.unit
    def test_engine_creation(self):
        """Test WorkflowEngine instantiation."""
        engine = WorkflowEngine()
        assert engine is not None
    
    @pytest.mark.asyncio
    async def test_execute_empty_graph(self):
        """Test executing an empty graph."""
        engine = WorkflowEngine()
        graph = WorkflowGraph()
        state = await engine.execute(graph)
        assert state.status == ExecutionStatus.COMPLETED


class TestWorkflowIntegration:
    """Integration tests for workflow components."""
    
    @pytest.mark.unit
    def test_graph_node_edge_integration(self):
        """Test graph, node, and edge integration."""
        graph = WorkflowGraph()
        
        # Add nodes
        node1 = WorkflowNode(id="source", node_type="data_source", config={"source": "file"})
        node2 = WorkflowNode(id="process", node_type="llm_process", config={"model": "gpt-4"})
        node3 = WorkflowNode(id="output", node_type="data_output", config={})
        
        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_node(node3)
        
        # Add edges
        graph.add_edge(WorkflowEdge(
            source_node_id="source",
            source_port="output",
            target_node_id="process",
            target_port="input",
        ))
        graph.add_edge(WorkflowEdge(
            source_node_id="process",
            source_port="output",
            target_node_id="output",
            target_port="input",
        ))
        
        # Verify structure
        assert len(graph.nodes) == 3
        assert len(graph.edges) == 2
    
    @pytest.mark.unit
    def test_state_progression(self):
        """Test state progression through workflow."""
        state = WorkflowState(workflow_id="test-workflow")
        
        # Initial state
        assert state.status == ExecutionStatus.PENDING
        
        # Start execution
        state.status = ExecutionStatus.RUNNING
        
        # Use start_node which creates the state if it doesn't exist
        node_state = state.start_node("node1", inputs={"query": "test"})
        node_state.complete({"data": "result"})
        
        # Verify state
        assert node_state.status == ExecutionStatus.COMPLETED
        assert node_state.outputs == {"data": "result"}
        
        # Complete workflow
        state.status = ExecutionStatus.COMPLETED
        assert state.status == ExecutionStatus.COMPLETED
