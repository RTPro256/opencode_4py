"""
Tests for provider base data models.
"""

import pytest
import json
from typing import Any, AsyncIterator, Optional, Union

from opencode.provider.base import (
    MessageRole,
    FinishReason,
    ToolDefinition,
    ToolCall,
    ContentPart,
    Message,
    Usage,
)


class TestMessageRole:
    """Tests for MessageRole enum."""

    def test_message_roles_exist(self):
        """Test that all message roles exist."""
        assert MessageRole.SYSTEM.value == "system"
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
        assert MessageRole.TOOL.value == "tool"

    def test_message_role_is_string(self):
        """Test that MessageRole is a string enum."""
        assert MessageRole.SYSTEM == "system"
        assert isinstance(MessageRole.USER, str)


class TestFinishReason:
    """Tests for FinishReason enum."""

    def test_finish_reasons_exist(self):
        """Test that all finish reasons exist."""
        assert FinishReason.STOP.value == "stop"
        assert FinishReason.LENGTH.value == "length"
        assert FinishReason.TOOL_CALL.value == "tool_call"
        assert FinishReason.CONTENT_FILTER.value == "content_filter"
        assert FinishReason.ERROR.value == "error"


class TestToolDefinition:
    """Tests for ToolDefinition."""

    def test_create_tool_definition(self):
        """Test creating a tool definition."""
        tool = ToolDefinition(
            name="test_tool",
            description="A test tool",
            parameters={"type": "object", "properties": {"input": {"type": "string"}}},
            required=["input"],
        )
        
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert "input" in tool.parameters["properties"]
        assert tool.required == ["input"]

    def test_tool_definition_default_required(self):
        """Test tool definition with default required list."""
        tool = ToolDefinition(
            name="test_tool",
            description="A test tool",
            parameters={"type": "object"},
        )
        
        assert tool.required == []

    def test_to_anthropic_format(self):
        """Test converting to Anthropic format."""
        tool = ToolDefinition(
            name="test_tool",
            description="A test tool",
            parameters={"type": "object", "properties": {}},
        )
        
        result = tool.to_anthropic_format()
        
        assert result["name"] == "test_tool"
        assert result["description"] == "A test tool"
        assert "input_schema" in result

    def test_to_openai_format(self):
        """Test converting to OpenAI format."""
        tool = ToolDefinition(
            name="test_tool",
            description="A test tool",
            parameters={"type": "object", "properties": {}},
            required=["input"],
        )
        
        result = tool.to_openai_format()
        
        assert result["type"] == "function"
        assert result["function"]["name"] == "test_tool"
        assert result["function"]["description"] == "A test tool"
        assert result["function"]["parameters"] == {"type": "object", "properties": {}}
        assert result["function"]["required"] == ["input"]


class TestToolCall:
    """Tests for ToolCall."""

    def test_create_tool_call(self):
        """Test creating a tool call."""
        call = ToolCall(
            id="call-123",
            name="test_tool",
            arguments={"input": "test"},
        )
        
        assert call.id == "call-123"
        assert call.name == "test_tool"
        assert call.arguments == {"input": "test"}

    def test_from_anthropic(self):
        """Test creating from Anthropic format."""
        data = {
            "id": "call-123",
            "name": "test_tool",
            "input": {"input": "test"},
        }
        
        call = ToolCall.from_anthropic(data)
        
        assert call.id == "call-123"
        assert call.name == "test_tool"
        assert call.arguments == {"input": "test"}

    def test_from_anthropic_no_input(self):
        """Test creating from Anthropic format without input."""
        data = {
            "id": "call-123",
            "name": "test_tool",
        }
        
        call = ToolCall.from_anthropic(data)
        
        assert call.arguments == {}

    def test_from_openai(self):
        """Test creating from OpenAI format."""
        data = {
            "id": "call-123",
            "function": {
                "name": "test_tool",
                "arguments": '{"input": "test"}',
            },
        }
        
        call = ToolCall.from_openai(data)
        
        assert call.id == "call-123"
        assert call.name == "test_tool"
        assert call.arguments == {"input": "test"}

    def test_from_openai_dict_arguments(self):
        """Test creating from OpenAI format with dict arguments."""
        data = {
            "id": "call-123",
            "function": {
                "name": "test_tool",
                "arguments": {"input": "test"},
            },
        }
        
        call = ToolCall.from_openai(data)
        
        assert call.arguments == {"input": "test"}


