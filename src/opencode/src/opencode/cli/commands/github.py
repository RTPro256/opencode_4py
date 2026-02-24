"""
GitHub integration commands for opencode_4py.

Commands for managing git repository initialization, commits, and GitHub operations.
"""

import subprocess
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(name="github", help="GitHub integration commands")
console = Console()

# Default LFS gitattributes content
LFS_GITATTRIBUTES = """# Git LFS Tracking Rules
# Configured for opencode_4py project

# Large binary files
*.dll filter=lfs diff=lfs merge=lfs -text
*.pyd filter=lfs diff=lfs merge=lfs -text
*.so filter=lfs diff=lfs merge=lfs -text
*.dylib filter=lfs diff=lfs merge=lfs -text

# Large media files
*.png filter=lfs diff=lfs merge=lfs -text
*.jpg filter=lfs diff=lfs merge=lfs -text
*.jpeg filter=lfs diff=lfs merge=lfs -text
*.gif filter=lfs diff=lfs merge=lfs -text
*.mp4 filter=lfs diff=lfs merge=lfs -text
*.mp3 filter=lfs diff=lfs merge=lfs -text
*.wav filter=lfs diff=lfs merge=lfs -text

# Large data files
*.parquet filter=lfs diff=lfs merge=lfs -text
*.pkl filter=lfs diff=lfs merge=lfs -text
*.pickle filter=lfs diff=lfs merge=lfs -text
*.h5 filter=lfs diff=lfs merge=lfs -text
*.hdf5 filter=lfs diff=lfs merge=lfs -text

# Archive files
*.zip filter=lfs diff=lfs merge=lfs -text
*.tar.gz filter=lfs diff=lfs merge=lfs -text
*.tar filter=lfs diff=lfs merge=lfs -text
*.7z filter=lfs diff=lfs merge=lfs -text

# Model files
*.pt filter=lfs diff=lfs merge=lfs -text
*.pth filter=lfs diff=lfs merge=lfs -text
*.bin filter=lfs diff=lfs merge=lfs -text
*.onnx filter=lfs diff=lfs merge=lfs -text
*.safetensors filter=lfs diff=lfs merge=lfs -text
"""


def run_command(
    cmd: list[str], check: bool = True, capture: bool = False
) -> subprocess.CompletedProcess[str]:
    """Run a shell command and handle errors."""
    result = subprocess.run(
        cmd, capture_output=capture, text=True, check=False
    )
    if check and result.returncode != 0:
        if capture and result.stderr:
            console.print(f"[red]Error: {result.stderr}[/red]")
        raise typer.Exit(result.returncode)
    return result


@app.command("init")
def init_github(
    repo_name: str = typer.Option(
        "opencode_4py", "--name", "-n", help="Repository name"
    ),
    use_lfs: bool = typer.Option(
        True, "--lfs/--no-lfs", help="Configure Git LFS"
    ),
) -> None:
    """
    Initialize git repository for GitHub.

    This command handles:
    - Initializing git repository
    - Configuring Git LFS (optional)
    - Creating .gitattributes for LFS tracking
    - Creating initial commit
    """
    # Check if already initialized
    git_dir = Path(".git")
    if git_dir.exists():
        console.print("[yellow]Git repository already exists.[/yellow]")
        return

    # Initialize git
    console.print("[yellow]Initializing git repository...[/yellow]")
    run_command(["git", "init"])

    if use_lfs:
        console.print("[yellow]Configuring Git LFS...[/yellow]")
        result = run_command(["git", "lfs", "install"], check=False)
        if result.returncode != 0:
            console.print(
                "[red]Git LFS not found. Please install Git LFS first.[/red]"
            )
            console.print(
                "Download from: https://git-lfs.com/"
            )
            raise typer.Exit(1)

        # Create .gitattributes
        gitattributes = Path(".gitattributes")
        if not gitattributes.exists():
            console.print("[yellow]Creating .gitattributes...[/yellow]")
            gitattributes.write_text(LFS_GITATTRIBUTES)

    # Initial commit
    console.print("[yellow]Creating initial commit...[/yellow]")
    run_command(["git", "add", "."])
    run_command(["git", "commit", "-m", "Initial commit"])

    console.print("[green]Git repository initialized successfully![/green]")
    console.print("[blue]Next steps:[/blue]")
    console.print("  1. Create repository on GitHub: https://github.com/new")
    console.print(
        f"  2. Add remote: git remote add origin "
        f"https://github.com/<username>/{repo_name}.git"
    )
    console.print("  3. Push: git push -u origin main")


