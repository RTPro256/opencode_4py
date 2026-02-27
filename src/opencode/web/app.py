"""FastAPI web application for OpenCode.

Provides REST API endpoints and WebSocket support for real-time
streaming interactions with the AI assistant.

Note: This is a stub implementation that requires the following dependencies:
- fastapi
- uvicorn
- pydantic

Install with: pip install fastapi uvicorn pydantic
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Optional

# Type checking imports to avoid errors when dependencies are not installed
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI


@dataclass
class ChatRequest:
    """Chat request model."""
    message: str
    session_id: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    stream: bool = True
    context: Optional[dict[str, Any]] = None


@dataclass
class ChatResponse:
    """Chat response model."""
    session_id: str
    message: str
    role: str = "assistant"
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionInfo:
    """Session information model."""
    id: str
    name: str
    created_at: float
    updated_at: float
    message_count: int
    provider: Optional[str] = None
    model: Optional[str] = None


@dataclass
class ProviderInfo:
    """Provider information model."""
    name: str
    models: list[str]
    configured: bool
    capabilities: list[str]


@dataclass
class ToolInfo:
    """Tool information model."""
    name: str
    description: str
    parameters: dict[str, Any]


def create_app(config: Optional[Any] = None) -> "FastAPI":
    """Create the FastAPI application.
    
    Args:
        config: Optional configuration
        
    Returns:
        FastAPI application
        
    Raises:
        ImportError: If fastapi is not installed
    """
    try:
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
    except ImportError as e:
        raise ImportError(
            "FastAPI is required for the web interface. "
            "Install with: pip install fastapi uvicorn"
        ) from e
    
    app = FastAPI(
        title="OpenCode",
        description="AI-powered coding assistant API",
        version="1.0.0",
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/")
    async def root():
        """Serve the web interface."""
        return {"message": "OpenCode API", "version": "1.0.0"}
    
    @app.get("/api/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "ok", "version": "1.0.0"}
    
    @app.post("/api/sessions")
    async def create_session(request: dict[str, Any]):
        """Create a new session."""
        return {
            "id": "session-1",
            "name": request.get("name", "New Session"),
            "created_at": 0.0,
            "updated_at": 0.0,
            "message_count": 0,
        }
    
    @app.get("/api/sessions")
    async def list_sessions():
        """List all sessions."""
        return []
    
    @app.get("/api/sessions/{session_id}")
    async def get_session(session_id: str):
        """Get session details."""
        return {
            "id": session_id,
            "name": "Session",
            "created_at": 0.0,
            "updated_at": 0.0,
            "message_count": 0,
        }
    
    @app.delete("/api/sessions/{session_id}")
    async def delete_session(session_id: str):
        """Delete a session."""
        return {"status": "deleted"}
    
    @app.post("/api/chat")
    async def chat(request: dict[str, Any]):
        """Send a chat message (non-streaming)."""
        return {
            "session_id": "session-1",
            "message": "Response from OpenCode",
            "role": "assistant",
        }
    
    @app.post("/api/chat/stream")
    async def chat_stream(request: dict[str, Any]):
        """Send a chat message (streaming)."""
        async def generate() -> AsyncIterator[str]:
            yield f'data: {{"session_id": "session-1"}}\n\n'
            yield f'data: {{"content": "Hello"}}\n\n'
            yield f'data: {{"done": true}}\n\n'
        
        from fastapi.responses import StreamingResponse
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
        )
    
    @app.get("/api/providers")
    async def list_providers():
        """List all available providers."""
        return [
            {"name": "anthropic", "models": ["claude-3-opus"], "configured": True, "capabilities": []},
            {"name": "openai", "models": ["gpt-4"], "configured": True, "capabilities": []},
        ]
    
    @app.get("/api/tools")
    async def list_tools():
        """List all available tools."""
        return [
            {"name": "bash", "description": "Execute shell commands", "parameters": {}},
            {"name": "read", "description": "Read file contents", "parameters": {}},
        ]
    
    @app.post("/api/tools/{tool_name}/execute")
    async def execute_tool(tool_name: str, params: dict[str, Any]):
        """Execute a tool."""
        return {"result": f"Executed {tool_name}"}
    
    @app.get("/api/config")
    async def get_config():
        """Get current configuration."""
        return {}
    
    @app.put("/api/config")
    async def update_config(update: dict[str, Any]):
        """Update configuration."""
        return {"status": "updated"}
    
    return app


def run_server(
    host: str = "0.0.0.0",
    port: int = 8080,
    config: Optional[Any] = None,
) -> None:
    """Run the web server.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        config: Optional configuration
        
    Raises:
        ImportError: If uvicorn is not installed
    """
    try:
        import uvicorn
    except ImportError as e:
        raise ImportError(
            "Uvicorn is required to run the web server. "
            "Install with: pip install uvicorn"
        ) from e
    
    app = create_app(config)
    uvicorn.run(app, host=host, port=port)


def _get_index_html() -> str:
    """Get the index HTML page."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenCode</title>
    <style>
        body { font-family: system-ui; background: #1a1a2e; color: #eee; }
        .container { max-width: 800px; margin: 0 auto; padding: 2rem; }
        h1 { color: #e94560; }
    </style>
</head>
<body>
    <div class="container">
        <h1>OpenCode</h1>
        <p>AI-powered coding assistant</p>
    </div>
</body>
</html>"""
