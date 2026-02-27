"""
HTTP Server for OpenCode.

FastAPI-based HTTP server for remote access and API integration.
"""

from opencode.server.app import create_app, run_server
from opencode.server.routes import chat, sessions, models, tools, files

__all__ = [
    "create_app",
    "run_server",
    "chat",
    "sessions",
    "models",
    "tools",
    "files",
]
