"""Tests for Project Index Generator."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from opencode.util.index_generator import (
    ProjectType,
    IndexConfig,
    ProjectIndex,
)


class TestProjectType:
    """Tests for ProjectType enum."""

    def test_python_value(self):
        """Test PYTHON type value."""
        assert ProjectType.PYTHON.value == "python"

    def test_node_typescript_value(self):
        """Test NODE_TYPESCRIPT type value."""
        assert ProjectType.NODE_TYPESCRIPT.value == "node_typescript"

    def test_php_value(self):
        """Test PHP type value."""
        assert ProjectType.PHP.value == "php"

    def test_mixed_value(self):
        """Test MIXED type value."""
        assert ProjectType.MIXED.value == "mixed"

    def test_unknown_value(self):
        """Test UNKNOWN type value."""
        assert ProjectType.UNKNOWN.value == "unknown"

    def test_all_types_exist(self):
        """Test all expected types exist."""
        types = [t.value for t in ProjectType]
        assert "python" in types
        assert "node_typescript" in types
        assert "php" in types
        assert "mixed" in types
        assert "unknown" in types


class TestIndexConfig:
    """Tests for IndexConfig dataclass."""

    def test_default_values(self):
        """Test default values."""
        config = IndexConfig()
        
        assert "node_modules" in config.exclude_dirs
        assert ".git" in config.exclude_dirs
        assert "__pycache__" in config.exclude_dirs
        assert config.tree_depth == 2
        assert config.max_extension_count == 15
        assert config.max_test_locations == 20
        assert config.index_filename == "index.md"
        assert config.index_dir == ".claude"

    def test_custom_values(self):
        """Test custom values."""
        config = IndexConfig(
            exclude_dirs={"custom_exclude"},
            tree_depth=5,
            max_extension_count=30,
            max_test_locations=50,
            index_filename="custom-index.md",
            index_dir=".custom",
        )
        
        assert config.exclude_dirs == {"custom_exclude"}
        assert config.tree_depth == 5
        assert config.max_extension_count == 30
        assert config.max_test_locations == 50
        assert config.index_filename == "custom-index.md"
        assert config.index_dir == ".custom"

    def test_exclude_dirs_immutable(self):
        """Test that exclude_dirs can be modified."""
        config = IndexConfig()
        original = config.exclude_dirs.copy()
        config.exclude_dirs.add("new_exclude")
        
        assert "new_exclude" in config.exclude_dirs


class TestProjectIndex:
    """Tests for ProjectIndex dataclass."""

    def test_create_with_required_fields(self):
        """Test creating index with required fields."""
        index = ProjectIndex(
            project_name="test-project",
            project_path=Path("/tmp/test"),
            project_type=ProjectType.PYTHON,
        )
        
        assert index.project_name == "test-project"
        assert index.project_path == Path("/tmp/test")
        assert index.project_type == ProjectType.PYTHON

    def test_default_values(self):
        """Test default values."""
        index = ProjectIndex(
            project_name="test",
            project_path=Path("/tmp"),
            project_type=ProjectType.UNKNOWN,
        )
        
        assert index.branch == "unknown"
        assert index.commit == "unknown"
        assert index.commit_date == "unknown"
        assert index.generated_at == ""
        assert index.directory_tree == ""
        assert index.file_counts == {}
        assert index.entry_points == []

    def test_custom_git_info(self):
        """Test custom git info."""
        index = ProjectIndex(
            project_name="test",
            project_path=Path("/tmp"),
            project_type=ProjectType.NODE_TYPESCRIPT,
            branch="main",
            commit="abc123",
            commit_date="2024-01-01",
        )
        
        assert index.branch == "main"
        assert index.commit == "abc123"
        assert index.commit_date == "2024-01-01"

    def test_file_counts(self):
        """Test file counts."""
        index = ProjectIndex(
            project_name="test",
            project_path=Path("/tmp"),
            project_type=ProjectType.PYTHON,
            file_counts={".py": 100, ".js": 50},
        )
        
        assert index.file_counts == {".py": 100, ".js": 50}

    def test_entry_points(self):
        """Test entry points."""
        index = ProjectIndex(
            project_name="test",
            project_path=Path("/tmp"),
            project_type=ProjectType.PYTHON,
            entry_points=["main.py", "app.py"],
        )
        
        assert index.entry_points == ["main.py", "app.py"]

    def test_generated_at(self):
        """Test generated_at field."""
        index = ProjectIndex(
            project_name="test",
            project_path=Path("/tmp"),
            project_type=ProjectType.PYTHON,
            generated_at="2024-01-01T00:00:00",
        )
        
        assert index.generated_at == "2024-01-01T00:00:00"

    def test_directory_tree(self):
        """Test directory_tree field."""
        index = ProjectIndex(
            project_name="test",
            project_path=Path("/tmp"),
            project_type=ProjectType.PYTHON,
            directory_tree="root/\n  subdir/\n    file.py",
        )
        
        assert "root" in index.directory_tree
        assert "subdir" in index.directory_tree
