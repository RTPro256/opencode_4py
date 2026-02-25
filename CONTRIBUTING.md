# Contributing to OpenCode Python

Thank you for your interest in contributing to OpenCode Python! This document provides guidelines and instructions for contributing.

> 📜 **Important:** Please read our [Mission Statement](MISSION.md) to understand the core principles that guide this project. All contributions should align with these values.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)

---

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment. Please be considerate of others and follow standard open-source community guidelines.

---

## Getting Started

### Prerequisites

- Python 3.12 or higher
- Git
- A code editor (VS Code recommended)
- Basic familiarity with async Python

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:

```bash
git clone https://github.com/YOUR_USERNAME/opencode_4py.git
cd opencode_4py
```

3. Add the upstream remote:

```bash
git remote add upstream https://github.com/RTPro256/opencode_4py.git
```

---

## Development Setup

### Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows
```

### Install Dependencies

```bash
# Install in development mode
pip install -e ".[dev]"

# Or with all optional dependencies
pip install -e ".[dev,test,docs]"
```

### Set Up Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/opencode

# Run specific test file
pytest tests/test_providers.py

# Run specific test
pytest tests/test_providers.py::test_anthropic_provider
```

### Run Linting

```bash
# Run ruff
ruff check src/

# Format code
ruff format src/

# Type check
mypy src/
```

---

## Project Structure

```
opencode_4py/
├── src/opencode/
│   ├── __init__.py          # Package initialization
│   ├── __main__.py          # Entry point for python -m opencode
│   ├── cli/                  # CLI commands
│   │   ├── __init__.py
│   │   ├── main.py          # Main CLI entry point
│   │   ├── commands.py      # Individual commands
│   │   └── completion.py    # Shell completion
│   ├── core/                 # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py        # Configuration management
│   │   ├── session.py       # Session management
│   │   ├── database.py      # Database layer
│   │   └── logging.py       # Logging setup
│   ├── providers/            # AI providers
│   │   ├── __init__.py
│   │   ├── base.py          # Abstract provider class
│   │   ├── anthropic.py     # Anthropic/Claude
│   │   ├── openai.py        # OpenAI/GPT
│   │   ├── google.py        # Google/Gemini
│   │   └── ...              # Other providers
│   ├── tools/                # Built-in tools
│   │   ├── __init__.py
│   │   ├── base.py          # Abstract tool class
│   │   ├── registry.py      # Tool registry
│   │   ├── bash.py          # Shell execution
│   │   ├── read.py          # File reading
│   │   └── ...              # Other tools
│   ├── lsp/                  # Language Server Protocol
│   │   ├── __init__.py
│   │   ├── client.py        # LSP client
│   │   ├── manager.py       # Server management
│   │   └── languages/       # Language configs
│   ├── mcp/                  # Model Context Protocol
│   │   ├── __init__.py
│   │   ├── client.py        # MCP client
│   │   ├── server.py        # MCP server mode
│   │   └── oauth.py         # OAuth flow
│   ├── tui/                  # Terminal UI (Textual)
│   │   ├── __init__.py
│   │   ├── app.py           # Main TUI app
│   │   ├── screens/         # TUI screens
│   │   └── widgets/         # TUI widgets
│   ├── web/                  # Web interface
│   │   ├── __init__.py
│   │   ├── app.py           # FastAPI app
│   │   ├── routes/          # API routes
│   │   └── static/          # Static files
│   ├── i18n/                 # Internationalization
│   │   ├── __init__.py
│   │   ├── manager.py       # I18n manager
│   │   └── locales/         # Translation files
│   └── git/                  # Git integration
│       ├── __init__.py
│       └── operations.py    # Git operations
├── tests/                    # Test suite
│   ├── conftest.py          # Pytest fixtures
│   ├── test_providers.py
│   ├── test_tools.py
│   └── ...
├── docs/                     # Documentation
│   ├── README.md            # Full documentation
│   ├── FEATURE_COVERAGE.md  # Feature status
│   └── MIGRATION_PLAN.md    # Implementation plan
├── pyproject.toml           # Project configuration
├── README.md                # Project README
├── CHANGELOG.md             # Version history
└── CONTRIBUTING.md          # This file
```

---

## Coding Standards

### Python Style

