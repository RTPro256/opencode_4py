"""
Tests for Mode Manager.
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile
import os

# Import modes to register them
from opencode.core.modes.modes import CodeMode, AskMode, ArchitectMode, DebugMode

from opencode.core.modes.manager import ModeManager
from opencode.core.modes.base import ModeConfig, ModeToolAccess


class TestModeManager:
    """Tests for ModeManager class."""

    def test_init_default_mode(self):
        """Test initialization with default mode."""
        manager = ModeManager()
        assert manager.get_current_mode_name() == "code"

    def test_init_custom_default_mode(self):
        """Test initialization with custom default mode."""
        manager = ModeManager(default_mode="ask")
        assert manager.get_current_mode_name() == "ask"

    def test_get_current_mode(self):
        """Test getting current mode class."""
        manager = ModeManager(default_mode="code")
        mode_class = manager.get_current_mode()
        assert mode_class is not None
        assert hasattr(mode_class, "get_config")

    def test_get_current_config(self):
        """Test getting current mode configuration."""
        manager = ModeManager(default_mode="code")
        config = manager.get_current_config()
        assert config is not None
        assert hasattr(config, "name")

    def test_set_mode_valid(self):
        """Test setting a valid mode."""
        manager = ModeManager(default_mode="code")
        result = manager.set_mode("ask")
        assert result is True
        assert manager.get_current_mode_name() == "ask"

    def test_set_mode_invalid(self):
        """Test setting an invalid mode."""
        manager = ModeManager(default_mode="code")
        result = manager.set_mode("nonexistent_mode")
        assert result is False
        assert manager.get_current_mode_name() == "code"

    def test_mode_history(self):
        """Test mode history tracking."""
        manager = ModeManager(default_mode="code")
        
        # Switch modes
        manager.set_mode("ask")
        manager.set_mode("architect")
        
        # Check history
        assert manager.get_previous_mode() == "ask"

    def test_restore_previous_mode(self):
        """Test restoring previous mode."""
        manager = ModeManager(default_mode="code")
        
        manager.set_mode("ask")
        manager.set_mode("architect")
        
        # Restore previous
        result = manager.restore_previous_mode()
        assert result is True
        assert manager.get_current_mode_name() == "ask"

    def test_restore_previous_mode_no_history(self):
        """Test restoring when there's no history."""
        manager = ModeManager(default_mode="code")
        
        result = manager.restore_previous_mode()
        assert result is False
        assert manager.get_current_mode_name() == "code"

    def test_mode_history_limit(self):
        """Test that mode history is limited to 10 entries."""
        manager = ModeManager(default_mode="code")
        
        # Switch modes 15 times
        modes = ["ask", "architect", "debug", "code", "ask",
                 "architect", "debug", "code", "ask", "architect",
                 "debug", "code", "ask", "architect", "debug"]
        
        for mode in modes:
            manager.set_mode(mode)
        
        # History should be limited
        assert len(manager._mode_history) <= 10

    def test_list_modes(self):
        """Test listing available modes."""
        manager = ModeManager()
        modes = manager.list_modes()
        
        assert isinstance(modes, list)
        assert len(modes) > 0
        # Should include builtin modes
        assert "code" in modes or "ask" in modes

    def test_get_mode_config(self):
        """Test getting configuration for a specific mode."""
        manager = ModeManager()
        config = manager.get_mode_config("code")
        
        assert config is not None
        assert hasattr(config, "name")

    def test_get_mode_config_invalid(self):
        """Test getting configuration for invalid mode."""
        manager = ModeManager()
        config = manager.get_mode_config("nonexistent_mode")
        
        assert config is None

    def test_is_tool_allowed(self):
        """Test checking if a tool is allowed."""
        manager = ModeManager(default_mode="code")
        
        # Most tools should be allowed in code mode
        result = manager.is_tool_allowed("read_file")
        assert isinstance(result, bool)

    def test_is_tool_allowed_specific_mode(self):
        """Test checking tool permission for a specific mode."""
        manager = ModeManager()
        
        result = manager.is_tool_allowed("read_file", mode_name="code")
        assert isinstance(result, bool)

    def test_filter_tools(self):
        """Test filtering tools based on mode."""
        manager = ModeManager(default_mode="code")
        
        tools = {"read_file", "write_file", "bash"}
        filtered = manager.filter_tools(tools)
        
        assert isinstance(filtered, set)

    def test_filter_tools_specific_mode(self):
        """Test filtering tools for a specific mode."""
        manager = ModeManager()
        
        tools = {"read_file", "write_file", "bash"}
        filtered = manager.filter_tools(tools, mode_name="ask")
        
        assert isinstance(filtered, set)

    def test_create_custom_mode(self):
        """Test creating a custom mode."""
        manager = ModeManager()
        
        config = ModeConfig(
            name="test_custom",
            description="Test custom mode",
            tool_access=ModeToolAccess.ALL,
            allowed_tools=set(),
            blocked_tools=set(),
        )
        
        mode_class = manager.create_custom_mode("test_custom", config)
        
        assert mode_class is not None
        assert "test_custom" in manager.list_modes()

    def test_create_custom_mode_with_save(self):
        """Test creating and saving a custom mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ModeManager(custom_modes_dir=Path(tmpdir))
            
            config = ModeConfig(
                name="saveable_mode",
                description="A mode that can be saved",
                tool_access=ModeToolAccess.ALL,
                allowed_tools=set(),
                blocked_tools=set(),
            )
            
            mode_class = manager.create_custom_mode("saveable_mode", config, save=True)
            
            assert mode_class is not None
            # Check file was created
            expected_file = Path(tmpdir) / "saveable_mode.yaml"
            assert expected_file.exists()


class TestModeManagerCustomModes:
    """Tests for custom mode loading."""

    def test_load_custom_modes_from_directory(self):
        """Test loading custom modes from a directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a custom mode YAML file
            yaml_content = """
name: custom_test
description: A custom test mode
tool_access: all
allowed_tools: []
blocked_tools: []
system_prompt_prefix: "You are a test assistant."
"""
            yaml_path = Path(tmpdir) / "custom_test.yaml"
            yaml_path.write_text(yaml_content)
            
            manager = ModeManager(custom_modes_dir=Path(tmpdir))
            
            # Check custom mode was loaded
            assert "custom_test" in manager.list_modes()

    def test_load_custom_modes_yml_extension(self):
        """Test loading custom modes with .yml extension."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_content = """
