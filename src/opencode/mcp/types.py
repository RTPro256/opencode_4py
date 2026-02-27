"""
MCP (Model Context Protocol) type definitions.

These types define the data structures used in MCP communication.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Union


class MCPRole(str, Enum):
    """Message roles in MCP."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MCPPromptArgumentType(str, Enum):
    """Types for prompt arguments."""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"


@dataclass
class MCPPromptArgument:
    """Argument definition for a prompt template."""
    name: str
    description: Optional[str] = None
    required: bool = False
    type: MCPPromptArgumentType = MCPPromptArgumentType.STRING
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "required": self.required,
            "type": self.type.value,
        }


@dataclass
class MCPPrompt:
    """A prompt template provided by an MCP server."""
    name: str
    description: Optional[str] = None
    arguments: list[MCPPromptArgument] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "arguments": [a.to_dict() for a in self.arguments],
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> MCPPrompt:
        arguments = [
            MCPPromptArgument(
                name=a.get("name", ""),
                description=a.get("description"),
                required=a.get("required", False),
                type=MCPPromptArgumentType(a.get("type", "string")),
            )
            for a in data.get("arguments", [])
        ]
        return cls(
            name=data.get("name", ""),
            description=data.get("description"),
            arguments=arguments,
        )


@dataclass
class MCPToolInputSchema:
    """JSON Schema for tool input parameters."""
    type: str = "object"
    properties: dict[str, Any] = field(default_factory=dict)
    required: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "properties": self.properties,
            "required": self.required,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> MCPToolInputSchema:
        return cls(
            type=data.get("type", "object"),
            properties=data.get("properties", {}),
            required=data.get("required", []),
        )


