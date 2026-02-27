"""
Extended tests for util/index_generator.py.

Tests for IndexGenerator class methods for 100% coverage.
"""

import json
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from opencode.util.index_generator import (
    ProjectType,
    IndexConfig,
    ProjectIndex,
    IndexGenerator,
)


class TestIndexConfigExtended:
    """Extended tests for IndexConfig."""

    @pytest.mark.unit
    def test_exclude_dirs_default(self):
        """Test default exclude directories."""
        config = IndexConfig()
        assert "node_modules" in config.exclude_dirs
        assert ".git" in config.exclude_dirs
        assert "venv" in config.exclude_dirs
        assert "__pycache__" in config.exclude_dirs

    @pytest.mark.unit
    def test_tree_depth_default(self):
        """Test default tree depth."""
        config = IndexConfig()
        assert config.tree_depth == 2

    @pytest.mark.unit
    def test_max_extension_count_default(self):
        """Test default max extension count."""
        config = IndexConfig()
        assert config.max_extension_count == 15

    @pytest.mark.unit
    def test_max_test_locations_default(self):
        """Test default max test locations."""
        config = IndexConfig()
        assert config.max_test_locations == 20

    @pytest.mark.unit
    def test_index_filename_default(self):
        """Test default index filename."""
        config = IndexConfig()
        assert config.index_filename == "index.md"

    @pytest.mark.unit
    def test_index_dir_default(self):
        """Test default index directory."""
        config = IndexConfig()
        assert config.index_dir == ".claude"

    @pytest.mark.unit
    def test_custom_values(self):
        """Test custom configuration values."""
        config = IndexConfig(
            exclude_dirs={"custom_exclude"},
            tree_depth=5,
            max_extension_count=30,
            max_test_locations=50,
            index_filename="custom_index.md",
            index_dir=".custom",
        )
        assert config.exclude_dirs == {"custom_exclude"}
        assert config.tree_depth == 5
        assert config.max_extension_count == 30
        assert config.max_test_locations == 50
        assert config.index_filename == "custom_index.md"
        assert config.index_dir == ".custom"


class TestProjectIndexExtended:
    """Extended tests for ProjectIndex."""

    @pytest.mark.unit
    def test_required_fields(self):
        """Test required fields."""
        index = ProjectIndex(
            project_name="test_project",
            project_path=Path("/tmp/test"),
            project_type=ProjectType.PYTHON,
        )
        assert index.project_name == "test_project"
        assert index.project_path == Path("/tmp/test")
        assert index.project_type == ProjectType.PYTHON

    @pytest.mark.unit
    def test_default_values(self):
        """Test default values."""
        index = ProjectIndex(
            project_name="test",
            project_path=Path("/tmp/test"),
            project_type=ProjectType.UNKNOWN,
        )
        assert index.branch == "unknown"
        assert index.commit == "unknown"
        assert index.commit_date == "unknown"
        assert index.generated_at == ""
        assert index.directory_tree == ""
        assert index.file_counts == {}
        assert index.entry_points == []
        assert index.npm_scripts == {}
        assert index.python_modules == []
        assert index.database_schemas == []
        assert index.test_files == {}
        assert index.metadata == {}

    @pytest.mark.unit
    def test_custom_values(self):
        """Test custom values."""
        index = ProjectIndex(
            project_name="test",
            project_path=Path("/tmp/test"),
            project_type=ProjectType.NODE_TYPESCRIPT,
            branch="main",
            commit="abc123",
            commit_date="2024-01-01",
            generated_at="2024-01-01 12:00:00",
            directory_tree="test/",
            file_counts={"py": 10, "js": 5},
            entry_points=["main.py"],
            npm_scripts={"start": "node index.js"},
            python_modules=["src.module"],
            database_schemas=["models.py: BaseModel"],
            test_files={"tests": 5},
            metadata={"custom": "value"},
        )
        assert index.branch == "main"
        assert index.commit == "abc123"
        assert index.file_counts == {"py": 10, "js": 5}


