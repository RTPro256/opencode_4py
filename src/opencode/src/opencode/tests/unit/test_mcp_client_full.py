"""
Comprehensive unit tests for MCP client implementation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
import json
from pathlib import Path

from opencode.mcp.client import MCPClient, MCPServer, MCPServerConfig
from opencode.mcp.types import (
    MCPTool,
    MCPResource,
    MCPPrompt,
    MCPServerInfo,
    MCPCapabilities,
    MCPResult,
)


class TestMCPServerConfigExtended:
    """Extended tests for MCP server configuration."""

    def test_config_defaults(self):
        """Test config default values."""
        config = MCPServerConfig(name="test", command="python")
        assert config.args == []
        assert config.env == {}
        assert config.cwd is None
        assert config.timeout == 30

    def test_config_from_dict_minimal(self):
        """Test creating config from minimal dictionary."""
        data = {}
        config = MCPServerConfig.from_dict("minimal", data)
        
        assert config.name == "minimal"
        assert config.command == ""
        assert config.args == []
        assert config.env == {}
        assert config.timeout == 30

    def test_config_from_dict_with_cwd(self):
        """Test creating config with cwd."""
        data = {"cwd": "/test/path"}
        config = MCPServerConfig.from_dict("test", data)
        
        assert config.cwd == Path("/test/path")

    def test_config_from_dict_with_env(self):
        """Test creating config with environment variables."""
        data = {"env": {"API_KEY": "secret", "DEBUG": "true"}}
        config = MCPServerConfig.from_dict("test", data)
        
        assert config.env["API_KEY"] == "secret"
        assert config.env["DEBUG"] == "true"


class TestMCPServerExtended:
    """Extended tests for MCP server."""

    @pytest.fixture
    def server_config(self):
        """Create server configuration."""
        return MCPServerConfig(
            name="test-server",
            command="echo",
            args=["test"],
            timeout=5,
        )

    @pytest.fixture
    def server(self, server_config):
        """Create MCP server instance."""
        return MCPServer(config=server_config)

    def test_server_initial_state(self, server):
        """Test server initial state."""
        assert server.process is None
        assert server.server_info is None
        assert server.tools == []
        assert server.resources == []
        assert server.prompts == []
        assert server._request_id == 0
        assert server._pending_requests == {}
        assert server._reader_task is None
        assert server._initialized is False

    @pytest.mark.asyncio
    async def test_server_start_already_running(self, server):
        """Test starting server when already running."""
        server.process = MagicMock()
        result = await server.start()
        assert result is True

    @pytest.mark.asyncio
    async def test_server_stop_with_reader_task(self, server):
        """Test stopping server with active reader task."""
        # Create a proper async task that can be cancelled
        async def dummy_task():
            await asyncio.sleep(10)
        
        mock_task = asyncio.create_task(dummy_task())
        server._reader_task = mock_task
        
        await server.stop()
        
        assert server._reader_task is None

    @pytest.mark.asyncio
    async def test_server_stop_with_process(self, server):
        """Test stopping server with process."""
        mock_process = MagicMock()
        mock_process.terminate = MagicMock()
        mock_process.wait = AsyncMock()
        mock_process.kill = MagicMock()
        server.process = mock_process
        
        await server.stop()
        
        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once()
        assert server.process is None

    @pytest.mark.asyncio
    async def test_server_stop_process_timeout(self, server):
        """Test stopping server when process times out."""
        mock_process = MagicMock()
        mock_process.terminate = MagicMock()
        # First wait call times out, second succeeds (after kill)
        mock_process.wait = AsyncMock(side_effect=[asyncio.TimeoutError(), None])
        mock_process.kill = MagicMock()
        server.process = mock_process
        
        await server.stop()
        
        mock_process.kill.assert_called_once()

    @pytest.mark.asyncio
    async def test_server_stop_process_exception(self, server):
        """Test stopping server when process raises exception."""
        mock_process = MagicMock()
        mock_process.terminate = MagicMock()
        mock_process.wait = AsyncMock(side_effect=Exception("Process error"))
        server.process = mock_process
        
        # Should not raise
        await server.stop()
        
        assert server.process is None

    @pytest.mark.asyncio
    async def test_send_request_no_process(self, server):
        """Test sending request without process."""
        result = await server._send_request("test_method", {})
        assert result is None

    @pytest.mark.asyncio
    async def test_send_request_no_stdin(self, server):
        """Test sending request without stdin."""
        server.process = MagicMock()
        server.process.stdin = None
        
        result = await server._send_request("test_method", {})
        assert result is None

    @pytest.mark.asyncio
    async def test_send_notification_no_process(self, server):
        """Test sending notification without process."""
        # Should not raise
        await server._send_notification("test_method", {})

    @pytest.mark.asyncio
    async def test_send_notification_no_stdin(self, server):
        """Test sending notification without stdin."""
        server.process = MagicMock()
        server.process.stdin = None
        
        # Should not raise
        await server._send_notification("test_method", {})

    @pytest.mark.asyncio
    async def test_call_tool_not_initialized(self, server):
        """Test calling tool when not initialized."""
        with pytest.raises(RuntimeError, match="not initialized"):
            await server.call_tool("test_tool", {})

    @pytest.mark.asyncio
    async def test_read_resource_not_initialized(self, server):
        """Test reading resource when not initialized."""
        with pytest.raises(RuntimeError, match="not initialized"):
            await server.read_resource("test://resource")

    @pytest.mark.asyncio
    async def test_get_prompt_not_initialized(self, server):
        """Test getting prompt when not initialized."""
        with pytest.raises(RuntimeError, match="not initialized"):
            await server.get_prompt("test_prompt")

    @pytest.mark.asyncio
    async def test_call_tool_success(self, server):
        """Test successful tool call."""
        server._initialized = True
        server._send_request = AsyncMock(return_value={
            "result": {
                "content": [{"type": "text", "text": "success"}],
                "isError": False,
            }
        })
        
        result = await server.call_tool("test_tool", {"arg": "value"})
        
        assert result is not None
        assert result.is_error is False

    @pytest.mark.asyncio
    async def test_call_tool_failure(self, server):
        """Test failed tool call."""
        server._initialized = True
        server._send_request = AsyncMock(return_value=None)
        
        result = await server.call_tool("test_tool", {})
        
        assert result.is_error is True

    @pytest.mark.asyncio
    async def test_read_resource_success(self, server):
        """Test successful resource read."""
        server._initialized = True
        server._send_request = AsyncMock(return_value={
            "result": {"contents": [{"uri": "test://resource"}]}
        })
        
        result = await server.read_resource("test://resource")
        
        assert result is not None
        assert "contents" in result

    @pytest.mark.asyncio
    async def test_read_resource_failure(self, server):
        """Test failed resource read."""
        server._initialized = True
        server._send_request = AsyncMock(return_value=None)
        
        result = await server.read_resource("test://resource")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_prompt_success(self, server):
        """Test successful prompt get."""
        server._initialized = True
        server._send_request = AsyncMock(return_value={
            "result": {"messages": [{"role": "user", "content": "test"}]}
        })
        
        result = await server.get_prompt("test_prompt", {"arg": "value"})
        
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_prompt_no_arguments(self, server):
        """Test getting prompt without arguments."""
        server._initialized = True
        server._send_request = AsyncMock(return_value={
            "result": {"messages": []}
        })
        
        result = await server.get_prompt("test_prompt")
        
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_prompt_failure(self, server):
        """Test failed prompt get."""
        server._initialized = True
        server._send_request = AsyncMock(return_value=None)
        
        result = await server.get_prompt("test_prompt")
        
        assert result is None


class TestMCPServerHandleNotification:
    """Tests for MCPServer notification handling."""

    @pytest.fixture
    def server(self):
        """Create MCP server instance."""
        config = MCPServerConfig(name="test", command="echo")
        return MCPServer(config=config)

    @pytest.mark.asyncio
    async def test_handle_tools_list_changed(self, server):
        """Test handling tools list changed notification."""
        server._load_tools = AsyncMock()
        
        await server._handle_notification({
            "method": "notifications/tools/list_changed",
            "params": {},
        })
        
        server._load_tools.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_resources_list_changed(self, server):
        """Test handling resources list changed notification."""
        server._load_resources = AsyncMock()
        
        await server._handle_notification({
            "method": "notifications/resources/list_changed",
            "params": {},
        })
        
        server._load_resources.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_prompts_list_changed(self, server):
        """Test handling prompts list changed notification."""
        server._load_prompts = AsyncMock()
        
        await server._handle_notification({
            "method": "notifications/prompts/list_changed",
            "params": {},
        })
        
        server._load_prompts.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_resources_updated(self, server):
        """Test handling resources updated notification."""
        # Should not raise
        await server._handle_notification({
            "method": "notifications/resources/updated",
            "params": {"uri": "test://resource"},
        })

    @pytest.mark.asyncio
    async def test_handle_unknown_notification(self, server):
        """Test handling unknown notification."""
        # Should not raise
        await server._handle_notification({
            "method": "unknown/method",
            "params": {},
        })


class TestMCPClientExtended:
    """Extended tests for MCP client."""

    @pytest.fixture
    def client(self):
        """Create MCP client instance."""
        return MCPClient()

    def test_client_initial_state(self, client):
        """Test client initial state."""
        assert client.servers == {}
        assert client._started is False

    @pytest.mark.asyncio
    async def test_add_server_already_exists(self, client):
        """Test adding server that already exists."""
        client.servers["test"] = MagicMock()
        
        config = MCPServerConfig(name="test", command="echo")
        result = await client.add_server(config)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_add_server_failure(self, client):
        """Test adding server that fails to start."""
        config = MCPServerConfig(name="test", command="nonexistent_command_xyz")
        
        with patch('shutil.which', return_value=None):
            result = await client.add_server(config)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_remove_server_not_found(self, client):
        """Test removing server that doesn't exist."""
        # Should not raise
        await client.remove_server("nonexistent")

    @pytest.mark.asyncio
    async def test_start_with_configs(self, client):
        """Test starting client with configs."""
        config1 = MCPServerConfig(name="server1", command="echo")
        config2 = MCPServerConfig(name="server2", command="echo")
        
        with patch.object(client, 'add_server', new_callable=AsyncMock) as mock_add:
            mock_add.return_value = True
            await client.start([config1, config2])
            
            assert mock_add.call_count == 2

    @pytest.mark.asyncio
    async def test_read_resource_server_not_found(self, client):
        """Test reading resource from nonexistent server."""
        result = await client.read_resource("nonexistent", "test://resource")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_prompt_server_not_found(self, client):
        """Test getting prompt from nonexistent server."""
        result = await client.get_prompt("nonexistent", "test_prompt")
        assert result is None

    def test_find_tool_found(self, client):
        """Test finding tool that exists."""
        mock_tool = MagicMock(spec=MCPTool)
        mock_tool.name = "test_tool"
        mock_server = MagicMock()
        mock_server.tools = [mock_tool]
        client.servers["test-server"] = mock_server
        
        result = client.find_tool("test_tool")
        
        assert result is not None
        assert result[0] == "test-server"
        assert result[1].name == "test_tool"

    def test_find_tool_not_found(self, client):
        """Test finding tool that doesn't exist."""
        result = client.find_tool("nonexistent")
        assert result is None

    def test_find_resource_found(self, client):
        """Test finding resource that exists."""
        mock_resource = MagicMock(spec=MCPResource)
        mock_resource.uri = "test://resource"
        mock_server = MagicMock()
        mock_server.resources = [mock_resource]
        client.servers["test-server"] = mock_server
        
        result = client.find_resource("test://resource")
        
        assert result is not None
        assert result[0] == "test-server"

    def test_find_resource_not_found(self, client):
        """Test finding resource that doesn't exist."""
        result = client.find_resource("test://nonexistent")
        assert result is None

    def test_get_all_prompts_multiple_servers(self, client):
        """Test getting all prompts from multiple servers."""
        mock_prompt1 = MagicMock(spec=MCPPrompt)
        mock_prompt1.name = "prompt1"
        mock_server1 = MagicMock()
        mock_server1.prompts = [mock_prompt1]
        
        mock_prompt2 = MagicMock(spec=MCPPrompt)
        mock_prompt2.name = "prompt2"
        mock_server2 = MagicMock()
        mock_server2.prompts = [mock_prompt2]
        
        client.servers["server1"] = mock_server1
        client.servers["server2"] = mock_server2
        
        prompts = client.get_all_prompts()
        
        assert len(prompts) == 2


