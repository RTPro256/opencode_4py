"""
Tests for Skill Discovery module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import os

from opencode.skills.discovery import SkillDiscovery, skill
from opencode.skills.models import Skill, SkillConfig, SkillType, SkillStatus


class TestSkillDiscovery:
    """Tests for SkillDiscovery class."""

    def test_init_default(self):
        """Test default initialization."""
        discovery = SkillDiscovery()
        assert discovery._skill_dirs == []
        assert discovery._auto_reload is False
        assert discovery._skills == {}
        assert discovery._loaded is False

    def test_init_with_dirs(self):
        """Test initialization with custom directories."""
        dirs = [Path("/tmp/skills"), Path("/home/user/skills")]
        discovery = SkillDiscovery(skill_dirs=dirs, auto_reload=True)
        assert discovery._skill_dirs == dirs
        assert discovery._auto_reload is True

    def test_add_directory(self):
        """Test adding a directory."""
        discovery = SkillDiscovery()
        dir_path = Path("/tmp/skills")
        discovery.add_directory(dir_path)
        assert dir_path in discovery._skill_dirs

    def test_add_directory_no_duplicate(self):
        """Test that duplicate directories are not added."""
        discovery = SkillDiscovery()
        dir_path = Path("/tmp/skills")
        discovery.add_directory(dir_path)
        discovery.add_directory(dir_path)
        assert discovery._skill_dirs.count(dir_path) == 1

    def test_discover_all_empty(self):
        """Test discover_all with no skills."""
        with tempfile.TemporaryDirectory() as tmpdir:
            discovery = SkillDiscovery(skill_dirs=[Path(tmpdir)])
            skills = discovery.discover_all()
            assert skills == {}
            assert discovery._loaded is True

    def test_discover_all_yaml_skill(self):
        """Test discovering a YAML skill file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a skill YAML file
            skill_file = Path(tmpdir) / "test_skill.yaml"
            skill_file.write_text("""
name: test-skill
description: A test skill
type: prompt
trigger: /test
template: "This is a test template"
parameters:
  arg1:
    type: string
    description: First argument
""")
            
            discovery = SkillDiscovery(skill_dirs=[Path(tmpdir)])
            skills = discovery.discover_all()
            
            assert "test-skill" in skills
            skill = skills["test-skill"]
            assert skill.config.name == "test-skill"
            assert skill.config.description == "A test skill"
            assert skill.config.skill_type == SkillType.PROMPT
            assert skill.config.trigger == "/test"
            assert skill.config.template == "This is a test template"
            assert "arg1" in skill.config.parameters

    def test_discover_all_yml_extension(self):
        """Test discovering a .yml skill file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_file = Path(tmpdir) / "test.yml"
            skill_file.write_text("""
