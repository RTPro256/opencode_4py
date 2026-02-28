"""
Subagent Manager - CRUD operations for subagent configurations.

Handles file-based storage of subagent configurations in markdown format
with YAML frontmatter.
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any
import yaml
import asyncio
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

from .types import (
    SubagentConfig,
    SubagentLevel,
    SubagentRuntimeConfig,
    ListSubagentsOptions,
    CreateSubagentOptions,
    SubagentTerminateMode,
    PromptConfig,
    ModelConfig,
    ToolConfig,
)
from .errors import (
    SubagentNotFoundError,
    SubagentAlreadyExistsError,
    SubagentFileError,
    SubagentValidationError,
)
from .validator import SubagentValidator
from .builtin import BuiltinAgentRegistry


class SubagentManager:
    """Manager for subagent configurations.
    
    Handles storage and retrieval of subagent configurations at both
    project and user levels.
    
    Storage locations:
    - Project: .opencode/subagents/*.md
    - User: ~/.opencode/subagents/*.md
    """
    
    def __init__(
        self,
        project_root: Optional[Path] = None,
        user_home: Optional[Path] = None,
    ):
        """Initialize the subagent manager.
        
        Args:
            project_root: Project root directory (defaults to cwd)
            user_home: User home directory (defaults to ~)
        """
        self.project_root = project_root or Path.cwd()
        self.user_home = user_home or Path.home()
        self.validator = SubagentValidator()
        self.builtin_registry = BuiltinAgentRegistry()
        
        # Storage directories
        self.project_subagents_dir = self.project_root / ".opencode" / "subagents"
        self.user_subagents_dir = self.user_home / ".opencode" / "subagents"
    
    async def list_subagents(
        self,
        options: Optional[ListSubagentsOptions] = None
    ) -> List[SubagentConfig]:
        """List available subagents.
        
        Args:
            options: Filtering options
            
        Returns:
            List of subagent configurations
        """
        options = options or ListSubagentsOptions()
        subagents: Dict[str, SubagentConfig] = {}
        
        # Load built-in agents
        if options.include_builtin:
            for config in self.builtin_registry.list_builtin():
                if options.enabled_only and not config.enabled:
                    continue
                if options.tags and not set(config.tags) & set(options.tags):
                    continue
                subagents[config.name] = config
        
        # Load from user level
        if options.level in (SubagentLevel.USER, SubagentLevel.PROJECT):
            user_configs = await self._load_from_directory(
                self.user_subagents_dir,
                SubagentLevel.USER
            )
            for config in user_configs:
                if options.enabled_only and not config.enabled:
                    continue
                if options.tags and not set(config.tags) & set(options.tags):
                    continue
                subagents[config.name] = config
        
        # Load from project level (overrides user level)
        if options.level == SubagentLevel.PROJECT:
            project_configs = await self._load_from_directory(
                self.project_subagents_dir,
                SubagentLevel.PROJECT
            )
            for config in project_configs:
                if options.enabled_only and not config.enabled:
                    continue
                if options.tags and not set(config.tags) & set(options.tags):
                    continue
                subagents[config.name] = config
        
        return list(subagents.values())
    
    async def get_subagent(self, name: str) -> SubagentConfig:
        """Get a specific subagent configuration.
        
        Args:
            name: Subagent name
            
        Returns:
            Subagent configuration
            
        Raises:
            SubagentNotFoundError: If subagent doesn't exist
        """
        # Check built-in first
        builtin = self.builtin_registry.get_builtin(name)
        if builtin:
            return builtin
        
        # Check project level
        project_config = await self._load_config(name, SubagentLevel.PROJECT)
        if project_config:
            return project_config
        
        # Check user level
        user_config = await self._load_config(name, SubagentLevel.USER)
        if user_config:
            return user_config
        
        raise SubagentNotFoundError(name)
    
    async def create_subagent(
        self,
        options: CreateSubagentOptions
    ) -> SubagentConfig:
        """Create a new subagent configuration.
        
        Args:
            options: Creation options
            
        Returns:
            Created subagent configuration
            
        Raises:
            SubagentAlreadyExistsError: If subagent already exists
            SubagentValidationError: If configuration is invalid
        """
        # Check if already exists
        try:
            existing = await self.get_subagent(options.name)
            if not options.overwrite:
                raise SubagentAlreadyExistsError(
                    options.name,
                    options.level.value
                )
        except SubagentNotFoundError:
            pass  # OK, doesn't exist
        
        # Build configuration
        config = SubagentConfig(
            name=options.name,
            description=options.description,
            prompt=PromptConfig(system=options.system_prompt),
            model=ModelConfig(name=options.model, provider=options.provider) if options.model else None,
            tools=ToolConfig(
                allow=options.allowed_tools,
                deny=options.denied_tools,
            ) if options.allowed_tools or options.denied_tools else None,
        )
        
        # Validate
        result = self.validator.validate_config(config)
        if not result.valid:
            raise SubagentValidationError(result.errors, result.warnings)
        
        # Save configuration
        await self._save_config(config, options.level)
        
        return config
    
    async def update_subagent(
        self,
        name: str,
        updates: Dict[str, Any],
        level: SubagentLevel = SubagentLevel.PROJECT
    ) -> SubagentConfig:
        """Update an existing subagent configuration.
        
        Args:
            name: Subagent name
            updates: Fields to update
            level: Storage level
            
        Returns:
            Updated subagent configuration
            
        Raises:
            SubagentNotFoundError: If subagent doesn't exist
        """
        # Load existing config
        config = await self.get_subagent(name)
        
        # Apply updates
        config_dict = config.model_dump()
        for key, value in updates.items():
            if key in config_dict:
                config_dict[key] = value
        
        # Validate updated config
        updated_config = SubagentConfig(**config_dict)
        result = self.validator.validate_config(updated_config)
        if not result.valid:
            raise SubagentValidationError(result.errors, result.warnings)
        
        # Save
        await self._save_config(updated_config, level)
        
        return updated_config
    
    async def delete_subagent(
        self,
        name: str,
        level: SubagentLevel = SubagentLevel.PROJECT
    ) -> None:
        """Delete a subagent configuration.
        
        Args:
            name: Subagent name
            level: Storage level
            
        Raises:
            SubagentNotFoundError: If subagent doesn't exist
        """
        file_path = self._get_config_path(name, level)
        
        if not file_path.exists():
            raise SubagentNotFoundError(name, level.value)
        
        try:
            file_path.unlink()
        except Exception as e:
            raise SubagentFileError(str(file_path), "delete", e)
    
    def get_runtime_config(
        self,
        config: SubagentConfig,
        default_provider: str = "openai",
        default_model: str = "gpt-4",
        available_tools: Optional[List[str]] = None,
    ) -> SubagentRuntimeConfig:
        """Convert a subagent config to runtime config.
        
        Args:
            config: Subagent configuration
            default_provider: Default provider to use
            default_model: Default model to use
            available_tools: List of all available tools
            
        Returns:
            Runtime configuration for execution
        """
        available_tools = available_tools or []
        
        # Resolve model settings
        model_provider = (config.model.provider if config.model and config.model.provider else default_provider) or default_provider
        model_name = (config.model.name if config.model and config.model.name else default_model) or default_model
        
        # Resolve tool settings
        allowed_tools = []
        denied_tools = []
        require_approval_tools = []
        auto_approve_tools = []
        
        if config.tools:
            if "*" in config.tools.allow:
                allowed_tools = available_tools.copy()
            else:
                allowed_tools = [t for t in config.tools.allow if t in available_tools]
            
            denied_tools = config.tools.deny
            require_approval_tools = config.tools.require_approval
            auto_approve_tools = config.tools.auto_approve
        
        # Build runtime config
        return SubagentRuntimeConfig(
            name=config.name,
            system_prompt=config.prompt.system or "",
            model_provider=model_provider,
            model_name=model_name,
            allowed_tools=allowed_tools,
            denied_tools=denied_tools,
            require_approval_tools=require_approval_tools,
            auto_approve_tools=auto_approve_tools,
            max_rounds=config.run.max_rounds,
            terminate_mode=config.run.terminate_mode,
            timeout=config.run.timeout,
        )
    
    async def _load_from_directory(
        self,
        directory: Path,
        level: SubagentLevel
    ) -> List[SubagentConfig]:
        """Load all subagent configurations from a directory."""
        configs = []
        
        if not directory.exists():
            return configs
        
        loop = asyncio.get_event_loop()
        
        for file_path in directory.glob("*.md"):
            try:
                config = await self._parse_markdown_file(file_path)
                if config:
                    configs.append(config)
            except Exception as e:
                logger.warning(f"Failed to load subagent from {file_path}: {e}")
        
        return configs
    
    async def _load_config(
        self,
        name: str,
        level: SubagentLevel
    ) -> Optional[SubagentConfig]:
        """Load a specific subagent configuration."""
        file_path = self._get_config_path(name, level)
        
        if not file_path.exists():
            return None
        
        return await self._parse_markdown_file(file_path)
    
    async def _parse_markdown_file(self, file_path: Path) -> Optional[SubagentConfig]:
        """Parse a markdown file with YAML frontmatter."""
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            raise SubagentFileError(str(file_path), "read", e)
        
        # Parse YAML frontmatter
        if not content.startswith("---"):
            return None
        
        parts = content.split("---", 2)
        if len(parts) < 3:
            return None
        
        frontmatter = parts[1].strip()
        
        try:
            config_dict = yaml.safe_load(frontmatter)
        except yaml.YAMLError as e:
            raise SubagentFileError(str(file_path), "parse", e)
        
        # Validate
        result = self.validator.validate(config_dict)
        if not result.valid:
            return None
        
        return result.config
    
    async def _save_config(
        self,
        config: SubagentConfig,
        level: SubagentLevel
    ) -> None:
        """Save a subagent configuration to a markdown file."""
        directory = self._get_storage_directory(level)
        file_path = self._get_config_path(config.name, level)
        
        # Ensure directory exists
        directory.mkdir(parents=True, exist_ok=True)
        
        # Build markdown content
        frontmatter = yaml.dump(
            config.model_dump(exclude_none=True),
            default_flow_style=False,
            sort_keys=False
        )
        
        content = f"---\n{frontmatter}---\n\n# {config.name}\n\n{config.description}\n"
        
        try:
            file_path.write_text(content, encoding="utf-8")
        except Exception as e:
            raise SubagentFileError(str(file_path), "write", e)
    
    def _get_storage_directory(self, level: SubagentLevel) -> Path:
        """Get the storage directory for a level."""
        if level == SubagentLevel.PROJECT:
            return self.project_subagents_dir
        elif level == SubagentLevel.USER:
            return self.user_subagents_dir
        else:
            raise ValueError(f"Invalid level for storage: {level}")
    
    def _get_config_path(self, name: str, level: SubagentLevel) -> Path:
        """Get the file path for a subagent configuration."""
        directory = self._get_storage_directory(level)
        return directory / f"{name}.md"
