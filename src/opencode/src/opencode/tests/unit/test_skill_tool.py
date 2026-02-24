"""Tests for Skill Tool."""

import pytest

from opencode.tool.skill import SkillTool, Skill, BUILTIN_SKILLS
from opencode.tool.base import PermissionLevel


class TestSkill:
    """Tests for Skill dataclass."""

    def test_skill_creation(self):
        """Test creating a skill."""
        skill = Skill(
            id="test-skill",
            name="Test Skill",
            description="A test skill",
            instructions="Test instructions",
            tags=["test", "example"]
        )
        
        assert skill.id == "test-skill"
        assert skill.name == "Test Skill"
        assert skill.description == "A test skill"
        assert skill.instructions == "Test instructions"
        assert skill.tags == ["test", "example"]

    def test_skill_to_dict(self):
        """Test converting skill to dictionary."""
        skill = Skill(
            id="test",
            name="Test",
            description="Test description",
            instructions="Test instructions",
            tags=["tag1"]
        )
        
        result = skill.to_dict()
        
        assert result["id"] == "test"
        assert result["name"] == "Test"
        assert result["description"] == "Test description"
        assert result["instructions"] == "Test instructions"
        assert result["tags"] == ["tag1"]

    def test_skill_default_tags(self):
        """Test default tags is empty list."""
        skill = Skill(
            id="test",
            name="Test",
            description="Test",
            instructions="Test"
        )
        
        assert skill.tags == []


class TestBuiltinSkills:
    """Tests for built-in skills."""

    def test_builtin_skills_exist(self):
        """Test that built-in skills are defined."""
        assert len(BUILTIN_SKILLS) > 0

    def test_code_review_skill(self):
        """Test code-review skill exists."""
        skill_ids = [s.id for s in BUILTIN_SKILLS]
        assert "code-review" in skill_ids

    def test_refactor_skill(self):
        """Test refactor skill exists."""
        skill_ids = [s.id for s in BUILTIN_SKILLS]
        assert "refactor" in skill_ids

    def test_debug_skill(self):
        """Test debug skill exists."""
        skill_ids = [s.id for s in BUILTIN_SKILLS]
        assert "debug" in skill_ids

    def test_all_skills_have_required_fields(self):
        """Test all skills have required fields."""
        for skill in BUILTIN_SKILLS:
            assert skill.id
            assert skill.name
            assert skill.description
            assert skill.instructions


class TestSkillTool:
    """Tests for SkillTool."""

    def test_name(self):
        """Test tool name."""
        tool = SkillTool()
        
        assert tool.name == "skill"

    def test_description(self):
        """Test tool description."""
        tool = SkillTool()
        
        assert "skill" in tool.description.lower()

    def test_parameters(self):
        """Test tool parameters schema."""
        tool = SkillTool()
        
        params = tool.parameters
        
        assert params["type"] == "object"
        assert "skill_id" in params["properties"]
        assert "skill_id" in params["required"]

    def test_permission_level(self):
        """Test permission level is READ."""
        tool = SkillTool()
        
        assert tool.permission_level == PermissionLevel.READ

    @pytest.mark.asyncio
    async def test_execute_valid_skill(self):
        """Test executing with valid skill ID."""
        tool = SkillTool()
        
        result = await tool.execute(skill_id="code-review")
        
        assert result.success is True
        assert "Code Review" in result.output

    @pytest.mark.asyncio
    async def test_execute_invalid_skill(self):
        """Test executing with invalid skill ID."""
        tool = SkillTool()
        
        result = await tool.execute(skill_id="nonexistent")
        
        assert result.success is False
        assert "Unknown skill" in result.error

    @pytest.mark.asyncio
    async def test_execute_missing_skill_id(self):
        """Test executing without skill_id."""
        tool = SkillTool()
        
        result = await tool.execute()
        
        assert result.success is False
        assert "required" in result.error.lower()

    @pytest.mark.asyncio
    async def test_metadata(self):
        """Test result metadata."""
        tool = SkillTool()
        
        result = await tool.execute(skill_id="debug")
        
        assert "skill" in result.metadata
        assert result.metadata["skill"]["id"] == "debug"

    def test_register_skill(self):
        """Test registering a custom skill."""
        tool = SkillTool()
        
        custom_skill = Skill(
            id="custom",
            name="Custom Skill",
            description="A custom skill",
            instructions="Custom instructions"
        )
        
        tool.register_skill(custom_skill)
        
        # Verify it was registered
        result = tool._skills.get("custom")
        assert result is not None
        assert result.name == "Custom Skill"

    def test_list_skills(self):
        """Test listing all skills."""
        tool = SkillTool()
        
        skills = tool.list_skills()
        
        assert len(skills) >= len(BUILTIN_SKILLS)
        assert all(isinstance(s, Skill) for s in skills)

    @pytest.mark.asyncio
    async def test_execute_refactor_skill(self):
        """Test executing refactor skill."""
        tool = SkillTool()
        
        result = await tool.execute(skill_id="refactor")
        
        assert result.success is True
        assert "Refactoring" in result.output

    @pytest.mark.asyncio
    async def test_execute_debug_skill(self):
        """Test executing debug skill."""
        tool = SkillTool()
        
        result = await tool.execute(skill_id="debug")
        
        assert result.success is True
        assert "Debugging" in result.output

    @pytest.mark.asyncio
    async def test_custom_skill_execution(self):
        """Test executing a custom registered skill."""
        tool = SkillTool()
        
        custom_skill = Skill(
            id="my-skill",
            name="My Custom Skill",
            description="Custom skill for testing",
            instructions="These are custom instructions."
        )
        
        tool.register_skill(custom_skill)
        
        result = await tool.execute(skill_id="my-skill")
        
        assert result.success is True
        assert "My Custom Skill" in result.output
        assert "custom instructions" in result.output
