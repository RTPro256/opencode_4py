"""
Executor workflow for task execution.

Refactored from get-shit-done/agents/gsd-executor.md
"""

from typing import Any, Optional

from .base import (
    Workflow,
    WorkflowContext,
    WorkflowRegistry,
    WorkflowStep,
    StepStatus,
)


@WorkflowRegistry.register
class ExecutorWorkflow(Workflow):
    """
    Executor workflow for implementing tasks.
    
    Follows the GSD executor pattern:
    1. Read task context
    2. Implement changes
    3. Run tests
    4. Fix failures
    5. Verify completion
    """
    
    name = "executor"
    description = "Execute implementation tasks with verification"
    
    def __init__(self, context: Optional[WorkflowContext] = None):
        super().__init__(context)
        self._task_id: Optional[str] = None
        self._task_description: Optional[str] = None
    
    def define_steps(self) -> list[WorkflowStep]:
        """Define executor workflow steps."""
        return [
            WorkflowStep(
                id="read_context",
                name="Read Context",
                description="Read task context and requirements",
                action=self._read_context,
            ),
            WorkflowStep(
                id="implement",
                name="Implement",
                description="Implement the required changes",
                action=self._implement,
                dependencies=["read_context"],
            ),
            WorkflowStep(
                id="run_tests",
                name="Run Tests",
                description="Run tests to verify implementation",
                action=self._run_tests,
                dependencies=["implement"],
            ),
            WorkflowStep(
                id="fix_failures",
                name="Fix Failures",
                description="Fix any test failures",
                action=self._fix_failures,
                dependencies=["run_tests"],
            ),
            WorkflowStep(
                id="verify",
                name="Verify",
                description="Verify task completion",
                action=self._verify,
                dependencies=["fix_failures"],
            ),
        ]
    
    async def _read_context(self, context: dict[str, Any]) -> dict[str, Any]:
        """Read task context."""
        task_file = context.get("task_file")
        
        if task_file and self._context:
            path = self._context.working_directory / task_file
            if path.exists():
                content = path.read_text()
                context["task_content"] = content
        
        return context
    
    async def _implement(self, context: dict[str, Any]) -> dict[str, Any]:
        """Implement changes."""
        # This would be overridden by actual implementation logic
        context["implementation_status"] = "pending"
        return context
    
    async def _run_tests(self, context: dict[str, Any]) -> dict[str, Any]:
        """Run tests."""
        import subprocess
        
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            context["test_output"] = result.stdout
            context["test_passed"] = result.returncode == 0
        except Exception as e:
            context["test_error"] = str(e)
            context["test_passed"] = False
        
        return context
    
    async def _fix_failures(self, context: dict[str, Any]) -> dict[str, Any]:
        """Fix test failures if any."""
        if context.get("test_passed", True):
            context["fixes_applied"] = 0
            return context
        
        # This would be overridden by actual fix logic
        context["fixes_applied"] = 0
        return context
    
    async def _verify(self, context: dict[str, Any]) -> dict[str, Any]:
        """Verify task completion."""
        context["verified"] = context.get("test_passed", False)
        return context
    
    async def run_with_task(
        self,
        task_id: str,
        task_description: str,
        task_file: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Run the executor workflow for a specific task.
        
        Args:
            task_id: Unique task identifier
            task_description: Description of the task
            task_file: Optional path to task file
            
        Returns:
            Workflow result data
        """
        self._task_id = task_id
        self._task_description = task_description
        
        result = await self.run(task_file=task_file)
        return result.data
