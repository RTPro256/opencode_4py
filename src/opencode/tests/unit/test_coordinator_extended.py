"""
Extended tests for Coordinator class to improve coverage.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime
import asyncio

from opencode.core.orchestration.coordinator import (
    Coordinator,
    CoordinatorConfig,
    CoordinatedTask,
    TaskStatus,
)
from opencode.core.orchestration.registry import AgentRegistry
from opencode.core.orchestration.agent import Agent, AgentDescription, AgentTask
from opencode.core.orchestration.router import RoutingResult, Intent, IntentCategory


class TestCoordinatedTask:
    """Tests for CoordinatedTask dataclass."""

    @pytest.mark.unit
    def test_coordinated_task_creation(self):
        """Test creating a coordinated task."""
        task = CoordinatedTask(
            task_id="test-123",
            prompt="Test prompt",
        )
        assert task.task_id == "test-123"
        assert task.prompt == "Test prompt"
        assert task.status == TaskStatus.PENDING
        assert task.routing_result is None
        assert task.agent_task is None
        assert task.result is None
        assert task.error is None
        assert task.metadata == {}

    @pytest.mark.unit
    def test_coordinated_task_to_dict(self):
        """Test converting task to dictionary."""
        task = CoordinatedTask(
            task_id="test-123",
            prompt="Test prompt",
            status=TaskStatus.COMPLETED,
            result="Done",
            metadata={"key": "value"},
        )
        d = task.to_dict()
        assert d["task_id"] == "test-123"
        assert d["prompt"] == "Test prompt"
        assert d["status"] == "completed"
        assert d["result"] == "Done"
        assert d["metadata"] == {"key": "value"}
        assert "created_at" in d

    @pytest.mark.unit
    def test_coordinated_task_to_dict_with_routing_result(self):
        """Test converting task with routing result to dict."""
        intent = Intent(
            category=IntentCategory.CODE_GENERATION,
            confidence=0.9,
        )
        routing = RoutingResult(
            agent_id="test_agent",
            intent=intent,
            confidence=0.9,
            routing_reason="Test reason",
        )
        task = CoordinatedTask(
            task_id="test-123",
            prompt="Test",
            routing_result=routing,
        )
        d = task.to_dict()
        assert d["routing_result"] is not None
        assert d["routing_result"]["agent_id"] == "test_agent"

    @pytest.mark.unit
    def test_coordinated_task_to_dict_with_dates(self):
        """Test converting task with dates to dict."""
        now = datetime.utcnow()
        task = CoordinatedTask(
            task_id="test-123",
            prompt="Test",
            started_at=now,
            completed_at=now,
        )
        d = task.to_dict()
        assert d["started_at"] is not None
        assert d["completed_at"] is not None


class TestTaskStatus:
    """Tests for TaskStatus enum."""

    @pytest.mark.unit
    def test_task_status_values(self):
        """Test TaskStatus enum values."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"


class TestCoordinatorConfig:
    """Tests for CoordinatorConfig dataclass."""

    @pytest.mark.unit
    def test_default_config(self):
        """Test default configuration values."""
        config = CoordinatorConfig()
        assert config.max_concurrent_tasks == 10
        assert config.task_timeout_seconds == 300
        assert config.retry_failed_tasks is True
        assert config.max_retries == 2
        assert config.enable_logging is True

    @pytest.mark.unit
    def test_custom_config(self):
        """Test custom configuration values."""
        config = CoordinatorConfig(
            max_concurrent_tasks=5,
            task_timeout_seconds=60,
            retry_failed_tasks=False,
            max_retries=5,
            enable_logging=False,
        )
        assert config.max_concurrent_tasks == 5
        assert config.task_timeout_seconds == 60
        assert config.retry_failed_tasks is False
        assert config.max_retries == 5
        assert config.enable_logging is False


