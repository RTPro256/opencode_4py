# GitHub Upload Plan

> **Related Documents:**
> - [README.md](../README.md) - Project overview and features
> - [MISSION.md](../MISSION.md) - Mission statement and core principles

## Overview

This plan outlines the approach for uploading the opencode_4py project to GitHub using Git Large File Storage (Git LFS). Previous attempts using standard git have been unsuccessful due to the project's size and history.

## Current State Analysis

### Project Size Summary

| Category | Size | Files | Git Status |
|----------|------|-------|------------|
| Core Project (to upload) | ~5 MB | 489 | Tracked |
| `for_testing/` | ~3+ GB | Many | Ignored (in .gitignore) |
| `merge_projects/` | ~500+ MB | Many | Ignored (in .gitignore) |
| `.git/` directory | ~500+ MB | N/A | Existing history |

### Key Findings

1. **Core project is small**: Only ~5MB of actual source code and documentation
2. **Large directories are already ignored**: `for_testing/` and `merge_projects/` are in `.gitignore`
3. **Existing `.git/` directory has bloat**: Previous git history contains large objects
4. **Git LFS is installed**: Version 3.7.1 confirmed available

### Problem Analysis

The existing `.git/` directory contains large objects from previous attempts:
- `.git/objects/` contains files up to 21MB
- `.git-rewrite/` directory exists (from previous cleanup attempts)
- Total git metadata is bloated

## Recommended Approach: Fresh Repository

Given the analysis, the cleanest approach is to **start fresh** with a new git repository:

### Why Fresh Repository?

1. **Clean history**: No large file baggage from previous attempts
2. **Simpler setup**: No need to migrate or clean existing history
3. **Git LFS ready**: Can configure LFS from the start for any future large files
4. **GitHub's 100MB limit**: Individual files over 100MB are rejected by GitHub

### Git LFS Configuration

While the core project is small, we'll configure Git LFS for future-proofing:

```gitattributes
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

# Large data files
*.parquet filter=lfs diff=lfs merge=lfs -text
*.pkl filter=lfs diff=lfs merge=lfs -text
*.pickle filter=lfs diff=lfs merge=lfs -text
*.h5 filter=lfs diff=lfs merge=lfs -text
*.hdf5 filter=lfs diff=lfs merge=lfs -text

# Archive files
*.zip filter=lfs diff=lfs merge=lfs -text
*.tar.gz filter=lfs diff=lfs merge=lfs -text
*.7z filter=lfs diff=lfs merge=lfs -text
```

## Implementation Plan

### Phase 1: Preparation

1. **Backup existing `.git/` directory** (optional, for safety)
2. **Remove existing git state**:
   - Delete `.git/` directory
   - Delete `.git-rewrite/` directory
3. **Verify `.gitignore` is correct**

### Phase 2: Repository Initialization

1. **Initialize new git repository**
   ```bash
   git init
   ```

2. **Configure Git LFS**
   ```bash
   git lfs install
   ```

3. **Create `.gitattributes` file** with LFS tracking rules

4. **Configure git user** (if not already configured)
   ```bash
   git config user.name "RTPro256"
   git config user.email "your-email@example.com"
   ```

### Phase 3: Initial Commit

1. **Stage all files**
   ```bash
   git add .
   ```

2. **Create initial commit**
   ```bash
   git commit -m "Initial commit: opencode_4py project"
   ```

3. **Verify commit size**
   ```bash
   git count-objects -vH
   ```

### Phase 4: GitHub Connection

1. **Create repository on GitHub** (via web interface or CLI)
   - Repository: `opencode_4py`
   - Owner: `RTPro256`
   - Visibility: Public or Private (user choice)

2. **Add remote origin**
   ```bash
   git remote add origin https://github.com/RTPro256/opencode_4py.git
   ```

3. **Set main branch and push**
   ```bash
   git branch -M main
   git push -u origin main
   ```

### Phase 5: Verification

1. **Verify repository on GitHub**
   - Check all files are present
   - Verify LFS objects are tracked correctly
   - Confirm commit history

2. **Test clone** (optional)
   ```bash
   git clone https://github.com/RTPro256/opencode_4py.git test_clone
   ```

## Feature: GitHub Update Command

### New CLI Command: `opencode github push`

Create a new CLI command to streamline future updates:

