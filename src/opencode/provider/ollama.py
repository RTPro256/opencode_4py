"""
Ollama provider implementation.

This module provides integration with Ollama for running local models.
Supports streaming, function calling, and vision capabilities through
Ollama's OpenAI-compatible API.
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator, Optional

import httpx

logger = logging.getLogger(__name__)

from opencode.core.defaults import LLM_TIMEOUT, OLLAMA_BASE_URL

from opencode.provider.base import (
    FinishReason,
    Message,
    ModelInfo,
    Provider,
    ProviderError,
    StreamChunk,
    ToolCall,
    ToolDefinition,
    Usage,
)


class OllamaProvider(Provider):
    """
    Provider for Ollama local models.
    
    Ollama runs models locally and provides an OpenAI-compatible API.
    Default endpoint is http://localhost:11434
    
    Supports any model available through Ollama:
    - llama3.1, llama3.2
    - mistral, mixtral
    - codellama
    - deepseek-coder
    - qwen2.5
    - And many more...
    
    Features:
    - Streaming responses
    - Function calling (on supported models)
    - Vision (on supported models like llava)
    - No API key required (local)
    """
    
    DEFAULT_URL = OLLAMA_BASE_URL
    
    # Common Ollama models with their specifications
    COMMON_MODELS = [
        ModelInfo(
            id="llama3.1:8b",
            name="Llama 3.1 8B",
            provider="ollama",
            context_length=128000,
            supports_tools=True,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=0.0,  # Local = free
            output_price_per_million=0.0,
            description="Meta's Llama 3.1 8B model, great for general tasks",
        ),
        ModelInfo(
            id="llama3.1:70b",
            name="Llama 3.1 70B",
            provider="ollama",
            context_length=128000,
            supports_tools=True,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=0.0,
            output_price_per_million=0.0,
            description="Meta's Llama 3.1 70B model, highly capable",
        ),
        ModelInfo(
            id="llama3.2:3b",
            name="Llama 3.2 3B",
            provider="ollama",
            context_length=128000,
            supports_tools=True,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=0.0,
            output_price_per_million=0.0,
            description="Lightweight Llama 3.2 model",
        ),
        ModelInfo(
            id="llama3.2-vision:11b",
            name="Llama 3.2 Vision 11B",
            provider="ollama",
            context_length=128000,
            supports_tools=True,
            supports_vision=True,
            supports_streaming=True,
            input_price_per_million=0.0,
            output_price_per_million=0.0,
            description="Llama 3.2 with vision capabilities",
        ),
        ModelInfo(
            id="mistral:7b",
            name="Mistral 7B",
            provider="ollama",
            context_length=32768,
            supports_tools=True,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=0.0,
            output_price_per_million=0.0,
            description="Mistral 7B, efficient and capable",
        ),
        ModelInfo(
            id="mixtral:8x7b",
            name="Mixtral 8x7B",
            provider="ollama",
            context_length=32768,
            supports_tools=True,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=0.0,
            output_price_per_million=0.0,
            description="Mixtral MoE model",
        ),
        ModelInfo(
            id="codellama:34b",
            name="Code Llama 34B",
            provider="ollama",
            context_length=16384,
            supports_tools=False,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=0.0,
            output_price_per_million=0.0,
            description="Specialized for code generation",
        ),
        ModelInfo(
            id="deepseek-coder:33b",
            name="DeepSeek Coder 33B",
            provider="ollama",
            context_length=16384,
            supports_tools=True,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=0.0,
            output_price_per_million=0.0,
            description="Excellent for coding tasks",
        ),
        ModelInfo(
            id="qwen2.5:72b",
            name="Qwen 2.5 72B",
            provider="ollama",
            context_length=131072,
            supports_tools=True,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=0.0,
            output_price_per_million=0.0,
            description="Alibaba's Qwen 2.5 model",
        ),
        ModelInfo(
            id="llava:13b",
            name="LLaVA 13B",
            provider="ollama",
            context_length=4096,
            supports_tools=False,
            supports_vision=True,
            supports_streaming=True,
            input_price_per_million=0.0,
            output_price_per_million=0.0,
            description="Vision-language model",
        ),
    ]
    
    def __init__(
        self,
        base_url: str = DEFAULT_URL,
        timeout: float = LLM_TIMEOUT,  # Uses centralized default from defaults.py
    ):
        """
        Initialize Ollama provider.
        
        Args:
            base_url: Ollama server URL (default: http://localhost:11434)
            timeout: Request timeout in seconds
        """
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)
        self._models_cache: Optional[list[ModelInfo]] = None
    
    @property
    def name(self) -> str:
        """Provider name."""
        return "ollama"
    
    @property
    def models(self) -> list[ModelInfo]:
        """Available models from this provider."""
        # Return common models as defaults
        # Actual available models are fetched dynamically
        return self.COMMON_MODELS
    
    async def get_available_models(self) -> list[str]:
        """
        Get list of models actually available on the Ollama server.
        
        Returns:
            List of model names/IDs
        """
        try:
            response = await self._client.get(f"{self._base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            logger.warning(f"Failed to parse Ollama models: {e}")
            return []
    
    async def complete(
        self,
        messages: list[Message],
        model: str,
        tools: Optional[list[ToolDefinition]] = None,
        *,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """
        Stream a completion from the Ollama model.
        
        Uses Ollama's OpenAI-compatible /v1/chat/completions endpoint.
        """
        # Build request body in OpenAI format
        body: dict[str, Any] = {
            "model": model,
            "messages": [],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }
        
        # Add system message if provided
        if system:
            body["messages"].append({"role": "system", "content": system})
        
        # Convert messages
        for msg in messages:
            body["messages"].append(msg.to_openai_format())
        
        # Add tools if provided
        if tools:
            body["tools"] = [t.to_openai_format() for t in tools]
        
        # Make streaming request
        url = f"{self._base_url}/v1/chat/completions"
        
        try:
            async with self._client.stream(
                "POST",
                url,
                json=body,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise ProviderError(
                        f"Ollama error: {response.status_code} - {error_text.decode()}",
                        provider="ollama",
                        model=model,
                    )
                
                async for line in response.aiter_lines():
                    if not line or line == "data: [DONE]":
                        continue
                    
                    if line.startswith("data: "):
                        line = line[6:]  # Remove "data: " prefix
                    
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    
                    choices = chunk.get("choices", [])
                    if not choices:
                        continue
                    
                    choice = choices[0]
                    delta = choice.get("delta", {})
                    finish_reason = choice.get("finish_reason")
                    
                    # Handle text content
                    text = delta.get("content", "")
                    
                    # Handle tool calls
                    tool_calls: list[ToolCall] = []
                    if "tool_calls" in delta:
                        for tc in delta["tool_calls"]:
                            # Ollama may stream tool calls incrementally
                            if "function" in tc and tc["function"].get("name"):
                                tool_calls.append(ToolCall.from_openai(tc))
                    
                    # Handle finish reason
                    reason = None
                    if finish_reason:
                        reason = FinishReason(finish_reason) if finish_reason in [r.value for r in FinishReason] else FinishReason.STOP
                    
                    # Handle usage (may come in final chunk)
                    usage = None
                    if "usage" in chunk:
                        u = chunk["usage"]
                        usage = Usage(
                            input_tokens=u.get("prompt_tokens", 0),
                            output_tokens=u.get("completion_tokens", 0),
                        )
                    
                    if text or tool_calls or reason:
                        yield StreamChunk(
                            delta=text,
                            tool_calls=tool_calls,
                            finish_reason=reason,
                            usage=usage,
                        )
                        
        except httpx.ConnectError as e:
            raise ProviderError(
                f"Cannot connect to Ollama at {self._base_url}. Is Ollama running?",
                provider="ollama",
                model=model,
            ) from e
        except httpx.ReadTimeout as e:
            raise ProviderError(
                f"Ollama request timed out after {self._timeout}s",
                provider="ollama",
                model=model,
            ) from e
    
    async def count_tokens(self, text: str, model: str) -> int:
        """
        Count tokens for the given text.
        
        Ollama doesn't have a dedicated token counting endpoint,
        so we estimate based on character count (rough approximation).
        """
        # Rough estimation: ~4 characters per token for most models
        # This is a simplification - actual tokenization varies by model
        return len(text) // 4
    
    async def pull_model(self, model: str) -> bool:
        """
        Pull/download a model to the Ollama server.
        
        Args:
            model: Model name to pull (e.g., "llama3.1:8b")
            
        Returns:
            True if successful
        """
        try:
            response = await self._client.post(
                f"{self._base_url}/api/pull",
                json={"name": model, "stream": False},
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.warning(f"Failed to pull model {model}: {e}")
            return False
    
    async def is_running(self) -> bool:
        """Check if Ollama server is running."""
        try:
            response = await self._client.get(f"{self._base_url}/api/version")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Failed to check Ollama running status: {e}")
            return False
    
    async def get_version(self) -> Optional[str]:
        """Get Ollama server version."""
        try:
            response = await self._client.get(f"{self._base_url}/api/version")
            response.raise_for_status()
            data = response.json()
            return data.get("version")
        except Exception as e:
            logger.warning(f"Failed to get Ollama version: {e}")
            return None
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
