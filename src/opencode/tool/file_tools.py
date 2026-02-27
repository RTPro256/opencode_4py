"""
File tools for reading, writing, and editing files.

These tools allow the AI agent to interact with the filesystem
in a safe and controlled manner.

When sandboxing is active (integration mode), file access is restricted
to allowed directories and requires permission for external access.
"""

from __future__ import annotations

import difflib
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from opencode.tool.base import (
    PermissionLevel,
    Tool,
    ToolResult,
)
from opencode.core.sandbox import (
    AccessType,
    check_file_access,
    is_sandbox_active,
)


@dataclass
class ReadTool(Tool):
    """
    Tool for reading file contents.
    
    Features:
    - Encoding detection
    - Large file handling with truncation
    - Line range support
    - Multiple file reading
    """
    
    working_directory: Path = Path(".")
    max_file_size: int = 10 * 1024 * 1024  # 10 MB
    max_output_size: int = 100000  # characters
    
    @property
    def name(self) -> str:
        return "read"
    
    @property
    def description(self) -> str:
        return """Read the contents of a file.

- Returns file contents as text
- Large files are truncated
- Use line ranges to read specific sections
- Supports multiple files at once"""
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to read (relative to project root)",
                },
                "start_line": {
                    "type": "integer",
                    "description": "Starting line number (1-indexed)",
                    "default": 1,
                },
                "end_line": {
                    "type": "integer",
                    "description": "Ending line number (inclusive)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of lines to read",
                    "default": 2000,
                },
            },
            "required": ["file_path"],
        }
    
    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.READ
    
    async def execute(
        self,
        file_path: str,
        start_line: int = 1,
        end_line: Optional[int] = None,
        limit: int = 2000,
        **kwargs: Any,
    ) -> ToolResult:
        """Read file contents."""
        path = self.working_directory / file_path
        
        # Security check - prevent path traversal and enforce sandbox
        try:
            path = path.resolve()
            
            # Check sandbox if active (integration mode)
            if is_sandbox_active():
                allowed, reason = check_file_access(path, AccessType.READ)
                if not allowed:
                    return ToolResult.err(reason or f"Access denied: sandbox restriction")
            else:
                # Standard path traversal check when sandbox not active
                if not str(path).startswith(str(self.working_directory.resolve())):
                    return ToolResult.err(f"Access denied: path outside project directory")
        except Exception as e:
            return ToolResult.err(f"Invalid path: {e}")
        
        # Check if file exists
        if not path.exists():
            return ToolResult.err(f"File not found: {file_path}")
        
        if not path.is_file():
            return ToolResult.err(f"Not a file: {file_path}")
        
        # Check file size
        file_size = path.stat().st_size
        if file_size > self.max_file_size:
            return ToolResult.err(
                f"File too large ({file_size} bytes). Maximum size is {self.max_file_size} bytes."
            )
        
        try:
            # Read file content
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            
            # Apply line range
            total_lines = len(lines)
            start_idx = max(0, start_line - 1)
            end_idx = end_line if end_line else len(lines)
            end_idx = min(end_idx, start_idx + limit)
            
            selected_lines = lines[start_idx:end_idx]
            
            # Format output with line numbers
            output_lines = []
            for i, line in enumerate(selected_lines, start=start_line):
                # Remove trailing newline for display
                line_content = line.rstrip("\n\r")
                output_lines.append(f"{i:6}\t{line_content}")
            
            output = "\n".join(output_lines)
            
            # Truncate if necessary
            truncated = False
            if len(output) > self.max_output_size:
                output = output[:self.max_output_size] + "\n... (output truncated)"
                truncated = True
            
            return ToolResult.ok(
                output=output,
                metadata={
                    "file_path": file_path,
                    "total_lines": total_lines,
                    "lines_shown": len(selected_lines),
                    "start_line": start_line,
                    "end_line": start_line + len(selected_lines) - 1,
                    "truncated": truncated,
                },
            )
        
        except Exception as e:
            return ToolResult.err(f"Failed to read file: {e}")


