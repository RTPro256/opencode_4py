"""
GitHub integration commands for opencode_4py.

Commands for managing git repository initialization, commits, and GitHub operations.
"""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

app = typer.Typer(name="github", help="GitHub integration commands")
console = Console()

# Repository configuration for multi-repo pushes
REPOSITORIES = {
    "opencode_4py": {
        "url": "https://github.com/RTPro256/opencode_4py.git",
        "owner": "RTPro256",
        "name": "opencode_4py",
    },
    "comfyui_portable_opencode-4py": {
        "url": "https://github.com/RTPro256/comfyui_portable_opencode-4py.git",
        "owner": "RTPro256",
        "name": "comfyui_portable_opencode-4py",
    },
}


@dataclass
class PushResult:
    """Result of a push operation."""
    repository: str
    success: bool
    message: str
    remote_url: str = ""

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
    cmd: list[str], check: bool = True, capture: bool = False, cwd: Optional[str] = None
) -> subprocess.CompletedProcess[str]:
    """Run a shell command and handle errors."""
    result = subprocess.run(
        cmd, capture_output=capture, text=True, check=False, cwd=cwd
    )
    if check and result.returncode != 0:
        if capture and result.stderr:
            console.print(f"[red]Error: {result.stderr}[/red]")
        raise typer.Exit(result.returncode)
    return result


def verify_push(remote_url: str, branch: str = "main") -> tuple[bool, str]:
    """
    Verify that push actually succeeded by checking remote refs.
    
    Returns:
        (success, message)
    """
    # Get the local commit hash
    local_result = run_command(
        ["git", "rev-parse", f"refs/heads/{branch}"],
        check=False,
        capture=True
    )
    if local_result.returncode != 0:
        return False, f"Could not get local {branch} commit"
    local_commit = local_result.stdout.strip()
    
    # Try to fetch and verify the remote commit
    fetch_result = run_command(
        ["git", "ls-remote", remote_url, f"refs/heads/{branch}"],
        check=False,
        capture=True
    )
    
    if fetch_result.returncode != 0:
        return False, f"Could not verify remote: {fetch_result.stderr or 'Unknown error'}"
    
    # Parse the output to get remote commit
    remote_output = fetch_result.stdout.strip()
    if not remote_output:
        return False, f"Remote branch {branch} not found"
    
    remote_commit = remote_output.split()[0]
    
    if local_commit == remote_commit:
        return True, f"Verified: commit {local_commit[:7]} present on remote"
    else:
        return False, f"Commit mismatch: local={local_commit[:7]}, remote={remote_commit[:7]}"


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


