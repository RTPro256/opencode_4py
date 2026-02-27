"""
File operation tools.

Refactored from Roo-Code's file tools.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from .base import BaseTool, ToolResult, ToolCallbacks, ToolRegistry


@dataclass
class ReadFileParams:
    """Parameters for read_file tool."""
    path: str
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


@dataclass
class WriteFileParams:
    """Parameters for write_to_file tool."""
    path: str
    content: str
    mode: str = "write"  # "write" or "append"


@dataclass
class EditFileParams:
    """Parameters for edit_file tool."""
    path: str
    old_string: str
    new_string: str
    expected_replacements: int = 1


@ToolRegistry.register
class ReadFileTool(BaseTool[ReadFileParams]):
    """Read file contents tool."""
    
    name = "read_file"
    description = "Read the contents of a file from the filesystem"
    
    @classmethod
    def get_parameters_schema(cls) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path to the file to read",
                },
                "start_line": {
                    "type": "integer",
                    "description": "Starting line number (1-based)",
                },
                "end_line": {
                    "type": "integer",
                    "description": "Ending line number (1-based)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of lines to read",
                },
                "offset": {
                    "type": "integer",
                    "description": "Number of lines to skip from start",
                },
            },
            "required": ["path"],
        }
    
    async def execute(
        self,
        params: ReadFileParams,
        callbacks: ToolCallbacks,
    ) -> ToolResult:
        """Execute the read file operation."""
        path = Path(params.path)
        
        if not path.exists():
            return ToolResult.error_result(f"File not found: {params.path}")
        
        if not path.is_file():
            return ToolResult.error_result(f"Not a file: {params.path}")
        
        try:
            content = path.read_text(encoding="utf-8")
            lines = content.splitlines(keepends=True)
            
            # Apply offset and limit
            start = params.offset or 0
            if params.start_line:
                start = max(0, params.start_line - 1)
            
            end = len(lines)
            if params.end_line:
                end = min(end, params.end_line)
            if params.limit:
                end = min(end, start + params.limit)
            
            selected_lines = lines[start:end]
            
            # Format with line numbers
            result_lines = []
            for i, line in enumerate(selected_lines, start=start + 1):
                result_lines.append(f"{i:6}\t{line}")
            
            output = "".join(result_lines)
            return ToolResult.success_result(
                output,
                data={
                    "path": str(path),
                    "total_lines": len(lines),
                    "lines_shown": len(selected_lines),
                },
            )
            
        except Exception as e:
            return ToolResult.error_result(f"Error reading file: {e}")


@ToolRegistry.register
class WriteFileTool(BaseTool[WriteFileParams]):
    """Write file contents tool."""
    
    name = "write_to_file"
    description = "Write content to a file, creating it if it doesn't exist"
    
    @classmethod
    def get_parameters_schema(cls) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path to the file to write",
                },
                "content": {
                    "type": "string",
                    "description": "The content to write to the file",
                },
                "mode": {
                    "type": "string",
                    "enum": ["write", "append"],
                    "description": "Write mode: 'write' to overwrite, 'append' to add",
                },
            },
            "required": ["path", "content"],
        }
    
    async def execute(
        self,
        params: WriteFileParams,
        callbacks: ToolCallbacks,
    ) -> ToolResult:
        """Execute the write file operation."""
        path = Path(params.path)
        
        # Create parent directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            mode = "a" if params.mode == "append" else "w"
            path.write_text(params.content, encoding="utf-8")
            
            return ToolResult.success_result(
                f"Successfully wrote to {params.path}",
                data={
                    "path": str(path),
                    "bytes_written": len(params.content.encode("utf-8")),
                    "mode": params.mode,
                },
            )
            
        except Exception as e:
            return ToolResult.error_result(f"Error writing file: {e}")


@ToolRegistry.register
class EditFileTool(BaseTool[EditFileParams]):
    """Edit file with string replacement tool."""
    
    name = "edit_file"
    description = "Edit a file by replacing text. Use this for precise edits."
    
    @classmethod
    def get_parameters_schema(cls) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path to the file to edit",
                },
                "old_string": {
                    "type": "string",
                    "description": "The text to find and replace",
                },
                "new_string": {
                    "type": "string",
                    "description": "The replacement text",
                },
                "expected_replacements": {
                    "type": "integer",
                    "description": "Expected number of replacements (default 1)",
                },
            },
            "required": ["path", "old_string", "new_string"],
        }
    
    async def execute(
        self,
        params: EditFileParams,
        callbacks: ToolCallbacks,
    ) -> ToolResult:
        """Execute the edit file operation."""
        path = Path(params.path)
        
        if not path.exists():
            return ToolResult.error_result(f"File not found: {params.path}")
        
        try:
            content = path.read_text(encoding="utf-8")
            
            # Count occurrences
            count = content.count(params.old_string)
            
            if count == 0:
                return ToolResult.error_result(
                    f"Text not found in file: {params.old_string[:50]}..."
                )
            
            if count != params.expected_replacements:
                return ToolResult.error_result(
                    f"Expected {params.expected_replacements} occurrences, found {count}"
                )
            
            # Perform replacement
            new_content = content.replace(
                params.old_string,
                params.new_string,
                params.expected_replacements,
            )
            
            path.write_text(new_content, encoding="utf-8")
            
            return ToolResult.success_result(
                f"Successfully replaced {count} occurrence(s) in {params.path}",
                data={
                    "path": str(path),
                    "replacements": count,
                },
            )
            
        except Exception as e:
            return ToolResult.error_result(f"Error editing file: {e}")
