"""
Tests for MCP client data classes.
"""

import pytest
from pathlib import Path

from opencode.mcp.client import MCPServerConfig, MCPServer, MCPClient
from opencode.mcp.types import (
    MCPTool,
    MCPToolInputSchema,
    MCPResource,
    MCPPrompt,
    MCPPromptArgument,
    MCPPromptArgumentType,
    MCPResult,
)


class TestMCPServerConfig:
    """Tests for MCPServerConfig."""

    def test_create_config(self):
        """Test creating a server config."""
        config = MCPServerConfig(
            name="test-server",
            command="python",
            args=["-m", "server"],
            env={"API_KEY": "test"},
            cwd=Path("/tmp"),
            timeout=60,
        )
        
        assert config.name == "test-server"
        assert config.command == "python"
        assert config.args == ["-m", "server"]
        assert config.env == {"API_KEY": "test"}
        assert config.cwd == Path("/tmp")
        assert config.timeout == 60

    def test_create_config_defaults(self):
        """Test creating config with defaults."""
        config = MCPServerConfig(name="test", command="node")
        
        assert config.name == "test"
        assert config.command == "node"
        assert config.args == []
        assert config.env == {}
        assert config.cwd is None
        assert config.timeout == 30

    def test_from_dict(self):
        """Test creating config from dict."""
        data = {
            "command": "python",
            "args": ["-m", "server"],
            "env": {"KEY": "value"},
            "cwd": "/tmp",
            "timeout": 60,
        }
        
        config = MCPServerConfig.from_dict("test-server", data)
        
        assert config.name == "test-server"
        assert config.command == "python"
        assert config.args == ["-m", "server"]
        assert config.env == {"KEY": "value"}
        assert config.cwd == Path("/tmp")
        assert config.timeout == 60

    def test_from_dict_minimal(self):
        """Test creating config from minimal dict."""
        data = {}
        
        config = MCPServerConfig.from_dict("test", data)
        
        assert config.name == "test"
        assert config.command == ""
        assert config.args == []
        assert config.env == {}
        assert config.cwd is None
        assert config.timeout == 30

    def test_from_dict_with_path(self):
        """Test creating config with path cwd."""
        data = {"cwd": "/home/user/project"}
        
        config = MCPServerConfig.from_dict("test", data)
        
        assert config.cwd == Path("/home/user/project")


class TestMCPServer:
    """Tests for MCPServer."""

    @pytest.fixture
    def config(self):
        """Create a server config."""
        return MCPServerConfig(name="test", command="echo")

    @pytest.fixture
    def server(self, config):
        """Create a server instance."""
        return MCPServer(config=config)

    def test_create_server(self, config):
        """Test creating a server."""
        server = MCPServer(config=config)
        
        assert server.config == config
        assert server.process is None
        assert server.server_info is None
        assert server.tools == []
        assert server.resources == []
        assert server.prompts == []
        assert server._request_id == 0
        assert server._initialized is False

    def test_server_default_attributes(self, server):
        """Test server default attributes."""
        assert server._pending_requests == {}
        assert server._reader_task is None


