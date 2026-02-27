"""
Tests for SubagentValidator.

Unit tests for the subagent configuration validator.
"""

import pytest
from opencode.core.subagents.validator import SubagentValidator
from opencode.core.subagents.types import (
    SubagentConfig,
    PromptConfig,
    ModelConfig,
    ToolConfig,
    RunConfig,
    SubagentTerminateMode,
)


class TestSubagentValidator:
    """Tests for SubagentValidator class."""
    
    @pytest.fixture
    def validator(self):
        """Create a validator instance."""
        return SubagentValidator()
    
    @pytest.fixture
    def valid_config_dict(self):
        """Create a valid configuration dictionary."""
        return {
            "name": "test_agent",
            "description": "A test subagent for validation",
        }
    
    @pytest.fixture
    def full_config_dict(self):
        """Create a full configuration dictionary with all fields."""
        return {
            "name": "full_agent",
            "description": "A fully configured subagent",
            "prompt": {
                "system": "You are a helpful assistant.",
            },
            "model": {
                "provider": "openai",
                "name": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 1000,
            },
            "tools": {
                "allow": ["bash", "file_read"],
                "deny": ["file_delete"],
                "require_approval": ["bash"],
                "auto_approve": ["file_read"],
            },
            "run": {
                "max_rounds": 10,
                "timeout": 300,
                "terminate_mode": "auto",
            },
            "tags": ["test", "demo"],
        }


class TestValidateName(TestSubagentValidator):
    """Tests for name validation."""
    
    def test_valid_name_simple(self, validator):
        """Test valid simple name."""
        result = validator._validate_name("myagent")
        assert result is True
    
    def test_valid_name_with_underscore(self, validator):
        """Test valid name with underscore."""
        result = validator._validate_name("my_agent")
        assert result is True
    
    def test_valid_name_with_hyphen(self, validator):
        """Test valid name with hyphen."""
        result = validator._validate_name("my-agent")
        assert result is True
    
    def test_valid_name_with_numbers(self, validator):
        """Test valid name with numbers."""
        result = validator._validate_name("agent123")
        assert result is True
    
    def test_valid_name_max_length(self, validator):
        """Test valid name at max length."""
        name = "a" + "b" * 63  # 64 chars total
        result = validator._validate_name(name)
        assert result is True
    
    def test_invalid_name_too_long(self, validator):
        """Test invalid name exceeding max length."""
        name = "a" + "b" * 64  # 65 chars total
        result = validator._validate_name(name)
        assert result is False
    
    def test_invalid_name_empty(self, validator):
        """Test invalid empty name."""
        result = validator._validate_name("")
        assert result is False
    
    def test_invalid_name_starts_with_number(self, validator):
        """Test invalid name starting with number."""
        result = validator._validate_name("123agent")
        assert result is False
    
    def test_invalid_name_starts_with_special(self, validator):
        """Test invalid name starting with special character."""
        result = validator._validate_name("_agent")
        assert result is False
    
    def test_invalid_name_with_spaces(self, validator):
        """Test invalid name with spaces."""
        result = validator._validate_name("my agent")
        assert result is False
    
    def test_invalid_name_with_special_chars(self, validator):
        """Test invalid name with special characters."""
        result = validator._validate_name("agent@name")
        assert result is False
    
    def test_reserved_name_default(self, validator):
        """Test reserved name 'default'."""
        result = validator._validate_name("default")
        assert result is False
    
    def test_reserved_name_system(self, validator):
        """Test reserved name 'system'."""
        result = validator._validate_name("system")
        assert result is False
    
    def test_reserved_name_user(self, validator):
        """Test reserved name 'user'."""
        result = validator._validate_name("user")
        assert result is False
    
    def test_reserved_name_assistant(self, validator):
        """Test reserved name 'assistant'."""
        result = validator._validate_name("assistant")
        assert result is False
    
    def test_reserved_name_all(self, validator):
        """Test reserved name 'all'."""
        result = validator._validate_name("all")
        assert result is False
    
    def test_reserved_name_none(self, validator):
        """Test reserved name 'none'."""
        result = validator._validate_name("none")
        assert result is False
    
    def test_reserved_name_builtin(self, validator):
        """Test reserved name 'builtin'."""
        result = validator._validate_name("builtin")
        assert result is False
    
    def test_reserved_name_case_insensitive(self, validator):
        """Test reserved name is case insensitive."""
        result = validator._validate_name("DEFAULT")
        assert result is False
    
    def test_reserved_name_mixed_case(self, validator):
        """Test reserved name with mixed case."""
        result = validator._validate_name("SyStEm")
        assert result is False


