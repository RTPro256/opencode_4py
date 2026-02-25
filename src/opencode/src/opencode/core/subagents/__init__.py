"""
Subagents System - File-based configuration for specialized AI assistants.

This module provides the foundation for the subagents feature by implementing
a file-based configuration system. It includes:

- Type definitions for file-based subagent configurations
- Validation system for configuration integrity
- Manager class for CRUD operations on subagent files
- Runtime execution with event system for UI integration

Storage locations:
- Project level: .opencode/subagents/*.md
- User level: ~/.opencode/subagents/*.md

Format: Markdown + YAML frontmatter
"""

from .types import (
    SubagentConfig,
    SubagentLevel,
    SubagentRuntimeConfig,
    ValidationResult,
    ListSubagentsOptions,
    CreateSubagentOptions,
    SubagentErrorCode,
    PromptConfig,
    ModelConfig,
    RunConfig,
    ToolConfig,
    SubagentTerminateMode,
)
from .errors import SubagentError
from .validator import SubagentValidator
from .manager import SubagentManager
from .builtin import BuiltinAgentRegistry
from .events import (
    SubAgentEventEmitter,
    SubAgentEventType,
    SubAgentEvent,
    SubAgentStartEvent,
    SubAgentRoundEvent,
    SubAgentStreamTextEvent,
    SubAgentUsageEvent,
    SubAgentToolCallEvent,
    SubAgentToolResultEvent,
    SubAgentFinishEvent,
    SubAgentErrorEvent,
    SubAgentApprovalRequestEvent,
)
from .statistics import SubagentStatsSummary, ToolUsageStats

__all__ = [
    # Types
    "SubagentConfig",
    "SubagentLevel",
    "SubagentRuntimeConfig",
    "ValidationResult",
    "ListSubagentsOptions",
    "CreateSubagentOptions",
    "SubagentErrorCode",
    "PromptConfig",
    "ModelConfig",
    "RunConfig",
    "ToolConfig",
    "SubagentTerminateMode",
    # Errors
    "SubagentError",
    # Components
    "SubagentValidator",
    "SubagentManager",
    "BuiltinAgentRegistry",
    # Events
    "SubAgentEventEmitter",
    "SubAgentEventType",
    "SubAgentEvent",
    "SubAgentStartEvent",
    "SubAgentRoundEvent",
    "SubAgentStreamTextEvent",
    "SubAgentUsageEvent",
    "SubAgentToolCallEvent",
    "SubAgentToolResultEvent",
    "SubAgentFinishEvent",
    "SubAgentErrorEvent",
    "SubAgentApprovalRequestEvent",
    # Statistics
    "SubagentStatsSummary",
    "ToolUsageStats",
]
