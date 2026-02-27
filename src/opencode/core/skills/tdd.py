"""
Test-Driven Development skill.

Refactored from superpowers/skills/test-driven-development/SKILL.md

Core principle: If you didn't watch the test fail, you don't know if it tests the right thing.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

from .base import Skill, SkillContext, SkillResult, SkillRegistry, SkillPriority


class TDDPhase(Enum):
    """The three phases of TDD."""
    RED = "red"      # Write failing test
    GREEN = "green"  # Write minimal code to pass
    REFACTOR = "refactor"  # Clean up while staying green


@dataclass
class TDDState:
    """State tracking for TDD cycle."""
    current_phase: TDDPhase = TDDPhase.RED
    test_file: Optional[Path] = None
    implementation_file: Optional[Path] = None
    cycle_count: int = 0
    last_test_result: Optional[bool] = None


@SkillRegistry.register
class TDDSkill(Skill):
    """
    Test-Driven Development skill.
    
    Enforces the red-green-refactor cycle:
    1. RED: Write a failing test first
    2. GREEN: Write minimal code to make it pass
    3. REFACTOR: Clean up while keeping tests green
    
    Iron Law: NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
    """
    
    name = "tdd"
    description = "Test-Driven Development - write tests first, watch them fail, then implement"
    priority = SkillPriority.HIGH
    tags = ["testing", "development", "quality"]
    
    def __init__(self, context: Optional[SkillContext] = None):
        super().__init__(context)
        self._state = TDDState()
    
    def validate(self, test_name: str, test_file: str, **kwargs) -> tuple[bool, list[str]]:
        """Validate TDD parameters."""
        errors = []
        
        if not test_name:
            errors.append("test_name is required")
        
        if not test_file:
            errors.append("test_file is required")
        
        test_path = Path(test_file)
        if not test_path.suffix.startswith(".py"):
            errors.append("test_file must be a Python file")
        
        if "test_" not in test_path.name:
            errors.append("test_file should start with 'test_' prefix")
        
        return len(errors) == 0, errors
    
    async def execute(
        self,
        test_name: str,
        test_file: str,
        implementation_file: Optional[str] = None,
        test_code: Optional[str] = None,
        **kwargs,
    ) -> SkillResult:
        """
        Execute TDD cycle.
        
        Args:
            test_name: Name of the test function/class
            test_file: Path to the test file
            implementation_file: Path to the implementation file (optional)
            test_code: The test code to write (optional, will generate if not provided)
            
        Returns:
            SkillResult with TDD cycle status
        """
        self._state.test_file = Path(test_file)
        if implementation_file:
            self._state.implementation_file = Path(implementation_file)
        
        # Phase 1: RED - Write failing test
        red_result = await self._execute_red_phase(test_name, test_code)
        if not red_result.success:
            return red_result
        
        # Phase 2: GREEN - Write minimal implementation
        green_result = await self._execute_green_phase(test_name)
        if not green_result.success:
            return green_result
        
        # Phase 3: REFACTOR - Clean up (optional)
        if kwargs.get("refactor", True):
            refactor_result = await self._execute_refactor_phase()
            return refactor_result
        
        return SkillResult(
            success=True,
            message=f"TDD cycle completed for {test_name}",
            data={
                "test_file": str(self._state.test_file),
                "implementation_file": str(self._state.implementation_file),
                "cycles": self._state.cycle_count,
            },
        )
    
    async def _execute_red_phase(self, test_name: str, test_code: Optional[str]) -> SkillResult:
        """
        RED phase: Write a failing test.
        
        The test must fail for the right reason - not because of syntax errors
        or missing imports, but because the functionality doesn't exist yet.
        """
        self._state.current_phase = TDDPhase.RED
        
        # Generate test code if not provided
        if not test_code:
            test_code = self._generate_test_template(test_name)
        
        # Write test file
        test_path = self._state.test_file
        if self._context:
            test_path = self._context.working_directory / test_path
        
        # Ensure directory exists
        test_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if test already exists
        if test_path.exists():
            existing = test_path.read_text()
            if test_name in existing:
                return SkillResult(
                    success=False,
                    message=f"Test {test_name} already exists",
                    errors=["Test already exists - choose a different name or delete first"],
                )
        
        # Append test to file or create new file
        if test_path.exists():
            test_path.write_text(existing + "\n\n" + test_code)
        else:
            test_path.write_text(test_code)
        
        # Verify test fails (run pytest)
        test_fails = await self._verify_test_fails(test_path, test_name)
        
        if not test_fails:
            return SkillResult(
                success=False,
                message="Test did not fail - it may already pass or have syntax errors",
                warnings=["Test should fail for the right reason (missing functionality)"],
            )
        
        return SkillResult(
            success=True,
            message=f"RED phase complete: test {test_name} fails as expected",
            data={"phase": "red", "test_file": str(test_path)},
        )
    
    async def _execute_green_phase(self, test_name: str) -> SkillResult:
        """
        GREEN phase: Write minimal code to make test pass.
        
        The implementation should be the simplest thing that works.
        No gold-plating, no future-proofing.
        """
        self._state.current_phase = TDDPhase.GREEN
        
        # Implementation file should be created/modified
        if not self._state.implementation_file:
            # Derive from test file
            impl_name = self._state.test_file.name.replace("test_", "").replace(".py", "")
            self._state.implementation_file = self._state.test_file.parent / f"{impl_name}.py"
        
        impl_path = self._state.implementation_file
        if self._context:
            impl_path = self._context.working_directory / impl_path
        
        # Create minimal implementation stub
        if not impl_path.exists():
            impl_path.parent.mkdir(parents=True, exist_ok=True)
            impl_path.write_text('"""Implementation module."""\n\n# TODO: Implement to pass tests\n')
        
        return SkillResult(
            success=True,
            message="GREEN phase: implement minimal code to pass test",
            data={
                "phase": "green",
                "implementation_file": str(impl_path),
                "instruction": "Write the minimal code to make the test pass",
            },
        )
    
    async def _execute_refactor_phase(self) -> SkillResult:
        """
        REFACTOR phase: Clean up code while keeping tests green.
        
        After tests pass, improve code quality without changing behavior.
        """
        self._state.current_phase = TDDPhase.REFACTOR
        self._state.cycle_count += 1
        
        return SkillResult(
            success=True,
            message="REFACTOR phase: clean up code while keeping tests green",
            data={
                "phase": "refactor",
                "cycle_count": self._state.cycle_count,
            },
        )
    
    async def _verify_test_fails(self, test_path: Path, test_name: str) -> bool:
        """Verify that the test fails for the right reason."""
        import subprocess
        
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", str(test_path), "-v", "--tb=no"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            # Test should fail (return code != 0)
            # But not because of collection errors
            if "collected" in result.stdout:
                return result.returncode != 0
            return False
        except Exception:
            return False
    
    def _generate_test_template(self, test_name: str) -> str:
        """Generate a basic test template."""
        return f'''
def {test_name}():
    """Test implementation."""
    # Arrange
    # TODO: Set up test data
    
    # Act
    # TODO: Call the function being tested
    
    # Assert
    # TODO: Verify the result
    assert False, "Test not yet implemented"
'''
