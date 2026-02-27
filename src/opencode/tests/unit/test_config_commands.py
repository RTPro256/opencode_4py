"""
Tests for CLI config commands.
"""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import io

from opencode.cli.commands.config import (
    config_app,
    _get_default_config,
    _parse_value,
)


class TestGetDefaultConfig:
    """Tests for _get_default_config function."""
    
    def test_returns_string(self):
        """Test that _get_default_config returns a string."""
        result = _get_default_config()
        assert isinstance(result, str)
    
    def test_contains_provider_section(self):
        """Test that default config contains provider sections."""
        result = _get_default_config()
        assert "[provider.anthropic]" in result
        assert "[provider.openai]" in result
        assert "[provider.google]" in result
    
    def test_contains_settings_section(self):
        """Test that default config contains settings section."""
        result = _get_default_config()
        assert "[settings]" in result
        assert "default_provider" in result
        assert "theme" in result
    
    def test_contains_mcp_servers_section(self):
        """Test that default config contains MCP servers section."""
        result = _get_default_config()
        assert "mcp.servers" in result


class TestParseValue:
    """Tests for _parse_value function."""
    
    def test_parse_boolean_true(self):
        """Test parsing boolean true values."""
        assert _parse_value("true") is True
        assert _parse_value("True") is True
        assert _parse_value("TRUE") is True
        assert _parse_value("yes") is True
        assert _parse_value("Yes") is True
        assert _parse_value("1") is True
    
    def test_parse_boolean_false(self):
        """Test parsing boolean false values."""
        assert _parse_value("false") is False
        assert _parse_value("False") is False
        assert _parse_value("FALSE") is False
        assert _parse_value("no") is False
        assert _parse_value("No") is False
        assert _parse_value("0") is False
    
    def test_parse_integer(self):
        """Test parsing integer values."""
        assert _parse_value("42") == 42
        assert _parse_value("0") == 0
        assert _parse_value("-10") == -10
    
    def test_parse_float(self):
        """Test parsing float values."""
        assert _parse_value("3.14") == 3.14
        assert _parse_value("0.5") == 0.5
        assert _parse_value("-2.5") == -2.5
    
    def test_parse_string(self):
        """Test parsing string values."""
        assert _parse_value("hello") == "hello"
        assert _parse_value("anthropic") == "anthropic"
        assert _parse_value("dark") == "dark"


class TestConfigShow:
    """Tests for config show command."""
    
    @patch("opencode.cli.commands.config.Config")
    @patch("opencode.cli.commands.config.console")
    def test_show_config_with_providers(self, mock_console, mock_config_class):
        """Test show_config with providers configured."""
        mock_config = MagicMock()
        mock_config.config_file = "/path/to/config.toml"
        mock_config.providers = {
            "anthropic": {"default_model": "claude-3", "api_key": "key123"},
            "openai": {"default_model": "gpt-4"},
        }
        mock_config.settings = {}
        mock_config.mcp_servers = {}
        mock_config_class.load.return_value = mock_config
        
        from opencode.cli.commands.config import show_config
        show_config()
        
        # Verify console.print was called
        assert mock_console.print.called
    
    @patch("opencode.cli.commands.config.Config")
    @patch("opencode.cli.commands.config.console")
    def test_show_config_with_settings(self, mock_console, mock_config_class):
        """Test show_config with settings configured."""
        mock_config = MagicMock()
        mock_config.config_file = "/path/to/config.toml"
        mock_config.providers = {}
        mock_config.settings = {"theme": "dark", "max_tokens": 8192}
        mock_config.mcp_servers = {}
        mock_config_class.load.return_value = mock_config
        
        from opencode.cli.commands.config import show_config
        show_config()
        
        assert mock_console.print.called
    
    @patch("opencode.cli.commands.config.Config")
    @patch("opencode.cli.commands.config.console")
    def test_show_config_with_mcp_servers(self, mock_console, mock_config_class):
        """Test show_config with MCP servers configured."""
        mock_config = MagicMock()
        mock_config.config_file = "/path/to/config.toml"
        mock_config.providers = {}
        mock_config.settings = {}
        mock_config.mcp_servers = {
            "filesystem": {"command": "mcp-filesystem"}
        }
        mock_config_class.load.return_value = mock_config
        
        from opencode.cli.commands.config import show_config
        show_config()
        
        assert mock_console.print.called


class TestConfigPath:
    """Tests for config path command."""
    
    @patch("opencode.cli.commands.config.Config")
    @patch("opencode.cli.commands.config.console")
    def test_config_path(self, mock_console, mock_config_class):
        """Test config_path command."""
        mock_config = MagicMock()
        mock_config.config_file = "/path/to/config.toml"
        mock_config.data_dir = "/path/to/data"
        mock_config_class.load.return_value = mock_config
        
        from opencode.cli.commands.config import config_path
        config_path()
        
        # Verify console.print was called twice
        assert mock_console.print.call_count == 2


