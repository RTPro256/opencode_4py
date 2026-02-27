"""
File system sandboxing for opencode_4py.

This module provides sandboxing functionality to restrict file system access
to specific directories, with permission requests for external access.

When opencode_4py is integrated as a dependency, this ensures it cannot
access files outside the target project without explicit user permission.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, Optional, List, Set
from datetime import datetime


class AccessDecision(Enum):
    """Decision for file access request."""
    ALLOW = "allow"
    DENY = "deny"
    ALLOW_ONCE = "allow_once"
    DENY_ONCE = "deny_once"


class AccessType(Enum):
    """Type of file access being requested."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"


@dataclass
class AccessRequest:
    """A request for file system access."""
    path: Path
    access_type: AccessType
    timestamp: datetime = field(default_factory=datetime.now)
    reason: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "path": str(self.path),
            "access_type": self.access_type.value,
            "timestamp": self.timestamp.isoformat(),
            "reason": self.reason,
        }


@dataclass
class AccessRule:
    """A rule for allowing or denying access to a path."""
    path: Path
    access_types: Set[AccessType] = field(default_factory=lambda: set(AccessType))
    recursive: bool = True
    description: Optional[str] = None
    
    def matches(self, path: Path, access_type: AccessType) -> bool:
        """Check if this rule matches the given path and access type."""
        if access_type not in self.access_types:
            return False
        
        resolved_path = path.resolve()
        resolved_rule_path = self.path.resolve()
        
        if self.recursive:
            return resolved_path == resolved_rule_path or resolved_path.is_relative_to(resolved_rule_path)
        else:
            return resolved_path == resolved_rule_path


@dataclass
class PermissionCache:
    """Cache of permission decisions."""
    allowed_paths: dict[str, Set[AccessType]] = field(default_factory=dict)
    denied_paths: dict[str, Set[AccessType]] = field(default_factory=dict)
    
    def is_allowed(self, path: Path, access_type: AccessType) -> Optional[bool]:
        """Check if access is cached as allowed or denied."""
        path_str = str(path.resolve())
        
        if path_str in self.allowed_paths:
            if access_type in self.allowed_paths[path_str]:
                return True
        
        if path_str in self.denied_paths:
            if access_type in self.denied_paths[path_str]:
                return False
        
        return None
    
    def add_allowed(self, path: Path, access_types: Set[AccessType]) -> None:
        """Add allowed access to cache."""
        path_str = str(path.resolve())
        if path_str not in self.allowed_paths:
            self.allowed_paths[path_str] = set()
        self.allowed_paths[path_str].update(access_types)
    
    def add_denied(self, path: Path, access_types: Set[AccessType]) -> None:
        """Add denied access to cache."""
        path_str = str(path.resolve())
        if path_str not in self.denied_paths:
            self.denied_paths[path_str] = set()
        self.denied_paths[path_str].update(access_types)


