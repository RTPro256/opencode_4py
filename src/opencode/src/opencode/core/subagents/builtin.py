"""
Built-in subagent registry.

Provides pre-configured subagents for common use cases.
"""

from typing import Dict, List, Optional
from .types import (
    SubagentConfig,
    PromptConfig,
    ModelConfig,
    ToolConfig,
    RunConfig,
    SubagentTerminateMode,
)


class BuiltinAgentRegistry:
    """Registry for built-in subagent configurations."""
    
    def __init__(self):
        """Initialize the registry with built-in agents."""
        self._agents: Dict[str, SubagentConfig] = {}
        self._register_builtin_agents()
    
    def _register_builtin_agents(self) -> None:
        """Register all built-in agents."""
        # General-purpose assistant
        self._register(SubagentConfig(
            name="general",
            description="General-purpose assistant for multi-step tasks and searches",
            prompt=PromptConfig(
                system="You are a helpful AI assistant. You can perform multi-step tasks and search for information as needed.",
                include_context=True,
            ),
            tools=ToolConfig(
                allow=["*"],
                deny=[],
                require_approval=[],
                auto_approve=["read", "glob", "grep", "ls"],
            ),
            run=RunConfig(
                max_rounds=10,
                terminate_mode=SubagentTerminateMode.AUTO,
            ),
            tags=["general", "assistant"],
            enabled=True,
        ))
        
        # Code reviewer
        self._register(SubagentConfig(
            name="code-reviewer",
            description="Specialized agent for code review and quality analysis",
            prompt=PromptConfig(
                system="You are a code reviewer. Analyze code for bugs, security issues, performance problems, and style violations. Provide constructive feedback.",
                include_context=True,
            ),
            tools=ToolConfig(
                allow=["read", "glob", "grep", "ls", "lsp"],
                deny=["write", "edit", "bash"],
                require_approval=[],
                auto_approve=["read", "glob", "grep", "ls"],
            ),
            run=RunConfig(
                max_rounds=5,
                terminate_mode=SubagentTerminateMode.AUTO,
            ),
            tags=["code", "review", "quality"],
            enabled=True,
        ))
        
        # Test generator
        self._register(SubagentConfig(
            name="test-generator",
            description="Specialized agent for generating unit tests",
            prompt=PromptConfig(
                system="You are a test engineer. Generate comprehensive unit tests for the provided code. Focus on edge cases, error handling, and code coverage.",
                include_context=True,
            ),
            tools=ToolConfig(
                allow=["read", "write", "glob", "grep", "ls", "bash"],
                deny=[],
                require_approval=["bash"],
                auto_approve=["read", "glob", "grep", "ls"],
            ),
            run=RunConfig(
                max_rounds=8,
                terminate_mode=SubagentTerminateMode.AUTO,
            ),
            tags=["testing", "generation"],
            enabled=True,
        ))
        
        # Documentation writer
        self._register(SubagentConfig(
            name="doc-writer",
            description="Specialized agent for writing documentation",
            prompt=PromptConfig(
                system="You are a technical writer. Create clear, comprehensive documentation for code. Include examples, usage notes, and API references.",
                include_context=True,
            ),
            tools=ToolConfig(
                allow=["read", "write", "glob", "grep", "ls"],
                deny=["bash", "edit"],
                require_approval=[],
                auto_approve=["read", "glob", "grep", "ls"],
            ),
            run=RunConfig(
                max_rounds=5,
                terminate_mode=SubagentTerminateMode.AUTO,
            ),
            tags=["documentation", "writing"],
            enabled=True,
        ))
        
        # Refactoring agent
        self._register(SubagentConfig(
            name="refactorer",
            description="Specialized agent for code refactoring",
            prompt=PromptConfig(
                system="You are a refactoring specialist. Improve code structure, readability, and maintainability while preserving functionality. Apply design patterns and best practices.",
                include_context=True,
            ),
            tools=ToolConfig(
                allow=["read", "write", "edit", "glob", "grep", "ls", "lsp"],
                deny=["bash"],
                require_approval=["write", "edit"],
                auto_approve=["read", "glob", "grep", "ls"],
            ),
            run=RunConfig(
                max_rounds=10,
                terminate_mode=SubagentTerminateMode.AUTO,
            ),
            tags=["refactoring", "code-quality"],
            enabled=True,
        ))
        
        # Security analyzer
        self._register(SubagentConfig(
            name="security-analyzer",
            description="Specialized agent for security analysis",
            prompt=PromptConfig(
                system="You are a security analyst. Identify security vulnerabilities, injection risks, authentication issues, and data exposure risks. Provide remediation recommendations.",
                include_context=True,
            ),
            tools=ToolConfig(
                allow=["read", "glob", "grep", "ls"],
                deny=["write", "edit", "bash"],
                require_approval=[],
                auto_approve=["read", "glob", "grep", "ls"],
            ),
            run=RunConfig(
                max_rounds=5,
                terminate_mode=SubagentTerminateMode.AUTO,
            ),
            tags=["security", "analysis"],
            enabled=True,
        ))
        
        # Project reviewer - project-level review capabilities
        self._register(SubagentConfig(
            name="project-reviewer",
            description="Specialized agent for project-level review and validation",
            prompt=PromptConfig(
                system="You are a project reviewer. Review entire projects for consistency, architecture alignment, documentation completeness, and goal achievement. Assess whether the project meets its stated objectives and identify gaps.",
                include_context=True,
            ),
            tools=ToolConfig(
                allow=["read", "glob", "grep", "ls", "lsp"],
                deny=["write", "edit", "bash"],
                require_approval=[],
                auto_approve=["read", "glob", "grep", "ls"],
            ),
            run=RunConfig(
                max_rounds=10,
                terminate_mode=SubagentTerminateMode.AUTO,
            ),
            tags=["review", "project", "validation"],
            enabled=True,
        ))
        
        # Plan validator - confirm accuracy of plans and documents
        self._register(SubagentConfig(
            name="plan-validator",
            description="Specialized agent for validating plans, documents, and goals",
            prompt=PromptConfig(
                system="You are a plan validator. Review plans, specifications, and documentation for accuracy, completeness, feasibility, and consistency. Identify missing requirements, unrealistic timelines, and potential risks.",
                include_context=True,
            ),
            tools=ToolConfig(
                allow=["read", "glob", "grep", "ls"],
                deny=["write", "edit", "bash"],
                require_approval=[],
                auto_approve=["read", "glob", "grep", "ls"],
            ),
            run=RunConfig(
                max_rounds=5,
                terminate_mode=SubagentTerminateMode.AUTO,
            ),
            tags=["validation", "planning", "review"],
            enabled=True,
        ))
        
        # Task orchestrator - coordinate tasks across multiple agents
        self._register(SubagentConfig(
            name="task-orchestrator",
            description="Specialized agent for coordinating complex multi-step tasks",
            prompt=PromptConfig(
                system="You are a task orchestrator. Break down complex tasks into subtasks, delegate to appropriate agents, track progress, and aggregate results. Ensure efficient use of specialized agents.",
                include_context=True,
            ),
            tools=ToolConfig(
                allow=["read", "glob", "grep", "ls"],
                deny=["write", "edit", "bash"],
                require_approval=[],
                auto_approve=["read", "glob", "grep", "ls"],
            ),
            run=RunConfig(
                max_rounds=15,
                terminate_mode=SubagentTerminateMode.AUTO,
            ),
            tags=["orchestration", "coordination", "workflow"],
            enabled=True,
        ))
    
    def _register(self, config: SubagentConfig) -> None:
        """Register a built-in agent configuration."""
        self._agents[config.name] = config
    
    def get_builtin(self, name: str) -> Optional[SubagentConfig]:
        """Get a built-in agent by name.
        
        Args:
            name: Agent name
            
        Returns:
            Agent configuration or None if not found
        """
        return self._agents.get(name)
    
    def list_builtin(self) -> List[SubagentConfig]:
        """List all built-in agents.
        
        Returns:
            List of built-in agent configurations
        """
        return list(self._agents.values())
    
    def is_builtin(self, name: str) -> bool:
        """Check if a name is a built-in agent.
        
        Args:
            name: Agent name
            
        Returns:
            True if built-in, False otherwise
        """
        return name in self._agents
