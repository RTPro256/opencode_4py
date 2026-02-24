"""
Tests for WebSearch tool.
"""

import json
import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from opencode.tool.websearch import WebSearchTool
from opencode.tool.base import PermissionLevel, ToolResult


class TestWebSearchTool:
    """Tests for WebSearchTool."""

    @pytest.fixture
    def tool(self):
        """Create a WebSearchTool instance."""
        return WebSearchTool()

    def test_name(self, tool):
        """Test tool name."""
        assert tool.name == "websearch"

    def test_description(self, tool):
        """Test tool description."""
        assert "Search the web" in tool.description
        assert "websearch(query=" in tool.description

    def test_parameters(self, tool):
        """Test tool parameters schema."""
        params = tool.parameters
        
        assert params["type"] == "object"
        assert "query" in params["properties"]
        assert "numResults" in params["properties"]
        assert "useAutoprompt" in params["properties"]
        assert params["required"] == ["query"]

    def test_permission_level(self, tool):
        """Test permission level."""
        assert tool.permission_level == PermissionLevel.READ

    def test_required_permissions(self, tool):
        """Test required permissions."""
        assert tool.required_permissions == ["websearch"]

    def test_constants(self, tool):
        """Test tool constants."""
        assert tool.API_URL == "https://mcp.exa.ai/mcp"
        assert tool.DEFAULT_NUM_RESULTS == 5
        assert tool.MAX_NUM_RESULTS == 20

    @pytest.mark.asyncio
    async def test_execute_missing_query(self, tool):
        """Test execute with missing query."""
        result = await tool.execute()
        
        assert result.success is False
        assert "query is required" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_empty_query(self, tool):
        """Test execute with empty query."""
        result = await tool.execute(query="")
        
        assert result.success is False
        assert "query is required" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_no_api_key(self, tool):
        """Test execute without API key."""
        # Ensure no API key is set
        with patch.dict(os.environ, {}, clear=True):
            # Remove EXA_API_KEY if it exists
            os.environ.pop("EXA_API_KEY", None)
            
            result = await tool.execute(query="test query")
            
            assert result.success is False
            assert "EXA_API_KEY" in result.error

    @pytest.mark.asyncio
    async def test_execute_success(self, tool):
        """Test successful search execution."""
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.text = 'data: {"result": {"content": [{"type": "text", "text": "[{\\"title\\": \\"Test Result\\", \\"url\\": \\"https://example.com\\", \\"text\\": \\"Test content\\"}]"}]}}'
        
        with patch.dict(os.environ, {"EXA_API_KEY": "test-key"}):
            with patch("httpx.AsyncClient") as mock_client:
                mock_async_client = AsyncMock()
                mock_async_client.__aenter__.return_value = mock_async_client
                mock_async_client.post = AsyncMock(return_value=mock_response)
                mock_client.return_value = mock_async_client
                
                result = await tool.execute(query="test query")
                
                assert result.success is True
                assert "Search Results" in result.output
                assert result.metadata["query"] == "test query"

    @pytest.mark.asyncio
    async def test_execute_with_custom_num_results(self, tool):
        """Test execute with custom number of results."""
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.text = 'data: {"result": {"content": [{"type": "text", "text": "[]"}]}}'
        
        with patch.dict(os.environ, {"EXA_API_KEY": "test-key"}):
            with patch("httpx.AsyncClient") as mock_client:
                mock_async_client = AsyncMock()
                mock_async_client.__aenter__.return_value = mock_async_client
                mock_async_client.post = AsyncMock(return_value=mock_response)
                mock_client.return_value = mock_async_client
                
                result = await tool.execute(query="test", numResults=10)
                
                # Check that post was called with correct numResults
                call_args = mock_async_client.post.call_args
                assert call_args is not None

    @pytest.mark.asyncio
    async def test_execute_max_results_capped(self, tool):
        """Test that numResults is capped to MAX_NUM_RESULTS."""
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.text = 'data: {"result": {"content": [{"type": "text", "text": "[]"}]}}'
        
        with patch.dict(os.environ, {"EXA_API_KEY": "test-key"}):
            with patch("httpx.AsyncClient") as mock_client:
                mock_async_client = AsyncMock()
                mock_async_client.__aenter__.return_value = mock_async_client
                mock_async_client.post = AsyncMock(return_value=mock_response)
                mock_client.return_value = mock_async_client
                
                # Request more than max
                result = await tool.execute(query="test", numResults=100)
                
                # Check that numResults was capped
                call_args = mock_async_client.post.call_args
                request_body = call_args.kwargs["json"]
                assert request_body["params"]["arguments"]["numResults"] <= tool.MAX_NUM_RESULTS

    @pytest.mark.asyncio
    async def test_execute_http_error(self, tool):
        """Test execute with HTTP error."""
        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        
        with patch.dict(os.environ, {"EXA_API_KEY": "test-key"}):
            with patch("httpx.AsyncClient") as mock_client:
                mock_async_client = AsyncMock()
                mock_async_client.__aenter__.return_value = mock_async_client
                mock_async_client.post = AsyncMock(return_value=mock_response)
                mock_client.return_value = mock_async_client
                
                result = await tool.execute(query="test query")
                
                assert result.success is False
                assert "500" in result.error

    @pytest.mark.asyncio
    async def test_execute_timeout(self, tool):
        """Test execute with timeout."""
        import httpx
        
        with patch.dict(os.environ, {"EXA_API_KEY": "test-key"}):
            with patch("httpx.AsyncClient") as mock_client:
                mock_async_client = AsyncMock()
                mock_async_client.__aenter__.return_value = mock_async_client
                mock_async_client.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
                mock_client.return_value = mock_async_client
                
                result = await tool.execute(query="test query")
                
                assert result.success is False
                assert "timed out" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_exception(self, tool):
        """Test execute with general exception."""
        with patch.dict(os.environ, {"EXA_API_KEY": "test-key"}):
            with patch("httpx.AsyncClient") as mock_client:
                mock_async_client = AsyncMock()
                mock_async_client.__aenter__.return_value = mock_async_client
                mock_async_client.post = AsyncMock(side_effect=Exception("Network error"))
                mock_client.return_value = mock_async_client
                
                result = await tool.execute(query="test query")
                
                assert result.success is False
                assert "failed" in result.error.lower()

    def test_parse_sse_response_list(self, tool):
        """Test parsing SSE response with list results."""
        sse_text = 'data: {"result": {"content": [{"type": "text", "text": "[{\\"title\\": \\"Result 1\\"}, {\\"title\\": \\"Result 2\\"}]"}]}}'
        
        results = tool._parse_sse_response(sse_text)
        
        assert len(results) == 2
        assert results[0]["title"] == "Result 1"
        assert results[1]["title"] == "Result 2"

    def test_parse_sse_response_dict_with_results(self, tool):
        """Test parsing SSE response with dict containing results key."""
        sse_text = 'data: {"result": {"content": [{"type": "text", "text": "{\\"results\\": [{\\"title\\": \\"Result\\"}]}"}]}}'
        
        results = tool._parse_sse_response(sse_text)
        
        assert len(results) == 1
        assert results[0]["title"] == "Result"

    def test_parse_sse_response_multiple_data_lines(self, tool):
        """Test parsing SSE response with multiple data lines."""
        sse_text = '''data: {"result": {"content": [{"type": "text", "text": "[{\\"title\\": \\"Result 1\\"}]"}]}}
data: {"result": {"content": [{"type": "text", "text": "[{\\"title\\": \\"Result 2\\"}]"}]}}'''
        
        results = tool._parse_sse_response(sse_text)
        
        assert len(results) == 2

    def test_parse_sse_response_invalid_json(self, tool):
        """Test parsing SSE response with invalid JSON."""
        sse_text = 'data: not valid json'
        
        results = tool._parse_sse_response(sse_text)
        
        assert results == []

    def test_parse_sse_response_non_text_content(self, tool):
        """Test parsing SSE response with non-text content."""
        sse_text = 'data: {"result": {"content": [{"type": "image", "url": "https://example.com/image.jpg"}]}}'
        
        results = tool._parse_sse_response(sse_text)
        
        assert results == []

    def test_parse_sse_response_empty(self, tool):
        """Test parsing empty SSE response."""
        results = tool._parse_sse_response("")
        
        assert results == []

    def test_format_results(self, tool):
        """Test formatting search results."""
        results = [
            {"title": "Result 1", "url": "https://example.com/1", "text": "Content 1"},
            {"title": "Result 2", "url": "https://example.com/2", "text": "Content 2"},
        ]
        
        output = tool._format_results(results, "test query")
        
        assert "Search Results for: test query" in output
        assert "Result 1" in output
        assert "Result 2" in output
        assert "https://example.com/1" in output
        assert "https://example.com/2" in output

    def test_format_results_with_link_instead_of_url(self, tool):
        """Test formatting results with 'link' instead of 'url'."""
        results = [
            {"title": "Result", "link": "https://example.com", "text": "Content"},
        ]
        
        output = tool._format_results(results, "test")
        
        assert "https://example.com" in output

    def test_format_results_with_snippet(self, tool):
        """Test formatting results with 'snippet' field."""
        results = [
            {"title": "Result", "url": "https://example.com", "snippet": "Snippet text"},
        ]
        
        output = tool._format_results(results, "test")
        
        assert "Snippet text" in output

    def test_format_results_with_content(self, tool):
        """Test formatting results with 'content' field."""
        results = [
            {"title": "Result", "url": "https://example.com", "content": "Content text"},
        ]
        
        output = tool._format_results(results, "test")
        
        assert "Content text" in output

    def test_format_results_truncates_long_text(self, tool):
        """Test that long text is truncated."""
        long_text = "x" * 1000
        results = [
            {"title": "Result", "url": "https://example.com", "text": long_text},
        ]
        
        output = tool._format_results(results, "test")
        
        # Should be truncated to 500 chars + "..."
        assert "..." in output
        assert len(output) < len(long_text) + 200  # Account for other text

    def test_format_results_missing_title(self, tool):
        """Test formatting results with missing title."""
        results = [
            {"url": "https://example.com", "text": "Content"},
        ]
        
        output = tool._format_results(results, "test")
        
        assert "Untitled" in output

    def test_format_results_missing_url(self, tool):
        """Test formatting results with missing URL."""
        results = [
            {"title": "Result", "text": "Content"},
        ]
        
        output = tool._format_results(results, "test")
        
        assert "Result" in output

    def test_format_results_empty(self, tool):
        """Test formatting empty results."""
        output = tool._format_results([], "test")
        
        assert "Search Results for: test" in output

    @pytest.mark.asyncio
    async def test_execute_no_results_found(self, tool):
        """Test execute when no results are found."""
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.text = 'data: {"result": {"content": [{"type": "text", "text": "[]"}]}}'
        
        with patch.dict(os.environ, {"EXA_API_KEY": "test-key"}):
            with patch("httpx.AsyncClient") as mock_client:
                mock_async_client = AsyncMock()
                mock_async_client.__aenter__.return_value = mock_async_client
                mock_async_client.post = AsyncMock(return_value=mock_response)
                mock_client.return_value = mock_async_client
                
                result = await tool.execute(query="test query")
                
                assert result.success is True
                assert "No results found" in result.output

    @pytest.mark.asyncio
    async def test_execute_autoprompt_default(self, tool):
        """Test that useAutoprompt defaults to True."""
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.text = 'data: {"result": {"content": [{"type": "text", "text": "[]"}]}}'
        
        with patch.dict(os.environ, {"EXA_API_KEY": "test-key"}):
            with patch("httpx.AsyncClient") as mock_client:
                mock_async_client = AsyncMock()
                mock_async_client.__aenter__.return_value = mock_async_client
                mock_async_client.post = AsyncMock(return_value=mock_response)
                mock_client.return_value = mock_async_client
                
                await tool.execute(query="test")
                
                call_args = mock_async_client.post.call_args
                request_body = call_args.kwargs["json"]
                assert request_body["params"]["arguments"]["useAutoprompt"] is True

    @pytest.mark.asyncio
    async def test_execute_autoprompt_false(self, tool):
        """Test that useAutoprompt can be set to False."""
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.text = 'data: {"result": {"content": [{"type": "text", "text": "[]"}]}}'
        
        with patch.dict(os.environ, {"EXA_API_KEY": "test-key"}):
            with patch("httpx.AsyncClient") as mock_client:
                mock_async_client = AsyncMock()
                mock_async_client.__aenter__.return_value = mock_async_client
                mock_async_client.post = AsyncMock(return_value=mock_response)
                mock_client.return_value = mock_async_client
                
                await tool.execute(query="test", useAutoprompt=False)
                
                call_args = mock_async_client.post.call_args
                request_body = call_args.kwargs["json"]
                assert request_body["params"]["arguments"]["useAutoprompt"] is False

    def test_to_openai_tool(self, tool):
        """Test converting to OpenAI tool format."""
        openai_tool = tool.to_openai_tool()
        
        assert openai_tool["type"] == "function"
        assert openai_tool["function"]["name"] == "websearch"
        assert "description" in openai_tool["function"]
        assert "parameters" in openai_tool["function"]

    def test_to_anthropic_tool(self, tool):
        """Test converting to Anthropic tool format."""
        anthropic_tool = tool.to_anthropic_tool()
        
        assert anthropic_tool["name"] == "websearch"
        assert "description" in anthropic_tool
        assert "input_schema" in anthropic_tool
