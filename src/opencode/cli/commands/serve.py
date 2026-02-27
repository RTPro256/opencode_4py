"""
Serve command for OpenCode CLI.

Start the HTTP server for remote access.
"""

from __future__ import annotations

import typer
from rich.console import Console

from opencode.server.app import run_server


console = Console()


def serve_command(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(3000, "--port", "-p", help="Port to bind to"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable auto-reload for development"),
    workers: int = typer.Option(1, "--workers", "-w", help="Number of worker processes"),
) -> None:
    """
    Start the OpenCode HTTP server.
    
    The server provides a REST API and WebSocket endpoints for remote access.
    
    Examples:
        opencode serve
        opencode serve --port 8080
        opencode serve --host 0.0.0.0 --port 3000
        opencode serve --reload  # Development mode
    """
    console.print(f"[green]Starting OpenCode server on {host}:{port}[/green]")
    console.print()
    console.print("Available endpoints:")
    console.print("  • [bold]GET /[/bold] - API info")
    console.print("  • [bold]GET /api/health[/bold] - Health check")
    console.print("  • [bold]GET /api/docs[/bold] - API documentation")
    console.print("  • [bold]POST /api/chat/message[/bold] - Send a message")
    console.print("  • [bold]WebSocket /api/chat/ws/{session_id}[/bold] - Real-time chat")
    console.print()
    console.print("[dim]Press Ctrl+C to stop[/dim]")
    console.print()
    
    run_server(
        host=host,
        port=port,
        reload=reload,
        workers=workers,
    )
