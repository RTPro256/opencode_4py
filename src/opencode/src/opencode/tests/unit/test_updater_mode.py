"""
Tests for Updater Mode

Tests verify that:
1. UpdaterMode is properly registered
2. System prompt references README.md and MISSION.md
3. Mode has correct tool access
"""

import pytest
from opencode.core.modes.modes.updater import UpdaterMode
from opencode.core.modes.registry import ModeRegistry


class TestUpdaterMode:
    """Test suite for UpdaterMode."""

    def test_updater_mode_registered(self):
        """Test that UpdaterMode is registered in ModeRegistry."""
        assert "updater" in ModeRegistry._modes, "UpdaterMode should be registered as 'updater'"
        assert ModeRegistry._modes["updater"] == UpdaterMode, "Registered mode should be UpdaterMode class"

    def test_updater_mode_config(self):
        """Test that UpdaterMode has correct configuration."""
        config = UpdaterMode.get_config()
        
        assert config.name == "updater", "Mode name should be 'updater'"
        assert "update" in config.description.lower(), "Description should mention update"
        assert "for_testing" in config.description.lower(), "Description should mention for_testing"

    def test_system_prompt_references_readme(self):
        """Test that system prompt references README.md."""
        config = UpdaterMode.get_config()
        
        assert "README.md" in config.system_prompt_prefix, (
            "System prompt prefix should reference README.md"
        )

    def test_system_prompt_references_mission(self):
        """Test that system prompt references MISSION.md."""
        config = UpdaterMode.get_config()
        
        assert "MISSION.md" in config.system_prompt_prefix, (
            "System prompt prefix should reference MISSION.md"
        )

    def test_system_prompt_mentions_opencode_project(self):
        """Test that system prompt mentions OpenCode Python project."""
        config = UpdaterMode.get_config()
        
        assert "OpenCode Python project" in config.system_prompt_prefix, (
            "System prompt should mention 'OpenCode Python project'"
        )

    def test_tool_access_whitelist(self):
        """Test that UpdaterMode uses whitelist tool access."""
        from opencode.core.modes.base import ModeToolAccess
        
        config = UpdaterMode.get_config()
        
        assert config.tool_access == ModeToolAccess.WHITELIST, (
            "UpdaterMode should use whitelist tool access"
        )

    def test_has_required_tools(self):
        """Test that UpdaterMode has required tools."""
        config = UpdaterMode.get_config()
        
        required_tools = {
            "read_file",
            "execute_command",
            "write_file",
            "edit_file",
        }
        
        for tool in required_tools:
            assert tool in config.allowed_tools, (
                f"UpdaterMode should have access to '{tool}' tool"
            )

    def test_suffix_mentions_update_plan(self):
        """Test that system prompt suffix mentions the update plan."""
        config = UpdaterMode.get_config()
        
        assert "UPDATE_OPENCODE_PLAN.md" in config.system_prompt_suffix, (
            "System prompt suffix should reference UPDATE_OPENCODE_PLAN.md"
        )

    def test_supports_streaming(self):
        """Test that UpdaterMode supports streaming."""
        config = UpdaterMode.get_config()
        
        assert config.supports_streaming is True, (
            "UpdaterMode should support streaming"
        )

    def test_does_not_support_images(self):
        """Test that UpdaterMode does not support images."""
        config = UpdaterMode.get_config()
        
        assert config.supports_images is False, (
            "UpdaterMode should not support images (not needed for updates)"
        )


class TestUpdaterModeIntegration:
    """Integration tests for UpdaterMode."""

    def test_get_mode_from_registry(self):
        """Test getting UpdaterMode from registry."""
        mode_class = ModeRegistry.get("updater")
        
        assert mode_class == UpdaterMode, (
            "Registry should return UpdaterMode class for 'updater'"
        )

    def test_all_modes_have_readme_mission_references(self):
        """Test that all registered modes reference README.md and MISSION.md."""
        for mode_name, mode_class in ModeRegistry._modes.items():
            config = mode_class.get_config()
            
            # Check that system prompt prefix contains the required references
            assert "README.md" in config.system_prompt_prefix, (
                f"Mode '{mode_name}' should reference README.md in system_prompt_prefix"
            )
            assert "MISSION.md" in config.system_prompt_prefix, (
                f"Mode '{mode_name}' should reference MISSION.md in system_prompt_prefix"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
