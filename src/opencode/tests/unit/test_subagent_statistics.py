"""
Unit tests for subagent statistics tracking.
"""

import pytest
from datetime import datetime, timedelta

from opencode.core.subagents.statistics import (
    ToolUsageStats,
    SubagentStatsSummary,
)


class TestToolUsageStats:
    """Tests for ToolUsageStats dataclass."""
    
    def test_creation(self):
        """Test creating ToolUsageStats."""
        stats = ToolUsageStats(tool_name="test_tool")
        
        assert stats.tool_name == "test_tool"
        assert stats.call_count == 0
        assert stats.success_count == 0
        assert stats.error_count == 0
        assert stats.total_duration_ms == 0.0
        assert stats.avg_duration_ms == 0.0
    
    def test_record_successful_call(self):
        """Test recording a successful tool call."""
        stats = ToolUsageStats(tool_name="test_tool")
        
        stats.record_call(success=True, duration_ms=100.0)
        
        assert stats.call_count == 1
        assert stats.success_count == 1
        assert stats.error_count == 0
        assert stats.total_duration_ms == 100.0
        assert stats.avg_duration_ms == 100.0
    
    def test_record_failed_call(self):
        """Test recording a failed tool call."""
        stats = ToolUsageStats(tool_name="test_tool")
        
        stats.record_call(success=False, duration_ms=50.0)
        
        assert stats.call_count == 1
        assert stats.success_count == 0
        assert stats.error_count == 1
        assert stats.total_duration_ms == 50.0
        assert stats.avg_duration_ms == 50.0
    
    def test_record_multiple_calls(self):
        """Test recording multiple tool calls."""
        stats = ToolUsageStats(tool_name="test_tool")
        
        stats.record_call(success=True, duration_ms=100.0)
        stats.record_call(success=True, duration_ms=200.0)
        stats.record_call(success=False, duration_ms=50.0)
        
        assert stats.call_count == 3
        assert stats.success_count == 2
        assert stats.error_count == 1
        assert stats.total_duration_ms == 350.0
        assert stats.avg_duration_ms == pytest.approx(350.0 / 3)


