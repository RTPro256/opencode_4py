"""
Tests for Router Engine module.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
import asyncio

from opencode.router.engine import RouterEngine, SemanticCache, RoutingResult
from opencode.router.config import (
    RouterConfig,
    ModelConfig,
    PromptCategory,
    Complexity,
    QualityPreference,
)
from opencode.router.skills import ClassificationResult


class TestRoutingResult:
    """Tests for RoutingResult dataclass."""

    def test_to_dict(self):
        """Test RoutingResult.to_dict()."""
        result = RoutingResult(
            model_id="test-model",
            provider="test-provider",
            confidence=0.95,
            category=PromptCategory.CODING,
            complexity=Complexity.HARD,
            reasoning="Test reasoning",
            alternatives=[("alt1", 0.8), ("alt2", 0.7)],
            cached=True,
        )
        
        d = result.to_dict()
        
        assert d["model_id"] == "test-model"
        assert d["provider"] == "test-provider"
        assert d["confidence"] == 0.95
        assert d["category"] == "coding"
        assert d["complexity"] == "hard"
        assert d["reasoning"] == "Test reasoning"
        assert d["alternatives"] == [("alt1", 0.8), ("alt2", 0.7)]
        assert d["cached"] is True

    def test_to_dict_string_category(self):
        """Test to_dict with string category (edge case)."""
        result = RoutingResult(
            model_id="test",
            provider="test",
            confidence=0.5,
            category="custom",  # String instead of enum
            complexity="medium",
            reasoning="test",
        )
        
        d = result.to_dict()
        
        assert d["category"] == "custom"


class TestSemanticCache:
    """Tests for SemanticCache class."""

    def test_init(self):
        """Test default initialization."""
        cache = SemanticCache()
        assert cache.max_size == 100
        assert cache.ttl_seconds == 3600
        assert cache._cache == {}

    def test_init_custom(self):
        """Test custom initialization."""
        cache = SemanticCache(max_size=50, ttl_seconds=1800)
        assert cache.max_size == 50
        assert cache.ttl_seconds == 1800

    def test_set_and_get(self):
        """Test setting and getting cached values."""
        cache = SemanticCache()
        result = RoutingResult(
            model_id="test-model",
            provider="test",
            confidence=0.9,
            category=PromptCategory.GENERAL,
            complexity=Complexity.MEDIUM,
            reasoning="test",
        )
        
        cache.set("test prompt", result)
        
        cached = cache.get("test prompt")
        assert cached is not None
        assert cached.model_id == "test-model"
        assert cached.cached is True

    def test_get_miss(self):
        """Test cache miss."""
        cache = SemanticCache()
        
        result = cache.get("non-existent prompt")
        assert result is None

    def test_get_expired(self):
        """Test expired cache entry."""
        cache = SemanticCache(ttl_seconds=1)
        result = RoutingResult(
            model_id="test",
            provider="test",
            confidence=0.9,
            category=PromptCategory.GENERAL,
            complexity=Complexity.MEDIUM,
            reasoning="test",
        )
        
        cache.set("test prompt", result)
        
        # Manually expire the entry
        key = cache._hash_prompt("test prompt")
        cache._cache[key] = (result, datetime.utcnow() - timedelta(seconds=10))
        
        cached = cache.get("test prompt")
        assert cached is None
        assert key not in cache._cache

    def test_eviction(self):
        """Test cache eviction when at capacity."""
        cache = SemanticCache(max_size=2)
        
        result1 = RoutingResult(
            model_id="model1", provider="test", confidence=0.9,
            category=PromptCategory.GENERAL, complexity=Complexity.MEDIUM, reasoning="test"
        )
        result2 = RoutingResult(
            model_id="model2", provider="test", confidence=0.9,
            category=PromptCategory.GENERAL, complexity=Complexity.MEDIUM, reasoning="test"
        )
        result3 = RoutingResult(
            model_id="model3", provider="test", confidence=0.9,
            category=PromptCategory.GENERAL, complexity=Complexity.MEDIUM, reasoning="test"
        )
        
        cache.set("prompt1", result1)
        cache.set("prompt2", result2)
        cache.set("prompt3", result3)  # Should evict oldest
        
        assert cache.get("prompt1") is None
        assert cache.get("prompt2") is not None
        assert cache.get("prompt3") is not None

    def test_clear(self):
        """Test clearing the cache."""
        cache = SemanticCache()
        result = RoutingResult(
            model_id="test", provider="test", confidence=0.9,
            category=PromptCategory.GENERAL, complexity=Complexity.MEDIUM, reasoning="test"
        )
        
        cache.set("prompt", result)
        assert len(cache._cache) == 1
        
        cache.clear()
        assert len(cache._cache) == 0

    def test_hash_consistency(self):
        """Test that hash is consistent for same prompt."""
        cache = SemanticCache()
        
        hash1 = cache._hash_prompt("test prompt")
        hash2 = cache._hash_prompt("test prompt")
        
        assert hash1 == hash2

    def test_hash_uniqueness(self):
        """Test that different prompts have different hashes."""
        cache = SemanticCache()
        
        hash1 = cache._hash_prompt("prompt 1")
        hash2 = cache._hash_prompt("prompt 2")
        
        assert hash1 != hash2


class TestRouterEngine:
    """Tests for RouterEngine class."""

    def test_init_default(self):
        """Test default initialization."""
        router = RouterEngine()
        
        assert router.config is not None
        assert router.provider is None
        assert router._models == {}
        assert router._initialized is False

    def test_init_with_config(self):
        """Test initialization with custom config."""
        config = RouterConfig(
            quality_preference=QualityPreference.QUALITY,
            cache_enabled=False,
        )
        router = RouterEngine(config=config)
        
        assert router.config.quality_preference == QualityPreference.QUALITY
        assert router.config.cache_enabled is False

    def test_init_with_provider(self):
        """Test initialization with provider."""
        provider = MagicMock()
        router = RouterEngine(provider=provider)
        
        assert router.provider == provider

    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test initialize method."""
        router = RouterEngine()
        
        assert router._initialized is False
        await router.initialize()
        assert router._initialized is True
        
        # Second call should be no-op
        await router.initialize()
        assert router._initialized is True

    @pytest.mark.asyncio
    async def test_initialize_with_provider(self):
        """Test initialize with provider that has models."""
        provider = MagicMock()
        model_info = MagicMock()
        model_info.id = "test-model"
        model_info.supports_tools = True
        model_info.supports_vision = False
        model_info.supports_streaming = True
        model_info.context_length = 4096
        provider.models = [model_info]
        
        config = RouterConfig(provider="test-provider")
        router = RouterEngine(config=config, provider=provider)
        
        await router.initialize()
        
        assert "test-model" in router._models

    @pytest.mark.asyncio
    async def test_initialize_provider_error(self):
        """Test initialize handles provider errors."""
        provider = MagicMock()
        provider.models = MagicMock(side_effect=Exception("Provider error"))
        
        router = RouterEngine(provider=provider)
        
        # Should not raise
        await router.initialize()
        assert router._initialized is True

    @pytest.mark.asyncio
    async def test_route_disabled(self):
        """Test routing when disabled."""
        config = RouterConfig(enabled=False, fallback_model="fallback-model")
        router = RouterEngine(config=config)
        
        result = await router.route("test prompt")
        
        assert result.model_id == "fallback-model"
        assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_route_pinned_model(self):
        """Test routing with pinned model."""
        config = RouterConfig(pinned_model="pinned-model")
        router = RouterEngine(config=config)
        
        result = await router.route("test prompt")
        
        assert result.model_id == "pinned-model"
        assert result.confidence == 1.0
        assert "pinned" in result.reasoning.lower()

    @pytest.mark.asyncio
    async def test_route_with_cache(self):
        """Test routing uses cache."""
        config = RouterConfig(cache_enabled=True)
        router = RouterEngine(config=config)
        
        # Register a model
        router.register_model(ModelConfig(
            model_id="test-model",
            provider="test",
        ))
        
        result1 = await router.route("test prompt")
        assert result1.cached is False
        
        result2 = await router.route("test prompt")
        assert result2.cached is True

    @pytest.mark.asyncio
    async def test_route_no_cache(self):
        """Test routing without cache."""
        config = RouterConfig(cache_enabled=False)
        router = RouterEngine(config=config)
        
        router.register_model(ModelConfig(
            model_id="test-model",
            provider="test",
        ))
        
        result1 = await router.route("test prompt")
        result2 = await router.route("test prompt")
        
        # Both should not be cached
        assert result1.cached is False
        assert result2.cached is False

    @pytest.mark.asyncio
    async def test_route_excluded_model(self):
        """Test routing excludes specified models."""
        config = RouterConfig(excluded_models=["bad-model"])
        router = RouterEngine(config=config)
        
        router.register_model(ModelConfig(
            model_id="bad-model",
            provider="test",
            quality_score=0.9,
        ))
        router.register_model(ModelConfig(
            model_id="good-model",
            provider="test",
            quality_score=0.5,
        ))
        
        result = await router.route("test prompt")
        
        assert result.model_id == "good-model"

    @pytest.mark.asyncio
    async def test_route_included_models(self):
        """Test routing only uses included models."""
        config = RouterConfig(included_models=["included-model"])
        router = RouterEngine(config=config)
        
        router.register_model(ModelConfig(
            model_id="included-model",
            provider="test",
            quality_score=0.5,
        ))
        router.register_model(ModelConfig(
            model_id="excluded-model",
            provider="test",
            quality_score=0.9,
        ))
        
        result = await router.route("test prompt")
        
        assert result.model_id == "included-model"

    @pytest.mark.asyncio
    async def test_route_no_models_fallback(self):
        """Test routing with no models uses fallback."""
        config = RouterConfig(fallback_model="fallback-model")
        router = RouterEngine(config=config)
        
        result = await router.route("test prompt")
        
        assert result.model_id == "fallback-model"
        assert "fallback" in result.reasoning.lower()

    @pytest.mark.asyncio
    async def test_route_no_models_default(self):
        """Test routing with no models and no fallback."""
        router = RouterEngine()
        
        result = await router.route("test prompt")
        
        assert result.model_id == "default"
        assert result.confidence == 0.0

    def test_register_model(self):
        """Test register_model method."""
        router = RouterEngine()
        
        config = ModelConfig(model_id="new-model", provider="test")
        router.register_model(config)
        
        assert "new-model" in router._models

    def test_unregister_model(self):
        """Test unregister_model method."""
        router = RouterEngine()
        
        router.register_model(ModelConfig(model_id="test-model", provider="test"))
        assert "test-model" in router._models
        
        result = router.unregister_model("test-model")
        
        assert result is True
        assert "test-model" not in router._models

    def test_unregister_model_not_found(self):
        """Test unregister_model with non-existent model."""
        router = RouterEngine()
        
        result = router.unregister_model("non-existent")
        assert result is False

    def test_get_model(self):
        """Test get_model method."""
        router = RouterEngine()
        
        config = ModelConfig(model_id="test-model", provider="test")
        router.register_model(config)
        
        result = router.get_model("test-model")
        assert result.model_id == "test-model"

    def test_get_model_not_found(self):
        """Test get_model with non-existent model."""
        router = RouterEngine()
        
        result = router.get_model("non-existent")
        assert result is None

    def test_list_models(self):
        """Test list_models method."""
        router = RouterEngine()
        
        router.register_model(ModelConfig(model_id="model1", provider="test"))
        router.register_model(ModelConfig(model_id="model2", provider="test"))
        
        models = router.list_models()
        
        assert len(models) == 2
        model_ids = [m.model_id for m in models]
        assert "model1" in model_ids
        assert "model2" in model_ids

    def test_set_provider(self):
        """Test set_provider method."""
        router = RouterEngine()
        router._initialized = True
        
        provider = MagicMock()
        router.set_provider(provider)
        
        assert router.provider == provider
        assert router._initialized is False

    def test_get_stats(self):
        """Test get_stats method."""
        router = RouterEngine()
        router.register_model(ModelConfig(model_id="model1", provider="test"))
        
        stats = router.get_stats()
        
        assert stats["models_registered"] == 1
        assert stats["profiles_cached"] == 0


