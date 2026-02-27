"""
Subagent error definitions.
"""

from typing import Optional
from .types import SubagentErrorCode


class SubagentError(Exception):
    """Base exception for subagent operations."""
    
    def __init__(
        self,
        message: str,
        code: SubagentErrorCode,
        details: Optional[dict] = None
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        return f"[{self.code.value}] {self.message}"
    
    def to_dict(self) -> dict:
        """Convert error to dictionary for serialization."""
        return {
            "code": self.code.value,
            "message": self.message,
            "details": self.details,
        }


class SubagentNotFoundError(SubagentError):
    """Raised when a subagent is not found."""
    
    def __init__(self, name: str, level: Optional[str] = None):
        message = f"Subagent '{name}' not found"
        if level:
            message += f" at {level} level"
        super().__init__(message, SubagentErrorCode.NOT_FOUND, {"name": name, "level": level})


class SubagentAlreadyExistsError(SubagentError):
    """Raised when trying to create a subagent that already exists."""
    
    def __init__(self, name: str, level: str):
        super().__init__(
            f"Subagent '{name}' already exists at {level} level",
            SubagentErrorCode.ALREADY_EXISTS,
            {"name": name, "level": level}
        )


class SubagentValidationError(SubagentError):
    """Raised when subagent configuration validation fails."""
    
    def __init__(self, errors: list[str], warnings: Optional[list[str]] = None):
        super().__init__(
            f"Validation failed: {'; '.join(errors)}",
            SubagentErrorCode.VALIDATION_ERROR,
            {"errors": errors, "warnings": warnings or []}
        )
        self.validation_errors = errors
        self.validation_warnings = warnings or []


class SubagentFileError(SubagentError):
    """Raised when there's an error reading/writing subagent files."""
    
    def __init__(self, path: str, operation: str, original_error: Optional[Exception] = None):
        super().__init__(
            f"Failed to {operation} subagent file: {path}",
            SubagentErrorCode.FILE_ERROR,
            {"path": path, "operation": operation, "original_error": str(original_error) if original_error else None}
        )


class SubagentExecutionError(SubagentError):
    """Raised when subagent execution fails."""
    
    def __init__(self, name: str, reason: str, details: Optional[dict] = None):
        super().__init__(
            f"Subagent '{name}' execution failed: {reason}",
            SubagentErrorCode.EXECUTION_ERROR,
            {"name": name, "reason": reason, **(details or {})}
        )


class SubagentPermissionError(SubagentError):
    """Raised when permission is denied for subagent operation."""
    
    def __init__(self, operation: str, resource: str):
        super().__init__(
            f"Permission denied for {operation} on {resource}",
            SubagentErrorCode.PERMISSION_DENIED,
            {"operation": operation, "resource": resource}
        )
