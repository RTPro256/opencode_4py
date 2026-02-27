"""
Tests for base provider functionality.

Tests the Provider abstract base class and common provider operations.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from opencode.provider.base import (
    Provider,
    Message,
    MessageRole,
    ToolDefinition,
    ToolCall,
    ContentPart,
    CompletionResponse,
    StreamChunk,
    FinishReason,
    Usage,
    ModelInfo,
    ProviderError,
)


class TestMessageRole:
    """Tests for MessageRole enum."""
    
    def test_role_values(self):
        """Test role enum values."""
        assert MessageRole.SYSTEM.value == "system"
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
        assert MessageRole.TOOL.value == "tool"


class TestFinishReason:
    """Tests for FinishReason enum."""
    
    def test_reason_values(self):
        """Test finish reason values."""
        assert FinishReason.STOP.value == "stop"
        assert FinishReason.LENGTH.value == "length"
        assert FinishReason.TOOL_CALL.value == "tool_call"
        assert FinishReason.CONTENT_FILTER.value == "content_filter"
        assert FinishReason.ERROR.value == "error"


class TestToolDefinition:
    """Tests for ToolDefinition."""
    
    def test_tool_definition_creation(self):
        """Test creating a tool definition."""
        tool = ToolDefinition(
            name="read_file",
            description="Read a file from disk",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                },
                "required": ["path"],
            },
        )
        
        assert tool.name == "read_file"
        assert "file" in tool.description.lower()
    
    def test_to_openai_format(self):
        """Test converting to OpenAI format."""
        tool = ToolDefinition(
            name="test_tool",
            description="A test tool",
            parameters={"type": "object"},
        )
        
        openai_format = tool.to_openai_format()
        
        assert openai_format["type"] == "function"
        assert openai_format["function"]["name"] == "test_tool"
    
    def test_to_anthropic_format(self):
        """Test converting to Anthropic format."""
        tool = ToolDefinition(
            name="test_tool",
            description="A test tool",
            parameters={"type": "object"},
        )
        
        anthropic_format = tool.to_anthropic_format()
        
        assert anthropic_format["name"] == "test_tool"
        assert "input_schema" in anthropic_format


class TestToolCall:
    """Tests for ToolCall."""
    
    def test_tool_call_creation(self):
        """Test creating a tool call."""
        call = ToolCall(
            id="call-123",
            name="read_file",
            arguments={"path": "/test/file.py"},
        )
        
        assert call.id == "call-123"
        assert call.name == "read_file"
        assert call.arguments["path"] == "/test/file.py"
    
    def test_from_openai(self):
        """Test creating from OpenAI format."""
        data = {
            "id": "call-456",
            "function": {
                "name": "write_file",
                "arguments": '{"path": "/test.txt", "content": "hello"}',
            },
        }
        
        call = ToolCall.from_openai(data)
        
        assert call.id == "call-456"
        assert call.name == "write_file"
        assert call.arguments["path"] == "/test.txt"
    
    def test_from_anthropic(self):
        """Test creating from Anthropic format."""
        data = {
            "id": "call-789",
            "name": "execute",
            "input": {"command": "ls"},
        }
        
        call = ToolCall.from_anthropic(data)
        
        assert call.id == "call-789"
        assert call.name == "execute"
        assert call.arguments["command"] == "ls"


class TestContentPart:
    """Tests for ContentPart."""
    
    def test_text_content(self):
        """Test text content part."""
        part = ContentPart(type="text", text="Hello, world!")
        
        assert part.type == "text"
        assert part.text == "Hello, world!"
    
    def test_image_url_content(self):
        """Test image URL content part."""
        part = ContentPart(
            type="image",
            image_url="https://example.com/image.png",
        )
        
        assert part.type == "image"
        assert part.image_url == "https://example.com/image.png"
    
    def test_tool_call_content(self):
        """Test tool call content part."""
        tool_call = ToolCall(id="1", name="test", arguments={})
        part = ContentPart(type="tool_call", tool_call=tool_call)
        
        assert part.type == "tool_call"
        assert part.tool_call is not None


class TestMessage:
    """Tests for Message."""
    
    def test_user_message(self):
        """Test creating a user message."""
        msg = Message(role=MessageRole.USER, content="Hello!")
        
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello!"
    
    def test_system_message(self):
        """Test creating a system message."""
        msg = Message(role=MessageRole.SYSTEM, content="You are helpful.")
        
        assert msg.role == MessageRole.SYSTEM
        assert msg.content == "You are helpful."
    
    def test_get_text(self):
        """Test getting text from message."""
        msg = Message(
            role=MessageRole.USER,
            content="Test message",
        )
        
        assert msg.get_text() == "Test message"
    
    def test_get_text_from_parts(self):
        """Test getting text from content parts."""
        msg = Message(
            role=MessageRole.ASSISTANT,
            content=[
                ContentPart(type="text", text="Part 1"),
                ContentPart(type="text", text="Part 2"),
            ],
        )
        
        text = msg.get_text()
        assert "Part 1" in text
        assert "Part 2" in text
    
    def test_to_openai_format(self):
        """Test converting to OpenAI format."""
        msg = Message(role=MessageRole.USER, content="Hello")
        
        openai_msg = msg.to_openai_format()
        
        assert openai_msg["role"] == "user"
        assert openai_msg["content"] == "Hello"
    
    def test_to_anthropic_format(self):
        """Test converting to Anthropic format."""
        msg = Message(role=MessageRole.USER, content="Hello")
        
        anthropic_msg = msg.to_anthropic_format()
        
        assert anthropic_msg["role"] == "user"
        assert anthropic_msg["content"] == "Hello"


class TestUsage:
    """Tests for Usage."""
    
    def test_usage_creation(self):
        """Test creating usage stats."""
        usage = Usage(
            input_tokens=100,
            output_tokens=50,
        )
        
        assert usage.input_tokens == 100
        assert usage.output_tokens == 50
    
    def test_total_tokens(self):
        """Test total tokens calculation."""
        usage = Usage(input_tokens=100, output_tokens=50)
        
        assert usage.total_tokens == 150
    
    def test_cache_tokens(self):
        """Test cache token tracking."""
        usage = Usage(
            input_tokens=100,
            output_tokens=50,
            cache_read_tokens=20,
            cache_write_tokens=10,
        )
        
        assert usage.cache_read_tokens == 20
        assert usage.cache_write_tokens == 10


class TestStreamChunk:
    """Tests for StreamChunk."""
    
    def test_text_chunk(self):
        """Test creating a text chunk."""
        chunk = StreamChunk.text("Hello")
        
        assert chunk.delta == "Hello"
        assert len(chunk.tool_calls) == 0
    
    def test_tool_call_chunk(self):
        """Test creating a tool call chunk."""
        tool_call = ToolCall(id="1", name="test", arguments={})
        chunk = StreamChunk.tool_call(tool_call)
        
        assert len(chunk.tool_calls) == 1
    
    def test_done_chunk(self):
        """Test creating a done chunk."""
        usage = Usage(input_tokens=10, output_tokens=5)
        chunk = StreamChunk.done(FinishReason.STOP, usage)
        
        assert chunk.finish_reason == FinishReason.STOP
        assert chunk.usage is not None


class TestCompletionResponse:
    """Tests for CompletionResponse."""
    
    def test_response_creation(self):
        """Test creating a completion response."""
        response = CompletionResponse(
            content="Hello, I'm here to help!",
            model="gpt-4",
        )
        
        assert response.content == "Hello, I'm here to help!"
        assert response.model == "gpt-4"
    
    def test_response_with_tool_calls(self):
        """Test response with tool calls."""
        tool_call = ToolCall(id="1", name="test", arguments={})
        response = CompletionResponse(
            content="",
            tool_calls=[tool_call],
            finish_reason=FinishReason.TOOL_CALL,
        )
        
        assert len(response.tool_calls) == 1
        assert response.finish_reason == FinishReason.TOOL_CALL
    
    def test_response_with_usage(self):
        """Test response with usage stats."""
        usage = Usage(input_tokens=100, output_tokens=50)
        response = CompletionResponse(
            content="Response",
            usage=usage,
        )
        
        assert response.usage is not None
        assert response.usage.total_tokens == 150


class TestModelInfo:
    """Tests for ModelInfo."""
    
    def test_model_info_creation(self):
        """Test creating model info."""
        info = ModelInfo(
            id="gpt-4",
            name="GPT-4",
            provider="openai",
            context_length=8192,
        )
        
        assert info.id == "gpt-4"
        assert info.context_length == 8192
    
    def test_model_capabilities(self):
        """Test model capability flags."""
        info = ModelInfo(
            id="gpt-4-vision",
            name="GPT-4 Vision",
            provider="openai",
            context_length=128000,
            supports_tools=True,
            supports_vision=True,
        )
        
        assert info.supports_tools is True
        assert info.supports_vision is True


class TestProviderError:
    """Tests for ProviderError."""
    
    def test_error_creation(self):
        """Test creating a provider error."""
        error = ProviderError(
            message="API rate limit exceeded",
            provider="openai",
            model="gpt-4",
        )
        
        assert "rate limit" in str(error)
        assert error.provider == "openai"
        assert error.model == "gpt-4"
    
    def test_error_with_code(self):
        """Test error with error code."""
        error = ProviderError(
            message="Invalid API key",
            code="invalid_api_key",
        )
        
        assert error.code == "invalid_api_key"


class TestMessageConversion:
    """Tests for message format conversion."""
    
    def test_user_message_to_openai(self):
        """Test user message to OpenAI format."""
        msg = Message(role=MessageRole.USER, content="Hello")
        
        result = msg.to_openai_format()
        
        assert result["role"] == "user"
        assert result["content"] == "Hello"
    
    def test_assistant_message_to_openai(self):
        """Test assistant message to OpenAI format."""
        msg = Message(role=MessageRole.ASSISTANT, content="Hi there!")
        
        result = msg.to_openai_format()
        
        assert result["role"] == "assistant"
    
    def test_message_with_image_to_anthropic(self):
        """Test message with image to Anthropic format."""
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
        
        result = msg.to_anthropic_format()
        
        assert result["role"] == "user"
        assert isinstance(result["content"], list)


class TestToolDefinitionFormats:
    """Tests for tool definition format conversions."""
    
    def test_complex_tool_to_openai(self):
        """Test complex tool to OpenAI format."""
        tool = ToolDefinition(
            name="search_files",
            description="Search for files matching a pattern",
            parameters={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Search pattern",
                    },
                    "recursive": {
                        "type": "boolean",
                        "default": False,
                    },
                },
                "required": ["pattern"],
            },
            required=["pattern"],
        )
        
        result = tool.to_openai_format()
        
        assert result["function"]["name"] == "search_files"
        assert "pattern" in result["function"]["parameters"]["properties"]
    
    def test_complex_tool_to_anthropic(self):
        """Test complex tool to Anthropic format."""
        tool = ToolDefinition(
            name="execute_command",
            description="Execute a shell command",
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string"},
                    "timeout": {"type": "number"},
                },
            },
        )
        
        result = tool.to_anthropic_format()
        
        assert result["name"] == "execute_command"
        assert "input_schema" in result
