"""
Skill tool for loading specialized instructions.

This tool allows the AI agent to load predefined skill instructions
for specialized tasks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from opencode.tool.base import PermissionLevel, Tool, ToolResult


@dataclass
class Skill:
    """A predefined skill with instructions."""
    
    id: str
    name: str
    description: str
    instructions: str
    tags: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "instructions": self.instructions,
            "tags": self.tags,
        }


# Built-in skills
BUILTIN_SKILLS = [
    Skill(
        id="code-review",
        name="Code Review",
        description="Perform a thorough code review with best practices",
        instructions="""You are performing a code review. Focus on:

1. **Code Quality**
   - Readability and maintainability
   - Naming conventions
   - Code organization and structure

2. **Best Practices**
   - Design patterns usage
   - SOLID principles
   - DRY (Don't Repeat Yourself)

3. **Potential Issues**
   - Bugs or logic errors
   - Security vulnerabilities
   - Performance concerns

4. **Testing**
   - Test coverage
   - Edge cases
   - Error handling

Provide constructive feedback with specific suggestions for improvement.""",
        tags=["review", "quality", "best-practices"],
    ),
    Skill(
        id="refactor",
        name="Refactoring",
        description="Refactor code for better maintainability",
        instructions="""You are refactoring code. Focus on:

1. **Identify Code Smells**
   - Long methods
   - Duplicate code
   - Complex conditionals
   - Large classes

2. **Apply Refactorings**
   - Extract method/function
   - Extract variable
   - Rename for clarity
   - Simplify conditionals

3. **Maintain Behavior**
   - Preserve existing functionality
   - Ensure tests still pass
   - Document changes

Always explain the refactoring and its benefits before making changes.""",
        tags=["refactor", "clean-code", "maintainability"],
    ),
    Skill(
        id="debug",
        name="Debugging",
        description="Systematically debug issues",
        instructions="""You are debugging an issue. Follow this process:

1. **Understand the Problem**
   - What is the expected behavior?
   - What is the actual behavior?
   - What error messages appear?

2. **Gather Information**
   - Check logs and stack traces
   - Review recent changes
   - Identify affected components

3. **Form Hypotheses**
   - List possible causes
   - Prioritize by likelihood

4. **Test Hypotheses**
   - Start with the most likely cause
   - Use binary search for complex issues
   - Verify fixes thoroughly

5. **Document the Fix**
   - Explain the root cause
   - Describe the solution
   - Add tests to prevent regression""",
        tags=["debug", "troubleshoot", "fix"],
    ),
    Skill(
        id="test-driven",
        name="Test-Driven Development",
        description="Write tests before implementation",
        instructions="""You are practicing TDD. Follow the red-green-refactor cycle:

1. **Red: Write a Failing Test**
   - Write a test for the next piece of functionality
   - The test should fail (feature not implemented)
   - Keep tests small and focused

2. **Green: Make It Pass**
   - Write the minimum code to make the test pass
   - Don't worry about perfection yet
   - Focus on correctness

3. **Refactor: Improve the Code**
   - Clean up the implementation
   - Remove duplication
   - Improve naming and structure
   - Ensure tests still pass

Repeat this cycle for each feature.""",
        tags=["testing", "tdd", "quality"],
    ),
    Skill(
        id="documentation",
        name="Documentation",
        description="Write clear documentation",
        instructions="""You are writing documentation. Focus on:

1. **Audience Awareness**
   - Who will read this?
   - What do they already know?
   - What do they need to learn?

2. **Structure**
   - Start with a clear summary
   - Use headings and sections
   - Include examples

3. **Clarity**
   - Use simple language
   - Avoid jargon when possible
   - Explain technical terms

4. **Completeness**
   - Cover all necessary topics
   - Include edge cases
   - Provide troubleshooting tips

5. **Accuracy**
   - Verify code examples work
   - Keep documentation updated
   - Link to relevant resources""",
        tags=["docs", "writing", "clarity"],
    ),
    Skill(
        id="api-design",
        name="API Design",
        description="Design clean and consistent APIs",
        instructions="""You are designing an API. Focus on:

1. **Consistency**
   - Use consistent naming conventions
   - Follow platform conventions
   - Maintain patterns across endpoints

2. **Simplicity**
   - Keep interfaces minimal
   - Use sensible defaults
   - Avoid unnecessary complexity

3. **Documentation**
   - Document all parameters
   - Provide examples
   - Explain error conditions

4. **Versioning**
   - Plan for backwards compatibility
   - Use semantic versioning
   - Document breaking changes

5. **Error Handling**
   - Use appropriate status codes
   - Provide helpful error messages
   - Include error codes for programmatic handling""",
        tags=["api", "design", "rest"],
    ),
]


class SkillTool(Tool):
    """
    Tool for loading specialized skill instructions.
    
    Provides access to predefined skills that help with specific
    types of tasks like code review, debugging, or refactoring.
    """
    
    def __init__(self):
        self._skills = {skill.id: skill for skill in BUILTIN_SKILLS}
    
    @property
    def name(self) -> str:
        return "skill"
    
    @property
    def description(self) -> str:
        skills_list = "\n".join(
            f"- {skill.id}: {skill.description}"
            for skill in BUILTIN_SKILLS
        )
        return f"""Load specialized instructions for specific tasks.

When you recognize that a task matches one of the available skills,
use this tool to load the full skill instructions.

Available skills:
{skills_list}

Example: skill(skill_id="code-review")
"""
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "skill_id": {
                    "type": "string",
                    "description": "ID of the skill to load",
                    "enum": [skill.id for skill in BUILTIN_SKILLS],
                },
            },
            "required": ["skill_id"],
        }
    
    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.READ
    
    async def execute(self, **params: Any) -> ToolResult:
        """Execute the skill loading."""
        skill_id = params.get("skill_id")
        
        if not skill_id:
            return ToolResult.err("skill_id is required")
        
        skill = self._skills.get(skill_id)
        
        if not skill:
            available = ", ".join(self._skills.keys())
            return ToolResult.err(f"Unknown skill: {skill_id}. Available: {available}")
        
        output = f"# {skill.name}\n\n{skill.instructions}"
        
        return ToolResult.ok(
            output=output,
            metadata={"skill": skill.to_dict()},
        )
    
    def register_skill(self, skill: Skill) -> None:
        """Register a custom skill."""
        self._skills[skill.id] = skill
    
    def list_skills(self) -> list[Skill]:
        """List all available skills."""
        return list(self._skills.values())
