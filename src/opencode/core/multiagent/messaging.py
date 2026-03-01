"""
Inter-agent messaging system.

Based on overstory (https://github.com/jayminwest/overstory)

SQLite-based messaging with ~1-5ms per query target.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import uuid
import json

from .models import Message, MessageType, MessagePriority


class MessageBus:
    """
    SQLite-based message bus for inter-agent communication.
    
    Provides low-latency messaging between agents with support for:
    - Direct messages
    - Broadcasts
    - Message threading
    - Priority handling
    """
    
    def __init__(self, db_path: str = ".overstory/mail.db"):
        """
        Initialize the message bus.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self._ensure_db_directory()
        self.conn = sqlite3.connect(db_path, timeout=30.0)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()
    
    def _ensure_db_directory(self):
        """Create database directory if it doesn't exist."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    def _init_schema(self):
        """Initialize database schema."""
        cursor = self.conn.cursor()
        
        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                from_agent TEXT NOT NULL,
                to_agent TEXT NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                message_type TEXT DEFAULT 'status',
                priority TEXT DEFAULT 'normal',
                thread_id TEXT,
                reply_to TEXT,
                task_id TEXT,
                created_at TEXT NOT NULL,
                read_at TEXT
            )
        """)
        
        # Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_to ON messages(to_agent)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_from ON messages(from_agent)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_thread ON messages(thread_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_type ON messages(message_type)")
        
        self.conn.commit()
    
    def send(
        self,
        from_agent: str,
        to_agent: str,
        subject: str,
        body: str,
        message_type: MessageType = MessageType.STATUS,
        priority: MessagePriority = MessagePriority.NORMAL,
        task_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> Message:
        """
        Send a message to an agent.
        
        Args:
            from_agent: Sender agent ID
            to_agent: Recipient agent ID
            subject: Message subject
            body: Message body
            message_type: Type of message
            priority: Message priority
            task_id: Associated task ID
            thread_id: Thread ID for grouping
            reply_to: Message being replied to
        
        Returns:
            The created message
        """
        cursor = self.conn.cursor()
        
        message_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        # Generate thread ID if not provided
        if thread_id is None and (reply_to is not None or message_type in [MessageType.QUESTION, MessageType.ERROR]):
            thread_id = message_id
        
        cursor.execute("""
            INSERT INTO messages 
            (id, from_agent, to_agent, subject, body, message_type, priority, 
             thread_id, reply_to, task_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            message_id,
            from_agent,
            to_agent,
            subject,
            body,
            message_type.value,
            priority.value,
            thread_id,
            reply_to,
            task_id,
            now,
        ))
        
        self.conn.commit()
        
        return Message(
            id=message_id,
            from_agent=from_agent,
            to_agent=to_agent,
            subject=subject,
            body=body,
            message_type=message_type,
            priority=priority,
            thread_id=thread_id,
            reply_to=reply_to,
            task_id=task_id,
            created_at=datetime.fromisoformat(now),
        )
    
    def receive(self, agent_id: str, unread_only: bool = True) -> List[Message]:
        """
        Get messages for an agent.
        
        Args:
            agent_id: Recipient agent ID
            unread_only: Only return unread messages
        
        Returns:
            List of messages
        """
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM messages WHERE to_agent = ?"
        params = [agent_id]
        
        if unread_only:
            query += " AND read_at IS NULL"
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        
        return [self._row_to_message(row) for row in cursor.fetchall()]
    
    def mark_read(self, message_id: str):
        """Mark a message as read."""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE messages SET read_at = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), message_id)
        )
        self.conn.commit()
    
    def get_thread(self, thread_id: str) -> List[Message]:
        """Get all messages in a thread."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM messages WHERE thread_id = ? ORDER BY created_at ASC",
            (thread_id,)
        )
        return [self._row_to_message(row) for row in cursor.fetchall()]
    
    def get_unread_count(self, agent_id: str) -> int:
        """Get count of unread messages for an agent."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM messages WHERE to_agent = ? AND read_at IS NULL",
            (agent_id,)
        )
        return cursor.fetchone()[0]
    
    def delete_message(self, message_id: str):
        """Delete a message."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM messages WHERE id = ?", (message_id,))
        self.conn.commit()
    
    def close(self):
        """Close the database connection."""
        self.conn.close()
    
    def _row_to_message(self, row: sqlite3.Row) -> Message:
        """Convert a database row to a Message object."""
        return Message(
            id=row["id"],
            from_agent=row["from_agent"],
            to_agent=row["to_agent"],
            subject=row["subject"],
            body=row["body"],
            message_type=MessageType(row["message_type"]),
            priority=MessagePriority(row["priority"]),
            thread_id=row["thread_id"],
            reply_to=row["reply_to"],
            task_id=row["task_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            read_at=datetime.fromisoformat(row["read_at"]) if row["read_at"] else None,
        )


# Convenience functions for common message patterns

def send_status(from_agent: str, to_agent: str, subject: str, body: str, task_id: Optional[str] = None):
    """Send a status update message."""
    bus = MessageBus()
    bus.send(from_agent, to_agent, subject, body, MessageType.STATUS, task_id=task_id)


def send_question(from_agent: str, to_agent: str, subject: str, body: str, task_id: Optional[str] = None):
    """Send a question message."""
    bus = MessageBus()
    bus.send(from_agent, to_agent, subject, body, MessageType.QUESTION, MessagePriority.NORMAL, task_id=task_id)


def send_error(from_agent: str, to_agent: str, subject: str, body: str, task_id: Optional[str] = None):
    """Send an error message (high priority)."""
    bus = MessageBus()
    bus.send(from_agent, to_agent, subject, body, MessageType.ERROR, MessagePriority.HIGH, task_id=task_id)


def send_done(from_agent: str, to_agent: str, subject: str, body: str, task_id: Optional[str] = None):
    """Send a worker done message."""
    bus = MessageBus()
    bus.send(from_agent, to_agent, subject, body, MessageType.WORKER_DONE, task_id=task_id)


def send_merge_ready(from_agent: str, to_agent: str, subject: str, body: str, task_id: Optional[str] = None):
    """Send a merge ready message."""
    bus = MessageBus()
    bus.send(from_agent, to_agent, subject, body, MessageType.MERGE_READY, task_id=task_id)