class TestMCPClient:
    """Tests for MCPClient."""

    @pytest.fixture
    def client(self):
        """Create a client instance."""
        return MCPClient()

    def test_create_client(self):
        """Test creating a client."""
        client = MCPClient()
        
        assert client.servers == {}
        assert client._started is False

    def test_get_all_tools_empty(self, client):
        """Test getting all tools when empty."""
        tools = client.get_all_tools()
        
        assert tools == []

    def test_get_all_resources_empty(self, client):
        """Test getting all resources when empty."""
        resources = client.get_all_resources()
        
        assert resources == []

    def test_get_all_prompts_empty(self, client):
        """Test getting all prompts when empty."""
        prompts = client.get_all_prompts()
        
        assert prompts == []

    def test_find_tool_not_found(self, client):
        """Test finding a tool that doesn't exist."""
        result = client.find_tool("nonexistent")
        
        assert result is None

    def test_find_resource_not_found(self, client):
        """Test finding a resource that doesn't exist."""
        result = client.find_resource("file:///nonexistent")
        
        assert result is None

    def test_get_all_tools_with_server(self, client):
        """Test getting all tools with a server."""
        config = MCPServerConfig(name="test", command="echo")
        server = MCPServer(config=config)
        server.tools = [
            MCPTool(name="tool1", description="Tool 1", input_schema=MCPToolInputSchema()),
            MCPTool(name="tool2", description="Tool 2", input_schema=MCPToolInputSchema()),
        ]
        client.servers["test"] = server
        
        tools = client.get_all_tools()
        
        assert len(tools) == 2
        assert tools[0][0] == "test"
        assert tools[0][1].name == "tool1"

    def test_get_all_resources_with_server(self, client):
        """Test getting all resources with a server."""
        config = MCPServerConfig(name="test", command="echo")
        server = MCPServer(config=config)
        server.resources = [
            MCPResource(uri="file:///test1", name="Resource 1"),
            MCPResource(uri="file:///test2", name="Resource 2"),
        ]
        client.servers["test"] = server
        
        resources = client.get_all_resources()
        
        assert len(resources) == 2
        assert resources[0][0] == "test"
        assert resources[0][1].uri == "file:///test1"

    def test_get_all_prompts_with_server(self, client):
        """Test getting all prompts with a server."""
        config = MCPServerConfig(name="test", command="echo")
        server = MCPServer(config=config)
        server.prompts = [
            MCPPrompt(name="prompt1", description="Prompt 1"),
            MCPPrompt(name="prompt2", description="Prompt 2"),
        ]
        client.servers["test"] = server
        
        prompts = client.get_all_prompts()
        
        assert len(prompts) == 2
        assert prompts[0][0] == "test"
        assert prompts[0][1].name == "prompt1"

    def test_find_tool_exists(self, client):
        """Test finding a tool that exists."""
        config = MCPServerConfig(name="test", command="echo")
        server = MCPServer(config=config)
        server.tools = [
            MCPTool(name="my_tool", description="My Tool", input_schema=MCPToolInputSchema()),
        ]
        client.servers["test"] = server
        
        result = client.find_tool("my_tool")
        
        assert result is not None
        assert result[0] == "test"
        assert result[1].name == "my_tool"

    def test_find_resource_exists(self, client):
        """Test finding a resource that exists."""
        config = MCPServerConfig(name="test", command="echo")
        server = MCPServer(config=config)
        server.resources = [
            MCPResource(uri="file:///my/resource", name="My Resource"),
        ]
        client.servers["test"] = server
        
        result = client.find_resource("file:///my/resource")
        
        assert result is not None
        assert result[0] == "test"
        assert result[1].uri == "file:///my/resource"

    @pytest.mark.asyncio
    async def test_call_tool_server_not_found(self, client):
        """Test calling a tool on non-existent server."""
        result = await client.call_tool("nonexistent", "tool", {})
        
        assert result.is_error is True
        assert "Server not found" in result.content[0]["text"]

    @pytest.mark.asyncio
    async def test_read_resource_server_not_found(self, client):
        """Test reading a resource from non-existent server."""
        result = await client.read_resource("nonexistent", "file:///test")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_prompt_server_not_found(self, client):
        """Test getting a prompt from non-existent server."""
        result = await client.get_prompt("nonexistent", "prompt")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_start_empty(self, client):
        """Test starting client with no configs."""
        await client.start()
        
        assert client._started is True

    @pytest.mark.asyncio
    async def test_stop_empty(self, client):
        """Test stopping client with no servers."""
        client._started = True
        await client.stop()
        
        assert client._started is False
        assert client.servers == {}


class TestMCPToolInputSchema:
    """Tests for MCPToolInputSchema."""

    def test_create_schema(self):
        """Test creating a schema."""
        schema = MCPToolInputSchema(
            type="object",
            properties={"input": {"type": "string"}},
            required=["input"],
        )
        
        assert schema.type == "object"
        assert "input" in schema.properties
        assert schema.required == ["input"]

    def test_create_schema_defaults(self):
        """Test creating schema with defaults."""
        schema = MCPToolInputSchema()
        
        assert schema.type == "object"
        assert schema.properties == {}
        assert schema.required == []

    def test_to_dict(self):
        """Test converting to dict."""
        schema = MCPToolInputSchema(
            type="object",
            properties={"input": {"type": "string"}},
            required=["input"],
        )
        
        d = schema.to_dict()
        
        assert d["type"] == "object"
        assert d["properties"] == {"input": {"type": "string"}}
        assert d["required"] == ["input"]

    def test_from_dict(self):
        """Test creating from dict."""
        data = {
            "type": "object",
            "properties": {"input": {"type": "string"}},
            "required": ["input"],
        }
        
        schema = MCPToolInputSchema.from_dict(data)
        
        assert schema.type == "object"
        assert "input" in schema.properties


class TestMCPTool:
    """Tests for MCPTool."""

    def test_create_tool(self):
        """Test creating a tool."""
        schema = MCPToolInputSchema()
        tool = MCPTool(
            name="test_tool",
            description="A test tool",
            input_schema=schema,
        )
        
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert tool.input_schema == schema

    def test_create_tool_default_schema(self):
        """Test creating tool with default schema."""
        tool = MCPTool(name="test_tool")
        
        assert tool.name == "test_tool"
        assert tool.description is None
        assert tool.input_schema is not None

    def test_to_dict(self):
        """Test converting to dict."""
        tool = MCPTool(
            name="test_tool",
            description="A test tool",
            input_schema=MCPToolInputSchema(),
        )
        
        d = tool.to_dict()
        
        assert d["name"] == "test_tool"
        assert d["description"] == "A test tool"
        assert "inputSchema" in d

    def test_from_dict(self):
        """Test creating from dict."""
        data = {
            "name": "test_tool",
            "description": "A test tool",
            "inputSchema": {
                "type": "object",
                "properties": {},
            },
        }
        
        tool = MCPTool.from_dict(data)
        
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"


