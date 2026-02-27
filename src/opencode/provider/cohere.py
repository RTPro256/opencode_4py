"""
Cohere provider implementation.

This module provides integration with Cohere's language models,
specializing in enterprise AI with RAG and embedding capabilities.
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


class CohereProvider(Provider):
    """
    Provider for Cohere API.
    
    Cohere provides enterprise-focused AI models with strong
    RAG (Retrieval Augmented Generation) capabilities.
    
    Features:
    - Streaming responses
    - Function calling
    - RAG optimization
    - Embedding generation
    """
    
    API_URL = "https://api.cohere.ai/v2/chat"
    
    # Available Cohere models
    MODELS = [
        ModelInfo(
            id="command-r-plus-08-2024",
            name="Command R+",
            provider="cohere",
            context_length=128000,
            supports_tools=True,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=2.50,
            output_price_per_million=10.00,
            description="Cohere's most powerful RAG-optimized model",
        ),
        ModelInfo(
            id="command-r-08-2024",
            name="Command R",
            provider="cohere",
            context_length=128000,
            supports_tools=True,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=0.15,
            output_price_per_million=0.60,
            description="Efficient RAG-optimized model",
        ),
        ModelInfo(
            id="command",
            name="Command",
            provider="cohere",
            context_length=4096,
            supports_tools=False,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=1.00,
            output_price_per_million=2.00,
            description="General-purpose instruction-following model",
        ),
        ModelInfo(
            id="command-light",
            name="Command Light",
            provider="cohere",
            context_length=4096,
            supports_tools=False,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=0.30,
            output_price_per_million=0.60,
            description="Lightweight and fast model",
        ),
        ModelInfo(
            id="command-nightly",
            name="Command Nightly",
            provider="cohere",
            context_length=4096,
            supports_tools=False,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=1.00,
            output_price_per_million=2.00,
            description="Latest experimental Command model",
        ),
    ]
    
    def __init__(
        self,
        api_key: str,
        timeout: float = 120.0,
    ):
        """
        Initialize Cohere provider.
        
        Args:
            api_key: Cohere API key
            timeout: Request timeout in seconds
        """
        self._api_key = api_key
        self._timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)
    
    @property
    def name(self) -> str:
        """Provider name."""
        return "cohere"
    
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
    
    def _convert_messages(self, messages: list[Message], system: Optional[str] = None) -> dict[str, Any]:
        """Convert messages to Cohere format."""
        # Cohere v2 API uses OpenAI-compatible format
        chat_history = []
        
        if system:
            chat_history.append({"role": "system", "content": system})
        
        for msg in messages:
            chat_history.append(msg.to_openai_format())
        
        return chat_history
    
    def _parse_error(self, response: httpx.Response) -> ProviderError:
        """Parse error response from Cohere."""
        try:
            error_data = response.json()
            error = error_data.get("error", {})
            code = error.get("code", "")
            message = error.get("message", response.text)
            
            if response.status_code == 401:
                return AuthenticationError(
                    message,
                    provider="cohere",
                    code=code,
                )
            elif response.status_code == 404:
                return ModelNotFoundError(
                    message,
                    provider="cohere",
                    code=code,
                )
            elif response.status_code == 429:
                return RateLimitError(
                    message,
                    provider="cohere",
                    code=code,
                )
            else:
                return ProviderError(
                    message,
                    provider="cohere",
                    code=code,
                )
        except Exception:
            return ProviderError(
                f"Cohere error: {response.status_code} - {response.text}",
                provider="cohere",
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
        Stream a completion from Cohere.
        
        Uses Cohere v2 API (OpenAI-compatible).
        """
        # Build request body
        body: dict[str, Any] = {
            "model": model,
            "messages": self._convert_messages(messages, system),
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }
        
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
                    
                    # Handle Cohere's response format
                    event_type = chunk.get("type")
                    
                    if event_type == "content-delta":
                        # Text content
                        delta = chunk.get("delta", {})
                        text = delta.get("message", {}).get("content", "")
                        if text:
                            yield StreamChunk(delta=text)
                    
                    elif event_type == "tool-call-delta":
                        # Tool call
                        delta = chunk.get("delta", {})
                        tool_calls = []
                        if "message" in delta and "tool_calls" in delta["message"]:
                            for tc in delta["message"]["tool_calls"]:
                                tool_calls.append(ToolCall.from_openai(tc))
                        if tool_calls:
                            yield StreamChunk(delta="", tool_calls=tool_calls)
                    
                    elif event_type == "message-end":
                        # Completion
                        usage_data = chunk.get("usage", {})
                        usage = Usage(
                            input_tokens=usage_data.get("tokens", {}).get("input", 0),
                            output_tokens=usage_data.get("tokens", {}).get("output", 0),
                        )
                        yield StreamChunk(
                            delta="",
                            finish_reason=FinishReason.STOP,
                            usage=usage,
                        )
                        
        except httpx.ConnectError as e:
            raise ProviderError(
                "Cannot connect to Cohere API",
                provider="cohere",
                model=model,
            ) from e
        except httpx.ReadTimeout as e:
            raise ProviderError(
                f"Cohere request timed out after {self._timeout}s",
                provider="cohere",
                model=model,
            ) from e
    
    async def count_tokens(self, text: str, model: str) -> int:
        """Count tokens (approximation)."""
        return len(text) // 4
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
