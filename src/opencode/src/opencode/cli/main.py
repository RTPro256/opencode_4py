"""
Main CLI entry point for OpenCode.

This module defines the main CLI application and all subcommands.
"""

import asyncio
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

from opencode import __version__

app = typer.Typer(
    name="opencode",
    help="Open source AI coding agent",
    add_completion=False,
    rich_markup_mode="rich",
)

console = Console()


def version_callback(value: bool) -> None:
    """Callback to display version and exit."""
    if value:
        console.print(f"[bold green]OpenCode[/bold green] version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option("--version", "-v", callback=version_callback, is_eager=True),
    ] = None,
) -> None:
    """
    OpenCode - Open Source AI Coding Agent
    
    An AI-powered coding assistant that runs in your terminal.
    """
    pass


@app.command()
def run(
    directory: Annotated[
        Path,
        typer.Argument(
            exists=False,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
            help="Directory to run OpenCode in",
        ),
    ] = Path("."),
    model: Annotated[
        Optional[str],
        typer.Option("--model", "-m", help="Model to use (e.g., claude-3-5-sonnet)"),
    ] = None,
    agent: Annotated[
        str,
        typer.Option("--agent", "-a", help="Agent to use (build or plan)"),
    ] = "build",
    sandbox_root: Annotated[
        Optional[Path],
        typer.Option("--sandbox-root", help="Root directory for file sandboxing (integration mode)"),
    ] = None,
) -> None:
    """
    Run OpenCode TUI in a directory.
    
    This is the default command when no subcommand is specified.
    
    Sessions and logs will be saved to: {directory}/docs/opencode/
    Plans will be saved to: {directory}/plans/
    """
    from opencode.cli.commands.run import launch_tui
    
    asyncio.run(launch_tui(directory=directory, model=model, agent=agent, sandbox_root=sandbox_root))


@app.command()
def serve(
    port: Annotated[int, typer.Option("--port", "-p", help="Port to listen on")] = 4096,
    host: Annotated[str, typer.Option("--host", help="Host to bind to")] = "127.0.0.1",
    web: Annotated[bool, typer.Option("--web", help="Open web interface")] = False,
) -> None:
    """
    Start the OpenCode HTTP server.
    
    This starts a headless API server that can be used with the web interface
    or other clients.
    """
    from opencode.cli.commands.serve import serve_command
    
    asyncio.run(serve_command(port=port, host=host, open_web=web))


@app.command()
def auth(
    provider: Annotated[
        Optional[str],
        typer.Argument(help="Provider to authenticate (e.g., anthropic, openai)"),
    ] = None,
) -> None:
    """
    Manage authentication for AI providers.
    
    Without arguments, shows current authentication status.
    With a provider name, initiates authentication flow.
    """
    from opencode.cli.commands.auth import auth_command
    
    asyncio.run(auth_command(provider=provider))


@app.command("config")
def config_cmd(
    key: Annotated[Optional[str], typer.Argument(help="Configuration key")] = None,
    value: Annotated[Optional[str], typer.Argument(help="Configuration value")] = None,
    list_all: Annotated[
        bool, typer.Option("--list", "-l", help="List all configuration")
    ] = False,
    global_config: Annotated[
        bool, typer.Option("--global", "-g", help="Use global configuration")
    ] = False,
) -> None:
    """
    View or modify configuration.
    
    Examples:
        opencode config                    # Show all config
        opencode config model              # Show model config
        opencode config model default claude-3-5-sonnet  # Set config value
    """
    from opencode.cli.commands.config import config_command
    
    asyncio.run(config_command(key=key, value=value, list_all=list_all, global_config=global_config))


@app.command()
def models(
    provider: Annotated[
        Optional[str],
        typer.Option("--provider", "-p", help="Filter by provider"),
    ] = None,
    search: Annotated[
        Optional[str],
        typer.Option("--search", "-s", help="Search models by name"),
    ] = None,
) -> None:
    """
    List available AI models.
    
    Shows all models from configured providers with their capabilities.
    """
    from opencode.cli.commands.models import models_command
    
    asyncio.run(models_command(provider=provider, search=search))


@app.command()
def session(
    action: Annotated[
        str,
        typer.Argument(help="Action: list, show, delete, export"),
    ] = "list",
    session_id: Annotated[
        Optional[str],
        typer.Argument(help="Session ID for show/delete/export actions"),
    ] = None,
    output: Annotated[
        Optional[Path],
        typer.Option("--output", "-o", help="Output file for export"),
    ] = None,
) -> None:
    """
    Manage sessions.
    
    Actions:
        list    - List all sessions (default)
        show    - Show session details
        delete  - Delete a session
        export  - Export session to file
    """
    from opencode.cli.commands.session import session_command
    
    asyncio.run(session_command(action=action, session_id=session_id, output=output))


@app.command()
def mcp(
    action: Annotated[
        str,
        typer.Argument(help="Action: list, add, remove, start"),
    ] = "list",
    name: Annotated[
        Optional[str],
        typer.Argument(help="MCP server name"),
    ] = None,
    command: Annotated[
        Optional[str],
        typer.Option("--command", "-c", help="Command to run MCP server"),
    ] = None,
) -> None:
    """
    Manage MCP (Model Context Protocol) servers.
    
    Actions:
        list    - List configured MCP servers
        add     - Add a new MCP server
        remove  - Remove an MCP server
        start   - Start an MCP server
    """
    from opencode.cli.commands.mcp import mcp_command
    
    asyncio.run(mcp_command(action=action, name=name, command=command))


@app.command()
def upgrade() -> None:
    """Upgrade OpenCode to the latest version."""
    from opencode.cli.commands.upgrade import upgrade_command
    
    asyncio.run(upgrade_command())


@app.command()
def uninstall() -> None:
    """Uninstall OpenCode."""
    from opencode.cli.commands.uninstall import uninstall_command
    
    asyncio.run(uninstall_command())


# Register RAG commands as a sub-app
from opencode.cli.commands.rag import app as rag_app
app.add_typer(rag_app, name="rag", help="RAG management commands")


@app.command()
def import_sessions(
    file: Annotated[Path, typer.Argument(help="File to import from")],
) -> None:
    """Import sessions from a file."""
    from opencode.cli.commands.import_export import import_command
    
    asyncio.run(import_command(file=file))


@app.command("export")
def export_sessions(
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output file"),
    ] = Path("opencode-export.json"),
    session_ids: Annotated[
        Optional[list[str]],
        typer.Argument(help="Session IDs to export (empty for all)"),
    ] = None,
) -> None:
    """Export sessions to a file."""
    from opencode.cli.commands.import_export import export_command
    
    asyncio.run(export_command(output=output, session_ids=session_ids))


# Add index subcommand group
from opencode.cli.commands.index import app as index_app
app.add_typer(index_app, name="index")

# Add llmchecker subcommand group
from opencode.cli.commands.llmchecker import app as llm_app
app.add_typer(llm_app, name="llm")

# Add local-llm subcommand group for local LLM management
from opencode.cli.commands.local_llm import llm_app as local_llm_app
app.add_typer(local_llm_app, name="local-llm")

# Add debug subcommand group for simplified troubleshooting
from opencode.cli.commands.debug_cmd import app as debug_app
app.add_typer(debug_app, name="debug", help="Simplified troubleshooting commands")

# Add github subcommand group for GitHub integration
from opencode.cli.commands.github import app as github_app
app.add_typer(github_app, name="github", help="GitHub integration commands")


if __name__ == "__main__":
    app()
