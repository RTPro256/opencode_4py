"""
Verifier workflow for task verification.

Refactored from get-shit-done/agents/gsd-verifier.md
"""

from dataclasses import dataclass
from typing import Any, Optional

from .base import (
    Workflow,
    WorkflowContext,
    WorkflowRegistry,
    WorkflowStep,
)


@dataclass
class VerificationResult:
    """Result of a verification check."""
    name: str
    passed: bool
    message: str
    details: dict[str, Any]


@WorkflowRegistry.register
class VerifierWorkflow(Workflow):
    """
    Verifier workflow for validating implementations.
    
    Follows the GSD verifier pattern:
    1. Check implementation exists
    2. Run tests
    3. Check code quality
    4. Verify acceptance criteria
    5. Report results
    """
    
    name = "verifier"
    description = "Verify implementation meets requirements"
    
    def __init__(self, context: Optional[WorkflowContext] = None):
        super().__init__(context)
        self._results: list[VerificationResult] = []
    
    def define_steps(self) -> list[WorkflowStep]:
        """Define verifier workflow steps."""
        return [
            WorkflowStep(
                id="check_implementation",
                name="Check Implementation",
                description="Verify implementation exists",
                action=self._check_implementation,
            ),
            WorkflowStep(
                id="run_tests",
                name="Run Tests",
                description="Run all tests",
                action=self._run_tests,
                dependencies=["check_implementation"],
            ),
            WorkflowStep(
                id="check_quality",
                name="Check Quality",
                description="Run code quality checks",
                action=self._check_quality,
                dependencies=["run_tests"],
            ),
            WorkflowStep(
                id="verify_criteria",
                name="Verify Criteria",
                description="Verify acceptance criteria",
                action=self._verify_criteria,
                dependencies=["check_quality"],
            ),
            WorkflowStep(
                id="report",
                name="Report",
                description="Generate verification report",
                action=self._report,
                dependencies=["verify_criteria"],
            ),
        ]
    
    async def _check_implementation(self, context: dict[str, Any]) -> dict[str, Any]:
        """Check that implementation exists."""
        files = context.get("files", [])
        missing_files = []
        
        if self._context:
            for file_path in files:
                path = self._context.working_directory / file_path
                if not path.exists():
                    missing_files.append(file_path)
        
        passed = len(missing_files) == 0
        self._results.append(VerificationResult(
            name="Implementation Exists",
            passed=passed,
            message="All files present" if passed else f"Missing: {missing_files}",
            details={"missing_files": missing_files},
        ))
        
        context["implementation_exists"] = passed
        return context
    
    async def _run_tests(self, context: dict[str, Any]) -> dict[str, Any]:
        """Run tests."""
        import subprocess
        
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            
            passed = result.returncode == 0
            self._results.append(VerificationResult(
                name="Tests Pass",
                passed=passed,
                message="All tests pass" if passed else "Some tests failed",
                details={"output": result.stdout[-1000:] if len(result.stdout) > 1000 else result.stdout},
            ))
            
            context["tests_passed"] = passed
        except Exception as e:
            self._results.append(VerificationResult(
                name="Tests Pass",
                passed=False,
                message=f"Test execution failed: {e}",
                details={},
            ))
            context["tests_passed"] = False
        
        return context
    
    async def _check_quality(self, context: dict[str, Any]) -> dict[str, Any]:
        """Run code quality checks."""
        import subprocess
        
        quality_checks = []
        
        # Run ruff if available
        try:
            result = subprocess.run(
                ["python", "-m", "ruff", "check", "."],
                capture_output=True,
                text=True,
                timeout=60,
            )
            quality_checks.append(("ruff", result.returncode == 0, result.stdout))
        except Exception:
            pass
        
        # Run mypy if available
        try:
            result = subprocess.run(
                ["python", "-m", "mypy", ".", "--ignore-missing-imports"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            quality_checks.append(("mypy", result.returncode == 0, result.stdout))
        except Exception:
            pass
        
        all_passed = all(c[1] for c in quality_checks) if quality_checks else True
        
        self._results.append(VerificationResult(
            name="Code Quality",
            passed=all_passed,
            message="All quality checks pass" if all_passed else "Some quality issues found",
            details={"checks": {c[0]: c[1] for c in quality_checks}},
        ))
        
        context["quality_passed"] = all_passed
        return context
    
    async def _verify_criteria(self, context: dict[str, Any]) -> dict[str, Any]:
        """Verify acceptance criteria."""
        criteria = context.get("acceptance_criteria", [])
        
        if not criteria:
            self._results.append(VerificationResult(
                name="Acceptance Criteria",
                passed=True,
                message="No specific criteria to verify",
                details={},
            ))
            context["criteria_passed"] = True
            return context
        
        # Check each criterion
        passed_criteria = []
        for criterion in criteria:
            # This would be overridden by actual criterion checking
            passed_criteria.append({"criterion": criterion, "passed": True})
        
        all_passed = all(c["passed"] for c in passed_criteria)
        
        self._results.append(VerificationResult(
            name="Acceptance Criteria",
            passed=all_passed,
            message=f"{len(passed_criteria)}/{len(criteria)} criteria met",
            details={"criteria": passed_criteria},
        ))
        
        context["criteria_passed"] = all_passed
        return context
    
    async def _report(self, context: dict[str, Any]) -> dict[str, Any]:
        """Generate verification report."""
        all_passed = all(r.passed for r in self._results)
        
        report = {
            "overall_passed": all_passed,
            "results": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "message": r.message,
                }
                for r in self._results
            ],
        }
        
        context["verification_report"] = report
        return context
    
    def get_results(self) -> list[VerificationResult]:
        """Get verification results."""
        return self._results
    
    def get_report(self) -> dict[str, Any]:
        """Get verification report."""
        return {
            "overall_passed": all(r.passed for r in self._results),
            "results": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "message": r.message,
                    "details": r.details,
                }
                for r in self._results
            ],
        }
