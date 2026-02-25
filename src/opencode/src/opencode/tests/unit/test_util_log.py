"""
Tests for util/log.py

Tests for logging utilities including LogLevel, LogFormat, StructuredFormatter,
Logger, BoundLogger, and convenience functions.
"""

import pytest
import logging
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from opencode.util.log import (
    LogLevel,
    LogFormat,
    StructuredFormatter,
    Logger,
    BoundLogger,
    get_context,
    set_context,
    clear_context,
    init_logging,
    get_logger,
    debug,
    info,
    warning,
    error,
    critical,
    exception,
)


class TestLogLevel:
    """Tests for LogLevel enum."""

    def test_debug_value(self):
        """Test DEBUG level value."""
        assert LogLevel.DEBUG.value == "DEBUG"

    def test_info_value(self):
        """Test INFO level value."""
        assert LogLevel.INFO.value == "INFO"

    def test_warning_value(self):
        """Test WARNING level value."""
        assert LogLevel.WARNING.value == "WARNING"

    def test_error_value(self):
        """Test ERROR level value."""
        assert LogLevel.ERROR.value == "ERROR"

    def test_critical_value(self):
        """Test CRITICAL level value."""
        assert LogLevel.CRITICAL.value == "CRITICAL"

    def test_is_string_enum(self):
        """Test that LogLevel is a string enum."""
        assert LogLevel.DEBUG == "DEBUG"
        assert isinstance(LogLevel.DEBUG, str)


class TestLogFormat:
    """Tests for LogFormat enum."""

    def test_text_value(self):
        """Test TEXT format value."""
        assert LogFormat.TEXT.value == "text"

    def test_json_value(self):
        """Test JSON format value."""
        assert LogFormat.JSON.value == "json"


class TestContextFunctions:
    """Tests for context management functions."""

    def test_get_context_default(self):
        """Test get_context returns empty dict by default."""
        clear_context()
        result = get_context()
        assert result == {}

    def test_set_context(self):
        """Test set_context sets values."""
        clear_context()
        set_context(user="test", request_id="123")
        
        result = get_context()
        assert result["user"] == "test"
        assert result["request_id"] == "123"

    def test_set_context_merges(self):
        """Test set_context merges with existing context."""
        clear_context()
        set_context(a=1)
        set_context(b=2)
        
        result = get_context()
        assert result["a"] == 1
        assert result["b"] == 2

    def test_set_context_overwrites(self):
        """Test set_context overwrites existing keys."""
        clear_context()
        set_context(key="value1")
        set_context(key="value2")
        
        result = get_context()
        assert result["key"] == "value2"

    def test_clear_context(self):
        """Test clear_context clears all values."""
        set_context(user="test")
        clear_context()
        
        result = get_context()
        assert result == {}


class TestStructuredFormatter:
    """Tests for StructuredFormatter class."""

    def test_format_text_basic(self):
        """Test text format with basic record."""
        formatter = StructuredFormatter(fmt=LogFormat.TEXT)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        
        result = formatter.format(record)
        
        assert "Test message" in result
        assert "INFO" in result
        assert "test" in result

    def test_format_json_basic(self):
        """Test JSON format with basic record."""
        formatter = StructuredFormatter(fmt=LogFormat.JSON)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        
        result = formatter.format(record)
        data = json.loads(result)
        
        assert data["message"] == "Test message"
        assert data["level"] == "INFO"
        assert data["logger"] == "test"
        assert "timestamp" in data

    def test_format_json_with_context(self):
        """Test JSON format includes context."""
        clear_context()
        set_context(user="testuser")
        
        formatter = StructuredFormatter(fmt=LogFormat.JSON)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        
        result = formatter.format(record)
        data = json.loads(result)
        
        assert data["user"] == "testuser"
        clear_context()

    def test_format_json_with_extra_data(self):
        """Test JSON format includes extra data."""
        formatter = StructuredFormatter(fmt=LogFormat.JSON)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.data = {"key": "value"}
        
        result = formatter.format(record)
        data = json.loads(result)
        
        assert data["data"]["key"] == "value"

    def test_format_text_with_context(self):
        """Test text format includes context."""
        clear_context()
        set_context(request_id="abc123")
        
        formatter = StructuredFormatter(fmt=LogFormat.TEXT)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        
        result = formatter.format(record)
        
        assert "request_id=abc123" in result
        clear_context()

    def test_format_text_with_extra_data(self):
        """Test text format includes extra data."""
        formatter = StructuredFormatter(fmt=LogFormat.TEXT)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.data = {"key": "value"}
        
        result = formatter.format(record)
        
        assert '"key": "value"' in result

    def test_format_text_with_exception(self):
        """Test text format includes exception info."""
        formatter = StructuredFormatter(fmt=LogFormat.TEXT)
        
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
        
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=exc_info,
        )
        
        result = formatter.format(record)
        
        assert "ValueError" in result
        assert "Test error" in result

    def test_format_json_with_exception(self):
        """Test JSON format includes exception info."""
        formatter = StructuredFormatter(fmt=LogFormat.JSON)
        
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
        
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=exc_info,
        )
        
        result = formatter.format(record)
        data = json.loads(result)
        
        assert "exception" in data
        assert "ValueError" in data["exception"]


