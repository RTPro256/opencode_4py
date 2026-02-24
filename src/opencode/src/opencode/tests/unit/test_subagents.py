"""
Unit tests for subagents functionality.

Tests for SubagentConfig, SubagentManager, and related subagent components.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from opencode.core.subagents.types import (
    SubagentConfig,
    SubagentLevel,
    SubagentErrorCode,
    SubagentTerminateMode,
    PromptConfig,
    ModelConfig,
    ToolConfig,
    RunConfig,
    SubagentRuntimeConfig,
    ValidationResult,
)


class TestPromptConfig:
    """Tests for PromptConfig."""
    
    def test_default_config(self):
        """Test default prompt configuration."""
        config = PromptConfig()
        
        assert config.system is None
        assert config.user_prefix is None
        assert config.user_suffix is None
        assert config.include_context is True
    
    def test_custom_config(self):
        """Test custom prompt configuration."""
        config = PromptConfig(
            system="You are a code reviewer.",
            user_prefix="[REVIEW] ",
            user_suffix="\n\nPlease review.",
            include_context=False,
        )
        
        assert config.system == "You are a code reviewer."
        assert config.user_prefix == "[REVIEW] "
        assert config.user_suffix == "\n\nPlease review."
        assert config.include_context is False
    
    def test_model_validation(self):
        """Test Pydantic model validation."""
        config = PromptConfig(system="Test system prompt")
        
        # Should serialize properly
        data = config.model_dump()
        assert data["system"] == "Test system prompt"


class TestModelConfig:
    """Tests for ModelConfig."""
    
    def test_default_config(self):
        """Test default model configuration."""
        config = ModelConfig()
        
        assert config.provider is None
        assert config.name is None
        assert config.temperature is None
        assert config.max_tokens is None
    
    def test_custom_config(self):
        """Test custom model configuration."""
        config = ModelConfig(
            provider="openai",
            name="gpt-4",
            temperature=0.7,
            max_tokens=4096,
        )
        
        assert config.provider == "openai"
        assert config.name == "gpt-4"
        assert config.temperature == 0.7
        assert config.max_tokens == 4096
    
    def test_temperature_validation(self):
        """Test temperature range validation."""
        # Valid temperatures
        config = ModelConfig(temperature=0.0)
        assert config.temperature == 0.0
        
        config = ModelConfig(temperature=2.0)
        assert config.temperature == 2.0
        
        # Invalid temperatures should raise validation error
        with pytest.raises(Exception):  # Pydantic ValidationError
            ModelConfig(temperature=-0.1)
        
        with pytest.raises(Exception):
            ModelConfig(temperature=2.1)
    
    def test_max_tokens_validation(self):
        """Test max_tokens validation."""
        config = ModelConfig(max_tokens=100)
        assert config.max_tokens == 100
        
        # Invalid max_tokens
        with pytest.raises(Exception):
            ModelConfig(max_tokens=0)


class TestToolConfig:
    """Tests for ToolConfig."""
    
    def test_default_config(self):
        """Test default tool configuration."""
        config = ToolConfig()
        
        assert config.allow == []
        assert config.deny == []
        assert config.require_approval == []
        assert config.auto_approve == []
    
    def test_custom_config(self):
        """Test custom tool configuration."""
        config = ToolConfig(
            allow=["file_read", "file_write"],
            deny=["bash"],
            require_approval=["file_write"],
            auto_approve=["file_read"],
        )
        
        assert "file_read" in config.allow
        assert "bash" in config.deny
        assert "file_write" in config.require_approval
        assert "file_read" in config.auto_approve
    
    def test_wildcard_allow(self):
        """Test wildcard allow configuration."""
        config = ToolConfig(allow=["*"])
        
        assert "*" in config.allow


class TestRunConfig:
    """Tests for RunConfig."""
    
    def test_default_config(self):
        """Test default run configuration."""
        config = RunConfig()
        
        assert config.max_rounds == 10
        assert config.terminate_mode == SubagentTerminateMode.AUTO
        assert config.timeout is None
        assert config.retry_on_error is False
        assert config.max_retries == 3
    
    def test_custom_config(self):
        """Test custom run configuration."""
        config = RunConfig(
            max_rounds=20,
            terminate_mode=SubagentTerminateMode.MANUAL,
            timeout=300,
            retry_on_error=True,
            max_retries=5,
        )
        
        assert config.max_rounds == 20
        assert config.terminate_mode == SubagentTerminateMode.MANUAL
        assert config.timeout == 300
        assert config.retry_on_error is True
        assert config.max_retries == 5
    
    def test_max_rounds_validation(self):
        """Test max_rounds validation."""
        config = RunConfig(max_rounds=1)
        assert config.max_rounds == 1
        
        with pytest.raises(Exception):
            RunConfig(max_rounds=0)


class TestSubagentConfig:
    """Tests for SubagentConfig."""
    
    def test_minimal_config(self):
        """Test minimal subagent configuration."""
        config = SubagentConfig(
            name="test_agent",
            description="A test agent",
        )
        
        assert config.name == "test_agent"
        assert config.description == "A test agent"
    
    def test_full_config(self):
        """Test full subagent configuration."""
        config = SubagentConfig(
            name="code_reviewer",
            description="Reviews code for quality",
            prompt=PromptConfig(system="You are a code reviewer."),
            model=ModelConfig(provider="anthropic", name="claude-3-opus"),
            tools=ToolConfig(allow=["file_read", "file_write"]),
            run=RunConfig(max_rounds=15),
            tags=["code", "review"],
            version="2.0.0",
            author="Test Author",
            enabled=True,
        )
        
        assert config.name == "code_reviewer"
        assert config.prompt.system == "You are a code reviewer."
        assert config.model is not None
        assert config.model.provider == "anthropic"
        assert config.tools is not None
        assert "file_read" in config.tools.allow
        assert config.run.max_rounds == 15
        assert "code" in config.tags
        assert config.version == "2.0.0"
        assert config.author == "Test Author"
        assert config.enabled is True
    
    def test_default_values(self):
        """Test default values for SubagentConfig."""
        config = SubagentConfig(
            name="test",
            description="Test",
        )
        
        assert config.version == "1.0.0"
        assert config.author is None
        assert config.enabled is True
        assert config.tags == []
        assert config.model is None
        assert config.tools is None
    
    def test_model_dump(self):
        """Test serialization of SubagentConfig."""
        config = SubagentConfig(
            name="test_agent",
            description="Test description",
        )
        
        data = config.model_dump()
        
        assert data["name"] == "test_agent"
        assert data["description"] == "Test description"


class TestSubagentLevel:
    """Tests for SubagentLevel enum."""
    
    def test_level_values(self):
        """Test enum values."""
        assert SubagentLevel.PROJECT.value == "project"
        assert SubagentLevel.USER.value == "user"
        assert SubagentLevel.BUILTIN.value == "builtin"
    
    def test_level_from_string(self):
        """Test creating enum from string."""
        level = SubagentLevel("project")
        assert level == SubagentLevel.PROJECT


class TestSubagentErrorCode:
    """Tests for SubagentErrorCode enum."""
    
    def test_error_codes(self):
        """Test error code values."""
        assert SubagentErrorCode.NOT_FOUND.value == "NOT_FOUND"
        assert SubagentErrorCode.ALREADY_EXISTS.value == "ALREADY_EXISTS"
        assert SubagentErrorCode.INVALID_CONFIG.value == "INVALID_CONFIG"
        assert SubagentErrorCode.VALIDATION_ERROR.value == "VALIDATION_ERROR"
        assert SubagentErrorCode.FILE_ERROR.value == "FILE_ERROR"
        assert SubagentErrorCode.EXECUTION_ERROR.value == "EXECUTION_ERROR"
        assert SubagentErrorCode.PERMISSION_DENIED.value == "PERMISSION_DENIED"


class TestSubagentTerminateMode:
    """Tests for SubagentTerminateMode enum."""
    
    def test_mode_values(self):
        """Test enum values."""
        assert SubagentTerminateMode.AUTO.value == "auto"
        assert SubagentTerminateMode.MANUAL.value == "manual"
        assert SubagentTerminateMode.ON_SUCCESS.value == "on_success"


class TestSubagentRuntimeConfig:
    """Tests for SubagentRuntimeConfig."""
    
    def test_runtime_config_creation(self):
        """Test creating a runtime config."""
        config = SubagentRuntimeConfig(
            name="test_agent",
            system_prompt="You are a test agent.",
            model_provider="openai",
            model_name="gpt-4",
            allowed_tools=["file_read", "file_write"],
            denied_tools=["bash"],
            require_approval_tools=["file_write"],
            auto_approve_tools=["file_read"],
            max_rounds=10,
            terminate_mode=SubagentTerminateMode.AUTO,
            timeout=300,
        )
        
        assert config.name == "test_agent"
        assert config.system_prompt == "You are a test agent."
        assert config.model_provider == "openai"
        assert config.model_name == "gpt-4"
        assert "file_read" in config.allowed_tools
        assert "bash" in config.denied_tools


class TestValidationResult:
    """Tests for ValidationResult."""
    
    def test_valid_result(self):
        """Test a valid validation result."""
        config = SubagentConfig(name="test", description="Test")
        result = ValidationResult(
            valid=True,
            errors=[],
            warnings=[],
            config=config,
        )
        
        assert result.valid is True
        assert len(result.errors) == 0
        assert result.config is not None
    
    def test_invalid_result(self):
        """Test an invalid validation result."""
        result = ValidationResult(
            valid=False,
            errors=["Name is required", "Description is required"],
            warnings=["No tools specified"],
        )
        
        assert result.valid is False
        assert len(result.errors) == 2
        assert len(result.warnings) == 1
        assert result.config is None


class TestSubagentConfigSerialization:
    """Tests for SubagentConfig serialization."""
    
    def test_to_dict(self):
        """Test converting to dictionary."""
        config = SubagentConfig(
            name="test_agent",
            description="Test agent",
            tags=["test", "agent"],
        )
        
        data = config.model_dump()
        
        assert isinstance(data, dict)
        assert data["name"] == "test_agent"
        assert "test" in data["tags"]
    
    def test_json_serialization(self):
        """Test JSON serialization."""
        config = SubagentConfig(
            name="json_agent",
            description="JSON test",
        )
        
        json_str = config.model_dump_json()
        
        assert isinstance(json_str, str)
        assert "json_agent" in json_str


class TestNestedConfigSerialization:
    """Tests for nested configuration serialization."""
    
    def test_nested_prompt_config(self):
        """Test nested prompt config serialization."""
        config = SubagentConfig(
            name="test",
            description="Test",
            prompt=PromptConfig(
                system="System prompt",
                user_prefix="Prefix: ",
            ),
        )
        
        data = config.model_dump()
        
        assert data["prompt"]["system"] == "System prompt"
        assert data["prompt"]["user_prefix"] == "Prefix: "
    
    def test_nested_model_config(self):
        """Test nested model config serialization."""
        config = SubagentConfig(
            name="test",
            description="Test",
            model=ModelConfig(
                provider="openai",
                name="gpt-4",
                temperature=0.5,
            ),
        )
        
        data = config.model_dump()
        
        assert data["model"]["provider"] == "openai"
        assert data["model"]["temperature"] == 0.5
    
    def test_nested_tool_config(self):
        """Test nested tool config serialization."""
        config = SubagentConfig(
            name="test",
            description="Test",
            tools=ToolConfig(
                allow=["file_read"],
                deny=["bash"],
            ),
        )
        
        data = config.model_dump()
        
        assert "file_read" in data["tools"]["allow"]
        assert "bash" in data["tools"]["deny"]