class TestConfigSet:
    """Tests for config set command."""
    
    @patch("opencode.cli.commands.config.Path")
    @patch("opencode.cli.commands.config.Config")
    @patch("opencode.cli.commands.config.console")
    def test_set_config_new_file(self, mock_console, mock_config_class, mock_path_class):
        """Test set_config when config file doesn't exist."""
        mock_config = MagicMock()
        mock_config.config_file = "/path/to/config.toml"
        mock_config_class.load.return_value = mock_config
        
        mock_config_file = MagicMock()
        mock_config_file.exists.return_value = False
        mock_path_class.return_value = mock_config_file
        
        from opencode.cli.commands.config import set_config
        
        # Mock the file operations
        with patch("builtins.open", mock_open()):
            set_config("settings.theme", "light")
        
        # Verify file was created
        assert mock_config_file.parent.mkdir.called
    
    @patch("opencode.cli.commands.config.Path")
    @patch("opencode.cli.commands.config.Config")
    @patch("opencode.cli.commands.config.console")
    def test_set_config_existing_file(self, mock_console, mock_config_class, mock_path_class):
        """Test set_config when config file exists."""
        mock_config = MagicMock()
        mock_config.config_file = "/path/to/config.toml"
        mock_config_class.load.return_value = mock_config
        
        mock_config_file = MagicMock()
        mock_config_file.exists.return_value = True
        mock_path_class.return_value = mock_config_file
        
        from opencode.cli.commands.config import set_config
        
        # Mock tomllib.load to return existing config
        mock_data = {"settings": {"theme": "dark"}}
        with patch("builtins.open", mock_open(read_data=b"")):
            with patch("tomllib.load", return_value=mock_data):
                with patch("tomli_w.dump"):
                    set_config("settings.theme", "light")
        
        assert mock_console.print.called


class TestConfigGet:
    """Tests for config get command."""
    
    @patch("opencode.cli.commands.config.Path")
    @patch("opencode.cli.commands.config.Config")
    @patch("opencode.cli.commands.config.console")
    def test_get_config_existing_key(self, mock_console, mock_config_class, mock_path_class):
        """Test get_config with existing key."""
        mock_config = MagicMock()
        mock_config.config_file = "/path/to/config.toml"
        mock_config_class.load.return_value = mock_config
        
        mock_config_file = MagicMock()
        mock_config_file.exists.return_value = True
        mock_path_class.return_value = mock_config_file
        
        mock_data = {"settings": {"theme": "dark"}}
        
        from opencode.cli.commands.config import get_config
        
        with patch("builtins.open", mock_open(read_data=b"")):
            with patch("tomllib.load", return_value=mock_data):
                get_config("settings.theme")
        
        assert mock_console.print.called
    
    @patch("opencode.cli.commands.config.Path")
    @patch("opencode.cli.commands.config.Config")
    @patch("opencode.cli.commands.config.console")
    def test_get_config_file_not_found(self, mock_console, mock_config_class, mock_path_class):
        """Test get_config when config file doesn't exist."""
        import typer
        
        mock_config = MagicMock()
        mock_config.config_file = "/path/to/config.toml"
        mock_config_class.load.return_value = mock_config
        
        mock_config_file = MagicMock()
        mock_config_file.exists.return_value = False
        mock_path_class.return_value = mock_config_file
        
        from opencode.cli.commands.config import get_config
        
        with pytest.raises(typer.Exit):
            get_config("settings.theme")


class TestConfigReset:
    """Tests for config reset command."""
    
    @patch("opencode.cli.commands.config.Path")
    @patch("opencode.cli.commands.config.Config")
    @patch("opencode.cli.commands.config.console")
    def test_reset_config_confirmed(self, mock_console, mock_config_class, mock_path_class):
        """Test reset_config with confirmation."""
        mock_config = MagicMock()
        mock_config.config_file = "/path/to/config.toml"
        mock_config_class.load.return_value = mock_config
        
        mock_config_file = MagicMock()
        mock_config_file.exists.return_value = True
        mock_path_class.return_value = mock_config_file
        
        from opencode.cli.commands.config import reset_config
        
        reset_config(confirm=True)
        
        # Verify file was deleted
        assert mock_config_file.unlink.called
        # Verify new file was written
        assert mock_config_file.write_text.called
    
    @patch("opencode.cli.commands.config.Path")
    @patch("opencode.cli.commands.config.Config")
    @patch("opencode.cli.commands.config.console")
    @patch("opencode.cli.commands.config.typer")
    def test_reset_config_not_confirmed(self, mock_typer, mock_config_class, 
                                         mock_console, mock_path_class):
        """Test reset_config without confirmation."""
        mock_typer.confirm.return_value = False
        
        mock_config = MagicMock()
        mock_config.config_file = "/path/to/config.toml"
        mock_config_class.load.return_value = mock_config
        
        mock_config_file = MagicMock()
        mock_path_class.return_value = mock_config_file
        
        from opencode.cli.commands.config import reset_config
        
        with pytest.raises(Exception):  # typer.Abort
            reset_config(confirm=False)


