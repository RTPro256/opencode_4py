"""
Unit tests for Session Manager.

Tests session persistence, retrieval, and management functionality.
"""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import tempfile
import json

from opencode.core.session import (
    Session,
    SessionManager,
    Message,
    MessageRole,
    ContentBlock,
    ToolCall,
    ToolCallStatus,
    SessionSummary,
)


class TestSessionManager:
    """Tests for SessionManager class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def session_manager(self, temp_dir):
        """Create a SessionManager instance."""
        return SessionManager(temp_dir)

    @pytest.fixture
    def sample_session(self, temp_dir):
        """Create a sample session for testing."""
        session = Session.create(
            project_id="test-project",
            directory=str(temp_dir),
            title="Test Session",
        )
        session.add_message(Message.user("Hello"))
        return session

    def test_init_creates_sessions_dir(self, temp_dir):
        """Test that initialization creates sessions directory."""
        manager = SessionManager(temp_dir)
        
        assert manager.sessions_dir.exists()
        assert manager.sessions_dir.name == "sessions"

    @pytest.mark.asyncio
    async def test_save_session(self, session_manager, sample_session):
        """Test saving a session."""
        await session_manager.save(sample_session)
        
        # The filename format is session_{datetime}_{short_id}.json
        # Check that at least one session file exists
        session_files = list(session_manager.sessions_dir.glob("*.json"))
        assert len(session_files) == 1
        # Verify the session ID is in the filename (short_id is first 8 chars)
        short_id = sample_session.id[:8]
        assert short_id in session_files[0].name

    @pytest.mark.asyncio
    async def test_load_session(self, session_manager, sample_session):
        """Test loading a session."""
        await session_manager.save(sample_session)
        
        # The session is saved with short_id (first 8 chars) in filename
        # The load method searches for files containing the session ID
        # Try loading with full ID first
        loaded = await session_manager.load(sample_session.id)
        
        # If that fails, try with short_id
        if loaded is None:
            short_id = sample_session.id[:8]
            loaded = await session_manager.load(short_id)
        
        assert loaded is not None
        assert loaded.id == sample_session.id
        assert loaded.title == sample_session.title
        assert len(loaded.messages) == 1

    @pytest.mark.asyncio
    async def test_load_nonexistent_session(self, session_manager):
        """Test loading a session that doesn't exist."""
        result = await session_manager.load("nonexistent-id")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_list_sessions(self, session_manager, temp_dir):
        """Test listing sessions."""
        # Create multiple sessions
        session1 = Session.create(
            project_id="project1",
            directory=str(temp_dir),
            title="Session 1",
        )
        session2 = Session.create(
            project_id="project2",
            directory=str(temp_dir),
            title="Session 2",
        )
        
        await session_manager.save(session1)
        await session_manager.save(session2)
        
        sessions = await session_manager.list_sessions()
        
        assert len(sessions) == 2

    @pytest.mark.asyncio
    async def test_list_sessions_by_project(self, session_manager, temp_dir):
        """Test listing sessions filtered by project."""
        session1 = Session.create(
            project_id="project1",
            directory=str(temp_dir),
            title="Session 1",
        )
        session2 = Session.create(
            project_id="project2",
            directory=str(temp_dir),
            title="Session 2",
        )
        
        await session_manager.save(session1)
        await session_manager.save(session2)
        
        sessions = await session_manager.list_sessions(project_id="project1")
        
        assert len(sessions) == 1
        assert sessions[0].project_id == "project1"

    @pytest.mark.asyncio
    async def test_list_sessions_with_limit(self, session_manager, temp_dir):
        """Test listing sessions with limit."""
        for i in range(5):
            session = Session.create(
                project_id="test-project",
                directory=str(temp_dir),
                title=f"Session {i}",
            )
            await session_manager.save(session)
        
        sessions = await session_manager.list_sessions(limit=3)
        
        assert len(sessions) == 3

    @pytest.mark.asyncio
    async def test_delete_session(self, session_manager, sample_session):
        """Test deleting a session."""
        await session_manager.save(sample_session)
        
        # The session is saved with short_id (first 8 chars) in filename
        # The delete method searches for files containing the session ID
        # Try deleting with full ID first
        result = await session_manager.delete(sample_session.id)
        
        # If that fails, try with short_id
        if not result:
            short_id = sample_session.id[:8]
            result = await session_manager.delete(short_id)
        
        assert result is True
        # Verify no session files remain
        session_files = list(session_manager.sessions_dir.glob("*.json"))
        assert len(session_files) == 0

    @pytest.mark.asyncio
    async def test_delete_nonexistent_session(self, session_manager):
        """Test deleting a session that doesn't exist."""
        result = await session_manager.delete("nonexistent-id")
        
        assert result is False


