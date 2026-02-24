# Comprehensive Testing Plan for OpenCode Python

This document outlines a comprehensive testing strategy for the OpenCode Python project, designed to accommodate future changes and ensure reliability across all components.

**Current Status:** See [docs/TESTING_STATUS.md](../docs/TESTING_STATUS.md) for the latest test coverage and results.

> **Related Documents:**
> - [README.md](../README.md) - Project overview and features
> - [MISSION.md](../MISSION.md) - Mission statement and core principles

---

## Definitions

### Complete Test Suite

A **complete test suite** is defined as:

1. **All test categories passing**: Unit, Integration, Provider, Prompt, Ollama, E2E, and Performance tests
2. **No skipped tests** (except those requiring unavailable external services like Ollama or API keys)
3. **No failing tests** - all tests must pass
4. **Minimum coverage threshold met**: At least 70% code coverage on non-excluded modules

### 100% Coverage

**100% coverage** means 100% of **non-excluded modules** are covered by tests. Modules listed in the Coverage Exclusions section below are not counted toward coverage calculations. This means:

- If excluded modules have 0% coverage, the project can still achieve 100% coverage
- Coverage reports should be interpreted as "coverage of testable code"
- The goal is meaningful test coverage, not arbitrary percentages on thin API wrappers

---

## Coverage Exclusions

The following modules are **excluded from coverage requirements** as they are thin wrappers around external APIs:

- All provider implementations in `provider/` (except `base.py`)
- These require complex HTTP mocking with limited testing value
- Focus provider testing on `provider/base.py` (currently at 90% coverage)

---

## Executive Summary

The testing strategy follows a multi-layered approach:
1. **Unit Tests** - Fast, isolated tests for individual components
2. **Integration Tests** - Tests for component interactions
3. **Provider Tests** - AI model provider testing with mock and real backends
4. **Prompt Evaluation Tests** - Compare prompts across different AI models
5. **Ollama Integration Tests** - Local LLM testing for accuracy and troubleshooting
6. **End-to-End Tests** - Full workflow testing
7. **Performance Tests** - Benchmark critical paths

---

## Part 1: Testing Infrastructure

### 1.1 Test Directory Structure

```
src/opencode/tests/
├── conftest.py                    # Shared fixtures and configuration
├── unit/                          # Unit tests
│   ├── test_context.py
│   ├── test_orchestration.py
│   ├── test_subagents.py
│   ├── test_rag.py
│   ├── test_workflow/
│   ├── test_provider/
│   └── test_tools/
├── integration/                   # Integration tests
│   ├── test_session_flow.py
│   ├── test_workflow_execution.py
│   └── test_mcp_integration.py
├── providers/                     # Provider-specific tests
│   ├── test_provider_base.py
│   ├── test_ollama_provider.py
│   ├── test_openai_provider.py
│   └── test_anthropic_provider.py
├── prompts/                       # Prompt evaluation tests
│   ├── test_prompt_comparison.py
│   ├── test_prompt_accuracy.py
│   └── prompt_fixtures/
├── ollama/                        # Ollama-specific tests
│   ├── test_ollama_integration.py
│   ├── test_ollama_accuracy.py
│   └── test_ollama_troubleshooting.py
├── e2e/                           # End-to-end tests
│   ├── test_cli_commands.py
│   ├── test_tui_flow.py
│   └── test_server_api.py
└── performance/                   # Performance tests
    ├── test_context_truncation_perf.py
    └── test_workflow_execution_perf.py
```

### 1.2 Test Configuration

```python
# conftest.py
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

# Provider fixtures
@pytest.fixture
def mock_httpx_client():
    """Mock httpx client for provider tests."""
    client = AsyncMock()
    return client

@pytest.fixture
def ollama_available():
    """Check if Ollama is available locally."""
    import httpx
    try:
        response = httpx.get("http://localhost:11434/api/tags", timeout=2.0)
        return response.status_code == 200
    except:
        return False

@pytest.fixture
def skip_if_no_ollama(ollama_available):
    """Skip test if Ollama is not available."""
    if not ollama_available:
        pytest.skip("Ollama not available")

# Model fixtures
@pytest.fixture
def test_models():
    """Models to test across providers."""
    return {
        "ollama": ["llama3.2:3b", "llama3.1:8b", "qwen2.5:7b"],
        "openai": ["gpt-4o-mini", "gpt-4o"],
        "anthropic": ["claude-3-5-sonnet-20241022"],
    }

# Prompt fixtures
@pytest.fixture
def test_prompts():
    """Standard test prompts for evaluation."""
    return {
        "simple": "What is 2 + 2?",
        "code": "Write a Python function to calculate fibonacci numbers.",
        "reasoning": "If all roses are flowers, and some flowers are red, can we conclude that some roses are red? Explain your reasoning.",
        "creative": "Write a haiku about programming.",
        "tool_use": "What is the weather in Tokyo?",
    }
```

