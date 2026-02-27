"""
FastAPI application for OpenCode HTTP server.

Provides REST API and WebSocket endpoints for remote access.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Optional

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from opencode.core.config import Config
from opencode.core.session import SessionManager
from opencode.db.connection import Database, init_database, close_database, get_database
from opencode.mcp.client import MCPClient
from opencode.tool.base import ToolRegistry


# Global state
_config: Optional[Config] = None
_session_manager: Optional[SessionManager] = None
_tool_registry: Optional[ToolRegistry] = None
_mcp_client: Optional[MCPClient] = None


def get_config() -> Config:
    """Get the global config."""
    if _config is None:
        raise RuntimeError("Server not initialized")
    return _config


def get_session_manager() -> SessionManager:
    """Get the global session manager."""
    if _session_manager is None:
        raise RuntimeError("Server not initialized")
    return _session_manager


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry."""
    if _tool_registry is None:
        raise RuntimeError("Server not initialized")
    return _tool_registry


def get_mcp_client() -> Optional[MCPClient]:
    """Get the global MCP client."""
    return _mcp_client


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    global _config, _session_manager, _tool_registry, _mcp_client
    
    # Initialize
    _config = Config.load()
    
    # Initialize database
    db_path = _config.data_dir / "opencode.db"
    await init_database(db_path)
    
    # Initialize session manager
    _session_manager = SessionManager(get_database())
    
    # Initialize tool registry
    _tool_registry = ToolRegistry()
    # Register default tools...
    
    # Initialize MCP client
    _mcp_client = MCPClient()
    mcp_configs = _config.get_mcp_server_configs()
    if mcp_configs:
        await _mcp_client.start(mcp_configs)
    
    yield
    
    # Cleanup
    if _mcp_client:
        await _mcp_client.stop()
    await close_database()


def create_app(
    title: str = "OpenCode API",
    version: str = "0.1.0",
    cors_origins: Optional[list[str]] = None,
) -> FastAPI:
    """
    Create the FastAPI application.
    
    Args:
        title: API title
        version: API version
        cors_origins: Allowed CORS origins
        
    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title=title,
        version=version,
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )
    
    # CORS middleware
    if cors_origins is None:
        cors_origins = ["*"]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Exception handlers
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        return JSONResponse(
            status_code=500,
            content={"error": str(exc)},
        )
    
    # Include routers
    from opencode.server.routes import chat, sessions, models, tools, files
    from opencode.server.routes import permissions, global_routes
    
    app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
    app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
    app.include_router(models.router, prefix="/api/models", tags=["models"])
    app.include_router(tools.router, prefix="/api/tools", tags=["tools"])
    app.include_router(files.router, prefix="/api/files", tags=["files"])
    app.include_router(permissions.router, prefix="/api/permissions", tags=["permissions"])
    app.include_router(global_routes.router, prefix="/api/global", tags=["global"])
    
    # Health check
    @app.get("/api/health")
    async def health_check():
        return {"status": "ok", "version": version}
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "name": title,
            "version": version,
            "docs": "/api/docs",
        }
    
    return app


def run_server(
    host: str = "127.0.0.1",
    port: int = 3000,
    reload: bool = False,
    workers: int = 1,
) -> None:
    """
    Run the HTTP server.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        reload: Enable auto-reload for development
        workers: Number of worker processes
    """
    app = create_app()
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        workers=workers,
    )


if __name__ == "__main__":
    run_server()
