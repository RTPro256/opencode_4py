"""
Tests for workflow/graph.py

Tests for WorkflowNode, WorkflowEdge, WorkflowMetadata, and WorkflowGraph classes.
"""

import pytest
from datetime import datetime
from typing import Dict, Any

from opencode.workflow.graph import (
    WorkflowNode,
    WorkflowEdge,
    WorkflowMetadata,
    WorkflowGraph,
)


class TestWorkflowNode:
    """Tests for WorkflowNode model."""

    def test_default_values(self):
        """Test WorkflowNode with minimal required fields."""
        node = WorkflowNode(node_type="test_node")
        
        assert node.node_type == "test_node"
        assert node.id is not None
        assert node.position_x == 0
        assert node.position_y == 0
        assert node.config == {}
        assert node.label is None
        assert node.disabled is False

    def test_custom_values(self):
        """Test WorkflowNode with custom values."""
        node = WorkflowNode(
            id="custom-id",
            node_type="data_source",
            position_x=100.5,
            position_y=200.5,
            config={"key": "value"},
            label="My Node",
            disabled=True,
        )
        
        assert node.id == "custom-id"
        assert node.node_type == "data_source"
        assert node.position_x == 100.5
        assert node.position_y == 200.5
        assert node.config == {"key": "value"}
        assert node.label == "My Node"
        assert node.disabled is True

    def test_unique_ids(self):
        """Test that nodes get unique IDs by default."""
        node1 = WorkflowNode(node_type="test")
        node2 = WorkflowNode(node_type="test")
        
        assert node1.id != node2.id

    def test_extra_fields_allowed(self):
        """Test that extra fields are allowed."""
        node = WorkflowNode(
            node_type="test",
            custom_field="custom_value",
        )
        
        assert hasattr(node, "custom_field")
        assert node.custom_field == "custom_value"


class TestWorkflowEdge:
    """Tests for WorkflowEdge model."""

    def test_default_values(self):
        """Test WorkflowEdge with required fields."""
        edge = WorkflowEdge(
            source_node_id="node1",
            source_port="output",
            target_node_id="node2",
            target_port="input",
        )
        
        assert edge.source_node_id == "node1"
        assert edge.source_port == "output"
        assert edge.target_node_id == "node2"
        assert edge.target_port == "input"
        assert edge.id is not None
        assert edge.label is None
        assert edge.disabled is False

    def test_custom_values(self):
        """Test WorkflowEdge with custom values."""
        edge = WorkflowEdge(
            id="edge-1",
            source_node_id="node1",
            source_port="output1",
            target_node_id="node2",
            target_port="input1",
            label="Connection",
            disabled=True,
        )
        
        assert edge.id == "edge-1"
        assert edge.label == "Connection"
        assert edge.disabled is True

    def test_unique_ids(self):
        """Test that edges get unique IDs by default."""
        edge1 = WorkflowEdge(
            source_node_id="n1", source_port="o",
            target_node_id="n2", target_port="i",
        )
        edge2 = WorkflowEdge(
            source_node_id="n1", source_port="o",
            target_node_id="n2", target_port="i",
        )
        
        assert edge1.id != edge2.id

    def test_extra_fields_allowed(self):
        """Test that extra fields are allowed."""
        edge = WorkflowEdge(
            source_node_id="n1", source_port="o",
            target_node_id="n2", target_port="i",
            custom_field="value",
        )
        
        assert hasattr(edge, "custom_field")


class TestWorkflowMetadata:
    """Tests for WorkflowMetadata model."""

    def test_default_values(self):
        """Test WorkflowMetadata with defaults."""
        meta = WorkflowMetadata()
        
        assert meta.name == "Untitled Workflow"
        assert meta.description == ""
        assert meta.version == "1.0.0"
        assert meta.author == ""
        assert meta.tags == []
        assert isinstance(meta.created_at, datetime)
        assert isinstance(meta.updated_at, datetime)

    def test_custom_values(self):
        """Test WorkflowMetadata with custom values."""
        meta = WorkflowMetadata(
            name="My Workflow",
            description="A test workflow",
            version="2.0.0",
            author="Test Author",
            tags=["test", "example"],
        )
        
        assert meta.name == "My Workflow"
        assert meta.description == "A test workflow"
        assert meta.version == "2.0.0"
        assert meta.author == "Test Author"
        assert meta.tags == ["test", "example"]


