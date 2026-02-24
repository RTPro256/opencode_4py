"""
Workflow Tools Package

This package contains tool implementations for the workflow engine,
inspired by agentic-signal's tool system.

Available Tools:
- BraveSearchTool: Brave Search API integration
- DuckDuckGoSearchTool: DuckDuckGo search (no API key required)
- WeatherTool: Weather data fetching
- CsvArrayTool: CSV/Array utilities
- GoogleCalendarTool: Google Calendar API (requires OAuth)
- GoogleDriveTool: Google Drive API (requires OAuth)
- GmailTool: Gmail API (requires OAuth)
"""

from opencode.workflow.tools.registry import ToolRegistry, BaseTool, ToolResult
from opencode.workflow.tools.brave_search import BraveSearchTool
from opencode.workflow.tools.duckduckgo_search import DuckDuckGoSearchTool
from opencode.workflow.tools.weather import WeatherTool
from opencode.workflow.tools.csv_array import CsvArrayTool

__all__ = [
    "ToolRegistry",
    "BaseTool",
    "ToolResult",
    "BraveSearchTool",
    "DuckDuckGoSearchTool",
    "WeatherTool",
    "CsvArrayTool",
]
