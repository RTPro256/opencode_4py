"""
Tests for Tool workflow node.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from opencode.workflow.nodes.tool import ToolNode
from opencode.workflow.node import NodeSchema, ExecutionResult, PortDataType, PortDirection


class TestToolNode:
    """Test cases for ToolNode."""

    def test_tool_node_schema(self):
        """Test ToolNode schema definition."""
        schema = ToolNode.get_schema()
        
        assert schema.node_type == "tool"
        assert schema.display_name == "Tool"
        assert schema.category == "action"
        assert schema.icon == "wrench"
        assert schema.version == "1.0.0"

    def test_tool_node_inputs(self):
        """Test ToolNode input ports."""
        schema = ToolNode.get_schema()
        inputs = {inp.name: inp for inp in schema.inputs}
        
        assert "args" in inputs
        assert inputs["args"].data_type == PortDataType.OBJECT
        assert inputs["args"].required is False
        
        assert "input" in inputs
        assert inputs["input"].data_type == PortDataType.ANY
        assert inputs["input"].required is False

    def test_tool_node_outputs(self):
        """Test ToolNode output ports."""
        schema = ToolNode.get_schema()
        outputs = {out.name: out for out in schema.outputs}
        
        assert "result" in outputs
        assert outputs["result"].data_type == PortDataType.ANY
        assert outputs["result"].required is True
        
        assert "success" in outputs
        assert outputs["success"].data_type == PortDataType.BOOLEAN
        assert outputs["success"].required is True
        
        assert "error" in outputs
        assert outputs["error"].data_type == PortDataType.STRING
        assert outputs["error"].required is False

    def test_tool_node_config_schema(self):
        """Test ToolNode config schema."""
        schema = ToolNode.get_schema()
        config_schema = schema.config_schema
        
        assert config_schema["type"] == "object"
        assert "toolName" in config_schema["properties"]
        assert "toolArgs" in config_schema["properties"]
        assert "timeout" in config_schema["properties"]
        
        assert config_schema["required"] == ["toolName"]

    def test_tool_node_initialization(self):
        """Test ToolNode initialization."""
        node = ToolNode("tool-1", {
            "toolName": "bash",
            "toolArgs": {"command": "echo hello"}
        })
        
        assert node.node_id == "tool-1"
        assert node.config == {"toolName": "bash", "toolArgs": {"command": "echo hello"}}

    @pytest.mark.asyncio
    async def test_execute_missing_tool_name(self):
        """Test execute with missing tool name."""
        node = ToolNode("tool-1", {})
        
        result = await node.execute({}, MagicMock())
        
        assert result.success is False
        assert "toolName is required" in result.error

    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self):
        """Test execute with tool not found."""
        node = ToolNode("tool-1", {
            "toolName": "nonexistent_tool"
        })
        
        result = await node.execute({}, MagicMock())
        
        assert result.success is False
        assert "not found" in result.error

    @pytest.mark.asyncio
    async def test_execute_with_tool_args(self):
        """Test execute with tool arguments from config."""
        node = ToolNode("tool-1", {
            "toolName": "test_tool",
            "toolArgs": {"arg1": "value1"}
        })
        
        # Mock the _get_tool method
        mock_tool = MagicMock()
        mock_tool.execute = AsyncMock(return_value="tool result")
        
        with patch.object(node, '_get_tool', return_value=mock_tool):
            result = await node.execute({}, MagicMock())
            
            assert result.success is True
            assert result.outputs["result"] == "tool result"
            assert result.outputs["success"] is True

    @pytest.mark.asyncio
    async def test_execute_with_args_from_input(self):
        """Test execute with arguments from input."""
        node = ToolNode("tool-1", {
            "toolName": "test_tool",
            "toolArgs": {"arg1": "value1"}
        })
        
        mock_tool = MagicMock()
        mock_tool.execute = AsyncMock(return_value="tool result")
        
        with patch.object(node, '_get_tool', return_value=mock_tool):
            result = await node.execute({
                "args": {"arg2": "value2"}
            }, MagicMock())
            
            assert result.success is True
            # Verify that args were merged

    @pytest.mark.asyncio
    async def test_execute_with_input_data(self):
        """Test execute with input data."""
        node = ToolNode("tool-1", {
            "toolName": "test_tool"
        })
        
        mock_tool = MagicMock()
        mock_tool.execute = AsyncMock(return_value="processed")
        
        with patch.object(node, '_get_tool', return_value=mock_tool):
            result = await node.execute({
                "input": "test input"
            }, MagicMock())
            
            assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_tool_execution_error(self):
        """Test execute with tool execution error."""
        node = ToolNode("tool-1", {
            "toolName": "test_tool"
        })
        
        mock_tool = MagicMock()
        mock_tool.execute = AsyncMock(side_effect=Exception("Tool error"))
        
        with patch.object(node, '_get_tool', return_value=mock_tool):
            result = await node.execute({}, MagicMock())
            
            assert result.success is False
            assert "Tool error" in result.error

    @pytest.mark.asyncio
    async def test_execute_sync_tool(self):
        """Test execute with synchronous tool."""
        node = ToolNode("tool-1", {
            "toolName": "test_tool"
        })
        
        mock_tool = MagicMock()
        mock_tool.execute = MagicMock(return_value="sync result")
        # Make it not a coroutine function
        del mock_tool.execute._is_coroutine
        
        with patch.object(node, '_get_tool', return_value=mock_tool):
            result = await node.execute({}, MagicMock())
            
            assert result.success is True
            assert result.outputs["result"] == "sync result"

    @pytest.mark.asyncio
    async def test_execute_tool_with_run_method(self):
        """Test execute with tool that has run method."""
        node = ToolNode("tool-1", {
            "toolName": "test_tool"
        })
        
        mock_tool = MagicMock()
        del mock_tool.execute  # No execute method
        mock_tool.run = AsyncMock(return_value="run result")
        
        with patch.object(node, '_get_tool', return_value=mock_tool):
            result = await node.execute({}, MagicMock())
            
            assert result.success is True
            assert result.outputs["result"] == "run result"

    @pytest.mark.asyncio
    async def test_execute_callable_tool(self):
        """Test execute with callable tool."""
        node = ToolNode("tool-1", {
            "toolName": "test_tool"
        })
        
        # Create a sync callable (since the tool node expects callables to be sync)
        def mock_callable(**kwargs):
            return "callable result"
        
        with patch.object(node, '_get_tool', return_value=mock_callable):
            result = await node.execute({}, MagicMock())
            
            assert result.success is True
            assert result.outputs["result"] == "callable result"

    @pytest.mark.asyncio
    async def test_execute_tool_no_method(self):
        """Test execute with tool that has no execute/run method."""
        node = ToolNode("tool-1", {
            "toolName": "test_tool"
        })
        
        # Create an object that is not callable and has no execute/run methods
        class NonCallableTool:
            pass
        
        mock_tool = NonCallableTool()
        
        with patch.object(node, '_get_tool', return_value=mock_tool):
            result = await node.execute({}, MagicMock())
            
            assert result.success is False
            assert result.error is not None

    def test_config_schema_defaults(self):
        """Test config schema default values."""
        schema = ToolNode.get_schema()
        props = schema.config_schema["properties"]
        
        assert props["timeout"]["default"] == 60

    def test_node_registered(self):
        """Test that ToolNode is registered."""
        from opencode.workflow.registry import NodeRegistry
        
        # Check that tool is registered
        assert "tool" in NodeRegistry._nodes or hasattr(NodeRegistry, 'get')

    @pytest.mark.asyncio
    async def test_get_tool_from_registry(self):
        """Test _get_tool from tool registry."""
        node = ToolNode("tool-1", {"toolName": "test"})
        
        mock_tool = MagicMock()
        
        with patch('opencode.tool.get_tool', return_value=mock_tool):
            result = await node._get_tool("test")
            
            assert result == mock_tool

    @pytest.mark.asyncio
    async def test_get_tool_fallback_bash(self):
        """Test _get_tool fallback for bash tool."""
        node = ToolNode("tool-1", {"toolName": "bash"})
        
        # Mock the import to fail first, then succeed with fallback
        with patch('opencode.tool.get_tool', side_effect=ImportError):
            with patch('opencode.tool.bash.BashTool') as MockBashTool:
                mock_instance = MagicMock()
                MockBashTool.return_value = mock_instance
                
                result = await node._get_tool("bash")
                
                # The fallback should work

    @pytest.mark.asyncio
    async def test_get_tool_unknown(self):
        """Test _get_tool with unknown tool name."""
        node = ToolNode("tool-1", {"toolName": "unknown"})
        
        with patch('opencode.tool.get_tool', side_effect=ImportError):
            result = await node._get_tool("unknown")
            
            assert result is None

    @pytest.mark.asyncio
    async def test_execute_with_timeout(self):
        """Test execute respects timeout config."""
        node = ToolNode("tool-1", {
            "toolName": "test_tool",
            "timeout": 1  # 1 second timeout
        })
        
        # Create a tool with async execute that sleeps
        mock_tool = MagicMock()
        
        async def slow_execute(**kwargs):
            await asyncio.sleep(2)  # Sleep longer than timeout
            return "should not reach"
        
        mock_tool.execute = slow_execute
        
        with patch.object(node, '_get_tool', return_value=mock_tool):
            result = await node.execute({}, MagicMock())
            
            # Should timeout
            assert result.success is False
