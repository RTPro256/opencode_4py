"""
Run all User Acceptance Tests.

This script runs all UAT test scripts for the OpenCode project.
Run: python scripts/run_uat.py
"""

import subprocess
import sys
from pathlib import Path


def run_uat_script(script_path: Path) -> tuple[bool, str]:
    """Run a UAT script and return success status and output."""
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        cwd=script_path.parent.parent,  # Run from project root
    )
    return result.returncode == 0, result.stdout + result.stderr


def main():
    """Run all UAT tests."""
    print("=" * 60)
    print("OpenCode User Acceptance Testing Suite")
    print("=" * 60)
    
    scripts_dir = Path(__file__).parent / "uat"
    
    # Find all UAT test scripts
    uat_scripts = sorted(scripts_dir.glob("test_*.py"))
    
    if not uat_scripts:
        print("No UAT test scripts found in scripts/uat/")
        return False
    
    results = []
    
    for script in uat_scripts:
        print(f"\n{'=' * 60}")
        print(f"Running: {script.name}")
        print("=" * 60)
        
        success, output = run_uat_script(script)
        print(output)
        
        results.append((script.name, success))
    
    # Summary
    print("\n" + "=" * 60)
    print("UAT Suite Summary")
    print("=" * 60)
    
    passed = sum(1 for _, s in results if s)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {name}: {status}")
    
    print(f"\nTotal: {passed}/{total} test suites passed")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