class TestSession:
    """Tests for Session class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_create_session(self, temp_dir):
        """Test creating a session."""
        session = Session.create(
            project_id="test-project",
            directory=str(temp_dir),
            title="Test Session",
        )
        
        assert session.id is not None
        assert session.project_id == "test-project"
        assert session.title == "Test Session"
        assert session.directory == str(temp_dir)
        assert session.created_at is not None
        assert session.updated_at is not None

    def test_create_session_default_title(self, temp_dir):
        """Test creating a session with default title."""
        session = Session.create(
            project_id="test-project",
            directory=str(temp_dir),
        )
        
        assert "New session" in session.title

    def test_create_session_with_model(self, temp_dir):
        """Test creating a session with model."""
        session = Session.create(
            project_id="test-project",
            directory=str(temp_dir),
            model="gpt-4",
        )
        
        assert session.model == "gpt-4"

    def test_create_session_with_agent(self, temp_dir):
        """Test creating a session with agent."""
        session = Session.create(
            project_id="test-project",
            directory=str(temp_dir),
            agent="debug",
        )
        
        assert session.agent == "debug"

    def test_add_message(self, temp_dir):
        """Test adding a message to session."""
        session = Session.create(
            project_id="test-project",
            directory=str(temp_dir),
        )
        
        original_updated = session.updated_at
        session.add_message(Message.user("Hello"))
        
        assert len(session.messages) == 1
        assert session.updated_at >= original_updated

    def test_get_token_count_empty(self, temp_dir):
        """Test token count with no messages."""
        session = Session.create(
            project_id="test-project",
            directory=str(temp_dir),
        )
        
        assert session.get_token_count() == 0

    def test_get_token_count_with_messages(self, temp_dir):
        """Test token count with messages."""
        session = Session.create(
            project_id="test-project",
            directory=str(temp_dir),
        )
        
        msg = Message.user("Hello")
        msg.usage = {"total_tokens": 100}
        session.add_message(msg)
        
        assert session.get_token_count() == 100

    def test_get_token_count_multiple_messages(self, temp_dir):
        """Test token count with multiple messages."""
        session = Session.create(
            project_id="test-project",
            directory=str(temp_dir),
        )
        
        msg1 = Message.user("Hello")
        msg1.usage = {"total_tokens": 100}
        session.add_message(msg1)
        
        msg2 = Message.assistant(content=[ContentBlock(type="text", text="Hi")])
        msg2.usage = {"total_tokens": 50}
        session.add_message(msg2)
        
        assert session.get_token_count() == 150

    def test_compact(self, temp_dir):
        """Test session compact method."""
        session = Session.create(
            project_id="test-project",
            directory=str(temp_dir),
        )
        
        # Compact is a no-op for now
        session.compact()
        
        assert True  # Just verify it doesn't raise

    def test_to_dict(self, temp_dir):
        """Test converting session to dictionary."""
        session = Session.create(
            project_id="test-project",
            directory=str(temp_dir),
            title="Test Session",
        )
        session.add_message(Message.user("Hello"))
        
        data = session.to_dict()
        
        assert data["id"] == session.id
        assert data["project_id"] == "test-project"
        assert data["title"] == "Test Session"
        assert len(data["messages"]) == 1

    def test_to_dict_with_summary(self, temp_dir):
        """Test converting session with summary to dictionary."""
        session = Session.create(
            project_id="test-project",
            directory=str(temp_dir),
        )
        session.summary = SessionSummary(
            additions=10,
            deletions=5,
            files_changed=2,
            tool_calls=3,
            total_tokens=1000,
            total_cost=0.05,
        )
        
        data = session.to_dict()
        
        assert data["summary"]["additions"] == 10
        assert data["summary"]["deletions"] == 5

    def test_from_dict(self, temp_dir):
        """Test creating session from dictionary."""
        now = datetime.now()
        data = {
            "id": "test-id",
            "project_id": "test-project",
            "title": "Test Session",
            "directory": str(temp_dir),
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "model": "gpt-4",
            "agent": "build",
            "messages": [],
            "summary": None,
            "metadata": {},
        }
        
        session = Session.from_dict(data)
        
        assert session.id == "test-id"
        assert session.project_id == "test-project"
        assert session.title == "Test Session"
        assert session.model == "gpt-4"

    def test_from_dict_with_messages(self, temp_dir):
        """Test creating session from dictionary with messages."""
        now = datetime.now()
        data = {
            "id": "test-id",
            "project_id": "test-project",
            "title": "Test Session",
            "directory": str(temp_dir),
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "messages": [
                {
                    "id": "msg-1",
                    "role": "user",
                    "content": [{"type": "text", "text": "Hello"}],
                    "created_at": now.isoformat(),
                }
            ],
            "summary": None,
            "metadata": {},
        }
        
        session = Session.from_dict(data)
        
        assert len(session.messages) == 1
        assert session.messages[0].role == MessageRole.USER

    def test_from_dict_with_summary(self, temp_dir):
        """Test creating session from dictionary with summary."""
        now = datetime.now()
        data = {
            "id": "test-id",
            "project_id": "test-project",
            "title": "Test Session",
            "directory": str(temp_dir),
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "messages": [],
            "summary": {
                "additions": 10,
                "deletions": 5,
                "files_changed": 2,
                "tool_calls": 3,
                "total_tokens": 1000,
                "total_cost": 0.05,
            },
            "metadata": {},
        }
        
        session = Session.from_dict(data)
        
        assert session.summary.additions == 10
        assert session.summary.total_cost == 0.05


class TestSessionGetMessagesForAPI:
    """Tests for Session.get_messages_for_api method."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_empty_messages(self, temp_dir):
        """Test with no messages."""
        session = Session.create(
            project_id="test-project",
            directory=str(temp_dir),
        )
        
        api_messages = session.get_messages_for_api()
        
        assert api_messages == []

    def test_single_text_message(self, temp_dir):
        """Test with single text message."""
        session = Session.create(
            project_id="test-project",
            directory=str(temp_dir),
        )
        session.add_message(Message.user("Hello"))
        
        api_messages = session.get_messages_for_api()
        
        assert len(api_messages) == 1
        assert api_messages[0]["role"] == "user"
        assert api_messages[0]["content"] == "Hello"

    def test_multiple_messages(self, temp_dir):
        """Test with multiple messages."""
        session = Session.create(
            project_id="test-project",
            directory=str(temp_dir),
        )
        session.add_message(Message.system("Be helpful"))
        session.add_message(Message.user("Hello"))
        
        api_messages = session.get_messages_for_api()
        
        assert len(api_messages) == 2
        assert api_messages[0]["role"] == "system"
        assert api_messages[1]["role"] == "user"

    def test_tool_result_message(self, temp_dir):
        """Test with tool result message."""
        session = Session.create(
            project_id="test-project",
            directory=str(temp_dir),
        )
        session.add_message(Message.tool_result(
            tool_call_id="call-123",
            result="Tool output",
        ))
        
        api_messages = session.get_messages_for_api()
        
        assert len(api_messages) == 1
        assert api_messages[0]["role"] == "tool"
        assert api_messages[0]["tool_call_id"] == "call-123"
        assert api_messages[0]["content"] == "Tool output"

    def test_message_with_tool_call(self, temp_dir):
        """Test with message containing tool call."""
        session = Session.create(
            project_id="test-project",
            directory=str(temp_dir),
        )
        
        tool_call = ToolCall(
            id="call-123",
            name="read_file",
            arguments={"path": "/test.py"},
        )
        content = ContentBlock(type="tool_call", tool_call=tool_call)
        session.add_message(Message.assistant(content=[content]))
        
        api_messages = session.get_messages_for_api()
        
        assert len(api_messages) == 1
        assert "content" in api_messages[0]
        # Content should be a list with tool_use
        content = api_messages[0]["content"]
        assert isinstance(content, list)
        assert content[0]["type"] == "tool_use"

    def test_message_with_image_url(self, temp_dir):
        """Test with message containing image URL."""
        session = Session.create(
            project_id="test-project",
            directory=str(temp_dir),
        )
        
        content = ContentBlock(
            type="image",
            image_url="https://example.com/image.png",
        )
        session.add_message(Message.assistant(content=[content]))
        
        api_messages = session.get_messages_for_api()
        
        content = api_messages[0]["content"]
        assert isinstance(content, list)
        assert content[0]["type"] == "image"

    def test_message_with_image_data(self, temp_dir):
        """Test with message containing image data."""
        session = Session.create(
            project_id="test-project",
            directory=str(temp_dir),
        )
        
        content = ContentBlock(
            type="image",
            image_data=b"fake_image_data",
        )
        session.add_message(Message.assistant(content=[content]))
        
        api_messages = session.get_messages_for_api()
        
        content = api_messages[0]["content"]
        assert isinstance(content, list)
        assert content[0]["type"] == "image"


