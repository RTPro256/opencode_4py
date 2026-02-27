"""
Tests for Provider implementations.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio


@pytest.mark.unit
class TestAnthropicProvider:
    """Tests for Anthropic provider."""
    
    def test_anthropic_provider_exists(self):
        """Test Anthropic provider exists."""
        from opencode.provider.anthropic import AnthropicProvider
        assert AnthropicProvider is not None
    
    def test_anthropic_provider_inherits_base(self):
        """Test Anthropic provider inherits from base."""
        from opencode.provider.anthropic import AnthropicProvider
        from opencode.provider.base import Provider
        
        assert issubclass(AnthropicProvider, Provider)
    
    def test_anthropic_provider_name(self):
        """Test Anthropic provider name."""
        from opencode.provider.anthropic import AnthropicProvider
        
        provider = AnthropicProvider(api_key="test-key")
        assert provider.name == "anthropic"


@pytest.mark.unit
class TestOpenAIProvider:
    """Tests for OpenAI provider."""
    
    def test_openai_provider_exists(self):
        """Test OpenAI provider exists."""
        from opencode.provider.openai import OpenAIProvider
        assert OpenAIProvider is not None
    
    def test_openai_provider_inherits_base(self):
        """Test OpenAI provider inherits from base."""
        from opencode.provider.openai import OpenAIProvider
        from opencode.provider.base import Provider
        
        assert issubclass(OpenAIProvider, Provider)
    
    def test_openai_provider_name(self):
        """Test OpenAI provider name."""
        from opencode.provider.openai import OpenAIProvider
        
        provider = OpenAIProvider(api_key="test-key")
        assert provider.name == "openai"


@pytest.mark.unit
class TestGroqProvider:
    """Tests for Groq provider."""
    
    def test_groq_provider_exists(self):
        """Test Groq provider exists."""
        from opencode.provider.groq import GroqProvider
        assert GroqProvider is not None
    
    def test_groq_provider_inherits_base(self):
        """Test Groq provider inherits from base."""
        from opencode.provider.groq import GroqProvider
        from opencode.provider.base import Provider
        
        assert issubclass(GroqProvider, Provider)
    
    def test_groq_provider_name(self):
        """Test Groq provider name."""
        from opencode.provider.groq import GroqProvider
        
        provider = GroqProvider(api_key="test-key")
        assert provider.name == "groq"


@pytest.mark.unit
class TestCohereProvider:
    """Tests for Cohere provider."""
    
    def test_cohere_provider_exists(self):
        """Test Cohere provider exists."""
        from opencode.provider.cohere import CohereProvider
        assert CohereProvider is not None
    
    def test_cohere_provider_inherits_base(self):
        """Test Cohere provider inherits from base."""
        from opencode.provider.cohere import CohereProvider
        from opencode.provider.base import Provider
        
        assert issubclass(CohereProvider, Provider)
    
    def test_cohere_provider_name(self):
        """Test Cohere provider name."""
        from opencode.provider.cohere import CohereProvider
        
        provider = CohereProvider(api_key="test-key")
        assert provider.name == "cohere"


@pytest.mark.unit
class TestMistralProvider:
    """Tests for Mistral provider."""
    
    def test_mistral_provider_exists(self):
        """Test Mistral provider exists."""
        from opencode.provider.mistral import MistralProvider
        assert MistralProvider is not None
    
    def test_mistral_provider_inherits_base(self):
        """Test Mistral provider inherits from base."""
        from opencode.provider.mistral import MistralProvider
        from opencode.provider.base import Provider
        
        assert issubclass(MistralProvider, Provider)
    
    def test_mistral_provider_name(self):
        """Test Mistral provider name."""
        from opencode.provider.mistral import MistralProvider
        
        provider = MistralProvider(api_key="test-key")
        assert provider.name == "mistral"


@pytest.mark.unit
class TestGoogleProvider:
    """Tests for Google provider."""
    
    def test_google_provider_exists(self):
        """Test Google provider exists."""
        from opencode.provider.google import GoogleProvider
        assert GoogleProvider is not None
    
    def test_google_provider_inherits_base(self):
        """Test Google provider inherits from base."""
        from opencode.provider.google import GoogleProvider
        from opencode.provider.base import Provider
        
        assert issubclass(GoogleProvider, Provider)


@pytest.mark.unit
class TestAzureProvider:
    """Tests for Azure provider."""
    
    def test_azure_provider_module_exists(self):
        """Test Azure provider module exists."""
        from opencode.provider import azure
        assert azure is not None
    
    def test_azure_provider_inherits_base(self):
        """Test Azure provider inherits from base."""
        from opencode.provider.azure import AzureOpenAIProvider
        from opencode.provider.base import Provider
        
        assert issubclass(AzureOpenAIProvider, Provider)


@pytest.mark.unit
class TestBedrockProvider:
    """Tests for Bedrock provider."""
    
    def test_bedrock_provider_exists(self):
        """Test Bedrock provider exists."""
        from opencode.provider.bedrock import BedrockProvider
        assert BedrockProvider is not None
    
    def test_bedrock_provider_inherits_base(self):
        """Test Bedrock provider inherits from base."""
        from opencode.provider.bedrock import BedrockProvider
        from opencode.provider.base import Provider
        
        assert issubclass(BedrockProvider, Provider)


@pytest.mark.unit
class TestOpenRouterProvider:
    """Tests for OpenRouter provider."""
    
    def test_openrouter_provider_exists(self):
        """Test OpenRouter provider exists."""
        from opencode.provider.openrouter import OpenRouterProvider
        assert OpenRouterProvider is not None
    
    def test_openrouter_provider_inherits_base(self):
        """Test OpenRouter provider inherits from base."""
        from opencode.provider.openrouter import OpenRouterProvider
        from opencode.provider.base import Provider
        
        assert issubclass(OpenRouterProvider, Provider)
    
    def test_openrouter_provider_name(self):
        """Test OpenRouter provider name."""
        from opencode.provider.openrouter import OpenRouterProvider
        
        provider = OpenRouterProvider(api_key="test-key")
        assert provider.name == "openrouter"


@pytest.mark.unit
class TestTogetherProvider:
    """Tests for Together provider."""
    
    def test_together_provider_exists(self):
        """Test Together provider exists."""
        from opencode.provider.together import TogetherProvider
        assert TogetherProvider is not None
    
    def test_together_provider_inherits_base(self):
        """Test Together provider inherits from base."""
        from opencode.provider.together import TogetherProvider
        from opencode.provider.base import Provider
        
        assert issubclass(TogetherProvider, Provider)


@pytest.mark.unit
class TestPerplexityProvider:
    """Tests for Perplexity provider."""
    
    def test_perplexity_provider_exists(self):
        """Test Perplexity provider exists."""
        from opencode.provider.perplexity import PerplexityProvider
        assert PerplexityProvider is not None
    
    def test_perplexity_provider_inherits_base(self):
        """Test Perplexity provider inherits from base."""
        from opencode.provider.perplexity import PerplexityProvider
        from opencode.provider.base import Provider
        
        assert issubclass(PerplexityProvider, Provider)


@pytest.mark.unit
class TestXAIProvider:
    """Tests for XAI provider."""
    
    def test_xai_provider_exists(self):
        """Test XAI provider exists."""
        from opencode.provider.xai import XAIProvider
        assert XAIProvider is not None
    
    def test_xai_provider_inherits_base(self):
        """Test XAI provider inherits from base."""
        from opencode.provider.xai import XAIProvider
        from opencode.provider.base import Provider
        
        assert issubclass(XAIProvider, Provider)


@pytest.mark.unit
class TestCerebrasProvider:
    """Tests for Cerebras provider."""
    
    def test_cerebras_provider_exists(self):
        """Test Cerebras provider exists."""
        from opencode.provider.cerebras import CerebrasProvider
        assert CerebrasProvider is not None
    
    def test_cerebras_provider_inherits_base(self):
        """Test Cerebras provider inherits from base."""
        from opencode.provider.cerebras import CerebrasProvider
        from opencode.provider.base import Provider
        
        assert issubclass(CerebrasProvider, Provider)


@pytest.mark.unit
class TestDeepInfraProvider:
    """Tests for DeepInfra provider."""
    
    def test_deepinfra_provider_exists(self):
        """Test DeepInfra provider exists."""
        from opencode.provider.deepinfra import DeepInfraProvider
        assert DeepInfraProvider is not None
    
    def test_deepinfra_provider_inherits_base(self):
        """Test DeepInfra provider inherits from base."""
        from opencode.provider.deepinfra import DeepInfraProvider
        from opencode.provider.base import Provider
        
        assert issubclass(DeepInfraProvider, Provider)


@pytest.mark.unit
class TestLMStudioProvider:
    """Tests for LMStudio provider."""
    
    def test_lmstudio_provider_exists(self):
        """Test LMStudio provider exists."""
        from opencode.provider.lmstudio import LMStudioProvider
        assert LMStudioProvider is not None
    
    def test_lmstudio_provider_inherits_base(self):
        """Test LMStudio provider inherits from base."""
        from opencode.provider.lmstudio import LMStudioProvider
        from opencode.provider.base import Provider
        
        assert issubclass(LMStudioProvider, Provider)


@pytest.mark.unit
class TestVercelProvider:
    """Tests for Vercel provider."""
    
    def test_vercel_provider_module_exists(self):
        """Test Vercel provider module exists."""
        from opencode.provider import vercel
        assert vercel is not None


@pytest.mark.unit
class TestCustomProvider:
    """Tests for Custom provider."""
    
    def test_custom_provider_module_exists(self):
        """Test Custom provider module exists."""
        from opencode.provider import custom
        assert custom is not None


@pytest.mark.unit
class TestProviderBase:
    """Tests for Provider base class."""
    
    def test_provider_is_abstract(self):
        """Test Provider is abstract class."""
        from opencode.provider.base import Provider
        from abc import ABC
        
        assert issubclass(Provider, ABC)
    
    def test_provider_error_exists(self):
        """Test ProviderError exists."""
        from opencode.provider.base import ProviderError
        assert ProviderError is not None
    
    def test_authentication_error_exists(self):
        """Test AuthenticationError exists."""
        from opencode.provider.base import AuthenticationError
        assert AuthenticationError is not None
    
    def test_rate_limit_error_exists(self):
        """Test RateLimitError exists."""
        from opencode.provider.base import RateLimitError
        assert RateLimitError is not None
    
    def test_model_not_found_error_exists(self):
        """Test ModelNotFoundError exists."""
        from opencode.provider.base import ModelNotFoundError
        assert ModelNotFoundError is not None
    
    def test_message_role_enum(self):
        """Test MessageRole enum."""
        from opencode.provider.base import MessageRole
        
        assert MessageRole.SYSTEM.value == "system"
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
        assert MessageRole.TOOL.value == "tool"
    
    def test_finish_reason_enum(self):
        """Test FinishReason enum."""
        from opencode.provider.base import FinishReason
        
        assert FinishReason.STOP.value == "stop"
        assert FinishReason.LENGTH.value == "length"
        assert FinishReason.TOOL_CALL.value == "tool_call"
