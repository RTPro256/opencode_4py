"""
Quick commands for the TUI.

Provides commands like /index, /plans, /docs, /files, /tools, /agents
to quickly display project information.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional
import os


class QuickCommand:
    """A quick command that can be executed in the TUI."""
    
    def __init__(
        self,
        name: str,
        description: str,
        aliases: list[str] = None,
    ):
        self.name = name
        self.description = description
        self.aliases = aliases or []
    
    def get_usage(self) -> str:
        """Get usage string."""
        aliases = ", ".join(f"/{a}" for a in self.aliases) if self.aliases else ""
        return f"/{self.name} {aliases}".strip()


# Built-in quick commands
QUICK_COMMANDS = [
    QuickCommand("help", "Show all quick commands", ["?", "commands", "cmds"]),
    QuickCommand("index", "Show PROJECT_INDEX.md summary"),
    QuickCommand("plans", "Show PLAN_INDEX.md summary"),
    QuickCommand("docs", "Show DOCS_INDEX.md summary"),
    QuickCommand("files", "Show all Python files with summaries"),
    QuickCommand("tools", "Show all available tools"),
    QuickCommand("agents", "Show all agents"),
    QuickCommand("mode", "Show/change current mode"),
    QuickCommand("status", "Show system status"),
    QuickCommand("clear", "Clear the chat"),
    QuickCommand("theme", "Toggle theme (dark/light/catppuccin/nord)"),
]


def get_command(name: str) -> Optional[QuickCommand]:
    """Get a command by name or alias."""
    name = name.lstrip("/").lower()
    for cmd in QUICK_COMMANDS:
        if cmd.name.lower() == name or name in [a.lower() for a in cmd.aliases]:
            return cmd
    return None


def get_all_commands() -> list[QuickCommand]:
    """Get all available commands."""
    return QUICK_COMMANDS


# Project root - will be set dynamically
_project_root: Optional[Path] = None


def set_project_root(root: Path) -> None:
    """Set the project root directory."""
    global _project_root
    _project_root = root


def get_project_root() -> Optional[Path]:
    """Get the project root directory."""
    return _project_root


# Command implementations

async def execute_index_command() -> str:
    """Execute /index command - show PROJECT_INDEX.md."""
    root = get_project_root()
    if not root:
        return "Error: Project root not set"
    
    index_file = root / "PROJECT_INDEX.md"
    if not index_file.exists():
        return f"Error: PROJECT_INDEX.md not found at {index_file}"
    
    content = index_file.read_text(encoding="utf-8")
    
    # Return first 100 lines with header
    lines = content.split("\n")[:100]
    result = ["## 📁 PROJECT_INDEX.md\n"]
    result.extend(lines)
    
    if len(content.split("\n")) > 100:
        result.append(f"\n... [truncated, full file at {index_file}]")
    
    return "\n".join(result)


async def execute_plans_command() -> str:
    """Execute /plans command - show PLAN_INDEX.md."""
    root = get_project_root()
    if not root:
        return "Error: Project root not set"
    
    index_file = root / "plans" / "PLAN_INDEX.md"
    if not index_file.exists():
        return f"Error: PLAN_INDEX.md not found at {index_file}"
    
    content = index_file.read_text(encoding="utf-8")
    
    # Return first 100 lines with header
    lines = content.split("\n")[:100]
    result = ["## 📋 PLAN_INDEX.md\n"]
    result.extend(lines)
    
    if len(content.split("\n")) > 100:
        result.append(f"\n... [truncated, full file at {index_file}]")
    
    return "\n".join(result)


async def execute_docs_command() -> str:
    """Execute /docs command - show DOCS_INDEX.md."""
    root = get_project_root()
    if not root:
        return "Error: Project root not set"
    
    index_file = root / "docs" / "DOCS_INDEX.md"
    if not index_file.exists():
        return f"Error: DOCS_INDEX.md not found at {index_file}"
    
    content = index_file.read_text(encoding="utf-8")
    
    # Return first 100 lines with header
    lines = content.split("\n")[:100]
    result = ["## 📚 DOCS_INDEX.md\n"]
    result.extend(lines)
    
    if len(content.split("\n")) > 100:
        result.append(f"\n... [truncated, full file at {index_file}]")
    
    return "\n".join(result)


async def execute_files_command() -> str:
    """Execute /files command - show all Python files with summaries."""
    root = get_project_root()
    if not root:
        return "Error: Project root not set"
    
    result = ["## 📄 Python Files\n"]
    result.append("")
    
    # Find all Python files in src/
    src_dir = root / "src"
    if not src_dir.exists():
        return "Error: src/ directory not found"
    
    py_files = []
    for py_file in src_dir.rglob("*.py"):
        if ".venv" in str(py_file) or "venv" in str(py_file):
            continue
        rel_path = py_file.relative_to(root)
        
        # Try to get first docstring as summary
        summary = _get_file_summary(py_file)
        
        py_files.append((rel_path, summary))
    
    # Sort by path
    py_files.sort(key=lambda x: str(x[0]))
    
    # Display first 50 files
    for i, (path, summary) in enumerate(py_files[:50]):
        result.append(f"### {i+1}. {path}")
        result.append(f"   - Summary: {summary}")
        result.append("")
    
    total = len(py_files)
    if total > 50:
        result.append(f"... and {total - 50} more files")
    
    return "\n".join(result)


def _get_file_summary(py_file: Path) -> str:
    """Get a summary from a Python file (first docstring or first line)."""
    try:
        content = py_file.read_text(encoding="utf-8")
        lines = content.split("\n")
        
        # Skip shebang and encoding
        start = 0
        if lines and (lines[0].startswith("#!") or "encoding" in lines[0].lower()):
            start = 1
        
        # Find first docstring
        in_docstring = False
        docstring_lines = []
        
        for i in range(start, min(len(lines), 20)):
            line = lines[i].strip()
            
            if not in_docstring:
                if '"""' in line or "'''" in line:
                    if line.count('"""') >= 2 or line.count("'''") >= 2:
                        # Single line docstring
                        return line.strip('"""').strip("'''").strip()[:80]
                    in_docstring = True
                    delimiter = '"""' if '"""' in line else "'''"
                    part = line.split(delimiter)[1] if delimiter in line else ""
                    if part:
                        docstring_lines.append(part)
            else:
                delimiter = '"""' if '"""' in line else "'''"
                if delimiter in line:
                    in_docstring = False
                    break
                docstring_lines.append(line)
        
        if docstring_lines:
            summary = " ".join(docstring_lines).strip()
            return summary[:80] if len(summary) > 80 else summary
        
        # Fall back to first non-empty line
        for line in lines[start:]:
            if line.strip() and not line.strip().startswith("#"):
                return line.strip()[:80]
        
        return "No description"
    
    except Exception:
        return "Error reading file"