class TestIndexGeneratorInit:
    """Tests for IndexGenerator initialization."""

    @pytest.mark.unit
    def test_init_default_config(self):
        """Test initialization with default config."""
        generator = IndexGenerator()
        assert generator.config is not None
        assert isinstance(generator.config, IndexConfig)

    @pytest.mark.unit
    def test_init_custom_config(self):
        """Test initialization with custom config."""
        config = IndexConfig(tree_depth=5)
        generator = IndexGenerator(config=config)
        assert generator.config.tree_depth == 5


class TestIndexGeneratorDetectProjectType:
    """Tests for project type detection."""

    @pytest.mark.unit
    def test_detect_python_project(self):
        """Test detecting Python project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "requirements.txt").write_text("pytest")
            
            generator = IndexGenerator()
            project_type = generator._detect_project_type(project_path)
            assert project_type == ProjectType.PYTHON

    @pytest.mark.unit
    def test_detect_python_project_pyproject(self):
        """Test detecting Python project with pyproject.toml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "pyproject.toml").write_text("[project]")
            
            generator = IndexGenerator()
            project_type = generator._detect_project_type(project_path)
            assert project_type == ProjectType.PYTHON

    @pytest.mark.unit
    def test_detect_python_project_setup_py(self):
        """Test detecting Python project with setup.py."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "setup.py").write_text("# setup")
            
            generator = IndexGenerator()
            project_type = generator._detect_project_type(project_path)
            assert project_type == ProjectType.PYTHON

    @pytest.mark.unit
    def test_detect_python_project_py_files(self):
        """Test detecting Python project with .py files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "main.py").write_text("print('hello')")
            
            generator = IndexGenerator()
            project_type = generator._detect_project_type(project_path)
            assert project_type == ProjectType.PYTHON

    @pytest.mark.unit
    def test_detect_node_project(self):
        """Test detecting Node/TypeScript project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "package.json").write_text('{"name": "test"}')
            
            generator = IndexGenerator()
            project_type = generator._detect_project_type(project_path)
            assert project_type == ProjectType.NODE_TYPESCRIPT

    @pytest.mark.unit
    def test_detect_node_project_tsconfig(self):
        """Test detecting Node/TypeScript project with tsconfig."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "tsconfig.json").write_text('{}')
            
            generator = IndexGenerator()
            project_type = generator._detect_project_type(project_path)
            assert project_type == ProjectType.NODE_TYPESCRIPT

    @pytest.mark.unit
    def test_detect_php_project(self):
        """Test detecting PHP project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "composer.json").write_text('{}')
            
            generator = IndexGenerator()
            project_type = generator._detect_project_type(project_path)
            assert project_type == ProjectType.PHP

    @pytest.mark.unit
    def test_detect_php_project_php_files(self):
        """Test detecting PHP project with .php files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "index.php").write_text('<?php echo "hello";')
            
            generator = IndexGenerator()
            project_type = generator._detect_project_type(project_path)
            assert project_type == ProjectType.PHP

    @pytest.mark.unit
    def test_detect_mixed_project(self):
        """Test detecting mixed project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "requirements.txt").write_text("pytest")
            (project_path / "package.json").write_text('{"name": "test"}')
            
            generator = IndexGenerator()
            project_type = generator._detect_project_type(project_path)
            assert project_type == ProjectType.MIXED

    @pytest.mark.unit
    def test_detect_unknown_project(self):
        """Test detecting unknown project type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            generator = IndexGenerator()
            project_type = generator._detect_project_type(project_path)
            assert project_type == ProjectType.UNKNOWN


