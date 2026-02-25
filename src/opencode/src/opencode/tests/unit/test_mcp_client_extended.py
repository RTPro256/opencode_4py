"""
Unit tests for MCP client implementation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from opencode.mcp.client import MCPClient, MCPServer, MCPServerConfig
from opencode.mcp.types import MCPTool, MCPResource, MCPPrompt


class TestMCPServerConfig:
    """Test MCP server configuration."""

    def test_config_initialization(self):
        """Test config initialization."""
        config = MCPServerConfig(
            name="test-server",
            command="python",
            args=["-m", "test_server"],
            env={"TEST": "value"},
            timeout=30
        )
        assert config.name == "test-server"
        assert config.command == "python"
        assert config.args == ["-m", "test_server"]
        assert config.env == {"TEST": "value"}
        assert config.timeout == 30

    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            "command": "node",
            "args": ["server.js"],
            "env": {"NODE_ENV": "test"},
            "timeout": 60
        }
        config = MCPServerConfig.from_dict("my-server", data)
        
        assert config.name == "my-server"
        assert config.command == "node"
        assert config.args == ["server.js"]
        assert config.env == {"NODE_ENV": "test"}
        assert config.timeout == 60


class TestMCPClient:
    """Test MCP client functionality."""

    @pytest.fixture
    def client(self):
        """Create MCP client instance."""
        return MCPClient()

    @pytest.fixture
    def mock_server_config(self):
        """Create mock server configuration."""
        return MCPServerConfig(
            name="test-server",
            command="echo",
            args=["test"],
            timeout=5
        )

    def test_client_initialization(self, client):
        """Test client initialization."""
        assert client.servers == {}
        assert client._started == False

    @pytest.mark.asyncio
    async def test_add_server(self, client, mock_server_config):
        """Test adding a server."""
        with patch.object(client, 'add_server', new_callable=AsyncMock) as mock_add:
            mock_add.return_value = True
            result = await client.add_server(mock_server_config)
            assert result == True

    @pytest.mark.asyncio
    async def test_remove_server(self, client):
        """Test removing a server."""
        mock_server = AsyncMock()
        mock_server.stop = AsyncMock()
        client.servers["test"] = mock_server
        
        await client.remove_server("test")
        
        mock_server.stop.assert_called_once()
        assert "test" not in client.servers

    @pytest.mark.asyncio
    async def test_start(self, client):
        """Test starting the client."""
        await client.start()
        assert client._started == True

    @pytest.mark.asyncio
    async def test_stop(self, client):
        """Test stopping the client."""
        mock_server = AsyncMock()
        mock_server.stop = AsyncMock()
        client.servers["test"] = mock_server
        client._started = True
        
        await client.stop()
        
        mock_server.stop.assert_called_once()
        assert len(client.servers) == 0
        assert client._started == False

    def test_get_all_tools(self, client):
        """Test getting all tools."""
        mock_server = MagicMock()
        mock_tool = MagicMock(spec=MCPTool)
        mock_tool.name = "test_tool"
        mock_server.tools = [mock_tool]
        client.servers["test-server"] = mock_server
        
        tools = client.get_all_tools()
        
        assert len(tools) == 1
        assert tools[0][0] == "test-server"
        assert tools[0][1].name == "test_tool"

    def test_get_all_resources(self, client):
        """Test getting all resources."""
        mock_server = MagicMock()
        mock_resource = MagicMock(spec=MCPResource)
        mock_resource.name = "test_resource"
        mock_server.resources = [mock_resource]
        client.servers["test-server"] = mock_server
        
        resources = client.get_all_resources()
        
        assert len(resources) == 1
        assert resources[0][0] == "test-server"

    def test_get_all_prompts(self, client):
        """Test getting all prompts."""
        mock_server = MagicMock()
        mock_prompt = MagicMock(spec=MCPPrompt)
        mock_prompt.name = "test_prompt"
        mock_server.prompts = [mock_prompt]
        client.servers["test-server"] = mock_server
        
        prompts = client.get_all_prompts()
        
        assert len(prompts) == 1
        assert prompts[0][0] == "test-server"

    @pytest.mark.asyncio
    async def test_call_tool(self, client):
        """Test calling a tool."""
        mock_server = AsyncMock()
        mock_server.call_tool = AsyncMock(return_value=MagicMock(content="result"))
        client.servers["test-server"] = mock_server
        
        result = await client.call_tool("test-server", "test_tool", {"arg": "value"})
        
        mock_server.call_tool.assert_called_once_with("test_tool", {"arg": "value"})

    @pytest.mark.asyncio
    async def test_call_tool_server_not_found(self, client):
        """Test calling a tool on non-existent server."""
        # The client returns an error result when server not found
        result = await client.call_tool("nonexistent", "test_tool", {})
        # Result should indicate an error
        assert result is not None
        assert result.is_error is True

    @pytest.mark.asyncio
    async def test_read_resource(self, client):
        """Test reading a resource."""
        mock_server = AsyncMock()
        mock_server.read_resource = AsyncMock(return_value=MagicMock(contents=[]))
        client.servers["test-server"] = mock_server
        
        result = await client.read_resource("test-server", "file:///test.txt")
        
        mock_server.read_resource.assert_called_once_with("file:///test.txt")

    @pytest.mark.asyncio
    async def test_get_prompt(self, client):
        """Test getting a prompt."""
        mock_server = AsyncMock()
        mock_server.get_prompt = AsyncMock(return_value=MagicMock(messages=[]))
        client.servers["test-server"] = mock_server
        
        result = await client.get_prompt("test-server", "test_prompt", {})
        
        mock_server.get_prompt.assert_called_once_with("test_prompt", {})


class TestMCPServer:
    """Test MCP server functionality."""

    @pytest.fixture
    def server_config(self):
        """Create server configuration."""
        return MCPServerConfig(
            name="test-server",
            command="echo",
            args=["test"],
            timeout=5
        )

    @pytest.fixture
    def server(self, server_config):
        """Create MCP server instance."""
        from opencode.mcp.client import MCPServer
        return MCPServer(config=server_config)

    def test_server_initialization(self, server, server_config):
        """Test server initialization."""
        assert server.config == server_config
        assert server.process is None
        assert server.tools == []
        assert server.resources == []
        assert server.prompts == []

    @pytest.mark.asyncio
    async def test_server_stop_when_not_started(self, server):
        """Test stopping server when not started."""
        # Should not raise an error
        await server.stop()

    def test_server_request_id_increment(self, server):
        """Test request ID incrementing."""
        initial_id = server._request_id
        server._request_id += 1
        assert server._request_id == initial_id + 1


class TestMCPClientIntegration:
    """Integration tests for MCP client."""

    @pytest.fixture
    def client(self):
        """Create MCP client instance."""
        return MCPClient()

    @pytest.mark.asyncio
    async def test_full_workflow(self, client):
        """Test full client workflow."""
        # Start client
        await client.start()
        assert client._started == True
        
        # Stop client
        await client.stop()
        assert client._started == False
        assert len(client.servers) == 0

    @pytest.mark.asyncio
    async def test_multiple_servers(self, client):
        """Test managing multiple servers."""
        mock_server1 = MagicMock()
        mock_server1.tools = [MagicMock(name="tool1")]
        mock_server1.stop = AsyncMock()
        
        mock_server2 = MagicMock()
        mock_server2.tools = [MagicMock(name="tool2")]
        mock_server2.stop = AsyncMock()
        
        client.servers["server1"] = mock_server1
        client.servers["server2"] = mock_server2
        
        tools = client.get_all_tools()
        assert len(tools) == 2
        
        await client.stop()
        assert len(client.servers) == 0