class TestMCPPromptArgument:
    """Tests for MCPPromptArgument."""

    def test_create_argument(self):
        """Test creating an argument."""
        arg = MCPPromptArgument(
            name="input",
            description="Input text",
            required=True,
            type=MCPPromptArgumentType.STRING,
        )
        
        assert arg.name == "input"
        assert arg.description == "Input text"
        assert arg.required is True
        assert arg.type == MCPPromptArgumentType.STRING

    def test_create_argument_defaults(self):
        """Test creating argument with defaults."""
        arg = MCPPromptArgument(name="input")
        
        assert arg.name == "input"
        assert arg.description is None
        assert arg.required is False
        assert arg.type == MCPPromptArgumentType.STRING

    def test_to_dict(self):
        """Test converting to dict."""
        arg = MCPPromptArgument(
            name="input",
            description="Input text",
            required=True,
            type=MCPPromptArgumentType.STRING,
        )
        
        d = arg.to_dict()
        
        assert d["name"] == "input"
        assert d["description"] == "Input text"
        assert d["required"] is True
        assert d["type"] == "string"


class TestMCPPrompt:
    """Tests for MCPPrompt."""

    def test_create_prompt(self):
        """Test creating a prompt."""
        prompt = MCPPrompt(
            name="test_prompt",
            description="A test prompt",
            arguments=[
                MCPPromptArgument(name="input"),
            ],
        )
        
        assert prompt.name == "test_prompt"
        assert prompt.description == "A test prompt"
        assert len(prompt.arguments) == 1

    def test_create_prompt_defaults(self):
        """Test creating prompt with defaults."""
        prompt = MCPPrompt(name="test_prompt")
        
        assert prompt.name == "test_prompt"
        assert prompt.description is None
        assert prompt.arguments == []

    def test_to_dict(self):
        """Test converting to dict."""
        prompt = MCPPrompt(
            name="test_prompt",
            description="A test prompt",
        )
        
        d = prompt.to_dict()
        
        assert d["name"] == "test_prompt"
        assert d["description"] == "A test prompt"
        assert d["arguments"] == []

    def test_from_dict(self):
        """Test creating from dict."""
        data = {
            "name": "test_prompt",
            "description": "A test prompt",
            "arguments": [
                {"name": "input", "description": "Input", "required": True}
            ],
        }
        
        prompt = MCPPrompt.from_dict(data)
        
        assert prompt.name == "test_prompt"
        assert prompt.description == "A test prompt"
        assert len(prompt.arguments) == 1


class TestMCPResource:
    """Tests for MCPResource."""

    def test_create_resource(self):
        """Test creating a resource."""
        resource = MCPResource(
            uri="file:///test",
            name="Test Resource",
            description="A test resource",
            mime_type="text/plain",
        )
        
        assert resource.uri == "file:///test"
        assert resource.name == "Test Resource"
        assert resource.description == "A test resource"
        assert resource.mime_type == "text/plain"

    def test_create_resource_defaults(self):
        """Test creating resource with defaults."""
        resource = MCPResource(uri="file:///test", name="Test")
        
        assert resource.uri == "file:///test"
        assert resource.name == "Test"
        assert resource.description is None
        assert resource.mime_type is None

    def test_to_dict(self):
        """Test converting to dict."""
        resource = MCPResource(
            uri="file:///test",
            name="Test Resource",
        )
        
        d = resource.to_dict()
        
        assert d["uri"] == "file:///test"
        assert d["name"] == "Test Resource"

    def test_from_dict(self):
        """Test creating from dict."""
        data = {
            "uri": "file:///test",
            "name": "Test Resource",
            "description": "A test resource",
        }
        
        resource = MCPResource.from_dict(data)
        
        assert resource.uri == "file:///test"
        assert resource.name == "Test Resource"
        assert resource.description == "A test resource"


class TestMCPResult:
    """Tests for MCPResult."""

    def test_create_result(self):
        """Test creating a result."""
        result = MCPResult(
            content=[{"type": "text", "text": "Hello"}],
            is_error=False,
        )
        
        assert len(result.content) == 1
        assert result.content[0]["text"] == "Hello"
        assert result.is_error is False

    def test_create_error_result(self):
        """Test creating an error result."""
        result = MCPResult(
            content=[{"type": "text", "text": "Error occurred"}],
            is_error=True,
        )
        
        assert result.is_error is True

    def test_to_dict(self):
        """Test converting to dict."""
        result = MCPResult(
            content=[{"type": "text", "text": "Hello"}],
            is_error=False,
        )
        
        d = result.to_dict()
        
        assert "content" in d
        assert "isError" in d

    def test_from_dict(self):
        """Test creating from dict."""
        data = {
            "content": [{"type": "text", "text": "Hello"}],
            "isError": False,
        }
        
        result = MCPResult.from_dict(data)
        
        assert len(result.content) == 1
        assert result.is_error is False