class TestConfigEdit:
    """Tests for config edit command."""
    
    @patch("opencode.cli.commands.config.Path")
    @patch("opencode.cli.commands.config.Config")
    @patch("opencode.cli.commands.config.console")
    def test_edit_config_existing_file(self, mock_console, mock_config_class, mock_path_class):
        """Test edit_config with existing file."""
        mock_config = MagicMock()
        mock_config.config_file = "/path/to/config.toml"
        mock_config_class.load.return_value = mock_config
        
        mock_config_file = MagicMock()
        mock_config_file.exists.return_value = True
        mock_path_class.return_value = mock_config_file
        
        from opencode.cli.commands.config import edit_config
        
        with patch.dict("os.environ", {"EDITOR": "nano"}):
            with patch("subprocess.run") as mock_run:
                edit_config()
                assert mock_run.called
    
    @patch("opencode.cli.commands.config.Path")
    @patch("opencode.cli.commands.config.Config")
    @patch("opencode.cli.commands.config.console")
    def test_edit_config_creates_file(self, mock_console, mock_config_class, mock_path_class):
        """Test edit_config creates file if it doesn't exist."""
        mock_config = MagicMock()
        mock_config.config_file = "/path/to/config.toml"
        mock_config_class.load.return_value = mock_config
        
        mock_config_file = MagicMock()
        mock_config_file.exists.return_value = False
        mock_path_class.return_value = mock_config_file
        
        from opencode.cli.commands.config import edit_config
        
        with patch.dict("os.environ", {"EDITOR": "nano"}):
            with patch("subprocess.run"):
                edit_config()
        
        # Verify parent directory was created
        assert mock_config_file.parent.mkdir.called
        # Verify file was written
        assert mock_config_file.write_text.called
    
    @patch("opencode.cli.commands.config.Path")
    @patch("opencode.cli.commands.config.Config")
    @patch("opencode.cli.commands.config.console")
    def test_edit_config_custom_editor(self, mock_console, mock_config_class, mock_path_class):
        """Test edit_config with custom editor."""
        mock_config = MagicMock()
        mock_config.config_file = "/path/to/config.toml"
        mock_config_class.load.return_value = mock_config
        
        mock_config_file = MagicMock()
        mock_config_file.exists.return_value = True
        mock_path_class.return_value = mock_config_file
        
        from opencode.cli.commands.config import edit_config
        
        with patch("subprocess.run") as mock_run:
            edit_config(editor="code")
            # Verify subprocess.run was called with custom editor
            call_args = mock_run.call_args
            assert "code" in call_args[0][0]
    
    @patch("opencode.cli.commands.config.Path")
    @patch("opencode.cli.commands.config.Config")
    @patch("opencode.cli.commands.config.console")
    def test_edit_config_editor_not_found(self, mock_console, mock_config_class, mock_path_class):
        """Test edit_config when editor is not found."""
        import typer
        
        mock_config = MagicMock()
        mock_config.config_file = "/path/to/config.toml"
        mock_config_class.load.return_value = mock_config
        
        mock_config_file = MagicMock()
        mock_config_file.exists.return_value = True
        mock_path_class.return_value = mock_config_file
        
        from opencode.cli.commands.config import edit_config
        
        with patch.dict("os.environ", {"EDITOR": "nonexistent_editor"}):
            with patch("subprocess.run", side_effect=FileNotFoundError()):
                with pytest.raises(typer.Exit):
                    edit_config()


class TestConfigApp:
    """Tests for the config typer app."""
    
    def test_config_app_exists(self):
        """Test that config_app is a Typer app."""
        assert config_app is not None
        assert config_app.info.name == "config"
    
    def test_config_app_has_commands(self):
        """Test that config_app has expected commands."""
        # Get registered commands
        commands = [cmd.name for cmd in config_app.registered_commands]
        assert "show" in commands
        assert "path" in commands
        assert "edit" in commands
        assert "set" in commands
        assert "get" in commands
        assert "reset" in commands