class TestValidateDescription(TestSubagentValidator):
    """Tests for description validation."""
    
    def test_valid_description(self, validator):
        """Test valid description."""
        result = validator._validate_description("A test agent")
        assert result is True
    
    def test_valid_description_max_length(self, validator):
        """Test valid description at max length."""
        desc = "x" * 500
        result = validator._validate_description(desc)
        assert result is True
    
    def test_invalid_description_too_long(self, validator):
        """Test invalid description exceeding max length."""
        desc = "x" * 501
        result = validator._validate_description(desc)
        assert result is False
    
    def test_invalid_description_empty(self, validator):
        """Test invalid empty description."""
        result = validator._validate_description("")
        assert result is False


class TestValidatePrompt(TestSubagentValidator):
    """Tests for prompt validation."""
    
    def test_valid_prompt_system(self, validator):
        """Test valid system prompt."""
        errors, warnings = validator._validate_prompt({
            "system": "You are helpful."
        })
        assert len(errors) == 0
        assert len(warnings) == 0
    
    def test_valid_prompt_max_length(self, validator):
        """Test valid system prompt at max length."""
        system = "x" * 32000
        errors, warnings = validator._validate_prompt({
            "system": system
        })
        assert len(errors) == 0
    
    def test_invalid_prompt_too_long(self, validator):
        """Test invalid system prompt exceeding max length."""
        system = "x" * 32001
        errors, warnings = validator._validate_prompt({
            "system": system
        })
        assert len(errors) == 1
        assert "exceeds maximum length" in errors[0]
    
    def test_empty_prompt(self, validator):
        """Test empty prompt dict."""
        errors, warnings = validator._validate_prompt({})
        assert len(errors) == 0
        assert len(warnings) == 0


class TestValidateModel(TestSubagentValidator):
    """Tests for model validation."""
    
    def test_valid_model_empty(self, validator):
        """Test valid empty model config."""
        errors, warnings = validator._validate_model({})
        assert len(errors) == 0
        assert len(warnings) == 0
    
    def test_valid_model_temperature(self, validator):
        """Test valid temperature."""
        errors, warnings = validator._validate_model({
            "temperature": 0.7
        })
        assert len(errors) == 0
    
    def test_valid_model_temperature_zero(self, validator):
        """Test valid temperature at zero."""
        errors, warnings = validator._validate_model({
            "temperature": 0
        })
        assert len(errors) == 0
    
    def test_valid_model_temperature_max(self, validator):
        """Test valid temperature at max."""
        errors, warnings = validator._validate_model({
            "temperature": 2
        })
        assert len(errors) == 0
    
    def test_invalid_model_temperature_negative(self, validator):
        """Test invalid negative temperature."""
        errors, warnings = validator._validate_model({
            "temperature": -0.1
        })
        assert len(errors) == 1
        assert "between 0 and 2" in errors[0]
    
    def test_invalid_model_temperature_too_high(self, validator):
        """Test invalid temperature too high."""
        errors, warnings = validator._validate_model({
            "temperature": 2.1
        })
        assert len(errors) == 1
        assert "between 0 and 2" in errors[0]
    
    def test_invalid_model_temperature_not_number(self, validator):
        """Test invalid temperature not a number."""
        errors, warnings = validator._validate_model({
            "temperature": "hot"
        })
        assert len(errors) == 1
        assert "must be a number" in errors[0]
    
    def test_valid_model_max_tokens(self, validator):
        """Test valid max_tokens."""
        errors, warnings = validator._validate_model({
            "max_tokens": 1000
        })
        assert len(errors) == 0
    
    def test_valid_model_max_tokens_one(self, validator):
        """Test valid max_tokens at minimum."""
        errors, warnings = validator._validate_model({
            "max_tokens": 1
        })
        assert len(errors) == 0
    
    def test_invalid_model_max_tokens_zero(self, validator):
        """Test invalid max_tokens at zero."""
        errors, warnings = validator._validate_model({
            "max_tokens": 0
        })
        assert len(errors) == 1
        assert "must be at least 1" in errors[0]
    
    def test_invalid_model_max_tokens_negative(self, validator):
        """Test invalid negative max_tokens."""
        errors, warnings = validator._validate_model({
            "max_tokens": -1
        })
        assert len(errors) == 1
    
    def test_invalid_model_max_tokens_not_int(self, validator):
        """Test invalid max_tokens not an integer."""
        errors, warnings = validator._validate_model({
            "max_tokens": 100.5
        })
        assert len(errors) == 1
        assert "must be an integer" in errors[0]


