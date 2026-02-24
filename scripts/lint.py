#!/usr/bin/env python3
"""
Run linting and type checking for OpenCode Python.

Usage:
    python scripts/lint.py
    python scripts/lint.py --fix
    python scripts/lint.py --mypy
    python scripts/lint.py --ruff
"""

import subprocess
import sys
from pathlib import Path


def run_ruff(fix: bool = False) -> int:
    """Run ruff linter."""
    cmd = ["ruff", "check", "src/opencode/src/opencode"]
    if fix:
        cmd.append("--fix")
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode


def run_ruff_format(check: bool = True) -> int:
    """Run ruff formatter."""
    cmd = ["ruff", "format", "src/opencode/src/opencode"]
    if check:
        cmd.append("--check")
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode


def run_mypy() -> int:
    """Run mypy type checker."""
    cmd = [
        "mypy",
        "src/opencode/src/opencode",
        "--ignore-missing-imports",
        "--no-error-summary",
    ]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode


def main() -> int:
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run linting for OpenCode")
    parser.add_argument("--fix", action="store_true", help="Auto-fix linting issues")
    parser.add_argument("--mypy", action="store_true", help="Run mypy only")
    parser.add_argument("--ruff", action="store_true", help="Run ruff only")
    parser.add_argument("--format", action="store_true", help="Run formatter only")
    
    args = parser.parse_args()
    
    exit_code = 0
    
    if args.mypy:
        exit_code = run_mypy()
    elif args.ruff:
        exit_code = run_ruff(args.fix)
    elif args.format:
        exit_code = run_ruff_format(check=not args.fix)
    else:
        # Run all checks
        print("=== Running Ruff Linter ===")
        exit_code |= run_ruff(args.fix)
        
        print("\n=== Running Ruff Formatter ===")
        exit_code |= run_ruff_format(check=not args.fix)
        
        print("\n=== Running Mypy ===")
        exit_code |= run_mypy()
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())