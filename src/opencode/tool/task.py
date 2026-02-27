"""
Task tool for sub-agent delegation.

This tool allows the main agent to delegate tasks to specialized sub-agents,
enabling parallel work and specialized expertise.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from opencode.tool.base import PermissionLevel, Tool, ToolResult


@dataclass
class TaskTool(Tool):
    """
    Tool for delegating tasks to sub-agents.
    
    Sub-agents are specialized agents that can handle specific types of tasks:
    - Code review agents
    - Testing agents
    - Documentation agents
    - Research agents
    
    Each sub-agent runs in its own session with restricted permissions.
    """
    
    working_directory: str = "."
    
    @property
    def name(self) -> str:
        return "task"
    
    @property
    def description(self) -> str:
        return """Launch a specialized sub-agent to handle a specific task.

Use this tool when you need to:
- Delegate complex tasks to specialized agents
- Run tasks in parallel
- Use agents with specific expertise

Available sub-agent types:
- build: General coding and implementation tasks
- plan: Planning and architecture tasks
- review: Code review and quality checks

The sub-agent will run in its own session and return results.
Use task_id to resume a previous sub-agent session.
"""
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "A short (3-5 words) description of the task",
                },
                "prompt": {
                    "type": "string",
                    "description": "The task for the agent to perform",
                },
                "subagent_type": {
                    "type": "string",
                    "description": "The type of specialized agent to use for this task",
                    "enum": ["build", "plan", "review"],
                },
                "task_id": {
                    "type": "string",
                    "description": (
                        "This should only be set if you mean to resume a previous task "
                        "(you can pass a prior task_id and the task will continue the "
                        "same subagent session as before instead of creating a fresh one)"
                    ),
                },
            },
            "required": ["description", "prompt", "subagent_type"],
        }
    
    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.EXECUTE
    
    @property
    def required_permissions(self) -> list[str]:
        return ["task"]
    
    async def execute(self, **params: Any) -> ToolResult:
        """Execute the task delegation."""
        description = params.get("description", "")
        prompt = params.get("prompt", "")
        subagent_type = params.get("subagent_type", "")
        task_id = params.get("task_id")
        
        # Validate subagent type
        valid_types = ["build", "plan", "review"]
        if subagent_type not in valid_types:
            return ToolResult.err(
                f"Unknown agent type: {subagent_type}. "
                f"Valid types are: {', '.join(valid_types)}"
            )
        
        # In a full implementation, this would:
        # 1. Create or resume a sub-agent session
        # 2. Configure the agent with appropriate permissions
        # 3. Run the agent with the prompt
        # 4. Return the results
        
        # For now, return a placeholder indicating the feature needs full implementation
        output = f"""Task delegation to {subagent_type} agent:

Description: {description}
Prompt: {prompt[:500]}{"..." if len(prompt) > 500 else ""}

Note: Full sub-agent implementation requires integration with the session and agent systems.
The sub-agent would run with restricted permissions and return results.

To fully implement this:
1. Create a new session with parent reference
2. Configure agent-specific permissions
3. Run the agent loop with the prompt
4. Collect and return results
"""
        
        return ToolResult.ok(
            output=output,
            metadata={
                "description": description,
                "subagent_type": subagent_type,
                "task_id": task_id,
                "status": "placeholder",
            },
        )
