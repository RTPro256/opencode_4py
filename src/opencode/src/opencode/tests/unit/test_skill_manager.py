"""
Tests for Skill Manager module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import tempfile
import asyncio

from opencode.skills.manager import SkillManager
from opencode.skills.models import (
    Skill,
    SkillConfig,
    SkillResult,
    SkillExecutionContext,
    SkillStatus,
    SkillType,
)
from opencode.skills.discovery import SkillDiscovery


class TestSkillManager:
    """Tests for SkillManager class."""

    def test_init_default(self):
        """Test default initialization."""
        with patch.object(SkillManager, 'discover_skills') as mock_discover:
            manager = SkillManager(auto_discover=False)
            assert manager._skills == {}
            assert manager._execution_hooks == []
            mock_discover.assert_not_called()

    def test_init_auto_discover(self):
        """Test initialization with auto_discover."""
        with patch.object(SkillManager, 'discover_skills') as mock_discover:
            mock_discover.return_value = {}
            manager = SkillManager(auto_discover=True)
            mock_discover.assert_called_once()

    def test_init_with_dirs(self):
        """Test initialization with custom directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SkillManager(
                skill_dirs=[Path(tmpdir)],
                auto_discover=False,
            )
            assert manager._discovery is not None

    def test_discover_skills(self):
        """Test discover_skills method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_file = Path(tmpdir) / "test.yaml"
            skill_file.write_text("name: test-skill")
            
            manager = SkillManager(skill_dirs=[Path(tmpdir)], auto_discover=False)
            skills = manager.discover_skills()
            
            assert "test-skill" in skills

    def test_discover_skills_reload(self):
        """Test discover_skills with reload=True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_file = Path(tmpdir) / "test.yaml"
            skill_file.write_text("name: reload-skill")
            
            manager = SkillManager(skill_dirs=[Path(tmpdir)], auto_discover=False)
            manager.discover_skills()
            
            # Add new skill
            (Path(tmpdir) / "new.yaml").write_text("name: new-skill")
            
            # Reload
            skills = manager.discover_skills(reload=True)
            assert "new-skill" in skills

    def test_add_skill(self):
        """Test add_skill method."""
        manager = SkillManager(auto_discover=False)
        
        config = SkillConfig(name="added-skill", trigger="/added")
        skill = Skill(config=config)
        
        manager.add_skill(skill)
        
        assert "added-skill" in manager._skills
        assert manager._skills["added-skill"].config.trigger == "/added"

    def test_remove_skill(self):
        """Test remove_skill method."""
        manager = SkillManager(auto_discover=False)
        
        config = SkillConfig(name="to-remove", trigger="/remove")
        skill = Skill(config=config)
        
        manager.add_skill(skill)
        assert "to-remove" in manager._skills
        
        result = manager.remove_skill("to-remove")
        
        assert result is True
        assert "to-remove" not in manager._skills

    def test_remove_skill_not_found(self):
        """Test remove_skill with non-existent skill."""
        manager = SkillManager(auto_discover=False)
        
        result = manager.remove_skill("non-existent")
        assert result is False

    def test_get_skill(self):
        """Test get_skill method."""
        manager = SkillManager(auto_discover=False)
        
        config = SkillConfig(name="get-test", trigger="/get")
        skill = Skill(config=config)
        manager.add_skill(skill)
        
        result = manager.get_skill("get-test")
        assert result is not None
        assert result.config.name == "get-test"

    def test_get_skill_not_found(self):
        """Test get_skill with non-existent skill."""
        manager = SkillManager(auto_discover=False)
        
        result = manager.get_skill("non-existent")
        assert result is None

    def test_list_skills(self):
        """Test list_skills method."""
        manager = SkillManager(auto_discover=False)
        
        manager.add_skill(Skill(config=SkillConfig(name="skill1")))
        manager.add_skill(Skill(config=SkillConfig(name="skill2")))
        
        names = manager.list_skills()
        
        assert set(names) == {"skill1", "skill2"}

    def test_get_all_skills(self):
        """Test get_all_skills method."""
        manager = SkillManager(auto_discover=False)
        
        manager.add_skill(Skill(config=SkillConfig(name="skill1")))
        manager.add_skill(Skill(config=SkillConfig(name="skill2")))
        
        skills = manager.get_all_skills()
        
        assert "skill1" in skills
        assert "skill2" in skills
        assert isinstance(skills["skill1"], Skill)

    def test_is_skill_trigger_true(self):
        """Test is_skill_trigger with valid trigger."""
        manager = SkillManager(auto_discover=False)
        
        config = SkillConfig(name="trigger-test", trigger="/trigger")
        manager.add_skill(Skill(config=config))
        
        assert manager.is_skill_trigger("/trigger arg1 arg2") is True

    def test_is_skill_trigger_false_no_slash(self):
        """Test is_skill_trigger without slash prefix."""
        manager = SkillManager(auto_discover=False)
        
        assert manager.is_skill_trigger("not a trigger") is False

    def test_is_skill_trigger_false_unknown(self):
        """Test is_skill_trigger with unknown trigger."""
        manager = SkillManager(auto_discover=False)
        
        config = SkillConfig(name="test", trigger="/known")
        manager.add_skill(Skill(config=config))
        
        assert manager.is_skill_trigger("/unknown") is False

    def test_parse_trigger_valid(self):
        """Test parse_trigger with valid trigger."""
        manager = SkillManager(auto_discover=False)
        
        config = SkillConfig(name="parse-test", trigger="/parse")
        manager.add_skill(Skill(config=config))
        
        result = manager.parse_trigger("/parse arg1 arg2")
        
        assert result is not None
        name, args = result
        assert name == "parse-test"
        assert args == "arg1 arg2"

    def test_parse_trigger_no_args(self):
        """Test parse_trigger without arguments."""
        manager = SkillManager(auto_discover=False)
        
        config = SkillConfig(name="no-args", trigger="/noargs")
        manager.add_skill(Skill(config=config))
        
        result = manager.parse_trigger("/noargs")
        
        assert result is not None
        name, args = result
        assert name == "no-args"
        assert args == ""

    def test_parse_trigger_no_slash(self):
        """Test parse_trigger without slash prefix."""
        manager = SkillManager(auto_discover=False)
        
        result = manager.parse_trigger("not a trigger")
        assert result is None

    def test_parse_trigger_unknown(self):
        """Test parse_trigger with unknown trigger."""
        manager = SkillManager(auto_discover=False)
        
        result = manager.parse_trigger("/unknown")
        assert result is None


