"""
Tests for Custom Endpoint Provider.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import json

from opencode.provider.custom import CustomEndpointProvider
from opencode.provider.base import Message, MessageRole, ToolDefinition


# Create a concrete test subclass since CustomEndpointProvider is abstract
class TestableCustomProvider(CustomEndpointProvider):
    """Testable version of CustomEndpointProvider with count_tokens implemented."""
    
    async def count_tokens(self, text: str, model: str) -> int:
        """Simple token counter for testing."""
        return len(text.split())


@pytest.mark.unit
class TestCustomEndpointProvider:
    """Tests for CustomEndpointProvider class."""

    def test_provider_creation(self):
        """Test CustomEndpointProvider instantiation."""
        provider = TestableCustomProvider(
            base_url="http://localhost:8000/v1",
            api_key="test-key",
            model="test-model"
        )
        assert provider.base_url == "http://localhost:8000/v1"
        assert provider.api_key == "test-key"
        assert provider.model_id == "test-model"

    def test_provider_creation_with_env_key(self):
        """Test CustomEndpointProvider uses env var for API key."""
        with patch.dict("os.environ", {"CUSTOM_API_KEY": "env-key"}):
            provider = TestableCustomProvider(
                base_url="http://localhost:8000/v1"
            )
            assert provider.api_key == "env-key"

    def test_provider_name(self):
        """Test CustomEndpointProvider name property."""
        provider = TestableCustomProvider(base_url="http://localhost:8000/v1")
        assert provider.name == "custom-endpoint"

    def test_provider_models_default(self):
        """Test CustomEndpointProvider models property with default model."""
        provider = TestableCustomProvider(
            base_url="http://localhost:8000/v1",
            model="default-model"
        )
        models = provider.models
        assert len(models) == 1
        assert models[0].id == "default-model"
        assert models[0].provider == "custom-endpoint"

    def test_provider_models_custom_list(self):
        """Test CustomEndpointProvider models property with custom list."""
        provider = TestableCustomProvider(
            base_url="http://localhost:8000/v1",
            models_list=["model-1", "model-2", "model-3"]
        )
        models = provider.models
        assert len(models) == 3
        assert models[0].id == "model-1"
        assert models[1].id == "model-2"
        assert models[2].id == "model-3"

    def test_get_headers_with_api_key(self):
        """Test _get_headers with API key."""
        provider = TestableCustomProvider(
            base_url="http://localhost:8000/v1",
            api_key="test-key"
        )
        headers = provider._get_headers()
        assert headers["Content-Type"] == "application/json"
        assert headers["Authorization"] == "Bearer test-key"

    def test_get_headers_without_api_key(self):
        """Test _get_headers without API key."""
        provider = TestableCustomProvider(base_url="http://localhost:8000/v1")
        headers = provider._get_headers()
        assert headers["Content-Type"] == "application/json"
        assert "Authorization" not in headers

    def test_base_url_trailing_slash_removed(self):
        """Test that trailing slash is removed from base_url."""
        provider = TestableCustomProvider(base_url="http://localhost:8000/v1/")
        assert provider.base_url == "http://localhost:8000/v1"

    def test_kwargs_stored(self):
        """Test that extra kwargs are stored."""
        provider = TestableCustomProvider(
            base_url="http://localhost:8000/v1",
            extra_option="value"
        )
        assert provider.kwargs == {"extra_option": "value"}

    def test_is_configured_true(self):
        """Test is_configured returns True when base_url is set."""
        provider = TestableCustomProvider(base_url="http://localhost:8000/v1")
        assert provider.is_configured() is True

    def test_is_configured_false(self):
        """Test is_configured returns False when base_url is empty."""
        provider = TestableCustomProvider(base_url="")
        assert provider.is_configured() is False

    @pytest.mark.asyncio
    async def test_count_tokens(self):
        """Test count_tokens method."""
        provider = TestableCustomProvider(base_url="http://localhost:8000/v1")
        count = await provider.count_tokens("Hello world this is a test", "test-model")
        assert count == 6  # 6 words

    @pytest.mark.asyncio
    async def test_list_models_fallback(self):
        """Test list_models falls back to configured list on error."""
        provider = TestableCustomProvider(
            base_url="http://localhost:8000/v1",
            models_list=["model-1", "model-2"]
        )
        
        # Mock httpx to raise an error
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.side_effect = Exception("Connection error")
            
            models = await provider.list_models()
            assert models == ["model-1", "model-2"]

    @pytest.mark.asyncio
    async def test_list_models_success(self):
        """Test list_models fetches from API."""
        provider = TestableCustomProvider(
            base_url="http://localhost:8000/v1",
            models_list=["fallback"]
        )
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "api-model-1"},
                {"id": "api-model-2"}
            ]
        }
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch("httpx.AsyncClient", return_value=mock_client):
            models = await provider.list_models()
            assert models == ["api-model-1", "api-model-2"]