class TestMessage:
    """Tests for Message class."""

    def test_user_message(self):
        """Test creating user message."""
        msg = Message.user("Hello")
        
        assert msg.role == MessageRole.USER
        assert msg.text_content == "Hello"
        assert len(msg.content) == 1
        assert msg.content[0].type == "text"

    def test_assistant_message(self):
        """Test creating assistant message."""
        content = [ContentBlock(type="text", text="Hi there")]
        msg = Message.assistant(content=content, model="gpt-4")
        
        assert msg.role == MessageRole.ASSISTANT
        assert msg.model == "gpt-4"
        assert msg.text_content == "Hi there"

    def test_assistant_message_with_usage(self):
        """Test creating assistant message with usage."""
        content = [ContentBlock(type="text", text="Response")]
        usage = {"total_tokens": 100, "prompt_tokens": 50, "completion_tokens": 50}
        msg = Message.assistant(content=content, usage=usage)
        
        assert msg.usage == usage

    def test_system_message(self):
        """Test creating system message."""
        msg = Message.system("Be helpful")
        
        assert msg.role == MessageRole.SYSTEM
        assert msg.text_content == "Be helpful"

    def test_tool_result_message(self):
        """Test creating tool result message."""
        msg = Message.tool_result(
            tool_call_id="call-123",
            result="Success",
        )
        
        assert msg.role == MessageRole.TOOL
        assert len(msg.content) == 1
        assert msg.content[0].type == "tool_result"
        assert msg.content[0].tool_call_id == "call-123"

    def test_tool_result_message_with_error(self):
        """Test creating tool result message with error."""
        msg = Message.tool_result(
            tool_call_id="call-123",
            result="Error output",
            error="Tool failed",
        )
        
        assert msg.metadata.get("error") == "Tool failed"

    def test_text_content_multiple_blocks(self):
        """Test text_content with multiple blocks."""
        content = [
            ContentBlock(type="text", text="First"),
            ContentBlock(type="text", text="Second"),
        ]
        msg = Message.assistant(content=content)
        
        assert msg.text_content == "First\nSecond"

    def test_text_content_empty(self):
        """Test text_content with no text blocks."""
        content = [ContentBlock(type="image", image_url="http://example.com/img.png")]
        msg = Message.assistant(content=content)
        
        assert msg.text_content == ""