class TestSkillManagerExecute:
    """Tests for SkillManager execution methods."""

    @pytest.mark.asyncio
    async def test_execute_skill_not_found(self):
        """Test execute_skill with non-existent skill."""
        manager = SkillManager(auto_discover=False)
        
        result = await manager.execute_skill("non-existent")
        
        assert result.success is False
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_skill_disabled(self):
        """Test execute_skill with disabled skill."""
        manager = SkillManager(auto_discover=False)
        
        config = SkillConfig(name="disabled-skill")
        skill = Skill(config=config, status=SkillStatus.DISABLED)
        manager.add_skill(skill)
        
        result = await manager.execute_skill("disabled-skill")
        
        assert result.success is False
        assert "disabled" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_prompt_skill(self):
        """Test executing a prompt-type skill."""
        manager = SkillManager(auto_discover=False)
        
        config = SkillConfig(
            name="prompt-skill",
            skill_type=SkillType.PROMPT,
            template="Hello {{args}}!",
        )
        manager.add_skill(Skill(config=config))
        
        result = await manager.execute_skill("prompt-skill", "World")
        
        assert result.success is True
        assert "Hello World!" in result.output

    @pytest.mark.asyncio
    async def test_execute_function_skill(self):
        """Test executing a function-type skill."""
        manager = SkillManager(auto_discover=False)
        
        async def my_executor(context):
            return SkillResult(success=True, output="Function executed")
        
        config = SkillConfig(
            name="func-skill",
            skill_type=SkillType.FUNCTION,
        )
        skill = Skill(config=config, _executor=my_executor)
        manager.add_skill(skill)
        
        result = await manager.execute_skill("func-skill", "args")
        
        assert result.success is True
        assert result.output == "Function executed"

    @pytest.mark.asyncio
    async def test_execute_function_skill_string_result(self):
        """Test function skill returning string."""
        manager = SkillManager(auto_discover=False)
        
        async def string_executor(context):
            return "String result"
        
        config = SkillConfig(
            name="string-skill",
            skill_type=SkillType.FUNCTION,
        )
        skill = Skill(config=config, _executor=string_executor)
        manager.add_skill(skill)
        
        result = await manager.execute_skill("string-skill")
        
        assert result.success is True
        assert result.output == "String result"

    @pytest.mark.asyncio
    async def test_execute_function_skill_dict_result(self):
        """Test function skill returning dict."""
        manager = SkillManager(auto_discover=False)
        
        async def dict_executor(context):
            return {"key": "value"}
        
        config = SkillConfig(
            name="dict-skill",
            skill_type=SkillType.FUNCTION,
        )
        skill = Skill(config=config, _executor=dict_executor)
        manager.add_skill(skill)
        
        result = await manager.execute_skill("dict-skill")
        
        assert result.success is True
        assert result.data == {"key": "value"}

    @pytest.mark.asyncio
    async def test_execute_function_skill_no_executor(self):
        """Test function skill without executor."""
        manager = SkillManager(auto_discover=False)
        
        config = SkillConfig(
            name="no-executor",
            skill_type=SkillType.FUNCTION,
        )
        skill = Skill(config=config)  # No _executor
        manager.add_skill(skill)
        
        result = await manager.execute_skill("no-executor")
        
        assert result.success is False
        assert "no executor" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_workflow_skill_no_id(self):
        """Test workflow skill without workflow_id."""
        manager = SkillManager(auto_discover=False)
        
        config = SkillConfig(
            name="no-workflow-id",
            skill_type=SkillType.WORKFLOW,
        )
        manager.add_skill(Skill(config=config))
        
        result = await manager.execute_skill("no-workflow-id")
        
        assert result.success is False
        assert "no workflow_id" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_chain_skill(self):
        """Test executing a chain skill."""
        manager = SkillManager(auto_discover=False)
        
        # Add individual skills
        manager.add_skill(Skill(config=SkillConfig(
            name="step1",
            skill_type=SkillType.PROMPT,
            template="Step1: {{args}}",
        )))
        manager.add_skill(Skill(config=SkillConfig(
            name="step2",
            skill_type=SkillType.PROMPT,
            template="Step2: {{args}}",
        )))
        
        # Add chain skill
        config = SkillConfig(
            name="chain-skill",
            skill_type=SkillType.CHAIN,
            chain=["step1", "step2"],
        )
        manager.add_skill(Skill(config=config))
        
        result = await manager.execute_skill("chain-skill", "test")
        
        assert result.success is True
        assert "Step1" in result.output
        assert "Step2" in result.output

    @pytest.mark.asyncio
    async def test_execute_chain_skill_empty(self):
        """Test chain skill with empty chain."""
        manager = SkillManager(auto_discover=False)
        
        config = SkillConfig(
            name="empty-chain",
            skill_type=SkillType.CHAIN,
            chain=[],
        )
        manager.add_skill(Skill(config=config))
        
        result = await manager.execute_skill("empty-chain")
        
        assert result.success is False
        assert "no chain" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_chain_skill_fails(self):
        """Test chain skill when a step fails."""
        manager = SkillManager(auto_discover=False)
        
        # Add a skill that will fail
        manager.add_skill(Skill(
            config=SkillConfig(name="failing-step"),
            status=SkillStatus.DISABLED,
        ))
        
        # Add chain skill
        config = SkillConfig(
            name="failing-chain",
            skill_type=SkillType.CHAIN,
            chain=["failing-step"],
        )
        manager.add_skill(Skill(config=config))
        
        result = await manager.execute_skill("failing-chain")
        
        assert result.success is False
        assert "chain failed" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_skill_updates_stats(self):
        """Test that execution updates skill stats."""
        manager = SkillManager(auto_discover=False)
        
        config = SkillConfig(
            name="stats-skill",
            skill_type=SkillType.PROMPT,
            template="test",
        )
        skill = Skill(config=config)
        manager.add_skill(skill)
        
        assert skill.use_count == 0
        assert skill.last_used_at is None
        
        await manager.execute_skill("stats-skill")
        
        assert skill.use_count == 1
        assert skill.last_used_at is not None

    @pytest.mark.asyncio
    async def test_execute_skill_with_context(self):
        """Test execute_skill with custom context."""
        manager = SkillManager(auto_discover=False)
        
        config = SkillConfig(
            name="context-skill",
            skill_type=SkillType.PROMPT,
            template="Hello {{name}}!",
        )
        manager.add_skill(Skill(config=config))
        
        context = SkillExecutionContext(
            skill_name="context-skill",
            arguments="args",
            variables={"name": "World"},
        )
        
        result = await manager.execute_skill("context-skill", context=context)
        
        assert result.success is True

    @pytest.mark.asyncio
    async def test_parse_and_execute(self):
        """Test parse_and_execute method."""
        manager = SkillManager(auto_discover=False)
        
        config = SkillConfig(
            name="parse-exec",
            trigger="/parseexec",
            skill_type=SkillType.PROMPT,
            template="Executed: {{args}}",
        )
        manager.add_skill(Skill(config=config))
        
        result = await manager.parse_and_execute("/parseexec test args")
        
        assert result is not None
        assert result.success is True
        assert "test args" in result.output

    @pytest.mark.asyncio
    async def test_parse_and_execute_no_trigger(self):
        """Test parse_and_execute with non-trigger message."""
        manager = SkillManager(auto_discover=False)
        
        result = await manager.parse_and_execute("not a trigger")
        
        assert result is None


