"""
Data models for the memory module.

Based on beads (https://github.com/steveyegge/beads)
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task status enumeration."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"


class RelationshipType(str, Enum):
    """Types of relationships between tasks."""
    BLOCKS = "blocks"
    RELATES_TO = "relates_to"
    PARENT = "parent"
    DUPLICATES = "duplicates"
    SUPERSEDES = "supersedes"
    REPLIES_TO = "replies_to"


class Task(BaseModel):
    """
    Represents a task in the memory graph.
    
    Uses hash-based IDs to prevent merge collisions in multi-agent workflows.
    """
    id: str = Field(..., description="Unique hash-based task ID (e.g., 'bd-a1b2')")
    title: str = Field(..., description="Task title")
    description: str = Field(default="", description="Task description")
    status: TaskStatus = Field(default=TaskStatus.OPEN, description="Task status")
    priority: int = Field(default=2, ge=0, le=4, description="Priority (0=P0 highest, 4=P4 lowest)")
    assignee: Optional[str] = Field(default=None, description="Assigned agent/user")
    parent_id: Optional[str] = Field(default=None, description="Parent task ID for hierarchical tasks")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = Field(default=None, description="When task was closed")
    
    # Metadata
    labels: list[str] = Field(default_factory=list)
    summary: Optional[str] = Field(default=None, description="Compacted summary for long tasks")
    
    class Config:
        use_enum_values = True


class TaskRelationship(BaseModel):
    """Represents a relationship between two tasks."""
    id: str = Field(..., description="Unique relationship ID")
    source_id: str = Field(..., description="Source task ID")
    target_id: str = Field(..., description="Target task ID")
    relationship_type: RelationshipType = Field(..., description="Type of relationship")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True


class Message(BaseModel):
    """
    Represents a message in the task system.
    
    Messages provide communication between agents about tasks.
    """
    id: str = Field(..., description="Unique message ID")
    task_id: str = Field(..., description="Associated task ID")
    author: str = Field(..., description="Message author")
    content: str = Field(..., description="Message content")
    message_type: str = Field(default="comment", description="Message type (comment, status, error)")
    priority: str = Field(default="normal", description="Message priority (normal, high)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Threading
    reply_to: Optional[str] = Field(default=None, description="Parent message ID for threading")


class AuditEntry(BaseModel):
    """Represents an audit trail entry for task changes."""
    id: str = Field(..., description="Unique audit entry ID")
    task_id: str = Field(..., description="Task ID")
    action: str = Field(..., description="Action performed (created, updated, closed, etc.)")
    actor: str = Field(..., description="Who performed the action")
    details: str = Field(default="", description="Action details")
    created_at: datetime = Field(default_factory=datetime.utcnow)