class TestValidateTools(TestSubagentValidator):
    """Tests for tools validation."""
    
    def test_valid_tools_empty(self, validator):
        """Test valid empty tools config."""
        errors, warnings = validator._validate_tools({})
        assert len(errors) == 0
        assert len(warnings) == 0
    
    def test_valid_tools_allow(self, validator):
        """Test valid allow list."""
        errors, warnings = validator._validate_tools({
            "allow": ["bash", "file_read"]
        })
        assert len(errors) == 0
        assert len(warnings) == 0
    
    def test_valid_tools_deny(self, validator):
        """Test valid deny list."""
        errors, warnings = validator._validate_tools({
            "deny": ["file_delete"]
        })
        assert len(errors) == 0
        assert len(warnings) == 0
    
    def test_warning_tools_conflict(self, validator):
        """Test warning for tools in both allow and deny."""
        errors, warnings = validator._validate_tools({
            "allow": ["bash", "file_read"],
            "deny": ["bash"]
        })
        assert len(warnings) == 1
        assert "both allowed and denied" in warnings[0]
    
    def test_valid_tools_require_approval(self, validator):
        """Test valid require_approval list."""
        errors, warnings = validator._validate_tools({
            "require_approval": ["bash"]
        })
        assert len(errors) == 0
    
    def test_valid_tools_auto_approve(self, validator):
        """Test valid auto_approve list."""
        errors, warnings = validator._validate_tools({
            "auto_approve": ["file_read"]
        })
        assert len(errors) == 0
    
    def test_error_tools_approval_conflict(self, validator):
        """Test error for tools in both require_approval and auto_approve."""
        errors, warnings = validator._validate_tools({
            "require_approval": ["bash", "file_read"],
            "auto_approve": ["file_read"]
        })
        assert len(errors) == 1
        assert "cannot be both" in errors[0]


