"""
Tests for router API routes.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from datetime import datetime

from opencode.server.routes.router import (
    router,
    RouteRequest,
    UpdateConfigRequest,
    RegisterModelRequest,
    get_engine,
    get_vram_monitor,
)


@pytest.fixture
def app():
    """Create FastAPI app with router router."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_engine():
    """Create mock router engine."""
    engine = MagicMock()
    engine.get_stats = MagicMock(return_value={
        "total_requests": 100,
        "cache_hits": 50,
        "cache_misses": 50,
    })
    engine.route = AsyncMock(return_value=MagicMock(
        to_dict=lambda: {
            "model_id": "test-model",
            "provider": "test-provider",
            "confidence": 0.95,
        }
    ))
    engine.list_models = MagicMock(return_value=[])
    engine.register_model = MagicMock()
    engine.unregister_model = MagicMock(return_value=True)
    engine.profiler = MagicMock()
    engine.profiler.get_profile = MagicMock(return_value=None)
    engine.profile_models = AsyncMock(return_value={})
    engine.config = MagicMock(
        enabled=True,
        provider="anthropic",
        quality_preference="balanced",
        pinned_model=None,
        fallback_model=None,
        cache_enabled=True,
        vram_monitoring=True,
        auto_unload=True,
        profiling_enabled=True,
    )
    engine.cache = MagicMock()
    engine.cache.clear = MagicMock()
    return engine


@pytest.fixture
def mock_vram_monitor():
    """Create mock VRAM monitor."""
    monitor = MagicMock()
    monitor.available = True
    monitor.vendor = MagicMock(value="nvidia")
    monitor.get_status = AsyncMock(return_value=MagicMock(
        gpus=[],
        total_memory_mb=8192,
        total_used_mb=4096,
        total_free_mb=4096,
        overall_usage_percent=50.0,
        timestamp=datetime.now(),
    ))
    monitor.get_recommended_model_size = AsyncMock(return_value=4096)
    return monitor


class TestRouteRequestModels:
    """Tests for request models."""
    
    def test_route_request_creation(self):
        """Test RouteRequest model creation."""
        req = RouteRequest(prompt="Hello")
        assert req.prompt == "Hello"
        assert req.context is None
    
    def test_route_request_with_context(self):
        """Test RouteRequest with context."""
        req = RouteRequest(prompt="Hello", context={"key": "value"})
        assert req.context == {"key": "value"}
    
    def test_update_config_request_defaults(self):
        """Test UpdateConfigRequest defaults."""
        req = UpdateConfigRequest()
        assert req.enabled is None
        assert req.quality_preference is None
        assert req.pinned_model is None
    
    def test_update_config_request_with_fields(self):
        """Test UpdateConfigRequest with fields."""
        req = UpdateConfigRequest(
            enabled=True,
            quality_preference="quality",
            pinned_model="gpt-4",
            fallback_model="claude-3",
            cache_enabled=False,
            vram_monitoring=True,
        )
        assert req.enabled is True
        assert req.quality_preference == "quality"
        assert req.pinned_model == "gpt-4"
    
    def test_register_model_request_defaults(self):
        """Test RegisterModelRequest defaults."""
        req = RegisterModelRequest(model_id="test", provider="anthropic")
        assert req.model_id == "test"
        assert req.provider == "anthropic"
        assert req.supports_tools is False
        assert req.supports_vision is False
        assert req.vram_required_gb is None
        assert req.context_length == 4096
    
    def test_register_model_request_with_all_fields(self):
        """Test RegisterModelRequest with all fields."""
        req = RegisterModelRequest(
            model_id="test",
            provider="anthropic",
            supports_tools=True,
            supports_vision=True,
            vram_required_gb=16.0,
            context_length=8192,
        )
        assert req.supports_tools is True
        assert req.supports_vision is True
        assert req.vram_required_gb == 16.0
        assert req.context_length == 8192


