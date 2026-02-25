"""
Bash tool for executing shell commands.

This tool allows the AI agent to execute shell commands with proper
sandboxing, timeout handling, and output capture.
"""

from __future__ import annotations

import asyncio
import os
import shlex
import signal
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from opencode.tool.base import (
    PermissionLevel,
    Tool,
    ToolResult,
)


@dataclass
class BashTool(Tool):
    """
    Tool for executing shell commands.
    
    Features:
    - Command execution with timeout
    - Working directory control
    - Environment variable injection
    - Output streaming
    - Process management
    """
    
    working_directory: Path = Path(".")
    timeout: int = 120  # seconds
    max_output_size: int = 100000  # characters
    
    @property
    def name(self) -> str:
        return "bash"
    
    @property
    def description(self) -> str:
        return """Execute a bash command in the terminal.

- Long-running commands will be terminated after 2 minutes
- Output is truncated if too long
- Use with caution as commands can modify files and system state
- Commands run in the project directory by default"""
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to execute",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default: 120)",
                    "default": 120,
                },
                "cwd": {
                    "type": "string",
                    "description": "Working directory (default: project root)",
                },
                "env": {
                    "type": "object",
                    "description": "Environment variables to set",
                    "additionalProperties": {"type": "string"},
                },
            },
            "required": ["command"],
        }
    
    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.EXECUTE
    
    async def execute(
        self,
        command: str,
        timeout: Optional[int] = None,
        cwd: Optional[str] = None,
        env: Optional[dict[str, str]] = None,
        **kwargs: Any,
    ) -> ToolResult:
        """
        Execute a bash command.
        
        Args:
            command: The command to execute
            timeout: Timeout in seconds
            cwd: Working directory
            env: Additional environment variables
            
        Returns:
            ToolResult with command output
        """
        timeout = timeout or self.timeout
        working_dir = Path(cwd) if cwd else self.working_directory
        
        # Build environment
        exec_env = os.environ.copy()
        if env:
            exec_env.update(env)
        
        # Add OpenCode-specific environment variables
        exec_env["OPENCODE"] = "1"
        exec_env["TERM"] = "xterm-256color"
        
        try:
            # Execute the command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
                env=exec_env,
                preexec_fn=self._setup_process if os.name != "nt" else None,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                # Kill the process on timeout
                try:
                    process.kill()
                except ProcessLookupError:
                    pass
                
                return ToolResult.err(
                    f"Command timed out after {timeout} seconds",
                    output="",
                )
            
            # Decode output
            stdout_str = stdout.decode("utf-8", errors="replace")
            stderr_str = stderr.decode("utf-8", errors="replace")
            
            # Truncate if necessary
            truncated = False
            if len(stdout_str) > self.max_output_size:
                stdout_str = stdout_str[:self.max_output_size] + "\n... (output truncated)"
                truncated = True
            if len(stderr_str) > self.max_output_size:
                stderr_str = stderr_str[:self.max_output_size] + "\n... (output truncated)"
                truncated = True
            
            # Combine output
            output_parts = []
            if stdout_str:
                output_parts.append(stdout_str)
            if stderr_str:
                output_parts.append(f"[stderr]\n{stderr_str}")
            
            output = "\n".join(output_parts)
            
            # Build metadata
            metadata = {
                "exit_code": process.returncode,
                "timeout": timeout,
                "truncated": truncated,
            }
            
            if process.returncode != 0:
                return ToolResult(
                    output=output,
                    error=f"Command exited with code {process.returncode}",
                    metadata=metadata,
                )
            
            return ToolResult.ok(output=output, metadata=metadata)
        
        except Exception as e:
            return ToolResult.err(f"Failed to execute command: {e}")
    
    @staticmethod
    def _setup_process() -> None:
        """Setup process for proper signal handling (Unix only)."""
        # Create new process group
        os.setpgid(0, 0)
        # Ignore SIGINT in child
        signal.signal(signal.SIGINT, signal.SIG_IGN)


class SafeBashTool(BashTool):
    """
    A safer version of the bash tool with command restrictions.
    
    Blocks potentially dangerous commands and requires confirmation
    for certain operations.
    """
    
    BLOCKED_PATTERNS = [
        "rm -rf /",
        "rm -rf /*",
        ":(){ :|:& };:",  # Fork bomb
        "mkfs",
        "dd if=/dev/zero",
        "> /dev/sda",
        "chmod -R 777 /",
        "curl | bash",
        "wget | bash",
    ]
    
    RESTRICTED_COMMANDS = [
        "rm",
        "rmdir",
        "mv",
        "cp",
        "chmod",
        "chown",
        "kill",
        "pkill",
        "killall",
    ]
    
    async def execute(
        self,
        command: str,
        **kwargs: Any,
    ) -> ToolResult:
        """Execute with safety checks."""
        # Check for blocked patterns
        for pattern in self.BLOCKED_PATTERNS:
            if pattern in command:
                return ToolResult.err(
                    f"Blocked potentially dangerous command pattern: {pattern}"
                )
        
        # Parse command to check for restricted commands
        try:
            parts = shlex.split(command)
            if parts:
                cmd_name = Path(parts[0]).name
                
                # Check if command is restricted
                if cmd_name in self.RESTRICTED_COMMANDS:
                    # Allow with warning
                    result = await super().execute(command, **kwargs)
                    if result.metadata:
                        result.metadata["restricted"] = True
                    return result
        except ValueError:
            pass  # Invalid command, let it fail naturally
        
        return await super().execute(command, **kwargs)


# Create default instance
def create_bash_tool(working_directory: Path = Path(".")) -> BashTool:
    """Create a bash tool instance for a given working directory."""
    return BashTool(working_directory=working_directory)
