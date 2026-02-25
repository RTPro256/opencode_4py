"""
Custom endpoint provider for connecting to arbitrary OpenAI-compatible APIs.

This provider allows connecting to any API that implements the OpenAI chat completions
format, enabling support for custom deployments, self-hosted models, and other
OpenAI-compatible services.
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


class CustomEndpointProvider(Provider):
    """
    Provider for custom OpenAI-compatible endpoints.
    
    This provider can connect to any API that implements the OpenAI chat completions
    format, including:
    - Self-hosted models (vLLM, TGI, etc.)
    - Custom deployments
    - Internal APIs
    - Other OpenAI-compatible services
    """
    
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        model: str = "default",
        models_list: Optional[list[str]] = None,
        **kwargs: Any,
    ):
        """
        Initialize the custom endpoint provider.
        
        Args:
            base_url: Base URL for the API (e.g., "http://localhost:8000/v1")
            api_key: Optional API key (defaults to CUSTOM_API_KEY env var)
            model: Default model ID to use
            models_list: Optional list of available model IDs
            **kwargs: Additional provider options
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.environ.get("CUSTOM_API_KEY")
        self.model_id = model
        self._models_list = models_list or [model]
        self.kwargs = kwargs
    
    @property
    def name(self) -> str:
        """Provider name."""
        return "custom-endpoint"
    
    @property
    def models(self) -> list[ModelInfo]:
        """List of supported models."""
        return [
            ModelInfo(
                id=model_id,
                name=model_id,
                provider="custom-endpoint",
                context_length=8192,  # Default, may vary
                supports_tools=True,
                supports_vision=False,
            )
            for model_id in self._models_list
        ]
    
    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers for requests."""
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
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
        
        # Convert messages to OpenAI format
        formatted_messages = [msg.to_openai_format() for msg in messages]
        
        # Add system message if provided
        if system:
            formatted_messages.insert(0, {"role": "system", "content": system})
        
        # Build request body
        body: dict[str, Any] = {
            "model": model,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        
        # Add tools if provided
        if tools:
            body["tools"] = [t.to_openai_format() for t in tools]
        
        # Add any extra parameters from kwargs
        extra_params = kwargs.get("extra_params", {})
        body.update(extra_params)
        
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
                    raise Exception(f"Custom endpoint error: {response.status_code} - {error_text.decode()}")
                
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
    
    async def list_models(self) -> list[str]:
        """List available models from the endpoint."""
        # Try to fetch models from the API
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers=self._get_headers(),
                )
                if response.status_code == 200:
                    data = response.json()
                    return [m["id"] for m in data.get("data", [])]
        except Exception:
            pass
        
        # Fall back to configured list
        return self._models_list
    
    def is_configured(self) -> bool:
        """Check if the provider is properly configured."""
        return bool(self.base_url)
