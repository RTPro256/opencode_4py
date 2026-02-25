"""
Mode Manager

This module provides the mode manager for handling mode switching and state.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Type

import yaml

from opencode.core.modes.base import Mode, ModeConfig, ModeToolAccess
from opencode.core.modes.registry import ModeRegistry

logger = logging.getLogger(__name__)


class ModeManager:
    """
    Manager for mode system.
    
    Handles mode switching, custom mode loading, and state management.
    
    Example:
        manager = ModeManager()
        manager.set_mode("code")
        
        # Get current mode
        current = manager.get_current_mode()
        
        # Check if tool is allowed
        if current.is_tool_allowed("write_file"):
            ...
    """
    
    def __init__(
        self,
        default_mode: str = "code",
        custom_modes_dir: Optional[Path] = None,
    ):
        """
        Initialize the mode manager.
        
        Args:
            default_mode: Default mode to use
            custom_modes_dir: Directory containing custom mode definitions
        """
        self._current_mode: str = default_mode
        self._custom_modes_dir = custom_modes_dir
        self._mode_history: List[str] = []
        
        # Load custom modes if directory provided
        if custom_modes_dir and custom_modes_dir.exists():
            self._load_custom_modes(custom_modes_dir)
    
    def get_current_mode_name(self) -> str:
        """Get the name of the current mode."""
        return self._current_mode
    
    def get_current_mode(self) -> Type[Mode]:
        """Get the current mode class."""
        return ModeRegistry.get_required(self._current_mode)
    
    def get_current_config(self) -> ModeConfig:
        """Get the configuration for the current mode."""
        return self.get_current_mode().get_config()
    
    def set_mode(self, mode_name: str) -> bool:
        """
        Switch to a different mode.
        
        Args:
            mode_name: Name of the mode to switch to
            
        Returns:
            True if the mode was switched successfully
        """
        if mode_name not in ModeRegistry.list_modes():
            logger.warning(f"Unknown mode: {mode_name}")
            return False
        
        # Add current mode to history
        self._mode_history.append(self._current_mode)
        
        # Keep history limited
        if len(self._mode_history) > 10:
            self._mode_history = self._mode_history[-10:]
        
        self._current_mode = mode_name
        logger.info(f"Switched to mode: {mode_name}")
        return True
    
    def get_previous_mode(self) -> Optional[str]:
        """Get the name of the previous mode."""
        if self._mode_history:
            return self._mode_history[-1]
        return None
    
    def restore_previous_mode(self) -> bool:
        """Restore the previous mode."""
        previous = self.get_previous_mode()
        if previous:
            self._mode_history.pop()
            self._current_mode = previous
            logger.info(f"Restored mode: {previous}")
            return True
        return False
    
    def list_modes(self) -> List[str]:
        """List all available modes."""
        return ModeRegistry.list_modes()
    
    def get_mode_config(self, mode_name: str) -> Optional[ModeConfig]:
        """Get the configuration for a mode."""
        mode_class = ModeRegistry.get(mode_name)
        if mode_class:
            return mode_class.get_config()
        return None
    
    def is_tool_allowed(self, tool_name: str, mode_name: Optional[str] = None) -> bool:
        """
        Check if a tool is allowed in the specified mode.
        
        Args:
            tool_name: Name of the tool to check
            mode_name: Mode to check (uses current mode if not specified)
            
        Returns:
            True if the tool is allowed
        """
        mode = mode_name or self._current_mode
        mode_class = ModeRegistry.get(mode)
        if mode_class:
            return mode_class.is_tool_allowed(tool_name)
        return True
    
    def filter_tools(
        self,
        tools: Set[str],
        mode_name: Optional[str] = None,
    ) -> Set[str]:
        """
        Filter tools based on mode configuration.
        
        Args:
            tools: Set of tool names to filter
            mode_name: Mode to use (uses current mode if not specified)
            
        Returns:
            Set of allowed tools
        """
        mode = mode_name or self._current_mode
        mode_class = ModeRegistry.get(mode)
        if mode_class:
            return mode_class.filter_tools(tools)
        return tools
    
    def _load_custom_modes(self, directory: Path) -> None:
        """
        Load custom modes from a directory.
        
        Args:
            directory: Directory containing YAML mode definitions
        """
        if not directory.exists():
            return
        
        for file_path in directory.glob("*.yaml"):
            try:
                self._load_custom_mode(file_path)
            except Exception as e:
                logger.warning(f"Failed to load custom mode from {file_path}: {e}")
        
        for file_path in directory.glob("*.yml"):
            try:
                self._load_custom_mode(file_path)
            except Exception as e:
                logger.warning(f"Failed to load custom mode from {file_path}: {e}")
    
    def _load_custom_mode(self, file_path: Path) -> None:
        """
        Load a custom mode from a YAML file.
        
        Args:
            file_path: Path to the YAML file
        """
        with open(file_path, "r") as f:
            data = yaml.safe_load(f)
        
        if not data or "name" not in data:
            logger.warning(f"Invalid mode definition in {file_path}")
            return
        
        # Create a custom mode class
        config = ModeConfig(
            name=data["name"],
            description=data.get("description", ""),
            tool_access=ModeToolAccess(data.get("tool_access", "all")),
            allowed_tools=set(data.get("allowed_tools", [])),
            blocked_tools=set(data.get("blocked_tools", [])),
            system_prompt_prefix=data.get("system_prompt_prefix", ""),
            system_prompt_suffix=data.get("system_prompt_suffix", ""),
            custom_instructions=data.get("custom_instructions", ""),
            max_tokens=data.get("max_tokens"),
            temperature=data.get("temperature"),
            supports_images=data.get("supports_images", True),
            supports_streaming=data.get("supports_streaming", True),
        )
        
        # Create a dynamic mode class
        class CustomMode(Mode):
            _config = config
            
            @classmethod
            def get_config(cls) -> ModeConfig:
                return cls._config
        
        CustomMode.__name__ = f"{config.name.title().replace('_', '')}Mode"
        
        # Register the custom mode
        ModeRegistry.register_mode(CustomMode, config.name)
        logger.info(f"Loaded custom mode: {config.name}")
    
    def create_custom_mode(
        self,
        name: str,
        config: ModeConfig,
        save: bool = False,
    ) -> Type[Mode]:
        """
        Create a new custom mode.
        
        Args:
            name: Name for the mode
            config: Configuration for the mode
            save: Whether to save to custom modes directory
            
        Returns:
            The created mode class
        """
        # Create a dynamic mode class
        class CustomMode(Mode):
            _config = config
            
            @classmethod
            def get_config(cls) -> ModeConfig:
                return cls._config
        
        CustomMode.__name__ = f"{name.title().replace('_', '')}Mode"
        
        # Register the mode
        ModeRegistry.register_mode(CustomMode, name)
        
        # Save to file if requested
        if save and self._custom_modes_dir:
            self._save_custom_mode(name, config)
        
        return CustomMode
    
    def _save_custom_mode(self, name: str, config: ModeConfig) -> None:
        """
        Save a custom mode to a YAML file.
        
        Args:
            name: Name of the mode
            config: Configuration to save
        """
        if not self._custom_modes_dir:
            return
        
        self._custom_modes_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = self._custom_modes_dir / f"{name}.yaml"
        
        data = {
            "name": config.name,
            "description": config.description,
            "tool_access": config.tool_access.value,
            "allowed_tools": list(config.allowed_tools),
            "blocked_tools": list(config.blocked_tools),
            "system_prompt_prefix": config.system_prompt_prefix,
            "system_prompt_suffix": config.system_prompt_suffix,
            "custom_instructions": config.custom_instructions,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "supports_images": config.supports_images,
            "supports_streaming": config.supports_streaming,
        }
        
        with open(file_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)
        
        logger.info(f"Saved custom mode to {file_path}")
