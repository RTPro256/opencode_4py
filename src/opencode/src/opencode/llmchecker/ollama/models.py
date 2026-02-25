"""
Data models for Ollama API responses.
"""

from dataclasses import dataclass, field
from typing import Optional, Any
from datetime import datetime


@dataclass
class OllamaModel:
    """Information about an Ollama model."""
    name: str
    size: int = 0  # Size in bytes
    digest: str = ""
    modified_at: Optional[datetime] = None
    details: dict = field(default_factory=dict)
    
    # Parsed details
    family: str = ""
    parameter_size: str = ""
    quantization_level: str = ""
    
    def __post_init__(self):
        """Parse details if available."""
        if self.details:
            self.family = self.details.get("family", "")
            self.parameter_size = self.details.get("parameter_size", "")
            self.quantization_level = self.details.get("quantization_level", "")
    
    @property
    def size_gb(self) -> float:
        """Get size in GB."""
        return self.size / (1024**3)
    
    @property
    def parameters_b(self) -> float:
        """Get parameter count in billions."""
        # Parse strings like "7B", "13B", "70B"
        param_str = self.parameter_size.upper()
        if "B" in param_str:
            try:
                return float(param_str.replace("B", "").strip())
            except ValueError:
                pass
        return 0.0
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "size": self.size,
            "size_gb": round(self.size_gb, 2),
            "digest": self.digest,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
            "family": self.family,
            "parameter_size": self.parameter_size,
            "parameters_b": self.parameters_b,
            "quantization_level": self.quantization_level,
        }


@dataclass
class OllamaResponse:
    """Response from Ollama API."""
    model: str
    content: str = ""
    done: bool = False
    total_duration: int = 0  # nanoseconds
    load_duration: int = 0
    prompt_eval_count: int = 0
    prompt_eval_duration: int = 0
    eval_count: int = 0
    eval_duration: int = 0
    
    @property
    def tokens_per_second(self) -> float:
        """Calculate tokens per second."""
        if self.eval_duration > 0:
            return self.eval_count / (self.eval_duration / 1e9)
        return 0.0
    
    @property
    def total_time_seconds(self) -> float:
        """Get total time in seconds."""
        return self.total_duration / 1e9
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "model": self.model,
            "content": self.content,
            "done": self.done,
            "total_duration_ns": self.total_duration,
            "total_time_seconds": round(self.total_time_seconds, 3),
            "tokens_per_second": round(self.tokens_per_second, 2),
            "prompt_eval_count": self.prompt_eval_count,
            "eval_count": self.eval_count,
        }


@dataclass
class OllamaRunningModel:
    """Information about a running Ollama model."""
    name: str
    model: str
    size: int = 0
    digest: str = ""
    details: dict = field(default_factory=dict)
    expires_at: Optional[datetime] = None
    size_vram: int = 0
    
    @property
    def size_gb(self) -> float:
        """Get size in GB."""
        return self.size / (1024**3)
    
    @property
    def vram_gb(self) -> float:
        """Get VRAM usage in GB."""
        return self.size_vram / (1024**3)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "model": self.model,
            "size": self.size,
            "size_gb": round(self.size_gb, 2),
            "vram_gb": round(self.vram_gb, 2),
            "digest": self.digest,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


@dataclass
class OllamaVersion:
    """Ollama version information."""
    version: str = "unknown"
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {"version": self.version}


@dataclass
class OllamaPullProgress:
    """Progress information for model pull."""
    status: str
    digest: str = ""
    total: int = 0
    completed: int = 0
    
    @property
    def percent(self) -> float:
        """Get completion percentage."""
        if self.total > 0:
            return (self.completed / self.total) * 100
        return 0.0
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "status": self.status,
            "digest": self.digest,
            "total": self.total,
            "completed": self.completed,
            "percent": round(self.percent, 1),
        }
