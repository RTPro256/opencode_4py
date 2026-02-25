"""
Workflow Graph Module

This module provides the DAG (Directed Acyclic Graph) representation
of workflows, including nodes, edges, and graph operations.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)


class WorkflowNode(BaseModel):
    """
    Represents a node instance in a workflow graph.
    
    Contains the node's position, configuration, and connection points.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique node instance ID")
    node_type: str = Field(..., description="Type of node (e.g., 'data_source', 'llm_process')")
    position_x: float = Field(default=0, description="X position in visual editor")
    position_y: float = Field(default=0, description="Y position in visual editor")
    config: Dict[str, Any] = Field(default_factory=dict, description="Node configuration")
    label: Optional[str] = Field(default=None, description="Optional display label")
    disabled: bool = Field(default=False, description="Whether this node is disabled")

    class Config:
        extra = "allow"


class WorkflowEdge(BaseModel):
    """
    Represents a connection between two nodes in a workflow.
    
    Edges define data flow from one node's output port to another node's input port.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique edge ID")
    source_node_id: str = Field(..., description="ID of the source node")
    source_port: str = Field(..., description="Name of the output port on source node")
    target_node_id: str = Field(..., description="ID of the target node")
    target_port: str = Field(..., description="Name of the input port on target node")
    label: Optional[str] = Field(default=None, description="Optional edge label")
    disabled: bool = Field(default=False, description="Whether this edge is disabled")

    class Config:
        extra = "allow"


class WorkflowMetadata(BaseModel):
    """Metadata for a workflow."""
    name: str = Field(default="Untitled Workflow", description="Workflow name")
    description: str = Field(default="", description="Workflow description")
    version: str = Field(default="1.0.0", description="Workflow version")
    author: str = Field(default="", description="Workflow author")
    tags: List[str] = Field(default_factory=list, description="Tags for organization")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")


class WorkflowGraph(BaseModel):
    """
    Represents a complete workflow as a directed acyclic graph.
    
    A workflow consists of nodes connected by edges, forming a DAG
    that defines the execution order and data flow.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique workflow ID")
    metadata: WorkflowMetadata = Field(default_factory=WorkflowMetadata, description="Workflow metadata")
    nodes: Dict[str, WorkflowNode] = Field(default_factory=dict, description="Nodes keyed by ID")
    edges: Dict[str, WorkflowEdge] = Field(default_factory=dict, description="Edges keyed by ID")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Workflow-level variables")
    
    class Config:
        arbitrary_types_allowed = True

    def add_node(self, node: WorkflowNode) -> str:
        """
        Add a node to the workflow.
        
        Args:
            node: The WorkflowNode to add
            
        Returns:
            The node's ID
        """
        self.nodes[node.id] = node
        self._touch()
        return node.id

    def remove_node(self, node_id: str) -> bool:
        """
        Remove a node and all connected edges from the workflow.
        
        Args:
            node_id: ID of the node to remove
            
        Returns:
            True if the node was removed, False if not found
        """
        if node_id not in self.nodes:
            return False
        
        # Remove connected edges
        edges_to_remove = [
            edge_id for edge_id, edge in self.edges.items()
            if edge.source_node_id == node_id or edge.target_node_id == node_id
        ]
        for edge_id in edges_to_remove:
            del self.edges[edge_id]
        
        del self.nodes[node_id]
        self._touch()
        return True

    def add_edge(self, edge: WorkflowEdge) -> Tuple[bool, Optional[str]]:
        """
        Add an edge to the workflow.
        
        Args:
            edge: The WorkflowEdge to add
            
        Returns:
            Tuple of (success, error_message)
        """
        # Validate nodes exist
        if edge.source_node_id not in self.nodes:
            return False, f"Source node '{edge.source_node_id}' not found"
        if edge.target_node_id not in self.nodes:
            return False, f"Target node '{edge.target_node_id}' not found"
        
        # Check for cycles
        if self._would_create_cycle(edge):
            return False, "Edge would create a cycle in the workflow"
        
        self.edges[edge.id] = edge
        self._touch()
        return True, None

    def remove_edge(self, edge_id: str) -> bool:
        """
        Remove an edge from the workflow.
        
        Args:
            edge_id: ID of the edge to remove
            
        Returns:
            True if removed, False if not found
        """
        if edge_id in self.edges:
            del self.edges[edge_id]
            self._touch()
            return True
        return False

    def get_node(self, node_id: str) -> Optional[WorkflowNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)

    def get_edge(self, edge_id: str) -> Optional[WorkflowEdge]:
        """Get an edge by ID."""
        return self.edges.get(edge_id)

    def get_edges_for_node(self, node_id: str) -> Tuple[List[WorkflowEdge], List[WorkflowEdge]]:
        """
        Get all edges connected to a node.
        
        Args:
            node_id: ID of the node
            
        Returns:
            Tuple of (incoming_edges, outgoing_edges)
        """
        incoming = []
        outgoing = []
        for edge in self.edges.values():
            if edge.target_node_id == node_id:
                incoming.append(edge)
            if edge.source_node_id == node_id:
                outgoing.append(edge)
        return incoming, outgoing

    def get_incoming_edges(self, node_id: str) -> List[WorkflowEdge]:
        """Get all edges where this node is the target."""
        return [e for e in self.edges.values() if e.target_node_id == node_id]

    def get_outgoing_edges(self, node_id: str) -> List[WorkflowEdge]:
        """Get all edges where this node is the source."""
        return [e for e in self.edges.values() if e.source_node_id == node_id]

    def get_source_nodes(self) -> List[WorkflowNode]:
        """
        Get all source nodes (nodes with no incoming edges).
        
        These are the entry points for workflow execution.
        """
        target_ids = {e.target_node_id for e in self.edges.values()}
        return [n for n in self.nodes.values() if n.id not in target_ids]

    def get_sink_nodes(self) -> List[WorkflowNode]:
        """
        Get all sink nodes (nodes with no outgoing edges).
        
        These are the terminal points for workflow execution.
        """
        source_ids = {e.source_node_id for e in self.edges.values()}
        return [n for n in self.nodes.values() if n.id not in source_ids]

    def get_execution_order(self) -> List[List[str]]:
        """
        Get the topological execution order of nodes.
        
        Returns:
            List of layers, where each layer is a list of node IDs
            that can be executed in parallel.
            
        Raises:
            ValueError: If the graph contains a cycle
        """
        # Kahn's algorithm for topological sort with layer tracking
        in_degree = {node_id: 0 for node_id in self.nodes}
        
        for edge in self.edges.values():
            if not edge.disabled:
                in_degree[edge.target_node_id] += 1
        
        layers = []
        remaining = set(in_degree.keys())
        
        while remaining:
            # Find all nodes with in-degree 0
            layer = [nid for nid in remaining if in_degree[nid] == 0]
            
            if not layer:
                # Cycle detected
                raise ValueError("Workflow contains a cycle - cannot determine execution order")
            
            layers.append(layer)
            
            # Remove processed nodes and update in-degrees
            for node_id in layer:
                remaining.remove(node_id)
                for edge in self.edges.values():
                    if edge.source_node_id == node_id and not edge.disabled:
                        in_degree[edge.target_node_id] -= 1
        
        return layers

    def get_dependencies(self, node_id: str) -> Set[str]:
        """
        Get all nodes that must complete before this node can execute.
        
        Args:
            node_id: ID of the node
            
        Returns:
            Set of node IDs that are dependencies
        """
        dependencies = set()
        to_visit = list(self.get_incoming_edges(node_id))
        
        while to_visit:
            edge = to_visit.pop()
            if edge.source_node_id not in dependencies:
                dependencies.add(edge.source_node_id)
                to_visit.extend(self.get_incoming_edges(edge.source_node_id))
        
        return dependencies

    def get_dependents(self, node_id: str) -> Set[str]:
        """
        Get all nodes that depend on this node.
        
        Args:
            node_id: ID of the node
            
        Returns:
            Set of node IDs that depend on this node
        """
        dependents = set()
        to_visit = list(self.get_outgoing_edges(node_id))
        
        while to_visit:
            edge = to_visit.pop()
            if edge.target_node_id not in dependents:
                dependents.add(edge.target_node_id)
                to_visit.extend(self.get_outgoing_edges(edge.target_node_id))
        
        return dependents

    def validate_graph(self) -> List[str]:
        """
        Validate the workflow graph.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check for cycles
        try:
            self.get_execution_order()
        except ValueError as e:
            errors.append(str(e))
        
        # Check for disconnected nodes
        if len(self.nodes) > 1:
            connected_nodes = set()
            for edge in self.edges.values():
                connected_nodes.add(edge.source_node_id)
                connected_nodes.add(edge.target_node_id)
            
            disconnected = set(self.nodes.keys()) - connected_nodes
            if disconnected:
                errors.append(f"Disconnected nodes found: {disconnected}")
        
        # Check for multiple source nodes (valid but worth noting)
        source_nodes = self.get_source_nodes()
        if len(source_nodes) > 1:
            logger.info(f"Workflow has multiple entry points: {[n.id for n in source_nodes]}")
        
        return errors

    def _would_create_cycle(self, new_edge: WorkflowEdge) -> bool:
        """Check if adding this edge would create a cycle."""
        # DFS to check if target can reach source
        visited = set()
        stack = [new_edge.target_node_id]
        
        while stack:
            current = stack.pop()
            if current == new_edge.source_node_id:
                return True
            if current in visited:
                continue
            visited.add(current)
            
            for edge in self.edges.values():
                if edge.source_node_id == current:
                    stack.append(edge.target_node_id)
        
        return False

    def _touch(self) -> None:
        """Update the modified timestamp."""
        self.metadata.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the workflow to a dictionary."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowGraph":
        """Deserialize a workflow from a dictionary."""
        return cls.model_validate(data)

    def __repr__(self) -> str:
        return f"WorkflowGraph(id={self.id!r}, name={self.metadata.name!r}, nodes={len(self.nodes)}, edges={len(self.edges)})"