class TestLogger:
    """Tests for Logger class."""

    def test_init(self):
        """Test Logger initialization."""
        logger = Logger("test_logger")
        
        assert logger.name == "test_logger"
        assert logger._logger.level == logging.INFO

    def test_init_with_level(self):
        """Test Logger initialization with custom level."""
        logger = Logger("test_logger", level=LogLevel.DEBUG)
        
        assert logger._logger.level == logging.DEBUG

    def test_init_with_format(self):
        """Test Logger initialization with custom format."""
        logger = Logger("test_logger", log_format=LogFormat.JSON)
        
        assert logger._format == LogFormat.JSON

    def test_add_console_handler(self):
        """Test adding console handler."""
        logger = Logger("test_console")
        logger.add_console_handler()
        
        assert len(logger._logger.handlers) == 1
        assert isinstance(logger._logger.handlers[0], logging.StreamHandler)

    def test_add_file_handler(self, tmp_path):
        """Test adding file handler."""
        logger = Logger("test_file")
        log_file = tmp_path / "logs" / "test.log"
        logger.add_file_handler(log_file)
        
        assert len(logger._logger.handlers) == 1
        assert isinstance(logger._logger.handlers[0], logging.FileHandler)

    def test_set_level(self):
        """Test setting log level."""
        logger = Logger("test_level")
        logger.set_level(LogLevel.DEBUG)
        
        assert logger._logger.level == logging.DEBUG

    def test_debug_log(self):
        """Test debug logging."""
        logger = Logger("test_debug", level=LogLevel.DEBUG)
        logger.add_console_handler()
        
        # Should not raise
        logger.debug("Debug message")

    def test_info_log(self):
        """Test info logging."""
        logger = Logger("test_info", level=LogLevel.INFO)
        logger.add_console_handler()
        
        # Should not raise
        logger.info("Info message")

    def test_warning_log(self):
        """Test warning logging."""
        logger = Logger("test_warning", level=LogLevel.WARNING)
        logger.add_console_handler()
        
        # Should not raise
        logger.warning("Warning message")

    def test_error_log(self):
        """Test error logging."""
        logger = Logger("test_error", level=LogLevel.ERROR)
        logger.add_console_handler()
        
        # Should not raise
        logger.error("Error message")

    def test_critical_log(self):
        """Test critical logging."""
        logger = Logger("test_critical", level=LogLevel.CRITICAL)
        logger.add_console_handler()
        
        # Should not raise
        logger.critical("Critical message")

    def test_log_with_kwargs(self):
        """Test logging with extra kwargs."""
        logger = Logger("test_kwargs", level=LogLevel.INFO)
        logger.add_console_handler()
        
        # Should not raise
        logger.info("Message with data", key="value", count=42)

    def test_exception_log(self):
        """Test exception logging."""
        logger = Logger("test_exception", level=LogLevel.ERROR)
        logger.add_console_handler()
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            # Should not raise
            logger.exception("Caught exception")

    def test_with_context(self):
        """Test creating bound logger."""
        logger = Logger("test_bound", level=LogLevel.INFO)
        bound = logger.with_context(request_id="123")
        
        assert isinstance(bound, BoundLogger)
        assert bound._context == {"request_id": "123"}


class TestBoundLogger:
    """Tests for BoundLogger class."""

    def test_debug_with_context(self):
        """Test debug with bound context."""
        logger = Logger("bound_test", level=LogLevel.DEBUG)
        logger.add_console_handler()
        bound = BoundLogger(logger, {"service": "test"})
        
        # Should not raise
        bound.debug("Debug message")

    def test_info_with_context(self):
        """Test info with bound context."""
        logger = Logger("bound_test", level=LogLevel.INFO)
        logger.add_console_handler()
        bound = BoundLogger(logger, {"service": "test"})
        
        # Should not raise
        bound.info("Info message")

    def test_warning_with_context(self):
        """Test warning with bound context."""
        logger = Logger("bound_test", level=LogLevel.WARNING)
        logger.add_console_handler()
        bound = BoundLogger(logger, {"service": "test"})
        
        # Should not raise
        bound.warning("Warning message")

    def test_error_with_context(self):
        """Test error with bound context."""
        logger = Logger("bound_test", level=LogLevel.ERROR)
        logger.add_console_handler()
        bound = BoundLogger(logger, {"service": "test"})
        
        # Should not raise
        bound.error("Error message")

    def test_critical_with_context(self):
        """Test critical with bound context."""
        logger = Logger("bound_test", level=LogLevel.CRITICAL)
        logger.add_console_handler()
        bound = BoundLogger(logger, {"service": "test"})
        
        # Should not raise
        bound.critical("Critical message")

    def test_context_merges_with_kwargs(self):
        """Test that bound context merges with kwargs."""
        logger = Logger("merge_test", level=LogLevel.INFO)
        logger.add_console_handler()
        bound = BoundLogger(logger, {"bound_key": "bound_value"})
        
        # Should not raise - kwargs should merge with bound context
        bound.info("Message", extra_key="extra_value")