class TestGetStatus:
    """Tests for get_status endpoint."""
    
    @patch('opencode.server.routes.router.get_engine')
    def test_get_status_returns_stats(self, mock_get_engine, client, mock_engine):
        """Test getting router status."""
        mock_get_engine.return_value = mock_engine
        
        response = client.get("/router/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data
        mock_engine.get_stats.assert_called_once()


class TestRoutePrompt:
    """Tests for route_prompt endpoint."""
    
    @patch('opencode.server.routes.router.get_engine')
    def test_route_prompt_returns_result(self, mock_get_engine, client, mock_engine):
        """Test routing a prompt."""
        mock_get_engine.return_value = mock_engine
        
        response = client.post(
            "/router/route",
            json={"prompt": "Write a function"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "model_id" in data
        mock_engine.route.assert_called_once()
    
    @patch('opencode.server.routes.router.get_engine')
    def test_route_prompt_with_context(self, mock_get_engine, client, mock_engine):
        """Test routing a prompt with context."""
        mock_get_engine.return_value = mock_engine
        
        response = client.post(
            "/router/route",
            json={"prompt": "Write a function", "context": {"language": "python"}},
        )
        
        assert response.status_code == 200
        call_args = mock_engine.route.call_args
        assert call_args[0][0] == "Write a function"
        assert call_args[0][1] == {"language": "python"}


class TestListModels:
    """Tests for list_models endpoint."""
    
    @patch('opencode.server.routes.router.get_engine')
    def test_list_models_empty(self, mock_get_engine, client, mock_engine):
        """Test listing models when empty."""
        mock_engine.list_models.return_value = []
        mock_get_engine.return_value = mock_engine
        
        response = client.get("/router/models")
        
        assert response.status_code == 200
        assert response.json() == []
    
    @patch('opencode.server.routes.router.get_engine')
    def test_list_models_with_models(self, mock_get_engine, client, mock_engine):
        """Test listing models."""
        mock_model = MagicMock(
            model_id="test-model",
            provider="anthropic",
            supports_tools=True,
            supports_vision=False,
            context_length=8192,
            speed_score=0.8,
            quality_score=0.9,
            is_loaded=True,
        )
        mock_engine.list_models.return_value = [mock_model]
        mock_get_engine.return_value = mock_engine
        
        response = client.get("/router/models")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["model_id"] == "test-model"
        assert data[0]["provider"] == "anthropic"


class TestRegisterModel:
    """Tests for register_model endpoint."""
    
    @patch('opencode.server.routes.router.get_engine')
    def test_register_model_success(self, mock_get_engine, client, mock_engine):
        """Test registering a model."""
        mock_get_engine.return_value = mock_engine
        
        response = client.post(
            "/router/models",
            json={
                "model_id": "new-model",
                "provider": "openai",
                "supports_tools": True,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "registered"
        assert data["model_id"] == "new-model"
        mock_engine.register_model.assert_called_once()


class TestUnregisterModel:
    """Tests for unregister_model endpoint."""
    
    @patch('opencode.server.routes.router.get_engine')
    def test_unregister_model_success(self, mock_get_engine, client, mock_engine):
        """Test unregistering a model."""
        mock_get_engine.return_value = mock_engine
        
        response = client.delete("/router/models/test-model")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unregistered"
        mock_engine.unregister_model.assert_called_once_with("test-model")
    
    @patch('opencode.server.routes.router.get_engine')
    def test_unregister_model_not_found(self, mock_get_engine, client, mock_engine):
        """Test unregistering a non-existent model."""
        mock_engine.unregister_model.return_value = False
        mock_get_engine.return_value = mock_engine
        
        response = client.delete("/router/models/nonexistent")
        
        assert response.status_code == 404


class TestGetModelProfile:
    """Tests for get_model_profile endpoint."""
    
    @patch('opencode.server.routes.router.get_engine')
    def test_get_model_profile_not_found(self, mock_get_engine, client, mock_engine):
        """Test getting profile for non-existent model."""
        mock_get_engine.return_value = mock_engine
        
        response = client.get("/router/models/nonexistent/profile")
        
        assert response.status_code == 404
    
    @patch('opencode.server.routes.router.get_engine')
    def test_get_model_profile_success(self, mock_get_engine, client, mock_engine):
        """Test getting model profile."""
        mock_profile = MagicMock(
            model_id="test-model",
            provider="anthropic",
            avg_latency_ms=100.0,
            tokens_per_second=50.0,
            coding_score=0.9,
            reasoning_score=0.8,
            creative_score=0.7,
            math_score=0.85,
            overall_quality=0.85,
            profiled_at=datetime.now(),
        )
        mock_engine.profiler.get_profile.return_value = mock_profile
        mock_get_engine.return_value = mock_engine
        
        response = client.get("/router/models/test-model/profile")
        
        assert response.status_code == 200
        data = response.json()
        assert data["model_id"] == "test-model"
        assert "avg_latency_ms" in data


class TestProfileAllModels:
    """Tests for profile_all_models endpoint."""
    
    @patch('opencode.server.routes.router.get_engine')
    def test_profile_all_models(self, mock_get_engine, client, mock_engine):
        """Test profiling all models."""
        mock_engine.profile_models.return_value = {"model1": {}, "model2": {}}
        mock_get_engine.return_value = mock_engine
        
        response = client.post("/router/profile")
        
        assert response.status_code == 200
        data = response.json()
        assert data["profiled"] == 2
        assert len(data["models"]) == 2


class TestGetConfig:
    """Tests for get_config endpoint."""
    
    @patch('opencode.server.routes.router.get_engine')
    def test_get_config(self, mock_get_engine, client, mock_engine):
        """Test getting router configuration."""
        mock_get_engine.return_value = mock_engine
        
        response = client.get("/router/config")
        
        assert response.status_code == 200
        data = response.json()
        assert "enabled" in data
        assert "provider" in data
        assert "quality_preference" in data


class TestUpdateConfig:
    """Tests for update_config endpoint."""
    
    @patch('opencode.server.routes.router.get_engine')
    def test_update_config_enabled(self, mock_get_engine, client, mock_engine):
        """Test updating enabled setting."""
        mock_get_engine.return_value = mock_engine
        
        response = client.put(
            "/router/config",
            json={"enabled": False},
        )
        
        assert response.status_code == 200
        assert mock_engine.config.enabled is False
    
    @patch('opencode.server.routes.router.get_engine')
    def test_update_config_quality_preference(self, mock_get_engine, client, mock_engine):
        """Test updating quality preference."""
        mock_get_engine.return_value = mock_engine
        
        response = client.put(
            "/router/config",
            json={"quality_preference": "quality"},
        )
        
        assert response.status_code == 200
    
    @patch('opencode.server.routes.router.get_engine')
    def test_update_config_pinned_model(self, mock_get_engine, client, mock_engine):
        """Test updating pinned model."""
        mock_get_engine.return_value = mock_engine
        
        response = client.put(
            "/router/config",
            json={"pinned_model": "gpt-4"},
        )
        
        assert response.status_code == 200
        assert mock_engine.config.pinned_model == "gpt-4"
    
    @patch('opencode.server.routes.router.get_engine')
    def test_update_config_multiple_fields(self, mock_get_engine, client, mock_engine):
        """Test updating multiple config fields."""
        mock_get_engine.return_value = mock_engine
        
        response = client.put(
            "/router/config",
            json={
                "enabled": True,
                "cache_enabled": False,
                "vram_monitoring": True,
            },
        )
        
        assert response.status_code == 200


class TestGetVRAMStatus:
    """Tests for get_vram_status endpoint."""
    
    @patch('opencode.server.routes.router.get_vram_monitor')
    def test_get_vram_status(self, mock_get_monitor, client, mock_vram_monitor):
        """Test getting VRAM status."""
        mock_get_monitor.return_value = mock_vram_monitor
        
        response = client.get("/router/vram")
        
        assert response.status_code == 200
        data = response.json()
        assert "available" in data
        assert "vendor" in data
        assert "gpus" in data
        assert "total_memory_mb" in data


class TestGetRecommendedModelSize:
    """Tests for get_recommended_model_size endpoint."""
    
    @patch('opencode.server.routes.router.get_vram_monitor')
    def test_get_recommended_model_size(self, mock_get_monitor, client, mock_vram_monitor):
        """Test getting recommended model size."""
        mock_get_monitor.return_value = mock_vram_monitor
        
        response = client.get("/router/vram/recommend")
        
        assert response.status_code == 200
        data = response.json()
        assert "recommended_size_mb" in data
        assert "recommended_size_gb" in data


class TestClearCache:
    """Tests for clear_cache endpoint."""
    
    @patch('opencode.server.routes.router.get_engine')
    def test_clear_cache(self, mock_get_engine, client, mock_engine):
        """Test clearing cache."""
        mock_get_engine.return_value = mock_engine
        
        response = client.post("/router/cache/clear")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cleared"
        mock_engine.cache.clear.assert_called_once()


class TestListCategories:
    """Tests for list_categories endpoint."""
    
    def test_list_categories(self, client):
        """Test listing prompt categories."""
        response = client.get("/router/categories")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Each category should have id and description
        for cat in data:
            assert "id" in cat
            assert "description" in cat


class TestGetEngine:
    """Tests for get_engine function."""
    
    def test_get_engine_creates_singleton(self):
        """Test that get_engine creates a singleton."""
        from opencode.server.routes.router import _engine
        
        # Reset the global
        import opencode.server.routes.router as router_module
        router_module._engine = None
        
        engine1 = get_engine()
        engine2 = get_engine()
        
        assert engine1 is engine2


class TestGetVRAMMonitor:
    """Tests for get_vram_monitor function."""
    
    def test_get_vram_monitor_creates_singleton(self):
        """Test that get_vram_monitor creates a singleton."""
        import opencode.server.routes.router as router_module
        router_module._vram_monitor = None
        
        monitor1 = get_vram_monitor()
        monitor2 = get_vram_monitor()
        
        assert monitor1 is monitor2
