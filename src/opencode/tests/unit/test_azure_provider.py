"""
Tests for Azure OpenAI Provider.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import httpx

from opencode.provider.azure import AzureOpenAIProvider
from opencode.provider.base import (
    AuthenticationError,
    ContentFilterError,
    ContextLengthExceededError,
    ModelNotFoundError,
    RateLimitError,
    Message,
    MessageRole,
    ToolDefinition,
)


@pytest.mark.unit
class TestAzureOpenAIProvider:
    """Tests for AzureOpenAIProvider class."""

    def test_provider_creation(self):
        """Test AzureOpenAIProvider instantiation."""
        provider = AzureOpenAIProvider(
            api_key="test-key",
            endpoint="https://test.openai.azure.com",
            deployment="gpt-4o",
        )
        assert provider is not None
        assert provider._api_key == "test-key"
        assert provider._endpoint == "https://test.openai.azure.com"
        assert provider._default_deployment == "gpt-4o"

    def test_provider_creation_with_api_version(self):
        """Test AzureOpenAIProvider with custom API version."""
        provider = AzureOpenAIProvider(
            api_key="test-key",
            endpoint="https://test.openai.azure.com",
            deployment="gpt-4o",
            api_version="2024-02-01",
        )
        assert provider._api_version == "2024-02-01"

    def test_provider_default_api_version(self):
        """Test AzureOpenAIProvider default API version."""
        provider = AzureOpenAIProvider(
            api_key="test-key",
            endpoint="https://test.openai.azure.com",
            deployment="gpt-4o",
        )
        assert provider._api_version == "2024-02-15-preview"

    def test_provider_name(self):
        """Test provider name property."""
        provider = AzureOpenAIProvider(
            api_key="test-key",
            endpoint="https://test.openai.azure.com",
            deployment="gpt-4o",
        )
        assert provider.name == "azure"

    def test_provider_models(self):
        """Test provider models property."""
        provider = AzureOpenAIProvider(
            api_key="test-key",
            endpoint="https://test.openai.azure.com",
            deployment="gpt-4o",
        )
        models = provider.models
        assert len(models) > 0
        assert any(m.id == "gpt-4o" for m in models)

    def test_get_chat_url(self):
        """Test chat URL generation."""
        provider = AzureOpenAIProvider(
            api_key="test-key",
            endpoint="https://test.openai.azure.com",
            deployment="gpt-4o",
        )
        url = provider._get_chat_url("my-deployment")
        assert "https://test.openai.azure.com/openai/deployments/my-deployment/chat/completions" in url
        assert "api-version=" in url

    def test_endpoint_trailing_slash(self):
        """Test that trailing slash is removed from endpoint."""
        provider = AzureOpenAIProvider(
            api_key="test-key",
            endpoint="https://test.openai.azure.com/",
            deployment="gpt-4o",
        )
        assert provider._endpoint == "https://test.openai.azure.com"

    @pytest.mark.asyncio
    async def test_complete_basic(self):
        """Test basic completion streaming."""
        provider = AzureOpenAIProvider(
            api_key="test-key",
            endpoint="https://test.openai.azure.com",
            deployment="gpt-4o",
        )
        
        # Create async generator for streaming
        async def mock_aiter_lines():
            yield 'data: {"choices": [{"delta": {"content": "Hello"}, "finish_reason": null}]}'
            yield 'data: {"choices": [{"delta": {"content": "!"}, "finish_reason": "stop"}]}'
            yield 'data: [DONE]'
        
        mock_response = MagicMock()
        mock_response.aiter_lines = mock_aiter_lines
        mock_response.status_code = 200
        
        with patch.object(provider._client, 'stream') as mock_stream:
            mock_stream.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_stream.return_value.__aexit__ = AsyncMock(return_value=None)
            
            messages = [Message(role=MessageRole.USER, content="Hi")]
            chunks = []
            async for chunk in provider.complete(messages, model="gpt-4o"):
                chunks.append(chunk)
            
            assert len(chunks) >= 1
            assert chunks[0].delta == "Hello"

    @pytest.mark.asyncio
    async def test_complete_with_tools(self):
        """Test completion with tool calling."""
        provider = AzureOpenAIProvider(
            api_key="test-key",
            endpoint="https://test.openai.azure.com",
            deployment="gpt-4o",
        )
        
        async def mock_aiter_lines():
            yield 'data: {"choices": [{"delta": {"tool_calls": [{"id": "call_123", "function": {"name": "get_weather", "arguments": "{\\"location\\": \\"NYC\\"}"}}]}, "finish_reason": "tool_calls"}]}'
            yield 'data: [DONE]'
        
        mock_response = MagicMock()
        mock_response.aiter_lines = mock_aiter_lines
        mock_response.status_code = 200
        
        with patch.object(provider._client, 'stream') as mock_stream:
            mock_stream.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_stream.return_value.__aexit__ = AsyncMock(return_value=None)
            
            messages = [Message(role=MessageRole.USER, content="What's the weather?")]
            tools = [ToolDefinition(
                name="get_weather",
                description="Get weather",
                parameters={"type": "object", "properties": {"location": {"type": "string"}}},
            )]
            chunks = []
            async for chunk in provider.complete(messages, model="gpt-4o", tools=tools):
                chunks.append(chunk)
            
            assert len(chunks) >= 1
            assert len(chunks[0].tool_calls) == 1
            assert chunks[0].tool_calls[0].name == "get_weather"

    @pytest.mark.asyncio
    async def test_complete_authentication_error(self):
        """Test completion with authentication error."""
        provider = AzureOpenAIProvider(
            api_key="invalid-key",
            endpoint="https://test.openai.azure.com",
            deployment="gpt-4o",
        )
        
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": {"message": "Invalid API key"}
        }
        mock_response.text = "Invalid API key"
        mock_response.headers = {}
        
        with patch.object(provider._client, 'stream') as mock_stream:
            mock_stream.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_stream.return_value.__aexit__ = AsyncMock(return_value=None)
            
            messages = [Message(role=MessageRole.USER, content="Hi")]
            
            with pytest.raises(AuthenticationError):
                async for _ in provider.complete(messages, model="gpt-4o"):
                    pass

    @pytest.mark.asyncio
    async def test_complete_rate_limit_error(self):
        """Test completion with rate limit error."""
        provider = AzureOpenAIProvider(
            api_key="test-key",
            endpoint="https://test.openai.azure.com",
            deployment="gpt-4o",
        )
        
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {
            "error": {"message": "Rate limit exceeded"}
        }
        mock_response.text = "Rate limit exceeded"
        mock_response.headers = {"retry-after": "60"}
        
        with patch.object(provider._client, 'stream') as mock_stream:
            mock_stream.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_stream.return_value.__aexit__ = AsyncMock(return_value=None)
            
            messages = [Message(role=MessageRole.USER, content="Hi")]
            
            with pytest.raises(RateLimitError):
                async for _ in provider.complete(messages, model="gpt-4o"):
                    pass

    @pytest.mark.asyncio
    async def test_complete_context_length_error(self):
        """Test completion with context length error."""
        provider = AzureOpenAIProvider(
            api_key="test-key",
            endpoint="https://test.openai.azure.com",
            deployment="gpt-4o",
        )
        
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": {"code": "context_length_exceeded", "message": "Context too long"}
        }
        mock_response.text = "Context too long"
        mock_response.headers = {}
        
        with patch.object(provider._client, 'stream') as mock_stream:
            mock_stream.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_stream.return_value.__aexit__ = AsyncMock(return_value=None)
            
            messages = [Message(role=MessageRole.USER, content="Hi")]
            
            with pytest.raises(ContextLengthExceededError):
                async for _ in provider.complete(messages, model="gpt-4o"):
                    pass

    @pytest.mark.asyncio
    async def test_complete_content_filter_error(self):
        """Test completion with content filter error."""
        provider = AzureOpenAIProvider(
            api_key="test-key",
            endpoint="https://test.openai.azure.com",
            deployment="gpt-4o",
        )
        
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": {"code": "content_filter", "message": "Content filtered"}
        }
        mock_response.text = "Content filtered"
        mock_response.headers = {}
        
        with patch.object(provider._client, 'stream') as mock_stream:
            mock_stream.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_stream.return_value.__aexit__ = AsyncMock(return_value=None)
            
            messages = [Message(role=MessageRole.USER, content="Hi")]
            
            with pytest.raises(ContentFilterError):
                async for _ in provider.complete(messages, model="gpt-4o"):
                    pass

    @pytest.mark.asyncio
    async def test_complete_model_not_found_error(self):
        """Test completion with model not found error."""
        provider = AzureOpenAIProvider(
            api_key="test-key",
            endpoint="https://test.openai.azure.com",
            deployment="gpt-4o",
        )
        
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {
            "error": {"code": "model_not_found", "message": "Model not found"}
        }
        mock_response.text = "Model not found"
        mock_response.headers = {}
        
        with patch.object(provider._client, 'stream') as mock_stream:
            mock_stream.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_stream.return_value.__aexit__ = AsyncMock(return_value=None)
            
            messages = [Message(role=MessageRole.USER, content="Hi")]
            
            with pytest.raises(ModelNotFoundError):
                async for _ in provider.complete(messages, model="gpt-4o"):
                    pass

    @pytest.mark.asyncio
    async def test_count_tokens(self):
        """Test token counting."""
        provider = AzureOpenAIProvider(
            api_key="test-key",
            endpoint="https://test.openai.azure.com",
            deployment="gpt-4o",
        )
        
        # Approximation: ~4 characters per token
        count = await provider.count_tokens("Hello world!", "gpt-4o")
        assert count == 3  # 12 chars / 4 = 3

    @pytest.mark.asyncio
    async def test_close(self):
        """Test closing the provider."""
        provider = AzureOpenAIProvider(
            api_key="test-key",
            endpoint="https://test.openai.azure.com",
            deployment="gpt-4o",
        )
        
        with patch.object(provider._client, 'aclose', new_callable=AsyncMock) as mock_close:
            await provider.close()
            mock_close.assert_called_once()

    def test_list_models(self):
        """Test listing models."""
        provider = AzureOpenAIProvider(
            api_key="test-key",
            endpoint="https://test.openai.azure.com",
            deployment="gpt-4o",
        )
        
        models = provider.models
        assert len(models) > 0
        assert any(m.id == "gpt-4o" for m in models)

    def test_get_model_info(self):
        """Test getting model info."""
        provider = AzureOpenAIProvider(
            api_key="test-key",
            endpoint="https://test.openai.azure.com",
            deployment="gpt-4o",
        )
        
        models = provider.models
        gpt4o = next((m for m in models if m.id == "gpt-4o"), None)
        assert gpt4o is not None
        assert gpt4o.id == "gpt-4o"
        assert gpt4o.provider == "azure"

    @pytest.mark.asyncio
    async def test_complete_no_deployment(self):
        """Test completion without deployment raises error."""
        provider = AzureOpenAIProvider(
            api_key="test-key",
            endpoint="https://test.openai.azure.com",
        )
        
        messages = [Message(role=MessageRole.USER, content="Hi")]
        
        with pytest.raises(Exception):  # ProviderError
            async for _ in provider.complete(messages, model=None):
                pass

    @pytest.mark.asyncio
    async def test_complete_with_system_message(self):
        """Test completion with system message."""
        provider = AzureOpenAIProvider(
            api_key="test-key",
            endpoint="https://test.openai.azure.com",
            deployment="gpt-4o",
        )
        
        async def mock_aiter_lines():
            yield 'data: {"choices": [{"delta": {"content": "Response"}, "finish_reason": "stop"}]}'
            yield 'data: [DONE]'
        
        mock_response = MagicMock()
        mock_response.aiter_lines = mock_aiter_lines
        mock_response.status_code = 200
        
        with patch.object(provider._client, 'stream') as mock_stream:
            mock_stream.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_stream.return_value.__aexit__ = AsyncMock(return_value=None)
            
            messages = [Message(role=MessageRole.USER, content="Hi")]
            chunks = []
            async for chunk in provider.complete(messages, model="gpt-4o", system="You are helpful"):
                chunks.append(chunk)
            
            assert len(chunks) >= 1
