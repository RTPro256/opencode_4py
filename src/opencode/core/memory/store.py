"""
SQLite-backed storage for the memory module.

Based on beads (https://github.com/steveyegge/beads)
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import json

from .models import Task, TaskStatus, Message, TaskRelationship, AuditEntry, RelationshipType


class MemoryStore:
    """
    SQLite-backed storage for tasks and relationships.
    
    This is the default storage backend. Optionally, Dolt can be used
    for version-controlled SQL database with cell-level merge.
    """
    
    def __init__(self, db_path: str = ".beads/memory.db"):
        """
        Initialize the memory store.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_db_directory()
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def _ensure_db_directory(self):
        """Create database directory if it doesn't exist."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    def _init_schema(self):
        """Initialize database schema."""
        cursor = self.conn.cursor()
        
        # Tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                status TEXT DEFAULT 'open',
                priority INTEGER DEFAULT 2,
                assignee TEXT,
                parent_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                closed_at TEXT,
                labels TEXT DEFAULT '[]',
                summary TEXT
            )
        """)
        
        # Relationships table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (source_id) REFERENCES tasks(id),
                FOREIGN KEY (target_id) REFERENCES tasks(id)
            )
        """)
        
        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                author TEXT NOT NULL,
                content TEXT NOT NULL,
                message_type TEXT DEFAULT 'comment',
                priority TEXT DEFAULT 'normal',
                created_at TEXT NOT NULL,
                reply_to TEXT,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )
        """)
        
        # Audit trail table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                action TEXT NOT NULL,
                actor TEXT NOT NULL,
                details TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )
        """)
        
        # Indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_parent ON tasks(parent_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(source_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships(target_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_task ON messages(task_id)")
        
        self.conn.commit()
    
    def close(self):
        """Close the database connection."""
        self.conn.close()
    
    # Task operations
    
    def create_task(self, task: Task, actor: str = "system") -> Task:
        """Create a new task."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO tasks (id, title, description, status, priority, assignee, 
                            parent_id, created_at, updated_at, closed_at, labels, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task.id,
            task.title,
            task.description,
            task.status.value,
            task.priority,
            task.assignee,
            task.parent_id,
            task.created_at.isoformat(),
            task.updated_at.isoformat(),
            task.closed_at.isoformat() if task.closed_at else None,
            json.dumps(task.labels),
            task.summary,
        ))
        
        # Add audit entry
        self._add_audit(task.id, "created", actor, f"Task created: {task.title}")
        self.conn.commit()
        
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        return self._row_to_task(row)
    
    def update_task(self, task: Task, actor: str = "system") -> Task:
        """Update an existing task."""
        cursor = self.conn.cursor()
        task.updated_at = datetime.utcnow()
        
        cursor.execute("""
            UPDATE tasks SET 
                title = ?, description = ?, status = ?, priority = ?,
                assignee = ?, parent_id = ?, updated_at = ?, closed_at = ?,
                labels = ?, summary = ?
            WHERE id = ?
        """, (
            task.title,
            task.description,
            task.status.value,
            task.priority,
            task.assignee,
            task.parent_id,
            task.updated_at.isoformat(),
            task.closed_at.isoformat() if task.closed_at else None,
            json.dumps(task.labels),
            task.summary,
            task.id,
        ))
        
        # Add audit entry
        self._add_audit(task.id, "updated", actor, "Task updated")
        self.conn.commit()
        
        return task
    
    def delete_task(self, task_id: str, actor: str = "system") -> bool:
        """Delete a task."""
        cursor = self.conn.cursor()
        
        # Delete related data first
        cursor.execute("DELETE FROM relationships WHERE source_id = ? OR target_id = ?", (task_id, task_id))
        cursor.execute("DELETE FROM messages WHERE task_id = ?", (task_id,))
        cursor.execute("DELETE FROM audit WHERE task_id = ?", (task_id,))
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        
        self.conn.commit()
        return True
    
    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        priority: Optional[int] = None,
        assignee: Optional[str] = None,
        parent_id: Optional[str] = None,
    ) -> List[Task]:
        """List tasks with optional filters."""
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status.value)
        if priority is not None:
            query += " AND priority = ?"
            params.append(priority)
        if assignee:
            query += " AND assignee = ?"
            params.append(assignee)
        if parent_id is not None:
            query += " AND parent_id = ?"
            params.append(parent_id)
        
        cursor.execute(query, params)
        
        return [self._row_to_task(row) for row in cursor.fetchall()]
    
    def get_ready_tasks(self) -> List[Task]:
        """
        Get tasks with no open blockers.
        
        A task is ready if all tasks that block it are closed.
        """
        cursor = self.conn.cursor()
        
        # Find tasks that have blocking relationships
        cursor.execute("""
            SELECT DISTINCT t.* FROM tasks t
            WHERE t.status = 'open'
            AND NOT EXISTS (
                SELECT 1 FROM relationships r
                WHERE r.source_id = t.id
                AND r.relationship_type = 'blocks'
                AND r.target_id IN (
                    SELECT id FROM tasks WHERE status != 'closed'
                )
            )
            ORDER BY t.priority ASC, t.created_at ASC
        """)
        
        return [self._row_to_task(row) for row in cursor.fetchall()]
    
    # Relationship operations
    
    def add_relationship(self, rel: TaskRelationship) -> TaskRelationship:
        """Add a relationship between tasks."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO relationships (id, source_id, target_id, relationship_type, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            rel.id,
            rel.source_id,
            rel.target_id,
            rel.relationship_type.value if hasattr(rel.relationship_type, "value") else rel.relationship_type,
            rel.created_at.isoformat(),
        ))
        self.conn.commit()
        return rel
    
    def get_relationships(self, task_id: str) -> List[TaskRelationship]:
        """Get all relationships for a task."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM relationships 
            WHERE source_id = ? OR target_id = ?
        """, (task_id, task_id))
        
        return [self._row_to_relationship(row) for row in cursor.fetchall()]
    
    def remove_relationship(self, rel_id: str) -> bool:
        """Remove a relationship."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM relationships WHERE id = ?", (rel_id,))
        self.conn.commit()
        return True
    
    # Message operations
    
    def add_message(self, message: Message) -> Message:
        """Add a message to a task."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO messages (id, task_id, author, content, message_type, priority, created_at, reply_to)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            message.id,
            message.task_id,
            message.author,
            message.content,
            message.message_type,
            message.priority,
            message.created_at.isoformat(),
            message.reply_to,
        ))
        self.conn.commit()
        return message
    
    def get_messages(self, task_id: str) -> List[Message]:
        """Get all messages for a task."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM messages WHERE task_id = ? ORDER BY created_at ASC", (task_id,))
        
        return [self._row_to_message(row) for row in cursor.fetchall()]
    
    # Audit operations
    
    def _add_audit(self, task_id: str, action: str, actor: str, details: str):
        """Add an audit entry."""
        import uuid
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO audit (id, task_id, action, actor, details, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            task_id,
            action,
            actor,
            details,
            datetime.utcnow().isoformat(),
        ))
    
    def get_audit_trail(self, task_id: str) -> List[AuditEntry]:
        """Get audit trail for a task."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM audit WHERE task_id = ? ORDER BY created_at DESC", (task_id,))
        
        return [self._row_to_audit(row) for row in cursor.fetchall()]
    
    # Helper methods
    
    def _row_to_task(self, row: sqlite3.Row) -> Task:
        """Convert a database row to a Task object."""
        return Task(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            status=TaskStatus(row["status"]),
            priority=row["priority"],
            assignee=row["assignee"],
            parent_id=row["parent_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            closed_at=datetime.fromisoformat(row["closed_at"]) if row["closed_at"] else None,
            labels=json.loads(row["labels"]) if row["labels"] else [],
            summary=row["summary"],
        )
    
    def _row_to_relationship(self, row: sqlite3.Row) -> TaskRelationship:
        """Convert a database row to a TaskRelationship object."""
        return TaskRelationship(
            id=row["id"],
            source_id=row["source_id"],
            target_id=row["target_id"],
            relationship_type=RelationshipType(row["relationship_type"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )
    
    def _row_to_message(self, row: sqlite3.Row) -> Message:
        """Convert a database row to a Message object."""
        return Message(
            id=row["id"],
            task_id=row["task_id"],
            author=row["author"],
            content=row["content"],
            message_type=row["message_type"],
            priority=row["priority"],
            created_at=datetime.fromisoformat(row["created_at"]),
            reply_to=row["reply_to"],
        )
    
    def _row_to_audit(self, row: sqlite3.Row) -> AuditEntry:
        """Convert a database row to an AuditEntry object."""
        return AuditEntry(
            id=row["id"],
            task_id=row["task_id"],
            action=row["action"],
            actor=row["actor"],
            details=row["details"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