class TestValidateRun(TestSubagentValidator):
    """Tests for run configuration validation."""
    
    def test_valid_run_empty(self, validator):
        """Test valid empty run config."""
        errors, warnings = validator._validate_run({})
        assert len(errors) == 0
        assert len(warnings) == 0
    
    def test_valid_run_max_rounds(self, validator):
        """Test valid max_rounds."""
        errors, warnings = validator._validate_run({
            "max_rounds": 10
        })
        assert len(errors) == 0
        assert len(warnings) == 0
    
    def test_valid_run_max_rounds_one(self, validator):
        """Test valid max_rounds at minimum."""
        errors, warnings = validator._validate_run({
            "max_rounds": 1
        })
        assert len(errors) == 0
    
    def test_warning_run_max_rounds_high(self, validator):
        """Test warning for high max_rounds."""
        errors, warnings = validator._validate_run({
            "max_rounds": 101
        })
        assert len(warnings) == 1
        assert "may cause long execution" in warnings[0]
    
    def test_invalid_run_max_rounds_zero(self, validator):
        """Test invalid max_rounds at zero."""
        errors, warnings = validator._validate_run({
            "max_rounds": 0
        })
        assert len(errors) == 1
        assert "must be at least 1" in errors[0]
    
    def test_invalid_run_max_rounds_negative(self, validator):
        """Test invalid negative max_rounds."""
        errors, warnings = validator._validate_run({
            "max_rounds": -1
        })
        assert len(errors) == 1
    
    def test_invalid_run_max_rounds_not_int(self, validator):
        """Test invalid max_rounds not an integer."""
        errors, warnings = validator._validate_run({
            "max_rounds": 10.5
        })
        assert len(errors) == 1
        assert "must be an integer" in errors[0]
    
    def test_valid_run_timeout(self, validator):
        """Test valid timeout."""
        errors, warnings = validator._validate_run({
            "timeout": 300
        })
        assert len(errors) == 0
    
    def test_valid_run_timeout_one(self, validator):
        """Test valid timeout at minimum."""
        errors, warnings = validator._validate_run({
            "timeout": 1
        })
        assert len(errors) == 0
    
    def test_invalid_run_timeout_zero(self, validator):
        """Test invalid timeout at zero."""
        errors, warnings = validator._validate_run({
            "timeout": 0
        })
        assert len(errors) == 1
        assert "must be at least 1 second" in errors[0]
    
    def test_invalid_run_timeout_negative(self, validator):
        """Test invalid negative timeout."""
        errors, warnings = validator._validate_run({
            "timeout": -1
        })
        assert len(errors) == 1
    
    def test_invalid_run_timeout_not_int(self, validator):
        """Test invalid timeout not an integer."""
        errors, warnings = validator._validate_run({
            "timeout": 30.5
        })
        assert len(errors) == 1
        assert "must be an integer" in errors[0]


class TestValidateTags(TestSubagentValidator):
    """Tests for tags validation."""
    
    def test_valid_tags_empty(self, validator):
        """Test valid empty tags list."""
        errors, warnings = validator._validate_tags([])
        assert len(errors) == 0
        assert len(warnings) == 0
    
    def test_valid_tags_list(self, validator):
        """Test valid tags list."""
        errors, warnings = validator._validate_tags(["test", "demo"])
        assert len(errors) == 0
        assert len(warnings) == 0
    
    def test_valid_tags_max_count(self, validator):
        """Test valid tags at max count."""
        tags = [f"tag{i}" for i in range(10)]
        errors, warnings = validator._validate_tags(tags)
        assert len(errors) == 0
        assert len(warnings) == 0
    
    def test_warning_tags_too_many(self, validator):
        """Test warning for too many tags."""
        tags = [f"tag{i}" for i in range(11)]
        errors, warnings = validator._validate_tags(tags)
        assert len(warnings) == 1
        assert "More than" in warnings[0]
    
    def test_invalid_tag_not_string(self, validator):
        """Test invalid tag not a string."""
        errors, warnings = validator._validate_tags([123])
        assert len(errors) == 1
        assert "must be a string" in errors[0]
    
    def test_warning_tag_too_long(self, validator):
        """Test warning for very long tag."""
        tag = "x" * 51
        errors, warnings = validator._validate_tags([tag])
        assert len(warnings) == 1
        assert "is very long" in warnings[0]


