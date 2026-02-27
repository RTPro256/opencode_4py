"""
Model Profiler

Profiles LLM models for performance and capability assessment.
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import logging

from opencode.router.config import ModelConfig, PromptCategory

logger = logging.getLogger(__name__)


@dataclass
class ModelProfile:
    """
    Profile of a model's capabilities and performance.
    
    Contains benchmark results and capability scores.
    """
    model_id: str
    provider: str
    
    # Performance metrics
    avg_latency_ms: float = 0.0
    tokens_per_second: float = 0.0
    time_to_first_token_ms: float = 0.0
    
    # Capability scores (0-1)
    coding_score: float = 0.5
    reasoning_score: float = 0.5
    creative_score: float = 0.5
    math_score: float = 0.5
    general_score: float = 0.5
    
    # Quality scores
    overall_quality: float = 0.5
    instruction_following: float = 0.5
    
    # Resource requirements
    vram_required_gb: Optional[float] = None
    context_length: int = 4096
    
    # Capabilities
    supports_tools: bool = False
    supports_vision: bool = False
    supports_streaming: bool = True
    
    # Metadata
    profiled_at: Optional[datetime] = None
    benchmark_count: int = 0
    
    def to_config(self) -> ModelConfig:
        """Convert to ModelConfig."""
        return ModelConfig(
            model_id=self.model_id,
            provider=self.provider,
            supports_tools=self.supports_tools,
            supports_vision=self.supports_vision,
            supports_streaming=self.supports_streaming,
            vram_required_gb=self.vram_required_gb,
            context_length=self.context_length,
            speed_score=self._calculate_speed_score(),
            quality_score=self.overall_quality,
            coding_score=self.coding_score,
            reasoning_score=self.reasoning_score,
            creative_score=self.creative_score,
            math_score=self.math_score,
        )
    
    def _calculate_speed_score(self) -> float:
        """Calculate speed score from performance metrics."""
        if self.tokens_per_second <= 0:
            return 0.5
        
        # Normalize tokens per second to 0-1 scale
        # Assuming 50 tps is "fast" (score 1.0) and 5 tps is "slow" (score 0.1)
        score = min(self.tokens_per_second / 50.0, 1.0)
        return max(score, 0.1)


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run."""
    prompt: str
    response: str
    latency_ms: float
    tokens_generated: int
    tokens_per_second: float
    time_to_first_token_ms: float
    success: bool
    error: Optional[str] = None