name: yml-skill
description: YML skill
trigger: /yml
""")
            
            discovery = SkillDiscovery(skill_dirs=[Path(tmpdir)])
            skills = discovery.discover_all()
            
            assert "yml-skill" in skills

    def test_discover_all_yaml_invalid(self):
        """Test handling invalid YAML skill file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_file = Path(tmpdir) / "invalid.yaml"
            skill_file.write_text("invalid: yaml: content: [")
            
            discovery = SkillDiscovery(skill_dirs=[Path(tmpdir)])
            skills = discovery.discover_all()
            
            assert skills == {}

    def test_discover_all_yaml_missing_name(self):
        """Test handling YAML skill file without name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_file = Path(tmpdir) / "no_name.yaml"
            skill_file.write_text("description: Missing name field")
            
            discovery = SkillDiscovery(skill_dirs=[Path(tmpdir)])
            skills = discovery.discover_all()
            
            assert skills == {}

    def test_discover_all_markdown_skill(self):
        """Test discovering a Markdown skill file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_file = Path(tmpdir) / "test.md"
            skill_file.write_text("""---
name: md-skill
description: A markdown skill
trigger: /md
---
This is the template content.
It can span multiple lines.
""")
            
            discovery = SkillDiscovery(skill_dirs=[Path(tmpdir)])
            skills = discovery.discover_all()
            
            assert "md-skill" in skills
            skill = skills["md-skill"]
            assert skill.config.name == "md-skill"
            assert skill.config.description == "A markdown skill"
            assert "template content" in skill.config.template

    def test_discover_all_markdown_no_frontmatter(self):
        """Test handling Markdown file without frontmatter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_file = Path(tmpdir) / "no_frontmatter.md"
            skill_file.write_text("No frontmatter here")
            
            discovery = SkillDiscovery(skill_dirs=[Path(tmpdir)])
            skills = discovery.discover_all()
            
            assert skills == {}

    def test_discover_all_markdown_incomplete_frontmatter(self):
        """Test handling Markdown file with incomplete frontmatter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_file = Path(tmpdir) / "incomplete.md"
            skill_file.write_text("---\nname: incomplete\nNo closing frontmatter")
            
            discovery = SkillDiscovery(skill_dirs=[Path(tmpdir)])
            skills = discovery.discover_all()
            
            assert skills == {}

    def test_discover_all_markdown_missing_name(self):
        """Test handling Markdown file without name in frontmatter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_file = Path(tmpdir) / "no_name.md"
            skill_file.write_text("---\ndescription: No name\n---\nContent")
            
            discovery = SkillDiscovery(skill_dirs=[Path(tmpdir)])
            skills = discovery.discover_all()
            
            assert skills == {}

    def test_discover_all_python_skill(self):
        """Test discovering a Python skill file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_file = Path(tmpdir) / "my_skills.py"
            skill_file.write_text("""
from opencode.skills.discovery import skill

@skill("py-skill", "A Python skill", "/py")
async def my_skill(context):
    return "Python skill executed"
""")
            
            discovery = SkillDiscovery(skill_dirs=[Path(tmpdir)])
            skills = discovery.discover_all()
            
            assert "py-skill" in skills
            skill = skills["py-skill"]
            assert skill.config.name == "py-skill"
            assert skill.config.skill_type == SkillType.FUNCTION
            assert skill._executor is not None

    def test_discover_all_python_invalid(self):
        """Test handling invalid Python skill file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_file = Path(tmpdir) / "invalid.py"
            skill_file.write_text("this is not valid python syntax {{{")
            
            discovery = SkillDiscovery(skill_dirs=[Path(tmpdir)])
            skills = discovery.discover_all()
            
            # Should not crash, just skip the file
            assert skills == {}

    def test_get_skill(self):
        """Test get_skill method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_file = Path(tmpdir) / "test.yaml"
            skill_file.write_text("name: my-skill\ndescription: Test")
            
            discovery = SkillDiscovery(skill_dirs=[Path(tmpdir)])
            
            # Before discovery
            assert discovery._loaded is False
            skill = discovery.get_skill("my-skill")
            assert skill is not None
            assert skill.config.name == "my-skill"
            assert discovery._loaded is True

    def test_get_skill_not_found(self):
        """Test get_skill with non-existent skill."""
        with tempfile.TemporaryDirectory() as tmpdir:
            discovery = SkillDiscovery(skill_dirs=[Path(tmpdir)])
            discovery.discover_all()
            
            skill = discovery.get_skill("non-existent")
            assert skill is None

    def test_get_skill_by_trigger(self):
        """Test get_skill_by_trigger method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_file = Path(tmpdir) / "test.yaml"
            skill_file.write_text("name: trigger-skill\ntrigger: /trigger")
            
            discovery = SkillDiscovery(skill_dirs=[Path(tmpdir)])
            
            skill = discovery.get_skill_by_trigger("/trigger")
            assert skill is not None
            assert skill.config.name == "trigger-skill"

    def test_get_skill_by_trigger_not_found(self):
        """Test get_skill_by_trigger with non-existent trigger."""
        with tempfile.TemporaryDirectory() as tmpdir:
            discovery = SkillDiscovery(skill_dirs=[Path(tmpdir)])
            discovery.discover_all()
            
            skill = discovery.get_skill_by_trigger("/nonexistent")
            assert skill is None

    def test_list_skills(self):
        """Test list_skills method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "skill1.yaml").write_text("name: skill1")
            (Path(tmpdir) / "skill2.yaml").write_text("name: skill2")
            
            discovery = SkillDiscovery(skill_dirs=[Path(tmpdir)])
            names = discovery.list_skills()
            
            assert set(names) == {"skill1", "skill2"}

    def test_get_all_skills(self):
        """Test get_all_skills method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "skill.yaml").write_text("name: test-skill")
            
            discovery = SkillDiscovery(skill_dirs=[Path(tmpdir)])
            skills = discovery.get_all_skills()
            
            assert "test-skill" in skills
            assert isinstance(skills["test-skill"], Skill)

    def test_reload(self):
        """Test reload method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_file = Path(tmpdir) / "test.yaml"
            skill_file.write_text("name: reload-skill")
            
            discovery = SkillDiscovery(skill_dirs=[Path(tmpdir)])
            skills1 = discovery.discover_all()
            assert "reload-skill" in skills1
            
            # Add a new skill
            (Path(tmpdir) / "new.yaml").write_text("name: new-skill")
            
            # Reload
            skills2 = discovery.reload()
            assert "reload-skill" in skills2
            assert "new-skill" in skills2

    def test_discover_multiple_directories(self):
        """Test discovering from multiple directories."""
        with tempfile.TemporaryDirectory() as tmpdir1:
            with tempfile.TemporaryDirectory() as tmpdir2:
                (Path(tmpdir1) / "skill1.yaml").write_text("name: dir1-skill")
                (Path(tmpdir2) / "skill2.yaml").write_text("name: dir2-skill")
                
                discovery = SkillDiscovery(skill_dirs=[Path(tmpdir1), Path(tmpdir2)])
                skills = discovery.discover_all()
                
                assert "dir1-skill" in skills
                assert "dir2-skill" in skills

    def test_discover_nonexistent_directory(self):
        """Test handling non-existent directory."""
        discovery = SkillDiscovery(skill_dirs=[Path("/nonexistent/path")])
        skills = discovery.discover_all()
        # Should not crash
        assert isinstance(skills, dict)


