"""
Unit tests for orchestration functionality.

Tests for Coordinator, Agent, Router, and related orchestration components.
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


class TestCoordinatedTask:
    """Tests for CoordinatedTask dataclass."""
    
    def test_task_creation(self):
        """Test creating a CoordinatedTask."""
        task = CoordinatedTask(
            task_id="task-123",
            prompt="Fix the bug in main.py",
        )
        
        assert task.task_id == "task-123"
        assert task.prompt == "Fix the bug in main.py"
        assert task.status == TaskStatus.PENDING
        assert task.result is None
        assert task.error is None
    
    def test_task_to_dict(self):
        """Test serializing CoordinatedTask to dictionary."""
        task = CoordinatedTask(
            task_id="task-456",
            prompt="Write a test",
            status=TaskStatus.RUNNING,
            metadata={"priority": "high"},
        )
        
        data = task.to_dict()
        
        assert data["task_id"] == "task-456"
        assert data["prompt"] == "Write a test"
        assert data["status"] == "running"
        assert data["metadata"]["priority"] == "high"
    
    def test_task_status_transitions(self):
        """Test task status transitions."""
        task = CoordinatedTask(task_id="task-1", prompt="Test")
        
        # Initial status
        assert task.status == TaskStatus.PENDING
        
        # Transition to running
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        assert task.status == TaskStatus.RUNNING
        
        # Transition to completed
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        assert task.status == TaskStatus.COMPLETED


class TestCoordinatorConfig:
    """Tests for CoordinatorConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = CoordinatorConfig()
        
        assert config.max_concurrent_tasks == 10
        assert config.task_timeout_seconds == 300
        assert config.retry_failed_tasks is True
        assert config.max_retries == 2
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = CoordinatorConfig(
            max_concurrent_tasks=5,
            task_timeout_seconds=600,
            retry_failed_tasks=False,
            max_retries=0,
        )
        
        assert config.max_concurrent_tasks == 5
        assert config.task_timeout_seconds == 600
        assert config.retry_failed_tasks is False
        assert config.max_retries == 0


class TestAgentDescription:
    """Tests for AgentDescription."""
    
    def test_description_creation(self):
        """Test creating an AgentDescription."""
        desc = AgentDescription(
            agent_id="code_agent",
            name="Code Agent",
            description="An agent for writing code",
            capabilities=[AgentCapability.CODE_GENERATION, AgentCapability.CODE_REVIEW],
            tools=["file_read", "file_write", "bash"],
        )
        
        assert desc.agent_id == "code_agent"
        assert desc.name == "Code Agent"
        assert desc.description == "An agent for writing code"
        assert AgentCapability.CODE_GENERATION in desc.capabilities
        assert "file_read" in desc.tools
    
    def test_description_to_dict(self):
        """Test serializing AgentDescription to dictionary."""
        desc = AgentDescription(
            agent_id="debug_agent",
            name="Debug Agent",
            description="An agent for debugging",
            capabilities=[AgentCapability.DEBUGGING],
            tools=["file_read", "bash"],
        )
        
        data = desc.to_dict()
        
        assert data["agent_id"] == "debug_agent"
        assert data["name"] == "Debug Agent"
        assert data["description"] == "An agent for debugging"
        assert len(data["capabilities"]) == 1
    
    def test_description_from_dict(self):
        """Test deserializing AgentDescription from dictionary."""
        data = {
            "agent_id": "test_agent",
            "name": "Test Agent",
            "description": "A test agent",
            "capabilities": ["code_generation"],
            "tools": ["file_read"],
            "priority": 5,
        }
        
        desc = AgentDescription.from_dict(data)
        
        assert desc.agent_id == "test_agent"
        assert desc.name == "Test Agent"
        assert AgentCapability.CODE_GENERATION in desc.capabilities


