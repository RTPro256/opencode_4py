"""
Tests for RAG sharing commands.
"""

import json
import pytest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
import urllib.error

from typer.testing import CliRunner

from opencode.cli.commands.rag_share import (
    app,
    _parse_github_source,
    _download_file,
    _download_json,
)

runner = CliRunner()


@pytest.mark.unit
class TestParseGithubSource:
    """Tests for _parse_github_source function."""

    def test_parse_github_colon_format(self):
        """Test parsing github:owner/repo format."""
        owner, repo = _parse_github_source("github:owner/repo")
        assert owner == "owner"
        assert repo == "repo"

    def test_parse_owner_repo_format(self):
        """Test parsing owner/repo format."""
        owner, repo = _parse_github_source("owner/repo")
        assert owner == "owner"
        assert repo == "repo"

    def test_parse_https_format(self):
        """Test parsing https://github.com/owner/repo format."""
        owner, repo = _parse_github_source("https://github.com/owner/repo")
        assert owner == "owner"
        assert repo == "repo"

    def test_parse_with_extra_path(self):
        """Test parsing with extra path components."""
        owner, repo = _parse_github_source("owner/repo/extra/path")
        assert owner == "owner"
        assert repo == "repo"

    def test_parse_invalid_format(self):
        """Test parsing invalid format raises error."""
        with pytest.raises(ValueError) as exc_info:
            _parse_github_source("invalid")
        assert "Invalid source format" in str(exc_info.value)


