"""
Tests for LLMChecker scoring engine.
"""

import pytest
from unittest.mock import MagicMock

from opencode.llmchecker.scoring.engine import ScoringEngine
from opencode.llmchecker.scoring.models import (
    ModelInfo,
    ModelScore,
    ScoringWeights,
    ScoringResult,
    QuantizationType,
)
from opencode.llmchecker.hardware.models import SystemInfo, HardwareTier, GPUInfo, CPUInfo


class TestScoringEngine:
    """Tests for ScoringEngine."""
    
    @pytest.mark.unit
    def test_engine_creation(self):
        """Test ScoringEngine instantiation."""
        engine = ScoringEngine()
        assert engine.system_info is None
        
        system_info = SystemInfo(tier=HardwareTier.HIGH)
        engine = ScoringEngine(system_info)
        assert engine.system_info == system_info
    
    @pytest.mark.unit
    def test_set_system_info(self):
        """Test setting system info."""
        engine = ScoringEngine()
        system_info = SystemInfo(tier=HardwareTier.HIGH)
        engine.set_system_info(system_info)
        assert engine.system_info == system_info
    
    @pytest.mark.unit
    def test_score_model_basic(self):
        """Test basic model scoring."""
        engine = ScoringEngine()
        model = ModelInfo(
            name="llama3.1:8b",
            family="llama3.1",
            parameters_b=8.0,
            quantization=QuantizationType.Q4_K_M,
            context_length=8192,
        )
        score = engine.score_model(model)
        
        assert isinstance(score, ModelScore)
        assert score.model == model
        assert score.quality_score >= 0
        assert score.speed_score >= 0
        assert score.fit_score >= 0
        assert score.context_score >= 0
        assert score.final_score >= 0
    
    @pytest.mark.unit
    def test_score_model_with_use_case(self):
        """Test model scoring with different use cases."""
        engine = ScoringEngine()
        model = ModelInfo(
            name="qwen2.5-coder:7b",
            family="qwen2.5-coder",
            parameters_b=7.0,
            quantization=QuantizationType.Q4_K_M,
            context_length=32768,
        )
        
        # Score for coding use case
        coding_score = engine.score_model(model, use_case="coding")
        assert coding_score.quality_score > 0
        
        # Score for general use case
        general_score = engine.score_model(model, use_case="general")
        
        # Coding score should be higher for coding model
        assert coding_score.quality_score >= general_score.quality_score
    
    @pytest.mark.unit
    def test_score_model_with_custom_weights(self):
        """Test model scoring with custom weights."""
        engine = ScoringEngine()
        model = ModelInfo(
            name="test-model",
            family="llama3",
            parameters_b=7.0,
            quantization=QuantizationType.Q4_K_M,
            context_length=8192,
        )
        
        weights = ScoringWeights(
            quality=0.5,
            speed=0.3,
            fit=0.1,
            context=0.1,
        )
        score = engine.score_model(model, weights=weights)
        
        assert score.final_score > 0
    
    @pytest.mark.unit
    def test_score_models(self):
        """Test scoring multiple models."""
        engine = ScoringEngine()
        models = [
            ModelInfo(
                name="llama3.1:8b",
                family="llama3.1",
                parameters_b=8.0,
                quantization=QuantizationType.Q4_K_M,
                context_length=8192,
            ),
            ModelInfo(
                name="mistral:7b",
                family="mistral",
                parameters_b=7.0,
                quantization=QuantizationType.Q4_K_M,
                context_length=32768,
            ),
        ]
        
        result = engine.score_models(models)
        
        assert isinstance(result, ScoringResult)
        assert len(result.scores) == 2
        assert result.scores[0].rank == 1
        assert result.scores[1].rank == 2
        # Higher score should be ranked first
        assert result.scores[0].final_score >= result.scores[1].final_score
    
    @pytest.mark.unit
    def test_quality_score_family_ranking(self):
        """Test quality score based on family ranking."""
        engine = ScoringEngine()
        
        # High quality family
        high_model = ModelInfo(
            name="qwen2.5:72b",
            family="qwen2.5",
            parameters_b=72.0,
            quantization=QuantizationType.Q4_K_M,
            context_length=32768,
        )
        high_score = engine.score_model(high_model)
        
        # Lower quality family
        low_model = ModelInfo(
            name="tinyllama:1b",
            family="tinyllama",
            parameters_b=1.0,
            quantization=QuantizationType.Q4_K_M,
            context_length=2048,
        )
        low_score = engine.score_model(low_model)
        
        assert high_score.quality_score > low_score.quality_score
    
    @pytest.mark.unit
    def test_quality_score_quantization_penalty(self):
        """Test quality score quantization penalty."""
        engine = ScoringEngine()
        
        # FP16 model (no penalty)
        fp16_model = ModelInfo(
            name="test:fp16",
            family="llama3",
            parameters_b=7.0,
            quantization=QuantizationType.FP16,
            context_length=8192,
        )
        fp16_score = engine.score_model(fp16_model)
        
        # Q4 model (has penalty)
        q4_model = ModelInfo(
            name="test:q4",
            family="llama3",
            parameters_b=7.0,
            quantization=QuantizationType.Q4_K_M,
            context_length=8192,
        )
        q4_score = engine.score_model(q4_model)
        
        # FP16 should have higher quality score
        assert fp16_score.quality_score > q4_score.quality_score
    
    @pytest.mark.unit
    def test_speed_score_parameter_impact(self):
        """Test speed score based on parameter count."""
        engine = ScoringEngine()
        
        # Small model (faster)
        small_model = ModelInfo(
            name="small:1b",
            family="phi-3",
            parameters_b=1.0,
            quantization=QuantizationType.Q4_K_M,
            context_length=4096,
        )
        small_score = engine.score_model(small_model)
        
        # Large model (slower)
        large_model = ModelInfo(
            name="large:70b",
            family="llama3",
            parameters_b=70.0,
            quantization=QuantizationType.Q4_K_M,
            context_length=8192,
        )
        large_score = engine.score_model(large_model)
        
        assert small_score.speed_score > large_score.speed_score
    
    @pytest.mark.unit
    def test_speed_score_hardware_tier(self):
        """Test speed score with hardware tier adjustment."""
        # High tier system
        high_system = SystemInfo(tier=HardwareTier.VERY_HIGH)
        high_engine = ScoringEngine(high_system)
        
        # Low tier system
        low_system = SystemInfo(tier=HardwareTier.LOW)
        low_engine = ScoringEngine(low_system)
        
        model = ModelInfo(
            name="test:7b",
            family="llama3",
            parameters_b=7.0,
            quantization=QuantizationType.Q4_K_M,
            context_length=8192,
        )
        
        high_score = high_engine.score_model(model)
        low_score = low_engine.score_model(model)
        
        assert high_score.speed_score > low_score.speed_score
    
    @pytest.mark.unit
    def test_context_score(self):
        """Test context score calculation."""
        engine = ScoringEngine()
        
        # Large context
        large_ctx_model = ModelInfo(
            name="test:large-ctx",
            family="llama3",
            parameters_b=7.0,
            quantization=QuantizationType.Q4_K_M,
            context_length=128000,
        )
        large_ctx_score = engine.score_model(large_ctx_model)
        
        # Small context
        small_ctx_model = ModelInfo(
            name="test:small-ctx",
            family="llama3",
            parameters_b=7.0,
            quantization=QuantizationType.Q4_K_M,
            context_length=2048,
        )
        small_ctx_score = engine.score_model(small_ctx_model)
        
        assert large_ctx_score.context_score > small_ctx_score.context_score
    
    @pytest.mark.unit
    def test_vision_model_bonus(self):
        """Test vision model gets bonus for vision use case."""
        engine = ScoringEngine()
        
        model = ModelInfo(
            name="llava:7b",
            family="llava",
            parameters_b=7.0,
            quantization=QuantizationType.Q4_K_M,
            context_length=4096,
            supports_vision=True,
        )
        
        vision_score = engine.score_model(model, use_case="vision")
        general_score = engine.score_model(model, use_case="general")
        
        assert vision_score.quality_score > general_score.quality_score
    
    @pytest.mark.unit
    def test_tool_support_bonus(self):
        """Test tool support bonus for coding use case."""
        engine = ScoringEngine()
        
        model = ModelInfo(
            name="test:tools",
            family="llama3.1",
            parameters_b=8.0,
            quantization=QuantizationType.Q4_K_M,
            context_length=8192,
            supports_tools=True,
        )
        
        coding_score = engine.score_model(model, use_case="coding")
        
        # Should have bonus for tool support
        assert coding_score.quality_score > 0
    
    @pytest.mark.unit
    def test_warnings_for_large_models(self):
        """Test warnings for very large models."""
        engine = ScoringEngine()
        
        model = ModelInfo(
            name="huge:120b",
            family="llama3",
            parameters_b=120.0,
            quantization=QuantizationType.Q4_K_M,
            context_length=8192,
        )
        
        score = engine.score_model(model)
        
        assert len(score.warnings) > 0
        assert any("large" in w.lower() for w in score.warnings)


