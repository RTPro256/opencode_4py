"""
Tests for Memory Tool.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import json

from opencode.tool.memory import MemoryTool, MemoryEntry, MemoryScope


@pytest.mark.unit
class TestMemoryTool:
    """Tests for MemoryTool."""
    
    def test_memory_tool_name(self):
        """Test tool name."""
        tool = MemoryTool()
        assert tool.name == "memory"
    
    def test_memory_tool_description(self):
        """Test tool description."""
        tool = MemoryTool()
        assert "memory" in tool.description.lower()
    
    def test_memory_tool_parameters(self):
        """Test tool parameters schema."""
        tool = MemoryTool()
        params = tool.parameters
        assert params["type"] == "object"
        assert "operation" in params["properties"]
        assert "operation" in params["required"]
    
    def test_memory_tool_init_with_paths(self):
        """Test initialization with custom paths."""
        with tempfile.TemporaryDirectory() as project_dir:
            with tempfile.TemporaryDirectory() as home_dir:
                tool = MemoryTool(
                    project_root=Path(project_dir),
                    user_home=Path(home_dir)
                )
                assert tool.project_root == Path(project_dir)
                assert tool.user_home == Path(home_dir)
    
    def test_memory_tool_init_default_paths(self):
        """Test initialization with default paths."""
        tool = MemoryTool()
        assert tool.project_root == Path.cwd()
    
    @pytest.mark.asyncio
    async def test_save_operation(self):
        """Test save operation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = MemoryTool(project_root=Path(tmpdir))
            result = await tool.execute(operation="save", key="test_key", value="test_value")
            assert result.success
            assert "Saved" in result.output
    
    @pytest.mark.asyncio
    async def test_get_operation(self):
        """Test get operation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = MemoryTool(project_root=Path(tmpdir))
            # First save
            await tool.execute(operation="save", key="test_key", value="test_value")
            # Then get
            result = await tool.execute(operation="get", key="test_key")
            assert result.success
            assert result.output == "test_value"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self):
        """Test get operation with nonexistent key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = MemoryTool(project_root=Path(tmpdir))
            result = await tool.execute(operation="get", key="nonexistent")
            assert not result.success
            assert result.error is not None
            assert "not found" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_list_operation_empty(self):
        """Test list operation when empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = MemoryTool(project_root=Path(tmpdir))
            result = await tool.execute(operation="list")
            assert result.success
            assert "No memory entries" in result.output or result.metadata.get("count") == 0
    
    @pytest.mark.asyncio
    async def test_list_operation_with_entries(self):
        """Test list operation with entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = MemoryTool(project_root=Path(tmpdir))
            # Save some entries
            await tool.execute(operation="save", key="key1", value="value1")
            await tool.execute(operation="save", key="key2", value="value2")
            # List
            result = await tool.execute(operation="list")
            assert result.success
            assert result.metadata.get("count") == 2
    
    @pytest.mark.asyncio
    async def test_delete_operation(self):
        """Test delete operation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = MemoryTool(project_root=Path(tmpdir))
            # First save
            await tool.execute(operation="save", key="test_key", value="test_value")
            # Then delete
            result = await tool.execute(operation="delete", key="test_key")
            assert result.success
            assert "Deleted" in result.output
            # Verify it's gone
            result = await tool.execute(operation="get", key="test_key")
            assert not result.success
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_key(self):
        """Test delete operation with nonexistent key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = MemoryTool(project_root=Path(tmpdir))
            result = await tool.execute(operation="delete", key="nonexistent")
            assert not result.success
    
    @pytest.mark.asyncio
    async def test_switch_scope_operation(self):
        """Test switch scope operation."""
        with tempfile.TemporaryDirectory() as project_dir:
            with tempfile.TemporaryDirectory() as home_dir:
                tool = MemoryTool(
                    project_root=Path(project_dir),
                    user_home=Path(home_dir)
                )
                result = await tool.execute(operation="switch", scope="global")
                assert result.success
                assert "Switched" in result.output
    
    @pytest.mark.asyncio
    async def test_invalid_operation(self):
        """Test invalid operation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = MemoryTool(project_root=Path(tmpdir))
            result = await tool.execute(operation="invalid")
            assert not result.success
    
    @pytest.mark.asyncio
    async def test_save_missing_key(self):
        """Test save operation without key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = MemoryTool(project_root=Path(tmpdir))
            result = await tool.execute(operation="save", value="test_value")
            assert not result.success
    
    @pytest.mark.asyncio
    async def test_save_missing_value(self):
        """Test save operation without value."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = MemoryTool(project_root=Path(tmpdir))
            result = await tool.execute(operation="save", key="test_key")
            assert not result.success


@pytest.mark.unit
class TestMemoryEntry:
    """Tests for MemoryEntry model."""
    
    def test_memory_entry_creation(self):
        """Test creating a MemoryEntry."""
        entry = MemoryEntry(key="test", value="test value")
        assert entry.key == "test"
        assert entry.value == "test value"
        assert entry.scope == MemoryScope.PROJECT
    
    def test_memory_entry_with_scope(self):
        """Test MemoryEntry with custom scope."""
        entry = MemoryEntry(key="test", value="test value", scope="global")
        assert entry.scope == "global"


@pytest.mark.unit
class TestMemoryScope:
    """Tests for MemoryScope."""
    
    def test_memory_scope_values(self):
        """Test MemoryScope values."""
        assert MemoryScope.PROJECT == "project"
        assert MemoryScope.GLOBAL == "global"
