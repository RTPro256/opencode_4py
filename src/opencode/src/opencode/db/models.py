"""
Database models for OpenCode.

SQLAlchemy 2.0 async models for session, message, and file persistence.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""
    
    pass


class MessageRole(str, PyEnum):
    """Message role enum."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class MessageStatus(str, PyEnum):
    """Message status enum."""
    PENDING = "pending"
    STREAMING = "streaming"
    COMPLETE = "complete"
    ERROR = "error"


class Session(Base):
    """
    A conversation session.
    
    Represents a single conversation with the AI, containing
    multiple messages and associated metadata.
    """
    
    __tablename__ = "sessions"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_path: Mapped[str] = mapped_column(String(1024), index=True)
    provider: Mapped[str] = mapped_column(String(64))
    model: Mapped[str] = mapped_column(String(128))
    title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    
    # Relationships
    messages: Mapped[list[Message]] = relationship(
        "Message",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )
    files: Mapped[list[File]] = relationship(
        "File",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"Session(id={self.id!r}, title={self.title!r})"


class Message(Base):
    """
    A message in a conversation.
    
    Represents a single message from either the user or the AI,
    including content, role, and metadata.
    """
    
    __tablename__ = "messages"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        index=True,
    )
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole))
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[MessageStatus] = mapped_column(
        Enum(MessageStatus),
        default=MessageStatus.COMPLETE,
    )
    model: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    provider: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    tokens_input: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tokens_output: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cost: Mapped[Optional[float]] = mapped_column(nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    
    # Relationships
    session: Mapped[Session] = relationship("Session", back_populates="messages")
    tool_executions: Mapped[list[ToolExecution]] = relationship(
        "ToolExecution",
        back_populates="message",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"Message(id={self.id!r}, role={self.role!r})"


class File(Base):
    """
    A file associated with a session.
    
    Tracks files that have been read, modified, or created
    during a conversation.
    """
    
    __tablename__ = "files"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        index=True,
    )
    path: Mapped[str] = mapped_column(String(2048), index=True)
    operation: Mapped[str] = mapped_column(String(16))  # read, write, edit
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    
    # Relationships
    session: Mapped[Session] = relationship("Session", back_populates="files")
    
    def __repr__(self) -> str:
        return f"File(id={self.id!r}, path={self.path!r})"


class ToolExecution(Base):
    """
    A tool execution record.
    
    Tracks tool calls made by the AI, including parameters,
    results, and timing information.
    """
    
    __tablename__ = "tool_executions"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    message_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("messages.id", ondelete="CASCADE"),
        index=True,
    )
    tool_name: Mapped[str] = mapped_column(String(128), index=True)
    tool_call_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    parameters: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    permission_granted: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    
    # Relationships
    message: Mapped[Message] = relationship("Message", back_populates="tool_executions")
    
    def __repr__(self) -> str:
        return f"ToolExecution(id={self.id!r}, tool={self.tool_name!r})"


class Setting(Base):
    """
    Application settings.
    
    Stores user preferences and configuration in the database.
    """
    
    __tablename__ = "settings"
    
    key: Mapped[str] = mapped_column(String(256), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    
    def __repr__(self) -> str:
        return f"Setting(key={self.key!r})"


class APIKey(Base):
    """
    Stored API keys (encrypted).
    
    Securely stores API keys for various providers.
    """
    
    __tablename__ = "api_keys"
    
    provider: Mapped[str] = mapped_column(String(64), primary_key=True)
    key_encrypted: Mapped[str] = mapped_column(Text)
    key_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    
    def __repr__(self) -> str:
        return f"APIKey(provider={self.provider!r})"