---

## Part 2: Prompt Comparison Tests

### 2.1 Cross-Model Prompt Comparison Test

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

### 2.2 Prompt Accuracy Benchmark

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

## Part 3: Ollama Integration Tests

### 3.1 Ollama Connection and Basic Tests

```python
# tests/ollama/test_ollama_integration.py
"""
Integration tests for Ollama provider.

Tests connection, model management, and basic operations.
"""

import pytest
from typing import List

from opencode.provider.ollama import OllamaProvider
from opencode.provider.base import Message, ToolDefinition


class TestOllamaIntegration:
    """Test Ollama integration."""
    
    @pytest.fixture
    async def provider(self) -> OllamaProvider:
        """Get Ollama provider instance."""
        provider = OllamaProvider()
        # Verify connection
        if not await provider.is_available():
            pytest.skip("Ollama not available at localhost:11434")
        return provider
    
    @pytest.mark.asyncio
    async def test_connection(self, provider: OllamaProvider):
        """Test basic connection to Ollama."""
        assert await provider.is_available()
    
    @pytest.mark.asyncio
    async def test_list_models(self, provider: OllamaProvider):
        """Test listing available models."""
        models = await provider.list_models()
        assert isinstance(models, list)
        assert len(models) > 0, "No models available in Ollama"
    
    @pytest.mark.asyncio
    async def test_simple_completion(self, provider: OllamaProvider):
        """Test simple completion."""
        response = await provider.complete(
            messages=[Message(role="user", content="Say 'hello world'")],
            model="llama3.2:3b",
        )
        
        assert response.content
        assert len(response.content) > 0
    
    @pytest.mark.asyncio
    async def test_streaming_completion(self, provider: OllamaProvider):
        """Test streaming completion."""
        chunks = []
        
        async for chunk in provider.stream(
            messages=[Message(role="user", content="Count from 1 to 5")],
            model="llama3.2:3b",
        ):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        full_content = "".join(c.content for c in chunks if c.content)
        assert len(full_content) > 0
    
    @pytest.mark.asyncio
    async def test_model_parameters(self, provider: OllamaProvider):
        """Test custom model parameters."""
        response = await provider.complete(
            messages=[Message(role="user", content="Hello")],
            model="llama3.2:3b",
            temperature=0.1,
            max_tokens=50,
        )
        
        # With low temperature and max_tokens, response should be short
        assert len(response.content.split()) < 50
    
    @pytest.mark.asyncio
    async def test_tool_calling(self, provider: OllamaProvider):
        """Test function/tool calling capability."""
        tools = [
            ToolDefinition(
                name="get_weather",
                description="Get current weather for a location",
                parameters={
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"},
                    },
                    "required": ["location"],
                },
            )
        ]
        
        response = await provider.complete(
            messages=[Message(role="user", content="What's the weather in Tokyo?")],
            model="llama3.2:3b",
            tools=tools,
        )
        
        # Check if model attempted to call the tool
        if response.tool_calls:
            assert response.tool_calls[0].name == "get_weather"
```

### 3.2 Ollama Accuracy and Troubleshooting Tests

