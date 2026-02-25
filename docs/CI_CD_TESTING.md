# CI/CD Testing Configuration

> **Navigation:** [TESTING_PLAN.md](../plans/TESTING_PLAN.md) - Main testing strategy overview

This document describes the CI/CD configuration for automated testing, including pytest configuration and GitHub Actions workflows.

---

## pytest Configuration

```toml
# pyproject.toml - test configuration

[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
asyncio_mode = "auto"
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "ollama: marks tests requiring Ollama",
    "provider: marks tests requiring external providers",
    "prompt: marks prompt evaluation tests",
]
filterwarnings = [
    "ignore::DeprecationWarning",
]
addopts = [
    "-ra",
    "-q",
    "--strict-markers",
    "--strict-config",
]
log_cli = true
log_cli_level = "INFO"

[tool.coverage.run]
source = ["src/opencode"]
branch = true
omit = [
    "*/tests/*",
    "*/__main__.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
]
fail_under = 70
```

---

## GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install -e .[dev]
      - name: Run unit tests
        run: pytest tests/unit -v --cov

  integration-tests:
    runs-on: ubuntu-latest
    services:
      ollama:
        image: ollama/ollama
        ports:
          - 11434:11434
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -e .[dev]
      - name: Pull Ollama model
        run: ollama pull llama3.2:3b
      - name: Run integration tests
        run: pytest tests/integration tests/ollama -v -m "not slow"

  prompt-tests:
    runs-on: ubuntu-latest
    services:
      ollama:
        image: ollama/ollama
        ports:
          - 11434:11434
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -e .[dev]
      - name: Pull Ollama model
        run: ollama pull llama3.2:3b
      - name: Run prompt tests
        run: pytest tests/prompts -v
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

---

## Test Priority Matrix

| Priority | Test Type | Frequency | Automation |
|----------|-----------|-----------|------------|
| P0 | Unit Tests | Every commit | Full |
| P0 | Provider Tests | Every commit | Full (mock) |
| P1 | Integration Tests | Every PR | Full |
| P1 | Ollama Tests | Every PR | Full |
| P2 | Prompt Comparison | Weekly | Partial |
| P2 | Accuracy Benchmarks | Weekly | Full |
| P3 | E2E Tests | Release | Manual trigger |

---

## Related Documentation

- [TESTING_INFRASTRUCTURE.md](TESTING_INFRASTRUCTURE.md) - Test directory structure and configuration
- [PROMPT_TESTING.md](PROMPT_TESTING.md) - Prompt comparison and accuracy tests
- [OLLAMA_TESTING.md](OLLAMA_TESTING.md) - Ollama integration tests
- [TEST_DISCOVERY.md](TEST_DISCOVERY.md) - Test discovery commands
