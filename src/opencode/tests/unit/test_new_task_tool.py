"""Tests for New Task Tool."""

import pytest

from opencode.tool.new_task import NewTaskTool
from opencode.tool.base import ToolResult


class TestNewTaskTool:
    """Tests for NewTaskTool."""

    def test_name(self):
        """Test tool name."""
        tool = NewTaskTool()
        
        assert tool.name == "new_task"

    def test_description(self):
        """Test tool description."""
        tool = NewTaskTool()
        
        assert "subagent" in tool.description.lower() or "task" in tool.description.lower()

    def test_parameters(self):
        """Test tool parameters schema."""
        tool = NewTaskTool()
        
        params = tool.parameters
        
        assert params["type"] == "object"
        assert "message" in params["properties"]
        assert "mode" in params["properties"]
        assert "context" in params["properties"]
        assert "resume" in params["properties"]
        assert "message" in params["required"]

    @pytest.mark.asyncio
    async def test_execute_basic(self):
        """Test basic execution."""
        tool = NewTaskTool()
        
        result = await tool.execute(message="Analyze the code")
        
        assert result.success is True
        assert "Created new task" in result.output

    @pytest.mark.asyncio
    async def test_execute_with_mode(self):
        """Test execution with mode."""
        tool = NewTaskTool()
        
        result = await tool.execute(
            message="Debug the issue",
            mode="debug"
        )
        
        assert result.success is True
        assert "Mode: debug" in result.output

    @pytest.mark.asyncio
    async def test_execute_with_context(self):
        """Test execution with context."""
        tool = NewTaskTool()
        
        result = await tool.execute(
            message="Fix the bug",
            context={"target": "auth.py"}
        )
        
        assert result.success is True
        assert result.metadata["context"] == {"target": "auth.py"}

    @pytest.mark.asyncio
    async def test_execute_with_resume_false(self):
        """Test execution with resume=False."""
        tool = NewTaskTool()
        
        result = await tool.execute(
            message="Test task",
            resume=False
        )
        
        assert result.success is True
        assert result.metadata["resume"] is False

    @pytest.mark.asyncio
    async def test_execute_missing_message(self):
        """Test execution with missing message."""
        tool = NewTaskTool()
        
        result = await tool.execute()
        
        assert result.success is False
        assert "missing" in result.error.lower()

    @pytest.mark.asyncio
    async def test_metadata(self):
        """Test result metadata."""
        tool = NewTaskTool()
        
        result = await tool.execute(
            message="Test task",
            mode="architect"
        )
        
        assert result.metadata["type"] == "new_task"
        assert result.metadata["message"] == "Test task"
        assert result.metadata["mode"] == "architect"
        assert result.metadata["status"] == "pending"
        assert "task_id" in result.metadata

    @pytest.mark.asyncio
    async def test_task_id_generated(self):
        """Test that task ID is generated."""
        tool = NewTaskTool()
        
        result = await tool.execute(message="Test")
        
        assert result.metadata["task_id"] is not None
        assert len(result.metadata["task_id"]) == 8

    @pytest.mark.asyncio
    async def test_long_message_truncated(self):
        """Test that long message is truncated in output."""
        tool = NewTaskTool()
        
        long_message = "A" * 200
        result = await tool.execute(message=long_message)
        
        assert result.success is True
        assert "..." in result.output

    @pytest.mark.asyncio
    async def test_default_mode(self):
        """Test default mode is 'code'."""
        tool = NewTaskTool()
        
        result = await tool.execute(message="Test")
        
        assert result.metadata["mode"] == "code"

    @pytest.mark.asyncio
    async def test_default_resume(self):
        """Test default resume is True."""
        tool = NewTaskTool()
        
        result = await tool.execute(message="Test")
        
        assert result.metadata["resume"] is True
