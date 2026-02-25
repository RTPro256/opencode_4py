"""
Tests for new modes: ReviewMode and OrchestratorMode.

Tests the configuration and registration of the new modes.
"""

import pytest
from opencode.core.modes.modes import (
    CodeMode,
    ArchitectMode,
    AskMode,
    DebugMode,
    ReviewMode,
    OrchestratorMode,
)
from opencode.core.modes.base import ModeToolAccess


class TestReviewMode:
    """Tests for ReviewMode configuration."""
    
    def test_review_mode_registered(self):
        """Test that ReviewMode is registered."""
        config = ReviewMode.get_config()
        assert config is not None
        assert config.name == "review"
    
    def test_review_mode_description(self):
        """Test ReviewMode description."""
        config = ReviewMode.get_config()
        assert "accuracy" in config.description.lower()
    
    def test_review_mode_tool_access(self):
        """Test ReviewMode has whitelist tool access."""
        config = ReviewMode.get_config()
        assert config.tool_access == ModeToolAccess.WHITELIST
    
    def test_review_mode_has_read_tools(self):
        """Test ReviewMode has read tools."""
        config = ReviewMode.get_config()
        assert "read_file" in config.allowed_tools
        assert "list_files" in config.allowed_tools
        assert "search_files" in config.allowed_tools
    
    def test_review_mode_has_git_tools(self):
        """Test ReviewMode has git tools for reviewing changes."""
        config = ReviewMode.get_config()
        assert "git_diff" in config.allowed_tools
        assert "git_log" in config.allowed_tools
        assert "git_blame" in config.allowed_tools
    
    def test_review_mode_blocks_write_tools(self):
        """Test ReviewMode blocks write tools."""
        config = ReviewMode.get_config()
        assert "write_file" in config.blocked_tools
        assert "edit_file" in config.blocked_tools
        assert "delete_file" in config.blocked_tools
        assert "execute_command" in config.blocked_tools
    
    def test_review_mode_system_prompt(self):
        """Test ReviewMode has appropriate system prompt."""
        config = ReviewMode.get_config()
        assert "reviewer" in config.system_prompt_prefix.lower()
        assert "accuracy" in config.system_prompt_prefix.lower()
    
    def test_review_mode_supports_streaming(self):
        """Test ReviewMode supports streaming."""
        config = ReviewMode.get_config()
        assert config.supports_streaming is True


class TestOrchestratorMode:
    """Tests for OrchestratorMode configuration."""
    
    def test_orchestrator_mode_registered(self):
        """Test that OrchestratorMode is registered."""
        config = OrchestratorMode.get_config()
        assert config is not None
        assert config.name == "orchestrator"
    
    def test_orchestrator_mode_description(self):
        """Test OrchestratorMode description."""
        config = OrchestratorMode.get_config()
        assert "coordinate" in config.description.lower()
    
    def test_orchestrator_mode_tool_access(self):
        """Test OrchestratorMode has whitelist tool access."""
        config = OrchestratorMode.get_config()
        assert config.tool_access == ModeToolAccess.WHITELIST
    
    def test_orchestrator_mode_has_mode_switching(self):
        """Test OrchestratorMode has mode switching capability."""
        config = OrchestratorMode.get_config()
        assert "switch_mode" in config.allowed_tools
    
    def test_orchestrator_mode_has_task_management(self):
        """Test OrchestratorMode has task management tools."""
        config = OrchestratorMode.get_config()
        assert "new_task" in config.allowed_tools
        assert "update_todo_list" in config.allowed_tools
    
    def test_orchestrator_mode_has_workflow_tools(self):
        """Test OrchestratorMode has workflow tools."""
        config = OrchestratorMode.get_config()
        assert "execute_workflow" in config.allowed_tools
        assert "create_workflow" in config.allowed_tools
    
    def test_orchestrator_mode_blocks_write_tools(self):
        """Test OrchestratorMode blocks direct file modifications."""
        config = OrchestratorMode.get_config()
        assert "write_file" in config.blocked_tools
        assert "edit_file" in config.blocked_tools
        assert "delete_file" in config.blocked_tools
    
    def test_orchestrator_mode_system_prompt(self):
        """Test OrchestratorMode has appropriate system prompt."""
        config = OrchestratorMode.get_config()
        assert "orchestrat" in config.system_prompt_prefix.lower()
        assert "delegate" in config.system_prompt_prefix.lower()
    
    def test_orchestrator_mode_lists_other_modes(self):
        """Test OrchestratorMode system prompt mentions other modes."""
        config = OrchestratorMode.get_config()
        prompt = config.system_prompt_prefix.lower()
        assert "architect" in prompt
        assert "code" in prompt
        assert "debug" in prompt
        assert "review" in prompt


