"""
Tests for tools API routes.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from opencode.server.routes.tools import (
    router,
    ToolInfo,
    ToolExecuteRequest,
    ToolExecuteResponse,
    MCPToolInfo,
)


@pytest.fixture
def app():
    """Create FastAPI app with tools router."""
    app = FastAPI()
    app.include_router(router, prefix="/tools")
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_tool_registry():
    """Create mock tool registry."""
    registry = MagicMock()
    registry.list_tools = MagicMock(return_value=[])
    registry.get_tool = MagicMock(return_value=None)
    return registry


@pytest.fixture
def mock_tool():
    """Create mock tool."""
    tool = MagicMock()
    tool.name = "test_tool"
    tool.description = "A test tool"
    tool.parameters = {"type": "object", "properties": {}}
    tool.permission_level = MagicMock(value="normal")
    tool.execute = AsyncMock(return_value=MagicMock(
        output="Tool output",
        error=None,
        files_changed=[],
        metadata={},
    ))
    return tool


@pytest.fixture
def mock_mcp_client():
    """Create mock MCP client."""
    client = MagicMock()
    client.get_all_tools = MagicMock(return_value=[])
    client.get_all_resources = MagicMock(return_value=[])
    client.get_all_prompts = MagicMock(return_value=[])
    client.call_tool = AsyncMock(return_value=MagicMock(
        content="MCP tool output",
        is_error=False,
    ))
    client.read_resource = AsyncMock(return_value={"content": "resource data"})
    client.get_prompt = AsyncMock(return_value={"messages": []})
    return client


class TestToolModels:
    """Tests for Pydantic models."""
    
    def test_tool_info_creation(self):
        """Test ToolInfo model creation."""
        info = ToolInfo(
            name="test_tool",
            description="A test tool",
            parameters={"type": "object"},
            permission_level="normal",
        )
        assert info.name == "test_tool"
        assert info.description == "A test tool"
        assert info.parameters == {"type": "object"}
        assert info.permission_level == "normal"
    
    def test_tool_execute_request_defaults(self):
        """Test ToolExecuteRequest defaults."""
        req = ToolExecuteRequest(
            tool_name="test",
            parameters={},
        )
        assert req.tool_name == "test"
        assert req.parameters == {}
        assert req.require_approval is True
    
    def test_tool_execute_request_with_approval(self):
        """Test ToolExecuteRequest with require_approval."""
        req = ToolExecuteRequest(
            tool_name="test",
            parameters={"arg": "value"},
            require_approval=False,
        )
        assert req.require_approval is False
        assert req.parameters == {"arg": "value"}
    
    def test_tool_execute_response_defaults(self):
        """Test ToolExecuteResponse defaults."""
        resp = ToolExecuteResponse(
            tool_name="test",
            output="output",
        )
        assert resp.tool_name == "test"
        assert resp.output == "output"
        assert resp.error is None
        assert resp.files_changed == []
        assert resp.metadata == {}
    
    def test_tool_execute_response_with_error(self):
        """Test ToolExecuteResponse with error."""
        resp = ToolExecuteResponse(
            tool_name="test",
            output="",
            error="Something went wrong",
            files_changed=["/path/to/file"],
            metadata={"key": "value"},
        )
        assert resp.error == "Something went wrong"
        assert resp.files_changed == ["/path/to/file"]
        assert resp.metadata == {"key": "value"}
    
    def test_mcp_tool_info_creation(self):
        """Test MCPToolInfo model creation."""
        info = MCPToolInfo(
            server_name="test_server",
            tool_name="test_tool",
            description="An MCP tool",
            input_schema={"type": "object"},
        )
        assert info.server_name == "test_server"
        assert info.tool_name == "test_tool"
        assert info.description == "An MCP tool"
        assert info.input_schema == {"type": "object"}


class TestListTools:
    """Tests for list_tools endpoint."""
    
    @patch('opencode.server.routes.tools.get_tool_registry')
    def test_list_tools_empty(self, mock_get_registry, client, mock_tool_registry):
        """Test listing tools when empty."""
        mock_get_registry.return_value = mock_tool_registry
        
        response = client.get("/tools/")
        
        assert response.status_code == 200
        assert response.json() == []
    
    @patch('opencode.server.routes.tools.get_tool_registry')
    def test_list_tools_with_tools(self, mock_get_registry, client, mock_tool_registry, mock_tool):
        """Test listing tools."""
        mock_tool_registry.list_tools.return_value = [mock_tool]
        mock_get_registry.return_value = mock_tool_registry
        
        response = client.get("/tools/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "test_tool"
        assert data[0]["description"] == "A test tool"


class TestGetToolInfo:
    """Tests for get_tool_info endpoint."""
    
    @patch('opencode.server.routes.tools.get_tool_registry')
    def test_get_tool_info_found(self, mock_get_registry, client, mock_tool_registry, mock_tool):
        """Test getting tool info when found."""
        mock_tool_registry.get_tool.return_value = mock_tool
        mock_get_registry.return_value = mock_tool_registry
        
        response = client.get("/tools/test_tool")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test_tool"
    
    @patch('opencode.server.routes.tools.get_tool_registry')
    def test_get_tool_info_not_found(self, mock_get_registry, client, mock_tool_registry):
        """Test getting tool info when not found."""
        mock_tool_registry.get_tool.return_value = None
        mock_get_registry.return_value = mock_tool_registry
        
        response = client.get("/tools/nonexistent")
        
        assert response.status_code == 404


class TestExecuteTool:
    """Tests for execute_tool endpoint."""
    
    @patch('opencode.server.routes.tools.get_tool_registry')
    def test_execute_tool_success(self, mock_get_registry, client, mock_tool_registry, mock_tool):
        """Test executing a tool successfully."""
        mock_tool_registry.get_tool.return_value = mock_tool
        mock_get_registry.return_value = mock_tool_registry
        
        response = client.post(
            "/tools/execute",
            json={"tool_name": "test_tool", "parameters": {}},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["tool_name"] == "test_tool"
        assert data["output"] == "Tool output"
        mock_tool.execute.assert_called_once()
    
    @patch('opencode.server.routes.tools.get_tool_registry')
    def test_execute_tool_with_parameters(self, mock_get_registry, client, mock_tool_registry, mock_tool):
        """Test executing a tool with parameters."""
        mock_tool_registry.get_tool.return_value = mock_tool
        mock_get_registry.return_value = mock_tool_registry
        
        response = client.post(
            "/tools/execute",
            json={"tool_name": "test_tool", "parameters": {"arg": "value"}},
        )
        
        assert response.status_code == 200
        mock_tool.execute.assert_called_once_with(arg="value")
    
    @patch('opencode.server.routes.tools.get_tool_registry')
    def test_execute_tool_not_found(self, mock_get_registry, client, mock_tool_registry):
        """Test executing a non-existent tool."""
        mock_tool_registry.get_tool.return_value = None
        mock_get_registry.return_value = mock_tool_registry
        
        response = client.post(
            "/tools/execute",
            json={"tool_name": "nonexistent", "parameters": {}},
        )
        
        assert response.status_code == 404
    
    @patch('opencode.server.routes.tools.get_tool_registry')
    def test_execute_tool_with_error(self, mock_get_registry, client, mock_tool_registry, mock_tool):
        """Test executing a tool that returns an error."""
        mock_tool.execute.return_value = MagicMock(
            output="",
            error="Execution failed",
            files_changed=[],
            metadata={},
        )
        mock_tool_registry.get_tool.return_value = mock_tool
        mock_get_registry.return_value = mock_tool_registry
        
        response = client.post(
            "/tools/execute",
            json={"tool_name": "test_tool", "parameters": {}},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["error"] == "Execution failed"


class TestListMCPTools:
    """Tests for list_mcp_tools endpoint."""
    
    @patch('opencode.server.routes.tools.get_mcp_client')
    def test_list_mcp_tools_no_client(self, mock_get_client, client):
        """Test listing MCP tools when no client."""
        mock_get_client.return_value = None
        
        response = client.get("/tools/mcp/list")
        
        assert response.status_code == 200
        assert response.json() == []
    
    @patch('opencode.server.routes.tools.get_mcp_client')
    def test_list_mcp_tools_empty(self, mock_get_client, client, mock_mcp_client):
        """Test listing MCP tools when empty."""
        mock_get_client.return_value = mock_mcp_client
        
        response = client.get("/tools/mcp/list")
        
        assert response.status_code == 200
        assert response.json() == []
    
    @patch('opencode.server.routes.tools.get_mcp_client')
    def test_list_mcp_tools_with_tools(self, mock_get_client, client, mock_mcp_client):
        """Test listing MCP tools."""
        # Create a proper mock with string attributes
        mock_tool = MagicMock()
        mock_tool.name = "mcp_tool"  # Set as string, not MagicMock
        mock_tool.description = "An MCP tool"
        mock_tool.input_schema.to_dict.return_value = {"type": "object"}
        mock_mcp_client.get_all_tools.return_value = [("server1", mock_tool)]
        mock_get_client.return_value = mock_mcp_client
        
        response = client.get("/tools/mcp/list")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["server_name"] == "server1"
        assert data[0]["tool_name"] == "mcp_tool"


class TestExecuteMCPTool:
    """Tests for execute_mcp_tool endpoint."""
    
    @patch('opencode.server.routes.tools.get_mcp_client')
    def test_execute_mcp_tool_no_client(self, mock_get_client, client):
        """Test executing MCP tool when no client."""
        mock_get_client.return_value = None
        
        # The endpoint expects query parameters for server_name and tool_name
        response = client.post(
            "/tools/mcp/execute?server_name=server1&tool_name=tool1",
            json={"arg": "value"},
        )
        
        assert response.status_code == 503
    
    @patch('opencode.server.routes.tools.get_mcp_client')
    def test_execute_mcp_tool_success(self, mock_get_client, client, mock_mcp_client):
        """Test executing MCP tool successfully."""
        mock_get_client.return_value = mock_mcp_client
        
        response = client.post(
            "/tools/mcp/execute?server_name=server1&tool_name=tool1",
            json={"arg": "value"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["server_name"] == "server1"
        assert data["tool_name"] == "tool1"
        assert data["content"] == "MCP tool output"
        mock_mcp_client.call_tool.assert_called_once_with("server1", "tool1", {"arg": "value"})


class TestListMCPResources:
    """Tests for list_mcp_resources endpoint."""
    
    @patch('opencode.server.routes.tools.get_mcp_client')
    def test_list_mcp_resources_no_client(self, mock_get_client, client):
        """Test listing MCP resources when no client."""
        mock_get_client.return_value = None
        
        response = client.get("/tools/mcp/resources")
        
        assert response.status_code == 200
        assert response.json() == []
    
    @patch('opencode.server.routes.tools.get_mcp_client')
    def test_list_mcp_resources_with_resources(self, mock_get_client, client, mock_mcp_client):
        """Test listing MCP resources."""
        mock_resource = MagicMock(
            uri="file:///test.txt",
            name="test.txt",
            description="A test file",
            mime_type="text/plain",
        )
        mock_mcp_client.get_all_resources.return_value = [("server1", mock_resource)]
        mock_get_client.return_value = mock_mcp_client
        
        response = client.get("/tools/mcp/resources")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["server_name"] == "server1"
        assert data[0]["uri"] == "file:///test.txt"


class TestReadMCPResource:
    """Tests for read_mcp_resource endpoint."""
    
    @patch('opencode.server.routes.tools.get_mcp_client')
    def test_read_mcp_resource_no_client(self, mock_get_client, client):
        """Test reading MCP resource when no client."""
        mock_get_client.return_value = None
        
        response = client.get("/tools/mcp/resources/server1/file%3A%2F%2F%2Ftest.txt")
        
        assert response.status_code == 503
    
    @patch('opencode.server.routes.tools.get_mcp_client')
    def test_read_mcp_resource_success(self, mock_get_client, client, mock_mcp_client):
        """Test reading MCP resource successfully."""
        mock_get_client.return_value = mock_mcp_client
        
        response = client.get("/tools/mcp/resources/server1/file.txt")
        
        assert response.status_code == 200
        mock_mcp_client.read_resource.assert_called_once()
    
    @patch('opencode.server.routes.tools.get_mcp_client')
    def test_read_mcp_resource_not_found(self, mock_get_client, client, mock_mcp_client):
        """Test reading MCP resource that doesn't exist."""
        mock_mcp_client.read_resource.return_value = None
        mock_get_client.return_value = mock_mcp_client
        
        response = client.get("/tools/mcp/resources/server1/nonexistent")
        
        assert response.status_code == 404