class TestContentPart:
    """Tests for ContentPart."""

    def test_text_content(self):
        """Test creating text content."""
        content = ContentPart(type="text", text="Hello")
        
        assert content.type == "text"
        assert content.text == "Hello"
        assert content.image_url is None

    def test_image_url_content(self):
        """Test creating image URL content."""
        content = ContentPart(type="image", image_url="https://example.com/image.png")
        
        assert content.type == "image"
        assert content.image_url == "https://example.com/image.png"

    def test_image_data_content(self):
        """Test creating image data content."""
        content = ContentPart(
            type="image",
            image_data=b"image bytes",
            image_media_type="image/png",
        )
        
        assert content.type == "image"
        assert content.image_data == b"image bytes"
        assert content.image_media_type == "image/png"

    def test_tool_call_content(self):
        """Test creating tool call content."""
        call = ToolCall(id="call-1", name="test", arguments={})
        content = ContentPart(type="tool_call", tool_call=call)
        
        assert content.type == "tool_call"
        assert content.tool_call == call

    def test_tool_result_content(self):
        """Test creating tool result content."""
        content = ContentPart(
            type="tool_result",
            tool_call_id="call-1",
            text="Tool result",
        )
        
        assert content.type == "tool_result"
        assert content.tool_call_id == "call-1"
        assert content.text == "Tool result"


