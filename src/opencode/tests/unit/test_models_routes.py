"""
Tests for server routes models module.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from opencode.server.routes.models import (
    router,
    ModelInfo,
    ProviderInfo,
    AVAILABLE_MODELS,
)


@pytest.fixture
def app():
    """Create a FastAPI app with the models router."""
    app = FastAPI()
    app.include_router(router, prefix="/models")
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_config():
    """Create a mock config."""
    config = MagicMock()
    config.get_provider_config = MagicMock(return_value=None)
    return config


@pytest.mark.unit
class TestModelInfo:
    """Tests for ModelInfo model."""

    def test_model_info_creation(self):
        """Test ModelInfo instantiation."""
        model = ModelInfo(
            id="test-model",
            name="Test Model",
            provider="test",
            context_length=4096,
        )
        assert model.id == "test-model"
        assert model.name == "Test Model"
        assert model.provider == "test"
        assert model.context_length == 4096
        assert model.supports_vision is False
        assert model.supports_tools is True
        assert model.cost_input == 0.0
        assert model.cost_output == 0.0

    def test_model_info_with_vision(self):
        """Test ModelInfo with vision support."""
        model = ModelInfo(
            id="vision-model",
            name="Vision Model",
            provider="test",
            context_length=8192,
            supports_vision=True,
        )
        assert model.supports_vision is True

    def test_model_info_with_costs(self):
        """Test ModelInfo with costs."""
        model = ModelInfo(
            id="paid-model",
            name="Paid Model",
            provider="test",
            context_length=16384,
            cost_input=5.0,
            cost_output=15.0,
        )
        assert model.cost_input == 5.0
        assert model.cost_output == 15.0


@pytest.mark.unit
class TestProviderInfo:
    """Tests for ProviderInfo model."""

    def test_provider_info_creation(self):
        """Test ProviderInfo instantiation."""
        provider = ProviderInfo(
            id="test-provider",
            name="Test Provider",
            models=[],
        )
        assert provider.id == "test-provider"
        assert provider.name == "Test Provider"
        assert provider.models == []
        assert provider.configured is False

    def test_provider_info_with_models(self):
        """Test ProviderInfo with models."""
        model = ModelInfo(
            id="test-model",
            name="Test Model",
            provider="test",
            context_length=4096,
        )
        provider = ProviderInfo(
            id="test-provider",
            name="Test Provider",
            models=[model],
            configured=True,
        )
        assert len(provider.models) == 1
        assert provider.configured is True


@pytest.mark.unit
class TestAvailableModels:
    """Tests for AVAILABLE_MODELS data."""

    def test_anthropic_models_exist(self):
        """Test Anthropic models are defined."""
        assert "anthropic" in AVAILABLE_MODELS
        models = AVAILABLE_MODELS["anthropic"]
        assert len(models) > 0
        model_ids = [m.id for m in models]
        assert "claude-3-5-sonnet-20241022" in model_ids

    def test_openai_models_exist(self):
        """Test OpenAI models are defined."""
        assert "openai" in AVAILABLE_MODELS
        models = AVAILABLE_MODELS["openai"]
        assert len(models) > 0
        model_ids = [m.id for m in models]
        assert "gpt-4o" in model_ids

    def test_google_models_exist(self):
        """Test Google models are defined."""
        assert "google" in AVAILABLE_MODELS
        models = AVAILABLE_MODELS["google"]
        assert len(models) > 0
        model_ids = [m.id for m in models]
        assert "gemini-2.0-flash" in model_ids

    def test_model_providers_match(self):
        """Test that model provider matches the key."""
        for provider_id, models in AVAILABLE_MODELS.items():
            for model in models:
                assert model.provider == provider_id


@pytest.mark.unit
class TestListProviders:
    """Tests for list_providers endpoint."""

    def test_list_providers_success(self, client, mock_config):
        """Test listing all providers."""
        with patch("opencode.server.routes.models.get_config", return_value=mock_config):
            response = client.get("/models/")
            
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3  # anthropic, openai, google

    def test_list_providers_returns_provider_info(self, client, mock_config):
        """Test that list_providers returns ProviderInfo objects."""
        with patch("opencode.server.routes.models.get_config", return_value=mock_config):
            response = client.get("/models/")
            
        data = response.json()
        for provider in data:
            assert "id" in provider
            assert "name" in provider
            assert "models" in provider
            assert "configured" in provider

    def test_list_providers_configured_status(self, client, mock_config):
        """Test that configured status is correct."""
        # Mock a configured provider
        provider_config = MagicMock()
        provider_config.api_key = "test-key"
        mock_config.get_provider_config = MagicMock(return_value=provider_config)
        
        with patch("opencode.server.routes.models.get_config", return_value=mock_config):
            response = client.get("/models/")
            
        data = response.json()
        # All providers should be configured since we mocked api_key
        for provider in data:
            assert provider["configured"] is True

    def test_list_providers_not_configured(self, client, mock_config):
        """Test that providers show not configured when no API key."""
        mock_config.get_provider_config = MagicMock(return_value=None)
        
        with patch("opencode.server.routes.models.get_config", return_value=mock_config):
            response = client.get("/models/")
            
        data = response.json()
        for provider in data:
            assert provider["configured"] is False


@pytest.mark.unit
class TestGetProviderModels:
    """Tests for get_provider_models endpoint."""

    def test_get_provider_models_anthropic(self, client, mock_config):
        """Test getting Anthropic models."""
        with patch("opencode.server.routes.models.get_config", return_value=mock_config):
            response = client.get("/models/anthropic")
            
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "anthropic"
        assert data["name"] == "Anthropic"
        assert len(data["models"]) > 0

    def test_get_provider_models_openai(self, client, mock_config):
        """Test getting OpenAI models."""
        with patch("opencode.server.routes.models.get_config", return_value=mock_config):
            response = client.get("/models/openai")
            
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "openai"
        assert data["name"] == "Openai"

    def test_get_provider_models_google(self, client, mock_config):
        """Test getting Google models."""
        with patch("opencode.server.routes.models.get_config", return_value=mock_config):
            response = client.get("/models/google")
            
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "google"
        assert data["name"] == "Google"

    def test_get_provider_models_not_found(self, client, mock_config):
        """Test getting models for non-existent provider."""
        with patch("opencode.server.routes.models.get_config", return_value=mock_config):
            response = client.get("/models/nonexistent")
            
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert data["error"] == "Provider not found"


@pytest.mark.unit
class TestGetModelInfo:
    """Tests for get_model_info endpoint."""

    def test_get_model_info_claude(self, client, mock_config):
        """Test getting Claude model info."""
        with patch("opencode.server.routes.models.get_config", return_value=mock_config):
            response = client.get("/models/anthropic/claude-3-5-sonnet-20241022")
            
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "claude-3-5-sonnet-20241022"
        assert data["name"] == "Claude 3.5 Sonnet"
        assert data["provider"] == "anthropic"
        assert data["context_length"] == 200000
        assert data["supports_vision"] is True
        assert data["supports_tools"] is True

    def test_get_model_info_gpt4o(self, client, mock_config):
        """Test getting GPT-4o model info."""
        with patch("opencode.server.routes.models.get_config", return_value=mock_config):
            response = client.get("/models/openai/gpt-4o")
            
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "gpt-4o"
        assert data["name"] == "GPT-4o"
        assert data["provider"] == "openai"

    def test_get_model_info_gemini(self, client, mock_config):
        """Test getting Gemini model info."""
        with patch("opencode.server.routes.models.get_config", return_value=mock_config):
            response = client.get("/models/google/gemini-2.0-flash")
            
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "gemini-2.0-flash"
        assert data["name"] == "Gemini 2.0 Flash"
        assert data["provider"] == "google"

    def test_get_model_info_provider_not_found(self, client, mock_config):
        """Test getting model info for non-existent provider."""
        with patch("opencode.server.routes.models.get_config", return_value=mock_config):
            response = client.get("/models/nonexistent/some-model")
            
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert data["error"] == "Provider not found"

    def test_get_model_info_model_not_found(self, client, mock_config):
        """Test getting model info for non-existent model."""
        with patch("opencode.server.routes.models.get_config", return_value=mock_config):
            response = client.get("/models/anthropic/nonexistent-model")
            
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert data["error"] == "Model not found"