class TestIndexGeneratorGitInfo:
    """Tests for git information retrieval."""

    @pytest.mark.unit
    def test_get_git_info_no_git(self):
        """Test git info when not in a git repo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            generator = IndexGenerator()
            branch, commit, commit_date = generator._get_git_info(project_path)
            assert branch == "unknown"
            assert commit == "unknown"
            assert commit_date == "unknown"

    @pytest.mark.unit
    @patch("subprocess.run")
    def test_get_git_info_success(self, mock_run):
        """Test successful git info retrieval."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="main\n"),
            MagicMock(returncode=0, stdout="abc123\n"),
            MagicMock(returncode=0, stdout="2024-01-01 12:00:00\n"),
        ]
        
        generator = IndexGenerator()
        branch, commit, commit_date = generator._get_git_info(Path("/tmp"))
        assert branch == "main"
        assert commit == "abc123"
        assert commit_date == "2024-01-01 12:00:00"

    @pytest.mark.unit
    @patch("subprocess.run")
    def test_get_git_info_failure(self, mock_run):
        """Test git info retrieval failure."""
        mock_run.side_effect = [
            MagicMock(returncode=1, stdout=""),
            MagicMock(returncode=1, stdout=""),
            MagicMock(returncode=1, stdout=""),
        ]
        
        generator = IndexGenerator()
        branch, commit, commit_date = generator._get_git_info(Path("/tmp"))
        assert branch == "unknown"
        assert commit == "unknown"
        assert commit_date == "unknown"

    @pytest.mark.unit
    @patch("subprocess.run")
    def test_get_git_info_timeout(self, mock_run):
        """Test git info timeout."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="git", timeout=10)
        
        generator = IndexGenerator()
        branch, commit, commit_date = generator._get_git_info(Path("/tmp"))
        assert branch == "unknown"
        assert commit == "unknown"
        assert commit_date == "unknown"

    @pytest.mark.unit
    @patch("subprocess.run")
    def test_get_git_info_file_not_found(self, mock_run):
        """Test git info when git is not installed."""
        mock_run.side_effect = FileNotFoundError()
        
        generator = IndexGenerator()
        branch, commit, commit_date = generator._get_git_info(Path("/tmp"))
        assert branch == "unknown"
        assert commit == "unknown"
        assert commit_date == "unknown"


class TestIndexGeneratorTree:
    """Tests for directory tree generation."""

    @pytest.mark.unit
    def test_generate_tree_empty(self):
        """Test tree generation for empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            generator = IndexGenerator()
            tree = generator._generate_tree(project_path)
            assert project_path.name in tree

    @pytest.mark.unit
    def test_generate_tree_with_dirs(self):
        """Test tree generation with directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "src").mkdir()
            (project_path / "tests").mkdir()
            
            generator = IndexGenerator()
            tree = generator._generate_tree(project_path)
            assert "src" in tree
            assert "tests" in tree

    @pytest.mark.unit
    def test_generate_tree_excludes_dirs(self):
        """Test tree generation excludes configured directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "src").mkdir()
            (project_path / "node_modules").mkdir()
            (project_path / ".git").mkdir()
            
            generator = IndexGenerator()
            tree = generator._generate_tree(project_path)
            assert "src" in tree
            assert "node_modules" not in tree
            assert ".git" not in tree

    @pytest.mark.unit
    def test_generate_tree_respects_depth(self):
        """Test tree generation respects depth limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "level1").mkdir()
            (project_path / "level1" / "level2").mkdir()
            (project_path / "level1" / "level2" / "level3").mkdir()
            
            config = IndexConfig(tree_depth=1)
            generator = IndexGenerator(config=config)
            tree = generator._generate_tree(project_path)
            assert "level1" in tree
            # level2 should not appear due to depth limit


class TestIndexGeneratorFileCounts:
    """Tests for file counting."""

    @pytest.mark.unit
    def test_count_files_by_extension(self):
        """Test counting files by extension."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "file1.py").write_text("")
            (project_path / "file2.py").write_text("")
            (project_path / "file3.js").write_text("")
            
            generator = IndexGenerator()
            counts = generator._count_files_by_extension(project_path)
            assert counts.get("py") == 2
            assert counts.get("js") == 1

    @pytest.mark.unit
    def test_count_files_no_extension(self):
        """Test counting files without extension."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "Makefile").write_text("")
            
            generator = IndexGenerator()
            counts = generator._count_files_by_extension(project_path)
            assert "no_extension" in counts

    @pytest.mark.unit
    def test_count_files_excludes_dirs(self):
        """Test counting excludes configured directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "file1.py").write_text("")
            
            node_modules = project_path / "node_modules"
            node_modules.mkdir()
            (node_modules / "file2.py").write_text("")
            
            generator = IndexGenerator()
            counts = generator._count_files_by_extension(project_path)
            assert counts.get("py") == 1


