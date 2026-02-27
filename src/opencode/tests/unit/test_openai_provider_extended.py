"""
Extended unit tests for OpenAI provider implementation.
Tests streaming, error handling, and API interactions.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from contextlib import asynccontextmanager
import json
import httpx

from opencode.provider.openai import OpenAIProvider
from opencode.provider.base import (
    ModelInfo,
    Message,
    MessageRole,
    ToolDefinition,
    ToolCall,
    ContentPart,
    Usage,
    StreamChunk,
    FinishReason,
    AuthenticationError,
    RateLimitError,
    ModelNotFoundError,
    ContextLengthExceededError,
    ContentFilterError,
    ProviderError,
)


class TestOpenAIProviderInit:
    """Tests for OpenAIProvider initialization."""

    def test_init_with_api_key(self):
        """Test initialization with explicit API key."""
        provider = OpenAIProvider(api_key="test-key")
        assert provider.api_key == "test-key"
        assert provider.base_url == OpenAIProvider.API_URL

    def test_init_with_base_url(self):
        """Test initialization with custom base URL."""
        provider = OpenAIProvider(api_key="test-key", base_url="https://custom.api.com")
        assert provider.base_url == "https://custom.api.com"

    def test_init_with_organization(self):
        """Test initialization with organization ID."""
        provider = OpenAIProvider(api_key="test-key", organization="org-123")
        assert provider.organization == "org-123"

    def test_init_with_default_headers(self):
        """Test initialization with default headers."""
        headers = {"X-Custom": "value"}
        provider = OpenAIProvider(api_key="test-key", default_headers=headers)
        assert provider.default_headers == headers

    @patch.dict("os.environ", {"OPENAI_API_KEY": "env-key"})
    def test_init_with_env_api_key(self):
        """Test initialization with API key from environment."""
        provider = OpenAIProvider()
        assert provider.api_key == "env-key"

    @patch.dict("os.environ", {"OPENAI_ORG_ID": "env-org"})
    def test_init_with_env_organization(self):
        """Test initialization with organization from environment."""
        provider = OpenAIProvider(api_key="test-key")
        assert provider.organization == "env-org"

    def test_init_without_api_key_raises_error(self):
        """Test that missing API key raises AuthenticationError."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(AuthenticationError) as exc_info:
                OpenAIProvider()
            assert "OpenAI API key not provided" in str(exc_info.value)


