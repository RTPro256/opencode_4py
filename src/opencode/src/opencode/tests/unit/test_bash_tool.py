"""Tests for Bash Tool."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from opencode.tool.bash import BashTool
from opencode.tool.base import PermissionLevel


class TestBashTool:
    """Tests for BashTool."""

    def test_name(self):
        """Test tool name."""
        tool = BashTool()
        
        assert tool.name == "bash"

    def test_description(self):
        """Test tool description."""
        tool = BashTool()
        
        assert "bash" in tool.description.lower()
        assert "command" in tool.description.lower()

    def test_parameters(self):
        """Test tool parameters schema."""
        tool = BashTool()
        
        params = tool.parameters
        
        assert params["type"] == "object"
        assert "command" in params["properties"]
        assert "timeout" in params["properties"]
        assert "cwd" in params["properties"]
        assert "env" in params["properties"]
        assert "command" in params["required"]

    def test_permission_level(self):
        """Test permission level."""
        tool = BashTool()
        
        assert tool.permission_level == PermissionLevel.EXECUTE

    def test_working_directory_default(self):
        """Test default working directory."""
        tool = BashTool()
        
        assert tool.working_directory == Path(".")

    def test_timeout_default(self):
        """Test default timeout."""
        tool = BashTool()
        
        assert tool.timeout == 120

    def test_max_output_size_default(self):
        """Test default max output size."""
        tool = BashTool()
        
        assert tool.max_output_size == 100000

    @pytest.mark.asyncio
    async def test_execute_simple_command(self):
        """Test executing a simple command."""
        tool = BashTool()
        
        # Mock the subprocess creation
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b"output", b""))
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            result = await tool.execute(command="echo hello")
            
            assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_with_timeout(self):
        """Test executing with custom timeout."""
        tool = BashTool()
        
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b"output", b""))
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            result = await tool.execute(command="echo hello", timeout=60)
            
            assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_with_cwd(self):
        """Test executing with custom working directory."""
        tool = BashTool()
        
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b"output", b""))
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            result = await tool.execute(command="echo hello", cwd="/tmp")
            
            assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_with_env(self):
        """Test executing with environment variables."""
        tool = BashTool()
        
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b"output", b""))
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            result = await tool.execute(
                command="echo hello",
                env={"MY_VAR": "value"}
            )
            
            assert result.success is True
