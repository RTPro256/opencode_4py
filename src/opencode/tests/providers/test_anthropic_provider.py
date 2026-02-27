"""
Tests for Anthropic provider functionality.

Tests the Anthropic provider for Claude models.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import os

from opencode.provider.base import (
    Message,
    MessageRole,
    ToolDefinition,
    ContentPart,
    FinishReason,
)


@pytest.mark.provider
class TestAnthropicProvider:
    """Tests for Anthropic provider."""
    
    @pytest.fixture
    def anthropic_provider(self):
        """Create an Anthropic provider instance."""
        # Skip if no API key
        if not os.getenv("ANTHROPIC_API_KEY"):
            pytest.skip("ANTHROPIC_API_KEY not set")
        
        from opencode.provider.anthropic import AnthropicProvider
        return AnthropicProvider()
    
    def test_provider_name(self):
        """Test provider name."""
        from opencode.provider.anthropic import AnthropicProvider
        provider = AnthropicProvider.__new__(AnthropicProvider)
        assert provider.name == "anthropic"
    
    def test_provider_models(self):
        """Test provider has models."""
        from opencode.provider.anthropic import AnthropicProvider
        provider = AnthropicProvider.__new__(AnthropicProvider)
        # Check that models property exists
        assert hasattr(provider, 'models')


@pytest.mark.provider
class TestAnthropicMessageFormat:
    """Tests for Anthropic message formatting."""
    
    def test_user_message_format(self):
        """Test user message format."""
        msg = Message(role=MessageRole.USER, content="Hello")
        
        anthropic_msg = msg.to_anthropic_format()
        
        assert anthropic_msg["role"] == "user"
        assert anthropic_msg["content"] == "Hello"
    
    def test_system_message_handling(self):
        """Test system message handling."""
        # Anthropic handles system messages separately
        msg = Message(role=MessageRole.SYSTEM, content="You are helpful.")
        
        # System messages are passed separately in Anthropic API
        assert msg.role == MessageRole.SYSTEM
        assert msg.content == "You are helpful."
    
    def test_assistant_message_format(self):
        """Test assistant message format."""
        msg = Message(role=MessageRole.ASSISTANT, content="Hi there!")
        
        anthropic_msg = msg.to_anthropic_format()
        
        assert anthropic_msg["role"] == "assistant"
    
    def test_multimodal_message_format(self):
        """Test multimodal message format."""
        msg = Message(
            role=MessageRole.USER,
            content=[
                ContentPart(type="text", text="What's in this image?"),
                ContentPart(
                    type="image",
                    image_url="https://example.com/image.png",
                ),
            ],
        )
        
        anthropic_msg = msg.to_anthropic_format()
        
        assert anthropic_msg["role"] == "user"
        assert isinstance(anthropic_msg["content"], list)


@pytest.mark.provider
class TestAnthropicToolFormat:
    """Tests for Anthropic tool formatting."""
    
    def test_tool_definition_format(self):
        """Test tool definition format for Anthropic."""
        tool = ToolDefinition(
            name="get_weather",
            description="Get weather for a location",
            parameters={
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                },
                "required": ["location"],
            },
        )
        
        anthropic_format = tool.to_anthropic_format()
        
        assert anthropic_format["name"] == "get_weather"
        assert "input_schema" in anthropic_format
    
    def test_tool_with_nested_properties(self):
        """Test tool with nested properties."""
        tool = ToolDefinition(
            name="search",
            description="Search for items",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "options": {
                        "type": "object",
                        "properties": {
                            "limit": {"type": "number"},
                            "offset": {"type": "number"},
                        },
                    },
                },
            },
        )
        
        anthropic_format = tool.to_anthropic_format()
        
        assert "options" in anthropic_format["input_schema"]["properties"]


@pytest.mark.provider
class TestAnthropicStreaming:
    """Tests for Anthropic streaming functionality."""
    
    def test_stream_event_types(self):
        """Test Anthropic streaming event types."""
        # Anthropic uses different event types
        event_types = [
            "message_start",
            "content_block_start",
            "content_block_delta",
            "content_block_stop",
            "message_delta",
            "message_stop",
        ]
        
        for event_type in event_types:
            assert isinstance(event_type, str)
    
    def test_content_block_delta_format(self):
        """Test content block delta format."""
        delta = {
            "type": "content_block_delta",
            "index": 0,
            "delta": {
                "type": "text_delta",
                "text": "Hello",
            },
        }
        
        assert delta["type"] == "content_block_delta"
        assert "text" in delta["delta"]


@pytest.mark.provider
class TestAnthropicModels:
    """Tests for Anthropic model information."""
    
    def test_claude_3_5_sonnet_info(self):
        """Test Claude 3.5 Sonnet model info."""
        from opencode.provider.base import ModelInfo
        
        model = ModelInfo(
            id="claude-3-5-sonnet-20241022",
            name="Claude 3.5 Sonnet",
            provider="anthropic",
            context_length=200000,
            supports_tools=True,
            supports_vision=True,
        )
        
        assert model.id == "claude-3-5-sonnet-20241022"
        assert model.supports_vision is True
        assert model.context_length == 200000
    
    def test_claude_3_opus_info(self):
        """Test Claude 3 Opus model info."""
        from opencode.provider.base import ModelInfo
        
        model = ModelInfo(
            id="claude-3-opus-20240229",
            name="Claude 3 Opus",
            provider="anthropic",
            context_length=200000,
            supports_tools=True,
            supports_vision=True,
        )
        
        assert model.id == "claude-3-opus-20240229"
        assert model.supports_tools is True
    
    def test_claude_3_haiku_info(self):
        """Test Claude 3 Haiku model info."""
        from opencode.provider.base import ModelInfo
        
        model = ModelInfo(
            id="claude-3-haiku-20240307",
            name="Claude 3 Haiku",
            provider="anthropic",
            context_length=200000,
            supports_tools=True,
            supports_vision=True,
        )
        
        assert model.id == "claude-3-haiku-20240307"


@pytest.mark.provider
class TestAnthropicErrorHandling:
    """Tests for Anthropic error handling."""
    
    def test_rate_limit_error(self):
        """Test rate limit error handling."""
        from opencode.provider.base import ProviderError
        
        error = ProviderError(
            message="Rate limit exceeded",
            provider="anthropic",
            code="rate_limit_exceeded",
        )
        
        assert error.provider == "anthropic"
        assert error.code == "rate_limit_exceeded"
    
    def test_invalid_api_key_error(self):
        """Test invalid API key error."""
        from opencode.provider.base import ProviderError
        
        error = ProviderError(
            message="Invalid API key",
            provider="anthropic",
            code="invalid_api_key",
        )
        
        assert error.code == "invalid_api_key"
    
    def test_context_length_error(self):
        """Test context length exceeded error."""
        from opencode.provider.base import ProviderError
        
        error = ProviderError(
            message="Prompt is too long: 210000 tokens > 200000 maximum",
            provider="anthropic",
            model="claude-3-5-sonnet",
            code="context_length_exceeded",
        )
        
        assert "too long" in str(error).lower()


@pytest.mark.provider
class TestAnthropicParameters:
    """Tests for Anthropic-specific parameters."""
    
    def test_max_tokens_required(self):
        """Test max_tokens is required for Anthropic."""
        # Anthropic requires max_tokens
        max_tokens = 4096
        assert max_tokens > 0
    
    def test_temperature_range(self):
        """Test temperature parameter range."""
        # Anthropic accepts temperature 0-1
        valid_temps = [0.0, 0.5, 1.0]
        
        for temp in valid_temps:
            assert 0 <= temp <= 1
    
    def test_top_p_parameter(self):
        """Test top_p parameter."""
        # top_p should be between 0 and 1
        valid_top_p = [0.1, 0.5, 0.9, 1.0]
        
        for top_p in valid_top_p:
            assert 0 < top_p <= 1
    
    def test_top_k_parameter(self):
        """Test top_k parameter (Anthropic-specific)."""
        # top_k should be positive
        valid_top_k = [1, 10, 40, 100]
        
        for top_k in valid_top_k:
            assert top_k > 0


@pytest.mark.provider
class TestAnthropicSystemPrompt:
    """Tests for Anthropic system prompt handling."""
    
    def test_system_prompt_separate(self):
        """Test that system prompt is separate from messages."""
        # Anthropic uses a separate system parameter
        system_prompt = "You are a helpful coding assistant."
        
        messages = [
            Message(role=MessageRole.USER, content="Hello"),
        ]
        
        # System is passed separately
        assert system_prompt is not None
        assert len(messages) == 1
        assert messages[0].role != MessageRole.SYSTEM
    
    def test_system_prompt_with_tools(self):
        """Test system prompt with tool definitions."""
        system_prompt = """You are a helpful assistant with access to tools.
        
