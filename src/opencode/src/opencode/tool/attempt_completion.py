"""
Attempt Completion Tool

Tool for marking a task as complete.
"""

import logging
from typing import Any, List

from opencode.tool.base import Tool, ToolResult

logger = logging.getLogger(__name__)


class AttemptCompletionTool(Tool):
    """
    Tool for marking a task as complete.
    
    This tool signals that the AI has completed its assigned task
    and provides a summary of what was done.
    
    Example:
        result = await tool.execute(
            result="Successfully implemented the authentication module",
            files_changed=["auth.py", "session.py"],
            requires_review=True
        )
    """
    
    @property
    def name(self) -> str:
        return "attempt_completion"
    
    @property
    def description(self) -> str:
        return "Mark the task as complete with a summary"
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "result": {
                    "type": "string",
                    "description": "Summary of what was accomplished",
                },
                "files_changed": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of files that were modified",
                },
                "requires_review": {
                    "type": "boolean",
                    "description": "Whether the changes require user review",
                    "default": False,
                },
            },
            "required": ["result"],
        }
    
    async def execute(self, **params: Any) -> ToolResult:
        """
        Execute the attempt completion tool.
        
        Args:
            **params: Tool parameters including:
                - result: The final result message
                - files_changed: List of modified files
                - requires_review: Whether changes need review
            
        Returns:
            ToolResult indicating task completion
        """
        result_message = params.get("result")
        if not result_message:
            return ToolResult.err("Required parameter 'result' is missing")
        
        files_changed: List[str] = params.get("files_changed", [])
        requires_review = params.get("requires_review", False)
        
        # Format output
        output = f"Task completed: {result_message}"
        if files_changed:
            output += f"\n\nFiles changed:\n"
            for file in files_changed:
                output += f"  - {file}\n"
        
        if requires_review:
            output += "\n⚠️ Changes require review before proceeding."
        
        return ToolResult.ok(
            output=output,
            metadata={
                "type": "task_completion",
                "result": result_message,
                "files_changed": files_changed,
                "requires_review": requires_review,
                "task_completed": True,
            },
            files_changed=files_changed,
        )