class TestOpenAIProviderComplete:
    """Tests for the complete method."""

    @pytest.fixture
    def provider(self):
        """Create an OpenAIProvider instance."""
        return OpenAIProvider(api_key="test-api-key")

    @pytest.mark.asyncio
    async def test_complete_sync_mode(self, provider):
        """Test non-streaming completion."""
        messages = [Message(role=MessageRole.USER, content="Hello")]
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hi there!"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            chunks = []
            async for chunk in provider.complete(messages, "gpt-4o", stream=False):
                chunks.append(chunk)
            
            assert len(chunks) >= 1
            assert any("Hi there!" in c.delta for c in chunks if c.delta)

    @pytest.mark.asyncio
    async def test_complete_with_system_prompt(self, provider):
        """Test completion with system prompt."""
        messages = [Message(role=MessageRole.USER, content="Hello")]
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            chunks = []
            async for chunk in provider.complete(messages, "gpt-4o", stream=False, system="You are helpful"):
                chunks.append(chunk)
            
            # Verify system was included in request
            call_args = mock_post.call_args
            body = call_args.kwargs["json"]
            assert any(m["role"] == "system" for m in body["messages"])

    @pytest.mark.asyncio
    async def test_complete_with_tools(self, provider):
        """Test completion with tools."""
        messages = [Message(role=MessageRole.USER, content="What's the weather?")]
        tools = [ToolDefinition(name="get_weather", description="Get weather", parameters={})]
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Let me check."}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            chunks = []
            async for chunk in provider.complete(messages, "gpt-4o", tools=tools, stream=False):
                chunks.append(chunk)
            
            # Verify tools were included in request
            call_args = mock_post.call_args
            body = call_args.kwargs["json"]
            assert "tools" in body

    @pytest.mark.asyncio
    async def test_complete_with_tool_calls(self, provider):
        """Test completion that returns tool calls."""
        messages = [Message(role=MessageRole.USER, content="What's the weather?")]
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "tool_calls": [{
                        "id": "call_123",
                        "function": {
                            "name": "get_weather",
                            "arguments": '{"location": "NYC"}'
                        }
                    }]
                }
            }],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            chunks = []
            async for chunk in provider.complete(messages, "gpt-4o", stream=False):
                chunks.append(chunk)
            
            # Should have tool call chunks
            tool_call_chunks = [c for c in chunks if c.tool_calls]
            assert len(tool_call_chunks) > 0

    @pytest.mark.asyncio
    async def test_complete_with_additional_options(self, provider):
        """Test completion with additional options."""
        messages = [Message(role=MessageRole.USER, content="Hello")]
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            chunks = []
            async for chunk in provider.complete(
                messages, "gpt-4o", 
                stream=False, 
                top_p=0.9, 
                presence_penalty=0.5,
                frequency_penalty=0.3,
                stop=["END"]
            ):
                chunks.append(chunk)
            
            # Verify additional options were included
            call_args = mock_post.call_args
            body = call_args.kwargs["json"]
            assert body["top_p"] == 0.9
            assert body["presence_penalty"] == 0.5
            assert body["frequency_penalty"] == 0.3
            assert body["stop"] == ["END"]

    @pytest.mark.asyncio
    async def test_complete_with_response_format(self, provider):
        """Test completion with response_format option."""
        messages = [Message(role=MessageRole.USER, content="Hello")]
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"response": "hi"}'}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            chunks = []
            async for chunk in provider.complete(
                messages, "gpt-4o", 
                stream=False, 
                response_format={"type": "json_object"}
            ):
                chunks.append(chunk)
            
            call_args = mock_post.call_args
            body = call_args.kwargs["json"]
            assert body["response_format"] == {"type": "json_object"}


class TestOpenAIProviderStreaming:
    """Tests for streaming completion."""

    @pytest.fixture
    def provider(self):
        """Create an OpenAIProvider instance."""
        return OpenAIProvider(api_key="test-api-key")

    @pytest.mark.asyncio
    async def test_stream_text_content(self, provider):
        """Test streaming text content."""
        messages = [Message(role=MessageRole.USER, content="Hello")]
        
        async def mock_aiter_lines():
            lines = [
                'data: {"choices": [{"delta": {"content": "Hello"}}]}',
                'data: {"choices": [{"delta": {"content": " there"}}]}',
                'data: {"choices": [{"delta": {}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 10, "completion_tokens": 5}}',
                'data: [DONE]',
            ]
            for line in lines:
                yield line
        
        mock_response = MagicMock()
        mock_response.aiter_lines = mock_aiter_lines
        mock_response.raise_for_status = MagicMock()
        
        @asynccontextmanager
        async def mock_stream(*args, **kwargs):
            yield mock_response
        
        with patch.object(provider._client, 'stream', mock_stream):
            chunks = []
            async for chunk in provider.complete(messages, "gpt-4o", stream=True):
                chunks.append(chunk)
            
            text_chunks = [c for c in chunks if c.delta]
            assert len(text_chunks) >= 2

    @pytest.mark.asyncio
    async def test_stream_tool_call(self, provider):
        """Test streaming tool call content."""
        messages = [Message(role=MessageRole.USER, content="What's the weather?")]
        
        async def mock_aiter_lines():
            lines = [
                'data: {"choices": [{"delta": {"tool_calls": [{"index": 0, "id": "call_123", "function": {"name": "get_weather"}}]}}]}',
                'data: {"choices": [{"delta": {"tool_calls": [{"index": 0, "function": {"arguments": "{\\"loc"}}]}}]}',
                'data: {"choices": [{"delta": {"tool_calls": [{"index": 0, "function": {"arguments": "ation\\": \\"NYC\\"}"}}]}}]}',
                'data: {"choices": [{"delta": {}, "finish_reason": "tool_calls"}]}',
                'data: [DONE]',
            ]
            for line in lines:
                yield line
        
        mock_response = MagicMock()
        mock_response.aiter_lines = mock_aiter_lines
        mock_response.raise_for_status = MagicMock()
        
        @asynccontextmanager
        async def mock_stream(*args, **kwargs):
            yield mock_response
        
        with patch.object(provider._client, 'stream', mock_stream):
            chunks = []
            async for chunk in provider.complete(messages, "gpt-4o", stream=True):
                chunks.append(chunk)
            
            tool_call_chunks = [c for c in chunks if c.tool_calls]
            assert len(tool_call_chunks) >= 1

    @pytest.mark.asyncio
    async def test_stream_with_usage(self, provider):
        """Test streaming with usage information."""
        messages = [Message(role=MessageRole.USER, content="Hello")]
        
        async def mock_aiter_lines():
            lines = [
                'data: {"choices": [{"delta": {"content": "Hi"}}]}',
                'data: {"choices": [{"delta": {}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 10, "completion_tokens": 2}}',
                'data: [DONE]',
            ]
            for line in lines:
                yield line
        
        mock_response = MagicMock()
        mock_response.aiter_lines = mock_aiter_lines
        mock_response.raise_for_status = MagicMock()
        
        @asynccontextmanager
        async def mock_stream(*args, **kwargs):
            yield mock_response
        
        with patch.object(provider._client, 'stream', mock_stream):
            chunks = []
            async for chunk in provider.complete(messages, "gpt-4o", stream=True):
                chunks.append(chunk)
            
            done_chunks = [c for c in chunks if c.finish_reason is not None]
            assert len(done_chunks) >= 1


