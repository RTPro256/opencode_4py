"""
Skills module for opencode_4py.

This module provides a skill system inspired by superpowers and ai-factory projects.
Skills are reusable patterns for common development tasks.
"""

from .base import Skill, SkillRegistry, SkillResult
from .tdd import TDDSkill
from .debugging import DebuggingSkill
from .planning import PlanningSkill

__all__ = [
    "Skill",
    "SkillRegistry",
    "SkillResult",
    "TDDSkill",
    "DebuggingSkill",
    "PlanningSkill",
]
