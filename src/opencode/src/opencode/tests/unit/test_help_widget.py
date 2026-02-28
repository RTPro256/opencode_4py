"""
Tests for help widget module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import tempfile

from opencode.tui.widgets.help import (
    HelpScreen,
    CommandPalette,
)


class TestHelpScreen:
    """Tests for HelpScreen class."""

    def test_help_screen_exists(self):
        """Test HelpScreen class exists."""
        assert HelpScreen is not None

    def test_help_screen_has_shortcuts(self):
        """Test HelpScreen has SHORTCUTS list."""
        assert hasattr(HelpScreen, "SHORTCUTS")
        assert len(HelpScreen.SHORTCUTS) > 0

    def test_help_screen_shortcuts_format(self):
        """Test shortcuts are tuples of (key, action)."""
        for shortcut in HelpScreen.SHORTCUTS:
            assert isinstance(shortcut, tuple)
            assert len(shortcut) == 2
            assert isinstance(shortcut[0], str)  # key
            assert isinstance(shortcut[1], str)  # action


class TestHelpScreenShortcuts:
    """Tests for HelpScreen keyboard shortcuts."""

    def test_shortcut_new_session(self):
        """Test New Session shortcut exists."""
        shortcuts = dict(HelpScreen.SHORTCUTS)
        assert "Ctrl+N" in shortcuts
        assert "New Session" in shortcuts["Ctrl+N"]

    def test_shortcut_save_session(self):
        """Test Save Session shortcut exists."""
        shortcuts = dict(HelpScreen.SHORTCUTS)
        assert "Ctrl+S" in shortcuts

    def test_shortcut_quit(self):
        """Test Quit shortcut exists."""
        shortcuts = dict(HelpScreen.SHORTCUTS)
        assert "Ctrl+Q" in shortcuts

    def test_shortcut_help(self):
        """Test Help shortcut exists."""
        shortcuts = dict(HelpScreen.SHORTCUTS)
        assert "F1" in shortcuts

    def test_shortcut_toggle_help(self):
        """Test Toggle Help shortcut exists."""
        shortcuts = dict(HelpScreen.SHORTCUTS)
        assert "?" in shortcuts

    def test_shortcut_focus_search(self):
        """Test Focus Search shortcut exists."""
        shortcuts = dict(HelpScreen.SHORTCUTS)
        assert "/" in shortcuts

    def test_shortcut_navigation(self):
        """Test navigation shortcuts exist."""
        shortcuts = dict(HelpScreen.SHORTCUTS)
        assert "j/k" in shortcuts

    def test_shortcut_send_message(self):
        """Test Send Message shortcut exists."""
        shortcuts = dict(HelpScreen.SHORTCUTS)
        assert "Enter" in shortcuts

    def test_shortcut_new_line(self):
        """Test New Line shortcut exists."""
        shortcuts = dict(HelpScreen.SHORTCUTS)
        assert "Shift+Enter" in shortcuts


class TestCommandPalette:
    """Tests for CommandPalette class."""

    def test_command_palette_exists(self):
        """Test CommandPalette class exists."""
        assert CommandPalette is not None

    def test_command_palette_inherits_modal_screen(self):
        """Test CommandPalette inherits from ModalScreen."""
        from textual.screen import ModalScreen
        assert issubclass(CommandPalette, ModalScreen)
