"""Tests for Todo tool module."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock

from opencode.tool.todo import TodoItem, TodoWriteTool, TodoReadTool
from opencode.tool.base import PermissionLevel, ToolResult


class TestTodoItem:
    """Tests for TodoItem."""
    
    def test_default_values(self):
        """Test default values."""
        item = TodoItem(id="1", content="Test task")
        assert item.id == "1"
        assert item.content == "Test task"
        assert item.status == "pending"
        assert item.priority == "medium"
        assert item.created_at is not None
        assert item.completed_at is None
    
    def test_custom_values(self):
        """Test custom values."""
        now = datetime.now()
        item = TodoItem(
            id="2",
            content="Another task",
            status="completed",
            priority="high",
            created_at=now,
            completed_at=now
        )
        assert item.id == "2"
        assert item.content == "Another task"
        assert item.status == "completed"
        assert item.priority == "high"
        assert item.completed_at == now
    
    def test_to_dict(self):
        """Test to_dict method."""
        now = datetime.now()
        item = TodoItem(
            id="1",
            content="Test task",
            status="in_progress",
            priority="high",
            created_at=now,
            completed_at=None
        )
        d = item.to_dict()
        
        assert d["id"] == "1"
        assert d["content"] == "Test task"
        assert d["status"] == "in_progress"
        assert d["priority"] == "high"
        assert d["created_at"] == now.isoformat()
        assert d["completed_at"] is None
    
    def test_to_dict_with_completed_at(self):
        """Test to_dict with completed_at set."""
        now = datetime.now()
        item = TodoItem(
            id="1",
            content="Test task",
            status="completed",
            created_at=now,
            completed_at=now
        )
        d = item.to_dict()
        
        assert d["completed_at"] == now.isoformat()


class TestTodoWriteTool:
    """Tests for TodoWriteTool."""
    
    def test_name(self):
        """Test name property."""
        tool = TodoWriteTool()
        assert tool.name == "todowrite"
    
    def test_description(self):
        """Test description property."""
        tool = TodoWriteTool()
        assert "todo list" in tool.description.lower()
    
    def test_parameters(self):
        """Test parameters property."""
        tool = TodoWriteTool()
        params = tool.parameters
        
        assert "todos" in params["properties"]
        assert "todos" in params["required"]
    
    def test_permission_level(self):
        """Test permission_level property."""
        tool = TodoWriteTool()
        assert tool.permission_level == PermissionLevel.WRITE
    
    @pytest.mark.asyncio
    async def test_execute_create_todo(self):
        """Test creating a new todo."""
        tool = TodoWriteTool()
        result = await tool.execute(todos=[{"content": "Test task"}])
        
        assert result.success is True
        assert "Created" in result.output
        assert "Test task" in result.output
        assert len(tool._todos) == 1
    
    @pytest.mark.asyncio
    async def test_execute_create_multiple_todos(self):
        """Test creating multiple todos."""
        tool = TodoWriteTool()
        result = await tool.execute(todos=[
            {"content": "Task 1"},
            {"content": "Task 2"},
            {"content": "Task 3"}
        ])
        
        assert result.success is True
        assert len(tool._todos) == 3
    
    @pytest.mark.asyncio
    async def test_execute_create_with_status(self):
        """Test creating todo with status."""
        tool = TodoWriteTool()
        result = await tool.execute(todos=[
            {"content": "Test task", "status": "in_progress"}
        ])
        
        assert result.success is True
        assert tool._todos[0].status == "in_progress"
    
    @pytest.mark.asyncio
    async def test_execute_create_with_priority(self):
        """Test creating todo with priority."""
        tool = TodoWriteTool()
        result = await tool.execute(todos=[
            {"content": "Test task", "priority": "high"}
        ])
        
        assert result.success is True
        assert tool._todos[0].priority == "high"
    
    @pytest.mark.asyncio
    async def test_execute_update_todo(self):
        """Test updating an existing todo."""
        tool = TodoWriteTool()
        
        # Create a todo first
        await tool.execute(todos=[{"content": "Original task"}])
        
        # Update it
        result = await tool.execute(todos=[
            {"id": "1", "content": "Updated task", "status": "completed"}
        ])
        
        assert result.success is True
        assert "Updated" in result.output
        assert tool._todos[0].content == "Updated task"
        assert tool._todos[0].status == "completed"
    
    @pytest.mark.asyncio
    async def test_execute_update_sets_completed_at(self):
        """Test that completing a todo sets completed_at."""
        tool = TodoWriteTool()
        
        # Create a todo
        await tool.execute(todos=[{"content": "Task to complete"}])
        assert tool._todos[0].completed_at is None
        
        # Complete it
        await tool.execute(todos=[{"id": "1", "status": "completed"}])
        assert tool._todos[0].completed_at is not None
    
    @pytest.mark.asyncio
    async def test_execute_update_nonexistent_todo(self):
        """Test updating a non-existent todo."""
        tool = TodoWriteTool()
        result = await tool.execute(todos=[{"id": "999", "status": "completed"}])
        
        assert result.success is True
        assert "not found" in result.output
    
    @pytest.mark.asyncio
    async def test_execute_empty_todos(self):
        """Test with empty todos list."""
        tool = TodoWriteTool()
        result = await tool.execute(todos=[])
        
        assert result.success is False
        assert result.error is not None
        assert "No todos" in result.error
    
    @pytest.mark.asyncio
    async def test_execute_no_todos_param(self):
        """Test without todos parameter."""
        tool = TodoWriteTool()
        result = await tool.execute()
        
        assert result.success is False
    
    @pytest.mark.asyncio
    async def test_execute_returns_metadata(self):
        """Test that execute returns todos in metadata."""
        tool = TodoWriteTool()
        result = await tool.execute(todos=[{"content": "Test task"}])
        
        assert result.success is True
        assert "todos" in result.metadata
        assert len(result.metadata["todos"]) == 1


class TestTodoReadTool:
    """Tests for TodoReadTool."""
    
    def test_name(self):
        """Test name property."""
        write_tool = TodoWriteTool()
        read_tool = TodoReadTool(write_tool)
        assert read_tool.name == "todoread"
    
    def test_description(self):
        """Test description property."""
        write_tool = TodoWriteTool()
        read_tool = TodoReadTool(write_tool)
        assert "todo list" in read_tool.description.lower()
    
    def test_parameters(self):
        """Test parameters property."""
        write_tool = TodoWriteTool()
        read_tool = TodoReadTool(write_tool)
        params = read_tool.parameters
        
        assert params["type"] == "object"
        assert "properties" in params
    
    def test_permission_level(self):
        """Test permission_level property."""
        write_tool = TodoWriteTool()
        read_tool = TodoReadTool(write_tool)
        assert read_tool.permission_level == PermissionLevel.READ
    
    @pytest.mark.asyncio
    async def test_execute_empty_list(self):
        """Test reading empty todo list."""
        write_tool = TodoWriteTool()
        read_tool = TodoReadTool(write_tool)
        result = await read_tool.execute()
        
        assert result.success is True
        assert "No todos" in result.output
    
    @pytest.mark.asyncio
    async def test_execute_with_todos(self):
        """Test reading todo list with items."""
        write_tool = TodoWriteTool()
        await write_tool.execute(todos=[
            {"content": "Task 1"},
            {"content": "Task 2", "status": "in_progress"},
            {"content": "Task 3", "status": "completed"}
        ])
        
        read_tool = TodoReadTool(write_tool)
        result = await read_tool.execute()
        
        assert result.success is True
        assert "Todo List" in result.output
        assert "Task 1" in result.output
        assert "Task 2" in result.output
        assert "Task 3" in result.output
    
    @pytest.mark.asyncio
    async def test_execute_groups_by_status(self):
        """Test that todos are grouped by status."""
        write_tool = TodoWriteTool()
        await write_tool.execute(todos=[
            {"content": "Pending task", "status": "pending"},
            {"content": "In progress task", "status": "in_progress"},
            {"content": "Completed task", "status": "completed"}
        ])
        
        read_tool = TodoReadTool(write_tool)
        result = await read_tool.execute()
        
        assert result.success is True
        assert "In Progress" in result.output
        assert "Pending" in result.output
        assert "Completed" in result.output
    
    @pytest.mark.asyncio
    async def test_execute_shows_progress(self):
        """Test that progress is shown."""
        write_tool = TodoWriteTool()
        await write_tool.execute(todos=[
            {"content": "Task 1"},
            {"content": "Task 2", "status": "completed"}
        ])
        
        read_tool = TodoReadTool(write_tool)
        result = await read_tool.execute()
        
        assert result.success is True
        assert "Progress:" in result.output
        assert "1/2" in result.output
    
    @pytest.mark.asyncio
    async def test_execute_returns_metadata(self):
        """Test that execute returns todos in metadata."""
        write_tool = TodoWriteTool()
        await write_tool.execute(todos=[{"content": "Test task"}])
        
        read_tool = TodoReadTool(write_tool)
        result = await read_tool.execute()
        
        assert result.success is True
        assert "todos" in result.metadata
        assert len(result.metadata["todos"]) == 1
