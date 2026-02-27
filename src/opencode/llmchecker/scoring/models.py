"""
Data models for model scoring.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ModelCategory(Enum):
    """Model category/types."""
    GENERAL = "general"
    CODING = "coding"
    REASONING = "reasoning"
    CHAT = "chat"
    VISION = "vision"
    EMBEDDING = "embedding"
    MULTIMODAL = "multimodal"


class QuantizationType(Enum):
    """Quantization types."""
    FP16 = "fp16"
    F16 = "f16"
    Q8_0 = "q8_0"
    Q6_K = "q6_k"
    Q5_K_M = "q5_k_m"
    Q5_K_S = "q5_k_s"
    Q5_0 = "q5_0"
    Q4_K_M = "q4_k_m"
    Q4_K_S = "q4_k_s"
    Q4_0 = "q4_0"
    Q3_K_M = "q3_k_m"
    Q3_K_S = "q3_k_s"
    Q3_K_L = "q3_k_l"
    IQ4_XS = "iq4_xs"
    IQ4_NL = "iq4_nl"
    IQ3_XXS = "iq3_xxs"
    IQ3_XS = "iq3_xs"
    IQ3_S = "iq3_s"
    IQ2_XS = "iq2_xs"
    IQ2_XXS = "iq2_xxs"
    Q2_K = "q2_k"
    Q2_K_S = "q2_k_s"
    UNKNOWN = "unknown"


@dataclass
class ScoringWeights:
    """Weights for scoring dimensions."""
    quality: float = 0.4
    speed: float = 0.25
    fit: float = 0.25
    context: float = 0.1
    
    def validate(self) -> bool:
        """Validate that weights sum to 1.0."""
        total = self.quality + self.speed + self.fit + self.context
        return abs(total - 1.0) < 0.01
    
    def normalize(self) -> "ScoringWeights":
        """Normalize weights to sum to 1.0."""
        total = self.quality + self.speed + self.fit + self.context
        if total == 0:
            return ScoringWeights(0.25, 0.25, 0.25, 0.25)
        return ScoringWeights(
            quality=self.quality / total,
            speed=self.speed / total,
            fit=self.fit / total,
            context=self.context / total,
        )
    
    @classmethod
    def for_use_case(cls, use_case: str) -> "ScoringWeights":
        """Get weights for a specific use case.
        
        Args:
            use_case: One of 'coding', 'reasoning', 'chat', 'vision', 'general'.
            
        Returns:
            ScoringWeights configured for the use case.
        """
        use_case = use_case.lower()
        
        if use_case == "coding":
            # Quality and speed are important for coding
            return cls(quality=0.45, speed=0.30, fit=0.15, context=0.10)
        elif use_case == "reasoning":
            # Quality is most important for reasoning
            return cls(quality=0.50, speed=0.20, fit=0.20, context=0.10)
        elif use_case == "chat":
            # Speed and quality balanced for chat
            return cls(quality=0.35, speed=0.35, fit=0.20, context=0.10)
        elif use_case == "vision":
            # Quality is critical for vision
            return cls(quality=0.45, speed=0.25, fit=0.20, context=0.10)
        else:
            # General/balanced
            return cls(quality=0.40, speed=0.25, fit=0.25, context=0.10)


@dataclass
class ModelInfo:
    """Information about an LLM model."""
    name: str
    family: str = "unknown"
    parameters_b: float = 0.0  # Billions of parameters
    quantization: QuantizationType = QuantizationType.UNKNOWN
    context_length: int = 4096
    size_gb: float = 0.0
    supports_vision: bool = False
    supports_tools: bool = False
    supports_streaming: bool = True
    description: str = ""
    tags: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "family": self.family,
            "parameters_b": self.parameters_b,
            "quantization": self.quantization.value,
            "context_length": self.context_length,
            "size_gb": self.size_gb,
            "supports_vision": self.supports_vision,
            "supports_tools": self.supports_tools,
            "supports_streaming": self.supports_streaming,
            "description": self.description,
            "tags": self.tags,
        }


@dataclass
class ModelScore:
    """Score for a model across multiple dimensions."""
    model: ModelInfo
    quality_score: float = 0.0  # 0-100
    speed_score: float = 0.0    # 0-100
    fit_score: float = 0.0      # 0-100 (memory fit)
    context_score: float = 0.0  # 0-100
    final_score: float = 0.0    # Weighted combination
    rank: int = 0
    
    # Additional info
    fits_in_memory: bool = True
    recommended_context: int = 4096
    warnings: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "model": self.model.to_dict(),
            "quality_score": round(self.quality_score, 2),
            "speed_score": round(self.speed_score, 2),
            "fit_score": round(self.fit_score, 2),
            "context_score": round(self.context_score, 2),
            "final_score": round(self.final_score, 2),
            "rank": self.rank,
            "fits_in_memory": self.fits_in_memory,
            "recommended_context": self.recommended_context,
            "warnings": self.warnings,
        }
    
    def calculate_final_score(self, weights: ScoringWeights) -> float:
        """Calculate final weighted score.
        
        Args:
            weights: Scoring weights to use.
            
        Returns:
            Weighted final score.
        """
        self.final_score = (
            self.quality_score * weights.quality +
            self.speed_score * weights.speed +
            self.fit_score * weights.fit +
            self.context_score * weights.context
        )
        return self.final_score


@dataclass
class ScoringResult:
    """Result of scoring multiple models."""
    scores: list[ModelScore] = field(default_factory=list)
    hardware_info: Optional[dict] = None
    weights_used: Optional[ScoringWeights] = None
    use_case: str = "general"
    
    def get_top_n(self, n: int = 5) -> list[ModelScore]:
        """Get top N models by score."""
        sorted_scores = sorted(self.scores, key=lambda s: s.final_score, reverse=True)
        return sorted_scores[:n]
    
    def get_compatible(self) -> list[ModelScore]:
        """Get only models that fit in memory."""
        return [s for s in self.scores if s.fits_in_memory]
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "scores": [s.to_dict() for s in self.scores],
            "hardware_info": self.hardware_info,
            "weights_used": {
                "quality": self.weights_used.quality if self.weights_used else 0.4,
                "speed": self.weights_used.speed if self.weights_used else 0.25,
                "fit": self.weights_used.fit if self.weights_used else 0.25,
                "context": self.weights_used.context if self.weights_used else 0.1,
            },
            "use_case": self.use_case,
        }