class TestSkillDecorator:
    """Tests for the @skill decorator."""

    def test_skill_decorator_basic(self):
        """Test basic skill decorator."""
        @skill("test-skill", "Test description", "/test")
        async def my_func(context):
            return "result"
        
        assert hasattr(my_func, "_skill_config")
        config = my_func._skill_config
        assert config.name == "test-skill"
        assert config.description == "Test description"
        assert config.trigger == "/test"
        assert config.skill_type == SkillType.FUNCTION
        assert config.function_name == "my_func"

    def test_skill_decorator_auto_trigger(self):
        """Test skill decorator with auto-generated trigger."""
        @skill("auto-trigger")
        async def auto_func(context):
            return "result"
        
        config = auto_func._skill_config
        assert config.trigger == "/auto-trigger"

    def test_skill_decorator_with_options(self):
        """Test skill decorator with additional options."""
        @skill(
            "options-skill",
            "Description",
            requires_confirmation=True,
            timeout_seconds=120.0,
        )
        async def options_func(context):
            return "result"
        
        config = options_func._skill_config
        assert config.requires_confirmation is True
        assert config.timeout_seconds == 120.0


class TestSkillConfig:
    """Tests for SkillConfig model."""

    def test_to_dict(self):
        """Test SkillConfig.to_dict()."""
        config = SkillConfig(
            name="test",
            description="Test skill",
            skill_type=SkillType.PROMPT,
            trigger="/test",
            template="Template",
            parameters={"arg1": "value1"},
        )
        
        result = config.to_dict()
        
        assert result["name"] == "test"
        assert result["description"] == "Test skill"
        assert result["skill_type"] == "prompt"
        assert result["trigger"] == "/test"
        assert result["template"] == "Template"
        assert result["parameters"] == {"arg1": "value1"}

    def test_from_dict(self):
        """Test SkillConfig.from_dict()."""
        data = {
            "name": "from-dict",
            "description": "From dict",
            "skill_type": "function",
            "trigger": "/fromdict",
            "template": "Template",
            "function_name": "my_func",
            "chain": ["skill1", "skill2"],
            "parameters": {"p1": "v1"},
            "requires_confirmation": True,
            "timeout_seconds": 30.0,
        }
        
        config = SkillConfig.from_dict(data)
        
        assert config.name == "from-dict"
        assert config.description == "From dict"
        assert config.skill_type == SkillType.FUNCTION
        assert config.trigger == "/fromdict"
        assert config.function_name == "my_func"
        assert config.chain == ["skill1", "skill2"]
        assert config.parameters == {"p1": "v1"}
        assert config.requires_confirmation is True
        assert config.timeout_seconds == 30.0


