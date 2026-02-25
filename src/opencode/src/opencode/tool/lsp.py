"""
LSP (Language Server Protocol) integration tool.

This tool provides code intelligence features through LSP:
- Go to definition
- Find references
- Get hover information
- Document symbols
- Workspace symbols
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
from enum import Enum

from opencode.tool.base import (
    PermissionLevel,
    Tool,
    ToolResult,
)


class LSPMethod(str, Enum):
    """Supported LSP methods."""
    DEFINITION = "textDocument/definition"
    REFERENCES = "textDocument/references"
    HOVER = "textDocument/hover"
    DOCUMENT_SYMBOLS = "textDocument/documentSymbol"
    WORKSPACE_SYMBOLS = "workspace/symbol"
    COMPLETION = "textDocument/completion"
    RENAME = "textDocument/rename"
    FORMATTING = "textDocument/formatting"
    RANGE_FORMATTING = "textDocument/rangeFormatting"


@dataclass
class LSPPosition:
    """Position in a document."""
    line: int
    character: int
    
    def to_lsp(self) -> dict:
        return {"line": self.line, "character": self.character}


@dataclass
class LSPRange:
    """Range in a document."""
    start: LSPPosition
    end: LSPPosition
    
    def to_lsp(self) -> dict:
        return {
            "start": self.start.to_lsp(),
            "end": self.end.to_lsp(),
        }


@dataclass
class LSPResult:
    """Result from an LSP query."""
    kind: str
    name: Optional[str] = None
    location: Optional[dict] = None
    message: Optional[str] = None
    children: list[LSPResult] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "name": self.name,
            "location": self.location,
            "message": self.message,
            "children": [c.to_dict() for c in self.children],
        }


@dataclass
class LSPTool(Tool):
    """
    Tool for LSP-based code intelligence.
    
    Features:
    - Go to definition
    - Find references
    - Hover information
    - Document/workspace symbols
    """
    
    working_directory: Path = Path(".")
    lsp_clients: dict[str, Any] = field(default_factory=dict)
    
    @property
    def name(self) -> str:
        return "lsp"
    
    @property
    def description(self) -> str:
        return """Get code intelligence using Language Server Protocol.

