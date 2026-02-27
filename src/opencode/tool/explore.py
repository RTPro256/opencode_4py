"""
Explore Tool

A fast codebase explorer that uses pre-computed structural indexes.
Reads index files first, then falls back to live search when needed.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import logging
import re

from opencode.tool.base import Tool, ToolResult
from opencode.util.index_generator import IndexGenerator, IndexConfig

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Result from an exploration search."""
    source: str  # "index" or "live"
    query: str
    answer: str
    file_paths: List[str] = field(default_factory=list)
    confidence: float = 1.0
    stale: bool = False


class ExploreTool(Tool):
    """
    Fast codebase explorer using pre-computed indexes.
    
    This tool reads structural indexes first to answer questions
    about project structure, file locations, and architecture
    without iterative Glob/Grep calls.
    
    Features:
    - Reads pre-computed indexes for fast responses
    - Falls back to live search when index is missing or stale
    - Two-layer staleness detection (age + git commit)
    - Project type awareness
    
    Example:
        tool = ExploreTool()
        result = await tool.execute("Where are the test files?")
        print(result.answer)
    """
    
    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path or Path.cwd()
        self.config = IndexConfig()
        self.generator = IndexGenerator(self.config)
        self._index_content: Optional[str] = None
        self._index_valid: bool = False
    
    @property
    def name(self) -> str:
        return "explore"
    
    @property
    def description(self) -> str:
        return "Fast codebase explorer using pre-computed indexes"
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The question about the project structure",
                },
            },
            "required": ["query"],
        }
    
    async def execute(self, **params: Any) -> ToolResult:
        """
        Execute an exploration query.
        
        Args:
            query: The question about the project structure
            
        Returns:
            ToolResult with the answer
        """
        # Get query from params
        query = params.get("query", "")
        
        # Normalize query
        query = query.strip().lower()
        
        # Try to answer from index
        index_path = self.project_path / self.config.index_dir / self.config.index_filename
        
        if self._load_index(index_path):
            result = self._answer_from_index(query)
            if result:
                return ToolResult.ok(result.answer, metadata={"source": result.source, "file_paths": result.file_paths})
        
        # Fall back to live search
        result = await self._live_search(query)
        return ToolResult.ok(result.answer, metadata={"source": result.source, "file_paths": result.file_paths})
    
    def _load_index(self, index_path: Path) -> bool:
        """Load and validate the index file."""
        if not index_path.exists():
            logger.debug(f"Index not found: {index_path}")
            return False
        
        # Check freshness
        if self.generator.is_index_fresh(index_path):
            self._index_valid = True
        elif self.generator.is_index_stale(self.project_path, index_path):
            logger.debug("Index is stale (commit mismatch)")
            self._index_valid = False
        else:
            self._index_valid = True
        
        try:
            self._index_content = index_path.read_text(encoding="utf-8")
            return True
        except Exception as e:
            logger.error(f"Error reading index: {e}")
            return False
    
    def _answer_from_index(self, query: str) -> Optional[SearchResult]:
        """Try to answer the query from the index."""
        if not self._index_content:
            return None
        
        content = self._index_content.lower()
        
        # Test files query
        if any(kw in query for kw in ["test", "tests", "testing", "spec", "specs"]):
            return self._extract_test_info()
        
        # Entry points query
        if any(kw in query for kw in ["entry", "entry point", "main", "start", "run"]):
            return self._extract_entry_points()
        
        # Directory structure query
        if any(kw in query for kw in ["structure", "directory", "directories", "folders", "tree"]):
            return self._extract_directory_tree()
        
        # File count query
        if any(kw in query for kw in ["how many files", "file count", "file types", "extensions"]):
            return self._extract_file_counts()
        
        # npm scripts query
        if any(kw in query for kw in ["npm script", "scripts", "npm run"]):
            return self._extract_npm_scripts()
        
        # Python modules query
        if any(kw in query for kw in ["python module", "modules", "package", "packages"]):
            return self._extract_python_modules()
        
        # Database schema query
        if any(kw in query for kw in ["database", "schema", "table", "model", "sql"]):
            return self._extract_database_info()
        
        # Project type query
        if any(kw in query for kw in ["project type", "what kind of project", "stack", "technology"]):
            return self._extract_project_type()
        
        # Branch/commit query
        if any(kw in query for kw in ["branch", "commit", "git", "version"]):
            return self._extract_git_info()
        
        # Generic search in index
        return self._search_in_index(query)
    
    def _extract_section(self, section_name: str) -> Optional[str]:
        """Extract a section from the index content."""
        if not self._index_content:
            return None
        
        lines = self._index_content.split("\n")
        in_section = False
        section_lines = []
        
        for line in lines:
            if line.strip().startswith(f"## {section_name}"):
                in_section = True
                continue
            elif line.strip().startswith("## ") and in_section:
                break
            elif in_section:
                section_lines.append(line)
        
        return "\n".join(section_lines).strip() if section_lines else None
    
    def _extract_test_info(self) -> SearchResult:
        """Extract test file information."""
        section = self._extract_section("Test Files")
        if section:
            return SearchResult(
                source="index",
                query="test files",
                answer=f"Test files found:\n\n{section}",
                stale=not self._index_valid,
            )
        return SearchResult(
            source="index",
            query="test files",
            answer="No test files found in the index.",
        )
    
    def _extract_entry_points(self) -> SearchResult:
        """Extract entry point information."""
        section = self._extract_section("Entry Points")
        if section:
            return SearchResult(
                source="index",
                query="entry points",
                answer=f"Entry points:\n\n{section}",
                stale=not self._index_valid,
            )
        return SearchResult(
            source="index",
            query="entry points",
            answer="No entry points found in the index.",
        )
    
    def _extract_directory_tree(self) -> SearchResult:
        """Extract directory tree."""
        section = self._extract_section("Directory Tree")
        if section:
            return SearchResult(
                source="index",
                query="directory structure",
                answer=f"Directory structure:\n\n{section}",
                stale=not self._index_valid,
            )
        return SearchResult(
            source="index",
            query="directory structure",
            answer="No directory tree found in the index.",
        )
    
    def _extract_file_counts(self) -> SearchResult:
        """Extract file count information."""
        section = self._extract_section("File Counts by Extension")
        if section:
            return SearchResult(
                source="index",
                query="file counts",
                answer=f"File counts by extension:\n\n{section}",
                stale=not self._index_valid,
            )
        return SearchResult(
            source="index",
            query="file counts",
            answer="No file count information found in the index.",
        )
    
    def _extract_npm_scripts(self) -> SearchResult:
        """Extract npm script information."""
        section = self._extract_section("npm Scripts")
        if section:
            return SearchResult(
                source="index",
                query="npm scripts",
                answer=f"npm scripts:\n\n{section}",
                stale=not self._index_valid,
            )
        return SearchResult(
            source="index",
            query="npm scripts",
            answer="No npm scripts found (not a Node.js project or no scripts defined).",
        )
    
    def _extract_python_modules(self) -> SearchResult:
        """Extract Python module information."""
        section = self._extract_section("Python Modules")
        if section:
            return SearchResult(
                source="index",
                query="python modules",
                answer=f"Python modules:\n\n{section}",
                stale=not self._index_valid,
            )
        return SearchResult(
            source="index",
            query="python modules",
            answer="No Python modules found (not a Python project).",
        )
    
    def _extract_database_info(self) -> SearchResult:
        """Extract database schema information."""
        section = self._extract_section("Database Schema References")
        if section:
            return SearchResult(
                source="index",
                query="database schema",
                answer=f"Database schema references:\n\n{section}",
                stale=not self._index_valid,
            )
        return SearchResult(
            source="index",
            query="database schema",
            answer="No database schema references found in the index.",
        )
    
    def _extract_project_type(self) -> SearchResult:
        """Extract project type information."""
        if not self._index_content:
            return SearchResult(
                source="index",
                query="project type",
                answer="Unknown",
            )
        
        for line in self._index_content.split("\n"):
            if line.startswith("Project Type:"):
                project_type = line.split(":", 1)[1].strip()
                return SearchResult(
                    source="index",
                    query="project type",
                    answer=f"Project type: {project_type}",
                    stale=not self._index_valid,
                )
        
        return SearchResult(
            source="index",
            query="project type",
            answer="Project type not found in index.",
        )
    
    def _extract_git_info(self) -> SearchResult:
        """Extract git information."""
        if not self._index_content:
            return SearchResult(
                source="index",
                query="git info",
                answer="Unknown",
            )
        
        info = {}
        for line in self._index_content.split("\n"):
            if line.startswith("Branch:"):
                info["branch"] = line.split(":", 1)[1].strip()
            elif line.startswith("Commit:"):
                info["commit"] = line.split(":", 1)[1].strip()
            elif line.startswith("Last commit:"):
                info["last_commit"] = line.split(":", 1)[1].strip()
        
        if info:
            answer = "\n".join(f"{k}: {v}" for k, v in info.items())
            return SearchResult(
                source="index",
                query="git info",
                answer=f"Git information:\n{answer}",
                stale=not self._index_valid,
            )
        
        return SearchResult(
            source="index",
            query="git info",
            answer="Git information not found in index.",
        )
    
    def _search_in_index(self, query: str) -> Optional[SearchResult]:
        """Search for a term in the index content."""
        if not self._index_content:
            return None
        
        # Simple text search
        query_terms = query.lower().split()
        matching_lines = []
        
        for line in self._index_content.split("\n"):
            line_lower = line.lower()
            if any(term in line_lower for term in query_terms):
                matching_lines.append(line)
        
        if matching_lines:
            return SearchResult(
                source="index",
                query=query,
                answer=f"Found {len(matching_lines)} matching lines:\n\n" + "\n".join(matching_lines[:20]),
                stale=not self._index_valid,
            )
        
        return None
    
    async def _live_search(self, query: str) -> SearchResult:
        """Fall back to live search when index is unavailable."""
        logger.info(f"Falling back to live search for: {query}")
        
        # Generate index on the fly
        try:
            index = self.generator.generate(self.project_path)
            self._index_content = self.generator.format_index(index)
            self._index_valid = True
            
            # Try to answer from the newly generated index
            result = self._answer_from_index(query)
            if result:
                result.source = "live"
                return result
            
        except Exception as e:
            logger.error(f"Error generating index: {e}")
        
        return SearchResult(
            source="live",
            query=query,
            answer=f"Could not find information about '{query}' in the project.",
            confidence=0.5,
        )
    
    def get_index_summary(self) -> Dict[str, Any]:
        """Get a summary of the current index."""
        if not self._index_content:
            return {"status": "no_index"}
        
        summary = {
            "status": "valid" if self._index_valid else "stale",
            "has_index": True,
        }
        
        for line in self._index_content.split("\n"):
            if line.startswith("Project Type:"):
                summary["project_type"] = line.split(":", 1)[1].strip()
            elif line.startswith("Branch:"):
                summary["branch"] = line.split(":", 1)[1].strip()
            elif line.startswith("Commit:"):
                summary["commit"] = line.split(":", 1)[1].strip()
        
        return summary


# Tool registration
def get_explore_tool(project_path: Optional[Path] = None) -> ExploreTool:
    """Get an instance of the explore tool."""
    return ExploreTool(project_path)