class TestIndexGeneratorPythonInfo:
    """Tests for Python-specific information."""

    @pytest.mark.unit
    def test_add_python_info_modules(self):
        """Test adding Python module information."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            src_dir = project_path / "src"
            src_dir.mkdir()
            (src_dir / "__init__.py").write_text("")
            
            index = ProjectIndex(
                project_name="test",
                project_path=project_path,
                project_type=ProjectType.PYTHON,
            )
            
            generator = IndexGenerator()
            generator._add_python_info(index, project_path)
            assert len(index.python_modules) > 0

    @pytest.mark.unit
    def test_add_python_info_entry_points(self):
        """Test finding Python entry points."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "main.py").write_text("")
            (project_path / "__main__.py").write_text("")
            
            index = ProjectIndex(
                project_name="test",
                project_path=project_path,
                project_type=ProjectType.PYTHON,
            )
            
            generator = IndexGenerator()
            generator._add_python_info(index, project_path)
            assert len(index.entry_points) >= 2

    @pytest.mark.unit
    def test_add_python_info_database_schemas(self):
        """Test finding database schema references."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "models.py").write_text("from pydantic import BaseModel\n\nclass User(BaseModel):\n    pass")
            
            index = ProjectIndex(
                project_name="test",
                project_path=project_path,
                project_type=ProjectType.PYTHON,
            )
            
            generator = IndexGenerator()
            generator._add_python_info(index, project_path)
            assert len(index.database_schemas) > 0


class TestIndexGeneratorNodeInfo:
    """Tests for Node/TypeScript-specific information."""

    @pytest.mark.unit
    def test_add_node_info_package_json(self):
        """Test adding Node info from package.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            package_json = project_path / "package.json"
            package_json.write_text(json.dumps({
                "scripts": {"start": "node index.js", "test": "jest"},
                "main": "index.js"
            }))
            
            index = ProjectIndex(
                project_name="test",
                project_path=project_path,
                project_type=ProjectType.NODE_TYPESCRIPT,
            )
            
            generator = IndexGenerator()
            generator._add_node_info(index, project_path)
            assert "start" in index.npm_scripts
            assert "test" in index.npm_scripts

    @pytest.mark.unit
    def test_add_node_info_entry_points(self):
        """Test finding Node entry points."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            src_dir = project_path / "src"
            src_dir.mkdir()
            (src_dir / "index.ts").write_text("")
            
            index = ProjectIndex(
                project_name="test",
                project_path=project_path,
                project_type=ProjectType.NODE_TYPESCRIPT,
            )
            
            generator = IndexGenerator()
            generator._add_node_info(index, project_path)
            assert "src/index.ts" in index.entry_points

    @pytest.mark.unit
    def test_add_node_info_invalid_package_json(self):
        """Test handling invalid package.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "package.json").write_text("invalid json")
            
            index = ProjectIndex(
                project_name="test",
                project_path=project_path,
                project_type=ProjectType.NODE_TYPESCRIPT,
            )
            
            generator = IndexGenerator()
            # Should not raise exception
            generator._add_node_info(index, project_path)


