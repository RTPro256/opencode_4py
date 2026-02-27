"""
Tests for CLI main module.
"""

import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.unit
class TestCLIMain:
    """Tests for CLI main module."""
    
    def test_cli_main_module_exists(self):
        """Test CLI main module exists."""
        from opencode.cli import main
        assert main is not None
    
    def test_cli_main_app_exists(self):
        """Test CLI main app exists."""
        from opencode.cli.main import app
        assert app is not None
    
    def test_cli_main_console_exists(self):
        """Test CLI main console exists."""
        from opencode.cli.main import console
        assert console is not None
    
    def test_version_callback_with_true(self):
        """Test version callback with True value."""
        from opencode.cli.main import version_callback
        import typer
        
        with pytest.raises(typer.Exit):
            version_callback(True)
    
    def test_version_callback_with_false(self):
        """Test version callback with False value."""
        from opencode.cli.main import version_callback
        
        # Should not raise
        version_callback(False)
    
    def test_app_has_registered_commands(self):
        """Test app has registered commands."""
        from opencode.cli.main import app
        
        # Check that app has registered commands
        assert len(app.registered_commands) > 0


@pytest.mark.unit
class TestCLIRunCommand:
    """Tests for CLI run command."""
    
    def test_run_command_exists(self):
        """Test run command exists."""
        from opencode.cli.main import run
        assert run is not None
    
    def test_run_command_is_callable(self):
        """Test run command is callable."""
        from opencode.cli.main import run
        assert callable(run)


@pytest.mark.unit
class TestCLIServeCommand:
    """Tests for CLI serve command."""
    
    def test_serve_command_exists(self):
        """Test serve command exists."""
        from opencode.cli.main import serve
        assert serve is not None
    
    def test_serve_command_is_callable(self):
        """Test serve command is callable."""
        from opencode.cli.main import serve
        assert callable(serve)


@pytest.mark.unit
class TestCLIAuthCommand:
    """Tests for CLI auth command."""
    
    def test_auth_command_exists(self):
        """Test auth command exists."""
        from opencode.cli.main import auth
        assert auth is not None
    
    def test_auth_command_is_callable(self):
        """Test auth command is callable."""
        from opencode.cli.main import auth
        assert callable(auth)
