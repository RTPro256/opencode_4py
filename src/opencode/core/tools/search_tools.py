"""
Search and list files tools.

Refactored from Roo-Code's search and list files tools.
"""

import fnmatch
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from .base import BaseTool, ToolResult, ToolCallbacks, ToolRegistry


@dataclass
class SearchFilesParams:
    """Parameters for search_files tool."""
    path: str
    regex: str
    file_pattern: Optional[str] = None
    ignore_case: bool = True


@dataclass
class ListFilesParams:
    """Parameters for list_files tool."""
    path: str
    recursive: bool = True


@ToolRegistry.register
class SearchFilesTool(BaseTool[SearchFilesParams]):
    """Search files for regex pattern tool."""
    
    name = "search_files"
    description = "Search for a regex pattern in files within a directory"
    
    @classmethod
    def get_parameters_schema(cls) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory to search in",
                },
                "regex": {
                    "type": "string",
                    "description": "Regex pattern to search for",
                },
                "file_pattern": {
                    "type": "string",
                    "description": "Glob pattern to filter files (e.g., '*.py')",
                },
                "ignore_case": {
                    "type": "boolean",
                    "description": "Whether to ignore case (default true)",
                },
            },
            "required": ["path", "regex"],
        }
    
    async def execute(
        self,
        params: SearchFilesParams,
        callbacks: ToolCallbacks,
    ) -> ToolResult:
        """Execute the search."""
        search_path = Path(params.path)
        
        if not search_path.exists():
            return ToolResult.error_result(f"Path not found: {params.path}")
        
        if not search_path.is_dir():
            return ToolResult.error_result(f"Not a directory: {params.path}")
        
        try:
            flags = re.IGNORECASE if params.ignore_case else 0
            pattern = re.compile(params.regex, flags)
        except re.error as e:
            return ToolResult.error_result(f"Invalid regex: {e}")
        
        results = []
        matches_count = 0
        
        # Get files to search
        if params.file_pattern:
            files = list(search_path.rglob(params.file_pattern))
        else:
            files = list(search_path.rglob("*"))
        
        for file_path in files:
            if not file_path.is_file():
                continue
            
            # Skip binary files and common ignore patterns
            if any(part.startswith(".") for part in file_path.parts):
                continue
            if file_path.suffix in {".pyc", ".pyo", ".so", ".dll", ".exe", ".bin"}:
                continue
            
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                lines = content.splitlines()
                
                file_matches = []
                for i, line in enumerate(lines, start=1):
                    if pattern.search(line):
                        file_matches.append((i, line.strip()))
                        matches_count += 1
                
                if file_matches:
                    rel_path = file_path.relative_to(search_path)
                    results.append(f"\n{rel_path}:")
                    for line_num, line in file_matches[:10]:  # Limit matches per file
                        results.append(f"  {line_num}: {line[:100]}")
                    if len(file_matches) > 10:
                        results.append(f"  ... and {len(file_matches) - 10} more matches")
                
            except Exception:
                continue
        
        if not results:
            return ToolResult.success_result(
                f"No matches found for pattern: {params.regex}",
                data={"matches": 0},
            )
        
        output = f"Found {matches_count} matches:\n" + "\n".join(results)
        return ToolResult.success_result(
            output,
            data={"matches": matches_count, "files_searched": len(files)},
        )


@ToolRegistry.register
class ListFilesTool(BaseTool[ListFilesParams]):
    """List files in directory tool."""
    
    name = "list_files"
    description = "List files and directories in a path"
    
    @classmethod
    def get_parameters_schema(cls) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory to list",
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Whether to list recursively (default true)",
                },
            },
            "required": ["path"],
        }
    
    async def execute(
        self,
        params: ListFilesParams,
        callbacks: ToolCallbacks,
    ) -> ToolResult:
        """Execute the list operation."""
        list_path = Path(params.path)
        
        if not list_path.exists():
            return ToolResult.error_result(f"Path not found: {params.path}")
        
        if not list_path.is_dir():
            return ToolResult.error_result(f"Not a directory: {params.path}")
        
        results = []
        file_count = 0
        dir_count = 0
        
        if params.recursive:
            iterator = list_path.rglob("*")
        else:
            iterator = list_path.iterdir()
        
        for item in sorted(iterator):
            rel_path = item.relative_to(list_path)
            
            if item.is_dir():
                results.append(f"📁 {rel_path}/")
                dir_count += 1
            else:
                size = item.stat().st_size
                size_str = self._format_size(size)
                results.append(f"📄 {rel_path} ({size_str})")
                file_count += 1
        
        output = f"Directory listing for {params.path}:\n\n"
        output += "\n".join(results)
        output += f"\n\n{file_count} files, {dir_count} directories"
        
        return ToolResult.success_result(
            output,
            data={
                "path": str(list_path),
                "files": file_count,
                "directories": dir_count,
                "recursive": params.recursive,
            },
        )
    
    @staticmethod
    def _format_size(size: int) -> str:
        """Format file size in human-readable format."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"
