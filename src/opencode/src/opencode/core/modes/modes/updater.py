"""
Updater Mode

Mode for updating opencode_4py installations in for_testing targets.
"""

from opencode.core.modes.base import Mode, ModeConfig, ModeToolAccess
from opencode.core.modes.registry import ModeRegistry


@ModeRegistry.register("updater")
class UpdaterMode(Mode):
    """
    Updater Mode - Update opencode_4py in for_testing targets.
    
    This mode is optimized for updating opencode_4py installations
    when changes are made to the source code. It handles:
    - Reinstalling from source
    - Copying documentation (README.md, MISSION.md)
    - Verifying updates
    - Troubleshooting update issues
    """
    
    _config = ModeConfig(
        name="updater",
        description="Update opencode_4py in for_testing targets",
        tool_access=ModeToolAccess.WHITELIST,
        allowed_tools={
            # File reading tools
            "read_file",
            "list_files",
            "search_files",
            # Execution tools
            "execute_command",
            # Interactive tools
            "ask_followup_question",
            "attempt_completion",
            "update_todo_list",
            # File writing (for updating configs)
            "write_file",
            "edit_file",
        },
        blocked_tools=set(),
        system_prompt_prefix=(
            "You are an AI assistant for the OpenCode Python project. "
            "Review README.md for project overview and MISSION.md for core principles. "
            "You are an update specialist. "
            "Your role is to help users update opencode_4py installations in for_testing targets. "
            "You understand the update process: uninstall, reinstall from source, verify. "
            "You ensure README.md and MISSION.md are copied to updated targets. "
            "You verify that agent modes have the correct system prompts referencing these documents."
        ),
        system_prompt_suffix=(
            "Follow the update plan in for_testing/as_dependency/ComfyUI_windows_portable/plans/UPDATE_OPENCODE_PLAN.md. "
            "Always verify updates by checking agent mode system prompts. "
            "Ensure README.md and MISSION.md are accessible in the target. "
            "Report any issues encountered during the update process."
        ),
        custom_instructions="",
        supports_images=False,
        supports_streaming=True,
    )
    
    @classmethod
    def get_config(cls) -> ModeConfig:
        """Return the configuration for this mode."""
        return cls._config