class TestAgentTask:
    """Tests for AgentTask."""
    
    def test_task_creation(self):
        """Test creating an AgentTask."""
        task = AgentTask(
            task_id="task-123",
            prompt="Fix the bug",
        )
        
        assert task.task_id == "task-123"
        assert task.prompt == "Fix the bug"
        assert task.status == "pending"
    
    def test_task_with_context(self):
        """Test creating an AgentTask with context."""
        task = AgentTask(
            task_id="task-456",
            prompt="Review the code",
            context={"files": ["main.py", "utils.py"]},
        )
        
        assert task.context["files"] == ["main.py", "utils.py"]
    
    def test_task_to_dict(self):
        """Test serializing AgentTask to dictionary."""
        task = AgentTask(
            task_id="task-789",
            prompt="Test task",
            context={"key": "value"},
        )
        
        data = task.to_dict()
        
        assert data["task_id"] == "task-789"
        assert data["prompt"] == "Test task"
        assert data["context"]["key"] == "value"


class TestAgent:
    """Tests for Agent class."""
    
    @pytest.fixture
    def agent_description(self):
        """Create an agent description."""
        return AgentDescription(
            agent_id="test_agent",
            name="Test Agent",
            description="A test agent",
            capabilities=[AgentCapability.CODE_GENERATION],
        )
    
    def test_agent_initialization(self, agent_description):
        """Test Agent initialization."""
        agent = Agent(agent_description)
        
        assert agent.agent_id == "test_agent"
        assert agent.status == AgentStatus.IDLE
        assert agent.is_available is True
    
    def test_agent_availability(self, agent_description):
        """Test agent availability check."""
        agent = Agent(agent_description)
        
        assert agent.is_available is True
        
        # Simulate busy state
        agent._status = AgentStatus.BUSY
        assert agent.is_available is False
    
    @pytest.mark.asyncio
    async def test_agent_execute(self, agent_description):
        """Test agent task execution."""
        handler = AsyncMock(return_value="Task result")
        agent = Agent(agent_description, handler=handler)
        
        task = AgentTask(task_id="test-1", prompt="Test prompt")
        result = await agent.execute(task)
        
        assert result == "Task result"


