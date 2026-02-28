"""
Tests for progress widgets module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile

from opencode.tui.widgets.progress import (
    ProgressBarWidget,
    SpinnerWidget,
    StatusIndicator,
)


class TestProgressBarWidget:
    """Tests for ProgressBarWidget class."""

    def test_progress_bar_creation(self):
        """Test creating a ProgressBarWidget."""
        widget = ProgressBarWidget()
        assert widget.progress == 0
        assert widget.max_value == 100

    def test_progress_bar_custom_values(self):
        """Test creating with custom values."""
        widget = ProgressBarWidget(progress=50, max_value=200)
        assert widget.progress == 50
        assert widget.max_value == 200

    def test_progress_bar_set_progress(self):
        """Test set_progress method."""
        widget = ProgressBarWidget()
        widget.set_progress(75)
        assert widget.progress == 75

    def test_progress_bar_set_progress_clamped(self):
        """Test set_progress clamps to max."""
        widget = ProgressBarWidget(max_value=100)
        widget.set_progress(150)
        assert widget.progress == 100

    def test_progress_bar_set_progress_negative(self):
        """Test set_progress clamps negative values."""
        widget = ProgressBarWidget()
        widget.set_progress(-10)
        assert widget.progress == 0

    def test_progress_bar_set_status(self):
        """Test set_status method."""
        widget = ProgressBarWidget()
        widget.set_status("Loading...")
        assert widget.status_text == "Loading..."

    def test_progress_bar_increment(self):
        """Test increment method."""
        widget = ProgressBarWidget(progress=10)
        widget.increment(5)
        assert widget.progress == 15

    def test_progress_bar_increment_default(self):
        """Test increment with default amount."""
        widget = ProgressBarWidget(progress=10)
        widget.increment()
        assert widget.progress == 11

    def test_progress_bar_complete(self):
        """Test complete method."""
        widget = ProgressBarWidget(max_value=100)
        widget.complete()
        assert widget.progress == 100

    def test_progress_bar_reset(self):
        """Test reset method."""
        widget = ProgressBarWidget(progress=50, max_value=100)
        widget.reset()
        assert widget.progress == 0
        assert widget.status_text == ""


class TestProgressBarWidgetRender:
    """Tests for ProgressBarWidget render method."""

    def test_progress_bar_render_zero(self):
        """Test rendering at zero progress."""
        widget = ProgressBarWidget(progress=0, max_value=100)
        rendered = widget.render()
        assert "░" in rendered  # Empty bar

    def test_progress_bar_render_full(self):
        """Test rendering at full progress."""
        widget = ProgressBarWidget(progress=100, max_value=100)
        rendered = widget.render()
        assert "█" in rendered  # Filled bar

    def test_progress_bar_render_with_status(self):
        """Test rendering with status text."""
        widget = ProgressBarWidget(progress=50, status_text="Processing")
        rendered = widget.render()
        assert "Processing" in rendered

    def test_progress_bar_render_percentage(self):
        """Test rendering shows percentage."""
        widget = ProgressBarWidget(progress=50, max_value=100)
        rendered = widget.render()
        assert "50%" in rendered


class TestSpinnerWidget:
    """Tests for SpinnerWidget class."""

    def test_spinner_creation(self):
        """Test creating a SpinnerWidget."""
        widget = SpinnerWidget()
        assert widget.text == "Loading..."
        assert widget.is_spinning is True

    def test_spinner_custom_values(self):
        """Test creating with custom values."""
        widget = SpinnerWidget(text="Please wait", is_spinning=True)
        assert widget.text == "Please wait"
        assert widget.is_spinning is True

    def test_spinner_start(self):
        """Test start method."""
        widget = SpinnerWidget(is_spinning=False)
        widget.start()
        assert widget.is_spinning is True

    def test_spinner_stop(self):
        """Test stop method."""
        widget = SpinnerWidget(is_spinning=True)
        widget.stop()
        assert widget.is_spinning is False


class TestSpinnerWidgetRender:
    """Tests for SpinnerWidget render method."""

    def test_spinner_render_spinning(self):
        """Test rendering while spinning."""
        widget = SpinnerWidget(text="Loading", is_spinning=True)
        rendered = widget.render()
        assert "Loading" in rendered

    def test_spinner_render_stopped(self):
        """Test rendering when stopped."""
        widget = SpinnerWidget(text="Done", is_spinning=False)
        rendered = widget.render()
        assert "✓" in rendered
        assert "Done" in rendered


class TestStatusIndicator:
    """Tests for StatusIndicator class."""

    def test_status_indicator_creation(self):
        """Test creating a StatusIndicator."""
        widget = StatusIndicator()
        assert widget.status == "unknown"
        assert widget.label == ""

    def test_status_indicator_custom_values(self):
        """Test creating with custom values."""
        widget = StatusIndicator(status="ok", label="System")
        assert widget.status == "ok"
        assert widget.label == "System"

    def test_status_indicator_set_status(self):
        """Test set_status method."""
        widget = StatusIndicator()
        widget.set_status("success")
        assert widget.status == "success"

    def test_status_indicator_set_label(self):
        """Test set_label method."""
        widget = StatusIndicator()
        widget.set_label("Server")
        assert widget.label == "Server"


class TestStatusIndicatorRender:
    """Tests for StatusIndicator render method."""

    def test_status_indicator_render_ok(self):
        """Test rendering with ok status."""
        widget = StatusIndicator(status="ok")
        rendered = widget.render()
        assert "●" in rendered

    def test_status_indicator_render_error(self):
        """Test rendering with error status."""
        widget = StatusIndicator(status="error")
        rendered = widget.render()
        assert "✕" in rendered

    def test_status_indicator_render_running(self):
        """Test rendering with running status."""
        widget = StatusIndicator(status="running")
        rendered = widget.render()
        assert "◐" in rendered

    def test_status_indicator_render_with_label(self):
        """Test rendering with label."""
        widget = StatusIndicator(status="ok", label="Database")
        rendered = widget.render()
        assert "Database" in rendered


class TestStatusColors:
    """Tests for status color mapping."""

    def test_status_colors_has_ok(self):
        """Test ok status color exists."""
        assert "ok" in StatusIndicator.STATUS_COLORS

    def test_status_colors_has_error(self):
        """Test error status color exists."""
        assert "error" in StatusIndicator.STATUS_COLORS

    def test_status_colors_has_warning(self):
        """Test warning status color exists."""
        assert "warning" in StatusIndicator.STATUS_COLORS


class TestStatusIcons:
    """Tests for status icon mapping."""

    def test_status_icons_has_ok(self):
        """Test ok status icon exists."""
        assert "ok" in StatusIndicator.STATUS_ICONS

    def test_status_icons_has_error(self):
        """Test error status icon exists."""
        assert "error" in StatusIndicator.STATUS_ICONS

    def test_status_icons_has_warning(self):
        """Test warning status icon exists."""
        assert "warning" in StatusIndicator.STATUS_ICONS

    def test_status_icons_ok_is_filled_circle(self):
        """Test ok icon is filled circle."""
        assert StatusIndicator.STATUS_ICONS["ok"] == "●"
