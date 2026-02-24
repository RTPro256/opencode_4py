"""
MCP Server Mode - Expose OpenCode tools via MCP protocol.

This module allows OpenCode to act as an MCP server, exposing its tools
to other MCP clients like Claude Desktop, Cursor, or other AI applications.
"""

import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from opencode.tool import get_registry
from opencode.tool.base import Tool


@dataclass
class MCPServerConfig:
    """Configuration for the MCP server."""
    name: str = "opencode"
    version: str = "1.0.0"
    transport: str = "stdio"  # stdio, tcp, websocket
    host: str = "localhost"
    port: int = 3000


class MCPServer:
    """
    MCP Server implementation for OpenCode.
    
    Exposes OpenCode tools to MCP clients via JSON-RPC 2.0 protocol.
    Supports stdio, TCP, and WebSocket transports.
    """
    
    def __init__(self, config: Optional[MCPServerConfig] = None):
        """Initialize the MCP server."""
        self.config = config or MCPServerConfig()
        self.tool_registry = get_registry()
        self._request_handlers: dict[str, Callable] = {}
        self._running = False
        
        # Register standard MCP handlers
        self._register_handlers()
    
    def _register_handlers(self) -> None:
        """Register MCP request handlers."""
        self._request_handlers["initialize"] = self._handle_initialize
        self._request_handlers["tools/list"] = self._handle_tools_list
        self._request_handlers["tools/call"] = self._handle_tools_call
        self._request_handlers["resources/list"] = self._handle_resources_list
        self._request_handlers["prompts/list"] = self._handle_prompts_list
    
    async def start(self) -> None:
        """Start the MCP server."""
        self._running = True
        
        if self.config.transport == "stdio":
            await self._run_stdio()
        elif self.config.transport == "tcp":
            await self._run_tcp()
        elif self.config.transport == "websocket":
            await self._run_websocket()
    
    async def stop(self) -> None:
        """Stop the MCP server."""
        self._running = False
    
    async def _run_stdio(self) -> None:
        """Run the MCP server using stdio transport."""
        while self._running:
            try:
                # Read line from stdin
                line = await asyncio.get_event_loop().run_in_executor(
                    None, input
                )
                if not line:
                    continue
                
                # Parse JSON-RPC request
                try:
                    request = json.loads(line)
                except json.JSONDecodeError:
                    await self._send_error(-32700, "Parse error")
                    continue
                
                # Handle request
                response = await self._handle_request(request)
                
                # Send response
                print(json.dumps(response), flush=True)
            
            except EOFError:
                break
            except Exception as e:
                await self._send_error(-32603, f"Internal error: {e}")
    
    async def _run_tcp(self) -> None:
        """Run the MCP server using TCP transport."""
        import socket
        
        server = await asyncio.start_server(
            self._handle_tcp_client,
            self.config.host,
            self.config.port,
        )
        
        async with server:
            await server.serve_forever()
    
    async def _handle_tcp_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Handle a TCP client connection."""
        addr = writer.get_extra_info('peername')
        
        while self._running:
            try:
                data = await reader.readline()
                if not data:
                    break
                
                request = json.loads(data.decode())
                response = await self._handle_request(request)
                writer.write(json.dumps(response).encode() + b"\n")
                await writer.drain()
            
            except Exception as e:
                error_response = self._make_error_response(-32603, str(e))
                writer.write(json.dumps(error_response).encode() + b"\n")
                await writer.drain()
        
        writer.close()
        await writer.wait_closed()
    
    async def _run_websocket(self) -> None:
        """Run the MCP server using WebSocket transport."""
        # WebSocket implementation would require a library like websockets
        # For now, this is a placeholder
        raise NotImplementedError("WebSocket transport not yet implemented")
    
    async def _handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Handle a JSON-RPC request."""
        method = request.get("method", "")
        params = request.get("params", {})
        request_id = request.get("id")
        
        handler = self._request_handlers.get(method)
        if not handler:
            return self._make_error_response(-32601, f"Method not found: {method}", request_id)
        
        try:
            result = await handler(params)
            return {
                "jsonrpc": "2.0",
                "result": result,
                "id": request_id,
            }
        except Exception as e:
            return self._make_error_response(-32603, str(e), request_id)
    
    async def _handle_initialize(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle MCP initialize request."""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {
                    "listChanged": False,
                },
                "resources": {
                    "subscribe": False,
                    "listChanged": False,
                },
                "prompts": {
                    "listChanged": False,
                },
            },
            "serverInfo": {
                "name": self.config.name,
                "version": self.config.version,
            },
        }
    
    async def _handle_tools_list(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle tools/list request."""
        tools = []
        for tool in self.tool_registry.list_tools():
            tools.append({
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.parameters,
            })
        
        return {"tools": tools}
    
    async def _handle_tools_call(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle tools/call request."""
        tool_name = params.get("name")
        tool_params = params.get("arguments", {})
        
        if not tool_name:
            raise ValueError("Tool name is required")
        
        result = await self.tool_registry.execute(tool_name, tool_params)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": result.output,
                }
            ],
            "isError": not result.success,
        }
    
    async def _handle_resources_list(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle resources/list request."""
        # OpenCode doesn't expose resources via MCP yet
        return {"resources": []}
    
    async def _handle_prompts_list(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle prompts/list request."""
        # OpenCode doesn't expose prompts via MCP yet
        return {"prompts": []}
    
    def _make_error_response(
        self, code: int, message: str, request_id: Any = None
    ) -> dict[str, Any]:
        """Create a JSON-RPC error response."""
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": code,
                "message": message,
            },
            "id": request_id,
        }
    
    async def _send_error(self, code: int, message: str) -> None:
        """Send an error response to stdout."""
        response = self._make_error_response(code, message)
        print(json.dumps(response), flush=True)


async def run_mcp_server(
    transport: str = "stdio",
    host: str = "localhost",
    port: int = 3000,
) -> None:
    """Run the MCP server with the specified transport."""
    config = MCPServerConfig(
        transport=transport,
        host=host,
        port=port,
    )
    server = MCPServer(config)
    await server.start()


def main() -> None:
    """Main entry point for MCP server mode."""
    import sys
    
    transport = "stdio"
    host = "localhost"
    port = 3000
    
    # Parse command line arguments
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--transport" and i + 1 < len(args):
            transport = args[i + 1]
            i += 2
        elif args[i] == "--host" and i + 1 < len(args):
            host = args[i + 1]
            i += 2
        elif args[i] == "--port" and i + 1 < len(args):
            port = int(args[i + 1])
            i += 2
        else:
            i += 1
    
    asyncio.run(run_mcp_server(transport, host, port))


if __name__ == "__main__":
    main()
