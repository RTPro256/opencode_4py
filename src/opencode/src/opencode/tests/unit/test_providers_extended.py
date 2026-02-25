"""Extended tests for Provider implementations."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from opencode.provider.base import (
    Provider,
    ProviderError,
    RateLimitError,
    ModelNotFoundError,
    ModelInfo,
    ToolDefinition,
    ToolCall,
)
from opencode.provider.anthropic import AnthropicProvider
from opencode.provider.openai import OpenAIProvider


class TestAnthropicProvider:
    """Tests for AnthropicProvider."""

    def test_init(self):
        """Test provider initialization."""
        provider = AnthropicProvider(api_key="test-key")
        
        # Provider should be initialized
        assert provider is not None

    def test_models_defined(self):
        """Test that models are defined."""
        provider = AnthropicProvider(api_key="test-key")
        
        assert len(provider.MODELS) > 0
        assert any("claude" in m.id for m in provider.MODELS)

    def test_get_model_info(self):
        """Test getting model info."""
        provider = AnthropicProvider(api_key="test-key")
        
        model = provider.get_model_info("claude-3-5-sonnet-20241022")
        
        assert model is not None
        assert "claude" in model.id

    def test_get_model_info_not_found(self):
        """Test getting model info for non-existent model."""
        provider = AnthropicProvider(api_key="test-key")
        
        model = provider.get_model_info("nonexistent-model")
        
        assert model is None


class TestOpenAIProvider:
    """Tests for OpenAIProvider."""

    def test_init(self):
        """Test provider initialization."""
        provider = OpenAIProvider(api_key="test-key")
        
        # Provider should be initialized
        assert provider is not None

    def test_models_defined(self):
        """Test that models are defined."""
        provider = OpenAIProvider(api_key="test-key")
        
        assert len(provider.MODELS) > 0
        assert any("gpt" in m.id for m in provider.MODELS)

    def test_get_model_info(self):
        """Test getting model info."""
        provider = OpenAIProvider(api_key="test-key")
        
        model = provider.get_model_info("gpt-4")
        
        assert model is not None


class TestProviderErrors:
    """Tests for provider error handling."""

    def test_provider_error(self):
        """Test ProviderError."""
        error = ProviderError("Test error")
        
        assert str(error) == "Test error"

    def test_rate_limit_error(self):
        """Test RateLimitError."""
        error = RateLimitError("Rate limited")
        
        assert str(error) == "Rate limited"

    def test_model_not_found_error(self):
        """Test ModelNotFoundError."""
        error = ModelNotFoundError("Model not found")
        
        assert str(error) == "Model not found"


class TestModelInfo:
    """Tests for ModelInfo dataclass."""

    def test_model_info_creation(self):
        """Test creating ModelInfo."""
        info = ModelInfo(
            id="test-model",
            name="Test Model",
            provider="test",
            context_length=4096,
        )
        
        assert info.id == "test-model"
        assert info.name == "Test Model"
        assert info.provider == "test"
        assert info.context_length == 4096


class TestToolDefinition:
    """Tests for ToolDefinition."""

    def test_tool_definition_creation(self):
        """Test creating ToolDefinition."""
        tool = ToolDefinition(
            name="test_tool",
            description="A test tool",
            parameters={"type": "object"},
        )
        
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"


class TestToolCall:
    """Tests for ToolCall."""

    def test_tool_call_creation(self):
        """Test creating ToolCall."""
        call = ToolCall(
            id="call-123",
            name="test_tool",
            arguments={"param": "value"},
        )
        
        assert call.id == "call-123"
        assert call.name == "test_tool"
        assert call.arguments == {"param": "value"}
