"""
Scoring engine for LLM model selection.

Implements multi-dimensional scoring (Quality, Speed, Fit, Context)
based on the llm-checker scoring system.
"""

from typing import Optional

from .models import (
    ModelInfo,
    ModelScore,
    ScoringWeights,
    ScoringResult,
    QuantizationType,
)
from ..hardware.models import SystemInfo, HardwareTier


class ScoringEngine:
    """Multi-dimensional model scoring engine.
    
    Calculates scores based on:
    - Q (Quality): Model quality based on params, family, quantization
    - S (Speed): Estimated inference speed on target hardware
    - F (Fit): How well the model fits in available memory
    - C (Context): Context length capability
    
    FinalScore = Q × wQ + S × wS + F × wF + C × wC
    """
    
    # Model family quality rankings (0-100 base score)
    FAMILY_QUALITY = {
        # Frontier models
        "qwen2.5": 95,
        "qwen2": 90,
        "llama3.3": 95,
        "llama3.2": 92,
        "llama3.1": 90,
        "llama3": 88,
        "deepseek-v3": 96,
        "deepseek-v2.5": 94,
        "deepseek-coder-v2": 92,
        "deepseek-r1": 96,
        "gemma2": 90,
        "gemma": 82,
        "phi-4": 92,
        "phi-3.5": 88,
        "phi-3": 85,
        "phi-2": 75,
        "mistral-large": 94,
        "mistral": 85,
        "mixtral": 88,
        "command-r": 90,
        "command-r-plus": 93,
        
        # Coding specialists
        "qwen2.5-coder": 96,
        "codellama": 82,
        "starcoder2": 85,
        "deepseek-coder": 88,
        "codegemma": 80,
        "granite-code": 78,
        
        # Chat/instruct
        "yi": 85,
        "yi-coder": 88,
        "openchat": 78,
        "neural-chat": 75,
        "zephyr": 80,
        "openhermes": 82,
        "nous-hermes": 82,
        "dolphin": 80,
        "orca": 78,
        
        # Vision models
        "llava": 82,
        "llava-llama3": 85,
        "llava-phi3": 80,
        "bakllava": 78,
        "moondream": 75,
        
        # Embeddings
        "nomic-embed-text": 85,
        "mxbai-embed-large": 88,
        "all-minilm": 80,
        "snowflake-arctic-embed": 85,
        
        # Other notable models
        "solar": 82,
        "falcon": 75,
        "vicuna": 72,
        "wizardlm": 78,
        "aya": 85,
        "smollm": 70,
        "tinyllama": 65,
    }
    
    # Quantization quality penalties (subtracted from base score)
    QUANT_PENALTIES = {
        QuantizationType.FP16: 0,
        QuantizationType.F16: 0,
        QuantizationType.Q8_0: 2,
        QuantizationType.Q6_K: 4,
        QuantizationType.Q5_K_M: 6,
        QuantizationType.Q5_K_S: 7,
        QuantizationType.Q5_0: 8,
        QuantizationType.Q4_K_M: 10,
        QuantizationType.Q4_K_S: 11,
        QuantizationType.Q4_0: 12,
        QuantizationType.Q3_K_M: 16,
        QuantizationType.Q3_K_S: 18,
        QuantizationType.Q3_K_L: 15,
        QuantizationType.IQ4_XS: 11,
        QuantizationType.IQ4_NL: 10,
        QuantizationType.IQ3_XXS: 20,
        QuantizationType.IQ3_XS: 18,
        QuantizationType.IQ3_S: 17,
        QuantizationType.IQ2_XS: 25,
        QuantizationType.IQ2_XXS: 28,
        QuantizationType.Q2_K: 22,
        QuantizationType.Q2_K_S: 24,
        QuantizationType.UNKNOWN: 5,
    }
    
    # Task-specific bonuses for model families
    TASK_BONUSES = {
        "coding": {
            "qwen2.5-coder": 15,
            "deepseek-coder": 12,
            "deepseek-coder-v2": 15,
            "codellama": 10,
            "starcoder2": 12,
            "codegemma": 8,
            "yi-coder": 10,
            "granite-code": 8,
        },
        "reasoning": {
            "deepseek-r1": 15,
            "qwen2.5": 10,
            "llama3.3": 10,
            "phi-4": 12,
            "command-r-plus": 10,
            "mistral-large": 10,
        },
        "chat": {
            "llama3.2": 10,
            "mistral": 8,
            "gemma2": 8,
            "openchat": 10,
            "neural-chat": 8,
            "dolphin": 8,
        },
        "vision": {
            "llava": 15,
            "llava-llama3": 18,
            "llava-phi3": 15,
            "bakllava": 12,
            "moondream": 10,
        },
    }
    
    # Bytes per parameter for different quantizations
    BYTES_PER_PARAM = {
        QuantizationType.FP16: 2.0,
        QuantizationType.F16: 2.0,
        QuantizationType.Q8_0: 1.0,
        QuantizationType.Q6_K: 0.75,
        QuantizationType.Q5_K_M: 0.625,
        QuantizationType.Q5_K_S: 0.625,
        QuantizationType.Q5_0: 0.625,
        QuantizationType.Q4_K_M: 0.5,
        QuantizationType.Q4_K_S: 0.5,
        QuantizationType.Q4_0: 0.5,
        QuantizationType.Q3_K_M: 0.375,
        QuantizationType.Q3_K_S: 0.375,
        QuantizationType.Q3_K_L: 0.375,
        QuantizationType.IQ4_XS: 0.45,
        QuantizationType.IQ4_NL: 0.5,
        QuantizationType.IQ3_XXS: 0.35,
        QuantizationType.IQ3_XS: 0.375,
        QuantizationType.IQ3_S: 0.375,
        QuantizationType.IQ2_XS: 0.25,
        QuantizationType.IQ2_XXS: 0.25,
        QuantizationType.Q2_K: 0.25,
        QuantizationType.Q2_K_S: 0.25,
        QuantizationType.UNKNOWN: 0.5,
    }
    
    def __init__(self, system_info: Optional[SystemInfo] = None):
        """Initialize scoring engine.
        
        Args:
            system_info: System hardware information for scoring.
        """
        self.system_info = system_info
    
    def set_system_info(self, system_info: SystemInfo) -> None:
        """Set system information for scoring.
        
        Args:
            system_info: System hardware information.
        """
        self.system_info = system_info
    
    def score_model(
        self,
        model: ModelInfo,
        use_case: str = "general",
        weights: Optional[ScoringWeights] = None,
    ) -> ModelScore:
        """Score a single model.
        
        Args:
            model: Model to score.
            use_case: Use case for scoring (coding, reasoning, chat, etc.).
            weights: Custom scoring weights. If None, uses use_case defaults.
            
        Returns:
            ModelScore with all dimension scores.
        """
        if weights is None:
            weights = ScoringWeights.for_use_case(use_case)
        
        score = ModelScore(model=model)
        
        # Calculate dimension scores
        score.quality_score = self._calculate_quality_score(model, use_case)
        score.speed_score = self._calculate_speed_score(model)
        score.fit_score, score.fits_in_memory = self._calculate_fit_score(model)
        score.context_score = self._calculate_context_score(model)
        
        # Calculate final score
        score.calculate_final_score(weights)
        
        # Determine recommended context
        score.recommended_context = self._get_recommended_context(model)
        
        # Add warnings
        if not score.fits_in_memory:
            score.warnings.append("Model may not fit in available memory")
        if model.parameters_b > 70:
            score.warnings.append("Very large model - may be slow")
        
        return score
    
    def score_models(
        self,
        models: list[ModelInfo],
        use_case: str = "general",
        weights: Optional[ScoringWeights] = None,
    ) -> ScoringResult:
        """Score multiple models and rank them.
        
        Args:
            models: List of models to score.
            use_case: Use case for scoring.
            weights: Custom scoring weights.
            
        Returns:
            ScoringResult with all scores and rankings.
        """
        if weights is None:
            weights = ScoringWeights.for_use_case(use_case)
        
        scores = []
        for model in models:
            score = self.score_model(model, use_case, weights)
            scores.append(score)
        
        # Sort by final score and assign ranks
        scores.sort(key=lambda s: s.final_score, reverse=True)
        for i, score in enumerate(scores):
            score.rank = i + 1
        
        result = ScoringResult(
            scores=scores,
            hardware_info=self.system_info.to_dict() if self.system_info else None,
            weights_used=weights,
            use_case=use_case,
        )
        
        return result
    
    def _calculate_quality_score(self, model: ModelInfo, use_case: str) -> float:
        """Calculate quality score for a model.
        
        Quality is based on:
        - Model family quality ranking
        - Parameter count
        - Quantization penalty
        - Task-specific bonus
        """
        score = 50.0  # Base score
        
        # Family quality bonus
        family_lower = model.family.lower()
        for family, quality in self.FAMILY_QUALITY.items():
            if family in family_lower or family_lower in family:
                score = quality
                break
        
        # Parameter count bonus (larger models tend to be better)
        params = model.parameters_b
        if params >= 100:
            score += 5
        elif params >= 70:
            score += 3
        elif params >= 30:
            score += 2
        elif params >= 7:
            score += 1
        
        # Quantization penalty
        penalty = self.QUANT_PENALTIES.get(model.quantization, 5)
        score -= penalty
        
        # Task-specific bonus
        task_bonuses = self.TASK_BONUSES.get(use_case.lower(), {})
        for family, bonus in task_bonuses.items():
            if family in family_lower:
                score += bonus
                break
        
        # Vision support bonus for vision use case
        if use_case.lower() == "vision" and model.supports_vision:
            score += 10
        
        # Tool support bonus for coding
        if use_case.lower() == "coding" and model.supports_tools:
            score += 5
        
        return max(0, min(100, score))
    
    def _calculate_speed_score(self, model: ModelInfo) -> float:
        """Calculate speed score for a model.
        
        Speed is estimated based on:
        - Parameter count (smaller = faster)
        - Quantization (lower bits = faster)
        - Hardware tier
        """
        score = 50.0
        
        # Parameter count impact (smaller is faster)
        params = model.parameters_b
        if params <= 1:
            score += 40
        elif params <= 3:
            score += 30
        elif params <= 7:
            score += 20
        elif params <= 14:
            score += 10
        elif params <= 30:
            score += 0
        elif params <= 70:
            score -= 10
        else:
            score -= 20
        
        # Quantization impact (lower bits = faster)
        quant_speed = {
            QuantizationType.FP16: 0,
            QuantizationType.F16: 0,
            QuantizationType.Q8_0: 5,
            QuantizationType.Q6_K: 8,
            QuantizationType.Q5_K_M: 10,
            QuantizationType.Q5_K_S: 10,
            QuantizationType.Q5_0: 12,
            QuantizationType.Q4_K_M: 15,
            QuantizationType.Q4_K_S: 15,
            QuantizationType.Q4_0: 18,
            QuantizationType.Q3_K_M: 20,
            QuantizationType.Q3_K_S: 22,
            QuantizationType.Q3_K_L: 18,
            QuantizationType.IQ4_XS: 16,
            QuantizationType.IQ4_NL: 15,
            QuantizationType.IQ3_XXS: 22,
            QuantizationType.IQ3_XS: 20,
            QuantizationType.IQ3_S: 20,
            QuantizationType.IQ2_XS: 25,
            QuantizationType.IQ2_XXS: 28,
            QuantizationType.Q2_K: 25,
            QuantizationType.Q2_K_S: 27,
            QuantizationType.UNKNOWN: 10,
        }
        score += quant_speed.get(model.quantization, 10)
        
        # Hardware tier adjustment
        if self.system_info:
            tier = self.system_info.tier
            if tier == HardwareTier.VERY_HIGH:
                score += 10
            elif tier == HardwareTier.HIGH:
                score += 5
            elif tier == HardwareTier.LOW:
                score -= 10
        
        return max(0, min(100, score))
    
    def _calculate_fit_score(self, model: ModelInfo) -> tuple[float, bool]:
        """Calculate fit score (memory compatibility).
        
        Args:
            model: Model to evaluate.
            
        Returns:
            Tuple of (fit_score, fits_in_memory).
        """
        if not self.system_info:
            return 50.0, True  # Assume fits if no hardware info
        
        # Calculate model memory requirement
        model_size = self._estimate_model_size(model)
        max_model_size = self.system_info.max_model_size_gb
        
        # Check if model fits
        fits = model_size <= max_model_size
        
        if not fits:
            # Calculate how much it exceeds
            overflow_ratio = model_size / max_model_size if max_model_size > 0 else 10
            score = max(0, 50 - (overflow_ratio - 1) * 30)
        else:
            # Score based on how much headroom is left
            if max_model_size > 0:
                utilization = model_size / max_model_size
                if utilization <= 0.5:
                    score = 100
                elif utilization <= 0.7:
                    score = 90
                elif utilization <= 0.85:
                    score = 80
                elif utilization <= 0.95:
                    score = 70
                else:
                    score = 60
            else:
                score = 50
        
        return score, fits
    
    def _calculate_context_score(self, model: ModelInfo) -> float:
        """Calculate context length score.
        
        Longer context is generally better, but with diminishing returns.
        """
        context = model.context_length
        
        if context >= 128000:
            return 100
        elif context >= 32000:
            return 90
        elif context >= 16000:
            return 80
        elif context >= 8192:
            return 70
        elif context >= 4096:
            return 60
        elif context >= 2048:
            return 50
        else:
            return 40
    
    def _estimate_model_size(self, model: ModelInfo) -> float:
        """Estimate model size in GB.
        
        Args:
            model: Model to estimate.
            
        Returns:
            Estimated size in GB.
        """
        if model.size_gb > 0:
            return model.size_gb
        
        # Estimate from parameters and quantization
        params = model.parameters_b
        bytes_per_param = self.BYTES_PER_PARAM.get(model.quantization, 0.5)
        
        # Size in GB = params * 1e9 * bytes_per_param / 1e9
        # Simplified: params * bytes_per_param
        size_gb = params * bytes_per_param
        
        # Add 15% overhead for KV cache and runtime
        size_gb *= 1.15
        
        return size_gb
    
    def _get_recommended_context(self, model: ModelInfo) -> int:
        """Get recommended context length based on hardware.
        
        Args:
            model: Model to evaluate.
            
        Returns:
            Recommended context length.
        """
        if not self.system_info:
            return min(model.context_length, 4096)
        
        # For Apple Silicon with unified memory, can use more context
        if self.system_info.is_apple_silicon():
            available = self.system_info.memory.total_gb
            if available >= 64:
                return min(model.context_length, 32000)
            elif available >= 32:
                return min(model.context_length, 16000)
            elif available >= 16:
                return min(model.context_length, 8192)
            else:
                return min(model.context_length, 4096)
        
        # For GPU, context is limited by VRAM
        total_vram = self.system_info.get_total_vram()
        if total_vram >= 24:
            return min(model.context_length, 16000)
        elif total_vram >= 16:
            return min(model.context_length, 8192)
        elif total_vram >= 8:
            return min(model.context_length, 4096)
        else:
            return min(model.context_length, 2048)
    
    @staticmethod
    def parse_quantization(quant_str: str) -> QuantizationType:
        """Parse quantization string to QuantizationType.
        
        Args:
            quant_str: Quantization string like "Q4_K_M" or "q4_k_m".
            
        Returns:
            QuantizationType enum value.
        """
        quant_upper = quant_str.upper().replace("-", "_")
        
        # Direct match
        for qt in QuantizationType:
            if qt.value == quant_upper.lower():
                return qt
        
        # Partial match
        quant_lower = quant_str.lower()
        if "fp16" in quant_lower or "f16" in quant_lower:
            return QuantizationType.F16
        elif "q8" in quant_lower:
            return QuantizationType.Q8_0
        elif "q6" in quant_lower:
            return QuantizationType.Q6_K
        elif "q5" in quant_lower:
            if "k_m" in quant_lower or "k-m" in quant_lower:
                return QuantizationType.Q5_K_M
            elif "k_s" in quant_lower or "k-s" in quant_lower:
                return QuantizationType.Q5_K_S
            return QuantizationType.Q5_0
        elif "q4" in quant_lower:
            if "k_m" in quant_lower or "k-m" in quant_lower:
                return QuantizationType.Q4_K_M
            elif "k_s" in quant_lower or "k-s" in quant_lower:
                return QuantizationType.Q4_K_S
            return QuantizationType.Q4_0
        elif "q3" in quant_lower:
            if "k_l" in quant_lower or "k-l" in quant_lower:
                return QuantizationType.Q3_K_L
            elif "k_m" in quant_lower or "k-m" in quant_lower:
                return QuantizationType.Q3_K_M
            elif "k_s" in quant_lower or "k-s" in quant_lower:
                return QuantizationType.Q3_K_S
            return QuantizationType.Q3_K_M
        elif "q2" in quant_lower:
            if "k_s" in quant_lower or "k-s" in quant_lower:
                return QuantizationType.Q2_K_S
            return QuantizationType.Q2_K
        elif "iq4" in quant_lower:
            if "xs" in quant_lower:
                return QuantizationType.IQ4_XS
            return QuantizationType.IQ4_NL
        elif "iq3" in quant_lower:
            if "xxs" in quant_lower:
                return QuantizationType.IQ3_XXS
            elif "xs" in quant_lower:
                return QuantizationType.IQ3_XS
            return QuantizationType.IQ3_S
        elif "iq2" in quant_lower:
            if "xxs" in quant_lower:
                return QuantizationType.IQ2_XXS
            return QuantizationType.IQ2_XS
        
        return QuantizationType.UNKNOWN
    
    @staticmethod
    def parse_model_name(name: str) -> tuple[str, str, float, QuantizationType]:
        """Parse model name to extract family, parameters, and quantization.
        
        Args:
            name: Model name like "llama3.2:3b-q4_k_m".
            
        Returns:
            Tuple of (name, family, parameters_b, quantization).
        """
        # Default values
        family = name.split(":")[0].split("-")[0]
        params = 0.0
        quant = QuantizationType.UNKNOWN
        
        # Extract parameters (e.g., "3b", "7b", "70b")
        import re
        param_match = re.search(r"(\d+(?:\.\d+)?)\s*b", name.lower())
        if param_match:
            params = float(param_match.group(1))
        
        # Extract quantization
        quant_match = re.search(r"[_-]?(q\d+[^_-]*|iq\d+[^_-]*|fp16|f16)", name.lower())
        if quant_match:
            quant = ScoringEngine.parse_quantization(quant_match.group(1))
        
        # Extract family (first part before numbers or special chars)
        family_match = re.match(r"^([a-z]+(?:[-.][a-z0-9]+)*)", name.lower())
        if family_match:
            family = family_match.group(1)
        
        return name, family, params, quant