class TestCoordinatorGetTaskMethods:
    """Tests for Coordinator task retrieval methods."""

    @pytest.fixture
    def mock_registry(self):
        """Create a mock agent registry."""
        registry = AgentRegistry()
        agent = MagicMock(spec=Agent)
        agent.agent_id = "test_agent"
        agent.description = AgentDescription(
            agent_id="test_agent",
            name="Test Agent",
            description="A test agent",
            capabilities=[],
        )
        registry.register(agent)
        return registry

    @pytest.mark.unit
    def test_get_task(self, mock_registry):
        """Test getting a task by ID."""
        coordinator = Coordinator(mock_registry)
        coordinator._tasks["test-id"] = CoordinatedTask(
            task_id="test-id",
            prompt="Test",
        )
        
        task = coordinator.get_task("test-id")
        assert task is not None
        assert task.task_id == "test-id"
        
        # Non-existent task
        assert coordinator.get_task("non-existent") is None

    @pytest.mark.unit
    def test_get_all_tasks(self, mock_registry):
        """Test getting all tasks."""
        coordinator = Coordinator(mock_registry)
        coordinator._tasks["task-1"] = CoordinatedTask(task_id="task-1", prompt="Test 1")
        coordinator._tasks["task-2"] = CoordinatedTask(task_id="task-2", prompt="Test 2")
        
        all_tasks = coordinator.get_all_tasks()
        assert len(all_tasks) == 2

    @pytest.mark.unit
    def test_get_pending_tasks(self, mock_registry):
        """Test getting pending tasks."""
        coordinator = Coordinator(mock_registry)
        coordinator._tasks["task-1"] = CoordinatedTask(
            task_id="task-1", prompt="Test 1", status=TaskStatus.PENDING
        )
        coordinator._tasks["task-2"] = CoordinatedTask(
            task_id="task-2", prompt="Test 2", status=TaskStatus.RUNNING
        )
        coordinator._tasks["task-3"] = CoordinatedTask(
            task_id="task-3", prompt="Test 3", status=TaskStatus.PENDING
        )
        
        pending = coordinator.get_pending_tasks()
        assert len(pending) == 2
        assert all(t.status == TaskStatus.PENDING for t in pending)

    @pytest.mark.unit
    def test_get_running_tasks(self, mock_registry):
        """Test getting running tasks."""
        coordinator = Coordinator(mock_registry)
        coordinator._tasks["task-1"] = CoordinatedTask(
            task_id="task-1", prompt="Test 1", status=TaskStatus.RUNNING
        )
        coordinator._tasks["task-2"] = CoordinatedTask(
            task_id="task-2", prompt="Test 2", status=TaskStatus.COMPLETED
        )
        
        running = coordinator.get_running_tasks()
        assert len(running) == 1
        assert running[0].status == TaskStatus.RUNNING


class TestCoordinatorCallbacks:
    """Tests for Coordinator callback functionality."""

    @pytest.fixture
    def mock_registry(self):
        """Create a mock agent registry."""
        registry = AgentRegistry()
        agent = MagicMock(spec=Agent)
        agent.agent_id = "test_agent"
        agent.description = AgentDescription(
            agent_id="test_agent",
            name="Test Agent",
            description="A test agent",
            capabilities=[],
        )
        agent.start_task = AsyncMock()
        registry.register(agent)
        return registry

    @pytest.mark.unit
    def test_add_result_callback(self, mock_registry):
        """Test adding a result callback."""
        coordinator = Coordinator(mock_registry)
        
        def callback(task):
            pass
        
        coordinator.add_result_callback(callback)
        assert callback in coordinator._result_callbacks


