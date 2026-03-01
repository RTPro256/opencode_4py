"""
Multi-Agent Module - Multi-agent orchestration for opencode_4py.

Based on overstory (https://github.com/jayminwest/overstory)

This module enables opencode_4py to spawn and coordinate multiple AI agents
for complex, long-horizon tasks through:
- Multi-agent coordination hierarchy
- Inter-agent messaging via SQLite
- Git worktree isolation
- Branch merging with conflict resolution
- Fleet monitoring via watchdog system
"""

from .models import AgentType, AgentState, Agent, Message, Worktree
from .coordinator import Coordinator
from .messaging import MessageBus
from .worktree import WorktreeManager
from .config import MultiAgentConfig

__all__ = [
    "AgentType",
    "AgentState",
    "Agent",
    "Message",
    "Worktree",
    "Coordinator",
    "MessageBus",
    "WorktreeManager",
    "MultiAgentConfig",
]
