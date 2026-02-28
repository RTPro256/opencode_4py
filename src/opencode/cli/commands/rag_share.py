"""
RAG Sharing Commands.

Commands for sharing and downloading community RAG indexes.
"""

import asyncio
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from opencode.core.defaults import DEFAULT_COMMUNITY_REPO, GITHUB_API_BASE

app = typer.Typer(name="rag-share", help="RAG sharing commands")
console = Console()

# Default community RAG repository (uses centralized default)
DEFAULT_COMMUNITY_REPO = DEFAULT_COMMUNITY_REPO
GITHUB_API_BASE = GITHUB_API_BASE
GITHUB_RAW_BASE = "https://raw.githubusercontent.com"


def _parse_github_source(source: str) -> tuple:
    """Parse a GitHub source string into (owner, repo).
    
    Formats:
    - github:owner/repo
    - owner/repo
    - https://github.com/owner/repo
    """
    if source.startswith("github:"):
        source = source[7:]
    elif source.startswith("https://github.com/"):
        source = source[19:]
    
    parts = source.split("/")
    if len(parts) >= 2:
        return parts[0], parts[1]
    else:
        raise ValueError(f"Invalid source format: {source}. Use 'owner/repo' format.")


def _download_file(url: str) -> str:
    """Download a file from URL and return content."""
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return response.read().decode("utf-8")
    except urllib.error.URLError as e:
        raise ConnectionError(f"Failed to download from {url}: {e}")


def _download_json(url: str) -> dict:
    """Download JSON from URL."""
    content = _download_file(url)
    return json.loads(content)


@app.command("get")
def get_community_rag(
    agent: str = typer.Argument(..., help="Agent name to download RAG for"),
    source: str = typer.Option(
        DEFAULT_COMMUNITY_REPO,
        "--from", "-f",
        help="Source repository (format: owner/repo or github:owner/repo)"
    ),
    output_dir: str = typer.Option("./RAG", "--output", "-o", help="Output directory"),
    force: bool = typer.Option(False, "--force", "-F", help="Overwrite existing RAG"),
    merge: bool = typer.Option(False, "--merge", "-m", help="Merge with existing RAG"),
):
    """Download a community RAG index.
    
    Examples:
        opencode rag get troubleshooting
        opencode rag get troubleshooting --from user/community-rag
        opencode rag get troubleshooting --merge  # Merge with existing
    """
    console.print(f"[bold blue]Downloading community RAG for: {agent}[/]")
    
    try:
        owner, repo = _parse_github_source(source)
        console.print(f"  Source: [cyan]{owner}/{repo}[/]")
    except ValueError as e:
        console.print(f"[red]Error: {e}[/]")
        raise typer.Exit(1)
    
    agent_dir = Path(output_dir) / f"agent_{agent}"
    
    # Check existing
    if agent_dir.exists() and not force and not merge:
        console.print(f"[yellow]RAG already exists at {agent_dir}[/]")
        console.print("  Use --force to overwrite or --merge to combine")
        raise typer.Exit(1)
    
    # Download RAG index from GitHub
    try:
        console.print("  Fetching RAG index...")
        
        # Get list of files in the RAG directory
        api_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/RAG/agent_{agent}"
        
        try:
            # Try to get directory listing
            req = urllib.request.Request(api_url, headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "OpenCode-4py-RAG-Client/1.0"
            })
            
            with urllib.request.urlopen(req, timeout=30) as response:
                files = json.loads(response.read().decode("utf-8"))
            
            if not isinstance(files, list):
                console.print(f"[red]Error: RAG 'agent_{agent}' not found in repository[/]")
                console.print(f"  Check available RAGs with: opencode rag list-remote --from {source}")
                raise typer.Exit(1)
            
            # Create agent directory
            if merge and agent_dir.exists():
                console.print("  [yellow]Merging with existing RAG...[/]")
            else:
                agent_dir.mkdir(parents=True, exist_ok=True)
            
            # Download each file
            downloaded_count = 0
            for file_info in files:
                if file_info["type"] == "file":
                    file_name = file_info["name"]
                    download_url = file_info["download_url"]
                    
                    console.print(f"    Downloading: [dim]{file_name}[/]")
                    
                    try:
                        content = _download_file(download_url)
                        
                        # Save file
                        file_path = agent_dir / file_name
                        file_path.write_text(content, encoding="utf-8")
                        downloaded_count += 1
                    except Exception as e:
                        console.print(f"    [yellow]Warning: Failed to download {file_name}: {e}[/]")
            
            console.print(f"\n[green]✓[/] Downloaded {downloaded_count} files to {agent_dir}")
            
            # Show summary
            config_file = agent_dir / "config.json"
            if config_file.exists():
                with open(config_file, "r") as f:
                    config = json.load(f)
                console.print(f"  Documents: {config.get('total_documents', 'unknown')}")
                console.print(f"  Model: {config.get('embedding_model', 'unknown')}")
            
        except urllib.error.HTTPError as e:
            if e.code == 404:
                console.print(f"[red]Error: RAG 'agent_{agent}' not found in {owner}/{repo}[/]")
                console.print(f"  Check available RAGs with: opencode rag list-remote --from {source}")
            else:
                console.print(f"[red]Error: HTTP {e.code} - {e.reason}[/]")
            raise typer.Exit(1)
            
    except ConnectionError as e:
        console.print(f"[red]Error: {e}[/]")
        console.print("  Check your internet connection and try again")
        raise typer.Exit(1)


