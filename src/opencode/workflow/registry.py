"""
Node Registry for Workflow Engine

This module provides a registry pattern for node types, allowing
dynamic discovery and instantiation of node classes.
"""

from typing import Dict, List, Optional, Type, TypeVar, Callable
import logging

from opencode.workflow.node import BaseNode, NodeSchema

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseNode)


class NodeRegistry:
    """
    Registry for node types.
    
    Provides a central place to register and retrieve node classes.
    Node types can be registered using the @register decorator or
    the register() method.
    
    Example:
        @NodeRegistry.register
        class MyCustomNode(BaseNode):
            ...
            
        # Or explicitly:
        NodeRegistry.register_node(MyCustomNode, "custom_node")
        
        # Retrieve a node class:
        node_class = NodeRegistry.get("my_custom_node")
    """
    
    _nodes: Dict[str, Type[BaseNode]] = {}
    _categories: Dict[str, List[str]] = {}
    
    @classmethod
    def register(cls, name: Optional[str] = None) -> Callable[[Type[BaseNode]], Type[BaseNode]]:
        """
        Decorator to register a node class.
        
        Args:
            name: Optional custom name for the node type.
                  If not provided, uses the class name converted to snake_case.
                  
        Returns:
            Decorator function
            
        Example:
            @NodeRegistry.register()
            class DataSourceNode(BaseNode):
                ...
                
            @NodeRegistry.register("custom_name")
            class MyNode(BaseNode):
                ...
        """
        def decorator(node_class: Type[BaseNode]) -> Type[BaseNode]:
            node_name = name or cls._to_snake_case(node_class.__name__)
            cls.register_node(node_class, node_name)
            return node_class
        return decorator
    
    @classmethod
    def register_node(cls, node_class: Type[BaseNode], name: Optional[str] = None) -> None:
        """
        Register a node class explicitly.
        
        Args:
            node_class: The node class to register
            name: Optional name for the node type. If not provided,
                  uses the class name converted to snake_case.
        """
        node_name = name or cls._to_snake_case(node_class.__name__)
        
        if node_name in cls._nodes:
            logger.warning(f"Overwriting existing node type: {node_name}")
        
        cls._nodes[node_name] = node_class
        
        # Get schema to determine category
        try:
            schema = node_class.get_schema()
            category = schema.category
            if category not in cls._categories:
                cls._categories[category] = []
            if node_name not in cls._categories[category]:
                cls._categories[category].append(node_name)
            logger.debug(f"Registered node type '{node_name}' in category '{category}'")
        except Exception as e:
            logger.warning(f"Could not get schema for node '{node_name}': {e}")
            # Add to default category
            if "general" not in cls._categories:
                cls._categories["general"] = []
            cls._categories["general"].append(node_name)
    
    @classmethod
    def get(cls, name: str) -> Optional[Type[BaseNode]]:
        """
        Get a node class by name.
        
        Args:
            name: The registered name of the node type
            
        Returns:
            The node class, or None if not found
        """
        return cls._nodes.get(name)
    
    @classmethod
    def get_required(cls, name: str) -> Type[BaseNode]:
        """
        Get a node class by name, raising an error if not found.
        
        Args:
            name: The registered name of the node type
            
        Returns:
            The node class
            
        Raises:
            KeyError: If the node type is not registered
        """
        if name not in cls._nodes:
            raise KeyError(f"Node type '{name}' is not registered. "
                          f"Available types: {list(cls._nodes.keys())}")
        return cls._nodes[name]
    
    @classmethod
    def create(cls, name: str, node_id: str, config: Dict) -> BaseNode:
        """
        Create a node instance by type name.
        
        Args:
            name: The registered name of the node type
            node_id: Unique identifier for the node instance
            config: Configuration dictionary for the node
            
        Returns:
            A new node instance
            
        Raises:
            KeyError: If the node type is not registered
        """
        node_class = cls.get_required(name)
        return node_class(node_id=node_id, config=config)
    
    @classmethod
    def list_nodes(cls) -> List[str]:
        """
        List all registered node type names.
        
        Returns:
            List of registered node type names
        """
        return list(cls._nodes.keys())
    
    @classmethod
    def list_categories(cls) -> List[str]:
        """
        List all node categories.
        
        Returns:
            List of category names
        """
        return list(cls._categories.keys())
    
    @classmethod
    def get_nodes_by_category(cls, category: str) -> List[str]:
        """
        Get all node types in a category.
        
        Args:
            category: The category name
            
        Returns:
            List of node type names in the category
        """
        return cls._categories.get(category, [])
    
    @classmethod
    def get_all_schemas(cls) -> Dict[str, NodeSchema]:
        """
        Get schemas for all registered node types.
        
        Returns:
            Dictionary mapping node type names to their schemas
        """
        schemas = {}
        for name, node_class in cls._nodes.items():
            try:
                schemas[name] = node_class.get_schema()
            except Exception as e:
                logger.warning(f"Could not get schema for node '{name}': {e}")
        return schemas
    
    @classmethod
    def unregister(cls, name: str) -> bool:
        """
        Unregister a node type.
        
        Args:
            name: The name of the node type to unregister
            
        Returns:
            True if the node was unregistered, False if it wasn't registered
        """
        if name in cls._nodes:
            node_class = cls._nodes[name]
            del cls._nodes[name]
            
            # Remove from categories
            try:
                schema = node_class.get_schema()
                category = schema.category
                if category in cls._categories and name in cls._categories[category]:
                    cls._categories[category].remove(name)
            except Exception:
                pass
            
            return True
        return False
    
    @classmethod
    def clear(cls) -> None:
        """Clear all registered nodes (useful for testing)."""
        cls._nodes.clear()
        cls._categories.clear()
    
    @staticmethod
    def _to_snake_case(name: str) -> str:
        """Convert CamelCase to snake_case."""
        result = []
        for i, char in enumerate(name):
            if char.isupper() and i > 0:
                result.append('_')
            result.append(char.lower())
        return ''.join(result)


class NodeRegistryError(Exception):
    """Raised when there's an error with the node registry."""
    pass