class TestMCPServerLoadCapabilities:
    """Tests for loading server capabilities."""

    @pytest.fixture
    def server(self):
        """Create MCP server instance."""
        config = MCPServerConfig(name="test", command="echo")
        server = MCPServer(config=config)
        server._send_request = AsyncMock()
        return server

    @pytest.mark.asyncio
    async def test_load_tools(self, server):
        """Test loading tools from server."""
        server._send_request.return_value = {
            "result": {
                "tools": [
                    {"name": "tool1", "description": "Tool 1"},
                    {"name": "tool2", "description": "Tool 2"},
                ]
            }
        }
        
        await server._load_tools()
        
        assert len(server.tools) == 2

    @pytest.mark.asyncio
    async def test_load_tools_no_result(self, server):
        """Test loading tools with no result."""
        server._send_request.return_value = None
        
        await server._load_tools()
        
        assert len(server.tools) == 0

    @pytest.mark.asyncio
    async def test_load_resources(self, server):
        """Test loading resources from server."""
        server._send_request.return_value = {
            "result": {
                "resources": [
                    {"uri": "test://res1", "name": "Resource 1"},
                ]
            }
        }
        
        await server._load_resources()
        
        assert len(server.resources) == 1

    @pytest.mark.asyncio
    async def test_load_resources_no_result(self, server):
        """Test loading resources with no result."""
        server._send_request.return_value = None
        
        await server._load_resources()
        
        assert len(server.resources) == 0

    @pytest.mark.asyncio
    async def test_load_prompts(self, server):
        """Test loading prompts from server."""
        server._send_request.return_value = {
            "result": {
                "prompts": [
                    {"name": "prompt1", "description": "Prompt 1"},
                ]
            }
        }
        
        await server._load_prompts()
        
        assert len(server.prompts) == 1

    @pytest.mark.asyncio
    async def test_load_prompts_no_result(self, server):
        """Test loading prompts with no result."""
        server._send_request.return_value = None
        
        await server._load_prompts()
        
        assert len(server.prompts) == 0


