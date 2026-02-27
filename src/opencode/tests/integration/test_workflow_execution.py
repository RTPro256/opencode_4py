"""
Integration tests for workflow execution.

Tests the complete flow of workflow execution including task routing,
agent coordination, and result collection.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from opencode.core.orchestration.coordinator import (
    Coordinator,
    CoordinatorConfig,
    CoordinatedTask,
    TaskStatus,
)
from opencode.core.orchestration.agent import (
    Agent,
    AgentTask,
    AgentDescription,
    AgentCapability,
    AgentStatus,
)
from opencode.core.orchestration.registry import AgentRegistry


@pytest.mark.integration
class TestWorkflowExecution:
    """Integration tests for workflow execution."""
    
    @pytest.fixture
    def registry(self):
        """Create an agent registry with test agents."""
        registry = AgentRegistry()
        
        # Create a code agent
        code_agent = Agent(
            description=AgentDescription(
                agent_id="code_agent",
                name="Code Agent",
                description="Handles code generation and modification",
                capabilities=[AgentCapability.CODE_GENERATION, AgentCapability.DEBUGGING],
            )
        )
        registry.register(code_agent)
        
        # Create a review agent
        review_agent = Agent(
            description=AgentDescription(
                agent_id="review_agent",
                name="Review Agent",
                description="Handles code review tasks",
                capabilities=[AgentCapability.CODE_REVIEW],
            )
        )
        registry.register(review_agent)
        
        return registry
    
    @pytest.fixture
    def coordinator(self, registry):
        """Create a coordinator with test registry."""
        config = CoordinatorConfig(
            max_concurrent_tasks=5,
            task_timeout_seconds=60,
        )
        return Coordinator(registry, config)
    
    @pytest.mark.asyncio
    async def test_coordinator_initialization(self, coordinator):
        """Test coordinator initializes correctly."""
        assert coordinator.registry is not None
        assert coordinator.config.max_concurrent_tasks == 5
    
    @pytest.mark.asyncio
    async def test_submit_task(self, coordinator):
        """Test submitting a task to coordinator."""
        task_id = await coordinator.submit("Write a hello world function")
        
        assert task_id is not None
        assert task_id in coordinator._tasks
    
    @pytest.mark.asyncio
    async def test_task_status_tracking(self, coordinator):
        """Test task status is tracked."""
        task_id = await coordinator.submit("Test task")
        
        task = coordinator._tasks.get(task_id)
        assert task is not None
        assert task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]
    
    @pytest.mark.asyncio
    async def test_coordinator_start_stop(self, coordinator):
        """Test coordinator start and stop."""
        await coordinator.start()
        assert coordinator._started is True
        
        await coordinator.stop()
        assert coordinator._started is False


@pytest.mark.integration
class TestAgentCoordination:
    """Integration tests for agent coordination."""
    
    @pytest.fixture
    def code_agent(self):
        """Create a code agent for testing."""
        return Agent(
            description=AgentDescription(
                agent_id="test_code_agent",
                name="Test Code Agent",
                description="Test agent for code tasks",
                capabilities=[AgentCapability.CODE_GENERATION],
                max_concurrent_tasks=2,
            )
        )
    
    def test_agent_initialization(self, code_agent):
        """Test agent initializes correctly."""
        assert code_agent.agent_id == "test_code_agent"
        assert code_agent.status == AgentStatus.IDLE
        assert code_agent.is_available is True
    
    def test_agent_availability(self, code_agent):
        """Test agent availability changes."""
        assert code_agent.is_available is True
        
        # Simulate busy state
        code_agent._status = AgentStatus.BUSY
        assert code_agent.is_available is False
    
    @pytest.mark.asyncio
    async def test_agent_task_execution(self, code_agent):
        """Test agent executes tasks."""
        handler = AsyncMock(return_value="Task completed successfully")
        code_agent._handler = handler
        
        task = AgentTask(
            task_id="test-task-1",
            prompt="Write a test function",
        )
        
        result = await code_agent.execute(task)
        
        assert result == "Task completed successfully"


@pytest.mark.integration
class TestTaskRouting:
    """Integration tests for task routing."""
    
    @pytest.fixture
    def registry_with_agents(self):
        """Create registry with multiple specialized agents."""
        registry = AgentRegistry()
        
        agents = [
            Agent(AgentDescription(
                agent_id="python_agent",
                name="Python Agent",
                description="Python code specialist",
                capabilities=[AgentCapability.CODE_GENERATION],
            )),
            Agent(AgentDescription(
                agent_id="debug_agent",
                name="Debug Agent",
                description="Debugging specialist",
                capabilities=[AgentCapability.DEBUGGING],
            )),
            Agent(AgentDescription(
                agent_id="review_agent",
                name="Review Agent",
                description="Code review specialist",
                capabilities=[AgentCapability.CODE_REVIEW],
            )),
        ]
        
        for agent in agents:
            registry.register(agent)
        
        return registry
    
    def test_registry_has_agents(self, registry_with_agents):
        """Test registry contains expected agents."""
        agents = registry_with_agents._agents
        
        assert "python_agent" in agents
        assert "debug_agent" in agents
        assert "review_agent" in agents
    
    def test_find_by_capability(self, registry_with_agents):
        """Test finding agents by capability."""
        code_agents = registry_with_agents.find_by_capability(
            AgentCapability.CODE_GENERATION
        )
        
        assert len(code_agents) == 1
        assert code_agents[0].agent_id == "python_agent"
    
    def test_find_debug_agents(self, registry_with_agents):
        """Test finding debug agents."""
        debug_agents = registry_with_agents.find_by_capability(
            AgentCapability.DEBUGGING
        )
        
        assert len(debug_agents) == 1
        assert debug_agents[0].agent_id == "debug_agent"


@pytest.mark.integration
class TestCoordinatedTask:
    """Integration tests for CoordinatedTask."""
    
    def test_task_creation(self):
        """Test creating a coordinated task."""
        task = CoordinatedTask(
            task_id="task-123",
            prompt="Fix the bug in authentication",
        )
        
        assert task.task_id == "task-123"
        assert task.prompt == "Fix the bug in authentication"
        assert task.status == TaskStatus.PENDING
    
    def test_task_status_progression(self):
        """Test task status progression."""
        task = CoordinatedTask(
            task_id="task-1",
            prompt="Test",
        )
        
        # Initial state
        assert task.status == TaskStatus.PENDING
        
        # Start task
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        assert task.status == TaskStatus.RUNNING
        
        # Complete task
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        task.result = "Done"
        assert task.status == TaskStatus.COMPLETED
    
    def test_task_failure(self):
        """Test task failure handling."""
        task = CoordinatedTask(
            task_id="task-1",
            prompt="Test",
        )
        
        task.status = TaskStatus.FAILED
        task.error = "Something went wrong"
        
        assert task.status == TaskStatus.FAILED
        assert task.error == "Something went wrong"


@pytest.mark.integration
class TestWorkflowScenarios:
    """Integration tests for complete workflow scenarios."""
    
    @pytest.fixture
    def setup_workflow(self):
        """Set up a complete workflow environment."""
        registry = AgentRegistry()
        
        # Create handler that returns results
        async def mock_handler(task: AgentTask):
            return f"Processed: {task.prompt}"
        
        agent = Agent(
            description=AgentDescription(
                agent_id="worker_agent",
                name="Worker Agent",
                description="General purpose worker",
                capabilities=[AgentCapability.CODE_GENERATION],
            ),
            handler=mock_handler,
        )
        registry.register(agent)
        
        coordinator = Coordinator(registry)
        return coordinator, agent
    
    @pytest.mark.asyncio
    async def test_simple_workflow(self, setup_workflow):
        """Test a simple workflow execution."""
        coordinator, agent = setup_workflow
        
        task_id = await coordinator.submit("Simple task")
        
        assert task_id is not None
        assert task_id in coordinator._tasks
    
    @pytest.mark.asyncio
    async def test_multiple_tasks(self, setup_workflow):
        """Test submitting multiple tasks."""
        coordinator, agent = setup_workflow
        
        task_ids = []
        for i in range(3):
            task_id = await coordinator.submit(f"Task {i}")
            task_ids.append(task_id)
        
        assert len(task_ids) == 3
        assert len(coordinator._tasks) == 3
    
    @pytest.mark.asyncio
    async def test_task_metadata(self, setup_workflow):
        """Test task with metadata."""
        coordinator, agent = setup_workflow
        
        task_id = await coordinator.submit(
            "Task with metadata",
            metadata={"priority": "high", "source": "test"},
        )
        
        task = coordinator._tasks[task_id]
        assert task.metadata["priority"] == "high"
        assert task.metadata["source"] == "test"


@pytest.mark.integration
class TestWorkflowErrorHandling:
    """Integration tests for workflow error handling."""
    
    @pytest.fixture
    def failing_agent_registry(self):
        """Create registry with a failing agent."""
        registry = AgentRegistry()
        
        async def failing_handler(task: AgentTask):
            raise RuntimeError("Agent failed!")
        
        agent = Agent(
            description=AgentDescription(
                agent_id="failing_agent",
                name="Failing Agent",
                description="An agent that fails",
                capabilities=[AgentCapability.CODE_GENERATION],
            ),
            handler=failing_handler,
        )
        registry.register(agent)
        
        return registry
    
    @pytest.mark.asyncio
    async def test_task_failure_handling(self, failing_agent_registry):
        """Test handling of task failures."""
        coordinator = Coordinator(failing_agent_registry)
        
        task_id = await coordinator.submit("This will fail")
        
        # Task should be tracked
        assert task_id in coordinator._tasks
    
    @pytest.mark.asyncio
    async def test_coordinator_timeout_config(self):
        """Test coordinator timeout configuration."""
        registry = AgentRegistry()
        config = CoordinatorConfig(
            task_timeout_seconds=30,
            retry_failed_tasks=True,
            max_retries=2,
        )
        
        coordinator = Coordinator(registry, config)
        
        assert coordinator.config.task_timeout_seconds == 30
        assert coordinator.config.retry_failed_tasks is True
        assert coordinator.config.max_retries == 2
