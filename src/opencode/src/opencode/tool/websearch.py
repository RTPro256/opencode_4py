"""
WebSearch tool for searching the web.

This tool uses Exa AI's MCP API to perform web searches and return
relevant results. Requires EXA_API_KEY environment variable.
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional

import httpx

from opencode.tool.base import PermissionLevel, Tool, ToolResult


class WebSearchTool(Tool):
    """
    Tool for searching the web using Exa AI.
    
    Provides web search capabilities with:
    - High-quality search results
    - Content extraction
    - Configurable result count
    """
    
    API_URL = "https://mcp.exa.ai/mcp"
    DEFAULT_NUM_RESULTS = 5
    MAX_NUM_RESULTS = 20
    
    @property
    def name(self) -> str:
        return "websearch"
    
    @property
    def description(self) -> str:
        return """Search the web for information.
        
Use this tool to find current information on the internet. Returns
relevant search results with titles, URLs, and content snippets.

Examples:
- Search for documentation: websearch(query="Python asyncio tutorial")
- Find latest news: websearch(query="latest AI developments 2024")
- Research a topic: websearch(query="best practices for REST API design")
"""
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query",
                },
                "numResults": {
                    "type": "integer",
                    "description": "Number of results to return (default 5, max 20)",
                    "default": self.DEFAULT_NUM_RESULTS,
                    "minimum": 1,
                    "maximum": self.MAX_NUM_RESULTS,
                },
                "useAutoprompt": {
                    "type": "boolean",
                    "description": "Let Exa automatically optimize your query",
                    "default": True,
                },
            },
            "required": ["query"],
        }
    
    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.READ
    
    @property
    def required_permissions(self) -> list[str]:
        return ["websearch"]
    
    async def execute(self, **params: Any) -> ToolResult:
        """Execute the web search."""
        query = params.get("query", "")
        num_results = min(params.get("numResults", self.DEFAULT_NUM_RESULTS), self.MAX_NUM_RESULTS)
        use_autoprompt = params.get("useAutoprompt", True)
        
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
                "name": "web_search_exa",
                "arguments": {
                    "query": query,
                    "numResults": num_results,
                    "useAutoprompt": use_autoprompt,
                    "contents": {
                        "text": True,
                    },
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
                        f"Search failed with status {response.status_code}: {response.text}"
                    )
                
                # Parse SSE response
                response_text = response.text
                results = self._parse_sse_response(response_text)
                
                if not results:
                    return ToolResult.ok(
                        output="No results found. Try a different query.",
                        metadata={"query": query},
                    )
                
                # Format results
                output = self._format_results(results, query)
                
                return ToolResult.ok(
                    output=output,
                    metadata={
                        "query": query,
                        "num_results": len(results),
                    },
                )
                
        except httpx.TimeoutException:
            return ToolResult.err("Search request timed out")
        except Exception as e:
            return ToolResult.err(f"Search failed: {e}")
    
    def _parse_sse_response(self, text: str) -> list[dict[str, Any]]:
        """Parse Server-Sent Events response from Exa API."""
        results = []
        
        for line in text.split("\n"):
            if line.startswith("data: "):
                try:
                    data = json.loads(line[6:])
                    if "result" in data and "content" in data["result"]:
                        for content in data["result"]["content"]:
                            if content.get("type") == "text":
                                # Parse the text content which contains results
                                text_content = content.get("text", "")
                                try:
                                    parsed = json.loads(text_content)
                                    if isinstance(parsed, list):
                                        results.extend(parsed)
                                    elif isinstance(parsed, dict) and "results" in parsed:
                                        results.extend(parsed["results"])
                                except json.JSONDecodeError:
                                    pass
                except json.JSONDecodeError:
                    continue
        
        return results
    
    def _format_results(self, results: list[dict[str, Any]], query: str) -> str:
        """Format search results for display."""
        lines = [f"## Search Results for: {query}", ""]
        
        for i, result in enumerate(results, 1):
            title = result.get("title", "Untitled")
            url = result.get("url", result.get("link", ""))
            snippet = result.get("text", result.get("snippet", result.get("content", "")))
            
            lines.append(f"### {i}. {title}")
            if url:
                lines.append(f"**URL:** {url}")
            if snippet:
                # Truncate long snippets
                if len(snippet) > 500:
                    snippet = snippet[:500] + "..."
                lines.append(f"**Content:** {snippet}")
            lines.append("")
        
        return "\n".join(lines)