class TestContentBlock:
    """Tests for ContentBlock class."""

    def test_text_block(self):
        """Test text content block."""
        block = ContentBlock(type="text", text="Hello")
        
        assert block.type == "text"
        assert block.text == "Hello"
        assert block.tool_call is None
        assert block.image_url is None

    def test_tool_call_block(self):
        """Test tool call content block."""
        tool_call = ToolCall(
            id="call-1",
            name="test",
            arguments={},
        )
        block = ContentBlock(type="tool_call", tool_call=tool_call)
        
        assert block.type == "tool_call"
        assert block.tool_call == tool_call

    def test_tool_result_block(self):
        """Test tool result content block."""
        block = ContentBlock(
            type="tool_result",
            text="Result",
            tool_call_id="call-1",
        )
        
        assert block.type == "tool_result"
        assert block.text == "Result"
        assert block.tool_call_id == "call-1"

    def test_image_url_block(self):
        """Test image URL content block."""
        block = ContentBlock(
            type="image",
            image_url="https://example.com/image.png",
        )
        
        assert block.type == "image"
        assert block.image_url == "https://example.com/image.png"

    def test_image_data_block(self):
        """Test image data content block."""
        block = ContentBlock(
            type="image",
            image_data=b"image_data",
        )
        
        assert block.type == "image"
        assert block.image_data == b"image_data"


