"""
Tests for CLI index commands.
"""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import time

from opencode.cli.commands.index import (
    app,
    generate_index,
    index_status,
    show_index,
    list_indexes,
    clean_indexes,
)


class TestGenerateIndex:
    """Tests for generate_index command."""
    
    @patch("opencode.cli.commands.index.IndexGenerator")
    @patch("opencode.cli.commands.index.IndexConfig")
    @patch("opencode.cli.commands.index.console")
    def test_generate_index_not_a_directory(self, mock_console, mock_config_class, mock_generator_class):
        """Test generate_index when path is not a directory."""
        import typer
        
        mock_path = MagicMock()
        mock_path.is_dir.return_value = False
        mock_path.resolve.return_value = mock_path
        
        with pytest.raises(typer.Exit):
            generate_index(path=mock_path)
    
    @patch("opencode.cli.commands.index.IndexGenerator")
    @patch("opencode.cli.commands.index.IndexConfig")
    @patch("opencode.cli.commands.index.console")
    def test_generate_index_fresh_index(self, mock_console, mock_config_class, mock_generator_class):
        """Test generate_index when index is fresh."""
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config
        
        mock_generator = MagicMock()
        mock_generator.is_index_fresh.return_value = True
        mock_generator_class.return_value = mock_generator
        
        mock_path = MagicMock()
        mock_path.is_dir.return_value = True
        mock_path.resolve.return_value = mock_path
        mock_path.__truediv__ = MagicMock()
        
        generate_index(path=mock_path)
        
        # Should print message about fresh index
        assert mock_console.print.called
    
    @patch("opencode.cli.commands.index.IndexGenerator")
    @patch("opencode.cli.commands.index.IndexConfig")
    @patch("opencode.cli.commands.index.console")
    def test_generate_index_up_to_date(self, mock_console, mock_config_class, mock_generator_class):
        """Test generate_index when index is up to date."""
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config
        
        mock_generator = MagicMock()
        mock_generator.is_index_fresh.return_value = False
        mock_generator.is_index_stale.return_value = False
        mock_generator_class.return_value = mock_generator
        
        mock_path = MagicMock()
        mock_path.is_dir.return_value = True
        mock_path.resolve.return_value = mock_path
        
        generate_index(path=mock_path)
        
        # Should print message about up-to-date index
        assert mock_console.print.called
    
    @patch("opencode.cli.commands.index.IndexGenerator")
    @patch("opencode.cli.commands.index.IndexConfig")
    @patch("opencode.cli.commands.index.console")
    def test_generate_index_force(self, mock_console, mock_config_class, mock_generator_class):
        """Test generate_index with force flag."""
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config
        
        # Create mock index result
        mock_index = MagicMock()
        mock_index.project_name = "test-project"
        mock_index.project_type.value = "python"
        mock_index.branch = "main"
        mock_index.commit = "abc123"
        mock_index.file_counts = {"py": 10}
        mock_index.test_files = {"py": 5}
        
        mock_generator = MagicMock()
        mock_generator.generate.return_value = mock_index
        mock_generator.save_index.return_value = Path("/path/to/index.md")
        mock_generator_class.return_value = mock_generator
        
        mock_path = MagicMock()
        mock_path.is_dir.return_value = True
        mock_path.resolve.return_value = mock_path
        mock_path.name = "test-project"
        
        generate_index(path=mock_path, force=True)
        
        # Should call generate
        assert mock_generator.generate.called
        assert mock_generator.save_index.called
    
    @patch("opencode.cli.commands.index.IndexGenerator")
    @patch("opencode.cli.commands.index.IndexConfig")
    @patch("opencode.cli.commands.index.console")
    def test_generate_index_error(self, mock_console, mock_config_class, mock_generator_class):
        """Test generate_index when error occurs."""
        import typer
        
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config
        
        mock_generator = MagicMock()
        mock_generator.generate.side_effect = Exception("Test error")
        mock_generator_class.return_value = mock_generator
        
        mock_path = MagicMock()
        mock_path.is_dir.return_value = True
        mock_path.resolve.return_value = mock_path
        mock_path.name = "test-project"
        
        with pytest.raises(typer.Exit):
            generate_index(path=mock_path, force=True)


class TestIndexStatus:
    """Tests for index_status command."""
    
    @patch("opencode.cli.commands.index.IndexGenerator")
    @patch("opencode.cli.commands.index.IndexConfig")
    @patch("opencode.cli.commands.index.console")
    def test_index_status_exists(self, mock_console, mock_config_class, mock_generator_class):
        """Test index_status when index exists."""
        mock_config = MagicMock()
        mock_config.index_dir = ".opencode"
        mock_config.index_filename = "INDEX.md"
        mock_config_class.return_value = mock_config
        
        mock_generator = MagicMock()
        mock_generator.is_index_fresh.return_value = True
        mock_generator.is_index_stale.return_value = False
        mock_generator_class.return_value = mock_generator
        
        mock_path = MagicMock()
        mock_path.resolve.return_value = mock_path
        mock_path.name = "test-project"
        
        mock_index_path = MagicMock()
        mock_index_path.exists.return_value = True
        mock_index_path.stat.return_value.st_mtime = time.time()
        mock_index_path.read_text.return_value = "Branch: main\nCommit: abc123\nProject Type: python"
        
        # Setup path division
        mock_path.__truediv__ = MagicMock(return_value=mock_index_path)
        mock_index_path.__truediv__ = MagicMock(return_value=mock_index_path)
        
        index_status(path=mock_path)
        
        assert mock_console.print.called
    
    @patch("opencode.cli.commands.index.IndexGenerator")
    @patch("opencode.cli.commands.index.IndexConfig")
    @patch("opencode.cli.commands.index.console")
    def test_index_status_not_exists(self, mock_console, mock_config_class, mock_generator_class):
        """Test index_status when index doesn't exist."""
        mock_config = MagicMock()
        mock_config.index_dir = ".opencode"
        mock_config.index_filename = "INDEX.md"
        mock_config_class.return_value = mock_config
        
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        
        mock_path = MagicMock()
        mock_path.resolve.return_value = mock_path
        mock_path.name = "test-project"
        
        mock_index_path = MagicMock()
        mock_index_path.exists.return_value = False
        mock_path.__truediv__ = MagicMock(return_value=mock_index_path)
        mock_index_path.__truediv__ = MagicMock(return_value=mock_index_path)
        
        index_status(path=mock_path)
        
        assert mock_console.print.called