class TestSkillManagerParseArguments:
    """Tests for argument parsing."""

    def test_parse_arguments_no_params(self):
        """Test parsing with no parameter definitions."""
        manager = SkillManager(auto_discover=False)
        
        config = SkillConfig(name="no-params")
        skill = Skill(config=config)
        
        result = manager._parse_arguments(skill, "arg1 arg2")
        
        assert result == {"args": "arg1 arg2"}

    def test_parse_arguments_positional(self):
        """Test parsing positional arguments."""
        manager = SkillManager(auto_discover=False)
        
        config = SkillConfig(
            name="positional",
            parameters={
                "first": {},
                "second": {},
            },
        )
        skill = Skill(config=config)
        
        result = manager._parse_arguments(skill, "value1 value2")
        
        assert result["first"] == "value1"
        assert result["second"] == "value2"

    def test_parse_arguments_flag(self):
        """Test parsing flag arguments."""
        manager = SkillManager(auto_discover=False)
        
        config = SkillConfig(
            name="flag-test",
            parameters={
                "verbose": {"type": "flag"},
            },
        )
        skill = Skill(config=config)
        
        result = manager._parse_arguments(skill, "--verbose")
        
        assert result["verbose"] is True

    def test_parse_arguments_flag_short(self):
        """Test parsing short flag arguments."""
        manager = SkillManager(auto_discover=False)
        
        config = SkillConfig(
            name="short-flag",
            parameters={
                "verbose": {"type": "flag"},
            },
        )
        skill = Skill(config=config)
        
        result = manager._parse_arguments(skill, "-v")
        
        assert result["verbose"] is True

    def test_parse_arguments_flag_not_present(self):
        """Test flag not present in arguments."""
        manager = SkillManager(auto_discover=False)
        
        config = SkillConfig(
            name="no-flag",
            parameters={
                "verbose": {"type": "flag"},
            },
        )
        skill = Skill(config=config)
        
        result = manager._parse_arguments(skill, "other args")
        
        assert result["verbose"] is False

    def test_parse_arguments_stores_raw(self):
        """Test that raw arguments are stored when parameters are defined."""
        manager = SkillManager(auto_discover=False)
        
        config = SkillConfig(
            name="raw-test",
            parameters={"first": {}},  # Need at least one param to get _raw
        )
        skill = Skill(config=config)
        
        result = manager._parse_arguments(skill, "arg1 arg2 arg3")
        
        assert result["_raw"] == "arg1 arg2 arg3"
        assert result["_args"] == ["arg1", "arg2", "arg3"]