class TestRouterEngineScoring:
    """Tests for model scoring in RouterEngine."""

    def test_score_model_coding(self):
        """Test scoring for coding category."""
        router = RouterEngine()
        
        model = ModelConfig(
            model_id="coder",
            provider="test",
            coding_score=0.9,
            quality_score=0.8,
            speed_score=0.7,
        )
        
        classification = ClassificationResult(
            category=PromptCategory.CODING,
            complexity=Complexity.MEDIUM,
            confidence=0.9,
            indicators=["code pattern"],
            suggested_skills=["code_generation"],
        )
        
        score, reasoning = router._score_model(model, classification)
        
        assert score > 0
        assert "category score" in reasoning

    def test_score_model_with_tools(self):
        """Test scoring boost for tool support."""
        router = RouterEngine()
        
        model = ModelConfig(
            model_id="tool-model",
            provider="test",
            supports_tools=True,
            coding_score=0.8,
            quality_score=0.8,
            speed_score=0.8,
        )
        
        classification = ClassificationResult(
            category=PromptCategory.CODING,
            complexity=Complexity.MEDIUM,
            confidence=0.9,
            indicators=["code pattern"],
            suggested_skills=["code_generation"],
        )
        
        score, reasoning = router._score_model(model, classification)
        
        assert "supports tools" in reasoning

    def test_score_model_quality_preference(self):
        """Test scoring with quality preference."""
        config = RouterConfig(quality_preference=QualityPreference.QUALITY)
        router = RouterEngine(config=config)
        
        model = ModelConfig(
            model_id="quality-model",
            provider="test",
            quality_score=0.9,
            speed_score=0.5,
        )
        
        classification = ClassificationResult(
            category=PromptCategory.GENERAL,
            complexity=Complexity.MEDIUM,
            confidence=0.9,
            indicators=[],
            suggested_skills=[],
        )
        
        score, reasoning = router._score_model(model, classification)
        
        assert "quality preference" in reasoning

    def test_score_model_speed_preference(self):
        """Test scoring with speed preference."""
        config = RouterConfig(quality_preference=QualityPreference.SPEED)
        router = RouterEngine(config=config)
        
        model = ModelConfig(
            model_id="speed-model",
            provider="test",
            quality_score=0.5,
            speed_score=0.9,
        )
        
        classification = ClassificationResult(
            category=PromptCategory.GENERAL,
            complexity=Complexity.MEDIUM,
            confidence=0.9,
            indicators=[],
            suggested_skills=[],
        )
        
        score, reasoning = router._score_model(model, classification)
        
        assert "speed preference" in reasoning

    def test_score_model_balanced_preference(self):
        """Test scoring with balanced preference."""
        config = RouterConfig(quality_preference=QualityPreference.BALANCED)
        router = RouterEngine(config=config)
        
        model = ModelConfig(
            model_id="balanced-model",
            provider="test",
            quality_score=0.7,
            speed_score=0.7,
        )
        
        classification = ClassificationResult(
            category=PromptCategory.GENERAL,
            complexity=Complexity.MEDIUM,
            confidence=0.9,
            indicators=[],
            suggested_skills=[],
        )
        
        score, reasoning = router._score_model(model, classification)
        
        assert "balanced preference" in reasoning

    def test_score_model_hard_complexity(self):
        """Test scoring for hard complexity."""
        router = RouterEngine()
        
        model = ModelConfig(
            model_id="quality-model",
            provider="test",
            quality_score=0.9,
        )
        
        classification = ClassificationResult(
            category=PromptCategory.GENERAL,
            complexity=Complexity.HARD,
            confidence=0.9,
            indicators=[],
            suggested_skills=[],
        )
        
        score, reasoning = router._score_model(model, classification)
        
        assert "quality boost" in reasoning

    def test_score_model_simple_complexity(self):
        """Test scoring for simple complexity."""
        router = RouterEngine()
        
        model = ModelConfig(
            model_id="speed-model",
            provider="test",
            speed_score=0.9,
        )
        
        classification = ClassificationResult(
            category=PromptCategory.GENERAL,
            complexity=Complexity.SIMPLE,
            confidence=0.9,
            indicators=[],
            suggested_skills=[],
        )
        
        score, reasoning = router._score_model(model, classification)
        
        assert "speed boost" in reasoning

    def test_score_model_below_speed_threshold(self):
        """Test scoring penalty for low speed."""
        config = RouterConfig(min_speed_score=0.5)
        router = RouterEngine(config=config)
        
        model = ModelConfig(
            model_id="slow-model",
            provider="test",
            speed_score=0.3,
            quality_score=0.9,
        )
        
        classification = ClassificationResult(
            category=PromptCategory.GENERAL,
            complexity=Complexity.MEDIUM,
            confidence=0.9,
            indicators=[],
            suggested_skills=[],
        )
        
        score, reasoning = router._score_model(model, classification)
        
        assert "min speed threshold" in reasoning

    def test_score_model_below_quality_threshold(self):
        """Test scoring penalty for low quality."""
        config = RouterConfig(min_quality_score=0.5)
        router = RouterEngine(config=config)
        
        model = ModelConfig(
            model_id="low-quality-model",
            provider="test",
            quality_score=0.3,
            speed_score=0.9,
        )
        
        classification = ClassificationResult(
            category=PromptCategory.GENERAL,
            complexity=Complexity.MEDIUM,
            confidence=0.9,
            indicators=[],
            suggested_skills=[],
        )
        
        score, reasoning = router._score_model(model, classification)
        
        assert "min quality threshold" in reasoning


