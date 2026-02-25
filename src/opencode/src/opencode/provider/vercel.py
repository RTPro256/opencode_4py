"""
Vercel AI Gateway provider for accessing multiple AI models through Vercel's gateway.

This provider uses Vercel's AI Gateway to access models from various providers
including Anthropic, OpenAI, and more through a unified API.
"""

import json
import os
from typing import Any, AsyncIterator, Optional

from opencode.provider.base import (
    FinishReason,
    Message,
    ModelInfo,
    Provider,
    StreamChunk,
    ToolCall,
    ToolDefinition,
)


class VercelGatewayProvider(Provider):
    """
    Provider for Vercel AI Gateway.
    
    Vercel AI Gateway provides a unified API to access multiple AI providers
    including Anthropic, OpenAI, and others through a single endpoint.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.vercel.ai/v1",
        model: str = "anthropic/claude-3-sonnet",
        **kwargs: Any,
    ):
        """
        Initialize the Vercel Gateway provider.
        
        Args:
            api_key: Vercel AI Gateway API key (defaults to VERCEL_AI_KEY env var)
            base_url: Base URL for the gateway API
            model: Model ID in format "provider/model" (e.g., "anthropic/claude-3-sonnet")
            **kwargs: Additional provider options
        """
        self.api_key = api_key or os.environ.get("VERCEL_AI_KEY") or os.environ.get("VERCEL_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.model_id = model
        self.kwargs = kwargs
    
    @property
    def name(self) -> str:
        """Provider name."""
        return "vercel-gateway"
    
    @property
    def models(self) -> list[ModelInfo]:
        """List of supported models."""
        return [
            # Anthropic models
            ModelInfo(
                id="anthropic/claude-3-opus",
                name="Claude 3 Opus",
                provider="vercel-gateway",
                context_length=200000,
                supports_tools=True,
                supports_vision=True,
            ),
            ModelInfo(
                id="anthropic/claude-3-sonnet",
                name="Claude 3 Sonnet",
                provider="vercel-gateway",
                context_length=200000,
                supports_tools=True,
                supports_vision=True,
            ),
            ModelInfo(
                id="anthropic/claude-3-haiku",
                name="Claude 3 Haiku",
                provider="vercel-gateway",
                context_length=200000,
                supports_tools=True,
                supports_vision=True,
            ),
            ModelInfo(
                id="anthropic/claude-3.5-sonnet",
                name="Claude 3.5 Sonnet",
                provider="vercel-gateway",
                context_length=200000,
                supports_tools=True,
                supports_vision=True,
            ),
            # OpenAI models
            ModelInfo(
                id="openai/gpt-4o",
                name="GPT-4o",
                provider="vercel-gateway",
                context_length=128000,
                supports_tools=True,
                supports_vision=True,
            ),
            ModelInfo(
                id="openai/gpt-4o-mini",
                name="GPT-4o Mini",
                provider="vercel-gateway",
                context_length=128000,
                supports_tools=True,
                supports_vision=True,
            ),
            ModelInfo(
                id="openai/gpt-4-turbo",
                name="GPT-4 Turbo",
                provider="vercel-gateway",
                context_length=128000,
                supports_tools=True,
                supports_vision=True,
            ),
            # Other providers
            ModelInfo(
                id="meta-llama/llama-3-70b",
                name="Llama 3 70B",
                provider="vercel-gateway",
                context_length=8192,
                supports_tools=True,
                supports_vision=False,
            ),
            ModelInfo(
                id="mistral/mistral-large",
                name="Mistral Large",
                provider="vercel-gateway",
                context_length=32000,
                supports_tools=True,
                supports_vision=False,
            ),
        ]
    
    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers for requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
    
    def _parse_model(self, model_id: str) -> tuple[str, str]:
        """
        Parse model ID into provider and model name.
        
        Args:
            model_id: Model ID in format "provider/model"
            
        Returns:
            Tuple of (provider, model_name)
        """
        if "/" in model_id:
            parts = model_id.split("/", 1)
            return parts[0], parts[1]
        return "openai", model_id
    
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
        Stream a completion from the model.
        
        Args:
            messages: Conversation history
            model: Model ID to use
            tools: Available tools for the model
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            system: System prompt
            **kwargs: Additional provider-specific options
            
        Yields:
            StreamChunk objects with text deltas and tool calls
        """
        import httpx
        
        provider_name, model_name = self._parse_model(model)
        
        # Convert messages to OpenAI format
        formatted_messages = [msg.to_openai_format() for msg in messages]
        
        # Add system message if provided
        if system:
            formatted_messages.insert(0, {"role": "system", "content": system})
        
        # Build request body
        body: dict[str, Any] = {
            "model": model_name,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        
        # Add provider-specific options
        body["provider"] = provider_name
        
        # Add tools if provided
        if tools:
            body["tools"] = [t.to_openai_format() for t in tools]
        
        # Make streaming request
        url = f"{self.base_url}/chat/completions"
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                url,
                headers=self._get_headers(),
                json=body,
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise Exception(f"Vercel Gateway error: {response.status_code} - {error_text.decode()}")
                
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        
                        try:
                            chunk = json.loads(data)
                            
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            
                            # Handle content
                            if "content" in delta and delta["content"]:
                                yield StreamChunk.text(delta["content"])
                            
                            # Handle tool calls
                            if "tool_calls" in delta:
                                for tc in delta["tool_calls"]:
                                    tool_call = ToolCall(
                                        id=tc.get("id", ""),
                                        name=tc.get("function", {}).get("name", ""),
                                        arguments=json.loads(tc.get("function", {}).get("arguments", "{}")),
                                    )
                                    yield StreamChunk.tool_call(tool_call)
                            
                            # Handle finish reason
                            finish_reason = chunk.get("choices", [{}])[0].get("finish_reason")
                            if finish_reason:
                                reason_map = {
                                    "stop": FinishReason.STOP,
                                    "length": FinishReason.LENGTH,
                                    "tool_calls": FinishReason.TOOL_CALL,
                                    "content_filter": FinishReason.CONTENT_FILTER,
                                }
                                yield StreamChunk.done(
                                    reason_map.get(finish_reason, FinishReason.STOP)
                                )
                        except json.JSONDecodeError:
                            continue
