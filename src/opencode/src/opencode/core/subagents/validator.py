"""
Subagent configuration validator.

Validates subagent configurations for correctness and completeness.
"""

import re
from typing import List, Optional
from .types import (
    SubagentConfig,
    ValidationResult,
    PromptConfig,
    ModelConfig,
    ToolConfig,
    RunConfig,
)


class SubagentValidator:
    """Validator for subagent configurations."""
    
    # Valid name pattern: alphanumeric, underscores, hyphens
    NAME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]{0,63}$")
    
    # Reserved names that cannot be used
    RESERVED_NAMES = {
        "default",
        "system",
        "user",
        "assistant",
        "all",
        "none",
        "builtin",
    }
    
    # Maximum lengths
    MAX_NAME_LENGTH = 64
    MAX_DESCRIPTION_LENGTH = 500
    MAX_SYSTEM_PROMPT_LENGTH = 32000
    MAX_TAGS = 10
    
    def validate(self, config: dict) -> ValidationResult:
        """Validate a subagent configuration dictionary.
        
        Args:
            config: Raw configuration dictionary to validate
            
        Returns:
            ValidationResult with validity status and any errors/warnings
        """
        errors: List[str] = []
        warnings: List[str] = []
        
        # Validate required fields
        if "name" not in config:
            errors.append("Missing required field: name")
        elif not self._validate_name(config["name"]):
            errors.append(f"Invalid name: {config['name']}")
        
        if "description" not in config:
            errors.append("Missing required field: description")
        elif not self._validate_description(config["description"]):
            errors.append(f"Description exceeds maximum length ({self.MAX_DESCRIPTION_LENGTH})")
        
        # If basic validation failed, return early
        if errors:
            return ValidationResult(valid=False, errors=errors, warnings=warnings)
        
        # Validate optional fields
        if "prompt" in config and config["prompt"] is not None:
            prompt_errors, prompt_warnings = self._validate_prompt(config["prompt"])
            errors.extend(prompt_errors)
            warnings.extend(prompt_warnings)
        
        if "model" in config and config["model"] is not None:
            model_errors, model_warnings = self._validate_model(config["model"])
            errors.extend(model_errors)
            warnings.extend(model_warnings)
        
        if "tools" in config and config["tools"] is not None:
            tool_errors, tool_warnings = self._validate_tools(config["tools"])
            errors.extend(tool_errors)
            warnings.extend(tool_warnings)
        
        if "run" in config and config["run"] is not None:
            run_errors, run_warnings = self._validate_run(config["run"])
            errors.extend(run_errors)
            warnings.extend(run_warnings)
        
        if "tags" in config and config["tags"] is not None:
            tag_errors, tag_warnings = self._validate_tags(config["tags"])
            errors.extend(tag_errors)
            warnings.extend(tag_warnings)
        
        # Parse configuration if valid
        parsed_config = None
        if not errors:
            try:
                parsed_config = SubagentConfig(**config)
            except Exception as e:
                errors.append(f"Failed to parse configuration: {str(e)}")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            config=parsed_config,
        )
    
    def validate_config(self, config: SubagentConfig) -> ValidationResult:
        """Validate a SubagentConfig object.
        
        Args:
            config: SubagentConfig object to validate
            
        Returns:
            ValidationResult with validity status and any errors/warnings
        """
        return self.validate(config.model_dump())
    
    def _validate_name(self, name: str) -> bool:
        """Validate subagent name."""
        if not name:
            return False
        
        if len(name) > self.MAX_NAME_LENGTH:
            return False
        
        if not self.NAME_PATTERN.match(name):
            return False
        
        if name.lower() in self.RESERVED_NAMES:
            return False
        
        return True
    
    def _validate_description(self, description: str) -> bool:
        """Validate subagent description."""
        if not description:
            return False
        
        return len(description) <= self.MAX_DESCRIPTION_LENGTH
    
    def _validate_prompt(self, prompt: dict) -> tuple[List[str], List[str]]:
        """Validate prompt configuration."""
        errors: List[str] = []
        warnings: List[str] = []
        
        if "system" in prompt and prompt["system"] is not None:
            if len(prompt["system"]) > self.MAX_SYSTEM_PROMPT_LENGTH:
                errors.append(f"System prompt exceeds maximum length ({self.MAX_SYSTEM_PROMPT_LENGTH})")
        
        return errors, warnings
    
    def _validate_model(self, model: dict) -> tuple[List[str], List[str]]:
        """Validate model configuration."""
        errors: List[str] = []
        warnings: List[str] = []
        
        if "temperature" in model and model["temperature"] is not None:
            temp = model["temperature"]
            if not isinstance(temp, (int, float)):
                errors.append("temperature must be a number")
            elif temp < 0 or temp > 2:
                errors.append("temperature must be between 0 and 2")
        
        if "max_tokens" in model and model["max_tokens"] is not None:
            tokens = model["max_tokens"]
            if not isinstance(tokens, int):
                errors.append("max_tokens must be an integer")
            elif tokens < 1:
                errors.append("max_tokens must be at least 1")
        
        return errors, warnings
    
    def _validate_tools(self, tools: dict) -> tuple[List[str], List[str]]:
        """Validate tool configuration."""
        errors: List[str] = []
        warnings: List[str] = []
        
        # Check for conflicting allow/deny
        allow = set(tools.get("allow", []))
        deny = set(tools.get("deny", []))
        
        conflicts = allow & deny
        if conflicts:
            warnings.append(f"Tools both allowed and denied: {conflicts}")
        
        # Check for conflicting approval settings
        require_approval = set(tools.get("require_approval", []))
        auto_approve = set(tools.get("auto_approve", []))
        
        approval_conflicts = require_approval & auto_approve
        if approval_conflicts:
            errors.append(f"Tools cannot be both require_approval and auto_approve: {approval_conflicts}")
        
        return errors, warnings
    
    def _validate_run(self, run: dict) -> tuple[List[str], List[str]]:
        """Validate run configuration."""
        errors: List[str] = []
        warnings: List[str] = []
        
        if "max_rounds" in run and run["max_rounds"] is not None:
            max_rounds = run["max_rounds"]
            if not isinstance(max_rounds, int):
                errors.append("max_rounds must be an integer")
            elif max_rounds < 1:
                errors.append("max_rounds must be at least 1")
            elif max_rounds > 100:
                warnings.append("max_rounds > 100 may cause long execution times")
        
        if "timeout" in run and run["timeout"] is not None:
            timeout = run["timeout"]
            if not isinstance(timeout, int):
                errors.append("timeout must be an integer")
            elif timeout < 1:
                errors.append("timeout must be at least 1 second")
        
        return errors, warnings
    
    def _validate_tags(self, tags: list) -> tuple[List[str], List[str]]:
        """Validate tags."""
        errors: List[str] = []
        warnings: List[str] = []
        
        if len(tags) > self.MAX_TAGS:
            warnings.append(f"More than {self.MAX_TAGS} tags, some may be ignored")
        
        for tag in tags:
            if not isinstance(tag, str):
                errors.append(f"Tag must be a string, got: {type(tag).__name__}")
            elif len(tag) > 50:
                warnings.append(f"Tag '{tag[:20]}...' is very long")
        
        return errors, warnings
