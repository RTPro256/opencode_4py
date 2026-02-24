#!/usr/bin/env python3
"""
Clean up generated files for OpenCode Python.

Usage:
    python scripts/clean.py
    python scripts/clean.py --all
    python scripts/clean.py --cache
    python scripts/clean.py --coverage
"""

import shutil
import sys
from pathlib import Path


def remove_path(path: Path) -> None:
    """Remove a file or directory."""
    if path.exists():
        if path.is_dir():
            shutil.rmtree(path)
            print(f"Removed directory: {path}")
        else:
            path.unlink()
            print(f"Removed file: {path}")


def clean_cache() -> None:
    """Clean Python cache files."""
    root = Path(".")
    
    # Remove __pycache__ directories
    for pycache in root.rglob("__pycache__"):
        remove_path(pycache)
    
    # Remove .pyc files
    for pyc in root.rglob("*.pyc"):
        remove_path(pyc)
    
    # Remove .pyo files
    for pyo in root.rglob("*.pyo"):
        remove_path(pyo)
    
    # Remove .pytest_cache
    pytest_cache = root / ".pytest_cache"
    remove_path(pytest_cache)
    
    # Remove pytest cache in src/opencode
    src_cache = Path("src/opencode/.pytest_cache")
    remove_path(src_cache)
    
    # Remove mypy cache
    for mypy_cache in root.rglob(".mypy_cache"):
        remove_path(mypy_cache)
    
    # Remove ruff cache
    for ruff_cache in root.rglob(".ruff_cache"):
        remove_path(ruff_cache)


def clean_coverage() -> None:
    """Clean coverage reports."""
    root = Path(".")
    
    # Remove .coverage file
    coverage_file = root / ".coverage"
    remove_path(coverage_file)
    
    # Remove coverage in src/opencode
    src_coverage = Path("src/opencode/.coverage")
    remove_path(src_coverage)
    
    # Remove htmlcov directories
    for htmlcov in root.rglob("htmlcov"):
        remove_path(htmlcov)
    
    # Remove .coverage.* files
    for cov in root.rglob(".coverage.*"):
        remove_path(cov)


def clean_build() -> None:
    """Clean build artifacts."""
    root = Path(".")
    
    # Remove dist directories
    for dist in root.rglob("dist"):
        remove_path(dist)
    
    # Remove build directories
    for build in root.rglob("build"):
        remove_path(build)
    
    # Remove egg-info directories
    for egg_info in root.rglob("*.egg-info"):
        remove_path(egg_info)
    
    # Remove .eggs
    for eggs in root.rglob(".eggs"):
        remove_path(eggs)


def clean_all() -> None:
    """Clean all generated files."""
    clean_cache()
    clean_coverage()
    clean_build()


def main() -> int:
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean generated files")
    parser.add_argument("--all", action="store_true", help="Clean all generated files")
    parser.add_argument("--cache", action="store_true", help="Clean cache files only")
    parser.add_argument("--coverage", action="store_true", help="Clean coverage reports only")
    parser.add_argument("--build", action="store_true", help="Clean build artifacts only")
    
    args = parser.parse_args()
    
    if args.all:
        clean_all()
    elif args.cache:
        clean_cache()
    elif args.coverage:
        clean_coverage()
    elif args.build:
        clean_build()
    else:
        # Default: clean cache and coverage
        clean_cache()
        clean_coverage()
    
    print("Clean complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())