class TestShowIndex:
    """Tests for show_index command."""
    
    @patch("opencode.cli.commands.index.IndexConfig")
    @patch("opencode.cli.commands.index.console")
    def test_show_index_exists(self, mock_console, mock_config_class):
        """Test show_index when index exists."""
        mock_config = MagicMock()
        mock_config.index_dir = ".opencode"
        mock_config.index_filename = "INDEX.md"
        mock_config_class.return_value = mock_config
        
        mock_path = MagicMock()
        mock_path.resolve.return_value = mock_path
        
        mock_index_path = MagicMock()
        mock_index_path.exists.return_value = True
        mock_index_path.read_text.return_value = "# Index\nBranch: main"
        mock_path.__truediv__ = MagicMock(return_value=mock_index_path)
        mock_index_path.__truediv__ = MagicMock(return_value=mock_index_path)
        
        show_index(path=mock_path)
        
        assert mock_console.print.called


class TestListIndexes:
    """Tests for list_indexes command."""
    
    @patch("opencode.cli.commands.index.IndexGenerator")
    @patch("opencode.cli.commands.index.IndexConfig")
    @patch("opencode.cli.commands.index.console")
    def test_list_indexes_found(self, mock_console, mock_config_class, mock_generator_class):
        """Test list_indexes when indexes are found."""
        mock_config = MagicMock()
        mock_config.index_dir = ".opencode"
        mock_config.index_filename = "INDEX.md"
        mock_config_class.return_value = mock_config
        
        mock_generator = MagicMock()
        mock_generator.is_index_stale.return_value = False
        mock_generator.is_index_fresh.return_value = True
        mock_generator_class.return_value = mock_generator
        
        mock_workspace = MagicMock()
        mock_workspace.resolve.return_value = mock_workspace
        
        # Create mock project directory
        mock_project = MagicMock()
        mock_project.is_dir.return_value = True
        mock_project.name = "test-project"
        
        mock_index_path = MagicMock()
        mock_index_path.exists.return_value = True
        mock_index_path.read_text.return_value = "Branch: main\nCommit: abc123\nProject Type: python"
        mock_project.__truediv__ = MagicMock(return_value=mock_index_path)
        mock_index_path.__truediv__ = MagicMock(return_value=mock_index_path)
        
        mock_workspace.iterdir.return_value = [mock_project]
        
        list_indexes(workspace=mock_workspace)
        
        assert mock_console.print.called
    
    @patch("opencode.cli.commands.index.IndexGenerator")
    @patch("opencode.cli.commands.index.IndexConfig")
    @patch("opencode.cli.commands.index.console")
    def test_list_indexes_none_found(self, mock_console, mock_config_class, mock_generator_class):
        """Test list_indexes when no indexes are found."""
        mock_config = MagicMock()
        mock_config.index_dir = ".opencode"
        mock_config.index_filename = "INDEX.md"
        mock_config_class.return_value = mock_config
        
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        
        mock_workspace = MagicMock()
        mock_workspace.resolve.return_value = mock_workspace
        
        # Create mock project directory without index
        mock_project = MagicMock()
        mock_project.is_dir.return_value = True
        mock_project.name = "test-project"
        
        mock_index_path = MagicMock()
        mock_index_path.exists.return_value = False
        mock_project.__truediv__ = MagicMock(return_value=mock_index_path)
        
        mock_workspace.iterdir.return_value = [mock_project]
        
        list_indexes(workspace=mock_workspace)
        
        assert mock_console.print.called


class TestCleanIndexes:
    """Tests for clean_indexes command."""
    
    @patch("opencode.cli.commands.index.IndexConfig")
    @patch("opencode.cli.commands.index.console")
    def test_clean_indexes_single_project_not_found(self, mock_console, mock_config_class):
        """Test clean_indexes when index doesn't exist."""
        mock_config = MagicMock()
        mock_config.index_dir = ".opencode"
        mock_config.index_filename = "INDEX.md"
        mock_config_class.return_value = mock_config
        
        mock_path = MagicMock()
        mock_path.resolve.return_value = mock_path
        
        mock_index_path = MagicMock()
        mock_index_path.exists.return_value = False
        mock_path.__truediv__ = MagicMock(return_value=mock_index_path)
        
        clean_indexes(path=mock_path, all_projects=False)
        
        assert mock_console.print.called


class TestIndexApp:
    """Tests for the index typer app."""
    
    def test_app_exists(self):
        """Test that app is a Typer app."""
        assert app is not None
        assert app.info.name == "index"
    
    def test_app_has_commands(self):
        """Test that app has expected commands."""
        commands = [cmd.name for cmd in app.registered_commands]
        assert "generate" in commands
        assert "status" in commands
        assert "show" in commands
        assert "list" in commands
        assert "clean" in commands