class TestAgentRegistry:
    """Tests for AgentRegistry."""
    
    def test_registry_initialization(self):
        """Test AgentRegistry initialization."""
        registry = AgentRegistry()
        
        assert len(registry._agents) == 0
    
    def test_register_agent(self):
        """Test registering an agent."""
        registry = AgentRegistry()
        agent = MagicMock(spec=Agent)
        agent.agent_id = "test_agent"
        agent.description = AgentDescription(
            agent_id="test_agent",
            name="Test Agent",
            description="A test agent",
            capabilities=[AgentCapability.CODE_GENERATION],
        )
        
        registry.register(agent)
        
        assert "test_agent" in registry._agents
    
    def test_register_duplicate_agent(self):
        """Test registering duplicate agent raises error."""
        registry = AgentRegistry()
        agent = MagicMock(spec=Agent)
        agent.agent_id = "test_agent"
        agent.description = AgentDescription(
            agent_id="test_agent",
            name="Test Agent",
            description="A test agent",
            capabilities=[AgentCapability.CODE_GENERATION],
        )
        
        registry.register(agent)
        
        with pytest.raises(ValueError, match="already registered"):
            registry.register(agent)
    
    def test_unregister_agent(self):
        """Test unregistering an agent."""
        registry = AgentRegistry()
        agent = MagicMock(spec=Agent)
        agent.agent_id = "test_agent"
        agent.description = AgentDescription(
            agent_id="test_agent",
            name="Test Agent",
            description="A test agent",
            capabilities=[AgentCapability.CODE_GENERATION],
        )
        
        registry.register(agent)
        result = registry.unregister("test_agent")
        
        assert result is True
        assert "test_agent" not in registry._agents
    
    def test_unregister_nonexistent_agent(self):
        """Test unregistering nonexistent agent."""
        registry = AgentRegistry()
        
        result = registry.unregister("nonexistent")
        
        assert result is False
    
    def test_get_agent(self):
        """Test getting an agent by ID."""
        registry = AgentRegistry()
        agent = MagicMock(spec=Agent)
        agent.agent_id = "test_agent"
        agent.description = AgentDescription(
            agent_id="test_agent",
            name="Test Agent",
            description="A test agent",
            capabilities=[AgentCapability.CODE_GENERATION],
        )
        
        registry.register(agent)
        retrieved = registry.get("test_agent")
        
        assert retrieved == agent
    
    def test_get_nonexistent_agent(self):
        """Test getting an agent that doesn't exist."""
        registry = AgentRegistry()
        
        retrieved = registry.get("nonexistent")
        
        assert retrieved is None
    
    def test_find_by_capability(self):
        """Test finding agents by capability."""
        registry = AgentRegistry()
        
        agent1 = MagicMock(spec=Agent)
        agent1.agent_id = "code_agent"
        agent1.description = AgentDescription(
            agent_id="code_agent",
            name="Code Agent",
            description="Code agent",
            capabilities=[AgentCapability.CODE_GENERATION],
        )
        
        agent2 = MagicMock(spec=Agent)
        agent2.agent_id = "debug_agent"
        agent2.description = AgentDescription(
            agent_id="debug_agent",
            name="Debug Agent",
            description="Debug agent",
            capabilities=[AgentCapability.DEBUGGING],
        )
        
        registry.register(agent1)
        registry.register(agent2)
        
        code_agents = registry.find_by_capability(AgentCapability.CODE_GENERATION)
        
        assert len(code_agents) == 1
        assert code_agents[0].agent_id == "code_agent"
    
    def test_find_by_capability_available_only(self):
        """Test finding agents by capability with available_only filter."""
        registry = AgentRegistry()
        
        agent1 = MagicMock(spec=Agent)
        agent1.agent_id = "code_agent"
        agent1.is_available = True
        agent1.description = AgentDescription(
            agent_id="code_agent",
            name="Code Agent",
            description="Code agent",
            capabilities=[AgentCapability.CODE_GENERATION],
        )
        
        agent2 = MagicMock(spec=Agent)
        agent2.agent_id = "busy_agent"
        agent2.is_available = False
        agent2.description = AgentDescription(
            agent_id="busy_agent",
            name="Busy Agent",
            description="Busy agent",
            capabilities=[AgentCapability.CODE_GENERATION],
        )
        
        registry.register(agent1)
        registry.register(agent2)
        
        available_agents = registry.find_by_capability(
            AgentCapability.CODE_GENERATION, available_only=True
        )
        
        assert len(available_agents) == 1
        assert available_agents[0].agent_id == "code_agent"
    
    def test_get_all(self):
        """Test getting all registered agents."""
        registry = AgentRegistry()
        
        agent1 = MagicMock(spec=Agent)
        agent1.agent_id = "agent1"
        agent1.description = AgentDescription(
            agent_id="agent1",
            name="Agent 1",
            description="First agent",
            capabilities=[AgentCapability.CODE_GENERATION],
        )
        
        agent2 = MagicMock(spec=Agent)
        agent2.agent_id = "agent2"
        agent2.description = AgentDescription(
            agent_id="agent2",
            name="Agent 2",
            description="Second agent",
            capabilities=[AgentCapability.DEBUGGING],
        )
        
        registry.register(agent1)
        registry.register(agent2)
        
        all_agents = registry.get_all()
        
        assert len(all_agents) == 2
        assert {a.agent_id for a in all_agents} == {"agent1", "agent2"}
    
    def test_get_all_descriptions(self):
        """Test getting all agent descriptions."""
        registry = AgentRegistry()
        
        agent = MagicMock(spec=Agent)
        agent.agent_id = "test_agent"
        agent.description = AgentDescription(
            agent_id="test_agent",
            name="Test Agent",
            description="A test agent",
            capabilities=[AgentCapability.CODE_GENERATION],
        )
        
        registry.register(agent)
        descriptions = registry.get_all_descriptions()
        
        assert len(descriptions) == 1
        assert descriptions[0].agent_id == "test_agent"
    
    def test_find_by_capabilities_match_any(self):
        """Test finding agents with any of the specified capabilities."""
        registry = AgentRegistry()
        
        agent1 = MagicMock(spec=Agent)
        agent1.agent_id = "code_agent"
        agent1.is_available = True
        agent1.description = AgentDescription(
            agent_id="code_agent",
            name="Code Agent",
            description="Code agent",
            capabilities=[AgentCapability.CODE_GENERATION],
        )
        
        agent2 = MagicMock(spec=Agent)
        agent2.agent_id = "debug_agent"
        agent2.is_available = True
        agent2.description = AgentDescription(
            agent_id="debug_agent",
            name="Debug Agent",
            description="Debug agent",
            capabilities=[AgentCapability.DEBUGGING],
        )
        
        registry.register(agent1)
        registry.register(agent2)
        
        agents = registry.find_by_capabilities(
            [AgentCapability.CODE_GENERATION, AgentCapability.DEBUGGING],
            match_all=False,
        )
        
        assert len(agents) == 2
    
    def test_find_by_capabilities_match_all(self):
        """Test finding agents with all specified capabilities."""
        registry = AgentRegistry()
        
        agent1 = MagicMock(spec=Agent)
        agent1.agent_id = "multi_agent"
        agent1.is_available = True
        agent1.description = AgentDescription(
            agent_id="multi_agent",
            name="Multi Agent",
            description="Multi-capability agent",
            capabilities=[AgentCapability.CODE_GENERATION, AgentCapability.DEBUGGING],
        )
        
        agent2 = MagicMock(spec=Agent)
        agent2.agent_id = "single_agent"
        agent2.is_available = True
        agent2.description = AgentDescription(
            agent_id="single_agent",
            name="Single Agent",
            description="Single capability agent",
            capabilities=[AgentCapability.CODE_GENERATION],
        )
        
        registry.register(agent1)
        registry.register(agent2)
        
        agents = registry.find_by_capabilities(
            [AgentCapability.CODE_GENERATION, AgentCapability.DEBUGGING],
            match_all=True,
        )
        
        assert len(agents) == 1
        assert agents[0].agent_id == "multi_agent"
    
    def test_find_by_capabilities_empty_list(self):
        """Test finding agents with empty capability list."""
        registry = AgentRegistry()
        
        agent = MagicMock(spec=Agent)
        agent.agent_id = "test_agent"
        agent.is_available = True
        agent.description = AgentDescription(
            agent_id="test_agent",
            name="Test Agent",
            description="Test agent",
            capabilities=[AgentCapability.CODE_GENERATION],
        )
        
        registry.register(agent)
        
        # Empty capabilities should return all agents
        agents = registry.find_by_capabilities([])
        assert len(agents) == 1
        
        # With available_only
        agents = registry.find_by_capabilities([], available_only=True)
        assert len(agents) == 1
    
    def test_find_by_capabilities_available_only(self):
        """Test finding agents with available_only filter."""
        registry = AgentRegistry()
        
        agent1 = MagicMock(spec=Agent)
        agent1.agent_id = "available_agent"
        agent1.is_available = True
        agent1.description = AgentDescription(
            agent_id="available_agent",
            name="Available Agent",
            description="Available agent",
            capabilities=[AgentCapability.CODE_GENERATION],
        )
        
        agent2 = MagicMock(spec=Agent)
        agent2.agent_id = "busy_agent"
        agent2.is_available = False
        agent2.description = AgentDescription(
            agent_id="busy_agent",
            name="Busy Agent",
            description="Busy agent",
            capabilities=[AgentCapability.CODE_GENERATION],
        )
        
        registry.register(agent1)
        registry.register(agent2)
        
        agents = registry.find_by_capabilities(
            [AgentCapability.CODE_GENERATION],
            available_only=True,
        )
        
        assert len(agents) == 1
        assert agents[0].agent_id == "available_agent"
    
    def test_get_best_agent_with_capabilities(self):
        """Test getting best agent with required capabilities."""
        registry = AgentRegistry()
        
        agent1 = MagicMock(spec=Agent)
        agent1.agent_id = "low_priority_agent"
        agent1.is_available = True
        agent1.description = AgentDescription(
            agent_id="low_priority_agent",
            name="Low Priority Agent",
            description="Low priority agent",
            capabilities=[AgentCapability.CODE_GENERATION],
            priority=1,
        )
        
        agent2 = MagicMock(spec=Agent)
        agent2.agent_id = "high_priority_agent"
        agent2.is_available = True
        agent2.description = AgentDescription(
            agent_id="high_priority_agent",
            name="High Priority Agent",
            description="High priority agent",
            capabilities=[AgentCapability.CODE_GENERATION],
            priority=10,
        )
        
        registry.register(agent1)
        registry.register(agent2)
        
        best = registry.get_best_agent(
            capabilities=[AgentCapability.CODE_GENERATION],
            available_only=True,
        )
        
        assert best.agent_id == "high_priority_agent"
    
    def test_get_best_agent_without_capabilities(self):
        """Test getting best agent without capability requirements."""
        registry = AgentRegistry()
        
        agent = MagicMock(spec=Agent)
        agent.agent_id = "test_agent"
        agent.is_available = True
        agent.description = AgentDescription(
            agent_id="test_agent",
            name="Test Agent",
            description="Test agent",
            capabilities=[AgentCapability.CODE_GENERATION],
            priority=5,
        )
        
        registry.register(agent)
        
        best = registry.get_best_agent(available_only=True)
        assert best.agent_id == "test_agent"
    
    def test_get_best_agent_no_match(self):
        """Test getting best agent when no agent matches."""
        registry = AgentRegistry()
        
        agent = MagicMock(spec=Agent)
        agent.agent_id = "test_agent"
        agent.is_available = True
        agent.description = AgentDescription(
            agent_id="test_agent",
            name="Test Agent",
            description="Test agent",
            capabilities=[AgentCapability.CODE_GENERATION],
        )
        
        registry.register(agent)
        
        # Request capability that no agent has
        best = registry.get_best_agent(
            capabilities=[AgentCapability.DEBUGGING],
            available_only=True,
        )
        
        assert best is None
    
    def test_get_best_agent_prefer_lower_priority(self):
        """Test getting best agent preferring lower priority."""
        registry = AgentRegistry()
        
        agent1 = MagicMock(spec=Agent)
        agent1.agent_id = "high_priority_agent"
        agent1.is_available = True
        agent1.description = AgentDescription(
            agent_id="high_priority_agent",
            name="High Priority Agent",
            description="High priority agent",
            capabilities=[AgentCapability.CODE_GENERATION],
            priority=10,
        )
        
        agent2 = MagicMock(spec=Agent)
        agent2.agent_id = "low_priority_agent"
        agent2.is_available = True
        agent2.description = AgentDescription(
            agent_id="low_priority_agent",
            name="Low Priority Agent",
            description="Low priority agent",
            capabilities=[AgentCapability.CODE_GENERATION],
            priority=1,
        )
        
        registry.register(agent1)
        registry.register(agent2)
        
        best = registry.get_best_agent(
            capabilities=[AgentCapability.CODE_GENERATION],
            prefer_higher_priority=False,
        )
        
        assert best.agent_id == "low_priority_agent"
    
    def test_get_available_agents(self):
        """Test getting all available agents."""
        registry = AgentRegistry()
        
        agent1 = MagicMock(spec=Agent)
        agent1.agent_id = "available_agent"
        agent1.is_available = True
        agent1.description = AgentDescription(
            agent_id="available_agent",
            name="Available Agent",
            description="Available agent",
            capabilities=[AgentCapability.CODE_GENERATION],
        )
        
        agent2 = MagicMock(spec=Agent)
        agent2.agent_id = "busy_agent"
        agent2.is_available = False
        agent2.description = AgentDescription(
            agent_id="busy_agent",
            name="Busy Agent",
            description="Busy agent",
            capabilities=[AgentCapability.CODE_GENERATION],
        )
        
        registry.register(agent1)
        registry.register(agent2)
        
        available = registry.get_available_agents()
        
        assert len(available) == 1
        assert available[0].agent_id == "available_agent"
    
    def test_get_stats(self):
        """Test getting registry statistics."""
        registry = AgentRegistry()
        
        agent1 = MagicMock(spec=Agent)
        agent1.agent_id = "agent1"
        agent1.is_available = True
        agent1.description = AgentDescription(
            agent_id="agent1",
            name="Agent 1",
            description="First agent",
            capabilities=[AgentCapability.CODE_GENERATION],
        )
        
        agent2 = MagicMock(spec=Agent)
        agent2.agent_id = "agent2"
        agent2.is_available = False
        agent2.description = AgentDescription(
            agent_id="agent2",
            name="Agent 2",
            description="Second agent",
            capabilities=[AgentCapability.DEBUGGING],
        )
        
        registry.register(agent1)
        registry.register(agent2)
        
        stats = registry.get_stats()
        
        assert stats["total_agents"] == 2
        assert stats["available_agents"] == 1
        assert "capability_counts" in stats
        assert stats["capability_counts"]["code_generation"] == 1
        assert stats["capability_counts"]["debugging"] == 1
    
    def test_clear(self):
        """Test clearing all registered agents."""
        registry = AgentRegistry()
        
        agent = MagicMock(spec=Agent)
        agent.agent_id = "test_agent"
        agent.description = AgentDescription(
            agent_id="test_agent",
            name="Test Agent",
            description="Test agent",
            capabilities=[AgentCapability.CODE_GENERATION],
        )
        
        registry.register(agent)
        assert len(registry._agents) == 1
        
        registry.clear()
        
        assert len(registry._agents) == 0
        # Verify capability index is also cleared
        for cap in AgentCapability:
            assert len(registry._capability_index[cap]) == 0
    
    def test_to_dict(self):
        """Test converting registry to dictionary."""
        registry = AgentRegistry()
        
        agent = MagicMock(spec=Agent)
        agent.agent_id = "test_agent"
        agent.to_dict = MagicMock(return_value={"id": "test_agent", "name": "Test Agent"})
        agent.is_available = True
        agent.description = AgentDescription(
            agent_id="test_agent",
            name="Test Agent",
            description="Test agent",
            capabilities=[AgentCapability.CODE_GENERATION],
        )
        
        registry.register(agent)
        data = registry.to_dict()
        
        assert "agents" in data
        assert "stats" in data
        assert "test_agent" in data["agents"]


