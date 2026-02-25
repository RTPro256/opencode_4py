"""
Review Mode

Mode for reviewing code changes, plans, documents, and goals.
"""

from opencode.core.modes.base import Mode, ModeConfig, ModeToolAccess
from opencode.core.modes.registry import ModeRegistry


@ModeRegistry.register("review")
class ReviewMode(Mode):
    """
    Review Mode - Review code changes, plans, documents, and goals.
    
    This mode is optimized for reviewing and validating work products.
    Has read-only access to prevent accidental modifications during review.
    Focuses on accuracy, completeness, and quality assessment.
    """
    
    _config = ModeConfig(
        name="review",
        description="Review code changes, plans, documents, and goals for accuracy",
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
            # Git tools for reviewing changes
            "git_diff",
            "git_log",
            "git_blame",
            # Comparison tools
            "diff_files",
        },
        blocked_tools={
            # Block write tools to ensure read-only review
            "write_file",
            "edit_file",
            "delete_file",
            "execute_command",
        },
        system_prompt_prefix=(
            "You are an AI assistant for the OpenCode Python project. "
            "Review README.md for project overview and MISSION.md for core principles. "
            "You are a code reviewer and quality assurance specialist. "
            "Your role is to review code changes, plans, documents, and goals for accuracy, "
            "completeness, and quality. "
            "Identify issues, inconsistencies, and areas for improvement. "
            "Provide constructive feedback with specific recommendations. "
            "Focus on: correctness, security, performance, maintainability, and best practices."
        ),
        system_prompt_suffix=(
            "Be thorough but fair in your reviews. "
            "Prioritize issues by severity (critical, major, minor, suggestion). "
            "Provide actionable feedback with specific line references when possible. "
            "Acknowledge good practices and improvements. "
            "Consider the broader context and project goals."
        ),
        custom_instructions="",
        supports_images=True,
        supports_streaming=True,
    )
    
    @classmethod
    def get_config(cls) -> ModeConfig:
        """Return the configuration for this mode."""
        return cls._config
