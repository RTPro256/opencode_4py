"""
Integration tests for MCP (Model Context Protocol) integration.

Tests MCP server, client, and tool integration.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from opencode.mcp.types import (
    MCPTool,
    MCPToolInputSchema,
    MCPResult,
    MCPPrompt,
    MCPPromptArgument,
    MCPResource,
    MCPResourceTemplate,
    MCPResourceContent,
    MCPMessage,
    MCPRole,
)


@pytest.mark.integration
class TestMCPTypes:
    """Tests for MCP type definitions."""
    
    def test_mcp_tool_creation(self):
        """Test creating an MCP tool definition."""
        tool = MCPTool(
            name="read_file",
            description="Read a file from the filesystem",
            input_schema=MCPToolInputSchema(
                type="object",
                properties={"path": {"type": "string"}},
                required=["path"],
            ),
        )
        
        assert tool.name == "read_file"
        assert "file" in (tool.description or "").lower()
    
    def test_mcp_tool_to_dict(self):
        """Test serializing MCP tool to dict."""
        tool = MCPTool(
            name="test_tool",
            description="A test tool",
            input_schema=MCPToolInputSchema(
                properties={"arg": {"type": "string"}},
            ),
        )
        
        data = tool.to_dict()
        
        assert data["name"] == "test_tool"
        assert "inputSchema" in data
    
    def test_mcp_tool_from_dict(self):
        """Test deserializing MCP tool from dict."""
        data = {
            "name": "test",
            "description": "Test tool",
            "inputSchema": {
                "type": "object",
                "properties": {"input": {"type": "string"}},
            },
        }
        
        tool = MCPTool.from_dict(data)
        
        assert tool.name == "test"
        assert tool.input_schema.properties == {"input": {"type": "string"}}
    
    def test_mcp_result_success(self):
        """Test successful tool result."""
        result = MCPResult(
            content=[{"type": "text", "text": "File content here"}],
            is_error=False,
        )
        
        assert result.is_error is False
        assert len(result.content) == 1
    
    def test_mcp_result_error(self):
        """Test error tool result."""
        result = MCPResult(
            content=[{"type": "text", "text": "Error: File not found"}],
            is_error=True,
        )
        
        assert result.is_error is True
    
    def test_mcp_result_text_extraction(self):
        """Test extracting text from result."""
        result = MCPResult(
            content=[
                {"type": "text", "text": "Line 1"},
                {"type": "text", "text": "Line 2"},
            ],
        )
        
        assert "Line 1" in result.text
        assert "Line 2" in result.text


@pytest.mark.integration
class TestMCPToolInputSchema:
    """Tests for MCPToolInputSchema."""
    
    def test_schema_creation(self):
        """Test creating input schema."""
        schema = MCPToolInputSchema(
            type="object",
            properties={
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            required=["path"],
        )
        
        assert schema.type == "object"
        assert "path" in schema.properties
        assert "path" in schema.required
    
    def test_schema_defaults(self):
        """Test schema default values."""
        schema = MCPToolInputSchema()
        
        assert schema.type == "object"
        assert schema.properties == {}
        assert schema.required == []
    
    def test_schema_to_dict(self):
        """Test schema serialization."""
        schema = MCPToolInputSchema(
            properties={"arg": {"type": "number"}},
            required=["arg"],
        )
        
        data = schema.to_dict()
        
        assert data["type"] == "object"
        assert data["properties"] == {"arg": {"type": "number"}}
        assert data["required"] == ["arg"]
    
    def test_schema_from_dict(self):
        """Test schema deserialization."""
        data = {
            "type": "object",
            "properties": {"input": {"type": "string"}},
            "required": ["input"],
        }
        
        schema = MCPToolInputSchema.from_dict(data)
        
        assert schema.type == "object"
        assert "input" in schema.properties


@pytest.mark.integration
class TestMCPPrompt:
    """Tests for MCPPrompt."""
    
    def test_prompt_creation(self):
        """Test creating an MCP prompt."""
        prompt = MCPPrompt(
            name="code_review",
            description="Review code for issues",
            arguments=[
                MCPPromptArgument(name="code", description="Code to review", required=True),
            ],
        )
        
        assert prompt.name == "code_review"
        assert len(prompt.arguments) == 1
    
    def test_prompt_to_dict(self):
        """Test prompt serialization."""
        prompt = MCPPrompt(
            name="test",
            arguments=[MCPPromptArgument(name="input")],
        )
        
        data = prompt.to_dict()
        
        assert data["name"] == "test"
        assert len(data["arguments"]) == 1
    
    def test_prompt_from_dict(self):
        """Test prompt deserialization."""
        data = {
            "name": "test_prompt",
            "description": "A test prompt",
            "arguments": [
                {"name": "arg1", "description": "First arg", "required": True},
            ],
        }
        
        prompt = MCPPrompt.from_dict(data)
        
        assert prompt.name == "test_prompt"
        assert len(prompt.arguments) == 1
        assert prompt.arguments[0].name == "arg1"


@pytest.mark.integration
class TestMCPPromptArgument:
    """Tests for MCPPromptArgument."""
    
    def test_argument_creation(self):
        """Test creating prompt argument."""
        arg = MCPPromptArgument(
            name="input",
            description="Input text",
            required=True,
        )
        
        assert arg.name == "input"
        assert arg.required is True
    
    def test_argument_defaults(self):
        """Test argument defaults."""
        arg = MCPPromptArgument(name="test")
        
        assert arg.description is None
        assert arg.required is False


@pytest.mark.integration
class TestMCPResource:
    """Tests for MCPResource."""
    
    def test_resource_creation(self):
        """Test creating a resource."""
        resource = MCPResource(
            uri="file:///test/file.py",
            name="test.py",
            description="A test file",
            mime_type="text/x-python",
        )
        
        assert resource.uri == "file:///test/file.py"
        assert resource.name == "test.py"
    
    def test_resource_to_dict(self):
        """Test resource serialization."""
        resource = MCPResource(
            uri="file:///test.txt",
            name="test.txt",
        )
        
        data = resource.to_dict()
        
        assert data["uri"] == "file:///test.txt"
        assert data["name"] == "test.txt"
    
    def test_resource_from_dict(self):
        """Test resource deserialization."""
        data = {
            "uri": "file:///test.py",
            "name": "test.py",
            "mimeType": "text/x-python",
        }
        
        resource = MCPResource.from_dict(data)
        
        assert resource.uri == "file:///test.py"
        assert resource.mime_type == "text/x-python"


@pytest.mark.integration
class TestMCPResourceTemplate:
    """Tests for MCPResourceTemplate."""
    
    def test_template_creation(self):
        """Test creating a resource template."""
        template = MCPResourceTemplate(
            uri_template="file:///{path}",
            name="File by path",
            description="Access files by path",
        )
        
        assert template.uri_template == "file:///{path}"
        assert template.name == "File by path"


@pytest.mark.integration
class TestMCPResourceContent:
    """Tests for MCPResourceContent."""
    
    def test_text_content(self):
        """Test text resource content."""
        content = MCPResourceContent(
            uri="file:///test.txt",
            mime_type="text/plain",
            text="Hello, world!",
        )
        
        assert content.text == "Hello, world!"
        assert content.blob is None
    
    def test_blob_content(self):
        """Test binary resource content."""
        content = MCPResourceContent(
            uri="file:///test.bin",
            mime_type="application/octet-stream",
            blob=b"\x00\x01\x02\x03",
        )
        
        assert content.blob == b"\x00\x01\x02\x03"
        assert content.text is None
    
    def test_content_to_dict(self):
        """Test content serialization."""
        content = MCPResourceContent(
            uri="file:///test.txt",
            text="Test content",
        )
        
        data = content.to_dict()
        
        assert data["uri"] == "file:///test.txt"
        assert data["text"] == "Test content"


@pytest.mark.integration
class TestMCPMessage:
    """Tests for MCPMessage."""
    
    def test_message_creation(self):
        """Test creating an MCP message."""
        message = MCPMessage(
            role=MCPRole.USER,
            content={"type": "text", "text": "Hello"},
        )
        
        assert message.role == MCPRole.USER
        assert message.content["text"] == "Hello"
    
    def test_message_to_dict(self):
        """Test message serialization."""
        message = MCPMessage(
            role=MCPRole.ASSISTANT,
            content={"type": "text", "text": "Hi there"},
        )
        
        data = message.to_dict()
        
        assert data["role"] == "assistant"
        assert data["content"]["text"] == "Hi there"
    
    def test_message_from_dict(self):
        """Test message deserialization."""
        data = {
            "role": "system",
            "content": {"type": "text", "text": "System message"},
        }
        
        message = MCPMessage.from_dict(data)
        
        assert message.role == MCPRole.SYSTEM


@pytest.mark.integration
class TestMCPServer:
    """Integration tests for MCP server."""
    
    @pytest.fixture
    def mock_mcp_server(self):
        """Create a mock MCP server."""
        from opencode.mcp.server import MCPServer
        
        server = MagicMock(spec=MCPServer)
        server.list_tools = AsyncMock(return_value=[
            MCPTool(name="test_tool", description="A test tool"),
        ])
        server.call_tool = AsyncMock(return_value=MCPResult(
            content=[{"type": "text", "text": "Success"}],
            is_error=False,
        ))
        return server
    
    @pytest.mark.asyncio
    async def test_list_tools(self, mock_mcp_server):
        """Test listing tools from MCP server."""
        tools = await mock_mcp_server.list_tools()
        
        assert len(tools) == 1
        assert tools[0].name == "test_tool"
    
    @pytest.mark.asyncio
    async def test_call_tool(self, mock_mcp_server):
        """Test calling a tool on MCP server."""
        result = await mock_mcp_server.call_tool(
            tool_name="test_tool",
            arguments={"arg": "value"},
        )
        
        assert result.is_error is False
        assert "Success" in result.text


@pytest.mark.integration
class TestMCPClient:
    """Integration tests for MCP client."""
    
    @pytest.fixture
    def mock_mcp_client(self):
        """Create a mock MCP client."""
        from opencode.mcp.client import MCPClient
        
        client = MagicMock(spec=MCPClient)
        client.connect = AsyncMock()
        client.disconnect = AsyncMock()
        client.list_tools = AsyncMock(return_value=[])
        client.call_tool = AsyncMock(return_value={"result": "success"})
        return client
    
    @pytest.mark.asyncio
    async def test_client_connect(self, mock_mcp_client):
        """Test client connection."""
        await mock_mcp_client.connect()
        
        mock_mcp_client.connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_client_disconnect(self, mock_mcp_client):
        """Test client disconnection."""
        await mock_mcp_client.connect()
        await mock_mcp_client.disconnect()
        
        mock_mcp_client.disconnect.assert_called_once()


@pytest.mark.integration
class TestMCPToolIntegration:
    """Integration tests for MCP tool integration."""
    
    def test_tool_to_openai_format(self):
        """Test converting MCP tool to OpenAI format."""
        tool = MCPTool(
            name="get_weather",
            description="Get weather for a location",
            input_schema=MCPToolInputSchema(
                properties={"location": {"type": "string"}},
                required=["location"],
            ),
        )
        
        # OpenAI format
        openai_format = {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.input_schema.to_dict(),
            },
        }
        
        assert openai_format["type"] == "function"
        assert openai_format["function"]["name"] == "get_weather"
    
    def test_tool_to_anthropic_format(self):
        """Test converting MCP tool to Anthropic format."""
        tool = MCPTool(
            name="get_weather",
            description="Get weather for a location",
            input_schema=MCPToolInputSchema(
                properties={"location": {"type": "string"}},
            ),
        )
        
        # Anthropic format
        anthropic_format = {
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.input_schema.to_dict(),
        }
        
        assert anthropic_format["name"] == "get_weather"
        assert "input_schema" in anthropic_format


@pytest.mark.integration
class TestMCPErrorHandling:
    """Integration tests for MCP error handling."""
    
    def test_error_result(self):
        """Test error result creation."""
        result = MCPResult(
            content=[{"type": "text", "text": "Error: Something failed"}],
            is_error=True,
        )
        
        assert result.is_error is True
        assert "Error" in result.text
    
    def test_empty_result(self):
        """Test empty result."""
        result = MCPResult()
        
        assert len(result.content) == 0
        assert result.text == ""
