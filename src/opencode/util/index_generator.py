"""
Project Index Generator

Generates structural indexes for projects to enable fast exploration.
Inspired by the bash-based generate-index.sh approach but implemented
in Python for cross-platform compatibility.

The index includes:
- Directory tree structure
- File counts by extension
- Project type detection (Python, Node/TS, etc.)
- Entry points and key files
- Test file locations
- Database schema references
- Git commit hash for staleness detection
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import logging

logger = logging.getLogger(__name__)


class ProjectType(str, Enum):
    """Detected project types."""
    PYTHON = "python"
    NODE_TYPESCRIPT = "node_typescript"
    PHP = "php"
    MIXED = "mixed"
    UNKNOWN = "unknown"


@dataclass
class IndexConfig:
    """Configuration for index generation."""
    
    # Directories to exclude from indexing
    exclude_dirs: Set[str] = field(default_factory=lambda: {
        "node_modules", "dist", "build", ".git", "venv", "__pycache__",
        ".vite", "coverage", ".next", "vendor", "playwright-report",
        "test-results", ".cache", ".turbo", ".tox", ".mypy_cache",
        ".pytest_cache", ".ruff_cache", "htmlcov", "*.egg-info",
    })
    
    # Maximum directory tree depth
    tree_depth: int = 2
    
    # Maximum file extension count to show
    max_extension_count: int = 15
    
    # Maximum test file locations to show
    max_test_locations: int = 20
    
    # Index file name
    index_filename: str = "index.md"
    
    # Index directory name
    index_dir: str = ".claude"


@dataclass
class ProjectIndex:
    """Generated project index data."""
    
    project_name: str
    project_path: Path
    project_type: ProjectType
    
    # Git information
    branch: str = "unknown"
    commit: str = "unknown"
    commit_date: str = "unknown"
    
    # Generated timestamp
    generated_at: str = ""
    
    # Directory tree
    directory_tree: str = ""
    
    # File counts by extension
    file_counts: Dict[str, int] = field(default_factory=dict)
    
    # Entry points
    entry_points: List[str] = field(default_factory=list)
    
    # npm scripts (for Node projects)
    npm_scripts: Dict[str, str] = field(default_factory=dict)
    
    # Python modules
    python_modules: List[str] = field(default_factory=list)
    
    # Database schema references
    database_schemas: List[str] = field(default_factory=list)
    
    # Test files by directory
    test_files: Dict[str, int] = field(default_factory=dict)
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class IndexGenerator:
    """
    Generates structural indexes for projects.
    
    Example:
        generator = IndexGenerator()
        index = generator.generate(Path("/path/to/project"))
        generator.save_index(index, Path("/path/to/project/.claude/index.md"))
    """
    
    def __init__(self, config: Optional[IndexConfig] = None):
        self.config = config or IndexConfig()
    
    def generate(self, project_path: Path) -> ProjectIndex:
        """
        Generate an index for a project.
        
        Args:
            project_path: Root path of the project
            
        Returns:
            ProjectIndex with structural information
        """
        project_path = project_path.resolve()
        project_name = project_path.name
        
        # Detect project type
        project_type = self._detect_project_type(project_path)
        
        # Get git information
        branch, commit, commit_date = self._get_git_info(project_path)
        
        # Generate directory tree
        directory_tree = self._generate_tree(project_path)
        
        # Count files by extension
        file_counts = self._count_files_by_extension(project_path)
        
        # Create base index
        index = ProjectIndex(
            project_name=project_name,
            project_path=project_path,
            project_type=project_type,
            branch=branch,
            commit=commit,
            commit_date=commit_date,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            directory_tree=directory_tree,
            file_counts=file_counts,
        )
        
        # Add project-type-specific information
        if project_type in (ProjectType.PYTHON, ProjectType.MIXED):
            self._add_python_info(index, project_path)
        
        if project_type in (ProjectType.NODE_TYPESCRIPT, ProjectType.MIXED):
            self._add_node_info(index, project_path)
        
        if project_type == ProjectType.PHP:
            self._add_php_info(index, project_path)
        
        # Add test file information
        self._add_test_info(index, project_path)
        
        return index
    
    def _detect_project_type(self, project_path: Path) -> ProjectType:
        """Detect the type of project."""
        has_python = bool(
            (project_path / "requirements.txt").exists() or
            (project_path / "pyproject.toml").exists() or
            (project_path / "setup.py").exists() or
            list(project_path.glob("*.py"))
        )
        
        has_node = bool(
            (project_path / "package.json").exists() or
            (project_path / "tsconfig.json").exists()
        )
        
        has_php = bool(
            (project_path / "composer.json").exists() or
            list(project_path.glob("*.php"))
        )
        
        types_count = sum([has_python, has_node, has_php])
        
        if types_count > 1:
            return ProjectType.MIXED
        elif has_python:
            return ProjectType.PYTHON
        elif has_node:
            return ProjectType.NODE_TYPESCRIPT
        elif has_php:
            return ProjectType.PHP
        else:
            return ProjectType.UNKNOWN
    
    def _get_git_info(self, project_path: Path) -> tuple[str, str, str]:
        """Get git branch, commit, and date."""
        try:
            # Get branch
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            branch = result.stdout.strip() if result.returncode == 0 else "unknown"
            
            # Get commit hash
            result = subprocess.run(
                ["git", "log", "-1", "--format=%h"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            commit = result.stdout.strip() if result.returncode == 0 else "unknown"
            
            # Get commit date
            result = subprocess.run(
                ["git", "log", "-1", "--format=%ci"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            commit_date = result.stdout.strip() if result.returncode == 0 else "unknown"
            
            return branch, commit, commit_date
            
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.debug(f"Git info error: {e}")
            return "unknown", "unknown", "unknown"
    
    def _generate_tree(self, project_path: Path) -> str:
        """Generate a directory tree string."""
        lines = []
        
        def should_exclude(name: str) -> bool:
            return name in self.config.exclude_dirs or name.startswith(".")
        
        def build_tree(path: Path, prefix: str = "", depth: int = 0) -> None:
            if depth > self.config.tree_depth:
                return
            
            try:
                entries = sorted(path.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
            except PermissionError:
                return
            
            dirs = [e for e in entries if e.is_dir() and not should_exclude(e.name)]
            
            for i, dir_entry in enumerate(dirs):
                is_last = i == len(dirs) - 1
                connector = "└── " if is_last else "├── "
                lines.append(f"{prefix}{connector}{dir_entry.name}/")
                
                extension = "    " if is_last else "│   "
                build_tree(dir_entry, prefix + extension, depth + 1)
        
        lines.append(f"{project_path.name}/")
        build_tree(project_path)
        
        return "\n".join(lines)
    
    def _count_files_by_extension(self, project_path: Path) -> Dict[str, int]:
        """Count files by extension."""
        counts: Dict[str, int] = {}
        
        def should_exclude(name: str) -> bool:
            return name in self.config.exclude_dirs
        
        for root, dirs, files in os.walk(project_path):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if not should_exclude(d)]
            
            for file in files:
                ext = Path(file).suffix.lower()
                if ext:
                    ext = ext[1:]  # Remove leading dot
                else:
                    ext = "no_extension"
                counts[ext] = counts.get(ext, 0) + 1
        
        # Sort by count descending
        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True)[:self.config.max_extension_count])
    
    def _add_python_info(self, index: ProjectIndex, project_path: Path) -> None:
        """Add Python-specific information to the index."""
        # Find Python modules (directories with __init__.py)
        modules = []
        for init_file in project_path.rglob("__init__.py"):
            rel_path = init_file.parent.relative_to(project_path)
            if not any(part in self.config.exclude_dirs for part in rel_path.parts):
                modules.append(str(rel_path).replace(os.sep, "/"))
        
        index.python_modules = sorted(modules)[:50]
        
        # Find database schema references
        schemas = []
        schema_patterns = ["CREATE TABLE", "BaseModel", "Table(", "schema"]
        
        for py_file in project_path.rglob("*.py"):
            if any(part in self.config.exclude_dirs for part in py_file.relative_to(project_path).parts):
                continue
            
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                for pattern in schema_patterns:
                    if pattern in content:
                        rel_path = py_file.relative_to(project_path)
                        schemas.append(f"{rel_path}: {pattern}")
                        break
            except Exception:
                pass
        
        index.database_schemas = schemas[:20]
        
        # Find entry points
        entry_points = []
        entry_candidates = [
            "__main__.py",
            "main.py",
            "app.py",
            "run.py",
            "cli.py",
            "wsgi.py",
            "asgi.py",
        ]
        
        for candidate in entry_candidates:
            for match in project_path.rglob(candidate):
                if any(part in self.config.exclude_dirs for part in match.relative_to(project_path).parts):
                    continue
                entry_points.append(str(match.relative_to(project_path)))
        
        index.entry_points.extend(entry_points)
    
    def _add_node_info(self, index: ProjectIndex, project_path: Path) -> None:
        """Add Node/TypeScript-specific information to the index."""
        package_json = project_path / "package.json"
        
        if package_json.exists():
            try:
                data = json.loads(package_json.read_text(encoding="utf-8"))
                
                # Get npm scripts
                scripts = data.get("scripts", {})
                index.npm_scripts = dict(list(scripts.items())[:20])
                
                # Get main entry point
                if main := data.get("main"):
                    index.entry_points.append(f"main: {main}")
                
            except Exception as e:
                logger.debug(f"Error parsing package.json: {e}")
        
        # Find common entry points
        entry_candidates = [
            "src/index.ts",
            "src/index.tsx",
            "src/main.ts",
            "src/main.tsx",
            "index.ts",
            "index.js",
            "src/App.tsx",
            "src/App.jsx",
        ]
        
        for candidate in entry_candidates:
            entry_path = project_path / candidate
            if entry_path.exists():
                index.entry_points.append(candidate)
    
    def _add_php_info(self, index: ProjectIndex, project_path: Path) -> None:
        """Add PHP-specific information to the index."""
        # Find PHP entry points
        php_files = []
        
        for php_file in project_path.rglob("*.php"):
            if any(part in self.config.exclude_dirs for part in php_file.relative_to(project_path).parts):
                continue
            php_files.append(str(php_file.relative_to(project_path)))
        
        index.metadata["php_files"] = php_files[:20]
    
    def _add_test_info(self, index: ProjectIndex, project_path: Path) -> None:
        """Add test file information to the index."""
        test_patterns = [
            "*.test.*",
            "*.spec.*",
            "test_*.py",
            "*_test.py",
            "*Test.java",
            "*Tests.java",
        ]
        
        test_dirs: Dict[str, int] = {}
        
        for pattern in test_patterns:
            for test_file in project_path.rglob(pattern):
                if any(part in self.config.exclude_dirs for part in test_file.relative_to(project_path).parts):
                    continue
                
                test_dir = str(test_file.parent.relative_to(project_path))
                test_dirs[test_dir] = test_dirs.get(test_dir, 0) + 1
        
        index.test_files = dict(sorted(test_dirs.items(), key=lambda x: x[1], reverse=True)[:self.config.max_test_locations])
    
    def format_index(self, index: ProjectIndex) -> str:
        """Format the index as markdown."""
        lines = [
            f"# Index: {index.project_name}",
            "",
            f"Generated: {index.generated_at}",
            f"Branch: {index.branch}",
            f"Commit: {index.commit}",
            f"Last commit: {index.commit_date}",
            f"Project Type: {index.project_type.value}",
            "",
            "## Directory Tree",
            "",
            "```",
            index.directory_tree,
            "```",
            "",
            "## File Counts by Extension",
            "",
            "```",
            *[f"  {ext}: {count}" for ext, count in index.file_counts.items()],
            "```",
            "",
        ]
        
        # npm scripts
        if index.npm_scripts:
            lines.extend([
                "## npm Scripts",
                "",
                "```",
                *[f"  {name}: {script}" for name, script in index.npm_scripts.items()],
                "```",
                "",
            ])
        
        # Entry points
        if index.entry_points:
            lines.extend([
                "## Entry Points",
                "",
                *[f"- `{ep}`" for ep in index.entry_points[:20]],
                "",
            ])
        
        # Python modules
        if index.python_modules:
            lines.extend([
                "## Python Modules",
                "",
                "```",
                *[f"  {mod}" for mod in index.python_modules[:30]],
                "```",
                "",
            ])
        
        # Database schemas
        if index.database_schemas:
            lines.extend([
                "## Database Schema References",
                "",
                "```",
                *[f"  {schema}" for schema in index.database_schemas],
                "```",
                "",
            ])
        
        # Test files
        if index.test_files:
            total_tests = sum(index.test_files.values())
            lines.extend([
                "## Test Files",
                "",
                f"{total_tests} test files in:",
                "",
                "```",
                *[f"  {count:4d} in {dir}" for dir, count in index.test_files.items()],
                "```",
                "",
            ])
        
        return "\n".join(lines)
    
    def save_index(self, index: ProjectIndex, output_path: Optional[Path] = None) -> Path:
        """
        Save the index to a file.
        
        Args:
            index: The project index to save
            output_path: Optional custom output path (default: project/.claude/index.md)
            
        Returns:
            Path to the saved index file
        """
        if output_path is None:
            output_path = index.project_path / self.config.index_dir / self.config.index_filename
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        content = self.format_index(index)
        output_path.write_text(content, encoding="utf-8")
        
        return output_path
    
    def is_index_fresh(self, index_path: Path, max_age_minutes: int = 5) -> bool:
        """
        Check if an existing index is fresh (recently generated).
        
        Args:
            index_path: Path to the index file
            max_age_minutes: Maximum age in minutes to consider fresh
            
        Returns:
            True if the index is fresh
        """
        if not index_path.exists():
            return False
        
        import time
        age_seconds = time.time() - index_path.stat().st_mtime
        return age_seconds < max_age_minutes * 60
    
    def is_index_stale(self, project_path: Path, index_path: Path) -> bool:
        """
        Check if an index is stale (git commit differs).
        
        Args:
            project_path: Path to the project
            index_path: Path to the index file
            
        Returns:
            True if the index is stale
        """
        if not index_path.exists():
            return True
        
        # Get current commit
        _, current_commit, _ = self._get_git_info(project_path)
        
        # Get commit from index
        try:
            content = index_path.read_text(encoding="utf-8")
            for line in content.split("\n"):
                if line.startswith("Commit:"):
                    index_commit = line.split(":", 1)[1].strip()
                    return index_commit != current_commit
        except Exception:
            return True
        
        return False
