"""
Logging utilities for OpenCode.

Provides structured logging with support for:
- Multiple output formats (text, JSON)
- File and console handlers
- Context-aware logging
- Log levels
"""

from __future__ import annotations

import json
import logging
import os
import sys
from contextvars import ContextVar
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class LogLevel(str, Enum):
    """Log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(str, Enum):
    """Log output formats."""
    TEXT = "text"
    JSON = "json"


# Context variables for structured logging
_context: ContextVar[dict[str, Any]] = ContextVar("log_context", default={})


def get_context() -> dict[str, Any]:
    """Get the current logging context."""
    return _context.get()


def set_context(**kwargs: Any) -> None:
    """Set context values for logging."""
    current = _context.get().copy()
    current.update(kwargs)
    _context.set(current)


def clear_context() -> None:
    """Clear the logging context."""
    _context.set({})


class StructuredFormatter(logging.Formatter):
    """Custom formatter that includes structured context."""
    
    def __init__(self, fmt: LogFormat = LogFormat.TEXT):
        super().__init__()
        self.fmt = fmt
    
    def format(self, record: logging.LogRecord) -> str:
        # Get context
        context = get_context()
        
        # Add timestamp
        timestamp = datetime.fromtimestamp(record.created).isoformat()
        
        if self.fmt == LogFormat.JSON:
            # JSON format
            log_entry = {
                "timestamp": timestamp,
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                **context,
            }
            
            # Add exception info if present
            if record.exc_info:
                log_entry["exception"] = self.formatException(record.exc_info)
            
            # Add extra fields
            if hasattr(record, "data"):
                log_entry["data"] = record.data
            
            return json.dumps(log_entry)
        else:
            # Text format with colors
            level_colors = {
                "DEBUG": "\033[36m",     # Cyan
                "INFO": "\033[32m",      # Green
                "WARNING": "\033[33m",   # Yellow
                "ERROR": "\033[31m",     # Red
                "CRITICAL": "\033[35m",  # Magenta
            }
            reset = "\033[0m"
            dim = "\033[2m"
            
            color = level_colors.get(record.levelname, "")
            
            # Build the log line
            parts = [
                f"{dim}{timestamp}{reset}",
                f"{color}{record.levelname:8}{reset}",
                f"{dim}[{record.name}]{reset}",
                record.getMessage(),
            ]
            
            # Add context if present
            if context:
                context_str = " ".join(f"{k}={v}" for k, v in context.items())
                parts.append(f"{dim}{context_str}{reset}")
            
            # Add extra data if present
            if hasattr(record, "data") and record.data:
                parts.append(f"{dim}{json.dumps(record.data)}{reset}")
            
            line = " ".join(parts)
            
            # Add exception if present
            if record.exc_info:
                line += f"\n{self.formatException(record.exc_info)}"
            
            return line


class Logger:
    """
    Enhanced logger with structured logging support.
    
    Features:
        - Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        - Multiple output formats (TEXT, JSON)
        - Console and file handlers
        - Module filtering for targeted debugging
        - Context-aware logging
    
    Usage:
        # Basic usage
        log = Logger("myapp")
        log.info("Starting application")
        log.info("Processing request", request_id="123")
        log.error("Failed to process", error=str(e))
        
        # Module filtering - only log from specific modules
        log = Logger("myapp")
        log.add_module_filter(["ollama", "anthropic"])  # Only log from these
        
        # Environment variables:
        # OPENCODE_LOG_LEVEL=DEBUG        # Set global log level
        # OPENCODE_LOG_FILE=/path/to.log  # Set log file
        # OPENCODE_LOG_MODULES=ollama,anthropic  # Filter specific modules
    """
    
    def __init__(
        self,
        name: str,
        level: LogLevel = LogLevel.INFO,
        log_format: LogFormat = LogFormat.TEXT,
    ):
        self.name = name
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level.value)
        self._logger.handlers.clear()
        self._format = log_format
        self._module_filters: Optional[list[str]] = None
        
        # Check for environment variable configuration
        self._load_env_config()
    
    def _load_env_config(self) -> None:
        """Load configuration from environment variables."""
        log_level = os.environ.get("OPENCODE_LOG_LEVEL", "INFO").upper()
        if log_level in [l.value for l in LogLevel]:
            self._logger.setLevel(LogLevel(log_level).value)
        
        # Load module filters from environment
        module_filter = os.environ.get("OPENCODE_LOG_MODULES", "")
        if module_filter:
            self._module_filters = [m.strip() for m in module_filter.split(",")]
    
    def add_module_filter(self, modules: list[str]) -> None:
        """
        Add module filters to only log from specific modules.
        
        Args:
            modules: List of module names (e.g., ["ollama", "anthropic"])
                    Logs from any logger whose name starts with these prefixes.
        """
        self._module_filters = modules
    
    def _should_log(self, logger_name: str) -> bool:
        """
        Check if the logger should log based on module filters.
        
        Args:
            logger_name: Name of the logger to check
            
        Returns:
            True if logging is allowed, False otherwise
        """
        if not self._module_filters:
            return True  # No filters, log everything
        
        return any(logger_name.startswith(f) for f in self._module_filters)
    
    def add_console_handler(
        self,
        level: Optional[LogLevel] = None,
        log_format: Optional[LogFormat] = None,
    ) -> None:
        """Add a console handler."""
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel((level or LogLevel.DEBUG).value)
        handler.setFormatter(StructuredFormatter(log_format or self._format))
        self._logger.addHandler(handler)
    
    def add_file_handler(
        self,
        path: Path,
        level: Optional[LogLevel] = None,
        log_format: Optional[LogFormat] = None,
    ) -> None:
        """Add a file handler."""
        path.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(path)
        handler.setLevel((level or LogLevel.DEBUG).value)
        handler.setFormatter(StructuredFormatter(log_format or LogFormat.JSON))
        self._logger.addHandler(handler)
    
    def set_level(self, level: LogLevel) -> None:
        """Set the log level."""
        self._logger.setLevel(level.value)
    
    def _log(self, level: int, message: str, **kwargs: Any) -> None:
        """Internal logging method."""
        # Check module filter
        if not self._should_log(self._logger.name):
            return
            
        # Create a record with extra data
        extra = {"data": kwargs} if kwargs else {}
        self._logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log a debug message."""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log an info message."""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message."""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Log an error message."""
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs: Any) -> None:
        """Log a critical message."""
        self._log(logging.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, **kwargs: Any) -> None:
        """Log an exception with traceback."""
        self._logger.exception(message, extra={"data": kwargs} if kwargs else {})
    
    def with_context(self, **kwargs: Any) -> "BoundLogger":
        """Create a logger with bound context."""
        return BoundLogger(self, kwargs)


class BoundLogger:
    """A logger with bound context values."""
    
    def __init__(self, logger: Logger, context: dict[str, Any]):
        self._logger = logger
        self._context = context
    
    def _log(self, level: int, message: str, **kwargs: Any) -> None:
        """Log with merged context."""
        merged = {**self._context, **kwargs}
        self._logger._log(level, message, **merged)
    
    def debug(self, message: str, **kwargs: Any) -> None:
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs: Any) -> None:
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs: Any) -> None:
        self._log(logging.CRITICAL, message, **kwargs)


# Global logger instance
_default_logger: Optional[Logger] = None


def init_logging(
    level: LogLevel = LogLevel.INFO,
    log_format: LogFormat = LogFormat.TEXT,
    log_file: Optional[Path] = None,
) -> Logger:
    """
    Initialize the global logger.
    
    Args:
        level: Log level
        log_format: Output format
        log_file: Optional file to log to
        
    Returns:
        The configured logger
    """
    global _default_logger
    
    _default_logger = Logger("opencode", level=level, log_format=log_format)
    _default_logger.add_console_handler()
    
    if log_file:
        _default_logger.add_file_handler(log_file, log_format=LogFormat.JSON)
    
    return _default_logger


def get_logger(name: Optional[str] = None) -> Logger:
    """Get a logger instance."""
    global _default_logger
    
    if name is None:
        if _default_logger is None:
            _default_logger = Logger("opencode")
        return _default_logger
    
    return Logger(name)


# Convenience functions using the default logger
def debug(message: str, **kwargs: Any) -> None:
    get_logger().debug(message, **kwargs)


def info(message: str, **kwargs: Any) -> None:
    get_logger().info(message, **kwargs)


def warning(message: str, **kwargs: Any) -> None:
    get_logger().warning(message, **kwargs)


def error(message: str, **kwargs: Any) -> None:
    get_logger().error(message, **kwargs)


def critical(message: str, **kwargs: Any) -> None:
    get_logger().critical(message, **kwargs)


def exception(message: str, **kwargs: Any) -> None:
    get_logger().exception(message, **kwargs)