class TestCoordinatorCancel:
    """Tests for Coordinator cancel functionality."""

    @pytest.fixture
    def mock_registry(self):
        """Create a mock agent registry."""
        registry = AgentRegistry()
        agent = MagicMock(spec=Agent)
        agent.agent_id = "test_agent"
        agent.description = AgentDescription(
            agent_id="test_agent",
            name="Test Agent",
            description="A test agent",
            capabilities=[],
        )
        registry.register(agent)
        return registry

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cancel_pending_task(self, mock_registry):
        """Test cancelling a pending task."""
        coordinator = Coordinator(mock_registry)
        coordinator._tasks["task-1"] = CoordinatedTask(
            task_id="task-1", prompt="Test", status=TaskStatus.PENDING
        )
        
        result = await coordinator.cancel_task("task-1")
        assert result is True
        assert coordinator._tasks["task-1"].status == TaskStatus.CANCELLED

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cancel_running_task(self, mock_registry):
        """Test cancelling a running task."""
        coordinator = Coordinator(mock_registry)
        coordinator._tasks["task-1"] = CoordinatedTask(
            task_id="task-1", prompt="Test", status=TaskStatus.RUNNING
        )
        # Add a mock running task
        mock_async_task = MagicMock()
        mock_async_task.cancel = MagicMock()
        coordinator._running_tasks["task-1"] = mock_async_task
        
        result = await coordinator.cancel_task("task-1")
        assert result is True
        assert coordinator._tasks["task-1"].status == TaskStatus.CANCELLED
        mock_async_task.cancel.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cancel_non_existent_task(self, mock_registry):
        """Test cancelling a non-existent task."""
        coordinator = Coordinator(mock_registry)
        
        result = await coordinator.cancel_task("non-existent")
        assert result is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cancel_completed_task(self, mock_registry):
        """Test cancelling a completed task fails."""
        coordinator = Coordinator(mock_registry)
        coordinator._tasks["task-1"] = CoordinatedTask(
            task_id="task-1", prompt="Test", status=TaskStatus.COMPLETED
        )
        
        result = await coordinator.cancel_task("task-1")
        assert result is False


class TestCoordinatorStats:
    """Tests for Coordinator statistics."""

    @pytest.fixture
    def mock_registry(self):
        """Create a mock agent registry."""
        registry = AgentRegistry()
        return registry

    @pytest.mark.unit
    def test_get_stats_empty(self, mock_registry):
        """Test getting stats with no tasks."""
        coordinator = Coordinator(mock_registry)
        
        stats = coordinator.get_stats()
        assert stats["total_tasks"] == 0
        assert stats["pending"] == 0
        assert stats["running"] == 0
        assert stats["completed"] == 0
        assert stats["failed"] == 0
        assert stats["cancelled"] == 0

    @pytest.mark.unit
    def test_get_stats_with_tasks(self, mock_registry):
        """Test getting stats with various tasks."""
        coordinator = Coordinator(mock_registry)
        coordinator._tasks["task-1"] = CoordinatedTask(
            task_id="task-1", prompt="Test", status=TaskStatus.PENDING
        )
        coordinator._tasks["task-2"] = CoordinatedTask(
            task_id="task-2", prompt="Test", status=TaskStatus.RUNNING
        )
        coordinator._tasks["task-3"] = CoordinatedTask(
            task_id="task-3", prompt="Test", status=TaskStatus.COMPLETED
        )
        coordinator._tasks["task-4"] = CoordinatedTask(
            task_id="task-4", prompt="Test", status=TaskStatus.FAILED
        )
        coordinator._tasks["task-5"] = CoordinatedTask(
            task_id="task-5", prompt="Test", status=TaskStatus.CANCELLED
        )
        
        stats = coordinator.get_stats()
        assert stats["total_tasks"] == 5
        assert stats["pending"] == 1
        assert stats["running"] == 1
        assert stats["completed"] == 1
        assert stats["failed"] == 1
        assert stats["cancelled"] == 1


class TestCoordinatorClearCompleted:
    """Tests for Coordinator clear_completed_tasks method."""

    @pytest.fixture
    def mock_registry(self):
        """Create a mock agent registry."""
        registry = AgentRegistry()
        return registry

    @pytest.mark.unit
    def test_clear_completed_tasks(self, mock_registry):
        """Test clearing completed tasks."""
        coordinator = Coordinator(mock_registry)
        coordinator._tasks["task-1"] = CoordinatedTask(
            task_id="task-1", prompt="Test", status=TaskStatus.COMPLETED
        )
        coordinator._tasks["task-2"] = CoordinatedTask(
            task_id="task-2", prompt="Test", status=TaskStatus.FAILED
        )
        coordinator._tasks["task-3"] = CoordinatedTask(
            task_id="task-3", prompt="Test", status=TaskStatus.CANCELLED
        )
        coordinator._tasks["task-4"] = CoordinatedTask(
            task_id="task-4", prompt="Test", status=TaskStatus.PENDING
        )
        
        removed = coordinator.clear_completed_tasks()
        assert removed == 3
        assert len(coordinator._tasks) == 1
        assert "task-4" in coordinator._tasks

    @pytest.mark.unit
    def test_clear_completed_tasks_none(self, mock_registry):
        """Test clearing when no completed tasks."""
        coordinator = Coordinator(mock_registry)
        coordinator._tasks["task-1"] = CoordinatedTask(
            task_id="task-1", prompt="Test", status=TaskStatus.PENDING
        )
        coordinator._tasks["task-2"] = CoordinatedTask(
            task_id="task-2", prompt="Test", status=TaskStatus.RUNNING
        )
        
        removed = coordinator.clear_completed_tasks()
        assert removed == 0
        assert len(coordinator._tasks) == 2


