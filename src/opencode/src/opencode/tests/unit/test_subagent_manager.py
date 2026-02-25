"""
Tests for SubagentManager.

Unit tests for the subagent configuration manager.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
import tempfile
import os

from opencode.core.subagents.manager import SubagentManager
from opencode.core.subagents.types import (
    SubagentConfig,
    SubagentLevel,
    SubagentRuntimeConfig,
    ListSubagentsOptions,
    CreateSubagentOptions,
    PromptConfig,
    ModelConfig,
    ToolConfig,
    RunConfig,
    SubagentTerminateMode,
)
from opencode.core.subagents.errors import (
    SubagentNotFoundError,
    SubagentAlreadyExistsError,
    SubagentValidationError,
    SubagentFileError,
)


class TestSubagentManager:
    """Tests for SubagentManager class."""
    
    @pytest.fixture
    def temp_project_root(self, tmp_path):
        """Create a temporary project root directory."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        return project_dir
    
    @pytest.fixture
    def temp_user_home(self, tmp_path):
        """Create a temporary user home directory."""
        home_dir = tmp_path / "home"
        home_dir.mkdir()
        return home_dir
    
    @pytest.fixture
    def manager(self, temp_project_root, temp_user_home):
        """Create a manager instance with temp directories."""
        return SubagentManager(
            project_root=temp_project_root,
            user_home=temp_user_home
        )
    
    @pytest.fixture
    def sample_config(self):
        """Create a sample subagent configuration."""
        return SubagentConfig(
            name="test_agent",
            description="A test agent",
            prompt=PromptConfig(system="You are helpful."),
            model=ModelConfig(provider="openai", name="gpt-4"),
            tools=ToolConfig(allow=["bash"], deny=["file_delete"]),
            run=RunConfig(max_rounds=10, timeout=300),
            tags=["test"],
        )


class TestSubagentManagerInit(TestSubagentManager):
    """Tests for SubagentManager initialization."""
    
    def test_init_with_paths(self, temp_project_root, temp_user_home):
        """Test initialization with explicit paths."""
        manager = SubagentManager(
            project_root=temp_project_root,
            user_home=temp_user_home
        )
        assert manager.project_root == temp_project_root
        assert manager.user_home == temp_user_home
        assert manager.project_subagents_dir == temp_project_root / ".opencode" / "subagents"
        assert manager.user_subagents_dir == temp_user_home / ".opencode" / "subagents"
    
    def test_init_defaults_to_cwd(self):
        """Test initialization defaults to cwd and home."""
        manager = SubagentManager()
        assert manager.project_root == Path.cwd()
        assert manager.user_home == Path.home()
    
    def test_init_creates_validator(self, manager):
        """Test that validator is created."""
        assert manager.validator is not None
    
    def test_init_creates_builtin_registry(self, manager):
        """Test that builtin registry is created."""
        assert manager.builtin_registry is not None