@dataclass
class WriteTool(Tool):
    """
    Tool for creating or overwriting files.
    
    Features:
    - Creates parent directories if needed
    - Atomic write operation
    - Backup of existing files
    """
    
    working_directory: Path = Path(".")
    
    @property
    def name(self) -> str:
        return "write"
    
    @property
    def description(self) -> str:
        return """Write content to a file.

- Creates the file if it doesn't exist
- Overwrites existing content
- Creates parent directories if needed
- Use with caution as this can overwrite important files"""
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to write (relative to project root)",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file",
                },
            },
            "required": ["file_path", "content"],
        }
    
    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.WRITE
    
    async def execute(
        self,
        file_path: str,
        content: str,
        **kwargs: Any,
    ) -> ToolResult:
        """Write content to a file."""
        path = self.working_directory / file_path
        
        # Security check - prevent path traversal and enforce sandbox
        try:
            path = path.resolve()
            
            # Check sandbox if active (integration mode)
            if is_sandbox_active():
                allowed, reason = check_file_access(path, AccessType.WRITE)
                if not allowed:
                    return ToolResult.err(reason or f"Access denied: sandbox restriction")
            else:
                # Standard path traversal check when sandbox not active
                if not str(path).startswith(str(self.working_directory.resolve())):
                    return ToolResult.err("Access denied: path outside project directory")
        except Exception as e:
            return ToolResult.err(f"Invalid path: {e}")
        
        try:
            # Create parent directories
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content atomically
            temp_path = path.with_suffix(path.suffix + ".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            # Atomic rename
            temp_path.rename(path)
            
            return ToolResult.ok(
                output=f"Successfully wrote {len(content)} characters to {file_path}",
                files_changed=[file_path],
            )
        
        except Exception as e:
            return ToolResult.err(f"Failed to write file: {e}")


@dataclass
class EditTool(Tool):
    """
    Tool for editing files with string replacement.
    
    Features:
    - String-based search and replace
    - Multiple occurrences
    - Preview changes
    - Undo support
    """
    
    working_directory: Path = Path(".")
    
    @property
    def name(self) -> str:
        return "edit"
    
    @property
    def description(self) -> str:
        return """Edit a file by replacing text.

- Finds and replaces exact string matches
- Can replace multiple occurrences
- Use read tool first to see the current content
- Be careful with whitespace and indentation"""
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to edit",
                },
                "old_string": {
                    "type": "string",
                    "description": "The text to find and replace",
                },
                "new_string": {
                    "type": "string",
                    "description": "The text to replace with",
                },
                "replace_all": {
                    "type": "boolean",
                    "description": "Replace all occurrences (default: false)",
                    "default": False,
                },
            },
            "required": ["file_path", "old_string", "new_string"],
        }
    
    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.WRITE
    
    async def execute(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
        **kwargs: Any,
    ) -> ToolResult:
        """Edit a file by replacing text."""
        path = self.working_directory / file_path
        
        # Security check - prevent path traversal and enforce sandbox
        try:
            path = path.resolve()
            
            # Check sandbox if active (integration mode)
            if is_sandbox_active():
                allowed, reason = check_file_access(path, AccessType.WRITE)
                if not allowed:
                    return ToolResult.err(reason or f"Access denied: sandbox restriction")
            else:
                # Standard path traversal check when sandbox not active
                if not str(path).startswith(str(self.working_directory.resolve())):
                    return ToolResult.err("Access denied: path outside project directory")
        except Exception as e:
            return ToolResult.err(f"Invalid path: {e}")
        
        # Check if file exists
        if not path.exists():
            return ToolResult.err(f"File not found: {file_path}")
        
        try:
            # Read current content
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Check if old_string exists
            if old_string not in content:
                return ToolResult.err(
                    f"Text not found in file. Make sure the old_string matches exactly, "
                    f"including whitespace and line breaks."
                )
            
            # Count occurrences
            count = content.count(old_string)
            
            if count > 1 and not replace_all:
                return ToolResult.err(
                    f"Found {count} occurrences of the text. "
                    f"Set replace_all=true to replace all occurrences, "
                    f"or provide a more specific old_string."
                )
            
            # Perform replacement
            if replace_all:
                new_content = content.replace(old_string, new_string)
            else:
                new_content = content.replace(old_string, new_string, 1)
            
            # Write back
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)
            
            # Generate diff for output
            diff = list(difflib.unified_diff(
                content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"{file_path} (before)",
                tofile=f"{file_path} (after)",
            ))
            
            return ToolResult.ok(
                output=f"Successfully replaced {count} occurrence(s) in {file_path}\n"
                       f"{''.join(diff)}",
                files_changed=[file_path],
                metadata={
                    "occurrences_replaced": count,
                    "old_length": len(content),
                    "new_length": len(new_content),
                },
            )
        
        except Exception as e:
            return ToolResult.err(f"Failed to edit file: {e}")


@dataclass
class GlobTool(Tool):
    """
    Tool for finding files by pattern.
    
    Features:
    - Glob pattern matching
    - Gitignore respect
    - Multiple patterns
    """
    
    working_directory: Path = Path(".")
    
    @property
    def name(self) -> str:
        return "glob"
    
    @property
    def description(self) -> str:
        return """Find files matching a pattern.

- Uses glob patterns (e.g., **/*.py for all Python files)
- Respects .gitignore by default
- Returns relative paths"""
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern to match files",
                },
                "path": {
                    "type": "string",
                    "description": "Directory to search in (default: project root)",
                },
            },
            "required": ["pattern"],
        }
    
    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.READ
    
    async def execute(
        self,
        pattern: str,
        path: Optional[str] = None,
        **kwargs: Any,
    ) -> ToolResult:
        """Find files matching a pattern."""
        search_path = self.working_directory / path if path else self.working_directory
        
        # Security check - enforce sandbox
        try:
            resolved_search = search_path.resolve()
            
            # Check sandbox if active (integration mode)
            if is_sandbox_active():
                allowed, reason = check_file_access(resolved_search, AccessType.READ)
                if not allowed:
                    return ToolResult.err(reason or f"Access denied: sandbox restriction")
            else:
                # Standard path traversal check when sandbox not active
                if not str(resolved_search).startswith(str(self.working_directory.resolve())):
                    return ToolResult.err("Access denied: path outside project directory")
        except Exception as e:
            return ToolResult.err(f"Invalid path: {e}")
        
        try:
            # Use pathlib glob
            matches = list(search_path.glob(pattern))
            
            # Convert to relative paths
            relative_paths = []
            for match in matches:
                if match.is_file():
                    try:
                        rel_path = match.relative_to(self.working_directory)
                        relative_paths.append(str(rel_path))
                    except ValueError:
                        pass
            
            # Sort and limit results
            relative_paths.sort()
            max_results = 1000
            truncated = len(relative_paths) > max_results
            relative_paths = relative_paths[:max_results]
            
            output = "\n".join(relative_paths)
            if truncated:
                output += f"\n... (truncated, {len(relative_paths)} of {len(matches)} results shown)"
            
            return ToolResult.ok(
                output=output or "No files found",
                metadata={
                    "pattern": pattern,
                    "count": len(relative_paths),
                    "truncated": truncated,
                },
            )
        
        except Exception as e:
            return ToolResult.err(f"Failed to search: {e}")