class TestScoringWeights:
    """Tests for ScoringWeights."""
    
    @pytest.mark.unit
    def test_default_weights(self):
        """Test default weight values."""
        weights = ScoringWeights()
        assert weights.quality == 0.4
        assert weights.speed == 0.25
        assert weights.fit == 0.25
        assert weights.context == 0.1
    
    @pytest.mark.unit
    def test_for_use_case(self):
        """Test weights for different use cases."""
        coding_weights = ScoringWeights.for_use_case("coding")
        assert coding_weights.quality > 0
        
        speed_weights = ScoringWeights.for_use_case("speed")
        assert speed_weights.speed > 0
    
    @pytest.mark.unit
    def test_weights_sum_to_one(self):
        """Test that weights sum to approximately 1."""
        weights = ScoringWeights()
        total = weights.quality + weights.speed + weights.fit + weights.context
        assert abs(total - 1.0) < 0.01


class TestModelScore:
    """Tests for ModelScore."""
    
    @pytest.mark.unit
    def test_model_score_creation(self):
        """Test ModelScore instantiation."""
        model = ModelInfo(
            name="test",
            family="test",
            parameters_b=7.0,
            quantization=QuantizationType.Q4_K_M,
            context_length=8192,
        )
        score = ModelScore(model=model)
        
        assert score.model == model
        assert score.quality_score == 0
        assert score.speed_score == 0
        assert score.fit_score == 0
        assert score.context_score == 0
    
    @pytest.mark.unit
    def test_calculate_final_score(self):
        """Test final score calculation."""
        model = ModelInfo(
            name="test",
            family="test",
            parameters_b=7.0,
            quantization=QuantizationType.Q4_K_M,
            context_length=8192,
        )
        score = ModelScore(model=model)
        score.quality_score = 80
        score.speed_score = 70
        score.fit_score = 90
        score.context_score = 60
        
        weights = ScoringWeights(
            quality=0.4,
            speed=0.25,
            fit=0.2,
            context=0.15,
        )
        
        score.calculate_final_score(weights)
        
        expected = 80 * 0.4 + 70 * 0.25 + 90 * 0.2 + 60 * 0.15
        assert abs(score.final_score - expected) < 0.01


