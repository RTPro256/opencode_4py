"""
Multi-edit tool for performing multiple edits on a single file.

This tool allows performing multiple string replacement edits on a file
in a single operation, which is more efficient than multiple individual
edit calls.
"""

from pathlib import Path
from typing import Any, Optional

from opencode.tool.base import Tool, ToolResult


class MultiEditTool(Tool):
    """Tool for performing multiple edits on a single file."""
    
    @property
    def name(self) -> str:
        return "multiedit"
    
    @property
    def description(self) -> str:
        return """Perform multiple string replacement edits on a single file.

This tool is more efficient than calling the edit tool multiple times
when you need to make several changes to the same file.

The edits are applied sequentially in the order provided. Each edit
uses string replacement - it finds the oldString and replaces it with
newString.

IMPORTANT: Each edit operates on the result of the previous edit, so
the oldString for later edits should account for changes made by
earlier edits.

Parameters:
- filePath: The absolute path to the file to modify
- edits: Array of edit operations, each containing:
  - oldString: The text to find and replace
  - newString: The text to replace it with
  - replaceAll: (optional) Replace all occurrences (default: false)

Example:
{
  "filePath": "/path/to/file.py",
  "edits": [
    {"oldString": "old_func", "newString": "new_func"},
    {"oldString": "import old_module", "newString": "import new_module"}
  ]
}"""
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "filePath": {
                    "type": "string",
                    "description": "The absolute path to the file to modify",
                },
                "edits": {
                    "type": "array",
                    "description": "Array of edit operations to perform sequentially on the file",
                    "items": {
                        "type": "object",
                        "properties": {
                            "oldString": {
                                "type": "string",
                                "description": "The text to replace",
                            },
                            "newString": {
                                "type": "string",
                                "description": "The text to replace it with (must be different from oldString)",
                            },
                            "replaceAll": {
                                "type": "boolean",
                                "description": "Replace all occurrences of oldString (default false)",
                            },
                        },
                        "required": ["oldString", "newString"],
                    },
                },
            },
            "required": ["filePath", "edits"],
        }
    
    async def execute(self, **params: Any) -> ToolResult:
        """Execute the multi-edit operation."""
        file_path = params.get("filePath", "")
        edits = params.get("edits", [])
        
        if not file_path:
            return ToolResult.err("filePath is required")
        
        if not edits:
            return ToolResult.err("edits array is required and must not be empty")
        
        path = Path(file_path)
        
        # Check if file exists
        if not path.exists():
            return ToolResult.err(f"File not found: {file_path}")
        
        if not path.is_file():
            return ToolResult.err(f"Not a file: {file_path}")
        
        # Read the file content
        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            return ToolResult.err(f"Failed to read file: {e}")
        
        original_content = content
        results = []
        total_replacements = 0
        
        # Apply each edit sequentially
        for i, edit in enumerate(edits):
            old_string = edit.get("oldString", "")
            new_string = edit.get("newString", "")
            replace_all = edit.get("replaceAll", False)
            
            if not old_string:
                results.append({
                    "index": i,
                    "success": False,
                    "error": "oldString is required",
                })
                continue
            
            if old_string == new_string:
                results.append({
                    "index": i,
                    "success": False,
                    "error": "oldString and newString must be different",
                })
                continue
            
            # Count occurrences
            count = content.count(old_string)
            
            if count == 0:
                results.append({
                    "index": i,
                    "success": False,
                    "error": f"Text not found in file: '{old_string[:100]}{'...' if len(old_string) > 100 else ''}'",
                })
                continue
            
            # Perform replacement
            if replace_all:
                content = content.replace(old_string, new_string)
                results.append({
                    "index": i,
                    "success": True,
                    "replacements": count,
                })
                total_replacements += count
            else:
                # Replace only first occurrence
                idx = content.find(old_string)
                content = content[:idx] + new_string + content[idx + len(old_string):]
                results.append({
                    "index": i,
                    "success": True,
                    "replacements": 1,
                })
                total_replacements += 1
        
        # Check if any edits were successful
        successful_edits = sum(1 for r in results if r.get("success"))
        failed_edits = len(results) - successful_edits
        
        if successful_edits == 0:
            return ToolResult.err(
                f"All {len(edits)} edits failed. See details:\n" +
                "\n".join(f"  Edit {r['index']}: {r.get('error', 'Unknown error')}" for r in results)
            )
        
        # Write the modified content back
        try:
            path.write_text(content, encoding="utf-8")
        except Exception as e:
            return ToolResult.err(f"Failed to write file: {e}")
        
        # Build output message
        output = f"Successfully applied {successful_edits}/{len(edits)} edits to {file_path}\n"
        output += f"Total replacements: {total_replacements}\n"
        
        if failed_edits > 0:
            output += f"\nFailed edits:\n"
            for r in results:
                if not r.get("success"):
                    output += f"  Edit {r['index']}: {r.get('error', 'Unknown error')}\n"
        
        return ToolResult.ok(
            output=output,
            metadata={
                "file_path": file_path,
                "total_edits": len(edits),
                "successful_edits": successful_edits,
                "failed_edits": failed_edits,
                "total_replacements": total_replacements,
                "results": results,
            },
            files_changed=[file_path],
        )
