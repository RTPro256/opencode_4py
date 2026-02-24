"""
Skills System Module

This module provides a skills system for the AI coding agent, inspired by mistral-vibe.
Skills allow custom slash commands and specialized behaviors.

Features:
- Skill discovery from .vibe/skills/ directory
- Skill parsing and execution
- Custom slash commands via skills
"""

from opencode.skills.manager import SkillManager
from opencode.skills.models import Skill, SkillConfig, SkillResult
from opencode.skills.discovery import SkillDiscovery

__all__ = [
    "SkillManager",
    "Skill",
    "SkillConfig",
    "SkillResult",
    "SkillDiscovery",
]
