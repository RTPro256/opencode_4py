"""
OpenAI provider implementation.

This module provides integration with OpenAI's GPT models through their API.
Supports streaming, function calling, and vision capabilities.
"""

from __future__ import annotations

import json
from typing import Any, AsyncIterator, Optional

import httpx

from opencode.provider.base import (
    AuthenticationError,
    ContentFilterError,
    ContextLengthExceededError,
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


class OpenAIProvider(Provider):
    """
    Provider for OpenAI models.
    
    Supports:
    - GPT-4o (recommended)
    - GPT-4o-mini
    - GPT-4 Turbo
    - GPT-4
    - GPT-3.5 Turbo
    - o1-preview
    - o1-mini
    
    Features:
    - Streaming responses
    - Function calling
    - Vision (GPT-4o, GPT-4 Turbo)
    - JSON mode
    """
    
    API_URL = "https://api.openai.com/v1"
    
    MODELS = [
        ModelInfo(
            id="gpt-4o",
            name="GPT-4o",
            provider="openai",
            context_length=128000,
            supports_tools=True,
            supports_vision=True,
            supports_streaming=True,
            input_price_per_million=2.50,
            output_price_per_million=10.00,
            description="Most capable GPT-4 model, fast and efficient",
        ),
        ModelInfo(
            id="gpt-4o-mini",
            name="GPT-4o Mini",
            provider="openai",
            context_length=128000,
            supports_tools=True,
            supports_vision=True,
            supports_streaming=True,
            input_price_per_million=0.15,
            output_price_per_million=0.60,
            description="Affordable and fast for everyday tasks",
        ),
        ModelInfo(
            id="gpt-4-turbo",
            name="GPT-4 Turbo",
            provider="openai",
            context_length=128000,
            supports_tools=True,
            supports_vision=True,
            supports_streaming=True,
            input_price_per_million=10.00,
            output_price_per_million=30.00,
            description="Previous generation flagship model",
        ),
        ModelInfo(
            id="gpt-4",
            name="GPT-4",
            provider="openai",
            context_length=8192,
            supports_tools=True,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=30.00,
            output_price_per_million=60.00,
            description="Original GPT-4 model",
        ),
        ModelInfo(
            id="gpt-3.5-turbo",
            name="GPT-3.5 Turbo",
            provider="openai",
            context_length=16385,
            supports_tools=True,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=0.50,
            output_price_per_million=1.50,
            description="Fast and affordable",
        ),
        ModelInfo(
            id="o1-preview",
            name="o1 Preview",
            provider="openai",
            context_length=128000,
            supports_tools=False,
            supports_vision=False,
            supports_streaming=False,
            input_price_per_million=15.00,
            output_price_per_million=60.00,
            description="Reasoning model for complex problems",
        ),
        ModelInfo(
            id="o1-mini",
            name="o1 Mini",
            provider="openai",
            context_length=128000,
            supports_tools=False,
            supports_vision=False,
            supports_streaming=False,
            input_price_per_million=3.00,
            output_price_per_million=12.00,
            description="Faster reasoning model",
        ),
    ]
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        organization: Optional[str] = None,
        default_headers: Optional[dict[str, str]] = None,
    ):
        """
        Initialize the OpenAI provider.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            base_url: Custom API base URL (for Azure or proxies)
            organization: OpenAI organization ID
            default_headers: Additional headers to include in requests
        """
        import os
        
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise AuthenticationError(
                "OpenAI API key not provided. Set OPENAI_API_KEY environment variable.",
                provider="openai",
            )
        
        self.base_url = base_url or self.API_URL
        self.organization = organization or os.environ.get("OPENAI_ORG_ID")
        self.default_headers = default_headers or {}
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            **self.default_headers,
        }
        
        if self.organization:
            headers["OpenAI-Organization"] = self.organization
        
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(300.0, connect=30.0),
            headers=headers,
        )
    
    @property
    def name(self) -> str:
        return "openai"
    
    @property
    def models(self) -> list[ModelInfo]:
        return self.MODELS
    
    async def complete(
        self,
        messages: list[Message],
        model: str,
        tools: Optional[list[ToolDefinition]] = None,
        *,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: Optional[str] = None,
        stream: bool = True,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """
        Stream a completion from OpenAI.
        
        Args:
            messages: Conversation history
            model: Model ID (e.g., "gpt-4o")
            tools: Available tools for the model
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-2)
            system: System prompt
            stream: Whether to stream the response
            **kwargs: Additional options (top_p, presence_penalty, etc.)
            
        Yields:
            StreamChunk objects
        """
        # Build messages list
        api_messages = []
        
        if system:
            api_messages.append({"role": "system", "content": system})
        
        for msg in messages:
            # Handle tool result messages separately
            if msg.role.value == "tool":
                for part in msg.content if isinstance(msg.content, list) else []:
                    if hasattr(part, 'type') and part.type == "tool_result":
                        api_messages.append({
                            "role": "tool",
                            "tool_call_id": part.tool_call_id,
                            "content": part.text or "",
                        })
            else:
                api_messages.append(msg.to_openai_format())
        
        # Build request body
        body: dict[str, Any] = {
            "model": model,
            "messages": api_messages,
            "max_tokens": max_tokens,
            "stream": stream,
        }
        
        if temperature is not None:
            body["temperature"] = temperature
        
        if tools:
            body["tools"] = [t.to_openai_format() for t in tools]
            body["tool_choice"] = kwargs.get("tool_choice", "auto")
        
        # Add additional options
        for key in ["top_p", "presence_penalty", "frequency_penalty", "stop", "response_format"]:
            if key in kwargs:
                body[key] = kwargs[key]
        
        try:
            if stream:
                async for chunk in self._stream_completion(body):
                    yield chunk
            else:
                response = await self._complete_sync(body)
                yield StreamChunk.text(response["content"])
                if response.get("tool_calls"):
                    for tc in response["tool_calls"]:
                        yield StreamChunk.tool_call(tc)
                yield StreamChunk.done(
                    FinishReason.TOOL_CALL if response.get("tool_calls") else FinishReason.STOP,
                    Usage(
                        input_tokens=response.get("usage", {}).get("prompt_tokens", 0),
                        output_tokens=response.get("usage", {}).get("completion_tokens", 0),
                    ),
                )
        
        except httpx.HTTPStatusError as e:
            raise self._handle_error(e)
    
    async def _stream_completion(
        self,
        body: dict[str, Any],
    ) -> AsyncIterator[StreamChunk]:
        """Stream completion from the API."""
        async with self._client.stream(
            "POST",
            f"{self.base_url}/chat/completions",
            json=body,
        ) as response:
            response.raise_for_status()
            
            tool_calls: dict[int, dict[str, Any]] = {}
            usage = Usage()
            
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                
                data = line[6:]
                if data == "[DONE]":
                    # Emit any remaining tool calls
                    for tc_data in tool_calls.values():
                        if tc_data.get("id"):
                            try:
                                args = json.loads(tc_data.get("arguments", "{}"))
                            except json.JSONDecodeError:
                                args = {}
                            yield StreamChunk.tool_call(ToolCall(
                                id=tc_data["id"],
                                name=tc_data.get("function", {}).get("name", ""),
                                arguments=args,
                            ))
                    yield StreamChunk.done(FinishReason.STOP, usage)
                    break
                
                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue
                
                delta = chunk.get("choices", [{}])[0].get("delta", {})
                
                # Text content
                if delta.get("content"):
                    yield StreamChunk.text(delta["content"])
                
                # Tool calls (streaming)
                if delta.get("tool_calls"):
                    for tc_delta in delta["tool_calls"]:
                        idx = tc_delta.get("index", 0)
                        if idx not in tool_calls:
                            tool_calls[idx] = {"id": "", "function": {"name": "", "arguments": ""}}
                        
                        if tc_delta.get("id"):
                            tool_calls[idx]["id"] = tc_delta["id"]
                        if tc_delta.get("function", {}).get("name"):
                            tool_calls[idx]["function"]["name"] = tc_delta["function"]["name"]
                        if tc_delta.get("function", {}).get("arguments"):
                            tool_calls[idx]["function"]["arguments"] += tc_delta["function"]["arguments"]
                
                # Usage (if provided)
                if chunk.get("usage"):
                    usage.input_tokens = chunk["usage"].get("prompt_tokens", 0)
                    usage.output_tokens = chunk["usage"].get("completion_tokens", 0)
                
                # Finish reason
                finish_reason = chunk.get("choices", [{}])[0].get("finish_reason")
                if finish_reason:
                    mapped_reason = {
                        "stop": FinishReason.STOP,
                        "length": FinishReason.LENGTH,
                        "tool_calls": FinishReason.TOOL_CALL,
                        "content_filter": FinishReason.CONTENT_FILTER,
                    }.get(finish_reason, FinishReason.STOP)
                    
                    # Don't emit done here, wait for [DONE]
    
    async def _complete_sync(
        self,
        body: dict[str, Any],
    ) -> dict[str, Any]:
        """Non-streaming completion."""
        body["stream"] = False
        response = await self._client.post(
            f"{self.base_url}/chat/completions",
            json=body,
        )
        response.raise_for_status()
        data = response.json()
        
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        
        tool_calls = []
        for tc in message.get("tool_calls", []):
            tool_calls.append(ToolCall.from_openai(tc))
        
        return {
            "content": message.get("content", ""),
            "tool_calls": tool_calls,
            "usage": data.get("usage", {}),
        }
    
    async def count_tokens(self, text: str, model: str) -> int:
        """
        Estimate token count.
        
        Uses tiktoken if available, otherwise falls back to estimation.
        """
        try:
            import tiktoken
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except ImportError:
            # Fallback: estimate ~4 characters per token
            return len(text) // 4
        except Exception:
            return len(text) // 4
    
    def _handle_error(self, error: httpx.HTTPStatusError) -> ProviderError:
        """Convert HTTP errors to provider errors."""
        status = error.response.status_code
        body = {}
        try:
            body = error.response.json()
        except Exception:
            pass
        
        error_type = body.get("error", {}).get("type", "")
        message = body.get("error", {}).get("message", str(error))
        
        if status == 401:
            return AuthenticationError(message, provider="openai")
        elif status == 403:
            return AuthenticationError(message, provider="openai")
        elif status == 404:
            return ModelNotFoundError(message, provider="openai")
        elif status == 429:
            return RateLimitError(message, provider="openai")
        elif status == 400 and "context_length" in message.lower():
            return ContextLengthExceededError(message, provider="openai")
        elif "content_filter" in error_type.lower():
            return ContentFilterError(message, provider="openai")
        else:
            return ProviderError(message, provider="openai")
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