- Follow [PEP 8](https://peps.python.org/pep-0008/) style guidelines
- Use [Ruff](https://docs.astral.sh/ruff/) for linting and formatting
- Maximum line length: 100 characters
- Use type hints for all public functions

### Code Organization

```python
# Good: Clear imports with explicit names
from opencode.providers.base import Provider, StreamChunk
from opencode.core.config import Config

# Bad: Wildcard imports
from opencode.providers.base import *

# Good: Async context managers
async with provider as p:
    response = await p.complete(messages)

# Good: Type hints
async def process_file(path: Path, encoding: str = "utf-8") -> str:
    """Process a file and return its contents.
    
    Args:
        path: Path to the file
        encoding: File encoding (default: utf-8)
    
    Returns:
        File contents as string
    
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    ...
```

### Naming Conventions

- **Classes**: PascalCase (`AnthropicProvider`, `ToolRegistry`)
- **Functions/Methods**: snake_case (`get_completion`, `execute_tool`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_TOKENS`, `DEFAULT_TIMEOUT`)
- **Private members**: Leading underscore (`_internal_state`)
- **Async functions**: No special prefix, just `async def`

### Error Handling

```python
# Good: Specific exceptions with context
try:
    result = await provider.complete(messages)
except ProviderError as e:
    logger.error(f"Provider failed: {e}")
    raise CompletionError(f"Failed to get completion: {e}") from e

# Good: Use context managers
async with aiofiles.open(path, "r") as f:
    content = await f.read()
```

### Documentation

- Use docstrings for all public modules, classes, and functions
- Follow Google-style docstrings:

```python
def calculate_tokens(text: str, model: str) -> int:
    """Calculate the number of tokens for a given text.
    
    Uses the appropriate tokenizer for the specified model.
    
    Args:
        text: The text to tokenize
        model: The model name (e.g., "gpt-4o", "claude-3-opus")
    
    Returns:
        The number of tokens in the text
    
    Example:
        >>> calculate_tokens("Hello, world!", "gpt-4o")
        4
    
    Note:
        Different models use different tokenizers.
    """
    ...
```

---

## Testing

### Documentation Requirement for Project Plans

**All project plans must maintain accompanying markdown documentation.**

When creating or modifying project plans in the `plans/` directory:

1. **Create a corresponding markdown file** in `docs/` that explains:
   - The purpose and scope of the plan
   - Implementation details and decisions
   - Progress tracking and status

2. **Keep documentation in sync** with plan changes:
   - Update documentation when plans are modified
   - Mark completed items in both the plan and documentation
   - Archive obsolete plans with corresponding documentation

3. **Follow the naming convention**:
   - Plan file: `plans/PLAN_NAME.md`
   - Documentation: `docs/PLAN_NAME.md` or relevant section in existing docs

Example:
```
plans/
├── TESTING_PLAN.md          # Testing strategy and progress
├── PLAN_ACTIVATION.md       # Activation workflows
└── MIGRATION_PLAN.md        # Migration details

docs/
├── TESTING_PLAN.md          # Testing documentation (if detailed)
├── FEATURE_COVERAGE.md      # Feature status (updated from plans)
└── MIGRATION_PLAN.md        # Migration documentation
```

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_providers/          # Provider tests
│   ├── test_anthropic.py
│   ├── test_openai.py
│   └── ...
├── test_tools/              # Tool tests
│   ├── test_bash.py
│   ├── test_read.py
│   └── ...
├── test_core/               # Core tests
│   ├── test_config.py
│   └── test_session.py
└── integration/             # Integration tests
    └── test_full_flow.py
```

### Writing Tests

```python
import pytest
from unittest.mock import AsyncMock, patch

from opencode.providers.anthropic import AnthropicProvider


@pytest.fixture
def mock_anthropic_response():
    return {
        "content": [{"type": "text", "text": "Hello!"}],
        "usage": {"input_tokens": 10, "output_tokens": 5}
    }


@pytest.mark.asyncio
async def test_anthropic_complete(mock_anthropic_response):
    """Test that Anthropic provider returns correct response."""
    provider = AnthropicProvider(api_key="test-key")
    
    with patch.object(
        provider, "_make_request", 
        new_callable=AsyncMock,
        return_value=mock_anthropic_response
    ):
        response = await provider.complete([{"role": "user", "content": "Hi"}])
    
    assert response.content == "Hello!"
    assert response.input_tokens == 10
    assert response.output_tokens == 5
```

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_providers/test_anthropic.py

# Run with coverage
pytest --cov=src/opencode --cov-report=html

# Run only unit tests (skip integration)
pytest -m "not integration"

# Run only integration tests
pytest -m integration
```

---

## Pull Request Process

### Before Submitting

1. **Update from upstream**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run tests**:
   ```bash
   pytest
   ```

3. **Run linting**:
   ```bash
   ruff check src/
   ruff format src/
   mypy src/
   ```

4. **Update documentation** if needed

### Submitting

1. Create a feature branch:
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. Make your changes and commit:
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

3. Push to your fork:
   ```bash
   git push origin feature/my-new-feature
   ```

4. Open a Pull Request on GitHub

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions/changes
- `refactor:` Code refactoring
- `perf:` Performance improvements
- `chore:` Maintenance tasks

Examples:
```
feat: add support for Cerebras provider
fix: handle empty response from OpenAI
docs: update installation instructions
test: add tests for context compaction
```

### PR Review Process

1. All PRs require at least one review
2. CI tests must pass
3. Code coverage should not decrease
4. Documentation must be updated for new features

---

## Reporting Issues

### Bug Reports

When reporting bugs, please include:

1. **Description**: Clear description of the bug
2. **Steps to Reproduce**: Minimal code example
3. **Expected Behavior**: What you expected to happen
4. **Actual Behavior**: What actually happened
5. **Environment**: OS, Python version, package versions
6. **Logs**: Relevant log output (with sensitive info removed)

### Feature Requests

For feature requests, please include:

1. **Description**: Clear description of the feature
2. **Use Case**: Why this feature would be useful
3. **Proposed Solution**: If you have ideas for implementation
4. **Alternatives**: Other solutions you've considered

### Issue Template

```markdown
## Description
[Clear description of the issue]

## Steps to Reproduce
1. [First step]
2. [Second step]
3. [Third step]

## Expected Behavior
[What you expected]

## Actual Behavior
[What actually happened]

## Environment
- OS: [e.g., macOS 14.0]
- Python: [e.g., 3.12.0]
- OpenCode: [e.g., 1.0.0]

## Logs
```
[Paste relevant logs here]
```

## Additional Context
[Any other context about the problem]
```

---

## Getting Help

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Code Review**: Tag maintainers for review

---

## License

By contributing to OpenCode Python, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing! 🎉
