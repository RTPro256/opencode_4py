# Test Maintenance Guidelines

> **Navigation:** [TESTING_PLAN.md](../plans/TESTING_PLAN.md) - Main testing strategy overview

This document provides guidelines for maintaining and extending the test suite for the OpenCode Python project.

---

## Adding New Tests

When adding new features, follow these guidelines:

### Unit Tests

Add to `tests/unit/` directory:
- Test individual functions/methods in isolation
- Mock external dependencies
- Aim for >90% code coverage on new code

### Integration Tests

Add to `tests/integration/`:
- Test component interactions
- Use real databases/filesystems when possible
- Clean up resources after tests

### Provider Tests

Add to `tests/providers/`:
- Test provider-specific behavior
- Include both mock and real tests
- Handle API rate limits gracefully

### Prompt Tests

Add to `tests/prompts/`:
- Use standardized test sets
- Document expected behavior
- Track accuracy metrics over time

---

## Test Naming Conventions

### Test File Naming

```python
test_<module_name>.py           # Unit tests for a module
test_<module_name>_integration.py  # Integration tests
```

### Test Class Naming

```python
class Test<FeatureName>:        # Tests for a specific feature
class Test<ClassName>:          # Tests for a specific class
```

### Test Method Naming

```python
def test_<action>_<expected_result>():
    """Test description."""
    pass

# Examples
def test_add_file_updates_context():
    """Test that adding a file updates the context tracker."""
    pass

def test_ollama_connection_fails_gracefully():
    """Test that Ollama connection failures are handled gracefully."""
    pass
```

---

## Test Data Management

### Centralized Test Data

```python
# tests/fixtures/test_data.py
"""
Centralized test data management.

Use this module to manage test data that can be updated
without changing test code.
"""

from pathlib import Path
import json

FIXTURES_DIR = Path(__file__).parent

def load_test_prompts() -> dict:
    """Load test prompts from JSON file."""
    with open(FIXTURES_DIR / "test_prompts.json") as f:
        return json.load(f)

def load_expected_responses() -> dict:
    """Load expected responses for validation."""
    with open(FIXTURES_DIR / "expected_responses.json") as f:
        return json.load(f)
```

---

## Monitoring and Reporting

### Test Metrics Dashboard

Track the following metrics:
- Test pass/fail rates by category
- Code coverage trends
- Prompt accuracy by model
- Test execution time trends
- Flaky test identification

### Accuracy Tracking

```python
# tests/utils/accuracy_tracker.py
"""
Track prompt accuracy over time.
"""

import json
from datetime import datetime
from pathlib import Path

class AccuracyTracker:
    """Track and store accuracy metrics."""
    
    def __init__(self, storage_dir: Path = None):
        self.storage_dir = storage_dir or Path("test_results/accuracy")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def record_result(
        self,
        test_name: str,
        model: str,
        accuracy: float,
        latency_ms: float,
    ):
        """Record a test result."""
        today = datetime.now().strftime("%Y-%m-%d")
        file_path = self.storage_dir / f"{today}.json"
        
        data = {}
        if file_path.exists():
            with open(file_path) as f:
                data = json.load(f)
        
        if test_name not in data:
            data[test_name] = {}
        
        data[test_name][model] = {
            "accuracy": accuracy,
            "latency_ms": latency_ms,
            "timestamp": datetime.now().isoformat(),
        }
        
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
```

---

## Related Documentation

- [TESTING_INFRASTRUCTURE.md](TESTING_INFRASTRUCTURE.md) - Test directory structure and configuration
- [CI_CD_TESTING.md](CI_CD_TESTING.md) - CI/CD configuration
- [TEST_DISCOVERY.md](TEST_DISCOVERY.md) - Test discovery commands