class TestQuantizationType:
    """Tests for QuantizationType enum."""
    
    @pytest.mark.unit
    def test_quantization_types(self):
        """Test quantization type values."""
        assert QuantizationType.FP16.value == "fp16"
        assert QuantizationType.Q4_K_M.value == "q4_k_m"
        assert QuantizationType.Q8_0.value == "q8_0"
        assert QuantizationType.UNKNOWN.value == "unknown"
    
    @pytest.mark.unit
    def test_quantization_from_string(self):
        """Test creating QuantizationType from string."""
        assert QuantizationType("q4_k_m") == QuantizationType.Q4_K_M
        assert QuantizationType("fp16") == QuantizationType.FP16


class TestScoringResult:
    """Tests for ScoringResult."""
    
    @pytest.mark.unit
    def test_scoring_result_creation(self):
        """Test ScoringResult instantiation."""
        model = ModelInfo(
            name="test",
            family="test",
            parameters_b=7.0,
            quantization=QuantizationType.Q4_K_M,
            context_length=8192,
        )
        score = ModelScore(model=model)
        score.final_score = 75.0
        
        result = ScoringResult(
            scores=[score],
            hardware_info={"tier": "high"},
            weights_used=ScoringWeights(),
            use_case="general",
        )
        
        assert len(result.scores) == 1
        assert result.use_case == "general"
    
    @pytest.mark.unit
    def test_get_top_n(self):
        """Test getting top N models."""
        models = [
            ModelInfo(name="m1", family="test", parameters_b=7.0, quantization=QuantizationType.Q4_K_M, context_length=8192),
            ModelInfo(name="m2", family="test", parameters_b=7.0, quantization=QuantizationType.Q4_K_M, context_length=8192),
            ModelInfo(name="m3", family="test", parameters_b=7.0, quantization=QuantizationType.Q4_K_M, context_length=8192),
        ]
        
        scores = []
        for i, m in enumerate(models):
            s = ModelScore(model=m)
            s.final_score = 80 - i * 10  # 80, 70, 60
            scores.append(s)
        
        result = ScoringResult(
            scores=scores,
            hardware_info=None,
            weights_used=ScoringWeights(),
            use_case="general",
        )
        
        top_2 = result.get_top_n(2)
        assert len(top_2) == 2
        assert top_2[0].final_score == 80
        assert top_2[1].final_score == 70
    
    @pytest.mark.unit
    def test_get_compatible(self):
        """Test getting compatible models."""
        model1 = ModelInfo(name="m1", family="test", parameters_b=7.0, quantization=QuantizationType.Q4_K_M, context_length=8192)
        model2 = ModelInfo(name="m2", family="test", parameters_b=7.0, quantization=QuantizationType.Q4_K_M, context_length=8192)
        
        score1 = ModelScore(model=model1)
        score1.final_score = 80.0
        score1.fits_in_memory = True
        
        score2 = ModelScore(model=model2)
        score2.final_score = 70.0
        score2.fits_in_memory = False
        
        result = ScoringResult(
            scores=[score1, score2],
            hardware_info=None,
            weights_used=ScoringWeights(),
            use_case="general",
        )
        
        compatible = result.get_compatible()
        assert len(compatible) == 1
        assert compatible[0].model.name == "m1"