class TestListSubagents(TestSubagentManager):
    """Tests for list_subagents method."""
    
    @pytest.mark.asyncio
    async def test_list_subagents_empty(self, manager):
        """Test listing when no subagents exist."""
        options = ListSubagentsOptions(include_builtin=False)
        result = await manager.list_subagents(options)
        assert result == []
    
    @pytest.mark.asyncio
    async def test_list_subagents_includes_builtin(self, manager):
        """Test listing includes builtin agents."""
        options = ListSubagentsOptions(include_builtin=True)
        result = await manager.list_subagents(options)
        # Should have at least some builtin agents
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_list_subagents_from_user_level(self, manager, temp_user_home, sample_config):
        """Test listing subagents from user level."""
        # Create user subagents directory
        user_subagents_dir = temp_user_home / ".opencode" / "subagents"
        user_subagents_dir.mkdir(parents=True, exist_ok=True)
        
        # Save a config file
        config_path = user_subagents_dir / "test_agent.md"
        content = f"""---
name: test_agent
description: A test agent
---
# test_agent

A test agent
"""
        config_path.write_text(content)
        
        options = ListSubagentsOptions(
            level=SubagentLevel.USER,
            include_builtin=False
        )
        result = await manager.list_subagents(options)
        assert len(result) >= 1
    
    @pytest.mark.asyncio
    async def test_list_subagents_from_project_level(self, manager, temp_project_root, sample_config):
        """Test listing subagents from project level."""
        # Create project subagents directory
        project_subagents_dir = temp_project_root / ".opencode" / "subagents"
        project_subagents_dir.mkdir(parents=True, exist_ok=True)
        
        # Save a config file
        config_path = project_subagents_dir / "test_agent.md"
        content = f"""---
name: test_agent
description: A test agent
---
# test_agent

A test agent
"""
        config_path.write_text(content)
        
        options = ListSubagentsOptions(
            level=SubagentLevel.PROJECT,
            include_builtin=False
        )
        result = await manager.list_subagents(options)
        assert len(result) >= 1
    
    @pytest.mark.asyncio
    async def test_list_subagents_filter_by_tags(self, manager, temp_project_root):
        """Test filtering subagents by tags."""
        # Create project subagents directory
        project_subagents_dir = temp_project_root / ".opencode" / "subagents"
        project_subagents_dir.mkdir(parents=True, exist_ok=True)
        
        # Save a config file with tags
        config_path = project_subagents_dir / "tagged_agent.md"
        content = """---
name: tagged_agent
description: A tagged agent
tags:
  - special
  - test
---
# tagged_agent

A tagged agent
"""
        config_path.write_text(content)
        
        options = ListSubagentsOptions(
            level=SubagentLevel.PROJECT,
            include_builtin=False,
            tags=["special"]
        )
        result = await manager.list_subagents(options)
        assert len(result) >= 1
    
    @pytest.mark.asyncio
    async def test_list_subagents_enabled_only(self, manager, temp_project_root):
        """Test filtering for enabled subagents only."""
        # Create project subagents directory
        project_subagents_dir = temp_project_root / ".opencode" / "subagents"
        project_subagents_dir.mkdir(parents=True, exist_ok=True)
        
        # Save an enabled config
        config_path = project_subagents_dir / "enabled_agent.md"
        content = """---
name: enabled_agent
description: An enabled agent
enabled: true
---
# enabled_agent

An enabled agent
"""
        config_path.write_text(content)
        
        options = ListSubagentsOptions(
            level=SubagentLevel.PROJECT,
            include_builtin=False,
            enabled_only=True
        )
        result = await manager.list_subagents(options)
        # All returned should be enabled
        for config in result:
            assert config.enabled is True


class TestGetSubagent(TestSubagentManager):
    """Tests for get_subagent method."""
    
    @pytest.mark.asyncio
    async def test_get_subagent_not_found(self, manager):
        """Test getting a non-existent subagent."""
        with pytest.raises(SubagentNotFoundError):
            await manager.get_subagent("nonexistent")
    
    @pytest.mark.asyncio
    async def test_get_subagent_builtin(self, manager):
        """Test getting a builtin subagent."""
        # This will depend on what builtin agents exist
        # If no builtin agents, this test will raise SubagentNotFoundError
        try:
            result = await manager.get_subagent("code")
            assert result.name == "code"
        except SubagentNotFoundError:
            pytest.skip("No builtin 'code' agent")
    
    @pytest.mark.asyncio
    async def test_get_subagent_from_project(self, manager, temp_project_root):
        """Test getting a subagent from project level."""
        # Create project subagents directory
        project_subagents_dir = temp_project_root / ".opencode" / "subagents"
        project_subagents_dir.mkdir(parents=True, exist_ok=True)
        
        # Save a config file
        config_path = project_subagents_dir / "project_agent.md"
        content = """---
name: project_agent
description: A project agent
---
# project_agent

A project agent
"""
        config_path.write_text(content)
        
        result = await manager.get_subagent("project_agent")
        assert result.name == "project_agent"
        assert result.description == "A project agent"
    
    @pytest.mark.asyncio
    async def test_get_subagent_from_user(self, manager, temp_user_home):
        """Test getting a subagent from user level."""
        # Create user subagents directory
        user_subagents_dir = temp_user_home / ".opencode" / "subagents"
        user_subagents_dir.mkdir(parents=True, exist_ok=True)
        
        # Save a config file
        config_path = user_subagents_dir / "user_agent.md"
        content = """---
name: user_agent
description: A user agent
---
# user_agent

A user agent
"""
        config_path.write_text(content)
        
        result = await manager.get_subagent("user_agent")
        assert result.name == "user_agent"
        assert result.description == "A user agent"
    
    @pytest.mark.asyncio
    async def test_get_subagent_project_overrides_user(self, manager, temp_project_root, temp_user_home):
        """Test that project level overrides user level."""
        # Create both directories
        user_subagents_dir = temp_user_home / ".opencode" / "subagents"
        user_subagents_dir.mkdir(parents=True, exist_ok=True)
        project_subagents_dir = temp_project_root / ".opencode" / "subagents"
        project_subagents_dir.mkdir(parents=True, exist_ok=True)
        
        # Save user level config
        user_config_path = user_subagents_dir / "override_agent.md"
        user_content = """---
name: override_agent
description: User level
---
# override_agent

User level
"""
        user_config_path.write_text(user_content)
        
        # Save project level config
        project_config_path = project_subagents_dir / "override_agent.md"
        project_content = """---
name: override_agent
description: Project level
---
# override_agent

Project level
"""
        project_config_path.write_text(project_content)
        
        result = await manager.get_subagent("override_agent")
        assert result.description == "Project level"