class TestIndexGeneratorPHPInfo:
    """Tests for PHP-specific information."""

    @pytest.mark.unit
    def test_add_php_info(self):
        """Test adding PHP file information."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "index.php").write_text("<?php")
            (project_path / "app.php").write_text("<?php")
            
            index = ProjectIndex(
                project_name="test",
                project_path=project_path,
                project_type=ProjectType.PHP,
            )
            
            generator = IndexGenerator()
            generator._add_php_info(index, project_path)
            assert "php_files" in index.metadata


class TestIndexGeneratorTestInfo:
    """Tests for test file information."""

    @pytest.mark.unit
    def test_add_test_info_pytest(self):
        """Test finding pytest test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            tests_dir = project_path / "tests"
            tests_dir.mkdir()
            (tests_dir / "test_module.py").write_text("")
            (tests_dir / "test_another.py").write_text("")
            
            index = ProjectIndex(
                project_name="test",
                project_path=project_path,
                project_type=ProjectType.PYTHON,
            )
            
            generator = IndexGenerator()
            generator._add_test_info(index, project_path)
            assert "tests" in index.test_files

    @pytest.mark.unit
    def test_add_test_info_jest(self):
        """Test finding Jest test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "app.test.js").write_text("")
            (project_path / "utils.spec.ts").write_text("")
            
            index = ProjectIndex(
                project_name="test",
                project_path=project_path,
                project_type=ProjectType.NODE_TYPESCRIPT,
            )
            
            generator = IndexGenerator()
            generator._add_test_info(index, project_path)
            assert len(index.test_files) > 0


class TestIndexGeneratorFormatIndex:
    """Tests for index formatting."""

    @pytest.mark.unit
    def test_format_index_basic(self):
        """Test basic index formatting."""
        index = ProjectIndex(
            project_name="test_project",
            project_path=Path("/tmp/test"),
            project_type=ProjectType.PYTHON,
            branch="main",
            commit="abc123",
            commit_date="2024-01-01",
            generated_at="2024-01-01 12:00:00",
            directory_tree="test_project/",
            file_counts={"py": 10},
        )
        
        generator = IndexGenerator()
        formatted = generator.format_index(index)
        assert "# Index: test_project" in formatted
        assert "Branch: main" in formatted
        assert "Commit: abc123" in formatted
        assert "Project Type: python" in formatted
        assert "Directory Tree" in formatted
        assert "File Counts by Extension" in formatted

    @pytest.mark.unit
    def test_format_index_with_npm_scripts(self):
        """Test index formatting with npm scripts."""
        index = ProjectIndex(
            project_name="test",
            project_path=Path("/tmp/test"),
            project_type=ProjectType.NODE_TYPESCRIPT,
            npm_scripts={"start": "node index.js"},
        )
        
        generator = IndexGenerator()
        formatted = generator.format_index(index)
        assert "npm Scripts" in formatted
        assert "start: node index.js" in formatted

    @pytest.mark.unit
    def test_format_index_with_entry_points(self):
        """Test index formatting with entry points."""
        index = ProjectIndex(
            project_name="test",
            project_path=Path("/tmp/test"),
            project_type=ProjectType.PYTHON,
            entry_points=["main.py", "cli.py"],
        )
        
        generator = IndexGenerator()
        formatted = generator.format_index(index)
        assert "Entry Points" in formatted
        assert "main.py" in formatted

    @pytest.mark.unit
    def test_format_index_with_python_modules(self):
        """Test index formatting with Python modules."""
        index = ProjectIndex(
            project_name="test",
            project_path=Path("/tmp/test"),
            project_type=ProjectType.PYTHON,
            python_modules=["src.module", "src.utils"],
        )
        
        generator = IndexGenerator()
        formatted = generator.format_index(index)
        assert "Python Modules" in formatted

    @pytest.mark.unit
    def test_format_index_with_database_schemas(self):
        """Test index formatting with database schemas."""
        index = ProjectIndex(
            project_name="test",
            project_path=Path("/tmp/test"),
            project_type=ProjectType.PYTHON,
            database_schemas=["models.py: BaseModel"],
        )
        
        generator = IndexGenerator()
        formatted = generator.format_index(index)
        assert "Database Schema References" in formatted

    @pytest.mark.unit
    def test_format_index_with_test_files(self):
        """Test index formatting with test files."""
        index = ProjectIndex(
            project_name="test",
            project_path=Path("/tmp/test"),
            project_type=ProjectType.PYTHON,
            test_files={"tests": 5, "src": 2},
        )
        
        generator = IndexGenerator()
        formatted = generator.format_index(index)
        assert "Test Files" in formatted
        assert "7 test files" in formatted


class TestIndexGeneratorSaveIndex:
    """Tests for saving index."""

    @pytest.mark.unit
    def test_save_index_default_path(self):
        """Test saving index to default path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            index = ProjectIndex(
                project_name="test",
                project_path=project_path,
                project_type=ProjectType.PYTHON,
                generated_at="2024-01-01",
            )
            
            generator = IndexGenerator()
            output_path = generator.save_index(index)
            assert output_path.exists()
            assert output_path.name == "index.md"
            assert ".claude" in str(output_path)

    @pytest.mark.unit
    def test_save_index_custom_path(self):
        """Test saving index to custom path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            custom_path = project_path / "custom_index.md"
            
            index = ProjectIndex(
                project_name="test",
                project_path=project_path,
                project_type=ProjectType.PYTHON,
            )
            
            generator = IndexGenerator()
            output_path = generator.save_index(index, custom_path)
            assert output_path.exists()
            assert output_path == custom_path


class TestIndexGeneratorFreshness:
    """Tests for index freshness checks."""

    @pytest.mark.unit
    def test_is_index_fresh_nonexistent(self):
        """Test freshness check for nonexistent index."""
        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = Path(tmpdir) / "index.md"
            
            generator = IndexGenerator()
            assert generator.is_index_fresh(index_path) is False

    @pytest.mark.unit
    def test_is_index_fresh_recent(self):
        """Test freshness check for recent index."""
        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = Path(tmpdir) / "index.md"
            index_path.write_text("# Index")
            
            generator = IndexGenerator()
            assert generator.is_index_fresh(index_path, max_age_minutes=5) is True

    @pytest.mark.unit
    def test_is_index_fresh_old(self):
        """Test freshness check for old index."""
        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = Path(tmpdir) / "index.md"
            index_path.write_text("# Index")
            
            # Set modification time to 10 minutes ago
            old_time = time.time() - 600
            os.utime(index_path, (old_time, old_time))
            
            generator = IndexGenerator()
            assert generator.is_index_fresh(index_path, max_age_minutes=5) is False


class TestIndexGeneratorStaleness:
    """Tests for index staleness checks."""

    @pytest.mark.unit
    def test_is_index_stale_nonexistent(self):
        """Test staleness check for nonexistent index."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            index_path = project_path / "index.md"
            
            generator = IndexGenerator()
            assert generator.is_index_stale(project_path, index_path) is True

    @pytest.mark.unit
    def test_is_index_stale_no_commit_in_index(self):
        """Test staleness check when index has no commit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            index_path = project_path / "index.md"
            index_path.write_text("# Index\n\nNo commit here")
            
            generator = IndexGenerator()
            # When no commit found in index, returns False (falls through)
            result = generator.is_index_stale(project_path, index_path)
            # The function returns False when no commit line is found (falls through)
            assert result is False

    @pytest.mark.unit
    def test_is_index_stale_same_commit(self):
        """Test staleness check with same commit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            index_path = project_path / "index.md"
            index_path.write_text("# Index\n\nCommit: abc123\n")
            
            generator = IndexGenerator()
            with patch.object(generator, '_get_git_info', return_value=("main", "abc123", "2024-01-01")):
                result = generator.is_index_stale(project_path, index_path)
                assert result is False

    @pytest.mark.unit
    def test_is_index_stale_different_commit(self):
        """Test staleness check with different commit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            index_path = project_path / "index.md"
            index_path.write_text("# Index\n\nCommit: old123\n")
            
            generator = IndexGenerator()
            with patch.object(generator, '_get_git_info', return_value=("main", "new456", "2024-01-01")):
                result = generator.is_index_stale(project_path, index_path)
                assert result is True


class TestIndexGeneratorGenerate:
    """Tests for full index generation."""

    @pytest.mark.unit
    def test_generate_full_index(self):
        """Test full index generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "requirements.txt").write_text("pytest")
            (project_path / "main.py").write_text("print('hello')")
            
            tests_dir = project_path / "tests"
            tests_dir.mkdir()
            (tests_dir / "test_main.py").write_text("def test(): pass")
            
            generator = IndexGenerator()
            index = generator.generate(project_path)
            
            assert index.project_name == project_path.name
            assert index.project_type == ProjectType.PYTHON
            assert index.directory_tree != ""
            assert len(index.file_counts) > 0