class ModelProfiler:
    """
    Profiles LLM models for performance and capabilities.
    
    Runs benchmarks to assess model speed, quality, and capabilities
    for intelligent routing decisions.
    """
    
    # Benchmark prompts for different categories
    BENCHMARK_PROMPTS = {
        PromptCategory.CODING: [
            "Write a Python function to find the longest common subsequence of two strings.",
            "Implement a binary search tree with insert, delete, and find operations.",
            "Create a REST API endpoint using FastAPI that handles user authentication.",
        ],
        PromptCategory.REASONING: [
            "Explain the difference between correlation and causation with examples.",
            "What are the logical fallacies in this argument: 'All birds can fly. Penguins are birds. Therefore penguins can fly.'",
            "Compare and contrast microservices and monolithic architectures.",
        ],
        PromptCategory.CREATIVE: [
            "Write a short story about a robot discovering emotions.",
            "Create a poem about the changing seasons.",
            "Write a dialogue between two characters debating the merits of space exploration.",
        ],
        PromptCategory.MATH: [
            "Solve the equation: 2x^2 + 5x - 3 = 0",
            "Calculate the derivative of f(x) = x^3 * sin(x)",
            "Prove that the sum of angles in a triangle is 180 degrees.",
        ],
        PromptCategory.GENERAL: [
            "Summarize the key principles of effective communication.",
            "What are the best practices for writing clean code?",
            "Explain the concept of recursion to a beginner.",
        ],
    }
    
    def __init__(self, timeout_seconds: int = 90):
        """
        Initialize the model profiler.
        
        Args:
            timeout_seconds: Timeout for benchmark runs
        """
        self.timeout_seconds = timeout_seconds
        self._profiles: Dict[str, ModelProfile] = {}
    
    async def profile_model(
        self,
        provider: Any,
        model_id: str,
        categories: Optional[List[PromptCategory]] = None,
    ) -> ModelProfile:
        """
        Profile a model by running benchmarks.
        
        Args:
            provider: The LLM provider instance
            model_id: The model identifier
            categories: Categories to benchmark (default: all)
            
        Returns:
            ModelProfile with benchmark results
        """
        if categories is None:
            categories = list(PromptCategory)
        
        profile = ModelProfile(
            model_id=model_id,
            provider=provider.name if hasattr(provider, 'name') else str(type(provider)),
        )
        
        benchmark_results: List[BenchmarkResult] = []
        
        for category in categories:
            prompts = self.BENCHMARK_PROMPTS.get(category, [])
            for prompt in prompts:
                try:
                    result = await self._run_benchmark(provider, model_id, prompt)
                    benchmark_results.append(result)
                    
                    # Update category score based on success
                    if result.success:
                        self._update_category_score(profile, category, result)
                    
                except asyncio.TimeoutError:
                    logger.warning(f"Benchmark timeout for {model_id} on {category}")
                except Exception as e:
                    logger.error(f"Benchmark error for {model_id}: {e}")
        
        # Calculate aggregate metrics
        if benchmark_results:
            successful = [r for r in benchmark_results if r.success]
            if successful:
                profile.avg_latency_ms = sum(r.latency_ms for r in successful) / len(successful)
                profile.tokens_per_second = sum(r.tokens_per_second for r in successful) / len(successful)
                profile.time_to_first_token_ms = sum(r.time_to_first_token_ms for r in successful) / len(successful)
                profile.benchmark_count = len(successful)
        
        profile.profiled_at = datetime.utcnow()
        
        # Cache the profile
        self._profiles[model_id] = profile
        
        return profile
    
    async def _run_benchmark(
        self,
        provider: Any,
        model_id: str,
        prompt: str,
    ) -> BenchmarkResult:
        """
        Run a single benchmark.
        
        Args:
            provider: The LLM provider
            model_id: Model identifier
            prompt: Benchmark prompt
            
        Returns:
            BenchmarkResult with timing and output
        """
        from opencode.provider.base import Message, MessageRole
        
        start_time = time.time()
        first_token_time = None
        tokens_generated = 0
        
        try:
            messages = [Message(role=MessageRole.USER, content=prompt)]
            
            # Stream response to measure time to first token
            chunks = []
            async for chunk in provider.complete(
                messages=messages,
                model=model_id,
                max_tokens=256,
                temperature=0.7,
            ):
                if not first_token_time and chunk.delta:
                    first_token_time = time.time()
                chunks.append(chunk)
                if chunk.delta:
                    tokens_generated += 1
            
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            
            # Calculate metrics
            if first_token_time:
                ttft_ms = (first_token_time - start_time) * 1000
            else:
                ttft_ms = latency_ms
            
            if latency_ms > 0 and tokens_generated > 0:
                tps = tokens_generated / (latency_ms / 1000)
            else:
                tps = 0
            
            # Get response text
            response = "".join(c.delta for c in chunks)
            
            return BenchmarkResult(
                prompt=prompt,
                response=response,
                latency_ms=latency_ms,
                tokens_generated=tokens_generated,
                tokens_per_second=tps,
                time_to_first_token_ms=ttft_ms,
                success=True,
            )
            
        except Exception as e:
            end_time = time.time()
            return BenchmarkResult(
                prompt=prompt,
                response="",
                latency_ms=(end_time - start_time) * 1000,
                tokens_generated=0,
                tokens_per_second=0,
                time_to_first_token_ms=0,
                success=False,
                error=str(e),
            )
    
    def _update_category_score(
        self,
        profile: ModelProfile,
        category: PromptCategory,
        result: BenchmarkResult,
    ) -> None:
        """Update category score based on benchmark result."""
        # Simple scoring based on response quality indicators
        # In a real implementation, this would use more sophisticated evaluation
        
        score = 0.5  # Base score
        
        # Adjust based on response length (longer = more detailed)
        if len(result.response) > 200:
            score += 0.1
        if len(result.response) > 500:
            score += 0.1
        
        # Adjust based on speed
        if result.tokens_per_second > 30:
            score += 0.1
        if result.tokens_per_second > 50:
            score += 0.1
        
        # Cap at 1.0
        score = min(score, 1.0)
        
        # Update the appropriate category score
        if category == PromptCategory.CODING:
            profile.coding_score = (profile.coding_score + score) / 2
        elif category == PromptCategory.REASONING:
            profile.reasoning_score = (profile.reasoning_score + score) / 2
        elif category == PromptCategory.CREATIVE:
            profile.creative_score = (profile.creative_score + score) / 2
        elif category == PromptCategory.MATH:
            profile.math_score = (profile.math_score + score) / 2
        elif category == PromptCategory.GENERAL:
            profile.general_score = (profile.general_score + score) / 2
        
        # Update overall quality
        profile.overall_quality = (
            profile.coding_score +
            profile.reasoning_score +
            profile.creative_score +
            profile.math_score +
            profile.general_score
        ) / 5
    
    def get_profile(self, model_id: str) -> Optional[ModelProfile]:
        """Get a cached profile for a model."""
        return self._profiles.get(model_id)
    
    def list_profiles(self) -> List[ModelProfile]:
        """List all cached profiles."""
        return list(self._profiles.values())
    
    def clear_profiles(self) -> None:
        """Clear all cached profiles."""
        self._profiles.clear()
    
    async def quick_profile(
        self,
        provider: Any,
        model_id: str,
    ) -> ModelProfile:
        """
        Quick profile with minimal benchmarks.
        
        Args:
            provider: The LLM provider
            model_id: Model identifier
            
        Returns:
            ModelProfile with basic metrics
        """
        return await self.profile_model(
            provider=provider,
            model_id=model_id,
            categories=[PromptCategory.GENERAL],
        )
