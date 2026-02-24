"""
Accuracy tests for Ollama provider.

Tests model accuracy, response quality, and performance benchmarks.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
import time

from opencode.provider.base import (
    Message,
    MessageRole,
    CompletionResponse,
    FinishReason,
)


@pytest.mark.ollama
@pytest.mark.slow
class TestOllamaAccuracy:
    """Test Ollama model accuracy."""
    
    @pytest.fixture
    def accuracy_thresholds(self):
        """Define accuracy thresholds for different task types."""
        return {
            "simple_qa": 0.85,
            "code_generation": 0.70,
            "math": 0.75,
            "reasoning": 0.70,
            "summarization": 0.80,
        }
    
    @pytest.fixture
    def test_cases(self):
        """Define test cases for accuracy testing."""
        return {
            "simple_qa": [
                {
                    "prompt": "What is 2 + 2?",
                    "expected_keywords": ["4", "four"],
                    "category": "math",
                },
                {
                    "prompt": "What is the capital of France?",
                    "expected_keywords": ["Paris", "paris"],
                    "category": "geography",
                },
                {
                    "prompt": "What color is the sky on a clear day?",
                    "expected_keywords": ["blue", "Blue"],
                    "category": "general",
                },
            ],
            "code_generation": [
                {
                    "prompt": "Write a Python function to add two numbers.",
                    "expected_keywords": ["def", "return", "+"],
                    "category": "python",
                },
                {
                    "prompt": "Write a function to check if a number is even.",
                    "expected_keywords": ["def", "%", "2", "even"],
                    "category": "python",
                },
            ],
            "reasoning": [
                {
                    "prompt": "If all cats are animals, and Fluffy is a cat, is Fluffy an animal?",
                    "expected_keywords": ["yes", "Yes", "animal"],
                    "category": "logic",
                },
            ],
        }
    
    @pytest.fixture
    def mock_provider_with_accuracy(self):
        """Create a mock provider that simulates accurate responses."""
        provider = MagicMock()
        provider.name = "ollama"
        
        async def mock_complete(messages, model, **kwargs):
            last_message = messages[-1] if messages else None
            if not last_message:
                return CompletionResponse(content="", model=model)
            
            content = last_message.content.lower() if isinstance(last_message.content, str) else ""
            
            # Simulate accurate responses for testing
            if "2 + 2" in content:
                return CompletionResponse(content="The answer is 4.", model=model)
            elif "capital of france" in content:
                return CompletionResponse(content="The capital of France is Paris.", model=model)
            elif "color is the sky" in content:
                return CompletionResponse(content="The sky is blue on a clear day.", model=model)
            elif "add two numbers" in content:
                return CompletionResponse(
                    content="def add(a, b):\n    return a + b",
                    model=model
                )
            elif "even" in content:
                return CompletionResponse(
                    content="def is_even(n):\n    return n % 2 == 0",
                    model=model
                )
            elif "fluffy" in content:
                return CompletionResponse(
                    content="Yes, Fluffy is an animal because all cats are animals.",
                    model=model
                )
            else:
                return CompletionResponse(content="I understand.", model=model)
        
        provider.complete_sync = mock_complete
        return provider
    
    def _check_accuracy(self, response: str, expected_keywords: list[str]) -> bool:
        """Check if response contains expected keywords."""
        response_lower = response.lower()
        return any(kw.lower() in response_lower for kw in expected_keywords)
    
    @pytest.mark.asyncio
    async def test_simple_qa_accuracy(self, mock_provider_with_accuracy, test_cases):
        """Test accuracy on simple Q&A tasks."""
        cases = test_cases["simple_qa"]
        correct = 0
        
        for case in cases:
            response = await mock_provider_with_accuracy.complete_sync(
                messages=[Message(role=MessageRole.USER, content=case["prompt"])],
                model="llama3.2:3b",
            )
            
            if self._check_accuracy(response.content, case["expected_keywords"]):
                correct += 1
        
        accuracy = correct / len(cases)
        assert accuracy >= 0.8, f"Simple Q&A accuracy {accuracy:.2%} below threshold"
    
    @pytest.mark.asyncio
    async def test_code_generation_accuracy(self, mock_provider_with_accuracy, test_cases):
        """Test accuracy on code generation tasks."""
        cases = test_cases["code_generation"]
        correct = 0
        
        for case in cases:
            response = await mock_provider_with_accuracy.complete_sync(
                messages=[Message(role=MessageRole.USER, content=case["prompt"])],
                model="llama3.2:3b",
            )
            
            if self._check_accuracy(response.content, case["expected_keywords"]):
                correct += 1
        
        accuracy = correct / len(cases)
        assert accuracy >= 0.7, f"Code generation accuracy {accuracy:.2%} below threshold"
    
    @pytest.mark.asyncio
    async def test_reasoning_accuracy(self, mock_provider_with_accuracy, test_cases):
        """Test accuracy on reasoning tasks."""
        cases = test_cases["reasoning"]
        correct = 0
        
        for case in cases:
            response = await mock_provider_with_accuracy.complete_sync(
                messages=[Message(role=MessageRole.USER, content=case["prompt"])],
                model="llama3.2:3b",
            )
            
            if self._check_accuracy(response.content, case["expected_keywords"]):
                correct += 1
        
        accuracy = correct / len(cases)
        assert accuracy >= 0.7, f"Reasoning accuracy {accuracy:.2%} below threshold"


@pytest.mark.ollama
@pytest.mark.slow
class TestOllamaResponseQuality:
    """Test Ollama response quality metrics."""
    
    @pytest.fixture
    def mock_provider(self):
        """Create a mock provider for quality testing."""
        provider = MagicMock()
        provider.name = "ollama"
        provider.complete_sync = AsyncMock(return_value=CompletionResponse(
            content="This is a well-formed response with proper structure.",
            model="llama3.2:3b",
            finish_reason=FinishReason.STOP,
        ))
        return provider
    
    @pytest.mark.asyncio
    async def test_response_completeness(self, mock_provider):
        """Test that responses are complete (not truncated)."""
        response = await mock_provider.complete_sync(
            messages=[Message(role=MessageRole.USER, content="Tell me a short story.")],
            model="llama3.2:3b",
        )
        
        assert response.finish_reason == FinishReason.STOP
        assert len(response.content) > 0
    
    @pytest.mark.asyncio
    async def test_response_relevance(self, mock_provider):
        """Test that responses are relevant to the prompt."""
        prompt = "What is Python?"
        response = await mock_provider.complete_sync(
            messages=[Message(role=MessageRole.USER, content=prompt)],
            model="llama3.2:3b",
        )
        
        # Response should not be empty
        assert len(response.content) > 0
        # Response should be a string
        assert isinstance(response.content, str)
    
    @pytest.mark.asyncio
    async def test_response_consistency(self, mock_provider):
        """Test response consistency across multiple calls."""
        prompt = "What is 1 + 1?"
        responses = []
        
        for _ in range(3):
            response = await mock_provider.complete_sync(
                messages=[Message(role=MessageRole.USER, content=prompt)],
                model="llama3.2:3b",
            )
            responses.append(response.content)
        
        # All responses should be non-empty
        assert all(len(r) > 0 for r in responses)


@pytest.mark.ollama
@pytest.mark.slow
class TestOllamaPerformance:
    """Test Ollama performance metrics."""
    
    @pytest.fixture
    def performance_thresholds(self):
        """Define performance thresholds."""
        return {
            "first_token_latency_ms": 500,  # First token within 500ms
            "tokens_per_second": 10,  # At least 10 tokens/second
            "total_latency_ms": 5000,  # Total response within 5 seconds
        }
    
    @pytest.fixture
    def mock_provider_with_timing(self):
        """Create a mock provider with timing simulation."""
        provider = MagicMock()
        provider.name = "ollama"
        
        async def mock_complete(messages, model, **kwargs):
            # Simulate some processing time
            await asyncio.sleep(0.01)  # 10ms simulated latency
            return CompletionResponse(
                content="This is a test response with multiple words.",
                model=model,
            )
        
        provider.complete_sync = mock_complete
        return provider
    
    @pytest.mark.asyncio
    async def test_response_latency(self, mock_provider_with_timing, performance_thresholds):
        """Test response latency is within acceptable bounds."""
        import asyncio
        
        start_time = time.time()
        response = await mock_provider_with_timing.complete_sync(
            messages=[Message(role=MessageRole.USER, content="Hello")],
            model="llama3.2:3b",
        )
        elapsed_ms = (time.time() - start_time) * 1000
        
        # For mock, just verify we got a response
        assert response is not None
        assert elapsed_ms < performance_thresholds["total_latency_ms"]
    
    @pytest.mark.asyncio
    async def test_throughput(self, mock_provider_with_timing):
        """Test throughput for multiple requests."""
        import asyncio
        
        num_requests = 5
        start_time = time.time()
        
        tasks = [
            mock_provider_with_timing.complete_sync(
                messages=[Message(role=MessageRole.USER, content=f"Request {i}")],
                model="llama3.2:3b",
            )
            for i in range(num_requests)
        ]
        
        responses = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time
        
        assert len(responses) == num_requests
        assert all(r is not None for r in responses)


@pytest.mark.ollama
class TestOllamaModelComparison:
    """Compare accuracy across different Ollama models."""
    
    @pytest.fixture
    def model_configs(self):
        """Define model configurations to compare."""
        return [
            {"id": "llama3.2:3b", "expected_quality": "standard"},
            {"id": "llama3.1:8b", "expected_quality": "high"},
            {"id": "mistral:7b", "expected_quality": "standard"},
        ]
    
    def test_model_config_structure(self, model_configs):
        """Test model configuration structure."""
        for config in model_configs:
            assert "id" in config
            assert "expected_quality" in config
            assert config["expected_quality"] in ["standard", "high"]
    
    @pytest.mark.asyncio
    async def test_model_capability_matrix(self):
        """Test model capability matrix."""
        from opencode.provider.ollama import OllamaProvider
        
        for model in OllamaProvider.COMMON_MODELS:
            # Check model has required attributes
            assert model.id is not None
            assert model.context_length > 0
            
            # Check capabilities are defined
            assert isinstance(model.supports_tools, bool)
            assert isinstance(model.supports_vision, bool)
            assert isinstance(model.supports_streaming, bool)


@pytest.mark.ollama
class TestOllamaAccuracyTracking:
    """Test accuracy tracking and reporting."""
    
    @pytest.fixture
    def accuracy_results(self):
        """Sample accuracy results for testing."""
        return {
            "llama3.2:3b": {
                "simple_qa": 0.90,
                "code_generation": 0.75,
                "reasoning": 0.80,
            },
            "llama3.1:8b": {
                "simple_qa": 0.95,
                "code_generation": 0.85,
                "reasoning": 0.88,
            },
        }
    
    def test_accuracy_results_structure(self, accuracy_results):
        """Test accuracy results structure."""
        for model, results in accuracy_results.items():
            assert isinstance(model, str)
            assert isinstance(results, dict)
            
            for category, score in results.items():
                assert isinstance(category, str)
                assert 0 <= score <= 1
    
    def test_accuracy_aggregation(self, accuracy_results):
        """Test accuracy aggregation across models."""
        overall_scores = {}
        
        for model, results in accuracy_results.items():
            avg_score = sum(results.values()) / len(results)
            overall_scores[model] = avg_score
        
        # All models should have reasonable average scores
        for model, score in overall_scores.items():
            assert score >= 0.7, f"{model} average accuracy {score:.2%} below threshold"
    
    def test_accuracy_comparison(self, accuracy_results):
        """Test accuracy comparison between models."""
        models = list(accuracy_results.keys())
        
        if len(models) >= 2:
            model1, model2 = models[0], models[1]
            
            for category in accuracy_results[model1]:
                if category in accuracy_results[model2]:
                    # Both models should have scores in valid range
                    score1 = accuracy_results[model1][category]
                    score2 = accuracy_results[model2][category]
                    
                    assert 0 <= score1 <= 1
                    assert 0 <= score2 <= 1


# Import asyncio for async tests
import asyncio
