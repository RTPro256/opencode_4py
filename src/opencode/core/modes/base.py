"""
Mode Base Classes

This module provides the base classes for the mode system.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, ClassVar
from pydantic import BaseModel, Field


class ModeToolAccess(str, Enum):
    """Tool access level for a mode."""
    ALL = "all"           # Access to all tools
    WHITELIST = "whitelist"  # Access only to whitelisted tools
    BLACKLIST = "blacklist"  # Access to all except blacklisted tools
    NONE = "none"         # No tool access


@dataclass
class ModeConfig:
    """
    Configuration for a mode.
    
    Defines the behavior, tool access, and prompts for a mode.
    """
    name: str
    description: str = ""
    tool_access: ModeToolAccess = ModeToolAccess.ALL
    allowed_tools: Set[str] = field(default_factory=set)
    blocked_tools: Set[str] = field(default_factory=set)
    system_prompt_prefix: str = ""
    system_prompt_suffix: str = ""
    custom_instructions: str = ""
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    supports_images: bool = True
    supports_streaming: bool = True
    rag_agents: List[str] = field(default_factory=list)  # RAG agents available to this mode
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "tool_access": self.tool_access.value,
            "allowed_tools": list(self.allowed_tools),
            "blocked_tools": list(self.blocked_tools),
            "system_prompt_prefix": self.system_prompt_prefix,
            "system_prompt_suffix": self.system_prompt_suffix,
            "custom_instructions": self.custom_instructions,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "supports_images": self.supports_images,
            "supports_streaming": self.supports_streaming,
            "rag_agents": self.rag_agents,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModeConfig":
        """Create from dictionary."""
        return cls(
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
            rag_agents=data.get("rag_agents", []),
        )


class Mode(ABC):
    """
    Abstract base class for modes.
    
    Modes define different behaviors and capabilities for the AI agent.
    Each mode has its own tool access rules, prompts, and settings.
    
    To implement a new mode:
    1. Subclass Mode
    2. Implement get_config() to define mode settings
    3. Optionally override get_system_prompt() for custom prompts
    4. Optionally override filter_tools() for custom tool filtering
    """
    
    # Class-level configuration
    _config: ClassVar[ModeConfig]
    
    @classmethod
    @abstractmethod
    def get_config(cls) -> ModeConfig:
        """
        Return the configuration for this mode.
        
        Returns:
            ModeConfig describing this mode
        """
        pass
    
    @classmethod
    def get_name(cls) -> str:
        """Get the mode name."""
        return cls.get_config().name
    
    @classmethod
    def get_description(cls) -> str:
        """Get the mode description."""
        return cls.get_config().description
    
    @classmethod
    def get_system_prompt(cls, base_prompt: str = "") -> str:
        """
        Generate the system prompt for this mode.
        
        Args:
            base_prompt: Base system prompt to build upon
            
        Returns:
            Complete system prompt for this mode
        """
        config = cls.get_config()
        
        parts = []
        
        if config.system_prompt_prefix:
            parts.append(config.system_prompt_prefix)
        
        if base_prompt:
            parts.append(base_prompt)
        
        if config.custom_instructions:
            parts.append(config.custom_instructions)
        
        if config.system_prompt_suffix:
            parts.append(config.system_prompt_suffix)
        
        return "\n\n".join(parts)
    
    @classmethod
    def filter_tools(cls, available_tools: Set[str]) -> Set[str]:
        """
        Filter available tools based on mode configuration.
        
        Args:
            available_tools: Set of all available tool names
            
        Returns:
            Set of tools allowed in this mode
        """
        config = cls.get_config()
        
        if config.tool_access == ModeToolAccess.ALL:
            return available_tools
        
        if config.tool_access == ModeToolAccess.NONE:
            return set()
        
        if config.tool_access == ModeToolAccess.WHITELIST:
            return available_tools & config.allowed_tools
        
        if config.tool_access == ModeToolAccess.BLACKLIST:
            return available_tools - config.blocked_tools
        
        return available_tools
    
    @classmethod
    def is_tool_allowed(cls, tool_name: str) -> bool:
        """
        Check if a specific tool is allowed in this mode.
        
        Args:
            tool_name: Name of the tool to check
            
        Returns:
            True if the tool is allowed
        """
        config = cls.get_config()
        
        if config.tool_access == ModeToolAccess.ALL:
            return True
        
        if config.tool_access == ModeToolAccess.NONE:
            return False
        
        if config.tool_access == ModeToolAccess.WHITELIST:
            return tool_name in config.allowed_tools
        
        if config.tool_access == ModeToolAccess.BLACKLIST:
            return tool_name not in config.blocked_tools
        
        return True
    
    @classmethod
    def get_model_settings(cls) -> Dict[str, Any]:
        """
        Get model settings for this mode.
        
        Returns:
            Dictionary of model settings
        """
        config = cls.get_config()
        settings = {}
        
        if config.max_tokens is not None:
            settings["max_tokens"] = config.max_tokens
        
        if config.temperature is not None:
            settings["temperature"] = config.temperature
        
        return settings
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
