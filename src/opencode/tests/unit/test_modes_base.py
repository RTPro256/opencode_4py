"""
Tests for core/modes/base.py

Tests for ModeToolAccess enum, ModeConfig dataclass, and Mode abstract base class.
"""

import pytest
from unittest.mock import patch
from typing import Set

from opencode.core.modes.base import (
    ModeToolAccess,
    ModeConfig,
    Mode,
)


class TestModeToolAccess:
    """Tests for ModeToolAccess enum."""

    def test_all_value(self):
        """Test ALL enum value."""
        assert ModeToolAccess.ALL.value == "all"

    def test_whitelist_value(self):
        """Test WHITELIST enum value."""
        assert ModeToolAccess.WHITELIST.value == "whitelist"

    def test_blacklist_value(self):
        """Test BLACKLIST enum value."""
        assert ModeToolAccess.BLACKLIST.value == "blacklist"

    def test_none_value(self):
        """Test NONE enum value."""
        assert ModeToolAccess.NONE.value == "none"

    def test_is_string_enum(self):
        """Test that ModeToolAccess is a string enum."""
        assert ModeToolAccess.ALL == "all"
        assert isinstance(ModeToolAccess.ALL, str)


class TestModeConfig:
    """Tests for ModeConfig dataclass."""

    def test_default_values(self):
        """Test ModeConfig with only required name."""
        config = ModeConfig(name="test_mode")
        
        assert config.name == "test_mode"
        assert config.description == ""
        assert config.tool_access == ModeToolAccess.ALL
        assert config.allowed_tools == set()
        assert config.blocked_tools == set()
        assert config.system_prompt_prefix == ""
        assert config.system_prompt_suffix == ""
        assert config.custom_instructions == ""
        assert config.max_tokens is None
        assert config.temperature is None
        assert config.supports_images is True
        assert config.supports_streaming is True

    def test_custom_values(self):
        """Test ModeConfig with custom values."""
        config = ModeConfig(
            name="custom_mode",
            description="A custom mode",
            tool_access=ModeToolAccess.WHITELIST,
            allowed_tools={"tool1", "tool2"},
            blocked_tools={"tool3"},
            system_prompt_prefix="Prefix",
            system_prompt_suffix="Suffix",
            custom_instructions="Instructions",
            max_tokens=1000,
            temperature=0.5,
            supports_images=False,
            supports_streaming=False,
        )
        
        assert config.name == "custom_mode"
        assert config.description == "A custom mode"
        assert config.tool_access == ModeToolAccess.WHITELIST
        assert config.allowed_tools == {"tool1", "tool2"}
        assert config.blocked_tools == {"tool3"}
        assert config.system_prompt_prefix == "Prefix"
        assert config.system_prompt_suffix == "Suffix"
        assert config.custom_instructions == "Instructions"
        assert config.max_tokens == 1000
        assert config.temperature == 0.5
        assert config.supports_images is False
        assert config.supports_streaming is False

    def test_to_dict(self):
        """Test ModeConfig.to_dict()."""
        config = ModeConfig(
            name="test_mode",
            description="Test description",
            tool_access=ModeToolAccess.BLACKLIST,
            allowed_tools={"tool1"},
            blocked_tools={"tool2"},
            system_prompt_prefix="Prefix",
            system_prompt_suffix="Suffix",
            custom_instructions="Instructions",
            max_tokens=500,
            temperature=0.7,
            supports_images=True,
            supports_streaming=False,
        )
        
        result = config.to_dict()
        
        assert result["name"] == "test_mode"
        assert result["description"] == "Test description"
        assert result["tool_access"] == "blacklist"
        assert set(result["allowed_tools"]) == {"tool1"}
        assert set(result["blocked_tools"]) == {"tool2"}
        assert result["system_prompt_prefix"] == "Prefix"
        assert result["system_prompt_suffix"] == "Suffix"
        assert result["custom_instructions"] == "Instructions"
        assert result["max_tokens"] == 500
        assert result["temperature"] == 0.7
        assert result["supports_images"] is True
        assert result["supports_streaming"] is False

    def test_to_dict_with_empty_sets(self):
        """Test to_dict with empty tool sets."""
        config = ModeConfig(name="test")
        result = config.to_dict()
        
        assert result["allowed_tools"] == []
        assert result["blocked_tools"] == []

    def test_from_dict_minimal(self):
        """Test ModeConfig.from_dict() with minimal data."""
        data = {"name": "test_mode"}
        config = ModeConfig.from_dict(data)
        
        assert config.name == "test_mode"
        assert config.description == ""
        assert config.tool_access == ModeToolAccess.ALL
        assert config.allowed_tools == set()
        assert config.blocked_tools == set()
        assert config.supports_images is True
        assert config.supports_streaming is True

    def test_from_dict_complete(self):
        """Test ModeConfig.from_dict() with all fields."""
        data = {
            "name": "full_mode",
            "description": "Full description",
            "tool_access": "whitelist",
            "allowed_tools": ["tool1", "tool2"],
            "blocked_tools": ["tool3"],
            "system_prompt_prefix": "Prefix",
            "system_prompt_suffix": "Suffix",
            "custom_instructions": "Instructions",
            "max_tokens": 2000,
            "temperature": 0.3,
            "supports_images": False,
            "supports_streaming": False,
        }
        
        config = ModeConfig.from_dict(data)
        
        assert config.name == "full_mode"
        assert config.description == "Full description"
        assert config.tool_access == ModeToolAccess.WHITELIST
        assert config.allowed_tools == {"tool1", "tool2"}
        assert config.blocked_tools == {"tool3"}
        assert config.system_prompt_prefix == "Prefix"
        assert config.system_prompt_suffix == "Suffix"
        assert config.custom_instructions == "Instructions"
        assert config.max_tokens == 2000
        assert config.temperature == 0.3
        assert config.supports_images is False
        assert config.supports_streaming is False

    def test_from_dict_with_none_values(self):
        """Test from_dict with None for optional values."""
        data = {
            "name": "test",
            "max_tokens": None,
            "temperature": None,
        }
        config = ModeConfig.from_dict(data)
        
        assert config.max_tokens is None
        assert config.temperature is None

    def test_round_trip(self):
        """Test that to_dict and from_dict are inverses."""
        original = ModeConfig(
            name="round_trip",
            description="Test round trip",
            tool_access=ModeToolAccess.BLACKLIST,
            allowed_tools={"a", "b"},
            blocked_tools={"c"},
            system_prompt_prefix="Pre",
            system_prompt_suffix="Suf",
            custom_instructions="Custom",
            max_tokens=100,
            temperature=0.9,
            supports_images=True,
            supports_streaming=True,
        )
        
        data = original.to_dict()
        restored = ModeConfig.from_dict(data)
        
        assert restored.name == original.name
        assert restored.description == original.description
        assert restored.tool_access == original.tool_access
        assert restored.allowed_tools == original.allowed_tools
        assert restored.blocked_tools == original.blocked_tools
        assert restored.system_prompt_prefix == original.system_prompt_prefix
        assert restored.system_prompt_suffix == original.system_prompt_suffix
        assert restored.custom_instructions == original.custom_instructions
        assert restored.max_tokens == original.max_tokens
        assert restored.temperature == original.temperature
        assert restored.supports_images == original.supports_images
        assert restored.supports_streaming == original.supports_streaming


