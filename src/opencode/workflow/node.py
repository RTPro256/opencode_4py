"""
Base Node Classes for Workflow Engine

This module provides the abstract base class for all workflow nodes,
including port definitions and schema management.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Type, ClassVar
from pydantic import BaseModel, Field
from datetime import datetime


class PortDirection(str, Enum):
    """Direction of a node port (input or output)."""
    INPUT = "input"
    OUTPUT = "output"


class PortDataType(str, Enum):
    """Supported data types for node ports."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"
    ANY = "any"
    BINARY = "binary"
    STREAM = "stream"


class NodePort(BaseModel):
    """
    Defines a port on a node for data input/output.
    
    Ports are connection points that allow data to flow between nodes.
    """
    name: str = Field(..., description="Unique name for this port within the node")
    data_type: PortDataType = Field(default=PortDataType.ANY, description="Data type this port accepts/produces")
    direction: PortDirection = Field(..., description="Whether this is an input or output port")
    required: bool = Field(default=True, description="Whether this port must be connected")
    description: str = Field(default="", description="Human-readable description of the port")
    default_value: Optional[Any] = Field(default=None, description="Default value if not connected")
    json_schema: Optional[Dict[str, Any]] = Field(default=None, description="JSON schema for complex types")

    class Config:
        use_enum_values = True


class NodeSchema(BaseModel):
    """
    Schema definition for a node type.
    
    Describes the configuration options, inputs, and outputs of a node.
    """
    node_type: str = Field(..., description="Unique identifier for this node type")
    display_name: str = Field(..., description="Human-readable name")
    description: str = Field(default="", description="Description of what this node does")
    category: str = Field(default="general", description="Category for organization in UI")
    icon: str = Field(default="cube", description="Icon name for UI display")
    inputs: List[NodePort] = Field(default_factory=list, description="Input port definitions")
    outputs: List[NodePort] = Field(default_factory=list, description="Output port definitions")
    config_schema: Dict[str, Any] = Field(default_factory=dict, description="JSON schema for node configuration")
    version: str = Field(default="1.0.0", description="Node type version")


class ExecutionContext(BaseModel):
    """
    Runtime context provided to nodes during execution.
    
    Contains information about the current execution state and utilities.
    """
    workflow_id: str = Field(..., description="ID of the workflow being executed")
    execution_id: str = Field(..., description="Unique ID for this execution run")
    node_id: str = Field(..., description="ID of the current node")
    started_at: datetime = Field(default_factory=datetime.utcnow, description="When execution started")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Workflow-level variables")
    parent_node_id: Optional[str] = Field(default=None, description="Parent node ID for nested executions")
    depth: int = Field(default=0, description="Nesting depth in execution tree")

    class Config:
        arbitrary_types_allowed = True


class ExecutionResult(BaseModel):
    """
    Result of a node execution.
    
    Contains the output data and metadata about the execution.
    """
    success: bool = Field(default=True, description="Whether execution succeeded")
    outputs: Dict[str, Any] = Field(default_factory=dict, description="Output data by port name")
    error: Optional[str] = Field(default=None, description="Error message if execution failed")
    error_traceback: Optional[str] = Field(default=None, description="Full traceback if available")
    duration_ms: Optional[float] = Field(default=None, description="Execution duration in milliseconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional execution metadata")


class BaseNode(ABC):
    """
    Abstract base class for all workflow nodes.
    
    Nodes are the building blocks of workflows. Each node performs a specific
    operation and can be connected to other nodes via ports.
    
    To implement a new node type:
    1. Subclass BaseNode
    2. Implement the execute() method
    3. Override get_schema() to define ports and configuration
    4. Optionally override validate_inputs() for custom validation
    """
    
    # Class-level schema (should be overridden by subclasses)
    _schema: ClassVar[NodeSchema]
    
    def __init__(self, node_id: str, config: Dict[str, Any]):
        """
        Initialize a node instance.
        
        Args:
            node_id: Unique identifier for this node instance
            config: Configuration dictionary for this node
        """
        self.node_id = node_id
        self.config = config
        self.inputs: Dict[str, Any] = {}
        self.outputs: Dict[str, Any] = {}
        self._execution_context: Optional[ExecutionContext] = None
    
    @property
    def schema(self) -> NodeSchema:
        """Get the schema for this node type."""
        return self._schema
    
    @classmethod
    @abstractmethod
    def get_schema(cls) -> NodeSchema:
        """
        Return the schema definition for this node type.
        
        This must be implemented by all node subclasses to define
        their inputs, outputs, and configuration options.
        
        Returns:
            NodeSchema describing this node type
        """
        pass
    
    @abstractmethod
    async def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> ExecutionResult:
        """
        Execute the node's logic.
        
        This is the main method that performs the node's operation.
        It should be implemented by all node subclasses.
        
        Args:
            inputs: Dictionary of input values keyed by port name
            context: Execution context with workflow information
            
        Returns:
            ExecutionResult containing outputs and status
        """
        pass
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> List[str]:
        """
        Validate input values against the node's input schema.
        
        Override this method to add custom validation logic.
        
        Args:
            inputs: Dictionary of input values to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        schema = self.get_schema()
        
        for port in schema.inputs:
            if port.required and port.name not in inputs:
                if port.default_value is None:
                    errors.append(f"Required input '{port.name}' is missing")
                else:
                    inputs[port.name] = port.default_value
        
        return errors
    
    def validate_config(self) -> List[str]:
        """
        Validate the node's configuration.
        
        Override this method to add custom configuration validation.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        # Basic validation - can be extended with JSON schema validation
        return errors
    
    def get_input_port(self, name: str) -> Optional[NodePort]:
        """Get an input port by name."""
        schema = self.get_schema()
        for port in schema.inputs:
            if port.name == name:
                return port
        return None
    
    def get_output_port(self, name: str) -> Optional[NodePort]:
        """Get an output port by name."""
        schema = self.get_schema()
        for port in schema.outputs:
            if port.name == name:
                return port
        return None
    
    def set_execution_context(self, context: ExecutionContext) -> None:
        """Set the execution context for this node."""
        self._execution_context = context
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(node_id={self.node_id!r})"


class NodeConfigurationError(Exception):
    """Raised when a node has invalid configuration."""
    pass


class NodeExecutionError(Exception):
    """Raised when a node execution fails."""
    pass


class NodeValidationError(Exception):
    """Raised when node input validation fails."""
    pass
