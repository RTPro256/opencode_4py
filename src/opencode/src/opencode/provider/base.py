"""
Base provider interface for AI model integrations.

This module defines the abstract interface that all AI providers must implement,
as well as common data structures for messages, tools, and responses.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator, Optional, Union


class MessageRole(str, Enum):
    """Message role types."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class FinishReason(str, Enum):
    """Reason for completion."""
    STOP = "stop"
    LENGTH = "length"
    TOOL_CALL = "tool_call"
    CONTENT_FILTER = "content_filter"
    ERROR = "error"


@dataclass
class ToolDefinition:
    """Definition of a tool/function that can be called by the model."""
    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema
    required: list[str] = field(default_factory=list)
    
    def to_anthropic_format(self) -> dict[str, Any]:
        """Convert to Anthropic tool format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }
    
    def to_openai_format(self) -> dict[str, Any]:
        """Convert to OpenAI tool format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
                "required": self.required,
            },
        }


@dataclass
class ToolCall:
    """A tool call from the model."""
    id: str
    name: str
    arguments: dict[str, Any]
    
    @classmethod
    def from_anthropic(cls, data: dict[str, Any]) -> "ToolCall":
        """Create from Anthropic format."""
        return cls(
            id=data["id"],
            name=data["name"],
            arguments=data.get("input", {}),
        )
    
    @classmethod
    def from_openai(cls, data: dict[str, Any]) -> "ToolCall":
        """Create from OpenAI format."""
        args = data.get("function", {}).get("arguments", "{}")
        if isinstance(args, str):
            args = json.loads(args)
        return cls(
            id=data["id"],
            name=data["function"]["name"],
            arguments=args,
        )


@dataclass
class ContentPart:
    """A part of a message's content."""
    type: str  # "text", "image", "tool_call", "tool_result"
    text: Optional[str] = None
    image_url: Optional[str] = None
    image_data: Optional[bytes] = None
    image_media_type: Optional[str] = None
    tool_call: Optional[ToolCall] = None
    tool_call_id: Optional[str] = None
    is_error: bool = False


@dataclass
class Message:
    """A message in a conversation."""
    role: MessageRole
    content: Union[str, list[ContentPart]]
    
    def get_text(self) -> str:
        """Get text content from the message."""
        if isinstance(self.content, str):
            return self.content
        texts = [p.text for p in self.content if p.text]
        return "\n".join(texts)
    
    def to_anthropic_format(self) -> dict[str, Any]:
        """Convert to Anthropic message format."""
        if isinstance(self.content, str):
            return {"role": self.role.value, "content": self.content}
        
        content = []
        for part in self.content:
            if part.type == "text" and part.text:
                content.append({"type": "text", "text": part.text})
            elif part.type == "image":
                if part.image_data:
                    content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": part.image_media_type or "image/png",
                            "data": part.image_data,
                        },
                    })
                elif part.image_url:
                    content.append({
                        "type": "image",
                        "source": {"type": "url", "url": part.image_url},
                    })
            elif part.type == "tool_call" and part.tool_call:
                content.append({
                    "type": "tool_use",
                    "id": part.tool_call.id,
                    "name": part.tool_call.name,
                    "input": part.tool_call.arguments,
                })
            elif part.type == "tool_result":
                content.append({
                    "type": "tool_result",
                    "tool_use_id": part.tool_call_id,
                    "content": part.text,
                    "is_error": part.is_error,
                })
        
        return {"role": self.role.value, "content": content}
    
    def to_openai_format(self) -> dict[str, Any]:
        """Convert to OpenAI message format."""
        if isinstance(self.content, str):
            return {"role": self.role.value, "content": self.content}
        
        content = []
        tool_calls = []
        
        for part in self.content:
            if part.type == "text" and part.text:
                content.append({"type": "text", "text": part.text})
            elif part.type == "image":
                if part.image_url:
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": part.image_url},
                    })
                elif part.image_data:
                    # Convert to data URL
                    import base64
                    b64 = base64.b64encode(part.image_data).decode()
                    content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{part.image_media_type or 'image/png'};base64,{b64}"
                        },
                    })
            elif part.type == "tool_call" and part.tool_call:
                tool_calls.append({
                    "id": part.tool_call.id,
                    "type": "function",
                    "function": {
                        "name": part.tool_call.name,
                        "arguments": json.dumps(part.tool_call.arguments),
                    },
                })
            elif part.type == "tool_result":
                # Tool results are separate messages in OpenAI
                pass
        
        msg: dict[str, Any] = {"role": self.role.value}
        
        if content:
            if len(content) == 1 and content[0]["type"] == "text":
                msg["content"] = content[0]["text"]
            else:
                msg["content"] = content
        
        if tool_calls:
            msg["tool_calls"] = tool_calls
        
        return msg


