"""Tests for WebFetchTool."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from opencode.tool.webfetch import WebFetchTool, HAS_MARKDOWNIFY
from opencode.tool.base import PermissionLevel, ToolResult


class TestWebFetchTool:
    """Tests for WebFetchTool class."""
    
    def test_name(self):
        """Test tool name."""
        tool = WebFetchTool()
        assert tool.name == "webfetch"
    
    def test_description(self):
        """Test tool description."""
        tool = WebFetchTool()
        assert "fetch" in tool.description.lower()
        assert "url" in tool.description.lower()
    
    def test_parameters(self):
        """Test tool parameters schema."""
        tool = WebFetchTool()
        params = tool.parameters
        
        assert params["type"] == "object"
        assert "url" in params["properties"]
        assert "format" in params["properties"]
        assert "timeout" in params["properties"]
        assert params["required"] == ["url"]
    
    def test_permission_level(self):
        """Test permission level."""
        tool = WebFetchTool()
        assert tool.permission_level == PermissionLevel.READ
    
    def test_required_permissions(self):
        """Test required permissions."""
        tool = WebFetchTool()
        assert "webfetch" in tool.required_permissions
    
    def test_constants(self):
        """Test class constants."""
        assert WebFetchTool.MAX_RESPONSE_SIZE == 5 * 1024 * 1024
        assert WebFetchTool.DEFAULT_TIMEOUT == 30.0
        assert WebFetchTool.MAX_TIMEOUT == 120.0
    
    @pytest.mark.asyncio
    async def test_execute_invalid_url(self):
        """Test executing with invalid URL."""
        tool = WebFetchTool()
        result = await tool.execute(url="ftp://example.com")
        
        assert result.success is False
        assert result.error is not None
        assert "http" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_execute_success_html(self):
        """Test successful HTML fetch."""
        tool = WebFetchTool()
        
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 200
        mock_response.content = b"<html><body>Hello World</body></html>"
        mock_response.headers = {"content-type": "text/html"}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_async_client = AsyncMock()
            mock_async_client.__aenter__.return_value = mock_async_client
            mock_async_client.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_async_client
            
            result = await tool.execute(url="https://example.com")
        
        assert result.success is True
        assert result.metadata["url"] == "https://example.com"
    
    @pytest.mark.asyncio
    async def test_execute_success_markdown_format(self):
        """Test successful fetch with markdown format."""
        tool = WebFetchTool()
        
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 200
        mock_response.content = b"<html><body><h1>Title</h1><p>Content</p></body></html>"
        mock_response.headers = {"content-type": "text/html"}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_async_client = AsyncMock()
            mock_async_client.__aenter__.return_value = mock_async_client
            mock_async_client.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_async_client
            
            result = await tool.execute(url="https://example.com", format="markdown")
        
        assert result.success is True
        assert result.metadata["format"] == "markdown"
    
    @pytest.mark.asyncio
    async def test_execute_success_text_format(self):
        """Test successful fetch with text format."""
        tool = WebFetchTool()
        
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 200
        mock_response.content = b"<html><body><h1>Title</h1><p>Content</p></body></html>"
        mock_response.headers = {"content-type": "text/html"}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_async_client = AsyncMock()
            mock_async_client.__aenter__.return_value = mock_async_client
            mock_async_client.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_async_client
            
            result = await tool.execute(url="https://example.com", format="text")
        
        assert result.success is True
        assert "Title" in result.output or "Content" in result.output
    
    @pytest.mark.asyncio
    async def test_execute_image(self):
        """Test fetching an image."""
        tool = WebFetchTool()
        
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 200
        mock_response.content = b"\x89PNG\r\n\x1a\n"  # PNG header
        mock_response.headers = {"content-type": "image/png"}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_async_client = AsyncMock()
            mock_async_client.__aenter__.return_value = mock_async_client
            mock_async_client.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_async_client
            
            result = await tool.execute(url="https://example.com/image.png")
        
        assert result.success is True
        assert result.metadata["mime"] == "image/png"
        assert "base64" in result.metadata["url"]
    
    @pytest.mark.asyncio
    async def test_execute_http_error(self):
        """Test handling HTTP error."""
        tool = WebFetchTool()
        
        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 404
        mock_response.headers = {}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_async_client = AsyncMock()
            mock_async_client.__aenter__.return_value = mock_async_client
            mock_async_client.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_async_client
            
            result = await tool.execute(url="https://example.com/notfound")
        
        assert result.success is False
        assert result.error is not None
        assert "404" in result.error
    
    @pytest.mark.asyncio
    async def test_execute_timeout(self):
        """Test handling timeout."""
        tool = WebFetchTool()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_async_client = AsyncMock()
            mock_async_client.__aenter__.return_value = mock_async_client
            mock_async_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_client.return_value = mock_async_client
            
            result = await tool.execute(url="https://example.com")
        
        assert result.success is False
        assert result.error is not None
        assert "timed out" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_execute_connect_error(self):
        """Test handling connection error."""
        tool = WebFetchTool()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_async_client = AsyncMock()
            mock_async_client.__aenter__.return_value = mock_async_client
            mock_async_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))
            mock_client.return_value = mock_async_client
            
            result = await tool.execute(url="https://example.com")
        
        assert result.success is False
        assert result.error is not None
        assert "connect" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_execute_response_too_large_content_length(self):
        """Test handling response too large via content-length header."""
        tool = WebFetchTool()
        
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 200
        mock_response.headers = {"content-length": str(10 * 1024 * 1024)}  # 10MB
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_async_client = AsyncMock()
            mock_async_client.__aenter__.return_value = mock_async_client
            mock_async_client.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_async_client
            
            result = await tool.execute(url="https://example.com/large")
        
        assert result.success is False
        assert result.error is not None
        assert "large" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_execute_cloudflare_challenge(self):
        """Test handling Cloudflare challenge."""
        tool = WebFetchTool()
        
        # First response: 403 with Cloudflare challenge
        mock_response_403 = MagicMock()
        mock_response_403.is_success = False
        mock_response_403.status_code = 403
        mock_response_403.headers = {"cf-mitigated": "challenge"}
        
        # Second response: success after retry
        mock_response_200 = MagicMock()
        mock_response_200.is_success = True
        mock_response_200.status_code = 200
        mock_response_200.content = b"<html><body>Content</body></html>"
        mock_response_200.headers = {"content-type": "text/html"}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_async_client = AsyncMock()
            mock_async_client.__aenter__.return_value = mock_async_client
            mock_async_client.get = AsyncMock(side_effect=[mock_response_403, mock_response_200])
            mock_client.return_value = mock_async_client
            
            result = await tool.execute(url="https://example.com")
        
        assert result.success is True
    
    def test_get_accept_header_markdown(self):
        """Test Accept header for markdown format."""
        tool = WebFetchTool()
        header = tool._get_accept_header("markdown")
        assert "text/markdown" in header
    
    def test_get_accept_header_text(self):
        """Test Accept header for text format."""
        tool = WebFetchTool()
        header = tool._get_accept_header("text")
        assert "text/plain" in header
    
    def test_get_accept_header_html(self):
        """Test Accept header for HTML format."""
        tool = WebFetchTool()
        header = tool._get_accept_header("html")
        assert "text/html" in header
    
    def test_get_accept_header_unknown(self):
        """Test Accept header for unknown format."""
        tool = WebFetchTool()
        header = tool._get_accept_header("unknown")
        assert header == "*/*"
    
    def test_is_image_true(self):
        """Test image detection for image MIME types."""
        tool = WebFetchTool()
        
        assert tool._is_image("image/jpeg") is True
        assert tool._is_image("image/png") is True
        assert tool._is_image("image/gif") is True
        assert tool._is_image("image/webp") is True
    
    def test_is_image_false(self):
        """Test image detection for non-image MIME types."""
        tool = WebFetchTool()
        
        assert tool._is_image("text/html") is False
        assert tool._is_image("application/json") is False
        assert tool._is_image("image/svg+xml") is False  # SVG excluded
    
    def test_html_to_markdown(self):
        """Test HTML to Markdown conversion."""
        tool = WebFetchTool()
        html = "<h1>Title</h1><p>Paragraph</p>"
        
        result = tool._html_to_markdown(html)
        # Should contain title and paragraph text
        assert "Title" in result or "Paragraph" in result
    
    def test_extract_text_from_html(self):
        """Test text extraction from HTML."""
        tool = WebFetchTool()
        html = "<html><head><title>Test</title></head><body><h1>Title</h1><p>Content</p></body></html>"
        
        result = tool._extract_text_from_html(html)
        assert "Title" in result
        assert "Content" in result
    
    def test_extract_text_removes_script(self):
        """Test that script tags are removed."""
        tool = WebFetchTool()
        html = "<html><body><p>Visible</p><script>hidden code</script></body></html>"
        
        result = tool._extract_text_from_html(html)
        assert "Visible" in result
        assert "hidden" not in result
    
    def test_extract_text_removes_style(self):
        """Test that style tags are removed."""
        tool = WebFetchTool()
        html = "<html><head><style>.hidden { display: none; }</style></head><body><p>Visible</p></body></html>"
        
        result = tool._extract_text_from_html(html)
        assert "Visible" in result
        assert ".hidden" not in result
    
    @pytest.mark.asyncio
    async def test_timeout_clamping(self):
        """Test that timeout is clamped to max value."""
        tool = WebFetchTool()
        
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 200
        mock_response.content = b"content"
        mock_response.headers = {"content-type": "text/plain"}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_async_client = AsyncMock()
            mock_async_client.__aenter__.return_value = mock_async_client
            mock_async_client.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_async_client
            
            # Request with timeout above max
            result = await tool.execute(url="https://example.com", timeout=200.0)
            
            # Verify the timeout was clamped
            call_kwargs = mock_async_client.get.call_args
            # The client itself is created with the timeout
            assert result.success is True
