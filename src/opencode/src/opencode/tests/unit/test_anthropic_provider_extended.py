"""
Extended unit tests for Anthropic provider implementation.
Tests streaming, error handling, and API interactions.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from contextlib import asynccontextmanager
import json
import httpx

from opencode.provider.anthropic import AnthropicProvider
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


class TestAnthropicProviderInit:
    """Tests for AnthropicProvider initialization."""

    def test_init_with_api_key(self):
        """Test initialization with explicit API key."""
        provider = AnthropicProvider(api_key="test-key")
        assert provider.api_key == "test-key"
        assert provider.base_url == AnthropicProvider.API_URL

    def test_init_with_base_url(self):
        """Test initialization with custom base URL."""
        provider = AnthropicProvider(api_key="test-key", base_url="https://custom.api.com")
        assert provider.base_url == "https://custom.api.com"

    def test_init_with_default_headers(self):
        """Test initialization with default headers."""
        headers = {"X-Custom": "value"}
        provider = AnthropicProvider(api_key="test-key", default_headers=headers)
        assert provider.default_headers == headers

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "env-key"})
    def test_init_with_env_api_key(self):
        """Test initialization with API key from environment."""
        provider = AnthropicProvider()
        assert provider.api_key == "env-key"

    def test_init_without_api_key_raises_error(self):
        """Test that missing API key raises AuthenticationError."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(AuthenticationError) as exc_info:
                AnthropicProvider()
            assert "Anthropic API key not provided" in str(exc_info.value)


class TestAnthropicProviderComplete:
    """Tests for the complete method."""

    @pytest.fixture
    def provider(self):
        """Create an AnthropicProvider instance."""
        return AnthropicProvider(api_key="test-api-key")

    @pytest.mark.asyncio
    async def test_complete_sync_mode(self, provider):
        """Test non-streaming completion."""
        messages = [Message(role=MessageRole.USER, content="Hello")]
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": [{"type": "text", "text": "Hi there!"}],
            "usage": {"input_tokens": 10, "output_tokens": 5}
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            chunks = []
            async for chunk in provider.complete(messages, "claude-3-5-sonnet-20241022", stream=False):
                chunks.append(chunk)
            
            assert len(chunks) >= 1
            assert any("Hi there!" in c.delta for c in chunks if c.delta)

    @pytest.mark.asyncio
    async def test_complete_with_system_prompt(self, provider):
        """Test completion with system prompt."""
        messages = [Message(role=MessageRole.USER, content="Hello")]
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": [{"type": "text", "text": "Response"}],
            "usage": {"input_tokens": 10, "output_tokens": 5}
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            chunks = []
            async for chunk in provider.complete(messages, "claude-3-5-sonnet-20241022", stream=False, system="You are helpful"):
                chunks.append(chunk)
            
            # Verify system was included in request
            call_args = mock_post.call_args
            assert "system" in call_args.kwargs["json"]

    @pytest.mark.asyncio
    async def test_complete_with_tools(self, provider):
        """Test completion with tools."""
        messages = [Message(role=MessageRole.USER, content="What's the weather?")]
        tools = [ToolDefinition(name="get_weather", description="Get weather", parameters={})]
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": [{"type": "text", "text": "Let me check."}],
            "usage": {"input_tokens": 10, "output_tokens": 5}
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            chunks = []
            async for chunk in provider.complete(messages, "claude-3-5-sonnet-20241022", tools=tools, stream=False):
                chunks.append(chunk)
            
            # Verify tools were included in request
            call_args = mock_post.call_args
            assert "tools" in call_args.kwargs["json"]

    @pytest.mark.asyncio
    async def test_complete_with_tool_calls(self, provider):
        """Test completion that returns tool calls."""
        messages = [Message(role=MessageRole.USER, content="What's the weather?")]
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": [
                {"type": "tool_use", "id": "tool_123", "name": "get_weather", "input": {"location": "NYC"}}
            ],
            "usage": {"input_tokens": 10, "output_tokens": 5}
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            chunks = []
            async for chunk in provider.complete(messages, "claude-3-5-sonnet-20241022", stream=False):
                chunks.append(chunk)
            
            # Should have tool call chunks
            tool_call_chunks = [c for c in chunks if c.tool_calls]
            assert len(tool_call_chunks) > 0

    @pytest.mark.asyncio
    async def test_complete_with_additional_options(self, provider):
        """Test completion with additional options like top_p, top_k."""
        messages = [Message(role=MessageRole.USER, content="Hello")]
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": [{"type": "text", "text": "Response"}],
            "usage": {"input_tokens": 10, "output_tokens": 5}
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            chunks = []
            async for chunk in provider.complete(
                messages, "claude-3-5-sonnet-20241022", 
                stream=False, 
                top_p=0.9, 
                top_k=50,
                stop_sequences=["END"]
            ):
                chunks.append(chunk)
            
            # Verify additional options were included
            call_args = mock_post.call_args
            body = call_args.kwargs["json"]
            assert body["top_p"] == 0.9
            assert body["top_k"] == 50
            assert body["stop_sequences"] == ["END"]

    @pytest.mark.asyncio
    async def test_complete_with_cache_prompt(self, provider):
        """Test completion with prompt caching."""
        messages = [Message(role=MessageRole.USER, content="Hello")]
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": [{"type": "text", "text": "Response"}],
            "usage": {"input_tokens": 10, "output_tokens": 5}
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            chunks = []
            async for chunk in provider.complete(
                messages, "claude-3-5-sonnet-20241022", 
                stream=False, 
                system="System prompt",
                cache_prompt=True
            ):
                chunks.append(chunk)
            
            # Verify cache_control was added
            call_args = mock_post.call_args
            body = call_args.kwargs["json"]
            # System should be converted to list with cache_control
            assert isinstance(body.get("system"), list)


