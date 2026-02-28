"""
Tests for quick commands module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import tempfile

from opencode.tui.quick_commands import (
    QuickCommand,
    QUICK_COMMANDS,
    get_command,
    get_all_commands,
    set_project_root,
    get_project_root,
    execute_command,
    execute_help_command,
    execute_status_command,
    execute_clear_command,
    execute_theme_command,
)


class TestQuickCommand:
    """Tests for QuickCommand class."""

    def test_quick_command_creation(self):
        """Test creating a QuickCommand."""
        cmd = QuickCommand("test", "Test command", ["t", "testing"])
        assert cmd.name == "test"
        assert cmd.description == "Test command"
        assert cmd.aliases == ["t", "testing"]

    def test_quick_command_creation_no_aliases(self):
        """Test creating a QuickCommand without aliases."""
        cmd = QuickCommand("test", "Test command")
        assert cmd.aliases == []

    def test_quick_command_get_usage(self):
        """Test get_usage method."""
        cmd = QuickCommand("help", "Show help", ["?", "commands"])
        usage = cmd.get_usage()
        assert "/help" in usage

    def test_quick_command_get_usage_with_aliases(self):
        """Test get_usage with aliases."""
        cmd = QuickCommand("help", "Show help", ["?"])
        usage = cmd.get_usage()
        assert "/?" in usage


class TestQuickCommandsList:
    """Tests for quick commands list."""

    def test_quick_commands_not_empty(self):
        """Test that QUICK_COMMANDS is not empty."""
        assert len(QUICK_COMMANDS) > 0

    def test_quick_commands_has_help(self):
        """Test that help command exists."""
        help_cmd = get_command("help")
        assert help_cmd is not None
        assert help_cmd.name == "help"

    def test_quick_commands_has_index(self):
        """Test that index command exists."""
        index_cmd = get_command("index")
        assert index_cmd is not None
        assert index_cmd.name == "index"

    def test_quick_commands_has_plans(self):
        """Test that plans command exists."""
        plans_cmd = get_command("plans")
        assert plans_cmd is not None
        assert plans_cmd.name == "plans"

    def test_quick_commands_has_docs(self):
        """Test that docs command exists."""
        docs_cmd = get_command("docs")
        assert docs_cmd is not None
        assert docs_cmd.name == "docs"

    def test_quick_commands_has_files(self):
        """Test that files command exists."""
        files_cmd = get_command("files")
        assert files_cmd is not None
        assert files_cmd.name == "files"

    def test_quick_commands_has_tools(self):
        """Test that tools command exists."""
        tools_cmd = get_command("tools")
        assert tools_cmd is not None
        assert tools_cmd.name == "tools"

    def test_quick_commands_has_agents(self):
        """Test that agents command exists."""
        agents_cmd = get_command("agents")
        assert agents_cmd is not None
        assert agents_cmd.name == "agents"

    def test_quick_commands_has_status(self):
        """Test that status command exists."""
        status_cmd = get_command("status")
        assert status_cmd is not None
        assert status_cmd.name == "status"

    def test_quick_commands_has_clear(self):
        """Test that clear command exists."""
        clear_cmd = get_command("clear")
        assert clear_cmd is not None
        assert clear_cmd.name == "clear"

    def test_quick_commands_has_theme(self):
        """Test that theme command exists."""
        theme_cmd = get_command("theme")
        assert theme_cmd is not None
        assert theme_cmd.name == "theme"


class TestGetCommand:
    """Tests for get_command function."""

    def test_get_command_by_name(self):
        """Test getting command by name."""
        cmd = get_command("help")
        assert cmd is not None
        assert cmd.name == "help"

    def test_get_command_by_alias(self):
        """Test getting command by alias."""
        cmd = get_command("?")
        assert cmd is not None
        assert cmd.name == "help"

    def test_get_command_not_found(self):
        """Test getting non-existent command."""
        cmd = get_command("nonexistent")
        assert cmd is None

    def test_get_command_strips_slash(self):
        """Test that slash is stripped from command."""
        cmd = get_command("/help")
        assert cmd is not None
        assert cmd.name == "help"

    def test_get_command_case_insensitive(self):
        """Test case insensitive command lookup."""
        cmd = get_command("HELP")
        assert cmd is not None
        assert cmd.name == "help"


class TestGetAllCommands:
    """Tests for get_all_commands function."""

    def test_get_all_commands_returns_list(self):
        """Test get_all_commands returns a list."""
        commands = get_all_commands()
        assert isinstance(commands, list)

    def test_get_all_commands_contains_all(self):
        """Test get_all_commands contains expected commands."""
        commands = get_all_commands()
        names = [cmd.name for cmd in commands]
        assert "help" in names
        assert "index" in names
        assert "plans" in names


class TestProjectRoot:
    """Tests for project root functions."""

    def test_set_project_root(self):
        """Test setting project root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            set_project_root(root)
            assert get_project_root() == root

    def test_get_project_root_not_set(self):
        """Test get_project_root when not set."""
        # Reset to None
        import opencode.tui.quick_commands as qc
        qc._project_root = None
        assert get_project_root() is None


