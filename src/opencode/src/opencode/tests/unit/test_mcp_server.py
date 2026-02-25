"""Tests for MCP Server module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from opencode.mcp.server import (
    MCPServer,
    MCPServerConfig,
    run_mcp_server,
    main,
)


class TestMCPServerConfig:
    """Tests for MCPServerConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = MCPServerConfig()
        
        assert config.name == "opencode"
        assert config.version == "1.0.0"
        assert config.transport == "stdio"
        assert config.host == "localhost"
        assert config.port == 3000

    def test_custom_config(self):
        """Test custom configuration values."""
        config = MCPServerConfig(
            name="custom-server",
            version="2.0.0",
            transport="tcp",
            host="0.0.0.0",
            port=8080,
        )
        
        assert config.name == "custom-server"
        assert config.version == "2.0.0"
        assert config.transport == "tcp"
        assert config.host == "0.0.0.0"
        assert config.port == 8080


class TestMCPServer:
    """Tests for MCPServer class."""

    def test_init_default_config(self):
        """Test server initialization with default config."""
        server = MCPServer()
        
        assert server.config.name == "opencode"
        assert server._running is False
        assert "initialize" in server._request_handlers
        assert "tools/list" in server._request_handlers
        assert "tools/call" in server._request_handlers

    def test_init_custom_config(self):
        """Test server initialization with custom config."""
        config = MCPServerConfig(transport="tcp", port=9000)
        server = MCPServer(config)
        
        assert server.config.transport == "tcp"
        assert server.config.port == 9000

    def test_register_handlers(self):
        """Test handler registration."""
        server = MCPServer()
        
        assert server._request_handlers["initialize"] == server._handle_initialize
        assert server._request_handlers["tools/list"] == server._handle_tools_list
        assert server._request_handlers["tools/call"] == server._handle_tools_call
        assert server._request_handlers["resources/list"] == server._handle_resources_list
        assert server._request_handlers["prompts/list"] == server._handle_prompts_list

    @pytest.mark.asyncio
    async def test_stop(self):
        """Test stopping the server."""
        server = MCPServer()
        server._running = True
        
        await server.stop()
        
        assert server._running is False

    @pytest.mark.asyncio
    async def test_handle_initialize(self):
        """Test initialize handler."""
        server = MCPServer()
        
        result = await server._handle_initialize({})
        
        assert result["protocolVersion"] == "2024-11-05"
        assert "tools" in result["capabilities"]
        assert "resources" in result["capabilities"]
        assert "prompts" in result["capabilities"]
        assert result["serverInfo"]["name"] == "opencode"
        assert result["serverInfo"]["version"] == "1.0.0"

    @pytest.mark.asyncio
    async def test_handle_tools_list(self):
        """Test tools/list handler."""
        server = MCPServer()
        
        result = await server._handle_tools_list({})
        
        assert "tools" in result
        assert isinstance(result["tools"], list)

    @pytest.mark.asyncio
    async def test_handle_resources_list(self):
        """Test resources/list handler."""
        server = MCPServer()
        
        result = await server._handle_resources_list({})
        
        assert result == {"resources": []}

    @pytest.mark.asyncio
    async def test_handle_prompts_list(self):
        """Test prompts/list handler."""
        server = MCPServer()
        
        result = await server._handle_prompts_list({})
        
        assert result == {"prompts": []}

    @pytest.mark.asyncio
    async def test_handle_request_initialize(self):
        """Test handling initialize request."""
        server = MCPServer()
        
        request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "id": 1,
            "params": {},
        }
        
        response = await server._handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert "result" in response
        assert response["id"] == 1

    @pytest.mark.asyncio
    async def test_handle_request_unknown_method(self):
        """Test handling unknown method request."""
        server = MCPServer()
        
        request = {
            "jsonrpc": "2.0",
            "method": "unknown/method",
            "id": 2,
            "params": {},
        }
        
        response = await server._handle_request(request)
        
        assert "error" in response
        assert response["error"]["code"] == -32601
        assert "Method not found" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_handle_tools_call_missing_name(self):
        """Test tools/call with missing tool name."""
        server = MCPServer()
        
        with pytest.raises(ValueError, match="Tool name is required"):
            await server._handle_tools_call({"arguments": {}})

    def test_make_error_response(self):
        """Test error response creation."""
        server = MCPServer()
        
        response = server._make_error_response(-32600, "Invalid Request", 1)
        
        assert response["jsonrpc"] == "2.0"
        assert response["error"]["code"] == -32600
        assert response["error"]["message"] == "Invalid Request"
        assert response["id"] == 1

    def test_make_error_response_no_id(self):
        """Test error response without request ID."""
        server = MCPServer()
        
        response = server._make_error_response(-32603, "Internal error")
        
        assert response["jsonrpc"] == "2.0"
        assert response["error"]["code"] == -32603
        assert response["id"] is None

    @pytest.mark.asyncio
    async def test_send_error(self, capsys):
        """Test sending error to stdout."""
        server = MCPServer()
        
        await server._send_error(-32700, "Parse error")
        
        captured = capsys.readouterr()
        output = json.loads(captured.out.strip())
        
        assert output["jsonrpc"] == "2.0"
        assert output["error"]["code"] == -32700
        assert output["error"]["message"] == "Parse error"

    @pytest.mark.asyncio
    async def test_run_websocket_not_implemented(self):
        """Test WebSocket transport raises NotImplementedError."""
        config = MCPServerConfig(transport="websocket")
        server = MCPServer(config)
        
        with pytest.raises(NotImplementedError, match="WebSocket transport not yet implemented"):
            await server._run_websocket()


