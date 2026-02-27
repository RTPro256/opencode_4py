"""
Tests for global configuration API routes.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from opencode.server.routes.global_routes import router, GlobalConfig, GlobalStats, GlobalStatus


@pytest.fixture
def app():
    """Create a FastAPI app with the global router."""
    app = FastAPI()
    app.include_router(router, prefix="/api/global")
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


class TestGlobalRoutes:
    """Tests for global routes."""
    
    @pytest.mark.unit
    def test_get_global_config(self, client):
        """Test getting global configuration."""
        response = client.get("/api/global")
        assert response.status_code == 200
        config = response.json()
        assert "version" in config
        assert "data_dir" in config
        assert "log_level" in config
        assert "default_provider" in config
        assert "default_model" in config
    
    @pytest.mark.unit
    def test_get_global_config_defaults(self, client):
        """Test global configuration defaults."""
        response = client.get("/api/global")
        config = response.json()
        
        assert config["log_level"] == "INFO"
        assert config["default_provider"] == "openai"
        assert config["default_model"] == "gpt-4"
        assert config["max_tokens"] == 4096
        assert config["temperature"] == 0.7
        assert config["enable_rag"] is True
        assert config["enable_mcp"] is True
    
    @pytest.mark.unit
    def test_update_global_config(self, client):
        """Test updating global configuration."""
        update_data = {
            "log_level": "DEBUG",
            "temperature": 0.5
        }
        response = client.patch("/api/global", json=update_data)
        assert response.status_code == 200
        config = response.json()
        assert config["log_level"] == "DEBUG"
        assert config["temperature"] == 0.5
    
    @pytest.mark.unit
    def test_update_global_config_invalid_key(self, client):
        """Test updating with invalid configuration key."""
        update_data = {
            "invalid_key": "value"
        }
        response = client.patch("/api/global", json=update_data)
        assert response.status_code == 400
    
    @pytest.mark.unit
    def test_get_global_stats(self, client):
        """Test getting global statistics."""
        response = client.get("/api/global/stats")
        assert response.status_code == 200
        stats = response.json()
        assert "total_sessions" in stats
        assert "total_messages" in stats
        assert "total_tokens_used" in stats
        assert "active_sessions" in stats
        assert "uptime_seconds" in stats
    
    @pytest.mark.unit
    def test_get_global_status(self, client):
        """Test getting global status."""
        response = client.get("/api/global/status")
        assert response.status_code == 200
        status = response.json()
        assert status["status"] == "running"
        assert "version" in status
        assert "database_connected" in status
        assert "mcp_connected" in status
        assert "providers_available" in status
    
    @pytest.mark.unit
    def test_get_global_status_providers(self, client):
        """Test that status includes available providers."""
        response = client.get("/api/global/status")
        status = response.json()
        
        providers = status["providers_available"]
        assert isinstance(providers, list)
        assert "openai" in providers
        assert "anthropic" in providers
    
    @pytest.mark.unit
    def test_reset_global_stats(self, client):
        """Test resetting global statistics."""
        response = client.post("/api/global/reset")
        assert response.status_code == 204
        
        # Verify stats are reset
        stats_response = client.get("/api/global/stats")
        stats = stats_response.json()
        assert stats["total_sessions"] == 0
        assert stats["total_messages"] == 0
        assert stats["total_tokens_used"] == 0
    
    @pytest.mark.unit
    def test_list_available_providers(self, client):
        """Test listing available providers."""
        response = client.get("/api/global/providers")
        assert response.status_code == 200
        providers = response.json()
        assert isinstance(providers, list)
        
        # Check structure of provider entries
        for provider in providers:
            assert "id" in provider
            assert "name" in provider
            assert "available" in provider
            assert "models" in provider
    
    @pytest.mark.unit
    def test_list_available_providers_contains_expected(self, client):
        """Test that provider list contains expected providers."""
        response = client.get("/api/global/providers")
        providers = response.json()
        provider_ids = [p["id"] for p in providers]
        
        assert "openai" in provider_ids
        assert "anthropic" in provider_ids
        assert "ollama" in provider_ids
        assert "azure" in provider_ids
    
    @pytest.mark.unit
    def test_global_config_model(self):
        """Test GlobalConfig model."""
        config = GlobalConfig()
        assert config.version == "1.0.0"
        assert config.log_level == "INFO"
        assert config.enable_rag is True
    
    @pytest.mark.unit
    def test_global_stats_model(self):
        """Test GlobalStats model."""
        stats = GlobalStats()
        assert stats.total_sessions == 0
        assert stats.total_messages == 0
        assert stats.uptime_seconds == 0.0
    
    @pytest.mark.unit
    def test_global_status_model(self):
        """Test GlobalStatus model."""
        status = GlobalStatus()
        assert status.status == "running"
        assert status.database_connected is True
        assert isinstance(status.providers_available, list)