r"""
Configuration management for OpenCode.

Supports loading configuration from:
- opencode.toml in project directory
- ~/.config/opencode/config.toml for global settings
- Environment variables (OPENCODE_*)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

try:
    import tomllib
except ImportError:
    import tomli as tomllib

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentType(str, Enum):
    """Available agent types."""
    BUILD = "build"
    PLAN = "plan"


class MultiModelPattern(str, Enum):
    """Available multi-model patterns."""
    SEQUENTIAL = "sequential"      # Chain of models refining output
    ENSEMBLE = "ensemble"          # Parallel models with aggregation
    VOTING = "voting"              # Multiple models vote on best answer
    SPECIALIZED = "specialized"    # Route to specialized models


class ModelStepConfig(BaseModel):
    """Configuration for a single model step in a multi-model pattern."""
    model: str                              # Model identifier
    provider: str = "ollama"                # Provider name
    system_prompt: Optional[str] = None     # System prompt for this step
    temperature: float = 0.7                # Sampling temperature
    max_tokens: int = 4096                  # Maximum tokens to generate
    
    # Multi-GPU support
    gpu_id: Optional[int] = None            # Specific GPU ID to use (None = auto-select)
    gpu_ids: Optional[list[int]] = None     # Multiple GPUs for tensor parallelism
    vram_required_gb: Optional[float] = None  # Estimated VRAM requirement
    exclusive_gpu: bool = False             # Reserve GPU exclusively for this model

    class Config:
        extra = "ignore"


class MultiModelConfig(BaseModel):
    """Configuration for multi-model patterns."""
    pattern: MultiModelPattern              # Pattern type
    models: list["ModelStepConfig"] = Field(default_factory=list)
    aggregator_model: Optional[str] = None  # For ensemble pattern
    voting_strategy: str = "majority"       # For voting pattern: majority, weighted, consensus
    enabled: bool = True

    class Config:
        extra = "ignore"


class ProviderConfig(BaseModel):
    """Configuration for an AI provider."""
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    models: list[str] = Field(default_factory=list)
    default_model: Optional[str] = None
    enabled: bool = True
    extra: dict[str, Any] = Field(default_factory=dict)


class ModelConfig(BaseModel):
    """Configuration for a specific model."""
    provider: str
    model_id: str
    max_tokens: int = 4096
    temperature: float = 0.7
    supports_tools: bool = True
    supports_vision: bool = False
    supports_streaming: bool = True
    cost_per_input_token: float = 0.0
    cost_per_output_token: float = 0.0


class MCPServerConfig(BaseModel):
    """Configuration for an MCP server."""
    command: str
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    enabled: bool = True


class LSPConfig(BaseModel):
    """Configuration for LSP servers."""
    enabled: bool = True
    servers: dict[str, dict[str, Any]] = Field(default_factory=dict)


class PermissionConfig(BaseModel):
    """Configuration for permission system."""
    auto_approve_tools: list[str] = Field(default_factory=list)
    auto_approve_bash_patterns: list[str] = Field(default_factory=list)
    ask_before_bash: bool = True
    ask_before_edit: bool = True


class TUIConfig(BaseModel):
    """Configuration for terminal UI."""
    theme: str = "dark"
    show_token_count: bool = True
    show_cost: bool = True
    compact_mode: bool = False


class ServerConfig(BaseModel):
    """Configuration for HTTP server."""
    host: str = "127.0.0.1"
    port: int = 4096
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:*"])
    auth_enabled: bool = False
    auth_password: Optional[str] = None


class GPUAllocationStrategy(str, Enum):
    """Strategy for allocating GPUs to models."""
    AUTO = "auto"              # Automatically select best available GPU
    ROUND_ROBIN = "round_robin"  # Distribute across GPUs evenly
    PACK = "pack"              # Fill GPUs before using next one
    SPREAD = "spread"          # Spread models across all GPUs
    MANUAL = "manual"          # Use explicitly configured GPU IDs


class GPUConfig(BaseModel):
    """Configuration for GPU management."""
    strategy: GPUAllocationStrategy = GPUAllocationStrategy.AUTO
    vram_threshold_percent: float = 85.0  # Don't allocate if GPU above this
    allow_shared_gpu: bool = True  # Allow multiple models on same GPU
    auto_unload: bool = True  # Auto-unload models when VRAM is low
    reserved_vram_gb: float = 1.0  # Reserve this much VRAM for system


class ProfileConfig(BaseModel):
    """Configuration for a profile/environment."""
    default_model: Optional[str] = None
    default_agent: Optional[AgentType] = None
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)
    models: dict[str, ModelConfig] = Field(default_factory=dict)
    mcp_servers: dict[str, MCPServerConfig] = Field(default_factory=dict)
    permissions: Optional[PermissionConfig] = None
    tui: Optional[TUIConfig] = None
    server: Optional[ServerConfig] = None


class Config(BaseSettings):
    """
    Main configuration class for OpenCode.
    
    Configuration is loaded from multiple sources in order of priority:
    1. Environment variables (highest priority)
    2. Project config file (opencode.toml)
    3. Global config file (~/.config/opencode/config.toml)
    4. Default values (lowest priority)
    """
    
    model_config = SettingsConfigDict(
        env_prefix="OPENCODE_",
        env_nested_delimiter="__",
        case_sensitive=False,
    )
    
    # Core settings
    default_model: str = "claude-3-5-sonnet"
    default_agent: AgentType = AgentType.BUILD
    log_level: str = "INFO"
    # data_dir will be set to project_dir/docs/opencode when project_dir is provided
    # Falls back to user home directory for standalone usage
    data_dir: Path = Field(default=None)  # type: ignore
    # plans_dir will be set to project_dir/plans when project_dir is provided
    # Falls back to user home directory for standalone usage
    plans_dir: Path = Field(default=None)  # type: ignore
    config_dir: Path = Field(default_factory=lambda: Path.home() / ".config" / "opencode")
    
    # Provider configurations
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)
    models: dict[str, ModelConfig] = Field(default_factory=dict)
    
    # Feature configurations
    mcp_servers: dict[str, MCPServerConfig] = Field(default_factory=dict)
    lsp: LSPConfig = Field(default_factory=LSPConfig)
    permissions: PermissionConfig = Field(default_factory=PermissionConfig)
    tui: TUIConfig = Field(default_factory=TUIConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    gpu: GPUConfig = Field(default_factory=GPUConfig)
    
    # Multi-model pattern configurations
    multi_model_patterns: dict[str, MultiModelConfig] = Field(default_factory=dict)
    
    # Project-specific
    project_dir: Path = Field(default_factory=Path.cwd)
    project_name: Optional[str] = None
    
    @classmethod
    def load(cls, project_dir: Optional[Path] = None) -> "Config":
        """
        Load configuration from all sources.
        
        Args:
            project_dir: Project directory to load config from
            
        Returns:
            Loaded configuration
        """
        config_data: dict[str, Any] = {}
        
        # Load global config
        global_config_path = Path.home() / ".config" / "opencode" / "config.toml"
        if global_config_path.exists():
            config_data.update(cls._load_toml(global_config_path))
        
        # Load project config
        if project_dir:
            project_config_path = project_dir / "opencode.toml"
            if project_config_path.exists():
                project_config = cls._load_toml(project_config_path)
                # Deep merge
                config_data = cls._deep_merge(config_data, project_config)
            config_data["project_dir"] = project_dir
        
        # Create config instance (this also loads from env vars)
        config = cls(**config_data)
        
        # Set data_dir and plans_dir based on project_dir
        # This ensures all opencode data is stored in the target project's folders
        if project_dir:
            # Docs, sessions, logs go to project's docs/opencode folder
            config.data_dir = project_dir / "docs" / "opencode"
            # Plans go to project's plans folder
            config.plans_dir = project_dir / "plans"
        else:
            # Fall back to user home directory for standalone usage
            if config.data_dir is None:
                config.data_dir = Path.home() / ".local" / "share" / "opencode"
            if config.plans_dir is None:
                config.plans_dir = Path.home() / ".local" / "share" / "opencode" / "plans"
        
        # Ensure directories exist
        config.data_dir.mkdir(parents=True, exist_ok=True)
        config.plans_dir.mkdir(parents=True, exist_ok=True)
        config.config_dir.mkdir(parents=True, exist_ok=True)
        
        return config
    
    @staticmethod
    def _load_toml(path: Path) -> dict[str, Any]:
        """Load a TOML configuration file."""
        with open(path, "rb") as f:
            return tomllib.load(f)
    
    @staticmethod
    def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = Config._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def get_provider_config(self, provider_name: str) -> ProviderConfig:
        """Get configuration for a specific provider."""
        if provider_name in self.providers:
            return self.providers[provider_name]
        return ProviderConfig()
    
    def get_model_config(self, model_id: str) -> Optional[ModelConfig]:
        """Get configuration for a specific model."""
        return self.models.get(model_id)
    
    def get_api_key(self, provider_name: str) -> Optional[str]:
        """
        Get API key for a provider.
        
        Checks in order:
        1. Provider config
        2. Environment variable (e.g., ANTHROPIC_API_KEY)
        """
        # Check provider config
        if provider_name in self.providers:
            key = self.providers[provider_name].api_key
            if key:
                return key
        
        # Check environment variable
        env_var_map = {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "google": "GOOGLE_API_KEY",
            "azure": "AZURE_OPENAI_API_KEY",
            "groq": "GROQ_API_KEY",
            "mistral": "MISTRAL_API_KEY",
            "cohere": "COHERE_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
        }
        
        env_var = env_var_map.get(provider_name.lower())
        if env_var:
            return os.environ.get(env_var)
        
        return None
    
    def get_database_path(self) -> Path:
        """Get the path to the SQLite database."""
        return self.data_dir / "opencode.db"
    
    def get_sessions_dir(self) -> Path:
        """Get the directory for session storage."""
        return self.data_dir / "sessions"
    
    def get_logs_dir(self) -> Path:
        """Get the directory for log files."""
        return self.data_dir / "logs"
    
    def get_plans_dir(self) -> Path:
        """Get the directory for plan files."""
        return self.plans_dir


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config.load()
    return _config


def set_config(config: Config) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config


def reload_config(project_dir: Optional[Path] = None) -> Config:
    """Reload configuration from sources."""
    global _config
    _config = Config.load(project_dir)
    return _config
