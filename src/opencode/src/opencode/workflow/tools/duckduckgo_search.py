"""
DuckDuckGo Search Tool

Integration with DuckDuckGo for web search capabilities (no API key required).
"""

import logging
from typing import Any, Dict, List, Optional, ClassVar
import urllib.parse

import httpx

from opencode.workflow.tools.registry import BaseTool, ToolResult, ToolSchema, ToolRegistry

logger = logging.getLogger(__name__)


@ToolRegistry.register("duckduckgo_search")
class DuckDuckGoSearchTool(BaseTool):
    """
    DuckDuckGo Search Tool - Web search without API key requirement.
    
    This tool provides web search capabilities using DuckDuckGo's
    instant answer API and HTML search fallback. No API key required.
    
    Configuration:
        max_results: Maximum number of results to return (default: 10)
        region: Region for search results (default: "us-en")
        safe_search: Enable safe search (default: True)
        timeout: Request timeout in seconds (default: 30)
    
    Example:
        tool = DuckDuckGoSearchTool()
        result = await tool.execute({"query": "Python async programming"})
        if result.success:
            for item in result.data["results"]:
                print(item["title"], item["url"])
    """
    
    _schema = ToolSchema(
        name="duckduckgo_search",
        description="Search the web using DuckDuckGo (no API key required)",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query string",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 50,
                },
                "region": {
                    "type": "string",
                    "description": "Region for search results (e.g., 'us-en', 'uk-en')",
                    "default": "us-en",
                },
                "safe_search": {
                    "type": "boolean",
                    "description": "Enable safe search",
                    "default": True,
                },
            },
        },
        required_params=["query"],
        returns="object",
        category="search",
        requires_auth=False,
    )
    
    # DuckDuckGo endpoints
    INSTANT_ANSWER_URL = "https://api.duckduckgo.com/"
    HTML_SEARCH_URL = "https://html.duckduckgo.com/html/"
    
    @classmethod
    def get_schema(cls) -> ToolSchema:
        """Return the schema for this tool."""
        return cls._schema
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        """
        Execute a web search using DuckDuckGo.
        
        Args:
            params: Dictionary containing:
                - query: Search query string (required)
                - max_results: Maximum number of results
                - region: Region for search results
                - safe_search: Enable safe search
            
        Returns:
            ToolResult with search results
        """
        query = params.get("query")
        if not query:
            return ToolResult(
                success=False,
                error="Required parameter 'query' is missing",
            )
        
        max_results = params.get("max_results", self.config.get("max_results", 10))
        region = params.get("region", self.config.get("region", "us-en"))
        safe_search = params.get("safe_search", self.config.get("safe_search", True))
        timeout = self.config.get("timeout", 30)
        
        results = []
        
        try:
            # Try instant answer API first
            instant_results = await self._instant_answer_search(
                query, region, safe_search, timeout
            )
            results.extend(instant_results)
            
            # If not enough results, fall back to HTML search
            if len(results) < max_results:
                html_results = await self._html_search(
                    query, region, safe_search, timeout, max_results - len(results)
                )
                results.extend(html_results)
            
            # Limit results
            results = results[:max_results]
            
            return ToolResult(
                success=True,
                data={
                    "query": query,
                    "results": results,
                    "total_results": len(results),
                },
                metadata={
                    "source": "duckduckgo_search",
                },
            )
            
        except httpx.TimeoutException:
            return ToolResult(
                success=False,
                error="DuckDuckGo search request timed out",
            )
        except Exception as e:
            logger.exception(f"DuckDuckGo search error: {e}")
            return ToolResult(
                success=False,
                error=f"Search failed: {str(e)}",
            )
    
    async def _instant_answer_search(
        self,
        query: str,
        region: str,
        safe_search: bool,
        timeout: float,
    ) -> List[Dict[str, Any]]:
        """
        Search using DuckDuckGo Instant Answer API.
        
        Args:
            query: Search query
            region: Region code
            safe_search: Safe search setting
            timeout: Request timeout
            
        Returns:
            List of search results
        """
        results = []
        
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1,
            "kl": region,
        }
        
        if safe_search:
            params["kp"] = 1
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(
                    self.INSTANT_ANSWER_URL,
                    params=params,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
            
            # Extract abstract (main answer)
            if data.get("Abstract"):
                results.append({
                    "title": data.get("Heading", "Instant Answer"),
                    "url": data.get("AbstractURL", ""),
                    "description": data.get("Abstract", ""),
                    "type": "instant_answer",
                    "source": data.get("AbstractSource", ""),
                })
            
            # Extract related topics
            for topic in data.get("RelatedTopics", []):
                if isinstance(topic, dict) and "Text" in topic:
                    results.append({
                        "title": topic.get("FirstURL", "").split("/")[-1].replace("_", " "),
                        "url": topic.get("FirstURL", ""),
                        "description": topic.get("Text", ""),
                        "type": "related_topic",
                    })
            
            # Extract results
            for result in data.get("Results", []):
                if isinstance(result, dict):
                    results.append({
                        "title": result.get("FirstURL", "").split("/")[-1].replace("_", " "),
                        "url": result.get("FirstURL", ""),
                        "description": result.get("Text", ""),
                        "type": "result",
                    })
                    
        except Exception as e:
            logger.debug(f"Instant answer search failed: {e}")
        
        return results
    
    async def _html_search(
        self,
        query: str,
        region: str,
        safe_search: bool,
        timeout: float,
        max_results: int,
    ) -> List[Dict[str, Any]]:
        """
        Search using DuckDuckGo HTML endpoint (fallback).
        
        Args:
            query: Search query
            region: Region code
            safe_search: Safe search setting
            timeout: Request timeout
            max_results: Maximum results to return
            
        Returns:
            List of search results
        """
        results = []
        
        params = {
            "q": query,
            "kl": region,
        }
        
        if safe_search:
            params["kp"] = "1"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html",
        }
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(
                    self.HTML_SEARCH_URL,
                    params=params,
                    headers=headers,
                )
                response.raise_for_status()
                html = response.text
            
            # Parse HTML results (simple regex-based parsing)
            import re
            
            # Find result links
            pattern = r'<a rel="nofollow" class="result__a" href="([^"]+)"[^>]*>([^<]+)</a>'
            matches = re.findall(pattern, html)
            
            for url, title in matches[:max_results]:
                # DuckDuckGo uses redirect URLs, extract actual URL
                if "uddg=" in url:
                    actual_url = urllib.parse.unquote(
                        url.split("uddg=")[-1].split("&")[0]
                    )
                else:
                    actual_url = url
                
                results.append({
                    "title": title.strip(),
                    "url": actual_url,
                    "description": "",  # Would need more complex parsing
                    "type": "web",
                })
                
        except Exception as e:
            logger.debug(f"HTML search failed: {e}")
        
        return results
