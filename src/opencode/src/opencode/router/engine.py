"""
Router Engine

Core routing engine for intelligent LLM model selection.
"""

import asyncio
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import json

from opencode.router.config import (
    RouterConfig,
    ModelConfig,
    PromptCategory,
    Complexity,
    QualityPreference,
)
from opencode.router.skills import SkillClassifier, ClassificationResult
from opencode.router.profiler import ModelProfiler, ModelProfile

logger = logging.getLogger(__name__)


@dataclass
class RoutingResult:
    """
    Result of a routing decision.
    
    Contains the selected model and routing metadata.
    """
    model_id: str
    provider: str
    confidence: float
    category: PromptCategory
    complexity: Complexity
    reasoning: str
    alternatives: List[Tuple[str, float]] = field(default_factory=list)
    cached: bool = False
    profile: Optional[ModelProfile] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "model_id": self.model_id,
            "provider": self.provider,
            "confidence": self.confidence,
            "category": self.category.value if isinstance(self.category, PromptCategory) else self.category,
            "complexity": self.complexity.value if isinstance(self.complexity, Complexity) else self.complexity,
            "reasoning": self.reasoning,
            "alternatives": self.alternatives,
            "cached": self.cached,
        }


class SemanticCache:
    """
    Simple semantic cache for routing decisions.
    
    Caches routing decisions based on prompt hash to avoid
    repeated classification for similar prompts.
    """
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Tuple[RoutingResult, datetime]] = {}
    
    def _hash_prompt(self, prompt: str) -> str:
        """Generate a hash for a prompt."""
        return hashlib.md5(prompt.encode()).hexdigest()
    
    def get(self, prompt: str) -> Optional[RoutingResult]:
        """Get a cached routing result."""
        key = self._hash_prompt(prompt)
        if key in self._cache:
            result, timestamp = self._cache[key]
            age = (datetime.utcnow() - timestamp).total_seconds()
            if age < self.ttl_seconds:
                result.cached = True
                return result
            else:
                del self._cache[key]
        return None
    
    def set(self, prompt: str, result: RoutingResult) -> None:
        """Cache a routing result."""
        # Evict old entries if at capacity
        if len(self._cache) >= self.max_size:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]
        
        key = self._hash_prompt(prompt)
        self._cache[key] = (result, datetime.utcnow())
    
    def clear(self) -> None:
        """Clear the cache."""
        self._cache.clear()


