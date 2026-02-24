"""
Base tool interface for agent tools.

Tools are functions that the AI agent can call to interact with the environment,
such as reading files, executing commands, or editing code.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class PermissionLevel(str, Enum):
    """Permission level required to execute a tool."""
    READ = "read"  # Read-only operations
    WRITE = "write"  # File modifications
    EXECUTE = "execute"  # Command execution
    DANGEROUS = "dangerous"  # Potentially harmful operations


@dataclass
class ToolResult:
    """Result of a tool execution."""
    output: str
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    files_changed: list[str] = field(default_factory=list)
    requires_permission: bool = False
    
    @property
    def success(self) -> bool:
        """Check if the tool execution was successful."""
        return self.error is None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata,
            "files_changed": self.files_changed,
            "success": self.success,
        }
    
    @classmethod
    def ok(cls, output: str, **kwargs: Any) -> "ToolResult":
        """Create a successful result."""
        return cls(output=output, **kwargs)
    
    @classmethod
    def err(cls, error: str, output: str = "") -> "ToolResult":
        """Create an error result."""
        return cls(output=output, error=error)


class Tool(ABC):
    """
    Abstract base class for agent tools.
    
    Tools define actions that the AI agent can take, such as:
    - Reading and writing files
    - Executing shell commands
    - Searching code
    - Interacting with LSP servers
    
    Each tool must define:
    - name: Unique identifier for the tool
    - description: Human-readable description for the AI
    - parameters: JSON Schema for the tool's parameters
    - execute: The actual implementation
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name for this tool."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what this tool does."""
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> dict[str, Any]:
        """JSON Schema for the tool's parameters."""
        pass
    
    @property
    def permission_level(self) -> PermissionLevel:
        """Permission level required to execute this tool."""
        return PermissionLevel.READ
    
    @property
    def required_permissions(self) -> list[str]:
        """List of required permissions for this tool."""
        return []
    
    @property
    def is_dangerous(self) -> bool:
        """Whether this tool can cause irreversible changes."""
        return self.permission_level in (PermissionLevel.WRITE, PermissionLevel.EXECUTE, PermissionLevel.DANGEROUS)
    
    @abstractmethod
    async def execute(self, **params: Any) -> ToolResult:
        """
        Execute the tool with the given parameters.
        
        Args:
            **params: Tool parameters as defined in the parameters schema
            
        Returns:
            ToolResult with output, error, and metadata
        """
        pass
    
    def to_openai_tool(self) -> dict[str, Any]:
        """Convert to OpenAI function calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
    
    def to_anthropic_tool(self) -> dict[str, Any]:
        """Convert to Anthropic tool format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }
    
    def validate_params(self, params: dict[str, Any]) -> Optional[str]:
        """
        Validate tool parameters against the schema.
        
        Returns:
            Error message if validation fails, None otherwise
        """
        # Basic validation - check required parameters
        required = self.parameters.get("required", [])
        properties = self.parameters.get("properties", {})
        
        for param in required:
            if param not in params:
                return f"Missing required parameter: {param}"
        
        # Type checking for provided parameters
        for param, value in params.items():
            if param in properties:
                expected_type = properties[param].get("type")
                if expected_type:
                    if not self._check_type(value, expected_type):
                        return f"Parameter '{param}' has wrong type. Expected {expected_type}"
        
        return None
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if a value matches the expected JSON Schema type."""
        type_map = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None),
        }
        
        expected = type_map.get(expected_type)
        if expected is None:
            return True  # Unknown type, skip validation
        
        return isinstance(value, expected)


class ToolRegistry:
    """
    Registry for available tools.
    
    Manages tool registration and lookup by name.
    """
    
    def __init__(self):
        self._tools: dict[str, Tool] = {}
    
    def register(self, tool: Tool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool
    
    def unregister(self, name: str) -> bool:
        """Unregister a tool by name."""
        if name in self._tools:
            del self._tools[name]
            return True
        return False
    
    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def list_tools(self) -> list[Tool]:
        """List all registered tools."""
        return list(self._tools.values())
    
    def get_tools_for_provider(self, provider: str) -> list[dict[str, Any]]:
        """
        Get tools in provider-specific format.
        
        Args:
            provider: Provider name ("openai" or "anthropic")
            
        Returns:
            List of tool definitions in the appropriate format
        """
        tools = []
        for tool in self._tools.values():
            if provider == "anthropic":
                tools.append(tool.to_anthropic_tool())
            else:
                tools.append(tool.to_openai_tool())
        return tools
    
    async def execute(self, name: str, params: dict[str, Any]) -> ToolResult:
        """
        Execute a tool by name.
        
        Args:
            name: Tool name
            params: Tool parameters
            
        Returns:
            ToolResult from the execution
        """
        tool = self.get(name)
        if tool is None:
            return ToolResult.err(f"Unknown tool: {name}")
        
        # Validate parameters
        error = tool.validate_params(params)
        if error:
            return ToolResult.err(error)
        
        # Execute the tool
        try:
            return await tool.execute(**params)
        except Exception as e:
            return ToolResult.err(f"Tool execution failed: {e}")
    
    def __contains__(self, name: str) -> bool:
        return name in self._tools
    
    def __getitem__(self, name: str) -> Tool:
        return self._tools[name]


# Global tool registry
_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """Get the global tool registry."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry


def register_tool(tool: Tool) -> None:
    """Register a tool with the global registry."""
    get_registry().register(tool)


def get_tool(name: str) -> Optional[Tool]:
    """Get a tool from the global registry."""
    return get_registry().get(name)