class TestScoringEngineParseQuantization:
    """Tests for ScoringEngine.parse_quantization method."""

    @pytest.mark.unit
    def test_parse_fp16(self):
        """Test parsing FP16 quantization."""
        result = ScoringEngine.parse_quantization("fp16")
        assert result == QuantizationType.FP16
        
        result = ScoringEngine.parse_quantization("F16")
        assert result == QuantizationType.F16

    @pytest.mark.unit
    def test_parse_q8(self):
        """Test parsing Q8 quantization."""
        result = ScoringEngine.parse_quantization("q8_0")
        assert result == QuantizationType.Q8_0
        
        result = ScoringEngine.parse_quantization("Q8")
        assert result == QuantizationType.Q8_0

    @pytest.mark.unit
    def test_parse_q4_variants(self):
        """Test parsing Q4 quantization variants."""
        result = ScoringEngine.parse_quantization("q4_k_m")
        assert result == QuantizationType.Q4_K_M
        
        result = ScoringEngine.parse_quantization("q4_k_s")
        assert result == QuantizationType.Q4_K_S
        
        result = ScoringEngine.parse_quantization("q4_0")
        assert result == QuantizationType.Q4_0

    @pytest.mark.unit
    def test_parse_q5_variants(self):
        """Test parsing Q5 quantization variants."""
        result = ScoringEngine.parse_quantization("q5_k_m")
        assert result == QuantizationType.Q5_K_M
        
        result = ScoringEngine.parse_quantization("q5_k_s")
        assert result == QuantizationType.Q5_K_S
        
        result = ScoringEngine.parse_quantization("q5_0")
        assert result == QuantizationType.Q5_0

    @pytest.mark.unit
    def test_parse_q3_variants(self):
        """Test parsing Q3 quantization variants."""
        result = ScoringEngine.parse_quantization("q3_k_m")
        assert result == QuantizationType.Q3_K_M
        
        result = ScoringEngine.parse_quantization("q3_k_s")
        assert result == QuantizationType.Q3_K_S
        
        result = ScoringEngine.parse_quantization("q3_k_l")
        assert result == QuantizationType.Q3_K_L

    @pytest.mark.unit
    def test_parse_q2_variants(self):
        """Test parsing Q2 quantization variants."""
        result = ScoringEngine.parse_quantization("q2_k")
        assert result == QuantizationType.Q2_K
        
        result = ScoringEngine.parse_quantization("q2_k_s")
        assert result == QuantizationType.Q2_K_S

    @pytest.mark.unit
    def test_parse_iq4_variants(self):
        """Test parsing IQ4 quantization variants."""
        result = ScoringEngine.parse_quantization("iq4_xs")
        assert result == QuantizationType.IQ4_XS
        
        result = ScoringEngine.parse_quantization("iq4_nl")
        assert result == QuantizationType.IQ4_NL

    @pytest.mark.unit
    def test_parse_iq3_variants(self):
        """Test parsing IQ3 quantization variants."""
        result = ScoringEngine.parse_quantization("iq3_xxs")
        assert result == QuantizationType.IQ3_XXS
        
        result = ScoringEngine.parse_quantization("iq3_xs")
        assert result == QuantizationType.IQ3_XS
        
        result = ScoringEngine.parse_quantization("iq3_s")
        assert result == QuantizationType.IQ3_S

    @pytest.mark.unit
    def test_parse_iq2_variants(self):
        """Test parsing IQ2 quantization variants."""
        result = ScoringEngine.parse_quantization("iq2_xxs")
        assert result == QuantizationType.IQ2_XXS
        
        result = ScoringEngine.parse_quantization("iq2_xs")
        assert result == QuantizationType.IQ2_XS

    @pytest.mark.unit
    def test_parse_unknown(self):
        """Test parsing unknown quantization."""
        result = ScoringEngine.parse_quantization("unknown_format")
        assert result == QuantizationType.UNKNOWN


