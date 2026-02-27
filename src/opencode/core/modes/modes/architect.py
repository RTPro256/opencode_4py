"""
Architect Mode

Mode for planning, specs, and migrations.
"""

from opencode.core.modes.base import Mode, ModeConfig, ModeToolAccess
from opencode.core.modes.registry import ModeRegistry


@ModeRegistry.register("architect")
class ArchitectMode(Mode):
    """
    Architect Mode - Planning, specs, and migrations.
    
    This mode is optimized for high-level planning, system design,
    and architectural decisions. Has limited tool access to focus
    on planning rather than implementation.
    """
    
    _config = ModeConfig(
        name="architect",
        description="Plan systems, specs, and migrations",
        tool_access=ModeToolAccess.WHITELIST,
        allowed_tools={
            # File reading tools
            "read_file",
            "list_files",
            "search_files",
            "codebase_search",
            # Interactive tools
            "ask_followup_question",
            "attempt_completion",
            "update_todo_list",
            # Planning tools
            "write_file",  # For creating specs and docs
        },
        blocked_tools=set(),
        system_prompt_prefix=(
            "You are an AI assistant for the OpenCode Python project. "
            "Review README.md for project overview and MISSION.md for core principles. "
            "You are a software architect. "
            "Your role is to plan, design, and document software systems. "
            "Focus on high-level architecture, design patterns, and best practices. "
            "Create clear specifications and documentation. "
            "Consider scalability, maintainability, and trade-offs in your recommendations."
        ),
        system_prompt_suffix=(
            "Focus on planning and documentation. "
            "Avoid implementation details unless specifically asked. "
            "Provide clear, actionable recommendations."
        ),
        custom_instructions="",
        supports_images=True,
        supports_streaming=True,
    )
    
    @classmethod
    def get_config(cls) -> ModeConfig:
        """Return the configuration for this mode."""
        return cls._config
