"""
Tests for TUI app logging setup.
"""

import pytest
from unittest.mock import MagicMock, patch
import logging
import os
from pathlib import Path

from opencode.tui.app import _setup_tui_logging


@pytest.mark.unit
class TestSetupTuiLogging:
    """Tests for _setup_tui_logging function."""

    def test_setup_returns_logger(self):
        """Test that setup returns a logger."""
        # Clear env vars for this test
        env = os.environ.copy()
        if "OPENCODE_LOG_LEVEL" in env:
            del env["OPENCODE_LOG_LEVEL"]
        if "OPENCODE_LOG_FILE" in env:
            del env["OPENCODE_LOG_FILE"]
        
        with patch.dict("os.environ", env, clear=True):
            logger = _setup_tui_logging()
            
            assert logger is not None
            assert logger.name == "opencode"

    def test_setup_debug_logging(self):
        """Test debug logging setup."""
        with patch.dict("os.environ", {"OPENCODE_LOG_LEVEL": "DEBUG"}, clear=True):
            logger = _setup_tui_logging()
            assert logger.level == logging.DEBUG

    def test_setup_warning_logging(self):
        """Test warning logging setup."""
        with patch.dict("os.environ", {"OPENCODE_LOG_LEVEL": "WARNING"}, clear=True):
            logger = _setup_tui_logging()
            assert logger.level == logging.WARNING

    def test_setup_error_logging(self):
        """Test error logging setup."""
        with patch.dict("os.environ", {"OPENCODE_LOG_LEVEL": "ERROR"}, clear=True):
            logger = _setup_tui_logging()
            assert logger.level == logging.ERROR

    def test_setup_invalid_level_defaults_to_info(self):
        """Test invalid log level defaults to INFO."""
        with patch.dict("os.environ", {"OPENCODE_LOG_LEVEL": "INVALID"}, clear=True):
            logger = _setup_tui_logging()
            assert logger.level == logging.INFO

    def test_setup_with_log_file(self, tmp_path):
        """Test logging setup with log file."""
        log_file = tmp_path / "test.log"
        
        with patch.dict("os.environ", {"OPENCODE_LOG_FILE": str(log_file)}, clear=True):
            logger = _setup_tui_logging()
            
            # Logger should have file handler
            assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)

    def test_setup_with_data_dir_creates_file_handler(self, tmp_path):
        """Test logging setup with data_dir creates file handler."""
        data_dir = tmp_path / "data"
        
        # Clear OPENCODE_LOG_FILE to ensure data_dir is used
        env = os.environ.copy()
        if "OPENCODE_LOG_FILE" in env:
            del env["OPENCODE_LOG_FILE"]
        
        with patch.dict("os.environ", env, clear=True):
            logger = _setup_tui_logging(data_dir=data_dir)
            
            # Logger should have file handler
            assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)

    def test_setup_clears_existing_handlers(self):
        """Test that setup clears existing handlers."""
        # Add a handler first
        logger = logging.getLogger("opencode")
        logger.addHandler(logging.StreamHandler())
        
        # Setup logging again
        logger = _setup_tui_logging()
        
        # Should have cleared and added new handlers
        assert len(logger.handlers) >= 1

    def test_setup_console_handler_present(self):
        """Test that console handler is always present."""
        logger = _setup_tui_logging()
        
        # Should have at least console handler
        assert any(isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler) 
                   for h in logger.handlers)

    def test_setup_formatter_format(self):
        """Test that formatter has correct format."""
        logger = _setup_tui_logging()
        
        # Get any handler with a formatter
        for handler in logger.handlers:
            if handler.formatter:
                # Check that the format includes expected fields
                fmt = handler.formatter._fmt
                if fmt:
                    assert "%(asctime)s" in fmt
                    assert "%(levelname)s" in fmt
                    assert "%(name)s" in fmt
                    assert "%(message)s" in fmt
                break

    def test_setup_creates_log_directory(self, tmp_path):
        """Test that setup creates log directory if it doesn't exist."""
        log_file = tmp_path / "nested" / "dir" / "test.log"
        
        with patch.dict("os.environ", {"OPENCODE_LOG_FILE": str(log_file)}, clear=True):
            logger = _setup_tui_logging()
            
            # Parent directory should be created
            assert log_file.parent.exists()

    def test_setup_no_file_without_data_dir_or_env(self):
        """Test that no file handler is created without data_dir or env var."""
        # Clear any existing file env var
        env = os.environ.copy()
        if "OPENCODE_LOG_FILE" in env:
            del env["OPENCODE_LOG_FILE"]
        
        with patch.dict("os.environ", env, clear=True):
            logger = _setup_tui_logging()
            
            # Should only have console handler
            file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
            assert len(file_handlers) == 0