class FileSandbox:
    """
    File system sandbox for restricting access to specific directories.
    
    Features:
    - Restricts file access to allowed directories
    - Requests permission for external access via callback
    - Caches permission decisions
    - Logs all access attempts
    """
    
    def __init__(
        self,
        allowed_roots: List[Path],
        permission_callback: Optional[Callable[[AccessRequest], AccessDecision]] = None,
        strict_mode: bool = True,
    ):
        """
        Initialize the file sandbox.
        
        Args:
            allowed_roots: List of root directories that are always allowed
            permission_callback: Callback for requesting permission for external access
            strict_mode: If True, deny access by default. If False, allow with warning.
        """
        self.allowed_roots = [p.resolve() for p in allowed_roots]
        self.permission_callback = permission_callback
        self.strict_mode = strict_mode
        self.permission_cache = PermissionCache()
        self.access_log: List[dict] = []
        
        # Additional allow rules (can be added dynamically)
        self.allow_rules: List[AccessRule] = []
        
        # Initialize default rules for allowed roots
        for root in self.allowed_roots:
            self.allow_rules.append(AccessRule(
                path=root,
                access_types=set(AccessType),
                recursive=True,
                description="Default allowed root",
            ))
    
    def add_allowed_path(
        self,
        path: Path,
        access_types: Optional[Set[AccessType]] = None,
        recursive: bool = True,
    ) -> None:
        """Add a new allowed path."""
        if access_types is None:
            access_types = set(AccessType)
        
        self.allow_rules.append(AccessRule(
            path=path.resolve(),
            access_types=access_types,
            recursive=recursive,
        ))
        
        # Also cache the permission
        self.permission_cache.add_allowed(path, access_types)
    
    def is_path_allowed(self, path: Path, access_type: AccessType) -> bool:
        """
        Check if a path is allowed for the given access type.
        
        This method checks:
        1. If the path matches any allow rules
        2. If the permission is cached
        3. If not, requests permission via callback (if available)
        
        Args:
            path: Path to check
            access_type: Type of access being requested
            
        Returns:
            True if access is allowed, False otherwise
        """
        resolved_path = path.resolve()
        
        # Log the access attempt
        self._log_access(resolved_path, access_type)
        
        # Check allow rules first
        for rule in self.allow_rules:
            if rule.matches(resolved_path, access_type):
                return True
        
        # Check permission cache
        cached = self.permission_cache.is_allowed(resolved_path, access_type)
        if cached is not None:
            return cached
        
        # Request permission if callback is available
        if self.permission_callback:
            request = AccessRequest(
                path=resolved_path,
                access_type=access_type,
                reason=f"Path is outside allowed directories: {resolved_path}",
            )
            decision = self.permission_callback(request)
            
            # Handle the decision
            if decision == AccessDecision.ALLOW:
                self.permission_cache.add_allowed(resolved_path, {access_type})
                return True
            elif decision == AccessDecision.ALLOW_ONCE:
                return True
            elif decision == AccessDecision.DENY:
                self.permission_cache.add_denied(resolved_path, {access_type})
                return False
            elif decision == AccessDecision.DENY_ONCE:
                return False
        
        # No callback or strict mode
        if self.strict_mode:
            return False
        else:
            # In non-strict mode, allow with a warning logged
            self._log_warning(resolved_path, access_type, "Allowed in non-strict mode")
            return True
    
    def check_path(self, path: Path, access_type: AccessType) -> tuple[bool, Optional[str]]:
        """
        Check if a path is allowed and return reason if denied.
        
        Returns:
            Tuple of (is_allowed, reason_if_denied)
        """
        resolved_path = path.resolve()
        
        # Check if path is within allowed roots
        for root in self.allowed_roots:
            if resolved_path == root or resolved_path.is_relative_to(root):
                return True, None
        
        # Check allow rules
        for rule in self.allow_rules:
            if rule.matches(resolved_path, access_type):
                return True, None
        
        # Check cache
        cached = self.permission_cache.is_allowed(resolved_path, access_type)
        if cached is True:
            return True, None
        if cached is False:
            return False, f"Access denied (cached): {resolved_path}"
        
        # Request permission
        if self.permission_callback:
            request = AccessRequest(
                path=resolved_path,
                access_type=access_type,
            )
            decision = self.permission_callback(request)
            
            if decision in (AccessDecision.ALLOW, AccessDecision.ALLOW_ONCE):
                return True, None
            else:
                return False, f"Access denied by user: {resolved_path}"
        
        # Strict mode denial
        if self.strict_mode:
            return False, f"Access denied: path outside allowed directories: {resolved_path}"
        
        return True, None
    
    def _log_access(self, path: Path, access_type: AccessType) -> None:
        """Log an access attempt."""
        self.access_log.append({
            "timestamp": datetime.now().isoformat(),
            "path": str(path),
            "access_type": access_type.value,
        })
    
    def _log_warning(self, path: Path, access_type: AccessType, message: str) -> None:
        """Log a warning."""
        self.access_log.append({
            "timestamp": datetime.now().isoformat(),
            "path": str(path),
            "access_type": access_type.value,
            "warning": message,
        })
    
    def get_access_log(self) -> List[dict]:
        """Get the access log."""
        return self.access_log.copy()
    
    def clear_cache(self) -> None:
        """Clear the permission cache."""
        self.permission_cache = PermissionCache()
    
    def to_dict(self) -> dict:
        """Serialize sandbox configuration."""
        return {
            "allowed_roots": [str(p) for p in self.allowed_roots],
            "strict_mode": self.strict_mode,
            "allow_rules": [
                {
                    "path": str(r.path),
                    "access_types": [t.value for t in r.access_types],
                    "recursive": r.recursive,
                    "description": r.description,
                }
                for r in self.allow_rules
            ],
        }


# Global sandbox instance (set when running in integration mode)
_global_sandbox: Optional[FileSandbox] = None


def initialize_sandbox(
    allowed_roots: List[Path],
    permission_callback: Optional[Callable[[AccessRequest], AccessDecision]] = None,
    strict_mode: bool = True,
) -> FileSandbox:
    """
    Initialize the global file sandbox.
    
    This should be called when opencode_4py is integrated as a dependency
    to restrict file system access.
    """
    global _global_sandbox
    _global_sandbox = FileSandbox(
        allowed_roots=allowed_roots,
        permission_callback=permission_callback,
        strict_mode=strict_mode,
    )
    return _global_sandbox


def get_sandbox() -> Optional[FileSandbox]:
    """Get the global file sandbox instance."""
    return _global_sandbox


def is_sandbox_active() -> bool:
    """Check if sandboxing is active."""
    return _global_sandbox is not None


def check_file_access(path: Path, access_type: AccessType) -> tuple[bool, Optional[str]]:
    """
    Check if file access is allowed.
    
    If sandbox is not active, returns (True, None).
    If sandbox is active, checks against the sandbox rules.
    """
    if _global_sandbox is None:
        return True, None
    
    return _global_sandbox.check_path(path, access_type)


# Convenience functions for common access types
def check_read_access(path: Path) -> tuple[bool, Optional[str]]:
    """Check if read access is allowed."""
    return check_file_access(path, AccessType.READ)


def check_write_access(path: Path) -> tuple[bool, Optional[str]]:
    """Check if write access is allowed."""
    return check_file_access(path, AccessType.WRITE)


def check_delete_access(path: Path) -> tuple[bool, Optional[str]]:
    """Check if delete access is allowed."""
    return check_file_access(path, AccessType.DELETE)
