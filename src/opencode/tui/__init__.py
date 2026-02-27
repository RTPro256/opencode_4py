"""
Terminal User Interface for OpenCode.

Built with Textual for a rich, interactive terminal experience.
"""

from opencode.tui.app import OpenCodeApp
from opencode.tui.widgets.chat import ChatWidget
from opencode.tui.widgets.sidebar import SidebarWidget
from opencode.tui.widgets.input import InputWidget

__all__ = [
    "OpenCodeApp",
    "ChatWidget",
    "SidebarWidget",
    "InputWidget",
]