class TestAllModesExported:
    """Tests to ensure all modes are properly exported."""
    
    def test_all_modes_in_all(self):
        """Test that all modes are in __all__."""
        from opencode.core.modes.modes import __all__
        
        assert "CodeMode" in __all__
        assert "ArchitectMode" in __all__
        assert "AskMode" in __all__
        assert "DebugMode" in __all__
        assert "ReviewMode" in __all__
        assert "OrchestratorMode" in __all__
    
    def test_all_modes_importable(self):
        """Test that all modes can be imported."""
        from opencode.core.modes.modes import (
            CodeMode,
            ArchitectMode,
            AskMode,
            DebugMode,
            ReviewMode,
            OrchestratorMode,
        )
        
        # Just verify they exist
        assert CodeMode is not None
        assert ArchitectMode is not None
        assert AskMode is not None
        assert DebugMode is not None
        assert ReviewMode is not None
        assert OrchestratorMode is not None
    
    def test_all_modes_have_config(self):
        """Test that all modes have a valid config."""
        modes = [CodeMode, ArchitectMode, AskMode, DebugMode, ReviewMode, OrchestratorMode]
        
        for mode in modes:
            config = mode.get_config()
            assert config is not None
            assert config.name is not None
            assert config.description is not None


class TestModeRegistry:
    """Tests for mode registry integration."""
    
    def test_review_mode_in_registry(self):
        """Test that ReviewMode is in the registry."""
        from opencode.core.modes.registry import ModeRegistry
        
        mode_class = ModeRegistry.get("review")
        assert mode_class is not None
        config = mode_class.get_config()
        assert config.name == "review"
    
    def test_orchestrator_mode_in_registry(self):
        """Test that OrchestratorMode is in the registry."""
        from opencode.core.modes.registry import ModeRegistry
        
        mode_class = ModeRegistry.get("orchestrator")
        assert mode_class is not None
        config = mode_class.get_config()
        assert config.name == "orchestrator"
    
    def test_all_modes_registered(self):
        """Test that all modes are registered."""
        from opencode.core.modes.registry import ModeRegistry
        
        expected_modes = ["code", "architect", "ask", "debug", "review", "orchestrator"]
        
        for mode_name in expected_modes:
            mode_class = ModeRegistry.get(mode_name)
            assert mode_class is not None, f"Mode '{mode_name}' not registered"


class TestNewSubagents:
    """Tests for new subagents."""
    
    def test_project_reviewer_exists(self):
        """Test that project-reviewer subagent exists."""
        from opencode.core.subagents.builtin import BuiltinAgentRegistry
        
        registry = BuiltinAgentRegistry()
        config = registry.get_builtin("project-reviewer")
        
        assert config is not None
        assert "review" in config.tags
        assert "project" in config.tags
    
    def test_plan_validator_exists(self):
        """Test that plan-validator subagent exists."""
        from opencode.core.subagents.builtin import BuiltinAgentRegistry
        
        registry = BuiltinAgentRegistry()
        config = registry.get_builtin("plan-validator")
        
        assert config is not None
        assert "validation" in config.tags
    
    def test_task_orchestrator_exists(self):
        """Test that task-orchestrator subagent exists."""
        from opencode.core.subagents.builtin import BuiltinAgentRegistry
        
        registry = BuiltinAgentRegistry()
        config = registry.get_builtin("task-orchestrator")
        
        assert config is not None
        assert "orchestration" in config.tags
    
    def test_all_new_subagents_are_builtin(self):
        """Test that all new subagents are marked as builtin."""
        from opencode.core.subagents.builtin import BuiltinAgentRegistry
        
        registry = BuiltinAgentRegistry()
        
        assert registry.is_builtin("project-reviewer")
        assert registry.is_builtin("plan-validator")
        assert registry.is_builtin("task-orchestrator")
    
    def test_new_subagents_count(self):
        """Test that we have 9 built-in subagents."""
        from opencode.core.subagents.builtin import BuiltinAgentRegistry
        
        registry = BuiltinAgentRegistry()
        agents = registry.list_builtin()
        
        assert len(agents) == 9


class TestNewAgentCapabilities:
    """Tests for new agent capabilities."""
    
    def test_project_review_capability_exists(self):
        """Test that PROJECT_REVIEW capability exists."""
        from opencode.core.orchestration.agent import AgentCapability
        
        assert AgentCapability.PROJECT_REVIEW is not None
        assert AgentCapability.PROJECT_REVIEW.value == "project_review"
    
    def test_plan_validation_capability_exists(self):
        """Test that PLAN_VALIDATION capability exists."""
        from opencode.core.orchestration.agent import AgentCapability
        
        assert AgentCapability.PLAN_VALIDATION is not None
        assert AgentCapability.PLAN_VALIDATION.value == "plan_validation"
    
    def test_task_orchestration_capability_exists(self):
        """Test that TASK_ORCHESTRATION capability exists."""
        from opencode.core.orchestration.agent import AgentCapability
        
        assert AgentCapability.TASK_ORCHESTRATION is not None
        assert AgentCapability.TASK_ORCHESTRATION.value == "task_orchestration"
    
    def test_quality_assurance_capability_exists(self):
        """Test that QUALITY_ASSURANCE capability exists."""
        from opencode.core.orchestration.agent import AgentCapability
        
        assert AgentCapability.QUALITY_ASSURANCE is not None
        assert AgentCapability.QUALITY_ASSURANCE.value == "quality_assurance"
    
    def test_goal_verification_capability_exists(self):
        """Test that GOAL_VERIFICATION capability exists."""
        from opencode.core.orchestration.agent import AgentCapability
        
        assert AgentCapability.GOAL_VERIFICATION is not None
        assert AgentCapability.GOAL_VERIFICATION.value == "goal_verification"
