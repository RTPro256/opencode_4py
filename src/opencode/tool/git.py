"""
Git integration tool for version control operations.

This tool provides git operations including status, diff, log, branch,
and commit operations, as well as repository management for known GitHub repositories.

Repository management allows users to:
- List known repositories from config
- Add new repositories to the known list
- Remove repositories from the known list
- Configure git remotes for pushing to specific repositories
"""

import json
from pathlib import Path
from typing import Any, Optional

from opencode.tool.base import PermissionLevel, Tool, ToolResult


# Default config path for known repositories
DEFAULT_REPO_CONFIG = Path(__file__).parent.parent.parent.parent / "config" / "github_repos.json"


class GitTool(Tool):
    """Tool for git version control operations."""
    
    @property
    def name(self) -> str:
        return "git"
    
    @property
    def description(self) -> str:
        return """Git version control operations.

Supports common git operations:
- status: Show working tree status
- diff: Show changes between commits, commit and working tree
- log: Show commit logs
- branch: List, create, or delete branches
- add: Add files to staging
- commit: Record changes to the repository
- checkout: Switch branches or restore working tree files
- pull: Fetch from and integrate with another repository
- push: Update remote refs along with associated objects
- init: Initialize a new repository

Repository management operations:
- repos: List known repositories from config
- add-repo: Add a new repository to known list
- remove-repo: Remove a repository from known list
- push-to: Push to a specific named repository
- remotes: List git remotes
- set-remote: Configure a remote URL

All operations are read-only by default unless explicitly allowed."""
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": [
                        "status", "diff", "log", "branch", "add", "commit",
                        "checkout", "pull", "push", "init", "repos", "add-repo",
                        "remove-repo", "push-to", "remotes", "set-remote"
                    ],
                    "description": "The git operation to perform",
                },
                "path": {
                    "type": "string",
                    "description": "Path to the file or directory (optional)",
                },
                "branch": {
                    "type": "string",
                    "description": "Branch name for branch/checkout operations",
                },
                "message": {
                    "type": "string",
                    "description": "Commit message for commit operation",
                },
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of files for add operation",
                },
                "limit": {
                    "type": "integer",
                    "description": "Limit for log output (default: 10)",
                },
                "repo_name": {
                    "type": "string",
                    "description": "Repository name from known repositories",
                },
                "remote_url": {
                    "type": "string",
                    "description": "Git remote URL (https://github.com/owner/repo.git)",
                },
                "owner": {
                    "type": "string",
                    "description": "Repository owner (for add-repo operation)",
                },
                "remote_name": {
                    "type": "string",
                    "description": "Remote name (default: origin)",
                },
            },
            "required": ["operation"],
        }
    
    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.WRITE
    
    async def execute(self, **params: Any) -> ToolResult:
        """Execute a git operation."""
        import subprocess
        
        operation = params.get("operation", "")
        path = params.get("path", ".")
        branch = params.get("branch")
        message = params.get("message")
        files = params.get("files", [])
        limit = params.get("limit", 10)
        repo_name = params.get("repo_name")
        remote_url = params.get("remote_url")
        owner = params.get("owner")
        remote_name = params.get("remote_name", "origin")
        
        workdir = Path.cwd()
        
        try:
            if operation == "status":
                return await self._git_status(workdir)
            
            elif operation == "diff":
                return await self._git_diff(workdir, path)
            
            elif operation == "log":
                return await self._git_log(workdir, limit)
            
            elif operation == "branch":
                return await self._git_branch(workdir, branch)
            
            elif operation == "add":
                return await self._git_add(workdir, files if files else [path])
            
            elif operation == "commit":
                if not message:
                    return ToolResult.err("Commit message is required")
                return await self._git_commit(workdir, message)
            
            elif operation == "checkout":
                if not branch:
                    return ToolResult.err("Branch name is required for checkout")
                return await self._git_checkout(workdir, branch)
            
            elif operation == "pull":
                return await self._git_pull(workdir)
            
            elif operation == "push":
                return await self._git_push(workdir)
            
            elif operation == "init":
                return await self._git_init(workdir)
            
            # Repository management operations
            elif operation == "repos":
                return self._list_repos()
            
            elif operation == "add-repo":
                if not repo_name or not remote_url:
                    return ToolResult.err("repo_name and remote_url are required for add-repo")
                return self._add_repo(repo_name, remote_url, owner)
            
            elif operation == "remove-repo":
                if not repo_name:
                    return ToolResult.err("repo_name is required for remove-repo")
                return self._remove_repo(repo_name)
            
            elif operation == "push-to":
                if not repo_name:
                    return ToolResult.err("repo_name is required for push-to")
                return await self._git_push_to(workdir, repo_name, branch)
            
            elif operation == "remotes":
                return await self._git_remotes(workdir)
            
            elif operation == "set-remote":
                if not remote_url:
                    return ToolResult.err("remote_url is required for set-remote")
                return await self._git_set_remote(workdir, remote_name, remote_url)
            
            else:
                return ToolResult.err(f"Unknown git operation: {operation}")
        
        except FileNotFoundError:
            return ToolResult.err("Git is not installed or not found in PATH")
        except Exception as e:
            return ToolResult.err(f"Git operation failed: {e}")
    
    async def _run_git(self, workdir: Path, args: list[str]) -> tuple[int, str, str]:
        """Run a git command and return the result."""
        import subprocess
        
        result = subprocess.run(
            ["git"] + args,
            cwd=workdir,
            capture_output=True,
            text=True,
        )
        return result.returncode, result.stdout, result.stderr
    
    async def _git_status(self, workdir: Path) -> ToolResult:
        """Show git status."""
        returncode, stdout, stderr = await self._run_git(workdir, ["status", "--porcelain=v1"])
        
        if returncode != 0:
            return ToolResult.err(f"Git status failed: {stderr}")
        
        if not stdout.strip():
            return ToolResult.ok("Working tree clean - no changes")
        
        lines = stdout.strip().split("\n")
        output = f"Git Status ({len(lines)} changes):\n"
        
        for line in lines:
            status = line[:2]
            filepath = line[3:]
            
            status_map = {
                " M": "Modified",
                "M ": "Staged",
                "MM": "Staged + Modified",
                " A": "Added",
                "A ": "Staged (new)",
                " D": "Deleted",
                "D ": "Staged (deleted)",
                "??": "Untracked",
                "!!": "Ignored",
            }
            status_text = status_map.get(status, status)
            output += f"  [{status_text}] {filepath}\n"
        
        return ToolResult.ok(output)
    
    async def _git_diff(self, workdir: Path, path: str) -> ToolResult:
        """Show git diff."""
        args = ["diff"]
        if path and path != ".":
            args.append("--")
            args.append(path)
        
        returncode, stdout, stderr = await self._run_git(workdir, args)
        
        if returncode != 0:
            return ToolResult.err(f"Git diff failed: {stderr}")
        
        if not stdout.strip():
            return ToolResult.ok("No differences found")
        
        # Truncate if too long
        if len(stdout) > 5000:
            stdout = stdout[:5000] + "\n... (truncated)"
        
        return ToolResult.ok(f"Git Diff:\n{stdout}")
    
    async def _git_log(self, workdir: Path, limit: int) -> ToolResult:
        """Show git log."""
        args = ["log", f"-{limit}", "--oneline", "--decorate"]
        
        returncode, stdout, stderr = await self._run_git(workdir, args)
        
        if returncode != 0:
            return ToolResult.err(f"Git log failed: {stderr}")
        
        if not stdout.strip():
            return ToolResult.ok("No commits found")
        
        return ToolResult.ok(f"Git Log (last {limit} commits):\n{stdout}")
    
    async def _git_branch(self, workdir: Path, branch: Optional[str]) -> ToolResult:
        """List branches or create a new branch."""
        if branch:
            # Create new branch
            returncode, stdout, stderr = await self._run_git(workdir, ["checkout", "-b", branch])
            if returncode != 0:
                return ToolResult.err(f"Failed to create branch: {stderr}")
            return ToolResult.ok(f"Created and switched to branch: {branch}")
        
        # List branches
        returncode, stdout, stderr = await self._run_git(workdir, ["branch", "-a"])
        if returncode != 0:
            return ToolResult.err(f"Git branch failed: {stderr}")
        
        return ToolResult.ok(f"Git Branches:\n{stdout}")
    
    async def _git_add(self, workdir: Path, files: list[str]) -> ToolResult:
        """Add files to staging."""
        args = ["add"] + files
        returncode, stdout, stderr = await self._run_git(workdir, args)
        
        if returncode != 0:
            return ToolResult.err(f"Git add failed: {stderr}")
        
        return ToolResult.ok(f"Added {len(files)} file(s) to staging")
    
    async def _git_commit(self, workdir: Path, message: str) -> ToolResult:
        """Commit staged changes."""
        returncode, stdout, stderr = await self._run_git(workdir, ["commit", "-m", message])
        
        if returncode != 0:
            return ToolResult.err(f"Git commit failed: {stderr}")
        
        return ToolResult.ok(f"Committed: {message}")
    
    async def _git_checkout(self, workdir: Path, branch: str) -> ToolResult:
        """Switch branches."""
        returncode, stdout, stderr = await self._run_git(workdir, ["checkout", branch])
        
        if returncode != 0:
            return ToolResult.err(f"Git checkout failed: {stderr}")
        
        return ToolResult.ok(f"Switched to branch: {branch}")
    
    async def _git_pull(self, workdir: Path) -> ToolResult:
        """Pull from remote."""
        returncode, stdout, stderr = await self._run_git(workdir, ["pull"])
        
        if returncode != 0:
            return ToolResult.err(f"Git pull failed: {stderr}")
        
        return ToolResult.ok(f"Pulled from remote:\n{stdout}" if stdout else "Already up to date")
    
    async def _git_push(self, workdir: Path) -> ToolResult:
        """Push to remote."""
        returncode, stdout, stderr = await self._run_git(workdir, ["push"])
        
        if returncode != 0:
            return ToolResult.err(f"Git push failed: {stderr}")
        
        return ToolResult.ok(f"Pushed to remote:\n{stdout}" if stdout else "Push completed")
    
    async def _git_init(self, workdir: Path) -> ToolResult:
        """Initialize a git repository."""
        returncode, stdout, stderr = await self._run_git(workdir, ["init"])
        
        if returncode != 0:
            return ToolResult.err(f"Git init failed: {stderr}")
        
        return ToolResult.ok(f"Initialized git repository in {workdir}")

    # ==================== Repository Management Methods ====================

    def _load_repos_config(self) -> dict[str, Any]:
        """Load the repositories configuration from JSON file."""
        config_path = DEFAULT_REPO_CONFIG
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {"repositories": {}, "default_remote": "origin", "default_branch": "main"}

    def _save_repos_config(self, config: dict[str, Any]) -> ToolResult:
        """Save the repositories configuration to JSON file."""
        config_path = DEFAULT_REPO_CONFIG
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)
            return ToolResult.ok(f"Saved configuration to {config_path}")
        except IOError as e:
            return ToolResult.err(f"Failed to save config: {e}")

    def _list_repos(self) -> ToolResult:
        """List known repositories from configuration."""
        config = self._load_repos_config()
        repos = config.get("repositories", {})

        if not repos:
            return ToolResult.ok("No known repositories. Use add-repo to add one.")

        output = "Known Repositories:\n"
        for name, info in repos.items():
            url = info.get("url", "N/A")
            owner = info.get("owner", "N/A")
            desc = info.get("description", "")
            output += f"\n  [{name}]\n"
            output += f"    Owner: {owner}\n"
            output += f"    URL: {url}\n"
            if desc:
                output += f"    Description: {desc}\n"

        return ToolResult.ok(output)

    def _add_repo(self, repo_name: str, remote_url: str, owner: Optional[str] = None) -> ToolResult:
        """Add a new repository to the known list."""
        config = self._load_repos_config()

        if repo_name in config.get("repositories", {}):
            return ToolResult.err(f"Repository '{repo_name}' already exists. Use remove-repo first.")

        # Extract owner from URL if not provided
        if not owner:
            # Try to extract from URL like https://github.com/owner/repo.git
            parts = remote_url.replace(".git", "").split("/")
            if len(parts) >= 2:
                owner = parts[-2]
            else:
                owner = "unknown"

        if "repositories" not in config:
            config["repositories"] = {}

        config["repositories"][repo_name] = {
            "url": remote_url,
            "owner": owner,
            "name": repo_name,
            "description": f"Repository: {repo_name}"
        }

        return self._save_repos_config(config)

    def _remove_repo(self, repo_name: str) -> ToolResult:
        """Remove a repository from the known list."""
        config = self._load_repos_config()
        repos = config.get("repositories", {})

        if repo_name not in repos:
            return ToolResult.err(f"Repository '{repo_name}' not found in known list.")

        del repos[repo_name]
        config["repositories"] = repos

        return self._save_repos_config(config)

    async def _git_push_to(self, workdir: Path, repo_name: str, branch: Optional[str] = None) -> ToolResult:
        """Push to a specific named repository."""
        config = self._load_repos_config()
        repos = config.get("repositories", {})

        if repo_name not in repos:
            return ToolResult.err(
                f"Repository '{repo_name}' not found. Use 'repos' to list known repos "
                f"or 'add-repo' to add a new one."
            )

        repo_info = repos[repo_name]
        remote_url = repo_info.get("url")

        if not remote_url:
            return ToolResult.err(f"Repository '{repo_name}' has no URL configured.")

        # Check if remote already exists and get its URL
        returncode, stdout, stderr = await self._run_git(workdir, ["remote", "get-url", "origin"])

        if returncode == 0 and stdout.strip() != remote_url:
            # Remote exists but URL is different, update it
            returncode, _, stderr = await self._run_git(workdir, ["remote", "set-url", "origin", remote_url])
            if returncode != 0:
                return ToolResult.err(f"Failed to update remote: {stderr}")
        elif returncode != 0:
            # Remote doesn't exist, add it
            returncode, _, stderr = await self._run_git(workdir, ["remote", "add", "origin", remote_url])
            if returncode != 0:
                return ToolResult.err(f"Failed to add remote: {stderr}")

        # Push to the remote
        branch = branch or config.get("default_branch", "main")
        returncode, stdout, stderr = await self._run_git(workdir, ["push", "origin", str(branch)])

        if returncode != 0:
            return ToolResult.err(f"Push failed: {stderr}")

        return ToolResult.ok(f"Pushed to {repo_name} ({remote_url}) on branch {branch}")

    async def _git_remotes(self, workdir: Path) -> ToolResult:
        """List git remotes."""
        returncode, stdout, stderr = await self._run_git(workdir, ["remote", "-v"])

        if returncode != 0:
            return ToolResult.err(f"Failed to list remotes: {stderr}")

        if not stdout.strip():
            return ToolResult.ok("No remotes configured.")

        return ToolResult.ok(f"Git Remotes:\n{stdout}")

    async def _git_set_remote(self, workdir: Path, remote_name: str, remote_url: str) -> ToolResult:
        """Configure a git remote URL."""
        # Check if remote exists
        returncode, stdout, stderr = await self._run_git(workdir, ["remote", "get-url", remote_name])

        if returncode == 0:
            # Remote exists, update URL
            returncode, _, stderr = await self._run_git(workdir, ["remote", "set-url", remote_name, remote_url])
            if returncode != 0:
                return ToolResult.err(f"Failed to update remote: {stderr}")
            return ToolResult.ok(f"Updated remote '{remote_name}' to {remote_url}")
        else:
            # Remote doesn't exist, add it
            returncode, _, stderr = await self._run_git(workdir, ["remote", "add", remote_name, remote_url])
            if returncode != 0:
                return ToolResult.err(f"Failed to add remote: {stderr}")
            return ToolResult.ok(f"Added remote '{remote_name}' at {remote_url}")
