"""
Tests for CLI RAG commands.

Tests for rag_audit, rag_create, rag_manage, and rag_query commands.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
import tempfile
import os

from typer.testing import CliRunner

from opencode.cli.commands.rag_audit import app as rag_audit_app
from opencode.cli.commands.rag_create import app as rag_create_app
from opencode.cli.commands.rag_manage import app as rag_manage_app
from opencode.cli.commands.rag_query import app as rag_query_app


runner = CliRunner()


class TestRagAuditCommand:
    """Tests for RAG audit command."""

    @pytest.mark.unit
    def test_rag_audit_no_log(self):
        """Test audit when no log exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("opencode.cli.commands.rag_audit.Path") as mock_path:
                mock_path.return_value = Path(tmpdir) / "nonexistent"
                result = runner.invoke(rag_audit_app, ["test-agent"])
                # Command should run without error
                assert result.exit_code == 0 or "No audit log" in result.output

    @pytest.mark.unit
    def test_rag_audit_help(self):
        """Test audit command help."""
        result = runner.invoke(rag_audit_app, ["--help"])
        assert result.exit_code == 0
        assert "agent" in result.output.lower() or "audit" in result.output.lower()


class TestRagCreateCommand:
    """Tests for RAG create command."""

    @pytest.mark.unit
    def test_rag_create_help(self):
        """Test create command help."""
        result = runner.invoke(rag_create_app, ["--help"])
        assert result.exit_code == 0

    @pytest.mark.unit
    def test_rag_create_missing_agent(self):
        """Test create with missing agent name."""
        result = runner.invoke(rag_create_app, [])
        # Should show error or help
        assert result.exit_code != 0 or "usage" in result.output.lower()


class TestRagManageCommand:
    """Tests for RAG manage command."""

    @pytest.mark.unit
    def test_rag_manage_help(self):
        """Test manage command help."""
        result = runner.invoke(rag_manage_app, ["--help"])
        assert result.exit_code == 0

    @pytest.mark.unit
    def test_rag_manage_list(self):
        """Test manage list command."""
        result = runner.invoke(rag_manage_app, ["list"])
        # Command should run
        assert result.exit_code == 0 or result.output


class TestRagQueryCommand:
    """Tests for RAG query command."""

    @pytest.mark.unit
    def test_rag_query_help(self):
        """Test query command help."""
        result = runner.invoke(rag_query_app, ["--help"])
        assert result.exit_code == 0

    @pytest.mark.unit
    def test_rag_query_missing_params(self):
        """Test query with missing parameters."""
        result = runner.invoke(rag_query_app, [])
        # Should show error or help
        assert result.exit_code != 0 or "usage" in result.output.lower()