class TestSkill:
    """Tests for Skill model."""

    def test_name_property(self):
        """Test Skill.name property."""
        config = SkillConfig(name="prop-test")
        skill = Skill(config=config)
        assert skill.name == "prop-test"

    def test_trigger_property_explicit(self):
        """Test Skill.trigger property with explicit trigger."""
        config = SkillConfig(name="test", trigger="/explicit")
        skill = Skill(config=config)
        assert skill.trigger == "/explicit"

    def test_trigger_property_auto(self):
        """Test Skill.trigger property with auto-generated trigger."""
        config = SkillConfig(name="auto-trigger-test")
        skill = Skill(config=config)
        assert skill.trigger == "/auto-trigger-test"

    def test_description_property(self):
        """Test Skill.description property."""
        config = SkillConfig(name="test", description="My description")
        skill = Skill(config=config)
        assert skill.description == "My description"

    def test_to_dict(self):
        """Test Skill.to_dict()."""
        config = SkillConfig(name="test")
        skill = Skill(
            config=config,
            status=SkillStatus.ENABLED,
            use_count=5,
        )
        
        result = skill.to_dict()
        
        assert result["config"]["name"] == "test"
        assert result["status"] == "enabled"
        assert result["use_count"] == 5

    def test_from_dict(self):
        """Test Skill.from_dict()."""
        data = {
            "config": {
                "name": "from-dict",
                "description": "Test",
                "skill_type": "prompt",
            },
            "status": "disabled",
            "use_count": 10,
        }
        
        skill = Skill.from_dict(data)
        
        assert skill.config.name == "from-dict"
        assert skill.status == SkillStatus.DISABLED
        assert skill.use_count == 10


class TestSkillResult:
    """Tests for SkillResult model."""

    def test_default_values(self):
        """Test SkillResult default values."""
        from opencode.skills.models import SkillResult
        
        result = SkillResult()
        assert result.success is True
        assert result.output == ""
        assert result.data is None
        assert result.error is None
        assert result.metadata == {}
        assert result.duration_ms is None

    def test_to_dict(self):
        """Test SkillResult.to_dict()."""
        from opencode.skills.models import SkillResult
        
        result = SkillResult(
            success=True,
            output="Test output",
            data={"key": "value"},
            error=None,
            metadata={"meta": "data"},
            duration_ms=100.5,
        )
        
        d = result.to_dict()
        
        assert d["success"] is True
        assert d["output"] == "Test output"
        assert d["data"] == {"key": "value"}
        assert d["metadata"] == {"meta": "data"}
        assert d["duration_ms"] == 100.5


class TestSkillExecutionContext:
    """Tests for SkillExecutionContext model."""

    def test_default_values(self):
        """Test SkillExecutionContext default values."""
        from opencode.skills.models import SkillExecutionContext
        
        ctx = SkillExecutionContext(skill_name="test", arguments="arg1 arg2")
        
        assert ctx.skill_name == "test"
        assert ctx.arguments == "arg1 arg2"
        assert ctx.parsed_args == {}
        assert ctx.variables == {}
        assert ctx.session_id is None
        assert ctx.user_id is None

    def test_to_dict(self):
        """Test SkillExecutionContext.to_dict()."""
        from opencode.skills.models import SkillExecutionContext
        
        ctx = SkillExecutionContext(
            skill_name="test",
            arguments="args",
            parsed_args={"arg1": "val1"},
            variables={"var1": "value1"},
            session_id="session-123",
            user_id="user-456",
        )
        
        d = ctx.to_dict()
        
        assert d["skill_name"] == "test"
        assert d["arguments"] == "args"
        assert d["parsed_args"] == {"arg1": "val1"}
        assert d["variables"] == {"var1": "value1"}
        assert d["session_id"] == "session-123"
        assert d["user_id"] == "user-456"