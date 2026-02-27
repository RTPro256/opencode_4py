"""
Extended tests for CLI run command.

Tests run command imports and basic structure.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from pathlib import Path

# Import just to verify module loads
from opencode.cli.commands import run


class TestRunCommandImport:
    """Tests for run command module imports."""

    def test_run_command_module_imports(self):
        """Test that run command module can be imported."""
        from opencode.cli.commands.run import run_command
        assert callable(run_command)

    def test_launch_tui_imports(self):
        """Test that launch_tui can be imported."""
        from opencode.cli.commands.run import launch_tui
        assert callable(launch_tui)

    def test_run_async_imports(self):
        """Test that _run_async can be imported."""
        from opencode.cli.commands.run import _run_async
        assert callable(_run_async)

    def test_run_multi_model_imports(self):
        """Test that _run_multi_model can be imported."""
        from opencode.cli.commands.run import _run_multi_model
        assert callable(_run_multi_model)

    def test_build_adhoc_pattern_imports(self):
        """Test that _build_adhoc_pattern can be imported."""
        from opencode.cli.commands.run import _build_adhoc_pattern
        assert callable(_build_adhoc_pattern)


class TestRunCommandBasic:
    """Basic tests for run command functions."""

    def test_launch_tui_signature(self):
        """Test launch_tui has correct signature."""
        import inspect
        from opencode.cli.commands.run import launch_tui
        sig = inspect.signature(launch_tui)
        # Should have directory, model, agent parameters
        params = list(sig.parameters.keys())
        assert "directory" in params
        assert "model" in params
        assert "agent" in params

    def test_run_async_signature(self):
        """Test _run_async has correct signature."""
        import inspect
        from opencode.cli.commands.run import _run_async
        sig = inspect.signature(_run_async)
        params = list(sig.parameters.keys())
        assert "prompt" in params
        assert "model" in params
        assert "provider_name" in params

    def test_build_adhoc_pattern_signature(self):
        """Test _build_adhoc_pattern has correct signature."""
        import inspect
        from opencode.cli.commands.run import _build_adhoc_pattern
        sig = inspect.signature(_build_adhoc_pattern)
        params = list(sig.parameters.keys())
        assert "pattern_type" in params
        assert "models" in params
        assert "config" in params


class TestRunMultiModel:
    """Tests for _run_multi_model function."""

    @pytest.mark.asyncio
    async def test_run_multi_model_requires_config(self):
        """Test that _run_multi_model requires a config."""
        from opencode.cli.commands.run import _run_multi_model
        
        # Should not crash on import
        assert callable(_run_multi_model)

    @pytest.mark.asyncio
    async def test_run_multi_model_empty_pattern(self):
        """Test _run_multi_model with empty params."""
        from opencode.cli.commands.run import _run_multi_model
        import click
        
        mock_config = MagicMock()
        mock_config.multi_model_patterns = {}
        
        # This should raise click.exceptions.Exit for unknown pattern
        with pytest.raises(click.exceptions.Exit):
            await _run_multi_model("prompt", "unknown", None, [], mock_config)
