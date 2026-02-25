"""
Tests for Explore Tool.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import tempfile
import os

from opencode.tool.explore import ExploreTool, SearchResult, get_explore_tool


@pytest.mark.unit
class TestSearchResult:
    """Tests for SearchResult dataclass."""

    def test_search_result_creation(self):
        """Test creating a SearchResult."""
        result = SearchResult(
            source="index",
            query="test files",
            answer="Found test files",
            file_paths=["/path/to/test.py"],
            confidence=0.9,
            stale=False,
        )
        assert result.source == "index"
        assert result.query == "test files"
        assert result.answer == "Found test files"
        assert result.file_paths == ["/path/to/test.py"]
        assert result.confidence == 0.9
        assert result.stale is False

    def test_search_result_defaults(self):
        """Test SearchResult default values."""
        result = SearchResult(
            source="live",
            query="test",
            answer="Answer",
        )
        assert result.file_paths == []
        assert result.confidence == 1.0
        assert result.stale is False


@pytest.mark.unit
class TestExploreTool:
    """Tests for ExploreTool."""

    def test_tool_name(self):
        """Test tool name property."""
        tool = ExploreTool()
        assert tool.name == "explore"

    def test_tool_description(self):
        """Test tool description property."""
        tool = ExploreTool()
        assert "explorer" in tool.description.lower()

    def test_tool_parameters(self):
        """Test tool parameters property."""
        tool = ExploreTool()
        params = tool.parameters
        assert params["type"] == "object"
        assert "query" in params["properties"]
        assert params["required"] == ["query"]

    def test_init_with_project_path(self):
        """Test initialization with custom project path."""
        path = Path("/custom/path")
        tool = ExploreTool(project_path=path)
        assert tool.project_path == path

    def test_init_default_project_path(self):
        """Test initialization with default project path."""
        tool = ExploreTool()
        assert tool.project_path == Path.cwd()

    def test_load_index_not_exists(self):
        """Test _load_index when index doesn't exist."""
        tool = ExploreTool()
        result = tool._load_index(Path("/nonexistent/path/index.md"))
        assert result is False

    def test_load_index_exists(self):
        """Test _load_index when index exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            index_dir = Path(tmpdir) / ".opencode"
            index_dir.mkdir()
            index_path = index_dir / "index.md"
            index_path.write_text("# Test Index\n\n## Test Files\n- test.py")

            tool = ExploreTool(project_path=Path(tmpdir))
            with patch.object(tool.generator, 'is_index_fresh', return_value=True):
                result = tool._load_index(index_path)

            assert result is True
            assert tool._index_content is not None

    def test_load_index_read_error(self):
        """Test _load_index with read error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = Path(tmpdir) / "index.md"
            index_path.write_text("test")

            tool = ExploreTool()
            # Mock read_text to raise an error
            with patch.object(Path, 'read_text', side_effect=PermissionError("No access")):
                result = tool._load_index(index_path)

            assert result is False

    def test_extract_section(self):
        """Test _extract_section method."""
        tool = ExploreTool()
        tool._index_content = """# Project Index

## Test Files
- test_one.py
- test_two.py

## Entry Points
- main.py

## Other Section
- other content
"""
        section = tool._extract_section("Test Files")
        assert "test_one.py" in section
        assert "test_two.py" in section
        assert "Entry Points" not in section

    def test_extract_section_not_found(self):
        """Test _extract_section when section doesn't exist."""
        tool = ExploreTool()
        tool._index_content = "# Index\n\n## Other\n- content"
        section = tool._extract_section("Nonexistent")
        assert section is None

    def test_extract_section_no_content(self):
        """Test _extract_section when no index content."""
        tool = ExploreTool()
        tool._index_content = None
        section = tool._extract_section("Test Files")
        assert section is None

    def test_extract_test_info(self):
        """Test _extract_test_info method."""
        tool = ExploreTool()
        tool._index_content = "## Test Files\n- test_one.py\n- test_two.py"
        tool._index_valid = True

        result = tool._extract_test_info()
        assert result.source == "index"
        assert "test_one.py" in result.answer
        assert result.stale is False

    def test_extract_test_info_no_section(self):
        """Test _extract_test_info when no test section."""
        tool = ExploreTool()
        tool._index_content = "## Other\n- content"
        tool._index_valid = True

        result = tool._extract_test_info()
        assert "No test files found" in result.answer

    def test_extract_entry_points(self):
        """Test _extract_entry_points method."""
        tool = ExploreTool()
        tool._index_content = "## Entry Points\n- main.py\n- cli.py"
        tool._index_valid = True

        result = tool._extract_entry_points()
        assert result.source == "index"
        assert "main.py" in result.answer

    def test_extract_entry_points_no_section(self):
        """Test _extract_entry_points when no entry points section."""
        tool = ExploreTool()
        tool._index_content = "## Other\n- content"

        result = tool._extract_entry_points()
        assert "No entry points found" in result.answer

    def test_extract_directory_tree(self):
        """Test _extract_directory_tree method."""
        tool = ExploreTool()
        tool._index_content = "## Directory Tree\nsrc/\n  main.py\n  utils.py"
        tool._index_valid = True

        result = tool._extract_directory_tree()
        assert result.source == "index"
        assert "src/" in result.answer

    def test_extract_directory_tree_no_section(self):
        """Test _extract_directory_tree when no tree section."""
        tool = ExploreTool()
        tool._index_content = "## Other\n- content"

        result = tool._extract_directory_tree()
        assert "No directory tree found" in result.answer

    def test_extract_file_counts(self):
        """Test _extract_file_counts method."""
        tool = ExploreTool()
        tool._index_content = "## File Counts by Extension\n.py: 10\n.js: 5"
        tool._index_valid = True

        result = tool._extract_file_counts()
        assert result.source == "index"
        assert ".py: 10" in result.answer

    def test_extract_file_counts_no_section(self):
        """Test _extract_file_counts when no counts section."""
        tool = ExploreTool()
        tool._index_content = "## Other\n- content"

        result = tool._extract_file_counts()
        assert "No file count information" in result.answer

    def test_extract_npm_scripts(self):
        """Test _extract_npm_scripts method."""
        tool = ExploreTool()
        tool._index_content = "## npm Scripts\ntest: pytest\nbuild: webpack"
        tool._index_valid = True

        result = tool._extract_npm_scripts()
        assert result.source == "index"
        assert "pytest" in result.answer

    def test_extract_npm_scripts_no_section(self):
        """Test _extract_npm_scripts when no scripts section."""
        tool = ExploreTool()
        tool._index_content = "## Other\n- content"

        result = tool._extract_npm_scripts()
        assert "No npm scripts found" in result.answer

    def test_extract_python_modules(self):
        """Test _extract_python_modules method."""
        tool = ExploreTool()
        tool._index_content = "## Python Modules\nsrc.opencode\nsrc.utils"
        tool._index_valid = True

        result = tool._extract_python_modules()
        assert result.source == "index"
        assert "src.opencode" in result.answer

    def test_extract_python_modules_no_section(self):
        """Test _extract_python_modules when no modules section."""
        tool = ExploreTool()
        tool._index_content = "## Other\n- content"

        result = tool._extract_python_modules()
        assert "No Python modules found" in result.answer

    def test_extract_database_info(self):
        """Test _extract_database_info method."""
        tool = ExploreTool()
        tool._index_content = "## Database Schema References\nusers table\nposts table"
        tool._index_valid = True

        result = tool._extract_database_info()
        assert result.source == "index"
        assert "users table" in result.answer

    def test_extract_database_info_no_section(self):
        """Test _extract_database_info when no schema section."""
        tool = ExploreTool()
        tool._index_content = "## Other\n- content"

        result = tool._extract_database_info()
        assert "No database schema references" in result.answer

    def test_extract_project_type(self):
        """Test _extract_project_type method."""
        tool = ExploreTool()
        tool._index_content = "Project Type: Python\n## Other\n- content"
        tool._index_valid = True

        result = tool._extract_project_type()
        assert result.source == "index"
        assert "Python" in result.answer

    def test_extract_project_type_not_found(self):
        """Test _extract_project_type when not found."""
        tool = ExploreTool()
        tool._index_content = "## Other\n- content"

        result = tool._extract_project_type()
        assert "not found" in result.answer.lower()

    def test_extract_project_type_no_content(self):
        """Test _extract_project_type when no content."""
        tool = ExploreTool()
        tool._index_content = None

        result = tool._extract_project_type()
        assert result.answer == "Unknown"

    def test_extract_git_info(self):
        """Test _extract_git_info method."""
        tool = ExploreTool()
        tool._index_content = "Branch: main\nCommit: abc123\nLast commit: 2024-01-01"
        tool._index_valid = True

        result = tool._extract_git_info()
        assert result.source == "index"
        assert "main" in result.answer
        assert "abc123" in result.answer

    def test_extract_git_info_not_found(self):
        """Test _extract_git_info when not found."""
        tool = ExploreTool()
        tool._index_content = "## Other\n- content"

        result = tool._extract_git_info()
        assert "not found" in result.answer.lower()

    def test_extract_git_info_no_content(self):
        """Test _extract_git_info when no content."""
        tool = ExploreTool()
        tool._index_content = None

        result = tool._extract_git_info()
        assert result.answer == "Unknown"

    def test_search_in_index(self):
        """Test _search_in_index method."""
        tool = ExploreTool()
        tool._index_content = "## Test Files\ntest_one.py\ntest_two.py\n## Other\nother.py"
        tool._index_valid = True

        result = tool._search_in_index("test")
        assert result is not None
        assert result.source == "index"
        assert "test" in result.answer.lower()

    def test_search_in_index_no_match(self):
        """Test _search_in_index when no match."""
        tool = ExploreTool()
        tool._index_content = "## Test Files\ntest.py"

        result = tool._search_in_index("nonexistent")
        assert result is None

    def test_search_in_index_no_content(self):
        """Test _search_in_index when no content."""
        tool = ExploreTool()
        tool._index_content = None

        result = tool._search_in_index("test")
        assert result is None

    def test_answer_from_index_test_query(self):
        """Test _answer_from_index with test query."""
        tool = ExploreTool()
        tool._index_content = "## Test Files\ntest_one.py"
        tool._index_valid = True

        result = tool._answer_from_index("where are the tests?")
        assert result is not None
        assert "test" in result.answer.lower()

    def test_answer_from_index_entry_query(self):
        """Test _answer_from_index with entry point query."""
        tool = ExploreTool()
        tool._index_content = "## Entry Points\nmain.py"
        tool._index_valid = True

        result = tool._answer_from_index("what is the entry point?")
        assert result is not None
        assert "main.py" in result.answer

    def test_answer_from_index_structure_query(self):
        """Test _answer_from_index with structure query."""
        tool = ExploreTool()
        tool._index_content = "## Directory Tree\nsrc/\n  main.py"
        tool._index_valid = True

        result = tool._answer_from_index("show me the directory structure")
        assert result is not None
        assert "src/" in result.answer

    def test_answer_from_index_no_content(self):
        """Test _answer_from_index when no content."""
        tool = ExploreTool()
        tool._index_content = None

        result = tool._answer_from_index("test query")
        assert result is None

    @pytest.mark.asyncio
    async def test_live_search(self):
        """Test _live_search method."""
        tool = ExploreTool()

        mock_generator = MagicMock()
        mock_index = {"project_type": "Python"}
        mock_generator.generate.return_value = mock_index
        mock_generator.format_index.return_value = "Project Type: Python\n## Test Files\ntest.py"
        tool.generator = mock_generator

        result = await tool._live_search("test files")

        assert result.source == "live"
        mock_generator.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_live_search_error(self):
        """Test _live_search with error."""
        tool = ExploreTool()

        mock_generator = MagicMock()
        mock_generator.generate.side_effect = Exception("Generation error")
        tool.generator = mock_generator

        result = await tool._live_search("test query")

        assert result.source == "live"
        assert result.confidence == 0.5

    @pytest.mark.asyncio
    async def test_execute_with_index(self):
        """Test execute method with valid index."""
        with tempfile.TemporaryDirectory() as tmpdir:
            index_dir = Path(tmpdir) / ".opencode"
            index_dir.mkdir()
            index_path = index_dir / "index.md"
            index_path.write_text("## Test Files\ntest_one.py\ntest_two.py")

            tool = ExploreTool(project_path=Path(tmpdir))
            with patch.object(tool.generator, 'is_index_fresh', return_value=True):
                result = await tool.execute(query="where are the tests?")

            assert result.success is True
            assert "test" in result.output.lower() or "Test" in result.output

    @pytest.mark.asyncio
    async def test_execute_without_index(self):
        """Test execute method without index (live search)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = ExploreTool(project_path=Path(tmpdir))

            mock_generator = MagicMock()
            mock_index = {"project_type": "Python"}
            mock_generator.generate.return_value = mock_index
            mock_generator.format_index.return_value = "Project Type: Python"
            tool.generator = mock_generator

            result = await tool.execute(query="what is this project?")

            assert result.success is True

    def test_get_index_summary_no_index(self):
        """Test get_index_summary when no index."""
        tool = ExploreTool()
        tool._index_content = None

        summary = tool.get_index_summary()
        assert summary["status"] == "no_index"

    def test_get_index_summary_valid(self):
        """Test get_index_summary with valid index."""
        tool = ExploreTool()
        tool._index_content = "Project Type: Python\nBranch: main\nCommit: abc123"
        tool._index_valid = True

        summary = tool.get_index_summary()
        assert summary["status"] == "valid"
        assert summary["has_index"] is True
        assert summary["project_type"] == "Python"
        assert summary["branch"] == "main"
        assert summary["commit"] == "abc123"

    def test_get_index_summary_stale(self):
        """Test get_index_summary with stale index."""
        tool = ExploreTool()
        tool._index_content = "Project Type: Python"
        tool._index_valid = False

        summary = tool.get_index_summary()
        assert summary["status"] == "stale"


@pytest.mark.unit
class TestGetExploreTool:
    """Tests for get_explore_tool function."""

    def test_get_explore_tool_default(self):
        """Test get_explore_tool with default path."""
        tool = get_explore_tool()
        assert isinstance(tool, ExploreTool)
        assert tool.project_path == Path.cwd()

    def test_get_explore_tool_custom_path(self):
        """Test get_explore_tool with custom path."""
        path = Path("/custom/path")
        tool = get_explore_tool(project_path=path)
        assert isinstance(tool, ExploreTool)
        assert tool.project_path == path