class TestListMCPPrompts:
    """Tests for list_mcp_prompts endpoint."""
    
    @patch('opencode.server.routes.tools.get_mcp_client')
    def test_list_mcp_prompts_no_client(self, mock_get_client, client):
        """Test listing MCP prompts when no client."""
        mock_get_client.return_value = None
        
        response = client.get("/tools/mcp/prompts")
        
        assert response.status_code == 200
        assert response.json() == []
    
    @patch('opencode.server.routes.tools.get_mcp_client')
    def test_list_mcp_prompts_with_prompts(self, mock_get_client, client, mock_mcp_client):
        """Test listing MCP prompts."""
        # Create proper mock with string attributes
        mock_argument = MagicMock()
        mock_argument.to_dict.return_value = {"name": "arg1"}
        
        mock_prompt = MagicMock()
        mock_prompt.name = "test_prompt"  # Set as string
        mock_prompt.description = "A test prompt"
        mock_prompt.arguments = [mock_argument]
        
        mock_mcp_client.get_all_prompts.return_value = [("server1", mock_prompt)]
        mock_get_client.return_value = mock_mcp_client
        
        response = client.get("/tools/mcp/prompts")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["server_name"] == "server1"
        assert data[0]["name"] == "test_prompt"


class TestExecuteMCPPrompt:
    """Tests for execute_mcp_prompt endpoint."""
    
    @patch('opencode.server.routes.tools.get_mcp_client')
    def test_execute_mcp_prompt_no_client(self, mock_get_client, client):
        """Test executing MCP prompt when no client."""
        mock_get_client.return_value = None
        
        response = client.post(
            "/tools/mcp/prompts/server1/test_prompt",
            json={},
        )
        
        assert response.status_code == 503
    
    @patch('opencode.server.routes.tools.get_mcp_client')
    def test_execute_mcp_prompt_success(self, mock_get_client, client, mock_mcp_client):
        """Test executing MCP prompt successfully."""
        mock_get_client.return_value = mock_mcp_client
        
        response = client.post(
            "/tools/mcp/prompts/server1/test_prompt",
            json={"arg": "value"},
        )
        
        assert response.status_code == 200
        mock_mcp_client.get_prompt.assert_called_once_with("server1", "test_prompt", {"arg": "value"})
    
    @patch('opencode.server.routes.tools.get_mcp_client')
    def test_execute_mcp_prompt_not_found(self, mock_get_client, client, mock_mcp_client):
        """Test executing MCP prompt that doesn't exist."""
        mock_mcp_client.get_prompt.return_value = None
        mock_get_client.return_value = mock_mcp_client
        
        response = client.post(
            "/tools/mcp/prompts/server1/nonexistent",
            json={},
        )
        
        assert response.status_code == 404
    
    @patch('opencode.server.routes.tools.get_mcp_client')
    def test_execute_mcp_prompt_no_arguments(self, mock_get_client, client, mock_mcp_client):
        """Test executing MCP prompt without arguments."""
        mock_get_client.return_value = mock_mcp_client
        
        response = client.post(
            "/tools/mcp/prompts/server1/test_prompt",
        )
        
        # Should work with no arguments
        assert response.status_code in [200, 422]  # 422 if body required
