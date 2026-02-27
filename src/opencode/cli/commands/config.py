"""
Config command for OpenCode CLI.

View and manage configuration.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from opencode.core.config import Config


console = Console()

# Create a typer app for config commands
config_app = typer.Typer(name="config", help="View and manage configuration")


@config_app.command("show")
def show_config() -> None:
    """
    Show the current configuration.
    
    Displays all configuration settings from the config file.
    
    Examples:
        opencode config show
    """
    config = Config.load()
    
    console.print(Panel(
        f"[bold]Config file:[/bold] {config.config_file}",
        title="OpenCode Configuration",
    ))
    console.print()
    
    # Show providers
    if config.providers:
        table = Table(title="Providers")
        table.add_column("Provider", style="cyan")
        table.add_column("Default Model", style="green")
        table.add_column("API Key", style="yellow")
        
        for name, provider_config in config.providers.items():
            model = provider_config.get("default_model", "—")
            has_key = "✓ Set" if provider_config.get("api_key") else "✗ Not set"
            table.add_row(name, model, has_key)
        
        console.print(table)
        console.print()
    
    # Show settings
    if config.settings:
        table = Table(title="Settings")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in config.settings.items():
            table.add_row(key, str(value))
        
        console.print(table)
        console.print()
    
    # Show MCP servers
    if config.mcp_servers:
        table = Table(title="MCP Servers")
        table.add_column("Name", style="cyan")
        table.add_column("Command", style="green")
        
        for name, server_config in config.mcp_servers.items():
            cmd = server_config.get("command", "—")
            table.add_row(name, cmd)
        
        console.print(table)


@config_app.command("path")
def config_path() -> None:
    """
    Show the path to the config file.
    
    Examples:
        opencode config path
    """
    config = Config.load()
    console.print(f"[bold]Config file:[/bold] {config.config_file}")
    console.print(f"[bold]Data directory:[/bold] {config.data_dir}")


@config_app.command("edit")
def edit_config(
    editor: str = typer.Option(None, "--editor", "-e", help="Editor to use"),
) -> None:
    """
    Open the config file in an editor.
    
    Examples:
        opencode config edit
        opencode config edit --editor code
    """
    import os
    import subprocess
    
    config = Config.load()
    config_file = Path(config.config_file)
    
    # Create config file if it doesn't exist
    if not config_file.exists():
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(_get_default_config())
    
    # Determine editor
    editor_cmd = editor or os.environ.get("EDITOR", "nano")
    
    # Open editor
    try:
        subprocess.run([editor_cmd, str(config_file)])
    except FileNotFoundError:
        console.print(f"[red]Error: Editor '{editor_cmd}' not found[/red]")
        console.print("Set the EDITOR environment variable or use --editor")
        raise typer.Exit(1)


@config_app.command("set")
def set_config(
    key: str = typer.Argument(..., help="Configuration key (e.g., settings.default_provider)"),
    value: str = typer.Argument(..., help="Configuration value"),
) -> None:
    """
    Set a configuration value.
    
    Examples:
        opencode config set settings.default_provider anthropic
        opencode config set settings.theme dark
    """
    import tomli_w
    import tomllib
    
    config = Config.load()
    config_file = Path(config.config_file)
    
    # Read existing config
    if config_file.exists():
        with open(config_file, "rb") as f:
            data = tomllib.load(f)
    else:
        data = {}
    
    # Set the value
    keys = key.split(".")
    current = data
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]
    current[keys[-1]] = _parse_value(value)
    
    # Write back
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, "wb") as f:
        tomli_w.dump(data, f)
    
    console.print(f"[green]✓ Set {key} = {value}[/green]")


@config_app.command("get")
def get_config(
    key: str = typer.Argument(..., help="Configuration key"),
) -> None:
    """
    Get a configuration value.
    
    Examples:
        opencode config get settings.default_provider
    """
    import tomllib
    
    config = Config.load()
    config_file = Path(config.config_file)
    
    if not config_file.exists():
        console.print("[red]Config file not found[/red]")
        raise typer.Exit(1)
    
    with open(config_file, "rb") as f:
        data = tomllib.load(f)
    
    # Navigate to the key
    keys = key.split(".")
    current = data
    try:
        for k in keys:
            current = current[k]
        console.print(f"[bold]{key}[/bold] = {current}")
    except KeyError:
        console.print(f"[red]Key not found: {key}[/red]")
        raise typer.Exit(1)


@config_app.command("reset")
def reset_config(
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
) -> None:
    """
    Reset configuration to defaults.
    
    Examples:
        opencode config reset
        opencode config reset --yes
    """
    if not confirm:
        if not typer.confirm("Reset all configuration to defaults?"):
            raise typer.Abort()
    
    config = Config.load()
    config_file = Path(config.config_file)
    
    if config_file.exists():
        config_file.unlink()
    
    # Create default config
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text(_get_default_config())
    
    console.print("[green]✓ Configuration reset to defaults[/green]")


@config_app.command("wizard")
def config_wizard() -> None:
    """
    Interactive configuration wizard.
    
    Guides you through setting up OpenCode configuration.
    
    Examples:
        opencode config wizard
    """
    import os
    import tomli_w
    
    console.print(Panel(
        "[bold]OpenCode Configuration Wizard[/bold]\n\n"
        "This wizard will help you set up your OpenCode configuration.",
        title="Welcome",
        border_style="blue",
    ))
    console.print()
    
    config = Config.load()
    config_file = Path(config.config_file)
    
    # Read existing config or start fresh
    if config_file.exists():
        import tomllib
        with open(config_file, "rb") as f:
            data = tomllib.load(f)
        console.print("[dim]Loaded existing configuration[/dim]")
    else:
        data = {}
    
    # Step 1: Default Provider
    console.print("\n[bold cyan]Step 1: Default Provider[/bold cyan]")
    console.print("Available providers: anthropic, openai, google, ollama, openrouter")
    
    current_provider = data.get("settings", {}).get("default_provider", "anthropic")
    provider = typer.prompt(
        "Default provider",
        default=current_provider,
        type=str,
    )
    
    if "settings" not in data:
        data["settings"] = {}
    data["settings"]["default_provider"] = provider
    
    # Step 2: Provider API Keys
    console.print("\n[bold cyan]Step 2: Provider API Keys[/bold cyan]")
    console.print("[dim]API keys are stored locally and never shared.[/dim]")
    
    providers_to_configure = ["anthropic", "openai", "google"]
    
    for prov in providers_to_configure:
        prov_key = typer.prompt(
            f"{prov.capitalize()} API key (leave empty to skip)",
            default="",
            show_default=False,
            hide_input=True,
        )
        
        if prov_key:
            if f"provider.{prov}" not in data:
                data[f"provider.{prov}"] = {}
            # Note: In production, this should be stored securely
            data[f"provider.{prov}"]["api_key"] = prov_key
            console.print(f"[green]✓ {prov.capitalize()} API key set[/green]")
    
    # Step 3: Default Models
    console.print("\n[bold cyan]Step 3: Default Models[/bold cyan]")
    
    model_suggestions = {
        "anthropic": "claude-3-5-sonnet-20241022",
        "openai": "gpt-4o",
        "google": "gemini-2.0-flash-exp",
        "ollama": "llama3.2",
        "openrouter": "anthropic/claude-3.5-sonnet",
    }
    
    for prov in providers_to_configure:
        if f"provider.{prov}" in data or prov == provider:
            current_model = data.get(f"provider.{prov}", {}).get("default_model", model_suggestions.get(prov, ""))
            model = typer.prompt(
                f"{prov.capitalize()} default model",
                default=current_model,
            )
            
            if f"provider.{prov}" not in data:
                data[f"provider.{prov}"] = {}
            data[f"provider.{prov}"]["default_model"] = model
    
    # Step 4: Generation Settings
    console.print("\n[bold cyan]Step 4: Generation Settings[/bold cyan]")
    
    current_max_tokens = data.get("settings", {}).get("max_tokens", 8192)
    max_tokens = typer.prompt(
        "Max tokens",
        default=current_max_tokens,
        type=int,
    )
    data["settings"]["max_tokens"] = max_tokens
    
    current_temp = data.get("settings", {}).get("temperature", 0.7)
    temperature = typer.prompt(
        "Temperature (0.0-2.0)",
        default=current_temp,
        type=float,
    )
    data["settings"]["temperature"] = min(2.0, max(0.0, temperature))
    
    # Step 5: Theme
    console.print("\n[bold cyan]Step 5: Theme[/bold cyan]")
    console.print("Available themes: dark, light, auto")
    
    current_theme = data.get("settings", {}).get("theme", "dark")
    theme = typer.prompt(
        "Theme",
        default=current_theme,
        type=str,
    )
    data["settings"]["theme"] = theme
    
    # Step 6: MCP Servers (optional)
    console.print("\n[bold cyan]Step 6: MCP Servers (Optional)[/bold cyan]")
    console.print("[dim]MCP servers extend OpenCode with additional tools.[/dim]")
    
    if typer.confirm("Configure MCP servers?", default=False):
        if "mcp" not in data:
            data["mcp"] = {}
        if "servers" not in data["mcp"]:
            data["mcp"]["servers"] = {}
        
        while True:
            server_name = typer.prompt(
                "Server name (leave empty to finish)",
                default="",
                show_default=False,
            )
            
            if not server_name:
                break
            
            server_cmd = typer.prompt(
                f"Command for {server_name}",
                default="",
            )
            
            if server_cmd:
                data["mcp"]["servers"][server_name] = {"command": server_cmd}
                console.print(f"[green]✓ Added MCP server: {server_name}[/green]")
    
    # Save configuration
    console.print("\n[bold cyan]Saving Configuration...[/bold cyan]")
    
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, "wb") as f:
        tomli_w.dump(data, f)
    
    console.print(f"\n[green]✓ Configuration saved to {config_file}[/green]")
    
    # Show summary
    console.print("\n[bold]Configuration Summary:[/bold]")
    console.print(f"  Default provider: {data['settings'].get('default_provider', 'not set')}")
    console.print(f"  Max tokens: {data['settings'].get('max_tokens', 'not set')}")
    console.print(f"  Temperature: {data['settings'].get('temperature', 'not set')}")
    console.print(f"  Theme: {data['settings'].get('theme', 'not set')}")
    
    configured_providers = [k.replace("provider.", "") for k in data.keys() if k.startswith("provider.")]
    if configured_providers:
        console.print(f"  Configured providers: {', '.join(configured_providers)}")
    
    mcp_servers = data.get("mcp", {}).get("servers", {})
    if mcp_servers:
        console.print(f"  MCP servers: {', '.join(mcp_servers.keys())}")
    
    console.print("\n[dim]Run 'opencode config show' to view full configuration[/dim]")


def _get_default_config() -> str:
    """Get the default configuration content."""
    return '''# OpenCode Configuration

[provider.anthropic]
# api_key = "your-anthropic-api-key"
default_model = "claude-3-5-sonnet-20241022"

[provider.openai]
# api_key = "your-openai-api-key"
default_model = "gpt-4o"

[provider.google]
# api_key = "your-google-api-key"
default_model = "gemini-2.0-flash-exp"

[settings]
default_provider = "anthropic"
theme = "dark"
max_tokens = 8192
temperature = 0.7

# MCP Servers
# [mcp.servers.filesystem]
# command = "mcp-filesystem"
# args = ["/path/to/project"]
'''


def _parse_value(value: str) -> any:
    """Parse a string value into the appropriate type."""
    # Boolean
    if value.lower() in ("true", "yes", "1"):
        return True
    if value.lower() in ("false", "no", "0"):
        return False
    
    # Number
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        pass
    
    # String
    return value


if __name__ == "__main__":
    config_app()
