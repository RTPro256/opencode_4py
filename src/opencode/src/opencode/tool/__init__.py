"""
Tool package for agent tools.

This package provides tools that the AI agent can use to interact
with the environment, including file operations, command execution,
and web access.
"""

from opencode.tool.base import (
    PermissionLevel,
    Tool,
    ToolRegistry,
    ToolResult,
    get_registry,
    get_tool,
    register_tool,
)

# Core tools
from opencode.tool.bash import BashTool
from opencode.tool.file_tools import EditTool, GlobTool, GrepTool, ReadTool, WriteTool
from opencode.tool.lsp import LSPTool

# Extended tools
from opencode.tool.apply_patch import ApplyPatchTool
from opencode.tool.batch import BatchTool
from opencode.tool.codesearch import CodeSearchTool
from opencode.tool.git import GitTool
from opencode.tool.multiedit import MultiEditTool
from opencode.tool.plan import PlanTool
from opencode.tool.question import QuestionTool
from opencode.tool.skill import SkillTool
from opencode.tool.task import TaskTool
from opencode.tool.todo import TodoReadTool, TodoWriteTool
from opencode.tool.webfetch import WebFetchTool
from opencode.tool.websearch import WebSearchTool

__all__ = [
    # Base classes
    "PermissionLevel",
    "Tool",
    "ToolRegistry",
    "ToolResult",
    # Registry functions
    "get_registry",
    "get_tool",
    "register_tool",
    # Core tools
    "BashTool",
    "EditTool",
    "GlobTool",
    "GrepTool",
    "LSPTool",
    "ReadTool",
    "WriteTool",
    # Extended tools
    "ApplyPatchTool",
    "BatchTool",
    "CodeSearchTool",
    "GitTool",
    "MultiEditTool",
    "PlanTool",
    "QuestionTool",
    "SkillTool",
    "TaskTool",
    "TodoReadTool",
    "TodoWriteTool",
    "WebFetchTool",
    "WebSearchTool",
]
