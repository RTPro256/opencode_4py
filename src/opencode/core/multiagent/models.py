"""
Data models for the multi-agent module.

Based on overstory (https://github.com/jayminwest/overstory)
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class AgentType(str, Enum):
    """Types of agents in the multi-agent system."""
    COORDINATOR = "coordinator"
    SUPERVISOR = "supervisor"
    LEAD = "lead"
    SCOUT = "scout"
    BUILDER = "builder"
    REVIEWER = "reviewer"
    MERGER = "merger"
    MONITOR = "monitor"


class AgentState(str, Enum):
    """Agent lifecycle states."""
    PENDING = "pending"
    READY = "ready"
    WORKING = "working"
    WAITING = "waiting"
    DONE = "done"
    FAILED = "failed"
    STOPPED = "stopped"


class RuntimeType(str, Enum):
    """Supported AI runtime adapters."""
    CLAUDE_CODE = "claude"
    PI = "pi"
    COPILOT = "copilot"
    CODEX = "codex"


class MessageType(str, Enum):
    """Types of inter-agent messages."""
    STATUS = "status"
    QUESTION = "question"
    ERROR = "error"
    WORKER_DONE = "worker_done"
    MERGE_READY = "merge_ready"
    ESCALATION = "escalation"
    NUDGE = "nudge"


class MessagePriority(str, Enum):
    """Message priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class Agent(BaseModel):
    """
    Represents an agent in the multi-agent system.
    """
    id: str = Field(..., description="Unique agent ID")
    name: str = Field(..., description="Agent name")
    agent_type: AgentType = Field(..., description="Type of agent")
    state: AgentState = Field(default=AgentState.PENDING, description="Current state")
    
    # Hierarchy
    parent_id: Optional[str] = Field(default=None, description="Parent agent ID")
    task_id: Optional[str] = Field(default=None, description="Associated task ID")
    
    # Runtime
    runtime: RuntimeType = Field(default=RuntimeType.CLAUDE_CODE, description="AI runtime")
    worktree_path: Optional[str] = Field(default=None, description="Git worktree path")
    branch: Optional[str] = Field(default=None, description="Worktree branch")
    
    # Capabilities
    capabilities: List[str] = Field(default_factory=list, description="Agent capabilities")
    file_scope: List[str] = Field(default_factory=list, description="Files agent can modify")
    
    # Tracking
    depth: int = Field(default=0, description="Depth in agent hierarchy")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = Field(default=None)
    finished_at: Optional[datetime] = Field(default=None)
    
    # Metrics
    tokens_used: int = Field(default=0)
    cost_estimate: float = Field(default=0.0)
    
    class Config:
        use_enum_values = True


class Message(BaseModel):
    """
    Represents a message between agents.
    """
    id: str = Field(..., description="Unique message ID")
    from_agent: str = Field(..., description="Sender agent ID")
    to_agent: str = Field(..., description="Recipient agent ID")
    subject: str = Field(..., description="Message subject")
    body: str = Field(..., description="Message body")
    message_type: MessageType = Field(default=MessageType.STATUS)
    priority: MessagePriority = Field(default=MessagePriority.NORMAL)
    
    # Threading
    thread_id: Optional[str] = Field(default=None)
    reply_to: Optional[str] = Field(default=None)
    
    # Context
    task_id: Optional[str] = Field(default=None)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    read_at: Optional[datetime] = Field(default=None)
    
    class Config:
        use_enum_values = True


class Worktree(BaseModel):
    """
    Represents a git worktree for agent isolation.
    """
    path: str = Field(..., description="Worktree path")
    branch: str = Field(..., description="Worktree branch")
    agent_id: str = Field(..., description="Associated agent ID")
    
    # Status
    is_clean: bool = Field(default=True)
    last_commit: Optional[str] = Field(default=None)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TaskGroup(BaseModel):
    """
    Represents a group of related tasks.
    """
    id: str = Field(..., description="Unique group ID")
    name: str = Field(..., description="Group name")
    description: str = Field(default="")
    
    # Members
    task_ids: List[str] = Field(default_factory=list)
    agent_ids: List[str] = Field(default_factory=list)
    
    # Status
    is_complete: bool = Field(default=False)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)


class OrchestrationRun(BaseModel):
    """
    Represents a single orchestration run.
    """
    id: str = Field(..., description="Unique run ID")
    name: str = Field(..., description="Run name")
    description: str = Field(default="")
    
    # Agents
    agent_ids: List[str] = Field(default_factory=list)
    
    # Status
    is_active: bool = Field(default=True)
    is_complete: bool = Field(default=False)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