class TestMessage:
    """Tests for Message."""

    def test_create_message(self):
        """Test creating a message."""
        msg = Message(role=MessageRole.USER, content="Hello")
        
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello"

    def test_message_with_string_content(self):
        """Test message with string content."""
        msg = Message(role=MessageRole.USER, content="Hello")
        
        assert msg.content == "Hello"

    def test_message_with_list_content(self):
        """Test message with list content."""
        parts = [ContentPart(type="text", text="Hello")]
        msg = Message(role=MessageRole.USER, content=parts)
        
        assert isinstance(msg.content, list)
        assert len(msg.content) == 1

    def test_get_text_from_string(self):
        """Test get_text from string content."""
        msg = Message(role=MessageRole.USER, content="Hello")
        
        assert msg.get_text() == "Hello"

    def test_get_text_from_list(self):
        """Test get_text from list content."""
        parts = [
            ContentPart(type="text", text="Hello"),
            ContentPart(type="text", text="World"),
        ]
        msg = Message(role=MessageRole.USER, content=parts)
        
        assert msg.get_text() == "Hello\nWorld"

    def test_to_anthropic_format_string(self):
        """Test converting string message to Anthropic format."""
        msg = Message(role=MessageRole.USER, content="Hello")
        
        result = msg.to_anthropic_format()
        
        assert result["role"] == "user"
        assert result["content"] == "Hello"

    def test_to_anthropic_format_list(self):
        """Test converting list message to Anthropic format."""
        parts = [ContentPart(type="text", text="Hello")]
        msg = Message(role=MessageRole.USER, content=parts)
        
        result = msg.to_anthropic_format()
        
        assert result["role"] == "user"
        assert isinstance(result["content"], list)
        assert result["content"][0]["type"] == "text"

    def test_to_anthropic_format_with_image_url(self):
        """Test converting message with image URL to Anthropic format."""
        parts = [ContentPart(type="image", image_url="https://example.com/img.png")]
        msg = Message(role=MessageRole.USER, content=parts)
        
        result = msg.to_anthropic_format()
        
        assert result["content"][0]["type"] == "image"
        assert result["content"][0]["source"]["type"] == "url"

    def test_to_anthropic_format_with_image_data(self):
        """Test converting message with image data to Anthropic format."""
        parts = [ContentPart(
            type="image",
            image_data=b"image bytes",
            image_media_type="image/png",
        )]
        msg = Message(role=MessageRole.USER, content=parts)
        
        result = msg.to_anthropic_format()
        
        assert result["content"][0]["type"] == "image"
        assert result["content"][0]["source"]["type"] == "base64"

    def test_to_anthropic_format_with_tool_call(self):
        """Test converting message with tool call to Anthropic format."""
        call = ToolCall(id="call-1", name="test_tool", arguments={"input": "test"})
        parts = [ContentPart(type="tool_call", tool_call=call)]
        msg = Message(role=MessageRole.ASSISTANT, content=parts)
        
        result = msg.to_anthropic_format()
        
        assert result["content"][0]["type"] == "tool_use"
        assert result["content"][0]["name"] == "test_tool"

    def test_to_anthropic_format_with_tool_result(self):
        """Test converting message with tool result to Anthropic format."""
        parts = [ContentPart(
            type="tool_result",
            tool_call_id="call-1",
            text="Result",
        )]
        msg = Message(role=MessageRole.TOOL, content=parts)
        
        result = msg.to_anthropic_format()
        
        assert result["content"][0]["type"] == "tool_result"

    def test_to_openai_format_string(self):
        """Test converting string message to OpenAI format."""
        msg = Message(role=MessageRole.USER, content="Hello")
        
        result = msg.to_openai_format()
        
        assert result["role"] == "user"
        assert result["content"] == "Hello"

    def test_to_openai_format_with_image_url(self):
        """Test converting message with image URL to OpenAI format."""
        parts = [ContentPart(type="image", image_url="https://example.com/img.png")]
        msg = Message(role=MessageRole.USER, content=parts)
        
        result = msg.to_openai_format()
        
        assert result["content"][0]["type"] == "image_url"
        assert result["content"][0]["image_url"]["url"] == "https://example.com/img.png"

    def test_to_openai_format_with_image_data(self):
        """Test converting message with image data to OpenAI format."""
        parts = [ContentPart(
            type="image",
            image_data=b"image bytes",
            image_media_type="image/png",
        )]
        msg = Message(role=MessageRole.USER, content=parts)
        
        result = msg.to_openai_format()
        
        assert result["content"][0]["type"] == "image_url"
        assert "data:image/png;base64," in result["content"][0]["image_url"]["url"]

    def test_to_openai_format_with_tool_call(self):
        """Test converting message with tool call to OpenAI format."""
        call = ToolCall(id="call-1", name="test_tool", arguments={"input": "test"})
        parts = [ContentPart(type="tool_call", tool_call=call)]
        msg = Message(role=MessageRole.ASSISTANT, content=parts)
        
        result = msg.to_openai_format()
        
        assert "tool_calls" in result
        assert result["tool_calls"][0]["function"]["name"] == "test_tool"


class TestUsage:
    """Tests for Usage."""

    def test_create_usage(self):
        """Test creating usage."""
        usage = Usage(input_tokens=100, output_tokens=50)
        
        assert usage.input_tokens == 100
        assert usage.output_tokens == 50

    def test_total_tokens(self):
        """Test total tokens calculation."""
        usage = Usage(input_tokens=100, output_tokens=50)
        
        assert usage.total_tokens == 150

    def test_usage_default_cache_tokens(self):
        """Test usage with default cache tokens."""
        usage = Usage(input_tokens=100, output_tokens=50)
        
        assert usage.cache_read_tokens == 0
        assert usage.cache_write_tokens == 0

    def test_usage_with_cache_tokens(self):
        """Test usage with cache tokens."""
        usage = Usage(
            input_tokens=100,
            output_tokens=50,
            cache_read_tokens=20,
            cache_write_tokens=10,
        )
        
        assert usage.cache_read_tokens == 20
        assert usage.cache_write_tokens == 10
