"""
Run command for OpenCode CLI.

Execute a single prompt and display the response, or launch the TUI.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from opencode.core.config import Config, MultiModelConfig, MultiModelPattern, ModelStepConfig
from opencode.core.session import SessionManager
from opencode.db.connection import init_database, close_database
from opencode.provider.anthropic import AnthropicProvider
from opencode.provider.openai import OpenAIProvider


console = Console()


async def launch_tui(
    directory: Path = Path("."),
    model: Optional[str] = None,
    agent: str = "build",
    sandbox_root: Optional[Path] = None,
) -> None:
    """
    Launch the OpenCode TUI application.
    
    Args:
        directory: Project directory to work in
        model: Model to use (optional, uses config default if not specified)
        agent: Agent type to use (build or plan)
        sandbox_root: Root directory for file sandboxing (integration mode)
    """
    from opencode.tui.app import OpenCodeApp
    from opencode.core.config import get_config
    from opencode.tool.base import ToolRegistry
    from opencode.mcp.client import MCPClient
    
    # Load configuration
    config = Config.load(directory)
    
    # Override model if specified
    if model:
        config.default_model = model
    
    # Initialize database
    db_path = config.data_dir / "opencode.db"
    await init_database(db_path)
    
    try:
        # Create session manager
        session_manager = SessionManager(config.data_dir)
        
        # Create tool registry
        tool_registry = ToolRegistry()
        
        # Create MCP client (optional)
        mcp_client = None
        try:
            mcp_client = MCPClient()
            if config.mcp_servers:
                await mcp_client.start(list(config.mcp_servers.values()))
        except Exception as e:
            console.print(f"[yellow]Warning: MCP client initialization failed: {e}[/yellow]")
        
        # Create and run TUI app
        app = OpenCodeApp(
            config=config,
            session_manager=session_manager,
            tool_registry=tool_registry,
            mcp_client=mcp_client,
            sandbox_root=sandbox_root,
        )
        
        await app.run_async()
        
    finally:
        await close_database()


def run_command(
    prompt: str = typer.Argument(None, help="The prompt to send to the AI (omit to launch TUI)"),
    model: str = typer.Option(None, "--model", "-m", help="Model to use"),
    provider: str = typer.Option("anthropic", "--provider", "-p", help="Provider to use"),
    project: Path = typer.Option(".", "--project", "-d", help="Project directory"),
    stream: bool = typer.Option(True, "--stream/--no-stream", help="Stream the response"),
    system: Optional[str] = typer.Option(None, "--system", "-s", help="System prompt"),
    # Multi-model options
    multi_model: str = typer.Option(
        None,
        "--multi-model",
        help="Multi-model pattern name from config (e.g., 'code_review')"
    ),
    pattern: str = typer.Option(
        None,
        "--pattern",
        help="Built-in pattern type: sequential, ensemble, voting"
    ),
    models: List[str] = typer.Option(
        [],
        "--models",
        help="Models to use in pattern (e.g., --models llama3.2 --models mistral:7b)"
    ),
    # TUI options
    directory: Path = typer.Option(None, "--directory", "-D", help="Directory to run TUI in"),
    agent: str = typer.Option("build", "--agent", "-a", help="Agent to use (build or plan)"),
) -> None:
    """
    Run OpenCode - either launch TUI or execute a single prompt.
    
    If no prompt is provided, launches the TUI interface.
    
    Examples:
        # Launch TUI
        opencode run
        opencode run --directory /path/to/project
        
        # Single prompt
        opencode run "Explain what this code does"
        opencode run "Write a function to sort a list" --model gpt-4o
        opencode run "Review this file" --system "You are a code reviewer"
        
        # Multi-model patterns
        opencode run "Write a function" --multi-model code_review
        opencode run "Write a function" --pattern sequential --models llama3.2 --models mistral:7b
    """
    # If no prompt provided, launch TUI
    if prompt is None:
        dir_path = directory or project
        asyncio.run(launch_tui(directory=dir_path, model=model, agent=agent))
        return
    
    # Otherwise, run single prompt
    asyncio.run(_run_async(
        prompt, model or "claude-3-5-sonnet-20241022", provider, project, stream, system,
        multi_model, pattern, models
    ))


async def _run_async(
    prompt: str,
    model: str,
    provider_name: str,
    project: Path,
    stream: bool,
    system: Optional[str],
    multi_model: Optional[str] = None,
    pattern: Optional[str] = None,
    models: Optional[List[str]] = None,
) -> None:
    """Async implementation of run command."""
    # Load configuration
    config = Config.load(project)
    
    # Check if multi-model mode
    if multi_model or pattern:
        await _run_multi_model(prompt, multi_model, pattern, models or [], config)
        return
    
    # Initialize database
    db_path = config.data_dir / "opencode.db"
    await init_database(db_path)
    
    try:
        # Get provider
        provider_config = config.get_provider_config(provider_name)
        if not provider_config or not provider_config.api_key:
            console.print(f"[red]Error: No API key configured for {provider_name}[/red]")
            console.print(f"Run [bold]opencode auth set {provider_name} <api-key>[/bold] to configure")
            raise typer.Exit(1)
        
        # Create provider instance
        if provider_name == "anthropic":
            provider = AnthropicProvider(
                api_key=provider_config.api_key,
            )
        elif provider_name == "openai":
            provider = OpenAIProvider(
                api_key=provider_config.api_key,
            )
        else:
            console.print(f"[red]Error: Unknown provider: {provider_name}[/red]")
            raise typer.Exit(1)
        
        # Build messages
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        # Display prompt
        console.print()
        console.print(Panel(prompt, title="You", border_style="blue"))
        console.print()
        
        # Get response
        if stream:
            # Stream response
            console.print(Panel("", title="Assistant", border_style="green"))
            full_response = ""
            
            async for chunk in provider.stream(messages, model=model):
                if chunk.content:
                    full_response += chunk.content
                    console.print(chunk.content, end="")
            
            console.print()
        else:
            # Get complete response
            response = await provider.complete(messages, model=model)
            
            # Display response
            console.print(Panel(
                Markdown(response.content),
                title="Assistant",
                border_style="green",
            ))
            
            # Display usage info
            if response.usage:
                console.print()
                console.print(
                    f"[dim]Tokens: {response.usage.input_tokens} in, "
                    f"{response.usage.output_tokens} out[/dim]"
                )
    
    finally:
        await close_database()


async def _run_multi_model(
    prompt: str,
    pattern_name: Optional[str],
    pattern_type: Optional[str],
    models: List[str],
    config: Config,
) -> None:
    """Execute a multi-model pattern."""
    from opencode.workflow.templates import get_template
    from opencode.workflow.engine import WorkflowEngine
    
    # Get pattern configuration
    if pattern_name:
        # Use named pattern from config
        mm_config = config.multi_model_patterns.get(pattern_name)
        if not mm_config:
            console.print(f"[red]Unknown multi-model pattern: {pattern_name}[/red]")
            console.print(f"Available patterns: {list(config.multi_model_patterns.keys())}")
            raise typer.Exit(1)
    elif pattern_type and models:
        # Build ad-hoc pattern
        mm_config = _build_adhoc_pattern(pattern_type, models, config)
    else:
        console.print("[red]Error: Specify --multi-model <name> or --pattern <type> with --models <model>...[/red]")
        console.print("\nExamples:")
        console.print("  opencode run 'Write a function' --multi-model code_review")
        console.print("  opencode run 'Write a function' --pattern sequential --models llama3.2 --models mistral:7b")
        raise typer.Exit(1)
    
    if not mm_config.enabled:
        console.print(f"[red]Pattern '{pattern_name or pattern_type}' is disabled[/red]")
        raise typer.Exit(1)
    
    # Display prompt
    console.print()
    console.print(Panel(prompt, title="You", border_style="blue"))
    console.print()
    
    # Display pattern info
    console.print(f"[blue]Running {mm_config.pattern.value} pattern with {len(mm_config.models)} models...[/blue]")
    for i, m in enumerate(mm_config.models):
        console.print(f"  [dim]Model {i+1}: {m.model} ({m.provider})[/dim]")
    console.print()
    
    try:
        # Get template and build workflow
        template = get_template(mm_config.pattern.value, mm_config)
        
        # Execute workflow
        engine = WorkflowEngine()
        state = await engine.execute(template, variables={"input": prompt})
        
        if state.is_successful():
            # Get final output - check the output node
            output = None
            for node_id, node_state in state.node_states.items():
                # Node state is NodeExecutionState, access attributes directly
                if hasattr(node_state, 'status') and str(node_state.status) == "completed":
                    if hasattr(node_state, 'outputs') and node_state.outputs:
                        output = node_state.outputs.get("output")
                        if output:
                            break
            
            if output:
                console.print(Panel(
                    Markdown(output),
                    title="Result",
                    border_style="green",
                ))
            else:
                console.print("[yellow]No output produced[/yellow]")
        else:
            console.print(f"[red]Workflow failed: {state.error}[/red]")
            raise typer.Exit(1)
    
    except Exception as e:
        console.print(f"[red]Error executing multi-model pattern: {e}[/red]")
        raise typer.Exit(1)


def _build_adhoc_pattern(
    pattern_type: str,
    models: List[str],
    config: Config,
) -> MultiModelConfig:
    """Build an ad-hoc multi-model configuration from CLI args."""
    model_configs = []
    
    for model_id in models:
        # Get model config from global config or create default
        model_cfg = config.models.get(model_id)
        model_configs.append(ModelStepConfig(
            model=model_id,
            provider=model_cfg.provider if model_cfg else "ollama",
            temperature=model_cfg.temperature if model_cfg else 0.7,
            max_tokens=model_cfg.max_tokens if model_cfg else 4096,
        ))
    
    try:
        pattern = MultiModelPattern(pattern_type)
    except ValueError:
        raise typer.Exit(1)
    
    return MultiModelConfig(
        pattern=pattern,
        models=model_configs,
    )
