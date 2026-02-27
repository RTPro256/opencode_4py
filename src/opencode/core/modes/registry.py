"""
Mode Registry

This module provides a registry for mode types.
"""

import logging
from typing import Dict, List, Optional, Type, Callable

from opencode.core.modes.base import Mode, ModeConfig

logger = logging.getLogger(__name__)


class ModeRegistry:
    """
    Registry for mode types.
    
    Provides a central place to register and retrieve modes.
    Modes can be registered using the @register decorator or
    the register() method.
    
    Example:
        @ModeRegistry.register()
        class CodeMode(Mode):
            ...
            
        # Retrieve a mode:
        mode_class = ModeRegistry.get("code")
    """
    
    _modes: Dict[str, Type[Mode]] = {}
    
    @classmethod
    def register(cls, name: Optional[str] = None) -> Callable[[Type[Mode]], Type[Mode]]:
        """
        Decorator to register a mode class.
        
        Args:
            name: Optional custom name for the mode.
                  If not provided, uses the mode's config name.
                  
        Returns:
            Decorator function
        """
        def decorator(mode_class: Type[Mode]) -> Type[Mode]:
            mode_name = name or mode_class.get_config().name
            cls.register_mode(mode_class, mode_name)
            return mode_class
        return decorator
    
    @classmethod
    def register_mode(cls, mode_class: Type[Mode], name: Optional[str] = None) -> None:
        """
        Register a mode class explicitly.
        
        Args:
            mode_class: The mode class to register
            name: Optional name for the mode. If not provided,
                  uses the mode's config name.
        """
        mode_name = name or mode_class.get_config().name
        
        if mode_name in cls._modes:
            logger.warning(f"Overwriting existing mode: {mode_name}")
        
        cls._modes[mode_name] = mode_class
        logger.debug(f"Registered mode: {mode_name}")
    
    @classmethod
    def get(cls, name: str) -> Optional[Type[Mode]]:
        """
        Get a mode class by name.
        
        Args:
            name: The registered name of the mode
            
        Returns:
            The mode class, or None if not found
        """
        return cls._modes.get(name)
    
    @classmethod
    def get_required(cls, name: str) -> Type[Mode]:
        """
        Get a mode class by name, raising an error if not found.
        
        Args:
            name: The registered name of the mode
            
        Returns:
            The mode class
            
        Raises:
            KeyError: If the mode is not registered
        """
        if name not in cls._modes:
            raise KeyError(f"Mode '{name}' is not registered. "
                          f"Available modes: {list(cls._modes.keys())}")
        return cls._modes[name]
    
    @classmethod
    def list_modes(cls) -> List[str]:
        """
        List all registered mode names.
        
        Returns:
            List of registered mode names
        """
        return list(cls._modes.keys())
    
    @classmethod
    def get_all_configs(cls) -> Dict[str, ModeConfig]:
        """
        Get configurations for all registered modes.
        
        Returns:
            Dictionary mapping mode names to their configurations
        """
        return {name: mode_class.get_config() for name, mode_class in cls._modes.items()}
    
    @classmethod
    def unregister(cls, name: str) -> bool:
        """
        Unregister a mode.
        
        Args:
            name: The name of the mode to unregister
            
        Returns:
            True if the mode was unregistered, False if it wasn't registered
        """
        if name in cls._modes:
            del cls._modes[name]
            return True
        return False
    
    @classmethod
    def clear(cls) -> None:
        """Clear all registered modes (useful for testing)."""
        cls._modes.clear()


class ModeRegistryError(Exception):
    """Raised when there's an error with the mode registry."""
    pass