- Go to definition: Find where a symbol is defined
- Find references: Find all usages of a symbol
- Hover: Get type information and documentation
- Document symbols: List all symbols in a file
- Workspace symbols: Search symbols across the project
- Completion: Get code completion suggestions
- Rename: Rename a symbol across the project
- Formatting: Format a document or range"""
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "method": {
                    "type": "string",
                    "enum": ["definition", "references", "hover", "documentSymbols", "workspaceSymbols", "completion", "rename", "formatting"],
                    "description": "The LSP method to call",
                },
                "file_path": {
                    "type": "string",
                    "description": "Path to the file (required for most methods)",
                },
                "line": {
                    "type": "integer",
                    "description": "Line number (0-indexed)",
                },
                "character": {
                    "type": "integer",
                    "description": "Character position in the line (0-indexed)",
                },
                "query": {
                    "type": "string",
                    "description": "Query string for workspace symbols",
                },
                "new_name": {
                    "type": "string",
                    "description": "New name for rename operation",
                },
                "end_line": {
                    "type": "integer",
                    "description": "End line for range formatting (0-indexed)",
                },
                "end_character": {
                    "type": "integer",
                    "description": "End character for range formatting (0-indexed)",
                },
            },
            "required": ["method"],
        }
    
    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.READ
    
    async def execute(self, **params: Any) -> ToolResult:
        """Execute an LSP query."""
        method = params.get("method", "")
        file_path = params.get("file_path")
        line = params.get("line")
        character = params.get("character")
        query = params.get("query")
        new_name = params.get("new_name")
        end_line = params.get("end_line")
        end_character = params.get("end_character")
        
        # Map method names to LSP methods
        method_map = {
            "definition": LSPMethod.DEFINITION,
            "references": LSPMethod.REFERENCES,
            "hover": LSPMethod.HOVER,
            "documentSymbols": LSPMethod.DOCUMENT_SYMBOLS,
            "workspaceSymbols": LSPMethod.WORKSPACE_SYMBOLS,
            "completion": LSPMethod.COMPLETION,
            "rename": LSPMethod.RENAME,
            "formatting": LSPMethod.FORMATTING,
        }
        
        lsp_method = method_map.get(method)
        if not lsp_method:
            return ToolResult.err(f"Unknown LSP method: {method}")
        
        # Validate required parameters
        if lsp_method in [LSPMethod.DEFINITION, LSPMethod.REFERENCES, LSPMethod.HOVER, LSPMethod.COMPLETION, LSPMethod.RENAME]:
            if not file_path or line is None or character is None:
                return ToolResult.err(
                    f"Method '{method}' requires file_path, line, and character parameters"
                )
        
        if lsp_method == LSPMethod.WORKSPACE_SYMBOLS and not query:
            return ToolResult.err("Method 'workspaceSymbols' requires a query parameter")
        
        if lsp_method == LSPMethod.RENAME and not new_name:
            return ToolResult.err("Method 'rename' requires a new_name parameter")
        
        try:
            # Get or create LSP client for the file type
            if file_path:
                client = await self._get_client(file_path)
                if not client:
                    return ToolResult.err(
                        f"No LSP client available for file type: {Path(file_path).suffix}"
                    )
            else:
                # Use first available client for workspace symbols
                client = next(iter(self.lsp_clients.values()), None)
                if not client:
                    return ToolResult.err("No LSP clients available")
            
            # Build and send request
            result = await self._send_request(
                client, lsp_method, file_path, line, character, query, new_name, end_line, end_character
            )
            
            # Format output
            output = self._format_result(result, method)
            
            return ToolResult.ok(
                output=output,
                metadata={"method": method, "result": result},
            )
        
        except Exception as e:
            return ToolResult.err(f"LSP query failed: {e}")
    
    async def _get_client(self, file_path: str) -> Optional[Any]:
        """Get or create an LSP client for the given file type."""
        suffix = Path(file_path).suffix
        
        # Check if we already have a client
        if suffix in self.lsp_clients:
            return self.lsp_clients[suffix]
        
        # Map file extensions to LSP server commands
        server_commands = {
            ".py": ["pylsp", "pyright-langserver", "ruff server"],
            ".ts": ["typescript-language-server", "--stdio"],
            ".js": ["typescript-language-server", "--stdio"],
            ".tsx": ["typescript-language-server", "--stdio"],
            ".jsx": ["typescript-language-server", "--stdio"],
            ".go": ["gopls"],
            ".rs": ["rust-analyzer"],
            ".java": ["jdtls"],
            ".cpp": ["clangd"],
            ".c": ["clangd"],
            ".h": ["clangd"],
        }
        
        command = server_commands.get(suffix)
        if not command:
            return None
        
        # Create LSP client (simplified - real implementation would use proper LSP library)
        client = await self._create_lsp_client(command)
        if client:
            self.lsp_clients[suffix] = client
        
        return client
    
    async def _create_lsp_client(self, command: list[str]) -> Optional[Any]:
        """Create an LSP client process."""
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.working_directory,
            )
            
            # Initialize LSP connection
            init_params = {
                "processId": process.pid,
                "rootUri": self.working_directory.as_uri(),
                "capabilities": {
                    "textDocument": {
                        "definition": {"linkSupport": True},
                        "references": {},
                        "hover": {"contentFormat": ["markdown", "plaintext"]},
                        "documentSymbol": {
                            "symbolKind": {"valueSet": list(range(1, 27))},
                        },
                    },
                    "workspace": {
                        "symbol": {
                            "symbolKind": {"valueSet": list(range(1, 27))},
                        },
                    },
                },
            }
            
            # Send initialize request
            await self._send_lsp_message(
                process, "initialize", init_params
            )
            
            # Send initialized notification
            await self._send_lsp_notification(process, "initialized", {})
            
            return process
        
        except Exception:
            return None
    
    async def _send_lsp_message(
        self,
        process: Any,
        method: str,
        params: dict,
        request_id: int = 1,
    ) -> Optional[dict]:
        """Send an LSP request and wait for response."""
        if not process.stdin or not process.stdout:
            return None
        
        message = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }
        
        content = json.dumps(message)
        header = f"Content-Length: {len(content)}\r\n\r\n"
        
        process.stdin.write(header.encode())
        process.stdin.write(content.encode())
        await process.stdin.drain()
        
        # Read response (simplified)
        response = await self._read_lsp_response(process)
        return response
    
    async def _send_lsp_notification(
        self,
        process: Any,
        method: str,
        params: dict,
    ) -> None:
        """Send an LSP notification (no response expected)."""
        if not process.stdin:
            return
        
        message = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }
        
        content = json.dumps(message)
        header = f"Content-Length: {len(content)}\r\n\r\n"
        
        process.stdin.write(header.encode())
        process.stdin.write(content.encode())
        await process.stdin.drain()
    
    async def _read_lsp_response(self, process: Any) -> Optional[dict]:
        """Read an LSP response from the process."""
        if not process.stdout:
            return None
        
        # Read headers
        headers = {}
        while True:
            line = await process.stdout.readline()
            if not line or line == b"\r\n":
                break
            if line:
                parts = line.decode().strip().split(": ", 1)
                if len(parts) == 2:
                    headers[parts[0]] = parts[1]
        
        # Read content
        content_length = int(headers.get("Content-Length", 0))
        if content_length > 0:
            content = await process.stdout.read(content_length)
            return json.loads(content)
        
        return None
    
    async def _send_request(
        self,
        client: Any,
        method: LSPMethod,
        file_path: Optional[str],
        line: Optional[int],
        character: Optional[int],
        query: Optional[str] = None,
        new_name: Optional[str] = None,
        end_line: Optional[int] = None,
        end_character: Optional[int] = None,
    ) -> Any:
        """Send an LSP request."""
        params = {}
        
        if file_path:
            path = self.working_directory / file_path
            params["textDocument"] = {"uri": path.as_uri()}
        
        if line is not None and character is not None:
            params["position"] = {"line": line, "character": character}
        
        if query:
            params["query"] = query
        
        if method == LSPMethod.REFERENCES:
            params["context"] = {"includeDeclaration": True}
        
        if method == LSPMethod.RENAME and new_name:
            params["newName"] = new_name
        
        if method == LSPMethod.FORMATTING:
            params["options"] = {
                "tabSize": 4,
                "insertSpaces": True,
            }
        
        if method == LSPMethod.RANGE_FORMATTING:
            if end_line is not None and end_character is not None:
                params["range"] = {
                    "start": {"line": line or 0, "character": character or 0},
                    "end": {"line": end_line, "character": end_character},
                }
                params["options"] = {
                    "tabSize": 4,
                    "insertSpaces": True,
                }
        
        return await self._send_lsp_message(client, method.value, params)
    
    def _format_result(self, result: Any, method: str) -> str:
        """Format LSP result for display."""
        if not result:
            return f"No {method} found"
        
        if "result" not in result:
            return f"LSP error: {result.get('error', 'Unknown error')}"
        
        lsp_result = result["result"]
        
        if lsp_result is None:
            return f"No {method} found"
        
        # Handle different result types
        if method == "definition":
            return self._format_location_result(lsp_result, "Definition")
        
        elif method == "references":
            return self._format_location_result(lsp_result, "References")
        
        elif method == "hover":
            return self._format_hover_result(lsp_result)
        
        elif method == "documentSymbols":
            return self._format_symbols_result(lsp_result)
        
        elif method == "workspaceSymbols":
            return self._format_symbols_result(lsp_result)
        
        elif method == "completion":
            return self._format_completion_result(lsp_result)
        
        elif method == "rename":
            return self._format_rename_result(lsp_result)
        
        elif method == "formatting":
            return self._format_formatting_result(lsp_result)
        
        return json.dumps(lsp_result, indent=2)
    
    def _format_completion_result(self, result: Any) -> str:
        """Format completion result."""
        if not result:
            return "No completions found"
        
        if isinstance(result, dict) and "items" in result:
            items = result["items"]
        elif isinstance(result, list):
            items = result
        else:
            return "No completions found"
        
        if not items:
            return "No completions found"
        
        lines = [f"Completions ({len(items)} found):"]
        for item in items[:20]:  # Limit to 20 items
            label = item.get("label", "Unknown")
            kind = item.get("kind", 0)
            detail = item.get("detail", "")
            
            kind_names = [
                "Text", "Method", "Function", "Constructor",
                "Field", "Variable", "Class", "Interface",
                "Module", "Property", "Unit", "Value",
                "Enum", "Keyword", "Snippet", "Color",
                "File", "Reference", "Folder", "EnumMember",
                "Constant", "Struct", "Event", "Operator",
                "TypeParameter",
            ]
            kind_name = kind_names[kind - 1] if 0 < kind <= len(kind_names) else "Unknown"
            
            if detail:
                lines.append(f"  [{kind_name}] {label} - {detail}")
            else:
                lines.append(f"  [{kind_name}] {label}")
        
        if len(items) > 20:
            lines.append(f"  ... and {len(items) - 20} more")
        
        return "\n".join(lines)
    
    def _format_rename_result(self, result: Any) -> str:
        """Format rename result."""
        if not result:
            return "Rename failed - no changes made"
        
        if "documentChanges" in result:
            changes = result["documentChanges"]
            lines = [f"Rename successful. Modified {len(changes)} file(s):"]
            for change in changes:
                if "textDocument" in change:
                    uri = change["textDocument"].get("uri", "Unknown")
                    edits = change.get("edits", [])
                    lines.append(f"  {uri}: {len(edits)} edit(s)")
            return "\n".join(lines)
        
        if "changes" in result:
            changes = result["changes"]
            lines = [f"Rename successful. Modified {len(changes)} file(s):"]
            for uri, edits in changes.items():
                lines.append(f"  {uri}: {len(edits)} edit(s)")
            return "\n".join(lines)
        
        return "Rename completed"
    
    def _format_formatting_result(self, result: Any) -> str:
        """Format formatting result."""
        if not result:
            return "No formatting changes needed"
        
        if isinstance(result, list):
            lines = [f"Formatting applied {len(result)} edit(s):"]
            for edit in result[:10]:
                range_info = edit.get("range", {})
                start = range_info.get("start", {})
                new_text = edit.get("newText", "")
                line_num = start.get("line", 0) + 1
                lines.append(f"  Line {line_num}: {len(new_text)} char(s)")
            if len(result) > 10:
                lines.append(f"  ... and {len(result) - 10} more")
            return "\n".join(lines)
        
        return "Formatting applied"
    
    def _format_location_result(self, result: Any, title: str) -> str:
        """Format location results (definition, references)."""
        if isinstance(result, list):
            if not result:
                return f"No {title.lower()} found"
            
            lines = [f"{title} ({len(result)} found):"]
            for loc in result:
                if "uri" in loc:
                    uri = loc["uri"]
                    range_info = loc.get("range", {})
                    start = range_info.get("start", {})
                    line_num = start.get("line", 0) + 1
                    lines.append(f"  {uri}:{line_num}")
                elif "targetUri" in loc:
                    # LocationLink
                    lines.append(f"  {loc['targetUri']}")
            return "\n".join(lines)
        
        # Single location
        if isinstance(result, dict) and "uri" in result:
            range_info = result.get("range", {})
            start = range_info.get("start", {})
            line_num = start.get("line", 0) + 1
            return f"{title}: {result['uri']}:{line_num}"
        
        return f"{title}: {result}"
    
    def _format_hover_result(self, result: Any) -> str:
        """Format hover result."""
        if not result:
            return "No hover information available"
        
        contents = result.get("contents", "")
        
        if isinstance(contents, str):
            return contents
        
        if isinstance(contents, list):
            return "\n".join(str(c) for c in contents)
        
        if isinstance(contents, dict):
            return contents.get("value", str(contents))
        
        return str(contents)
    
    def _format_symbols_result(self, result: Any) -> str:
        """Format document/workspace symbols result."""
        if not result:
            return "No symbols found"
        
        if isinstance(result, list):
            lines = [f"Symbols ({len(result)} found):"]
            for symbol in result:
                name = symbol.get("name", "Unknown")
                kind = symbol.get("kind", 0)
                kind_names = [
                    "File", "Module", "Namespace", "Package",
                    "Class", "Method", "Property", "Field",
                    "Constructor", "Enum", "Interface", "Function",
                    "Variable", "Constant", "String", "Number",
                    "Boolean", "Array", "Object", "Key",
                    "Null", "EnumMember", "Struct", "Event",
                    "Operator", "TypeParameter",
                ]
                kind_name = kind_names[kind - 1] if 0 < kind <= len(kind_names) else "Unknown"
                
                location = symbol.get("location", {})
                uri = location.get("uri", "")
                if uri:
                    path = Path(uri).name
                    lines.append(f"  [{kind_name}] {name} ({path})")
                else:
                    lines.append(f"  [{kind_name}] {name}")
            
            return "\n".join(lines)
        
        return str(result)


# Factory function
def create_lsp_tool(working_directory: Path = Path(".")) -> LSPTool:
    return LSPTool(working_directory=working_directory)
