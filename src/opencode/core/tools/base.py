"""
Base tool classes and registry.

Refactored from Roo-Code's tool system patterns.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional, TypeVar, Generic
import asyncio
from pathlib import Path


class ToolStatus(Enum):
    """Status of tool execution."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class ToolResult:
    """Result of a tool execution."""
    success: bool
    output: str
    error: Optional[str] = None
    data: dict[str, Any] = field(default_factory=dict)
    images: list[str] = field(default_factory=list)  # Base64 encoded images
    
    @classmethod
    def success_result(cls, output: str, **kwargs) -> "ToolResult":
        """Create a successful result."""
        return cls(success=True, output=output, **kwargs)
    
    @classmethod
    def error_result(cls, error: str, output: str = "") -> "ToolResult":
        """Create an error result."""
        return cls(success=False, output=output, error=error)


@dataclass
class ToolCallbacks:
    """Callbacks passed to tool execution."""
    ask_approval: Callable[[str, str], asyncio.Future]  # (message, default) -> approved
    handle_error: Callable[[str, Exception], asyncio.Future]  # (context, error) -> None
    push_tool_result: Callable[[str], None]  # (result) -> None
    tool_call_id: Optional[str] = None


@dataclass
class ToolUse:
    """Represents a tool use block from the assistant."""
    name: str
    params: dict[str, Any]
    partial: bool = False
    native_args: Optional[dict[str, Any]] = None
    tool_call_id: Optional[str] = None


T = TypeVar("T")


class BaseTool(ABC, Generic[T]):
    """
    Abstract base class for all tools.
    
    Tools receive typed arguments from native tool calling.
    Inspired by Roo-Code's BaseTool pattern.
    
    Attributes:
        name: Unique identifier for the tool
        description: Human-readable description for the LLM
    """
    
    name: str = "base_tool"
    description: str = "Base tool class"
    
    def __init__(self):
        """Initialize the tool."""
        self._last_seen_partial_path: Optional[str] = None
    
    @abstractmethod
    async def execute(
        self,
        params: T,
        callbacks: ToolCallbacks,
    ) -> ToolResult:
        """
        Execute the tool with typed parameters.
        
        Must be implemented by subclasses.
        
        Args:
            params: Typed parameters from native tool calling
            callbacks: Tool execution callbacks
            
        Returns:
            ToolResult with execution outcome
        """
        pass
    
    async def handle_partial(
        self,
        block: ToolUse,
        callbacks: ToolCallbacks,
    ) -> None:
        """
        Handle partial (streaming) tool messages.
        
        Override to show streaming UI updates.
        Default implementation does nothing.
        """
        pass
    
    def has_path_stabilized(self, path: Optional[str]) -> bool:
        """
        Check if a path parameter has stabilized during streaming.
        
        During native tool call streaming, partial values may be truncated.
        This method tracks the path value and returns true only when
        the path has stopped changing.
        
        Args:
            path: The current path value from the partial block
            
        Returns:
            True if path has stabilized and is non-empty
        """
        path_stabilized = (
            self._last_seen_partial_path is not None
            and self._last_seen_partial_path == path
        )
        self._last_seen_partial_path = path
        return path_stabilized and bool(path)
    
    def reset_partial_state(self) -> None:
        """Reset partial state tracking."""
        self._last_seen_partial_path = None
    
    async def handle(
        self,
        block: ToolUse,
        callbacks: ToolCallbacks,
    ) -> ToolResult:
        """
        Main entry point for tool execution.
        
        Handles the complete flow:
        1. Partial message handling (if partial)
        2. Parameter parsing
        3. Core execution
        
        Args:
            block: ToolUse block from assistant message
            callbacks: Tool execution callbacks
            
        Returns:
            ToolResult with execution outcome
        """
        # Handle partial messages
        if block.partial:
            try:
                await self.handle_partial(block, callbacks)
            except Exception as e:
                await callbacks.handle_error(
                    f"handling partial {self.name}",
                    e if isinstance(e, Exception) else Exception(str(e)),
                )
            return ToolResult(success=True, output="")  # Empty result for partial
        
        # Get typed parameters
        params: T
        if block.native_args is not None:
            params = block.native_args  # type: ignore
        elif block.params:
            params = block.params  # type: ignore
        else:
            return ToolResult.error_result(
                "Tool call is missing arguments",
            )
        
        # Execute with typed parameters
        try:
            result = await self.execute(params, callbacks)
            return result
        except Exception as e:
            return ToolResult.error_result(str(e))
        finally:
            self.reset_partial_state()
    
    @classmethod
    def get_schema(cls) -> dict[str, Any]:
        """Get the JSON schema for this tool."""
        return {
            "name": cls.name,
            "description": cls.description,
            "parameters": cls.get_parameters_schema(),
        }
    
    @classmethod
    def get_parameters_schema(cls) -> dict[str, Any]:
        """Get the JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }


class ToolRegistry:
    """
    Registry for managing available tools.
    """
    
    _instance: Optional["ToolRegistry"] = None
    _tools: dict[str, type[BaseTool]] = {}
    
    def __new__(cls) -> "ToolRegistry":
        """Singleton pattern for global registry."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def register(cls, tool_class: type[BaseTool]) -> type[BaseTool]:
        """
        Register a tool class.
        
        Can be used as a decorator.
        """
        cls._tools[tool_class.name] = tool_class
        return tool_class
    
    @classmethod
    def get(cls, name: str) -> Optional[type[BaseTool]]:
        """Get a tool class by name."""
        return cls._tools.get(name)
    
    @classmethod
    def list_tools(cls) -> list[dict[str, Any]]:
        """List all registered tools."""
        return [tool_class.get_schema() for tool_class in cls._tools.values()]
    
    @classmethod
    def create(cls, name: str) -> Optional[BaseTool]:
        """Create an instance of a tool by name."""
        tool_class = cls.get(name)
        if tool_class:
            return tool_class()
        return None
    
    @classmethod
    def clear(cls) -> None:
        """Clear all registered tools (for testing)."""
        cls._tools.clear()