```python
# src/opencode/cli/commands/github.py

"""
GitHub integration commands for opencode_4py.
"""

import typer
from rich.console import Console

app = typer.Typer(name="github", help="GitHub integration commands")
console = Console()


@app.command("push")
def push_to_github(
    message: str = typer.Option(None, "--message", "-m", help="Commit message"),
    branch: str = typer.Option("main", "--branch", "-b", help="Branch name"),
) -> None:
    """
    Push changes to GitHub repository.
    
    This command handles:
    - Staging all changes
    - Creating a commit with the provided message
    - Pushing to the configured remote
    """
    import subprocess
    
    # Check if git is initialized
    result = subprocess.run(["git", "rev-parse", "--git-dir"], capture_output=True)
    if result.returncode != 0:
        console.print("[red]Git repository not initialized. Run 'opencode github init' first.[/red]")
        raise typer.Exit(1)
    
    # Get commit message if not provided
    if not message:
        message = typer.prompt("Enter commit message")
    
    # Stage changes
    console.print("[yellow]Staging changes...[/yellow]")
    subprocess.run(["git", "add", "."], check=True)
    
    # Commit
    console.print(f"[yellow]Committing: {message}[/yellow]")
    subprocess.run(["git", "commit", "-m", message], check=True)
    
    # Push
    console.print("[yellow]Pushing to GitHub...[/yellow]")
    subprocess.run(["git", "push", "origin", branch], check=True)
    
    console.print("[green]Successfully pushed to GitHub![/green]")


@app.command("init")
def init_github(
    repo_name: str = typer.Option("opencode_4py", "--name", "-n", help="Repository name"),
    use_lfs: bool = typer.Option(True, "--lfs/--no-lfs", help="Configure Git LFS"),
) -> None:
    """
    Initialize git repository for GitHub.
    
    This command handles:
    - Initializing git repository
    - Configuring Git LFS (optional)
    - Creating .gitattributes for LFS tracking
    - Creating initial commit
    """
    import subprocess
    from pathlib import Path
    
    # Check if already initialized
    git_dir = Path(".git")
    if git_dir.exists():
        console.print("[yellow]Git repository already exists.[/yellow]")
        return
    
    # Initialize git
    console.print("[yellow]Initializing git repository...[/yellow]")
    subprocess.run(["git", "init"], check=True)
    
    if use_lfs:
        console.print("[yellow]Configuring Git LFS...[/yellow]")
        subprocess.run(["git", "lfs", "install"], check=True)
        
        # Create .gitattributes
        gitattributes = Path(".gitattributes")
        if not gitattributes.exists():
            console.print("[yellow]Creating .gitattributes...[/yellow]")
            gitattributes.write_text(LFS_GITATTRIBUTES)
    
    # Initial commit
    console.print("[yellow]Creating initial commit...[/yellow]")
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)
    
    console.print(f"[green]Git repository initialized successfully![/green]")
    console.print(f"[blue]Next steps:[/blue]")
    console.print(f"  1. Create repository on GitHub: https://github.com/new")
    console.print(f"  2. Add remote: git remote add origin https://github.com/RTPro256/{repo_name}.git")
    console.print(f"  3. Push: git push -u origin main")


LFS_GITATTRIBUTES = """# Git LFS Tracking Rules
# Large binary files
*.dll filter=lfs diff=lfs merge=lfs -text
*.pyd filter=lfs diff=lfs merge=lfs -text
*.so filter=lfs diff=lfs merge=lfs -text

# Large media files
*.png filter=lfs diff=lfs merge=lfs -text
*.jpg filter=lfs diff=lfs merge=lfs -text
*.gif filter=lfs diff=lfs merge=lfs -text

# Large data files
*.pkl filter=lfs diff=lfs merge=lfs -text
*.h5 filter=lfs diff=lfs merge=lfs -text
"""
```

### Update CLI Main

Register the new command group in the CLI:

```python
# Add to src/opencode/cli/main.py

from opencode.cli.commands.github import app as github_app

# In the main app registration
app.add_typer(github_app, name="github")
```

## Rollback Plan

If issues arise:

1. **Local repository issues**: Delete `.git/` and reinitialize
2. **Push rejected**: Force push with `git push -f origin main` (use with caution)
3. **LFS issues**: Use `git lfs migrate import` to convert existing files

## Security Considerations

1. **Never commit secrets**: Ensure `.gitignore` includes:
   - `.env`
   - `*.pem`
   - `*.key`
   - `secrets.*`

2. **Review before push**: Always review staged files with `git diff --staged`

3. **Use SSH or token authentication**: For secure GitHub access

## Success Criteria

- [x] Repository initialized locally with Git LFS
- [x] `.gitattributes` present with LFS rules
- [x] Clean commit history (503 files, 1.24 MiB)
- [x] Remote configured: `https://github.com/RTPro256/opencode_4py.git`
- [ ] **Repository created on GitHub** (USER ACTION REQUIRED)
- [ ] Push completed
- [ ] `opencode github` CLI commands available

## Timeline

| Phase | Estimated Time |
|-------|---------------|
| Phase 1: Preparation | 5 minutes |
| Phase 2: Repository Initialization | 5 minutes |
| Phase 3: Initial Commit | 2 minutes |
| Phase 4: GitHub Connection | 5 minutes |
| Phase 5: Verification | 5 minutes |
| **Total** | **~20-25 minutes** |

## Next Steps

1. Review and approve this plan
2. Execute Phase 1 (backup and cleanup)
3. Execute remaining phases
4. Implement CLI command feature (optional enhancement)

---

*Created: 2026-02-24*
*Author: OpenCode AI Assistant*
