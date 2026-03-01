"""
Memory Module - Structured memory management for opencode_4py.

This module provides persistent, structured memory for coding agents through
a dependency-aware graph backed by SQLite (with optional Dolt support).

Based on beads (https://github.com/steveyegge/beads)

Key Features:
- Task dependency graph with zero-conflict hash IDs
- Version-controlled memory (optional Dolt backend)
- Memory compaction for long-term context optimization
- Graph links (relates_to, duplicates, supersedes, replies_to)
- Hierarchical task structure (Epic → Task → Sub-task)
"""

from .models import Task, TaskStatus, Message, RelationshipType
from .ids import generate_task_id, parse_task_id
from .graph import MemoryGraph
from .store import MemoryStore
from .config import MemoryConfig

__all__ = [
    "Task",
    "TaskStatus", 
    "Message",
    "RelationshipType",
    "generate_task_id",
    "parse_task_id",
    "MemoryGraph",
    "MemoryStore",
    "MemoryConfig",
]
