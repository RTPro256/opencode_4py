"""Tests for Attempt Completion Tool."""

import pytest

from opencode.tool.attempt_completion import AttemptCompletionTool
from opencode.tool.base import ToolResult


class TestAttemptCompletionTool:
    """Tests for AttemptCompletionTool."""

    def test_name(self):
        """Test tool name."""
        tool = AttemptCompletionTool()
        
        assert tool.name == "attempt_completion"

    def test_description(self):
        """Test tool description."""
        tool = AttemptCompletionTool()
        
        assert "complete" in tool.description.lower()

    def test_parameters(self):
        """Test tool parameters schema."""
        tool = AttemptCompletionTool()
        
        params = tool.parameters
        
        assert params["type"] == "object"
        assert "result" in params["properties"]
        assert "files_changed" in params["properties"]
        assert "requires_review" in params["properties"]
        assert "result" in params["required"]

    @pytest.mark.asyncio
    async def test_execute_basic(self):
        """Test basic execution."""
        tool = AttemptCompletionTool()
        
        result = await tool.execute(result="Task completed successfully")
        
        assert result.success is True
        assert "Task completed successfully" in result.output

    @pytest.mark.asyncio
    async def test_execute_with_files_changed(self):
        """Test execution with files changed."""
        tool = AttemptCompletionTool()
        
        result = await tool.execute(
            result="Implemented feature",
            files_changed=["src/main.py", "src/test.py"]
        )
        
        assert result.success is True
        assert "Files changed" in result.output
        assert "src/main.py" in result.output
        assert "src/test.py" in result.output

    @pytest.mark.asyncio
    async def test_execute_with_requires_review(self):
        """Test execution with requires_review flag."""
        tool = AttemptCompletionTool()
        
        result = await tool.execute(
            result="Changes made",
            requires_review=True
        )
        
        assert result.success is True
        assert "review" in result.output.lower()

    @pytest.mark.asyncio
    async def test_execute_missing_result(self):
        """Test execution with missing result parameter."""
        tool = AttemptCompletionTool()
        
        result = await tool.execute()
        
        assert result.success is False
        assert "missing" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_empty_result(self):
        """Test execution with empty result."""
        tool = AttemptCompletionTool()
        
        result = await tool.execute(result="")
        
        assert result.success is False

    @pytest.mark.asyncio
    async def test_metadata(self):
        """Test result metadata."""
        tool = AttemptCompletionTool()
        
        result = await tool.execute(
            result="Done",
            files_changed=["file1.py"],
            requires_review=True
        )
        
        assert result.metadata["type"] == "task_completion"
        assert result.metadata["result"] == "Done"
        assert result.metadata["files_changed"] == ["file1.py"]
        assert result.metadata["requires_review"] is True
        assert result.metadata["task_completed"] is True

    @pytest.mark.asyncio
    async def test_files_changed_in_result(self):
        """Test files_changed is in result."""
        tool = AttemptCompletionTool()
        
        result = await tool.execute(
            result="Done",
            files_changed=["file1.py", "file2.py"]
        )
        
        assert result.files_changed == ["file1.py", "file2.py"]
