"""
Tests for skills CLI commands module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import tempfile

from click.testing import CliRunner
from typer.testing import CliRunner as TyperRunner


class TestSkillsCLIExists:
    """Tests for skills CLI module existence."""

    def test_skills_cli_module_can_be_imported(self):
        """Test skills CLI can be imported."""
        try:
            from opencode.cli.commands.skills import app
            assert app is not None
        except ImportError:
            pytest.skip("Skills CLI module not found")

    def test_skills_cli_has_setup_command(self):
        """Test skills CLI has setup command."""
        from opencode.cli.commands.skills import app
        # Verify app has commands
        commands = list(app.registered_commands)
        command_names = [c.name for c in commands]
        assert "setup" in command_names or any("setup" in str(c) for c in commands)

    def test_skills_cli_has_migrate_command(self):
        """Test skills CLI has migrate command."""
        from opencode.cli.commands.skills import app
        commands = list(app.registered_commands)
        command_names = [c.name for c in commands]
        assert "migrate" in command_names or any("migrate" in str(c) for c in commands)

    def test_skills_cli_has_generate_command(self):
        """Test skills CLI has generate command."""
        from opencode.cli.commands.skills import app
        commands = list(app.registered_commands)
        command_names = [c.name for c in commands]
        assert "generate" in command_names or any("generate" in str(c) for c in commands)

    def test_skills_cli_has_list_command(self):
        """Test skills CLI has list command."""
        from opencode.cli.commands.skills import app
        commands = list(app.registered_commands)
        command_names = [c.name for c in commands]
        assert "list" in command_names or any("list" in str(c) for c in commands)

    def test_skills_cli_has_stats_command(self):
        """Test skills CLI has stats command."""
        from opencode.cli.commands.skills import app
        commands = list(app.registered_commands)
        command_names = [c.name for c in commands]
        assert "stats" in command_names or any("stats" in str(c) for c in commands)

    def test_skills_cli_has_categorize_command(self):
        """Test skills CLI has categorize command."""
        from opencode.cli.commands.skills import app
        commands = list(app.registered_commands)
        command_names = [c.name for c in commands]
        assert "categorize" in command_names or any("categorize" in str(c) for c in commands)

    def test_skills_cli_has_categories_command(self):
        """Test skills CLI has categories command."""
        from opencode.cli.commands.skills import app
        commands = list(app.registered_commands)
        command_names = [c.name for c in commands]
        assert "categories" in command_names or any("categories" in str(c) for c in commands)

    def test_skills_cli_has_revert_command(self):
        """Test skills CLI has revert command."""
        from opencode.cli.commands.skills import app
        commands = list(app.registered_commands)
        command_names = [c.name for c in commands]
        assert "revert" in command_names or any("revert" in str(c) for c in commands)


class TestSkillsCLICommands:
    """Tests for skills CLI commands."""

    def test_skills_setup_dry_run(self):
        """Test skills setup --dry-run."""
        from opencode.cli.commands.skills import setup_skillpointer
        # Just verify the function exists and is callable
        assert callable(setup_skillpointer)

    def test_skills_migrate_command(self):
        """Test skills migrate command."""
        from opencode.cli.commands.skills import migrate_skills
        assert callable(migrate_skills)

    def test_skills_generate_command(self):
        """Test skills generate command."""
        from opencode.cli.commands.skills import generate_pointers
        assert callable(generate_pointers)

    def test_skills_list_command(self):
        """Test skills list command."""
        from opencode.cli.commands.skills import list_categories
        assert callable(list_categories)

    def test_skills_stats_command(self):
        """Test skills stats command."""
        from opencode.cli.commands.skills import show_stats
        assert callable(show_stats)

    def test_skills_categorize_command(self):
        """Test skills categorize command."""
        from opencode.cli.commands.skills import categorize
        assert callable(categorize)

    def test_skills_categories_command(self):
        """Test skills categories command."""
        from opencode.cli.commands.skills import list_all_categories
        assert callable(list_all_categories)

    def test_skills_revert_command(self):
        """Test skills revert command."""
        from opencode.cli.commands.skills import revert_pointers
        assert callable(revert_pointers)
