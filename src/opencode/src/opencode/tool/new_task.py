"""
New Task Tool

Tool for spawning subagent tasks.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from opencode.tool.base import Tool, ToolResult

logger = logging.getLogger(__name__)


class NewTaskTool(Tool):
    """
    Tool for spawning a new subagent task.
    
    This tool allows the AI to delegate work to a subagent with
    its own context and instructions.
    
    Example:
        result = await tool.execute(
            message="Analyze the authentication module for security issues",
            mode="debug",
            context={"target_files": ["auth.py", "session.py"]}
        )
    """
    
    @property
    def name(self) -> str:
        return "new_task"
    
    @property
    def description(self) -> str:
        return "Spawn a new subagent task with specific instructions"
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The task message/instructions for the subagent",
                },
                "mode": {
                    "type": "string",
                    "description": "Mode for the subagent (code, architect, ask, debug)",
                    "enum": ["code", "architect", "ask", "debug"],
                },
                "context": {
                    "type": "object",
                    "description": "Additional context for the subagent",
                    "additionalProperties": {"type": "string"},
                },
                "resume": {
                    "type": "boolean",
                    "description": "Whether to resume after subagent completes",
                    "default": True,
                },
            },
            "required": ["message"],
        }
    
    async def execute(self, **params: Any) -> ToolResult:
        """
        Execute the new task tool.
        
        Args:
            **params: Tool parameters including:
                - message: Task instructions for the subagent
                - mode: Mode for the subagent
                - context: Additional context
                - resume: Whether to resume after completion
            
        Returns:
            ToolResult with task spawn details
        """
        message = params.get("message")
        if not message:
            return ToolResult.err("Required parameter 'message' is missing")
        
        mode = params.get("mode", "code")
        context: Dict[str, Any] = params.get("context", {})
        resume = params.get("resume", True)
        
        # Generate task ID
        task_id = str(uuid.uuid4())[:8]
        
        # Format output
        output = f"Created new task: {task_id}\n"
        output += f"Mode: {mode}\n"
        output += f"Instructions: {message[:100]}{'...' if len(message) > 100 else ''}\n"
        output += f"Resume after completion: {resume}"
        
        return ToolResult.ok(
            output=output,
            metadata={
                "type": "new_task",
                "task_id": task_id,
                "message": message,
                "mode": mode,
                "context": context,
                "resume": resume,
                "status": "pending",
            },
        )
