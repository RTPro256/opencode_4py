"""
Anthropic Claude provider implementation.

This module provides integration with Anthropic's Claude models through their API.
Supports streaming, tool use, and vision capabilities.
"""

from __future__ import annotations

import base64
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


class AnthropicProvider(Provider):
    """
    Provider for Anthropic Claude models.
    
    Supports:
    - Claude 3.5 Sonnet (recommended)
    - Claude 3.5 Haiku
    - Claude 3 Opus
    - Claude 3 Sonnet
    - Claude 3 Haiku
    
    Features:
    - Streaming responses
    - Tool/function calling
    - Vision (image understanding)
    - Prompt caching
    """
    
    API_URL = "https://api.anthropic.com/v1"
    
    MODELS = [
        ModelInfo(
            id="claude-3-5-sonnet-20241022",
            name="Claude 3.5 Sonnet",
            provider="anthropic",
            context_length=200000,
            supports_tools=True,
            supports_vision=True,
            supports_streaming=True,
            input_price_per_million=3.00,
            output_price_per_million=15.00,
            description="Most intelligent model, best for complex tasks",
        ),
        ModelInfo(
            id="claude-3-5-haiku-20241022",
            name="Claude 3.5 Haiku",
            provider="anthropic",
            context_length=200000,
            supports_tools=True,
            supports_vision=True,
            supports_streaming=True,
            input_price_per_million=0.80,
            output_price_per_million=4.00,
            description="Fast and efficient for everyday tasks",
        ),
        ModelInfo(
            id="claude-3-opus-20240229",
            name="Claude 3 Opus",
            provider="anthropic",
            context_length=200000,
            supports_tools=True,
            supports_vision=True,
            supports_streaming=True,
            input_price_per_million=15.00,
            output_price_per_million=75.00,
            description="Most powerful model for highly complex tasks",
        ),
        ModelInfo(
            id="claude-3-sonnet-20240229",
            name="Claude 3 Sonnet",
            provider="anthropic",
            context_length=200000,
            supports_tools=True,
            supports_vision=True,
            supports_streaming=True,
            input_price_per_million=3.00,
            output_price_per_million=15.00,
            description="Balanced performance and speed",
        ),
        ModelInfo(
            id="claude-3-haiku-20240307",
            name="Claude 3 Haiku",
            provider="anthropic",
            context_length=200000,
            supports_tools=True,
            supports_vision=True,
            supports_streaming=True,
            input_price_per_million=0.25,
            output_price_per_million=1.25,
            description="Fastest and most cost-effective",
        ),
    ]
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_headers: Optional[dict[str, str]] = None,
    ):
        """
        Initialize the Anthropic provider.
        
        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            base_url: Custom API base URL (for proxies)
            default_headers: Additional headers to include in requests
        """
        import os
        
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise AuthenticationError(
                "Anthropic API key not provided. Set ANTHROPIC_API_KEY environment variable.",
                provider="anthropic",
            )
        
        self.base_url = base_url or self.API_URL
        self.default_headers = default_headers or {}
        
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(300.0, connect=30.0),
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
                **self.default_headers,
            },
        )
    
    @property
    def name(self) -> str:
        return "anthropic"
    
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
        Stream a completion from Claude.
        
        Args:
            messages: Conversation history
            model: Model ID (e.g., "claude-3-5-sonnet-20241022")
            tools: Available tools for the model
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)
            system: System prompt
            stream: Whether to stream the response
            **kwargs: Additional options (top_p, top_k, stop_sequences, etc.)
            
        Yields:
            StreamChunk objects
        """
        # Build request body
        body: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [m.to_anthropic_format() for m in messages],
            "stream": stream,
        }
        
        if system:
            body["system"] = system
        
        if temperature is not None:
            body["temperature"] = temperature
        
        if tools:
            body["tools"] = [t.to_anthropic_format() for t in tools]
        
        # Add additional options
        for key in ["top_p", "top_k", "stop_sequences", "metadata"]:
            if key in kwargs:
                body[key] = kwargs[key]
        
        # Prompt caching
        if kwargs.get("cache_prompt"):
            # Add cache control to system and last user message
            if "system" in body:
                if isinstance(body["system"], str):
                    body["system"] = [
                        {"type": "text", "text": body["system"], "cache_control": {"type": "ephemeral"}}
                    ]
            if body["messages"]:
                last_msg = body["messages"][-1]
                if isinstance(last_msg.get("content"), list):
                    last_msg["content"][-1]["cache_control"] = {"type": "ephemeral"}
        
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
                        input_tokens=response.get("usage", {}).get("input_tokens", 0),
                        output_tokens=response.get("usage", {}).get("output_tokens", 0),
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
            f"{self.base_url}/messages",
            json=body,
        ) as response:
            response.raise_for_status()
            
            current_tool_call: dict[str, Any] = {}
            usage = Usage()
            
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                
                data = json.loads(line[6:])
                event_type = data.get("type")
                
                if event_type == "content_block_delta":
                    delta = data.get("delta", {})
                    if delta.get("type") == "text_delta":
                        yield StreamChunk.text(delta.get("text", ""))
                    elif delta.get("type") == "input_json_delta":
                        # Tool call argument streaming
                        if current_tool_call:
                            current_tool_call["arguments"] += delta.get("partial_json", "")
                
                elif event_type == "content_block_start":
                    block = data.get("content_block", {})
                    if block.get("type") == "tool_use":
                        current_tool_call = {
                            "id": block.get("id"),
                            "name": block.get("name"),
                            "arguments": "",
                        }
                
                elif event_type == "content_block_stop":
                    if current_tool_call:
                        # Parse accumulated arguments
                        try:
                            args = json.loads(current_tool_call["arguments"])
                        except json.JSONDecodeError:
                            args = {}
                        
                        yield StreamChunk.tool_call(ToolCall(
                            id=current_tool_call["id"],
                            name=current_tool_call["name"],
                            arguments=args,
                        ))
                        current_tool_call = {}
                
                elif event_type == "message_delta":
                    delta = data.get("delta", {})
                    if delta.get("stop_reason"):
                        finish_reason = {
                            "end_turn": FinishReason.STOP,
                            "max_tokens": FinishReason.LENGTH,
                            "tool_use": FinishReason.TOOL_CALL,
                            "stop_sequence": FinishReason.STOP,
                        }.get(delta["stop_reason"], FinishReason.STOP)
                        
                        usage_data = data.get("usage", {})
                        usage.output_tokens = usage_data.get("output_tokens", 0)
                        
                        yield StreamChunk.done(finish_reason, usage)
                
                elif event_type == "message_start":
                    usage_data = data.get("message", {}).get("usage", {})
                    usage.input_tokens = usage_data.get("input_tokens", 0)
                    usage.cache_read_tokens = usage_data.get("cache_read_input_tokens", 0)
                    usage.cache_write_tokens = usage_data.get("cache_creation_input_tokens", 0)
    
    async def _complete_sync(
        self,
        body: dict[str, Any],
    ) -> dict[str, Any]:
        """Non-streaming completion."""
        body["stream"] = False
        response = await self._client.post(
            f"{self.base_url}/messages",
            json=body,
        )
        response.raise_for_status()
        data = response.json()
        
        content = ""
        tool_calls = []
        
        for block in data.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")
            elif block.get("type") == "tool_use":
                tool_calls.append(ToolCall(
                    id=block["id"],
                    name=block["name"],
                    arguments=block.get("input", {}),
                ))
        
        return {
            "content": content,
            "tool_calls": tool_calls,
            "usage": data.get("usage", {}),
        }
    
    async def count_tokens(self, text: str, model: str) -> int:
        """
        Count tokens using Anthropic's token counting API.
        
        Falls back to estimation if API is unavailable.
        """
        try:
            response = await self._client.post(
                f"{self.base_url}/messages/count_tokens",
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": text}],
                },
            )
            response.raise_for_status()
            return response.json().get("input_tokens", 0)
        except Exception:
            # Fallback: estimate ~4 characters per token
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
            return AuthenticationError(message, provider="anthropic")
        elif status == 403:
            return AuthenticationError(message, provider="anthropic")
        elif status == 404:
            return ModelNotFoundError(message, provider="anthropic")
        elif status == 429:
            retry_after = error.response.headers.get("retry-after")
            return RateLimitError(
                message,
                retry_after=int(retry_after) if retry_after else None,
                provider="anthropic",
            )
        elif status == 400 and "context_length" in message.lower():
            return ContextLengthExceededError(message, provider="anthropic")
        elif "content_filter" in error_type.lower():
            return ContentFilterError(message, provider="anthropic")
        else:
            return ProviderError(message, provider="anthropic")
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
