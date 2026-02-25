"""
Tests for modes module.
"""

import pytest
from unittest.mock import MagicMock, patch

from opencode.core.modes import base, manager, registry
from opencode.core.modes.modes import architect, ask, code, debug


@pytest.mark.unit
class TestModesBase:
    """Tests for mode base."""
    
    def test_base_module_exists(self):
        """Test base module exists."""
        assert base is not None


@pytest.mark.unit
class TestModesManager:
    """Tests for mode manager."""
    
    def test_manager_module_exists(self):
        """Test manager module exists."""
        assert manager is not None


@pytest.mark.unit
class TestModesRegistry:
    """Tests for mode registry."""
    
    def test_registry_module_exists(self):
        """Test registry module exists."""
        assert registry is not None


@pytest.mark.unit
class TestArchitectMode:
    """Tests for architect mode."""
    
    def test_architect_module_exists(self):
        """Test architect module exists."""
        assert architect is not None


@pytest.mark.unit
class TestAskMode:
    """Tests for ask mode."""
    
    def test_ask_module_exists(self):
        """Test ask module exists."""
        assert ask is not None


@pytest.mark.unit
class TestCodeMode:
    """Tests for code mode."""
    
    def test_code_module_exists(self):
        """Test code module exists."""
        assert code is not None


@pytest.mark.unit
class TestDebugMode:
    """Tests for debug mode."""
    
    def test_debug_module_exists(self):
        """Test debug module exists."""
        assert debug is not None