async def execute_tools_command() -> str:
    """Execute /tools command - show all available tools."""
    root = get_project_root()
    if not root:
        return "Error: Project root not set"
    
    result = ["## 🔧 Available Tools\n"]
    result.append("")
    
    # Find tool definitions in src/opencode/tool/
    tool_dir = root / "src" / "opencode" / "tool"
    
    # Fallback to core/tools if primary path doesn't exist
    if not tool_dir.exists():
        tool_dir = root / "src" / "opencode" / "core" / "tools"
    
    if not tool_dir.exists():
        return "Error: tool/ directory not found"
    
    tools = []
    for tool_file in tool_dir.glob("*.py"):
        if tool_file.name.startswith("_"):
            continue
        
        name = tool_file.stem
        description = _get_file_summary(tool_file)
        
        tools.append((name, description))
    
    # Sort by name
    tools.sort()
    
    for i, (name, desc) in enumerate(tools):
        result.append(f"### {i+1}. {name}")
        result.append(f"   - {desc}")
        result.append("")
    
    return "\n".join(result)


async def execute_agents_command() -> str:
    """Execute /agents command - show all agents."""
    root = get_project_root()
    if not root:
        return "Error: Project root not set"
    
    result = ["## 🤖 Agents\n"]
    result.append("")
    
    # Find agent definitions - look in core/modes/modes/ and core/orchestration
    agent_dirs = [
        root / "src" / "opencode" / "core" / "modes" / "modes",
        root / "src" / "opencode" / "core" / "orchestration",
    ]
    
    agents_found = []
    
    for agent_dir in agent_dirs:
        if not agent_dir.exists():
            continue
        
        for py_file in agent_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            
            name = py_file.stem
            description = _get_file_summary(py_file)
            
            agents_found.append((name, description))
    
    if not agents_found:
        result.append("No agents found")
    else:
        for i, (name, desc) in enumerate(agents_found):
            result.append(f"### {i+1}. {name}")
            result.append(f"   - {desc}")
            result.append("")
    
    return "\n".join(result)


