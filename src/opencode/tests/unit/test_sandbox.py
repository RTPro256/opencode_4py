"""
Tests for file system sandbox module.
"""

import pytest
from unittest.mock import MagicMock
from pathlib import Path
from datetime import datetime

from opencode.core.sandbox import (
    AccessDecision,
    AccessType,
    AccessRequest,
    AccessRule,
    PermissionCache,
    FileSandbox,
)


@pytest.mark.unit
class TestAccessDecision:
    """Tests for AccessDecision enum."""

    def test_access_decision_values(self):
        """Test AccessDecision enum values."""
        assert AccessDecision.ALLOW.value == "allow"
        assert AccessDecision.DENY.value == "deny"
        assert AccessDecision.ALLOW_ONCE.value == "allow_once"
        assert AccessDecision.DENY_ONCE.value == "deny_once"


@pytest.mark.unit
class TestAccessType:
    """Tests for AccessType enum."""

    def test_access_type_values(self):
        """Test AccessType enum values."""
        assert AccessType.READ.value == "read"
        assert AccessType.WRITE.value == "write"
        assert AccessType.DELETE.value == "delete"
        assert AccessType.EXECUTE.value == "execute"


@pytest.mark.unit
class TestAccessRequest:
    """Tests for AccessRequest dataclass."""

    def test_access_request_creation(self):
        """Test AccessRequest instantiation."""
        path = Path("/test/path")
        request = AccessRequest(path=path, access_type=AccessType.READ)
        assert request.path == path
        assert request.access_type == AccessType.READ
        assert isinstance(request.timestamp, datetime)

    def test_access_request_with_reason(self):
        """Test AccessRequest with reason."""
        path = Path("/test/path")
        request = AccessRequest(
            path=path,
            access_type=AccessType.WRITE,
            reason="Test reason"
        )
        assert request.reason == "Test reason"

    def test_access_request_to_dict(self):
        """Test AccessRequest.to_dict method."""
        path = Path("/test/path")
        request = AccessRequest(
            path=path,
            access_type=AccessType.READ,
            reason="Test reason"
        )
        result = request.to_dict()
        assert "path" in result
        assert "access_type" in result
        assert "timestamp" in result
        assert "reason" in result
        assert result["access_type"] == "read"


@pytest.mark.unit
class TestAccessRule:
    """Tests for AccessRule dataclass."""

    def test_access_rule_creation(self):
        """Test AccessRule instantiation."""
        path = Path("/test/path")
        rule = AccessRule(path=path)
        assert rule.path == path
        assert rule.recursive is True
        assert len(rule.access_types) == 4  # All access types by default

    def test_access_rule_matches_exact_path(self):
        """Test AccessRule.matches for exact path."""
        path = Path("/test/path")
        rule = AccessRule(path=path, recursive=False)
        
        # Exact match should work
        assert rule.matches(path, AccessType.READ) is True
        
        # Different path should not match
        other_path = Path("/other/path")
        assert rule.matches(other_path, AccessType.READ) is False

    def test_access_rule_matches_recursive(self, tmp_path):
        """Test AccessRule.matches for recursive paths."""
        # Create a temporary directory structure
        root = tmp_path / "root"
        root.mkdir()
        subfolder = root / "subfolder"
        subfolder.mkdir()
        file_path = subfolder / "file.txt"
        file_path.touch()
        
        rule = AccessRule(path=root, recursive=True)
        
        # Root should match
        assert rule.matches(root, AccessType.READ) is True
        # Subfolder should match
        assert rule.matches(subfolder, AccessType.READ) is True
        # File should match
        assert rule.matches(file_path, AccessType.READ) is True

    def test_access_rule_access_type_filter(self):
        """Test AccessRule with specific access types."""
        path = Path("/test/path")
        rule = AccessRule(path=path, access_types={AccessType.READ, AccessType.WRITE})
        
        assert rule.matches(path, AccessType.READ) is True
        assert rule.matches(path, AccessType.WRITE) is True
        assert rule.matches(path, AccessType.DELETE) is False
        assert rule.matches(path, AccessType.EXECUTE) is False


@pytest.mark.unit
class TestPermissionCache:
    """Tests for PermissionCache dataclass."""

    def test_permission_cache_creation(self):
        """Test PermissionCache instantiation."""
        cache = PermissionCache()
        assert cache.allowed_paths == {}
        assert cache.denied_paths == {}

    def test_add_allowed(self):
        """Test PermissionCache.add_allowed method."""
        cache = PermissionCache()
        path = Path("/test/path")
        
        cache.add_allowed(path, {AccessType.READ})
        
        assert cache.is_allowed(path, AccessType.READ) is True
        assert cache.is_allowed(path, AccessType.WRITE) is None

    def test_add_denied(self):
        """Test PermissionCache.add_denied method."""
        cache = PermissionCache()
        path = Path("/test/path")
        
        cache.add_denied(path, {AccessType.WRITE})
        
        assert cache.is_allowed(path, AccessType.WRITE) is False
        assert cache.is_allowed(path, AccessType.READ) is None

    def test_is_allowed_returns_none_for_unknown(self):
        """Test PermissionCache.is_allowed returns None for unknown paths."""
        cache = PermissionCache()
        path = Path("/test/path")
        
        assert cache.is_allowed(path, AccessType.READ) is None

    def test_multiple_access_types(self):
        """Test PermissionCache with multiple access types."""
        cache = PermissionCache()
        path = Path("/test/path")
        
        cache.add_allowed(path, {AccessType.READ, AccessType.WRITE})
        
        assert cache.is_allowed(path, AccessType.READ) is True
        assert cache.is_allowed(path, AccessType.WRITE) is True
        assert cache.is_allowed(path, AccessType.DELETE) is None


