"""
Data models for calibration system.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any
from datetime import datetime


class CalibrationObjective(Enum):
    """Calibration objective types."""
    SPEED = "speed"
    QUALITY = "quality"
    BALANCED = "balanced"
    COST = "cost"


class CalibrationStatus(Enum):
    """Calibration status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PromptSuiteEntry:
    """A single prompt in a calibration suite."""
    prompt: str
    task: str = "general"
    expected_output: Optional[str] = None
    quality_check: Optional[dict] = None  # Regex patterns, keywords, etc.
    timeout_seconds: int = 120
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "prompt": self.prompt,
            "task": self.task,
            "expected_output": self.expected_output,
            "quality_check": self.quality_check,
            "timeout_seconds": self.timeout_seconds,
        }


@dataclass
class CalibrationRun:
    """Result of a single calibration run."""
    model: str
    prompt: str
    task: str
    response: str = ""
    tokens_per_second: float = 0.0
    total_time_seconds: float = 0.0
    prompt_eval_time: float = 0.0
    eval_time: float = 0.0
    tokens_generated: int = 0
    quality_score: float = 0.0
    quality_passed: bool = True
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "model": self.model,
            "prompt": self.prompt[:100] + "..." if len(self.prompt) > 100 else self.prompt,
            "task": self.task,
            "tokens_per_second": round(self.tokens_per_second, 2),
            "total_time_seconds": round(self.total_time_seconds, 3),
            "tokens_generated": self.tokens_generated,
            "quality_score": round(self.quality_score, 2),
            "quality_passed": self.quality_passed,
            "error": self.error,
        }


@dataclass
class ModelCalibrationResult:
    """Calibration results for a single model."""
    model: str
    runs: list[CalibrationRun] = field(default_factory=list)
    avg_tokens_per_second: float = 0.0
    avg_quality_score: float = 0.0
    avg_total_time: float = 0.0
    success_rate: float = 0.0
    overall_score: float = 0.0
    
    def calculate_aggregates(self) -> None:
        """Calculate aggregate statistics from runs."""
        if not self.runs:
            return
        
        successful_runs = [r for r in self.runs if r.error is None]
        
        if successful_runs:
            self.avg_tokens_per_second = sum(
                r.tokens_per_second for r in successful_runs
            ) / len(successful_runs)
            self.avg_quality_score = sum(
                r.quality_score for r in successful_runs
            ) / len(successful_runs)
            self.avg_total_time = sum(
                r.total_time_seconds for r in successful_runs
            ) / len(successful_runs)
        
        self.success_rate = len(successful_runs) / len(self.runs)
        
        # Overall score combines speed and quality
        self.overall_score = (
            self.avg_tokens_per_second * 0.4 +
            self.avg_quality_score * 0.4 +
            self.success_rate * 100 * 0.2
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "model": self.model,
            "runs": len(self.runs),
            "avg_tokens_per_second": round(self.avg_tokens_per_second, 2),
            "avg_quality_score": round(self.avg_quality_score, 2),
            "avg_total_time": round(self.avg_total_time, 3),
            "success_rate": round(self.success_rate, 2),
            "overall_score": round(self.overall_score, 2),
        }


@dataclass
class CalibrationResult:
    """Complete calibration result."""
    id: str = ""
    objective: CalibrationObjective = CalibrationObjective.BALANCED
    models: list[str] = field(default_factory=list)
    model_results: list[ModelCalibrationResult] = field(default_factory=list)
    best_model: str = ""
    created_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    status: CalibrationStatus = CalibrationStatus.PENDING
    hardware_info: dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Set defaults."""
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def determine_best_model(self) -> str:
        """Determine the best model based on objective."""
        if not self.model_results:
            return ""
        
        # Sort by overall score
        sorted_results = sorted(
            self.model_results,
            key=lambda r: r.overall_score,
            reverse=True
        )
        
        if sorted_results:
            self.best_model = sorted_results[0].model
        
        return self.best_model
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "objective": self.objective.value,
            "models": self.models,
            "model_results": [r.to_dict() for r in self.model_results],
            "best_model": self.best_model,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "duration_seconds": round(self.duration_seconds, 2),
            "status": self.status.value,
            "hardware_info": self.hardware_info,
        }


@dataclass
class RoutingRule:
    """A routing rule in a calibration policy."""
    task: str
    model: str
    priority: int = 0
    conditions: dict = field(default_factory=dict)
    
    def matches(self, task: str, **kwargs) -> bool:
        """Check if this rule matches the given criteria."""
        if self.task != "*" and self.task.lower() != task.lower():
            return False
        
        # Check additional conditions
        for key, value in self.conditions.items():
            if key in kwargs:
                if isinstance(value, list):
                    if kwargs[key] not in value:
                        return False
                elif kwargs[key] != value:
                    return False
        
        return True
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "task": self.task,
            "model": self.model,
            "priority": self.priority,
            "conditions": self.conditions,
        }


@dataclass
class CalibrationPolicy:
    """Routing policy generated from calibration."""
    version: str = "1.0"
    name: str = "default"
    description: str = ""
    created_at: Optional[datetime] = None
    calibration_id: str = ""
    default_model: str = ""
    rules: list[RoutingRule] = field(default_factory=list)
    fallback_model: str = ""
    
    def __post_init__(self):
        """Set defaults."""
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def get_model_for_task(self, task: str, **kwargs) -> str:
        """Get the best model for a task.
        
        Args:
            task: Task type (coding, reasoning, etc.)
            **kwargs: Additional conditions to match.
            
        Returns:
            Model name to use.
        """
        # Sort rules by priority (higher first)
        sorted_rules = sorted(self.rules, key=lambda r: r.priority, reverse=True)
        
        for rule in sorted_rules:
            if rule.matches(task, **kwargs):
                return rule.model
        
        # Return default or fallback
        return self.default_model or self.fallback_model
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "calibration_id": self.calibration_id,
            "default_model": self.default_model,
            "rules": [r.to_dict() for r in self.rules],
            "fallback_model": self.fallback_model,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CalibrationPolicy":
        """Create policy from dictionary."""
        rules = []
        for rule_data in data.get("rules", []):
            rules.append(RoutingRule(
                task=rule_data.get("task", "*"),
                model=rule_data.get("model", ""),
                priority=rule_data.get("priority", 0),
                conditions=rule_data.get("conditions", {}),
            ))
        
        created_at = None
        if data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(data["created_at"])
            except (ValueError, TypeError):
                pass
        
        return cls(
            version=data.get("version", "1.0"),
            name=data.get("name", "default"),
            description=data.get("description", ""),
            created_at=created_at,
            calibration_id=data.get("calibration_id", ""),
            default_model=data.get("default_model", ""),
            rules=rules,
            fallback_model=data.get("fallback_model", ""),
        )