class TestMCPServerToolsCall:
    """Tests for tools/call functionality."""

    @pytest.mark.asyncio
    async def test_handle_tools_call_success(self):
        """Test successful tool call."""
        server = MCPServer()
        
        # Mock the tool registry
        mock_result = MagicMock()
        mock_result.output = "Tool executed successfully"
        mock_result.success = True
        
        with patch.object(server.tool_registry, 'execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = mock_result
            
            result = await server._handle_tools_call({
                "name": "test_tool",
                "arguments": {"param": "value"},
            })
            
            assert "content" in result
            assert result["content"][0]["type"] == "text"
            assert result["content"][0]["text"] == "Tool executed successfully"
            assert result["isError"] is False

    @pytest.mark.asyncio
    async def test_handle_tools_call_failure(self):
        """Test failed tool call."""
        server = MCPServer()
        
        # Mock the tool registry
        mock_result = MagicMock()
        mock_result.output = "Tool execution failed"
        mock_result.success = False
        
        with patch.object(server.tool_registry, 'execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = mock_result
            
            result = await server._handle_tools_call({
                "name": "failing_tool",
                "arguments": {},
            })
            
            assert result["isError"] is True


class TestRunMCPServer:
    """Tests for run_mcp_server function."""

    @pytest.mark.asyncio
    async def test_run_mcp_server_stdio(self):
        """Test running MCP server with stdio transport."""
        with patch('opencode.mcp.server.MCPServer') as MockServer:
            mock_server = MagicMock()
            mock_server.start = AsyncMock()
            MockServer.return_value = mock_server
            
            await run_mcp_server(transport="stdio")
            
            MockServer.assert_called_once()
            mock_server.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_mcp_server_tcp(self):
        """Test running MCP server with TCP transport."""
        with patch('opencode.mcp.server.MCPServer') as MockServer:
            mock_server = MagicMock()
            mock_server.start = AsyncMock()
            MockServer.return_value = mock_server
            
            await run_mcp_server(transport="tcp", host="0.0.0.0", port=8080)
            
            # Verify config was created with correct values
            call_args = MockServer.call_args
            config = call_args[0][0]
            assert config.transport == "tcp"
            assert config.host == "0.0.0.0"
            assert config.port == 8080


class TestMain:
    """Tests for main function."""

    def test_main_default_args(self):
        """Test main with default arguments."""
        with patch('sys.argv', ['mcp_server']):
            with patch('asyncio.run') as mock_run:
                main()
                
                mock_run.assert_called_once()

    def test_main_custom_args(self):
        """Test main with custom arguments."""
        with patch('sys.argv', ['mcp_server', '--transport', 'tcp', '--host', '0.0.0.0', '--port', '9000']):
            with patch('asyncio.run') as mock_run:
                main()
                
                mock_run.assert_called_once()

    def test_main_partial_args(self):
        """Test main with partial arguments."""
        with patch('sys.argv', ['mcp_server', '--transport', 'tcp']):
            with patch('asyncio.run') as mock_run:
                main()
                
                mock_run.assert_called_once()