@pytest.mark.unit
class TestFileSandbox:
    """Tests for FileSandbox class."""

    def test_sandbox_creation(self, tmp_path):
        """Test FileSandbox instantiation."""
        sandbox = FileSandbox(allowed_roots=[tmp_path])
        assert len(sandbox.allowed_roots) == 1
        assert sandbox.strict_mode is True
        assert len(sandbox.allow_rules) == 1

    def test_sandbox_with_multiple_roots(self, tmp_path):
        """Test FileSandbox with multiple allowed roots."""
        root1 = tmp_path / "root1"
        root2 = tmp_path / "root2"
        root1.mkdir()
        root2.mkdir()
        
        sandbox = FileSandbox(allowed_roots=[root1, root2])
        assert len(sandbox.allowed_roots) == 2
        assert len(sandbox.allow_rules) == 2

    def test_is_path_allowed_for_root(self, tmp_path):
        """Test FileSandbox.is_path_allowed for allowed root."""
        sandbox = FileSandbox(allowed_roots=[tmp_path])
        
        assert sandbox.is_path_allowed(tmp_path, AccessType.READ) is True
        
        # File within root
        file_path = tmp_path / "test.txt"
        file_path.touch()
        assert sandbox.is_path_allowed(file_path, AccessType.READ) is True

    def test_is_path_allowed_for_external_path(self, tmp_path):
        """Test FileSandbox.is_path_allowed for external path."""
        sandbox = FileSandbox(allowed_roots=[tmp_path], strict_mode=True)
        
        external_path = Path("/external/path")
        assert sandbox.is_path_allowed(external_path, AccessType.READ) is False

    def test_is_path_allowed_with_permission_callback(self, tmp_path):
        """Test FileSandbox.is_path_allowed with permission callback."""
        def callback(request):
            return AccessDecision.ALLOW
        
        sandbox = FileSandbox(
            allowed_roots=[tmp_path],
            permission_callback=callback,
            strict_mode=True
        )
        
        external_path = Path("/external/path")
        assert sandbox.is_path_allowed(external_path, AccessType.READ) is True

    def test_is_path_allowed_with_deny_callback(self, tmp_path):
        """Test FileSandbox.is_path_allowed with deny callback."""
        def callback(request):
            return AccessDecision.DENY
        
        sandbox = FileSandbox(
            allowed_roots=[tmp_path],
            permission_callback=callback,
            strict_mode=True
        )
        
        external_path = Path("/external/path")
        assert sandbox.is_path_allowed(external_path, AccessType.READ) is False

    def test_is_path_allowed_non_strict_mode(self, tmp_path):
        """Test FileSandbox.is_path_allowed in non-strict mode."""
        sandbox = FileSandbox(allowed_roots=[tmp_path], strict_mode=False)
        
        external_path = Path("/external/path")
        assert sandbox.is_path_allowed(external_path, AccessType.READ) is True

    def test_add_allowed_path(self, tmp_path):
        """Test FileSandbox.add_allowed_path method."""
        sandbox = FileSandbox(allowed_roots=[tmp_path])
        
        additional_path = tmp_path / "additional"
        additional_path.mkdir()
        sandbox.add_allowed_path(additional_path)
        
        assert sandbox.is_path_allowed(additional_path, AccessType.READ) is True

    def test_check_path_allowed(self, tmp_path):
        """Test FileSandbox.check_path for allowed path."""
        sandbox = FileSandbox(allowed_roots=[tmp_path])
        
        is_allowed, reason = sandbox.check_path(tmp_path, AccessType.READ)
        assert is_allowed is True
        assert reason is None

    def test_check_path_denied(self, tmp_path):
        """Test FileSandbox.check_path for denied path."""
        sandbox = FileSandbox(allowed_roots=[tmp_path], strict_mode=True)
        
        external_path = Path("/external/path")
        is_allowed, reason = sandbox.check_path(external_path, AccessType.READ)
        assert is_allowed is False
        assert reason is not None

    def test_access_log(self, tmp_path):
        """Test FileSandbox logs access attempts."""
        sandbox = FileSandbox(allowed_roots=[tmp_path])
        
        sandbox.is_path_allowed(tmp_path, AccessType.READ)
        
        assert len(sandbox.access_log) == 1
        assert sandbox.access_log[0]["path"] == str(tmp_path.resolve())

    def test_allow_once_decision(self, tmp_path):
        """Test FileSandbox with ALLOW_ONCE decision."""
        def callback(request):
            return AccessDecision.ALLOW_ONCE
        
        sandbox = FileSandbox(
            allowed_roots=[tmp_path],
            permission_callback=callback,
            strict_mode=True
        )
        
        external_path = Path("/external/path")
        # First request should be allowed
        assert sandbox.is_path_allowed(external_path, AccessType.READ) is True
        # Second request should be denied (not cached)
        # Note: ALLOW_ONCE doesn't cache, so it will ask again
        # but since callback still returns ALLOW_ONCE, it will be allowed
        assert sandbox.is_path_allowed(external_path, AccessType.READ) is True

    def test_deny_once_decision(self, tmp_path):
        """Test FileSandbox with DENY_ONCE decision."""
        def callback(request):
            return AccessDecision.DENY_ONCE
        
        sandbox = FileSandbox(
            allowed_roots=[tmp_path],
            permission_callback=callback,
            strict_mode=True
        )
        
        external_path = Path("/external/path")
        assert sandbox.is_path_allowed(external_path, AccessType.READ) is False
