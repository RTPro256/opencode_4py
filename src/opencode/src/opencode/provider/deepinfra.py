"""
DeepInfra provider implementation.

This module provides integration with DeepInfra for cost-effective
inference of open-source models.
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


class DeepInfraProvider(Provider):
    """
    Provider for DeepInfra API.
    
    DeepInfra provides cost-effective inference for open-source models
    with competitive pricing and good performance.
    
    Features:
    - Streaming responses
    - Function calling (on supported models)
    - OpenAI-compatible API
    """
    
    API_URL = "https://api.deepinfra.com/v1/openai/chat/completions"
    
    MODELS = [
        ModelInfo(
            id="meta-llama/Llama-3.3-70B-Instruct",
            name="Llama 3.3 70B (DeepInfra)",
            provider="deepinfra",
            context_length=131072,
            supports_tools=True,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=0.23,
            output_price_per_million=0.40,
            description="Meta Llama 3.3 70B on DeepInfra",
        ),
        ModelInfo(
            id="meta-llama/Meta-Llama-3.1-405B-Instruct",
            name="Llama 3.1 405B (DeepInfra)",
            provider="deepinfra",
            context_length=32768,
            supports_tools=False,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=0.80,
            output_price_per_million=0.80,
            description="Meta Llama 3.1 405B on DeepInfra",
        ),
        ModelInfo(
            id="mistralai/Mistral-Small-24B-Instruct-2501",
            name="Mistral Small 24B (DeepInfra)",
            provider="deepinfra",
            context_length=32768,
            supports_tools=False,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=0.06,
            output_price_per_million=0.12,
            description="Mistral Small 24B on DeepInfra",
        ),
        ModelInfo(
            id="Qwen/Qwen2.5-72B-Instruct",
            name="Qwen 2.5 72B (DeepInfra)",
            provider="deepinfra",
            context_length=32768,
            supports_tools=True,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=0.35,
            output_price_per_million=0.40,
            description="Alibaba Qwen 2.5 72B on DeepInfra",
        ),
        ModelInfo(
            id="deepseek-ai/DeepSeek-V3",
            name="DeepSeek V3 (DeepInfra)",
            provider="deepinfra",
            context_length=64000,
            supports_tools=False,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=0.30,
            output_price_per_million=0.60,
            description="DeepSeek V3 on DeepInfra",
        ),
    ]
    
    def __init__(
        self,
        api_key: str,
        timeout: float = 120.0,
    ):
        self._api_key = api_key
        self._timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)
    
    @property
    def name(self) -> str:
        return "deepinfra"
    
    @property
    def models(self) -> list[ModelInfo]:
        return self.MODELS
    
    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
    
    def _parse_error(self, response: httpx.Response) -> ProviderError:
        try:
            error_data = response.json()
            error = error_data.get("error", {})
            code = error.get("code", "")
            message = error.get("message", response.text)
            
            if response.status_code == 401:
                return AuthenticationError(message, provider="deepinfra", code=code)
            elif response.status_code == 404:
                return ModelNotFoundError(message, provider="deepinfra", code=code)
            elif response.status_code == 429:
                return RateLimitError(message, provider="deepinfra", code=code)
            else:
                return ProviderError(message, provider="deepinfra", code=code)
        except Exception:
            return ProviderError(f"DeepInfra error: {response.status_code} - {response.text}", provider="deepinfra")
    
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
                        yield StreamChunk(delta=text, tool_calls=tool_calls, finish_reason=reason, usage=usage)
                        
        except httpx.ConnectError as e:
            raise ProviderError("Cannot connect to DeepInfra API", provider="deepinfra", model=model) from e
        except httpx.ReadTimeout as e:
            raise ProviderError(f"DeepInfra request timed out after {self._timeout}s", provider="deepinfra", model=model) from e
    
    async def count_tokens(self, text: str, model: str) -> int:
        return len(text) // 4
    
    async def close(self) -> None:
        await self._client.aclose()
