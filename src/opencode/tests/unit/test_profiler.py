"""
Tests for Model Profiler.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from opencode.router.profiler import ModelProfile, BenchmarkResult, ModelProfiler
from opencode.router.config import PromptCategory


class TestModelProfile:
    """Tests for ModelProfile dataclass."""

    def test_init_defaults(self):
        """Test ModelProfile initialization with defaults."""
        profile = ModelProfile(model_id="test-model", provider="test-provider")
        
        assert profile.model_id == "test-model"
        assert profile.provider == "test-provider"
        assert profile.avg_latency_ms == 0.0
        assert profile.tokens_per_second == 0.0
        assert profile.time_to_first_token_ms == 0.0
        assert profile.coding_score == 0.5
        assert profile.reasoning_score == 0.5
        assert profile.creative_score == 0.5
        assert profile.math_score == 0.5
        assert profile.general_score == 0.5
        assert profile.overall_quality == 0.5
        assert profile.instruction_following == 0.5
        assert profile.vram_required_gb is None
        assert profile.context_length == 4096
        assert profile.supports_tools is False
        assert profile.supports_vision is False
        assert profile.supports_streaming is True
        assert profile.profiled_at is None
        assert profile.benchmark_count == 0

    def test_init_custom_values(self):
        """Test ModelProfile initialization with custom values."""
        profile = ModelProfile(
            model_id="test-model",
            provider="test-provider",
            avg_latency_ms=150.5,
            tokens_per_second=45.0,
            time_to_first_token_ms=50.0,
            coding_score=0.9,
            reasoning_score=0.8,
            creative_score=0.7,
            math_score=0.6,
            general_score=0.75,
            overall_quality=0.85,
            instruction_following=0.9,
            vram_required_gb=16.0,
            context_length=8192,
            supports_tools=True,
            supports_vision=True,
            supports_streaming=False,
            benchmark_count=10,
        )
        
        assert profile.avg_latency_ms == 150.5
        assert profile.tokens_per_second == 45.0
        assert profile.coding_score == 0.9
        assert profile.supports_tools is True
        assert profile.supports_vision is True
        assert profile.supports_streaming is False
        assert profile.vram_required_gb == 16.0
        assert profile.context_length == 8192

    def test_to_config(self):
        """Test converting ModelProfile to ModelConfig."""
        profile = ModelProfile(
            model_id="test-model",
            provider="test-provider",
            tokens_per_second=25.0,
            overall_quality=0.85,
            coding_score=0.9,
            reasoning_score=0.8,
            creative_score=0.7,
            math_score=0.6,
            supports_tools=True,
            supports_vision=True,
            vram_required_gb=16.0,
            context_length=8192,
        )
        
        config = profile.to_config()
        
        assert config.model_id == "test-model"
        assert config.provider == "test-provider"
        assert config.supports_tools is True
        assert config.supports_vision is True
        assert config.vram_required_gb == 16.0
        assert config.context_length == 8192
        assert config.quality_score == 0.85
        assert config.coding_score == 0.9
        assert config.reasoning_score == 0.8

    def test_calculate_speed_score_zero(self):
        """Test speed score calculation with zero tps."""
        profile = ModelProfile(model_id="test", provider="test", tokens_per_second=0)
        score = profile._calculate_speed_score()
        assert score == 0.5

    def test_calculate_speed_score_negative(self):
        """Test speed score calculation with negative tps."""
        profile = ModelProfile(model_id="test", provider="test", tokens_per_second=-10)
        score = profile._calculate_speed_score()
        assert score == 0.5

    def test_calculate_speed_score_fast(self):
        """Test speed score calculation with fast tps."""
        profile = ModelProfile(model_id="test", provider="test", tokens_per_second=50)
        score = profile._calculate_speed_score()
        assert score == 1.0

    def test_calculate_speed_score_medium(self):
        """Test speed score calculation with medium tps."""
        profile = ModelProfile(model_id="test", provider="test", tokens_per_second=25)
        score = profile._calculate_speed_score()
        assert score == 0.5

    def test_calculate_speed_score_slow(self):
        """Test speed score calculation with slow tps."""
        profile = ModelProfile(model_id="test", provider="test", tokens_per_second=5)
        score = profile._calculate_speed_score()
        assert score == 0.1  # Minimum score

    def test_calculate_speed_score_very_fast(self):
        """Test speed score calculation with very fast tps (capped)."""
        profile = ModelProfile(model_id="test", provider="test", tokens_per_second=100)
        score = profile._calculate_speed_score()
        assert score == 1.0  # Capped at 1.0


class TestBenchmarkResult:
    """Tests for BenchmarkResult dataclass."""

    def test_init_success(self):
        """Test BenchmarkResult initialization for successful run."""
        result = BenchmarkResult(
            prompt="Test prompt",
            response="Test response",
            latency_ms=100.0,
            tokens_generated=50,
            tokens_per_second=25.0,
            time_to_first_token_ms=50.0,
            success=True,
        )
        
        assert result.prompt == "Test prompt"
        assert result.response == "Test response"
        assert result.latency_ms == 100.0
        assert result.tokens_generated == 50
        assert result.tokens_per_second == 25.0
        assert result.time_to_first_token_ms == 50.0
        assert result.success is True
        assert result.error is None

    def test_init_failure(self):
        """Test BenchmarkResult initialization for failed run."""
        result = BenchmarkResult(
            prompt="Test prompt",
            response="",
            latency_ms=0.0,
            tokens_generated=0,
            tokens_per_second=0.0,
            time_to_first_token_ms=0.0,
            success=False,
            error="Connection timeout",
        )
        
        assert result.success is False
        assert result.error == "Connection timeout"


class TestModelProfiler:
    """Tests for ModelProfiler class."""

    def test_init(self):
        """Test ModelProfiler initialization."""
        profiler = ModelProfiler()
        assert profiler.timeout_seconds == 90
        assert profiler._profiles == {}

    def test_init_custom_timeout(self):
        """Test ModelProfiler initialization with custom timeout."""
        profiler = ModelProfiler(timeout_seconds=120)
        assert profiler.timeout_seconds == 120

    def test_benchmark_prompts_defined(self):
        """Test that benchmark prompts are defined for all categories."""
        profiler = ModelProfiler()
        
        assert PromptCategory.CODING in profiler.BENCHMARK_PROMPTS
        assert PromptCategory.REASONING in profiler.BENCHMARK_PROMPTS
        assert PromptCategory.CREATIVE in profiler.BENCHMARK_PROMPTS
        assert PromptCategory.MATH in profiler.BENCHMARK_PROMPTS
        assert PromptCategory.GENERAL in profiler.BENCHMARK_PROMPTS
        
        # Each category should have at least one prompt
        for category, prompts in profiler.BENCHMARK_PROMPTS.items():
            assert len(prompts) > 0, f"No prompts for {category}"

    def test_benchmark_prompts_content(self):
        """Test that benchmark prompts have appropriate content."""
        profiler = ModelProfiler()
        
        # Coding prompts should mention code-related terms
        coding_prompts = profiler.BENCHMARK_PROMPTS[PromptCategory.CODING]
        assert any("function" in p.lower() or "code" in p.lower() for p in coding_prompts)
        
        # Math prompts should have math-related content
        math_prompts = profiler.BENCHMARK_PROMPTS[PromptCategory.MATH]
        assert len(math_prompts) > 0

    @pytest.mark.asyncio
    async def test_profile_model_mock_provider(self):
        """Test profiling a model with a mock provider."""
        profiler = ModelProfiler(timeout_seconds=30)
        
        # Create mock provider
        mock_provider = MagicMock()
        mock_provider.name = "test-provider"
        mock_provider.complete = AsyncMock(return_value=MagicMock(
            content="Test response content",
            usage=MagicMock(input_tokens=10, output_tokens=20),
        ))
        
        # Mock the _run_benchmark method
        with patch.object(profiler, "_run_benchmark", new_callable=AsyncMock) as mock_benchmark:
            mock_benchmark.return_value = BenchmarkResult(
                prompt="Test prompt",
                response="Test response",
                latency_ms=100.0,
                tokens_generated=20,
                tokens_per_second=25.0,
                time_to_first_token_ms=50.0,
                success=True,
            )
            
            profile = await profiler.profile_model(
                provider=mock_provider,
                model_id="test-model",
                categories=[PromptCategory.GENERAL],
            )
            
            assert profile.model_id == "test-model"
            assert profile.provider == "test-provider"
            assert profile.benchmark_count > 0

    @pytest.mark.asyncio
    async def test_profile_model_all_categories(self):
        """Test profiling with all categories."""
        profiler = ModelProfiler(timeout_seconds=30)
        
        mock_provider = MagicMock()
        mock_provider.name = "test-provider"
        
        with patch.object(profiler, "_run_benchmark", new_callable=AsyncMock) as mock_benchmark:
            mock_benchmark.return_value = BenchmarkResult(
                prompt="Test",
                response="Response",
                latency_ms=100.0,
                tokens_generated=10,
                tokens_per_second=10.0,
                time_to_first_token_ms=50.0,
                success=True,
            )
            
            profile = await profiler.profile_model(
                provider=mock_provider,
                model_id="test-model",
                categories=None,  # All categories
            )
            
            # Should have been called for each prompt in all categories
            assert mock_benchmark.call_count > 0

    @pytest.mark.asyncio
    async def test_profile_model_timeout(self):
        """Test handling timeout during profiling."""
        profiler = ModelProfiler(timeout_seconds=1)
        
        mock_provider = MagicMock()
        mock_provider.name = "test-provider"
        
        with patch.object(profiler, "_run_benchmark", new_callable=AsyncMock) as mock_benchmark:
            mock_benchmark.side_effect = asyncio.TimeoutError()
            
            profile = await profiler.profile_model(
                provider=mock_provider,
                model_id="test-model",
                categories=[PromptCategory.GENERAL],
            )
            
            # Should handle timeout gracefully
            assert profile.model_id == "test-model"
            assert profile.benchmark_count == 0

    @pytest.mark.asyncio
    async def test_profile_model_error(self):
        """Test handling errors during profiling."""
        profiler = ModelProfiler(timeout_seconds=30)
        
        mock_provider = MagicMock()
        mock_provider.name = "test-provider"
        
        with patch.object(profiler, "_run_benchmark", new_callable=AsyncMock) as mock_benchmark:
            mock_benchmark.side_effect = Exception("Test error")
            
            profile = await profiler.profile_model(
                provider=mock_provider,
                model_id="test-model",
                categories=[PromptCategory.GENERAL],
            )
            
            # Should handle error gracefully
            assert profile.model_id == "test-model"


class TestModelProfilerIntegration:
    """Integration tests for ModelProfiler."""

    def test_profile_storage(self):
        """Test that profiles can be stored."""
        profiler = ModelProfiler()
        
        profile = ModelProfile(model_id="test-model", provider="test-provider")
        profiler._profiles["test-model"] = profile
        
        assert "test-model" in profiler._profiles
        assert profiler._profiles["test-model"].model_id == "test-model"

    def test_multiple_profiles(self):
        """Test storing multiple profiles."""
        profiler = ModelProfiler()
        
        profiler._profiles["model-1"] = ModelProfile(model_id="model-1", provider="provider-1")
        profiler._profiles["model-2"] = ModelProfile(model_id="model-2", provider="provider-2")
        
        assert len(profiler._profiles) == 2
        assert "model-1" in profiler._profiles
        assert "model-2" in profiler._profiles
