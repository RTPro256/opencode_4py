"""
Base workflow classes and registry.

Refactored from get-shit-done workflow patterns.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional, TypeVar
import asyncio
from pathlib import Path


class WorkflowStatus(Enum):
    """Status of a workflow execution."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(Enum):
    """Status of a workflow step."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """A single step in a workflow."""
    id: str
    name: str
    description: str
    action: Callable
    dependencies: list[str] = field(default_factory=list)
    status: StepStatus = StepStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    async def execute(self, context: dict[str, Any]) -> "WorkflowStep":
        """Execute this step."""
        self.status = StepStatus.RUNNING
        try:
            if asyncio.iscoroutinefunction(self.action):
                self.result = await self.action(context)
            else:
                self.result = self.action(context)
            self.status = StepStatus.COMPLETED
        except Exception as e:
            self.status = StepStatus.FAILED
            self.error = str(e)
        return self


@dataclass
class WorkflowResult:
    """Result of a workflow execution."""
    success: bool
    status: WorkflowStatus
    message: str
    steps_completed: int = 0
    steps_total: int = 0
    data: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    
    @property
    def progress(self) -> float:
        """Calculate progress percentage."""
        if self.steps_total == 0:
            return 0.0
        return (self.steps_completed / self.steps_total) * 100


@dataclass
class WorkflowContext:
    """Context passed through workflow execution."""
    working_directory: Path
    project_root: Optional[Path] = None
    variables: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, Any] = field(default_factory=dict)
    parent_context: Optional["WorkflowContext"] = None
    
    def get_variable(self, key: str, default: Any = None) -> Any:
        """Get a variable value."""
        if key in self.variables:
            return self.variables[key]
        if self.parent_context:
            return self.parent_context.get_variable(key, default)
        return default
    
    def set_variable(self, key: str, value: Any) -> None:
        """Set a variable value."""
        self.variables[key] = value
    
    def add_artifact(self, name: str, artifact: Any) -> None:
        """Add an artifact to the context."""
        self.artifacts[name] = artifact


T = TypeVar("T")


class Workflow(ABC):
    """
    Abstract base class for workflows.
    
    Workflows are multi-step processes that coordinate skills and tools.
    Inspired by get-shit-done's executor and verifier agents.
    
    Attributes:
        name: Unique identifier for the workflow
        description: Human-readable description
        steps: List of workflow steps
    """
    
    name: str = "base_workflow"
    description: str = "Base workflow class"
    
    def __init__(self, context: Optional[WorkflowContext] = None):
        """Initialize the workflow with optional context."""
        self._context = context
        self._steps: list[WorkflowStep] = []
        self._status = WorkflowStatus.PENDING
        self._current_step: Optional[str] = None
    
    @abstractmethod
    def define_steps(self) -> list[WorkflowStep]:
        """
        Define the steps for this workflow.
        
        Must be implemented by subclasses.
        
        Returns:
            List of WorkflowStep objects
        """
        pass
    
    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate workflow before execution.
        
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        # Check for circular dependencies
        step_ids = {s.id for s in self._steps}
        for step in self._steps:
            for dep in step.dependencies:
                if dep not in step_ids:
                    errors.append(f"Step {step.id} has unknown dependency: {dep}")
        
        # Check for circular dependencies using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(step_id: str) -> bool:
            visited.add(step_id)
            rec_stack.add(step_id)
            
            step = next((s for s in self._steps if s.id == step_id), None)
            if step:
                for dep in step.dependencies:
                    if dep not in visited:
                        if has_cycle(dep):
                            return True
                    elif dep in rec_stack:
                        return True
            
            rec_stack.remove(step_id)
            return False
        
        for step in self._steps:
            if step.id not in visited:
                if has_cycle(step.id):
                    errors.append("Circular dependency detected in workflow steps")
                    break
        
        return len(errors) == 0, errors
    
    async def run(self, **kwargs) -> WorkflowResult:
        """
        Execute the workflow.
        
        Returns:
            WorkflowResult with execution outcome
        """
        # Initialize steps
        self._steps = self.define_steps()
        
        # Validate
        is_valid, errors = self.validate()
        if not is_valid:
            return WorkflowResult(
                success=False,
                status=WorkflowStatus.FAILED,
                message="Workflow validation failed",
                errors=errors,
            )
        
        self._status = WorkflowStatus.RUNNING
        context_data = kwargs.copy()
        
        # Execute steps in dependency order
        completed: set[str] = set()
        failed: set[str] = set()
        steps_completed = 0
        
        while len(completed) + len(failed) < len(self._steps):
            # Find steps ready to execute
            ready = []
            for step in self._steps:
                if step.id in completed or step.id in failed:
                    continue
                if all(d in completed for d in step.dependencies):
                    ready.append(step)
            
            if not ready:
                # No steps ready - something failed
                break
            
            # Execute ready steps
            for step in ready:
                self._current_step = step.id
                await step.execute(context_data)
                
                if step.status == StepStatus.COMPLETED:
                    completed.add(step.id)
                    steps_completed += 1
                    if step.result:
                        context_data[step.id] = step.result
                else:
                    failed.add(step.id)
        
        # Determine final status
        if len(failed) > 0:
            self._status = WorkflowStatus.FAILED
            success = False
            message = f"Workflow failed at step(s): {', '.join(failed)}"
        else:
            self._status = WorkflowStatus.COMPLETED
            success = True
            message = "Workflow completed successfully"
        
        return WorkflowResult(
            success=success,
            status=self._status,
            message=message,
            steps_completed=steps_completed,
            steps_total=len(self._steps),
            data=context_data,
            errors=[s.error for s in self._steps if s.error],
        )
    
    def get_status(self) -> WorkflowStatus:
        """Get current workflow status."""
        return self._status
    
    def get_progress(self) -> dict[str, Any]:
        """Get execution progress."""
        completed = sum(1 for s in self._steps if s.status == StepStatus.COMPLETED)
        failed = sum(1 for s in self._steps if s.status == StepStatus.FAILED)
        running = sum(1 for s in self._steps if s.status == StepStatus.RUNNING)
        
        return {
            "status": self._status.value,
            "current_step": self._current_step,
            "completed": completed,
            "failed": failed,
            "running": running,
            "total": len(self._steps),
        }


class WorkflowRegistry:
    """
    Registry for managing available workflows.
    """
    
    _instance: Optional["WorkflowRegistry"] = None
    _workflows: dict[str, type[Workflow]] = {}
    
    def __new__(cls) -> "WorkflowRegistry":
        """Singleton pattern for global registry."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def register(cls, workflow_class: type[Workflow]) -> type[Workflow]:
        """Register a workflow class."""
        cls._workflows[workflow_class.name] = workflow_class
        return workflow_class
    
    @classmethod
    def get(cls, name: str) -> Optional[type[Workflow]]:
        """Get a workflow class by name."""
        return cls._workflows.get(name)
    
    @classmethod
    def list_workflows(cls) -> list[dict[str, str]]:
        """List all registered workflows."""
        return [
            {"name": w.name, "description": w.description}
            for w in cls._workflows.values()
        ]
    
    @classmethod
    def create(cls, name: str, context: Optional[WorkflowContext] = None) -> Optional[Workflow]:
        """Create an instance of a workflow by name."""
        workflow_class = cls.get(name)
        if workflow_class:
            return workflow_class(context)
        return None
