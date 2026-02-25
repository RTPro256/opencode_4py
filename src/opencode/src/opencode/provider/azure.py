"""
Azure OpenAI provider implementation.

This module provides integration with Azure OpenAI Service.
Supports streaming, function calling, and vision capabilities
through Azure's OpenAI-compatible API.
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


class AzureOpenAIProvider(Provider):
    """
    Provider for Azure OpenAI Service.
    
    Azure OpenAI provides access to OpenAI models through Azure's infrastructure
    with enterprise features like private networking, RBAC, and compliance.
    
    Required configuration:
    - API key (from Azure portal)
    - Endpoint (your Azure OpenAI resource endpoint)
    - Deployment name (the name you gave your model deployment)
    
    Features:
    - Streaming responses
    - Function calling
    - Vision (on supported deployments)
    - Azure AD authentication support
    - Private endpoints
    """
    
    # Common Azure OpenAI deployments
    COMMON_DEPLOYMENTS = [
        ModelInfo(
            id="gpt-4o",
            name="GPT-4o (Azure)",
            provider="azure",
            context_length=128000,
            supports_tools=True,
            supports_vision=True,
            supports_streaming=True,
            input_price_per_million=5.00,  # Azure pricing may vary
            output_price_per_million=15.00,
            description="GPT-4o on Azure",
        ),
        ModelInfo(
            id="gpt-4o-mini",
            name="GPT-4o Mini (Azure)",
            provider="azure",
            context_length=128000,
            supports_tools=True,
            supports_vision=True,
            supports_streaming=True,
            input_price_per_million=0.15,
            output_price_per_million=0.60,
            description="GPT-4o Mini on Azure",
        ),
        ModelInfo(
            id="gpt-4-turbo",
            name="GPT-4 Turbo (Azure)",
            provider="azure",
            context_length=128000,
            supports_tools=True,
            supports_vision=True,
            supports_streaming=True,
            input_price_per_million=10.00,
            output_price_per_million=30.00,
            description="GPT-4 Turbo on Azure",
        ),
        ModelInfo(
            id="gpt-4",
            name="GPT-4 (Azure)",
            provider="azure",
            context_length=8192,
            supports_tools=True,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=30.00,
            output_price_per_million=60.00,
            description="GPT-4 on Azure",
        ),
        ModelInfo(
            id="gpt-35-turbo",
            name="GPT-3.5 Turbo (Azure)",
            provider="azure",
            context_length=16384,
            supports_tools=True,
            supports_vision=False,
            supports_streaming=True,
            input_price_per_million=0.50,
            output_price_per_million=1.50,
            description="GPT-3.5 Turbo on Azure",
        ),
    ]
    
    def __init__(
        self,
        api_key: str,
        endpoint: str,
        api_version: str = "2024-02-15-preview",
        deployment: Optional[str] = None,
        timeout: float = 120.0,
    ):
        """
        Initialize Azure OpenAI provider.
        
        Args:
            api_key: Azure OpenAI API key
            endpoint: Azure OpenAI endpoint (e.g., https://your-resource.openai.azure.com)
            api_version: Azure API version
            deployment: Default deployment name to use
            timeout: Request timeout in seconds
        """
        self._api_key = api_key
        self._endpoint = endpoint.rstrip("/")
        self._api_version = api_version
        self._default_deployment = deployment
        self._timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)
    
    @property
    def name(self) -> str:
        """Provider name."""
        return "azure"
    
    @property
    def models(self) -> list[ModelInfo]:
        """Available models from this provider."""
        return self.COMMON_DEPLOYMENTS
    
    def _get_chat_url(self, deployment: str) -> str:
        """Get the chat completions URL for a deployment."""
        return (
            f"{self._endpoint}/openai/deployments/{deployment}"
            f"/chat/completions?api-version={self._api_version}"
        )
    
    def _parse_error(self, response: httpx.Response) -> ProviderError:
        """Parse error response from Azure."""
        try:
            error_data = response.json()
            error = error_data.get("error", {})
            code = error.get("code", "")
            message = error.get("message", response.text)
            
            if response.status_code == 401:
                return AuthenticationError(
                    message,
                    provider="azure",
                    code=code,
                )
            elif response.status_code == 404:
                return ModelNotFoundError(
                    message,
                    provider="azure",
                    code=code,
                )
            elif response.status_code == 429:
                retry_after = response.headers.get("retry-after")
                return RateLimitError(
                    message,
                    retry_after=int(retry_after) if retry_after else None,
                    provider="azure",
                    code=code,
                )
            elif "context_length" in message.lower() or code == "context_length_exceeded":
                return ContextLengthExceededError(
                    message,
                    provider="azure",
                    code=code,
                )
            elif "content_filter" in code.lower():
                return ContentFilterError(
                    message,
                    provider="azure",
                    code=code,
                )
            else:
                return ProviderError(
                    message,
                    provider="azure",
                    code=code,
                )
        except Exception:
            return ProviderError(
                f"Azure error: {response.status_code} - {response.text}",
                provider="azure",
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
        Stream a completion from Azure OpenAI.
        
        The 'model' parameter should be the deployment name.
        """
        # Use deployment from model parameter or default
        deployment = model or self._default_deployment
        if not deployment:
            raise ProviderError(
                "No deployment specified. Set 'deployment' parameter or pass model name.",
                provider="azure",
            )
        
        # Build request body
        body: dict[str, Any] = {
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
        
        # Make streaming request
        url = self._get_chat_url(deployment)
        headers = {
            "api-key": self._api_key,
            "Content-Type": "application/json",
        }
        
        try:
            async with self._client.stream(
                "POST",
                url,
                json=body,
                headers=headers,
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
                f"Cannot connect to Azure OpenAI at {self._endpoint}",
                provider="azure",
                model=deployment,
            ) from e
        except httpx.ReadTimeout as e:
            raise ProviderError(
                f"Azure OpenAI request timed out after {self._timeout}s",
                provider="azure",
                model=deployment,
            ) from e
    
    async def count_tokens(self, text: str, model: str) -> int:
        """
        Count tokens for the given text.
        
        Uses the same tokenization as OpenAI models (tiktoken).
        Approximation: ~4 characters per token.
        """
        return len(text) // 4
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