```python
# tests/ollama/test_ollama_accuracy.py
"""
Accuracy and troubleshooting tests for Ollama.

Tests for common issues, error handling, and accuracy benchmarks.
"""

import pytest
import time
from typing import Dict, Any, List

from opencode.provider.ollama import OllamaProvider
from opencode.provider.base import Message, ProviderError


class TestOllamaAccuracy:
    """Test Ollama accuracy and handle common issues."""
    
    @pytest.fixture
    async def provider(self) -> OllamaProvider:
        provider = OllamaProvider()
        if not await provider.is_available():
            pytest.skip("Ollama not available")
        return provider
    
    @pytest.mark.asyncio
    async def test_context_window_handling(self, provider: OllamaProvider):
        """Test handling of context window limits."""
        # Create a prompt that might exceed context
        long_prompt = "Repeat this: " + "hello " * 10000
        
        try:
            response = await provider.complete(
                messages=[Message(role="user", content=long_prompt)],
                model="llama3.2:3b",
            )
            # Should either truncate or handle gracefully
            assert response.content or response.finish_reason == "length"
        except ProviderError as e:
            # Should get a meaningful error
            assert "context" in str(e).lower() or "length" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_unicode_handling(self, provider: OllamaProvider):
        """Test Unicode character handling."""
        unicode_prompts = [
            "こんにちは",  # Japanese
            "Привет",      # Russian
            "🎉🎊🎈",      # Emojis
            "中文测试",    # Chinese
        ]
        
        for prompt in unicode_prompts:
            response = await provider.complete(
                messages=[Message(role="user", content=prompt)],
                model="llama3.2:3b",
            )
            # Should not crash and should return something
            assert response.content is not None
    
    @pytest.mark.asyncio
    async def test_empty_response_handling(self, provider: OllamaProvider):
        """Test handling of potentially empty responses."""
        # Very short max_tokens might cause empty response
        response = await provider.complete(
            messages=[Message(role="user", content="Hello")],
            model="llama3.2:3b",
            max_tokens=1,
        )
        
        # Should handle gracefully
        assert response is not None
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, provider: OllamaProvider):
        """Test timeout handling for slow responses."""
        with pytest.raises((ProviderError, TimeoutError)):
            await provider.complete(
                messages=[Message(role="user", content="Write a novel")],
                model="llama3.2:3b",
                timeout=0.001,  # Very short timeout
            )
    
    @pytest.mark.asyncio
    async def test_model_not_found(self, provider: OllamaProvider):
        """Test error when model doesn't exist."""
        with pytest.raises(ProviderError) as exc_info:
            await provider.complete(
                messages=[Message(role="user", content="Hello")],
                model="nonexistent-model-xyz",
            )
        assert "not found" in str(exc_info.value).lower() or "error" in str(exc_info.value).lower()


class TestOllamaTroubleshooting:
    """Troubleshooting tests for common Ollama issues."""
    
    @pytest.fixture
    async def provider(self) -> OllamaProvider:
        provider = OllamaProvider()
        if not await provider.is_available():
            pytest.skip("Ollama not available")
        return provider
    
    @pytest.mark.asyncio
    async def test_memory_usage(self, provider: OllamaProvider):
        """Monitor memory usage during generation."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Generate multiple responses
        for _ in range(5):
            await provider.complete(
                messages=[Message(role="user", content="Hello")],
                model="llama3.2:3b",
            )
        
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        
        # Memory shouldn't grow excessively (allow 100MB increase)
        assert memory_increase < 100, f"Memory increased by {memory_increase:.1f}MB"
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, provider: OllamaProvider):
        """Test handling of concurrent requests."""
        import asyncio
        
        async def make_request(i: int):
            return await provider.complete(
                messages=[Message(role="user", content=f"Say {i}")],
                model="llama3.2:3b",
            )
        
        # Make 5 concurrent requests
        results = await asyncio.gather(
            *[make_request(i) for i in range(5)],
            return_exceptions=True,
        )
        
        # All should complete (either success or handled error)
        assert len(results) == 5
        successes = sum(1 for r in results if not isinstance(r, Exception))
        assert successes >= 3, "Too many concurrent request failures"
    
    @pytest.mark.asyncio
    async def test_response_quality_consistency(self, provider: OllamaProvider):
        """Test consistency of responses with same prompt."""
        prompt = "What is 2 + 2? Answer with just the number."
        responses = []
        
        for _ in range(5):
            response = await provider.complete(
                messages=[Message(role="user", content=prompt)],
                model="llama3.2:3b",
                temperature=0.0,  # Deterministic
            )
            responses.append(response.content.strip())
        
        # With temperature=0, responses should be very similar
        unique_responses = set(responses)
        # Allow some variation but expect consistency
        assert len(unique_responses) <= 2, \
            f"Inconsistent responses: {unique_responses}"
    
    @pytest.mark.asyncio
    async def test_error_recovery(self, provider: OllamaProvider):
        """Test recovery from errors."""
        # First, cause an error
        try:
            await provider.complete(
                messages=[Message(role="user", content="Hello")],
                model="nonexistent-model",
            )
        except ProviderError:
            pass
        
        # Provider should still work after error
        response = await provider.complete(
            messages=[Message(role="user", content="Hello")],
            model="llama3.2:3b",
        )
        assert response.content


# tests/ollama/test_ollama_troubleshooting.py
"""
Diagnostic tests for Ollama issues.

These tests help identify and diagnose common problems.
"""

import pytest
import httpx

from opencode.provider.ollama import OllamaProvider


class TestOllamaDiagnostics:
    """Diagnostic tests for Ollama setup."""
    
    @pytest.mark.asyncio
    async def test_ollama_server_running(self):
        """Check if Ollama server is running."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "http://localhost:11434/api/tags",
                    timeout=5.0,
                )
            assert response.status_code == 200
        except httpx.ConnectError:
            pytest.fail(
                "Ollama server not running. Start with: ollama serve"
            )
    
    @pytest.mark.asyncio
    async def test_required_models_available(self):
        """Check if required models are pulled."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://localhost:11434/api/tags",
                timeout=5.0,
            )
        
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]
            
            # Check for at least one usable model
            recommended = ["llama3.2", "llama3.1", "qwen2.5", "mistral"]
            has_model = any(
                any(rec in name for name in model_names)
                for rec in recommended
            )
            
            if not has_model:
                pytest.fail(
                    f"No recommended models found. Pull one with: ollama pull llama3.2"
                )
    
    @pytest.mark.asyncio
    async def test_gpu_availability(self):
        """Check GPU availability for Ollama."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://localhost:11434/api/ps",
                timeout=5.0,
            )
        
        if response.status_code == 200:
            data = response.json()
            # Log GPU info for diagnostics
            print(f"Ollama status: {data}")
```