name: yml_mode
description: A mode with yml extension
tool_access: all
"""
            yaml_path = Path(tmpdir) / "yml_mode.yml"
            yaml_path.write_text(yaml_content)
            
            manager = ModeManager(custom_modes_dir=Path(tmpdir))
            
            assert "yml_mode" in manager.list_modes()

    def test_load_custom_modes_invalid_yaml(self):
        """Test handling invalid YAML files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create invalid YAML
            yaml_path = Path(tmpdir) / "invalid.yaml"
            yaml_path.write_text("this is not: valid: yaml: :::")
            
            # Should not raise exception
            manager = ModeManager(custom_modes_dir=Path(tmpdir))
            
            # Should still have default modes
            assert len(manager.list_modes()) > 0

    def test_load_custom_modes_missing_name(self):
        """Test handling YAML without required name field."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_content = """
description: A mode without a name
tool_access: all
"""
            yaml_path = Path(tmpdir) / "no_name.yaml"
            yaml_path.write_text(yaml_content)
            
            # Should not raise exception
            manager = ModeManager(custom_modes_dir=Path(tmpdir))
            
            # Mode should not be loaded
            assert "no_name" not in manager.list_modes()

    def test_load_custom_modes_nonexistent_directory(self):
        """Test handling nonexistent custom modes directory."""
        manager = ModeManager(custom_modes_dir=Path("/nonexistent/path"))
        
        # Should still work with default modes
        assert len(manager.list_modes()) > 0

    def test_custom_mode_full_config(self):
        """Test loading custom mode with full configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_content = """
name: full_config_mode
description: A mode with full configuration
tool_access: all
allowed_tools:
  - read_file
  - write_file
blocked_tools:
  - bash
system_prompt_prefix: "Prefix text"
system_prompt_suffix: "Suffix text"
custom_instructions: "Custom instructions here"
max_tokens: 4096
temperature: 0.7
supports_images: false
supports_streaming: true
"""
            yaml_path = Path(tmpdir) / "full_config.yaml"
            yaml_path.write_text(yaml_content)
            
            manager = ModeManager(custom_modes_dir=Path(tmpdir))
            
            config = manager.get_mode_config("full_config_mode")
            assert config is not None
            assert config.description == "A mode with full configuration"
            assert config.max_tokens == 4096
            assert config.temperature == 0.7
            assert config.supports_images is False


class TestModeManagerEdgeCases:
    """Edge case tests for ModeManager."""

    def test_multiple_mode_switches(self):
        """Test multiple rapid mode switches."""
        manager = ModeManager(default_mode="code")
        
        modes_to_switch = ["ask", "architect", "debug", "ask", "code"]
        
        for mode in modes_to_switch:
            result = manager.set_mode(mode)
            assert result is True
            assert manager.get_current_mode_name() == mode

    def test_switch_to_same_mode(self):
        """Test switching to the current mode."""
        manager = ModeManager(default_mode="code")
        
        result = manager.set_mode("code")
        assert result is True
        # Should still be in code mode
        assert manager.get_current_mode_name() == "code"

    def test_filter_empty_tools(self):
        """Test filtering an empty tool set."""
        manager = ModeManager()
        
        filtered = manager.filter_tools(set())
        assert filtered == set()

    def test_is_tool_allowed_unknown_mode(self):
        """Test tool check with unknown mode."""
        manager = ModeManager()
        
        # Should return True (default) for unknown mode
        result = manager.is_tool_allowed("read_file", mode_name="unknown_mode")
        assert result is True

    def test_filter_tools_unknown_mode(self):
        """Test filtering tools with unknown mode."""
        manager = ModeManager()
        
        tools = {"read_file", "write_file"}
        filtered = manager.filter_tools(tools, mode_name="unknown_mode")
        
        # Should return original tools for unknown mode
        assert filtered == tools
