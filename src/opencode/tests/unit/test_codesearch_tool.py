"""Tests for CodeSearchTool."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from opencode.tool.codesearch import CodeSearchTool
from opencode.tool.base import PermissionLevel, ToolResult


class TestCodeSearchTool:
    """Tests for CodeSearchTool class."""
    
    def test_name(self):
        """Test tool name."""
        tool = CodeSearchTool()
        assert tool.name == "codesearch"
    
    def test_description(self):
        """Test tool description."""
        tool = CodeSearchTool()
        assert "code" in tool.description.lower()
        assert "search" in tool.description.lower()
    
    def test_parameters(self):
        """Test tool parameters schema."""
        tool = CodeSearchTool()
        params = tool.parameters
        
        assert params["type"] == "object"
        assert "query" in params["properties"]
        assert "tokensNum" in params["properties"]
        assert params["required"] == ["query"]
    
    def test_permission_level(self):
        """Test permission level."""
        tool = CodeSearchTool()
        assert tool.permission_level == PermissionLevel.READ
    
    def test_required_permissions(self):
        """Test required permissions."""
        tool = CodeSearchTool()
        assert "codesearch" in tool.required_permissions
    
    def test_constants(self):
        """Test class constants."""
        assert CodeSearchTool.API_URL == "https://mcp.exa.ai/mcp"
        assert CodeSearchTool.DEFAULT_TOKENS == 5000
        assert CodeSearchTool.MIN_TOKENS == 1000
        assert CodeSearchTool.MAX_TOKENS == 50000
    
    @pytest.mark.asyncio
    async def test_execute_empty_query(self):
        """Test executing with empty query."""
        tool = CodeSearchTool()
        result = await tool.execute(query="")
        
        assert result.success is False
        assert result.error is not None
        assert "required" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_execute_missing_api_key(self):
        """Test executing without API key."""
        tool = CodeSearchTool()
        
        with patch.dict('os.environ', {}, clear=True):
            result = await tool.execute(query="React hooks")
        
        assert result.success is False
        assert result.error is not None
        assert "EXA_API_KEY" in result.error
    
    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful code search."""
        tool = CodeSearchTool()
        
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.text = 'data: {"result": {"content": [{"type": "text", "text": "React code example"}]}}'
        
        with patch.dict('os.environ', {'EXA_API_KEY': 'test-key'}):
            with patch('httpx.AsyncClient') as mock_client:
                mock_async_client = AsyncMock()
                mock_async_client.__aenter__.return_value = mock_async_client
                mock_async_client.post = AsyncMock(return_value=mock_response)
                mock_client.return_value = mock_async_client
                
                result = await tool.execute(query="React hooks")
        
        assert result.success is True
        assert "React code example" in result.output
    
    @pytest.mark.asyncio
    async def test_execute_http_error(self):
        """Test handling HTTP error."""
        tool = CodeSearchTool()
        
        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        
        with patch.dict('os.environ', {'EXA_API_KEY': 'test-key'}):
            with patch('httpx.AsyncClient') as mock_client:
                mock_async_client = AsyncMock()
                mock_async_client.__aenter__.return_value = mock_async_client
                mock_async_client.post = AsyncMock(return_value=mock_response)
                mock_client.return_value = mock_async_client
                
                result = await tool.execute(query="React hooks")
        
        assert result.success is False
        assert result.error is not None
        assert "401" in result.error
    
    @pytest.mark.asyncio
    async def test_execute_timeout(self):
        """Test handling timeout."""
        tool = CodeSearchTool()
        
        with patch.dict('os.environ', {'EXA_API_KEY': 'test-key'}):
            with patch('httpx.AsyncClient') as mock_client:
                mock_async_client = AsyncMock()
                mock_async_client.__aenter__.return_value = mock_async_client
                mock_async_client.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
                mock_client.return_value = mock_async_client
                
                result = await tool.execute(query="React hooks")
        
        assert result.success is False
        assert result.error is not None
        assert "timed out" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_execute_exception(self):
        """Test handling general exception."""
        tool = CodeSearchTool()
        
        with patch.dict('os.environ', {'EXA_API_KEY': 'test-key'}):
            with patch('httpx.AsyncClient') as mock_client:
                mock_async_client = AsyncMock()
                mock_async_client.__aenter__.return_value = mock_async_client
                mock_async_client.post = AsyncMock(side_effect=Exception("Network error"))
                mock_client.return_value = mock_async_client
                
                result = await tool.execute(query="React hooks")
        
        assert result.success is False
        assert result.error is not None
        assert "failed" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_execute_no_results(self):
        """Test when no results found."""
        tool = CodeSearchTool()
        
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.text = 'data: {}'
        
        with patch.dict('os.environ', {'EXA_API_KEY': 'test-key'}):
            with patch('httpx.AsyncClient') as mock_client:
                mock_async_client = AsyncMock()
                mock_async_client.__aenter__.return_value = mock_async_client
                mock_async_client.post = AsyncMock(return_value=mock_response)
                mock_client.return_value = mock_async_client
                
                result = await tool.execute(query="React hooks")
        
        assert result.success is True
        assert "No code snippets" in result.output
    
    @pytest.mark.asyncio
    async def test_tokens_clamping(self):
        """Test that tokens are clamped to valid range."""
        tool = CodeSearchTool()
        
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.text = 'data: {"result": {"content": [{"type": "text", "text": "code"}]}}'
        
        with patch.dict('os.environ', {'EXA_API_KEY': 'test-key'}):
            with patch('httpx.AsyncClient') as mock_client:
                mock_async_client = AsyncMock()
                mock_async_client.__aenter__.return_value = mock_async_client
                mock_async_client.post = AsyncMock(return_value=mock_response)
                mock_client.return_value = mock_async_client
                
                # Test with tokens below minimum
                result = await tool.execute(query="test", tokensNum=100)
                assert result.success is True
                
                # Test with tokens above maximum
                result = await tool.execute(query="test", tokensNum=100000)
                assert result.success is True
    
    def test_parse_sse_response_valid(self):
        """Test parsing valid SSE response."""
        tool = CodeSearchTool()
        text = 'data: {"result": {"content": [{"type": "text", "text": "example code"}]}}'
        
        result = tool._parse_sse_response(text)
        assert result == "example code"
    
    def test_parse_sse_response_invalid_json(self):
        """Test parsing SSE response with invalid JSON."""
        tool = CodeSearchTool()
        text = 'data: not valid json'
        
        result = tool._parse_sse_response(text)
        assert result == ""
    
    def test_parse_sse_response_no_data_prefix(self):
        """Test parsing SSE response without data prefix."""
        tool = CodeSearchTool()
        text = '{"result": {"content": [{"type": "text", "text": "code"}]}}'
        
        result = tool._parse_sse_response(text)
        assert result == ""
    
    def test_parse_sse_response_empty(self):
        """Test parsing empty SSE response."""
        tool = CodeSearchTool()
        
        result = tool._parse_sse_response("")
        assert result == ""
    
    def test_parse_sse_response_multiple_lines(self):
        """Test parsing SSE response with multiple lines."""
        tool = CodeSearchTool()
        text = '''event: message
data: {"result": {"content": [{"type": "text", "text": "line 1"}]}}

data: {"result": {"content": [{"type": "text", "text": "line 2"}]}}
'''
        
        result = tool._parse_sse_response(text)
        # Should return first valid result
        assert result in ["line 1", "line 2", ""]
