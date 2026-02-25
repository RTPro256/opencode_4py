"""
Router Configuration

Configuration settings for the intelligent LLM router.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class QualityPreference(str, Enum):
    """Quality vs speed preference."""
    SPEED = "speed"  # Prefer faster models
    BALANCED = "balanced"  # Balance between speed and quality
    QUALITY = "quality"  # Prefer higher quality models


class PromptCategory(str, Enum):
    """Categories for prompt classification."""
    CODING = "coding"
    REASONING = "reasoning"
    CREATIVE = "creative"
    GENERAL = "general"
    MATH = "math"
    ANALYSIS = "analysis"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"


class Complexity(str, Enum):
    """Complexity levels for prompts."""
    SIMPLE = "simple"
    MEDIUM = "medium"
    HARD = "hard"


class RouterConfig(BaseModel):
    """
    Configuration for the router engine.
    
    Controls how the router selects models and manages resources.
    """
    
    # Basic settings
    enabled: bool = Field(default=True, description="Enable/disable routing")
    provider: str = Field(default="ollama", description="Default provider")
    
    # Quality preference
    quality_preference: QualityPreference = Field(
        default=QualityPreference.BALANCED,
        description="Quality vs speed preference"
    )
    
    # Model selection
    pinned_model: Optional[str] = Field(
        default=None,
        description="Pin to a specific model (bypasses routing)"
    )
    fallback_model: Optional[str] = Field(
        default=None,
        description="Fallback model if routing fails"
    )
    
    # VRAM management
    vram_monitoring: bool = Field(default=True, description="Enable VRAM monitoring")
    auto_unload: bool = Field(default=True, description="Auto-unload models when VRAM is low")
    vram_threshold_percent: float = Field(
        default=90.0,
        description="VRAM usage threshold for auto-unload"
    )
    
    # Caching
    cache_enabled: bool = Field(default=True, description="Enable routing cache")
    cache_max_size: int = Field(default=100, description="Maximum cache entries")
    cache_ttl_seconds: int = Field(default=3600, description="Cache TTL in seconds")
    
    # Profiling
    profiling_enabled: bool = Field(default=True, description="Enable model profiling")
    profile_on_startup: bool = Field(default=False, description="Profile models on startup")
    profiling_timeout_seconds: int = Field(default=90, description="Profiling timeout")
    
    # Model preferences by category
    category_models: Dict[str, str] = Field(
        default_factory=lambda: {
            "coding": "",
            "reasoning": "",
            "creative": "",
            "general": "",
            "math": "",
            "analysis": "",
            "translation": "",
            "summarization": "",
        },
        description="Preferred models for each category"
    )
    
    # Model blacklist/whitelist
    excluded_models: List[str] = Field(
        default_factory=list,
        description="Models to exclude from routing"
    )
    included_models: List[str] = Field(
        default_factory=list,
        description="Models to include in routing (empty = all)"
    )
    
    # Performance thresholds
    min_speed_score: float = Field(default=0.0, description="Minimum speed score (0-1)")
    min_quality_score: float = Field(default=0.0, description="Minimum quality score (0-1)")
    
    class Config:
        use_enum_values = True


class ModelConfig(BaseModel):
    """Configuration for a specific model."""
    
    model_id: str = Field(..., description="Model identifier")
    provider: str = Field(..., description="Provider name")
    
    # Capabilities
    supports_tools: bool = Field(default=False, description="Supports function calling")
    supports_vision: bool = Field(default=False, description="Supports image input")
    supports_streaming: bool = Field(default=True, description="Supports streaming")
    
    # Resource requirements
    vram_required_gb: Optional[float] = Field(default=None, description="VRAM required in GB")
    context_length: int = Field(default=4096, description="Maximum context length")
    
    # Performance scores (0-1)
    speed_score: float = Field(default=0.5, description="Speed score")
    quality_score: float = Field(default=0.5, description="Quality score")
    
    # Category scores (0-1)
    coding_score: float = Field(default=0.5, description="Coding capability score")
    reasoning_score: float = Field(default=0.5, description="Reasoning capability score")
    creative_score: float = Field(default=0.5, description="Creative writing score")
    math_score: float = Field(default=0.5, description="Math capability score")
    
    # Metadata
    is_loaded: bool = Field(default=False, description="Whether model is loaded")
    last_used: Optional[str] = Field(default=None, description="Last usage timestamp")
    
    class Config:
        extra = "allow"
