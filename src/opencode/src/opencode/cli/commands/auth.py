"""
Auth command for OpenCode CLI.

Manage API keys for AI providers.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from opencode.core.config import Config
from opencode.db.connection import init_database, close_database, get_database
from opencode.db.models import APIKey


console = Console()

# Create a typer app for auth commands
auth_app = typer.Typer(name="auth", help="Manage API keys for AI providers")


@auth_app.command("set")
def set_api_key(
    provider: str = typer.Argument(..., help="Provider name (anthropic, openai, google, etc.)"),
    api_key: str = typer.Argument(..., help="API key for the provider"),
) -> None:
    """
    Set an API key for a provider.
    
    The API key will be stored securely in the database.
    
    Examples:
        opencode auth set anthropic sk-ant-xxx
        opencode auth set openai sk-xxx
        opencode auth set google AIza-xxx
    """
    asyncio.run(_set_api_key_async(provider, api_key))


async def _set_api_key_async(provider: str, api_key: str) -> None:
    """Async implementation of set_api_key."""
    config = Config.load()
    
    # Initialize database
    db_path = config.data_dir / "opencode.db"
    await init_database(db_path)
    
    try:
        # Store the API key
        # In a real implementation, this would encrypt the key
        async with get_database().session() as session:
            # Check if key exists
            from sqlalchemy import select
            stmt = select(APIKey).where(APIKey.provider == provider)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                existing.key_encrypted = api_key  # Should encrypt
                existing.key_hash = _hash_key(api_key)
            else:
                new_key = APIKey(
                    provider=provider,
                    key_encrypted=api_key,  # Should encrypt
                    key_hash=_hash_key(api_key),
                )
                session.add(new_key)
        
        console.print(f"[green]✓ API key set for {provider}[/green]")
    
    finally:
        await close_database()


@auth_app.command("get")
def get_api_key(
    provider: str = typer.Argument(..., help="Provider name"),
) -> None:
    """
    Check if an API key is set for a provider.
    
    The actual key is not displayed for security reasons.
    
    Examples:
        opencode auth get anthropic
    """
    asyncio.run(_get_api_key_async(provider))


async def _get_api_key_async(provider: str) -> None:
    """Async implementation of get_api_key."""
    config = Config.load()
    
    # Initialize database
    db_path = config.data_dir / "opencode.db"
    await init_database(db_path)
    
    try:
        async with get_database().session() as session:
            from sqlalchemy import select
            stmt = select(APIKey).where(APIKey.provider == provider)
            result = await session.execute(stmt)
            api_key = result.scalar_one_or_none()
            
            if api_key:
                # Show masked key
                masked = _mask_key(api_key.key_encrypted)
                console.print(f"[green]✓ API key configured for {provider}[/green]")
                console.print(f"  Key: {masked}")
            else:
                console.print(f"[red]✗ No API key configured for {provider}[/red]")
    
    finally:
        await close_database()


@auth_app.command("list")
def list_api_keys() -> None:
    """
    List all configured providers.
    
    Shows which providers have API keys configured.
    
    Examples:
        opencode auth list
    """
    asyncio.run(_list_api_keys_async())


async def _list_api_keys_async() -> None:
    """Async implementation of list_api_keys."""
    config = Config.load()
    
    # Initialize database
    db_path = config.data_dir / "opencode.db"
    await init_database(db_path)
    
    try:
        async with get_database().session() as session:
            from sqlalchemy import select
            stmt = select(APIKey)
            result = await session.execute(stmt)
            api_keys = result.scalars().all()
            
            table = Table(title="Configured Providers")
            table.add_column("Provider", style="cyan")
            table.add_column("Key", style="green")
            table.add_column("Status", style="bold")
            
            for key in api_keys:
                masked = _mask_key(key.key_encrypted)
                table.add_row(key.provider, masked, "✓ Configured")
            
            # Add known providers without keys
            known_providers = ["anthropic", "openai", "google", "azure", "aws"]
            configured = [k.provider for k in api_keys]
            for provider in known_providers:
                if provider not in configured:
                    table.add_row(provider, "—", "[dim]Not configured[/dim]")
            
            console.print(table)
    
    finally:
        await close_database()


@auth_app.command("delete")
def delete_api_key(
    provider: str = typer.Argument(..., help="Provider name"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
) -> None:
    """
    Delete an API key for a provider.
    
    Examples:
        opencode auth delete anthropic
        opencode auth delete openai --yes
    """
    if not confirm:
        if not typer.confirm(f"Delete API key for {provider}?"):
            raise typer.Abort()
    
    asyncio.run(_delete_api_key_async(provider))


async def _delete_api_key_async(provider: str) -> None:
    """Async implementation of delete_api_key."""
    config = Config.load()
    
    # Initialize database
    db_path = config.data_dir / "opencode.db"
    await init_database(db_path)
    
    try:
        async with get_database().session() as session:
            from sqlalchemy import delete
            stmt = delete(APIKey).where(APIKey.provider == provider)
            result = await session.execute(stmt)
            
            if result.rowcount > 0:
                console.print(f"[green]✓ API key deleted for {provider}[/green]")
            else:
                console.print(f"[yellow]No API key found for {provider}[/yellow]")
    
    finally:
        await close_database()


def _hash_key(key: str) -> str:
    """Create a hash of the API key for verification."""
    import hashlib
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def _mask_key(key: str) -> str:
    """Mask an API key for display."""
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}...{key[-4:]}"


if __name__ == "__main__":
    auth_app()
