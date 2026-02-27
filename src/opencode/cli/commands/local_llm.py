"""
LLM command for OpenCode CLI.

Local LLM model management inspired by igllama CLI:
- pull: Download models from HuggingFace
- list: List available local models
- show: Show model metadata
- run: Run inference with a model
- serve: Start OpenAI-compatible API server
- remove: Remove a model
"""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from opencode.core.llm import (
    LLMConfig,
    ModelManager,
    get_model_manager,
    get_llm_server,
)

console = Console()


llm_app = typer.Typer(
    name="local-llm",
    help="Local LLM model management (inspired by igllama)",
)


@llm_app.command("list")
def list_models(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show verbose output"),
) -> None:
    """
    List available local models.
    
    Examples:
        opencode llm list
        opencode llm list --verbose
    """
    manager = get_model_manager()
    models = manager.list_models()
    
    if not models:
        console.print("[yellow]No models found.[/yellow]")
        console.print("[dim]Use 'opencode llm pull' to download a model.[/dim]")
        return
    
    table = Table(title="Available Models")
    table.add_column("Name", style="cyan")
    table.add_column("Size", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Source", style="blue")
    
    for model in models:
        table.add_row(
            model.name,
            model._format_size(model.size),
            model.status.value,
            model.source.value,
        )
    
    console.print(table)


@llm_app.command("pull")
def pull_model(
    model_id: str = typer.Argument(..., help="HuggingFace model ID (e.g., TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF)"),
    filename: Optional[str] = typer.Option(None, "--filename", "-f", help="Specific file to download"),
) -> None:
    """
    Download a model from HuggingFace.
    
    Examples:
        opencode llm pull TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF
        opencode llm pull TheBloke/Mistral-7B-Instruct-v0.2-GGUF --filename mistral-7b-instruct-v0.2.Q4_K_M.gguf
    """
    console.print(f"[cyan]Pulling model: {model_id}[/cyan]")
    
    manager = get_model_manager()
    
    try:
        # Note: This is async in the manager, but typer can handle it
        import asyncio
        model = asyncio.run(manager.pull_model(model_id, filename))
        
        console.print(f"[green]Model downloaded successfully![/green]")
        console.print(f"  Name: {model.name}")
        console.print(f"  Path: {model.path}")
        console.print(f"  Size: {model._format_size(model.size)}")
    except Exception as e:
        console.print(f"[red]Error pulling model: {e}[/red]")
        raise typer.Exit(1)


@llm_app.command("show")
def show_model(
    name: str = typer.Argument(..., help="Model name"),
) -> None:
    """
    Show model metadata and information.
    
    Examples:
        opencode llm show tinyllama-1.1b-chat-v1.0
    """
    manager = get_model_manager()
    model = manager.get_model(name)
    
    if not model:
        console.print(f"[red]Model not found: {name}[/red]")
        raise typer.Exit(1)
    
    console.print(f"[cyan]Model: {model.name}[/cyan]")
    console.print(f"  Path: {model.path}")
    console.print(f"  Size: {model._format_size(model.size)}")
    console.print(f"  Status: {model.status.value}")
    console.print(f"  Source: {model.source.value}")
    
    if model.metadata:
        console.print("  Metadata:")
        for key, value in model.metadata.model_dump().items():
            if value is not None:
                console.print(f"    {key}: {value}")


@llm_app.command("remove")
def remove_model(
    name: str = typer.Argument(..., help="Model name to remove"),
    force: bool = typer.Option(False, "--force", "-f", help="Force removal without confirmation"),
) -> None:
    """
    Remove a model from the cache and disk.
    
    Examples:
        opencode llm remove tinyllama-1.1b-chat-v1.0
        opencode llm remove tinyllama-1.1b-chat-v1.0 --force
    """
    manager = get_model_manager()
    model = manager.get_model(name)
    
    if not model:
        console.print(f"[red]Model not found: {name}[/red]")
        raise typer.Exit(1)
    
    if not force:
        confirm = typer.confirm(
            f"Remove model '{name}' ({model._format_size(model.size)})?",
            default=False,
        )
        if not confirm:
            console.print("[yellow]Cancelled.[/yellow]")
            return
    
    if manager.remove_model(name):
        console.print(f"[green]Model '{name}' removed successfully.[/green]")
    else:
        console.print(f"[red]Failed to remove model '{name}'.[/red]")
        raise typer.Exit(1)


@llm_app.command("serve")
def serve_llm(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Server host"),
    port: int = typer.Option(8080, "--port", "-p", help="Server port"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model to load"),
) -> None:
    """
    Start the OpenAI-compatible API server.
    
    Examples:
        opencode llm serve
        opencode llm serve --port 8080 --model tinyllama
    """
    from opencode.core.llm.server import get_llm_server
    
    console.print(f"[green]Starting LLM server on {host}:{port}[/green]")
    
    if model:
        console.print(f"  Model: {model}")
    
    console.print()
    console.print("Available endpoints:")
    console.print("  • [bold]POST /v1/chat/completions[/bold] - Chat completions")
    console.print("  • [bold]POST /v1/embeddings[/bold] - Get embeddings")
    console.print("  • [bold]GET /v1/models[/bold] - List models")
    console.print()
    console.print("[dim]Press Ctrl+C to stop[/dim]")
    
    # Get server and start it
    server = get_llm_server()
    
    try:
        import asyncio
        asyncio.run(server.start())
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped.[/yellow]")


@llm_app.command("run", deprecated=True)
def run_inference(
    model: str = typer.Option(..., "--model", "-m", help="Model to use"),
    prompt: str = typer.Option(..., "--prompt", "-p", help="Prompt to send"),
    temperature: float = typer.Option(0.7, "--temperature", "-t", help="Sampling temperature"),
    max_tokens: int = typer.Option(256, "--max-tokens", help="Maximum tokens to generate"),
) -> None:
    """
    Run inference with a local model. [DEPRECATED - Not yet implemented]
    
    Use 'opencode llm serve' to start the API server instead.
    
    Examples:
        opencode llm run -m tinyllama -p "Hello, how are you?"
    """
    console.print(f"[cyan]Running inference with {model}[/cyan]")
    console.print(f"Prompt: {prompt}")
    console.print()
    
    # TODO: Implement actual inference
    console.print("[yellow]Inference not yet implemented.[/yellow]")
    console.print("[dim]Use 'opencode llm serve' to start the API server.[/dim]")
