"""
Index CLI Command

CLI commands for generating and managing project indexes.
"""

from pathlib import Path
from typing import Optional
import logging

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from opencode.util.index_generator import IndexGenerator, IndexConfig, ProjectType

app = typer.Typer(name="index", help="Project index management")
console = Console()
logger = logging.getLogger(__name__)


@app.command("generate")
def generate_index(
    path: Optional[Path] = typer.Argument(
        None,
        help="Project path to index (default: current directory)",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force regeneration even if index is fresh",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Custom output path for index file",
    ),
    depth: int = typer.Option(
        2,
        "--depth",
        "-d",
        help="Maximum directory tree depth",
    ),
) -> None:
    """
    Generate a structural index for a project.
    
    The index includes directory tree, file counts, entry points,
    test locations, and project-specific information.
    
    Examples:
        opencode index generate                    # Index current directory
        opencode index generate /path/to/project   # Index specific project
        opencode index generate --force            # Force regeneration
        opencode index generate --depth 3          # Deeper tree
    """
    project_path = (path or Path.cwd()).resolve()
    
    if not project_path.is_dir():
        console.print(f"[red]Error: {project_path} is not a directory[/red]")
        raise typer.Exit(1)
    
    config = IndexConfig(tree_depth=depth)
    generator = IndexGenerator(config)
    
    index_path = output or (project_path / config.index_dir / config.index_filename)
    
    # Check if index is fresh
    if not force and generator.is_index_fresh(index_path):
        console.print(f"[yellow]Index is fresh (< 5 minutes old). Use --force to regenerate.[/yellow]")
        console.print(f"[dim]Index location: {index_path}[/dim]")
        return
    
    # Check staleness
    if not force and not generator.is_index_stale(project_path, index_path):
        console.print(f"[green]Index is up-to-date (commit hash matches).[/green]")
        console.print(f"[dim]Index location: {index_path}[/dim]")
        return
    
    # Generate index
    console.print(f"[blue]Generating index for {project_path.name}...[/blue]")
    
    try:
        index = generator.generate(project_path)
        saved_path = generator.save_index(index, output)
        
        console.print(Panel(
            f"[green]✓ Index generated successfully[/green]\n\n"
            f"Project: {index.project_name}\n"
            f"Type: {index.project_type.value}\n"
            f"Branch: {index.branch}\n"
            f"Commit: {index.commit}\n"
            f"Files indexed: {sum(index.file_counts.values())}\n"
            f"Test files: {sum(index.test_files.values())}\n\n"
            f"[dim]Saved to: {saved_path}[/dim]",
            title="Index Generated",
        ))
        
    except Exception as e:
        console.print(f"[red]Error generating index: {e}[/red]")
        logger.exception("Index generation failed")
        raise typer.Exit(1)


@app.command("status")
def index_status(
    path: Optional[Path] = typer.Argument(
        None,
        help="Project path to check (default: current directory)",
    ),
) -> None:
    """
    Show the status of a project's index.
    
    Displays whether the index exists, is fresh, and matches the current commit.
    """
    project_path = (path or Path.cwd()).resolve()
    config = IndexConfig()
    generator = IndexGenerator(config)
    
    index_path = project_path / config.index_dir / config.index_filename
    
    table = Table(title=f"Index Status: {project_path.name}")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    if index_path.exists():
        table.add_row("Index Exists", "✓ Yes")
        table.add_row("Index Path", str(index_path))
        
        # Check freshness
        if generator.is_index_fresh(index_path):
            table.add_row("Freshness", "✓ Fresh (< 5 min)")
        else:
            import time
            age_minutes = (time.time() - index_path.stat().st_mtime) / 60
            table.add_row("Freshness", f"⚠ Stale ({age_minutes:.1f} min old)")
        
        # Check staleness
        if generator.is_index_stale(project_path, index_path):
            table.add_row("Commit Match", "⚠ Out of date")
        else:
            table.add_row("Commit Match", "✓ Up to date")
        
        # Show index info
        try:
            content = index_path.read_text(encoding="utf-8")
            for line in content.split("\n")[:10]:
                if ":" in line and not line.startswith("#"):
                    key, value = line.split(":", 1)
                    if key.strip() in ["Branch", "Commit", "Project Type"]:
                        table.add_row(key.strip(), value.strip())
        except Exception:
            pass
        
    else:
        table.add_row("Index Exists", "✗ No")
        table.add_row("Index Path", str(index_path))
        table.add_row("Action", "Run 'opencode index generate' to create")
    
    console.print(table)


