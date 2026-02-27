"""
Todo tool for task tracking.

This tool allows the AI agent to create and manage a todo list
for tracking progress on complex tasks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from opencode.tool.base import PermissionLevel, Tool, ToolResult


@dataclass
class TodoItem:
    """A single todo item."""
    
    id: str
    content: str
    status: str = "pending"  # pending, in_progress, completed
    priority: str = "medium"  # low, medium, high
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "status": self.status,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class TodoWriteTool(Tool):
    """
    Tool for writing/updating the todo list.
    
    Allows the agent to:
    - Create new todos
    - Update existing todos
    - Mark todos as complete
    - Delete todos
    """
    
    def __init__(self):
        self._todos: list[TodoItem] = []
        self._next_id = 1
    
    @property
    def name(self) -> str:
        return "todowrite"
    
    @property
    def description(self) -> str:
        return """Create and manage a todo list for tracking task progress.

Use this tool to:
- Create new todo items
- Update the status of existing items
- Mark items as completed
- Track progress on complex multi-step tasks

Todo statuses:
- pending: Not yet started
- in_progress: Currently working on
- completed: Finished

Example usage:
- Create: todowrite(todos=[{"content": "Implement feature X", "status": "pending"}])
- Update: todowrite(todos=[{"id": "1", "status": "completed"}])
"""
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "todos": {
                    "type": "array",
                    "description": "List of todo items to create or update",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "string",
                                "description": "ID of existing todo to update (optional for new items)",
                            },
                            "content": {
                                "type": "string",
                                "description": "Content/description of the todo item",
                            },
                            "status": {
                                "type": "string",
                                "enum": ["pending", "in_progress", "completed"],
                                "description": "Status of the todo item",
                            },
                            "priority": {
                                "type": "string",
                                "enum": ["low", "medium", "high"],
                                "description": "Priority level",
                            },
                        },
                        "required": ["content"],
                    },
                },
            },
            "required": ["todos"],
        }
    
    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.WRITE
    
    async def execute(self, **params: Any) -> ToolResult:
        """Execute the todo write operation."""
        todos = params.get("todos", [])
        
        if not todos:
            return ToolResult.err("No todos provided")
        
        results = []
        
        for todo_data in todos:
            todo_id = todo_data.get("id")
            content = todo_data.get("content", "")
            status = todo_data.get("status", "pending")
            priority = todo_data.get("priority", "medium")
            
            if todo_id:
                # Update existing todo
                existing = next((t for t in self._todos if t.id == todo_id), None)
                if existing:
                    if content:
                        existing.content = content
                    existing.status = status
                    existing.priority = priority
                    if status == "completed" and not existing.completed_at:
                        existing.completed_at = datetime.now()
                    results.append(f"Updated: {existing.content} [{status}]")
                else:
                    results.append(f"Warning: Todo {todo_id} not found")
            else:
                # Create new todo
                new_todo = TodoItem(
                    id=str(self._next_id),
                    content=content,
                    status=status,
                    priority=priority,
                )
                self._todos.append(new_todo)
                self._next_id += 1
                results.append(f"Created: {content} [{status}]")
        
        output = "Todo list updated:\n" + "\n".join(f"- {r}" for r in results)
        output += f"\n\nTotal items: {len(self._todos)}"
        
        return ToolResult.ok(
            output=output,
            metadata={"todos": [t.to_dict() for t in self._todos]},
        )


class TodoReadTool(Tool):
    """
    Tool for reading the current todo list.
    """
    
    def __init__(self, todo_write_tool: TodoWriteTool):
        self._todo_write = todo_write_tool
    
    @property
    def name(self) -> str:
        return "todoread"
    
    @property
    def description(self) -> str:
        return """Read the current todo list.

Returns all todo items with their status and progress.
"""
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
        }
    
    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.READ
    
    async def execute(self, **params: Any) -> ToolResult:
        """Execute the todo read operation."""
        todos = self._todo_write._todos
        
        if not todos:
            return ToolResult.ok("No todos in the list.")
        
        # Group by status
        pending = [t for t in todos if t.status == "pending"]
        in_progress = [t for t in todos if t.status == "in_progress"]
        completed = [t for t in todos if t.status == "completed"]
        
        lines = ["## Todo List", ""]
        
        if in_progress:
            lines.append("### In Progress")
            for t in in_progress:
                lines.append(f"- [ ] {t.content} (#{t.id})")
            lines.append("")
        
        if pending:
            lines.append("### Pending")
            for t in pending:
                lines.append(f"- [ ] {t.content} (#{t.id})")
            lines.append("")
        
        if completed:
            lines.append("### Completed")
            for t in completed:
                lines.append(f"- [x] {t.content} (#{t.id})")
            lines.append("")
        
        lines.append(f"Progress: {len(completed)}/{len(todos)} completed")
        
        return ToolResult.ok(
            output="\n".join(lines),
            metadata={"todos": [t.to_dict() for t in todos]},
        )
