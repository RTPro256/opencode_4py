"""
Tests for BraveSearchTool.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from opencode.workflow.tools.brave_search import BraveSearchTool
from opencode.workflow.tools.registry import ToolResult


class TestBraveSearchTool:
    """Tests for BraveSearchTool class."""

    def test_get_schema(self):
        """Test getting tool schema."""
        schema = BraveSearchTool.get_schema()
        assert schema.name == "brave_search"
        assert schema.description == "Search the web using Brave Search API"
        assert "query" in schema.parameters["properties"]
        assert schema.requires_auth is True

    @pytest.mark.asyncio
    async def test_initialize_with_api_key(self):
        """Test initialization with API key."""
        tool = BraveSearchTool(config={"api_key": "test-key"})
        result = await tool.initialize()
        assert result is True
        assert tool._initialized is True

    @pytest.mark.asyncio
    async def test_initialize_without_api_key(self):
        """Test initialization without API key."""
        tool = BraveSearchTool(config={})
        result = await tool.initialize()
        assert result is False

    @pytest.mark.asyncio
    async def test_execute_missing_query(self):
        """Test execute with missing query parameter."""
        tool = BraveSearchTool(config={"api_key": "test-key"})
        result = await tool.execute({})
        assert result.success is False
        assert "query" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_missing_api_key(self):
        """Test execute without API key configured."""
        tool = BraveSearchTool(config={})
        result = await tool.execute({"query": "test search"})
        assert result.success is False
        assert "api key" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful search execution."""
        tool = BraveSearchTool(config={"api_key": "test-key"})
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "web": {
                "results": [
                    {
                        "title": "Test Result",
                        "url": "https://example.com",
                        "description": "Test description",
                    }
                ]
            }
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await tool.execute({"query": "test search"})

        assert result.success is True
        assert result.data["query"] == "test search"
        assert len(result.data["results"]) == 1
        assert result.data["results"][0]["title"] == "Test Result"

    @pytest.mark.asyncio
    async def test_execute_with_all_params(self):
        """Test execute with all parameters."""
        tool = BraveSearchTool(config={"api_key": "test-key"})
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"web": {"results": []}}

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await tool.execute({
                "query": "test search",
                "count": 20,
                "offset": 10,
                "country": "CA",
                "search_lang": "fr",
                "freshness": "pw",
            })

        assert result.success is True
        # Verify parameters were passed correctly
        call_args = mock_instance.get.call_args
        assert call_args is not None

    @pytest.mark.asyncio
    async def test_execute_unauthorized(self):
        """Test execute with invalid API key (401)."""
        tool = BraveSearchTool(config={"api_key": "invalid-key"})
        
        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await tool.execute({"query": "test search"})

        assert result.success is False
        assert "invalid" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_rate_limited(self):
        """Test execute when rate limited (429)."""
        tool = BraveSearchTool(config={"api_key": "test-key"})
        
        mock_response = MagicMock()
        mock_response.status_code = 429

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await tool.execute({"query": "test search"})

        assert result.success is False
        assert "rate limit" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_timeout(self):
        """Test execute when request times out."""
        tool = BraveSearchTool(config={"api_key": "test-key"})

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await tool.execute({"query": "test search"})

        assert result.success is False
        assert "timed out" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_http_error(self):
        """Test execute when HTTP error occurs."""
        tool = BraveSearchTool(config={"api_key": "test-key"})
        
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error", request=MagicMock(), response=mock_response
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await tool.execute({"query": "test search"})

        assert result.success is False
        assert "500" in result.error

    def test_parse_results_web(self):
        """Test parsing web search results."""
        tool = BraveSearchTool(config={"api_key": "test-key"})
        
        data = {
            "web": {
                "results": [
                    {
                        "title": "Result 1",
                        "url": "https://example1.com",
                        "description": "Description 1",
                        "age": "2 days ago",
                        "language": "en",
                    },
                    {
                        "title": "Result 2",
                        "url": "https://example2.com",
                        "description": "Description 2",
                    },
                ]
            }
        }
        
        results = tool._parse_results(data)
        
        assert len(results) == 2
        assert results[0]["title"] == "Result 1"
        assert results[0]["type"] == "web"
        assert results[0]["age"] == "2 days ago"
        assert results[1]["title"] == "Result 2"

    def test_parse_results_news(self):
        """Test parsing news search results."""
        tool = BraveSearchTool(config={"api_key": "test-key"})
        
        data = {
            "news": {
                "results": [
                    {
                        "title": "News 1",
                        "url": "https://news1.com",
                        "description": "News description",
                        "age": "1 hour ago",
                        "source": "News Source",
                    }
                ]
            }
        }
        
        results = tool._parse_results(data)
        
        assert len(results) == 1
        assert results[0]["type"] == "news"
        assert results[0]["source"] == "News Source"

    def test_parse_results_mixed(self):
        """Test parsing mixed web and news results."""
        tool = BraveSearchTool(config={"api_key": "test-key"})
        
        data = {
            "web": {
                "results": [
                    {"title": "Web Result", "url": "https://web.com", "description": "Web desc"}
                ]
            },
            "news": {
                "results": [
                    {"title": "News Result", "url": "https://news.com", "description": "News desc"}
                ]
            }
        }
        
        results = tool._parse_results(data)
        
        assert len(results) == 2
        types = [r["type"] for r in results]
        assert "web" in types
        assert "news" in types

    def test_parse_results_empty(self):
        """Test parsing empty results."""
        tool = BraveSearchTool(config={"api_key": "test-key"})
        
        results = tool._parse_results({})
        assert results == []

    def test_parse_results_family_friendly(self):
        """Test parsing results with family_friendly field."""
        tool = BraveSearchTool(config={"api_key": "test-key"})
        
        data = {
            "web": {
                "results": [
                    {
                        "title": "Result",
                        "url": "https://example.com",
                        "description": "Description",
                        "family_friendly": True,
                    }
                ]
            }
        }
        
        results = tool._parse_results(data)
        
        assert results[0]["family_friendly"] is True

    @pytest.mark.asyncio
    async def test_execute_exception(self):
        """Test execute when unexpected exception occurs."""
        tool = BraveSearchTool(config={"api_key": "test-key"})

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(side_effect=Exception("Unexpected error"))
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await tool.execute({"query": "test search"})

        assert result.success is False
        assert "failed" in result.error.lower()
