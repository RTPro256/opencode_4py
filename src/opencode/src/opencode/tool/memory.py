"""
Memory Tool - Persistent memory storage across sessions.

Based on qwen-code memoryTool implementation.

Operations:
- save: Save a memory entry
- get: Retrieve a memory entry
- list: List all memory entries
- delete: Delete a memory entry
- switch: Switch between project and global scope
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .base import Tool, ToolResult


class MemoryScope(str):
    """Memory storage scope."""
    PROJECT = "project"
    GLOBAL = "global"


class MemoryEntry(BaseModel):
    """A single memory entry."""
    key: str
    """Unique key for the entry."""
    
    value: str
    """Stored value."""
    
    scope: str = MemoryScope.PROJECT
    """Storage scope (project or global)."""
    
    created_at: datetime = Field(default_factory=datetime.now)
    """When the entry was created."""
    
    updated_at: datetime = Field(default_factory=datetime.now)
    """When the entry was last updated."""
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    """Additional metadata."""


class MemoryTool(Tool):
    """Persistent memory storage for sessions.
    
    Provides a way to store and retrieve information across sessions.
    Supports both project-level and global (user-level) storage.
    
    Storage locations:
    - Project: .opencode/memory.json
    - Global: ~/.opencode/memory.json
    """
    
    def __init__(
        self,
        project_root: Optional[Path] = None,
        user_home: Optional[Path] = None,
    ):
        """Initialize the memory tool.
        
        Args:
            project_root: Project root directory (defaults to cwd)
            user_home: User home directory (defaults to ~)
        """
        self.project_root = project_root or Path.cwd()
        self.user_home = user_home or Path.home()
        
        # Storage files
        self.project_memory_file = self.project_root / ".opencode" / "memory.json"
        self.global_memory_file = self.user_home / ".opencode" / "memory.json"
        
        # Current scope
        self._current_scope = MemoryScope.PROJECT
        
        # Cache
        self._project_memory: Optional[Dict[str, MemoryEntry]] = None
        self._global_memory: Optional[Dict[str, MemoryEntry]] = None
    
    @property
    def name(self) -> str:
        return "memory"
    
    @property
    def description(self) -> str:
        return "Persistent memory storage for saving and retrieving information across sessions"
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["save", "get", "list", "delete", "switch"],
                    "description": "Operation to perform"
                },
                "key": {
                    "type": "string",
                    "description": "Key for the memory entry (required for save, get, delete)"
                },
                "value": {
                    "type": "string",
                    "description": "Value to store (required for save)"
                },
                "scope": {
                    "type": "string",
                    "enum": ["project", "global"],
                    "default": "project",
                    "description": "Storage scope"
                }
            },
            "required": ["operation"]
        }
    
    async def execute(self, **params: Any) -> ToolResult:
        """Execute a memory operation.
        
        Args:
            params: Tool parameters including operation, key, value, scope
            
        Returns:
            ToolResult with operation result
        """
        operation = params.get("operation")
        key = params.get("key")
        value = params.get("value")
        scope = params.get("scope") or self._current_scope
        
        try:
            if operation == "save":
                return await self._save(key, value, scope)
            elif operation == "get":
                return await self._get(key, scope)
            elif operation == "list":
                return await self._list(scope)
            elif operation == "delete":
                return await self._delete(key, scope)
            elif operation == "switch":
                return await self._switch_scope(scope)
            else:
                return ToolResult.err(
                    f"Unknown operation: {operation}. Must be one of: save, get, list, delete, switch"
                )
        except Exception as e:
            return ToolResult.err(f"Memory operation failed: {str(e)}")
    
    async def _save(
        self,
        key: Optional[str],
        value: Optional[str],
        scope: str
    ) -> ToolResult:
        """Save a memory entry."""
        if not key:
            return ToolResult.err("Key is required for save operation")
        
        if not value:
            return ToolResult.err("Value is required for save operation")
        
        memory = self._get_memory(scope)
        
        # Check if updating existing entry
        existing = memory.get(key)
        if existing:
            entry = MemoryEntry(
                key=key,
                value=value,
                scope=scope,
                created_at=existing.created_at,
                updated_at=datetime.now(),
                metadata=existing.metadata
            )
        else:
            entry = MemoryEntry(
                key=key,
                value=value,
                scope=scope
            )
        
        memory[key] = entry
        self._save_memory(scope, memory)
        
        return ToolResult.ok(
            f"Saved memory entry '{key}' in {scope} scope",
            metadata={"key": key, "scope": scope, "created": entry.created_at.isoformat()}
        )
    
    async def _get(
        self,
        key: Optional[str],
        scope: str
    ) -> ToolResult:
        """Get a memory entry."""
        if not key:
            return ToolResult.err("Key is required for get operation")
        
        memory = self._get_memory(scope)
        entry = memory.get(key)
        
        if not entry:
            return ToolResult.err(f"Memory entry '{key}' not found in {scope} scope")
        
        return ToolResult.ok(
            entry.value,
            metadata={
                "key": entry.key,
                "value": entry.value,
                "scope": entry.scope,
                "created_at": entry.created_at.isoformat(),
                "updated_at": entry.updated_at.isoformat(),
            }
        )
    
    async def _list(self, scope: str) -> ToolResult:
        """List all memory entries."""
        memory = self._get_memory(scope)
        
        if not memory:
            return ToolResult.ok(
                f"No memory entries in {scope} scope",
                metadata={"entries": [], "count": 0}
            )
        
        entries = [
            {
                "key": entry.key,
                "value": entry.value[:100] + "..." if len(entry.value) > 100 else entry.value,
                "created_at": entry.created_at.isoformat(),
                "updated_at": entry.updated_at.isoformat(),
            }
            for entry in memory.values()
        ]
        
        return ToolResult.ok(
            f"Found {len(entries)} memory entries in {scope} scope",
            metadata={"entries": entries, "count": len(entries)}
        )
    
    async def _delete(
        self,
        key: Optional[str],
        scope: str
    ) -> ToolResult:
        """Delete a memory entry."""
        if not key:
            return ToolResult.err("Key is required for delete operation")
        
        memory = self._get_memory(scope)
        
        if key not in memory:
            return ToolResult.err(f"Memory entry '{key}' not found in {scope} scope")
        
        del memory[key]
        self._save_memory(scope, memory)
        
        return ToolResult.ok(
            f"Deleted memory entry '{key}' from {scope} scope",
            metadata={"key": key, "scope": scope}
        )
    
    async def _switch_scope(self, scope: str) -> ToolResult:
        """Switch the current scope."""
        if scope not in [MemoryScope.PROJECT, MemoryScope.GLOBAL]:
            return ToolResult.err(f"Invalid scope: {scope}. Must be 'project' or 'global'")
        
        old_scope = self._current_scope
        self._current_scope = scope
        
        return ToolResult.ok(
            f"Switched from {old_scope} to {scope} scope",
            metadata={"previous_scope": old_scope, "current_scope": scope}
        )
    
    def _get_memory_file(self, scope: str) -> Path:
        """Get the memory file path for a scope."""
        if scope == MemoryScope.GLOBAL:
            return self.global_memory_file
        return self.project_memory_file
    
    def _get_memory(self, scope: str) -> Dict[str, MemoryEntry]:
        """Load memory for a scope."""
        if scope == MemoryScope.GLOBAL:
            if self._global_memory is None:
                self._global_memory = self._load_memory(self.global_memory_file)
            return self._global_memory
        
        if self._project_memory is None:
            self._project_memory = self._load_memory(self.project_memory_file)
        return self._project_memory
    
    def _load_memory(self, path: Path) -> Dict[str, MemoryEntry]:
        """Load memory from a file."""
        if not path.exists():
            return {}
        
        try:
            with open(path, "r") as f:
                data = json.load(f)
            
            return {
                key: MemoryEntry(**entry)
                for key, entry in data.items()
            }
        except Exception:
            return {}
    
    def _save_memory(self, scope: str, memory: Dict[str, MemoryEntry]) -> None:
        """Save memory to a file."""
        path = self._get_memory_file(scope)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            key: entry.model_dump()
            for key, entry in memory.items()
        }
        
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)


# Tool registration function
def get_memory_tool(
    project_root: Optional[Path] = None,
    user_home: Optional[Path] = None
) -> MemoryTool:
    """Get an instance of the memory tool."""
    return MemoryTool(project_root, user_home)
