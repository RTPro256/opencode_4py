"""
Session management for OpenCode.

A session represents a conversation with an AI assistant, including
message history, tool calls, and metadata.
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, AsyncIterator, Optional
import logging

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MessageRole(str, Enum):
    """Message role types."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ToolCallStatus(str, Enum):
    """Status of a tool call."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class ToolCall:
    """Represents a tool/function call."""
    id: str
    name: str
    arguments: dict[str, Any]
    status: ToolCallStatus = ToolCallStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class ContentBlock:
    """A block of content in a message."""
    type: str  # "text", "tool_call", "tool_result", "image"
    text: Optional[str] = None
    tool_call: Optional[ToolCall] = None
    tool_call_id: Optional[str] = None
    image_url: Optional[str] = None
    image_data: Optional[bytes] = None


@dataclass
class Message:
    """A message in a conversation."""
    id: str
    role: MessageRole
    content: list[ContentBlock]
    created_at: datetime
    model: Optional[str] = None
    usage: Optional[dict[str, int]] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @property
    def text_content(self) -> str:
        """Get all text content from the message."""
        texts = [block.text for block in self.content if block.text]
        return "\n".join(texts)
    
    @classmethod
    def user(cls, text: str, **kwargs: Any) -> "Message":
        """Create a user message."""
        return cls(
            id=str(uuid.uuid4()),
            role=MessageRole.USER,
            content=[ContentBlock(type="text", text=text)],
            created_at=datetime.now(),
            **kwargs,
        )
    
    @classmethod
    def assistant(
        cls,
        content: list[ContentBlock],
        model: Optional[str] = None,
        usage: Optional[dict[str, int]] = None,
        **kwargs: Any,
    ) -> "Message":
        """Create an assistant message."""
        return cls(
            id=str(uuid.uuid4()),
            role=MessageRole.ASSISTANT,
            content=content,
            created_at=datetime.now(),
            model=model,
            usage=usage,
            **kwargs,
        )
    
    @classmethod
    def system(cls, text: str, **kwargs: Any) -> "Message":
        """Create a system message."""
        return cls(
            id=str(uuid.uuid4()),
            role=MessageRole.SYSTEM,
            content=[ContentBlock(type="text", text=text)],
            created_at=datetime.now(),
            **kwargs,
        )
    
    @classmethod
    def tool_result(
        cls,
        tool_call_id: str,
        result: str,
        error: Optional[str] = None,
        **kwargs: Any,
    ) -> "Message":
        """Create a tool result message."""
        return cls(
            id=str(uuid.uuid4()),
            role=MessageRole.TOOL,
            content=[ContentBlock(
                type="tool_result",
                text=result,
                tool_call_id=tool_call_id,
            )],
            created_at=datetime.now(),
            metadata={"error": error} if error else {},
            **kwargs,
        )


@dataclass
class SessionSummary:
    """Summary statistics for a session."""
    additions: int = 0
    deletions: int = 0
    files_changed: int = 0
    tool_calls: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0


@dataclass
class Session:
    """
    A conversation session with an AI assistant.
    
    Manages message history, tool calls, and session state.
    """
    id: str
    project_id: str
    title: str
    directory: str
    created_at: datetime
    updated_at: datetime
    messages: list[Message] = field(default_factory=list)
    model: Optional[str] = None
    agent: str = "build"
    parent_id: Optional[str] = None
    summary: Optional[SessionSummary] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    # Runtime state (not persisted)
    _is_running: bool = False
    _pending_tool_calls: dict[str, ToolCall] = field(default_factory=dict)
    
    # Project-specific index files to look for (in order of priority)
    # These are checked in order - first match wins for context
    PROJECT_INDEX_FILES = [
        # Project-specific indexes
        "COMFYUI_INDEX.md",
        "OPENCODE_4PY_README.md",
        "PROJECT_INDEX.md",
        # Generic indexes
        "INDEX.md",
        "README.md",
        ".claude/index.md",
        ".opencode/index.md",
    ]
    
    # Project root detection markers
    PROJECT_ROOT_MARKERS = [
        "ComfyUI_windows_portable",
        "opencode.toml",
        "pyproject.toml",
        "package.json",
        ".git",
    ]
    
    @classmethod
    def create(
        cls,
        project_id: str,
        directory: str,
        title: Optional[str] = None,
        model: Optional[str] = None,
        agent: str = "build",
    ) -> "Session":
        """Create a new session."""
        now = datetime.now()
        session = cls(
            id=str(uuid.uuid4()),
            project_id=project_id,
            title=title or f"New session - {now.isoformat()}",
            directory=directory,
            created_at=now,
            updated_at=now,
            model=model,
            agent=agent,
        )
        
        # Load project-specific self-knowledge into session
        session._load_project_context(directory)
        
        return session
    
    def _load_project_context(self, directory: str) -> None:
        """
        Load project-specific self-knowledge documents into session context.
        
        Looks for index files like COMFYUI_INDEX.md, PROJECT_INDEX.md, etc.
        in the project root and adds them as system messages for the AI to reference.
        
        This is generic - works for ANY project with index files, not just ComfyUI.
        """
        session_dir = Path(directory)
        
        # If directory doesn't exist, try to find project root
        if not session_dir.exists():
            session_dir = Path.cwd()
        
        # Detect project root by looking for common markers
        project_root = self._find_project_root(session_dir)
        
        if not project_root or not project_root.exists():
            logger.debug("No project root found for context loading")
            return
        
        context_parts = []
        found_files = []
        
        # Check each potential index file
        for index_file in self.PROJECT_INDEX_FILES:
            index_path = project_root / index_file
            if index_path.exists():
                try:
                    content = index_path.read_text(encoding='utf-8', errors='ignore')
                    # Get first 2000 chars to avoid overwhelming context
                    context_parts.append(f"\n\n=== {index_file} ===\n{content[:2000]}")
                    found_files.append(index_file)
                except Exception as e:
                    logger.warning(f"Failed to read {index_file}: {e}")
        
        if context_parts:
            context_text = (
                "Project Context - Reference these documents for project-specific information:\n"
                f"Found context files: {', '.join(found_files)}\n"
                + "\n".join(context_parts)
            )
            # Add as system message
            system_msg = Message.system(context_text)
            self.messages.append(system_msg)
            logger.info(f"Loaded project context from: {found_files}")
    
    def _find_project_root(self, start_path: Path) -> Optional[Path]:
        """
        Find the project root by looking for common project markers.
        
        Generic method that works for any project type.
        """
        # Check if starting path is the root
        for marker in self.PROJECT_ROOT_MARKERS:
            if (start_path / marker).exists():
                return start_path
        
        # Check parent directories (max 5 levels up)
        current = start_path
        for _ in range(5):
            for marker in self.PROJECT_ROOT_MARKERS:
                if (current / marker).exists():
                    return current
            parent = current.parent
            if parent == current:  # Reached root
                break
            current = parent
        
        # Fall back to starting path
        return start_path if start_path.exists() else None
    
    def add_message(self, message: Message) -> None:
        """Add a message to the session."""
        self.messages.append(message)
        self.updated_at = datetime.now()
    
    def get_messages_for_api(self) -> list[dict[str, Any]]:
        """
        Get messages formatted for API calls.
        
        Converts internal message format to provider-specific format.
        """
        api_messages = []
        
        for message in self.messages:
            if message.role == MessageRole.TOOL:
                # Tool results are handled differently
                for block in message.content:
                    if block.type == "tool_result":
                        api_messages.append({
                            "role": "tool",
                            "tool_call_id": block.tool_call_id,
                            "content": block.text,
                        })
            else:
                # Regular messages
                content = self._format_content_for_api(message.content)
                api_messages.append({
                    "role": message.role.value,
                    "content": content,
                })
        
        return api_messages
    
    def _format_content_for_api(self, content: list[ContentBlock]) -> Any:
        """Format content blocks for API."""
        if len(content) == 1 and content[0].type == "text":
            return content[0].text
        
        # Multiple blocks or non-text blocks
        formatted = []
        for block in content:
            if block.type == "text" and block.text:
                formatted.append({"type": "text", "text": block.text})
            elif block.type == "tool_call" and block.tool_call:
                formatted.append({
                    "type": "tool_use",
                    "id": block.tool_call.id,
                    "name": block.tool_call.name,
                    "input": block.tool_call.arguments,
                })
            elif block.type == "image":
                if block.image_url:
                    formatted.append({
                        "type": "image",
                        "source": {"type": "url", "url": block.image_url},
                    })
                elif block.image_data:
                    formatted.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": block.image_data,
                        },
                    })
        
        return formatted
    
    def get_token_count(self) -> int:
        """Get total token count for the session."""
        return sum(
            msg.usage.get("total_tokens", 0)
            for msg in self.messages
            if msg.usage
        )
    
    def compact(self) -> None:
        """
        Compact the session by summarizing old messages.
        
        This reduces context size while preserving important information.
        """
        # TODO: Implement compaction logic
        # For now, just keep the last N messages
        pass
    
    def to_dict(self) -> dict[str, Any]:
        """Convert session to dictionary for serialization."""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "title": self.title,
            "directory": self.directory,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "model": self.model,
            "agent": self.agent,
            "parent_id": self.parent_id,
            "messages": [self._message_to_dict(m) for m in self.messages],
            "summary": {
                "additions": self.summary.additions,
                "deletions": self.summary.deletions,
                "files_changed": self.summary.files_changed,
                "tool_calls": self.summary.tool_calls,
                "total_tokens": self.summary.total_tokens,
                "total_cost": self.summary.total_cost,
            } if self.summary else None,
            "metadata": self.metadata,
        }
    
    def _message_to_dict(self, message: Message) -> dict[str, Any]:
        """Convert a message to dictionary."""
        return {
            "id": message.id,
            "role": message.role.value,
            "content": [
                {
                    "type": block.type,
                    "text": block.text,
                    "tool_call_id": block.tool_call_id,
                }
                for block in message.content
            ],
            "created_at": message.created_at.isoformat(),
            "model": message.model,
            "usage": message.usage,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Session":
        """Create a session from a dictionary."""
        messages = [
            Message(
                id=m["id"],
                role=MessageRole(m["role"]),
                content=[
                    ContentBlock(
                        type=b["type"],
                        text=b.get("text"),
                        tool_call_id=b.get("tool_call_id"),
                    )
                    for b in m["content"]
                ],
                created_at=datetime.fromisoformat(m["created_at"]),
                model=m.get("model"),
                usage=m.get("usage"),
            )
            for m in data.get("messages", [])
        ]
        
        summary_data = data.get("summary")
        summary = SessionSummary(
            additions=summary_data.get("additions", 0),
            deletions=summary_data.get("deletions", 0),
            files_changed=summary_data.get("files_changed", 0),
            tool_calls=summary_data.get("tool_calls", 0),
            total_tokens=summary_data.get("total_tokens", 0),
            total_cost=summary_data.get("total_cost", 0.0),
        ) if summary_data else None
        
        return cls(
            id=data["id"],
            project_id=data["project_id"],
            title=data["title"],
            directory=data["directory"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            model=data.get("model"),
            agent=data.get("agent", "build"),
            parent_id=data.get("parent_id"),
            messages=messages,
            summary=summary,
            metadata=data.get("metadata", {}),
        )


class SessionManager:
    """Manages session persistence and retrieval."""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.sessions_dir = data_dir / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
    
    async def save(self, session: Session) -> None:
        """Save a session to disk.
        
        Filename format: session_{datetime}_{id}.json
        The datetime is from the session's created_at or updated_at field.
        """
        import json
        
        # Use session's created_at for datetime in filename
        # Format: session_YYYY-MM-DD_HH-MM-SS_{short_id}.json
        if session.created_at:
            dt_str = session.created_at.strftime("%Y-%m-%d_%H-%M-%S")
        else:
            dt_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        # Use first 8 chars of UUID for shorter ID
        short_id = session.id[:8] if len(session.id) > 8 else session.id
        filename = f"session_{dt_str}_{short_id}.json"
        session_file = self.sessions_dir / filename
        
        with open(session_file, "w") as f:
            json.dump(session.to_dict(), f, indent=2)
    
    async def load(self, session_id: str) -> Optional[Session]:
        """Load a session from disk.
        
        Searches for files matching the session ID (can be full UUID or short ID).
        """
        import json
        
        # Try exact match first (for backward compatibility)
        session_file = self.sessions_dir / f"{session_id}.json"
        if session_file.exists():
            with open(session_file) as f:
                data = json.load(f)
            return Session.from_dict(data)
        
        # Search for files containing the session ID (new format)
        for f in self.sessions_dir.glob("*.json"):
            if session_id in f.stem:
                with open(f) as fp:
                    data = json.load(fp)
                session = Session.from_dict(data)
                # Check if this is the right session
                if session.id == session_id or session.id.startswith(session_id):
                    return session
        
        return None
    
    async def list_sessions(
        self,
        project_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[Session]:
        """List all sessions, optionally filtered by project."""
        import json
        
        sessions = []
        for session_file in sorted(
            self.sessions_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        ):
            try:
                with open(session_file) as f:
                    data = json.load(f)
                session = Session.from_dict(data)
                if project_id is None or session.project_id == project_id:
                    sessions.append(session)
                    if len(sessions) >= limit:
                        break
            except Exception as e:
                logger.warning(f"Failed to load session from {session_file}: {e}")
                continue
        
        return sessions
    
    async def delete(self, session_id: str) -> bool:
        """Delete a session.
        
        Searches for files matching the session ID (can be full UUID or short ID).
        """
        # Try exact match first (for backward compatibility)
        session_file = self.sessions_dir / f"{session_id}.json"
        if session_file.exists():
            session_file.unlink()
            return True
        
        # Search for files containing the session ID (new format)
        for f in self.sessions_dir.glob("*.json"):
            if session_id in f.stem:
                # Verify it's the correct session by loading it
                import json
                with open(f) as fp:
                    data = json.load(fp)
                session = Session.from_dict(data)
                if session.id == session_id or session.id.startswith(session_id):
                    f.unlink()
                    return True
        
        return False
    
    async def create_session(
        self,
        title: Optional[str] = None,
        project_id: Optional[str] = None,
        directory: str = ".",
        model: Optional[str] = None,
    ) -> Session:
        """Create a new session."""
        session = Session(
            id=str(uuid.uuid4()),
            project_id=project_id or "default",
            title=title or "New Session",
            directory=directory,
            model=model,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            messages=[],
        )
        await self.save(session)
        return session
    
    async def get_messages(self, session_id: str) -> list[Message]:
        """Get messages for a session."""
        session = await self.load(session_id)
        return session.messages if session else []
    
    async def add_message(
        self,
        session_id: str,
        role: MessageRole,
        content: str,
        model: Optional[str] = None,
    ) -> Message:
        """Add a message to a session."""
        session = await self.load(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        message = Message(
            id=str(uuid.uuid4()),
            role=role,
            content=[ContentBlock(type="text", text=content)],
            created_at=datetime.now(),
            model=model,
        )
        
        session.messages.append(message)
        session.updated_at = datetime.now()
        await self.save(session)
        
        return message


# Import Path for type hints
from pathlib import Path
