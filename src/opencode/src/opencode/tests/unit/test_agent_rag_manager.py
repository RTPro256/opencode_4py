"""
Tests for Agent RAG Manager.

Tests agent-specific RAG management functionality.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

from opencode.core.rag.agent_rag_manager import AgentRAGConfig, AgentRAGManager


class TestAgentRAGConfig:
    """Tests for AgentRAGConfig dataclass."""

    def test_config_creation(self):
        """Test creating an AgentRAGConfig instance."""
        config = AgentRAGConfig(
            agent="code",
            description="Code agent RAG",
            embedding_model="nomic-embed-text",
            chunk_size=512,
        )
        assert config.agent == "code"
        assert config.description == "Code agent RAG"
        assert config.embedding_model == "nomic-embed-text"
        assert config.chunk_size == 512

    def test_config_defaults(self):
        """Test AgentRAGConfig default values."""
        config = AgentRAGConfig(agent="test")
        assert config.description == ""
        assert config.embedding_model == "nomic-embed-text"
        assert config.embedding_provider == "ollama"
        assert config.chunk_size == 512
        assert config.chunk_overlap == 50
        assert config.top_k == 5
        assert config.min_similarity == 0.7
        assert config.sources == []
        assert config.file_patterns == ["*.py", "*.md", "*.txt"]
        assert config.created_at is None
        assert config.updated_at is None
        assert config.document_count == 0

    def test_config_to_dict(self):
        """Test converting AgentRAGConfig to dictionary."""
        config = AgentRAGConfig(
            agent="code",
            description="Test RAG",
            sources=["./src"],
            document_count=10,
        )
        result = config.to_dict()
        assert result["agent"] == "code"
        assert result["description"] == "Test RAG"
        assert result["sources"] == ["./src"]
        assert result["document_count"] == 10
        assert "embedding_model" in result
        assert "chunk_size" in result

    def test_config_from_dict(self):
        """Test creating AgentRAGConfig from dictionary."""
        data = {
            "agent": "architect",
            "description": "Architect RAG",
            "embedding_model": "custom-model",
            "chunk_size": 1024,
            "sources": ["./docs"],
            "document_count": 25,
        }
        config = AgentRAGConfig.from_dict(data)
        assert config.agent == "architect"
        assert config.description == "Architect RAG"
        assert config.embedding_model == "custom-model"
        assert config.chunk_size == 1024
        assert config.sources == ["./docs"]
        assert config.document_count == 25

    def test_config_from_dict_defaults(self):
        """Test creating AgentRAGConfig from dict with missing keys."""
        data = {"agent": "test"}
        config = AgentRAGConfig.from_dict(data)
        assert config.agent == "test"
        assert config.embedding_model == "nomic-embed-text"
        assert config.sources == []


class TestAgentRAGManager:
    """Tests for AgentRAGManager class."""

    @pytest.fixture
    def temp_rag_root(self, tmp_path):
        """Create a temporary RAG root directory."""
        return tmp_path / "RAG"

    @pytest.fixture
    def manager(self, temp_rag_root):
        """Create an AgentRAGManager instance with temp directory."""
        return AgentRAGManager(rag_root=temp_rag_root)

    def test_init_creates_directory(self, temp_rag_root):
        """Test that initialization creates the RAG directory."""
        manager = AgentRAGManager(rag_root=temp_rag_root)
        assert temp_rag_root.exists()

    def test_init_with_default_path(self):
        """Test initialization with default path."""
        with patch.object(Path, 'cwd') as mock_cwd:
            mock_cwd.return_value = Path("/test/path")
            manager = AgentRAGManager()
            assert manager.rag_root == Path("/test/path/RAG")

    def test_get_agent_dir(self, manager, temp_rag_root):
        """Test getting agent directory path."""
        result = manager._get_agent_dir("code")
        expected = temp_rag_root / "agent_code"
        assert result == expected

    def test_get_rag_dir(self, manager, temp_rag_root):
        """Test getting RAG directory path."""
        result = manager._get_rag_dir("code")
        expected = temp_rag_root / "agent_code" / "RAG"
        assert result == expected

    def test_get_config_path(self, manager, temp_rag_root):
        """Test getting config file path."""
        result = manager._get_config_path("code")
        expected = temp_rag_root / "agent_code" / "config.json"
        assert result == expected

    def test_get_index_path(self, manager, temp_rag_root):
        """Test getting index directory path."""
        result = manager._get_index_path("code")
        expected = temp_rag_root / "agent_code" / "RAG" / "code-RAG"
        assert result == expected

    def test_agent_exists_true(self, manager):
        """Test agent_exists returns True when config exists."""
        # Create config file
        config_path = manager._get_config_path("code")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text("{}")
        
        assert manager.agent_exists("code") is True

    def test_agent_exists_false(self, manager):
        """Test agent_exists returns False when config doesn't exist."""
        assert manager.agent_exists("nonexistent") is False

    def test_list_agents_empty(self, manager):
        """Test listing agents when none exist."""
        assert manager.list_agents() == []

    def test_list_agents(self, manager):
        """Test listing agents with existing configs."""
        # Create multiple agent configs
        for agent in ["code", "architect", "debug"]:
            config_path = manager._get_config_path(agent)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(json.dumps({"agent": agent}))
        
        agents = manager.list_agents()
        assert "code" in agents
        assert "architect" in agents
        assert "debug" in agents
        assert agents == sorted(agents)  # Should be sorted

    def test_list_agents_ignores_incomplete(self, manager):
        """Test that list_agents ignores directories without config."""
        # Create directory without config
        incomplete_dir = manager._get_agent_dir("incomplete")
        incomplete_dir.mkdir(parents=True)
        
        # Create complete agent
        config_path = manager._get_config_path("complete")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps({"agent": "complete"}))
        
        agents = manager.list_agents()
        assert "complete" in agents
        assert "incomplete" not in agents

    def test_load_config(self, manager):
        """Test loading an agent's configuration."""
        config_data = {
            "agent": "code",
            "description": "Code agent",
            "embedding_model": "test-model",
        }
        config_path = manager._get_config_path("code")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(config_data))
        
        config = manager.load_config("code")
        assert config is not None
        assert config.agent == "code"
        assert config.description == "Code agent"
        assert config.embedding_model == "test-model"

    def test_load_config_nonexistent(self, manager):
        """Test loading config for nonexistent agent."""
        config = manager.load_config("nonexistent")
        assert config is None

    def test_load_config_invalid_json(self, manager):
        """Test loading config with invalid JSON."""
        config_path = manager._get_config_path("invalid")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text("not valid json")
        
        config = manager.load_config("invalid")
        assert config is None

    def test_save_config(self, manager):
        """Test saving an agent's configuration."""
        config = AgentRAGConfig(
            agent="code",
            description="Test config",
            sources=["./src"],
        )
        manager.save_config(config)
        
        config_path = manager._get_config_path("code")
        assert config_path.exists()
        
        with open(config_path) as f:
            data = json.load(f)
        assert data["agent"] == "code"
        assert data["description"] == "Test config"
        assert data["sources"] == ["./src"]

    @pytest.mark.asyncio
    async def test_create_rag(self, manager):
        """Test creating a RAG for an agent."""
        config = await manager.create_rag(
            agent="code",
            description="Code agent RAG",
            embedding_model="test-model",
        )
        
        assert config.agent == "code"
        assert config.description == "Code agent RAG"
        assert config.embedding_model == "test-model"
        assert config.created_at is not None
        assert config.updated_at is not None
        
        # Check directory structure
        assert manager._get_agent_dir("code").exists()
        assert manager._get_rag_dir("code").exists()
        assert manager._get_index_path("code").exists()
        
        # Check config file
        assert manager._get_config_path("code").exists()
        
        # Check README
        readme_path = manager._get_rag_dir("code") / "README-RAG.md"
        assert readme_path.exists()

    @pytest.mark.asyncio
    async def test_create_rag_with_sources(self, manager, tmp_path):
        """Test creating a RAG with source files."""
        # Create source files
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "test.py").write_text("print('hello')")
        (src_dir / "test.md").write_text("# Test")
        
        config = await manager.create_rag(
            agent="code",
            sources=[str(src_dir)],
        )
        
        assert config.document_count > 0
        
        # Check files were copied
        rag_dir = manager._get_rag_dir("code")
        assert (rag_dir / "src" / "test.py").exists()
        assert (rag_dir / "src" / "test.md").exists()

    @pytest.mark.asyncio
    async def test_create_rag_with_single_file(self, manager, tmp_path):
        """Test creating a RAG with a single source file."""
        # Create source file
        src_file = tmp_path / "single.py"
        src_file.write_text("# Single file")
        
        config = await manager.create_rag(
            agent="code",
            sources=[str(src_file)],
        )
        
        assert config.document_count >= 1
        
        # Check file was copied
        rag_dir = manager._get_rag_dir("code")
        assert (rag_dir / "single.py").exists()

    @pytest.mark.asyncio
    async def test_create_rag_nonexistent_source(self, manager):
        """Test creating RAG with nonexistent source (should not fail)."""
        config = await manager.create_rag(
            agent="code",
            sources=["./nonexistent/path"],
        )
        
        # Should still create the RAG, just with 0 documents
        assert config.document_count == 0

    @pytest.mark.asyncio
    async def test_add_files(self, manager, tmp_path):
        """Test adding files to an existing RAG."""
        # Create initial RAG
        await manager.create_rag(agent="code")
        
        # Create new files
        new_file = tmp_path / "new.py"
        new_file.write_text("# New file")
        
        added = await manager.add_files("code", [str(new_file)])
        assert added >= 1
        
        # Check file was copied
        rag_dir = manager._get_rag_dir("code")
        assert (rag_dir / "new.py").exists()

    @pytest.mark.asyncio
    async def test_add_files_nonexistent_agent(self, manager, tmp_path):
        """Test adding files to nonexistent agent raises error."""
        new_file = tmp_path / "new.py"
        new_file.write_text("# New file")
        
        with pytest.raises(ValueError, match="No RAG found"):
            await manager.add_files("nonexistent", [str(new_file)])

    @pytest.mark.asyncio
    async def test_query(self, manager, tmp_path):
        """Test querying an agent's RAG."""
        # Create RAG with source files
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "test.py").write_text("def hello_world():\n    print('hello world')")
        
        await manager.create_rag(
            agent="code",
            sources=[str(src_dir)],
        )
        
        # Query for content
        results = await manager.query("code", "hello world")
        
        assert len(results) > 0
        assert "hello world" in results[0]["content"].lower()
        assert results[0]["score"] == 1.0

    @pytest.mark.asyncio
    async def test_query_with_top_k(self, manager, tmp_path):
        """Test querying with custom top_k."""
        # Create RAG with multiple files
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        for i in range(5):
            (src_dir / f"test{i}.py").write_text(f"# test content {i}")
        
        await manager.create_rag(
            agent="code",
            sources=[str(src_dir)],
        )
        
        # Query with top_k
        results = await manager.query("code", "test content", top_k=2)
        assert len(results) <= 2

    @pytest.mark.asyncio
    async def test_query_nonexistent_agent(self, manager):
        """Test querying nonexistent agent raises error."""
        with pytest.raises(ValueError, match="No RAG found"):
            await manager.query("nonexistent", "query")

    @pytest.mark.asyncio
    async def test_query_no_matches(self, manager, tmp_path):
        """Test querying with no matches."""
        # Create RAG with source files
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "test.py").write_text("# Some content")
        
        await manager.create_rag(
            agent="code",
            sources=[str(src_dir)],
        )
        
        # Query for something that doesn't exist
        results = await manager.query("code", "xyznonexistent123")
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_delete_rag(self, manager):
        """Test deleting an agent's RAG."""
        # Create RAG
        await manager.create_rag(agent="code")
        assert manager.agent_exists("code")
        
        # Delete it
        result = await manager.delete_rag("code")
        assert result is True
        assert not manager.agent_exists("code")
        assert not manager._get_agent_dir("code").exists()

    @pytest.mark.asyncio
    async def test_delete_rag_nonexistent(self, manager):
        """Test deleting nonexistent RAG."""
        result = await manager.delete_rag("nonexistent")
        assert result is False

    def test_get_status_existing(self, manager):
        """Test getting status of existing RAG."""
        # Create config
        config = AgentRAGConfig(
            agent="code",
            description="Test RAG",
            document_count=10,
        )
        manager.save_config(config)
        
        status = manager.get_status("code")
        assert status["exists"] is True
        assert status["agent"] == "code"
        assert status["description"] == "Test RAG"
        assert status["document_count"] == 10

    def test_get_status_nonexistent(self, manager):
        """Test getting status of nonexistent RAG."""
        status = manager.get_status("nonexistent")
        assert status["exists"] is False
        assert status["agent"] == "nonexistent"

    def test_get_status_with_index(self, manager):
        """Test getting status includes index existence."""
        # Create config and index directory
        config = AgentRAGConfig(agent="code")
        manager.save_config(config)
        
        index_dir = manager._get_index_path("code")
        index_dir.mkdir(parents=True)
        
        status = manager.get_status("code")
        assert status["index_exists"] is True

    @pytest.mark.asyncio
    async def test_readme_content(self, manager):
        """Test that README is created with correct content."""
        config = await manager.create_rag(
            agent="code",
            description="Code agent for testing",
            embedding_model="test-model",
        )
        
        readme_path = manager._get_rag_dir("code") / "README-RAG.md"
        content = readme_path.read_text()
        
        assert "Code Agent RAG" in content
        assert "Code agent for testing" in content
        assert "test-model" in content
        assert "opencode rag query --agent code" in content

    @pytest.mark.asyncio
    async def test_index_sources_replaces_existing(self, manager, tmp_path):
        """Test that indexing replaces existing source directory."""
        # Create initial RAG
        src1 = tmp_path / "src1"
        src1.mkdir()
        (src1 / "file1.py").write_text("# File 1")
        
        await manager.create_rag(agent="code", sources=[str(src1)])
        
        # Index new source with same name
        src2 = tmp_path / "src1"  # Same name
        src2.mkdir(exist_ok=True)
        (src2 / "file2.py").write_text("# File 2")
        
        await manager.add_files("code", [str(src2)])
        
        rag_dir = manager._get_rag_dir("code")
        # Should have the new file
        assert (rag_dir / "src1" / "file2.py").exists()
