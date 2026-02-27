"""
Tool Node

Handles external tool execution for workflows.
"""

import json
from typing import Any, Dict, Optional
import logging

from opencode.workflow.node import (
    BaseNode,
    NodePort,
    NodeSchema,
    ExecutionContext,
    ExecutionResult,
    PortDataType,
    PortDirection,
)
from opencode.workflow.registry import NodeRegistry

logger = logging.getLogger(__name__)


@NodeRegistry.register("tool")
class ToolNode(BaseNode):
    """
    Tool Node - External tool execution.
    
    This node executes external tools and returns the results.
    It integrates with the existing opencode tool system.
    
    Configuration:
        toolName: Name of the tool to execute
        toolArgs: Arguments to pass to the tool
        timeout: Execution timeout in seconds
    """
    
    _schema = NodeSchema(
        node_type="tool",
        display_name="Tool",
        description="Execute external tools",
        category="action",
        icon="wrench",
        inputs=[
            NodePort(
                name="args",
                data_type=PortDataType.OBJECT,
                direction=PortDirection.INPUT,
                required=False,
                description="Tool arguments (overrides config)",
            ),
            NodePort(
                name="input",
                data_type=PortDataType.ANY,
                direction=PortDirection.INPUT,
                required=False,
                description="Input data for the tool",
            ),
        ],
        outputs=[
            NodePort(
                name="result",
                data_type=PortDataType.ANY,
                direction=PortDirection.OUTPUT,
                required=True,
                description="Tool execution result",
            ),
            NodePort(
                name="success",
                data_type=PortDataType.BOOLEAN,
                direction=PortDirection.OUTPUT,
                required=True,
                description="Whether execution succeeded",
            ),
            NodePort(
                name="error",
                data_type=PortDataType.STRING,
                direction=PortDirection.OUTPUT,
                required=False,
                description="Error message if failed",
            ),
        ],
        config_schema={
            "type": "object",
            "properties": {
                "toolName": {
                    "type": "string",
                    "description": "Name of the tool to execute",
                },
                "toolArgs": {
                    "type": "object",
                    "description": "Arguments to pass to the tool",
                },
                "timeout": {
                    "type": "integer",
                    "default": 60,
                    "description": "Execution timeout in seconds",
                },
            },
            "required": ["toolName"],
        },
        version="1.0.0",
    )
    
    @classmethod
    def get_schema(cls) -> NodeSchema:
        return cls._schema
    
    async def execute(
        self,
        inputs: Dict[str, Any],
        context: ExecutionContext,
    ) -> ExecutionResult:
        """Execute the tool node."""
        import time
        start_time = time.time()
        
        try:
            tool_name = self.config.get("toolName")
            if not tool_name:
                return ExecutionResult(
                    success=False,
                    error="toolName is required",
                )
            
            # Get tool arguments
            tool_args = dict(self.config.get("toolArgs", {}))
            if inputs.get("args"):
                tool_args.update(inputs["args"])
            
            # Add input if provided
            if "input" in inputs:
                tool_args["input"] = inputs["input"]
            
            # Get the tool
            tool = await self._get_tool(tool_name)
            
            if tool is None:
                return ExecutionResult(
                    success=False,
                    error=f"Tool '{tool_name}' not found",
                )
            
            # Execute the tool
            try:
                result = await self._execute_tool(tool, tool_args)
                
                duration_ms = (time.time() - start_time) * 1000
                return ExecutionResult(
                    success=True,
                    outputs={
                        "result": result,
                        "success": True,
                        "error": None,
                    },
                    duration_ms=duration_ms,
                )
            except Exception as e:
                logger.exception(f"Tool execution failed: {e}")
                return ExecutionResult(
                    success=False,
                    outputs={
                        "result": None,
                        "success": False,
                        "error": str(e),
                    },
                    error=str(e),
                )
            
        except Exception as e:
            logger.exception(f"Tool node execution failed: {e}")
            return ExecutionResult(
                success=False,
                error=str(e),
            )
    
    async def _get_tool(self, tool_name: str):
        """Get a tool by name from the tool registry."""
        try:
            # Try to import from the tool module
            from opencode.tool import get_tool
            return get_tool(tool_name)
        except ImportError:
            # Fallback: try direct import
            try:
                if tool_name == "bash":
                    from opencode.tool.bash import BashTool
                    return BashTool()
                elif tool_name == "file_read":
                    from opencode.tool.file_tools import ReadFileTool
                    return ReadFileTool()
                elif tool_name == "file_write":
                    from opencode.tool.file_tools import WriteFileTool
                    return WriteFileTool()
                elif tool_name == "web_search":
                    from opencode.tool.websearch import WebSearchTool
                    return WebSearchTool()
                elif tool_name == "web_fetch":
                    from opencode.tool.webfetch import WebFetchTool
                    return WebFetchTool()
                else:
                    logger.warning(f"Unknown tool: {tool_name}")
                    return None
            except Exception as e:
                logger.error(f"Failed to load tool {tool_name}: {e}")
                return None
        except Exception as e:
            logger.error(f"Failed to get tool {tool_name}: {e}")
            return None
    
    async def _execute_tool(self, tool, args: Dict[str, Any]) -> Any:
        """Execute a tool with the given arguments."""
        import asyncio
        
        timeout = self.config.get("timeout", 60)
        
        # Check if tool has an execute method
        if hasattr(tool, "execute"):
            if asyncio.iscoroutinefunction(tool.execute):
                result = await asyncio.wait_for(
                    tool.execute(**args),
                    timeout=timeout
                )
            else:
                result = tool.execute(**args)
        elif hasattr(tool, "run"):
            if asyncio.iscoroutinefunction(tool.run):
                result = await asyncio.wait_for(
                    tool.run(**args),
                    timeout=timeout
                )
            else:
                result = tool.run(**args)
        elif callable(tool):
            result = tool(**args)
        else:
            raise ValueError(f"Tool has no execute method")
        
        return result