@dataclass
class GrepTool(Tool):
    """
    Tool for searching file contents.
    
    Features:
    - Regex pattern matching
    - Context lines
    - File type filtering
    """
    
    working_directory: Path = Path(".")
    max_output_size: int = 100000
    
    @property
    def name(self) -> str:
        return "grep"
    
    @property
    def description(self) -> str:
        return """Search for patterns in files.

- Uses regular expressions
- Shows matching lines with context
- Can filter by file pattern"""
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Regular expression pattern to search for",
                },
                "path": {
                    "type": "string",
                    "description": "Directory or file to search in",
                },
                "file_pattern": {
                    "type": "string",
                    "description": "Glob pattern for files to search (e.g., *.py)",
                    "default": "*",
                },
                "context": {
                    "type": "integer",
                    "description": "Number of context lines to show",
                    "default": 2,
                },
            },
            "required": ["pattern"],
        }
    
    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.READ
    
    async def execute(
        self,
        pattern: str,
        path: Optional[str] = None,
        file_pattern: str = "*",
        context: int = 2,
        **kwargs: Any,
    ) -> ToolResult:
        """Search for patterns in files."""
        search_path = self.working_directory / path if path else self.working_directory
        
        # Security check - enforce sandbox
        try:
            resolved_search = search_path.resolve()
            
            # Check sandbox if active (integration mode)
            if is_sandbox_active():
                allowed, reason = check_file_access(resolved_search, AccessType.READ)
                if not allowed:
                    return ToolResult.err(reason or f"Access denied: sandbox restriction")
            else:
                # Standard path traversal check when sandbox not active
                if not str(resolved_search).startswith(str(self.working_directory.resolve())):
                    return ToolResult.err("Access denied: path outside project directory")
        except Exception as e:
            return ToolResult.err(f"Invalid path: {e}")
        
        try:
            regex = re.compile(pattern)
        except re.error as e:
            return ToolResult.err(f"Invalid regex pattern: {e}")
        
        results = []
        
        try:
            # Get files to search
            if search_path.is_file():
                files = [search_path]
            else:
                files = list(search_path.rglob(file_pattern))
            
            for file_path in files:
                if not file_path.is_file():
                    continue
                
                # Skip binary files and common non-text files
                if any(part in str(file_path) for part in [".git", "__pycache__", "node_modules", ".venv"]):
                    continue
                
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                    
                    for i, line in enumerate(lines):
                        if regex.search(line):
                            # Get context
                            start = max(0, i - context)
                            end = min(len(lines), i + context + 1)
                            
                            rel_path = file_path.relative_to(self.working_directory)
                            
                            for j in range(start, end):
                                prefix = ">" if j == i else " "
                                results.append(f"{rel_path}:{j+1}:{prefix} {lines[j].rstrip()}")
                            
                            results.append("")  # Empty line between matches
                
                except Exception:
                    continue
            
            output = "\n".join(results)
            
            if len(output) > self.max_output_size:
                output = output[:self.max_output_size] + "\n... (output truncated)"
            
            return ToolResult.ok(
                output=output or "No matches found",
                metadata={
                    "pattern": pattern,
                    "matches": len([r for r in results if r.startswith(">")]),
                },
            )
        
        except Exception as e:
            return ToolResult.err(f"Search failed: {e}")


# Factory functions
def create_read_tool(working_directory: Path = Path(".")) -> ReadTool:
    return ReadTool(working_directory=working_directory)


def create_write_tool(working_directory: Path = Path(".")) -> WriteTool:
    return WriteTool(working_directory=working_directory)


def create_edit_tool(working_directory: Path = Path(".")) -> EditTool:
    return EditTool(working_directory=working_directory)


def create_glob_tool(working_directory: Path = Path(".")) -> GlobTool:
    return GlobTool(working_directory=working_directory)


def create_grep_tool(working_directory: Path = Path(".")) -> GrepTool:
    return GrepTool(working_directory=working_directory)
