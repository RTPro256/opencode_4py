"""Web interface for OpenCode.

Provides a FastAPI-based web interface for interacting with OpenCode
through a browser, including REST API endpoints and WebSocket support
for real-time streaming.
"""

from .app import create_app, run_server

__all__ = [
    "create_app",
    "run_server",
]
