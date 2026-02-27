"""Tests for Bash Tool."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from opencode.tool.bash import BashTool, SafeBashTool, create_bash_tool
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
        mock_process.returncode = 0
        
        with patch('asyncio.create_subprocess_shell', return_value=mock_process):
            result = await tool.execute(command="echo hello")
            
            assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_with_timeout(self):
        """Test executing with custom timeout."""
        tool = BashTool()
        
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b"output", b""))
        mock_process.returncode = 0
        
        with patch('asyncio.create_subprocess_shell', return_value=mock_process):
            result = await tool.execute(command="echo hello", timeout=60)
            
            assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_with_cwd(self):
        """Test executing with custom working directory."""
        tool = BashTool()
        
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b"output", b""))
        mock_process.returncode = 0
        
        with patch('asyncio.create_subprocess_shell', return_value=mock_process):
            result = await tool.execute(command="echo hello", cwd="/tmp")
            
            assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_with_env(self):
        """Test executing with environment variables."""
        tool = BashTool()
        
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b"output", b""))
        mock_process.returncode = 0
        
        with patch('asyncio.create_subprocess_shell', return_value=mock_process):
            result = await tool.execute(
                command="echo hello",
                env={"MY_VAR": "value"}
            )
            
            assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_with_stderr(self):
        """Test executing command with stderr output."""
        tool = BashTool()
        
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b"stdout", b"stderr"))
        mock_process.returncode = 0
        
        with patch('asyncio.create_subprocess_shell', return_value=mock_process):
            result = await tool.execute(command="some_command")
            
            assert result.success is True
            assert "stdout" in result.output
            assert "stderr" in result.output

    @pytest.mark.asyncio
    async def test_execute_non_zero_exit(self):
        """Test command with non-zero exit code."""
        tool = BashTool()
        
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b"", b"error"))
        mock_process.returncode = 1
        
        with patch('asyncio.create_subprocess_shell', return_value=mock_process):
            result = await tool.execute(command="exit 1")
            
            assert result.success is False
            assert result.error is not None
            assert "exit" in result.error.lower() or "code" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_timeout_exceeded(self):
        """Test command that times out."""
        tool = BashTool(timeout=1)
        
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_process.kill = MagicMock()
        
        with patch('asyncio.create_subprocess_shell', return_value=mock_process):
            with patch('asyncio.wait_for', side_effect=asyncio.TimeoutError()):
                result = await tool.execute(command="sleep 100")
                
                assert result.success is False
                assert "timed out" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_truncates_large_output(self):
        """Test that large output is truncated."""
        tool = BashTool(max_output_size=100)
        
        large_output = b"x" * 200
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(large_output, b""))
        mock_process.returncode = 0
        
        with patch('asyncio.create_subprocess_shell', return_value=mock_process):
            result = await tool.execute(command="cat large_file")
            
            assert result.success is True
            assert len(result.output) <= 150  # Truncated + message
            assert "truncated" in result.output.lower()

    @pytest.mark.asyncio
    async def test_execute_exception(self):
        """Test handling of execution exception."""
        tool = BashTool()
        
        with patch('asyncio.create_subprocess_shell', side_effect=Exception("Process failed")):
            result = await tool.execute(command="bad_command")
            
            assert result.success is False
            assert result.error is not None


class TestSafeBashTool:
    """Tests for SafeBashTool."""

    def test_blocked_patterns_exist(self):
        """Test that blocked patterns are defined."""
        tool = SafeBashTool()
        
        assert len(tool.BLOCKED_PATTERNS) > 0
        assert "rm -rf /" in tool.BLOCKED_PATTERNS

    def test_restricted_commands_exist(self):
        """Test that restricted commands are defined."""
        tool = SafeBashTool()
        
        assert len(tool.RESTRICTED_COMMANDS) > 0
        assert "rm" in tool.RESTRICTED_COMMANDS

    @pytest.mark.asyncio
    async def test_blocks_dangerous_command(self):
        """Test that dangerous commands are blocked."""
        tool = SafeBashTool()
        
        result = await tool.execute(command="rm -rf /")
        
        assert result.success is False
        assert "blocked" in result.error.lower()

    @pytest.mark.asyncio
    async def test_blocks_fork_bomb(self):
        """Test that fork bomb is blocked."""
        tool = SafeBashTool()
        
        result = await tool.execute(command=":(){ :|:& };:")
        
        assert result.success is False
        assert "blocked" in result.error.lower()

    @pytest.mark.asyncio
    async def test_allows_restricted_command(self):
        """Test that restricted commands are allowed with warning."""
        tool = SafeBashTool()
        
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b"deleted", b""))
        mock_process.returncode = 0
        
        with patch('asyncio.create_subprocess_shell', return_value=mock_process):
            result = await tool.execute(command="rm file.txt")
            
            assert result.success is True
            assert result.metadata.get("restricted") is True

    @pytest.mark.asyncio
    async def test_allows_safe_command(self):
        """Test that safe commands are allowed."""
        tool = SafeBashTool()
        
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b"output", b""))
        mock_process.returncode = 0
        
        with patch('asyncio.create_subprocess_shell', return_value=mock_process):
            result = await tool.execute(command="echo hello")
            
            assert result.success is True


class TestCreateBashTool:
    """Tests for create_bash_tool factory function."""

    def test_creates_bash_tool(self):
        """Test that factory creates BashTool instance."""
        tool = create_bash_tool()
        
        assert isinstance(tool, BashTool)

    def test_sets_working_directory(self):
        """Test that factory sets working directory."""
        tool = create_bash_tool(working_directory=Path("/tmp"))
        
        assert tool.working_directory == Path("/tmp")

    def test_default_working_directory(self):
        """Test default working directory."""
        tool = create_bash_tool()
        
        assert tool.working_directory == Path(".")
