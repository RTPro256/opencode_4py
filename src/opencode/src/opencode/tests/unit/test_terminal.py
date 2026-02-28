"""
Tests for terminal capability detection module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch
import os

from opencode.tui.terminal import (
    TerminalCapabilities,
    get_terminal_capabilities,
)


class TestTerminalCapabilities:
    """Tests for TerminalCapabilities dataclass."""

    def test_capabilities_defaults(self):
        """Test default capabilities."""
        caps = TerminalCapabilities()
        assert caps.color_level == 0
        assert caps.unicode is True
        assert caps.mouse is True

    def test_capabilities_custom_values(self):
        """Test custom capabilities."""
        caps = TerminalCapabilities(
            color_level=256,
            unicode=True,
            mouse=False,
        )
        assert caps.color_level == 256
        assert caps.mouse is False


class TestGetTerminalCapabilities:
    """Tests for get_terminal_capabilities function."""

    def test_get_capabilities_returns_object(self):
        """Test get_terminal_capabilities returns TerminalCapabilities."""
        caps = get_terminal_capabilities()
        assert isinstance(caps, TerminalCapabilities)

    def test_get_capabilities_ci_environment(self):
        """Test capabilities in CI environment."""
        with patch.dict(os.environ, {"CI": "true"}):
            caps = get_terminal_capabilities()
            assert caps.color_level == 0
            assert caps.unicode is False
            assert caps.mouse is False

    def test_get_capabilities_dumb_terminal(self):
        """Test capabilities with dumb terminal."""
        with patch.dict(os.environ, {"TERM": "dumb"}):
            caps = get_terminal_capabilities()
            assert caps.color_level == 0
            assert caps.unicode is False


class TestTerminalCapabilitiesColors:
    """Tests for terminal color detection."""

    def test_color_level_xterm(self):
        """Test color level for xterm."""
        with patch.dict(os.environ, {"TERM": "xterm-256color"}):
            caps = get_terminal_capabilities()
            assert caps.color_level > 0

    def test_color_level_screen(self):
        """Test color level for screen."""
        with patch.dict(os.environ, {"TERM": "screen-256color"}):
            caps = get_terminal_capabilities()
            assert caps.color_level > 0

    def test_color_level_vt100(self):
        """Test color level for vt100."""
        with patch.dict(os.environ, {"TERM": "vt100"}):
            caps = get_terminal_capabilities()
            # vt100 typically has basic color support


class TestTerminalCapabilitiesUnicode:
    """Tests for Unicode detection."""

    def test_unicode_detection(self):
        """Test Unicode detection."""
        caps = get_terminal_capabilities()
        # Most modern terminals support Unicode
        assert isinstance(caps.unicode, bool)


class TestTerminalCapabilitiesMouse:
    """Tests for mouse support detection."""

    def test_mouse_support_xterm(self):
        """Test mouse support for xterm."""
        with patch.dict(os.environ, {"TERM": "xterm"}):
            caps = get_terminal_capabilities()
            assert caps.mouse is True

    def test_mouse_support_vt100(self):
        """Test mouse support for vt100."""
        with patch.dict(os.environ, {"TERM": "vt100"}):
            caps = get_terminal_capabilities()
            assert caps.mouse is False


class TestTerminalCapabilitiesOther:
    """Tests for other terminal capabilities."""

    def test_bell_support(self):
        """Test bell support."""
        caps = get_terminal_capabilities()
        # Bell is a basic terminal feature
        assert caps.bell is True

    def test_title_support_vt100(self):
        """Test title support for vt100."""
        with patch.dict(os.environ, {"TERM": "vt100"}):
            caps = get_terminal_capabilities()
            assert caps.title is False

    def test_title_support_xterm(self):
        """Test title support for xterm."""
        with patch.dict(os.environ, {"TERM": "xterm"}):
            caps = get_terminal_capabilities()
            assert caps.title is True


class TestSynchronizedOutput:
    """Tests for synchronized output detection."""

    def test_synchronized_output_tmux(self):
        """Test synchronized output for tmux."""
        with patch.dict(os.environ, {"TERM": "screen-256color"}):
            caps = get_terminal_capabilities()
            # screen/tmux should have synchronized output

    def test_synchronized_output_dumb(self):
        """Test synchronized output for dumb terminal."""
        with patch.dict(os.environ, {"TERM": "dumb"}):
            caps = get_terminal_capabilities()
            assert caps.synchronized_output is False