class TestRouterEngineProfileModels:
    """Tests for model profiling in RouterEngine."""

    @pytest.mark.asyncio
    async def test_profile_models_no_provider(self):
        """Test profile_models without provider."""
        router = RouterEngine()
        router.register_model(ModelConfig(model_id="test", provider="test"))
        
        profiles = await router.profile_models()
        
        assert profiles == {}

    @pytest.mark.asyncio
    async def test_profile_models_with_provider(self):
        """Test profile_models with provider."""
        router = RouterEngine(provider=MagicMock())
        router.register_model(ModelConfig(model_id="test-model", provider="test"))
        
        # Mock the profiler
        mock_profile = MagicMock()
        mock_profile._calculate_speed_score.return_value = 0.8
        mock_profile.overall_quality = 0.9
        mock_profile.coding_score = 0.85
        mock_profile.reasoning_score = 0.9
        mock_profile.creative_score = 0.8
        mock_profile.math_score = 0.85
        
        with patch.object(router.profiler, 'quick_profile', new_callable=AsyncMock) as mock_quick:
            mock_quick.return_value = mock_profile
            
            profiles = await router.profile_models()
            
            assert "test-model" in profiles
            assert router._models["test-model"].speed_score == 0.8
            assert router._models["test-model"].quality_score == 0.9

    @pytest.mark.asyncio
    async def test_profile_models_error(self):
        """Test profile_models handles errors."""
        router = RouterEngine(provider=MagicMock())
        router.register_model(ModelConfig(model_id="test-model", provider="test"))
        
        with patch.object(router.profiler, 'quick_profile', new_callable=AsyncMock) as mock_quick:
            mock_quick.side_effect = Exception("Profile error")
            
            profiles = await router.profile_models()
            
            # Should not crash, just log error
            assert "test-model" not in profiles


class TestModelConfig:
    """Tests for ModelConfig."""

    def test_default_values(self):
        """Test ModelConfig default values."""
        config = ModelConfig(model_id="test", provider="test")
        
        assert config.quality_score == 0.5
        assert config.speed_score == 0.5
        assert config.coding_score == 0.5
        assert config.reasoning_score == 0.5
        assert config.creative_score == 0.5
        assert config.math_score == 0.5
        assert config.supports_tools is False
        assert config.supports_vision is False
        assert config.supports_streaming is True


class TestRouterConfig:
    """Tests for RouterConfig."""

    def test_default_values(self):
        """Test RouterConfig default values."""
        config = RouterConfig()
        
        assert config.enabled is True
        assert config.cache_enabled is True
        assert config.quality_preference == QualityPreference.BALANCED
        assert config.fallback_model is None
        assert config.pinned_model is None
        assert config.excluded_models == []
        assert config.included_models == []