class TestAnthropicProviderStreaming:
    """Tests for streaming completion."""

    @pytest.fixture
    def provider(self):
        """Create an AnthropicProvider instance."""
        return AnthropicProvider(api_key="test-api-key")

    @pytest.mark.asyncio
    async def test_stream_text_content(self, provider):
        """Test streaming text content."""
        messages = [Message(role=MessageRole.USER, content="Hello")]
        
        # Create mock stream response
        async def mock_aiter_lines():
            lines = [
                'data: {"type": "message_start", "message": {"usage": {"input_tokens": 10}}}',
                'data: {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "Hello"}}',
                'data: {"type": "content_block_delta", "delta": {"type": "text_delta", "text": " there"}}',
                'data: {"type": "message_delta", "delta": {"stop_reason": "end_turn"}, "usage": {"output_tokens": 5}}',
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
            async for chunk in provider.complete(messages, "claude-3-5-sonnet-20241022", stream=True):
                chunks.append(chunk)
            
            text_chunks = [c for c in chunks if c.delta]
            assert len(text_chunks) >= 2
            assert "Hello" in "".join(c.delta for c in text_chunks)

    @pytest.mark.asyncio
    async def test_stream_tool_call(self, provider):
        """Test streaming tool call content."""
        messages = [Message(role=MessageRole.USER, content="What's the weather?")]
        
        async def mock_aiter_lines():
            lines = [
                'data: {"type": "message_start", "message": {"usage": {"input_tokens": 10}}}',
                'data: {"type": "content_block_start", "content_block": {"type": "tool_use", "id": "tool_123", "name": "get_weather"}}',
                'data: {"type": "content_block_delta", "delta": {"type": "input_json_delta", "partial_json": "{\\"loc"}}',
                'data: {"type": "content_block_delta", "delta": {"type": "input_json_delta", "partial_json": "ation\\": \\"NYC\\"}"}}',
                'data: {"type": "content_block_stop"}',
                'data: {"type": "message_delta", "delta": {"stop_reason": "tool_use"}, "usage": {"output_tokens": 5}}',
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
            async for chunk in provider.complete(messages, "claude-3-5-sonnet-20241022", stream=True):
                chunks.append(chunk)
            
            tool_call_chunks = [c for c in chunks if c.tool_calls]
            assert len(tool_call_chunks) == 1
            assert tool_call_chunks[0].tool_calls[0].name == "get_weather"

    @pytest.mark.asyncio
    async def test_stream_with_cache_tokens(self, provider):
        """Test streaming with cache token tracking."""
        messages = [Message(role=MessageRole.USER, content="Hello")]
        
        async def mock_aiter_lines():
            lines = [
                'data: {"type": "message_start", "message": {"usage": {"input_tokens": 10, "cache_read_input_tokens": 5, "cache_creation_input_tokens": 3}}}',
                'data: {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "Hi"}}',
                'data: {"type": "message_delta", "delta": {"stop_reason": "end_turn"}, "usage": {"output_tokens": 2}}',
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
            async for chunk in provider.complete(messages, "claude-3-5-sonnet-20241022", stream=True):
                chunks.append(chunk)
            
            done_chunks = [c for c in chunks if c.finish_reason is not None]
            assert len(done_chunks) == 1
            assert done_chunks[0].usage.cache_read_tokens == 5
            assert done_chunks[0].usage.cache_write_tokens == 3


class TestAnthropicProviderErrorHandling:
    """Tests for error handling."""

    @pytest.fixture
    def provider(self):
        """Create an AnthropicProvider instance."""
        return AnthropicProvider(api_key="test-api-key")

    def test_handle_401_error(self, provider):
        """Test handling 401 authentication error."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": {"message": "Invalid API key"}}
        
        error = httpx.HTTPStatusError("401", request=MagicMock(), response=mock_response)
        result = provider._handle_error(error)
        
        assert isinstance(result, AuthenticationError)
        assert "Invalid API key" in str(result)

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
        mock_response.headers = {"retry-after": "60"}
        mock_response.json.return_value = {"error": {"message": "Rate limit exceeded"}}
        
        error = httpx.HTTPStatusError("429", request=MagicMock(), response=mock_response)
        result = provider._handle_error(error)
        
        assert isinstance(result, RateLimitError)
        assert result.retry_after == 60

    def test_handle_429_error_without_retry_after(self, provider):
        """Test handling 429 rate limit error without retry-after header."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {}
        mock_response.json.return_value = {"error": {"message": "Rate limit exceeded"}}
        
        error = httpx.HTTPStatusError("429", request=MagicMock(), response=mock_response)
        result = provider._handle_error(error)
        
        assert isinstance(result, RateLimitError)
        assert result.retry_after is None

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


class TestAnthropicProviderCountTokens:
    """Tests for token counting."""

    @pytest.fixture
    def provider(self):
        """Create an AnthropicProvider instance."""
        return AnthropicProvider(api_key="test-api-key")

    @pytest.mark.asyncio
    async def test_count_tokens_api_success(self, provider):
        """Test token counting via API."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"input_tokens": 42}
        mock_response.raise_for_status = MagicMock()
        
        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            result = await provider.count_tokens("Hello world", "claude-3-5-sonnet-20241022")
            
            assert result == 42

    @pytest.mark.asyncio
    async def test_count_tokens_fallback_on_error(self, provider):
        """Test token counting fallback when API fails."""
        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = Exception("API error")
            
            result = await provider.count_tokens("Hello world", "claude-3-5-sonnet-20241022")
            
            # Should fallback to ~4 chars per token
            assert result == len("Hello world") // 4


class TestAnthropicProviderClose:
    """Tests for closing the provider."""

    @pytest.fixture
    def provider(self):
        """Create an AnthropicProvider instance."""
        return AnthropicProvider(api_key="test-api-key")

    @pytest.mark.asyncio
    async def test_close_client(self, provider):
        """Test closing the HTTP client."""
        with patch.object(provider._client, 'aclose', new_callable=AsyncMock) as mock_close:
            await provider.close()
            mock_close.assert_called_once()


class TestAnthropicProviderMessageFormats:
    """Tests for message format conversions."""

    @pytest.fixture
    def provider(self):
        """Create an AnthropicProvider instance."""
        return AnthropicProvider(api_key="test-api-key")

    def test_message_to_anthropic_format_with_image(self, provider):
        """Test message with image converts correctly."""
        message = Message(
            role=MessageRole.USER,
            content=[
                ContentPart(type="text", text="What's in this image?"),
                ContentPart(type="image", image_url="https://example.com/image.png")
            ]
        )
        
        result = message.to_anthropic_format()
        
        assert result["role"] == "user"
        assert isinstance(result["content"], list)
        assert len(result["content"]) == 2

    def test_message_to_anthropic_format_with_tool_result(self, provider):
        """Test message with tool result converts correctly."""
        message = Message(
            role=MessageRole.USER,
            content=[
                ContentPart(
                    type="tool_result",
                    tool_call_id="tool_123",
                    text="Temperature: 72F"
                )
            ]
        )
        
        result = message.to_anthropic_format()
        
        assert result["role"] == "user"
        assert isinstance(result["content"], list)
        assert result["content"][0]["type"] == "tool_result"

    def test_message_to_anthropic_format_assistant_with_tool_call(self, provider):
        """Test assistant message with tool call converts correctly."""
        message = Message(
            role=MessageRole.ASSISTANT,
            content=[
                ContentPart(type="text", text="Let me check that."),
                ContentPart(
                    type="tool_call",
                    tool_call=ToolCall(
                        id="tool_123",
                        name="get_weather",
                        arguments={"location": "NYC"}
                    )
                )
            ]
        )
        
        result = message.to_anthropic_format()
        
        assert result["role"] == "assistant"
        assert isinstance(result["content"], list)
        tool_use_blocks = [c for c in result["content"] if c["type"] == "tool_use"]
        assert len(tool_use_blocks) == 1
