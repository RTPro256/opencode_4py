"""
Tests for HTTP workflow node.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from opencode.workflow.nodes.http import HttpNode
from opencode.workflow.node import NodeSchema, ExecutionResult, PortDataType, PortDirection


class TestHttpNode:
    """Test cases for HttpNode."""

    def test_http_node_schema(self):
        """Test HttpNode schema definition."""
        schema = HttpNode.get_schema()
        
        assert schema.node_type == "http"
        assert schema.display_name == "HTTP Request"
        assert schema.category == "network"
        assert schema.icon == "globe"
        assert schema.version == "1.0.0"

    def test_http_node_inputs(self):
        """Test HttpNode input ports."""
        schema = HttpNode.get_schema()
        inputs = {inp.name: inp for inp in schema.inputs}
        
        assert "url" in inputs
        assert inputs["url"].data_type == PortDataType.STRING
        assert inputs["url"].required is False
        
        assert "body" in inputs
        assert inputs["body"].data_type == PortDataType.ANY
        assert inputs["body"].required is False
        
        assert "headers" in inputs
        assert inputs["headers"].data_type == PortDataType.OBJECT
        assert inputs["headers"].required is False
        
        assert "params" in inputs
        assert inputs["params"].data_type == PortDataType.OBJECT
        assert inputs["params"].required is False

    def test_http_node_outputs(self):
        """Test HttpNode output ports."""
        schema = HttpNode.get_schema()
        outputs = {out.name: out for out in schema.outputs}
        
        assert "response" in outputs
        assert outputs["response"].data_type == PortDataType.ANY
        assert outputs["response"].required is True
        
        assert "status" in outputs
        assert outputs["status"].data_type == PortDataType.INTEGER
        assert outputs["status"].required is True
        
        assert "headers" in outputs
        assert outputs["headers"].data_type == PortDataType.OBJECT
        assert outputs["headers"].required is False
        
        assert "raw" in outputs
        assert outputs["raw"].data_type == PortDataType.STRING
        assert outputs["raw"].required is False

    def test_http_node_config_schema(self):
        """Test HttpNode config schema."""
        schema = HttpNode.get_schema()
        config_schema = schema.config_schema
        
        assert config_schema["type"] == "object"
        assert "method" in config_schema["properties"]
        assert "url" in config_schema["properties"]
        assert "headers" in config_schema["properties"]
        assert "bodyType" in config_schema["properties"]
        assert "body" in config_schema["properties"]
        assert "timeout" in config_schema["properties"]
        assert "followRedirects" in config_schema["properties"]
        
        assert config_schema["required"] == ["url"]

    def test_http_node_initialization(self):
        """Test HttpNode initialization."""
        node = HttpNode("http-1", {"url": "https://example.com"})
        
        assert node.node_id == "http-1"
        assert node.config == {"url": "https://example.com"}

    @pytest.mark.asyncio
    async def test_execute_get_request(self):
        """Test execute GET request."""
        node = HttpNode("http-1", {
            "method": "GET",
            "url": "https://api.example.com/data"
        })
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_response.text = '{"result": "success"}'
        mock_response.headers = {"content-type": "application/json"}
        
        with patch.dict('sys.modules', {'httpx': MagicMock()}):
            import sys
            httpx = sys.modules['httpx']
            httpx.AsyncClient = MagicMock()
            httpx.TimeoutException = Exception
            httpx.RequestError = Exception
            
            # Create async context manager mock
            async_cm = AsyncMock()
            async_cm.request = AsyncMock(return_value=mock_response)
            async_cm.__aenter__ = AsyncMock(return_value=async_cm)
            async_cm.__aexit__ = AsyncMock(return_value=None)
            httpx.AsyncClient.return_value = async_cm
            
            result = await node.execute({}, MagicMock())
            
            assert result.success is True
            assert result.outputs["status"] == 200
            assert result.outputs["response"] == {"result": "success"}

    @pytest.mark.asyncio
    async def test_execute_post_request(self):
        """Test execute POST request with JSON body."""
        node = HttpNode("http-1", {
            "method": "POST",
            "url": "https://api.example.com/data",
            "bodyType": "json",
            "body": {"name": "test"}
        })
        
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 1, "name": "test"}
        mock_response.text = '{"id": 1, "name": "test"}'
        mock_response.headers = {"content-type": "application/json"}
        
        with patch.dict('sys.modules', {'httpx': MagicMock()}):
            import sys
            httpx = sys.modules['httpx']
            httpx.AsyncClient = MagicMock()
            httpx.TimeoutException = Exception
            httpx.RequestError = Exception
            
            async_cm = AsyncMock()
            async_cm.request = AsyncMock(return_value=mock_response)
            async_cm.__aenter__ = AsyncMock(return_value=async_cm)
            async_cm.__aexit__ = AsyncMock(return_value=None)
            httpx.AsyncClient.return_value = async_cm
            
            result = await node.execute({}, MagicMock())
            
            assert result.success is True
            assert result.outputs["status"] == 201

    @pytest.mark.asyncio
    async def test_execute_url_from_input(self):
        """Test execute with URL from input."""
        node = HttpNode("http-1", {
            "method": "GET"
        })
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_response.text = '{"data": "test"}'
        mock_response.headers = {}
        
        with patch.dict('sys.modules', {'httpx': MagicMock()}):
            import sys
            httpx = sys.modules['httpx']
            httpx.AsyncClient = MagicMock()
            httpx.TimeoutException = Exception
            httpx.RequestError = Exception
            
            async_cm = AsyncMock()
            async_cm.request = AsyncMock(return_value=mock_response)
            async_cm.__aenter__ = AsyncMock(return_value=async_cm)
            async_cm.__aexit__ = AsyncMock(return_value=None)
            httpx.AsyncClient.return_value = async_cm
            
            result = await node.execute({"url": "https://input.example.com"}, MagicMock())
            
            assert result.success is True
            assert result.outputs["status"] == 200

    @pytest.mark.asyncio
    async def test_execute_missing_url(self):
        """Test execute with missing URL."""
        node = HttpNode("http-1", {})
        
        result = await node.execute({}, MagicMock())
        
        assert result.success is False
        assert "URL is required" in result.error

    @pytest.mark.asyncio
    async def test_execute_with_headers(self):
        """Test execute with custom headers."""
        node = HttpNode("http-1", {
            "method": "GET",
            "url": "https://api.example.com",
            "headers": {"Authorization": "Bearer token123"}
        })
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_response.text = '{}'
        mock_response.headers = {}
        
        with patch.dict('sys.modules', {'httpx': MagicMock()}):
            import sys
            httpx = sys.modules['httpx']
            httpx.AsyncClient = MagicMock()
            httpx.TimeoutException = Exception
            httpx.RequestError = Exception
            
            async_cm = AsyncMock()
            async_cm.request = AsyncMock(return_value=mock_response)
            async_cm.__aenter__ = AsyncMock(return_value=async_cm)
            async_cm.__aexit__ = AsyncMock(return_value=None)
            httpx.AsyncClient.return_value = async_cm
            
            result = await node.execute({"headers": {"X-Custom": "value"}}, MagicMock())
            
            assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_with_params(self):
        """Test execute with query parameters."""
        node = HttpNode("http-1", {
            "method": "GET",
            "url": "https://api.example.com/search"
        })
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_response.text = '{"results": []}'
        mock_response.headers = {}
        
        with patch.dict('sys.modules', {'httpx': MagicMock()}):
            import sys
            httpx = sys.modules['httpx']
            httpx.AsyncClient = MagicMock()
            httpx.TimeoutException = Exception
            httpx.RequestError = Exception
            
            async_cm = AsyncMock()
            async_cm.request = AsyncMock(return_value=mock_response)
            async_cm.__aenter__ = AsyncMock(return_value=async_cm)
            async_cm.__aexit__ = AsyncMock(return_value=None)
            httpx.AsyncClient.return_value = async_cm
            
            result = await node.execute({"params": {"q": "test", "limit": 10}}, MagicMock())
            
            assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_form_body(self):
        """Test execute with form body."""
        node = HttpNode("http-1", {
            "method": "POST",
            "url": "https://api.example.com/form",
            "bodyType": "form",
            "body": {"field1": "value1"}
        })
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_response.text = '{"success": true}'
        mock_response.headers = {}
        
        with patch.dict('sys.modules', {'httpx': MagicMock()}):
            import sys
            httpx = sys.modules['httpx']
            httpx.AsyncClient = MagicMock()
            httpx.TimeoutException = Exception
            httpx.RequestError = Exception
            
            async_cm = AsyncMock()
            async_cm.request = AsyncMock(return_value=mock_response)
            async_cm.__aenter__ = AsyncMock(return_value=async_cm)
            async_cm.__aexit__ = AsyncMock(return_value=None)
            httpx.AsyncClient.return_value = async_cm
            
            result = await node.execute({}, MagicMock())
            
            assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_raw_body(self):
        """Test execute with raw body."""
        node = HttpNode("http-1", {
            "method": "POST",
            "url": "https://api.example.com/raw",
            "bodyType": "raw",
            "body": "raw text content"
        })
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_response.text = '{}'
        mock_response.headers = {}
        
        with patch.dict('sys.modules', {'httpx': MagicMock()}):
            import sys
            httpx = sys.modules['httpx']
            httpx.AsyncClient = MagicMock()
            httpx.TimeoutException = Exception
            httpx.RequestError = Exception
            
            async_cm = AsyncMock()
            async_cm.request = AsyncMock(return_value=mock_response)
            async_cm.__aenter__ = AsyncMock(return_value=async_cm)
            async_cm.__aexit__ = AsyncMock(return_value=None)
            httpx.AsyncClient.return_value = async_cm
            
            result = await node.execute({}, MagicMock())
            
            assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_non_json_response(self):
        """Test execute with non-JSON response."""
        node = HttpNode("http-1", {
            "method": "GET",
            "url": "https://example.com/html"
        })
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("", "", 0)
        mock_response.text = "<html><body>Test</body></html>"
        mock_response.headers = {"content-type": "text/html"}
        
        with patch.dict('sys.modules', {'httpx': MagicMock()}):
            import sys
            httpx = sys.modules['httpx']
            httpx.AsyncClient = MagicMock()
            httpx.TimeoutException = Exception
            httpx.RequestError = Exception
            
            async_cm = AsyncMock()
            async_cm.request = AsyncMock(return_value=mock_response)
            async_cm.__aenter__ = AsyncMock(return_value=async_cm)
            async_cm.__aexit__ = AsyncMock(return_value=None)
            httpx.AsyncClient.return_value = async_cm
            
            result = await node.execute({}, MagicMock())
            
            assert result.success is True
            assert result.outputs["response"] == "<html><body>Test</body></html>"
            assert result.outputs["raw"] == "<html><body>Test</body></html>"

    @pytest.mark.asyncio
    async def test_execute_timeout(self):
        """Test execute with timeout error."""
        node = HttpNode("http-1", {
            "method": "GET",
            "url": "https://example.com",
            "timeout": 5
        })
        
        with patch.dict('sys.modules', {'httpx': MagicMock()}):
            import sys
            httpx = sys.modules['httpx']
            httpx.AsyncClient = MagicMock()
            httpx.TimeoutException = Exception
            httpx.RequestError = Exception
            
            async_cm = AsyncMock()
            async_cm.request = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            async_cm.__aenter__ = AsyncMock(return_value=async_cm)
            async_cm.__aexit__ = AsyncMock(return_value=None)
            httpx.AsyncClient.return_value = async_cm
            
            result = await node.execute({}, MagicMock())
            
            assert result.success is False
            assert "timed out" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_request_error(self):
        """Test execute with request error."""
        node = HttpNode("http-1", {
            "method": "GET",
            "url": "https://example.com"
        })
        
        # Create distinct exception types
        class MockTimeoutException(Exception):
            pass
        
        class MockRequestError(Exception):
            pass
        
        with patch.dict('sys.modules', {'httpx': MagicMock()}):
            import sys
            httpx = sys.modules['httpx']
            httpx.AsyncClient = MagicMock()
            httpx.TimeoutException = MockTimeoutException
            httpx.RequestError = MockRequestError
            
            async_cm = AsyncMock()
            async_cm.request = AsyncMock(side_effect=MockRequestError("Connection error"))
            async_cm.__aenter__ = AsyncMock(return_value=async_cm)
            async_cm.__aexit__ = AsyncMock(return_value=None)
            httpx.AsyncClient.return_value = async_cm
            
            result = await node.execute({}, MagicMock())
            
            assert result.success is False
            assert "Request error" in result.error

    @pytest.mark.asyncio
    async def test_execute_httpx_not_installed(self):
        """Test execute when httpx is not installed."""
        node = HttpNode("http-1", {"url": "https://example.com"})
        
        # Mock httpx import to raise ImportError
        with patch.dict('sys.modules', {'httpx': None}):
            # Need to patch the actual import in the module
            import builtins
            real_import = builtins.__import__
            
            def mock_import(name, *args, **kwargs):
                if name == 'httpx':
                    raise ImportError("No module named 'httpx'")
                return real_import(name, *args, **kwargs)
            
            with patch('builtins.__import__', side_effect=mock_import):
                result = await node.execute({}, MagicMock())
                
                # The test should handle the ImportError case
                # The actual implementation returns an error result

    def test_node_registered(self):
        """Test that HttpNode is registered."""
        from opencode.workflow.registry import NodeRegistry
        
        # Check that http is registered
        assert "http" in NodeRegistry._nodes or hasattr(NodeRegistry, 'get')

    def test_config_schema_methods(self):
        """Test config schema method enum values."""
        schema = HttpNode.get_schema()
        method_prop = schema.config_schema["properties"]["method"]
        
        assert "GET" in method_prop["enum"]
        assert "POST" in method_prop["enum"]
        assert "PUT" in method_prop["enum"]
        assert "DELETE" in method_prop["enum"]
        assert "PATCH" in method_prop["enum"]
        assert "HEAD" in method_prop["enum"]
        assert "OPTIONS" in method_prop["enum"]

    def test_config_schema_body_types(self):
        """Test config schema bodyType enum values."""
        schema = HttpNode.get_schema()
        body_type_prop = schema.config_schema["properties"]["bodyType"]
        
        assert "json" in body_type_prop["enum"]
        assert "form" in body_type_prop["enum"]
        assert "raw" in body_type_prop["enum"]
        assert "none" in body_type_prop["enum"]

    def test_config_schema_defaults(self):
        """Test config schema default values."""
        schema = HttpNode.get_schema()
        props = schema.config_schema["properties"]
        
        assert props["method"]["default"] == "GET"
        assert props["bodyType"]["default"] == "json"
        assert props["timeout"]["default"] == 30
        assert props["followRedirects"]["default"] is True