class TestSubagentStatsSummary:
    """Tests for SubagentStatsSummary dataclass."""
    
    def test_creation(self):
        """Test creating SubagentStatsSummary."""
        start = datetime.now()
        stats = SubagentStatsSummary(
            agent_name="test_agent",
            session_id="session-123",
            start_time=start,
        )
        
        assert stats.agent_name == "test_agent"
        assert stats.session_id == "session-123"
        assert stats.start_time == start
        assert stats.input_tokens == 0
        assert stats.output_tokens == 0
        assert stats.total_tokens == 0
        assert stats.total_rounds == 0
        assert stats.total_tool_calls == 0
        assert stats.successful_tool_calls == 0
        assert stats.failed_tool_calls == 0
        assert stats.success is False
        assert stats.error_message == ""
    
    def test_duration_seconds(self):
        """Test duration_seconds property."""
        start = datetime.now()
        end = start + timedelta(seconds=5.5)
        stats = SubagentStatsSummary(
            agent_name="test_agent",
            session_id="session-123",
            start_time=start,
            end_time=end,
        )
        
        assert stats.duration_seconds == pytest.approx(5.5)
    
    def test_tokens_per_second(self):
        """Test tokens_per_second property."""
        start = datetime.now()
        end = start + timedelta(seconds=10)
        stats = SubagentStatsSummary(
            agent_name="test_agent",
            session_id="session-123",
            start_time=start,
            end_time=end,
            input_tokens=500,
            output_tokens=500,
            total_tokens=1000,
        )
        
        assert stats.tokens_per_second == pytest.approx(100.0)
    
    def test_tokens_per_second_zero_duration(self):
        """Test tokens_per_second with zero duration."""
        start = datetime.now()
        stats = SubagentStatsSummary(
            agent_name="test_agent",
            session_id="session-123",
            start_time=start,
            end_time=start,  # Same time
            total_tokens=1000,
        )
        
        assert stats.tokens_per_second == 0.0
    
    def test_record_tool_call_success(self):
        """Test recording a successful tool call."""
        start = datetime.now()
        stats = SubagentStatsSummary(
            agent_name="test_agent",
            session_id="session-123",
            start_time=start,
        )
        
        stats.record_tool_call("file_read", success=True, duration_ms=50.0)
        
        assert stats.total_tool_calls == 1
        assert stats.successful_tool_calls == 1
        assert stats.failed_tool_calls == 0
        assert "file_read" in stats.tool_stats
        assert stats.tool_stats["file_read"].call_count == 1
    
    def test_record_tool_call_failure(self):
        """Test recording a failed tool call."""
        start = datetime.now()
        stats = SubagentStatsSummary(
            agent_name="test_agent",
            session_id="session-123",
            start_time=start,
        )
        
        stats.record_tool_call("file_write", success=False, duration_ms=100.0)
        
        assert stats.total_tool_calls == 1
        assert stats.successful_tool_calls == 0
        assert stats.failed_tool_calls == 1
        assert "file_write" in stats.tool_stats
    
    def test_record_multiple_tool_calls(self):
        """Test recording multiple tool calls."""
        start = datetime.now()
        stats = SubagentStatsSummary(
            agent_name="test_agent",
            session_id="session-123",
            start_time=start,
        )
        
        stats.record_tool_call("file_read", success=True, duration_ms=50.0)
        stats.record_tool_call("file_read", success=True, duration_ms=60.0)
        stats.record_tool_call("bash", success=False, duration_ms=200.0)
        
        assert stats.total_tool_calls == 3
        assert stats.successful_tool_calls == 2
        assert stats.failed_tool_calls == 1
        assert len(stats.tool_stats) == 2
        assert stats.tool_stats["file_read"].call_count == 2
    
    def test_update_tokens(self):
        """Test updating token counts."""
        start = datetime.now()
        stats = SubagentStatsSummary(
            agent_name="test_agent",
            session_id="session-123",
            start_time=start,
        )
        
        stats.update_tokens(input_tokens=100, output_tokens=50)
        
        assert stats.input_tokens == 100
        assert stats.output_tokens == 50
        assert stats.total_tokens == 150
        
        # Update again
        stats.update_tokens(input_tokens=50, output_tokens=25)
        
        assert stats.input_tokens == 150
        assert stats.output_tokens == 75
        assert stats.total_tokens == 225
    
    def test_to_dict(self):
        """Test converting to dictionary."""
        start = datetime(2024, 1, 1, 12, 0, 0)
        end = datetime(2024, 1, 1, 12, 0, 10)
        stats = SubagentStatsSummary(
            agent_name="test_agent",
            session_id="session-123",
            start_time=start,
            end_time=end,
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            total_rounds=3,
            total_tool_calls=5,
            successful_tool_calls=4,
            failed_tool_calls=1,
            success=True,
            error_message="",
        )
        stats.record_tool_call("file_read", success=True, duration_ms=50.0)
        
        data = stats.to_dict()
        
        assert data["agent_name"] == "test_agent"
        assert data["session_id"] == "session-123"
        assert data["start_time"] == "2024-01-01T12:00:00"
        assert data["end_time"] == "2024-01-01T12:00:10"
        assert data["duration_seconds"] == 10.0
        assert data["input_tokens"] == 100
        assert data["output_tokens"] == 50
        assert data["total_tokens"] == 150
        assert data["tokens_per_second"] == 15.0
        assert data["total_rounds"] == 3
        assert data["total_tool_calls"] == 6  # 5 + 1 from record_tool_call
        assert data["successful_tool_calls"] == 5
        assert data["failed_tool_calls"] == 1
        assert data["success"] is True
        assert data["error_message"] == ""
        assert "tool_stats" in data
        assert "file_read" in data["tool_stats"]
    
    def test_format_summary_success(self):
        """Test formatting summary for successful execution."""
        start = datetime.now()
        end = start + timedelta(seconds=5)
        stats = SubagentStatsSummary(
            agent_name="code_agent",
            session_id="session-123",
            start_time=start,
            end_time=end,
            input_tokens=500,
            output_tokens=250,
            total_tokens=750,
            total_rounds=3,
            total_tool_calls=10,
            successful_tool_calls=10,
            failed_tool_calls=0,
            success=True,
        )
        stats.record_tool_call("file_read", success=True, duration_ms=50.0)
        stats.record_tool_call("file_write", success=True, duration_ms=100.0)
        
        summary = stats.format_summary()
        
        assert "Subagent: code_agent" in summary
        assert "Duration:" in summary
        assert "Tokens: 750" in summary
        assert "500 in" in summary
        assert "250 out" in summary
        assert "Rounds: 3" in summary
        assert "Tool Calls:" in summary
        assert "Tool Breakdown:" in summary
        assert "file_read" in summary
        assert "file_write" in summary
        assert "Error:" not in summary  # No error for successful execution
    
    def test_format_summary_with_error(self):
        """Test formatting summary for failed execution."""
        start = datetime.now()
        end = start + timedelta(seconds=2)
        stats = SubagentStatsSummary(
            agent_name="debug_agent",
            session_id="session-456",
            start_time=start,
            end_time=end,
            input_tokens=200,
            output_tokens=100,
            total_tokens=300,
            total_rounds=1,
            total_tool_calls=2,
            successful_tool_calls=1,
            failed_tool_calls=1,
            success=False,
            error_message="Tool execution failed",
        )
        
        summary = stats.format_summary()
        
        assert "Subagent: debug_agent" in summary
        assert "Error: Tool execution failed" in summary
        assert "1 failed" in summary
    
    def test_format_summary_no_tools(self):
        """Test formatting summary with no tool calls."""
        start = datetime.now()
        end = start + timedelta(seconds=1)
        stats = SubagentStatsSummary(
            agent_name="ask_agent",
            session_id="session-789",
            start_time=start,
            end_time=end,
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            total_rounds=1,
            success=True,
        )
        
        summary = stats.format_summary()
        
        assert "Tool Calls: 0" in summary
        assert "Tool Breakdown:" not in summary  # No tools section when empty
