"""
MCP (Model Context Protocol) support for OpenCode.

MCP allows external tools and resources to be integrated into the AI agent,
enabling extensibility and custom tool support.
"""

from opencode.mcp.client import MCPClient, MCPServer
from opencode.mcp.types import (
    MCPTool,
    MCPResource,
    MCPPrompt,
    MCPMessage,
    MCPResult,
)

__all__ = [
    "MCPClient",
    "MCPServer",
    "MCPTool",
    "MCPResource",
    "MCPPrompt",
    "MCPMessage",
    "MCPResult",
]
