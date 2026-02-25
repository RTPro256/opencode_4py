"""
MCP (Model Context Protocol) client implementation.

This module provides the client for connecting to and communicating
with MCP servers via stdio transport.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from opencode.mcp.types import (
    JSONRPCNotification,
    JSONRPCRequest,
    JSONRPCResponse,
    MCPCapabilities,
    MCPInitializeParams,
    MCPServerInfo,
    MCPPrompt,
    MCPResource,
    MCPResult,
    MCPTool,
)


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server connection."""
    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    cwd: Optional[Path] = None
    timeout: int = 30  # seconds
    
    @classmethod
    def from_dict(cls, name: str, data: dict) -> MCPServerConfig:
        return cls(
            name=name,
            command=data.get("command", ""),
            args=data.get("args", []),
            env=data.get("env", {}),
            cwd=Path(data["cwd"]) if data.get("cwd") else None,
            timeout=data.get("timeout", 30),
        )


@dataclass
class MCPServer:
    """
    Represents a connected MCP server.
    
    Manages the lifecycle and communication with an MCP server process.
    """
    
    config: MCPServerConfig
    process: Optional[asyncio.subprocess.Process] = None
    server_info: Optional[MCPServerInfo] = None
    tools: list[MCPTool] = field(default_factory=list)
    resources: list[MCPResource] = field(default_factory=list)
    prompts: list[MCPPrompt] = field(default_factory=list)
    _request_id: int = 0
    _pending_requests: dict[int, asyncio.Future] = field(default_factory=dict)
    _reader_task: Optional[asyncio.Task] = None
    _initialized: bool = False
    
    async def start(self) -> bool:
        """Start the MCP server process."""
        if self.process:
            return True
        
        # Build environment
        env = os.environ.copy()
        env.update(self.config.env)
        
        # Find the command
        command = shutil.which(self.config.command)
        if not command:
            command = self.config.command
        
        try:
            self.process = await asyncio.create_subprocess_exec(
                command,
                *self.config.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=self.config.cwd,
            )
            
            # Start reader task
            self._reader_task = asyncio.create_task(self._read_responses())
            
            # Initialize the server
            await self._initialize()
            
            return True
        
        except Exception as e:
            print(f"Failed to start MCP server {self.config.name}: {e}")
            return False
    
    async def stop(self) -> None:
        """Stop the MCP server process."""
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
            self._reader_task = None
        
        if self.process:
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=5)
            except asyncio.TimeoutError:
                self.process.kill()
                await self.process.wait()
            except Exception:
                pass
            self.process = None
        
        self._initialized = False
    
    async def _initialize(self) -> None:
        """Initialize the MCP connection."""
        params = MCPInitializeParams()
        
        response = await self._send_request("initialize", params.to_dict())
        
        if response and "result" in response:
            self.server_info = MCPServerInfo.from_dict(response["result"])
            
            # Send initialized notification
            await self._send_notification("notifications/initialized", {})
            
            # Load capabilities
            if self.server_info.capabilities.tools:
                await self._load_tools()
            if self.server_info.capabilities.resources:
                await self._load_resources()
            if self.server_info.capabilities.prompts:
                await self._load_prompts()
            
            self._initialized = True
    
    async def _load_tools(self) -> None:
        """Load available tools from the server."""
        response = await self._send_request("tools/list", {})
        if response and "result" in response:
            tools_data = response["result"].get("tools", [])
            self.tools = [MCPTool.from_dict(t) for t in tools_data]
    
    async def _load_resources(self) -> None:
        """Load available resources from the server."""
        response = await self._send_request("resources/list", {})
        if response and "result" in response:
            resources_data = response["result"].get("resources", [])
            self.resources = [MCPResource.from_dict(r) for r in resources_data]
    
    async def _load_prompts(self) -> None:
        """Load available prompts from the server."""
        response = await self._send_request("prompts/list", {})
        if response and "result" in response:
            prompts_data = response["result"].get("prompts", [])
            self.prompts = [MCPPrompt.from_dict(p) for p in prompts_data]
    
    async def _send_request(
        self,
        method: str,
        params: Optional[dict] = None,
    ) -> Optional[dict]:
        """Send a JSON-RPC request and wait for response."""
        if not self.process or not self.process.stdin:
            return None
        
        self._request_id += 1
        request_id = self._request_id
        
        request = JSONRPCRequest(
            id=request_id,
            method=method,
            params=params,
        )
        
        # Create future for response
        loop = asyncio.get_event_loop()
        future: asyncio.Future[Optional[dict]] = loop.create_future()
        self._pending_requests[request_id] = future
        
        # Send request
        content = json.dumps(request.to_dict())
        message = f"Content-Length: {len(content)}\r\n\r\n{content}"
        
        try:
            self.process.stdin.write(message.encode())
            await self.process.stdin.drain()
            
            # Wait for response with timeout
            return await asyncio.wait_for(future, timeout=self.config.timeout)
        
        except asyncio.TimeoutError:
            self._pending_requests.pop(request_id, None)
            return None
        
        except Exception as e:
            self._pending_requests.pop(request_id, None)
            print(f"MCP request error: {e}")
            return None
    
    async def _send_notification(
        self,
        method: str,
        params: Optional[dict] = None,
    ) -> None:
        """Send a JSON-RPC notification."""
        if not self.process or not self.process.stdin:
            return
        
        notification = JSONRPCNotification(
            method=method,
            params=params,
        )
        
        content = json.dumps(notification.to_dict())
        message = f"Content-Length: {len(content)}\r\n\r\n{content}"
        
        try:
            self.process.stdin.write(message.encode())
            await self.process.stdin.drain()
        except Exception:
            pass
    
    async def _read_responses(self) -> None:
        """Read responses from the server process."""
        if not self.process or not self.process.stdout:
            return
        
        try:
            while True:
                # Read headers
                headers = {}
                while True:
                    line = await self.process.stdout.readline()
                    if not line:
                        return
                    if line == b"\r\n":
                        break
                    try:
                        header = line.decode().strip()
                        if ": " in header:
                            key, value = header.split(": ", 1)
                            headers[key] = value
                    except Exception:
                        continue
                
                # Read content
                content_length = int(headers.get("Content-Length", 0))
                if content_length <= 0:
                    continue
                
                content = await self.process.stdout.read(content_length)
                
                try:
                    data = json.loads(content)
                    
                    # Handle response
                    if "id" in data:
                        request_id = data["id"]
                        if request_id in self._pending_requests:
                            future = self._pending_requests.pop(request_id)
                            if not future.done():
                                future.set_result(data)
                    
                    # Handle notification
                    elif "method" in data:
                        await self._handle_notification(data)
                
                except json.JSONDecodeError:
                    continue
        
        except asyncio.CancelledError:
            raise
        except Exception as e:
            print(f"MCP reader error: {e}")
    
    async def _handle_notification(self, data: dict) -> None:
        """Handle a notification from the server."""
        method = data.get("method", "")
        params = data.get("params", {})
        
        # Handle resource updates
        if method == "notifications/resources/updated":
            uri = params.get("uri")
            if uri:
                # Emit event for resource update
                pass
        
        # Handle tool list changes
        elif method == "notifications/tools/list_changed":
            await self._load_tools()
        
        # Handle resource list changes
        elif method == "notifications/resources/list_changed":
            await self._load_resources()
        
        # Handle prompt list changes
        elif method == "notifications/prompts/list_changed":
            await self._load_prompts()
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> MCPResult:
        """Call a tool on the MCP server."""
        if not self._initialized:
            raise RuntimeError("MCP server not initialized")
        
        response = await self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments,
        })
        
        if response and "result" in response:
            return MCPResult.from_dict(response["result"])
        
        return MCPResult(
            content=[{"type": "text", "text": "Tool call failed"}],
            is_error=True,
        )
    
    async def read_resource(self, uri: str) -> Optional[dict]:
        """Read a resource from the MCP server."""
        if not self._initialized:
            raise RuntimeError("MCP server not initialized")
        
        response = await self._send_request("resources/read", {"uri": uri})
        
        if response and "result" in response:
            return response["result"]
        
        return None
    
    async def get_prompt(
        self,
        prompt_name: str,
        arguments: Optional[dict[str, str]] = None,
    ) -> Optional[dict]:
        """Get a prompt from the MCP server."""
        if not self._initialized:
            raise RuntimeError("MCP server not initialized")
        
        params = {"name": prompt_name}
        if arguments:
            params["arguments"] = arguments
        
        response = await self._send_request("prompts/get", params)
        
        if response and "result" in response:
            return response["result"]
        
        return None