@dataclass
class Usage:
    """Token usage statistics."""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    
    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class StreamChunk:
    """A chunk of streaming response."""
    delta: str  # Text delta
    tool_calls: list[ToolCall] = field(default_factory=list)
    finish_reason: Optional[FinishReason] = None
    usage: Optional[Usage] = None
    
    @classmethod
    def text(cls, delta: str) -> "StreamChunk":
        """Create a text chunk."""
        return cls(delta=delta)
    
    @classmethod
    def tool_call(cls, tool_call: ToolCall) -> "StreamChunk":
        """Create a tool call chunk."""
        return cls(delta="", tool_calls=[tool_call])
    
    @classmethod
    def done(cls, finish_reason: FinishReason, usage: Optional[Usage] = None) -> "StreamChunk":
        """Create a completion chunk."""
        return cls(delta="", finish_reason=finish_reason, usage=usage)


@dataclass
class CompletionResponse:
    """A complete response from the model."""
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    finish_reason: FinishReason = FinishReason.STOP
    usage: Optional[Usage] = None
    model: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelInfo:
    """Information about a model."""
    id: str
    name: str
    provider: str
    context_length: int
    supports_tools: bool = True
    supports_vision: bool = False
    supports_streaming: bool = True
    input_price_per_million: float = 0.0
    output_price_per_million: float = 0.0
    description: Optional[str] = None


class Provider(ABC):
    """
    Abstract base class for AI providers.
    
    All providers must implement the complete() method for streaming
    completions. The complete_sync() method provides a non-streaming
    convenience wrapper.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass
    
    @property
    @abstractmethod
    def models(self) -> list[ModelInfo]:
        """Available models from this provider."""
        pass
    
    @abstractmethod
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
        pass
    
    async def complete_sync(
        self,
        messages: list[Message],
        model: str,
        tools: Optional[list[ToolDefinition]] = None,
        **kwargs: Any,
    ) -> CompletionResponse:
        """
        Non-streaming completion convenience method.
        
        Collects all chunks and returns a complete response.
        """
        content_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        finish_reason = FinishReason.STOP
        usage: Optional[Usage] = None
        
        async for chunk in self.complete(messages, model, tools, **kwargs):
            if chunk.delta:
                content_parts.append(chunk.delta)
            if chunk.tool_calls:
                tool_calls.extend(chunk.tool_calls)
            if chunk.finish_reason:
                finish_reason = chunk.finish_reason
            if chunk.usage:
                usage = chunk.usage
        
        return CompletionResponse(
            content="".join(content_parts),
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            usage=usage,
            model=model,
        )
    
    @abstractmethod
    async def count_tokens(self, text: str, model: str) -> int:
        """
        Count tokens for the given text.
        
        Args:
            text: Text to count tokens for
            model: Model to use for tokenization
            
        Returns:
            Number of tokens
        """
        pass
    
    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Get information about a specific model."""
        for model in self.models:
            if model.id == model_id:
                return model
        return None
    
    def supports_model(self, model_id: str) -> bool:
        """Check if this provider supports the given model."""
        return any(m.id == model_id for m in self.models)


class ProviderError(Exception):
    """Base error for provider operations."""
    
    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        code: Optional[str] = None,
    ):
        super().__init__(message)
        self.provider = provider
        self.model = model
        self.code = code


class AuthenticationError(ProviderError):
    """Authentication failed."""
    pass


class RateLimitError(ProviderError):
    """Rate limit exceeded."""
    
    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        **kwargs: Any,
    ):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class ModelNotFoundError(ProviderError):
    """Model not found."""
    pass


class ContextLengthExceededError(ProviderError):
    """Context length exceeded."""
    pass


class ContentFilterError(ProviderError):
    """Content was filtered by safety systems."""
    pass
