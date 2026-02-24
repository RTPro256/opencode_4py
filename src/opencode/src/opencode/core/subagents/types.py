"""
Type definitions for the subagents system.

Based on qwen-code subagents implementation.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class SubagentLevel(str, Enum):
    """Storage level for subagent configurations."""
    PROJECT = "project"  # Stored in .opencode/subagents/
    USER = "user"  # Stored in ~/.opencode/subagents/
    BUILTIN = "builtin"  # Built-in agents


class SubagentErrorCode(str, Enum):
    """Error codes for subagent operations."""
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    INVALID_CONFIG = "INVALID_CONFIG"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    FILE_ERROR = "FILE_ERROR"
    EXECUTION_ERROR = "EXECUTION_ERROR"
    PERMISSION_DENIED = "PERMISSION_DENIED"


class SubagentTerminateMode(str, Enum):
    """How a subagent should terminate."""
    AUTO = "auto"  # Automatically terminate when done
    MANUAL = "manual"  # Require manual termination
    ON_SUCCESS = "on_success"  # Terminate only on success


class PromptConfig(BaseModel):
    """Configuration for subagent prompts."""
    system: Optional[str] = None
    """System prompt for the subagent."""
    
    user_prefix: Optional[str] = None
    """Prefix to add to user messages."""
    
    user_suffix: Optional[str] = None
    """Suffix to add to user messages."""
    
    include_context: bool = True
    """Whether to include conversation context."""


class ModelConfig(BaseModel):
    """Configuration for model selection."""
    provider: Optional[str] = None
    """Provider to use (e.g., 'openai', 'anthropic')."""
    
    name: Optional[str] = None
    """Model name (e.g., 'gpt-4', 'claude-3-opus')."""
    
    temperature: Optional[float] = Field(default=None, ge=0, le=2)
    """Temperature for model responses."""
    
    max_tokens: Optional[int] = Field(default=None, ge=1)
    """Maximum tokens in response."""


class ToolConfig(BaseModel):
    """Configuration for tool access."""
    allow: List[str] = Field(default_factory=list)
    """List of allowed tools (use '*' for all)."""
    
    deny: List[str] = Field(default_factory=list)
    """List of denied tools."""
    
    require_approval: List[str] = Field(default_factory=list)
    """Tools that require user approval before execution."""
    
    auto_approve: List[str] = Field(default_factory=list)
    """Tools that can be executed without approval."""


class RunConfig(BaseModel):
    """Configuration for subagent execution."""
    max_rounds: int = Field(default=10, ge=1)
    """Maximum number of conversation rounds."""
    
    terminate_mode: SubagentTerminateMode = SubagentTerminateMode.AUTO
    """How to terminate the subagent."""
    
    timeout: Optional[int] = Field(default=None, ge=1)
    """Timeout in seconds for subagent execution."""
    
    retry_on_error: bool = False
    """Whether to retry on errors."""
    
    max_retries: int = Field(default=3, ge=0)
    """Maximum number of retries."""


class SubagentConfig(BaseModel):
    """File-based subagent configuration.
    
    This is the primary configuration object stored in markdown files
    with YAML frontmatter.
    """
    name: str
    """Unique identifier for the subagent."""
    
    description: str
    """Human-readable description of when to use this agent."""
    
    prompt: PromptConfig = Field(default_factory=PromptConfig)
    """Prompt configuration."""
    
    model: Optional[ModelConfig] = None
    """Model configuration."""
    
    tools: Optional[ToolConfig] = None
    """Tool access configuration."""
    
    run: RunConfig = Field(default_factory=RunConfig)
    """Execution configuration."""
    
    tags: List[str] = Field(default_factory=list)
    """Tags for categorization and search."""
    
    version: str = "1.0.0"
    """Configuration version."""
    
    author: Optional[str] = None
    """Author of the subagent configuration."""
    
    enabled: bool = True
    """Whether this subagent is enabled."""

    class Config:
        extra = "forbid"


class SubagentRuntimeConfig(BaseModel):
    """Runtime configuration for subagent execution.
    
    This is the resolved configuration used during execution,
    combining file-based config with runtime overrides.
    """
    name: str
    """Subagent name."""
    
    system_prompt: str
    """Resolved system prompt."""
    
    model_provider: str
    """Resolved provider name."""
    
    model_name: str
    """Resolved model name."""
    
    allowed_tools: List[str]
    """Resolved list of allowed tools."""
    
    denied_tools: List[str]
    """Resolved list of denied tools."""
    
    require_approval_tools: List[str]
    """Tools requiring approval."""
    
    auto_approve_tools: List[str]
    """Tools that can auto-approve."""
    
    max_rounds: int
    """Maximum conversation rounds."""
    
    terminate_mode: SubagentTerminateMode
    """Termination mode."""
    
    timeout: Optional[int]
    """Execution timeout."""
    
    context: Dict[str, Any] = Field(default_factory=dict)
    """Additional runtime context."""


class ValidationResult(BaseModel):
    """Result of subagent configuration validation."""
    valid: bool
    """Whether the configuration is valid."""
    
    errors: List[str] = Field(default_factory=list)
    """List of validation errors."""
    
    warnings: List[str] = Field(default_factory=list)
    """List of validation warnings."""
    
    config: Optional[SubagentConfig] = None
    """Parsed configuration if valid."""


class ListSubagentsOptions(BaseModel):
    """Options for listing subagents."""
    level: SubagentLevel = SubagentLevel.PROJECT
    """Filter by storage level."""
    
    enabled_only: bool = True
    """Only return enabled subagents."""
    
    tags: Optional[List[str]] = None
    """Filter by tags."""
    
    include_builtin: bool = True
    """Include built-in agents in results."""


class CreateSubagentOptions(BaseModel):
    """Options for creating a subagent."""
    name: str
    """Subagent name."""
    
    description: str
    """Description of the subagent."""
    
    system_prompt: str
    """System prompt for the subagent."""
    
    model: Optional[str] = None
    """Model to use."""
    
    provider: Optional[str] = None
    """Provider to use."""
    
    allowed_tools: List[str] = Field(default_factory=lambda: ["*"])
    """Allowed tools."""
    
    denied_tools: List[str] = Field(default_factory=list)
    """Denied tools."""
    
    level: SubagentLevel = SubagentLevel.PROJECT
    """Storage level for the configuration."""
    
    overwrite: bool = False
    """Whether to overwrite existing configuration."""