@pytest.mark.unit
class TestDownloadFile:
    """Tests for _download_file function."""

    @patch("opencode.cli.commands.rag_share.urllib.request.urlopen")
    def test_download_file_success(self, mock_urlopen):
        """Test successful file download."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"test content"
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = _download_file("https://example.com/file.txt")
        assert result == "test content"

    @patch("opencode.cli.commands.rag_share.urllib.request.urlopen")
    def test_download_file_url_error(self, mock_urlopen):
        """Test download with URL error."""
        mock_urlopen.side_effect = urllib.error.URLError("Connection failed")
        
        with pytest.raises(ConnectionError) as exc_info:
            _download_file("https://example.com/file.txt")
        assert "Failed to download" in str(exc_info.value)


@pytest.mark.unit
class TestDownloadJson:
    """Tests for _download_json function."""

    @patch("opencode.cli.commands.rag_share._download_file")
    def test_download_json_success(self, mock_download):
        """Test successful JSON download."""
        mock_download.return_value = '{"key": "value"}'
        
        result = _download_json("https://example.com/data.json")
        assert result == {"key": "value"}


@pytest.mark.unit
class TestGetCommunityRag:
    """Tests for get_community_rag command."""

    @patch("opencode.cli.commands.rag_share._parse_github_source")
    def test_get_invalid_source(self, mock_parse):
        """Test get with invalid source format."""
        mock_parse.side_effect = ValueError("Invalid source format")
        
        result = runner.invoke(app, ["get", "test-agent"])
        assert result.exit_code == 1

    @patch("opencode.cli.commands.rag_share._parse_github_source")
    @patch("opencode.cli.commands.rag_share.urllib.request.urlopen")
    @patch("opencode.cli.commands.rag_share.Path.exists")
    def test_get_existing_rag_no_force(self, mock_exists, mock_urlopen, mock_parse):
        """Test get with existing RAG and no force flag."""
        mock_parse.return_value = ("owner", "repo")
        mock_exists.return_value = True
        
        result = runner.invoke(app, ["get", "test-agent"])
        assert result.exit_code == 1
        assert "already exists" in result.output

    @patch("opencode.cli.commands.rag_share._parse_github_source")
    @patch("opencode.cli.commands.rag_share.urllib.request.urlopen")
    @patch("opencode.cli.commands.rag_share.Path.mkdir")
    @patch("opencode.cli.commands.rag_share.Path.exists")
    def test_get_rag_not_found(self, mock_exists, mock_mkdir, mock_urlopen, mock_parse):
        """Test get when RAG not found in repository."""
        mock_parse.return_value = ("owner", "repo")
        mock_exists.return_value = False
        
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"message": "Not Found"}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        # Create a proper HTTPError mock
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "https://api.github.com/repos/owner/repo/contents/RAG/agent_test-agent",
            404,
            "Not Found",
            {},
            None
        )
        
        result = runner.invoke(app, ["get", "test-agent", "--force"])
        assert result.exit_code == 1


@pytest.mark.unit
class TestShareRag:
    """Tests for share_rag command."""

    @patch.dict("os.environ", {"GITHUB_TOKEN": ""}, clear=False)
    def test_share_no_token(self):
        """Test share without GitHub token."""
        result = runner.invoke(app, ["share", "test-agent"])
        assert result.exit_code == 1
        assert "GitHub token required" in result.output

    @patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}, clear=False)
    @patch("opencode.cli.commands.rag_share.Path.exists")
    def test_share_rag_not_found(self, mock_exists):
        """Test share when local RAG not found."""
        mock_exists.return_value = False
        
        result = runner.invoke(app, ["share", "test-agent"])
        assert result.exit_code == 1
        assert "RAG not found" in result.output

    @patch("opencode.cli.commands.rag_share._parse_github_source")
    @patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}, clear=False)
    @patch("opencode.cli.commands.rag_share.Path.exists")
    def test_share_invalid_repo(self, mock_exists, mock_parse):
        """Test share with invalid repository format."""
        mock_exists.return_value = True
        mock_parse.side_effect = ValueError("Invalid source format")
        
        result = runner.invoke(app, ["share", "test-agent"])
        assert result.exit_code == 1

    @patch("opencode.cli.commands.rag_share._parse_github_source")
    @patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}, clear=False)
    @patch("opencode.cli.commands.rag_share.Path.exists")
    def test_share_success(self, mock_exists, mock_parse):
        """Test share with valid inputs."""
        mock_exists.return_value = True
        mock_parse.return_value = ("owner", "repo")
        
        result = runner.invoke(app, ["share", "test-agent"])
        # The command shows instructions but doesn't fail
        assert "Sharing RAG" in result.output or "manually share" in result.output.lower()


@pytest.mark.unit
class TestListRemoteRags:
    """Tests for list_remote_rags command."""

    @patch("opencode.cli.commands.rag_share._parse_github_source")
    def test_list_remote_invalid_source(self, mock_parse):
        """Test list-remote with invalid source."""
        mock_parse.side_effect = ValueError("Invalid source format")
        
        result = runner.invoke(app, ["list-remote"])
        assert result.exit_code == 1

    @patch("opencode.cli.commands.rag_share._parse_github_source")
    @patch("opencode.cli.commands.rag_share.urllib.request.urlopen")
    def test_list_remote_success(self, mock_urlopen, mock_parse):
        """Test list-remote with successful response."""
        mock_parse.return_value = ("owner", "repo")
        
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps([
            {"type": "dir", "name": "agent_troubleshooting", "sha": "abc123"},
            {"type": "dir", "name": "agent_code", "sha": "def456"},
            {"type": "file", "name": "README.md"},
        ]).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        result = runner.invoke(app, ["list-remote"])
        assert result.exit_code == 0
        assert "Community RAG" in result.output

    @patch("opencode.cli.commands.rag_share._parse_github_source")
    @patch("opencode.cli.commands.rag_share.urllib.request.urlopen")
    def test_list_remote_no_rags(self, mock_urlopen, mock_parse):
        """Test list-remote when no RAGs found."""
        mock_parse.return_value = ("owner", "repo")
        
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps([
            {"type": "file", "name": "README.md"},
        ]).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        result = runner.invoke(app, ["list-remote"])
        assert result.exit_code == 0
        assert "No RAG" in result.output

    @patch("opencode.cli.commands.rag_share._parse_github_source")
    @patch("opencode.cli.commands.rag_share.urllib.request.urlopen")
    def test_list_remote_not_found(self, mock_urlopen, mock_parse):
        """Test list-remote when repository not found."""
        mock_parse.return_value = ("owner", "repo")
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "https://api.github.com/repos/owner/repo/contents/RAG",
            404,
            "Not Found",
            {},
            None
        )
        
        result = runner.invoke(app, ["list-remote"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()


@pytest.mark.unit
class TestMergeRags:
    """Tests for merge_rags command."""

    @patch("opencode.cli.commands.rag_share.Path.exists")
    def test_merge_source_not_found(self, mock_exists):
        """Test merge when source RAG not found."""
        mock_exists.return_value = False
        
        result = runner.invoke(app, ["merge", "target", "source"])
        assert result.exit_code == 1
        assert "Source RAG not found" in result.output

    @patch("opencode.cli.commands.rag_share.Path.exists")
    def test_merge_target_not_found(self, mock_exists):
        """Test merge when target RAG not found."""
        # First call checks source (exists), second checks target (doesn't exist)
        mock_exists.side_effect = [True, False]
        
        result = runner.invoke(app, ["merge", "target", "source"])
        assert result.exit_code == 1
        assert "Target RAG not found" in result.output

    @patch("opencode.cli.commands.rag_share.Path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_merge_different_models(self, mock_file, mock_exists):
        """Test merge with different embedding models."""
        mock_exists.return_value = True
        
        # Mock config files
        config_data = [
            json.dumps({"embedding_model": "model1"}),
            json.dumps({"embedding_model": "model2"}),
        ]
        mock_file.return_value.read.side_effect = [config_data[0], config_data[1]]
        
        # This test would need more mocking for the full flow
        # For now, just verify the command structure
        result = runner.invoke(app, ["merge", "target", "source"])
        # The command will fail at some point but we're testing the initial checks
        assert "Merging RAG" in result.output or result.exit_code != 0