class TestInitLogging:
    """Tests for init_logging function."""

    def test_init_logging_basic(self):
        """Test basic logging initialization."""
        import opencode.util.log as log_module
        log_module._default_logger = None
        
        logger = init_logging()
        
        assert logger is not None
        assert logger.name == "opencode"
        assert len(logger._logger.handlers) == 1  # Console handler

    def test_init_logging_with_level(self):
        """Test logging initialization with custom level."""
        import opencode.util.log as log_module
        log_module._default_logger = None
        
        logger = init_logging(level=LogLevel.DEBUG)
        
        assert logger._logger.level == logging.DEBUG

    def test_init_logging_with_format(self):
        """Test logging initialization with custom format."""
        import opencode.util.log as log_module
        log_module._default_logger = None
        
        logger = init_logging(log_format=LogFormat.JSON)
        
        assert logger._format == LogFormat.JSON

    def test_init_logging_with_file(self, tmp_path):
        """Test logging initialization with file handler."""
        import opencode.util.log as log_module
        log_module._default_logger = None
        
        log_file = tmp_path / "test.log"
        logger = init_logging(log_file=log_file)
        
        assert len(logger._logger.handlers) == 2  # Console + File


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_default(self):
        """Test getting default logger."""
        import opencode.util.log as log_module
        log_module._default_logger = None
        
        logger = get_logger()
        
        assert logger.name == "opencode"

    def test_get_logger_with_name(self):
        """Test getting named logger."""
        logger = get_logger("custom_logger")
        
        assert logger.name == "custom_logger"

    def test_get_logger_returns_same_default(self):
        """Test that get_logger returns same default instance."""
        import opencode.util.log as log_module
        log_module._default_logger = None
        
        logger1 = get_logger()
        logger2 = get_logger()
        
        assert logger1 is logger2


class TestConvenienceFunctions:
    """Tests for convenience logging functions."""

    def test_debug_function(self):
        """Test debug convenience function."""
        import opencode.util.log as log_module
        log_module._default_logger = None
        
        # Should not raise
        debug("Debug message")

    def test_info_function(self):
        """Test info convenience function."""
        import opencode.util.log as log_module
        log_module._default_logger = None
        
        # Should not raise
        info("Info message")

    def test_warning_function(self):
        """Test warning convenience function."""
        import opencode.util.log as log_module
        log_module._default_logger = None
        
        # Should not raise
        warning("Warning message")

    def test_error_function(self):
        """Test error convenience function."""
        import opencode.util.log as log_module
        log_module._default_logger = None
        
        # Should not raise
        error("Error message")

    def test_critical_function(self):
        """Test critical convenience function."""
        import opencode.util.log as log_module
        log_module._default_logger = None
        
        # Should not raise
        critical("Critical message")

    def test_exception_function(self):
        """Test exception convenience function."""
        import opencode.util.log as log_module
        log_module._default_logger = None
        
        try:
            raise ValueError("Test error")
        except ValueError:
            # Should not raise
            exception("Caught exception")

    def test_functions_with_kwargs(self):
        """Test convenience functions with kwargs."""
        import opencode.util.log as log_module
        log_module._default_logger = None
        
        # Should not raise
        info("Message with data", key="value", count=42)


class TestLoggerIntegration:
    """Integration tests for logging."""

    def test_full_logging_workflow(self, tmp_path):
        """Test a complete logging workflow."""
        import opencode.util.log as log_module
        log_module._default_logger = None
        
        # Initialize logging
        log_file = tmp_path / "app.log"
        logger = init_logging(
            level=LogLevel.DEBUG,
            log_format=LogFormat.TEXT,
            log_file=log_file,
        )
        
        # Set context
        set_context(app="test_app")
        
        # Log messages
        logger.debug("Debug message")
        logger.info("Info message", user="test")
        logger.warning("Warning message")
        logger.error("Error message")
        
        # Create bound logger
        bound = logger.with_context(request_id="req-123")
        bound.info("Request started")
        
        # Clear context
        clear_context()
        
        # Verify log file exists
        assert log_file.exists()

    def test_json_logging_to_file(self, tmp_path):
        """Test JSON logging to file."""
        import opencode.util.log as log_module
        log_module._default_logger = None
        
        log_file = tmp_path / "json.log"
        logger = Logger("json_test", level=LogLevel.INFO, log_format=LogFormat.JSON)
        logger.add_file_handler(log_file)
        
        logger.info("Test message", key="value")
        
        # Read and parse log file
        with open(log_file) as f:
            content = f.read()
        
        # Should be valid JSON
        data = json.loads(content.strip())
        assert data["message"] == "Test message"
        assert data["data"]["key"] == "value"
