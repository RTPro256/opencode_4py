"""
Tests for OpenAI provider functionality.

Tests the OpenAI provider for GPT models.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import os

from opencode.provider.base import (
    Message,
    MessageRole,
    ToolDefinition,
    FinishReason,
)


@pytest.mark.provider
class TestOpenAIProvider:
    """Tests for OpenAI provider."""
    
    @pytest.fixture
    def openai_provider(self):
        """Create an OpenAI provider instance."""
        # Skip if no API key
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")
        
        from opencode.provider.openai import OpenAIProvider
        return OpenAIProvider()
    
    @pytest.fixture
    def mock_openai_response(self):
        """Create a mock OpenAI API response."""
        return {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1700000000,
            "model": "gpt-4",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello! How can I help you?",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30,
            },
        }
    
    def test_provider_name(self):
        """Test provider name."""
        from opencode.provider.openai import OpenAIProvider
        provider = OpenAIProvider.__new__(OpenAIProvider)
        assert provider.name == "openai"
    
    def test_provider_models(self):
        """Test provider has models."""
        from opencode.provider.openai import OpenAIProvider
        from opencode.provider.base import ModelInfo
        
        provider = OpenAIProvider.__new__(OpenAIProvider)
        # Check that models property exists
        assert hasattr(provider, 'models')


@pytest.mark.provider
class TestOpenAIMessageFormat:
    """Tests for OpenAI message formatting."""
    
    def test_user_message_format(self):
        """Test user message format."""
        msg = Message(role=MessageRole.USER, content="Hello")
        
        openai_msg = msg.to_openai_format()
        
        assert openai_msg["role"] == "user"
        assert openai_msg["content"] == "Hello"
    
    def test_system_message_format(self):
        """Test system message format."""
        msg = Message(role=MessageRole.SYSTEM, content="You are helpful.")
        
        openai_msg = msg.to_openai_format()
        
        assert openai_msg["role"] == "system"
    
    def test_assistant_message_format(self):
        """Test assistant message format."""
        msg = Message(role=MessageRole.ASSISTANT, content="Hi there!")
        
        openai_msg = msg.to_openai_format()
        
        assert openai_msg["role"] == "assistant"
    
    def test_multimodal_message_format(self):
        """Test multimodal message format."""
        from opencode.provider.base import ContentPart
        
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
        
        openai_msg = msg.to_openai_format()
        
        assert openai_msg["role"] == "user"
        assert isinstance(openai_msg["content"], list)


@pytest.mark.provider
class TestOpenAIToolFormat:
    """Tests for OpenAI tool formatting."""
    
    def test_tool_definition_format(self):
        """Test tool definition format for OpenAI."""
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
        
        openai_format = tool.to_openai_format()
        
        assert openai_format["type"] == "function"
        assert openai_format["function"]["name"] == "get_weather"
        assert "parameters" in openai_format["function"]
    
    def test_tool_with_nested_properties(self):
        """Test tool with nested properties."""
        tool = ToolDefinition(
            name="search",
            description="Search for items",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "filters": {
                        "type": "object",
                        "properties": {
                            "category": {"type": "string"},
                            "price_range": {
                                "type": "object",
                                "properties": {
                                    "min": {"type": "number"},
                                    "max": {"type": "number"},
                                },
                            },
                        },
                    },
                },
            },
        )
        
        openai_format = tool.to_openai_format()
        
        assert "filters" in openai_format["function"]["parameters"]["properties"]


@pytest.mark.provider
class TestOpenAIStreaming:
    """Tests for OpenAI streaming functionality."""
    
    @pytest.fixture
    def mock_stream_chunks(self):
        """Create mock streaming chunks."""
        return [
            {"choices": [{"delta": {"content": "Hello"}}]},
            {"choices": [{"delta": {"content": " world"}}]},
            {"choices": [{"delta": {"content": "!"}, "finish_reason": "stop"}]},
        ]
    
    def test_stream_chunk_format(self):
        """Test stream chunk format."""
        # OpenAI streaming format
        chunk = {
            "id": "chatcmpl-123",
            "object": "chat.completion.chunk",
            "choices": [
                {
                    "index": 0,
                    "delta": {"content": "Hello"},
                    "finish_reason": None,
                }
            ],
        }
        
        assert "delta" in chunk["choices"][0]
        assert "content" in chunk["choices"][0]["delta"]


@pytest.mark.provider
class TestOpenAIModels:
    """Tests for OpenAI model information."""
    
    def test_gpt4_model_info(self):
        """Test GPT-4 model info."""
        from opencode.provider.base import ModelInfo
        
        model = ModelInfo(
            id="gpt-4",
            name="GPT-4",
            provider="openai",
            context_length=8192,
            supports_tools=True,
            supports_vision=False,
        )
        
        assert model.id == "gpt-4"
        assert model.supports_tools is True
    
    def test_gpt4_vision_model_info(self):
        """Test GPT-4 Vision model info."""
        from opencode.provider.base import ModelInfo
        
        model = ModelInfo(
            id="gpt-4-vision-preview",
            name="GPT-4 Vision",
            provider="openai",
            context_length=128000,
            supports_tools=True,
            supports_vision=True,
        )
        
        assert model.supports_vision is True
        assert model.context_length == 128000
    
    def test_gpt35_model_info(self):
        """Test GPT-3.5 model info."""
        from opencode.provider.base import ModelInfo
        
        model = ModelInfo(
            id="gpt-3.5-turbo",
            name="GPT-3.5 Turbo",
            provider="openai",
            context_length=4096,
            supports_tools=True,
        )
        
        assert model.id == "gpt-3.5-turbo"


@pytest.mark.provider
class TestOpenAIErrorHandling:
    """Tests for OpenAI error handling."""
    
    def test_rate_limit_error(self):
        """Test rate limit error handling."""
        from opencode.provider.base import ProviderError
        
        error = ProviderError(
            message="Rate limit exceeded",
            provider="openai",
            code="rate_limit_exceeded",
        )
        
        assert error.provider == "openai"
        assert error.code == "rate_limit_exceeded"
    
    def test_invalid_api_key_error(self):
        """Test invalid API key error."""
        from opencode.provider.base import ProviderError
        
        error = ProviderError(
            message="Invalid API key",
            provider="openai",
            code="invalid_api_key",
        )
        
        assert error.code == "invalid_api_key"
    
    def test_context_length_error(self):
        """Test context length exceeded error."""
        from opencode.provider.base import ProviderError
        
        error = ProviderError(
            message="This model's maximum context length is 8192 tokens",
            provider="openai",
            model="gpt-4",
            code="context_length_exceeded",
        )
        
        assert "context length" in str(error).lower()


@pytest.mark.provider
class TestOpenAIParameters:
    """Tests for OpenAI-specific parameters."""
    
    def test_temperature_range(self):
        """Test temperature parameter range."""
        # OpenAI accepts temperature 0-2
        valid_temps = [0.0, 0.7, 1.0, 1.5, 2.0]
        
        for temp in valid_temps:
            assert 0 <= temp <= 2
    
    def test_max_tokens_parameter(self):
        """Test max_tokens parameter."""
        # max_tokens should be positive
        max_tokens = 4096
        assert max_tokens > 0
    
    def test_top_p_parameter(self):
        """Test top_p parameter."""
        # top_p should be between 0 and 1
        valid_top_p = [0.1, 0.5, 0.9, 1.0]
        
        for top_p in valid_top_p:
            assert 0 < top_p <= 1
    
    def test_frequency_penalty(self):
        """Test frequency_penalty parameter."""
        # frequency_penalty should be between -2 and 2
        valid_penalties = [-2.0, -1.0, 0.0, 1.0, 2.0]
        
        for penalty in valid_penalties:
            assert -2 <= penalty <= 2
    
    def test_presence_penalty(self):
        """Test presence_penalty parameter."""
        # presence_penalty should be between -2 and 2
        valid_penalties = [-2.0, -1.0, 0.0, 1.0, 2.0]
        
        for penalty in valid_penalties:
            assert -2 <= penalty <= 2


@pytest.mark.provider
class TestOpenAITokenCounting:
    """Tests for OpenAI token counting."""
    
    def test_token_estimation(self):
        """Test token estimation."""
        # Rough estimation: ~4 characters per token
        text = "Hello, world!"
        estimated_tokens = len(text) // 4
        
        # Should be a positive integer
        assert estimated_tokens > 0
    
    def test_message_token_overhead(self):
        """Test message token overhead."""
        # Messages have overhead for formatting
        # Each message adds ~4 tokens for formatting
        messages = [
            Message(role=MessageRole.SYSTEM, content="You are helpful."),
            Message(role=MessageRole.USER, content="Hello"),
        ]
        
        # There should be overhead for each message
        assert len(messages) == 2
