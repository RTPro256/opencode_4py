"""
Switch Mode Tool

Tool for switching between different agent modes.
"""

import logging
from typing import Any

from opencode.tool.base import Tool, ToolResult

logger = logging.getLogger(__name__)


class SwitchModeTool(Tool):
    """
    Tool for switching between agent modes.
    
    This tool allows the AI to switch to a different mode to better
    handle the current task (e.g., switching to debug mode for troubleshooting).
    
    Example:
        result = await tool.execute(mode="debug", reason="Need to investigate an error")
    """
    
    @property
    def name(self) -> str:
        return "switch_mode"
    
    @property
    def description(self) -> str:
        return "Switch to a different agent mode (code, architect, ask, debug)"
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "description": "The mode to switch to",
                    "enum": ["code", "architect", "ask", "debug"],
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for switching modes",
                },
            },
            "required": ["mode"],
        }
    
    async def execute(self, **params: Any) -> ToolResult:
        """
        Execute the switch mode tool.
        
        Args:
            **params: Tool parameters including:
                - mode: The mode to switch to
                - reason: Reason for switching
            
        Returns:
            ToolResult with mode switch details
        """
        mode = params.get("mode")
        if not mode:
            return ToolResult.err("Required parameter 'mode' is missing")
        
        reason = params.get("reason", "")
        
        # Validate mode
        valid_modes = ["code", "architect", "ask", "debug"]
        if mode not in valid_modes:
            return ToolResult.err(f"Invalid mode '{mode}'. Valid modes: {valid_modes}")
        
        # Format output
        output = f"Switched to {mode} mode"
        if reason:
            output += f"\nReason: {reason}"
        
        # Mode descriptions
        mode_descriptions = {
            "code": "Full access to all tools for coding tasks",
            "architect": "Planning and documentation focus",
            "ask": "Quick answers and explanations",
            "debug": "Systematic debugging and troubleshooting",
        }
        
        output += f"\n\n{mode_descriptions.get(mode, '')}"
        
        return ToolResult.ok(
            output=output,
            metadata={
                "type": "mode_switch",
                "mode": mode,
                "reason": reason,
                "mode_changed": True,
            },
        )