@dataclass
class MCPTool:
    """A tool provided by an MCP server."""
    name: str
    description: Optional[str] = None
    input_schema: MCPToolInputSchema = field(default_factory=MCPToolInputSchema)
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema.to_dict(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> MCPTool:
        schema_data = data.get("inputSchema", {})
        return cls(
            name=data.get("name", ""),
            description=data.get("description"),
            input_schema=MCPToolInputSchema.from_dict(schema_data),
        )


@dataclass
class MCPResourceTemplate:
    """Template for resource URIs."""
    uri_template: str
    name: str
    description: Optional[str] = None
    mime_type: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "uriTemplate": self.uri_template,
            "name": self.name,
            "description": self.description,
            "mimeType": self.mime_type,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> MCPResourceTemplate:
        return cls(
            uri_template=data.get("uriTemplate", ""),
            name=data.get("name", ""),
            description=data.get("description"),
            mime_type=data.get("mimeType"),
        )


@dataclass
class MCPResource:
    """A resource provided by an MCP server."""
    uri: str
    name: str
    description: Optional[str] = None
    mime_type: Optional[str] = None
    template: Optional[MCPResourceTemplate] = None
    
    def to_dict(self) -> dict:
        result = {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
            "mimeType": self.mime_type,
        }
        if self.template:
            result["template"] = self.template.to_dict()
        return result
    
    @classmethod
    def from_dict(cls, data: dict) -> MCPResource:
        template_data = data.get("template")
        template = MCPResourceTemplate.from_dict(template_data) if template_data else None
        return cls(
            uri=data.get("uri", ""),
            name=data.get("name", ""),
            description=data.get("description"),
            mime_type=data.get("mimeType"),
            template=template,
        )


@dataclass
class MCPResourceContent:
    """Content of a resource."""
    uri: str
    mime_type: Optional[str] = None
    text: Optional[str] = None
    blob: Optional[bytes] = None
    
    def to_dict(self) -> dict:
        result = {"uri": self.uri}
        if self.mime_type:
            result["mimeType"] = self.mime_type
        if self.text is not None:
            result["text"] = self.text
        if self.blob is not None:
            import base64
            result["blob"] = base64.b64encode(self.blob).decode()
        return result


@dataclass
class MCPMessage:
    """A message in MCP communication."""
    role: MCPRole
    content: dict[str, Any]
    
    def to_dict(self) -> dict:
        return {
            "role": self.role.value,
            "content": self.content,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> MCPMessage:
        return cls(
            role=MCPRole(data.get("role", "user")),
            content=data.get("content", {}),
        )


@dataclass
class MCPResult:
    """Result from an MCP tool call."""
    content: list[dict[str, Any]] = field(default_factory=list)
    is_error: bool = False
    
    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "isError": self.is_error,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> MCPResult:
        return cls(
            content=data.get("content", []),
            is_error=data.get("isError", False),
        )
    
    @property
    def text(self) -> str:
        """Extract text content from result."""
        texts = []
        for item in self.content:
            if item.get("type") == "text":
                texts.append(item.get("text", ""))
        return "\n".join(texts)


@dataclass
class MCPCapabilities:
    """Capabilities of an MCP server."""
    tools: bool = False
    resources: bool = False
    prompts: bool = False
    logging: bool = False
    experimental: dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: dict) -> MCPCapabilities:
        return cls(
            tools=data.get("tools", {}).get("supported", False),
            resources=data.get("resources", {}).get("supported", False),
            prompts=data.get("prompts", {}).get("supported", False),
            logging=data.get("logging", {}).get("supported", False),
            experimental=data.get("experimental", {}),
        )


@dataclass
class MCPServerInfo:
    """Information about an MCP server."""
    name: str
    version: str
    protocol_version: str = "2024-11-05"
    capabilities: MCPCapabilities = field(default_factory=MCPCapabilities)
    
    @classmethod
    def from_dict(cls, data: dict) -> MCPServerInfo:
        return cls(
            name=data.get("name", "unknown"),
            version=data.get("version", "0.0.0"),
            protocol_version=data.get("protocolVersion", "2024-11-05"),
            capabilities=MCPCapabilities.from_dict(data.get("capabilities", {})),
        )


@dataclass
class MCPImplementationInfo:
    """Information about the client implementation."""
    name: str = "opencode"
    version: str = "0.1.0"


@dataclass
class MCPInitializeParams:
    """Parameters for MCP initialization."""
    protocol_version: str = "2024-11-05"
    capabilities: dict[str, Any] = field(default_factory=lambda: {
        "tools": {"supported": True},
        "resources": {"supported": True, "subscribe": True},
        "prompts": {"supported": True},
        "logging": {"supported": True},
    })
    client_info: MCPImplementationInfo = field(default_factory=MCPImplementationInfo)
    
    def to_dict(self) -> dict:
        return {
            "protocolVersion": self.protocol_version,
            "capabilities": self.capabilities,
            "clientInfo": {
                "name": self.client_info.name,
                "version": self.client_info.version,
            },
        }


# JSON-RPC types

@dataclass
class JSONRPCRequest:
    """A JSON-RPC request."""
    id: Union[int, str]
    method: str
    params: Optional[dict[str, Any]] = None
    jsonrpc: str = "2.0"
    
    def to_dict(self) -> dict:
        result = {
            "jsonrpc": self.jsonrpc,
            "id": self.id,
            "method": self.method,
        }
        if self.params:
            result["params"] = self.params
        return result


@dataclass
class JSONRPCResponse:
    """A JSON-RPC response."""
    id: Union[int, str]
    result: Optional[Any] = None
    error: Optional[dict[str, Any]] = None
    jsonrpc: str = "2.0"
    
    @classmethod
    def from_dict(cls, data: dict) -> JSONRPCResponse:
        return cls(
            id=data.get("id", 0),
            result=data.get("result"),
            error=data.get("error"),
            jsonrpc=data.get("jsonrpc", "2.0"),
        )


@dataclass
class JSONRPCNotification:
    """A JSON-RPC notification (no id, no response expected)."""
    method: str
    params: Optional[dict[str, Any]] = None
    jsonrpc: str = "2.0"
    
    def to_dict(self) -> dict:
        result = {
            "jsonrpc": self.jsonrpc,
            "method": self.method,
        }
        if self.params:
            result["params"] = self.params
        return result