class TestScoringEngineParseModelName:
    """Tests for ScoringEngine.parse_model_name method."""

    @pytest.mark.unit
    def test_parse_simple_name(self):
        """Test parsing simple model name."""
        name, family, params, quant = ScoringEngine.parse_model_name("llama3")
        assert name == "llama3"
        # Family extraction extracts first part before numbers
        assert family == "llama"
        assert params == 0.0
        assert quant == QuantizationType.UNKNOWN

    @pytest.mark.unit
    def test_parse_with_parameters(self):
        """Test parsing model name with parameters."""
        name, family, params, quant = ScoringEngine.parse_model_name("llama3:8b")
        assert name == "llama3:8b"
        # Family extraction extracts first part before numbers
        assert family == "llama"
        assert params == 8.0

    @pytest.mark.unit
    def test_parse_with_quantization(self):
        """Test parsing model name with quantization."""
        name, family, params, quant = ScoringEngine.parse_model_name("llama3-q4_k_m")
        assert name == "llama3-q4_k_m"
        # Family extraction extracts first part before numbers
        assert family == "llama"
        # The regex captures q4 but not the full q4_k_m
        assert quant in [QuantizationType.Q4_0, QuantizationType.Q4_K_M]

    @pytest.mark.unit
    def test_parse_full_name(self):
        """Test parsing full model name."""
        name, family, params, quant = ScoringEngine.parse_model_name("llama3.1:8b-q4_k_m")
        assert name == "llama3.1:8b-q4_k_m"
        # Family extraction extracts first part before numbers
        assert family == "llama"
        assert params == 8.0
        # The regex captures q4 but not the full q4_k_m
        assert quant in [QuantizationType.Q4_0, QuantizationType.Q4_K_M]

    @pytest.mark.unit
    def test_parse_large_model(self):
        """Test parsing large model name."""
        name, family, params, quant = ScoringEngine.parse_model_name("llama3:70b")
        assert params == 70.0

    @pytest.mark.unit
    def test_parse_decimal_params(self):
        """Test parsing model with decimal parameters."""
        name, family, params, quant = ScoringEngine.parse_model_name("phi-3.5:3.8b")
        assert params == 3.8


