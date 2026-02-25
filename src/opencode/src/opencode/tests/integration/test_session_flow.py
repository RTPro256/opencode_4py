"""
Integration tests for session flow.

Tests the complete flow of session creation, management, and persistence.
"""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from opencode.core.session import (
    Session,
    Message,
    MessageRole,
    ContentBlock,
    ToolCall,
    ToolCallStatus,
    SessionSummary,
)


@pytest.mark.integration
class TestSessionFlow:
    """Integration tests for session flow."""
    
    @pytest.fixture
    def session(self, temp_workspace):
        """Create a test session."""
        return Session.create(
            project_id="test-project",
            directory=str(temp_workspace),
            title="Test Session",
        )
    
    def test_session_creation(self, session):
        """Test session is created correctly."""
        assert session.id is not None
        assert session.title == "Test Session"
        assert session.directory is not None
        assert len(session.messages) == 0
    
    def test_session_add_user_message(self, session):
        """Test adding user messages to a session."""
        message = Message.user("Hello, world!")
        session.add_message(message)
        
        assert len(session.messages) == 1
        assert session.messages[0].role == MessageRole.USER
        assert session.messages[0].text_content == "Hello, world!"
    
    def test_session_add_assistant_message(self, session):
        """Test adding assistant messages."""
        user_msg = Message.user("What is 2+2?")
        session.add_message(user_msg)
        
        assistant_msg = Message.assistant(
            content=[ContentBlock(type="text", text="2+2 equals 4.")],
        )
        session.add_message(assistant_msg)
        
        assert len(session.messages) == 2
        assert session.messages[1].role == MessageRole.ASSISTANT
    
    def test_session_add_system_message(self, session):
        """Test adding system messages."""
        system_msg = Message.system("You are a helpful assistant.")
        session.add_message(system_msg)
        
        assert len(session.messages) == 1
        assert session.messages[0].role == MessageRole.SYSTEM
    
    def test_session_message_history(self, session):
        """Test session message history."""
        # Add multiple messages
        for i in range(5):
            session.add_message(Message.user(f"Message {i}"))
            session.add_message(Message.assistant(
                content=[ContentBlock(type="text", text=f"Response {i}")]
            ))
        
        assert len(session.messages) == 10
    
    def test_session_get_messages_for_api(self, session):
        """Test getting messages formatted for API."""
        session.add_message(Message.system("System prompt"))
        session.add_message(Message.user("Hello"))
        
        api_messages = session.get_messages_for_api()
        
        assert len(api_messages) == 2
        assert api_messages[0]["role"] == "system"
        assert api_messages[1]["role"] == "user"
    
    def test_session_updated_at(self, session):
        """Test that updated_at changes when messages are added."""
        original_updated = session.updated_at
        
        session.add_message(Message.user("Test"))
        
        assert session.updated_at >= original_updated


@pytest.mark.integration
class TestMessageTypes:
    """Tests for different message types."""
    
    def test_user_message_creation(self):
        """Test creating user messages."""
        msg = Message.user("Hello")
        
        assert msg.role == MessageRole.USER
        assert msg.text_content == "Hello"
    
    def test_assistant_message_creation(self):
        """Test creating assistant messages."""
        msg = Message.assistant(
            content=[ContentBlock(type="text", text="Hi there!")],
            model="gpt-4",
        )
        
        assert msg.role == MessageRole.ASSISTANT
        assert msg.model == "gpt-4"
    
    def test_system_message_creation(self):
        """Test creating system messages."""
        msg = Message.system("You are helpful.")
        
        assert msg.role == MessageRole.SYSTEM
        assert msg.text_content == "You are helpful."
    
    def test_tool_result_message(self):
        """Test creating tool result messages."""
        msg = Message.tool_result(
            tool_call_id="call-123",
            result="Tool executed successfully",
        )
        
        assert msg.role == MessageRole.TOOL
        assert len(msg.content) == 1
        assert msg.content[0].type == "tool_result"


