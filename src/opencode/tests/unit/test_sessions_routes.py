"""
Tests for server routes sessions module.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime
from fastapi import FastAPI
from fastapi.testclient import TestClient

from opencode.server.routes.sessions import (
    router,
    SessionCreate,
    SessionUpdate,
    SessionResponse,
)


@pytest.fixture
def app():
    """Create a FastAPI app with the sessions router."""
    app = FastAPI()
    app.include_router(router, prefix="/sessions")
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_session():
    """Create a mock session."""
    session = MagicMock()
    session.id = "session-123"
    session.project_path = "/test/project"
    session.provider = "anthropic"
    session.model = "claude-3-5-sonnet-20241022"
    session.title = "Test Session"
    session.created_at = datetime(2026, 2, 24, 12, 0, 0)
    session.updated_at = datetime(2026, 2, 24, 12, 30, 0)
    return session


@pytest.fixture
def mock_session_manager(mock_session):
    """Create a mock session manager."""
    manager = MagicMock()
    manager.create_session = AsyncMock(return_value=mock_session)
    manager.list_sessions = AsyncMock(return_value=[mock_session])
    manager.get_session = AsyncMock(return_value=mock_session)
    manager.update_session = AsyncMock(return_value=mock_session)
    manager.delete_session = AsyncMock(return_value=True)
    manager.export_session = AsyncMock(return_value={"id": "session-123"})
    manager.import_session = AsyncMock(return_value=mock_session)
    return manager


@pytest.mark.unit
class TestSessionModels:
    """Tests for Pydantic models."""

    def test_session_create_defaults(self):
        """Test SessionCreate with default values."""
        request = SessionCreate(project_path="/test")
        assert request.project_path == "/test"
        assert request.provider == "anthropic"
        assert request.model == "claude-3-5-sonnet-20241022"
        assert request.title is None

    def test_session_create_custom(self):
        """Test SessionCreate with custom values."""
        request = SessionCreate(
            project_path="/custom",
            provider="openai",
            model="gpt-4o",
            title="Custom Session",
        )
        assert request.project_path == "/custom"
        assert request.provider == "openai"
        assert request.model == "gpt-4o"
        assert request.title == "Custom Session"

    def test_session_update_empty(self):
        """Test SessionUpdate with no values."""
        request = SessionUpdate()
        assert request.title is None
        assert request.model is None

    def test_session_update_title(self):
        """Test SessionUpdate with title only."""
        request = SessionUpdate(title="New Title")
        assert request.title == "New Title"
        assert request.model is None

    def test_session_update_model(self):
        """Test SessionUpdate with model only."""
        request = SessionUpdate(model="gpt-4o-mini")
        assert request.title is None
        assert request.model == "gpt-4o-mini"

    def test_session_update_both(self):
        """Test SessionUpdate with both values."""
        request = SessionUpdate(title="New Title", model="gpt-4o")
        assert request.title == "New Title"
        assert request.model == "gpt-4o"

    def test_session_response(self):
        """Test SessionResponse model."""
        response = SessionResponse(
            id="session-123",
            project_path="/test",
            provider="anthropic",
            model="claude-3-5-sonnet-20241022",
            title="Test",
            created_at="2026-02-24T12:00:00",
            updated_at="2026-02-24T12:30:00",
        )
        assert response.id == "session-123"
        assert response.project_path == "/test"
        assert response.provider == "anthropic"
        assert response.model == "claude-3-5-sonnet-20241022"
        assert response.title == "Test"


@pytest.mark.unit
class TestCreateSession:
    """Tests for create_session endpoint."""

    def test_create_session_success(self, client, mock_session_manager):
        """Test successful session creation."""
        with patch("opencode.server.routes.sessions.get_session_manager", return_value=mock_session_manager):
            response = client.post("/sessions/", json={
                "project_path": "/test/project",
            })
            
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "session-123"
        assert data["project_path"] == "/test/project"

    def test_create_session_with_all_fields(self, client, mock_session_manager):
        """Test session creation with all fields."""
        with patch("opencode.server.routes.sessions.get_session_manager", return_value=mock_session_manager):
            response = client.post("/sessions/", json={
                "project_path": "/test/project",
                "provider": "openai",
                "model": "gpt-4o",
                "title": "My Session",
            })
            
        assert response.status_code == 200
        mock_session_manager.create_session.assert_called_once()

    def test_create_session_calls_manager(self, client, mock_session_manager):
        """Test that create_session calls the session manager."""
        with patch("opencode.server.routes.sessions.get_session_manager", return_value=mock_session_manager):
            client.post("/sessions/", json={
                "project_path": "/test",
                "provider": "anthropic",
                "model": "claude-3-5-sonnet-20241022",
                "title": "Test",
            })
            
        mock_session_manager.create_session.assert_called_once_with(
            project_path="/test",
            provider="anthropic",
            model="claude-3-5-sonnet-20241022",
            title="Test",
        )


@pytest.mark.unit
class TestListSessions:
    """Tests for list_sessions endpoint."""

    def test_list_sessions_success(self, client, mock_session_manager):
        """Test successful session listing."""
        with patch("opencode.server.routes.sessions.get_session_manager", return_value=mock_session_manager):
            response = client.get("/sessions/")
            
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1

    def test_list_sessions_with_project_path(self, client, mock_session_manager):
        """Test session listing with project path filter."""
        with patch("opencode.server.routes.sessions.get_session_manager", return_value=mock_session_manager):
            response = client.get("/sessions/?project_path=/test")
            
        assert response.status_code == 200
        mock_session_manager.list_sessions.assert_called_once()

    def test_list_sessions_with_pagination(self, client, mock_session_manager):
        """Test session listing with pagination."""
        with patch("opencode.server.routes.sessions.get_session_manager", return_value=mock_session_manager):
            response = client.get("/sessions/?limit=10&offset=5")
            
        assert response.status_code == 200
        mock_session_manager.list_sessions.assert_called_once()


@pytest.mark.unit
class TestGetSession:
    """Tests for get_session endpoint."""

    def test_get_session_success(self, client, mock_session_manager, mock_session):
        """Test successful session retrieval."""
        with patch("opencode.server.routes.sessions.get_session_manager", return_value=mock_session_manager):
            response = client.get("/sessions/session-123")
            
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "session-123"

    def test_get_session_not_found(self, client, mock_session_manager):
        """Test session not found."""
        mock_session_manager.get_session = AsyncMock(return_value=None)
        
        with patch("opencode.server.routes.sessions.get_session_manager", return_value=mock_session_manager):
            response = client.get("/sessions/nonexistent")
            
        assert response.status_code == 404


@pytest.mark.unit
class TestUpdateSession:
    """Tests for update_session endpoint."""

    def test_update_session_success(self, client, mock_session_manager):
        """Test successful session update."""
        with patch("opencode.server.routes.sessions.get_session_manager", return_value=mock_session_manager):
            response = client.patch("/sessions/session-123", json={
                "title": "Updated Title",
            })
            
        assert response.status_code == 200
        mock_session_manager.update_session.assert_called_once()

    def test_update_session_not_found(self, client, mock_session_manager):
        """Test session update not found."""
        mock_session_manager.update_session = AsyncMock(return_value=None)
        
        with patch("opencode.server.routes.sessions.get_session_manager", return_value=mock_session_manager):
            response = client.patch("/sessions/nonexistent", json={
                "title": "Updated",
            })
            
        assert response.status_code == 404


@pytest.mark.unit
class TestDeleteSession:
    """Tests for delete_session endpoint."""

    def test_delete_session_success(self, client, mock_session_manager):
        """Test successful session deletion."""
        with patch("opencode.server.routes.sessions.get_session_manager", return_value=mock_session_manager):
            response = client.delete("/sessions/session-123")
            
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_delete_session_not_found(self, client, mock_session_manager):
        """Test session deletion not found."""
        mock_session_manager.delete_session = AsyncMock(return_value=False)
        
        with patch("opencode.server.routes.sessions.get_session_manager", return_value=mock_session_manager):
            response = client.delete("/sessions/nonexistent")
            
        assert response.status_code == 404


@pytest.mark.unit
class TestExportSession:
    """Tests for export_session endpoint."""

    def test_export_session_success(self, client, mock_session_manager):
        """Test successful session export."""
        with patch("opencode.server.routes.sessions.get_session_manager", return_value=mock_session_manager):
            response = client.post("/sessions/session-123/export")
            
        assert response.status_code == 200
        data = response.json()
        assert "id" in data

    def test_export_session_not_found(self, client, mock_session_manager):
        """Test session export not found."""
        mock_session_manager.export_session = AsyncMock(return_value=None)
        
        with patch("opencode.server.routes.sessions.get_session_manager", return_value=mock_session_manager):
            response = client.post("/sessions/nonexistent/export")
            
        assert response.status_code == 404


@pytest.mark.unit
class TestImportSession:
    """Tests for import_session endpoint."""

    def test_import_session_success(self, client, mock_session_manager):
        """Test successful session import."""
        with patch("opencode.server.routes.sessions.get_session_manager", return_value=mock_session_manager):
            response = client.post("/sessions/import", json={
                "id": "imported-session",
                "project_path": "/imported",
            })
            
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "session-123"

    def test_import_session_calls_manager(self, client, mock_session_manager):
        """Test that import_session calls the session manager."""
        import_data = {"id": "test", "project_path": "/test"}
        
        with patch("opencode.server.routes.sessions.get_session_manager", return_value=mock_session_manager):
            client.post("/sessions/import", json=import_data)
            
        mock_session_manager.import_session.assert_called_once_with(import_data)
