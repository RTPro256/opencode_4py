"""
Ask Mode

Mode for fast answers and explanations.
"""

from opencode.core.modes.base import Mode, ModeConfig, ModeToolAccess
from opencode.core.modes.registry import ModeRegistry


@ModeRegistry.register("ask")
class AskMode(Mode):
    """
    Ask Mode - Fast answers and explanations.
    
    This mode is optimized for quick questions and explanations.
    Has limited tool access to provide fast, focused responses.
    """
    
    _config = ModeConfig(
        name="ask",
        description="Fast answers and explanations",
        tool_access=ModeToolAccess.WHITELIST,
        allowed_tools={
            # File reading tools (for context)
            "read_file",
            "search_files",
            # Interactive tools
            "ask_followup_question",
            "attempt_completion",
        },
        blocked_tools=set(),
        system_prompt_prefix=(
            "You are an AI assistant for the OpenCode Python project. "
            "Review README.md for project overview and MISSION.md for core principles. "
            "You are a helpful assistant. "
            "Provide concise, accurate answers to questions. "
            "Focus on clarity and brevity. "
            "Explain concepts in simple terms when appropriate."
        ),
        system_prompt_suffix=(
            "Be concise and direct. "
            "Avoid unnecessary elaboration. "
            "If you need more context, ask clarifying questions."
        ),
        custom_instructions="",
        max_tokens=2000,  # Shorter responses
        temperature=0.3,  # More focused responses
        supports_images=True,
        supports_streaming=True,
    )
    
    @classmethod
    def get_config(cls) -> ModeConfig:
        """Return the configuration for this mode."""
        return cls._config