class TestCoordinatorStartStop:
    """Tests for Coordinator start/stop functionality."""

    @pytest.fixture
    def mock_registry(self):
        """Create a mock agent registry."""
        registry = AgentRegistry()
        return registry

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_start_already_started(self, mock_registry):
        """Test starting when already started."""
        coordinator = Coordinator(mock_registry)
        coordinator._started = True
        
        # Should return without doing anything
        await coordinator.start()
        # No additional task processors should be created
        assert coordinator._started is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_stop_cancels_running_tasks(self, mock_registry):
        """Test stop cancels running tasks."""
        coordinator = Coordinator(mock_registry)
        
        # Create mock running tasks
        mock_task1 = MagicMock()
        mock_task1.cancel = MagicMock()
        mock_task2 = MagicMock()
        mock_task2.cancel = MagicMock()
        
        coordinator._running_tasks["task-1"] = mock_task1
        coordinator._running_tasks["task-2"] = mock_task2
        coordinator._started = True
        
        await coordinator.stop()
        
        assert coordinator._started is False
        mock_task1.cancel.assert_called_once()
        mock_task2.cancel.assert_called_once()
        assert len(coordinator._running_tasks) == 0


class TestCoordinatorWaitForResult:
    """Tests for Coordinator wait_for_result method."""

    @pytest.fixture
    def mock_registry(self):
        """Create a mock agent registry."""
        registry = AgentRegistry()
        return registry

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_wait_for_result_task_not_found(self, mock_registry):
        """Test wait_for_result with non-existent task."""
        coordinator = Coordinator(mock_registry)
        
        with pytest.raises(ValueError, match="Task not found"):
            await coordinator.wait_for_result("non-existent", timeout=0.1)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_wait_for_result_timeout(self, mock_registry):
        """Test wait_for_result timeout."""
        coordinator = Coordinator(mock_registry)
        coordinator._tasks["task-1"] = CoordinatedTask(
            task_id="task-1", prompt="Test", status=TaskStatus.PENDING
        )
        
        with pytest.raises(asyncio.TimeoutError):
            await coordinator.wait_for_result("task-1", timeout=0.1)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_wait_for_result_completed(self, mock_registry):
        """Test wait_for_result with completed task."""
        coordinator = Coordinator(mock_registry)
        coordinator._tasks["task-1"] = CoordinatedTask(
            task_id="task-1", prompt="Test", status=TaskStatus.COMPLETED, result="Done"
        )
        
        task = await coordinator.wait_for_result("task-1", timeout=1.0)
        assert task.status == TaskStatus.COMPLETED
        assert task.result == "Done"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_wait_for_result_failed(self, mock_registry):
        """Test wait_for_result with failed task."""
        coordinator = Coordinator(mock_registry)
        coordinator._tasks["task-1"] = CoordinatedTask(
            task_id="task-1", prompt="Test", status=TaskStatus.FAILED, error="Error"
        )
        
        task = await coordinator.wait_for_result("task-1", timeout=1.0)
        assert task.status == TaskStatus.FAILED
        assert task.error == "Error"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_wait_for_result_cancelled(self, mock_registry):
        """Test wait_for_result with cancelled task."""
        coordinator = Coordinator(mock_registry)
        coordinator._tasks["task-1"] = CoordinatedTask(
            task_id="task-1", prompt="Test", status=TaskStatus.CANCELLED
        )
        
        task = await coordinator.wait_for_result("task-1", timeout=1.0)
        assert task.status == TaskStatus.CANCELLED