@app.command("share")
def share_rag(
    agent: str = typer.Argument(..., help="Agent name to share"),
    repo: str = typer.Option(
        DEFAULT_COMMUNITY_REPO,
        "--to", "-t",
        help="Target repository (format: owner/repo)"
    ),
    token: Optional[str] = typer.Option(
        None,
        "--token", "-k",
        help="GitHub personal access token (or set GITHUB_TOKEN env var)"
    ),
    message: str = typer.Option(
        "Update RAG index",
        "--message", "-m",
        help="Commit message"
    ),
):
    """Share your RAG index with the community.
    
    This creates a pull request to the community repository with your RAG.
    
    Examples:
        opencode rag share troubleshooting
        opencode rag share troubleshooting --to my-fork/community-rag
        opencode rag share troubleshooting --token ghp_xxxx
    
    Note: Requires GitHub personal access token with 'repo' scope.
    Set GITHUB_TOKEN environment variable or use --token option.
    """
    console.print(f"[bold blue]Sharing RAG for agent: {agent}[/]")
    
    # Check for token
    github_token = token or os.environ.get("GITHUB_TOKEN")
    if not github_token:
        console.print("[red]Error: GitHub token required[/]")
        console.print("  Set GITHUB_TOKEN environment variable or use --token option")
        console.print("  Create a token at: https://github.com/settings/tokens")
        console.print("  Required scopes: 'repo' (for private repos) or 'public_repo' (for public)")
        raise typer.Exit(1)
    
    # Check local RAG exists
    agent_dir = Path("./RAG") / f"agent_{agent}"
    if not agent_dir.exists():
        console.print(f"[red]Error: RAG not found for agent '{agent}'[/]")
        console.print(f"  Create it first with: opencode rag create {agent}")
        raise typer.Exit(1)
    
    try:
        owner, repo_name = _parse_github_source(repo)
        console.print(f"  Target: [cyan]{owner}/{repo_name}[/]")
    except ValueError as e:
        console.print(f"[red]Error: {e}[/]")
        raise typer.Exit(1)
    
    console.print("\n[yellow]Note: This feature requires GitHub API integration.[/]")
    console.print("For now, manually share your RAG by:")
    console.print(f"  1. Fork the repository: https://github.com/{owner}/{repo_name}")
    console.print(f"  2. Copy your RAG folder: {agent_dir}")
    console.print("  3. Create a pull request")
    
    # TODO: Implement full GitHub API integration
    # This would involve:
    # 1. Check if user has fork of the repo
    # 2. Create fork if needed
    # 3. Create a new branch
    # 4. Upload RAG files
    # 5. Create pull request
    
    console.print("\n[dim]Full GitHub integration coming soon![/]")


@app.command("list-remote")
def list_remote_rags(
    source: str = typer.Option(
        DEFAULT_COMMUNITY_REPO,
        "--from", "-f",
        help="Source repository (format: owner/repo)"
    ),
):
    """List available community RAG indexes.
    
    Examples:
        opencode rag list-remote
        opencode rag list-remote --from user/community-rag
    """
    console.print("[bold blue]Available Community RAG Indexes[/]\n")
    
    try:
        owner, repo = _parse_github_source(source)
        console.print(f"Repository: [cyan]{owner}/{repo}[/]\n")
    except ValueError as e:
        console.print(f"[red]Error: {e}[/]")
        raise typer.Exit(1)
    
    try:
        # Get list of RAG directories
        api_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/RAG"
        
        req = urllib.request.Request(api_url, headers={
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "OpenCode-4py-RAG-Client/1.0"
        })
        
        with urllib.request.urlopen(req, timeout=30) as response:
            contents = json.loads(response.read().decode("utf-8"))
        
        if not isinstance(contents, list):
            console.print("[yellow]No RAG indexes found in repository[/]")
            return
        
        # Filter for agent directories
        agent_dirs = [c for c in contents if c["type"] == "dir" and c["name"].startswith("agent_")]
        
        if not agent_dirs:
            console.print("[yellow]No RAG indexes found[/]")
            return
        
        # Get details for each RAG
        table = Table(title="Community RAG Indexes")
        table.add_column("Agent", style="cyan")
        table.add_column("Documents", style="green")
        table.add_column("Model", style="blue")
        table.add_column("Updated", style="dim")
        
        for agent_dir in agent_dirs:
            agent_name = agent_dir["name"].replace("agent_", "")
            
            # Try to get config
            try:
                config_url = f"{GITHUB_RAW_BASE}/{owner}/{repo}/main/RAG/{agent_dir['name']}/config.json"
                config = _download_json(config_url)
                
                table.add_row(
                    agent_name,
                    str(config.get("total_documents", "?")),
                    config.get("embedding_model", "?"),
                    agent_dir.get("sha", "")[:8] if "sha" in agent_dir else "?",
                )
            except Exception:
                table.add_row(agent_name, "?", "?", "?")
        
        console.print(table)
        
        console.print(f"\n[dim]Download with: opencode rag get <agent> --from {owner}/{repo}[/]")
        
    except urllib.error.HTTPError as e:
        if e.code == 404:
            console.print(f"[red]Error: Repository or RAG directory not found[/]")
            console.print(f"  Check that {owner}/{repo} exists and has a RAG/ folder")
        else:
            console.print(f"[red]Error: HTTP {e.code} - {e.reason}[/]")
        raise typer.Exit(1)
    except ConnectionError as e:
        console.print(f"[red]Error: {e}[/]")
        raise typer.Exit(1)


