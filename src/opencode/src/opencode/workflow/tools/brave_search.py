"""
Brave Search Tool

Integration with Brave Search API for web search capabilities.
"""

import logging
from typing import Any, Dict, List, Optional, ClassVar

import httpx

from opencode.workflow.tools.registry import BaseTool, ToolResult, ToolSchema, ToolRegistry

logger = logging.getLogger(__name__)


@ToolRegistry.register("brave_search")
class BraveSearchTool(BaseTool):
    """
    Brave Search Tool - Web search using Brave Search API.
    
    This tool provides web search capabilities using the Brave Search API.
    Requires an API key from https://brave.com/search/api/
    
    Configuration:
        api_key: Brave Search API key (required)
        base_url: API base URL (optional, defaults to Brave's API)
        count: Number of results to return (default: 10)
        country: Country code for results (default: "US")
        search_lang: Search language (default: "en")
    
    Example:
        tool = BraveSearchTool(config={"api_key": "your-api-key"})
        result = await tool.execute(query="Python async programming")
        if result.success:
            for item in result.data["results"]:
                print(item["title"], item["url"])
    """
    
    _schema = ToolSchema(
        name="brave_search",
        description="Search the web using Brave Search API",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query string",
                },
                "count": {
                    "type": "integer",
                    "description": "Number of results to return",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 50,
                },
                "offset": {
                    "type": "integer",
                    "description": "Offset for pagination",
                    "default": 0,
                },
                "country": {
                    "type": "string",
                    "description": "Country code for search results",
                    "default": "US",
                },
                "search_lang": {
                    "type": "string",
                    "description": "Search language",
                    "default": "en",
                },
                "freshness": {
                    "type": "string",
                    "description": "Freshness filter (pd, pw, pm, py)",
                },
            },
        },
        required_params=["query"],
        returns="object",
        category="search",
        requires_auth=True,
        auth_type="api_key",
    )
    
    BASE_URL = "https://api.search.brave.com/res/v1/web/search"
    
    @classmethod
    def get_schema(cls) -> ToolSchema:
        """Return the schema for this tool."""
        return cls._schema
    
    async def initialize(self) -> bool:
        """Initialize the tool and validate API key."""
        if not self.config.get("api_key"):
            logger.warning("Brave Search API key not configured")
            return False
        self._initialized = True
        return True
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        """
        Execute a web search using Brave Search API.
        
        Args:
            params: Dictionary containing:
                - query: Search query string (required)
                - count: Number of results to return (1-50)
                - offset: Offset for pagination
                - country: Country code for results
                - search_lang: Search language
                - freshness: Freshness filter (pd=past day, pw=past week, 
                          pm=past month, py=past year)
            
        Returns:
            ToolResult with search results
        """
        if not self._initialized:
            await self.initialize()
        
        # Extract parameters
        query = params.get("query")
        if not query:
            return ToolResult(
                success=False,
                error="Required parameter 'query' is missing",
            )
        
        api_key = self.config.get("api_key")
        if not api_key:
            return ToolResult(
                success=False,
                error="Brave Search API key not configured. "
                      "Set 'api_key' in tool configuration.",
            )
        
        # Build request parameters
        request_params = {
            "q": query,
            "count": params.get("count", self.config.get("count", 10)),
            "offset": params.get("offset", 0),
            "country": params.get("country", self.config.get("country", "US")),
            "search_lang": params.get("search_lang", self.config.get("search_lang", "en")),
        }
        
        freshness = params.get("freshness")
        if freshness:
            request_params["freshness"] = freshness
        
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": api_key,
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    self.BASE_URL,
                    params=request_params,
                    headers=headers,
                )
                
                if response.status_code == 401:
                    return ToolResult(
                        success=False,
                        error="Invalid Brave Search API key",
                    )
                
                if response.status_code == 429:
                    return ToolResult(
                        success=False,
                        error="Brave Search API rate limit exceeded",
                    )
                
                response.raise_for_status()
                data = response.json()
            
            # Parse and format results
            results = self._parse_results(data)
            
            return ToolResult(
                success=True,
                data={
                    "query": query,
                    "results": results,
                    "total_results": len(results),
                },
                metadata={
                    "source": "brave_search",
                    "status_code": response.status_code,
                },
            )
            
        except httpx.TimeoutException:
            return ToolResult(
                success=False,
                error="Brave Search API request timed out",
            )
        except httpx.HTTPStatusError as e:
            return ToolResult(
                success=False,
                error=f"Brave Search API error: {e.response.status_code}",
            )
        except Exception as e:
            logger.exception(f"Brave Search error: {e}")
            return ToolResult(
                success=False,
                error=f"Search failed: {str(e)}",
            )
    
    def _parse_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse Brave Search API response into standardized format.
        
        Args:
            data: Raw API response
            
        Returns:
            List of search results
        """
        results = []
        
        # Extract web results
        web_results = data.get("web", {}).get("results", [])
        
        for item in web_results:
            result = {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "description": item.get("description", ""),
                "type": "web",
            }
            
            # Add extra fields if available
            if "age" in item:
                result["age"] = item["age"]
            if "language" in item:
                result["language"] = item["language"]
            if "family_friendly" in item:
                result["family_friendly"] = item["family_friendly"]
            
            results.append(result)
        
        # Extract news results if available
        news_results = data.get("news", {}).get("results", [])
        for item in news_results:
            result = {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "description": item.get("description", ""),
                "type": "news",
                "age": item.get("age", ""),
                "source": item.get("source", ""),
            }
            results.append(result)
        
        return results
