"""
Git integration tool for version control operations.

This tool provides git operations including status, diff, log, branch,
and commit operations.
"""

from pathlib import Path
from typing import Any, Optional

from opencode.tool.base import PermissionLevel, Tool, ToolResult


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

All operations are read-only by default unless explicitly allowed."""
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["status", "diff", "log", "branch", "add", "commit", "checkout", "pull", "push", "init"],
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
