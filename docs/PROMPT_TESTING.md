# Prompt Comparison and Accuracy Testing

> **Navigation:** [TESTING_PLAN.md](../plans/TESTING_PLAN.md) - Main testing strategy overview

This document describes prompt comparison tests that evaluate how different AI models respond to the same prompts, helping identify model-specific behaviors and prompt engineering needs.

---

## Cross-Model Prompt Comparison Test

```python
# tests/prompts/test_prompt_comparison.py
"""
Tests for comparing prompts across different AI models.

These tests evaluate how different models respond to the same prompts,
helping identify model-specific behaviors and prompt engineering needs.
"""

import pytest
from typing import Dict, List, Any
from dataclasses import dataclass
import asyncio

from opencode.provider.base import Message, Provider
from opencode.provider.ollama import OllamaProvider
from opencode.provider.openai import OpenAIProvider
from opencode.provider.anthropic import AnthropicProvider


@dataclass
class PromptComparisonResult:
    """Result of comparing a prompt across models."""
    prompt: str
    model_responses: Dict[str, str]
    similarity_scores: Dict[str, float]
    accuracy_scores: Dict[str, float]
    latency_ms: Dict[str, float]
    errors: Dict[str, str]


class TestPromptComparison:
    """Compare prompts across different AI models."""
    
    @pytest.fixture
    def providers(self, request) -> Dict[str, Provider]:
        """Get available providers based on configuration."""
        providers = {}
        
        # Always include Ollama if available
        try:
            providers["ollama"] = OllamaProvider()
        except Exception:
            pass
        
        # Include cloud providers if API keys are available
        import os
        if os.getenv("OPENAI_API_KEY"):
            providers["openai"] = OpenAIProvider()
        if os.getenv("ANTHROPIC_API_KEY"):
            providers["anthropic"] = AnthropicProvider()
        
        return providers
    
    @pytest.fixture
    def comparison_prompts(self) -> List[Dict[str, str]]:
        """Prompts to use for comparison testing."""
        return [
            {
                "id": "math_simple",
                "prompt": "What is 15 * 17? Show your work.",
                "expected_contains": ["255", "15", "17"],
            },
            {
                "id": "code_generation",
                "prompt": "Write a Python function that checks if a string is a palindrome.",
                "expected_contains": ["def", "return", "palindrome"],
            },
            {
                "id": "reasoning",
                "prompt": "If it takes 5 machines 5 minutes to make 5 widgets, how long would it take 100 machines to make 100 widgets?",
                "expected_contains": ["5 minutes", "5"],
            },
            {
                "id": "explanation",
                "prompt": "Explain the difference between a list and a tuple in Python.",
                "expected_contains": ["mutable", "immutable", "list", "tuple"],
            },
        ]
    
    @pytest.mark.asyncio
    async def test_compare_simple_prompt(
        self,
        providers: Dict[str, Provider],
        comparison_prompts: List[Dict[str, str]],
    ):
        """Compare simple prompts across all available models."""
        results = []
        
        for prompt_data in comparison_prompts:
            result = await self._compare_prompt(
                providers=providers,
                prompt=prompt_data["prompt"],
                expected_contains=prompt_data["expected_contains"],
            )
            results.append(result)
            
            # Assert at least one model provides correct answer
            assert any(result.accuracy_scores.values()), \
                f"No model correctly answered: {prompt_data['id']}"
    
    @pytest.mark.asyncio
    async def test_compare_code_prompts(self, providers: Dict[str, Provider]):
        """Compare code generation across models."""
        prompt = "Write a Python function to sort a list of dictionaries by a specific key."
        
        result = await self._compare_prompt(
            providers=providers,
            prompt=prompt,
            expected_contains=["def", "sort", "key", "lambda"],
        )
        
        # All models should generate valid Python code
        for model, response in result.model_responses.items():
            assert "def " in response, f"{model} did not generate a function"
    
    @pytest.mark.asyncio
    async def test_compare_reasoning_prompts(self, providers: Dict[str, Provider]):
        """Compare reasoning capabilities across models."""
        prompt = """
        A bat and ball cost $1.10 total.
        The bat costs $1.00 more than the ball.
        How much does the ball cost?
        """
        
        result = await self._compare_prompt(
            providers=providers,
            prompt=prompt,
            expected_contains=["0.05", "5 cents", "five cents"],
        )
        
        # Track which models get the correct answer (it's $0.05)
        # This is a known tricky question that many models get wrong
        for model, response in result.model_responses.items():
            # Log for analysis, don't fail - this is diagnostic
            print(f"{model}: {response[:100]}...")
    
    async def _compare_prompt(
        self,
        providers: Dict[str, Provider],
        prompt: str,
        expected_contains: List[str],
    ) -> PromptComparisonResult:
        """Execute prompt comparison across providers."""
        import time
        
        responses = {}
        scores = {}
        latency = {}
        errors = {}
        
        for name, provider in providers.items():
            try:
                start = time.time()
                response = await provider.complete(
                    messages=[Message(role="user", content=prompt)],
                    model=provider.default_model,
                )
                latency[name] = (time.time() - start) * 1000
                
                content = response.content
                responses[name] = content
                
                # Calculate accuracy score
                found = sum(1 for exp in expected_contains if exp.lower() in content.lower())
                scores[name] = found / len(expected_contains) if expected_contains else 1.0
                
            except Exception as e:
                errors[name] = str(e)
                responses[name] = ""
                scores[name] = 0.0
                latency[name] = 0.0
        
        return PromptComparisonResult(
            prompt=prompt,
            model_responses=responses,
            accuracy_scores=scores,
            latency_ms=latency,
            errors=errors,
        )
```

