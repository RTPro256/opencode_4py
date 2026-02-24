"""
Mode System Module

This module provides a mode system for the AI coding agent, inspired by Roo-Code.
Modes allow different behaviors, tool access, and prompts based on the task at hand.

Available Modes:
- Code Mode: Everyday coding, edits, file operations
- Architect Mode: Planning, specs, migrations
- Ask Mode: Fast answers, explanations
- Debug Mode: Issue tracing, logging, root cause analysis
- Custom Modes: User-defined specialized modes
"""

from opencode.core.modes.base import Mode, ModeConfig
from opencode.core.modes.manager import ModeManager
from opencode.core.modes.registry import ModeRegistry

__all__ = [
    "Mode",
    "ModeConfig",
    "ModeManager",
    "ModeRegistry",
]
