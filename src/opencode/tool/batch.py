"""
Batch tool for executing multiple tool calls in parallel.

This tool allows the AI to execute multiple independent tool calls
simultaneously, improving efficiency for operations that don't depend
on each other.
"""

import asyncio
from typing import Any, Optional
from dataclasses import dataclass

from opencode.tool.base import Tool, ToolResult, get_registry


# Tools that cannot be used in batch mode
DISALLOWED_TOOLS = {"batch"}

# Tools to filter from suggestions
FILTERED_FROM_SUGGESTIONS = {"invalid", "patch", "batch"}


@dataclass
class BatchResult:
    """Result of a single tool call in a batch."""
    tool: str
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class BatchTool(Tool):
    """Tool for executing multiple tool calls in parallel."""
    
    @property
    def name(self) -> str:
        return "batch"
    
    @property
    def description(self) -> str:
        return """Execute multiple tool calls in parallel for improved efficiency.

This tool allows you to execute multiple independent tool calls simultaneously.
Use this when you have multiple operations that don't depend on each other's results.

Benefits:
- Faster execution through parallelism
- Reduced round-trips for independent operations
- Better performance for bulk operations

Limitations:
- Maximum 25 tool calls per batch
- Cannot batch the 'batch' tool itself
- External tools (MCP, environment) cannot be batched

Example usage:
{
  "tool_calls": [
    {"tool": "read", "parameters": {"path": "file1.py"}},
    {"tool": "read", "parameters": {"path": "file2.py"}},
    {"tool": "glob", "parameters": {"pattern": "**/*.ts"}}
  ]
}"""
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "tool_calls": {
                    "type": "array",
                    "description": "Array of tool calls to execute in parallel",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "properties": {
                            "tool": {
                                "type": "string",
                                "description": "The name of the tool to execute",
                            },
                            "parameters": {
                                "type": "object",
                                "description": "Parameters for the tool",
                                "additionalProperties": True,
                            },
                        },
                        "required": ["tool", "parameters"],
                    },
                },
            },
            "required": ["tool_calls"],
        }
    
    async def execute(self, **params: Any) -> ToolResult:
        """Execute the batch of tool calls."""
        tool_calls = params.get("tool_calls", [])
        
        if not tool_calls:
            return ToolResult.err("Provide at least one tool call")
        
        # Limit to 25 calls
        max_calls = 25
        executed_calls = tool_calls[:max_calls]
        discarded_calls = tool_calls[max_calls:]
        
        registry = get_registry()
        available_tools = {t.name: t for t in registry.list_tools()}
        
        async def execute_single_call(call: dict[str, Any]) -> BatchResult:
            """Execute a single tool call."""
            tool_name = call.get("tool", "")
            tool_params = call.get("parameters", {})
            
            # Check if tool is disallowed
            if tool_name in DISALLOWED_TOOLS:
                return BatchResult(
                    tool=tool_name,
                    success=False,
                    error=f"Tool '{tool_name}' is not allowed in batch. Disallowed tools: {', '.join(DISALLOWED_TOOLS)}",
                )
            
            # Check if tool exists
            tool = available_tools.get(tool_name)
            if not tool:
                available_list = [name for name in available_tools.keys() 
                                  if name not in FILTERED_FROM_SUGGESTIONS]
                return BatchResult(
                    tool=tool_name,
                    success=False,
                    error=f"Tool '{tool_name}' not in registry. External tools (MCP, environment) cannot be batched - call them directly. Available tools: {', '.join(available_list)}",
                )
            
            # Validate parameters
            error = tool.validate_params(tool_params)
            if error:
                return BatchResult(
                    tool=tool_name,
                    success=False,
                    error=error,
                )
            
            # Execute the tool
            try:
                result = await tool.execute(**tool_params)
                return BatchResult(
                    tool=tool_name,
                    success=result.success,
                    output=result.output,
                    error=result.error,
                    metadata=result.metadata,
                )
            except Exception as e:
                return BatchResult(
                    tool=tool_name,
                    success=False,
                    error=f"Tool execution failed: {e}",
                )
        
        # Execute all calls in parallel
        tasks = [execute_single_call(call) for call in executed_calls]
        results = await asyncio.gather(*tasks)
        
        # Add discarded calls as errors
        for call in discarded_calls:
            results.append(BatchResult(
                tool=call.get("tool", "unknown"),
                success=False,
                error="Maximum of 25 tools allowed in batch",
            ))
        
        # Count successes and failures
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        # Build output message
        if failed > 0:
            output = f"Executed {successful}/{len(results)} tools successfully. {failed} failed.\n\n"
        else:
            output = f"All {successful} tools executed successfully.\n\nKeep using the batch tool for optimal performance in your next response!\n\n"
        
        # Add details for each result
        for result in results:
            if result.success:
                output += f"✓ {result.tool}: {result.output[:200] if result.output else 'OK'}\n"
            else:
                output += f"✗ {result.tool}: {result.error}\n"
        
        return ToolResult.ok(
            output=output,
            metadata={
                "total_calls": len(results),
                "successful": successful,
                "failed": failed,
                "tools": [call.get("tool", "") for call in tool_calls],
                "details": [
                    {
                        "tool": r.tool,
                        "success": r.success,
                        "output": r.output[:500] if r.output else None,
                        "error": r.error,
                    }
                    for r in results
                ],
            },
        )
