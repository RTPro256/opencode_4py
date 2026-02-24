"""
Tools API routes for OpenCode HTTP server.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from opencode.server.app import get_tool_registry, get_mcp_client


router = APIRouter()


class ToolInfo(BaseModel):
    """Tool information."""
    name: str
    description: str
    parameters: dict[str, Any]
    permission_level: str


class ToolExecuteRequest(BaseModel):
    """Tool execution request."""
    tool_name: str
    parameters: dict[str, Any]
    require_approval: bool = True


class ToolExecuteResponse(BaseModel):
    """Tool execution response."""
    tool_name: str
    output: str
    error: Optional[str] = None
    files_changed: list[str] = []
    metadata: dict[str, Any] = {}


class MCPToolInfo(BaseModel):
    """MCP tool information."""
    server_name: str
    tool_name: str
    description: Optional[str]
    input_schema: dict[str, Any]


@router.get("/")
async def list_tools():
    """List all available tools."""
    tool_registry = get_tool_registry()
    tools = tool_registry.list_tools()
    
    return [
        ToolInfo(
            name=tool.name,
            description=tool.description,
            parameters=tool.parameters,
            permission_level=tool.permission_level.value,
        )
        for tool in tools
    ]


@router.get("/{tool_name}")
async def get_tool_info(tool_name: str):
    """Get information about a specific tool."""
    tool_registry = get_tool_registry()
    tool = tool_registry.get_tool(tool_name)
    
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    return ToolInfo(
        name=tool.name,
        description=tool.description,
        parameters=tool.parameters,
        permission_level=tool.permission_level.value,
    )


@router.post("/execute", response_model=ToolExecuteResponse)
async def execute_tool(request: ToolExecuteRequest):
    """Execute a tool."""
    tool_registry = get_tool_registry()
    tool = tool_registry.get_tool(request.tool_name)
    
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    # Execute the tool
    result = await tool.execute(**request.parameters)
    
    return ToolExecuteResponse(
        tool_name=request.tool_name,
        output=result.output,
        error=result.error,
        files_changed=result.files_changed,
        metadata=result.metadata or {},
    )


@router.get("/mcp/list")
async def list_mcp_tools():
    """List all MCP tools from connected servers."""
    mcp_client = get_mcp_client()
    
    if not mcp_client:
        return []
    
    tools = mcp_client.get_all_tools()
    
    return [
        MCPToolInfo(
            server_name=server_name,
            tool_name=tool.name,
            description=tool.description,
            input_schema=tool.input_schema.to_dict(),
        )
        for server_name, tool in tools
    ]


@router.post("/mcp/execute")
async def execute_mcp_tool(
    server_name: str,
    tool_name: str,
    arguments: dict[str, Any],
):
    """Execute an MCP tool."""
    mcp_client = get_mcp_client()
    
    if not mcp_client:
        raise HTTPException(status_code=503, detail="MCP not available")
    
    result = await mcp_client.call_tool(server_name, tool_name, arguments)
    
    return {
        "server_name": server_name,
        "tool_name": tool_name,
        "content": result.content,
        "is_error": result.is_error,
    }


@router.get("/mcp/resources")
async def list_mcp_resources():
    """List all MCP resources from connected servers."""
    mcp_client = get_mcp_client()
    
    if not mcp_client:
        return []
    
    resources = mcp_client.get_all_resources()
    
    return [
        {
            "server_name": server_name,
            "uri": resource.uri,
            "name": resource.name,
            "description": resource.description,
            "mime_type": resource.mime_type,
        }
        for server_name, resource in resources
    ]


@router.get("/mcp/resources/{server_name}/{uri:path}")
async def read_mcp_resource(server_name: str, uri: str):
    """Read an MCP resource."""
    mcp_client = get_mcp_client()
    
    if not mcp_client:
        raise HTTPException(status_code=503, detail="MCP not available")
    
    result = await mcp_client.read_resource(server_name, uri)
    
    if not result:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    return result


@router.get("/mcp/prompts")
async def list_mcp_prompts():
    """List all MCP prompts from connected servers."""
    mcp_client = get_mcp_client()
    
    if not mcp_client:
        return []
    
    prompts = mcp_client.get_all_prompts()
    
    return [
        {
            "server_name": server_name,
            "name": prompt.name,
            "description": prompt.description,
            "arguments": [a.to_dict() for a in prompt.arguments],
        }
        for server_name, prompt in prompts
    ]


@router.post("/mcp/prompts/{server_name}/{prompt_name}")
async def execute_mcp_prompt(
    server_name: str,
    prompt_name: str,
    arguments: Optional[dict[str, str]] = None,
):
    """Execute an MCP prompt."""
    mcp_client = get_mcp_client()
    
    if not mcp_client:
        raise HTTPException(status_code=503, detail="MCP not available")
    
    result = await mcp_client.get_prompt(server_name, prompt_name, arguments)
    
    if not result:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    return result