class MCPClient:
    """
    MCP Client for managing multiple MCP server connections.
    
    This is the main entry point for MCP functionality in OpenCode.
    """
    
    def __init__(self) -> None:
        self.servers: dict[str, MCPServer] = {}
        self._started: bool = False
    
    async def add_server(self, config: MCPServerConfig) -> bool:
        """Add and start an MCP server."""
        if config.name in self.servers:
            return True
        
        server = MCPServer(config=config)
        success = await server.start()
        
        if success:
            self.servers[config.name] = server
            return True
        
        return False
    
    async def remove_server(self, name: str) -> None:
        """Remove and stop an MCP server."""
        if name in self.servers:
            await self.servers[name].stop()
            del self.servers[name]
    
    async def start(self, configs: Optional[list[MCPServerConfig]] = None) -> None:
        """Start the MCP client with optional server configs."""
        if configs:
            for config in configs:
                await self.add_server(config)
        self._started = True
    
    async def stop(self) -> None:
        """Stop all MCP servers."""
        for server in list(self.servers.values()):
            await server.stop()
        self.servers.clear()
        self._started = False
    
    def get_all_tools(self) -> list[tuple[str, MCPTool]]:
        """Get all tools from all servers."""
        tools = []
        for server_name, server in self.servers.items():
            for tool in server.tools:
                tools.append((server_name, tool))
        return tools
    
    def get_all_resources(self) -> list[tuple[str, MCPResource]]:
        """Get all resources from all servers."""
        resources = []
        for server_name, server in self.servers.items():
            for resource in server.resources:
                resources.append((server_name, resource))
        return resources
    
    def get_all_prompts(self) -> list[tuple[str, MCPPrompt]]:
        """Get all prompts from all servers."""
        prompts = []
        for server_name, server in self.servers.items():
            for prompt in server.prompts:
                prompts.append((server_name, prompt))
        return prompts
    
    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> MCPResult:
        """Call a tool on a specific server."""
        if server_name not in self.servers:
            return MCPResult(
                content=[{"type": "text", "text": f"Server not found: {server_name}"}],
                is_error=True,
            )
        
        return await self.servers[server_name].call_tool(tool_name, arguments)
    
    async def read_resource(
        self,
        server_name: str,
        uri: str,
    ) -> Optional[dict]:
        """Read a resource from a specific server."""
        if server_name not in self.servers:
            return None
        
        return await self.servers[server_name].read_resource(uri)
    
    async def get_prompt(
        self,
        server_name: str,
        prompt_name: str,
        arguments: Optional[dict[str, str]] = None,
    ) -> Optional[dict]:
        """Get a prompt from a specific server."""
        if server_name not in self.servers:
            return None
        
        return await self.servers[server_name].get_prompt(prompt_name, arguments)
    
    def find_tool(self, tool_name: str) -> Optional[tuple[str, MCPTool]]:
        """Find a tool by name across all servers."""
        for server_name, server in self.servers.items():
            for tool in server.tools:
                if tool.name == tool_name:
                    return (server_name, tool)
        return None
    
    def find_resource(self, uri: str) -> Optional[tuple[str, MCPResource]]:
        """Find a resource by URI across all servers."""
        for server_name, server in self.servers.items():
            for resource in server.resources:
                if resource.uri == uri:
                    return (server_name, resource)
        return None
