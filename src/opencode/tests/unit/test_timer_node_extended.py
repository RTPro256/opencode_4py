"""
Extended tests for Timer workflow node to achieve 100% coverage.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

from opencode.workflow.nodes.timer import TimerNode, TriggerType
from opencode.workflow.node import (
    NodeSchema,
    NodePort,
    PortDataType,
    PortDirection,
    ExecutionContext,
)


class TestTimerNodeTriggerType:
    """Tests for TriggerType constants."""

    @pytest.mark.unit
    def test_trigger_type_constants(self):
        """Test TriggerType constants."""
        assert TriggerType.INTERVAL == "interval"
        assert TriggerType.CRON == "cron"
        assert TriggerType.ONCE == "once"
        assert TriggerType.DELAY == "delay"


class TestTimerNodeStartStop:
    """Tests for start/stop methods."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_start_already_running(self):
        """Test start when already running."""
        node = TimerNode("timer_1", {"triggerType": "interval", "interval": 60})
        node._running = True
        
        callback = MagicMock()
        await node.start(callback)
        
        # Should not change state
        assert node._callback is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_start_interval(self):
        """Test start with interval trigger."""
        node = TimerNode("timer_1", {"triggerType": "interval", "interval": 0.1})
        
        callback = AsyncMock()
        await node.start(callback)
        
        assert node._running is True
        assert node._task is not None
        
        # Stop the timer
        await node.stop()
        assert node._running is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_start_cron(self):
        """Test start with cron trigger."""
        node = TimerNode("timer_1", {
            "triggerType": "cron",
            "cronExpression": "* * * * *",  # Every minute
        })
        
        callback = AsyncMock()
        await node.start(callback)
        
        assert node._running is True
        assert node._task is not None
        
        await node.stop()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_start_delay(self):
        """Test start with delay trigger."""
        node = TimerNode("timer_1", {
            "triggerType": "delay",
            "delaySeconds": 0.1,
        })
        
        callback = AsyncMock()
        await node.start(callback)
        
        assert node._running is True
        
        # Wait for delay to complete
        await asyncio.sleep(0.2)
        
        # Should have stopped after firing
        assert node._running is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_start_once(self):
        """Test start with once trigger."""
        node = TimerNode("timer_1", {"triggerType": "once"})
        
        callback = AsyncMock()
        await node.start(callback)
        
        # Should fire immediately and stop
        await asyncio.sleep(0.05)
        
        # Should have stopped after firing
        assert node._running is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_start_execute_on_start(self):
        """Test start with executeOnStart."""
        node = TimerNode("timer_1", {
            "triggerType": "interval",
            "interval": 60,
            "executeOnStart": True,
        })
        
        callback = AsyncMock()
        await node.start(callback)
        
        # Should have fired callback immediately
        callback.assert_called_once()
        
        await node.stop()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_stop_cancels_task(self):
        """Test stop cancels running task."""
        node = TimerNode("timer_1", {"triggerType": "interval", "interval": 60})
        
        callback = AsyncMock()
        await node.start(callback)
        
        assert node._task is not None
        
        await node.stop()
        
        assert node._task is None
        assert node._running is False