---

## Prompt Accuracy Benchmark

```python
# tests/prompts/test_prompt_accuracy.py
"""
Benchmark tests for prompt accuracy across models.

Uses standardized test sets to measure and track accuracy over time.
"""

import pytest
from typing import List, Dict, Any
import json
from pathlib import Path

from opencode.provider.base import Message


class PromptAccuracyBenchmark:
    """Benchmark suite for prompt accuracy."""
    
    # Standard test sets
    MATH_TEST_SET = [
        {"q": "What is 7 * 8?", "a": "56"},
        {"q": "What is 144 / 12?", "a": "12"},
        {"q": "What is 15% of 200?", "a": "30"},
    ]
    
    CODE_TEST_SET = [
        {
            "q": "Write a Python one-liner to reverse a string.",
            "validate": lambda r: "[::-1]" in r or "reversed" in r,
        },
        {
            "q": "Write a Python list comprehension to square numbers 1-10.",
            "validate": lambda r: "[" in r and "**2" in r and "for" in r,
        },
    ]
    
    REASONING_TEST_SET = [
        {
            "q": "If John is taller than Mary, and Mary is taller than Sue, who is the shortest?",
            "a": "Sue",
        },
        {
            "q": "All cats are animals. All animals need water. Do cats need water?",
            "a": "yes",
        },
    ]


class TestPromptAccuracy:
    """Test prompt accuracy across models."""
    
    @pytest.fixture
    def benchmark(self) -> PromptAccuracyBenchmark:
        return PromptAccuracyBenchmark()
    
    @pytest.mark.asyncio
    async def test_math_accuracy(self, ollama_provider, benchmark):
        """Test mathematical accuracy."""
        correct = 0
        total = len(benchmark.MATH_TEST_SET)
        
        for item in benchmark.MATH_TEST_SET:
            response = await ollama_provider.complete(
                messages=[Message(role="user", content=item["q"])],
                model="llama3.2:3b",
            )
            if item["a"] in response.content:
                correct += 1
        
        accuracy = correct / total
        # Require at least 80% accuracy on simple math
        assert accuracy >= 0.8, f"Math accuracy too low: {accuracy:.1%}"
    
    @pytest.mark.asyncio
    async def test_code_generation_validity(self, ollama_provider, benchmark):
        """Test that generated code is syntactically valid."""
        import ast
        
        for item in benchmark.CODE_TEST_SET:
            response = await ollama_provider.complete(
                messages=[Message(role="user", content=item["q"])],
                model="llama3.2:3b",
            )
            
            # Extract code from response
            code = self._extract_code(response.content)
            
            # Validate syntax
            try:
                ast.parse(code)
                is_valid = True
            except SyntaxError:
                is_valid = False
            
            assert is_valid or item["validate"](response.content), \
                f"Invalid code generated for: {item['q']}"
    
    def _extract_code(self, text: str) -> str:
        """Extract code from markdown-formatted response."""
        import re
        # Extract code blocks
        matches = re.findall(r'```(?:python)?\n(.*?)```', text, re.DOTALL)
        return matches[0] if matches else text
```

---

## Related Documentation

- [TESTING_INFRASTRUCTURE.md](TESTING_INFRASTRUCTURE.md) - Test directory structure and configuration
- [OLLAMA_TESTING.md](OLLAMA_TESTING.md) - Ollama integration tests
- [CI_CD_TESTING.md](CI_CD_TESTING.md) - CI/CD configuration
