"""
TUI widgets for OpenCode.
"""

from opencode.tui.widgets.chat import ChatWidget
from opencode.tui.widgets.sidebar import SidebarWidget
from opencode.tui.widgets.input import InputWidget
from opencode.tui.widgets.completion import (
    CompletionWidget,
    CompletionManager,
    CompletionProvider,
    CompletionItem,
    PathCompletionProvider,
    CommandCompletionProvider,
    MentionCompletionProvider,
)
from opencode.tui.widgets.approval import (
    ApprovalDialog,
    ApprovalManager,
    ApprovalRequest,
    ApprovalResponse,
    ApprovalStatus,
)
from opencode.tui.widgets.progress import (
    ProgressBarWidget,
    SpinnerWidget,
    StatusIndicator,
)

__all__ = [
    "ChatWidget",
    "SidebarWidget",
    "InputWidget",
    # Progress
    "ProgressBarWidget",
    "SpinnerWidget",
    "StatusIndicator",
    # Completion
    "CompletionWidget",
    "CompletionManager",
    "CompletionProvider",
    "CompletionItem",
    "PathCompletionProvider",
    "CommandCompletionProvider",
    "MentionCompletionProvider",
    # Approval
    "ApprovalDialog",
    "ApprovalManager",
    "ApprovalRequest",
    "ApprovalResponse",
    "ApprovalStatus",
]
