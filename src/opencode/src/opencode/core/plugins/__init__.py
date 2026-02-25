"""
Plugins module for opencode_4py.

This module provides a plugin architecture inspired by compound-engineering-plugin.
Plugins extend the core functionality with additional features.
"""

from .base import Plugin, PluginRegistry, PluginResult, PluginHook
from .manager import PluginManager

__all__ = [
    "Plugin",
    "PluginRegistry",
    "PluginResult",
    "PluginHook",
    "PluginManager",
]
