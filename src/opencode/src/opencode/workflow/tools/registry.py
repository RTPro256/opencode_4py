"""
Tool Registry for Workflow Engine

This module provides a registry pattern for workflow tools, allowing
dynamic discovery and instantiation of tool classes.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, ClassVar, Callable
from dataclasses import dataclass, field
from datetime import datetime
import logging
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    """
    Result of a tool execution.
    
    Contains the output data and metadata about the execution.
    """
    success: bool = True
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
        }


@dataclass
class ToolSchema:
    """
    Schema definition for a tool.
    
    Describes the tool's parameters and capabilities.
    """
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema for parameters
    required_params: List[str] = field(default_factory=list)
    returns: str = "object"
    category: str = "general"
    requires_auth: bool = False
    auth_type: Optional[str] = None  # e.g., "api_key", "oauth"


class BaseTool(ABC):
    """
    Abstract base class for all workflow tools.
    
    Tools are external integrations that can be used within workflows
    to perform specific operations like web search, API calls, etc.
    
    To implement a new tool:
    1. Subclass BaseTool
    2. Implement the execute() method
    3. Override get_schema() to define parameters
    4. Optionally add authentication handling
    """
    
    # Class-level schema (should be overridden by subclasses)
    _schema: ClassVar[ToolSchema]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a tool instance.
        
        Args:
            config: Configuration dictionary (API keys, settings, etc.)
        """
        self.config = config or {}
        self._initialized = False
    
    @property
    def schema(self) -> ToolSchema:
        """Get the schema for this tool."""
        return self._schema
    
    @classmethod
    @abstractmethod
    def get_schema(cls) -> ToolSchema:
        """
        Return the schema definition for this tool.
        
        Returns:
            ToolSchema describing this tool
        """
        pass
    
    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        """
        Execute the tool's logic.
        
        Args:
            params: Dictionary of tool parameters as defined in schema
            
        Returns:
            ToolResult containing output and status
        """
        pass
    
    def validate_params(self, params: Dict[str, Any]) -> List[str]:
        """
        Validate parameters against the tool's schema.
        
        Args:
            params: Parameters to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        schema = self.get_schema()
        
        for required_param in schema.required_params:
            if required_param not in params:
                errors.append(f"Required parameter '{required_param}' is missing")
        
        return errors
    
    async def initialize(self) -> bool:
        """
        Initialize the tool (e.g., validate API keys, set up connections).
        
        Override this method for tools that need setup.
        
        Returns:
            True if initialization successful
        """
        self._initialized = True
        return True
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


class ToolRegistry:
    """
    Registry for workflow tools.
    
    Provides a central place to register and retrieve tool classes.
    Tools can be registered using the @register decorator or
    the register() method.
    
    Example:
        @ToolRegistry.register()
        class MyCustomTool(BaseTool):
            ...
            
        # Or explicitly:
        ToolRegistry.register_tool(MyCustomTool, "custom_tool")
        
        # Retrieve a tool class:
        tool_class = ToolRegistry.get("my_custom_tool")
        
        # Create and execute a tool:
        tool = ToolRegistry.create("brave_search", config={"api_key": "..."})
        result = await tool.execute(query="Python tutorials")
    """
    
    _tools: Dict[str, Type[BaseTool]] = {}
    _categories: Dict[str, List[str]] = {}
    
    @classmethod
    def register(cls, name: Optional[str] = None) -> Callable[[Type[BaseTool]], Type[BaseTool]]:
        """
        Decorator to register a tool class.
        
        Args:
            name: Optional custom name for the tool.
                  If not provided, uses the class name converted to snake_case.
                  
        Returns:
            Decorator function
        """
        def decorator(tool_class: Type[BaseTool]) -> Type[BaseTool]:
            tool_name = name or cls._to_snake_case(tool_class.__name__)
            cls.register_tool(tool_class, tool_name)
            return tool_class
        return decorator
    
    @classmethod
    def register_tool(cls, tool_class: Type[BaseTool], name: Optional[str] = None) -> None:
        """
        Register a tool class explicitly.
        
        Args:
            tool_class: The tool class to register
            name: Optional name for the tool. If not provided,
                  uses the class name converted to snake_case.
        """
        tool_name = name or cls._to_snake_case(tool_class.__name__)
        
        if tool_name in cls._tools:
            logger.warning(f"Overwriting existing tool: {tool_name}")
        
        cls._tools[tool_name] = tool_class
        
        # Get schema to determine category
        try:
            schema = tool_class.get_schema()
            category = schema.category
            if category not in cls._categories:
                cls._categories[category] = []
            if tool_name not in cls._categories[category]:
                cls._categories[category].append(tool_name)
            logger.debug(f"Registered tool '{tool_name}' in category '{category}'")
        except Exception as e:
            logger.warning(f"Could not get schema for tool '{tool_name}': {e}")
            if "general" not in cls._categories:
                cls._categories["general"] = []
            cls._categories["general"].append(tool_name)
    
    @classmethod
    def get(cls, name: str) -> Optional[Type[BaseTool]]:
        """
        Get a tool class by name.
        
        Args:
            name: The registered name of the tool
            
        Returns:
            The tool class, or None if not found
        """
        return cls._tools.get(name)
    
    @classmethod
    def get_required(cls, name: str) -> Type[BaseTool]:
        """
        Get a tool class by name, raising an error if not found.
        
        Args:
            name: The registered name of the tool
            
        Returns:
            The tool class
            
        Raises:
            KeyError: If the tool is not registered
        """
        if name not in cls._tools:
            raise KeyError(f"Tool '{name}' is not registered. "
                          f"Available tools: {list(cls._tools.keys())}")
        return cls._tools[name]
    
    @classmethod
    def create(cls, name: str, config: Optional[Dict[str, Any]] = None) -> BaseTool:
        """
        Create a tool instance by type name.
        
        Args:
            name: The registered name of the tool
            config: Configuration dictionary for the tool
            
        Returns:
            A new tool instance
            
        Raises:
            KeyError: If the tool is not registered
        """
        tool_class = cls.get_required(name)
        return tool_class(config=config)
    
    @classmethod
    def list_tools(cls) -> List[str]:
        """
        List all registered tool names.
        
        Returns:
            List of registered tool names
        """
        return list(cls._tools.keys())
    
    @classmethod
    def list_categories(cls) -> List[str]:
        """
        List all tool categories.
        
        Returns:
            List of category names
        """
        return list(cls._categories.keys())
    
    @classmethod
    def get_tools_by_category(cls, category: str) -> List[str]:
        """
        Get all tools in a category.
        
        Args:
            category: The category name
            
        Returns:
            List of tool names in the category
        """
        return cls._categories.get(category, [])
    
    @classmethod
    def get_all_schemas(cls) -> Dict[str, ToolSchema]:
        """
        Get schemas for all registered tools.
        
        Returns:
            Dictionary mapping tool names to their schemas
        """
        schemas = {}
        for name, tool_class in cls._tools.items():
            try:
                schemas[name] = tool_class.get_schema()
            except Exception as e:
                logger.warning(f"Could not get schema for tool '{name}': {e}")
        return schemas
    
    @classmethod
    def unregister(cls, name: str) -> bool:
        """
        Unregister a tool.
        
        Args:
            name: The name of the tool to unregister
            
        Returns:
            True if the tool was unregistered, False if it wasn't registered
        """
        if name in cls._tools:
            tool_class = cls._tools[name]
            del cls._tools[name]
            
            # Remove from categories
            try:
                schema = tool_class.get_schema()
                category = schema.category
                if category in cls._categories and name in cls._categories[category]:
                    cls._categories[category].remove(name)
            except Exception:
                pass
            
            return True
        return False
    
    @classmethod
    def clear(cls) -> None:
        """Clear all registered tools (useful for testing)."""
        cls._tools.clear()
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


class ToolRegistryError(Exception):
    """Raised when there's an error with the tool registry."""
    pass


class ToolExecutionError(Exception):
    """Raised when a tool execution fails."""
    pass