@app.command("push")
def push_to_github(
    message: str = typer.Option(
        None, "--message", "-m", help="Commit message"
    ),
    branch: str = typer.Option("main", "--branch", "-b", help="Branch name"),
) -> None:
    """
    Push changes to GitHub repository.

    This command handles:
    - Staging all changes
    - Creating a commit with the provided message
    - Pushing to the configured remote
    """
    # Check if git is initialized
    result = run_command(
        ["git", "rev-parse", "--git-dir"], check=False, capture=True
    )
    if result.returncode != 0:
        console.print(
            "[red]Git repository not initialized. "
            "Run 'opencode github init' first.[/red]"
        )
        raise typer.Exit(1)

    # Check for changes
    status_result = run_command(
        ["git", "status", "--porcelain"], capture=True
    )
    if not status_result.stdout.strip():
        console.print("[green]No changes to commit.[/green]")
        return

    # Get commit message if not provided
    if not message:
        message = typer.prompt("Enter commit message")

    # Stage changes
    console.print("[yellow]Staging changes...[/yellow]")
    run_command(["git", "add", "."])

    # Commit
    console.print(f"[yellow]Committing: {message}[/yellow]")
    run_command(["git", "commit", "-m", message])

    # Push
    console.print("[yellow]Pushing to GitHub...[/yellow]")
    push_result = run_command(
        ["git", "push", "origin", branch], check=False
    )
    if push_result.returncode != 0:
        console.print(
            "[red]Push failed. Make sure the remote repository exists.[/red]"
        )
        console.print(
            "[blue]Create it at: https://github.com/new[/blue]"
        )
        raise typer.Exit(1)

    console.print("[green]Successfully pushed to GitHub![/green]")


@app.command("status")
def github_status() -> None:
    """
    Show git repository status.

    Displays:
    - Current branch
    - Remote configuration
    - LFS status
    - Uncommitted changes
    """
    # Check if git is initialized
    result = run_command(
        ["git", "rev-parse", "--git-dir"], check=False, capture=True
    )
    if result.returncode != 0:
        console.print("[red]Not a git repository.[/red]")
        return

    # Get current branch
    branch_result = run_command(
        ["git", "branch", "--show-current"], capture=True
    )
    branch = branch_result.stdout.strip()

    # Get remote
    remote_result = run_command(
        ["git", "remote", "get-url", "origin"], check=False, capture=True
    )
    remote = remote_result.stdout.strip() if remote_result.returncode == 0 else "Not configured"

    # Check LFS
    lfs_result = run_command(
        ["git", "lfs", "version"], check=False, capture=True
    )
    lfs_status = lfs_result.stdout.strip() if lfs_result.returncode == 0 else "Not installed"

    # Get object count
    objects_result = run_command(
        ["git", "count-objects", "-vH"], capture=True
    )

    # Create status table
    table = Table(title="Git Repository Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Branch", branch)
    table.add_row("Remote", remote)
    table.add_row("Git LFS", lfs_status)

    # Parse object info
    for line in objects_result.stdout.strip().split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            table.add_row(key.strip(), value.strip())

    console.print(table)

    # Show git status
    console.print("\n[yellow]Working Directory Status:[/yellow]")
    run_command(["git", "status", "--short"])


@app.command("remote")
def configure_remote(
    url: str = typer.Argument(..., help="Remote repository URL"),
    name: str = typer.Option("origin", "--name", "-n", help="Remote name"),
) -> None:
    """
    Configure git remote repository.

    Sets the URL for the specified remote (default: origin).
    """
    # Check if remote exists
    result = run_command(
        ["git", "remote", "get-url", name], check=False, capture=True
    )

    if result.returncode == 0:
        # Update existing remote
        run_command(["git", "remote", "set-url", name, url])
        console.print(f"[green]Updated remote '{name}' to: {url}[/green]")
    else:
        # Add new remote
        run_command(["git", "remote", "add", name, url])
        console.print(f"[green]Added remote '{name}': {url}[/green]")


@app.command("create-attributes")
def create_gitattributes(
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite existing file"
    ),
) -> None:
    """
    Create .gitattributes file with LFS tracking rules.

    Creates a .gitattributes file configured for Git LFS
    to track common large file types.
    """
    gitattributes = Path(".gitattributes")

    if gitattributes.exists() and not force:
        console.print(
            "[yellow].gitattributes already exists. "
            "Use --force to overwrite.[/yellow]"
        )
        return

    gitattributes.write_text(LFS_GITATTRIBUTES)
    console.print("[green]Created .gitattributes with LFS tracking rules.[/green]")


if __name__ == "__main__":
    app()
