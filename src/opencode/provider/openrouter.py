"""
OpenRouter provider implementation.

This module provides integration with OpenRouter, a unified API for multiple
AI model providers. Supports streaming, function calling, and access to
models from OpenAI, Anthropic, Google, Meta, and more.
"""

from __future__ import annotations

import json
from typing import Any, AsyncIterator, Optional

import httpx

from opencode.provider.base import (
    AuthenticationError,
    FinishReason,
    Message,
    ModelInfo,
    ModelNotFoundError,
    Provider,
    ProviderError,
    RateLimitError,
    StreamChunk,
    ToolCall,
    ToolDefinition,
    Usage,
)


class OpenRouterProvider(Provider):
    """
    Provider for OpenRouter API.
    
    OpenRouter provides a unified API to access models from multiple providers:
    - OpenAI (GPT-4, GPT-3.5)
    - Anthropic (Claude)
    - Google (Gemini)
    - Meta (Llama)
    - Mistral
    - And many more...
    
    Features:
    - Streaming responses
    - Function calling (on supported models)
    - Vision (on supported models)
    - Automatic fallbacks
    - Cost optimization
    """
    
    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    
    # Popular models available through OpenRouter
    POPULAR_MODELS = [
        ModelInfo(
            id="openai/gpt-4o",
            name="GPT-4o (OpenRouter)",
            provider="openrouter",
            context_length=128000,
            supports_tools=True,
            supports_vision=True,
            supports_streaming=True,
            input_price_per_million=5.00,
            output_price_per_million=15.00,
            description="OpenAI GPT-4o via OpenRouter",
        ),
        ModelInfo(
            id="openai/gpt-4o-mini",
            name="GPT-4o Mini (OpenRouter)",
            provider="openrouter",
            context_length=128000,
            supports_tools=True,
            supports_vision=True,
            supports_streaming=True,
            input_price_per_million=0.15,
            output_price_per_million=0.60,
            description="OpenAI GPT-4o Mini via OpenRouter",
        ),
        ModelInfo(
            id="anthropic/claude-3.5-sonnet",
            name="Claude 3.5 Sonnet (OpenRouter)",
            provider="openrouter",
            context_length=200000,
            supports_tools=True,
            supports_vision=True,
            supports_streaming=True,
            input_price_per_million=3.00,
            output_price_per_million=15.00,
            description="Anthropic Claude 3.5 Sonnet via OpenRouter",
        ),
        ModelInfo(
            id="anthropic/claude-3-opus",
            name="Claude 3 Opus (OpenRouter)",
            provider="openrouter",
            context_length=200000,
            supports_tools=True,
            supports_vision=True,
            supports_streaming=True,
            input_price_per_million=15.00,
            output_price_per_million=75.00,
            description="Anthropic Claude 3 Opus via OpenRouter",
        ),
        ModelInfo(
            id="google/gemini-pro-1.5",
            name="Gemini Pro 1.5 (OpenRouter)",
            provider="openrouter",
            context_length=2800000,
            supports_tools=True,
            supports_vision=True,
            supports_streaming=True,
            input_price_per_million=1.25,
            output_price_per_million=5.00,
            description="Google Gemini Pro 1.5 via OpenRouter",
        ),
        ModelInfo(
            id="meta-llama/llama-3.1-70b-instruct",
            name="Llama 3.1 70B (OpenRouter)",
            provider="openrouter",
            context_length=131072,
            supports_tools=True,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=0.52,
            output_price_per_million=0.75,
            description="Meta Llama 3.1 70B via OpenRouter",
        ),
        ModelInfo(
            id="meta-llama/llama-3.1-405b-instruct",
            name="Llama 3.1 405B (OpenRouter)",
            provider="openrouter",
            context_length=131072,
            supports_tools=True,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=2.70,
            output_price_per_million=2.70,
            description="Meta Llama 3.1 405B via OpenRouter",
        ),
        ModelInfo(
            id="mistralai/mistral-large",
            name="Mistral Large (OpenRouter)",
            provider="openrouter",
            context_length=128000,
            supports_tools=True,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=2.00,
            output_price_per_million=6.00,
            description="Mistral Large via OpenRouter",
        ),
        ModelInfo(
            id="deepseek/deepseek-coder",
            name="DeepSeek Coder (OpenRouter)",
            provider="openrouter",
            context_length=16384,
            supports_tools=True,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=0.14,
            output_price_per_million=0.28,
            description="DeepSeek Coder via OpenRouter",
        ),
        ModelInfo(
            id="qwen/qwen-2.5-72b-instruct",
            name="Qwen 2.5 72B (OpenRouter)",
            provider="openrouter",
            context_length=131072,
            supports_tools=True,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=0.35,
            output_price_per_million=0.40,
            description="Alibaba Qwen 2.5 72B via OpenRouter",
        ),
    ]
    
    def __init__(
        self,
        api_key: str,
        site_url: Optional[str] = None,
        site_name: Optional[str] = None,
        timeout: float = 120.0,
    ):
        """
        Initialize OpenRouter provider.
        
        Args:
            api_key: OpenRouter API key
            site_url: Optional site URL for rankings on openrouter.ai
            site_name: Optional site name for rankings
            timeout: Request timeout in seconds
        """
        self._api_key = api_key
        self._site_url = site_url
        self._site_name = site_name
        self._timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)
    
    @property
    def name(self) -> str:
        """Provider name."""
        return "openrouter"
    
    @property
    def models(self) -> list[ModelInfo]:
        """Available models from this provider."""
        return self.POPULAR_MODELS
    
    async def get_available_models(self) -> list[dict[str, Any]]:
        """
        Get list of all models available on OpenRouter.
        
        Returns:
            List of model information dictionaries
        """
        try:
            response = await self._client.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {self._api_key}"},
            )
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except Exception:
            return []
    
    def _get_headers(self) -> dict[str, str]:
        """Build request headers."""
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self._site_url or "https://github.com/opencode",
            "X-Title": self._site_name or "OpenCode",
        }
        return headers
    
    def _parse_error(self, response: httpx.Response) -> ProviderError:
        """Parse error response from OpenRouter."""
        try:
            error_data = response.json()
            error = error_data.get("error", {})
            code = error.get("code", "")
            message = error.get("message", response.text)
            
            if response.status_code == 401:
                return AuthenticationError(
                    message,
                    provider="openrouter",
                    code=code,
                )
            elif response.status_code == 404 or "not found" in message.lower():
                return ModelNotFoundError(
                    message,
                    provider="openrouter",
                    code=code,
                )
            elif response.status_code == 429:
                retry_after = response.headers.get("retry-after")
                return RateLimitError(
                    message,
                    retry_after=int(retry_after) if retry_after else None,
                    provider="openrouter",
                    code=code,
                )
            else:
                return ProviderError(
                    message,
                    provider="openrouter",
                    code=code,
                )
        except Exception:
            return ProviderError(
                f"OpenRouter error: {response.status_code} - {response.text}",
                provider="openrouter",
            )
    
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
        Stream a completion from OpenRouter.
        
        Uses OpenAI-compatible API format.
        """
        # Build request body
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
        
        # Add OpenRouter-specific options
        if "transforms" in kwargs:
            body["transforms"] = kwargs["transforms"]
        if "route" in kwargs:
            body["route"] = kwargs["route"]
        if "provider" in kwargs:
            body["provider"] = kwargs["provider"]
        
        try:
            async with self._client.stream(
                "POST",
                self.API_URL,
                json=body,
                headers=self._get_headers(),
            ) as response:
                if response.status_code != 200:
                    raise self._parse_error(response)
                
                async for line in response.aiter_lines():
                    if not line or line == "data: [DONE]":
                        continue
                    
                    if line.startswith("data: "):
                        line = line[6:]
                    
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
                            if "function" in tc and tc["function"].get("name"):
                                tool_calls.append(ToolCall.from_openai(tc))
                    
                    # Handle finish reason
                    reason = None
                    if finish_reason:
                        reason = FinishReason(finish_reason) if finish_reason in [r.value for r in FinishReason] else FinishReason.STOP
                    
                    # Handle usage
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
                "Cannot connect to OpenRouter API",
                provider="openrouter",
                model=model,
            ) from e
        except httpx.ReadTimeout as e:
            raise ProviderError(
                f"OpenRouter request timed out after {self._timeout}s",
                provider="openrouter",
                model=model,
            ) from e
    
    async def count_tokens(self, text: str, model: str) -> int:
        """
        Count tokens for the given text.
        
        Approximation: ~4 characters per token.
        """
        return len(text) // 4
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
