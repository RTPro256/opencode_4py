#!/usr/bin/env python3
"""
Run tests with coverage for OpenCode Python.

Usage:
    python scripts/run_tests.py
    python scripts/run_tests.py --unit
    python scripts/run_tests.py --integration
    python scripts/run_tests.py --coverage
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], cwd: Path | None = None) -> int:
    """Run a command and return the exit code."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    return result.returncode


def run_unit_tests(coverage: bool = False) -> int:
    """Run unit tests."""
    cmd = ["pytest", "src/opencode/src/opencode/tests/unit", "-v"]
    if coverage:
        cmd.extend(["--cov=opencode", "--cov-report=html", "--cov-report=term"])
    return run_command(cmd, Path("src/opencode"))


def run_integration_tests(coverage: bool = False) -> int:
    """Run integration tests."""
    cmd = ["pytest", "src/opencode/src/opencode/tests/integration", "-v"]
    if coverage:
        cmd.extend(["--cov=opencode", "--cov-report=html", "--cov-report=term"])
    return run_command(cmd, Path("src/opencode"))


def run_all_tests(coverage: bool = False) -> int:
    """Run all tests."""
    cmd = ["pytest", "src/opencode/src/opencode/tests", "-v"]
    if coverage:
        cmd.extend(["--cov=opencode", "--cov-report=html", "--cov-report=term"])
    return run_command(cmd, Path("src/opencode"))


def main() -> int:
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run OpenCode tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    
    args = parser.parse_args()
    
    if args.unit:
        return run_unit_tests(args.coverage)
    elif args.integration:
        return run_integration_tests(args.coverage)
    else:
        return run_all_tests(args.coverage)


if __name__ == "__main__":
    sys.exit(main())