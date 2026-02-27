"""
Tests for DuckDuckGoSearchTool.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from opencode.workflow.tools.duckduckgo_search import DuckDuckGoSearchTool
from opencode.workflow.tools.registry import ToolResult


class TestDuckDuckGoSearchTool:
    """Tests for DuckDuckGoSearchTool class."""

    def test_get_schema(self):
        """Test getting tool schema."""
        schema = DuckDuckGoSearchTool.get_schema()
        assert schema.name == "duckduckgo_search"
        assert "query" in schema.parameters["properties"]
        assert schema.requires_auth is False

    @pytest.mark.asyncio
    async def test_execute_missing_query(self):
        """Test execute with missing query parameter."""
        tool = DuckDuckGoSearchTool(config={})
        result = await tool.execute({})
        assert result.success is False
        assert result.error is not None
        assert "query" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_success_instant_answer(self):
        """Test successful search with instant answer."""
        tool = DuckDuckGoSearchTool(config={})
        
        instant_response = MagicMock()
        instant_response.status_code = 200
        instant_response.json.return_value = {
            "Abstract": "Python is a programming language",
            "Heading": "Python (programming language)",
            "AbstractURL": "https://example.com/python",
            "AbstractSource": "Wikipedia",
            "RelatedTopics": [],
            "Results": [],
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            # First call is instant answer, second is HTML search
            mock_instance.get = AsyncMock(return_value=instant_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await tool.execute({"query": "python programming"})

        assert result.success is True
        assert result.data["query"] == "python programming"
        assert len(result.data["results"]) >= 1

    @pytest.mark.asyncio
    async def test_execute_with_related_topics(self):
        """Test search with related topics."""
        tool = DuckDuckGoSearchTool(config={})
        
        instant_response = MagicMock()
        instant_response.status_code = 200
        instant_response.json.return_value = {
            "Abstract": "",
            "RelatedTopics": [
                {
                    "Text": "Python is a programming language",
                    "FirstURL": "https://example.com/Python_(language)",
                }
            ],
            "Results": [],
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=instant_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await tool.execute({"query": "python"})

        assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_with_results(self):
        """Test search with results field."""
        tool = DuckDuckGoSearchTool(config={})
        
        instant_response = MagicMock()
        instant_response.status_code = 200
        instant_response.json.return_value = {
            "Abstract": "",
            "RelatedTopics": [],
            "Results": [
                {
                    "Text": "Official Python website",
                    "FirstURL": "https://www.python.org/",
                }
            ],
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=instant_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await tool.execute({"query": "python"})

        assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_with_html_fallback(self):
        """Test search with HTML fallback when instant answer is empty."""
        tool = DuckDuckGoSearchTool(config={})
        
        instant_response = MagicMock()
        instant_response.status_code = 200
        instant_response.json.return_value = {
            "Abstract": "",
            "RelatedTopics": [],
            "Results": [],
        }
        
        html_response = MagicMock()
        html_response.status_code = 200
        html_response.text = '''
        <a rel="nofollow" class="result__a" href="https://duckduckgo.com/l/?uddg=https%3A%2F%2Fwww.python.org">Python Official</a>
        <a rel="nofollow" class="result__a" href="https://duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com">Example</a>
        '''

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            call_count = [0]
            
            async def side_effect(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:
                    return instant_response
                return html_response
            
            mock_instance.get = side_effect
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await tool.execute({"query": "python", "max_results": 5})

        assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_timeout(self):
        """Test execute when request times out."""
        tool = DuckDuckGoSearchTool(config={})

        with patch("httpx.AsyncClient") as mock_client:
            # Make both instant answer and HTML search raise timeout
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            # The tool catches TimeoutException and returns success with empty results
            # because both instant answer and HTML search are allowed to fail gracefully
            result = await tool.execute({"query": "test search"})

        # The tool returns success with empty results when both searches fail
        assert result.success is True
        assert result.data["results"] == []

    @pytest.mark.asyncio
    async def test_execute_exception(self):
        """Test execute when unexpected exception occurs."""
        tool = DuckDuckGoSearchTool(config={})

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(side_effect=Exception("Unexpected error"))
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            # The tool catches exceptions and returns success with empty results
            result = await tool.execute({"query": "test search"})

        # The tool returns success with empty results when both searches fail
        assert result.success is True
        assert result.data["results"] == []

    @pytest.mark.asyncio
    async def test_execute_with_custom_params(self):
        """Test execute with custom parameters."""
        tool = DuckDuckGoSearchTool(config={"max_results": 5, "region": "uk-en"})
        
        instant_response = MagicMock()
        instant_response.status_code = 200
        instant_response.json.return_value = {
            "Abstract": "Test",
            "Heading": "Test",
            "AbstractURL": "https://example.com",
            "AbstractSource": "Test",
            "RelatedTopics": [],
            "Results": [],
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=instant_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await tool.execute({
                "query": "test",
                "max_results": 3,
                "region": "de-de",
                "safe_search": False,
            })

        assert result.success is True

    @pytest.mark.asyncio
    async def test_instant_answer_search(self):
        """Test _instant_answer_search method."""
        tool = DuckDuckGoSearchTool(config={})
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Abstract": "Test abstract",
            "Heading": "Test Heading",
            "AbstractURL": "https://example.com",
            "AbstractSource": "Wikipedia",
            "RelatedTopics": [
                {"Text": "Topic 1", "FirstURL": "https://example.com/topic1"}
            ],
            "Results": [
                {"Text": "Result 1", "FirstURL": "https://example.com/result1"}
            ],
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            results = await tool._instant_answer_search("test", "us-en", True, 30)

        assert len(results) >= 1
        assert results[0]["type"] == "instant_answer"

    @pytest.mark.asyncio
    async def test_instant_answer_search_error(self):
        """Test _instant_answer_search with error."""
        tool = DuckDuckGoSearchTool(config={})

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(side_effect=Exception("Error"))
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            results = await tool._instant_answer_search("test", "us-en", True, 30)

        assert results == []

    @pytest.mark.asyncio
    async def test_html_search(self):
        """Test _html_search method."""
        tool = DuckDuckGoSearchTool(config={})
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '''
        <a rel="nofollow" class="result__a" href="https://duckduckgo.com/l/?uddg=https%3A%2F%2Fwww.example.com">Example Site</a>
        '''

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            results = await tool._html_search("test", "us-en", True, 30, 5)

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_html_search_error(self):
        """Test _html_search with error."""
        tool = DuckDuckGoSearchTool(config={})

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(side_effect=Exception("Error"))
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            results = await tool._html_search("test", "us-en", True, 30, 5)

        assert results == []

    @pytest.mark.asyncio
    async def test_html_search_direct_url(self):
        """Test _html_search with direct URL (no redirect)."""
        tool = DuckDuckGoSearchTool(config={})
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '''
        <a rel="nofollow" class="result__a" href="https://www.example.com/direct">Direct Link</a>
        '''

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            results = await tool._html_search("test", "us-en", True, 30, 5)

        assert isinstance(results, list)
