"""
Plan tool for structured planning mode.

This tool allows the AI agent to create and manage structured plans
for complex tasks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from opencode.tool.base import PermissionLevel, Tool, ToolResult


@dataclass
class PlanStep:
    """A step in a plan."""
    
    id: str
    description: str
    status: str = "pending"  # pending, in_progress, completed, blocked
    dependencies: list[str] = field(default_factory=list)
    notes: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status,
            "dependencies": self.dependencies,
            "notes": self.notes,
        }


class PlanTool(Tool):
    """
    Tool for creating and managing structured plans.
    
    Enables the agent to:
    - Create detailed plans with steps
    - Track dependencies between steps
    - Update step status
    - Generate plan summaries
    """
    
    def __init__(self):
        self._plans: dict[str, list[PlanStep]] = {}
        self._current_plan: Optional[str] = None
    
    @property
    def name(self) -> str:
        return "plan"
    
    @property
    def description(self) -> str:
        return """Create and manage structured plans for complex tasks.

Use this tool to:
- Create a new plan with ordered steps
- Update the status of plan steps
- Track dependencies between steps
- View current plan progress

Plan steps can have statuses:
- pending: Not yet started
- in_progress: Currently being worked on
- completed: Finished successfully
- blocked: Cannot proceed (with reason in notes)

Example:
- Create plan: plan(action="create", steps=[{"description": "Step 1"}, {"description": "Step 2"}])
- Update step: plan(action="update", step_id="1", status="completed")
- View plan: plan(action="view")
"""
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["create", "update", "view", "delete"],
                    "description": "Action to perform on the plan",
                },
                "plan_id": {
                    "type": "string",
                    "description": "Plan ID (optional, uses current plan if not specified)",
                },
                "steps": {
                    "type": "array",
                    "description": "List of plan steps (for create action)",
                    "items": {
                        "type": "object",
                        "properties": {
                            "description": {"type": "string"},
                            "dependencies": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["description"],
                    },
                },
                "step_id": {
                    "type": "string",
                    "description": "Step ID to update (for update action)",
                },
                "status": {
                    "type": "string",
                    "enum": ["pending", "in_progress", "completed", "blocked"],
                    "description": "New status for the step",
                },
                "notes": {
                    "type": "string",
                    "description": "Notes for the step",
                },
            },
            "required": ["action"],
        }
    
    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.WRITE
    
    async def execute(self, **params: Any) -> ToolResult:
        """Execute the plan action."""
        action = params.get("action")
        plan_id = params.get("plan_id")
        
        if action == "create":
            return self._create_plan(params.get("steps", []), plan_id)
        elif action == "update":
            return self._update_step(
                params.get("step_id"),
                params.get("status"),
                params.get("notes"),
                plan_id,
            )
        elif action == "view":
            return self._view_plan(plan_id)
        elif action == "delete":
            return self._delete_plan(plan_id)
        else:
            return ToolResult.err(f"Unknown action: {action}")
    
    def _create_plan(self, steps: list[dict], plan_id: Optional[str]) -> ToolResult:
        """Create a new plan."""
        import time
        
        plan_id = plan_id or f"plan_{int(time.time())}"
        
        plan_steps = []
        for i, step_data in enumerate(steps, 1):
            step = PlanStep(
                id=str(i),
                description=step_data.get("description", ""),
                dependencies=step_data.get("dependencies", []),
            )
            plan_steps.append(step)
        
        self._plans[plan_id] = plan_steps
        self._current_plan = plan_id
        
        output = f"Created plan: {plan_id}\n\n"
        output += self._format_plan(plan_steps)
        
        return ToolResult.ok(output, metadata={"plan_id": plan_id, "steps": [s.to_dict() for s in plan_steps]})
    
    def _update_step(
        self,
        step_id: Optional[str],
        status: Optional[str],
        notes: Optional[str],
        plan_id: Optional[str],
    ) -> ToolResult:
        """Update a step in a plan."""
        plan_id = plan_id or self._current_plan
        
        if not plan_id or plan_id not in self._plans:
            return ToolResult.err("No plan found. Create a plan first.")
        
        if not step_id:
            return ToolResult.err("step_id is required for update action")
        
        plan = self._plans[plan_id]
        step = next((s for s in plan if s.id == step_id), None)
        
        if not step:
            return ToolResult.err(f"Step {step_id} not found in plan")
        
        if status:
            step.status = status
        if notes:
            step.notes = notes
        
        output = f"Updated step {step_id} in plan {plan_id}\n\n"
        output += self._format_plan(plan)
        
        return ToolResult.ok(output, metadata={"plan_id": plan_id, "step": step.to_dict()})
    
    def _view_plan(self, plan_id: Optional[str]) -> ToolResult:
        """View a plan."""
        plan_id = plan_id or self._current_plan
        
        if not plan_id or plan_id not in self._plans:
            return ToolResult.ok("No plan found. Create a plan first.")
        
        plan = self._plans[plan_id]
        output = f"Plan: {plan_id}\n\n"
        output += self._format_plan(plan)
        
        return ToolResult.ok(output, metadata={"plan_id": plan_id, "steps": [s.to_dict() for s in plan]})
    
    def _delete_plan(self, plan_id: Optional[str]) -> ToolResult:
        """Delete a plan."""
        plan_id = plan_id or self._current_plan
        
        if not plan_id or plan_id not in self._plans:
            return ToolResult.err("No plan found to delete.")
        
        del self._plans[plan_id]
        
        if self._current_plan == plan_id:
            self._current_plan = None
        
        return ToolResult.ok(f"Deleted plan: {plan_id}")
    
    def _format_plan(self, steps: list[PlanStep]) -> str:
        """Format plan for display."""
        lines = []
        
        status_icons = {
            "pending": "○",
            "in_progress": "◐",
            "completed": "●",
            "blocked": "✗",
        }
        
        for step in steps:
            icon = status_icons.get(step.status, "○")
            line = f"{icon} {step.id}. {step.description}"
            if step.status == "in_progress":
                line += " [IN PROGRESS]"
            elif step.status == "completed":
                line += " [DONE]"
            elif step.status == "blocked":
                line += f" [BLOCKED: {step.notes or 'no reason given'}]"
            lines.append(line)
        
        # Summary
        total = len(steps)
        completed = sum(1 for s in steps if s.status == "completed")
        lines.append("")
        lines.append(f"Progress: {completed}/{total} steps completed")
        
        return "\n".join(lines)