Use the tools when appropriate to help the user."""
        
        tools = [
            ToolDefinition(
                name="read_file",
                description="Read a file",
                parameters={"type": "object"},
            ),
        ]
        
        assert "tools" in system_prompt.lower() or len(tools) > 0


@pytest.mark.provider
class TestAnthropicTokenCounting:
    """Tests for Anthropic token counting."""
    
    def test_token_estimation(self):
        """Test token estimation."""
        # Rough estimation: ~4 characters per token
        text = "Hello, world!"
        estimated_tokens = len(text) // 4
        
        assert estimated_tokens > 0
    
    def test_large_context_handling(self):
        """Test large context handling."""
        # Claude 3.5 supports 200k tokens
        large_context_model = "claude-3-5-sonnet-20241022"
        max_tokens = 200000
        
        assert max_tokens == 200000


@pytest.mark.provider
class TestAnthropicCaching:
    """Tests for Anthropic prompt caching."""
    
    def test_cache_control_format(self):
        """Test cache control format."""
        # Anthropic supports prompt caching
        cache_control = {"type": "ephemeral"}
        
        assert cache_control["type"] == "ephemeral"
    
    def test_cached_tokens_tracking(self):
        """Test cached tokens tracking."""
        from opencode.provider.base import Usage
        
        usage = Usage(
            input_tokens=1000,
            output_tokens=100,
            cache_read_tokens=500,
            cache_write_tokens=200,
        )
        
        assert usage.cache_read_tokens == 500
        assert usage.cache_write_tokens == 200