# Concrete implementation of Mode for testing
class ConcreteMode(Mode):
    """Concrete implementation of Mode for testing."""
    
    _config = ModeConfig(
        name="concrete",
        description="A concrete mode for testing",
        tool_access=ModeToolAccess.ALL,
    )
    
    @classmethod
    def get_config(cls) -> ModeConfig:
        return cls._config


class WhitelistMode(Mode):
    """Mode with whitelist tool access."""
    
    _config = ModeConfig(
        name="whitelist_mode",
        description="Whitelist mode",
        tool_access=ModeToolAccess.WHITELIST,
        allowed_tools={"allowed_tool1", "allowed_tool2"},
    )
    
    @classmethod
    def get_config(cls) -> ModeConfig:
        return cls._config


class BlacklistMode(Mode):
    """Mode with blacklist tool access."""
    
    _config = ModeConfig(
        name="blacklist_mode",
        description="Blacklist mode",
        tool_access=ModeToolAccess.BLACKLIST,
        blocked_tools={"blocked_tool1", "blocked_tool2"},
    )
    
    @classmethod
    def get_config(cls) -> ModeConfig:
        return cls._config


class NoneMode(Mode):
    """Mode with no tool access."""
    
    _config = ModeConfig(
        name="none_mode",
        description="No tools mode",
        tool_access=ModeToolAccess.NONE,
    )
    
    @classmethod
    def get_config(cls) -> ModeConfig:
        return cls._config


