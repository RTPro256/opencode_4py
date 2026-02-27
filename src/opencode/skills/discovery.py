"""
Skill Discovery

Discovers and loads skills from directories.
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from opencode.skills.models import Skill, SkillConfig, SkillType, SkillStatus

logger = logging.getLogger(__name__)


class SkillDiscovery:
    """
    Discovers and loads skills from directories.
    
    Skills can be defined in:
    - YAML files (.yaml, .yml)
    - Python files (.py) with skill decorators
    - Markdown files (.md) with frontmatter
    
    Example directory structure:
        .vibe/skills/
        ├── test.yaml
        ├── review.yaml
        └── custom.py
    """
    
    # Default skill directories to search
    DEFAULT_DIRS = [
        ".vibe/skills",
        ".opencode/skills",
        "~/.opencode/skills",
    ]
    
    def __init__(
        self,
        skill_dirs: Optional[List[Path]] = None,
        auto_reload: bool = False,
    ):
        """
        Initialize skill discovery.
        
        Args:
            skill_dirs: List of directories to search for skills
            auto_reload: Whether to watch for changes
        """
        self._skill_dirs = skill_dirs or []
        self._auto_reload = auto_reload
        self._skills: Dict[str, Skill] = {}
        self._loaded = False
    
    def add_directory(self, directory: Path) -> None:
        """Add a directory to search for skills."""
        if directory not in self._skill_dirs:
            self._skill_dirs.append(directory)
    
    def discover_all(self) -> Dict[str, Skill]:
        """
        Discover all skills from configured directories.
        
        Returns:
            Dictionary mapping skill names to Skill objects
        """
        self._skills.clear()
        
        # Add default directories
        for dir_path in self.DEFAULT_DIRS:
            path = Path(dir_path).expanduser()
            if path.exists() and path not in self._skill_dirs:
                self._skill_dirs.append(path)
        
        # Discover from each directory
        for directory in self._skill_dirs:
            if directory.exists():
                self._discover_from_directory(directory)
        
        self._loaded = True
        return self._skills
    
    def _discover_from_directory(self, directory: Path) -> None:
        """
        Discover skills from a specific directory.
        
        Args:
            directory: Directory to search
        """
        # YAML files
        for file_path in directory.glob("*.yaml"):
            self._load_yaml_skill(file_path)
        
        for file_path in directory.glob("*.yml"):
            self._load_yaml_skill(file_path)
        
        # Python files
        for file_path in directory.glob("*.py"):
            self._load_python_skills(file_path)
        
        # Markdown files
        for file_path in directory.glob("*.md"):
            self._load_markdown_skill(file_path)
    
    def _load_yaml_skill(self, file_path: Path) -> Optional[Skill]:
        """
        Load a skill from a YAML file.
        
        Args:
            file_path: Path to the YAML file
            
        Returns:
            Loaded Skill or None if failed
        """
        try:
            with open(file_path, "r") as f:
                data = yaml.safe_load(f)
            
            if not data or "name" not in data:
                logger.warning(f"Invalid skill file: {file_path}")
                return None
            
            config = SkillConfig(
                name=data["name"],
                description=data.get("description", ""),
                skill_type=SkillType(data.get("type", "prompt")),
                trigger=data.get("trigger", ""),
                template=data.get("template", ""),
                function_name=data.get("function_name", ""),
                workflow_id=data.get("workflow_id", ""),
                chain=data.get("chain", []),
                parameters=data.get("parameters", {}),
                requires_confirmation=data.get("requires_confirmation", False),
                timeout_seconds=data.get("timeout_seconds", 60.0),
            )
            
            skill = Skill(
                config=config,
                source_path=file_path,
                status=SkillStatus.ENABLED,
            )
            
            self._skills[config.name] = skill
            logger.debug(f"Loaded skill: {config.name} from {file_path}")
            return skill
            
        except Exception as e:
            logger.warning(f"Failed to load skill from {file_path}: {e}")
            return None
    
    def _load_python_skills(self, file_path: Path) -> List[Skill]:
        """
        Load skills from a Python file.
        
        Looks for functions decorated with @skill decorator.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            List of loaded Skills
        """
        skills = []
        
        try:
            # Import the module
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                f"skill_{file_path.stem}",
                file_path,
            )
            
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find skill functions
                for name in dir(module):
                    obj = getattr(module, name)
                    
                    if callable(obj) and hasattr(obj, "_skill_config"):
                        config = obj._skill_config
                        skill = Skill(
                            config=config,
                            source_path=file_path,
                            status=SkillStatus.ENABLED,
                            _executor=obj,
                        )
                        self._skills[config.name] = skill
                        skills.append(skill)
                        logger.debug(f"Loaded Python skill: {config.name}")
                        
        except Exception as e:
            logger.warning(f"Failed to load Python skills from {file_path}: {e}")
        
        return skills
    
    def _load_markdown_skill(self, file_path: Path) -> Optional[Skill]:
        """
        Load a skill from a Markdown file with frontmatter.
        
        Args:
            file_path: Path to the Markdown file
            
        Returns:
            Loaded Skill or None if failed
        """
        try:
            with open(file_path, "r") as f:
                content = f.read()
            
            # Parse frontmatter
            if not content.startswith("---"):
                return None
            
            # Find end of frontmatter
            end_match = content.find("---", 3)
            if end_match == -1:
                return None
            
            frontmatter = content[3:end_match].strip()
            template = content[end_match + 3:].strip()
            
            # Parse YAML frontmatter
            data = yaml.safe_load(frontmatter)
            
            if not data or "name" not in data:
                return None
            
            config = SkillConfig(
                name=data["name"],
                description=data.get("description", ""),
                skill_type=SkillType.PROMPT,
                trigger=data.get("trigger", ""),
                template=template,
                parameters=data.get("parameters", {}),
            )
            
            skill = Skill(
                config=config,
                source_path=file_path,
                status=SkillStatus.ENABLED,
            )
            
            self._skills[config.name] = skill
            logger.debug(f"Loaded Markdown skill: {config.name}")
            return skill
            
        except Exception as e:
            logger.warning(f"Failed to load Markdown skill from {file_path}: {e}")
            return None
    
    def get_skill(self, name: str) -> Optional[Skill]:
        """
        Get a skill by name.
        
        Args:
            name: Name of the skill
            
        Returns:
            Skill or None if not found
        """
        if not self._loaded:
            self.discover_all()
        return self._skills.get(name)
    
    def get_skill_by_trigger(self, trigger: str) -> Optional[Skill]:
        """
        Get a skill by its trigger (slash command).
        
        Args:
            trigger: The slash command trigger (e.g., "/test")
            
        Returns:
            Skill or None if not found
        """
        if not self._loaded:
            self.discover_all()
        
        for skill in self._skills.values():
            if skill.trigger == trigger:
                return skill
        
        return None
    
    def list_skills(self) -> List[str]:
        """List all discovered skill names."""
        if not self._loaded:
            self.discover_all()
        return list(self._skills.keys())
    
    def get_all_skills(self) -> Dict[str, Skill]:
        """Get all discovered skills."""
        if not self._loaded:
            self.discover_all()
        return self._skills
    
    def reload(self) -> Dict[str, Skill]:
        """Reload all skills from directories."""
        self._loaded = False
        return self.discover_all()


def skill(
    name: str,
    description: str = "",
    trigger: str = "",
    requires_confirmation: bool = False,
    **kwargs,
):
    """
    Decorator to define a skill from a Python function.
    
    Args:
        name: Name of the skill
        description: Description of what the skill does
        trigger: Slash command trigger
        requires_confirmation: Whether execution requires confirmation
        **kwargs: Additional configuration options
        
    Returns:
        Decorator function
    
    Example:
        @skill("test", "Run tests", "/test")
        async def run_tests(context):
            return SkillResult(output="Tests passed!")
    """
    def decorator(func):
        config = SkillConfig(
            name=name,
            description=description,
            skill_type=SkillType.FUNCTION,
            trigger=trigger or f"/{name}",
            function_name=func.__name__,
            requires_confirmation=requires_confirmation,
            **kwargs,
        )
        func._skill_config = config
        return func
    
    return decorator