---

## Part 4: Test Automation and CI/CD

### 4.1 pytest Configuration

```toml
# pyproject.toml - test configuration

[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
asyncio_mode = "auto"
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "ollama: marks tests requiring Ollama",
    "provider: marks tests requiring external providers",
    "prompt: marks prompt evaluation tests",
]
filterwarnings = [
    "ignore::DeprecationWarning",
]
addopts = [
    "-ra",
    "-q",
    "--strict-markers",
    "--strict-config",
]
log_cli = true
log_cli_level = "INFO"

[tool.coverage.run]
source = ["src/opencode"]
branch = true
omit = [
    "*/tests/*",
    "*/__main__.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
]
fail_under = 70
```

### 4.2 CI/CD Test Matrix

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install -e .[dev]
      - name: Run unit tests
        run: pytest tests/unit -v --cov

  integration-tests:
    runs-on: ubuntu-latest
    services:
      ollama:
        image: ollama/ollama
        ports:
          - 11434:11434
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -e .[dev]
      - name: Pull Ollama model
        run: ollama pull llama3.2:3b
      - name: Run integration tests
        run: pytest tests/integration tests/ollama -v -m "not slow"

  prompt-tests:
    runs-on: ubuntu-latest
    services:
      ollama:
        image: ollama/ollama
        ports:
          - 11434:11434
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -e .[dev]
      - name: Pull Ollama model
        run: ollama pull llama3.2:3b
      - name: Run prompt tests
        run: pytest tests/prompts -v
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

---

## Part 5: Test Maintenance Guidelines

### 5.1 Adding New Tests

When adding new features, follow these guidelines:

1. **Unit Tests**: Add to `tests/unit/` directory
   - Test individual functions/methods in isolation
   - Mock external dependencies
   - Aim for >90% code coverage on new code

2. **Integration Tests**: Add to `tests/integration/`
   - Test component interactions
   - Use real databases/filesystems when possible
   - Clean up resources after tests

3. **Provider Tests**: Add to `tests/providers/`
   - Test provider-specific behavior
   - Include both mock and real tests
   - Handle API rate limits gracefully

4. **Prompt Tests**: Add to `tests/prompts/`
   - Use standardized test sets
   - Document expected behavior
   - Track accuracy metrics over time

