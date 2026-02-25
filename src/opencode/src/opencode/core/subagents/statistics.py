"""
Subagent statistics tracking.

Provides statistics and formatting for subagent execution.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any
from datetime import datetime


@dataclass
class ToolUsageStats:
    """Statistics for tool usage within a subagent execution."""
    tool_name: str
    call_count: int = 0
    success_count: int = 0
    error_count: int = 0
    total_duration_ms: float = 0.0
    avg_duration_ms: float = 0.0
    
    def record_call(self, success: bool, duration_ms: float) -> None:
        """Record a tool call.
        
        Args:
            success: Whether the call succeeded
            duration_ms: Duration in milliseconds
        """
        self.call_count += 1
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
        self.total_duration_ms += duration_ms
        self.avg_duration_ms = self.total_duration_ms / self.call_count


@dataclass
class SubagentStatsSummary:
    """Summary statistics for a subagent execution."""
    agent_name: str
    session_id: str
    start_time: datetime
    end_time: datetime = field(default_factory=datetime.now)
    
    # Token usage
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    
    # Execution stats
    total_rounds: int = 0
    total_tool_calls: int = 0
    successful_tool_calls: int = 0
    failed_tool_calls: int = 0
    
    # Tool breakdown
    tool_stats: Dict[str, ToolUsageStats] = field(default_factory=dict)
    
    # Result
    success: bool = False
    error_message: str = ""
    
    @property
    def duration_seconds(self) -> float:
        """Get total duration in seconds."""
        return (self.end_time - self.start_time).total_seconds()
    
    @property
    def tokens_per_second(self) -> float:
        """Get tokens per second rate."""
        duration = self.duration_seconds
        if duration > 0:
            return self.total_tokens / duration
        return 0.0
    
    def record_tool_call(
        self,
        tool_name: str,
        success: bool,
        duration_ms: float
    ) -> None:
        """Record a tool call.
        
        Args:
            tool_name: Name of the tool
            success: Whether the call succeeded
            duration_ms: Duration in milliseconds
        """
        self.total_tool_calls += 1
        if success:
            self.successful_tool_calls += 1
        else:
            self.failed_tool_calls += 1
        
        # Update tool-specific stats
        if tool_name not in self.tool_stats:
            self.tool_stats[tool_name] = ToolUsageStats(tool_name=tool_name)
        self.tool_stats[tool_name].record_call(success, duration_ms)
    
    def update_tokens(self, input_tokens: int, output_tokens: int) -> None:
        """Update token counts.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        """
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_tokens = self.input_tokens + self.output_tokens
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization.
        
        Returns:
            Dictionary representation
        """
        return {
            "agent_name": self.agent_name,
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_seconds": self.duration_seconds,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "tokens_per_second": self.tokens_per_second,
            "total_rounds": self.total_rounds,
            "total_tool_calls": self.total_tool_calls,
            "successful_tool_calls": self.successful_tool_calls,
            "failed_tool_calls": self.failed_tool_calls,
            "tool_stats": {
                name: {
                    "call_count": stats.call_count,
                    "success_count": stats.success_count,
                    "error_count": stats.error_count,
                    "avg_duration_ms": stats.avg_duration_ms,
                }
                for name, stats in self.tool_stats.items()
            },
            "success": self.success,
            "error_message": self.error_message,
        }
    
    def format_summary(self) -> str:
        """Format a human-readable summary.
        
        Returns:
            Formatted summary string
        """
        lines = [
            f"Subagent: {self.agent_name}",
            f"Duration: {self.duration_seconds:.2f}s",
            f"Tokens: {self.total_tokens:,} ({self.input_tokens:,} in / {self.output_tokens:,} out)",
            f"Rounds: {self.total_rounds}",
            f"Tool Calls: {self.total_tool_calls} ({self.successful_tool_calls} success / {self.failed_tool_calls} failed)",
        ]
        
        if self.tool_stats:
            lines.append("\nTool Breakdown:")
            for name, stats in sorted(self.tool_stats.items(), key=lambda x: x[1].call_count, reverse=True):
                lines.append(f"  - {name}: {stats.call_count} calls, {stats.avg_duration_ms:.1f}ms avg")
        
        if not self.success:
            lines.append(f"\nError: {self.error_message}")
        
        return "\n".join(lines)