class TestCreateSubagent(TestSubagentManager):
    """Tests for create_subagent method."""
    
    @pytest.mark.asyncio
    async def test_create_subagent_success(self, manager, temp_project_root):
        """Test creating a subagent successfully."""
        options = CreateSubagentOptions(
            name="new_agent",
            description="A new agent",
            system_prompt="You are helpful.",
            level=SubagentLevel.PROJECT
        )
        
        result = await manager.create_subagent(options)
        assert result.name == "new_agent"
        assert result.description == "A new agent"
    
    @pytest.mark.asyncio
    async def test_create_subagent_already_exists(self, manager, temp_project_root):
        """Test creating a subagent that already exists."""
        # Create project subagents directory
        project_subagents_dir = temp_project_root / ".opencode" / "subagents"
        project_subagents_dir.mkdir(parents=True, exist_ok=True)
        
        # Save an existing config
        config_path = project_subagents_dir / "existing_agent.md"
        content = """---
name: existing_agent
description: Existing agent
---
# existing_agent

Existing agent
"""
        config_path.write_text(content)
        
        options = CreateSubagentOptions(
            name="existing_agent",
            description="A new agent",
            system_prompt="You are helpful.",
            level=SubagentLevel.PROJECT
        )
        
        with pytest.raises(SubagentAlreadyExistsError):
            await manager.create_subagent(options)
    
    @pytest.mark.asyncio
    async def test_create_subagent_overwrite(self, manager, temp_project_root):
        """Test creating a subagent with overwrite."""
        # Create project subagents directory
        project_subagents_dir = temp_project_root / ".opencode" / "subagents"
        project_subagents_dir.mkdir(parents=True, exist_ok=True)
        
        # Save an existing config
        config_path = project_subagents_dir / "overwrite_agent.md"
        content = """---
name: overwrite_agent
description: Original description
---
# overwrite_agent

Original description
"""
        config_path.write_text(content)
        
        options = CreateSubagentOptions(
            name="overwrite_agent",
            description="New description",
            system_prompt="You are helpful.",
            level=SubagentLevel.PROJECT,
            overwrite=True
        )
        
        result = await manager.create_subagent(options)
        assert result.description == "New description"
    
    @pytest.mark.asyncio
    async def test_create_subagent_with_model(self, manager, temp_project_root):
        """Test creating a subagent with model config."""
        options = CreateSubagentOptions(
            name="model_agent",
            description="Agent with model",
            system_prompt="You are helpful.",
            model="gpt-4",
            provider="openai",
            level=SubagentLevel.PROJECT
        )
        
        result = await manager.create_subagent(options)
        assert result.model is not None
        assert result.model.name == "gpt-4"
        assert result.model.provider == "openai"
    
    @pytest.mark.asyncio
    async def test_create_subagent_with_tools(self, manager, temp_project_root):
        """Test creating a subagent with tool config."""
        options = CreateSubagentOptions(
            name="tools_agent",
            description="Agent with tools",
            system_prompt="You are helpful.",
            allowed_tools=["bash", "file_read"],
            denied_tools=["file_delete"],
            level=SubagentLevel.PROJECT
        )
        
        result = await manager.create_subagent(options)
        assert result.tools is not None
        assert "bash" in result.tools.allow
        assert "file_delete" in result.tools.deny


