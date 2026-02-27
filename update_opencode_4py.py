#!/usr/bin/env python3
"""
OpenCode_4py Update Script

This script updates the opencode_4py installation in a for_testing target.
It reinstalls from the source code to ensure all changes are propagated.

Usage:
    python update_opencode_4py.py [--source PATH] [--target PATH]

Related Documents:
- README.md - Project overview and features
- MISSION.md - Mission statement and core principles
"""

import argparse
import subprocess
import sys
from pathlib import Path


def get_default_source() -> Path:
    """Get the default source path (project root)."""
    # Navigate up from this script's location to find project root
    script_path = Path(__file__).resolve()
    # This script is in for_testing/as_dependency/ComfyUI_windows_portable/
    # Project root is 4 levels up
    return script_path.parents[4] / "src" / "opencode"


def get_default_target() -> Path:
    """Get the default target path (embedded Python site-packages)."""
    script_path = Path(__file__).resolve()
    # This script is in for_testing/as_dependency/ComfyUI_windows_portable/
    return script_path.parent / "python_embeded" / "Lib" / "site-packages" / "opencode"


def update_opencode(source: Path, target: Path, python_exe: Path) -> bool:
    """
    Update opencode_4py installation.
    
    Args:
        source: Path to source opencode package
        target: Path to target site-packages
        python_exe: Path to Python executable
        
    Returns:
        True if successful, False otherwise
    """
    print(f"Updating opencode_4py...")
    print(f"  Source: {source}")
    print(f"  Target: {target}")
    print(f"  Python: {python_exe}")
    
    # Check source exists
    if not source.exists():
        print(f"ERROR: Source path does not exist: {source}")
        return False
    
    # Check pyproject.toml exists
    pyproject = source / "pyproject.toml"
    if not pyproject.exists():
        print(f"ERROR: pyproject.toml not found in source: {pyproject}")
        return False
    
    # Uninstall existing version
    print("\n[1/3] Uninstalling existing opencode_4py...")
    subprocess.run(
        [str(python_exe), "-m", "pip", "uninstall", "-y", "opencode"],
        capture_output=True,
        text=True
    )
    
    # Install from source
    print("\n[2/3] Installing opencode_4py from source...")
    result = subprocess.run(
        [str(python_exe), "-m", "pip", "install", "-e", str(source)],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"ERROR: Installation failed:\n{result.stderr}")
        return False
    
    print("Installation successful!")
    
    # Verify installation
    print("\n[3/3] Verifying installation...")
    result = subprocess.run(
        [str(python_exe), "-c", "import opencode; print(opencode.__version__)"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"WARNING: Could not verify version: {result.stderr}")
    else:
        print(f"Installed version: {result.stdout.strip()}")
    
    # Copy README.md and MISSION.md to target docs
    print("\n[4/4] Copying documentation...")
    docs_target = target / "docs"
    docs_target.mkdir(parents=True, exist_ok=True)
    
    project_root = source.parents[1]  # Go up from src/opencode to project root
    readme_source = project_root / "README.md"
    mission_source = project_root / "MISSION.md"
    
    if readme_source.exists():
        (docs_target / "README.md").write_text(readme_source.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"  Copied: README.md")
    
    if mission_source.exists():
        (docs_target / "MISSION.md").write_text(mission_source.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"  Copied: MISSION.md")
    
    print("\n✅ Update complete!")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Update opencode_4py in for_testing target",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Update with default paths
    python update_opencode_4py.py
    
    # Update with custom paths
    python update_opencode_4py.py --source /path/to/src/opencode --target /path/to/site-packages
"""
    )
    
    parser.add_argument(
        "--source",
        type=Path,
        default=get_default_source(),
        help="Path to source opencode package (default: project src/opencode)"
    )
    
    parser.add_argument(
        "--target",
        type=Path,
        default=get_default_target(),
        help="Path to target site-packages (default: embedded Python site-packages)"
    )
    
    parser.add_argument(
        "--python",
        type=Path,
        default=None,
        help="Path to Python executable (default: embedded Python)"
    )
    
    args = parser.parse_args()
    
    # Determine Python executable
    if args.python:
        python_exe = args.python
    else:
        # Use embedded Python
        script_path = Path(__file__).resolve()
        python_exe = script_path.parent / "python_embeded" / "python.exe"
    
    if not python_exe.exists():
        print(f"ERROR: Python executable not found: {python_exe}")
        sys.exit(1)
    
    success = update_opencode(args.source, args.target, python_exe)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
