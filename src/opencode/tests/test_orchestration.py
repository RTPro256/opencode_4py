"""
Tests for Orchestration Module
"""

import pytest
import asyncio

from opencode.core.orchestration.agent import (
    Agent,
    AgentDescription,
    AgentTask,
    AgentCapability,
    AgentStatus,
)
from opencode.core.orchestration.registry import AgentRegistry
from opencode.core.orchestration.router import (
    OrchestrationRouter,
    IntentClassifier,
    IntentCategory,
    Intent,
)


class TestAgent:
    """Tests for Agent class."""
    
    def test_agent_creation(self):
        """Test creating an agent."""
        description = AgentDescription(
            agent_id="test_agent",
            name="Test Agent",
            description="A test agent",
            capabilities=[AgentCapability.CODE_GENERATION],
        )
        
        agent = Agent(description)
        assert agent.agent_id == "test_agent"
        assert agent.status == AgentStatus.IDLE
        assert agent.is_available is True
    
    def test_agent_availability(self):
        """Test agent availability tracking."""
        description = AgentDescription(
            agent_id="test_agent",
            name="Test Agent",
            description="A test agent",
            max_concurrent_tasks=1,
        )
        
        agent = Agent(description)
        assert agent.is_available is True
        
        # Simulate task assignment
        task = AgentTask(task_id="1", prompt="Test")
        agent._current_tasks.append(task)
        agent._status = AgentStatus.BUSY
        
        assert agent.is_available is False
    
    def test_agent_description_serialization(self):
        """Test agent description serialization."""
        description = AgentDescription(
            agent_id="test_agent",
            name="Test Agent",
            description="A test agent",
            capabilities=[AgentCapability.CODE_GENERATION, AgentCapability.DEBUGGING],
            tools=["read_file", "write_file"],
        )
        
        data = description.to_dict()
        restored = AgentDescription.from_dict(data)
        
        assert restored.agent_id == "test_agent"
        assert len(restored.capabilities) == 2
        assert AgentCapability.CODE_GENERATION in restored.capabilities


class TestAgentRegistry:
    """Tests for AgentRegistry."""
    
    def test_register_agent(self):
        """Test registering an agent."""
        registry = AgentRegistry()
        
        description = AgentDescription(
            agent_id="code_agent",
            name="Code Agent",
            description="Handles code tasks",
            capabilities=[AgentCapability.CODE_GENERATION],
        )
        
        agent = Agent(description)
        registry.register(agent)
        
        assert registry.get("code_agent") == agent
        assert len(registry.get_all()) == 1
    
    def test_unregister_agent(self):
        """Test unregistering an agent."""
        registry = AgentRegistry()
        
        description = AgentDescription(agent_id="test", name="Test", description="Test")
        agent = Agent(description)
        registry.register(agent)
        
        assert registry.unregister("test") is True
        assert registry.get("test") is None
        assert registry.unregister("nonexistent") is False
    
    def test_find_by_capability(self):
        """Test finding agents by capability."""
        registry = AgentRegistry()
        
        code_agent = Agent(AgentDescription(
            agent_id="code",
            name="Code",
            description="Code agent",
            capabilities=[AgentCapability.CODE_GENERATION],
        ))
        
        debug_agent = Agent(AgentDescription(
            agent_id="debug",
            name="Debug",
            description="Debug agent",
            capabilities=[AgentCapability.DEBUGGING],
        ))
        
        registry.register(code_agent)
        registry.register(debug_agent)
        
        code_agents = registry.find_by_capability(AgentCapability.CODE_GENERATION)
        assert len(code_agents) == 1
        assert code_agents[0].agent_id == "code"
    
    def test_find_by_multiple_capabilities(self):
        """Test finding agents with multiple capabilities."""
        registry = AgentRegistry()
        
        agent1 = Agent(AgentDescription(
            agent_id="agent1",
            name="Agent 1",
            description="Has code and debug",
            capabilities=[AgentCapability.CODE_GENERATION, AgentCapability.DEBUGGING],
        ))
        
        agent2 = Agent(AgentDescription(
            agent_id="agent2",
            name="Agent 2",
            description="Has only code",
            capabilities=[AgentCapability.CODE_GENERATION],
        ))
        
        registry.register(agent1)
        registry.register(agent2)
        
        # Match all
        both = registry.find_by_capabilities(
            [AgentCapability.CODE_GENERATION, AgentCapability.DEBUGGING],
            match_all=True,
        )
        assert len(both) == 1
        assert both[0].agent_id == "agent1"
        
        # Match any
        any_cap = registry.find_by_capabilities(
            [AgentCapability.CODE_GENERATION, AgentCapability.DEBUGGING],
            match_all=False,
        )
        assert len(any_cap) == 2
    
    def test_get_best_agent(self):
        """Test getting the best agent."""
        registry = AgentRegistry()
        
        low_priority = Agent(AgentDescription(
            agent_id="low",
            name="Low Priority",
            description="Low priority agent",
            capabilities=[AgentCapability.CODE_GENERATION],
            priority=1,
        ))
        
        high_priority = Agent(AgentDescription(
            agent_id="high",
            name="High Priority",
            description="High priority agent",
            capabilities=[AgentCapability.CODE_GENERATION],
            priority=10,
        ))
        
        registry.register(low_priority)
        registry.register(high_priority)
        
        best = registry.get_best_agent(capabilities=[AgentCapability.CODE_GENERATION])
        assert best.agent_id == "high"
    
    def test_registry_stats(self):
        """Test registry statistics."""
        registry = AgentRegistry()
        
        agent = Agent(AgentDescription(
            agent_id="test",
            name="Test",
            description="Test agent",
            capabilities=[AgentCapability.CODE_GENERATION],
        ))
        
        registry.register(agent)
        stats = registry.get_stats()
        
        assert stats["total_agents"] == 1
        assert stats["available_agents"] == 1


