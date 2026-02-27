"""
Memory Palace - Knowledge Graph Storage

Provides a knowledge graph for storing and retrieving research information.
Based on Locally-Hosted-LM-Research-Assistant implementation.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Set
from pydantic import BaseModel, Field
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class KnowledgeNode(BaseModel):
    """A node in the knowledge graph"""
    id: str = Field(..., description="Unique node identifier")
    type: str = Field(..., description="Node type (e.g., 'paper', 'model', 'concept')")
    data: Dict[str, Any] = Field(default_factory=dict, description="Node data")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "type": self.type,
            "data": self.data,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class KnowledgeEdge(BaseModel):
    """An edge connecting two nodes"""
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    relation: str = Field(..., description="Relationship type")
    weight: float = Field(1.0, description="Edge weight")
    data: Dict[str, Any] = Field(default_factory=dict, description="Edge metadata")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "source": self.source,
            "target": self.target,
            "relation": self.relation,
            "weight": self.weight,
            "data": self.data,
        }


class MemoryPalace:
    """
    Knowledge graph storage for research information.
    
    Features:
    - Node storage with types
    - Edge relationships
    - Graph traversal
    - Persistence to file
    - Search by type, data, or relation
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize the memory palace.
        
        Args:
            storage_path: Path to persist the knowledge graph
        """
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.edges: List[KnowledgeEdge] = []
        self.storage_path = Path(storage_path) if storage_path else None
        
        # Index for fast lookups
        self._type_index: Dict[str, Set[str]] = {}
        self._outgoing: Dict[str, List[int]] = {}  # node_id -> edge indices
        self._incoming: Dict[str, List[int]] = {}  # node_id -> edge indices
        
        if self.storage_path and self.storage_path.exists():
            self.load()
    
    def add_node(
        self,
        node_id: str,
        node_type: str,
        data: Dict[str, Any],
    ) -> KnowledgeNode:
        """
        Add a node to the knowledge graph.
        
        Args:
            node_id: Unique identifier
            node_type: Type of node
            data: Node data
            
        Returns:
            The created KnowledgeNode
        """
        node = KnowledgeNode(
            id=node_id,
            type=node_type,
            data=data,
        )
        
        self.nodes[node_id] = node
        
        # Update type index
        if node_type not in self._type_index:
            self._type_index[node_type] = set()
        self._type_index[node_type].add(node_id)
        
        logger.debug(f"Added node: {node_id} (type: {node_type})")
        return node
    
    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        """Get a node by ID"""
        return self.nodes.get(node_id)
    
    def update_node(self, node_id: str, data: Dict[str, Any]) -> bool:
        """Update node data"""
        if node_id not in self.nodes:
            return False
        
        node = self.nodes[node_id]
        node.data.update(data)
        node.updated_at = datetime.now().isoformat()
        return True
    
    def delete_node(self, node_id: str) -> bool:
        """Delete a node and its edges"""
        if node_id not in self.nodes:
            return False
        
        node = self.nodes[node_id]
        
        # Remove from type index
        if node.type in self._type_index:
            self._type_index[node.type].discard(node_id)
        
        # Remove edges
        self.edges = [
            e for e in self.edges
            if e.source != node_id and e.target != node_id
        ]
        
        # Rebuild edge indices
        self._rebuild_edge_indices()
        
        del self.nodes[node_id]
        return True
    
    def add_edge(
        self,
        source: str,
        target: str,
        relation: str,
        weight: float = 1.0,
        data: Optional[Dict[str, Any]] = None,
    ) -> Optional[KnowledgeEdge]:
        """
        Add an edge between two nodes.
        
        Args:
            source: Source node ID
            target: Target node ID
            relation: Relationship type
            weight: Edge weight
            data: Edge metadata
            
        Returns:
            The created KnowledgeEdge or None if nodes don't exist
        """
        if source not in self.nodes or target not in self.nodes:
            logger.warning(f"Cannot add edge: node not found")
            return None
        
        edge = KnowledgeEdge(
            source=source,
            target=target,
            relation=relation,
            weight=weight,
            data=data or {},
        )
        
        edge_idx = len(self.edges)
        self.edges.append(edge)
        
        # Update indices
        if source not in self._outgoing:
            self._outgoing[source] = []
        self._outgoing[source].append(edge_idx)
        
        if target not in self._incoming:
            self._incoming[target] = []
        self._incoming[target].append(edge_idx)
        
        logger.debug(f"Added edge: {source} --[{relation}]--> {target}")
        return edge
    
    def get_outgoing_edges(self, node_id: str) -> List[KnowledgeEdge]:
        """Get all outgoing edges from a node"""
        if node_id not in self._outgoing:
            return []
        return [self.edges[i] for i in self._outgoing[node_id]]
    
    def get_incoming_edges(self, node_id: str) -> List[KnowledgeEdge]:
        """Get all incoming edges to a node"""
        if node_id not in self._incoming:
            return []
        return [self.edges[i] for i in self._incoming[node_id]]
    
    def get_neighbors(
        self,
        node_id: str,
        relation: Optional[str] = None,
    ) -> List[KnowledgeNode]:
        """
        Get neighboring nodes.
        
        Args:
            node_id: Node ID
            relation: Filter by relation type (optional)
            
        Returns:
            List of neighboring KnowledgeNodes
        """
        neighbors = []
        
        # Outgoing
        for edge in self.get_outgoing_edges(node_id):
            if relation is None or edge.relation == relation:
                neighbor = self.nodes.get(edge.target)
                if neighbor:
                    neighbors.append(neighbor)
        
        # Incoming
        for edge in self.get_incoming_edges(node_id):
            if relation is None or edge.relation == relation:
                neighbor = self.nodes.get(edge.source)
                if neighbor:
                    neighbors.append(neighbor)
        
        return neighbors
    
    def search_nodes(
        self,
        node_type: Optional[str] = None,
        data_query: Optional[Dict[str, Any]] = None,
    ) -> List[KnowledgeNode]:
        """
        Search for nodes.
        
        Args:
            node_type: Filter by type
            data_query: Filter by data fields
            
        Returns:
            List of matching KnowledgeNodes
        """
        results = []
        
        # Get candidates by type
        if node_type:
            candidates = [
                self.nodes[nid] for nid in self._type_index.get(node_type, set())
            ]
        else:
            candidates = list(self.nodes.values())
        
        # Filter by data query
        for node in candidates:
            if data_query:
                match = all(
                    node.data.get(k) == v
                    for k, v in data_query.items()
                )
                if not match:
                    continue
            results.append(node)
        
        return results
    
    def traverse(
        self,
        start_id: str,
        max_depth: int = 3,
        relations: Optional[List[str]] = None,
    ) -> Dict[str, KnowledgeNode]:
        """
        Traverse the graph from a starting node.
        
        Args:
            start_id: Starting node ID
            max_depth: Maximum traversal depth
            relations: Filter by relation types
            
        Returns:
            Dictionary of visited nodes
        """
        visited: Dict[str, KnowledgeNode] = {}
        queue = [(start_id, 0)]
        
        while queue:
            node_id, depth = queue.pop(0)
            
            if node_id in visited or depth > max_depth:
                continue
            
            node = self.nodes.get(node_id)
            if not node:
                continue
            
            visited[node_id] = node
            
            # Add neighbors to queue
            for edge in self.get_outgoing_edges(node_id):
                if relations and edge.relation not in relations:
                    continue
                if edge.target not in visited:
                    queue.append((edge.target, depth + 1))
            
            for edge in self.get_incoming_edges(node_id):
                if relations and edge.relation not in relations:
                    continue
                if edge.source not in visited:
                    queue.append((edge.source, depth + 1))
        
        return visited
    
    def save(self) -> bool:
        """Save the knowledge graph to file"""
        if not self.storage_path:
            return False
        
        try:
            data = {
                "nodes": {nid: n.to_dict() for nid, n in self.nodes.items()},
                "edges": [e.to_dict() for e in self.edges],
            }
            
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved knowledge graph to {self.storage_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save: {e}")
            return False
    
    def load(self) -> bool:
        """Load the knowledge graph from file"""
        if not self.storage_path or not self.storage_path.exists():
            return False
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            self.nodes = {
                nid: KnowledgeNode(**ndata)
                for nid, ndata in data.get("nodes", {}).items()
            }
            self.edges = [KnowledgeEdge(**edata) for edata in data.get("edges", [])]
            
            self._rebuild_indices()
            
            logger.info(f"Loaded knowledge graph from {self.storage_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load: {e}")
            return False
    
    def _rebuild_indices(self):
        """Rebuild all indices"""
        self._rebuild_type_index()
        self._rebuild_edge_indices()
    
    def _rebuild_type_index(self):
        """Rebuild the type index"""
        self._type_index = {}
        for nid, node in self.nodes.items():
            if node.type not in self._type_index:
                self._type_index[node.type] = set()
            self._type_index[node.type].add(nid)
    
    def _rebuild_edge_indices(self):
        """Rebuild edge indices"""
        self._outgoing = {}
        self._incoming = {}
        
        for i, edge in enumerate(self.edges):
            if edge.source not in self._outgoing:
                self._outgoing[edge.source] = []
            self._outgoing[edge.source].append(i)
            
            if edge.target not in self._incoming:
                self._incoming[edge.target] = []
            self._incoming[edge.target].append(i)
    
    def to_dict(self) -> Dict[str, Any]:
        """Export the entire graph as a dictionary"""
        return {
            "nodes": {nid: n.to_dict() for nid, n in self.nodes.items()},
            "edges": [e.to_dict() for e in self.edges],
        }
    
    def __len__(self) -> int:
        """Return number of nodes"""
        return len(self.nodes)
    
    def __contains__(self, node_id: str) -> bool:
        """Check if node exists"""
        return node_id in self.nodes
