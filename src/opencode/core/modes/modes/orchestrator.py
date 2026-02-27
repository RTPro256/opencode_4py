"""
Orchestrator Mode

Mode for coordinating tasks across multiple modes and agents.
"""

from opencode.core.modes.base import Mode, ModeConfig, ModeToolAccess
from opencode.core.modes.registry import ModeRegistry


@ModeRegistry.register("orchestrator")
class OrchestratorMode(Mode):
    """
    Orchestrator Mode - Coordinate tasks across multiple modes and agents.
    
    This mode is optimized for managing complex workflows that require
    coordination between different specialized modes. It can delegate
    tasks to appropriate modes and aggregate results.
    """
    
    _config = ModeConfig(
        name="orchestrator",
        description="Coordinate tasks across multiple modes and agents",
        tool_access=ModeToolAccess.WHITELIST,
        allowed_tools={
            # File reading tools (for context)
            "read_file",
            "list_files",
            "search_files",
            "codebase_search",
            # Interactive tools
            "ask_followup_question",
            "attempt_completion",
            "update_todo_list",
            # Mode switching
            "switch_mode",
            # Task management
            "new_task",
            # Workflow tools
            "execute_workflow",
            "create_workflow",
            # Agent coordination
            "delegate_to_agent",
            "list_agents",
            "get_agent_status",
        },
        blocked_tools={
            # Block direct file modifications - delegate to Code mode instead
            "write_file",
            "edit_file",
            "delete_file",
        },
        system_prompt_prefix=(
            "You are an AI assistant for the OpenCode Python project. "
            "Review README.md for project overview and MISSION.md for core principles. "
            "You are a task orchestrator and workflow coordinator. "
            "Your role is to break down complex tasks into subtasks, "
            "delegate them to appropriate specialized modes, and coordinate "
            "the overall workflow. "
            "You understand the capabilities of each mode: "
            "- Architect: Planning, design, specifications "
            "- Code: Implementation, file operations "
            "- Debug: Troubleshooting, root cause analysis "
            "- Ask: Quick answers, explanations "
            "- Review: Quality assurance, accuracy validation "
            "Choose the right mode for each subtask and sequence them appropriately."
        ),
        system_prompt_suffix=(
            "Break complex tasks into clear, sequential subtasks. "
            "Delegate to specialized modes rather than doing everything yourself. "
            "Track progress and handle errors gracefully. "
            "Aggregate results from multiple modes into coherent outputs. "
            "Communicate the overall plan and progress to the user."
        ),
        custom_instructions="",
        supports_images=True,
        supports_streaming=True,
    )
    
    @classmethod
    def get_config(cls) -> ModeConfig:
        """Return the configuration for this mode."""
        return cls._config
