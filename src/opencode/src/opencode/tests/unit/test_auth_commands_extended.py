"""
Extended tests for CLI auth commands.

Tests the auth command functions: set, get, list, delete API keys.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, patch as mock_patch
from pathlib import Path

from opencode.cli.commands.auth import (
    _hash_key,
    _mask_key,
    _set_api_key_async,
    _get_api_key_async,
    _list_api_keys_async,
    _delete_api_key_async,
)


class TestHashKey:
    """Tests for _hash_key function."""

    def test_hash_key_basic(self):
        """Test basic key hashing."""
        result = _hash_key("test-api-key-12345")
        assert isinstance(result, str)
        assert len(result) == 16

    def test_hash_key_consistency(self):
        """Test that same key produces same hash."""
        key = "my-secret-key"
        hash1 = _hash_key(key)
        hash2 = _hash_key(key)
        assert hash1 == hash2

    def test_hash_key_different_keys(self):
        """Test that different keys produce different hashes."""
        hash1 = _hash_key("key1")
        hash2 = _hash_key("key2")
        assert hash1 != hash2

    def test_hash_key_empty_string(self):
        """Test hashing empty string."""
        result = _hash_key("")
        assert isinstance(result, str)
        assert len(result) == 16

    def test_hash_key_unicode(self):
        """Test hashing unicode key."""
        result = _hash_key("🔑 ключ ключ")
        assert isinstance(result, str)
        assert len(result) == 16


class TestMaskKey:
    """Tests for _mask_key function."""

    def test_mask_key_short(self):
        """Test masking short key."""
        result = _mask_key("abc")
        assert result == "****"

    def test_mask_key_exact_length(self):
        """Test masking key with exactly 8 characters."""
        result = _mask_key("12345678")
        assert result == "****"

    def test_mask_key_long(self):
        """Test masking long key."""
        result = _mask_key("sk-ant-api-key-12345")
        assert result == "sk-a...2345"

    def test_mask_key_very_long(self):
        """Test masking very long key."""
        key = "sk-ant-" + "a" * 50
        result = _mask_key(key)
        assert result.startswith("sk-a")
        assert result.endswith("a" * 4)
        assert "..." in result

    def test_mask_key_typical_api_key(self):
        """Test masking typical API key format."""
        result = _mask_key("sk-ant-api03-abc123xyz")
        # Key is 20 chars, so takes first 4 + ... + last 4
        assert result.startswith("sk-a")
        assert result.endswith("yz")
        assert "..." in result


class TestSetApiKey:
    """Tests for _set_api_key_async function."""

    @pytest.mark.asyncio
    async def test_set_api_key_new(self):
        """Test setting a new API key."""
        mock_config = MagicMock()
        mock_config.data_dir = MagicMock()
        mock_db_path = MagicMock()
        mock_config.data_dir.__truediv__ = MagicMock(return_value=mock_db_path)

        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_db = MagicMock()
        mock_db.session = MagicMock(return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock()))

        with mock_patch("opencode.cli.commands.auth.Config.load", return_value=mock_config), \
             mock_patch("opencode.cli.commands.auth.init_database", new_callable=AsyncMock), \
             mock_patch("opencode.cli.commands.auth.close_database", new_callable=AsyncMock), \
             mock_patch("opencode.cli.commands.auth.get_database", return_value=mock_db), \
             mock_patch("opencode.cli.commands.auth.console") as mock_console:
            
            await _set_api_key_async("anthropic", "sk-ant-test123")

            # Verify session add was called for new key
            mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_api_key_existing(self):
        """Test updating an existing API key."""
        mock_config = MagicMock()
        mock_config.data_dir = MagicMock()
        mock_db_path = MagicMock()
        mock_config.data_dir.__truediv__ = MagicMock(return_value=mock_db_path)

        existing_key = MagicMock()
        existing_key.key_encrypted = "old-key"
        existing_key.key_hash = "oldhash"

        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=existing_key)
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_db = MagicMock()
        mock_db.session = MagicMock(return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock()))

        with mock_patch("opencode.cli.commands.auth.Config.load", return_value=mock_config), \
             mock_patch("opencode.cli.commands.auth.init_database", new_callable=AsyncMock), \
             mock_patch("opencode.cli.commands.auth.close_database", new_callable=AsyncMock), \
             mock_patch("opencode.cli.commands.auth.get_database", return_value=mock_db), \
             mock_patch("opencode.cli.commands.auth.console") as mock_console:
            
            await _set_api_key_async("anthropic", "sk-ant-newkey")

            # Verify existing key was updated (not added)
            assert mock_session.add.call_count == 0  # Should update existing, not add new


class TestGetApiKey:
    """Tests for _get_api_key_async function."""

    @pytest.mark.asyncio
    async def test_get_api_key_exists(self):
        """Test getting an existing API key."""
        mock_config = MagicMock()
        mock_config.data_dir = MagicMock()
        mock_db_path = MagicMock()
        mock_config.data_dir.__truediv__ = MagicMock(return_value=mock_db_path)

        api_key = MagicMock()
        api_key.key_encrypted = "sk-ant-test123"

        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=api_key)
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_db = MagicMock()
        mock_db.session = MagicMock(return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock()))

        with mock_patch("opencode.cli.commands.auth.Config.load", return_value=mock_config), \
             mock_patch("opencode.cli.commands.auth.init_database", new_callable=AsyncMock), \
             mock_patch("opencode.cli.commands.auth.close_database", new_callable=AsyncMock), \
             mock_patch("opencode.cli.commands.auth.get_database", return_value=mock_db), \
             mock_patch("opencode.cli.commands.auth.console") as mock_console:
            
            await _get_api_key_async("anthropic")

            # Verify console print was called
            mock_console.print.assert_called()

    @pytest.mark.asyncio
    async def test_get_api_key_not_exists(self):
        """Test getting a non-existent API key."""
        mock_config = MagicMock()
        mock_config.data_dir = MagicMock()
        mock_db_path = MagicMock()
        mock_config.data_dir.__truediv__ = MagicMock(return_value=mock_db_path)

        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_db = MagicMock()
        mock_db.session = MagicMock(return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock()))

        with mock_patch("opencode.cli.commands.auth.Config.load", return_value=mock_config), \
             mock_patch("opencode.cli.commands.auth.init_database", new_callable=AsyncMock), \
             mock_patch("opencode.cli.commands.auth.close_database", new_callable=AsyncMock), \
             mock_patch("opencode.cli.commands.auth.get_database", return_value=mock_db), \
             mock_patch("opencode.cli.commands.auth.console") as mock_console:
            
            await _get_api_key_async("anthropic")

            # Verify console print was called with not found message
            mock_console.print.assert_called()


class TestListApiKeys:
    """Tests for _list_api_keys_async function."""

    @pytest.mark.asyncio
    async def test_list_api_keys_empty(self):
        """Test listing with no API keys configured."""
        mock_config = MagicMock()
        mock_config.data_dir = MagicMock()
        mock_db_path = MagicMock()
        mock_config.data_dir.__truediv__ = MagicMock(return_value=mock_db_path)

        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all = MagicMock(return_value=[])
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_db = MagicMock()
        mock_db.session = MagicMock(return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock()))

        with mock_patch("opencode.cli.commands.auth.Config.load", return_value=mock_config), \
             mock_patch("opencode.cli.commands.auth.init_database", new_callable=AsyncMock), \
             mock_patch("opencode.cli.commands.auth.close_database", new_callable=AsyncMock), \
             mock_patch("opencode.cli.commands.auth.get_database", return_value=mock_db), \
             mock_patch("opencode.cli.commands.auth.console") as mock_console:
            
            await _list_api_keys_async()

            # Verify table was printed
            mock_console.print.assert_called()

    @pytest.mark.asyncio
    async def test_list_api_keys_with_keys(self):
        """Test listing with some API keys configured."""
        mock_config = MagicMock()
        mock_config.data_dir = MagicMock()
        mock_db_path = MagicMock()
        mock_config.data_dir.__truediv__ = MagicMock(return_value=mock_db_path)

        api_key = MagicMock()
        api_key.provider = "anthropic"
        api_key.key_encrypted = "sk-ant-test"

        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all = MagicMock(return_value=[api_key])
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_db = MagicMock()
        mock_db.session = MagicMock(return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock()))

        with mock_patch("opencode.cli.commands.auth.Config.load", return_value=mock_config), \
             mock_patch("opencode.cli.commands.auth.init_database", new_callable=AsyncMock), \
             mock_patch("opencode.cli.commands.auth.close_database", new_callable=AsyncMock), \
             mock_patch("opencode.cli.commands.auth.get_database", return_value=mock_db), \
             mock_patch("opencode.cli.commands.auth.console") as mock_console:
            
            await _list_api_keys_async()

            # Verify table was printed
            mock_console.print.assert_called()


class TestDeleteApiKey:
    """Tests for _delete_api_key_async function."""

    @pytest.mark.asyncio
    async def test_delete_api_key_exists(self):
        """Test deleting an existing API key."""
        mock_config = MagicMock()
        mock_config.data_dir = MagicMock()
        mock_db_path = MagicMock()
        mock_config.data_dir.__truediv__ = MagicMock(return_value=mock_db_path)

        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_db = MagicMock()
        mock_db.session = MagicMock(return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock()))

        with mock_patch("opencode.cli.commands.auth.Config.load", return_value=mock_config), \
             mock_patch("opencode.cli.commands.auth.init_database", new_callable=AsyncMock), \
             mock_patch("opencode.cli.commands.auth.close_database", new_callable=AsyncMock), \
             mock_patch("opencode.cli.commands.auth.get_database", return_value=mock_db), \
             mock_patch("opencode.cli.commands.auth.console") as mock_console:
            
            await _delete_api_key_async("anthropic")

            # Verify success message
            mock_console.print.assert_called()

    @pytest.mark.asyncio
    async def test_delete_api_key_not_exists(self):
        """Test deleting a non-existent API key."""
        mock_config = MagicMock()
        mock_config.data_dir = MagicMock()
        mock_db_path = MagicMock()
        mock_config.data_dir.__truediv__ = MagicMock(return_value=mock_db_path)

        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_db = MagicMock()
        mock_db.session = MagicMock(return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock()))

        with mock_patch("opencode.cli.commands.auth.Config.load", return_value=mock_config), \
             mock_patch("opencode.cli.commands.auth.init_database", new_callable=AsyncMock), \
             mock_patch("opencode.cli.commands.auth.close_database", new_callable=AsyncMock), \
             mock_patch("opencode.cli.commands.auth.get_database", return_value=mock_db), \
             mock_patch("opencode.cli.commands.auth.console") as mock_console:
            
            await _delete_api_key_async("anthropic")

            # Verify not found message
            mock_console.print.assert_called()