@app.command("push-all")
def push_to_multiple_repos(
    message: str = typer.Option(
        None, "--message", "-m", help="Commit message"
    ),
    repos: str = typer.Option(
        None, "--repos", "-r", 
        help="Comma-separated list of repository names (or 'all' for all configured repos)"
    ),
    branch: str = typer.Option("main", "--branch", "-b", help="Branch name"),
    verify: bool = typer.Option(
        True, "--verify/--no-verify", help="Verify push success by checking remote"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be pushed without actually pushing"
    ),
) -> None:
    """
    Push changes to multiple GitHub repositories.
    
    This command handles:
    - Staging all changes
    - Creating a commit with the provided message
    - Pushing to multiple configured remotes
    - Verifying each push succeeded
    
    Examples:
        
        Push to all configured repositories:
        
        >>> opencode github push-all -m "Update features"
        
        Push to specific repositories:
        
        >>> opencode github push-all -r "opencode_4py,opencode_comfyui" -m "Update"
        
        Dry run to see what would happen:
        
        >>> opencode github push-all --dry-run
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

    # Determine which repos to push to
    repo_list = []
    if repos:
        if repos.lower() == "all":
            repo_list = list(REPOSITORIES.keys())
        else:
            repo_list = [r.strip() for r in repos.split(",")]
    else:
        # Default: push to origin if configured
        remote_result = run_command(
            ["git", "remote", "get-url", "origin"], check=False, capture=True
        )
        if remote_result.returncode == 0:
            repo_list = ["origin"]
        else:
            console.print("[yellow]No repositories specified and no origin remote configured.[/yellow]")
            console.print("[blue]Use --repos to specify repositories or configure origin remote.[/blue]")
            raise typer.Exit(1)
    
    # Show which repos will be pushed to
    console.print(f"\n[cyan]Repositories to push:[/cyan] {', '.join(repo_list)}")

    # Check for changes
    status_result = run_command(
        ["git", "status", "--porcelain"], capture=True
    )
    has_changes = bool(status_result.stdout.strip())
    
    if not has_changes and not dry_run:
        console.print("[green]No changes to commit.[/green]")
        return

    # Get commit message if not provided
    if not message and not dry_run:
        message = typer.prompt("Enter commit message")

    # Stage and commit (if there are changes)
    if has_changes:
        console.print("[yellow]Staging changes...[/yellow]")
        run_command(["git", "add", "."])
        
        if not dry_run:
            console.print(f"[yellow]Committing: {message}[/yellow]")
            run_command(["git", "commit", "-m", message])
        else:
            console.print(f"[yellow]Would commit: {message}[/yellow]")
    
    # Get local commit info
    commit_result = run_command(
        ["git", "log", "-1", "--oneline"], check=False, capture=True
    )
    commit_info = commit_result.stdout.strip() if commit_result.returncode == 0 else "No commits"
    
    # Push to each repository
    results: list[PushResult] = []
    
    console.print(f"\n[bold]Pushing to {len(repo_list)} repository(s)...[/bold]\n")
    
    for repo_name in repo_list:
        # Determine remote URL
        if repo_name in REPOSITORIES:
            remote_url = REPOSITORIES[repo_name]["url"]
            remote_name = "temp_push_remote"
        else:
            # Assume it's a remote name (like "origin")
            remote_result = run_command(
                ["git", "remote", "get-url", repo_name], check=False, capture=True
            )
            if remote_result.returncode != 0:
                results.append(PushResult(
                    repository=repo_name,
                    success=False,
                    message=f"Remote '{repo_name}' not found",
                ))
                continue
            remote_url = remote_result.stdout.strip()
            remote_name = repo_name
        
        console.print(f"[cyan]→ {repo_name}[/cyan] ({remote_url})")
        
        if dry_run:
            console.print(f"  [yellow]Would push to {remote_url}[/yellow]")
            results.append(PushResult(
                repository=repo_name,
                success=True,
                message="Dry run - would push",
                remote_url=remote_url,
            ))
            continue
        
        # Push to remote
        push_result = run_command(
            ["git", "push", remote_name, branch], check=False
        )
        
        if push_result.returncode != 0:
            error_msg = push_result.stderr or "Unknown error"
            console.print(f"  [red]✗ Push failed: {error_msg}[/red]")
            results.append(PushResult(
                repository=repo_name,
                success=False,
                message=error_msg,
                remote_url=remote_url,
            ))
            continue
        
        console.print(f"  [green]✓ Push completed[/green]")
        
        # Verify push if requested
        if verify:
            console.print(f"  [yellow]Verifying push...[/yellow]")
            verified, verify_msg = verify_push(remote_url, branch)
            if verified:
                console.print(f"  [green]✓ {verify_msg}[/green]")
                results.append(PushResult(
                    repository=repo_name,
                    success=True,
                    message=verify_msg,
                    remote_url=remote_url,
                ))
            else:
                console.print(f"  [red]✗ Verification failed: {verify_msg}[/red]")
                results.append(PushResult(
                    repository=repo_name,
                    success=False,
                    message=verify_msg,
                    remote_url=remote_url,
                ))
        else:
            results.append(PushResult(
                repository=repo_name,
                success=True,
                message="Push completed (verification skipped)",
                remote_url=remote_url,
            ))
    
    # Summary
    console.print("\n[bold]=== Push Summary ===[/bold]")
    
    success_count = sum(1 for r in results if r.success)
    fail_count = len(results) - success_count
    
    for r in results:
        status = "[green]✓[/green]" if r.success else "[red]✗[/red]"
        console.print(f"{status} {r.repository}: {r.message}")
    
    console.print(f"\n[bold]Total: {success_count} succeeded, {fail_count} failed[/bold]")
    
    if fail_count > 0:
        console.print("\n[red]Some pushes failed! Please check the errors above.[/red]")
        raise typer.Exit(1)
    else:
        console.print("\n[green]All pushes completed successfully![/green]")


@app.command("repos")
def list_repos() -> None:
    """
    List configured GitHub repositories.
    
    Displays all repositories configured for multi-repo push operations.
    """
    table = Table(title="Configured GitHub Repositories")
    table.add_column("Name", style="cyan")
    table.add_column("Owner", style="green")
    table.add_column("URL", style="blue")
    
    for name, info in REPOSITORIES.items():
        table.add_row(
            info["name"],
            info["owner"],
            info["url"],
        )
    
    console.print(table)
    console.print("\n[dim]Use 'opencode github push-all --repos <name>' to push to specific repos[/dim]")
    console.print("[dim]Use 'opencode github push-all --repos all' to push to all repos[/dim]")


@app.command("add-repo")
def add_repo(
    name: str = typer.Argument(..., help="Repository name (e.g., opencode_4py)"),
    url: str = typer.Argument(..., help="GitHub repository URL"),
    owner: str = typer.Option(
        "RTPro256", "--owner", "-o", help="Repository owner (username or organization)"
    ),
) -> None:
    """
    Add a repository to the push configuration.
    
    Example:
        
        >>> opencode github add-repo my-project https://github.com/RTPro256/my-project.git
    """
    global REPOSITORIES
    
    REPOSITORIES[name] = {
        "url": url,
        "owner": owner,
        "name": name,
    }
    
    console.print(f"[green]Added repository: {name}[/green]")
    console.print(f"  URL: {url}")
    console.print(f"  Owner: {owner}")
    console.print("\n[yellow]Note: This addition is temporary for the current session.[/yellow]")
    console.print("[dim]To persist, add to REPOSITORIES dict in github.py[/dim]")


@app.command("sync")
def sync_to_target(
    target: str = typer.Option(
        "for_testing/as_dependency/ComfyUI_windows_portable",
        "--target", "-t",
        help="Target project directory path"
    ),
    message: str = typer.Option(
        None, "--message", "-m", help="Commit message for target repo"
    ),
    branch: str = typer.Option("main", "--branch", "-b", help="Branch name"),
    verify: bool = typer.Option(
        True, "--verify/--no-verify", help="Verify push success"
    ),
    push: bool = typer.Option(
        True, "--push/--no-push", help="Push to remote after syncing"
    ),
) -> None:
    """
    Sync changes to a local target project directory.
    
    This command:
    1. Commits changes in current repo (if any)
    2. Copies specified files/directories to target directory
    3. Commits changes in target directory
    4. Optionally pushes to target's remote
    
    Examples:
        
        Sync to default target (ComfyUI portable):
        
        >>> opencode github sync -m "Update opencode_4py"
        
        Sync to custom target:
        
        >>> opencode github sync -t path/to/target -m "Update"
    
    This is useful for keeping integrated projects (like ComfyUI with opencode_4py)
    in sync with the main repository.
    """
    from pathlib import Path
    import shutil
    
    target_path = Path(target).resolve()
    
    # Check if target exists
    if not target_path.exists():
        console.print(f"[red]Target directory not found: {target}[/red]")
        raise typer.Exit(1)
    
    # Check if target is a git repo
    target_git = target_path / ".git"
    if not target_git.exists():
        console.print(f"[yellow]Warning: {target} is not a git repository[/yellow]")
        console.print("[yellow]Initializing git repository in target...[/yellow]")
        run_command(["git", "init"], cwd=str(target_path))
    
    # Get current project root
    project_root = Path.cwd()
    
    console.print(f"[cyan]Syncing from: {project_root}[/cyan]")
    console.print(f"[cyan]Syncing to: {target_path}[/cyan]")
    
    # Files/directories to sync (relative to project root)
    sync_items = ["src", "docs", "plans", "RAG", "README.md", "MISSION.md"]
    
    # Check which items exist
    existing_items = []
    for item in sync_items:
        item_path = project_root / item
        if item_path.exists():
            existing_items.append(item)
        else:
            console.print(f"[dim]Skipping {item} (not found)[/dim]")
    
    if not existing_items:
        console.print("[red]No items to sync![/red]")
        raise typer.Exit(1)
    
    console.print(f"\n[cyan]Items to sync:[/cyan] {', '.join(existing_items)}")
    
    # Get commit message
    if not message:
        default_msg = f"Sync from opencode_4py - {', '.join(existing_items[:3])}"
        if len(existing_items) > 3:
            default_msg += f" (+{len(existing_items) - 3} more)"
        message = typer.prompt("Commit message", default=default_msg)
    
    # Stage and commit in target
    console.print(f"\n[yellow]Staging sync items in target...[/yellow]")
    
    for item in existing_items:
        source = project_root / item
        dest = target_path / item
        
        # Remove existing if present
        if dest.exists():
            if dest.is_dir():
                shutil.rmtree(dest)
            else:
                dest.unlink()
        
        # Copy item
        if source.is_dir():
            shutil.copytree(source, dest)
        else:
            shutil.copy2(source, dest)
        
        console.print(f"  [green]✓[/green] Synced: {item}")
    
    # Add to git in target
    run_command(["git", "add", "."], cwd=str(target_path))
    
    # Check if there are changes to commit
    status_result = run_command(
        ["git", "status", "--porcelain"], check=False, capture=True, cwd=str(target_path)
    )
    
    if not status_result.stdout.strip():
        console.print("\n[green]No changes to commit in target.[/green]")
    else:
        # Commit in target
        console.print(f"[yellow]Committing in target: {message}[/yellow]")
        commit_result = run_command(
            ["git", "commit", "-m", message],
            check=False,
            cwd=str(target_path)
        )
        
        if commit_result.returncode != 0:
            console.print(f"[red]Commit failed: {commit_result.stderr}[/red]")
            raise typer.Exit(1)
        
        console.print("[green]✓ Committed in target[/green]")
        
        # Push if requested
        if push:
            console.print(f"[yellow]Pushing to remote...[/yellow]")
            
            # Check if remote exists
            remote_result = run_command(
                ["git", "remote", "get-url", "origin"],
                check=False,
                capture=True,
                cwd=str(target_path)
            )
            
            if remote_result.returncode != 0:
                console.print("[red]No origin remote configured in target![/red]")
                console.print("[blue]Add remote with: git remote add origin <url>[/blue]")
                raise typer.Exit(1)
            
            remote_url = remote_result.stdout.strip()
            
            push_result = run_command(
                ["git", "push", "origin", branch],
                check=False,
                cwd=str(target_path)
            )
            
            if push_result.returncode != 0:
                console.print(f"[red]Push failed: {push_result.stderr}[/red]")
                raise typer.Exit(1)
            
            console.print(f"[green]✓ Pushed to {remote_url}[/green]")
            
            # Verify push
            if verify:
                console.print(f"[yellow]Verifying push...[/yellow]")
                verified, verify_msg = verify_push(remote_url, branch)
                if verified:
                    console.print(f"[green]✓ {verify_msg}[/green]")
                else:
                    console.print(f"[red]✗ Verification failed: {verify_msg}[/red]")
                    raise typer.Exit(1)
    
    console.print(f"\n[bold green]Sync completed successfully![/bold green]")


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
