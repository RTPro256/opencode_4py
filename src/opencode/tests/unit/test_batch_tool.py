"""Tests for BatchTool."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from opencode.tool.batch import BatchTool, BatchResult, DISALLOWED_TOOLS, FILTERED_FROM_SUGGESTIONS
from opencode.tool.base import ToolResult


class TestBatchResult:
    """Tests for BatchResult dataclass."""
    
    def test_batch_result_creation_success(self):
        """Test creating a successful BatchResult."""
        result = BatchResult(
            tool="read",
            success=True,
            output="file contents",
            metadata={"lines": 10}
        )
        assert result.tool == "read"
        assert result.success is True
        assert result.output == "file contents"
        assert result.error is None
        assert result.metadata == {"lines": 10}
    
    def test_batch_result_creation_error(self):
        """Test creating an error BatchResult."""
        result = BatchResult(
            tool="write",
            success=False,
            error="Permission denied"
        )
        assert result.tool == "write"
        assert result.success is False
        assert result.output is None
        assert result.error == "Permission denied"
    
    def test_batch_result_defaults(self):
        """Test BatchResult default values."""
        result = BatchResult(tool="test", success=True)
        assert result.output is None
        assert result.error is None
        assert result.metadata is None


class TestBatchTool:
    """Tests for BatchTool class."""
    
    def test_name(self):
        """Test tool name."""
        tool = BatchTool()
        assert tool.name == "batch"
    
    def test_description(self):
        """Test tool description."""
        tool = BatchTool()
        assert "parallel" in tool.description.lower()
        assert "multiple" in tool.description.lower()
    
    def test_parameters(self):
        """Test tool parameters schema."""
        tool = BatchTool()
        params = tool.parameters
        
        assert params["type"] == "object"
        assert "tool_calls" in params["properties"]
        assert params["required"] == ["tool_calls"]
        
        tool_calls_schema = params["properties"]["tool_calls"]
        assert tool_calls_schema["type"] == "array"
        assert tool_calls_schema["minItems"] == 1
    
    @pytest.mark.asyncio
    async def test_execute_empty_calls(self):
        """Test executing with empty tool calls."""
        tool = BatchTool()
        result = await tool.execute(tool_calls=[])
        
        assert result.success is False
        assert result.error is not None
        assert "at least one tool call" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_execute_disallowed_tool(self):
        """Test executing with disallowed tool."""
        tool = BatchTool()
        
        mock_registry = MagicMock()
        mock_tool = MagicMock()
        mock_tool.name = "batch"
        mock_registry.list_tools.return_value = []
        
        with patch('opencode.tool.batch.get_registry', return_value=mock_registry):
            result = await tool.execute(tool_calls=[{"tool": "batch", "parameters": {}}])
        
        assert result.success is True  # Batch returns success with error details
        assert "batch" in DISALLOWED_TOOLS
    
    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool(self):
        """Test executing with non-existent tool."""
        tool = BatchTool()
        
        mock_registry = MagicMock()
        mock_registry.list_tools.return_value = []
        
        with patch('opencode.tool.batch.get_registry', return_value=mock_registry):
            result = await tool.execute(tool_calls=[{"tool": "nonexistent", "parameters": {}}])
        
        assert result.success is True  # Batch returns success with error details
        output = result.output.lower()
        assert "failed" in output or "nonexistent" in output
    
    @pytest.mark.asyncio
    async def test_execute_successful_tool(self):
        """Test executing a successful tool call."""
        tool = BatchTool()
        
        mock_read_tool = MagicMock()
        mock_read_tool.name = "read"
        mock_read_tool.validate_params.return_value = None
        mock_read_tool.execute = AsyncMock(return_value=ToolResult.ok(output="file contents"))
        
        mock_registry = MagicMock()
        mock_registry.list_tools.return_value = [mock_read_tool]
        
        with patch('opencode.tool.batch.get_registry', return_value=mock_registry):
            result = await tool.execute(
                tool_calls=[{"tool": "read", "parameters": {"path": "test.py"}}]
            )
        
        assert result.success is True
        assert "executed successfully" in result.output.lower() or "success" in result.output.lower()
    
    @pytest.mark.asyncio
    async def test_execute_multiple_tools(self):
        """Test executing multiple tool calls."""
        tool = BatchTool()
        
        mock_read_tool = MagicMock()
        mock_read_tool.name = "read"
        mock_read_tool.validate_params.return_value = None
        mock_read_tool.execute = AsyncMock(return_value=ToolResult.ok(output="contents"))
        
        mock_glob_tool = MagicMock()
        mock_glob_tool.name = "glob"
        mock_glob_tool.validate_params.return_value = None
        mock_glob_tool.execute = AsyncMock(return_value=ToolResult.ok(output="file1.py\nfile2.py"))
        
        mock_registry = MagicMock()
        mock_registry.list_tools.return_value = [mock_read_tool, mock_glob_tool]
        
        with patch('opencode.tool.batch.get_registry', return_value=mock_registry):
            result = await tool.execute(
                tool_calls=[
                    {"tool": "read", "parameters": {"path": "test.py"}},
                    {"tool": "glob", "parameters": {"pattern": "*.py"}}
                ]
            )
        
        assert result.success is True
        assert result.metadata["total_calls"] == 2
        assert result.metadata["successful"] == 2
        assert result.metadata["failed"] == 0
    
    @pytest.mark.asyncio
    async def test_execute_mixed_success_failure(self):
        """Test executing with mixed success and failure."""
        tool = BatchTool()
        
        mock_read_tool = MagicMock()
        mock_read_tool.name = "read"
        mock_read_tool.validate_params.return_value = None
        mock_read_tool.execute = AsyncMock(return_value=ToolResult.ok(output="contents"))
        
        mock_write_tool = MagicMock()
        mock_write_tool.name = "write"
        mock_write_tool.validate_params.return_value = None
        mock_write_tool.execute = AsyncMock(return_value=ToolResult.err("Permission denied"))
        
        mock_registry = MagicMock()
        mock_registry.list_tools.return_value = [mock_read_tool, mock_write_tool]
        
        with patch('opencode.tool.batch.get_registry', return_value=mock_registry):
            result = await tool.execute(
                tool_calls=[
                    {"tool": "read", "parameters": {"path": "test.py"}},
                    {"tool": "write", "parameters": {"path": "test.py", "content": "data"}}
                ]
            )
        
        assert result.success is True
        assert result.metadata["successful"] == 1
        assert result.metadata["failed"] == 1
    
    @pytest.mark.asyncio
    async def test_execute_tool_with_validation_error(self):
        """Test executing tool with parameter validation error."""
        tool = BatchTool()
        
        mock_tool = MagicMock()
        mock_tool.name = "read"
        mock_tool.validate_params.return_value = "Missing required parameter: path"
        
        mock_registry = MagicMock()
        mock_registry.list_tools.return_value = [mock_tool]
        
        with patch('opencode.tool.batch.get_registry', return_value=mock_registry):
            result = await tool.execute(
                tool_calls=[{"tool": "read", "parameters": {}}]
            )
        
        assert result.success is True  # Batch returns success with error details
        assert result.metadata["failed"] == 1
    
    @pytest.mark.asyncio
    async def test_execute_tool_with_exception(self):
        """Test executing tool that raises exception."""
        tool = BatchTool()
        
        mock_tool = MagicMock()
        mock_tool.name = "read"
        mock_tool.validate_params.return_value = None
        mock_tool.execute = AsyncMock(side_effect=RuntimeError("Unexpected error"))
        
        mock_registry = MagicMock()
        mock_registry.list_tools.return_value = [mock_tool]
        
        with patch('opencode.tool.batch.get_registry', return_value=mock_registry):
            result = await tool.execute(
                tool_calls=[{"tool": "read", "parameters": {"path": "test.py"}}]
            )
        
        assert result.success is True  # Batch returns success with error details
        assert result.metadata["failed"] == 1
    
    @pytest.mark.asyncio
    async def test_execute_max_calls_limit(self):
        """Test that batch limits to 25 calls."""
        tool = BatchTool()
        
        mock_tool = MagicMock()
        mock_tool.name = "read"
        mock_tool.validate_params.return_value = None
        mock_tool.execute = AsyncMock(return_value=ToolResult.ok(output="ok"))
        
        mock_registry = MagicMock()
        mock_registry.list_tools.return_value = [mock_tool]
        
        # Create 30 tool calls
        tool_calls = [
            {"tool": "read", "parameters": {"path": f"file{i}.py"}}
            for i in range(30)
        ]
        
        with patch('opencode.tool.batch.get_registry', return_value=mock_registry):
            result = await tool.execute(tool_calls=tool_calls)
        
        # Should have 25 successful + 5 failed (discarded)
        assert result.metadata["total_calls"] == 30
        assert result.metadata["failed"] == 5
    
    def test_disallowed_tools_contains_batch(self):
        """Test that batch is in disallowed tools."""
        assert "batch" in DISALLOWED_TOOLS
    
    def test_filtered_from_suggestions(self):
        """Test filtered suggestions list."""
        assert "batch" in FILTERED_FROM_SUGGESTIONS
        assert "invalid" in FILTERED_FROM_SUGGESTIONS
        assert "patch" in FILTERED_FROM_SUGGESTIONS