### 5.2 Test Naming Conventions

```python
# Test file naming
test_<module_name>.py           # Unit tests for a module
test_<module_name>_integration.py  # Integration tests

# Test class naming
class Test<FeatureName>:        # Tests for a specific feature
class Test<ClassName>:          # Tests for a specific class

# Test method naming
def test_<action>_<expected_result>():
    """Test description."""
    pass

# Examples
def test_add_file_updates_context():
    """Test that adding a file updates the context tracker."""
    pass

def test_ollama_connection_fails_gracefully():
    """Test that Ollama connection failures are handled gracefully."""
    pass
```

### 5.3 Test Data Management

```python
# tests/fixtures/test_data.py
"""
Centralized test data management.

Use this module to manage test data that can be updated
without changing test code.
"""

from pathlib import Path
import json

FIXTURES_DIR = Path(__file__).parent

def load_test_prompts() -> dict:
    """Load test prompts from JSON file."""
    with open(FIXTURES_DIR / "test_prompts.json") as f:
        return json.load(f)

def load_expected_responses() -> dict:
    """Load expected responses for validation."""
    with open(FIXTURES_DIR / "expected_responses.json") as f:
        return json.load(f)
```

---

## Part 6: Monitoring and Reporting

### 6.1 Test Metrics Dashboard

Track the following metrics:
- Test pass/fail rates by category
- Code coverage trends
- Prompt accuracy by model
- Test execution time trends
- Flaky test identification

### 6.2 Accuracy Tracking

```python
# tests/utils/accuracy_tracker.py
"""
Track prompt accuracy over time.
"""

import json
from datetime import datetime
from pathlib import Path

class AccuracyTracker:
    """Track and store accuracy metrics."""
    
    def __init__(self, storage_dir: Path = None):
        self.storage_dir = storage_dir or Path("test_results/accuracy")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def record_result(
        self,
        test_name: str,
        model: str,
        accuracy: float,
        latency_ms: float,
    ):
        """Record a test result."""
        today = datetime.now().strftime("%Y-%m-%d")
        file_path = self.storage_dir / f"{today}.json"
        
        data = {}
        if file_path.exists():
            with open(file_path) as f:
                data = json.load(f)
        
        if test_name not in data:
            data[test_name] = {}
        
        data[test_name][model] = {
            "accuracy": accuracy,
            "latency_ms": latency_ms,
            "timestamp": datetime.now().isoformat(),
        }
        
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
```

---

## Summary

This testing plan provides:

1. **Comprehensive Coverage**: Unit, integration, provider, prompt, and E2E tests
2. **Prompt Comparison**: Cross-model comparison tests for prompt evaluation
3. **Ollama Testing**: Dedicated tests for Ollama integration, accuracy, and troubleshooting
4. **Future-Proof Design**: Modular structure that accommodates new features
5. **CI/CD Ready**: GitHub Actions workflow for automated testing
6. **Monitoring**: Accuracy tracking and metrics collection

---

## Quick Reference Commands

```bash
# Full test suite with coverage
cd src/opencode && python -m pytest src/opencode/tests/ --cov=src/opencode --cov-report=term-missing -q

# Quick test run (unit tests only)
cd src/opencode && python -m pytest src/opencode/tests/unit/ -v --tb=short

# Run specific test category
cd src/opencode && python -m pytest src/opencode/tests/integration/ -v
cd src/opencode && python -m pytest src/opencode/tests/providers/ -v

# Run with markers
cd src/opencode && python -m pytest -m "not slow" -v
cd src/opencode && python -m pytest -m "ollama" -v

# Generate HTML coverage report
cd src/opencode && python -m pytest --cov=src/opencode --cov-report=html
```

### Test Priority Matrix

| Priority | Test Type | Frequency | Automation |
|----------|-----------|-----------|------------|
| P0 | Unit Tests | Every commit | Full |
| P0 | Provider Tests | Every commit | Full (mock) |
| P1 | Integration Tests | Every PR | Full |
| P1 | Ollama Tests | Every PR | Full |
| P2 | Prompt Comparison | Weekly | Partial |
| P2 | Accuracy Benchmarks | Weekly | Full |
| P3 | E2E Tests | Release | Manual trigger |
