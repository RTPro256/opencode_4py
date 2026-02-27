"""
OpenCode Multi-AI Provider System

A unified interface for connecting to multiple AI providers:
- OpenAI (GPT models)
- Google AI (Gemini models)
- Anthropic (Claude models)
- Ollama (local models)
- Groq (fast inference)
- HuggingFace (community models)
- OpenRouter (gateway to many models)
- GitHub Models (Azure-hosted models)

Usage:
    from opencode.core.providers import MultiAIClient, OpenAIProvider, GoogleAIProvider

    client = MultiAIClient()
    client.add("openai", OpenAIProvider(api_key="sk-..."))
    client.add("gemini", GoogleAIProvider(api_key="..."))

    response = client.chat("openai", "Hello!")
"""

from .base import BaseProvider
from .client import MultiAIClient
from .usage_tracker import UsageTracker

# Provider implementations
from .openai_provider import OpenAIProvider
from .google_provider import GoogleAIProvider
from .anthropic_provider import AnthropicProvider
from .ollama_provider import OllamaProvider
from .groq_provider import GroqProvider
from .huggingface_provider import HuggingFaceProvider
from .openrouter_provider import OpenRouterProvider
from .github_provider import GitHubModelsProvider

__all__ = [
    # Base classes
    "BaseProvider",
    "MultiAIClient",
    "UsageTracker",
    # Providers
    "OpenAIProvider",
    "GoogleAIProvider",
    "AnthropicProvider",
    "OllamaProvider",
    "GroqProvider",
    "HuggingFaceProvider",
    "OpenRouterProvider",
    "GitHubModelsProvider",
]