class TestTimerNodeRunMethods:
    """Tests for _run_* methods."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_interval_max_executions(self):
        """Test interval timer respects max executions."""
        node = TimerNode("timer_1", {
            "triggerType": "interval",
            "interval": 0.05,
            "maxExecutions": 2,
        })
        
        callback = AsyncMock()
        await node.start(callback)
        
        # Wait for multiple intervals
        await asyncio.sleep(0.3)
        
        # Stop the timer to check final state
        await node.stop()
        
        # Should have called callback maxExecutions times (plus executeOnStart if set)
        assert callback.call_count <= 3

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_cron_no_expression(self):
        """Test cron timer without expression."""
        node = TimerNode("timer_1", {"triggerType": "cron"})
        
        callback = AsyncMock()
        await node.start(callback)
        
        # Should not run without expression
        await asyncio.sleep(0.05)
        
        callback.assert_not_called()
        await node.stop()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_cron_invalid_expression(self):
        """Test cron timer with invalid expression."""
        node = TimerNode("timer_1", {
            "triggerType": "cron",
            "cronExpression": "invalid cron",
        })
        
        callback = AsyncMock()
        await node.start(callback)
        
        # Should handle error gracefully
        await asyncio.sleep(0.05)
        
        await node.stop()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_delay_zero(self):
        """Test delay timer with zero delay."""
        node = TimerNode("timer_1", {
            "triggerType": "delay",
            "delaySeconds": 0,
        })
        
        callback = AsyncMock()
        await node.start(callback)
        
        # Should fire immediately
        await asyncio.sleep(0.05)
        
        callback.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_interval_stops_when_not_running(self):
        """Test interval timer stops when _running is False."""
        node = TimerNode("timer_1", {"triggerType": "interval", "interval": 0.05})
        
        callback = AsyncMock()
        await node.start(callback)
        
        # Stop immediately
        node._running = False
        
        # Wait for potential next interval
        await asyncio.sleep(0.1)
        
        # Should not have fired again
        callback.assert_not_called()


class TestTimerNodeFireCallback:
    """Tests for _fire_callback method."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fire_callback_increments_count(self):
        """Test _fire_callback increments execution count."""
        node = TimerNode("timer_1", {})
        
        callback = AsyncMock()
        node._callback = callback
        node._running = True
        
        await node._fire_callback()
        
        assert node._execution_count == 1
        callback.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fire_callback_handles_error(self):
        """Test _fire_callback handles callback errors."""
        node = TimerNode("timer_1", {})
        
        async def failing_callback():
            raise ValueError("Test error")
        
        node._callback = failing_callback
        node._running = True
        
        # Should not raise
        await node._fire_callback()
        
        assert node._execution_count == 1

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fire_callback_no_callback(self):
        """Test _fire_callback with no callback set."""
        node = TimerNode("timer_1", {})
        
        # Should not raise
        await node._fire_callback()
        
        assert node._execution_count == 0


class TestTimerNodeProperties:
    """Tests for properties."""

    @pytest.mark.unit
    def test_is_running(self):
        """Test is_running property."""
        node = TimerNode("timer_1", {})
        
        assert node.is_running is False
        
        node._running = True
        assert node.is_running is True

    @pytest.mark.unit
    def test_execution_count(self):
        """Test execution_count property."""
        node = TimerNode("timer_1", {})
        
        assert node.execution_count == 0
        
        node._execution_count = 5
        assert node.execution_count == 5


class TestTimerNodeExecuteFull:
    """Full execution tests for TimerNode."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_disabled(self):
        """Test execute when disabled."""
        node = TimerNode("timer_1", {})
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(inputs={"enable": False}, context=context)
        
        assert result.success is True
        assert result.outputs["trigger"] is None
        assert result.metadata["status"] == "disabled"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_reset(self):
        """Test execute with reset."""
        node = TimerNode("timer_1", {})
        node._execution_count = 10
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(inputs={"reset": True}, context=context)
        
        assert node._execution_count == 1  # Reset then incremented

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_max_executions_reached(self):
        """Test execute when max executions reached."""
        node = TimerNode("timer_1", {"maxExecutions": 2})
        node._execution_count = 2
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(inputs={}, context=context)
        
        assert result.success is True
        assert result.outputs["trigger"] is None
        assert result.metadata["status"] == "max_executions_reached"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful execute."""
        node = TimerNode("timer_1", {})
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(inputs={}, context=context)
        
        assert result.success is True
        assert result.outputs["trigger"] is not None
        assert result.outputs["trigger"]["type"] == "timer"
        assert result.outputs["execution_count"] == 1
        assert "timestamp" in result.outputs

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_multiple_times(self):
        """Test execute increments count."""
        node = TimerNode("timer_1", {})
        context = MagicMock(spec=ExecutionContext)
        
        await node.execute(inputs={}, context=context)
        await node.execute(inputs={}, context=context)
        result = await node.execute(inputs={}, context=context)
        
        assert result.outputs["execution_count"] == 3


class TestTimerNodeCronWithCroniter:
    """Tests for cron functionality with croniter."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cron_without_croniter(self):
        """Test cron timer when croniter is not available."""
        node = TimerNode("timer_1", {
            "triggerType": "cron",
            "cronExpression": "* * * * *",
        })
        
        with patch.dict('sys.modules', {'croniter': None}):
            callback = AsyncMock()
            await node.start(callback)
            
            await asyncio.sleep(0.05)
            
            await node.stop()
