"""
Code Mode

Default mode for everyday coding, edits, and file operations.
"""

from opencode.core.modes.base import Mode, ModeConfig, ModeToolAccess
from opencode.core.modes.registry import ModeRegistry


@ModeRegistry.register("code")
class CodeMode(Mode):
    """
    Code Mode - Everyday coding, edits, and file operations.
    
    This is the default mode with full access to all tools.
    Optimized for general coding tasks, file operations, and
    development workflows.
    """
    
    _config = ModeConfig(
        name="code",
        description="Everyday coding, edits, and file operations",
        tool_access=ModeToolAccess.ALL,
        allowed_tools=set(),  # All tools allowed
        blocked_tools=set(),  # No tools blocked
        system_prompt_prefix=(
            "You are an AI assistant for the OpenCode Python project. "
            "Review README.md for project overview and MISSION.md for core principles. "
        ),
        system_prompt_suffix=(
            "You are an expert software developer. "
            "Focus on writing clean, efficient, and well-documented code. "
            "Follow best practices and coding standards. "
            "When making changes, consider the broader context and potential impacts."
        ),
        custom_instructions="",
        supports_images=True,
        supports_streaming=True,
    )
    
    @classmethod
    def get_config(cls) -> ModeConfig:
        """Return the configuration for this mode."""
        return cls._config
