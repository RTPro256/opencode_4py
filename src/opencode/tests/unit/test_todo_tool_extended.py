"""
Tests for Todo tool implementation.
"""

import pytest
from datetime import datetime
from opencode.tool.todo import TodoWriteTool, TodoItem


@pytest.mark.unit
class TestTodoItem:
    """Tests for TodoItem dataclass."""
    
    def test_todo_item_creation(self):
        """Test creating a todo item."""
        item = TodoItem(
            id="1",
            content="Test task",
            status="pending",
            priority="high"
        )
        
        assert item.id == "1"
        assert item.content == "Test task"
        assert item.status == "pending"
        assert item.priority == "high"
        assert item.created_at is not None
        assert item.completed_at is None
    
    def test_todo_item_to_dict(self):
        """Test converting todo item to dict."""
        item = TodoItem(
            id="1",
            content="Test task",
            status="completed",
            priority="medium",
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            completed_at=datetime(2024, 1, 1, 14, 0, 0)
        )
        
        result = item.to_dict()
        
        assert result["id"] == "1"
        assert result["content"] == "Test task"
        assert result["status"] == "completed"
        assert result["priority"] == "medium"
        assert "created_at" in result
        assert "completed_at" in result
    
    def test_todo_item_default_values(self):
        """Test todo item default values."""
        item = TodoItem(id="1", content="Test")
        
        assert item.status == "pending"
        assert item.priority == "medium"
        assert item.completed_at is None


@pytest.mark.unit
class TestTodoWriteTool:
    """Tests for TodoWriteTool class."""
    
    def test_tool_name(self):
        """Test tool name."""
        tool = TodoWriteTool()
        assert tool.name == "todowrite"
    
    def test_tool_description(self):
        """Test tool has description."""
        tool = TodoWriteTool()
        assert tool.description is not None
        assert len(tool.description) > 0
    
    def test_tool_parameters(self):
        """Test tool parameters schema."""
        tool = TodoWriteTool()
        params = tool.parameters
        
        assert "properties" in params
        assert "todos" in params["properties"]
    
    @pytest.mark.asyncio
    async def test_create_todo(self):
        """Test creating a todo."""
        tool = TodoWriteTool()
        
        result = await tool.execute(
            todos=[
                {"content": "Task 1", "status": "pending"},
                {"content": "Task 2", "status": "pending"},
            ]
        )
        
        assert result.success
    
    @pytest.mark.asyncio
    async def test_update_todo_status(self):
        """Test updating todo status."""
        tool = TodoWriteTool()
        
        # Create todos
        await tool.execute(
            todos=[
                {"content": "Task 1", "status": "pending"},
            ]
        )
        
        # Update status
        result = await tool.execute(
            todos=[
                {"id": "1", "status": "completed"}
            ]
        )
        
        assert result.success
    
    @pytest.mark.asyncio
    async def test_update_todo_content(self):
        """Test updating todo content."""
        tool = TodoWriteTool()
        
        # Create todo
        await tool.execute(
            todos=[{"content": "Original content", "status": "pending"}]
        )
        
        # Update content
        result = await tool.execute(
            todos=[{"id": "1", "content": "Updated content"}]
        )
        
        assert result.success
    
    @pytest.mark.asyncio
    async def test_multiple_priorities(self):
        """Test todos with different priorities."""
        tool = TodoWriteTool()
        
        result = await tool.execute(
            todos=[
                {"content": "Low priority task", "status": "pending", "priority": "low"},
                {"content": "Medium priority task", "status": "pending", "priority": "medium"},
                {"content": "High priority task", "status": "pending", "priority": "high"},
            ]
        )
        
        assert result.success
    
    @pytest.mark.asyncio
    async def test_status_transitions(self):
        """Test todo status transitions."""
        tool = TodoWriteTool()
        
        # Create todo
        await tool.execute(
            todos=[{"content": "Task", "status": "pending"}]
        )
        
        # Transition to in_progress
        await tool.execute(todos=[{"id": "1", "status": "in_progress"}])
        
        # Transition to completed
        result = await tool.execute(todos=[{"id": "1", "status": "completed"}])
        
        assert result.success
    
    @pytest.mark.asyncio
    async def test_empty_todos(self):
        """Test with empty todos list."""
        tool = TodoWriteTool()
        
        result = await tool.execute(todos=[])
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_invalid_status(self):
        """Test with invalid status."""
        tool = TodoWriteTool()
        
        result = await tool.execute(
            todos=[{"content": "Task", "status": "invalid_status"}]
        )
        
        # Should handle gracefully
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_invalid_priority(self):
        """Test with invalid priority."""
        tool = TodoWriteTool()
        
        result = await tool.execute(
            todos=[{"content": "Task", "status": "pending", "priority": "invalid"}]
        )
        
        # Should handle gracefully
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_todo(self):
        """Test updating a todo that doesn't exist."""
        tool = TodoWriteTool()
        
        result = await tool.execute(
            todos=[{"id": "nonexistent", "status": "completed"}]
        )
        
        # Should handle gracefully
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_large_todo_list(self):
        """Test with large todo list."""
        tool = TodoWriteTool()
        
        todos = [
            {"content": f"Task {i}", "status": "pending"}
            for i in range(50)
        ]
        
        result = await tool.execute(todos=todos)
        
        assert result.success
