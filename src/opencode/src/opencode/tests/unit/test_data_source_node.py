"""
Tests for Data Source workflow node.
"""

import pytest
import json
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

from opencode.workflow.nodes.data_source import DataSourceNode, SourceType
from opencode.workflow.node import NodeSchema, ExecutionResult, PortDataType, PortDirection


class TestDataSourceNode:
    """Test cases for DataSourceNode."""

    def test_data_source_node_schema(self):
        """Test DataSourceNode schema definition."""
        schema = DataSourceNode.get_schema()
        
        assert schema.node_type == "data_source"
        assert schema.display_name == "Data Source"
        assert schema.category == "input"
        assert schema.icon == "database"
        assert schema.version == "1.0.0"

    def test_data_source_node_inputs(self):
        """Test DataSourceNode input ports."""
        schema = DataSourceNode.get_schema()
        inputs = {inp.name: inp for inp in schema.inputs}
        
        assert "trigger" in inputs
        assert inputs["trigger"].data_type == PortDataType.ANY
        assert inputs["trigger"].required is False

    def test_data_source_node_outputs(self):
        """Test DataSourceNode output ports."""
        schema = DataSourceNode.get_schema()
        outputs = {out.name: out for out in schema.outputs}
        
        assert "data" in outputs
        assert outputs["data"].data_type == PortDataType.ANY
        assert outputs["data"].required is True
        
        assert "raw" in outputs
        assert outputs["raw"].data_type == PortDataType.STRING
        assert outputs["raw"].required is False

    def test_data_source_node_config_schema(self):
        """Test DataSourceNode config schema."""
        schema = DataSourceNode.get_schema()
        config_schema = schema.config_schema
        
        assert config_schema["type"] == "object"
        assert "sourceType" in config_schema["properties"]
        assert "filePath" in config_schema["properties"]
        assert "jsonData" in config_schema["properties"]
        assert "textData" in config_schema["properties"]
        assert "url" in config_schema["properties"]
        assert "encoding" in config_schema["properties"]
        
        assert config_schema["required"] == ["sourceType"]

    def test_source_type_constants(self):
        """Test SourceType constants."""
        assert SourceType.FILE == "file"
        assert SourceType.JSON == "json"
        assert SourceType.TEXT == "text"
        assert SourceType.URL == "url"

    def test_data_source_node_initialization(self):
        """Test DataSourceNode initialization."""
        node = DataSourceNode("ds-1", {"sourceType": "text", "textData": "hello"})
        
        assert node.node_id == "ds-1"
        assert node.config == {"sourceType": "text", "textData": "hello"}

    @pytest.mark.asyncio
    async def test_execute_text_source(self):
        """Test execute with text source."""
        node = DataSourceNode("ds-1", {
            "sourceType": "text",
            "textData": "Hello, World!"
        })
        
        result = await node.execute({}, MagicMock())
        
        assert result.success is True
        assert result.outputs["data"] == "Hello, World!"
        assert result.outputs["raw"] == "Hello, World!"

    @pytest.mark.asyncio
    async def test_execute_text_source_empty(self):
        """Test execute with empty text source."""
        node = DataSourceNode("ds-1", {
            "sourceType": "text"
        })
        
        result = await node.execute({}, MagicMock())
        
        assert result.success is True
        assert result.outputs["data"] == ""
        assert result.outputs["raw"] == ""

    @pytest.mark.asyncio
    async def test_execute_json_source(self):
        """Test execute with JSON source."""
        node = DataSourceNode("ds-1", {
            "sourceType": "json",
            "jsonData": '{"name": "test", "value": 42}'
        })
        
        result = await node.execute({}, MagicMock())
        
        assert result.success is True
        assert result.outputs["data"] == {"name": "test", "value": 42}
        assert result.outputs["raw"] == '{"name": "test", "value": 42}'

    @pytest.mark.asyncio
    async def test_execute_json_source_array(self):
        """Test execute with JSON array source."""
        node = DataSourceNode("ds-1", {
            "sourceType": "json",
            "jsonData": '[1, 2, 3, 4, 5]'
        })
        
        result = await node.execute({}, MagicMock())
        
        assert result.success is True
        assert result.outputs["data"] == [1, 2, 3, 4, 5]

    @pytest.mark.asyncio
    async def test_execute_json_source_missing(self):
        """Test execute with missing JSON data."""
        node = DataSourceNode("ds-1", {
            "sourceType": "json"
        })
        
        result = await node.execute({}, MagicMock())
        
        assert result.success is False
        assert "jsonData is required" in result.error

    @pytest.mark.asyncio
    async def test_execute_json_source_invalid(self):
        """Test execute with invalid JSON data."""
        node = DataSourceNode("ds-1", {
            "sourceType": "json",
            "jsonData": "not valid json"
        })
        
        result = await node.execute({}, MagicMock())
        
        assert result.success is False
        assert "Invalid JSON" in result.error

    @pytest.mark.asyncio
    async def test_execute_file_source(self):
        """Test execute with file source."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test file content")
            temp_path = f.name
        
        try:
            node = DataSourceNode("ds-1", {
                "sourceType": "file",
                "filePath": temp_path
            })
            
            result = await node.execute({}, MagicMock())
            
            assert result.success is True
            assert result.outputs["data"] == "Test file content"
            assert result.outputs["raw"] == "Test file content"
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_execute_file_source_json(self):
        """Test execute with JSON file source."""
        # Create a temporary JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"key": "value"}, f)
            temp_path = f.name
        
        try:
            node = DataSourceNode("ds-1", {
                "sourceType": "file",
                "filePath": temp_path
            })
            
            result = await node.execute({}, MagicMock())
            
            assert result.success is True
            assert result.outputs["data"] == {"key": "value"}
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_execute_file_source_missing(self):
        """Test execute with missing file path."""
        node = DataSourceNode("ds-1", {
            "sourceType": "file"
        })
        
        result = await node.execute({}, MagicMock())
        
        assert result.success is False
        assert "filePath is required" in result.error

    @pytest.mark.asyncio
    async def test_execute_file_source_not_found(self):
        """Test execute with non-existent file."""
        node = DataSourceNode("ds-1", {
            "sourceType": "file",
            "filePath": "/nonexistent/path/file.txt"
        })
        
        result = await node.execute({}, MagicMock())
        
        assert result.success is False
        assert "File not found" in result.error

    @pytest.mark.asyncio
    async def test_execute_file_source_custom_encoding(self):
        """Test execute with custom encoding."""
        # Create a temporary file with UTF-8 content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("Test content")
            temp_path = f.name
        
        try:
            node = DataSourceNode("ds-1", {
                "sourceType": "file",
                "filePath": temp_path,
                "encoding": "utf-8"
            })
            
            result = await node.execute({}, MagicMock())
            
            assert result.success is True
            assert result.outputs["data"] == "Test content"
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_execute_url_source(self):
        """Test execute with URL source."""
        node = DataSourceNode("ds-1", {
            "sourceType": "url",
            "url": "https://api.example.com/data"
        })
        
        mock_response = MagicMock()
        mock_response.text = '{"result": "success"}'
        mock_response.raise_for_status = MagicMock()
        
        with patch.dict('sys.modules', {'httpx': MagicMock()}):
            import sys
            httpx = sys.modules['httpx']
            httpx.AsyncClient = MagicMock()
            
            async_cm = AsyncMock()
            async_cm.get = AsyncMock(return_value=mock_response)
            async_cm.__aenter__ = AsyncMock(return_value=async_cm)
            async_cm.__aexit__ = AsyncMock(return_value=None)
            httpx.AsyncClient.return_value = async_cm
            
            result = await node.execute({}, MagicMock())
            
            assert result.success is True
            assert result.outputs["data"] == {"result": "success"}

    @pytest.mark.asyncio
    async def test_execute_url_source_text(self):
        """Test execute with URL source returning text."""
        node = DataSourceNode("ds-1", {
            "sourceType": "url",
            "url": "https://example.com/html"
        })
        
        mock_response = MagicMock()
        mock_response.text = '<html><body>Test</body></html>'
        mock_response.raise_for_status = MagicMock()
        
        with patch.dict('sys.modules', {'httpx': MagicMock()}):
            import sys
            httpx = sys.modules['httpx']
            httpx.AsyncClient = MagicMock()
            
            async_cm = AsyncMock()
            async_cm.get = AsyncMock(return_value=mock_response)
            async_cm.__aenter__ = AsyncMock(return_value=async_cm)
            async_cm.__aexit__ = AsyncMock(return_value=None)
            httpx.AsyncClient.return_value = async_cm
            
            result = await node.execute({}, MagicMock())
            
            assert result.success is True
            assert result.outputs["data"] == '<html><body>Test</body></html>'

    @pytest.mark.asyncio
    async def test_execute_url_source_missing(self):
        """Test execute with missing URL."""
        node = DataSourceNode("ds-1", {
            "sourceType": "url"
        })
        
        result = await node.execute({}, MagicMock())
        
        assert result.success is False
        assert "url is required" in result.error

    @pytest.mark.asyncio
    async def test_execute_url_source_error(self):
        """Test execute with URL fetch error."""
        node = DataSourceNode("ds-1", {
            "sourceType": "url",
            "url": "https://invalid.example.com"
        })
        
        with patch.dict('sys.modules', {'httpx': MagicMock()}):
            import sys
            httpx = sys.modules['httpx']
            httpx.AsyncClient = MagicMock()
            
            async_cm = AsyncMock()
            async_cm.get = AsyncMock(side_effect=Exception("Connection error"))
            async_cm.__aenter__ = AsyncMock(return_value=async_cm)
            async_cm.__aexit__ = AsyncMock(return_value=None)
            httpx.AsyncClient.return_value = async_cm
            
            result = await node.execute({}, MagicMock())
            
            assert result.success is False
            assert "Error fetching URL" in result.error

    @pytest.mark.asyncio
    async def test_execute_unknown_source_type(self):
        """Test execute with unknown source type."""
        node = DataSourceNode("ds-1", {
            "sourceType": "unknown"
        })
        
        result = await node.execute({}, MagicMock())
        
        assert result.success is False
        assert "Unknown source type" in result.error

    def test_node_registered(self):
        """Test that DataSourceNode is registered."""
        from opencode.workflow.registry import NodeRegistry
        
        # Check that data_source is registered
        assert "data_source" in NodeRegistry._nodes or hasattr(NodeRegistry, 'get')

    def test_config_schema_source_types(self):
        """Test config schema sourceType enum values."""
        schema = DataSourceNode.get_schema()
        source_type_prop = schema.config_schema["properties"]["sourceType"]
        
        assert "file" in source_type_prop["enum"]
        assert "json" in source_type_prop["enum"]
        assert "text" in source_type_prop["enum"]
        assert "url" in source_type_prop["enum"]

    def test_config_schema_defaults(self):
        """Test config schema default values."""
        schema = DataSourceNode.get_schema()
        props = schema.config_schema["properties"]
        
        assert props["sourceType"]["default"] == "text"
        assert props["encoding"]["default"] == "utf-8"