class PromptMode(Mode):
    """Mode with custom prompts."""
    
    _config = ModeConfig(
        name="prompt_mode",
        description="Mode with prompts",
        system_prompt_prefix="You are a helpful assistant.",
        system_prompt_suffix="Be concise.",
        custom_instructions="Always be polite.",
    )
    
    @classmethod
    def get_config(cls) -> ModeConfig:
        return cls._config


class SettingsMode(Mode):
    """Mode with custom model settings."""
    
    _config = ModeConfig(
        name="settings_mode",
        description="Mode with settings",
        max_tokens=1000,
        temperature=0.5,
    )
    
    @classmethod
    def get_config(cls) -> ModeConfig:
        return cls._config


class TestMode:
    """Tests for Mode abstract base class."""

    def test_get_name(self):
        """Test Mode.get_name()."""
        assert ConcreteMode.get_name() == "concrete"

    def test_get_description(self):
        """Test Mode.get_description()."""
        assert ConcreteMode.get_description() == "A concrete mode for testing"

    def test_get_system_prompt_empty(self):
        """Test get_system_prompt with no base prompt."""
        result = ConcreteMode.get_system_prompt()
        assert result == ""

    def test_get_system_prompt_with_base(self):
        """Test get_system_prompt with base prompt."""
        result = ConcreteMode.get_system_prompt(base_prompt="Base prompt")
        assert result == "Base prompt"

    def test_get_system_prompt_with_prefix(self):
        """Test get_system_prompt with prefix."""
        result = PromptMode.get_system_prompt()
        assert "You are a helpful assistant." in result

    def test_get_system_prompt_with_suffix(self):
        """Test get_system_prompt with suffix."""
        result = PromptMode.get_system_prompt()
        assert "Be concise." in result

    def test_get_system_prompt_with_custom_instructions(self):
        """Test get_system_prompt with custom instructions."""
        result = PromptMode.get_system_prompt()
        assert "Always be polite." in result

    def test_get_system_prompt_all_parts(self):
        """Test get_system_prompt with all parts."""
        result = PromptMode.get_system_prompt(base_prompt="Base content")
        
        assert "You are a helpful assistant." in result
        assert "Base content" in result
        assert "Always be polite." in result
        assert "Be concise." in result

    def test_get_system_prompt_order(self):
        """Test that system prompt parts are in correct order."""
        result = PromptMode.get_system_prompt(base_prompt="Base")
        
        prefix_idx = result.find("You are a helpful assistant.")
        base_idx = result.find("Base")
        instructions_idx = result.find("Always be polite.")
        suffix_idx = result.find("Be concise.")
        
        assert prefix_idx < base_idx
        assert base_idx < instructions_idx
        assert instructions_idx < suffix_idx

    def test_filter_tools_all_access(self):
        """Test filter_tools with ALL access."""
        tools = {"tool1", "tool2", "tool3"}
        result = ConcreteMode.filter_tools(tools)
        assert result == tools

    def test_filter_tools_none_access(self):
        """Test filter_tools with NONE access."""
        tools = {"tool1", "tool2", "tool3"}
        result = NoneMode.filter_tools(tools)
        assert result == set()

    def test_filter_tools_whitelist_access(self):
        """Test filter_tools with WHITELIST access."""
        tools = {"allowed_tool1", "allowed_tool2", "other_tool"}
        result = WhitelistMode.filter_tools(tools)
        assert result == {"allowed_tool1", "allowed_tool2"}

    def test_filter_tools_whitelist_no_match(self):
        """Test filter_tools with WHITELIST when no tools match."""
        tools = {"other_tool1", "other_tool2"}
        result = WhitelistMode.filter_tools(tools)
        assert result == set()

    def test_filter_tools_blacklist_access(self):
        """Test filter_tools with BLACKLIST access."""
        tools = {"blocked_tool1", "blocked_tool2", "allowed_tool"}
        result = BlacklistMode.filter_tools(tools)
        assert result == {"allowed_tool"}

    def test_filter_tools_blacklist_all_blocked(self):
        """Test filter_tools with BLACKLIST when all tools are blocked."""
        tools = {"blocked_tool1", "blocked_tool2"}
        result = BlacklistMode.filter_tools(tools)
        assert result == set()

    def test_is_tool_allowed_all_access(self):
        """Test is_tool_allowed with ALL access."""
        assert ConcreteMode.is_tool_allowed("any_tool") is True

    def test_is_tool_allowed_none_access(self):
        """Test is_tool_allowed with NONE access."""
        assert NoneMode.is_tool_allowed("any_tool") is False

    def test_is_tool_allowed_whitelist_in_list(self):
        """Test is_tool_allowed with WHITELIST and tool in list."""
        assert WhitelistMode.is_tool_allowed("allowed_tool1") is True

    def test_is_tool_allowed_whitelist_not_in_list(self):
        """Test is_tool_allowed with WHITELIST and tool not in list."""
        assert WhitelistMode.is_tool_allowed("other_tool") is False

    def test_is_tool_allowed_blacklist_in_list(self):
        """Test is_tool_allowed with BLACKLIST and tool in list."""
        assert BlacklistMode.is_tool_allowed("blocked_tool1") is False

    def test_is_tool_allowed_blacklist_not_in_list(self):
        """Test is_tool_allowed with BLACKLIST and tool not in list."""
        assert BlacklistMode.is_tool_allowed("other_tool") is True

    def test_get_model_settings_empty(self):
        """Test get_model_settings with no custom settings."""
        result = ConcreteMode.get_model_settings()
        assert result == {}

    def test_get_model_settings_with_values(self):
        """Test get_model_settings with custom settings."""
        result = SettingsMode.get_model_settings()
        assert result == {"max_tokens": 1000, "temperature": 0.5}

    def test_get_model_settings_only_max_tokens(self):
        """Test get_model_settings with only max_tokens."""
        class MaxTokensMode(Mode):
            _config = ModeConfig(name="max_tokens", max_tokens=500)
            
            @classmethod
            def get_config(cls) -> ModeConfig:
                return cls._config
        
        result = MaxTokensMode.get_model_settings()
        assert result == {"max_tokens": 500}

    def test_get_model_settings_only_temperature(self):
        """Test get_model_settings with only temperature."""
        class TemperatureMode(Mode):
            _config = ModeConfig(name="temp", temperature=0.7)
            
            @classmethod
            def get_config(cls) -> ModeConfig:
                return cls._config
        
        result = TemperatureMode.get_model_settings()
        assert result == {"temperature": 0.7}

    def test_repr(self):
        """Test __repr__ method."""
        mode = ConcreteMode()
        assert repr(mode) == "ConcreteMode()"

    def test_repr_subclass(self):
        """Test __repr__ for subclass."""
        mode = WhitelistMode()
        assert repr(mode) == "WhitelistMode()"


