"""
OpenCode Summaries Package
==========================

This package contains programmatic summaries of the project's
key documentation files (README.md and MISSION.md) for use
in code, tests, and documentation.

These summaries allow the project documentation to be accessed
programmatically throughout the codebase.
"""

from .README_summary import (
    __version__,
    __project__,
    __description__,
    FEATURES,
    PROVIDERS,
    CLI_COMMANDS,
    API_ENDPOINTS,
)

from .MISSION_summary import (
    CORE_PRINCIPLES,
    VIRTUES,
    SINS,
    PERSONAL_PREFERENCES,
    AUTHOR,
    ESTABLISHED_DATE,
    PLAN_TEMPLATE,
    AGENT_TEMPLATE,
)

__all__ = [
    # README summary
    "__version__",
    "__project__",
    "__description__",
    "FEATURES",
    "PROVIDERS",
    "CLI_COMMANDS",
    "API_ENDPOINTS",
    # MISSION summary
    "CORE_PRINCIPLES",
    "VIRTUES",
    "SINS",
    "PERSONAL_PREFERENCES",
    "AUTHOR",
    "ESTABLISHED_DATE",
    "PLAN_TEMPLATE",
    "AGENT_TEMPLATE",
]
