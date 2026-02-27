"""
Tests for Google Gemini Provider.

Note: The Google provider has some implementation inconsistencies with the base
Provider interface. These tests focus on the testable methods.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from opencode.provider.google import GoogleProvider
from opencode.provider.base import ModelInfo


# Create a concrete test subclass since GoogleProvider is abstract
class TestableGoogleProvider(GoogleProvider):
    """Testable version of GoogleProvider with models property implemented."""
    
    @property
    def models(self) -> list[ModelInfo]:
        """Return list of available models."""
        return [
            ModelInfo(
                id=self.model,
                name=self.model,
                provider=self.name,
                context_length=8192,
            )
        ]


@pytest.fixture
def google_provider():
    """Create a GoogleProvider instance for testing."""
    return TestableGoogleProvider(
        api_key="test-api-key",
        model="gemini-2.0-flash-exp",
        base_url="https://generativelanguage.googleapis.com/v1beta",
        max_tokens=8192,
        temperature=0.7,
    )


@pytest.mark.unit
class TestGoogleProvider:
    """Tests for GoogleProvider class."""

    def test_provider_creation(self, google_provider):
        """Test GoogleProvider instantiation."""
        assert google_provider.api_key == "test-api-key"
        assert google_provider.model == "gemini-2.0-flash-exp"
        assert google_provider.base_url == "https://generativelanguage.googleapis.com/v1beta"
        assert google_provider.max_tokens == 8192
        assert google_provider.temperature == 0.7

    def test_provider_name(self, google_provider):
        """Test GoogleProvider name property."""
        assert google_provider.name == "google"

    def test_provider_models(self, google_provider):
        """Test GoogleProvider models property."""
        models = google_provider.models
        assert len(models) == 1
        assert models[0].id == "gemini-2.0-flash-exp"
        assert models[0].provider == "google"

    def test_get_endpoint(self, google_provider):
        """Test _get_endpoint method."""
        endpoint = google_provider._get_endpoint()
        assert endpoint == "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp"

    def test_pricing(self, google_provider):
        """Test PRICING constant has expected models."""
        assert "gemini-2.0-flash-exp" in GoogleProvider.PRICING
        assert "gemini-1.5-pro" in GoogleProvider.PRICING
        assert "gemini-1.5-flash" in GoogleProvider.PRICING
        assert GoogleProvider.PRICING["gemini-2.0-flash-exp"]["input"] == 0.0
        assert GoogleProvider.PRICING["gemini-1.5-pro"]["input"] == 1.25

    def test_convert_messages_basic(self, google_provider):
        """Test _convert_messages with basic messages."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        result = google_provider._convert_messages(messages)
        
        assert len(result) == 2
        assert result[0]["role"] == "user"
        assert result[0]["parts"][0]["text"] == "Hello"
        assert result[1]["role"] == "model"
        assert result[1]["parts"][0]["text"] == "Hi there!"

    def test_convert_messages_with_system(self, google_provider):
        """Test _convert_messages with system message."""
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello"},
        ]
        result = google_provider._convert_messages(messages)
        
        # System messages are converted to user role
        assert len(result) == 2
        assert result[0]["role"] == "user"
        assert result[1]["role"] == "user"

    def test_convert_tools(self, google_provider):
        """Test _convert_tools method."""
        tools = [
            {
                "function": {
                    "name": "get_weather",
                    "description": "Get weather info",
                    "parameters": {
                        "properties": {
                            "location": {"type": "string"}
                        },
                        "required": ["location"]
                    }
                }
            }
        ]
        result = google_provider._convert_tools(tools)
        
        assert "functionDeclarations" in result
        assert len(result["functionDeclarations"]) == 1
        assert result["functionDeclarations"][0]["name"] == "get_weather"
        assert result["functionDeclarations"][0]["description"] == "Get weather info"

    def test_parse_response_empty_candidates(self, google_provider):
        """Test _parse_response with empty candidates."""
        data = {"candidates": []}
        result = google_provider._parse_response(data)
        
        # Should return empty message
        assert result is not None

    def test_parse_stream_chunk_empty(self, google_provider):
        """Test _parse_stream_chunk with empty chunk."""
        data = {"candidates": []}
        result = google_provider._parse_stream_chunk(data)
        
        assert result is None

    def test_parse_stream_chunk_no_text(self, google_provider):
        """Test _parse_stream_chunk with no text."""
        data = {
            "candidates": [
                {
                    "content": {
                        "parts": [{}]
                    }
                }
            ]
        }
        result = google_provider._parse_stream_chunk(data)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_count_tokens_success(self, google_provider):
        """Test count_tokens with successful response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"totalTokens": 42}
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch("httpx.AsyncClient", return_value=mock_client):
            count = await google_provider.count_tokens([{"role": "user", "content": "Hello"}])
            assert count == 42

    @pytest.mark.asyncio
    async def test_count_tokens_error(self, google_provider):
        """Test count_tokens with error response."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch("httpx.AsyncClient", return_value=mock_client):
            count = await google_provider.count_tokens([{"role": "user", "content": "Hello"}])
            assert count == 0

    def test_default_model(self):
        """Test default model is set correctly."""
        provider = TestableGoogleProvider(api_key="test-key")
        assert provider.model == "gemini-2.0-flash-exp"

    def test_default_max_tokens(self):
        """Test default max_tokens is set correctly."""
        provider = TestableGoogleProvider(api_key="test-key")
        assert provider.max_tokens == 8192

    def test_default_temperature(self):
        """Test default temperature is set correctly."""
        provider = TestableGoogleProvider(api_key="test-key")
        assert provider.temperature == 0.7

    def test_custom_model(self):
        """Test custom model can be set."""
        provider = TestableGoogleProvider(
            api_key="test-key",
            model="gemini-1.5-pro"
        )
        assert provider.model == "gemini-1.5-pro"

    def test_custom_base_url(self):
        """Test custom base_url can be set."""
        provider = TestableGoogleProvider(
            api_key="test-key",
            base_url="https://custom.googleapis.com/v1"
        )
        assert provider.base_url == "https://custom.googleapis.com/v1"

    def test_convert_messages_empty(self, google_provider):
        """Test _convert_messages with empty messages."""
        result = google_provider._convert_messages([])
        assert result == []

    def test_convert_messages_unknown_role(self, google_provider):
        """Test _convert_messages with unknown role maps to model."""
        messages = [
            {"role": "unknown", "content": "Test"},
        ]
        result = google_provider._convert_messages(messages)
        
        assert len(result) == 1
        # Unknown roles (not user/system) map to model
        assert result[0]["role"] == "model"

    def test_convert_tools_empty(self, google_provider):
        """Test _convert_tools with empty tools."""
        result = google_provider._convert_tools([])
        
        assert "functionDeclarations" in result
        assert len(result["functionDeclarations"]) == 0
