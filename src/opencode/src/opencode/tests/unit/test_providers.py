"""
Tests for Provider modules.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.mark.unit
class TestProviderBase:
    """Tests for provider base module."""
    
    def test_provider_base_module_exists(self):
        """Test provider base module exists."""
        from opencode.provider import base
        assert base is not None
    
    def test_provider_base_has_model_info(self):
        """Test ModelInfo class."""
        from opencode.provider.base import ModelInfo
        info = ModelInfo(
            id="test-model",
            name="Test Model",
            provider="test",
            context_length=4096
        )
        assert info.id == "test-model"


@pytest.mark.unit
class TestProviderInit:
    """Tests for provider __init__ module."""
    
    def test_provider_init_exports(self):
        """Test provider module exports."""
        from opencode.provider import (
            Provider,
            Message,
            MessageRole,
            ModelInfo,
        )
        assert Provider is not None
        assert Message is not None
        assert MessageRole is not None
        assert ModelInfo is not None
    
    def test_message_role_values(self):
        """Test MessageRole enum values."""
        from opencode.provider import MessageRole
        assert MessageRole.USER in [MessageRole.USER, MessageRole.ASSISTANT, MessageRole.SYSTEM]
    
    def test_anthropic_provider_exists(self):
        """Test AnthropicProvider is exported."""
        from opencode.provider import AnthropicProvider
        assert AnthropicProvider is not None
    
    def test_openai_provider_exists(self):
        """Test OpenAIProvider is exported."""
        from opencode.provider import OpenAIProvider
        assert OpenAIProvider is not None
    
    def test_ollama_provider_exists(self):
        """Test OllamaProvider is exported."""
        from opencode.provider import OllamaProvider
        assert OllamaProvider is not None


@pytest.mark.unit
class TestProviderErrors:
    """Tests for provider error classes."""
    
    def test_provider_error(self):
        """Test ProviderError class."""
        from opencode.provider import ProviderError
        error = ProviderError("Test error")
        assert str(error) == "Test error"
    
    def test_authentication_error(self):
        """Test AuthenticationError class."""
        from opencode.provider import AuthenticationError
        error = AuthenticationError("Auth failed")
        assert str(error) == "Auth failed"
    
    def test_rate_limit_error(self):
        """Test RateLimitError class."""
        from opencode.provider import RateLimitError
        error = RateLimitError("Rate limited")
        assert str(error) == "Rate limited"
    
    def test_model_not_found_error(self):
        """Test ModelNotFoundError class."""
        from opencode.provider import ModelNotFoundError
        error = ModelNotFoundError("Model not found")
        assert str(error) == "Model not found"


@pytest.mark.unit
class TestMessage:
    """Tests for Message class."""
    
    def test_message_creation(self):
        """Test creating a Message."""
        from opencode.provider import Message, MessageRole
        msg = Message(
            role=MessageRole.USER,
            content="Hello"
        )
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello"