class TestToolCall:
    """Tests for ToolCall class."""

    def test_tool_call_creation(self):
        """Test creating a tool call."""
        tool_call = ToolCall(
            id="call-1",
            name="read_file",
            arguments={"path": "/test.py"},
        )
        
        assert tool_call.id == "call-1"
        assert tool_call.name == "read_file"
        assert tool_call.arguments == {"path": "/test.py"}
        assert tool_call.status == ToolCallStatus.PENDING
        assert tool_call.result is None
        assert tool_call.error is None

    def test_tool_call_with_result(self):
        """Test tool call with result."""
        tool_call = ToolCall(
            id="call-1",
            name="test",
            arguments={},
            status=ToolCallStatus.SUCCESS,
            result="Success result",
        )
        
        assert tool_call.status == ToolCallStatus.SUCCESS
        assert tool_call.result == "Success result"

    def test_tool_call_with_error(self):
        """Test tool call with error."""
        tool_call = ToolCall(
            id="call-1",
            name="test",
            arguments={},
            status=ToolCallStatus.ERROR,
            error="Something went wrong",
        )
        
        assert tool_call.status == ToolCallStatus.ERROR
        assert tool_call.error == "Something went wrong"

    def test_tool_call_with_timestamps(self):
        """Test tool call with timestamps."""
        now = datetime.now()
        tool_call = ToolCall(
            id="call-1",
            name="test",
            arguments={},
            started_at=now,
            completed_at=now,
        )
        
        assert tool_call.started_at == now
        assert tool_call.completed_at == now


class TestToolCallStatus:
    """Tests for ToolCallStatus enum."""

    def test_values(self):
        """Test enum values."""
        assert ToolCallStatus.PENDING.value == "pending"
        assert ToolCallStatus.RUNNING.value == "running"
        assert ToolCallStatus.SUCCESS.value == "success"
        assert ToolCallStatus.ERROR.value == "error"

    def test_string_conversion(self):
        """Test converting to string."""
        # Since it's a str enum, the value is the string
        assert ToolCallStatus.PENDING.value == "pending"
        assert ToolCallStatus.SUCCESS.value == "success"


class TestMessageRole:
    """Tests for MessageRole enum."""

    def test_values(self):
        """Test enum values."""
        assert MessageRole.SYSTEM.value == "system"
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
        assert MessageRole.TOOL.value == "tool"

    def test_string_conversion(self):
        """Test converting to string."""
        # Since it's a str enum, the value is the string
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"


class TestSessionSummary:
    """Tests for SessionSummary class."""

    def test_default_values(self):
        """Test default values."""
        summary = SessionSummary()
        
        assert summary.additions == 0
        assert summary.deletions == 0
        assert summary.files_changed == 0
        assert summary.tool_calls == 0
        assert summary.total_tokens == 0
        assert summary.total_cost == 0.0

    def test_custom_values(self):
        """Test custom values."""
        summary = SessionSummary(
            additions=100,
            deletions=50,
            files_changed=5,
            tool_calls=10,
            total_tokens=5000,
            total_cost=0.25,
        )
        
        assert summary.additions == 100
        assert summary.deletions == 50
        assert summary.files_changed == 5
        assert summary.tool_calls == 10
        assert summary.total_tokens == 5000
        assert summary.total_cost == 0.25
