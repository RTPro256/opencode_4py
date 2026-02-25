# ERR-004: Missing Pre-flight Checks

## Metadata
- **Error ID**: ERR-004
- **Category**: Integration
- **Severity**: Medium
- **Status**: Fixed
- **Date Encountered**: 2026-02-23
- **Related Errors**: ERR-003

## Symptom
Integration fails with cryptic errors because prerequisites were not verified before attempting to run.

## Root Cause
No verification of prerequisites before attempting to run. Missing pre-flight checks with clear error messages.

## Fix
Created `check_prerequisites.py` with comprehensive checks:

```python
#!/usr/bin/env python3
"""Pre-flight checks for OpenCode integration."""

import sys
from pathlib import Path

def check_python_version():
    """Check Python version is 3.10+."""
    version = sys.version_info
    if version < (3, 10):
        print(f"❌ Python 3.10+ required, found {version.major}.{version.minor}")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_ollama():
    """Check Ollama is running and has models."""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            if models:
                print(f"✓ Ollama running with {len(models)} model(s)")
                return True
            else:
                print("⚠ Ollama running but no models installed")
                return False
    except Exception as e:
        print(f"❌ Ollama not available: {e}")
        return False

def check_config():
    """Check configuration file exists."""
    config_path = Path.home() / ".config" / "opencode" / "config.yaml"
    if config_path.exists():
        print(f"✓ Config found at {config_path}")
        return True
    else:
        print(f"⚠ No config at {config_path}")
        return False

def main():
    """Run all pre-flight checks."""
    print("Running pre-flight checks...\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("Ollama", check_ollama),
        ("Configuration", check_config),
    ]
    
    results = []
    for name, check in checks:
        print(f"\n{name}:")
        results.append(check())
    
    print("\n" + "="*50)
    if all(results):
        print("✓ All checks passed!")
        return 0
    else:
        print("⚠ Some checks failed. Review above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

## Verification
```bash
python check_prerequisites.py
```

## Lesson Learned
Always include pre-flight checks with clear error messages.

## Prevention
- Create pre-flight check script for all integrations
- Run checks before main application starts
- Provide clear guidance for resolving failures
