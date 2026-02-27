"""
Base plugin classes and registry.

Refactored from compound-engineering-plugin patterns.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional, TypeVar
from pathlib import Path


class PluginState(Enum):
    """State of a plugin."""
    UNLOADED = "unloaded"
    LOADED = "loaded"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


class PluginHook(Enum):
    """Hook points for plugin execution."""
    PRE_COMMAND = "pre_command"
    POST_COMMAND = "post_command"
    PRE_TOOL = "pre_tool"
    POST_TOOL = "post_tool"
    PRE_AGENT = "pre_agent"
    POST_AGENT = "post_agent"
    ON_ERROR = "on_error"
    ON_STARTUP = "on_startup"
    ON_SHUTDOWN = "on_shutdown"


@dataclass
class PluginResult:
    """Result of a plugin hook execution."""
    success: bool
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    should_continue: bool = True  # False to stop chain


@dataclass
class PluginMetadata:
    """Metadata for a plugin."""
    name: str
    version: str
    description: str
    author: Optional[str] = None
    homepage: Optional[str] = None
    dependencies: list[str] = field(default_factory=list)
    hooks: list[PluginHook] = field(default_factory=list)


class Plugin(ABC):
    """
    Abstract base class for plugins.
    
    Plugins extend the core functionality with additional features.
    Inspired by compound-engineering-plugin architecture.
    
    Attributes:
        metadata: Plugin metadata
        state: Current plugin state
    """
    
    def __init__(self):
        """Initialize the plugin."""
        self._state = PluginState.UNLOADED
        self._hooks: dict[PluginHook, Callable] = {}
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        pass
    
    @property
    def state(self) -> PluginState:
        """Get current plugin state."""
        return self._state
    
    def register_hook(self, hook: PluginHook, callback: Callable) -> None:
        """Register a callback for a hook."""
        self._hooks[hook] = callback
    
    def get_hook(self, hook: PluginHook) -> Optional[Callable]:
        """Get the callback for a hook."""
        return self._hooks.get(hook)
    
    async def load(self) -> PluginResult:
        """
        Load the plugin.
        
        Override to perform initialization tasks.
        """
        self._state = PluginState.LOADED
        return PluginResult(
            success=True,
            message=f"Plugin {self.metadata.name} loaded",
        )
    
    async def enable(self) -> PluginResult:
        """
        Enable the plugin.
        
        Override to activate plugin functionality.
        """
        self._state = PluginState.ENABLED
        return PluginResult(
            success=True,
            message=f"Plugin {self.metadata.name} enabled",
        )
    
    async def disable(self) -> PluginResult:
        """
        Disable the plugin.
        
        Override to deactivate plugin functionality.
        """
        self._state = PluginState.DISABLED
        return PluginResult(
            success=True,
            message=f"Plugin {self.metadata.name} disabled",
        )
    
    async def unload(self) -> PluginResult:
        """
        Unload the plugin.
        
        Override to perform cleanup tasks.
        """
        self._state = PluginState.UNLOADED
        return PluginResult(
            success=True,
            message=f"Plugin {self.metadata.name} unloaded",
        )
    
    async def execute_hook(
        self,
        hook: PluginHook,
        context: dict[str, Any],
    ) -> PluginResult:
        """
        Execute a hook callback.
        
        Args:
            hook: The hook to execute
            context: Context data for the hook
            
        Returns:
            PluginResult from the hook execution
        """
        callback = self._hooks.get(hook)
        if callback is None:
            return PluginResult(
                success=True,
                message=f"No hook registered for {hook.value}",
            )
        
        try:
            import asyncio
            if asyncio.iscoroutinefunction(callback):
                result = await callback(context)
            else:
                result = callback(context)
            
            if isinstance(result, PluginResult):
                return result
            
            return PluginResult(
                success=True,
                message="Hook executed successfully",
                data=result if isinstance(result, dict) else {},
            )
        except Exception as e:
            self._state = PluginState.ERROR
            return PluginResult(
                success=False,
                message=f"Hook execution failed: {e}",
                should_continue=False,
            )


class PluginRegistry:
    """
    Registry for managing plugins.
    """
    
    _instance: Optional["PluginRegistry"] = None
    _plugins: dict[str, Plugin] = {}
    _hook_subscribers: dict[PluginHook, list[str]] = {
        hook: [] for hook in PluginHook
    }
    
    def __new__(cls) -> "PluginRegistry":
        """Singleton pattern for global registry."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def register(cls, plugin: Plugin) -> None:
        """Register a plugin."""
        name = plugin.metadata.name
        cls._plugins[name] = plugin
        
        # Register hook subscriptions
        for hook in plugin.metadata.hooks:
            if name not in cls._hook_subscribers[hook]:
                cls._hook_subscribers[hook].append(name)
    
    @classmethod
    def unregister(cls, name: str) -> None:
        """Unregister a plugin."""
        if name in cls._plugins:
            plugin = cls._plugins[name]
            for hook in plugin.metadata.hooks:
                if name in cls._hook_subscribers[hook]:
                    cls._hook_subscribers[hook].remove(name)
            del cls._plugins[name]
    
    @classmethod
    def get(cls, name: str) -> Optional[Plugin]:
        """Get a plugin by name."""
        return cls._plugins.get(name)
    
    @classmethod
    def list_plugins(cls) -> list[dict[str, Any]]:
        """List all registered plugins."""
        return [
            {
                "name": p.metadata.name,
                "version": p.metadata.version,
                "description": p.metadata.description,
                "state": p.state.value,
            }
            for p in cls._plugins.values()
        ]
    
    @classmethod
    def get_plugins_for_hook(cls, hook: PluginHook) -> list[Plugin]:
        """Get all plugins subscribed to a hook."""
        return [
            cls._plugins[name]
            for name in cls._hook_subscribers[hook]
            if name in cls._plugins
        ]
    
    @classmethod
    async def execute_hook(
        cls,
        hook: PluginHook,
        context: dict[str, Any],
    ) -> list[PluginResult]:
        """
        Execute a hook for all subscribed plugins.
        
        Args:
            hook: The hook to execute
            context: Context data for the hook
            
        Returns:
            List of PluginResult from all plugins
        """
        results = []
        for plugin in cls.get_plugins_for_hook(hook):
            if plugin.state == PluginState.ENABLED:
                result = await plugin.execute_hook(hook, context)
                results.append(result)
                if not result.should_continue:
                    break
        return results
    
    @classmethod
    def clear(cls) -> None:
        """Clear all registered plugins (for testing)."""
        cls._plugins.clear()
        for hook in PluginHook:
            cls._hook_subscribers[hook] = []
