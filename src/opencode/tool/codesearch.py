"""
CodeSearch tool for searching code and documentation.

This tool uses Exa AI's MCP API to search for code examples,
API documentation, and SDK usage patterns.
"""

from __future__ import annotations

import json
import os
from typing import Any

import httpx

from opencode.tool.base import PermissionLevel, Tool, ToolResult


class CodeSearchTool(Tool):
    """
    Tool for searching code examples and documentation.
    
    Uses Exa AI's code search to find:
    - Code examples and snippets
    - API documentation
    - SDK usage patterns
    - Library tutorials
    """
    
    API_URL = "https://mcp.exa.ai/mcp"
    DEFAULT_TOKENS = 5000
    MIN_TOKENS = 1000
    MAX_TOKENS = 50000
    
    @property
    def name(self) -> str:
        return "codesearch"
    
    @property
    def description(self) -> str:
        return """Search for code examples, API documentation, and SDK usage patterns.
        
Use this tool to find relevant code snippets and documentation for:
- Libraries and frameworks
- API usage examples
- SDK documentation
- Programming patterns

Examples:
- Find React patterns: codesearch(query="React useState hook examples")
- Python libraries: codesearch(query="Python pandas dataframe filtering")
- Framework docs: codesearch(query="Next.js partial prerendering configuration")
"""
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Search query to find relevant context for APIs, Libraries, and SDKs. "
                        "For example, 'React useState hook examples', 'Python pandas dataframe filtering'"
                    ),
                },
                "tokensNum": {
                    "type": "integer",
                    "description": (
                        "Number of tokens to return (1000-50000). Default is 5000 tokens. "
                        "Adjust based on how much context you need."
                    ),
                    "default": self.DEFAULT_TOKENS,
                    "minimum": self.MIN_TOKENS,
                    "maximum": self.MAX_TOKENS,
                },
            },
            "required": ["query"],
        }
    
    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.READ
    
    @property
    def required_permissions(self) -> list[str]:
        return ["codesearch"]
    
    async def execute(self, **params: Any) -> ToolResult:
        """Execute the code search."""
        query = params.get("query", "")
        tokens_num = params.get("tokensNum", self.DEFAULT_TOKENS)
        tokens_num = max(self.MIN_TOKENS, min(tokens_num, self.MAX_TOKENS))
        
        if not query:
            return ToolResult.err("Search query is required")
        
        # Check for API key
        api_key = os.environ.get("EXA_API_KEY")
        if not api_key:
            return ToolResult.err(
                "EXA_API_KEY environment variable not set. "
                "Get your API key at https://exa.ai"
            )
        
        # Build MCP request
        request_body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "get_code_context_exa",
                "arguments": {
                    "query": query,
                    "tokensNum": tokens_num,
                },
            },
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.API_URL,
                    json=request_body,
                    headers=headers,
                )
                
                if not response.is_success:
                    return ToolResult.err(
                        f"Code search failed with status {response.status_code}: {response.text}"
                    )
                
                # Parse SSE response
                response_text = response.text
                result = self._parse_sse_response(response_text)
                
                if not result:
                    return ToolResult.ok(
                        output=(
                            "No code snippets or documentation found. "
                            "Please try a different query, be more specific about the library "
                            "or programming concept, or check the spelling of framework names."
                        ),
                        metadata={"query": query},
                    )
                
                return ToolResult.ok(
                    output=result,
                    metadata={
                        "query": query,
                        "tokens_requested": tokens_num,
                    },
                )
                
        except httpx.TimeoutException:
            return ToolResult.err("Code search request timed out")
        except Exception as e:
            return ToolResult.err(f"Code search failed: {e}")
    
    def _parse_sse_response(self, text: str) -> str:
        """Parse Server-Sent Events response from Exa API."""
        for line in text.split("\n"):
            if line.startswith("data: "):
                try:
                    data = json.loads(line[6:])
                    if "result" in data and "content" in data["result"]:
                        for content in data["result"]["content"]:
                            if content.get("type") == "text":
                                return content.get("text", "")
                except json.JSONDecodeError:
                    continue
        
        return ""
