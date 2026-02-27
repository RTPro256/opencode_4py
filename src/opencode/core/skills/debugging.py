"""
Systematic debugging skill.

Refactored from superpowers/skills/systematic-debugging/SKILL.md
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from .base import Skill, SkillContext, SkillResult, SkillRegistry, SkillPriority


class DebugPhase(Enum):
    """Phases in the debugging process."""
    REPRODUCE = "reproduce"
    ISOLATE = "isolate"
    HYPOTHESIZE = "hypothesize"
    TEST = "test"
    FIX = "fix"
    VERIFY = "verify"


@dataclass
class DebugState:
    """State tracking for debugging session."""
    current_phase: DebugPhase = DebugPhase.REPRODUCE
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    hypotheses: list[str] = field(default_factory=list)
    tested_hypotheses: list[dict[str, Any]] = field(default_factory=list)
    fix_applied: bool = False


@SkillRegistry.register
class DebuggingSkill(Skill):
    """
    Systematic debugging skill.
    
    Follows a structured approach:
    1. REPRODUCE: Get a reliable reproduction
    2. ISOLATE: Narrow down the problem location
    3. HYPOTHESIZE: Form theories about the cause
    4. TEST: Verify or disprove hypotheses
    5. FIX: Apply the fix
    6. VERIFY: Ensure fix works and doesn't break anything
    
    Key principle: Never fix what you can't reproduce.
    """
    
    name = "debugging"
    description = "Systematic debugging - reproduce, isolate, hypothesize, test, fix, verify"
    priority = SkillPriority.HIGH
    tags = ["debugging", "troubleshooting", "quality"]
    
    def __init__(self, context: Optional[SkillContext] = None):
        super().__init__(context)
        self._state = DebugState()
    
    def validate(
        self,
        error_description: str,
        **kwargs,
    ) -> tuple[bool, list[str]]:
        """Validate debugging parameters."""
        errors = []
        
        if not error_description:
            errors.append("error_description is required")
        
        return len(errors) == 0, errors
    
    async def execute(
        self,
        error_description: str,
        stack_trace: Optional[str] = None,
        reproduction_steps: Optional[list[str]] = None,
        **kwargs,
    ) -> SkillResult:
        """
        Execute systematic debugging.
        
        Args:
            error_description: Description of the error/bug
            stack_trace: Optional stack trace
            reproduction_steps: Steps to reproduce the issue
            
        Returns:
            SkillResult with debugging guidance
        """
        self._state.error_message = error_description
        self._state.stack_trace = stack_trace
        
        results = []
        
        # Phase 1: REPRODUCE
        if not reproduction_steps:
            reproduce_result = await self._phase_reproduce(error_description)
            results.append(reproduce_result)
            if not reproduce_result.success:
                return reproduce_result
        else:
            self._state.current_phase = DebugPhase.ISOLATE
        
        # Phase 2: ISOLATE
        isolate_result = await self._phase_isolate(stack_trace)
        results.append(isolate_result)
        
        # Phase 3: HYPOTHESIZE
        hypothesize_result = await self._phase_hypothesize(error_description)
        results.append(hypothesize_result)
        
        # Return guidance for remaining phases
        return SkillResult(
            success=True,
            message="Debugging analysis complete",
            data={
                "phase": self._state.current_phase.value,
                "hypotheses": self._state.hypotheses,
                "next_steps": [
                    "Test each hypothesis systematically",
                    "Apply fix when root cause is confirmed",
                    "Verify fix doesn't introduce regressions",
                ],
            },
        )
    
    async def _phase_reproduce(self, error_description: str) -> SkillResult:
        """
        REPRODUCE phase: Get a reliable reproduction.
        
        Without reproduction, debugging is guessing.
        """
        self._state.current_phase = DebugPhase.REPRODUCE
        
        return SkillResult(
            success=True,
            message="REPRODUCE phase: establish reliable reproduction steps",
            data={
                "phase": "reproduce",
                "questions": [
                    "What are the exact steps to trigger this error?",
                    "Is it consistent or intermittent?",
                    "What environment does it occur in?",
                    "When did it first appear?",
                ],
            },
        )
    
    async def _phase_isolate(self, stack_trace: Optional[str]) -> SkillResult:
        """
        ISOLATE phase: Narrow down the problem location.
        
        Use binary search approach to find the problematic code.
        """
        self._state.current_phase = DebugPhase.ISOLATE
        
        isolation_data = {
            "phase": "isolate",
            "techniques": [
                "Binary search: comment out half the code",
                "Logging: add print statements at key points",
                "Debugger: step through execution",
                "Diff: compare with last working version",
            ],
        }
        
        if stack_trace:
            # Parse stack trace for location hints
            lines = stack_trace.split("\n")
            file_lines = [l for l in lines if "File " in l]
            if file_lines:
                isolation_data["stack_locations"] = file_lines[:5]
        
        return SkillResult(
            success=True,
            message="ISOLATE phase: narrow down problem location",
            data=isolation_data,
        )
    
    async def _phase_hypothesize(self, error_description: str) -> SkillResult:
        """
        HYPOTHESIZE phase: Form theories about the cause.
        
        Generate multiple hypotheses, then test them systematically.
        """
        self._state.current_phase = DebugPhase.HYPOTHESIZE
        
        # Common bug categories to check
        common_causes = [
            "Null/undefined value",
            "Off-by-one error",
            "Race condition",
            "Type mismatch",
            "Missing initialization",
            "Incorrect condition",
            "Side effects",
            "Resource leak",
        ]
        
        self._state.hypotheses = common_causes
        
        return SkillResult(
            success=True,
            message="HYPOTHESIZE phase: generate possible causes",
            data={
                "phase": "hypothesize",
                "hypotheses": common_causes,
                "instruction": "Test hypotheses one at a time, starting with most likely",
            },
        )
    
    async def test_hypothesis(
        self,
        hypothesis: str,
        test_code: Optional[str] = None,
    ) -> SkillResult:
        """
        TEST phase: Verify or disprove a hypothesis.
        
        Args:
            hypothesis: The hypothesis to test
            test_code: Optional test code to verify
            
        Returns:
            SkillResult with test outcome
        """
        self._state.current_phase = DebugPhase.TEST
        
        test_result = {
            "hypothesis": hypothesis,
            "tested": True,
        }
        
        self._state.tested_hypotheses.append(test_result)
        
        return SkillResult(
            success=True,
            message=f"Testing hypothesis: {hypothesis}",
            data={
                "phase": "test",
                "hypothesis": hypothesis,
            },
        )
    
    async def apply_fix(
        self,
        fix_description: str,
        files_changed: list[str],
    ) -> SkillResult:
        """
        FIX phase: Apply the fix.
        
        Args:
            fix_description: Description of the fix
            files_changed: List of files modified
            
        Returns:
            SkillResult with fix details
        """
        self._state.current_phase = DebugPhase.FIX
        self._state.fix_applied = True
        
        return SkillResult(
            success=True,
            message=f"FIX phase: {fix_description}",
            data={
                "phase": "fix",
                "files_changed": files_changed,
            },
        )
    
    async def verify_fix(self) -> SkillResult:
        """
        VERIFY phase: Ensure fix works and doesn't break anything.
        
        Run tests and verify the original issue is resolved.
        """
        self._state.current_phase = DebugPhase.VERIFY
        
        return SkillResult(
            success=True,
            message="VERIFY phase: confirm fix works",
            data={
                "phase": "verify",
                "checklist": [
                    "Original issue is resolved",
                    "No new test failures",
                    "No regressions in related features",
                    "Edge cases handled",
                ],
            },
        )
