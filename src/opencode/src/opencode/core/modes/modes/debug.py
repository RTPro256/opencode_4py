"""
Debug Mode

Mode for issue tracing, logging, and root cause analysis.
"""

from opencode.core.modes.base import Mode, ModeConfig, ModeToolAccess
from opencode.core.modes.registry import ModeRegistry


@ModeRegistry.register("debug")
class DebugMode(Mode):
    """
    Debug Mode - Trace issues and isolate root causes.
    
    This mode is optimized for debugging and troubleshooting.
    Has access to tools useful for investigating issues.
    Includes RAG access for troubleshooting knowledge base.
    """
    
    _config = ModeConfig(
        name="debug",
        description="Trace issues and isolate root causes",
        tool_access=ModeToolAccess.WHITELIST,
        allowed_tools={
            # File reading tools
            "read_file",
            "list_files",
            "search_files",
            "codebase_search",
            # Execution tools
            "execute_command",
            # Interactive tools
            "ask_followup_question",
            "attempt_completion",
            "update_todo_list",
            # Git tools (for history/blame)
            "git_diff",
            "git_log",
            "git_blame",
            # RAG tools for troubleshooting knowledge
            "rag_query",
            "rag_search",
        },
        blocked_tools=set(),
        system_prompt_prefix=(
            "You are an AI assistant for the OpenCode Python project. "
            "Review README.md for project overview and MISSION.md for core principles. "
            "You are a debugging specialist. "
            "Your role is to systematically investigate issues, identify root causes, "
            "and propose solutions. "
            "Follow a methodical approach: reproduce, isolate, analyze, fix. "
            "Use logs, stack traces, and code inspection to diagnose problems. "
            "IMPORTANT: Always query the troubleshooting RAG first when encountering "
            "known error patterns. Use 'rag_query --agent troubleshooting <symptom>' "
            "to find relevant error documents with fixes."
        ),
        system_prompt_suffix=(
            "Focus on systematic debugging. "
            "Start by understanding the problem, then narrow down the cause. "
            "Query the troubleshooting RAG for known errors before investigating manually. "
            "Propose specific, actionable fixes. "
            "Consider edge cases and potential side effects of fixes."
        ),
        custom_instructions="",
        supports_images=True,
        supports_streaming=True,
        rag_agents=["troubleshooting"],  # RAG agents available to this mode
    )
    
    @classmethod
    def get_config(cls) -> ModeConfig:
        """Return the configuration for this mode."""
        return cls._config
