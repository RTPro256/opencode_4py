"""
xAI (Grok) provider implementation.

This module provides integration with xAI's Grok models.
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


class XAIProvider(Provider):
    """
    Provider for xAI (Grok) API.
    
    xAI provides Grok models developed by Elon Musk's AI company.
    Known for having real-time knowledge via X (Twitter) integration.
    
    Features:
    - Streaming responses
    - Function calling
    - Vision support
    - OpenAI-compatible API
    """
    
    API_URL = "https://api.x.ai/v1/chat/completions"
    
    # Available xAI models
    MODELS = [
        ModelInfo(
            id="grok-2-latest",
            name="Grok 2",
            provider="xai",
            context_length=131072,
            supports_tools=True,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=2.00,
            output_price_per_million=10.00,
            description="xAI's latest Grok 2 model",
        ),
        ModelInfo(
            id="grok-2-vision-latest",
            name="Grok 2 Vision",
            provider="xai",
            context_length=32768,
            supports_tools=True,
            supports_vision=True,
            supports_streaming=True,
            input_price_per_million=2.00,
            output_price_per_million=10.00,
            description="Grok 2 with vision capabilities",
        ),
        ModelInfo(
            id="grok-beta",
            name="Grok Beta",
            provider="xai",
            context_length=131072,
            supports_tools=True,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=5.00,
            output_price_per_million=15.00,
            description="Grok beta model",
        ),
    ]
    
    def __init__(
        self,
        api_key: str,
        timeout: float = 120.0,
    ):
        """
        Initialize xAI provider.
        
        Args:
            api_key: xAI API key
            timeout: Request timeout in seconds
        """
        self._api_key = api_key
        self._timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)
    
    @property
    def name(self) -> str:
        """Provider name."""
        return "xai"
    
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
        """Parse error response from xAI."""
        try:
            error_data = response.json()
            error = error_data.get("error", {})
            code = error.get("code", "")
            message = error.get("message", response.text)
            
            if response.status_code == 401:
                return AuthenticationError(
                    message,
                    provider="xai",
                    code=code,
                )
            elif response.status_code == 404:
                return ModelNotFoundError(
                    message,
                    provider="xai",
                    code=code,
                )
            elif response.status_code == 429:
                return RateLimitError(
                    message,
                    provider="xai",
                    code=code,
                )
            else:
                return ProviderError(
                    message,
                    provider="xai",
                    code=code,
                )
        except Exception:
            return ProviderError(
                f"xAI error: {response.status_code} - {response.text}",
                provider="xai",
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
        Stream a completion from xAI.
        
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
                "Cannot connect to xAI API",
                provider="xai",
                model=model,
            ) from e
        except httpx.ReadTimeout as e:
            raise ProviderError(
                f"xAI request timed out after {self._timeout}s",
                provider="xai",
                model=model,
            ) from e
    
    async def count_tokens(self, text: str, model: str) -> int:
        """Count tokens (approximation)."""
        return len(text) // 4
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
