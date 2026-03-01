"""
Configuration for the multi-agent module.

Based on overstory (https://github.com/jayminwest/overstory)
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class MultiAgentConfig(BaseModel):
    """Configuration for the multi-agent system."""
    
    # Directory settings
    base_dir: str = Field(
        default=".overstory",
        description="Base directory for multi-agent files"
    )
    
    worktree_base: str = Field(
        default=".overstory/worktrees",
        description="Base directory for agent worktrees"
    )
    
    # Database settings
    message_db_path: str = Field(
        default=".overstory/mail.db",
        description="Path to message database"
    )
    
    # Agent settings
    default_runtime: str = Field(
        default="claude",
        description="Default AI runtime (claude, pi, copilot, codex)"
    )
    
    max_agents_per_run: int = Field(
        default=25,
        description="Maximum number of agents per run"
    )
    
    max_depth: int = Field(
        default=2,
        description="Maximum agent hierarchy depth"
    )
    
    # Cost settings
    max_cost_per_run: float = Field(
        default=100.0,
        description="Maximum cost per run in USD"
    )
    
    cost_warning_threshold: float = Field(
        default=0.8,
        description="Warn when cost exceeds this fraction of max_cost_per_run"
    )
    
    # Timeout settings
    agent_timeout_minutes: int = Field(
        default=60,
        description="Agent timeout in minutes"
    )
    
    message_poll_interval_ms: int = Field(
        default=3000,
        description="Message polling interval in milliseconds"
    )
    
    # Watchdog settings
    watchdog_enabled: bool = Field(
        default=True,
        description="Enable watchdog daemon"
    )
    
    watchdog_interval_seconds: int = Field(
        default=60,
        description="Watchdog check interval in seconds"
    )
    
    # Merge settings
    auto_merge_enabled: bool = Field(
        default=False,
        description="Enable automatic merging"
    )
    
    conflict_resolution_tiers: List[str] = Field(
        default=["auto", "heuristic", "agent", "human"],
        description="Conflict resolution tiers in order"
    )
    
    # Hook settings
    hooks_enabled: bool = Field(
        default=False,
        description="Enable Claude Code hooks"
    )
    
    hooks_path: str = Field(
        default=".claude/settings.local.json",
        description="Path to hooks configuration"
    )
    
    # Monitoring settings
    dashboard_enabled: bool = Field(
        default=True,
        description="Enable dashboard"
    )
    
    dashboard_interval_ms: int = Field(
        default=3000,
        description="Dashboard refresh interval"
    )
    
    # Quality gates
    quality_gates: List[str] = Field(
        default=["lint", "tests"],
        description="Quality gates to run before merge"
    )
    
    class Config:
        frozen = False
    
    def get_worktree_path(self, agent_id: str) -> str:
        """Get the worktree path for an agent."""
        return f"{self.worktree_base}/{agent_id}"
    
    def validate_settings(self) -> List[str]:
        """
        Validate configuration settings.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if self.max_agents_per_run < 1:
            errors.append("max_agents_per_run must be at least 1")
        
        if self.max_depth < 1:
            errors.append("max_depth must be at least 1")
        
        if self.max_cost_per_run <= 0:
            errors.append("max_cost_per_run must be positive")
        
        if self.agent_timeout_minutes < 1:
            errors.append("agent_timeout_minutes must be at least 1")
        
        return errors
