"""
Plugin manager for loading and managing plugins.

Refactored from compound-engineering-plugin patterns.
"""

import importlib
import importlib.util
from pathlib import Path
from typing import Any, Optional

from .base import Plugin, PluginRegistry, PluginState, PluginHook


class PluginManager:
    """
    Manager for plugin lifecycle.
    
    Handles discovery, loading, and management of plugins.
    """
    
    def __init__(self, plugin_dir: Optional[Path] = None):
        """
        Initialize the plugin manager.
        
        Args:
            plugin_dir: Directory to search for plugins
        """
        self._plugin_dir = plugin_dir
        self._registry = PluginRegistry()
    
    def discover_plugins(self, plugin_dir: Optional[Path] = None) -> list[str]:
        """
        Discover available plugins in a directory.
        
        Args:
            plugin_dir: Directory to search (uses instance dir if not provided)
            
        Returns:
            List of discovered plugin names
        """
        search_dir = plugin_dir or self._plugin_dir
        if not search_dir or not search_dir.exists():
            return []
        
        discovered = []
        for path in search_dir.iterdir():
            if path.is_dir():
                # Check for plugin.py or __init__.py
                plugin_file = path / "plugin.py"
                init_file = path / "__init__.py"
                
                if plugin_file.exists() or init_file.exists():
                    discovered.append(path.name)
            
            elif path.suffix == ".py" and not path.name.startswith("_"):
                discovered.append(path.stem)
        
        return discovered
    
    async def load_plugin(self, name: str, plugin_dir: Optional[Path] = None) -> bool:
        """
        Load a plugin by name.
        
        Args:
            name: Plugin name or module path
            plugin_dir: Directory containing the plugin
            
        Returns:
            True if loaded successfully
        """
        try:
            # Try to import as module first
            if "." in name:
                module = importlib.import_module(name)
            else:
                # Try to load from plugin directory
                search_dir = plugin_dir or self._plugin_dir
                if search_dir:
                    plugin_path = search_dir / name / "plugin.py"
                    if plugin_path.exists():
                        spec = importlib.util.spec_from_file_location(
                            f"plugins.{name}",
                            plugin_path,
                        )
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)
                        else:
                            return False
                    else:
                        # Try as installed package
                        module = importlib.import_module(f"plugins.{name}")
                else:
                    module = importlib.import_module(f"plugins.{name}")
            
            # Find Plugin subclass in module
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, Plugin)
                    and attr is not Plugin
                ):
                    plugin_class = attr
                    break
            
            if plugin_class is None:
                return False
            
            # Instantiate and register
            plugin = plugin_class()
            result = await plugin.load()
            
            if result.success:
                self._registry.register(plugin)
                return True
            
            return False
            
        except Exception as e:
            print(f"Error loading plugin {name}: {e}")
            return False
    
    async def enable_plugin(self, name: str) -> bool:
        """Enable a loaded plugin."""
        plugin = self._registry.get(name)
        if plugin is None:
            return False
        
        result = await plugin.enable()
        return result.success
    
    async def disable_plugin(self, name: str) -> bool:
        """Disable a plugin."""
        plugin = self._registry.get(name)
        if plugin is None:
            return False
        
        result = await plugin.disable()
        return result.success
    
    async def unload_plugin(self, name: str) -> bool:
        """Unload a plugin."""
        plugin = self._registry.get(name)
        if plugin is None:
            return False
        
        result = await plugin.unload()
        if result.success:
            self._registry.unregister(name)
            return True
        return False
    
    async def load_all(self, plugin_dir: Optional[Path] = None) -> dict[str, bool]:
        """
        Load all discovered plugins.
        
        Args:
            plugin_dir: Directory to search for plugins
            
        Returns:
            Dict mapping plugin names to load success
        """
        results = {}
        for name in self.discover_plugins(plugin_dir):
            results[name] = await self.load_plugin(name, plugin_dir)
        return results
    
    async def enable_all(self) -> dict[str, bool]:
        """Enable all loaded plugins."""
        results = {}
        for plugin_info in self._registry.list_plugins():
            name = plugin_info["name"]
            results[name] = await self.enable_plugin(name)
        return results
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get a plugin by name."""
        return self._registry.get(name)
    
    def list_plugins(self) -> list[dict[str, Any]]:
        """List all registered plugins."""
        return self._registry.list_plugins()
    
    async def execute_hook(
        self,
        hook: PluginHook,
        context: dict[str, Any],
    ) -> list[Any]:
        """
        Execute a hook for all enabled plugins.
        
        Args:
            hook: The hook to execute
            context: Context data for the hook
            
        Returns:
            List of results from plugins
        """
        return await self._registry.execute_hook(hook, context)
