# Ollama Integration Testing

> **Navigation:** [TESTING_PLAN.md](../plans/TESTING_PLAN.md) - Main testing strategy overview

This document describes Ollama-specific integration tests, including connection testing, accuracy benchmarks, and troubleshooting diagnostics.

---

## Ollama Connection and Basic Tests

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

---

## Ollama Accuracy and Troubleshooting Tests

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
```

---

## Ollama Diagnostic Tests

```python
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

## Related Documentation

- [TESTING_INFRASTRUCTURE.md](TESTING_INFRASTRUCTURE.md) - Test directory structure and configuration
- [PROMPT_TESTING.md](PROMPT_TESTING.md) - Prompt comparison and accuracy tests
- [CI_CD_TESTING.md](CI_CD_TESTING.md) - CI/CD configuration
