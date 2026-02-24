"""
Tests for chat API routes.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect

from opencode.server.routes.chat import (
    router,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    SessionCreate,
)


@pytest.fixture
def app():
    """Create FastAPI app with chat router."""
    app = FastAPI()
    app.include_router(router, prefix="/chat")
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_session_manager():
    """Create mock session manager."""
    manager = AsyncMock()
    manager.create_session = AsyncMock(return_value=MagicMock(id="test-session-id"))
    manager.add_message = AsyncMock()
    manager.get_messages = AsyncMock(return_value=[])
    manager.clear_messages = AsyncMock()
    return manager


class TestChatModels:
    """Tests for Pydantic models."""
    
    def test_chat_message_creation(self):
        """Test ChatMessage model creation."""
        msg = ChatMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
    
    def test_chat_request_defaults(self):
        """Test ChatRequest default values."""
        req = ChatRequest(message="Test")
        assert req.message == "Test"
        assert req.session_id is None
        assert req.model is None
        assert req.stream is True
    
    def test_chat_request_with_all_fields(self):
        """Test ChatRequest with all fields."""
        req = ChatRequest(
            session_id="session-123",
            message="Test message",
            model="gpt-4",
            stream=False,
        )
        assert req.session_id == "session-123"
        assert req.message == "Test message"
        assert req.model == "gpt-4"
        assert req.stream is False
    
    def test_chat_response_creation(self):
        """Test ChatResponse model creation."""
        msg = ChatMessage(role="assistant", content="Response")
        resp = ChatResponse(session_id="session-123", message=msg)
        assert resp.session_id == "session-123"
        assert resp.message.role == "assistant"
        assert resp.usage is None
    
    def test_chat_response_with_usage(self):
        """Test ChatResponse with usage stats."""
        msg = ChatMessage(role="assistant", content="Response")
        usage = {"prompt_tokens": 10, "completion_tokens": 20}
        resp = ChatResponse(session_id="session-123", message=msg, usage=usage)
        assert resp.usage == usage
    
    def test_session_create_defaults(self):
        """Test SessionCreate default values."""
        req = SessionCreate(project_path="/test")
        assert req.project_path == "/test"
        assert req.provider == "anthropic"
        assert req.model == "claude-3-5-sonnet-20241022"
    
    def test_session_create_with_all_fields(self):
        """Test SessionCreate with all fields."""
        req = SessionCreate(
            project_path="/test",
            provider="openai",
            model="gpt-4",
        )
        assert req.provider == "openai"
        assert req.model == "gpt-4"


class TestSendMessage:
    """Tests for send_message endpoint."""
    
    @patch('opencode.server.routes.chat.get_session_manager')
    def test_send_message_creates_new_session(self, mock_get_manager, client, mock_session_manager):
        """Test sending message creates new session when no session_id."""
        mock_get_manager.return_value = mock_session_manager
        
        response = client.post(
            "/chat/message",
            json={"message": "Hello"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["message"]["role"] == "assistant"
        mock_session_manager.create_session.assert_called_once()
    
    @patch('opencode.server.routes.chat.get_session_manager')
    def test_send_message_uses_existing_session(self, mock_get_manager, client, mock_session_manager):
        """Test sending message uses existing session."""
        mock_get_manager.return_value = mock_session_manager
        
        response = client.post(
            "/chat/message",
            json={"message": "Hello", "session_id": "existing-session"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "existing-session"
        mock_session_manager.create_session.assert_not_called()
    
    @patch('opencode.server.routes.chat.get_session_manager')
    def test_send_message_adds_user_message(self, mock_get_manager, client, mock_session_manager):
        """Test that user message is added."""
        mock_get_manager.return_value = mock_session_manager
        
        client.post(
            "/chat/message",
            json={"message": "Hello", "session_id": "test-session"},
        )
        
        # Check add_message was called for user message
        calls = mock_session_manager.add_message.call_args_list
        assert len(calls) >= 1
        user_call = calls[0]
        assert user_call[0][0] == "test-session"
        assert user_call[1]["role"] == "user"
        assert user_call[1]["content"] == "Hello"
    
    @patch('opencode.server.routes.chat.get_session_manager')
    def test_send_message_adds_assistant_message(self, mock_get_manager, client, mock_session_manager):
        """Test that assistant message is added."""
        mock_get_manager.return_value = mock_session_manager
        
        client.post(
            "/chat/message",
            json={"message": "Hello", "session_id": "test-session"},
        )
        
        # Check add_message was called for assistant message
        calls = mock_session_manager.add_message.call_args_list
        assert len(calls) >= 2
        assistant_call = calls[1]
        assert assistant_call[0][0] == "test-session"
        assert assistant_call[1]["role"] == "assistant"
    
    @patch('opencode.server.routes.chat.get_session_manager')
    def test_send_message_with_custom_model(self, mock_get_manager, client, mock_session_manager):
        """Test sending message with custom model."""
        mock_get_manager.return_value = mock_session_manager
        
        response = client.post(
            "/chat/message",
            json={"message": "Hello", "model": "gpt-4"},
        )
        
        assert response.status_code == 200
        # Check create_session was called with the custom model
        mock_session_manager.create_session.assert_called_once()
        call_kwargs = mock_session_manager.create_session.call_args[1]
        assert call_kwargs["model"] == "gpt-4"


class TestStreamMessage:
    """Tests for stream_message endpoint."""
    
    def test_stream_message_returns_streaming_response(self, client):
        """Test that stream endpoint returns streaming response."""
        response = client.post(
            "/chat/stream",
            json={"message": "Hello"},
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    
    def test_stream_message_content(self, client):
        """Test streaming response content."""
        response = client.post(
            "/chat/stream",
            json={"message": "Hello"},
        )
        
        content = response.content.decode()
        assert "data:" in content
        assert "[DONE]" in content
    
    def test_stream_message_with_session(self, client):
        """Test streaming with session_id."""
        response = client.post(
            "/chat/stream",
            json={"message": "Hello", "session_id": "test-session"},
        )
        
        assert response.status_code == 200


class TestGetHistory:
    """Tests for get_history endpoint."""
    
    @patch('opencode.server.routes.chat.get_session_manager')
    def test_get_history_returns_messages(self, mock_get_manager, client, mock_session_manager):
        """Test getting chat history."""
        mock_msg = MagicMock()
        mock_msg.role = "user"
        mock_msg.content = "Hello"
        mock_session_manager.get_messages.return_value = [mock_msg]
        mock_get_manager.return_value = mock_session_manager
        
        response = client.get("/chat/history/test-session")
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test-session"
        assert len(data["messages"]) == 1
        assert data["messages"][0]["role"] == "user"
    
    @patch('opencode.server.routes.chat.get_session_manager')
    def test_get_history_with_limit(self, mock_get_manager, client, mock_session_manager):
        """Test getting chat history with limit."""
        mock_get_manager.return_value = mock_session_manager
        
        client.get("/chat/history/test-session?limit=50")
        
        mock_session_manager.get_messages.assert_called_once()
        call_args = mock_session_manager.get_messages.call_args
        assert call_args[0][0] == "test-session"
        assert call_args[1]["limit"] == 50
    
    @patch('opencode.server.routes.chat.get_session_manager')
    def test_get_history_empty(self, mock_get_manager, client, mock_session_manager):
        """Test getting empty chat history."""
        mock_session_manager.get_messages.return_value = []
        mock_get_manager.return_value = mock_session_manager
        
        response = client.get("/chat/history/test-session")
        
        assert response.status_code == 200
        data = response.json()
        assert data["messages"] == []


class TestClearHistory:
    """Tests for clear_history endpoint."""
    
    @patch('opencode.server.routes.chat.get_session_manager')
    def test_clear_history_success(self, mock_get_manager, client, mock_session_manager):
        """Test clearing chat history."""
        mock_get_manager.return_value = mock_session_manager
        
        response = client.delete("/chat/history/test-session")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        mock_session_manager.clear_messages.assert_called_once_with("test-session")


class TestWebSocketChat:
    """Tests for WebSocket chat endpoint."""
    
    @patch('opencode.server.routes.chat.get_session_manager')
    def test_websocket_connection(self, mock_get_manager, app, mock_session_manager):
        """Test WebSocket connection is accepted."""
        mock_get_manager.return_value = mock_session_manager
        
        with TestClient(app).websocket_connect("/chat/ws/test-session") as websocket:
            # Connection should be established
            pass
    
    @patch('opencode.server.routes.chat.get_session_manager')
    def test_websocket_send_message(self, mock_get_manager, app, mock_session_manager):
        """Test sending message through WebSocket."""
        mock_get_manager.return_value = mock_session_manager
        
        with TestClient(app).websocket_connect("/chat/ws/test-session") as websocket:
            websocket.send_json({"message": "Hello"})
            
            # Should receive acknowledgment
            ack = websocket.receive_json()
            assert ack["type"] == "ack"
    
    @patch('opencode.server.routes.chat.get_session_manager')
    def test_websocket_receives_chunks(self, mock_get_manager, app, mock_session_manager):
        """Test receiving chunks through WebSocket."""
        mock_get_manager.return_value = mock_session_manager
        
        with TestClient(app).websocket_connect("/chat/ws/test-session") as websocket:
            websocket.send_json({"message": "Hello"})
            
            # Skip acknowledgment
            websocket.receive_json()
            
            # Receive chunks
            chunks = []
            while True:
                data = websocket.receive_json()
                if data["type"] == "done":
                    break
                if data["type"] == "chunk":
                    chunks.append(data["content"])
            
            assert len(chunks) > 0
    
    @patch('opencode.server.routes.chat.get_session_manager')
    def test_websocket_receives_done(self, mock_get_manager, app, mock_session_manager):
        """Test receiving done message through WebSocket."""
        mock_get_manager.return_value = mock_session_manager
        
        with TestClient(app).websocket_connect("/chat/ws/test-session") as websocket:
            websocket.send_json({"message": "Hello"})
            
            # Skip acknowledgment and chunks
            while True:
                data = websocket.receive_json()
                if data["type"] == "done":
                    assert "message" in data
                    break
    
    @patch('opencode.server.routes.chat.get_session_manager')
    def test_websocket_adds_user_message(self, mock_get_manager, app, mock_session_manager):
        """Test that user message is added via WebSocket."""
        mock_get_manager.return_value = mock_session_manager
        
        with TestClient(app).websocket_connect("/chat/ws/test-session") as websocket:
            websocket.send_json({"message": "Hello"})
            
            # Receive all messages
            while True:
                data = websocket.receive_json()
                if data["type"] == "done":
                    break
        
        # Check add_message was called for user
        calls = mock_session_manager.add_message.call_args_list
        user_calls = [c for c in calls if c[1].get("role") == "user"]
        assert len(user_calls) >= 1
    
    @patch('opencode.server.routes.chat.get_session_manager')
    def test_websocket_custom_model(self, mock_get_manager, app, mock_session_manager):
        """Test WebSocket with custom model."""
        mock_get_manager.return_value = mock_session_manager
        
        with TestClient(app).websocket_connect("/chat/ws/test-session") as websocket:
            websocket.send_json({"message": "Hello", "model": "gpt-4"})
            
            # Receive all messages
            while True:
                data = websocket.receive_json()
                if data["type"] == "done":
                    break
        
        # Check add_message was called with model
        calls = mock_session_manager.add_message.call_args_list
        assistant_calls = [c for c in calls if c[1].get("role") == "assistant"]
        assert len(assistant_calls) >= 1
        assert assistant_calls[0][1].get("model") == "gpt-4"