class TestWorkflowGraph:
    """Tests for WorkflowGraph model."""

    def test_default_values(self):
        """Test WorkflowGraph with defaults."""
        graph = WorkflowGraph()
        
        assert graph.id is not None
        assert graph.metadata.name == "Untitled Workflow"
        assert graph.nodes == {}
        assert graph.edges == {}
        assert graph.variables == {}

    def test_custom_metadata(self):
        """Test WorkflowGraph with custom metadata."""
        graph = WorkflowGraph(
            metadata=WorkflowMetadata(name="Custom Workflow"),
            variables={"var1": "value1"},
        )
        
        assert graph.metadata.name == "Custom Workflow"
        assert graph.variables == {"var1": "value1"}

    def test_add_node(self):
        """Test adding a node to the graph."""
        graph = WorkflowGraph()
        node = WorkflowNode(node_type="data_source")
        
        node_id = graph.add_node(node)
        
        assert node_id == node.id
        assert node.id in graph.nodes
        assert graph.nodes[node.id] == node

    def test_add_node_updates_timestamp(self):
        """Test that adding a node updates the timestamp."""
        graph = WorkflowGraph()
        original_time = graph.metadata.updated_at
        
        # Add a node
        node = WorkflowNode(node_type="test")
        graph.add_node(node)
        
        # Timestamp should be updated
        assert graph.metadata.updated_at >= original_time

    def test_remove_node(self):
        """Test removing a node from the graph."""
        graph = WorkflowGraph()
        node = WorkflowNode(node_type="test")
        graph.add_node(node)
        
        result = graph.remove_node(node.id)
        
        assert result is True
        assert node.id not in graph.nodes

    def test_remove_node_not_found(self):
        """Test removing a non-existent node."""
        graph = WorkflowGraph()
        
        result = graph.remove_node("non-existent")
        
        assert result is False

    def test_remove_node_removes_connected_edges(self):
        """Test that removing a node also removes connected edges."""
        graph = WorkflowGraph()
        
        node1 = WorkflowNode(id="n1", node_type="source")
        node2 = WorkflowNode(id="n2", node_type="target")
        graph.add_node(node1)
        graph.add_node(node2)
        
        edge = WorkflowEdge(
            id="e1",
            source_node_id="n1",
            source_port="out",
            target_node_id="n2",
            target_port="in",
        )
        graph.add_edge(edge)
        
        # Remove source node
        graph.remove_node("n1")
        
        assert "n1" not in graph.nodes
        assert "e1" not in graph.edges

    def test_add_edge(self):
        """Test adding an edge to the graph."""
        graph = WorkflowGraph()
        
        node1 = WorkflowNode(id="n1", node_type="source")
        node2 = WorkflowNode(id="n2", node_type="target")
        graph.add_node(node1)
        graph.add_node(node2)
        
        edge = WorkflowEdge(
            id="e1",
            source_node_id="n1",
            source_port="out",
            target_node_id="n2",
            target_port="in",
        )
        
        success, error = graph.add_edge(edge)
        
        assert success is True
        assert error is None
        assert "e1" in graph.edges

    def test_add_edge_source_not_found(self):
        """Test adding an edge with non-existent source node."""
        graph = WorkflowGraph()
        node2 = WorkflowNode(id="n2", node_type="target")
        graph.add_node(node2)
        
        edge = WorkflowEdge(
            source_node_id="non-existent",
            source_port="out",
            target_node_id="n2",
            target_port="in",
        )
        
        success, error = graph.add_edge(edge)
        
        assert success is False
        assert "Source node" in error

    def test_add_edge_target_not_found(self):
        """Test adding an edge with non-existent target node."""
        graph = WorkflowGraph()
        node1 = WorkflowNode(id="n1", node_type="source")
        graph.add_node(node1)
        
        edge = WorkflowEdge(
            source_node_id="n1",
            source_port="out",
            target_node_id="non-existent",
            target_port="in",
        )
        
        success, error = graph.add_edge(edge)
        
        assert success is False
        assert "Target node" in error

    def test_add_edge_creates_cycle(self):
        """Test that adding an edge that creates a cycle is rejected."""
        graph = WorkflowGraph()
        
        # Create nodes
        node1 = WorkflowNode(id="n1", node_type="a")
        node2 = WorkflowNode(id="n2", node_type="b")
        node3 = WorkflowNode(id="n3", node_type="c")
        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_node(node3)
        
        # Create edges: n1 -> n2 -> n3
        edge1 = WorkflowEdge(
            id="e1", source_node_id="n1", source_port="o",
            target_node_id="n2", target_port="i",
        )
        edge2 = WorkflowEdge(
            id="e2", source_node_id="n2", source_port="o",
            target_node_id="n3", target_port="i",
        )
        graph.add_edge(edge1)
        graph.add_edge(edge2)
        
        # Try to create cycle: n3 -> n1
        cycle_edge = WorkflowEdge(
            source_node_id="n3", source_port="o",
            target_node_id="n1", target_port="i",
        )
        
        success, error = graph.add_edge(cycle_edge)
        
        assert success is False
        assert "cycle" in error.lower()

    def test_remove_edge(self):
        """Test removing an edge from the graph."""
        graph = WorkflowGraph()
        
        node1 = WorkflowNode(id="n1", node_type="a")
        node2 = WorkflowNode(id="n2", node_type="b")
        graph.add_node(node1)
        graph.add_node(node2)
        
        edge = WorkflowEdge(
            id="e1", source_node_id="n1", source_port="o",
            target_node_id="n2", target_port="i",
        )
        graph.add_edge(edge)
        
        result = graph.remove_edge("e1")
        
        assert result is True
        assert "e1" not in graph.edges

    def test_remove_edge_not_found(self):
        """Test removing a non-existent edge."""
        graph = WorkflowGraph()
        
        result = graph.remove_edge("non-existent")
        
        assert result is False

    def test_get_node(self):
        """Test getting a node by ID."""
        graph = WorkflowGraph()
        node = WorkflowNode(id="n1", node_type="test")
        graph.add_node(node)
        
        result = graph.get_node("n1")
        
        assert result == node

    def test_get_node_not_found(self):
        """Test getting a non-existent node."""
        graph = WorkflowGraph()
        
        result = graph.get_node("non-existent")
        
        assert result is None

    def test_get_edge(self):
        """Test getting an edge by ID."""
        graph = WorkflowGraph()
        
        node1 = WorkflowNode(id="n1", node_type="a")
        node2 = WorkflowNode(id="n2", node_type="b")
        graph.add_node(node1)
        graph.add_node(node2)
        
        edge = WorkflowEdge(
            id="e1", source_node_id="n1", source_port="o",
            target_node_id="n2", target_port="i",
        )
        graph.add_edge(edge)
        
        result = graph.get_edge("e1")
        
        assert result == edge

    def test_get_edge_not_found(self):
        """Test getting a non-existent edge."""
        graph = WorkflowGraph()
        
        result = graph.get_edge("non-existent")
        
        assert result is None

    def test_get_edges_for_node(self):
        """Test getting all edges for a node."""
        graph = WorkflowGraph()
        
        node1 = WorkflowNode(id="n1", node_type="a")
        node2 = WorkflowNode(id="n2", node_type="b")
        node3 = WorkflowNode(id="n3", node_type="c")
        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_node(node3)
        
        edge1 = WorkflowEdge(
            id="e1", source_node_id="n1", source_port="o",
            target_node_id="n2", target_port="i",
        )
        edge2 = WorkflowEdge(
            id="e2", source_node_id="n2", source_port="o",
            target_node_id="n3", target_port="i",
        )
        graph.add_edge(edge1)
        graph.add_edge(edge2)
        
        incoming, outgoing = graph.get_edges_for_node("n2")
        
        assert len(incoming) == 1
        assert incoming[0].id == "e1"
        assert len(outgoing) == 1
        assert outgoing[0].id == "e2"

    def test_get_incoming_edges(self):
        """Test getting incoming edges for a node."""
        graph = WorkflowGraph()
        
        node1 = WorkflowNode(id="n1", node_type="a")
        node2 = WorkflowNode(id="n2", node_type="b")
        graph.add_node(node1)
        graph.add_node(node2)
        
        edge = WorkflowEdge(
            id="e1", source_node_id="n1", source_port="o",
            target_node_id="n2", target_port="i",
        )
        graph.add_edge(edge)
        
        result = graph.get_incoming_edges("n2")
        
        assert len(result) == 1
        assert result[0].id == "e1"

    def test_get_outgoing_edges(self):
        """Test getting outgoing edges for a node."""
        graph = WorkflowGraph()
        
        node1 = WorkflowNode(id="n1", node_type="a")
        node2 = WorkflowNode(id="n2", node_type="b")
        graph.add_node(node1)
        graph.add_node(node2)
        
        edge = WorkflowEdge(
            id="e1", source_node_id="n1", source_port="o",
            target_node_id="n2", target_port="i",
        )
        graph.add_edge(edge)
        
        result = graph.get_outgoing_edges("n1")
        
        assert len(result) == 1
        assert result[0].id == "e1"

    def test_get_source_nodes(self):
        """Test getting source nodes (no incoming edges)."""
        graph = WorkflowGraph()
        
        node1 = WorkflowNode(id="n1", node_type="a")
        node2 = WorkflowNode(id="n2", node_type="b")
        node3 = WorkflowNode(id="n3", node_type="c")
        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_node(node3)
        
        edge = WorkflowEdge(
            id="e1", source_node_id="n1", source_port="o",
            target_node_id="n2", target_port="i",
        )
        graph.add_edge(edge)
        
        result = graph.get_source_nodes()
        
        # n1 and n3 have no incoming edges
        assert len(result) == 2
        ids = {n.id for n in result}
        assert "n1" in ids
        assert "n3" in ids

    def test_get_sink_nodes(self):
        """Test getting sink nodes (no outgoing edges)."""
        graph = WorkflowGraph()
        
        node1 = WorkflowNode(id="n1", node_type="a")
        node2 = WorkflowNode(id="n2", node_type="b")
        node3 = WorkflowNode(id="n3", node_type="c")
        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_node(node3)
        
        edge = WorkflowEdge(
            id="e1", source_node_id="n1", source_port="o",
            target_node_id="n2", target_port="i",
        )
        graph.add_edge(edge)
        
        result = graph.get_sink_nodes()
        
        # n2 and n3 have no outgoing edges
        assert len(result) == 2
        ids = {n.id for n in result}
        assert "n2" in ids
        assert "n3" in ids

    def test_get_execution_order_simple(self):
        """Test execution order for a simple linear graph."""
        graph = WorkflowGraph()
        
        node1 = WorkflowNode(id="n1", node_type="a")
        node2 = WorkflowNode(id="n2", node_type="b")
        node3 = WorkflowNode(id="n3", node_type="c")
        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_node(node3)
        
        edge1 = WorkflowEdge(
            id="e1", source_node_id="n1", source_port="o",
            target_node_id="n2", target_port="i",
        )
        edge2 = WorkflowEdge(
            id="e2", source_node_id="n2", source_port="o",
            target_node_id="n3", target_port="i",
        )
        graph.add_edge(edge1)
        graph.add_edge(edge2)
        
        result = graph.get_execution_order()
        
        # n1 must execute first, then n2, then n3
        assert result[0] == ["n1"]
        assert result[1] == ["n2"]
        assert result[2] == ["n3"]

    def test_get_execution_order_parallel(self):
        """Test execution order with parallel nodes."""
        graph = WorkflowGraph()
        
        node1 = WorkflowNode(id="n1", node_type="a")
        node2 = WorkflowNode(id="n2", node_type="b")
        node3 = WorkflowNode(id="n3", node_type="c")
        node4 = WorkflowNode(id="n4", node_type="d")
        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_node(node3)
        graph.add_node(node4)
        
        # n1 -> n2, n1 -> n3, n2 -> n4, n3 -> n4
        edge1 = WorkflowEdge(
            id="e1", source_node_id="n1", source_port="o",
            target_node_id="n2", target_port="i",
        )
        edge2 = WorkflowEdge(
            id="e2", source_node_id="n1", source_port="o",
            target_node_id="n3", target_port="i",
        )
        edge3 = WorkflowEdge(
            id="e3", source_node_id="n2", source_port="o",
            target_node_id="n4", target_port="i",
        )
        edge4 = WorkflowEdge(
            id="e4", source_node_id="n3", source_port="o",
            target_node_id="n4", target_port="i",
        )
        graph.add_edge(edge1)
        graph.add_edge(edge2)
        graph.add_edge(edge3)
        graph.add_edge(edge4)
        
        result = graph.get_execution_order()
        
        # n1 first, then n2 and n3 in parallel, then n4
        assert result[0] == ["n1"]
        assert set(result[1]) == {"n2", "n3"}
        assert result[2] == ["n4"]

    def test_get_execution_order_with_cycle(self):
        """Test that execution order raises error for cyclic graph."""
        graph = WorkflowGraph()
        
        node1 = WorkflowNode(id="n1", node_type="a")
        node2 = WorkflowNode(id="n2", node_type="b")
        node3 = WorkflowNode(id="n3", node_type="c")
        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_node(node3)
        
        # Create edges: n1 -> n2 -> n3 -> n1 (cycle)
        edge1 = WorkflowEdge(
            id="e1", source_node_id="n1", source_port="o",
            target_node_id="n2", target_port="i",
        )
        edge2 = WorkflowEdge(
            id="e2", source_node_id="n2", source_port="o",
            target_node_id="n3", target_port="i",
        )
        # Add edges directly to bypass cycle check
        graph.edges["e1"] = edge1
        graph.edges["e2"] = edge2
        graph.edges["e3"] = WorkflowEdge(
            id="e3", source_node_id="n3", source_port="o",
            target_node_id="n1", target_port="i",
        )
        
        with pytest.raises(ValueError, match="cycle"):
            graph.get_execution_order()

    def test_get_dependencies(self):
        """Test getting dependencies of a node."""
        graph = WorkflowGraph()
        
        node1 = WorkflowNode(id="n1", node_type="a")
        node2 = WorkflowNode(id="n2", node_type="b")
        node3 = WorkflowNode(id="n3", node_type="c")
        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_node(node3)
        
        edge1 = WorkflowEdge(
            id="e1", source_node_id="n1", source_port="o",
            target_node_id="n2", target_port="i",
        )
        edge2 = WorkflowEdge(
            id="e2", source_node_id="n2", source_port="o",
            target_node_id="n3", target_port="i",
        )
        graph.add_edge(edge1)
        graph.add_edge(edge2)
        
        result = graph.get_dependencies("n3")
        
        assert result == {"n1", "n2"}

    def test_get_dependencies_no_dependencies(self):
        """Test getting dependencies of a source node."""
        graph = WorkflowGraph()
        
        node1 = WorkflowNode(id="n1", node_type="a")
        node2 = WorkflowNode(id="n2", node_type="b")
        graph.add_node(node1)
        graph.add_node(node2)
        
        edge = WorkflowEdge(
            id="e1", source_node_id="n1", source_port="o",
            target_node_id="n2", target_port="i",
        )
        graph.add_edge(edge)
        
        result = graph.get_dependencies("n1")
        
        assert result == set()

    def test_get_dependents(self):
        """Test getting dependents of a node."""
        graph = WorkflowGraph()
        
        node1 = WorkflowNode(id="n1", node_type="a")
        node2 = WorkflowNode(id="n2", node_type="b")
        node3 = WorkflowNode(id="n3", node_type="c")
        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_node(node3)
        
        edge1 = WorkflowEdge(
            id="e1", source_node_id="n1", source_port="o",
            target_node_id="n2", target_port="i",
        )
        edge2 = WorkflowEdge(
            id="e2", source_node_id="n2", source_port="o",
            target_node_id="n3", target_port="i",
        )
        graph.add_edge(edge1)
        graph.add_edge(edge2)
        
        result = graph.get_dependents("n1")
        
        assert result == {"n2", "n3"}

    def test_get_dependents_no_dependents(self):
        """Test getting dependents of a sink node."""
        graph = WorkflowGraph()
        
        node1 = WorkflowNode(id="n1", node_type="a")
        node2 = WorkflowNode(id="n2", node_type="b")
        graph.add_node(node1)
        graph.add_node(node2)
        
        edge = WorkflowEdge(
            id="e1", source_node_id="n1", source_port="o",
            target_node_id="n2", target_port="i",
        )
        graph.add_edge(edge)
        
        result = graph.get_dependents("n2")
        
        assert result == set()

    def test_validate_graph_valid(self):
        """Test validating a valid graph."""
        graph = WorkflowGraph()
        
        node1 = WorkflowNode(id="n1", node_type="a")
        node2 = WorkflowNode(id="n2", node_type="b")
        graph.add_node(node1)
        graph.add_node(node2)
        
        edge = WorkflowEdge(
            id="e1", source_node_id="n1", source_port="o",
            target_node_id="n2", target_port="i",
        )
        graph.add_edge(edge)
        
        errors = graph.validate_graph()
        
        assert errors == []

    def test_validate_graph_disconnected_nodes(self):
        """Test validating a graph with disconnected nodes."""
        graph = WorkflowGraph()
        
        node1 = WorkflowNode(id="n1", node_type="a")
        node2 = WorkflowNode(id="n2", node_type="b")
        node3 = WorkflowNode(id="n3", node_type="c")  # Disconnected
        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_node(node3)
        
        edge = WorkflowEdge(
            id="e1", source_node_id="n1", source_port="o",
            target_node_id="n2", target_port="i",
        )
        graph.add_edge(edge)
        
        errors = graph.validate_graph()
        
        assert len(errors) == 1
        assert "Disconnected" in errors[0]
        assert "n3" in errors[0]

    def test_validate_graph_single_node(self):
        """Test validating a graph with a single node (no disconnected error)."""
        graph = WorkflowGraph()
        
        node = WorkflowNode(id="n1", node_type="a")
        graph.add_node(node)
        
        errors = graph.validate_graph()
        
        # Single node is valid
        assert errors == []

    def test_to_dict(self):
        """Test serializing graph to dictionary."""
        graph = WorkflowGraph(
            id="test-id",
            metadata=WorkflowMetadata(name="Test"),
        )
        node = WorkflowNode(id="n1", node_type="test")
        graph.add_node(node)
        
        result = graph.to_dict()
        
        assert result["id"] == "test-id"
        assert result["metadata"]["name"] == "Test"
        assert "n1" in result["nodes"]

    def test_from_dict(self):
        """Test deserializing graph from dictionary."""
        data = {
            "id": "test-id",
            "metadata": {
                "name": "Test Workflow",
                "description": "Test",
                "version": "1.0.0",
                "author": "",
                "tags": [],
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
            },
            "nodes": {
                "n1": {
                    "id": "n1",
                    "node_type": "test",
                    "position_x": 0,
                    "position_y": 0,
                    "config": {},
                    "label": None,
                    "disabled": False,
                }
            },
            "edges": {},
            "variables": {},
        }
        
        result = WorkflowGraph.from_dict(data)
        
        assert result.id == "test-id"
        assert result.metadata.name == "Test Workflow"
        assert "n1" in result.nodes

    def test_repr(self):
        """Test string representation of graph."""
        graph = WorkflowGraph(
            id="test-id",
            metadata=WorkflowMetadata(name="Test"),
        )
        node = WorkflowNode(id="n1", node_type="test")
        graph.add_node(node)
        
        result = repr(graph)
        
        assert "WorkflowGraph" in result
        assert "test-id" in result
        assert "Test" in result
        assert "nodes=1" in result


