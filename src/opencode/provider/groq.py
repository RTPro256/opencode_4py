"""
Groq provider implementation.

This module provides integration with Groq for ultra-fast inference.
Groq uses their LPU (Language Processing Unit) for extremely fast
inference speeds.
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


class GroqProvider(Provider):
    """
    Provider for Groq API.
    
    Groq provides ultra-fast inference using their custom LPU hardware.
    Known for being the fastest inference provider.
    
    Features:
    - Ultra-fast streaming responses
    - Function calling
    - OpenAI-compatible API
    """
    
    API_URL = "https://api.groq.com/openai/v1/chat/completions"
    
    # Available Groq models
    MODELS = [
        ModelInfo(
            id="llama-3.3-70b-versatile",
            name="Llama 3.3 70B Versatile",
            provider="groq",
            context_length=131072,
            supports_tools=True,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=0.59,
            output_price_per_million=0.79,
            description="Meta Llama 3.3 70B - versatile model for various tasks",
        ),
        ModelInfo(
            id="llama-3.3-70b-specdec",
            name="Llama 3.3 70B Speculative",
            provider="groq",
            context_length=131072,
            supports_tools=True,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=0.59,
            output_price_per_million=0.99,
            description="Llama 3.3 70B with speculative decoding for faster responses",
        ),
        ModelInfo(
            id="llama-3.1-8b-instant",
            name="Llama 3.1 8B Instant",
            provider="groq",
            context_length=131072,
            supports_tools=True,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=0.05,
            output_price_per_million=0.08,
            description="Fast and efficient Llama 3.1 8B model",
        ),
        ModelInfo(
            id="mixtral-8x7b-32768",
            name="Mixtral 8x7B",
            provider="groq",
            context_length=32768,
            supports_tools=True,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=0.24,
            output_price_per_million=0.24,
            description="Mistral's mixture-of-experts model",
        ),
        ModelInfo(
            id="gemma2-9b-it",
            name="Gemma 2 9B",
            provider="groq",
            context_length=8192,
            supports_tools=False,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=0.20,
            output_price_per_million=0.20,
            description="Google's Gemma 2 9B instruction-tuned model",
        ),
        ModelInfo(
            id="deepseek-r1-distill-llama-70b",
            name="DeepSeek R1 Distill Llama 70B",
            provider="groq",
            context_length=131072,
            supports_tools=True,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=0.75,
            output_price_per_million=1.00,
            description="DeepSeek R1 distilled into Llama 70B",
        ),
    ]
    
    def __init__(
        self,
        api_key: str,
        timeout: float = 60.0,
    ):
        """
        Initialize Groq provider.
        
        Args:
            api_key: Groq API key
            timeout: Request timeout in seconds
        """
        self._api_key = api_key
        self._timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)
    
    @property
    def name(self) -> str:
        """Provider name."""
        return "groq"
    
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
        """Parse error response from Groq."""
        try:
            error_data = response.json()
            error = error_data.get("error", {})
            code = error.get("code", "")
            message = error.get("message", response.text)
            
            if response.status_code == 401:
                return AuthenticationError(
                    message,
                    provider="groq",
                    code=code,
                )
            elif response.status_code == 404:
                return ModelNotFoundError(
                    message,
                    provider="groq",
                    code=code,
                )
            elif response.status_code == 429:
                return RateLimitError(
                    message,
                    provider="groq",
                    code=code,
                )
            else:
                return ProviderError(
                    message,
                    provider="groq",
                    code=code,
                )
        except Exception:
            return ProviderError(
                f"Groq error: {response.status_code} - {response.text}",
                provider="groq",
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
        Stream a completion from Groq.
        
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
                "Cannot connect to Groq API",
                provider="groq",
                model=model,
            ) from e
        except httpx.ReadTimeout as e:
            raise ProviderError(
                f"Groq request timed out after {self._timeout}s",
                provider="groq",
                model=model,
            ) from e
    
    async def count_tokens(self, text: str, model: str) -> int:
        """Count tokens (approximation)."""
        return len(text) // 4
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