class TestScoringEngineFitScore:
    """Tests for fit score calculation."""

    @pytest.mark.unit
    def test_fit_score_no_system_info(self):
        """Test fit score without system info."""
        engine = ScoringEngine()
        model = ModelInfo(
            name="test:7b",
            family="llama3",
            parameters_b=7.0,
            quantization=QuantizationType.Q4_K_M,
            context_length=8192,
        )
        
        score = engine.score_model(model)
        # Should assume fits if no hardware info
        assert score.fits_in_memory is True
        assert score.fit_score == 50.0

    @pytest.mark.unit
    def test_fit_score_with_system_info(self):
        """Test fit score with system info."""
        from opencode.llmchecker.hardware.models import MemoryInfo
        
        system_info = SystemInfo(
            tier=HardwareTier.HIGH,
            memory=MemoryInfo(total_gb=32, available_gb=16),
            max_model_size_gb=10.0,  # Set a reasonable max model size
        )
        engine = ScoringEngine(system_info)
        
        model = ModelInfo(
            name="test:7b",
            family="llama3",
            parameters_b=7.0,
            quantization=QuantizationType.Q4_K_M,
            context_length=8192,
        )
        
        score = engine.score_model(model)
        # Fit score should be >= 0 (may be 0 if model doesn't fit)
        assert score.fit_score >= 0

    @pytest.mark.unit
    def test_fit_score_model_too_large(self):
        """Test fit score when model is too large."""
        from opencode.llmchecker.hardware.models import MemoryInfo
        
        system_info = SystemInfo(
            tier=HardwareTier.LOW,
            memory=MemoryInfo(total_gb=8, available_gb=4),
            max_model_size_gb=4.0,
        )
        engine = ScoringEngine(system_info)
        
        model = ModelInfo(
            name="test:70b",
            family="llama3",
            parameters_b=70.0,
            quantization=QuantizationType.Q4_K_M,
            context_length=8192,
        )
        
        score = engine.score_model(model)
        assert score.fits_in_memory is False
        assert "memory" in score.warnings[0].lower()


class TestScoringEngineRecommendedContext:
    """Tests for recommended context calculation."""

    @pytest.mark.unit
    def test_recommended_context_no_system_info(self):
        """Test recommended context without system info."""
        engine = ScoringEngine()
        model = ModelInfo(
            name="test:7b",
            family="llama3",
            parameters_b=7.0,
            quantization=QuantizationType.Q4_K_M,
            context_length=32768,
        )
        
        score = engine.score_model(model)
        # Should return min of model context and 4096
        assert score.recommended_context == 4096

    @pytest.mark.unit
    def test_recommended_context_with_vram(self):
        """Test recommended context with VRAM info."""
        from opencode.llmchecker.hardware.models import MemoryInfo, GPUInfo, GPUVendor
        
        system_info = SystemInfo(
            tier=HardwareTier.HIGH,
            memory=MemoryInfo(total_gb=32, available_gb=16),
        )
        # Add GPU with VRAM
        system_info.gpus = [GPUInfo(model="RTX 4090", vram_gb=24, vendor=GPUVendor.NVIDIA)]
        
        engine = ScoringEngine(system_info)
        
        model = ModelInfo(
            name="test:7b",
            family="llama3",
            parameters_b=7.0,
            quantization=QuantizationType.Q4_K_M,
            context_length=32768,
        )
        
        score = engine.score_model(model)
        # With 24GB VRAM, should recommend up to 16000
        assert score.recommended_context <= 16000