class TestMCPClientGetAllMethods:
    """Tests for MCPClient get_all_* methods with edge cases."""

    @pytest.fixture
    def client(self):
        """Create MCP client instance."""
        return MCPClient()

    def test_get_all_tools_empty(self, client):
        """Test getting all tools when no servers."""
        tools = client.get_all_tools()
        assert tools == []

    def test_get_all_resources_empty(self, client):
        """Test getting all resources when no servers."""
        resources = client.get_all_resources()
        assert resources == []

    def test_get_all_prompts_empty(self, client):
        """Test getting all prompts when no servers."""
        prompts = client.get_all_prompts()
        assert prompts == []

    def test_get_all_tools_multiple_servers(self, client):
        """Test getting all tools from multiple servers."""
        mock_tool1 = MagicMock(spec=MCPTool)
        mock_tool1.name = "tool1"
        mock_server1 = MagicMock()
        mock_server1.tools = [mock_tool1]
        
        mock_tool2 = MagicMock(spec=MCPTool)
        mock_tool2.name = "tool2"
        mock_server2 = MagicMock()
        mock_server2.tools = [mock_tool2]
        
        client.servers["server1"] = mock_server1
        client.servers["server2"] = mock_server2
        
        tools = client.get_all_tools()
        
        assert len(tools) == 2

    def test_get_all_resources_multiple_servers(self, client):
        """Test getting all resources from multiple servers."""
        mock_resource1 = MagicMock(spec=MCPResource)
        mock_resource1.uri = "test://res1"
        mock_server1 = MagicMock()
        mock_server1.resources = [mock_resource1]
        
        mock_resource2 = MagicMock(spec=MCPResource)
        mock_resource2.uri = "test://res2"
        mock_server2 = MagicMock()
        mock_server2.resources = [mock_resource2]
        
        client.servers["server1"] = mock_server1
        client.servers["server2"] = mock_server2
        
        resources = client.get_all_resources()
        
        assert len(resources) == 2
