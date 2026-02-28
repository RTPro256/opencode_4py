"""
LM Studio provider implementation.

This module provides integration with LM Studio for running local models
through an OpenAI-compatible API.
"""

from __future__ import annotations

import json
from typing import Any, AsyncIterator, Optional

import httpx

from opencode.core.defaults import LLM_TIMEOUT, LMSTUDIO_BASE_URL

from opencode.provider.base import (
    FinishReason,
    Message,
    ModelInfo,
    Provider,
    ProviderError,
    StreamChunk,
    ToolCall,
    ToolDefinition,
    Usage,
)


class LMStudioProvider(Provider):
    """
    Provider for LM Studio local models.
    
    LM Studio runs models locally and provides an OpenAI-compatible API.
    Default endpoint is http://localhost:1234
    
    Features:
    - Streaming responses
    - Function calling (on supported models)
    - Vision (on supported models)
    - No API key required (local)
    """
    
    DEFAULT_URL = LMSTUDIO_BASE_URL
    
    MODELS = [
        ModelInfo(
            id="local-model",
            name="Local Model (LM Studio)",
            provider="lmstudio",
            context_length=8192,  # Varies by loaded model
            supports_tools=True,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=0.0,
            output_price_per_million=0.0,
            description="Currently loaded model in LM Studio",
        ),
    ]
    
    def __init__(
        self,
        base_url: str = DEFAULT_URL,
        timeout: float = LLM_TIMEOUT,
    ):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)
    
    @property
    def name(self) -> str:
        return "lmstudio"
    
    @property
    def models(self) -> list[ModelInfo]:
        return self.MODELS
    
    async def get_available_models(self) -> list[str]:
        """Get list of loaded models from LM Studio."""
        try:
            response = await self._client.get(f"{self._base_url}/v1/models")
            response.raise_for_status()
            data = response.json()
            return [model["id"] for model in data.get("data", [])]
        except Exception:
            return []
    
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
        
        url = f"{self._base_url}/v1/chat/completions"
        
        try:
            async with self._client.stream(
                "POST",
                url,
                json=body,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise ProviderError(
                        f"LM Studio error: {response.status_code} - {error_text.decode()}",
                        provider="lmstudio",
                        model=model,
                    )
                
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
                        yield StreamChunk(delta=text, tool_calls=tool_calls, finish_reason=reason, usage=usage)
                        
        except httpx.ConnectError as e:
            raise ProviderError(
                f"Cannot connect to LM Studio at {self._base_url}. Is LM Studio running?",
                provider="lmstudio",
                model=model,
            ) from e
        except httpx.ReadTimeout as e:
            raise ProviderError(f"LM Studio request timed out after {self._timeout}s", provider="lmstudio", model=model) from e
    
    async def count_tokens(self, text: str, model: str) -> int:
        return len(text) // 4
    
    async def is_running(self) -> bool:
        """Check if LM Studio server is running."""
        try:
            response = await self._client.get(f"{self._base_url}/v1/models")
            return response.status_code == 200
        except Exception:
            return False
    
    async def close(self) -> None:
        await self._client.aclose()