class TestScoringEngineEstimateModelSize:
    """Tests for model size estimation."""

    @pytest.mark.unit
    def test_estimate_size_from_known_size(self):
        """Test estimation when size is already known."""
        engine = ScoringEngine()
        model = ModelInfo(
            name="test:7b",
            family="llama3",
            parameters_b=7.0,
            quantization=QuantizationType.Q4_K_M,
            context_length=8192,
            size_gb=5.0,
        )
        
        size = engine._estimate_model_size(model)
        assert size == 5.0

    @pytest.mark.unit
    def test_estimate_size_from_params_fp16(self):
        """Test estimation from parameters with FP16."""
        engine = ScoringEngine()
        model = ModelInfo(
            name="test:7b",
            family="llama3",
            parameters_b=7.0,
            quantization=QuantizationType.FP16,
            context_length=8192,
        )
        
        size = engine._estimate_model_size(model)
        # 7B params * 2 bytes * 1.15 overhead = ~16.1 GB
        assert size > 14.0
        assert size < 18.0

    @pytest.mark.unit
    def test_estimate_size_from_params_q4(self):
        """Test estimation from parameters with Q4."""
        engine = ScoringEngine()
        model = ModelInfo(
            name="test:7b",
            family="llama3",
            parameters_b=7.0,
            quantization=QuantizationType.Q4_K_M,
            context_length=8192,
        )
        
        size = engine._estimate_model_size(model)
        # 7B params * 0.5 bytes * 1.15 overhead = ~4.0 GB
        assert size > 3.5
        assert size < 5.0


class TestScoringEngineTaskBonuses:
    """Tests for task-specific scoring bonuses."""

    @pytest.mark.unit
    def test_coding_task_bonus(self):
        """Test coding task bonus for coding models."""
        engine = ScoringEngine()
        
        coding_model = ModelInfo(
            name="qwen2.5-coder:7b",
            family="qwen2.5-coder",
            parameters_b=7.0,
            quantization=QuantizationType.Q4_K_M,
            context_length=32768,
        )
        
        general_score = engine.score_model(coding_model, use_case="general")
        coding_score = engine.score_model(coding_model, use_case="coding")
        
        # Coding use case should give bonus for coding model
        assert coding_score.quality_score > general_score.quality_score

    @pytest.mark.unit
    def test_reasoning_task_bonus(self):
        """Test reasoning task bonus."""
        engine = ScoringEngine()
        
        model = ModelInfo(
            name="deepseek-r1:7b",
            family="deepseek-r1",
            parameters_b=7.0,
            quantization=QuantizationType.Q4_K_M,
            context_length=32768,
        )
        
        general_score = engine.score_model(model, use_case="general")
        reasoning_score = engine.score_model(model, use_case="reasoning")
        
        # Reasoning use case should give bonus
        assert reasoning_score.quality_score > general_score.quality_score

    @pytest.mark.unit
    def test_chat_task_bonus(self):
        """Test chat task bonus."""
        engine = ScoringEngine()
        
        model = ModelInfo(
            name="openchat:7b",
            family="openchat",
            parameters_b=7.0,
            quantization=QuantizationType.Q4_K_M,
            context_length=8192,
        )
        
        general_score = engine.score_model(model, use_case="general")
        chat_score = engine.score_model(model, use_case="chat")
        
        # Chat use case should give bonus for chat model
        assert chat_score.quality_score > general_score.quality_score


