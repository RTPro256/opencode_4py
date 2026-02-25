"""
Unit tests for the Subagents system.
"""

import pytest
from datetime import datetime

from opencode.core.subagents import (
    SubagentConfig,
    SubagentLevel,
    SubagentRuntimeConfig,
    ValidationResult,
    SubagentError,
    SubagentNotFoundError,
    SubagentAlreadyExistsError,
    SubagentValidationError,
    SubagentValidator,
    SubagentManager,
    BuiltinAgentRegistry,
    SubAgentEventEmitter,
    SubAgentEventType,
    SubAgentStartEvent,
    SubAgentFinishEvent,
    PromptConfig,
    ModelConfig,
    ToolConfig,
    RunConfig,
    SubagentTerminateMode,
)


class TestSubagentConfig:
    """Tests for SubagentConfig."""
    
    def test_create_minimal_config(self):
        """Test creating a minimal valid config."""
        config = SubagentConfig(
            name="test-agent",
            description="A test agent"
        )
        
        assert config.name == "test-agent"
        assert config.description == "A test agent"
        assert config.enabled is True
        assert config.version == "1.0.0"
    
    def test_create_full_config(self):
        """Test creating a config with all fields."""
        config = SubagentConfig(
            name="full-agent",
            description="A fully configured agent",
            prompt=PromptConfig(
                system="You are a helpful assistant.",
                include_context=True
            ),
            model=ModelConfig(
                provider="openai",
                name="gpt-4",
                temperature=0.7
            ),
            tools=ToolConfig(
                allow=["read", "write"],
                deny=["bash"],
                require_approval=["write"],
                auto_approve=["read"]
            ),
            run=RunConfig(
                max_rounds=5,
                terminate_mode=SubagentTerminateMode.AUTO
            ),
            tags=["test", "example"],
            author="Test Author"
        )
        
        assert config.name == "full-agent"
        assert config.prompt.system == "You are a helpful assistant."
        assert config.model.provider == "openai"
        assert config.tools.allow == ["read", "write"]
        assert config.run.max_rounds == 5


class TestSubagentValidator:
    """Tests for SubagentValidator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = SubagentValidator()
    
    def test_validate_valid_config(self):
        """Test validating a valid configuration."""
        config = {
            "name": "valid-agent",
            "description": "A valid agent configuration"
        }
        
        result = self.validator.validate(config)
        
        assert result.valid is True
        assert len(result.errors) == 0
        assert result.config is not None
        assert result.config.name == "valid-agent"
    
    def test_validate_missing_name(self):
        """Test validation with missing name."""
        config = {
            "description": "Missing name"
        }
        
        result = self.validator.validate(config)
        
        assert result.valid is False
        assert "Missing required field: name" in result.errors
    
    def test_validate_invalid_name(self):
        """Test validation with invalid name."""
        config = {
            "name": "123-invalid",
            "description": "Invalid name"
        }
        
        result = self.validator.validate(config)
        
        assert result.valid is False
        assert any("Invalid name" in e for e in result.errors)
    
    def test_validate_reserved_name(self):
        """Test validation with reserved name."""
        config = {
            "name": "system",
            "description": "Reserved name"
        }
        
        result = self.validator.validate(config)
        
        assert result.valid is False
    
    def test_validate_tool_conflicts(self):
        """Test validation with conflicting tool settings."""
        config = {
            "name": "conflict-agent",
            "description": "Has conflicts",
            "tools": {
                "allow": ["read"],
                "deny": ["read"]
            }
        }
        
        result = self.validator.validate(config)
        
        # Should have warnings but still be valid
        assert len(result.warnings) > 0


class TestBuiltinAgentRegistry:
    """Tests for BuiltinAgentRegistry."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.registry = BuiltinAgentRegistry()
    
    def test_list_builtin(self):
        """Test listing built-in agents."""
        agents = self.registry.list_builtin()
        
        assert len(agents) > 0
        assert any(a.name == "general" for a in agents)
        assert any(a.name == "code-reviewer" for a in agents)
    
    def test_get_builtin(self):
        """Test getting a built-in agent."""
        agent = self.registry.get_builtin("general")
        
        assert agent is not None
        assert agent.name == "general"
    
    def test_get_nonexistent_builtin(self):
        """Test getting a non-existent built-in agent."""
        agent = self.registry.get_builtin("nonexistent")
        
        assert agent is None
    
    def test_is_builtin(self):
        """Test checking if a name is built-in."""
        assert self.registry.is_builtin("general") is True
        assert self.registry.is_builtin("nonexistent") is False


