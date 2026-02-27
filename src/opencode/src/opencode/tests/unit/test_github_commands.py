"""Tests for GitHub CLI commands."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest
from typer.testing import CliRunner

from opencode.cli.commands.github import app, run_command, LFS_GITATTRIBUTES

runner = CliRunner()


class TestRunCommand:
    """Tests for run_command function."""

    def test_run_command_success(self):
        """Test successful command execution."""
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            result = run_command(["git", "status"])

            assert result.returncode == 0
            mock_run.assert_called_once()

    def test_run_command_with_capture(self):
        """Test command execution with output capture."""
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "output"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            result = run_command(["git", "status"], capture=True)

            assert result.returncode == 0
            mock_run.assert_called_once_with(
                ["git", "status"], capture_output=True, text=True, check=False, cwd=None
            )

    def test_run_command_failure_with_check(self):
        """Test command failure with check=True raises Exit."""
        from click.exceptions import Exit

        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stderr = "error message"
            mock_run.return_value = mock_result

            with pytest.raises(Exit) as exc_info:
                run_command(["git", "invalid"], check=True)

            assert exc_info.value.exit_code == 1

    def test_run_command_failure_without_check(self):
        """Test command failure with check=False returns result."""
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stderr = "error message"
            mock_run.return_value = mock_result

            result = run_command(["git", "invalid"], check=False)

            assert result.returncode == 1


class TestInitGithub:
    """Tests for init_github command."""

    def test_init_already_exists(self):
        """Test init when git already exists."""
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = True

            result = runner.invoke(app, ["init"])

            assert "already exists" in result.output

    def test_init_without_lfs(self):
        """Test init without LFS."""
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.side_effect = [False, False]  # .git, .gitattributes
            with patch("opencode.cli.commands.github.run_command") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)

                result = runner.invoke(app, ["init", "--no-lfs"])

                assert "initialized successfully" in result.output
                # Check git init was called
                assert any("init" in str(call) for call in mock_run.call_args_list)

    def test_init_with_lfs_success(self):
        """Test init with LFS configured successfully."""
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.side_effect = [False, False]  # .git, .gitattributes
            with patch("opencode.cli.commands.github.run_command") as mock_run:
                # Setup mock returns
                mock_run.return_value = MagicMock(returncode=0)
                with patch("pathlib.Path.write_text") as mock_write:
                    result = runner.invoke(app, ["init", "--lfs"])

                    assert "initialized successfully" in result.output
                    # Check git lfs install was called
                    assert any("lfs" in str(call) for call in mock_run.call_args_list)

    def test_init_with_lfs_not_installed(self):
        """Test init when LFS is not installed."""
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.side_effect = [False, False]
            with patch("opencode.cli.commands.github.run_command") as mock_run:
                # First call (git init) succeeds, second (lfs install) fails
                mock_results = [
                    MagicMock(returncode=0),
                    MagicMock(returncode=1)
                ]
                mock_run.side_effect = mock_results

                result = runner.invoke(app, ["init", "--lfs"])

                assert "LFS not found" in result.output
                assert result.exit_code == 1


class TestPushToGithub:
    """Tests for push_to_github command."""

    def test_push_not_git_repo(self):
        """Test push when not in a git repo."""
        with patch("opencode.cli.commands.github.run_command") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_run.return_value = mock_result

            result = runner.invoke(app, ["push", "-m", "test message"])

            assert "not initialized" in result.output
            assert result.exit_code == 1

    def test_push_no_changes(self):
        """Test push when there are no changes."""
        with patch("opencode.cli.commands.github.run_command") as mock_run:
            # git rev-parse succeeds
            mock_results = [
                MagicMock(returncode=0, stdout=".git"),  # rev-parse
                MagicMock(returncode=0, stdout=""),  # status --porcelain
            ]
            mock_run.side_effect = mock_results

            result = runner.invoke(app, ["push", "-m", "test message"])

            assert "No changes to commit" in result.output

    def test_push_with_message_success(self):
        """Test push with message succeeds."""
        with patch("opencode.cli.commands.github.run_command") as mock_run:
            mock_results = [
                MagicMock(returncode=0, stdout=".git"),  # rev-parse
                MagicMock(returncode=0, stdout="M file.txt"),  # status
                MagicMock(returncode=0),  # git add
                MagicMock(returncode=0),  # git commit
                MagicMock(returncode=0),  # git push
            ]
            mock_run.side_effect = mock_results

            result = runner.invoke(app, ["push", "-m", "test message"])

            assert "Successfully pushed" in result.output

    def test_push_with_message_push_fails(self):
        """Test push when push fails."""
        with patch("opencode.cli.commands.github.run_command") as mock_run:
            mock_results = [
                MagicMock(returncode=0, stdout=".git"),  # rev-parse
                MagicMock(returncode=0, stdout="M file.txt"),  # status
                MagicMock(returncode=0),  # git add
                MagicMock(returncode=0),  # git commit
                MagicMock(returncode=1),  # git push fails
            ]
            mock_run.side_effect = mock_results

            result = runner.invoke(app, ["push", "-m", "test message"])

            assert "Push failed" in result.output
            assert result.exit_code == 1


class TestGithubStatus:
    """Tests for github_status command."""

    def test_status_not_git_repo(self):
        """Test status when not in a git repo."""
        with patch("opencode.cli.commands.github.run_command") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_run.return_value = mock_result

            result = runner.invoke(app, ["status"])

            assert "Not a git repository" in result.output

    def test_status_success(self):
        """Test status command success."""
        with patch("opencode.cli.commands.github.run_command") as mock_run:
            mock_results = [
                MagicMock(returncode=0, stdout=".git"),  # rev-parse
                MagicMock(returncode=0, stdout="main"),  # branch
                MagicMock(returncode=0, stdout="https://github.com/user/repo.git"),  # remote
                MagicMock(returncode=0, stdout="git-lfs/3.0.0"),  # lfs version
                MagicMock(returncode=0, stdout="count: 10\nsize: 1.2 KiB"),  # count-objects
                MagicMock(returncode=0),  # git status --short
            ]
            mock_run.side_effect = mock_results

            result = runner.invoke(app, ["status"])

            assert "Git Repository Status" in result.output


class TestConfigureRemote:
    """Tests for configure_remote command."""

    def test_configure_remote_add_new(self):
        """Test adding a new remote."""
        with patch("opencode.cli.commands.github.run_command") as mock_run:
            # get-url fails (remote doesn't exist)
            mock_results = [
                MagicMock(returncode=1),  # get-url fails
                MagicMock(returncode=0),  # remote add
            ]
            mock_run.side_effect = mock_results

            result = runner.invoke(app, ["remote", "https://github.com/user/repo.git"])

            assert "Added remote" in result.output

    def test_configure_remote_update_existing(self):
        """Test updating an existing remote."""
        with patch("opencode.cli.commands.github.run_command") as mock_run:
            mock_results = [
                MagicMock(returncode=0, stdout="https://github.com/old/repo.git"),  # get-url
                MagicMock(returncode=0),  # set-url
            ]
            mock_run.side_effect = mock_results

            result = runner.invoke(app, ["remote", "https://github.com/user/newrepo.git"])

            assert "Updated remote" in result.output

    def test_configure_remote_with_custom_name(self):
        """Test configuring remote with custom name."""
        with patch("opencode.cli.commands.github.run_command") as mock_run:
            mock_results = [
                MagicMock(returncode=1),  # get-url fails
                MagicMock(returncode=0),  # remote add
            ]
            mock_run.side_effect = mock_results

            result = runner.invoke(
                app, ["remote", "https://github.com/user/repo.git", "-n", "upstream"]
            )

            assert "Added remote 'upstream'" in result.output


class TestCreateGitattributes:
    """Tests for create_gitattributes command."""

    def test_create_gitattributes_new(self):
        """Test creating new .gitattributes file."""
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = False
            with patch("pathlib.Path.write_text") as mock_write:
                result = runner.invoke(app, ["create-attributes"])

                assert "Created .gitattributes" in result.output
                mock_write.assert_called_once_with(LFS_GITATTRIBUTES)

    def test_create_gitattributes_exists_no_force(self):
        """Test when .gitattributes already exists without force."""
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = True

            result = runner.invoke(app, ["create-attributes"])

            assert "already exists" in result.output

    def test_create_gitattributes_exists_with_force(self):
        """Test overwriting .gitattributes with force."""
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = True
            with patch("pathlib.Path.write_text") as mock_write:
                result = runner.invoke(app, ["create-attributes", "--force"])

                assert "Created .gitattributes" in result.output
                mock_write.assert_called_once_with(LFS_GITATTRIBUTES)


class TestLFSGitattributes:
    """Tests for LFS_GITATTRIBUTES constant."""

    def test_lfs_gitattributes_content(self):
        """Test LFS_GITATTRIBUTES has expected content."""
        assert "filter=lfs" in LFS_GITATTRIBUTES
        assert "*.dll" in LFS_GITATTRIBUTES
        assert "*.png" in LFS_GITATTRIBUTES
        assert "*.pt" in LFS_GITATTRIBUTES
        assert "*.safetensors" in LFS_GITATTRIBUTES