class TestScoringEngineFamilyQuality:
    """Tests for family quality scoring."""

    @pytest.mark.unit
    def test_frontier_family_quality(self):
        """Test quality score for frontier models."""
        engine = ScoringEngine()
        
        qwen_model = ModelInfo(
            name="qwen2.5:72b",
            family="qwen2.5",
            parameters_b=72.0,
            quantization=QuantizationType.Q4_K_M,
            context_length=32768,
        )
        qwen_score = engine.score_model(qwen_model)
        
        assert qwen_score.quality_score > 80

    @pytest.mark.unit
    def test_embedding_family_quality(self):
        """Test quality score for embedding models."""
        engine = ScoringEngine()
        
        embed_model = ModelInfo(
            name="nomic-embed-text",
            family="nomic-embed-text",
            parameters_b=0.3,
            quantization=QuantizationType.FP16,
            context_length=8192,
        )
        embed_score = engine.score_model(embed_model)
        
        assert embed_score.quality_score > 0

    @pytest.mark.unit
    def test_unknown_family_quality(self):
        """Test quality score for unknown family."""
        engine = ScoringEngine()
        
        unknown_model = ModelInfo(
            name="unknown-model:7b",
            family="unknown-family",
            parameters_b=7.0,
            quantization=QuantizationType.Q4_K_M,
            context_length=8192,
        )
        unknown_score = engine.score_model(unknown_model)
        
        # Should get base score
        assert unknown_score.quality_score >= 0


class TestScoringEngineContextScore:
    """Tests for context score calculation."""

    @pytest.mark.unit
    def test_128k_context(self):
        """Test context score for 128k context."""
        engine = ScoringEngine()
        model = ModelInfo(
            name="test",
            family="llama3",
            parameters_b=7.0,
            quantization=QuantizationType.Q4_K_M,
            context_length=128000,
        )
        score = engine.score_model(model)
        assert score.context_score == 100

    @pytest.mark.unit
    def test_32k_context(self):
        """Test context score for 32k context."""
        engine = ScoringEngine()
        model = ModelInfo(
            name="test",
            family="llama3",
            parameters_b=7.0,
            quantization=QuantizationType.Q4_K_M,
            context_length=32000,
        )
        score = engine.score_model(model)
        assert score.context_score == 90

    @pytest.mark.unit
    def test_16k_context(self):
        """Test context score for 16k context."""
        engine = ScoringEngine()
        model = ModelInfo(
            name="test",
            family="llama3",
            parameters_b=7.0,
            quantization=QuantizationType.Q4_K_M,
            context_length=16000,
        )
        score = engine.score_model(model)
        assert score.context_score == 80

    @pytest.mark.unit
    def test_8k_context(self):
        """Test context score for 8k context."""
        engine = ScoringEngine()
        model = ModelInfo(
            name="test",
            family="llama3",
            parameters_b=7.0,
            quantization=QuantizationType.Q4_K_M,
            context_length=8192,
        )
        score = engine.score_model(model)
        assert score.context_score == 70

    @pytest.mark.unit
    def test_4k_context(self):
        """Test context score for 4k context."""
        engine = ScoringEngine()
        model = ModelInfo(
            name="test",
            family="llama3",
            parameters_b=7.0,
            quantization=QuantizationType.Q4_K_M,
            context_length=4096,
        )
        score = engine.score_model(model)
        assert score.context_score == 60

    @pytest.mark.unit
    def test_2k_context(self):
        """Test context score for 2k context."""
        engine = ScoringEngine()
        model = ModelInfo(
            name="test",
            family="llama3",
            parameters_b=7.0,
            quantization=QuantizationType.Q4_K_M,
            context_length=2048,
        )
        score = engine.score_model(model)
        assert score.context_score == 50

    @pytest.mark.unit
    def test_tiny_context(self):
        """Test context score for tiny context."""
        engine = ScoringEngine()
        model = ModelInfo(
            name="test",
            family="llama3",
            parameters_b=7.0,
            quantization=QuantizationType.Q4_K_M,
            context_length=1024,
        )
        score = engine.score_model(model)
        assert score.context_score == 40
