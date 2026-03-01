"""
Git worktree management for agent isolation.

Based on overstory (https://github.com/jayminwest/overstory)

Provides worktree isolation for agents to prevent conflicting changes.
"""

import subprocess
import os
from pathlib import Path
from typing import Optional, List
import uuid

from .models import Worktree


class WorktreeManager:
    """
    Manages git worktrees for agent isolation.
    
    Each agent gets its own worktree to work in, preventing
    conflicting changes during multi-agent workflows.
    """
    
    def __init__(self, base_path: str = ".overstory/worktrees"):
        """
        Initialize the worktree manager.
        
        Args:
            base_path: Base directory for worktrees
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def create_worktree(
        self,
        agent_id: str,
        branch: Optional[str] = None,
        from_branch: str = "main",
    ) -> Worktree:
        """
        Create a new worktree for an agent.
        
        Args:
            agent_id: Agent ID to create worktree for
            branch: Branch name (auto-generated if not provided)
            from_branch: Branch to create from
        
        Returns:
            Worktree object
        """
        # Generate branch name if not provided
        if branch is None:
            branch = f"agent/{agent_id}"
        
        worktree_path = self.base_path / agent_id
        
        # Create the worktree
        try:
            subprocess.run(
                ["git", "worktree", "add", str(worktree_path), "-b", branch, from_branch],
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            # Worktree might already exist
            if worktree_path.exists():
                pass  # Continue, worktree exists
            else:
                raise RuntimeError(f"Failed to create worktree: {e}")
        
        # Get the current commit
        try:
            result = subprocess.run(
                ["git", "-C", str(worktree_path), "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            last_commit = result.stdout.strip()
        except subprocess.CalledProcessError:
            last_commit = None
        
        return Worktree(
            path=str(worktree_path),
            branch=branch,
            agent_id=agent_id,
            is_clean=True,
            last_commit=last_commit,
        )
    
    def remove_worktree(self, agent_id: str, force: bool = False):
        """
        Remove a worktree.
        
        Args:
            agent_id: Agent ID whose worktree to remove
            force: Force removal even with uncommitted changes
        """
        worktree_path = self.base_path / agent_id
        
        if not worktree_path.exists():
            return
        
        cmd = ["git", "worktree", "remove", str(worktree_path)]
        if force:
            cmd.append("--force")
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to remove worktree: {e}")
    
    def list_worktrees(self) -> List[Worktree]:
        """
        List all worktrees.
        
        Returns:
            List of worktree objects
        """
        worktrees = []
        
        if not self.base_path.exists():
            return worktrees
        
        for agent_dir in self.base_path.iterdir():
            if agent_dir.is_dir():
                agent_id = agent_dir.name
                
                # Get branch
                try:
                    result = subprocess.run(
                        ["git", "-C", str(agent_dir), "rev-parse", "--abbrev-ref", "HEAD"],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    branch = result.stdout.strip()
                except subprocess.CalledProcessError:
                    branch = "unknown"
                
                # Check if clean
                try:
                    result = subprocess.run(
                        ["git", "-C", str(agent_dir), "status", "--porcelain"],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    is_clean = len(result.stdout.strip()) == 0
                except subprocess.CalledProcessError:
                    is_clean = False
                
                worktrees.append(Worktree(
                    path=str(agent_dir),
                    branch=branch,
                    agent_id=agent_id,
                    is_clean=is_clean,
                ))
        
        return worktrees
    
    def get_worktree(self, agent_id: str) -> Optional[Worktree]:
        """Get a specific worktree by agent ID."""
        worktree_path = self.base_path / agent_id
        
        if not worktree_path.exists():
            return None
        
        worktrees = self.list_worktrees()
        for wt in worktrees:
            if wt.agent_id == agent_id:
                return wt
        
        return None
    
    def cleanup_completed(self) -> int:
        """
        Remove all completed worktrees.
        
        Returns:
            Number of worktrees cleaned up
        """
        count = 0
        worktrees = self.list_worktrees()
        
        for wt in worktrees:
            if wt.is_clean:
                self.remove_worktree(wt.agent_id)
                count += 1
        
        return count
