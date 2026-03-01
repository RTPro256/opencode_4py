"""
Configuration for the memory module.

Based on beads (https://github.com/steveyegge/beads)
"""

from typing import Optional
from pydantic import BaseModel, Field


class MemoryConfig(BaseModel):
    """Configuration for the memory module."""
    
    # Database settings
    db_path: str = Field(
        default=".beads/memory.db",
        description="Path to SQLite database file"
    )
    
    # ID generation settings
    id_prefix: str = Field(
        default="bd",
        description="Prefix for task IDs"
    )
    
    # Task settings
    default_priority: int = Field(
        default=2,
        ge=0,
        le=4,
        description="Default priority for new tasks (0=P0 highest)"
    )
    
    # Memory compaction settings
    compaction_enabled: bool = Field(
        default=True,
        description="Enable automatic memory compaction"
    )
    compaction_threshold_days: int = Field(
        default=30,
        description="Days after which closed tasks can be compacted"
    )
    max_context_tasks: int = Field(
        default=100,
        description="Maximum number of tasks to keep in context"
    )
    
    # Stealth mode
    stealth_mode: bool = Field(
        default=False,
        description="Run locally without committing to main repo"
    )
    
    # Contributor vs Maintainer mode
    # When working on open-source projects:
    # - Contributors (forked repos): Use separate namespace
    # - Maintainers (write access): Use main repository
    role: str = Field(
        default="maintainer",
        description="Role: 'maintainer' or 'contributor'"
    )
    
    # Contributor namespace (for forked repos)
    contributor_namespace: Optional[str] = Field(
        default=None,
        description="Separate namespace for contributors (e.g., '~/.beads-planning')"
    )
    
    # Backend settings
    backend: str = Field(
        default="sqlite",
        description="Storage backend: 'sqlite' or 'dolt'"
    )
    
    # Dolt settings (optional)
    dolt_data_dir: Optional[str] = Field(
        default=None,
        description="Custom Dolt data directory"
    )
    dolt_database: Optional[str] = Field(
        default=None,
        description="Dolt database name"
    )
    
    class Config:
        frozen = False
    
    def get_db_path(self) -> str:
        """Get the effective database path."""
        if self.stealth_mode or self.role == "contributor":
            # Use separate directory for stealth/contributor mode
            if self.contributor_namespace:
                return f"{self.contributor_namespace}/memory.db"
            else:
                return ".beads-local/memory.db"
        return self.db_path
    
    def is_contributor_mode(self) -> bool:
        """Check if running in contributor mode."""
        return self.role == "contributor" or self.stealth_mode
