"""
Unit tests for Anthropic provider implementation.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json

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
)


class TestAnthropicProvider:
    """Tests for AnthropicProvider class."""

    @pytest.fixture
    def provider(self):
        """Create an AnthropicProvider instance."""
        return AnthropicProvider(api_key="test-api-key")

    def test_provider_initialization(self, provider):
        """Test provider initializes correctly."""
        assert provider.api_key == "test-api-key"

    def test_models_property(self, provider):
        """Test getting available models via models property."""
        models = provider.models
        
        assert isinstance(models, list)
        assert len(models) > 0
        assert all(isinstance(m, ModelInfo) for m in models)
        assert any("claude" in m.id.lower() for m in models)

    def test_name_property(self, provider):
        """Test provider name property."""
        assert provider.name == "anthropic"


class TestAnthropicProviderModels:
    """Tests for model information."""

    @pytest.fixture
    def provider(self):
        """Create an AnthropicProvider instance."""
        return AnthropicProvider(api_key="test-api-key")

    def test_models_have_required_fields(self, provider):
        """Test that all models have required fields."""
        models = provider.models
        
        for model in models:
            assert model.id is not None
            assert model.name is not None
            assert model.provider == "anthropic"
            assert model.context_length > 0

    def test_models_support_tools(self, provider):
        """Test that Claude models support tools."""
        models = provider.models
        
        for model in models:
            assert model.supports_tools is True

    def test_models_support_vision(self, provider):
        """Test that Claude models support vision."""
        models = provider.models
        
        for model in models:
            assert model.supports_vision is True

    def test_models_support_streaming(self, provider):
        """Test that Claude models support streaming."""
        models = provider.models
        
        for model in models:
            assert model.supports_streaming is True


class TestToolDefinition:
    """Tests for ToolDefinition class."""

    def test_to_anthropic_format(self):
        """Test converting tool definition to Anthropic format."""
        tool = ToolDefinition(
            name="get_weather",
            description="Get weather info",
            parameters={
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                }
            }
        )
        
        result = tool.to_anthropic_format()
        
        assert result["name"] == "get_weather"
        assert result["description"] == "Get weather info"
        assert "input_schema" in result

    def test_to_openai_format(self):
        """Test converting tool definition to OpenAI format."""
        tool = ToolDefinition(
            name="get_weather",
            description="Get weather info",
            parameters={
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                }
            },
            required=["location"]
        )
        
        result = tool.to_openai_format()
        
        assert result["type"] == "function"
        assert result["function"]["name"] == "get_weather"
        assert result["function"]["required"] == ["location"]


class TestToolCall:
    """Tests for ToolCall class."""

    def test_from_anthropic(self):
        """Test creating ToolCall from Anthropic format."""
        data = {
            "id": "tool_123",
            "name": "get_weather",
            "input": {"location": "NYC"}
        }
        
        result = ToolCall.from_anthropic(data)
        
        assert result.id == "tool_123"
        assert result.name == "get_weather"
        assert result.arguments == {"location": "NYC"}

    def test_from_openai(self):
        """Test creating ToolCall from OpenAI format."""
        data = {
            "id": "call_123",
            "function": {
                "name": "get_weather",
                "arguments": '{"location": "NYC"}'
            }
        }
        
        result = ToolCall.from_openai(data)
        
        assert result.id == "call_123"
        assert result.name == "get_weather"
        assert result.arguments == {"location": "NYC"}

    def test_from_openai_with_dict_args(self):
        """Test creating ToolCall from OpenAI format with dict args."""
        data = {
            "id": "call_123",
            "function": {
                "name": "get_weather",
                "arguments": {"location": "NYC"}
            }
        }
        
        result = ToolCall.from_openai(data)
        
        assert result.arguments == {"location": "NYC"}


class TestMessage:
    """Tests for Message class."""

    def test_get_text_string_content(self):
        """Test getting text from string content."""
        message = Message(role=MessageRole.USER, content="Hello")
        
        result = message.get_text()
        
        assert result == "Hello"

    def test_get_text_list_content(self):
        """Test getting text from list content."""
        message = Message(
            role=MessageRole.USER,
            content=[
                ContentPart(type="text", text="Hello"),
                ContentPart(type="text", text="World")
            ]
        )
        
        result = message.get_text()
        
        assert "Hello" in result
        assert "World" in result

    def test_to_anthropic_format_string(self):
        """Test converting message to Anthropic format with string content."""
        message = Message(role=MessageRole.USER, content="Hello")
        
        result = message.to_anthropic_format()
        
        assert result["role"] == "user"
        assert result["content"] == "Hello"

    def test_to_openai_format_string(self):
        """Test converting message to OpenAI format with string content."""
        message = Message(role=MessageRole.USER, content="Hello")
        
        result = message.to_openai_format()
        
        assert result["role"] == "user"
        assert result["content"] == "Hello"

    def test_to_anthropic_format_with_tool_call(self):
        """Test converting message with tool call to Anthropic format."""
        message = Message(
            role=MessageRole.ASSISTANT,
            content=[
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
        assert any(c["type"] == "tool_use" for c in result["content"])


class TestUsage:
    """Tests for Usage class."""

    def test_total_tokens(self):
        """Test total tokens calculation."""
        usage = Usage(input_tokens=100, output_tokens=50)
        
        assert usage.total_tokens == 150

    def test_default_values(self):
        """Test default values."""
        usage = Usage()
        
        assert usage.input_tokens == 0
        assert usage.output_tokens == 0
        assert usage.cache_read_tokens == 0
        assert usage.cache_write_tokens == 0


class TestStreamChunk:
    """Tests for StreamChunk class."""

    def test_text_factory(self):
        """Test creating text chunk."""
        chunk = StreamChunk.text("Hello")
        
        assert chunk.delta == "Hello"
        assert chunk.tool_calls == []
        assert chunk.finish_reason is None

    def test_tool_call_factory(self):
        """Test creating tool call chunk."""
        tool_call = ToolCall(id="tool_123", name="get_weather", arguments={})
        chunk = StreamChunk.tool_call(tool_call)
        
        assert chunk.delta == ""
        assert len(chunk.tool_calls) == 1
        assert chunk.tool_calls[0].name == "get_weather"

    def test_done_factory(self):
        """Test creating completion chunk."""
        usage = Usage(input_tokens=10, output_tokens=5)
        chunk = StreamChunk.done(FinishReason.STOP, usage)
        
        assert chunk.delta == ""
        assert chunk.finish_reason == FinishReason.STOP
        assert chunk.usage == usage


class TestContentPart:
    """Tests for ContentPart class."""

    def test_text_part(self):
        """Test creating text content part."""
        part = ContentPart(type="text", text="Hello")
        
        assert part.type == "text"
        assert part.text == "Hello"

    def test_image_url_part(self):
        """Test creating image URL content part."""
        part = ContentPart(type="image", image_url="https://example.com/image.png")
        
        assert part.type == "image"
        assert part.image_url == "https://example.com/image.png"

    def test_tool_result_part(self):
        """Test creating tool result content part."""
        part = ContentPart(
            type="tool_result",
            tool_call_id="tool_123",
            text="Result text"
        )
        
        assert part.type == "tool_result"
        assert part.tool_call_id == "tool_123"
        assert part.text == "Result text"
