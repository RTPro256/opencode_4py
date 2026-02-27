"""
Command execution tools.

Refactored from Roo-Code's execute_command tool.
"""

import asyncio
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from .base import BaseTool, ToolResult, ToolCallbacks, ToolRegistry


@dataclass
class ExecuteCommandParams:
    """Parameters for execute_command tool."""
    command: str
    cwd: Optional[str] = None
    timeout: int = 60
    capture_output: bool = True


@ToolRegistry.register
class ExecuteCommandTool(BaseTool[ExecuteCommandParams]):
    """Execute shell command tool."""
    
    name = "execute_command"
    description = "Execute a shell command and return the output"
    
    @classmethod
    def get_parameters_schema(cls) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The command to execute",
                },
                "cwd": {
                    "type": "string",
                    "description": "Working directory for the command",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default 60)",
                },
                "capture_output": {
                    "type": "boolean",
                    "description": "Whether to capture stdout/stderr",
                },
            },
            "required": ["command"],
        }
    
    async def execute(
        self,
        params: ExecuteCommandParams,
        callbacks: ToolCallbacks,
    ) -> ToolResult:
        """Execute the command."""
        try:
            cwd = Path(params.cwd) if params.cwd else None
            
            process = await asyncio.create_subprocess_shell(
                params.command,
                stdout=asyncio.subprocess.PIPE if params.capture_output else None,
                stderr=asyncio.subprocess.PIPE if params.capture_output else None,
                cwd=cwd,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=params.timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                return ToolResult.error_result(
                    f"Command timed out after {params.timeout} seconds"
                )
            
            output_parts = []
            if stdout:
                output_parts.append(stdout.decode("utf-8", errors="replace"))
            if stderr:
                output_parts.append(f"STDERR:\n{stderr.decode('utf-8', errors='replace')}")
            
            output = "\n".join(output_parts) if output_parts else "Command completed (no output)"
            
            return ToolResult.success_result(
                output,
                data={
                    "command": params.command,
                    "return_code": process.returncode,
                    "cwd": str(cwd) if cwd else None,
                },
            )
            
        except Exception as e:
            return ToolResult.error_result(f"Error executing command: {e}")