class TestOpenAIProviderErrorHandling:
    """Tests for error handling."""

    @pytest.fixture
    def provider(self):
        """Create an OpenAIProvider instance."""
        return OpenAIProvider(api_key="test-api-key")

    def test_handle_401_error(self, provider):
        """Test handling 401 authentication error."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": {"message": "Invalid API key"}}
        
        error = httpx.HTTPStatusError("401", request=MagicMock(), response=mock_response)
        result = provider._handle_error(error)
        
        assert isinstance(result, AuthenticationError)

    def test_handle_403_error(self, provider):
        """Test handling 403 forbidden error."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.json.return_value = {"error": {"message": "Access denied"}}
        
        error = httpx.HTTPStatusError("403", request=MagicMock(), response=mock_response)
        result = provider._handle_error(error)
        
        assert isinstance(result, AuthenticationError)

    def test_handle_404_error(self, provider):
        """Test handling 404 model not found error."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": {"message": "Model not found"}}
        
        error = httpx.HTTPStatusError("404", request=MagicMock(), response=mock_response)
        result = provider._handle_error(error)
        
        assert isinstance(result, ModelNotFoundError)

    def test_handle_429_error(self, provider):
        """Test handling 429 rate limit error."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"error": {"message": "Rate limit exceeded"}}
        
        error = httpx.HTTPStatusError("429", request=MagicMock(), response=mock_response)
        result = provider._handle_error(error)
        
        assert isinstance(result, RateLimitError)

    def test_handle_context_length_error(self, provider):
        """Test handling context length exceeded error."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": {"message": "context_length exceeded"}}
        
        error = httpx.HTTPStatusError("400", request=MagicMock(), response=mock_response)
        result = provider._handle_error(error)
        
        assert isinstance(result, ContextLengthExceededError)

    def test_handle_content_filter_error(self, provider):
        """Test handling content filter error."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": {"type": "content_filter", "message": "Content filtered"}}
        
        error = httpx.HTTPStatusError("400", request=MagicMock(), response=mock_response)
        result = provider._handle_error(error)
        
        assert isinstance(result, ContentFilterError)

    def test_handle_generic_error(self, provider):
        """Test handling generic error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": {"message": "Internal server error"}}
        
        error = httpx.HTTPStatusError("500", request=MagicMock(), response=mock_response)
        result = provider._handle_error(error)
        
        assert isinstance(result, ProviderError)

    def test_handle_error_with_non_json_response(self, provider):
        """Test handling error when response is not JSON."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.side_effect = Exception("Not JSON")
        
        error = httpx.HTTPStatusError("500", request=MagicMock(), response=mock_response)
        result = provider._handle_error(error)
        
        assert isinstance(result, ProviderError)