class RouterEngine:
    """
    Intelligent LLM routing engine.
    
    Analyzes prompts and selects the most appropriate model
    based on category, complexity, and quality/speed preferences.
    
    Example:
        config = RouterConfig(quality_preference=QualityPreference.QUALITY)
        router = RouterEngine(config)
        
        result = await router.route("Write a Python function to sort a list")
        print(f"Selected model: {result.model_id}")
    """
    
    def __init__(
        self,
        config: Optional[RouterConfig] = None,
        provider: Optional[Any] = None,
    ):
        """
        Initialize the router engine.
        
        Args:
            config: Router configuration
            provider: LLM provider instance for model listing
        """
        self.config = config or RouterConfig()
        self.provider = provider
        self.classifier = SkillClassifier()
        self.profiler = ModelProfiler(timeout_seconds=self.config.profiling_timeout_seconds)
        self.cache = SemanticCache(
            max_size=self.config.cache_max_size,
            ttl_seconds=self.config.cache_ttl_seconds,
        )
        
        self._models: Dict[str, ModelConfig] = {}
        self._profiles: Dict[str, ModelProfile] = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the router by discovering available models."""
        if self._initialized:
            return
        
        if self.provider:
            await self._discover_models()
        
        self._initialized = True
    
    async def _discover_models(self) -> None:
        """Discover available models from the provider."""
        try:
            if hasattr(self.provider, 'models'):
                for model_info in self.provider.models:
                    model_config = ModelConfig(
                        model_id=model_info.id,
                        provider=self.config.provider,
                        supports_tools=model_info.supports_tools,
                        supports_vision=model_info.supports_vision,
                        supports_streaming=model_info.supports_streaming,
                        context_length=model_info.context_length,
                    )
                    self._models[model_info.id] = model_config
                    logger.debug(f"Discovered model: {model_info.id}")
        except Exception as e:
            logger.error(f"Failed to discover models: {e}")
    
    async def route(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RoutingResult:
        """
        Route a prompt to the most appropriate model.
        
        Args:
            prompt: The prompt to route
            context: Optional context for routing decisions
            
        Returns:
            RoutingResult with selected model and metadata
        """
        await self.initialize()
        
        # Check if routing is disabled
        if not self.config.enabled:
            return self._default_routing(prompt)
        
        # Check for pinned model
        if self.config.pinned_model:
            return RoutingResult(
                model_id=self.config.pinned_model,
                provider=self.config.provider,
                confidence=1.0,
                category=PromptCategory.GENERAL,
                complexity=Complexity.MEDIUM,
                reasoning="Model is pinned by configuration",
            )
        
        # Check cache
        if self.config.cache_enabled:
            cached = self.cache.get(prompt)
            if cached:
                logger.debug(f"Cache hit for prompt")
                return cached
        
        # Classify the prompt
        classification = self.classifier.classify(prompt)
        
        # Select the best model
        result = await self._select_model(prompt, classification, context)
        
        # Cache the result
        if self.config.cache_enabled:
            self.cache.set(prompt, result)
        
        return result
    
    async def _select_model(
        self,
        prompt: str,
        classification: ClassificationResult,
        context: Optional[Dict[str, Any]] = None,
    ) -> RoutingResult:
        """
        Select the best model for a classified prompt.
        
        Args:
            prompt: The original prompt
            classification: Classification result
            context: Optional context
            
        Returns:
            RoutingResult with selected model
        """
        candidates: List[Tuple[str, float, str]] = []
        
        # Score each available model
        for model_id, model_config in self._models.items():
            # Skip excluded models
            if model_id in self.config.excluded_models:
                continue
            
            # Skip if not in included list (when specified)
            if self.config.included_models and model_id not in self.config.included_models:
                continue
            
            score, reasoning = self._score_model(model_config, classification)
            candidates.append((model_id, score, reasoning))
        
        # Sort by score
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        if not candidates:
            # No models available, use fallback
            if self.config.fallback_model:
                return RoutingResult(
                    model_id=self.config.fallback_model,
                    provider=self.config.provider,
                    confidence=0.5,
                    category=classification.category,
                    complexity=classification.complexity,
                    reasoning="Using fallback model (no models available)",
                )
            return self._default_routing(prompt)
        
        # Get best model
        best_model_id, best_score, best_reasoning = candidates[0]
        
        # Build alternatives list
        alternatives = [(m, s) for m, s, _ in candidates[1:4]]
        
        return RoutingResult(
            model_id=best_model_id,
            provider=self.config.provider,
            confidence=min(best_score, 1.0),
            category=classification.category,
            complexity=classification.complexity,
            reasoning=best_reasoning,
            alternatives=alternatives,
            profile=self._profiles.get(best_model_id),
        )
    
    def _score_model(
        self,
        model: ModelConfig,
        classification: ClassificationResult,
    ) -> Tuple[float, str]:
        """
        Score a model for a given classification.
        
        Args:
            model: Model configuration
            classification: Prompt classification
            
        Returns:
            Tuple of (score, reasoning)
        """
        score = 0.0
        reasons = []
        
        # Base score from category
        category_scores = {
            PromptCategory.CODING: model.coding_score,
            PromptCategory.REASONING: model.reasoning_score,
            PromptCategory.CREATIVE: model.creative_score,
            PromptCategory.MATH: model.math_score,
            PromptCategory.GENERAL: model.quality_score,
            PromptCategory.ANALYSIS: model.reasoning_score,
            PromptCategory.TRANSLATION: model.quality_score,
            PromptCategory.SUMMARIZATION: model.quality_score,
        }
        
        category_score = category_scores.get(classification.category, 0.5)
        score += category_score * 0.4
        reasons.append(f"category score: {category_score:.2f}")
        
        # Quality preference adjustment
        if self.config.quality_preference == QualityPreference.QUALITY:
            score += model.quality_score * 0.3
            reasons.append("quality preference")
        elif self.config.quality_preference == QualityPreference.SPEED:
            score += model.speed_score * 0.3
            reasons.append("speed preference")
        else:
            score += (model.quality_score + model.speed_score) * 0.15
            reasons.append("balanced preference")
        
        # Complexity adjustment
        if classification.complexity == Complexity.HARD:
            # Prefer higher quality for hard tasks
            score += model.quality_score * 0.2
            reasons.append("complex task -> quality boost")
        elif classification.complexity == Complexity.SIMPLE:
            # Prefer speed for simple tasks
            score += model.speed_score * 0.2
            reasons.append("simple task -> speed boost")
        
        # Capability requirements
        if classification.suggested_skills:
            if "code_generation" in classification.suggested_skills and model.supports_tools:
                score += 0.1
                reasons.append("supports tools")
        
        # Minimum thresholds
        if model.speed_score < self.config.min_speed_score:
            score *= 0.5
            reasons.append("below min speed threshold")
        
        if model.quality_score < self.config.min_quality_score:
            score *= 0.5
            reasons.append("below min quality threshold")
        
        reasoning = "; ".join(reasons)
        return score, reasoning
    
    def _default_routing(self, prompt: str) -> RoutingResult:
        """Return default routing when no models are available."""
        return RoutingResult(
            model_id=self.config.fallback_model or "default",
            provider=self.config.provider,
            confidence=0.0,
            category=PromptCategory.GENERAL,
            complexity=Complexity.MEDIUM,
            reasoning="Default routing (no models available)",
        )
    
    async def profile_models(self) -> Dict[str, ModelProfile]:
        """
        Profile all available models.
        
        Returns:
            Dictionary of model profiles
        """
        if not self.provider:
            logger.warning("No provider set, cannot profile models")
            return {}
        
        for model_id in self._models:
            try:
                profile = await self.profiler.quick_profile(self.provider, model_id)
                self._profiles[model_id] = profile
                
                # Update model config with profile data
                if model_id in self._models:
                    self._models[model_id].speed_score = profile._calculate_speed_score()
                    self._models[model_id].quality_score = profile.overall_quality
                    self._models[model_id].coding_score = profile.coding_score
                    self._models[model_id].reasoning_score = profile.reasoning_score
                    self._models[model_id].creative_score = profile.creative_score
                    self._models[model_id].math_score = profile.math_score
                
            except Exception as e:
                logger.error(f"Failed to profile model {model_id}: {e}")
        
        return self._profiles
    
    def register_model(self, config: ModelConfig) -> None:
        """Manually register a model configuration."""
        self._models[config.model_id] = config
    
    def unregister_model(self, model_id: str) -> bool:
        """Unregister a model."""
        if model_id in self._models:
            del self._models[model_id]
            return True
        return False
    
    def get_model(self, model_id: str) -> Optional[ModelConfig]:
        """Get a model configuration."""
        return self._models.get(model_id)
    
    def list_models(self) -> List[ModelConfig]:
        """List all registered models."""
        return list(self._models.values())
    
    def set_provider(self, provider: Any) -> None:
        """Set the LLM provider."""
        self.provider = provider
        self._initialized = False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get router statistics."""
        return {
            "models_registered": len(self._models),
            "profiles_cached": len(self._profiles),
            "cache_size": len(self.cache._cache),
            "config": {
                "enabled": self.config.enabled,
                "quality_preference": self.config.quality_preference,
                "cache_enabled": self.config.cache_enabled,
                "vram_monitoring": self.config.vram_monitoring,
            },
        }
