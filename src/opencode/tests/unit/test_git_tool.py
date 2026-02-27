"""
Tests for Git Tool.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path

from opencode.tool.git import GitTool
from opencode.tool.base import PermissionLevel, ToolResult


@pytest.mark.unit
class TestGitTool:
    """Tests for GitTool."""

    def test_tool_name(self):
        """Test tool name property."""
        tool = GitTool()
        assert tool.name == "git"

    def test_tool_description(self):
        """Test tool description property."""
        tool = GitTool()
        assert "git" in tool.description.lower()
        assert "status" in tool.description.lower()
        assert "commit" in tool.description.lower()

    def test_tool_parameters(self):
        """Test tool parameters property."""
        tool = GitTool()
        params = tool.parameters
        assert params["type"] == "object"
        assert "operation" in params["properties"]
        assert params["required"] == ["operation"]

    def test_tool_permission_level(self):
        """Test tool permission level property."""
        tool = GitTool()
        assert tool.permission_level == PermissionLevel.WRITE

    @pytest.mark.asyncio
    async def test_run_git(self):
        """Test _run_git method."""
        tool = GitTool()

        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "output"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            returncode, stdout, stderr = await tool._run_git(Path.cwd(), ["status"])

            assert returncode == 0
            assert stdout == "output"
            assert stderr == ""

    @pytest.mark.asyncio
    async def test_git_status_success(self):
        """Test _git_status with successful result."""
        tool = GitTool()

        with patch.object(tool, '_run_git', new_callable=AsyncMock) as mock_run:
            # "M " means staged (M followed by space), "??" means untracked
            mock_run.return_value = (0, "M  file1.py\n?? file2.py\n", "")

            result = await tool._git_status(Path.cwd())

            assert result.success is True
            assert "file1.py" in result.output
            assert "file2.py" in result.output

    @pytest.mark.asyncio
    async def test_git_status_clean(self):
        """Test _git_status with clean working tree."""
        tool = GitTool()

        with patch.object(tool, '_run_git', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = (0, "", "")

            result = await tool._git_status(Path.cwd())

            assert result.success is True
            assert "clean" in result.output.lower()

    @pytest.mark.asyncio
    async def test_git_status_error(self):
        """Test _git_status with error."""
        tool = GitTool()

        with patch.object(tool, '_run_git', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = (1, "", "Not a git repository")

            result = await tool._git_status(Path.cwd())

            assert result.success is False
            assert result.error is not None

    @pytest.mark.asyncio
    async def test_git_diff_success(self):
        """Test _git_diff with successful result."""
        tool = GitTool()

        with patch.object(tool, '_run_git', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = (0, "+ added line\n- removed line\n", "")

            result = await tool._git_diff(Path.cwd(), ".")

            assert result.success is True
            assert "Diff" in result.output

    @pytest.mark.asyncio
    async def test_git_diff_no_changes(self):
        """Test _git_diff with no changes."""
        tool = GitTool()

        with patch.object(tool, '_run_git', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = (0, "", "")

            result = await tool._git_diff(Path.cwd(), ".")

            assert result.success is True
            assert "No differences" in result.output

    @pytest.mark.asyncio
    async def test_git_diff_error(self):
        """Test _git_diff with error."""
        tool = GitTool()

        with patch.object(tool, '_run_git', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = (1, "", "Error")

            result = await tool._git_diff(Path.cwd(), ".")

            assert result.success is False

    @pytest.mark.asyncio
    async def test_git_diff_truncation(self):
        """Test _git_diff truncates long output."""
        tool = GitTool()

        long_output = "x" * 6000
        with patch.object(tool, '_run_git', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = (0, long_output, "")

            result = await tool._git_diff(Path.cwd(), ".")

            assert result.success is True
            assert "truncated" in result.output

    @pytest.mark.asyncio
    async def test_git_log_success(self):
        """Test _git_log with successful result."""
        tool = GitTool()

        with patch.object(tool, '_run_git', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = (0, "abc123 Commit message\ndef456 Another commit\n", "")

            result = await tool._git_log(Path.cwd(), 10)

            assert result.success is True
            assert "Log" in result.output
            assert "abc123" in result.output

    @pytest.mark.asyncio
    async def test_git_log_no_commits(self):
        """Test _git_log with no commits."""
        tool = GitTool()

        with patch.object(tool, '_run_git', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = (0, "", "")

            result = await tool._git_log(Path.cwd(), 10)

            assert result.success is True
            assert "No commits" in result.output

    @pytest.mark.asyncio
    async def test_git_log_error(self):
        """Test _git_log with error."""
        tool = GitTool()

        with patch.object(tool, '_run_git', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = (1, "", "Error")

            result = await tool._git_log(Path.cwd(), 10)

            assert result.success is False

    @pytest.mark.asyncio
    async def test_git_branch_list(self):
        """Test _git_branch listing branches."""
        tool = GitTool()

        with patch.object(tool, '_run_git', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = (0, "* main\n  develop\n", "")

            result = await tool._git_branch(Path.cwd(), None)

            assert result.success is True
            assert "Branches" in result.output

    @pytest.mark.asyncio
    async def test_git_branch_create(self):
        """Test _git_branch creating a new branch."""
        tool = GitTool()

        with patch.object(tool, '_run_git', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = (0, "", "")

            result = await tool._git_branch(Path.cwd(), "new-feature")

            assert result.success is True
            assert "new-feature" in result.output

    @pytest.mark.asyncio
    async def test_git_branch_create_error(self):
        """Test _git_branch creating a branch with error."""
        tool = GitTool()

        with patch.object(tool, '_run_git', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = (1, "", "Branch already exists")

            result = await tool._git_branch(Path.cwd(), "existing-branch")

            assert result.success is False

    @pytest.mark.asyncio
    async def test_git_add_success(self):
        """Test _git_add with successful result."""
        tool = GitTool()

        with patch.object(tool, '_run_git', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = (0, "", "")

            result = await tool._git_add(Path.cwd(), ["file1.py", "file2.py"])

            assert result.success is True
            assert "2" in result.output

    @pytest.mark.asyncio
    async def test_git_add_error(self):
        """Test _git_add with error."""
        tool = GitTool()

        with patch.object(tool, '_run_git', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = (1, "", "Error")

            result = await tool._git_add(Path.cwd(), ["file.py"])

            assert result.success is False

    @pytest.mark.asyncio
    async def test_git_commit_success(self):
        """Test _git_commit with successful result."""
        tool = GitTool()

        with patch.object(tool, '_run_git', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = (0, "", "")

            result = await tool._git_commit(Path.cwd(), "Test commit")

            assert result.success is True
            assert "Test commit" in result.output

    @pytest.mark.asyncio
    async def test_git_commit_error(self):
        """Test _git_commit with error."""
        tool = GitTool()

        with patch.object(tool, '_run_git', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = (1, "", "Nothing to commit")

            result = await tool._git_commit(Path.cwd(), "Test commit")

            assert result.success is False

    @pytest.mark.asyncio
    async def test_git_checkout_success(self):
        """Test _git_checkout with successful result."""
        tool = GitTool()

        with patch.object(tool, '_run_git', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = (0, "", "")

            result = await tool._git_checkout(Path.cwd(), "develop")

            assert result.success is True
            assert "develop" in result.output

    @pytest.mark.asyncio
    async def test_git_checkout_error(self):
        """Test _git_checkout with error."""
        tool = GitTool()

        with patch.object(tool, '_run_git', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = (1, "", "Branch not found")

            result = await tool._git_checkout(Path.cwd(), "nonexistent")

            assert result.success is False

    @pytest.mark.asyncio
    async def test_git_pull_success(self):
        """Test _git_pull with successful result."""
        tool = GitTool()

        with patch.object(tool, '_run_git', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = (0, "Updated 2 files", "")

            result = await tool._git_pull(Path.cwd())

            assert result.success is True
            assert "Updated" in result.output

    @pytest.mark.asyncio
    async def test_git_pull_up_to_date(self):
        """Test _git_pull when already up to date."""
        tool = GitTool()

        with patch.object(tool, '_run_git', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = (0, "", "")

            result = await tool._git_pull(Path.cwd())

            assert result.success is True
            assert "up to date" in result.output.lower()

    @pytest.mark.asyncio
    async def test_git_pull_error(self):
        """Test _git_pull with error."""
        tool = GitTool()

        with patch.object(tool, '_run_git', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = (1, "", "Connection refused")

            result = await tool._git_pull(Path.cwd())

            assert result.success is False

    @pytest.mark.asyncio
    async def test_git_push_success(self):
        """Test _git_push with successful result."""
        tool = GitTool()

        with patch.object(tool, '_run_git', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = (0, "Pushed to origin", "")

            result = await tool._git_push(Path.cwd())

            assert result.success is True

    @pytest.mark.asyncio
    async def test_git_push_error(self):
        """Test _git_push with error."""
        tool = GitTool()

        with patch.object(tool, '_run_git', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = (1, "", "Push rejected")

            result = await tool._git_push(Path.cwd())

            assert result.success is False

    @pytest.mark.asyncio
    async def test_git_init_success(self):
        """Test _git_init with successful result."""
        tool = GitTool()

        with patch.object(tool, '_run_git', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = (0, "", "")

            result = await tool._git_init(Path.cwd())

            assert result.success is True
            assert "Initialized" in result.output

    @pytest.mark.asyncio
    async def test_git_init_error(self):
        """Test _git_init with error."""
        tool = GitTool()

        with patch.object(tool, '_run_git', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = (1, "", "Permission denied")

            result = await tool._git_init(Path.cwd())

            assert result.success is False


@pytest.mark.unit
class TestGitToolExecute:
    """Tests for GitTool.execute method."""

    @pytest.mark.asyncio
    async def test_execute_status(self):
        """Test execute with status operation."""
        tool = GitTool()

        with patch.object(tool, '_git_status', new_callable=AsyncMock) as mock_status:
            mock_status.return_value = ToolResult.ok("Status output")

            result = await tool.execute(operation="status")

            mock_status.assert_called_once()
            assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_diff(self):
        """Test execute with diff operation."""
        tool = GitTool()

        with patch.object(tool, '_git_diff', new_callable=AsyncMock) as mock_diff:
            mock_diff.return_value = ToolResult.ok("Diff output")

            result = await tool.execute(operation="diff", path="file.py")

            mock_diff.assert_called_once()
            assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_log(self):
        """Test execute with log operation."""
        tool = GitTool()

        with patch.object(tool, '_git_log', new_callable=AsyncMock) as mock_log:
            mock_log.return_value = ToolResult.ok("Log output")

            result = await tool.execute(operation="log", limit=5)

            mock_log.assert_called_once()
            assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_branch_list(self):
        """Test execute with branch list operation."""
        tool = GitTool()

        with patch.object(tool, '_git_branch', new_callable=AsyncMock) as mock_branch:
            mock_branch.return_value = ToolResult.ok("Branches")

            result = await tool.execute(operation="branch")

            mock_branch.assert_called_once()
            assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_branch_create(self):
        """Test execute with branch create operation."""
        tool = GitTool()

        with patch.object(tool, '_git_branch', new_callable=AsyncMock) as mock_branch:
            mock_branch.return_value = ToolResult.ok("Created branch")

            result = await tool.execute(operation="branch", branch="new-branch")

            mock_branch.assert_called_once()
            assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_add(self):
        """Test execute with add operation."""
        tool = GitTool()

        with patch.object(tool, '_git_add', new_callable=AsyncMock) as mock_add:
            mock_add.return_value = ToolResult.ok("Added files")

            result = await tool.execute(operation="add", files=["file1.py"])

            mock_add.assert_called_once()
            assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_commit_no_message(self):
        """Test execute with commit operation but no message."""
        tool = GitTool()

        result = await tool.execute(operation="commit")

        assert result.success is False
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_execute_commit_with_message(self):
        """Test execute with commit operation and message."""
        tool = GitTool()

        with patch.object(tool, '_git_commit', new_callable=AsyncMock) as mock_commit:
            mock_commit.return_value = ToolResult.ok("Committed")

            result = await tool.execute(operation="commit", message="Test commit")

            mock_commit.assert_called_once()
            assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_checkout_no_branch(self):
        """Test execute with checkout operation but no branch."""
        tool = GitTool()

        result = await tool.execute(operation="checkout")

        assert result.success is False
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_execute_checkout_with_branch(self):
        """Test execute with checkout operation and branch."""
        tool = GitTool()

        with patch.object(tool, '_git_checkout', new_callable=AsyncMock) as mock_checkout:
            mock_checkout.return_value = ToolResult.ok("Switched")

            result = await tool.execute(operation="checkout", branch="develop")

            mock_checkout.assert_called_once()
            assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_pull(self):
        """Test execute with pull operation."""
        tool = GitTool()

        with patch.object(tool, '_git_pull', new_callable=AsyncMock) as mock_pull:
            mock_pull.return_value = ToolResult.ok("Pulled")

            result = await tool.execute(operation="pull")

            mock_pull.assert_called_once()
            assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_push(self):
        """Test execute with push operation."""
        tool = GitTool()

        with patch.object(tool, '_git_push', new_callable=AsyncMock) as mock_push:
            mock_push.return_value = ToolResult.ok("Pushed")

            result = await tool.execute(operation="push")

            mock_push.assert_called_once()
            assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_init(self):
        """Test execute with init operation."""
        tool = GitTool()

        with patch.object(tool, '_git_init', new_callable=AsyncMock) as mock_init:
            mock_init.return_value = ToolResult.ok("Initialized")

            result = await tool.execute(operation="init")

            mock_init.assert_called_once()
            assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_unknown_operation(self):
        """Test execute with unknown operation."""
        tool = GitTool()

        result = await tool.execute(operation="unknown")

        assert result.success is False
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_execute_git_not_found(self):
        """Test execute when git is not installed."""
        tool = GitTool()

        with patch.object(tool, '_git_status', side_effect=FileNotFoundError("git not found")):
            result = await tool.execute(operation="status")

            assert result.success is False
            assert result.error is not None

    @pytest.mark.asyncio
    async def test_execute_exception(self):
        """Test execute with unexpected exception."""
        tool = GitTool()

        with patch.object(tool, '_git_status', side_effect=Exception("Unexpected error")):
            result = await tool.execute(operation="status")

            assert result.success is False
            assert result.error is not None