class TestSubagentErrors:
    """Tests for subagent errors."""
    
    def test_subagent_not_found_error(self):
        """Test SubagentNotFoundError."""
        error = SubagentNotFoundError("test-agent", "project")
        
        assert error.code.value == "NOT_FOUND"
        assert "test-agent" in str(error)
        assert "project" in str(error)
    
    def test_subagent_already_exists_error(self):
        """Test SubagentAlreadyExistsError."""
        error = SubagentAlreadyExistsError("test-agent", "project")
        
        assert error.code.value == "ALREADY_EXISTS"
        assert "test-agent" in str(error)
    
    def test_subagent_validation_error(self):
        """Test SubagentValidationError."""
        error = SubagentValidationError(
            errors=["Invalid name", "Missing description"],
            warnings=["Long description"]
        )
        
        assert error.code.value == "VALIDATION_ERROR"
        assert len(error.validation_errors) == 2
        assert len(error.validation_warnings) == 1


class TestSubAgentEventEmitter:
    """Tests for SubAgentEventEmitter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.emitter = SubAgentEventEmitter()
        self.received_events = []
    
    async def _handler(self, event):
        """Test event handler."""
        self.received_events.append(event)
    
    @pytest.mark.asyncio
    async def test_emit_event(self):
        """Test emitting an event."""
        self.emitter.on(SubAgentEventType.START, self._handler)
        
        event = SubAgentStartEvent(
            agent_name="test-agent",
            task="Test task"
        )
        
        await self.emitter.emit(event)
        
        assert len(self.received_events) == 1
        assert self.received_events[0].agent_name == "test-agent"
    
    @pytest.mark.asyncio
    async def test_on_any(self):
        """Test subscribing to all events."""
        self.emitter.on_any(self._handler)
        
        start_event = SubAgentStartEvent(agent_name="test")
        finish_event = SubAgentFinishEvent(agent_name="test", success=True)
        
        await self.emitter.emit(start_event)
        await self.emitter.emit(finish_event)
        
        assert len(self.received_events) == 2
    
    def test_off(self):
        """Test unsubscribing."""
        self.emitter.on(SubAgentEventType.START, self._handler)
        self.emitter.off(SubAgentEventType.START, self._handler)
        
        # Should not raise
        assert len(self.emitter._handlers[SubAgentEventType.START]) == 0


class TestSubagentManager:
    """Tests for SubagentManager."""
    
    def test_manager_initialization(self, tmp_path):
        """Test manager initialization."""
        manager = SubagentManager(
            project_root=tmp_path,
            user_home=tmp_path / "home"
        )
        
        assert manager.project_root == tmp_path
        assert manager.validator is not None
        assert manager.builtin_registry is not None
    
    @pytest.mark.asyncio
    async def test_list_subagents(self, tmp_path):
        """Test listing subagents."""
        manager = SubagentManager(project_root=tmp_path)
        
        subagents = await manager.list_subagents()
        
        # Should include built-in agents
        assert len(subagents) > 0
        assert any(s.name == "general" for s in subagents)
    
    @pytest.mark.asyncio
    async def test_get_subagent_builtin(self, tmp_path):
        """Test getting a built-in subagent."""
        manager = SubagentManager(project_root=tmp_path)
        
        agent = await manager.get_subagent("general")
        
        assert agent.name == "general"
    
    @pytest.mark.asyncio
    async def test_get_subagent_not_found(self, tmp_path):
        """Test getting a non-existent subagent."""
        manager = SubagentManager(project_root=tmp_path)
        
        with pytest.raises(SubagentNotFoundError):
            await manager.get_subagent("nonexistent")
    
    def test_get_runtime_config(self, tmp_path):
        """Test converting to runtime config."""
        manager = SubagentManager(project_root=tmp_path)
        
        config = SubagentConfig(
            name="test",
            description="Test",
            model=ModelConfig(provider="anthropic", name="claude-3"),
            tools=ToolConfig(allow=["read", "write"], deny=["bash"])
        )
        
        runtime = manager.get_runtime_config(
            config,
            default_provider="openai",
            default_model="gpt-4",
            available_tools=["read", "write", "bash", "grep"]
        )
        
        assert runtime.name == "test"
        assert runtime.model_provider == "anthropic"
        assert runtime.model_name == "claude-3"
        assert "read" in runtime.allowed_tools
        assert "write" in runtime.allowed_tools
        assert "bash" in runtime.denied_tools
