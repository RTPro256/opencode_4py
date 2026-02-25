"""
Perplexity AI provider implementation.

This module provides integration with Perplexity AI's models,
which combine LLM capabilities with real-time web search.
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


class PerplexityProvider(Provider):
    """
    Provider for Perplexity AI API.
    
    Perplexity provides AI models with built-in web search
    capabilities, giving them access to real-time information.
    
    Features:
    - Streaming responses
    - Real-time web search integration
    - Citations in responses
    - OpenAI-compatible API
    """
    
    API_URL = "https://api.perplexity.ai/chat/completions"
    
    # Available Perplexity models
    MODELS = [
        ModelInfo(
            id="sonar-pro",
            name="Sonar Pro",
            provider="perplexity",
            context_length=200000,
            supports_tools=False,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=3.00,
            output_price_per_million=15.00,
            description="Perplexity's most capable model with deep web search",
        ),
        ModelInfo(
            id="sonar",
            name="Sonar",
            provider="perplexity",
            context_length=127000,
            supports_tools=False,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=1.00,
            output_price_per_million=1.00,
            description="Fast model with web search capabilities",
        ),
        ModelInfo(
            id="sonar-reasoning-pro",
            name="Sonar Reasoning Pro",
            provider="perplexity",
            context_length=127000,
            supports_tools=False,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=2.00,
            output_price_per_million=8.00,
            description="Advanced reasoning with web search",
        ),
        ModelInfo(
            id="sonar-reasoning",
            name="Sonar Reasoning",
            provider="perplexity",
            context_length=127000,
            supports_tools=False,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=1.00,
            output_price_per_million=5.00,
            description="Reasoning-focused model with web search",
        ),
    ]
    
    def __init__(
        self,
        api_key: str,
        timeout: float = 120.0,
    ):
        """
        Initialize Perplexity provider.
        
        Args:
            api_key: Perplexity API key
            timeout: Request timeout in seconds
        """
        self._api_key = api_key
        self._timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)
    
    @property
    def name(self) -> str:
        """Provider name."""
        return "perplexity"
    
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
        """Parse error response from Perplexity."""
        try:
            error_data = response.json()
            error = error_data.get("error", {})
            code = error.get("code", "")
            message = error.get("message", response.text)
            
            if response.status_code == 401:
                return AuthenticationError(
                    message,
                    provider="perplexity",
                    code=code,
                )
            elif response.status_code == 404:
                return ModelNotFoundError(
                    message,
                    provider="perplexity",
                    code=code,
                )
            elif response.status_code == 429:
                return RateLimitError(
                    message,
                    provider="perplexity",
                    code=code,
                )
            else:
                return ProviderError(
                    message,
                    provider="perplexity",
                    code=code,
                )
        except Exception:
            return ProviderError(
                f"Perplexity error: {response.status_code} - {response.text}",
                provider="perplexity",
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
        Stream a completion from Perplexity.
        
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
        
        # Note: Perplexity doesn't support tools, but we accept the parameter
        
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
                    
                    # Handle citations (Perplexity-specific)
                    citations = None
                    if "citations" in chunk:
                        citations = chunk["citations"]
                    
                    if text or reason:
                        metadata = {}
                        if citations:
                            metadata["citations"] = citations
                        
                        yield StreamChunk(
                            delta=text,
                            finish_reason=reason,
                            usage=usage,
                        )
                        
        except httpx.ConnectError as e:
            raise ProviderError(
                "Cannot connect to Perplexity API",
                provider="perplexity",
                model=model,
            ) from e
        except httpx.ReadTimeout as e:
            raise ProviderError(
                f"Perplexity request timed out after {self._timeout}s",
                provider="perplexity",
                model=model,
            ) from e
    
    async def count_tokens(self, text: str, model: str) -> int:
        """Count tokens (approximation)."""
        return len(text) // 4
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