class TestUpdateSubagent(TestSubagentManager):
    """Tests for update_subagent method."""
    
    @pytest.mark.asyncio
    async def test_update_subagent_not_found(self, manager):
        """Test updating a non-existent subagent."""
        with pytest.raises(SubagentNotFoundError):
            await manager.update_subagent(
                "nonexistent",
                {"description": "Updated"}
            )
    
    @pytest.mark.asyncio
    async def test_update_subagent_description(self, manager, temp_project_root):
        """Test updating subagent description."""
        # Create project subagents directory
        project_subagents_dir = temp_project_root / ".opencode" / "subagents"
        project_subagents_dir.mkdir(parents=True, exist_ok=True)
        
        # Save an existing config
        config_path = project_subagents_dir / "update_agent.md"
        content = """---
name: update_agent
description: Original description
---
# update_agent

Original description
"""
        config_path.write_text(content)
        
        result = await manager.update_subagent(
            "update_agent",
            {"description": "Updated description"}
        )
        assert result.description == "Updated description"
    
    @pytest.mark.asyncio
    async def test_update_subagent_tags(self, manager, temp_project_root):
        """Test updating subagent tags."""
        # Create project subagents directory
        project_subagents_dir = temp_project_root / ".opencode" / "subagents"
        project_subagents_dir.mkdir(parents=True, exist_ok=True)
        
        # Save an existing config
        config_path = project_subagents_dir / "update_tags_agent.md"
        content = """---
name: update_tags_agent
description: Agent to update tags
tags:
  - old
---
# update_tags_agent

Agent to update tags
"""
        config_path.write_text(content)
        
        result = await manager.update_subagent(
            "update_tags_agent",
            {"tags": ["new", "updated"]}
        )
        assert "new" in result.tags
        assert "updated" in result.tags


class TestDeleteSubagent(TestSubagentManager):
    """Tests for delete_subagent method."""
    
    @pytest.mark.asyncio
    async def test_delete_subagent_not_found(self, manager):
        """Test deleting a non-existent subagent."""
        with pytest.raises(SubagentNotFoundError):
            await manager.delete_subagent("nonexistent")
    
    @pytest.mark.asyncio
    async def test_delete_subagent_success(self, manager, temp_project_root):
        """Test deleting a subagent successfully."""
        # Create project subagents directory
        project_subagents_dir = temp_project_root / ".opencode" / "subagents"
        project_subagents_dir.mkdir(parents=True, exist_ok=True)
        
        # Save a config to delete
        config_path = project_subagents_dir / "delete_agent.md"
        content = """---
name: delete_agent
description: Agent to delete
---
# delete_agent

Agent to delete
"""
        config_path.write_text(content)
        
        # Verify it exists
        assert config_path.exists()
        
        # Delete it
        await manager.delete_subagent("delete_agent")
        
        # Verify it's gone
        assert not config_path.exists()


class TestGetRuntimeConfig(TestSubagentManager):
    """Tests for get_runtime_config method."""
    
    def test_get_runtime_config_minimal(self, manager):
        """Test getting runtime config with minimal config."""
        config = SubagentConfig(
            name="minimal_agent",
            description="Minimal agent"
        )
        
        result = manager.get_runtime_config(config)
        assert result.name == "minimal_agent"
        assert result.system_prompt == ""
        assert result.model_provider == "openai"  # default
        assert result.model_name == "gpt-4"  # default
    
    def test_get_runtime_config_full(self, manager):
        """Test getting runtime config with full config."""
        config = SubagentConfig(
            name="full_agent",
            description="Full agent",
            prompt=PromptConfig(system="You are helpful."),
            model=ModelConfig(provider="anthropic", name="claude-3"),
            tools=ToolConfig(
                allow=["bash", "file_read"],
                deny=["file_delete"],
                require_approval=["bash"],
                auto_approve=["file_read"]
            ),
            run=RunConfig(max_rounds=20, timeout=600, terminate_mode=SubagentTerminateMode.MANUAL)
        )
        
        result = manager.get_runtime_config(
            config,
            available_tools=["bash", "file_read", "file_write", "file_delete"]
        )
        assert result.name == "full_agent"
        assert result.system_prompt == "You are helpful."
        assert result.model_provider == "anthropic"
        assert result.model_name == "claude-3"
        assert "bash" in result.allowed_tools
        assert "file_read" in result.allowed_tools
        assert "file_delete" in result.denied_tools
        assert "bash" in result.require_approval_tools
        assert "file_read" in result.auto_approve_tools
        assert result.max_rounds == 20
        assert result.timeout == 600
    
    def test_get_runtime_config_wildcard_allow(self, manager):
        """Test runtime config with wildcard allow."""
        config = SubagentConfig(
            name="wildcard_agent",
            description="Wildcard agent",
            tools=ToolConfig(allow=["*"])
        )
        
        available = ["bash", "file_read", "file_write"]
        result = manager.get_runtime_config(config, available_tools=available)
        assert set(result.allowed_tools) == set(available)
    
    def test_get_runtime_config_filters_available_tools(self, manager):
        """Test that runtime config filters to available tools."""
        config = SubagentConfig(
            name="filtered_agent",
            description="Filtered agent",
            tools=ToolConfig(allow=["bash", "nonexistent_tool"])
        )
        
        available = ["bash", "file_read"]
        result = manager.get_runtime_config(config, available_tools=available)
        assert "bash" in result.allowed_tools
        assert "nonexistent_tool" not in result.allowed_tools
    
    def test_get_runtime_config_default_provider_model(self, manager):
        """Test runtime config uses provided defaults."""
        config = SubagentConfig(
            name="default_agent",
            description="Default agent"
        )
        
        result = manager.get_runtime_config(
            config,
            default_provider="anthropic",
            default_model="claude-3-opus"
        )
        assert result.model_provider == "anthropic"
        assert result.model_name == "claude-3-opus"


