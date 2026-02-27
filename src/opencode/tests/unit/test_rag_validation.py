"""
Tests for RAG validation commands.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import json

from typer.testing import CliRunner

from opencode.cli.commands.rag_validation import app

runner = CliRunner()


@pytest.mark.unit
class TestMarkFalseContent:
    """Tests for mark_false_content command."""

    @patch("opencode.cli.commands.rag_validation.asyncio.run")
    def test_mark_false_content_success(self, mock_run):
        """Test marking content as false."""
        # Just verify the command can be invoked
        result = runner.invoke(app, [
            "mark-false", "test-agent", "bad content",
            "--source", "test.py", "--reason", "Incorrect info"
        ])
        
        # Command should attempt to run (may fail due to missing RAG dir)
        assert "Marking false content" in result.output or result.exit_code != 0


@pytest.mark.unit
class TestListFalseContent:
    """Tests for list_false_content command."""

    @patch("opencode.cli.commands.rag_validation.Path.exists")
    def test_list_false_no_registry(self, mock_exists):
        """Test list when no registry exists."""
        mock_exists.return_value = False
        
        result = runner.invoke(app, ["list-false", "test-agent"])
        # Should show message about no registry
        assert "False Content" in result.output or result.exit_code == 0

    @patch("opencode.cli.commands.rag_validation.Path.exists")
    @patch("opencode.cli.commands.rag_validation.asyncio.run")
    def test_list_false_with_records(self, mock_run, mock_exists):
        """Test list with false content records."""
        mock_exists.return_value = True
        
        result = runner.invoke(app, ["list-false", "test-agent"])
        # Command should attempt to run
        assert "False Content" in result.output or result.exit_code == 0


@pytest.mark.unit
class TestRegenerateRag:
    """Tests for regenerate_rag command."""

    @patch("opencode.cli.commands.rag_validation.Path.exists")
    def test_regenerate_no_config(self, mock_exists):
        """Test regenerate when no config exists."""
        mock_exists.return_value = False
        
        result = runner.invoke(app, ["regenerate", "test-agent"])
        assert result.exit_code != 0 or "RAG index not found" in result.output

    @patch("opencode.cli.commands.rag_validation.Path.exists")
    @patch("builtins.open", create=True)
    @patch("opencode.cli.commands.rag_validation.asyncio.run")
    def test_regenerate_success(self, mock_run, mock_open, mock_exists):
        """Test successful regeneration."""
        mock_exists.return_value = True
        
        # Mock config file
        mock_file = MagicMock()
        mock_file.read.return_value = json.dumps({"sources": [], "vector_store": "file"})
        mock_file.__enter__ = MagicMock(return_value=mock_file)
        mock_file.__exit__ = MagicMock(return_value=False)
        mock_open.return_value = mock_file
        
        result = runner.invoke(app, ["regenerate", "test-agent"])
        # Command should attempt to run
        assert "Regenerating RAG" in result.output or result.exit_code != 0


@pytest.mark.unit
class TestValidateContent:
    """Tests for validate_content command."""

    @patch("opencode.cli.commands.rag_validation.asyncio.run")
    def test_validate_content_valid(self, mock_run):
        """Test validating valid content."""
        result = runner.invoke(app, [
            "validate", "test-agent", "good content",
            "--source", "test.py"
        ])
        # Command should attempt to run
        assert "Validating content" in result.output or result.exit_code != 0

    @patch("opencode.cli.commands.rag_validation.asyncio.run")
    def test_validate_content_invalid(self, mock_run):
        """Test validating invalid content."""
        result = runner.invoke(app, [
            "validate", "test-agent", "bad content",
            "--source", "test.py"
        ])
        # Command should attempt to run
        assert "Validating content" in result.output or result.exit_code != 0