class TestSkillManagerRenderTemplate:
    """Tests for template rendering."""

    def test_render_template_args(self):
        """Test rendering {{args}} placeholder."""
        manager = SkillManager(auto_discover=False)
        
        context = SkillExecutionContext(
            skill_name="test",
            arguments="my arguments",
            parsed_args={},
        )
        
        result = manager._render_template("Hello {{args}}!", context)
        
        assert result == "Hello my arguments!"

    def test_render_template_arg_index(self):
        """Test rendering {{arg0}}, {{arg1}} placeholders."""
        manager = SkillManager(auto_discover=False)
        
        context = SkillExecutionContext(
            skill_name="test",
            arguments="first second third",
            parsed_args={"_args": ["first", "second", "third"]},
        )
        
        result = manager._render_template(
            "First: {{arg0}}, Second: {{arg1}}",
            context,
        )
        
        assert result == "First: first, Second: second"

    def test_render_template_named_params(self):
        """Test rendering named parameter placeholders."""
        manager = SkillManager(auto_discover=False)
        
        context = SkillExecutionContext(
            skill_name="test",
            arguments="",
            parsed_args={"name": "World", "value": "test"},
        )
        
        result = manager._render_template(
            "Hello {{name}}, value: {{value}}",
            context,
        )
        
        assert result == "Hello World, value: test"

    def test_render_template_variables(self):
        """Test rendering context variables."""
        manager = SkillManager(auto_discover=False)
        
        context = SkillExecutionContext(
            skill_name="test",
            arguments="",
            parsed_args={},
            variables={"user": "Alice", "project": "MyProject"},
        )
        
        result = manager._render_template(
            "User: {{user}}, Project: {{project}}",
            context,
        )
        
        assert result == "User: Alice, Project: MyProject"