class TestIntentClassifier:
    """Tests for IntentClassifier."""
    
    def setup_method(self):
        self.classifier = IntentClassifier()
    
    def test_code_generation_intent(self):
        """Test code generation intent classification."""
        intent = self.classifier.classify("Create a new function to calculate fibonacci")
        
        assert intent.category == IntentCategory.CODE_GENERATION
        assert intent.confidence > 0
    
    def test_debugging_intent(self):
        """Test debugging intent classification."""
        intent = self.classifier.classify("Fix the bug in main.py")
        
        assert intent.category == IntentCategory.DEBUGGING
    
    def test_question_intent(self):
        """Test question intent classification."""
        intent = self.classifier.classify("What is the purpose of this function?")
        
        assert intent.category == IntentCategory.QUESTION
    
    def test_file_operation_intent(self):
        """Test file operation intent classification."""
        intent = self.classifier.classify("Read the file config.yaml")
        
        assert intent.category == IntentCategory.FILE_OPERATION
    
    def test_capability_mapping(self):
        """Test intent to capability mapping."""
        intent = Intent(category=IntentCategory.CODE_GENERATION, confidence=0.8)
        capability = self.classifier.get_capability_for_intent(intent)
        
        assert capability == AgentCapability.CODE_GENERATION


class TestOrchestrationRouter:
    """Tests for OrchestrationRouter."""
    
    def setup_method(self):
        self.registry = AgentRegistry()
        
        # Register test agents
        code_agent = Agent(AgentDescription(
            agent_id="code_agent",
            name="Code Agent",
            description="Handles code generation and modification",
            capabilities=[AgentCapability.CODE_GENERATION],
            priority=10,
        ))
        
        debug_agent = Agent(AgentDescription(
            agent_id="debug_agent",
            name="Debug Agent",
            description="Handles debugging tasks",
            capabilities=[AgentCapability.DEBUGGING],
            priority=5,
        ))
        
        self.registry.register(code_agent)
        self.registry.register(debug_agent)
        
        self.router = OrchestrationRouter(self.registry)
    
    def test_route_code_request(self):
        """Test routing a code request."""
        result = self.router.route("Create a new function")
        
        assert result.agent_id == "code_agent"
        assert result.intent.category == IntentCategory.CODE_GENERATION
    
    def test_route_debug_request(self):
        """Test routing a debug request."""
        result = self.router.route("Fix the bug in the code")
        
        assert result.agent_id == "debug_agent"
        assert result.intent.category == IntentCategory.DEBUGGING
    
    def test_routing_confidence(self):
        """Test routing confidence."""
        result = self.router.route("Create a function")
        
        assert result.confidence >= 0
        assert result.confidence <= 1
    
    def test_routing_suggestions(self):
        """Test getting routing suggestions."""
        suggestions = self.router.get_routing_suggestions("Create a function")
        
        assert len(suggestions) > 0
        assert "agent_id" in suggestions[0]
        assert "match_score" in suggestions[0]


class TestAgentTask:
    """Tests for AgentTask."""
    
    def test_task_creation(self):
        """Test creating a task."""
        task = AgentTask(
            task_id="test_1",
            prompt="Test prompt",
            context={"key": "value"},
        )
        
        assert task.task_id == "test_1"
        assert task.status == "pending"
        assert task.context["key"] == "value"
    
    def test_task_serialization(self):
        """Test task serialization."""
        task = AgentTask(
            task_id="test_1",
            prompt="Test",
            result="Done",
        )
        
        data = task.to_dict()
        assert data["task_id"] == "test_1"
        assert data["result"] == "Done"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