class TestPrivateMethods(TestSubagentManager):
    """Tests for private helper methods."""
    
    def test_get_storage_directory_project(self, manager, temp_project_root):
        """Test getting storage directory for project level."""
        result = manager._get_storage_directory(SubagentLevel.PROJECT)
        assert result == temp_project_root / ".opencode" / "subagents"
    
    def test_get_storage_directory_user(self, manager, temp_user_home):
        """Test getting storage directory for user level."""
        result = manager._get_storage_directory(SubagentLevel.USER)
        assert result == temp_user_home / ".opencode" / "subagents"
    
    def test_get_config_path(self, manager, temp_project_root):
        """Test getting config file path."""
        result = manager._get_config_path("test_agent", SubagentLevel.PROJECT)
        expected = temp_project_root / ".opencode" / "subagents" / "test_agent.md"
        assert result == expected
    
    @pytest.mark.asyncio
    async def test_load_from_directory_nonexistent(self, manager):
        """Test loading from nonexistent directory."""
        result = await manager._load_from_directory(
            Path("/nonexistent/path"),
            SubagentLevel.PROJECT
        )
        assert result == []
    
    @pytest.mark.asyncio
    async def test_parse_markdown_file_valid(self, manager, temp_project_root):
        """Test parsing a valid markdown file."""
        # Create a valid markdown file
        project_subagents_dir = temp_project_root / ".opencode" / "subagents"
        project_subagents_dir.mkdir(parents=True, exist_ok=True)
        
        config_path = project_subagents_dir / "valid_agent.md"
        content = """---
name: valid_agent
description: A valid agent
---
# valid_agent

A valid agent
"""
        config_path.write_text(content)
        
        result = await manager._parse_markdown_file(config_path)
        assert result is not None
        assert result.name == "valid_agent"
    
    @pytest.mark.asyncio
    async def test_parse_markdown_file_no_frontmatter(self, manager, temp_project_root):
        """Test parsing a file without frontmatter."""
        project_subagents_dir = temp_project_root / ".opencode" / "subagents"
        project_subagents_dir.mkdir(parents=True, exist_ok=True)
        
        config_path = project_subagents_dir / "no_frontmatter.md"
        content = """# no_frontmatter

This has no frontmatter.
"""
        config_path.write_text(content)
        
        result = await manager._parse_markdown_file(config_path)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_parse_markdown_file_invalid_yaml(self, manager, temp_project_root):
        """Test parsing a file with invalid YAML."""
        project_subagents_dir = temp_project_root / ".opencode" / "subagents"
        project_subagents_dir.mkdir(parents=True, exist_ok=True)
        
        config_path = project_subagents_dir / "invalid_yaml.md"
        content = """---
name: [invalid yaml
description: missing quote
---
# invalid_yaml

Invalid YAML
"""
        config_path.write_text(content)
        
        with pytest.raises(SubagentFileError):
            await manager._parse_markdown_file(config_path)
