"""
Agent and Agent Description

Defines the Agent class and description for multi-agent orchestration.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Status of an agent."""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


class AgentCapability(Enum):
    """Capabilities an agent can have."""
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    DEBUGGING = "debugging"
    REFACTORING = "refactoring"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    ARCHITECTURE = "architecture"
    PLANNING = "planning"
    RESEARCH = "research"
    FILE_OPERATIONS = "file_operations"
    SHELL_EXECUTION = "shell_execution"
    WEB_SEARCH = "web_search"
    API_INTEGRATION = "api_integration"
    # New capabilities for review and orchestration
    PROJECT_REVIEW = "project_review"
    PLAN_VALIDATION = "plan_validation"
    TASK_ORCHESTRATION = "task_orchestration"
    QUALITY_ASSURANCE = "quality_assurance"
    GOAL_VERIFICATION = "goal_verification"


@dataclass
class AgentDescription:
    """
    Description of an agent for routing purposes.
    
    This is used by the orchestration router to determine which agent
    should handle a given request based on natural language descriptions.
    
    Example:
        description = AgentDescription(
            agent_id="code_assistant",
            name="Code Assistant",
            description="Handles code generation, refactoring, and debugging tasks",
            capabilities=[AgentCapability.CODE_GENERATION, AgentCapability.DEBUGGING],
        )
    """
    agent_id: str
    name: str
    description: str
    capabilities: List[AgentCapability] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    modes: List[str] = field(default_factory=list)
    priority: int = 0
    max_concurrent_tasks: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "capabilities": [c.value for c in self.capabilities],
            "tools": self.tools,
            "modes": self.modes,
            "priority": self.priority,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentDescription":
        """Create from dictionary."""
        capabilities = [
            AgentCapability(c) for c in data.get("capabilities", [])
        ]
        return cls(
            agent_id=data["agent_id"],
            name=data["name"],
            description=data["description"],
            capabilities=capabilities,
            tools=data.get("tools", []),
            modes=data.get("modes", []),
            priority=data.get("priority", 0),
            max_concurrent_tasks=data.get("max_concurrent_tasks", 1),
            metadata=data.get("metadata", {}),
        )


@dataclass
class AgentTask:
    """A task assigned to an agent."""
    task_id: str
    prompt: str
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "pending"
    result: Optional[Any] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "prompt": self.prompt,
            "context": self.context,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            "result": self.result,
            "error": self.error,
        }


class Agent:
    """
    Base class for agents in the orchestration system.
    
    An agent is a specialized component that can handle specific types
    of tasks. Agents register their capabilities and descriptions,
    allowing the orchestration router to direct requests appropriately.
    
    Example:
        class CodeAgent(Agent):
            async def execute(self, task: AgentTask) -> Any:
                # Process the task
                result = await self._process_code(task.prompt)
                return result
        
        agent = CodeAgent(
            description=AgentDescription(
                agent_id="code_agent",
                name="Code Agent",
                description="Handles code generation and modification",
                capabilities=[AgentCapability.CODE_GENERATION],
            )
        )
    """
    
    def __init__(
        self,
        description: AgentDescription,
        handler: Optional[Callable] = None,
    ):
        """
        Initialize the agent.
        
        Args:
            description: Agent description for routing
            handler: Optional async handler function
        """
        self.description = description
        self._handler = handler
        self._status = AgentStatus.IDLE
        self._current_tasks: List[AgentTask] = []
        self._completed_tasks: List[AgentTask] = []
    
    @property
    def agent_id(self) -> str:
        """Get agent ID."""
        return self.description.agent_id
    
    @property
    def status(self) -> AgentStatus:
        """Get current status."""
        return self._status
    
    @property
    def is_available(self) -> bool:
        """Check if agent can accept new tasks."""
        return (
            self._status == AgentStatus.IDLE
            and len(self._current_tasks) < self.description.max_concurrent_tasks
        )
    
    async def execute(self, task: AgentTask) -> Any:
        """
        Execute a task.
        
        Override this method to implement custom execution logic.
        
        Args:
            task: Task to execute
            
        Returns:
            Task result
        """
        if self._handler:
            return await self._handler(task)
        
        raise NotImplementedError("Agent must implement execute() or provide a handler")
    
    async def start_task(self, task: AgentTask) -> None:
        """
        Start a task.
        
        Args:
            task: Task to start
        """
        if not self.is_available:
            raise RuntimeError(f"Agent {self.agent_id} is not available")
        
        self._current_tasks.append(task)
        task.status = "running"
        task.started_at = datetime.utcnow()
        
        if len(self._current_tasks) >= self.description.max_concurrent_tasks:
            self._status = AgentStatus.BUSY
        
        try:
            result = await self.execute(task)
            task.result = result
            task.status = "completed"
        except Exception as e:
            task.error = str(e)
            task.status = "failed"
            logger.error(f"Task {task.task_id} failed: {e}")
        finally:
            task.completed_at = datetime.utcnow()
            self._current_tasks.remove(task)
            self._completed_tasks.append(task)
            
            if not self._current_tasks:
                self._status = AgentStatus.IDLE
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics."""
        return {
            "agent_id": self.agent_id,
            "status": self._status.value,
            "current_tasks": len(self._current_tasks),
            "completed_tasks": len(self._completed_tasks),
            "is_available": self.is_available,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "description": self.description.to_dict(),
            "stats": self.get_stats(),
        }