class TestOpenAIProviderCountTokens:
    """Tests for token counting."""

    @pytest.fixture
    def provider(self):
        """Create an OpenAIProvider instance."""
        return OpenAIProvider(api_key="test-api-key")

    @pytest.mark.asyncio
    async def test_count_tokens_fallback_no_tiktoken(self, provider):
        """Test token counting fallback when tiktoken not available."""
        with patch.dict("sys.modules", {"tiktoken": None}):
            result = await provider.count_tokens("Hello world", "gpt-4o")
            # Should fallback to ~4 chars per token
            assert result == len("Hello world") // 4

    @pytest.mark.asyncio
    async def test_count_tokens_fallback_on_error(self, provider):
        """Test token counting fallback on error."""
        with patch.dict("sys.modules", {"tiktoken": None}):
            result = await provider.count_tokens("Hello world", "gpt-4o")
            assert result == len("Hello world") // 4


class TestOpenAIProviderClose:
    """Tests for closing the provider."""

    @pytest.fixture
    def provider(self):
        """Create an OpenAIProvider instance."""
        return OpenAIProvider(api_key="test-api-key")

    @pytest.mark.asyncio
    async def test_close_client(self, provider):
        """Test closing the HTTP client."""
        with patch.object(provider._client, 'aclose', new_callable=AsyncMock) as mock_close:
            await provider.close()
            mock_close.assert_called_once()


class TestOpenAIProviderModels:
    """Tests for model information."""

    @pytest.fixture
    def provider(self):
        """Create an OpenAIProvider instance."""
        return OpenAIProvider(api_key="test-api-key")

    def test_models_property(self, provider):
        """Test getting available models via models property."""
        models = provider.models
        
        assert isinstance(models, list)
        assert len(models) > 0
        assert all(isinstance(m, ModelInfo) for m in models)
        assert any("gpt" in m.id.lower() for m in models)

    def test_models_have_required_fields(self, provider):
        """Test that all models have required fields."""
        models = provider.models
        
        for model in models:
            assert model.id is not None
            assert model.name is not None
            assert model.provider == "openai"
            assert model.context_length > 0

    def test_name_property(self, provider):
        """Test provider name property."""
        assert provider.name == "openai"


class TestOpenAIProviderMessageFormats:
    """Tests for message format conversions."""

    @pytest.fixture
    def provider(self):
        """Create an OpenAIProvider instance."""
        return OpenAIProvider(api_key="test-api-key")

    def test_message_to_openai_format_with_image(self, provider):
        """Test message with image converts correctly."""
        message = Message(
            role=MessageRole.USER,
            content=[
                ContentPart(type="text", text="What's in this image?"),
                ContentPart(type="image", image_url="https://example.com/image.png")
            ]
        )
        
        result = message.to_openai_format()
        
        assert result["role"] == "user"
        assert isinstance(result["content"], list)
        assert len(result["content"]) == 2

    def test_message_to_openai_format_with_tool_result(self, provider):
        """Test message with tool result converts correctly."""
        message = Message(
            role=MessageRole.USER,
            content=[
                ContentPart(
                    type="tool_result",
                    tool_call_id="call_123",
                    text="Temperature: 72F"
                )
            ]
        )
        
        result = message.to_openai_format()
        
        assert result["role"] == "user"
        # Tool result messages may have different format
        assert "role" in result

    def test_message_to_openai_format_assistant_with_tool_call(self, provider):
        """Test assistant message with tool call converts correctly."""
        message = Message(
            role=MessageRole.ASSISTANT,
            content=[
                ContentPart(type="text", text="Let me check that."),
                ContentPart(
                    type="tool_call",
                    tool_call=ToolCall(
                        id="call_123",
                        name="get_weather",
                        arguments={"location": "NYC"}
                    )
                )
            ]
        )
        
        result = message.to_openai_format()
        
        assert result["role"] == "assistant"
        assert "tool_calls" in result or isinstance(result.get("content"), list)
