"""
Base skill classes and registry for the skills system.

Refactored from:
- superpowers/skills/ pattern
- ai-factory/skills/ pattern
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional, TypeVar, Generic
import asyncio
from pathlib import Path


class SkillPriority(Enum):
    """Priority levels for skill execution."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class SkillPhase(Enum):
    """Phases in the skill lifecycle."""
    PREPARE = "prepare"
    EXECUTE = "execute"
    VERIFY = "verify"
    CLEANUP = "cleanup"


@dataclass
class SkillResult:
    """Result of a skill execution."""
    success: bool
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    
    def merge(self, other: "SkillResult") -> "SkillResult":
        """Merge another result into this one."""
        return SkillResult(
            success=self.success and other.success,
            message=f"{self.message}; {other.message}",
            data={**self.data, **other.data},
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings,
        )


@dataclass
class SkillContext:
    """Context passed to skill execution."""
    working_directory: Path
    project_root: Optional[Path] = None
    user_preferences: dict[str, Any] = field(default_factory=dict)
    environment: dict[str, str] = field(default_factory=dict)
    parent_context: Optional["SkillContext"] = None
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference value."""
        if key in self.user_preferences:
            return self.user_preferences[key]
        if self.parent_context:
            return self.parent_context.get_preference(key, default)
        return default


T = TypeVar("T")


class Skill(ABC, Generic[T]):
    """
    Abstract base class for all skills.
    
    Skills are reusable patterns for common development tasks.
    Inspired by superpowers and ai-factory projects.
    
    Attributes:
        name: Unique identifier for the skill
        description: Human-readable description
        priority: Execution priority
        tags: Categories this skill belongs to
    """
    
    name: str = "base_skill"
    description: str = "Base skill class"
    priority: SkillPriority = SkillPriority.MEDIUM
    tags: list[str] = []
    
    def __init__(self, context: Optional[SkillContext] = None):
        """Initialize the skill with optional context."""
        self._context = context
        self._hooks: dict[SkillPhase, list[Callable]] = {
            phase: [] for phase in SkillPhase
        }
    
    def add_hook(self, phase: SkillPhase, callback: Callable) -> None:
        """Add a callback for a specific phase."""
        self._hooks[phase].append(callback)
    
    async def _run_hooks(self, phase: SkillPhase, *args, **kwargs) -> None:
        """Run all hooks for a phase."""
        for callback in self._hooks[phase]:
            if asyncio.iscoroutinefunction(callback):
                await callback(*args, **kwargs)
            else:
                callback(*args, **kwargs)
    
    @abstractmethod
    async def execute(self, *args, **kwargs) -> SkillResult:
        """
        Execute the skill.
        
        Must be implemented by subclasses.
        
        Returns:
            SkillResult with execution outcome
        """
        pass
    
    @abstractmethod
    def validate(self, *args, **kwargs) -> tuple[bool, list[str]]:
        """
        Validate skill parameters before execution.
        
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        pass
    
    async def run(self, *args, **kwargs) -> SkillResult:
        """
        Run the skill with full lifecycle.
        
        Includes prepare, execute, verify, and cleanup phases.
        """
        # Validate
        is_valid, errors = self.validate(*args, **kwargs)
        if not is_valid:
            return SkillResult(
                success=False,
                message="Validation failed",
                errors=errors,
            )
        
        # Prepare phase
        await self._run_hooks(SkillPhase.PREPARE, *args, **kwargs)
        
        try:
            # Execute phase
            await self._run_hooks(SkillPhase.EXECUTE, *args, **kwargs)
            result = await self.execute(*args, **kwargs)
            
            # Verify phase
            await self._run_hooks(SkillPhase.VERIFY, result, *args, **kwargs)
            
            return result
            
        except Exception as e:
            return SkillResult(
                success=False,
                message=f"Skill execution failed: {e}",
                errors=[str(e)],
            )
        finally:
            # Cleanup phase
            await self._run_hooks(SkillPhase.CLEANUP, *args, **kwargs)
    
    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        """Get skill metadata."""
        return {
            "name": cls.name,
            "description": cls.description,
            "priority": cls.priority.value,
            "tags": cls.tags,
        }


class SkillRegistry:
    """
    Registry for managing available skills.
    
    Provides discovery, lookup, and execution of skills.
    """
    
    _instance: Optional["SkillRegistry"] = None
    _skills: dict[str, type[Skill]] = {}
    
    def __new__(cls) -> "SkillRegistry":
        """Singleton pattern for global registry."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def register(cls, skill_class: type[Skill]) -> type[Skill]:
        """
        Register a skill class.
        
        Can be used as a decorator:
            @SkillRegistry.register
            class MySkill(Skill):
                ...
        """
        cls._skills[skill_class.name] = skill_class
        return skill_class
    
    @classmethod
    def get(cls, name: str) -> Optional[type[Skill]]:
        """Get a skill class by name."""
        return cls._skills.get(name)
    
    @classmethod
    def list_skills(cls, tag: Optional[str] = None) -> list[dict[str, Any]]:
        """
        List all registered skills.
        
        Args:
            tag: Optional tag to filter by
            
        Returns:
            List of skill metadata dictionaries
        """
        skills = []
        for skill_class in cls._skills.values():
            if tag is None or tag in skill_class.tags:
                skills.append(skill_class.get_metadata())
        return skills
    
    @classmethod
    def create(cls, name: str, context: Optional[SkillContext] = None) -> Optional[Skill]:
        """Create an instance of a skill by name."""
        skill_class = cls.get(name)
        if skill_class:
            return skill_class(context)
        return None
    
    @classmethod
    def clear(cls) -> None:
        """Clear all registered skills (for testing)."""
        cls._skills.clear()