class TestSkillManagerHooks:
    """Tests for execution hooks."""

    @pytest.mark.asyncio
    async def test_add_execution_hook(self):
        """Test adding an execution hook."""
        manager = SkillManager(auto_discover=False)
        
        hook_called = []
        
        async def my_hook(skill, context, result):
            hook_called.append((skill.name, result.success))
        
        manager.add_execution_hook(my_hook)
        
        config = SkillConfig(
            name="hook-test",
            skill_type=SkillType.PROMPT,
            template="test",
        )
        manager.add_skill(Skill(config=config))
        
        await manager.execute_skill("hook-test")
        
        assert len(hook_called) == 1
        assert hook_called[0] == ("hook-test", True)

    @pytest.mark.asyncio
    async def test_hook_error_handling(self):
        """Test that hook errors don't break execution."""
        manager = SkillManager(auto_discover=False)
        
        async def failing_hook(skill, context, result):
            raise ValueError("Hook error")
        
        manager.add_execution_hook(failing_hook)
        
        config = SkillConfig(
            name="failing-hook",
            skill_type=SkillType.PROMPT,
            template="test",
        )
        manager.add_skill(Skill(config=config))
        
        result = await manager.execute_skill("failing-hook")
        
        # Should still succeed despite hook error
        assert result.success is True


class TestSkillManagerUnknownType:
    """Tests for unknown skill types."""

    @pytest.mark.asyncio
    async def test_execute_unknown_type(self):
        """Test executing a skill with unknown type."""
        manager = SkillManager(auto_discover=False)
        
        config = SkillConfig(
            name="unknown-type",
            skill_type="unknown",  # type: ignore
        )
        manager.add_skill(Skill(config=config))
        
        result = await manager.execute_skill("unknown-type")
        
        assert result.success is False
        assert "unknown skill type" in result.error.lower()