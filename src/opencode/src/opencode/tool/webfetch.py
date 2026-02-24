"""
WebFetch tool for fetching content from URLs.

This tool fetches content from URLs and returns it in various formats
(text, markdown, or HTML). It handles various content types including
images.
"""

from __future__ import annotations

import base64
import re
from typing import Any, Optional

import httpx

from opencode.tool.base import PermissionLevel, Tool, ToolResult

# Optional dependency for HTML to Markdown conversion
try:
    from markdownify import markdownify as md
    HAS_MARKDOWNIFY = True
except ImportError:
    HAS_MARKDOWNIFY = False


class WebFetchTool(Tool):
    """
    Tool for fetching content from URLs.
    
    Supports:
    - Text content extraction
    - HTML to Markdown conversion
    - Image fetching (returns base64)
    - Configurable timeout
    """
    
    MAX_RESPONSE_SIZE = 5 * 1024 * 1024  # 5MB
    DEFAULT_TIMEOUT = 30.0  # seconds
    MAX_TIMEOUT = 120.0  # seconds
    
    @property
    def name(self) -> str:
        return "webfetch"
    
    @property
    def description(self) -> str:
        return """Fetch content from a URL.
        
Use this tool to retrieve content from web pages, APIs, or other URLs.
The content can be returned in different formats:
- markdown: HTML pages are converted to markdown (default)
- text: Plain text extraction from HTML
- html: Raw HTML content

For images, the tool returns base64-encoded data.

Examples:
- Fetch documentation: webfetch(url="https://docs.python.org/3/library/asyncio.html")
- Get API response: webfetch(url="https://api.github.com/repos/python/cpython")
- Fetch as text: webfetch(url="https://example.com", format="text")
"""
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to fetch content from",
                },
                "format": {
                    "type": "string",
                    "enum": ["text", "markdown", "html"],
                    "default": "markdown",
                    "description": "The format to return content in (text, markdown, or html). Defaults to markdown.",
                },
                "timeout": {
                    "type": "number",
                    "description": "Optional timeout in seconds (max 120)",
                },
            },
            "required": ["url"],
        }
    
    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.READ
    
    @property
    def required_permissions(self) -> list[str]:
        return ["webfetch"]
    
    async def execute(self, **params: Any) -> ToolResult:
        """Execute the web fetch."""
        url = params.get("url", "")
        format_type = params.get("format", "markdown")
        timeout = min(params.get("timeout", self.DEFAULT_TIMEOUT), self.MAX_TIMEOUT)
        
        # Validate URL
        if not url.startswith(("http://", "https://")):
            return ToolResult.err("URL must start with http:// or https://")
        
        # Build headers based on format
        accept_header = self._get_accept_header(format_type)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            "Accept": accept_header,
            "Accept-Language": "en-US,en;q=0.9",
        }
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, headers=headers, follow_redirects=True)
                
                # Handle Cloudflare challenge
                if response.status_code == 403 and response.headers.get("cf-mitigated") == "challenge":
                    # Retry with honest UA
                    headers["User-Agent"] = "opencode"
                    response = await client.get(url, headers=headers, follow_redirects=True)
                
                if not response.is_success:
                    return ToolResult.err(f"Request failed with status code: {response.status_code}")
                
                # Check content length
                content_length = response.headers.get("content-length")
                if content_length and int(content_length) > self.MAX_RESPONSE_SIZE:
                    return ToolResult.err("Response too large (exceeds 5MB limit)")
                
                content = response.content
                if len(content) > self.MAX_RESPONSE_SIZE:
                    return ToolResult.err("Response too large (exceeds 5MB limit)")
                
                # Determine content type
                content_type = response.headers.get("content-type", "")
                mime = content_type.split(";")[0].strip().lower() if content_type else ""
                
                # Handle images
                if self._is_image(mime):
                    b64_content = base64.b64encode(content).decode()
                    return ToolResult.ok(
                        output="Image fetched successfully",
                        metadata={
                            "mime": mime,
                            "url": f"data:{mime};base64,{b64_content}",
                            "content_type": content_type,
                        },
                    )
                
                # Decode text content
                try:
                    text_content = content.decode("utf-8")
                except UnicodeDecodeError:
                    text_content = content.decode("latin-1")
                
                # Process based on format
                if format_type == "markdown" and "text/html" in content_type:
                    output = self._html_to_markdown(text_content)
                elif format_type == "text" and "text/html" in content_type:
                    output = self._extract_text_from_html(text_content)
                else:
                    output = text_content
                
                return ToolResult.ok(
                    output=output,
                    metadata={
                        "url": url,
                        "content_type": content_type,
                        "format": format_type,
                    },
                )
                
        except httpx.TimeoutException:
            return ToolResult.err(f"Request timed out after {timeout} seconds")
        except httpx.ConnectError as e:
            return ToolResult.err(f"Failed to connect to URL: {e}")
        except Exception as e:
            return ToolResult.err(f"Failed to fetch URL: {e}")
    
    def _get_accept_header(self, format_type: str) -> str:
        """Get Accept header based on requested format."""
        headers = {
            "markdown": "text/markdown;q=1.0, text/x-markdown;q=0.9, text/plain;q=0.8, text/html;q=0.7, */*;q=0.1",
            "text": "text/plain;q=1.0, text/markdown;q=0.9, text/html;q=0.8, */*;q=0.1",
            "html": "text/html;q=1.0, application/xhtml+xml;q=0.9, text/plain;q=0.8, text/markdown;q=0.7, */*;q=0.1",
        }
        return headers.get(format_type, "*/*")
    
    def _is_image(self, mime: str) -> bool:
        """Check if MIME type is an image (excluding SVG)."""
        image_types = [
            "image/jpeg", "image/png", "image/gif", "image/webp",
            "image/bmp", "image/tiff", "image/x-icon",
        ]
        return mime in image_types
    
    def _html_to_markdown(self, html: str) -> str:
        """Convert HTML to Markdown."""
        if HAS_MARKDOWNIFY:
            return md(html, heading_style="atx", bullets="-")
        # Fallback: simple HTML to text conversion
        return self._extract_text_from_html(html)
    
    def _extract_text_from_html(self, html: str) -> str:
        """Extract plain text from HTML."""
        # Simple text extraction - remove tags
        import re
        # Remove script and style elements
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        # Remove all other tags
        text = re.sub(r'<[^>]+>', ' ', html)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