class TestWorkflowGraphIntegration:
    """Integration tests for WorkflowGraph."""

    def test_complex_workflow(self):
        """Test a complex workflow with multiple paths."""
        graph = WorkflowGraph()
        
        # Create nodes
        source = WorkflowNode(id="source", node_type="data_source")
        process1 = WorkflowNode(id="process1", node_type="llm_process")
        process2 = WorkflowNode(id="process2", node_type="llm_process")
        aggregator = WorkflowNode(id="aggregator", node_type="ensemble_aggregator")
        sink = WorkflowNode(id="sink", node_type="data_validation")
        
        graph.add_node(source)
        graph.add_node(process1)
        graph.add_node(process2)
        graph.add_node(aggregator)
        graph.add_node(sink)
        
        # Create edges
        graph.add_edge(WorkflowEdge(
            id="e1", source_node_id="source", source_port="out",
            target_node_id="process1", target_port="in",
        ))
        graph.add_edge(WorkflowEdge(
            id="e2", source_node_id="source", source_port="out",
            target_node_id="process2", target_port="in",
        ))
        graph.add_edge(WorkflowEdge(
            id="e3", source_node_id="process1", source_port="out",
            target_node_id="aggregator", target_port="in1",
        ))
        graph.add_edge(WorkflowEdge(
            id="e4", source_node_id="process2", source_port="out",
            target_node_id="aggregator", target_port="in2",
        ))
        graph.add_edge(WorkflowEdge(
            id="e5", source_node_id="aggregator", source_port="out",
            target_node_id="sink", target_port="in",
        ))
        
        # Validate
        errors = graph.validate_graph()
        assert errors == []
        
        # Check execution order
        order = graph.get_execution_order()
        assert order[0] == ["source"]
        assert set(order[1]) == {"process1", "process2"}
        assert order[2] == ["aggregator"]
        assert order[3] == ["sink"]

    def test_disabled_edge_not_in_execution(self):
        """Test that disabled edges are not considered in execution order."""
        graph = WorkflowGraph()
        
        node1 = WorkflowNode(id="n1", node_type="a")
        node2 = WorkflowNode(id="n2", node_type="b")
        node3 = WorkflowNode(id="n3", node_type="c")
        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_node(node3)
        
        edge1 = WorkflowEdge(
            id="e1", source_node_id="n1", source_port="o",
            target_node_id="n2", target_port="i",
        )
        edge2 = WorkflowEdge(
            id="e2", source_node_id="n2", source_port="o",
            target_node_id="n3", target_port="i",
            disabled=True,  # This edge is disabled
        )
        graph.add_edge(edge1)
        graph.add_edge(edge2)
        
        # Execution order should not include n3 after n2 since edge is disabled
        order = graph.get_execution_order()
        
        # n1 and n3 can both start (n3's incoming edge is disabled)
        # Actually, get_execution_order checks edge.disabled, so n3 should be in layer 0 or 1
        # n1 is a source, n3 is also a source (disabled incoming edge)
        # But get_source_nodes doesn't check disabled, so let's check execution order
        layer0 = set(order[0])
        layer1 = set(order[1]) if len(order) > 1 else set()
        
        # n1 should be in first layer (no incoming edges)
        assert "n1" in layer0
        # n2 depends on n1
        assert "n2" in layer1
        # n3's incoming edge is disabled, so it should be in layer 0
        assert "n3" in layer0
