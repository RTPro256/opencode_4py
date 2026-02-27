"""
Tests for Cerebras Provider.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from opencode.provider.cerebras import CerebrasProvider
from opencode.provider.base import (
    Message,
    MessageRole,
    ToolDefinition,
)


@pytest.mark.unit
class TestCerebrasProvider:
    """Tests for CerebrasProvider class."""

    def test_provider_creation(self):
        """Test CerebrasProvider instantiation."""
        provider = CerebrasProvider(api_key="test-key")
        assert provider is not None

    def test_provider_name(self):
        """Test provider name property."""
        provider = CerebrasProvider(api_key="test-key")
        assert provider.name == "cerebras"

    def test_provider_models(self):
        """Test provider models property."""
        provider = CerebrasProvider(api_key="test-key")
        models = provider.models
        assert len(models) > 0

    @pytest.mark.asyncio
    async def test_complete_basic(self):
        """Test basic completion."""
        provider = CerebrasProvider(api_key="test-key")
        
        async def mock_aiter_lines():
            yield 'data: {"choices": [{"delta": {"content": "Hello"}}]}'
            yield 'data: [DONE]'
        
        mock_response = MagicMock()
        mock_response.aiter_lines = mock_aiter_lines
        mock_response.status_code = 200
        
        with patch.object(provider._client, 'stream') as mock_stream:
            mock_stream.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_stream.return_value.__aexit__ = AsyncMock(return_value=None)
            
            messages = [Message(role=MessageRole.USER, content="Hi")]
            chunks = []
            async for chunk in provider.complete(messages, model="llama3.1-8b"):
                chunks.append(chunk)
            
            assert len(chunks) >= 1

    @pytest.mark.asyncio
    async def test_count_tokens(self):
        """Test token counting."""
        provider = CerebrasProvider(api_key="test-key")
        
        count = await provider.count_tokens("Hello world!", "llama3.1-8b")
        assert count > 0

    @pytest.mark.asyncio
    async def test_close(self):
        """Test closing the provider."""
        provider = CerebrasProvider(api_key="test-key")
        
        with patch.object(provider._client, 'aclose', new_callable=AsyncMock) as mock_close:
            await provider.close()
            mock_close.assert_called_once()