class TestExecuteHelpCommand:
    """Tests for execute_help_command function."""

    @pytest.mark.asyncio
    async def test_execute_help_command(self):
        """Test help command execution."""
        result = await execute_help_command()
        assert "Quick Commands" in result
        assert "/help" in result


class TestExecuteStatusCommand:
    """Tests for execute_status_command function."""

    @pytest.mark.asyncio
    async def test_execute_status_command(self):
        """Test status command execution."""
        result = await execute_status_command()
        assert "System Status" in result
        assert "Ready" in result


class TestExecuteClearCommand:
    """Tests for execute_clear_command function."""

    @pytest.mark.asyncio
    async def test_execute_clear_command(self):
        """Test clear command execution."""
        result = await execute_clear_command()
        assert result == "__CLEAR__"


class TestExecuteThemeCommand:
    """Tests for execute_theme_command function."""

    @pytest.mark.asyncio
    async def test_execute_theme_command_no_args(self):
        """Test theme command without arguments."""
        result = await execute_theme_command("")
        assert "themes:" in result

    @pytest.mark.asyncio
    async def test_execute_theme_command_valid(self):
        """Test theme command with valid theme."""
        result = await execute_theme_command("dark")
        assert result == "__THEME__dark"

    @pytest.mark.asyncio
    async def test_execute_theme_command_invalid(self):
        """Test theme command with invalid theme."""
        result = await execute_theme_command("invalid")
        assert "Unknown theme" in result


class TestExecuteCommand:
    """Tests for execute_command function."""

    @pytest.mark.asyncio
    async def test_execute_non_command(self):
        """Test executing a non-command message."""
        result, is_command = await execute_command("Hello world")
        assert result == ""
        assert is_command is False

    @pytest.mark.asyncio
    async def test_execute_help_command(self):
        """Test executing help command."""
        result, is_command = await execute_command("/help")
        assert is_command is True
        assert "Quick Commands" in result

    @pytest.mark.asyncio
    async def test_execute_status_command(self):
        """Test executing status command."""
        result, is_command = await execute_command("/status")
        assert is_command is True
        assert "System Status" in result

    @pytest.mark.asyncio
    async def test_execute_clear_command(self):
        """Test executing clear command."""
        result, is_command = await execute_command("/clear")
        assert is_command is True
        assert result == "__CLEAR__"

    @pytest.mark.asyncio
    async def test_execute_theme_command(self):
        """Test executing theme command."""
        result, is_command = await execute_command("/theme dark")
        assert is_command is True
        assert result == "__THEME__dark"

    @pytest.mark.asyncio
    async def test_execute_unknown_command(self):
        """Test executing unknown command."""
        result, is_command = await execute_command("/unknown")
        assert is_command is True
        assert "Unknown command" in result

    @pytest.mark.asyncio
    async def test_execute_whitespace_command(self):
        """Test executing whitespace-only message."""
        result, is_command = await execute_command("   ")
        assert result == ""
        assert is_command is False
