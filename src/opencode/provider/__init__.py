"""
Provider package for AI model integrations.

This package provides unified interfaces for various AI model providers.
"""

from opencode.provider.base import (
    AuthenticationError,
    ContentFilterError,
    ContextLengthExceededError,
    FinishReason,
    Message,
    MessageRole,
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
from opencode.provider.anthropic import AnthropicProvider
from opencode.provider.google import GoogleProvider
from opencode.provider.openai import OpenAIProvider

# Extended providers
from opencode.provider.azure import AzureOpenAIProvider
from opencode.provider.bedrock import BedrockProvider
from opencode.provider.cerebras import CerebrasProvider
from opencode.provider.cohere import CohereProvider
from opencode.provider.custom import CustomEndpointProvider
from opencode.provider.deepinfra import DeepInfraProvider
from opencode.provider.groq import GroqProvider
from opencode.provider.lmstudio import LMStudioProvider
from opencode.provider.mistral import MistralProvider
from opencode.provider.ollama import OllamaProvider
from opencode.provider.openrouter import OpenRouterProvider
from opencode.provider.perplexity import PerplexityProvider
from opencode.provider.together import TogetherProvider
from opencode.provider.vercel import VercelGatewayProvider
from opencode.provider.xai import XAIProvider

__all__ = [
    # Base classes and types
    "AuthenticationError",
    "ContentFilterError",
    "ContextLengthExceededError",
    "FinishReason",
    "Message",
    "MessageRole",
    "ModelInfo",
    "ModelNotFoundError",
    "Provider",
    "ProviderError",
    "RateLimitError",
    "StreamChunk",
    "ToolCall",
    "ToolDefinition",
    "Usage",
    # Provider implementations
    "AnthropicProvider",
    "AzureOpenAIProvider",
    "BedrockProvider",
    "CerebrasProvider",
    "CohereProvider",
    "CustomEndpointProvider",
    "DeepInfraProvider",
    "GoogleProvider",
    "GroqProvider",
    "LMStudioProvider",
    "MistralProvider",
    "OllamaProvider",
    "OpenAIProvider",
    "OpenRouterProvider",
    "PerplexityProvider",
    "TogetherProvider",
    "VercelGatewayProvider",
    "XAIProvider",
]