@app.command("merge")
def merge_rags(
    target: str = typer.Argument(..., help="Target agent name"),
    source: str = typer.Argument(..., help="Source agent name to merge from"),
    output_dir: str = typer.Option("./RAG", "--output", "-o", help="RAG directory"),
):
    """Merge two local RAG indexes.
    
    Combines documents from source RAG into target RAG.
    Both RAGs must use the same embedding model.
    
    Examples:
        opencode rag merge troubleshooting my-local-troubleshooting
    """
    console.print(f"[bold blue]Merging RAG indexes[/]")
    console.print(f"  Source: [cyan]{source}[/]")
    console.print(f"  Target: [cyan]{target}[/]\n")
    
    target_dir = Path(output_dir) / f"agent_{target}"
    source_dir = Path(output_dir) / f"agent_{source}"
    
    # Check both exist
    if not source_dir.exists():
        console.print(f"[red]Error: Source RAG not found: {source_dir}[/]")
        raise typer.Exit(1)
    
    if not target_dir.exists():
        console.print(f"[red]Error: Target RAG not found: {target_dir}[/]")
        console.print(f"  Create it first with: opencode rag create {target}")
        raise typer.Exit(1)
    
    # Load configs
    target_config_file = target_dir / "config.json"
    source_config_file = source_dir / "config.json"
    
    with open(target_config_file, "r") as f:
        target_config = json.load(f)
    
    with open(source_config_file, "r") as f:
        source_config = json.load(f)
    
    # Check embedding model compatibility
    target_model = target_config.get("embedding_model", "unknown")
    source_model = source_config.get("embedding_model", "unknown")
    
    if target_model != source_model:
        console.print(f"[yellow]Warning: Different embedding models[/]")
        console.print(f"  Target: {target_model}")
        console.print(f"  Source: {source_model}")
        console.print("  Merging may produce inconsistent results")
        
        if not typer.confirm("Continue anyway?"):
            console.print("[yellow]Cancelled[/]")
            return
    
    # Merge vector stores
    async def _merge():
        from opencode.core.rag.local_vector_store import LocalVectorStore
        
        target_store = LocalVectorStore(
            path=str(target_dir / ".vector_store"),
            engine=target_config.get("vector_store", "file"),
        )
        
        source_store = LocalVectorStore(
            path=str(source_dir / ".vector_store"),
            engine=source_config.get("vector_store", "file"),
        )
        
        # Get source documents
        source_count = await source_store.count()
        target_count = await target_store.count()
        
        console.print(f"  Source documents: {source_count}")
        console.print(f"  Target documents: {target_count}")
        
        if source_count == 0:
            console.print("[yellow]Source RAG is empty, nothing to merge[/]")
            return
        
        # Read all source data
        # Note: This is a simplified merge - in production you'd want deduplication
        source_data_file = source_dir / ".vector_store" / "data.json"
        source_embeddings_file = source_dir / ".vector_store" / "embeddings.npy"
        
        if source_data_file.exists():
            with open(source_data_file, "r") as f:
                source_data = json.load(f)
            
            # Load embeddings
            import numpy as np
            source_embeddings = None
            if source_embeddings_file.exists():
                source_embeddings = np.load(str(source_embeddings_file))
            
            # Add to target
            if source_embeddings is not None:
                await target_store.add(
                    ids=source_data["ids"],
                    embeddings=source_embeddings.tolist(),
                    texts=source_data["texts"],
                    metadata=source_data["metadata"],
                )
                
                # Update config
                new_count = await target_store.count()
                target_config["total_documents"] = new_count
                
                # Merge sources list
                existing_sources = set(target_config.get("sources", []))
                for s in source_config.get("sources", []):
                    if s not in existing_sources:
                        target_config.setdefault("sources", []).append(s)
                
                with open(target_config_file, "w") as f:
                    json.dump(target_config, f, indent=2)
                
                console.print(f"\n[green]✓[/] Merged {source_count} documents")
                console.print(f"  New total: {new_count}")
            else:
                console.print("[red]Error: Source embeddings not found[/]")
        else:
            console.print("[red]Error: Source vector store data not found[/]")
    
    asyncio.run(_merge())


if __name__ == "__main__":
    app()
