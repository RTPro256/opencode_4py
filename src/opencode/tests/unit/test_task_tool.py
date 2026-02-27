"""
Tests for Task tool implementation.
"""

import pytest
from opencode.tool.task import TaskTool


@pytest.mark.unit
class TestTaskTool:
    """Tests for TaskTool class."""
    
    def test_tool_name(self):
        """Test tool name."""
        tool = TaskTool()
        assert tool.name == "task"
    
    def test_tool_description(self):
        """Test tool has description."""
        tool = TaskTool()
        assert tool.description is not None
        assert len(tool.description) > 0
    
    def test_tool_parameters(self):
        """Test tool parameters schema."""
        tool = TaskTool()
        params = tool.parameters
        
        assert "properties" in params
    
    @pytest.mark.asyncio
    async def test_create_task(self):
        """Test creating a task."""
        tool = TaskTool()
        
        result = await tool.execute(
            mode="code",
            message="Implement a new feature"
        )
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_create_task_with_todos(self):
        """Test creating a task with todos."""
        tool = TaskTool()
        
        result = await tool.execute(
            mode="code",
            message="Implement feature X",
            todos=["Step 1: Design", "Step 2: Implement", "Step 3: Test"]
        )
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_create_task_empty_message(self):
        """Test creating a task with empty message."""
        tool = TaskTool()
        
        result = await tool.execute(mode="code", message="")
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_different_modes(self):
        """Test creating tasks in different modes."""
        tool = TaskTool()
        
        modes = ["code", "architect", "ask", "debug"]
        
        for mode in modes:
            result = await tool.execute(mode=mode, message=f"Task in {mode} mode")
            assert result is not None
