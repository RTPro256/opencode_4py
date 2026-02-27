"""
Skill Models

Data models for the skills system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from pydantic import BaseModel, Field


class SkillType(str, Enum):
    """Type of skill."""
    PROMPT = "prompt"      # Simple prompt template
    FUNCTION = "function"  # Python function execution
    WORKFLOW = "workflow"  # Workflow execution
    CHAIN = "chain"        # Chain of multiple skills


class SkillStatus(str, Enum):
    """Status of a skill."""
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


@dataclass
class SkillConfig:
    """
    Configuration for a skill.
    
    Defines how the skill behaves and what it does.
    """
    name: str
    description: str = ""
    skill_type: SkillType = SkillType.PROMPT
    trigger: str = ""  # Slash command trigger (e.g., "/test")
    template: str = ""  # Prompt template for prompt skills
    function_name: str = ""  # Function name for function skills
    workflow_id: str = ""  # Workflow ID for workflow skills
    chain: List[str] = field(default_factory=list)  # Skill names for chain skills
    parameters: Dict[str, Any] = field(default_factory=dict)
    requires_confirmation: bool = False
    timeout_seconds: float = 60.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "skill_type": self.skill_type.value,
            "trigger": self.trigger,
            "template": self.template,
            "function_name": self.function_name,
            "workflow_id": self.workflow_id,
            "chain": self.chain,
            "parameters": self.parameters,
            "requires_confirmation": self.requires_confirmation,
            "timeout_seconds": self.timeout_seconds,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillConfig":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            skill_type=SkillType(data.get("skill_type", "prompt")),
            trigger=data.get("trigger", ""),
            template=data.get("template", ""),
            function_name=data.get("function_name", ""),
            workflow_id=data.get("workflow_id", ""),
            chain=data.get("chain", []),
            parameters=data.get("parameters", {}),
            requires_confirmation=data.get("requires_confirmation", False),
            timeout_seconds=data.get("timeout_seconds", 60.0),
        )


@dataclass
class Skill:
    """
    A skill that can be executed via slash commands.
    
    Skills are custom commands that can perform various actions
    like generating prompts, executing functions, or running workflows.
    """
    config: SkillConfig
    source_path: Optional[Path] = None
    status: SkillStatus = SkillStatus.ENABLED
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = None
    use_count: int = 0
    error_message: Optional[str] = None
    _executor: Optional[Callable] = None
    
    @property
    def name(self) -> str:
        """Get the skill name."""
        return self.config.name
    
    @property
    def trigger(self) -> str:
        """Get the slash command trigger."""
        return self.config.trigger or f"/{self.config.name}"
    
    @property
    def description(self) -> str:
        """Get the skill description."""
        return self.config.description
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "config": self.config.to_dict(),
            "source_path": str(self.source_path) if self.source_path else None,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "use_count": self.use_count,
            "error_message": self.error_message,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Skill":
        """Create from dictionary."""
        return cls(
            config=SkillConfig.from_dict(data["config"]),
            source_path=Path(data["source_path"]) if data.get("source_path") else None,
            status=SkillStatus(data.get("status", "enabled")),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.utcnow(),
            last_used_at=datetime.fromisoformat(data["last_used_at"]) if data.get("last_used_at") else None,
            use_count=data.get("use_count", 0),
            error_message=data.get("error_message"),
        )


@dataclass
class SkillResult:
    """
    Result of a skill execution.
    
    Contains the output and metadata about the execution.
    """
    success: bool = True
    output: str = ""
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    duration_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "output": self.output,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
            "duration_ms": self.duration_ms,
        }


@dataclass
class SkillExecutionContext:
    """
    Context provided to skills during execution.
    
    Contains information about the current state and utilities.
    """
    skill_name: str
    arguments: str  # Raw arguments after the slash command
    parsed_args: Dict[str, Any] = field(default_factory=dict)
    working_directory: Path = field(default_factory=Path.cwd)
    variables: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "skill_name": self.skill_name,
            "arguments": self.arguments,
            "parsed_args": self.parsed_args,
            "working_directory": str(self.working_directory),
            "variables": self.variables,
            "session_id": self.session_id,
            "user_id": self.user_id,
        }
