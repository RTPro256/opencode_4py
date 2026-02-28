"""
Skills System Module

This module provides a skills system for the AI coding agent, inspired by mistral-vibe.
Skills allow custom slash commands and specialized behaviors.

Features:
- Skill discovery from .vibe/skills/ directory
- Skill parsing and execution
- Custom slash commands via skills
- SkillPointer architecture for large libraries (token optimization)
"""

from opencode.skills.manager import SkillManager
from opencode.skills.models import Skill, SkillConfig, SkillResult
from opencode.skills.discovery import SkillDiscovery
from opencode.skills.pointer import (
    SkillPointerManager,
    CategoryPointer,
    categorize_skill,
    get_categories,
    estimate_token_savings,
    is_pointer_skill,
    extract_category,
    SkillPointerConfig,
)

__all__ = [
    # Core
    "SkillManager",
    "Skill",
    "SkillConfig",
    "SkillResult",
    "SkillDiscovery",
    # SkillPointer
    "SkillPointerManager",
    "CategoryPointer",
    "categorize_skill",
    "get_categories",
    "estimate_token_savings",
    "is_pointer_skill",
    "extract_category",
    "SkillPointerConfig",
]
