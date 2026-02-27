"""
Coordinator

Coordinates multi-agent task execution and manages the orchestration flow.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable

from opencode.core.orchestration.agent import Agent, AgentTask, AgentDescription
from opencode.core.orchestration.registry import AgentRegistry
from opencode.core.orchestration.router import OrchestrationRouter, RoutingResult

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Status of a coordinated task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class CoordinatedTask:
    """A task being coordinated by the coordinator."""
    task_id: str
    prompt: str
    status: TaskStatus = TaskStatus.PENDING
    routing_result: Optional[RoutingResult] = None
    agent_task: Optional[AgentTask] = None
    result: Any = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "prompt": self.prompt,
            "status": self.status.value,
            "routing_result": self.routing_result.to_dict() if self.routing_result else None,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata,
        }


@dataclass
class CoordinatorConfig:
    """Configuration for the coordinator."""
    max_concurrent_tasks: int = 10
    task_timeout_seconds: int = 300
    retry_failed_tasks: bool = True
    max_retries: int = 2
    enable_logging: bool = True


class Coordinator:
    """
    Coordinates multi-agent task execution.
    
    The coordinator manages the flow of tasks through the orchestration
    system, handling routing, execution, and result collection.
    
    Example:
        registry = AgentRegistry()
        registry.register(code_agent)
        
        coordinator = Coordinator(registry)
        
        # Submit a task
        task_id = await coordinator.submit("Fix the bug in main.py")
        
        # Wait for result
        result = await coordinator.wait_for_result(task_id)
    """
    
    def __init__(
        self,
        registry: AgentRegistry,
        config: Optional[CoordinatorConfig] = None,
    ):
        """
        Initialize the coordinator.
        
        Args:
            registry: Agent registry
            config: Optional configuration
        """
        self.registry = registry
        self.config = config or CoordinatorConfig()
        self.router = OrchestrationRouter(registry)
        
        self._tasks: Dict[str, CoordinatedTask] = {}
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._task_queue: asyncio.Queue = asyncio.Queue()
        self._result_callbacks: List[Callable] = []
        self._started = False
    
    async def start(self) -> None:
        """Start the coordinator."""
        if self._started:
            return
        
        self._started = True
        
        # Start task processor
        for _ in range(self.config.max_concurrent_tasks):
            asyncio.create_task(self._process_tasks())
        
        logger.info("Coordinator started")
    
    async def stop(self) -> None:
        """Stop the coordinator."""
        self._started = False
        
        # Cancel running tasks
        for task in self._running_tasks.values():
            task.cancel()
        
        self._running_tasks.clear()
        logger.info("Coordinator stopped")
    
    async def submit(
        self,
        prompt: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Submit a new task.
        
        Args:
            prompt: Task prompt
            metadata: Optional metadata
            
        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())[:8]
        
        task = CoordinatedTask(
            task_id=task_id,
            prompt=prompt,
            metadata=metadata or {},
        )
        
        self._tasks[task_id] = task
        
        await self._task_queue.put(task_id)
        
        logger.info(f"Submitted task {task_id}: {prompt[:50]}...")
        
        return task_id
    
    async def submit_and_wait(
        self,
        prompt: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CoordinatedTask:
        """
        Submit a task and wait for completion.
        
        Args:
            prompt: Task prompt
            metadata: Optional metadata
            
        Returns:
            Completed task
        """
        task_id = await self.submit(prompt, metadata)
        return await self.wait_for_result(task_id)
    
    async def wait_for_result(
        self,
        task_id: str,
        timeout: Optional[float] = None,
    ) -> CoordinatedTask:
        """
        Wait for a task to complete.
        
        Args:
            task_id: Task ID
            timeout: Optional timeout in seconds
            
        Returns:
            Completed task
            
        Raises:
            asyncio.TimeoutError: If timeout exceeded
        """
        timeout = timeout or self.config.task_timeout_seconds
        
        async def wait_for_completion():
            while True:
                task = self._tasks.get(task_id)
                if not task:
                    raise ValueError(f"Task not found: {task_id}")
                
                if task.status in (
                    TaskStatus.COMPLETED,
                    TaskStatus.FAILED,
                    TaskStatus.CANCELLED,
                ):
                    return task
                
                await asyncio.sleep(0.1)
        
        return await asyncio.wait_for(wait_for_completion(), timeout)
    
    def get_task(self, task_id: str) -> Optional[CoordinatedTask]:
        """Get a task by ID."""
        return self._tasks.get(task_id)
    
    def get_all_tasks(self) -> List[CoordinatedTask]:
        """Get all tasks."""
        return list(self._tasks.values())
    
    def get_pending_tasks(self) -> List[CoordinatedTask]:
        """Get pending tasks."""
        return [t for t in self._tasks.values() if t.status == TaskStatus.PENDING]
    
    def get_running_tasks(self) -> List[CoordinatedTask]:
        """Get running tasks."""
        return [t for t in self._tasks.values() if t.status == TaskStatus.RUNNING]
    
    def add_result_callback(self, callback: Callable) -> None:
        """Add a callback for task results."""
        self._result_callbacks.append(callback)
    
    async def _process_tasks(self) -> None:
        """Process tasks from the queue."""
        while self._started:
            try:
                task_id = await asyncio.wait_for(
                    self._task_queue.get(),
                    timeout=1.0,
                )
                
                await self._execute_task(task_id)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing task: {e}")
    
    async def _execute_task(self, task_id: str) -> None:
        """Execute a task."""
        task = self._tasks.get(task_id)
        if not task:
            return
        
        try:
            # Update status
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.utcnow()
            
            # Route to agent
            routing_result = self.router.route(task.prompt)
            task.routing_result = routing_result
            
            # Get agent
            agent = self.registry.get(routing_result.agent_id)
            if not agent:
                raise RuntimeError(f"Agent not found: {routing_result.agent_id}")
            
            # Create agent task
            agent_task = AgentTask(
                task_id=task_id,
                prompt=task.prompt,
                context=task.metadata,
            )
            task.agent_task = agent_task
            
            # Execute
            await agent.start_task(agent_task)
            
            # Update result
            task.result = agent_task.result
            task.error = agent_task.error
            task.status = TaskStatus.COMPLETED if not agent_task.error else TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            
            # Notify callbacks
            for callback in self._result_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(task)
                    else:
                        callback(task)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
            
            logger.info(f"Task {task_id} completed with status: {task.status.value}")
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.utcnow()
            logger.error(f"Task {task_id} failed: {e}")
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task.
        
        Args:
            task_id: Task ID
            
        Returns:
            True if cancelled
        """
        task = self._tasks.get(task_id)
        if not task:
            return False
        
        if task.status not in (TaskStatus.PENDING, TaskStatus.RUNNING):
            return False
        
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.utcnow()
        
        # Cancel asyncio task if running
        if task_id in self._running_tasks:
            self._running_tasks[task_id].cancel()
            del self._running_tasks[task_id]
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get coordinator statistics."""
        tasks = list(self._tasks.values())
        
        return {
            "total_tasks": len(tasks),
            "pending": len([t for t in tasks if t.status == TaskStatus.PENDING]),
            "running": len([t for t in tasks if t.status == TaskStatus.RUNNING]),
            "completed": len([t for t in tasks if t.status == TaskStatus.COMPLETED]),
            "failed": len([t for t in tasks if t.status == TaskStatus.FAILED]),
            "cancelled": len([t for t in tasks if t.status == TaskStatus.CANCELLED]),
            "queue_size": self._task_queue.qsize(),
        }
    
    def clear_completed_tasks(self) -> int:
        """
        Remove completed tasks.
        
        Returns:
            Number of tasks removed
        """
        to_remove = [
            tid for tid, task in self._tasks.items()
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)
        ]
        
        for tid in to_remove:
            del self._tasks[tid]
        
        return len(to_remove)
