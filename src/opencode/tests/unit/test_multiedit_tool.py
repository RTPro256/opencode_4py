"""
Unit tests for MultiEdit tool implementation.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import os

from opencode.tool.multiedit import MultiEditTool
from opencode.tool.base import ToolResult


class TestMultiEditTool:
    """Tests for MultiEditTool class."""

    @pytest.fixture
    def tool(self):
        """Create a MultiEditTool instance."""
        return MultiEditTool()

    @pytest.fixture
    def temp_file(self):
        """Create a temporary file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def old_func():\n    pass\n\ndef another_func():\n    old_func()\n")
            name = f.name
        yield name
        os.unlink(name)

    def test_tool_name(self, tool):
        """Test tool name property."""
        assert tool.name == "multiedit"

    def test_tool_description(self, tool):
        """Test tool description property."""
        desc = tool.description
        assert "multiple" in desc.lower()
        assert "edit" in desc.lower()

    def test_tool_parameters(self, tool):
        """Test tool parameters schema."""
        params = tool.parameters
        assert params["type"] == "object"
        assert "filePath" in params["properties"]
        assert "edits" in params["properties"]
        assert "required" in params
        assert "filePath" in params["required"]
        assert "edits" in params["required"]

    @pytest.mark.asyncio
    async def test_execute_missing_file_path(self, tool):
        """Test execute with missing filePath."""
        result = await tool.execute(edits=[])
        assert not result.success
        assert "filePath is required" in result.error

    @pytest.mark.asyncio
    async def test_execute_missing_edits(self, tool):
        """Test execute with missing edits."""
        result = await tool.execute(filePath="/some/path.py")
        assert not result.success
        assert "edits array is required" in result.error

    @pytest.mark.asyncio
    async def test_execute_empty_edits(self, tool):
        """Test execute with empty edits array."""
        result = await tool.execute(filePath="/some/path.py", edits=[])
        assert not result.success
        assert "edits array is required" in result.error

    @pytest.mark.asyncio
    async def test_execute_file_not_found(self, tool):
        """Test execute with non-existent file."""
        result = await tool.execute(
            filePath="/nonexistent/path/file.py",
            edits=[{"oldString": "old", "newString": "new"}]
        )
        assert not result.success
        assert "File not found" in result.error

    @pytest.mark.asyncio
    async def test_execute_not_a_file(self, tool):
        """Test execute with directory path instead of file."""
        result = await tool.execute(
            filePath="/",
            edits=[{"oldString": "old", "newString": "new"}]
        )
        assert not result.success
        assert "Not a file" in result.error

    @pytest.mark.asyncio
    async def test_execute_single_edit(self, tool, temp_file):
        """Test execute with a single successful edit."""
        result = await tool.execute(
            filePath=temp_file,
            edits=[{"oldString": "old_func", "newString": "new_func"}]
        )
        assert result.success
        assert "Successfully applied 1/1 edits" in result.output
        assert "Total replacements: 1" in result.output
        
        # Verify file was modified
        content = Path(temp_file).read_text()
        assert "new_func" in content
        assert content.count("old_func") == 1  # The one in another_func remains

    @pytest.mark.asyncio
    async def test_execute_multiple_edits(self, tool, temp_file):
        """Test execute with multiple successful edits."""
        result = await tool.execute(
            filePath=temp_file,
            edits=[
                {"oldString": "old_func", "newString": "new_func"},
                {"oldString": "another_func", "newString": "other_func"}
            ]
        )
        assert result.success
        assert "Successfully applied 2/2 edits" in result.output
        
        content = Path(temp_file).read_text()
        assert "new_func" in content
        assert "other_func" in content

    @pytest.mark.asyncio
    async def test_execute_replace_all(self, tool, temp_file):
        """Test execute with replaceAll option."""
        result = await tool.execute(
            filePath=temp_file,
            edits=[{"oldString": "old_func", "newString": "new_func", "replaceAll": True}]
        )
        assert result.success
        assert "Total replacements: 2" in result.output
        
        content = Path(temp_file).read_text()
        assert "new_func" in content
        assert "old_func" not in content

    @pytest.mark.asyncio
    async def test_execute_edit_missing_old_string(self, tool, temp_file):
        """Test execute with edit missing oldString."""
        result = await tool.execute(
            filePath=temp_file,
            edits=[{"newString": "new"}]
        )
        assert not result.success
        assert "oldString is required" in result.error

    @pytest.mark.asyncio
    async def test_execute_edit_same_strings(self, tool, temp_file):
        """Test execute with oldString same as newString."""
        result = await tool.execute(
            filePath=temp_file,
            edits=[{"oldString": "same", "newString": "same"}]
        )
        assert not result.success
        assert "must be different" in result.error

    @pytest.mark.asyncio
    async def test_execute_text_not_found(self, tool, temp_file):
        """Test execute when oldString not found in file."""
        result = await tool.execute(
            filePath=temp_file,
            edits=[{"oldString": "nonexistent_text", "newString": "new"}]
        )
        assert not result.success
        assert "Text not found" in result.error

    @pytest.mark.asyncio
    async def test_execute_partial_failure(self, tool, temp_file):
        """Test execute with some edits succeeding and some failing."""
        result = await tool.execute(
            filePath=temp_file,
            edits=[
                {"oldString": "old_func", "newString": "new_func"},
                {"oldString": "nonexistent", "newString": "new"},
                {"oldString": "pass", "newString": "return"}
            ]
        )
        assert result.success  # Partial success is still success
        assert "Successfully applied 2/3 edits" in result.output
        assert "Failed edits:" in result.output

    @pytest.mark.asyncio
    async def test_execute_all_edits_fail(self, tool, temp_file):
        """Test execute when all edits fail."""
        result = await tool.execute(
            filePath=temp_file,
            edits=[
                {"oldString": "nonexistent1", "newString": "new1"},
                {"oldString": "nonexistent2", "newString": "new2"}
            ]
        )
        assert not result.success
        assert "All 2 edits failed" in result.error

    @pytest.mark.asyncio
    async def test_execute_long_old_string_truncation(self, tool, temp_file):
        """Test error message truncation for long oldString."""
        long_string = "x" * 200
        result = await tool.execute(
            filePath=temp_file,
            edits=[{"oldString": long_string, "newString": "new"}]
        )
        assert not result.success
        assert "..." in result.error  # Should be truncated

    @pytest.mark.asyncio
    async def test_execute_read_error(self, tool):
        """Test execute handling read error."""
        import sys
        if sys.platform == "win32":
            # Windows doesn't support Unix-style file permissions
            pytest.skip("File permission test not applicable on Windows")
        
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            # Create a file and make it unreadable
            name = f.name
        
        try:
            os.chmod(name, 0o000)  # No permissions
            result = await tool.execute(
                filePath=name,
                edits=[{"oldString": "old", "newString": "new"}]
            )
            assert not result.success
            assert "Failed to read file" in result.error
        finally:
            os.chmod(name, 0o644)  # Restore permissions
            os.unlink(name)

    @pytest.mark.asyncio
    async def test_execute_write_error(self, tool):
        """Test execute handling write error."""
        import sys
        if sys.platform == "win32":
            # Windows doesn't support Unix-style file permissions
            pytest.skip("File permission test not applicable on Windows")
        
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            f.write(b"test content")
            name = f.name
        
        try:
            os.chmod(name, 0o444)  # Read-only
            result = await tool.execute(
                filePath=name,
                edits=[{"oldString": "test", "newString": "new"}]
            )
            assert not result.success
            assert "Failed to write file" in result.error
        finally:
            os.chmod(name, 0o644)  # Restore permissions
            os.unlink(name)

    @pytest.mark.asyncio
    async def test_execute_sequential_edits(self, tool):
        """Test that edits are applied sequentially."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("value = 1\n")
            name = f.name
        
        try:
            # First edit changes "value" to "result"
            # Second edit should work on the modified content
            result = await tool.execute(
                filePath=name,
                edits=[
                    {"oldString": "value = 1", "newString": "result = 1"},
                    {"oldString": "result = 1", "newString": "result = 2"}
                ]
            )
            assert result.success
            
            content = Path(name).read_text()
            assert content == "result = 2\n"
        finally:
            os.unlink(name)

    @pytest.mark.asyncio
    async def test_execute_metadata(self, tool, temp_file):
        """Test that metadata is correctly populated."""
        result = await tool.execute(
            filePath=temp_file,
            edits=[{"oldString": "old_func", "newString": "new_func"}]
        )
        assert result.success
        assert result.metadata["file_path"] == temp_file
        assert result.metadata["total_edits"] == 1
        assert result.metadata["successful_edits"] == 1
        assert result.metadata["failed_edits"] == 0
        assert result.metadata["total_replacements"] == 1
        assert "results" in result.metadata

    @pytest.mark.asyncio
    async def test_execute_files_changed(self, tool, temp_file):
        """Test that files_changed is populated."""
        result = await tool.execute(
            filePath=temp_file,
            edits=[{"oldString": "old_func", "newString": "new_func"}]
        )
        assert result.success
        assert temp_file in result.files_changed


class TestMultiEditToolEdgeCases:
    """Edge case tests for MultiEditTool."""

    @pytest.fixture
    def tool(self):
        """Create a MultiEditTool instance."""
        return MultiEditTool()

    @pytest.mark.asyncio
    async def test_empty_old_string(self, tool):
        """Test with empty oldString."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("content\n")
            name = f.name
        
        try:
            result = await tool.execute(
                filePath=name,
                edits=[{"oldString": "", "newString": "new"}]
            )
            assert not result.success
            assert "oldString is required" in result.error
        finally:
            os.unlink(name)

    @pytest.mark.asyncio
    async def test_unicode_content(self, tool):
        """Test with unicode content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write("# -*- coding: utf-8 -*-\nmessage = 'こんにちは'\n")
            name = f.name
        
        try:
            result = await tool.execute(
                filePath=name,
                edits=[{"oldString": "こんにちは", "newString": "你好"}]
            )
            assert result.success
            
            content = Path(name).read_text(encoding='utf-8')
            assert "你好" in content
        finally:
            os.unlink(name)

    @pytest.mark.asyncio
    async def test_multiline_replacement(self, tool):
        """Test replacing multiline strings."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def func():\n    pass\n\ndef other():\n    pass\n")
            name = f.name
        
        try:
            result = await tool.execute(
                filePath=name,
                edits=[{"oldString": "def func():\n    pass", "newString": "def func():\n    return 42"}]
            )
            assert result.success
            
            content = Path(name).read_text()
            assert "return 42" in content
        finally:
            os.unlink(name)

    @pytest.mark.asyncio
    async def test_special_characters(self, tool):
        """Test with special regex-like characters."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("pattern = r'\\d+\\.\\d*'\n")
            name = f.name
        
        try:
            # These should be treated as literal strings, not regex
            result = await tool.execute(
                filePath=name,
                edits=[{"oldString": r"\d+\.\d*", "newString": r"\w+"}]
            )
            assert result.success
            
            content = Path(name).read_text()
            assert r"\w+" in content
        finally:
            os.unlink(name)

    @pytest.mark.asyncio
    async def test_large_file(self, tool):
        """Test with a larger file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            # Create a file with many lines
            for i in range(1000):
                f.write(f"def func_{i}():\n    pass\n\n")
            name = f.name
        
        try:
            result = await tool.execute(
                filePath=name,
                edits=[{"oldString": "func_500", "newString": "renamed_func"}]
            )
            assert result.success
            
            content = Path(name).read_text()
            assert "renamed_func" in content
        finally:
            os.unlink(name)

    @pytest.mark.asyncio
    async def test_multiple_occurrences_first_only(self, tool):
        """Test replacing only first occurrence when replaceAll is False."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("x = 1\nx = 2\nx = 3\n")
            name = f.name
        
        try:
            result = await tool.execute(
                filePath=name,
                edits=[{"oldString": "x", "newString": "y", "replaceAll": False}]
            )
            assert result.success
            assert "Total replacements: 1" in result.output
            
            content = Path(name).read_text()
            lines = content.strip().split('\n')
            assert lines[0] == "y = 1"
            assert lines[1] == "x = 2"
            assert lines[2] == "x = 3"
        finally:
            os.unlink(name)
