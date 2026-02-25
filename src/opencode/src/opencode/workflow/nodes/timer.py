"""
Timer Node

Handles scheduled/cron triggers for workflows.
"""

import asyncio
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
import logging

from opencode.workflow.node import (
    BaseNode,
    NodePort,
    NodeSchema,
    ExecutionContext,
    ExecutionResult,
    PortDataType,
    PortDirection,
)
from opencode.workflow.registry import NodeRegistry

logger = logging.getLogger(__name__)


class TriggerType:
    """Supported trigger types for TimerNode."""
    INTERVAL = "interval"
    CRON = "cron"
    ONCE = "once"
    DELAY = "delay"


@NodeRegistry.register("timer")
class TimerNode(BaseNode):
    """
    Timer Node - Scheduled workflow triggers.
    
    This node triggers workflow execution based on time schedules.
    Supports interval-based, cron-based, one-time, and delayed triggers.
    
    Configuration:
        triggerType: Type of trigger (interval, cron, once, delay)
        interval: Interval in seconds (for interval type)
        cronExpression: Cron expression (for cron type)
        delaySeconds: Delay in seconds (for delay type)
        executeOnStart: Whether to execute immediately on workflow start
        maxExecutions: Maximum number of executions (0 = unlimited)
    """
    
    _schema = NodeSchema(
        node_type="timer",
        display_name="Timer",
        description="Trigger workflow execution on a schedule",
        category="trigger",
        icon="clock",
        inputs=[
            NodePort(
                name="enable",
                data_type=PortDataType.BOOLEAN,
                direction=PortDirection.INPUT,
                required=False,
                default_value=True,
                description="Enable/disable the timer",
            ),
            NodePort(
                name="reset",
                data_type=PortDataType.BOOLEAN,
                direction=PortDirection.INPUT,
                required=False,
                description="Reset the timer when true",
            ),
        ],
        outputs=[
            NodePort(
                name="trigger",
                data_type=PortDataType.ANY,
                direction=PortDirection.OUTPUT,
                required=True,
                description="Trigger signal for downstream nodes",
            ),
            NodePort(
                name="timestamp",
                data_type=PortDataType.STRING,
                direction=PortDirection.OUTPUT,
                required=True,
                description="ISO timestamp of trigger",
            ),
            NodePort(
                name="execution_count",
                data_type=PortDataType.INTEGER,
                direction=PortDirection.OUTPUT,
                required=False,
                description="Number of times triggered",
            ),
        ],
        config_schema={
            "type": "object",
            "properties": {
                "triggerType": {
                    "type": "string",
                    "enum": ["interval", "cron", "once", "delay"],
                    "default": "interval",
                    "description": "Type of trigger",
                },
                "interval": {
                    "type": "number",
                    "default": 60,
                    "description": "Interval in seconds (for interval type)",
                },
                "cronExpression": {
                    "type": "string",
                    "description": "Cron expression (for cron type)",
                },
                "delaySeconds": {
                    "type": "number",
                    "default": 0,
                    "description": "Delay in seconds (for delay type)",
                },
                "executeOnStart": {
                    "type": "boolean",
                    "default": False,
                    "description": "Execute immediately on workflow start",
                },
                "maxExecutions": {
                    "type": "integer",
                    "default": 0,
                    "description": "Maximum executions (0 = unlimited)",
                },
            },
            "required": ["triggerType"],
        },
        version="1.0.0",
    )
    
    @classmethod
    def get_schema(cls) -> NodeSchema:
        return cls._schema
    
    def __init__(self, node_id: str, config: Dict[str, Any]):
        super().__init__(node_id, config)
        self._execution_count = 0
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._callback: Optional[Callable] = None
    
    async def execute(
        self,
        inputs: Dict[str, Any],
        context: ExecutionContext,
    ) -> ExecutionResult:
        """Execute the timer node."""
        import time
        start_time = time.time()
        
        try:
            # Check if timer is enabled
            enabled = inputs.get("enable", True)
            if not enabled:
                return ExecutionResult(
                    success=True,
                    outputs={
                        "trigger": None,
                        "timestamp": datetime.utcnow().isoformat(),
                        "execution_count": self._execution_count,
                    },
                    metadata={"status": "disabled"},
                )
            
            # Check for reset
            if inputs.get("reset"):
                self._execution_count = 0
            
            # Check max executions
            max_executions = self.config.get("maxExecutions", 0)
            if max_executions > 0 and self._execution_count >= max_executions:
                return ExecutionResult(
                    success=True,
                    outputs={
                        "trigger": None,
                        "timestamp": datetime.utcnow().isoformat(),
                        "execution_count": self._execution_count,
                    },
                    metadata={"status": "max_executions_reached"},
                )
            
            # Increment execution count
            self._execution_count += 1
            
            # Generate trigger output
            outputs = {
                "trigger": {"type": "timer", "count": self._execution_count},
                "timestamp": datetime.utcnow().isoformat(),
                "execution_count": self._execution_count,
            }
            
            duration_ms = (time.time() - start_time) * 1000
            return ExecutionResult(
                success=True,
                outputs=outputs,
                duration_ms=duration_ms,
            )
            
        except Exception as e:
            logger.exception(f"Timer execution failed: {e}")
            return ExecutionResult(
                success=False,
                error=str(e),
            )
    
    async def start(self, callback: Callable[[], None]) -> None:
        """
        Start the timer for continuous scheduling.
        
        This is used when the timer is a trigger node that runs
        continuously and fires callbacks.
        
        Args:
            callback: Function to call when timer triggers
        """
        if self._running:
            logger.warning(f"Timer {self.node_id} is already running")
            return
        
        self._callback = callback
        self._running = True
        
        trigger_type = self.config.get("triggerType", "interval")
        
        # Execute immediately if configured
        if self.config.get("executeOnStart", False):
            await self._fire_callback()
        
        # Start the appropriate timer task
        if trigger_type == TriggerType.INTERVAL:
            self._task = asyncio.create_task(self._run_interval())
        elif trigger_type == TriggerType.CRON:
            self._task = asyncio.create_task(self._run_cron())
        elif trigger_type == TriggerType.DELAY:
            self._task = asyncio.create_task(self._run_delay())
        elif trigger_type == TriggerType.ONCE:
            self._task = asyncio.create_task(self._run_once())
    
    async def stop(self) -> None:
        """Stop the timer."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
    
    async def _run_interval(self) -> None:
        """Run interval-based timer."""
        interval = self.config.get("interval", 60)
        max_executions = self.config.get("maxExecutions", 0)
        
        while self._running:
            await asyncio.sleep(interval)
            
            if not self._running:
                break
            
            # Check max executions
            if max_executions > 0 and self._execution_count >= max_executions:
                break
            
            await self._fire_callback()
    
    async def _run_cron(self) -> None:
        """Run cron-based timer."""
        try:
            from croniter import croniter
        except ImportError:
            logger.error("croniter is required for cron triggers. Install with: pip install croniter")
            return
        
        cron_expression = self.config.get("cronExpression")
        if not cron_expression:
            logger.error("cronExpression is required for cron trigger type")
            return
        
        max_executions = self.config.get("maxExecutions", 0)
        
        try:
            cron = croniter(cron_expression, datetime.utcnow())
            
            while self._running:
                # Get next execution time
                next_time = cron.get_next(datetime)
                now = datetime.utcnow()
                
                # Calculate wait time
                wait_seconds = (next_time - now).total_seconds()
                if wait_seconds > 0:
                    await asyncio.sleep(wait_seconds)
                
                if not self._running:
                    break
                
                # Check max executions
                if max_executions > 0 and self._execution_count >= max_executions:
                    break
                
                await self._fire_callback()
                
        except Exception as e:
            logger.error(f"Cron timer error: {e}")
    
    async def _run_delay(self) -> None:
        """Run delay-based timer (one-time after delay)."""
        delay = self.config.get("delaySeconds", 0)
        
        if delay > 0:
            await asyncio.sleep(delay)
        
        if self._running:
            await self._fire_callback()
        
        self._running = False
    
    async def _run_once(self) -> None:
        """Run once immediately."""
        if self._running:
            await self._fire_callback()
        self._running = False
    
    async def _fire_callback(self) -> None:
        """Fire the callback if set."""
        if self._callback:
            try:
                self._execution_count += 1
                await self._callback()
            except Exception as e:
                logger.error(f"Timer callback error: {e}")
    
    @property
    def is_running(self) -> bool:
        """Check if the timer is running."""
        return self._running
    
    @property
    def execution_count(self) -> int:
        """Get the number of times the timer has triggered."""
        return self._execution_count
