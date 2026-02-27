"""
Together AI provider implementation.

This module provides integration with Together AI's inference platform,
offering access to open-source models at competitive prices.
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


class TogetherProvider(Provider):
    """
    Provider for Together AI API.
    
    Together AI provides access to open-source models with fast
    inference and competitive pricing.
    
    Features:
    - Streaming responses
    - Function calling (on supported models)
    - OpenAI-compatible API
    - Wide model selection
    """
    
    API_URL = "https://api.together.xyz/v1/chat/completions"
    
    # Popular Together AI models
    MODELS = [
        ModelInfo(
            id="meta-llama/Llama-3.3-70B-Instruct-Turbo",
            name="Llama 3.3 70B Turbo",
            provider="together",
            context_length=131072,
            supports_tools=True,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=0.88,
            output_price_per_million=0.88,
            description="Meta Llama 3.3 70B on Together AI",
        ),
        ModelInfo(
            id="meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo",
            name="Llama 3.2 90B Vision",
            provider="together",
            context_length=131072,
            supports_tools=True,
            supports_vision=True,
            supports_streaming=True,
            input_price_per_million=0.88,
            output_price_per_million=0.88,
            description="Llama 3.2 with vision capabilities",
        ),
        ModelInfo(
            id="Qwen/Qwen2.5-72B-Instruct-Turbo",
            name="Qwen 2.5 72B Turbo",
            provider="together",
            context_length=32768,
            supports_tools=True,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=0.88,
            output_price_per_million=0.88,
            description="Alibaba's Qwen 2.5 72B model",
        ),
        ModelInfo(
            id="mistralai/Mixtral-8x7B-Instruct-v0.1",
            name="Mixtral 8x7B",
            provider="together",
            context_length=32768,
            supports_tools=False,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=0.60,
            output_price_per_million=0.60,
            description="Mistral's mixture-of-experts model",
        ),
        ModelInfo(
            id="mistralai/Mistral-7B-Instruct-v0.3",
            name="Mistral 7B",
            provider="together",
            context_length=32768,
            supports_tools=True,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=0.20,
            output_price_per_million=0.20,
            description="Efficient Mistral 7B model",
        ),
        ModelInfo(
            id="deepseek-ai/DeepSeek-V3",
            name="DeepSeek V3",
            provider="together",
            context_length=128000,
            supports_tools=True,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=0.50,
            output_price_per_million=1.20,
            description="DeepSeek's latest model",
        ),
        ModelInfo(
            id="google/gemma-2-27b-it",
            name="Gemma 2 27B",
            provider="together",
            context_length=8192,
            supports_tools=False,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=0.80,
            output_price_per_million=0.80,
            description="Google's Gemma 2 27B model",
        ),
    ]
    
    def __init__(
        self,
        api_key: str,
        timeout: float = 120.0,
    ):
        """
        Initialize Together AI provider.
        
        Args:
            api_key: Together AI API key
            timeout: Request timeout in seconds
        """
        self._api_key = api_key
        self._timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)
    
    @property
    def name(self) -> str:
        """Provider name."""
        return "together"
    
    @property
    def models(self) -> list[ModelInfo]:
        """Available models from this provider."""
        return self.MODELS
    
    def _get_headers(self) -> dict[str, str]:
        """Build request headers."""
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
    
    def _parse_error(self, response: httpx.Response) -> ProviderError:
        """Parse error response from Together AI."""
        try:
            error_data = response.json()
            error = error_data.get("error", {})
            code = error.get("code", "")
            message = error.get("message", response.text)
            
            if response.status_code == 401:
                return AuthenticationError(
                    message,
                    provider="together",
                    code=code,
                )
            elif response.status_code == 404:
                return ModelNotFoundError(
                    message,
                    provider="together",
                    code=code,
                )
            elif response.status_code == 429:
                return RateLimitError(
                    message,
                    provider="together",
                    code=code,
                )
            else:
                return ProviderError(
                    message,
                    provider="together",
                    code=code,
                )
        except Exception:
            return ProviderError(
                f"Together AI error: {response.status_code} - {response.text}",
                provider="together",
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
        Stream a completion from Together AI.
        
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
                "Cannot connect to Together AI API",
                provider="together",
                model=model,
            ) from e
        except httpx.ReadTimeout as e:
            raise ProviderError(
                f"Together AI request timed out after {self._timeout}s",
                provider="together",
                model=model,
            ) from e
    
    async def count_tokens(self, text: str, model: str) -> int:
        """Count tokens (approximation)."""
        return len(text) // 4
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
