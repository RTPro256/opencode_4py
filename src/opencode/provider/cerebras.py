"""
Cerebras provider implementation.

This module provides integration with Cerebras AI for ultra-fast
inference using their wafer-scale engine technology.
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


class CerebrasProvider(Provider):
    """
    Provider for Cerebras AI API.
    
    Cerebras provides ultra-fast inference using their wafer-scale
    engine technology, enabling extremely fast response times.
    
    Features:
    - Ultra-fast streaming responses
    - Function calling
    - OpenAI-compatible API
    """
    
    API_URL = "https://api.cerebras.ai/v1/chat/completions"
    
    MODELS = [
        ModelInfo(
            id="llama-3.3-70b",
            name="Llama 3.3 70B (Cerebras)",
            provider="cerebras",
            context_length=8192,
            supports_tools=True,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=0.60,
            output_price_per_million=0.60,
            description="Llama 3.3 70B on Cerebras - ultra-fast inference",
        ),
        ModelInfo(
            id="llama-3.1-8b",
            name="Llama 3.1 8B (Cerebras)",
            provider="cerebras",
            context_length=8192,
            supports_tools=True,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=0.10,
            output_price_per_million=0.10,
            description="Llama 3.1 8B on Cerebras - fastest inference",
        ),
    ]
    
    def __init__(
        self,
        api_key: str,
        timeout: float = 60.0,
    ):
        """
        Initialize Cerebras provider.
        
        Args:
            api_key: Cerebras API key
            timeout: Request timeout in seconds
        """
        self._api_key = api_key
        self._timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)
    
    @property
    def name(self) -> str:
        """Provider name."""
        return "cerebras"
    
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
        """Parse error response from Cerebras."""
        try:
            error_data = response.json()
            error = error_data.get("error", {})
            code = error.get("code", "")
            message = error.get("message", response.text)
            
            if response.status_code == 401:
                return AuthenticationError(message, provider="cerebras", code=code)
            elif response.status_code == 404:
                return ModelNotFoundError(message, provider="cerebras", code=code)
            elif response.status_code == 429:
                return RateLimitError(message, provider="cerebras", code=code)
            else:
                return ProviderError(message, provider="cerebras", code=code)
        except Exception:
            return ProviderError(
                f"Cerebras error: {response.status_code} - {response.text}",
                provider="cerebras",
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
        """Stream a completion from Cerebras."""
        body: dict[str, Any] = {
            "model": model,
            "messages": [],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }
        
        if system:
            body["messages"].append({"role": "system", "content": system})
        
        for msg in messages:
            body["messages"].append(msg.to_openai_format())
        
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
                    
                    text = delta.get("content", "")
                    
                    tool_calls: list[ToolCall] = []
                    if "tool_calls" in delta:
                        for tc in delta["tool_calls"]:
                            if "function" in tc and tc["function"].get("name"):
                                tool_calls.append(ToolCall.from_openai(tc))
                    
                    reason = None
                    if finish_reason:
                        reason = FinishReason(finish_reason) if finish_reason in [r.value for r in FinishReason] else FinishReason.STOP
                    
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
            raise ProviderError("Cannot connect to Cerebras API", provider="cerebras", model=model) from e
        except httpx.ReadTimeout as e:
            raise ProviderError(f"Cerebras request timed out after {self._timeout}s", provider="cerebras", model=model) from e
    
    async def count_tokens(self, text: str, model: str) -> int:
        return len(text) // 4
    
    async def close(self) -> None:
        await self._client.aclose()