@pytest.mark.integration
class TestToolCalls:
    """Tests for tool call handling in sessions."""
    
    def test_tool_call_creation(self):
        """Test creating a tool call."""
        tool_call = ToolCall(
            id="call-123",
            name="read_file",
            arguments={"path": "/test/file.py"},
        )
        
        assert tool_call.id == "call-123"
        assert tool_call.name == "read_file"
        assert tool_call.status == ToolCallStatus.PENDING
    
    def test_tool_call_status_transitions(self):
        """Test tool call status transitions."""
        tool_call = ToolCall(
            id="call-1",
            name="test_tool",
            arguments={},
        )
        
        assert tool_call.status == ToolCallStatus.PENDING
        
        tool_call.status = ToolCallStatus.RUNNING
        assert tool_call.status == ToolCallStatus.RUNNING
        
        tool_call.status = ToolCallStatus.SUCCESS
        tool_call.result = "Success"
        assert tool_call.status == ToolCallStatus.SUCCESS
    
    def test_tool_call_error(self):
        """Test tool call with error."""
        tool_call = ToolCall(
            id="call-1",
            name="failing_tool",
            arguments={},
            status=ToolCallStatus.ERROR,
            error="Tool failed",
        )
        
        assert tool_call.status == ToolCallStatus.ERROR
        assert tool_call.error == "Tool failed"
    
    def test_message_with_tool_call(self):
        """Test message containing tool call."""
        tool_call = ToolCall(
            id="call-1",
            name="test_tool",
            arguments={"arg": "value"},
        )
        
        content = ContentBlock(
            type="tool_call",
            tool_call=tool_call,
        )
        
        msg = Message.assistant(content=[content])
        
        assert len(msg.content) == 1
        assert msg.content[0].tool_call is not None


@pytest.mark.integration
class TestSessionSummary:
    """Tests for session summary."""
    
    def test_summary_creation(self):
        """Test creating session summary."""
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
    
    def test_summary_defaults(self):
        """Test summary default values."""
        summary = SessionSummary()
        
        assert summary.additions == 0
        assert summary.deletions == 0
        assert summary.files_changed == 0
        assert summary.tool_calls == 0
        assert summary.total_tokens == 0
        assert summary.total_cost == 0.0


@pytest.mark.integration
class TestContentBlock:
    """Tests for content blocks."""
    
    def test_text_block(self):
        """Test text content block."""
        block = ContentBlock(type="text", text="Hello")
        
        assert block.type == "text"
        assert block.text == "Hello"
    
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
            image_data=b"fake_image_data",
        )
        
        assert block.type == "image"
        assert block.image_data == b"fake_image_data"


@pytest.mark.integration
class TestSessionSerialization:
    """Tests for session serialization."""
    
    def test_session_to_dict(self, temp_workspace):
        """Test session serialization to dictionary."""
        session = Session.create(
            project_id="test-project",
            directory=str(temp_workspace),
            title="Serialization Test",
        )
        session.add_message(Message.user("Test"))
        
        # Session should be serializable
        assert session.id is not None
        assert len(session.messages) == 1


@pytest.mark.integration
class TestSessionEdgeCases:
    """Edge case tests for sessions."""
    
    def test_empty_session(self, temp_workspace):
        """Test session with no messages."""
        session = Session.create(
            project_id="test",
            directory=str(temp_workspace),
        )
        
        assert len(session.messages) == 0
        api_messages = session.get_messages_for_api()
        assert len(api_messages) == 0
    
    def test_large_message_content(self, temp_workspace):
        """Test session with large message content."""
        session = Session.create(
            project_id="test",
            directory=str(temp_workspace),
        )
        
        # Create a large message
        large_text = "x" * 100000
        msg = Message.user(large_text)
        session.add_message(msg)
        
        assert len(session.messages) == 1
        assert len(session.messages[0].text_content) == 100000
    
    def test_unicode_message_content(self, temp_workspace):
        """Test session with unicode content."""
        session = Session.create(
            project_id="test",
            directory=str(temp_workspace),
        )
        
        unicode_text = "日本語テスト 🎉 émoji"
        msg = Message.user(unicode_text)
        session.add_message(msg)
        
        assert session.messages[0].text_content == unicode_text
    
    def test_special_characters_in_message(self, temp_workspace):
        """Test session with special characters."""
        session = Session.create(
            project_id="test",
            directory=str(temp_workspace),
        )
        
        special_text = "Line1\nLine2\tTabbed\r\nWindows\n\"Quotes\" 'and' \\backslash\\"
        msg = Message.user(special_text)
        session.add_message(msg)
        
        assert session.messages[0].text_content == special_text
