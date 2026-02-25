# Testing Infrastructure

> **Navigation:** [TESTING_PLAN.md](../plans/TESTING_PLAN.md) - Main testing strategy overview

This document describes the testing infrastructure for the OpenCode Python project, including directory structure and configuration.

---

## Test Directory Structure

```
src/opencode/tests/
├── conftest.py                    # Shared fixtures and configuration
├── unit/                          # Unit tests
│   ├── test_context.py
│   ├── test_orchestration.py
│   ├── test_subagents.py
│   ├── test_rag.py
│   ├── test_workflow/
│   ├── test_provider/
│   └── test_tools/
├── integration/                   # Integration tests
│   ├── test_session_flow.py
│   ├── test_workflow_execution.py
│   └── test_mcp_integration.py
├── providers/                     # Provider-specific tests
│   ├── test_provider_base.py
│   ├── test_ollama_provider.py
│   ├── test_openai_provider.py
│   └── test_anthropic_provider.py
├── prompts/                       # Prompt evaluation tests
│   ├── test_prompt_comparison.py
│   ├── test_prompt_accuracy.py
│   └── prompt_fixtures/
├── ollama/                        # Ollama-specific tests
│   ├── test_ollama_integration.py
│   ├── test_ollama_accuracy.py
│   └── test_ollama_troubleshooting.py
├── e2e/                           # End-to-end tests
│   ├── test_cli_commands.py
│   ├── test_tui_flow.py
│   └── test_server_api.py
└── performance/                   # Performance tests
    ├── test_context_truncation_perf.py
    └── test_workflow_execution_perf.py
```

---

## Test Configuration

### conftest.py

```python
# conftest.py
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

# Provider fixtures
@pytest.fixture
def mock_httpx_client():
    """Mock httpx client for provider tests."""
    client = AsyncMock()
    return client

@pytest.fixture
def ollama_available():
    """Check if Ollama is available locally."""
    import httpx
    try:
        response = httpx.get("http://localhost:11434/api/tags", timeout=2.0)
        return response.status_code == 200
    except:
        return False

@pytest.fixture
def skip_if_no_ollama(ollama_available):
    """Skip test if Ollama is not available."""
    if not ollama_available:
        pytest.skip("Ollama not available")

# Model fixtures
@pytest.fixture
def test_models():
    """Models to test across providers."""
    return {
        "ollama": ["llama3.2:3b", "llama3.1:8b", "qwen2.5:7b"],
        "openai": ["gpt-4o-mini", "gpt-4o"],
        "anthropic": ["claude-3-5-sonnet-20241022"],
    }

# Prompt fixtures
@pytest.fixture
def test_prompts():
    """Standard test prompts for evaluation."""
    return {
        "simple": "What is 2 + 2?",
        "code": "Write a Python function to calculate fibonacci numbers.",
        "reasoning": "If all roses are flowers, and some flowers are red, can we conclude that some roses are red? Explain your reasoning.",
        "creative": "Write a haiku about programming.",
        "tool_use": "What is the weather in Tokyo?",
    }
```

---

## Related Documentation

- [PROMPT_TESTING.md](PROMPT_TESTING.md) - Prompt comparison and accuracy tests
- [OLLAMA_TESTING.md](OLLAMA_TESTING.md) - Ollama integration tests
- [CI_CD_TESTING.md](CI_CD_TESTING.md) - CI/CD configuration
- [TEST_MAINTENANCE_GUIDE.md](TEST_MAINTENANCE_GUIDE.md) - Test maintenance guidelines
- [TEST_DISCOVERY.md](TEST_DISCOVERY.md) - Test discovery commands