class TestModeIntegration:
    """Integration tests for Mode classes."""

    def test_full_workflow(self):
        """Test a complete workflow with a mode."""
        # Create a mode with all features
        class FullMode(Mode):
            _config = ModeConfig(
                name="full",
                description="Full featured mode",
                tool_access=ModeToolAccess.WHITELIST,
                allowed_tools={"read", "write"},
                system_prompt_prefix="You are helpful.",
                custom_instructions="Be accurate.",
                system_prompt_suffix="Good luck!",
                max_tokens=2000,
                temperature=0.3,
            )
            
            @classmethod
            def get_config(cls) -> ModeConfig:
                return cls._config
        
        # Test all methods
        assert FullMode.get_name() == "full"
        assert FullMode.get_description() == "Full featured mode"
        
        prompt = FullMode.get_system_prompt(base_prompt="Help the user.")
        assert "You are helpful." in prompt
        assert "Help the user." in prompt
        assert "Be accurate." in prompt
        assert "Good luck!" in prompt
        
        tools = {"read", "write", "delete", "execute"}
        filtered = FullMode.filter_tools(tools)
        assert filtered == {"read", "write"}
        
        assert FullMode.is_tool_allowed("read") is True
        assert FullMode.is_tool_allowed("delete") is False
        
        settings = FullMode.get_model_settings()
        assert settings == {"max_tokens": 2000, "temperature": 0.3}

    def test_mode_config_serialization_workflow(self):
        """Test workflow of serializing and deserializing mode configs."""
        # Create config
        original = ModeConfig(
            name="workflow_test",
            description="Test workflow",
            tool_access=ModeToolAccess.BLACKLIST,
            allowed_tools={"a"},
            blocked_tools={"b", "c"},
            max_tokens=500,
        )
        
        # Serialize
        data = original.to_dict()
        
        # Modify data (simulating storage/transmission)
        data["description"] = "Modified description"
        
        # Deserialize
        restored = ModeConfig.from_dict(data)
        
        assert restored.name == "workflow_test"
        assert restored.description == "Modified description"
        assert restored.tool_access == ModeToolAccess.BLACKLIST
        assert restored.max_tokens == 500