async def execute_mode_command(mode: str = "") -> str:
    """
    Execute /mode command - show or change current mode.
    
    Args:
        mode: Optional mode name to switch to
    """
    from opencode.core.modes.manager import ModeManager
    
    manager = ModeManager()
    modes = manager.list_modes()
    current_mode = manager.get_current_mode_name()
    
    if not mode:
        # Show current mode and available modes
        result = ["## 🎯 Current Mode\n"]
        result.append(f"**Current:** {current_mode}\n")
        result.append("\n### Available Modes:\n")
        for m in modes:
            marker = "👉" if m == current_mode else "  "
            result.append(f"{marker} {m}")
        result.append("\nUse `/mode <name>` to switch (e.g., /mode code)")
        result.append("Or press Ctrl+Shift+M in TUI to cycle through modes")
        return "\n".join(result)
    
    # Try to switch mode
    mode_lower = mode.lower()
    for m in modes:
        if m.lower() == mode_lower:
            success = manager.set_mode(m)
            if success:
                return f"__MODE__{m}"
            return f"Failed to switch to mode: {m}"
    
    return f"Unknown mode: {mode}. Available: {', '.join(modes)}"


async def execute_help_command() -> str:
    """Execute /help command - show all quick commands."""
    result = ["## ⚡ Quick Commands\n"]
    result.append("")
    result.append("Use these commands in the chat input:")
    result.append("")
    
    for cmd in QUICK_COMMANDS:
        result.append(f"- `/{cmd.name}` - {cmd.description}")
        if cmd.aliases:
            for alias in cmd.aliases:
                result.append(f"  - Alias: /{alias}")
    
    result.append("")
    result.append("**Tip:** Commands start with `/` in the input field")
    
    return "\n".join(result)


async def execute_status_command() -> str:
    """Execute /status command - show system status."""
    return """## 📊 System Status

- **Status**: Ready
- **TUI**: OpenCode Terminal Interface
- **Theme**: Use /theme to change

Use /help for quick commands"""


async def execute_clear_command() -> str:
    """Execute /clear command - clear the chat."""
    return "__CLEAR__"


async def execute_theme_command(theme: str = "") -> str:
    """Execute /theme command - toggle theme."""
    themes = ["dark", "light", "catppuccin", "nord"]
    
    if not theme:
        return f"Current themes: {', '.join(themes)}. Use /theme <name> to switch"
    
    if theme.lower() not in themes:
        return f"Unknown theme: {theme}. Available: {', '.join(themes)}"
    
    return f"__THEME__{theme.lower()}"


async def execute_command(command: str) -> tuple[str, bool]:
    """
    Execute a quick command.
    
    Returns:
        tuple of (result, is_command) - result is the command output,
        is_command is True if this was a valid command
    """
    command = command.strip()
    
    if not command.startswith("/"):
        return "", False
    
    # Parse command and arguments
    parts = command[1:].split(maxsplit=1)
    cmd_name = parts[0]
    args = parts[1] if len(parts) > 1 else ""
    
    # Get command
    cmd = get_command(cmd_name)
    if not cmd:
        return f"Unknown command: /{cmd_name}. Use /help for available commands", True
    
    # Execute based on command name
    if cmd.name == "help":
        return await execute_help_command(), True
    elif cmd.name == "index":
        return await execute_index_command(), True
    elif cmd.name == "plans":
        return await execute_plans_command(), True
    elif cmd.name == "docs":
        return await execute_docs_command(), True
    elif cmd.name == "files":
        return await execute_files_command(), True
    elif cmd.name == "tools":
        return await execute_tools_command(), True
    elif cmd.name == "agents":
        return await execute_agents_command(), True
    elif cmd.name == "mode":
        return await execute_mode_command(args), True
    elif cmd.name == "status":
        return await execute_status_command(), True
    elif cmd.name == "clear":
        return await execute_clear_command(), True
    elif cmd.name == "theme":
        return await execute_theme_command(args), True
    
    return f"Command not implemented: {cmd.name}", True
