"""
Workflow Database Models

SQLAlchemy models for workflow persistence.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, Any, Dict

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    Boolean,
    Float,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class WorkflowBase(DeclarativeBase):
    """Base class for workflow models."""
    pass


class WorkflowStatus(str, PyEnum):
    """Workflow status enum."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class ExecutionStatus(str, PyEnum):
    """Execution status enum."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class Workflow(WorkflowBase):
    """
    A workflow definition.
    
    Represents a complete workflow with its graph structure,
    metadata, and configuration.
    """
    
    __tablename__ = "workflows"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(256))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(32), default="1.0.0")
    status: Mapped[WorkflowStatus] = mapped_column(
        Enum(WorkflowStatus),
        default=WorkflowStatus.DRAFT,
    )
    
    # Graph structure stored as JSON
    graph_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Variables and configuration
    variables: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Metadata
    author: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    tags: Mapped[Dict[str, Any]] = mapped_column(JSON, default=list)
    
    # Timestamps
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
    executions: Mapped[list[WorkflowExecution]] = relationship(
        "WorkflowExecution",
        back_populates="workflow",
        cascade="all, delete-orphan",
        order_by="WorkflowExecution.created_at.desc()",
    )
    
    def __repr__(self) -> str:
        return f"Workflow(id={self.id!r}, name={self.name!r})"


class WorkflowExecution(WorkflowBase):
    """
    A workflow execution record.
    
    Tracks the execution state and history of a workflow run.
    """
    
    __tablename__ = "workflow_executions"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workflow_id: Mapped[str] = mapped_column(String(36), ForeignKey("workflows.id"))
    
    status: Mapped[ExecutionStatus] = mapped_column(
        Enum(ExecutionStatus),
        default=ExecutionStatus.PENDING,
    )
    
    # Execution state
    current_layer: Mapped[int] = mapped_column(Integer, default=0)
    total_layers: Mapped[int] = mapped_column(Integer, default=0)
    variables: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Error information
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_traceback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    
    # Trigger information
    trigger_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    trigger_source: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    
    # Relationships
    workflow: Mapped[Workflow] = relationship("Workflow", back_populates="executions")
    node_executions: Mapped[list[NodeExecution]] = relationship(
        "NodeExecution",
        back_populates="execution",
        cascade="all, delete-orphan",
        order_by="NodeExecution.started_at",
    )
    
    def __repr__(self) -> str:
        return f"WorkflowExecution(id={self.id!r}, workflow_id={self.workflow_id!r}, status={self.status!r})"
    
    @property
    def duration_ms(self) -> Optional[float]:
        """Get execution duration in milliseconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() * 1000
        return None


class NodeExecution(WorkflowBase):
    """
    A node execution record.
    
    Tracks the execution state and results of a single node.
    """
    
    __tablename__ = "node_executions"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    execution_id: Mapped[str] = mapped_column(String(36), ForeignKey("workflow_executions.id"))
    
    node_id: Mapped[str] = mapped_column(String(36))
    node_type: Mapped[str] = mapped_column(String(128))
    
    status: Mapped[ExecutionStatus] = mapped_column(
        Enum(ExecutionStatus),
        default=ExecutionStatus.PENDING,
    )
    
    # Input/output data
    inputs: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    outputs: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Error information
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_traceback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Retry information
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    execution: Mapped[WorkflowExecution] = relationship(
        "WorkflowExecution",
        back_populates="node_executions",
    )
    
    def __repr__(self) -> str:
        return f"NodeExecution(id={self.id!r}, node_id={self.node_id!r}, status={self.status!r})"
    
    @property
    def duration_ms(self) -> Optional[float]:
        """Get execution duration in milliseconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() * 1000
        return None


class WorkflowTemplate(WorkflowBase):
    """
    A workflow template.
    
    Pre-defined workflow templates that can be used as starting points.
    """
    
    __tablename__ = "workflow_templates"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(256))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(64), default="general")
    
    # Template data
    graph_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    default_variables: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Metadata
    author: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    tags: Mapped[Dict[str, Any]] = mapped_column(JSON, default=list)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False)
    
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
        return f"WorkflowTemplate(id={self.id!r}, name={self.name!r})"