class TestValidate(TestSubagentValidator):
    """Tests for the main validate method."""
    
    def test_validate_minimal_config(self, validator, valid_config_dict):
        """Test validating minimal valid config."""
        result = validator.validate(valid_config_dict)
        assert result.valid is True
        assert len(result.errors) == 0
        assert result.config is not None
        assert result.config.name == "test_agent"
    
    def test_validate_full_config(self, validator, full_config_dict):
        """Test validating full config with all fields."""
        result = validator.validate(full_config_dict)
        assert result.valid is True
        assert len(result.errors) == 0
        assert result.config is not None
        assert result.config.name == "full_agent"
    
    def test_validate_missing_name(self, validator):
        """Test validating config missing name."""
        result = validator.validate({"description": "Test"})
        assert result.valid is False
        assert "Missing required field: name" in result.errors
    
    def test_validate_missing_description(self, validator):
        """Test validating config missing description."""
        result = validator.validate({"name": "test_agent"})
        assert result.valid is False
        assert "Missing required field: description" in result.errors
    
    def test_validate_invalid_name(self, validator):
        """Test validating config with invalid name."""
        result = validator.validate({
            "name": "123invalid",
            "description": "Test"
        })
        assert result.valid is False
        assert "Invalid name" in result.errors[0]
    
    def test_validate_invalid_description(self, validator):
        """Test validating config with invalid description."""
        result = validator.validate({
            "name": "test_agent",
            "description": "x" * 501
        })
        assert result.valid is False
    
    def test_validate_returns_early_on_basic_errors(self, validator):
        """Test that validation returns early on basic field errors."""
        result = validator.validate({
            "name": "invalid!",
            "description": "x" * 501,
            "model": {"temperature": -1}
        })
        assert result.valid is False
        # Should have name and description errors, but not model error
        assert len(result.errors) == 2
        assert "Invalid name" in result.errors[0]
        assert "Description exceeds" in result.errors[1]
    
    def test_validate_collects_all_field_errors(self, validator):
        """Test that validation collects errors from all fields."""
        result = validator.validate({
            "name": "test_agent",
            "description": "Test description",
            "model": {"temperature": -1},
            "run": {"max_rounds": 0}
        })
        assert result.valid is False
        assert len(result.errors) == 2
    
    def test_validate_collects_warnings(self, validator):
        """Test that validation collects warnings."""
        result = validator.validate({
            "name": "test_agent",
            "description": "Test description",
            "run": {"max_rounds": 200}
        })
        assert result.valid is True
        assert len(result.warnings) == 1


class TestValidateConfig(TestSubagentValidator):
    """Tests for validate_config method with SubagentConfig objects."""
    
    def test_validate_config_object(self, validator):
        """Test validating a SubagentConfig object."""
        config = SubagentConfig(
            name="test_agent",
            description="Test description"
        )
        result = validator.validate_config(config)
        assert result.valid is True
    
    def test_validate_config_object_full(self, validator):
        """Test validating a full SubagentConfig object."""
        config = SubagentConfig(
            name="full_agent",
            description="Full description",
            prompt=PromptConfig(system="You are helpful."),
            model=ModelConfig(
                provider="openai",
                name="gpt-4",
                temperature=0.7,
                max_tokens=1000
            ),
            tools=ToolConfig(
                allow=["bash"],
                deny=["file_delete"],
                require_approval=["bash"],
                auto_approve=["file_read"]
            ),
            run=RunConfig(
                max_rounds=10,
                timeout=300,
                terminate_mode=SubagentTerminateMode.AUTO
            ),
            tags=["test"]
        )
        result = validator.validate_config(config)
        assert result.valid is True


class TestValidationResult(TestSubagentValidator):
    """Tests for ValidationResult."""
    
    def test_validation_result_attributes(self, validator, valid_config_dict):
        """Test ValidationResult has correct attributes."""
        result = validator.validate(valid_config_dict)
        assert hasattr(result, "valid")
        assert hasattr(result, "errors")
        assert hasattr(result, "warnings")
        assert hasattr(result, "config")
    
    def test_validation_result_config_none_on_error(self, validator):
        """Test config is None when validation fails."""
        result = validator.validate({"name": "invalid!"})
        assert result.config is None