@app.command("show")
def show_index(
    path: Optional[Path] = typer.Argument(
        None,
        help="Project path (default: current directory)",
    ),
) -> None:
    """
    Display the contents of a project's index.
    """
    project_path = (path or Path.cwd()).resolve()
    config = IndexConfig()
    
    index_path = project_path / config.index_dir / config.index_filename
    
    if not index_path.exists():
        console.print(f"[red]No index found at {index_path}[/red]")
        console.print("[dim]Run 'opencode index generate' to create an index.[/dim]")
        raise typer.Exit(1)
    
    content = index_path.read_text(encoding="utf-8")
    
    # Use rich's syntax highlighting
    from rich.syntax import Syntax
    syntax = Syntax(content, "markdown", theme="monokai", line_numbers=False)
    console.print(syntax)


@app.command("list")
def list_indexes(
    workspace: Optional[Path] = typer.Argument(
        None,
        help="Workspace path containing multiple projects (default: current directory)",
    ),
) -> None:
    """
    List all project indexes in a workspace.
    """
    workspace_path = (workspace or Path.cwd()).resolve()
    config = IndexConfig()
    generator = IndexGenerator(config)
    
    table = Table(title="Project Indexes")
    table.add_column("Project", style="cyan")
    table.add_column("Type", style="blue")
    table.add_column("Branch", style="green")
    table.add_column("Commit", style="yellow")
    table.add_column("Status", style="magenta")
    
    found_any = False
    
    for project_dir in workspace_path.iterdir():
        if not project_dir.is_dir():
            continue
        
        index_path = project_dir / config.index_dir / config.index_filename
        
        if index_path.exists():
            found_any = True
            
            try:
                content = index_path.read_text(encoding="utf-8")
                
                branch = "unknown"
                commit = "unknown"
                project_type = "unknown"
                
                for line in content.split("\n"):
                    if line.startswith("Branch:"):
                        branch = line.split(":", 1)[1].strip()[:15]
                    elif line.startswith("Commit:"):
                        commit = line.split(":", 1)[1].strip()[:7]
                    elif line.startswith("Project Type:"):
                        project_type = line.split(":", 1)[1].strip()
                
                # Check staleness
                if generator.is_index_stale(project_dir, index_path):
                    status = "⚠ Stale"
                elif generator.is_index_fresh(index_path):
                    status = "✓ Fresh"
                else:
                    status = "✓ OK"
                
                table.add_row(
                    project_dir.name,
                    project_type,
                    branch,
                    commit,
                    status,
                )
                
            except Exception as e:
                table.add_row(project_dir.name, "error", "-", "-", str(e)[:20])
    
    if not found_any:
        console.print("[yellow]No project indexes found.[/yellow]")
        console.print("[dim]Run 'opencode index generate' in a project directory to create an index.[/dim]")
    else:
        console.print(table)


@app.command("clean")
def clean_indexes(
    path: Optional[Path] = typer.Argument(
        None,
        help="Project path to clean (default: current directory)",
    ),
    all_projects: bool = typer.Option(
        False,
        "--all",
        "-a",
        help="Clean indexes for all projects in workspace",
    ),
) -> None:
    """
    Remove project index files.
    """
    config = IndexConfig()
    
    if all_projects:
        workspace_path = (path or Path.cwd()).resolve()
        removed = 0
        
        for project_dir in workspace_path.iterdir():
            if not project_dir.is_dir():
                continue
            
            index_path = project_dir / config.index_dir / config.index_filename
            if index_path.exists():
                index_path.unlink()
                removed += 1
                console.print(f"[dim]Removed: {index_path}[/dim]")
        
        console.print(f"[green]Removed {removed} index file(s)[/green]")
        
    else:
        project_path = (path or Path.cwd()).resolve()
        index_path = project_path / config.index_dir / config.index_filename
        
        if index_path.exists():
            index_path.unlink()
            console.print(f"[green]Removed: {index_path}[/green]")
        else:
            console.print("[yellow]No index file found to remove.[/yellow]")


if __name__ == "__main__":
    app()
