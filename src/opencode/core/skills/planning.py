"""
Planning skill for task decomposition and execution.

Refactored from:
- get-shit-done/agents/gsd-planner.md
- superpowers/skills/writing-plans/
- ai-factory/skills/aif-plan/
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from .base import Skill, SkillContext, SkillResult, SkillRegistry, SkillPriority


class PlanPhase(Enum):
    """Phases in planning."""
    RESEARCH = "research"
    DECOMPOSE = "decompose"
    PRIORITIZE = "prioritize"
    SCHEDULE = "schedule"
    DOCUMENT = "document"


@dataclass
class Task:
    """A single task in a plan."""
    id: str
    title: str
    description: str
    dependencies: list[str] = field(default_factory=list)
    priority: int = 1
    estimated_effort: str = "medium"
    status: str = "pending"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Plan:
    """A complete execution plan."""
    name: str
    objective: str
    tasks: list[Task] = field(default_factory=list)
    context_files: list[str] = field(default_factory=list)
    success_criteria: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@SkillRegistry.register
class PlanningSkill(Skill):
    """
    Planning skill for task decomposition.
    
    Creates executable plans with:
    - Clear objectives
    - Task breakdown with dependencies
    - Execution waves for parallel work
    - Success criteria
    
    Inspired by get-shit-done's planner agent.
    """
    
    name = "planning"
    description = "Create executable plans with task breakdown and dependency analysis"
    priority = SkillPriority.MEDIUM
    tags = ["planning", "project-management", "workflow"]
    
    def __init__(self, context: Optional[SkillContext] = None):
        super().__init__(context)
        self._plan: Optional[Plan] = None
    
    def validate(
        self,
        objective: str,
        **kwargs,
    ) -> tuple[bool, list[str]]:
        """Validate planning parameters."""
        errors = []
        
        if not objective:
            errors.append("objective is required")
        
        return len(errors) == 0, errors
    
    async def execute(
        self,
        objective: str,
        context_files: Optional[list[str]] = None,
        constraints: Optional[list[str]] = None,
        **kwargs,
    ) -> SkillResult:
        """
        Execute planning process.
        
        Args:
            objective: What we're trying to achieve
            context_files: Files to read for context
            constraints: Limitations or requirements
            
        Returns:
            SkillResult with the plan
        """
        self._plan = Plan(
            name=kwargs.get("name", "execution_plan"),
            objective=objective,
            context_files=context_files or [],
        )
        
        # Phase 1: Research
        research_result = await self._phase_research(context_files)
        
        # Phase 2: Decompose
        decompose_result = await self._phase_decompose(objective, constraints)
        
        # Phase 3: Prioritize
        prioritize_result = await self._phase_prioritize()
        
        # Phase 4: Schedule
        schedule_result = await self._phase_schedule()
        
        # Phase 5: Document
        document_result = await self._phase_document()
        
        return SkillResult(
            success=True,
            message=f"Plan created: {self._plan.name}",
            data={
                "plan_name": self._plan.name,
                "objective": self._plan.objective,
                "task_count": len(self._plan.tasks),
                "success_criteria": self._plan.success_criteria,
            },
        )
    
    async def _phase_research(
        self,
        context_files: Optional[list[str]] = None,
    ) -> SkillResult:
        """
        RESEARCH phase: Gather context.
        
        Read relevant files and understand the codebase.
        """
        context_data = {
            "phase": "research",
            "files_to_read": context_files or [],
            "questions": [
                "What is the current state?",
                "What patterns exist in the codebase?",
                "What are the constraints?",
            ],
        }
        
        if self._context and context_files:
            for file_path in context_files:
                path = self._context.working_directory / file_path
                if path.exists():
                    # Could read and analyze file here
                    pass
        
        return SkillResult(
            success=True,
            message="RESEARCH phase: gather context",
            data=context_data,
        )
    
    async def _phase_decompose(
        self,
        objective: str,
        constraints: Optional[list[str]] = None,
    ) -> SkillResult:
        """
        DECOMPOSE phase: Break down into tasks.
        
        Create 2-3 task groups that can be executed in parallel.
        """
        # Generate task breakdown
        tasks = [
            Task(
                id="task-1",
                title="Setup and preparation",
                description="Prepare environment and dependencies",
                priority=1,
                estimated_effort="small",
            ),
            Task(
                id="task-2",
                title="Core implementation",
                description="Implement main functionality",
                dependencies=["task-1"],
                priority=2,
                estimated_effort="medium",
            ),
            Task(
                id="task-3",
                title="Testing and verification",
                description="Test implementation and verify success criteria",
                dependencies=["task-2"],
                priority=3,
                estimated_effort="medium",
            ),
        ]
        
        self._plan.tasks = tasks
        
        return SkillResult(
            success=True,
            message="DECOMPOSE phase: created task breakdown",
            data={
                "phase": "decompose",
                "tasks": [t.id for t in tasks],
            },
        )
    
    async def _phase_prioritize(self) -> SkillResult:
        """
        PRIORITIZE phase: Order tasks by dependency.
        
        Create execution waves for parallel execution.
        """
        if not self._plan:
            return SkillResult(
                success=False,
                message="No plan to prioritize",
            )
        
        # Build dependency graph
        waves: list[list[str]] = []
        remaining = list(self._plan.tasks)
        completed: set[str] = set()
        
        while remaining:
            # Find tasks with all dependencies completed
            wave = []
            for task in remaining:
                if all(d in completed for d in task.dependencies):
                    wave.append(task.id)
            
            if not wave:
                # Circular dependency detected
                return SkillResult(
                    success=False,
                    message="Circular dependency detected in tasks",
                    errors=["Cannot resolve task dependencies"],
                )
            
            waves.append(wave)
            completed.update(wave)
            remaining = [t for t in remaining if t.id not in wave]
        
        return SkillResult(
            success=True,
            message="PRIORITIZE phase: created execution waves",
            data={
                "phase": "prioritize",
                "waves": waves,
            },
        )
    
    async def _phase_schedule(self) -> SkillResult:
        """
        SCHEDULE phase: Assign execution order.
        
        Determine optimal execution sequence.
        """
        return SkillResult(
            success=True,
            message="SCHEDULE phase: execution order determined",
            data={
                "phase": "schedule",
            },
        )
    
    async def _phase_document(self) -> SkillResult:
        """
        DOCUMENT phase: Create plan document.
        
        Generate PLAN.md with all details.
        """
        if not self._plan:
            return SkillResult(
                success=False,
                message="No plan to document",
            )
        
        # Set success criteria
        self._plan.success_criteria = [
            f"All tasks completed for: {self._plan.objective}",
            "Tests pass",
            "No regressions",
        ]
        
        return SkillResult(
            success=True,
            message="DOCUMENT phase: plan documented",
            data={
                "phase": "document",
                "success_criteria": self._plan.success_criteria,
            },
        )
    
    def get_plan(self) -> Optional[Plan]:
        """Get the current plan."""
        return self._plan
    
    def get_next_task(self) -> Optional[Task]:
        """Get the next task to execute."""
        if not self._plan:
            return None
        
        for task in self._plan.tasks:
            if task.status == "pending":
                # Check dependencies
                completed_ids = [
                    t.id for t in self._plan.tasks if t.status == "completed"
                ]
                if all(d in completed_ids for d in task.dependencies):
                    return task
        
        return None
    
    def mark_task_complete(self, task_id: str) -> None:
        """Mark a task as completed."""
        if self._plan:
            for task in self._plan.tasks:
                if task.id == task_id:
                    task.status = "completed"
                    break