class TestCoordinator:
    """Tests for Coordinator class."""
    
    @pytest.fixture
    def mock_registry(self):
        """Create a mock agent registry."""
        registry = AgentRegistry()
        
        # Add a mock agent
        agent = MagicMock(spec=Agent)
        agent.agent_id = "test_agent"
        agent.description = AgentDescription(
            agent_id="test_agent",
            name="Test Agent",
            description="A test agent",
            capabilities=[AgentCapability.CODE_GENERATION],
        )
        agent.execute = AsyncMock(return_value=MagicMock(output="Task completed"))
        
        registry.register(agent)
        return registry
    
    def test_coordinator_initialization(self, mock_registry):
        """Test Coordinator initialization."""
        coordinator = Coordinator(mock_registry)
        
        assert coordinator.registry == mock_registry
        assert len(coordinator._tasks) == 0
    
    def test_coordinator_with_config(self, mock_registry):
        """Test Coordinator with custom config."""
        config = CoordinatorConfig(max_concurrent_tasks=5)
        coordinator = Coordinator(mock_registry, config)
        
        assert coordinator.config.max_concurrent_tasks == 5
    
    @pytest.mark.asyncio
    async def test_submit_task(self, mock_registry):
        """Test submitting a task."""
        coordinator = Coordinator(mock_registry)
        
        task_id = await coordinator.submit("Fix the bug in main.py")
        
        assert task_id is not None
        assert task_id in coordinator._tasks
    
    @pytest.mark.asyncio
    async def test_submit_and_wait(self, mock_registry):
        """Test submitting and waiting for a task."""
        coordinator = Coordinator(mock_registry)
        await coordinator.start()
        
        try:
            task = await coordinator.submit_and_wait("Test task")
            assert task is not None
        finally:
            await coordinator.stop()
    
    @pytest.mark.asyncio
    async def test_coordinator_start_stop(self, mock_registry):
        """Test coordinator start and stop."""
        coordinator = Coordinator(mock_registry)
        
        await coordinator.start()
        assert coordinator._started is True
        
        await coordinator.stop()
        assert coordinator._started is False


class TestCoordinatorEdgeCases:
    """Edge case tests for Coordinator."""
    
    @pytest.fixture
    def mock_registry(self):
        """Create a mock agent registry."""
        registry = AgentRegistry()
        return registry
    
    def test_empty_registry(self, mock_registry):
        """Test coordinator with empty registry."""
        coordinator = Coordinator(mock_registry)
        
        assert coordinator.registry == mock_registry
        assert len(coordinator.registry._agents) == 0
    
    @pytest.mark.asyncio
    async def test_task_timeout_config(self, mock_registry):
        """Test task timeout configuration."""
        config = CoordinatorConfig(task_timeout_seconds=1)
        coordinator = Coordinator(mock_registry, config)
        
        assert coordinator.config.task_timeout_seconds == 1
