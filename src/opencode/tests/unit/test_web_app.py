"""Tests for web application."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from opencode.web.app import (
    ChatRequest,
    ChatResponse,
    SessionInfo,
    ProviderInfo,
    ToolInfo,
    create_app,
)


class TestModels:
    """Tests for data models."""

    def test_chat_request_defaults(self):
        """Test ChatRequest default values."""
        request = ChatRequest(message="Hello")
        
        assert request.message == "Hello"
        assert request.session_id is None
        assert request.provider is None
        assert request.model is None
        assert request.stream is True
        assert request.context is None

    def test_chat_request_with_values(self):
        """Test ChatRequest with all values."""
        request = ChatRequest(
            message="Hello",
            session_id="session-123",
            provider="anthropic",
            model="claude-3-opus",
            stream=False,
            context={"key": "value"},
        )
        
        assert request.message == "Hello"
        assert request.session_id == "session-123"
        assert request.provider == "anthropic"
        assert request.model == "claude-3-opus"
        assert request.stream is False
        assert request.context == {"key": "value"}

    def test_chat_response_defaults(self):
        """Test ChatResponse default values."""
        response = ChatResponse(session_id="session-1", message="Hello")
        
        assert response.session_id == "session-1"
        assert response.message == "Hello"
        assert response.role == "assistant"
        assert response.tool_calls == []
        assert response.metadata == {}

    def test_chat_response_with_values(self):
        """Test ChatResponse with all values."""
        response = ChatResponse(
            session_id="session-1",
            message="Hello",
            role="user",
            tool_calls=[{"name": "bash"}],
            metadata={"tokens": 100},
        )
        
        assert response.session_id == "session-1"
        assert response.message == "Hello"
        assert response.role == "user"
        assert response.tool_calls == [{"name": "bash"}]
        assert response.metadata == {"tokens": 100}

    def test_session_info(self):
        """Test SessionInfo model."""
        session = SessionInfo(
            id="session-1",
            name="Test Session",
            created_at=1234567890.0,
            updated_at=1234567900.0,
            message_count=5,
            provider="anthropic",
            model="claude-3-opus",
        )
        
        assert session.id == "session-1"
        assert session.name == "Test Session"
        assert session.created_at == 1234567890.0
        assert session.updated_at == 1234567900.0
        assert session.message_count == 5
        assert session.provider == "anthropic"
        assert session.model == "claude-3-opus"

    def test_session_info_defaults(self):
        """Test SessionInfo default values."""
        session = SessionInfo(
            id="session-1",
            name="Test",
            created_at=0.0,
            updated_at=0.0,
            message_count=0,
        )
        
        assert session.provider is None
        assert session.model is None

    def test_provider_info(self):
        """Test ProviderInfo model."""
        provider = ProviderInfo(
            name="anthropic",
            models=["claude-3-opus", "claude-3-sonnet"],
            configured=True,
            capabilities=["chat", "streaming"],
        )
        
        assert provider.name == "anthropic"
        assert provider.models == ["claude-3-opus", "claude-3-sonnet"]
        assert provider.configured is True
        assert provider.capabilities == ["chat", "streaming"]

    def test_tool_info(self):
        """Test ToolInfo model."""
        tool = ToolInfo(
            name="bash",
            description="Execute shell commands",
            parameters={"type": "object"},
        )
        
        assert tool.name == "bash"
        assert tool.description == "Execute shell commands"
        assert tool.parameters == {"type": "object"}


class TestCreateApp:
    """Tests for create_app function."""

    def test_create_app_returns_fastapi(self):
        """Test that create_app returns a FastAPI app."""
        app = create_app()
        
        assert app is not None
        assert app.title == "OpenCode"
        assert app.version == "1.0.0"

    def test_create_app_with_config(self):
        """Test creating app with config."""
        config = MagicMock()
        app = create_app(config)
        
        assert app is not None


class TestAppRoutes:
    """Tests for app routes."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        app = create_app()
        return TestClient(app)

    def test_root_route(self, client):
        """Test root route."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "OpenCode API"
        assert data["version"] == "1.0.0"

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "1.0.0"

    def test_create_session(self, client):
        """Test creating a session."""
        response = client.post("/api/sessions", json={"name": "Test Session"})
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["name"] == "Test Session"

    def test_create_session_default_name(self, client):
        """Test creating a session with default name."""
        response = client.post("/api/sessions", json={})
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Session"

    def test_list_sessions(self, client):
        """Test listing sessions."""
        response = client.get("/api/sessions")
        
        assert response.status_code == 200
        assert response.json() == []

    def test_get_session(self, client):
        """Test getting a session."""
        response = client.get("/api/sessions/session-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "session-123"

    def test_delete_session(self, client):
        """Test deleting a session."""
        response = client.delete("/api/sessions/session-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deleted"

    def test_chat(self, client):
        """Test chat endpoint."""
        response = client.post("/api/chat", json={"message": "Hello"})
        
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "message" in data
        assert data["role"] == "assistant"

    def test_chat_stream(self, client):
        """Test streaming chat endpoint."""
        response = client.post("/api/chat/stream", json={"message": "Hello"})
        
        assert response.status_code == 200
        # Verify it's a streaming response
        assert "text/event-stream" in response.headers.get("content-type", "")

    def test_list_providers(self, client):
        """Test listing providers."""
        response = client.get("/api/providers")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_tools(self, client):
        """Test listing tools."""
        response = client.get("/api/tools")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_execute_tool(self, client):
        """Test executing a tool."""
        response = client.post(
            "/api/tools/bash/execute",
            json={"command": "echo hello"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "result" in data

    def test_get_config(self, client):
        """Test getting configuration."""
        response = client.get("/api/config")
        
        assert response.status_code == 200
        assert response.json() == {}

    def test_update_config(self, client):
        """Test updating configuration."""
        response = client.put("/api/config", json={"key": "value"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"


class TestRunServer:
    """Tests for run_server function."""

    def test_run_server_exists(self):
        """Test run_server function exists."""
        from opencode.web.app import run_server
        
        assert callable(run_server)

    def test_run_server_function_signature(self):
        """Test run_server has correct signature."""
        from opencode.web.app import run_server
        import inspect
        
        sig = inspect.signature(run_server)
        params = list(sig.parameters.keys())
        
        assert "host" in params
        assert "port" in params
        assert "config" in params
        
        # Check defaults
        assert sig.parameters["host"].default == "0.0.0.0"
        assert sig.parameters["port"].default == 8080
