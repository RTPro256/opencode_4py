# Project Organization Plan for OpenCode Python

> *"Organization is not about perfection; it's about efficiency, reducing errors, and not losing your mind when you need to find that one file you wrote six months ago."*

## Overview

This plan establishes a comprehensive organization strategy for the OpenCode Python project. It defines the project structure, naming conventions, module organization, and processes to ensure the codebase remains maintainable and scalable as the project grows.

> **Related Documents:**
> - [README.md](../README.md) - Project overview and features
> - [MISSION.md](../MISSION.md) - Mission statement and core principles

---

## Current Project Structure

```
opencode_4py/
├── .gitignore
├── CHANGELOG.md
├── CONTRIBUTING.md
├── README.md
├── docs/
│   ├── FEATURE_COVERAGE.md
│   ├── IMPLEMENTATION_STATUS.md
│   ├── INTEGRATION_FEATURE_COVERAGE.md
│   ├── MIGRATION_PLAN.md
│   └── README.md
├── plans/
│   ├── CODE_IMPROVEMENT_PLAN.md
│   ├── DOCUMENTATION_PLAN.md
│   └── TESTING_PLAN.md
├── src/
│   └── opencode/
│       ├── .gitignore
│       ├── pyproject.toml
│       ├── README.md
│       └── src/
│           └── opencode/
│               ├── __init__.py
│               ├── __main__.py
│               ├── cli/
│               ├── core/
│               ├── db/
│               ├── i18n/
│               ├── llmchecker/
│               ├── mcp/
│               ├── provider/
│               ├── router/
│               ├── server/
│               ├── session/
│               ├── skills/
│               ├── tests/
│               ├── tool/
│               ├── tui/
│               ├── util/
│               ├── web/
│               └── workflow/
└── .github/
    └── workflows/
        └── test.yml
```

---

## Proposed Project Structure

### Root Level Organization

```
opencode_4py/
├── .github/                    # GitHub-specific files
│   ├── workflows/              # CI/CD workflows
│   │   ├── test.yml           # Test workflow
│   │   ├── release.yml        # Release workflow
│   │   └── docs.yml           # Documentation workflow
│   ├── ISSUE_TEMPLATE/         # Issue templates
│   │   ├── bug_report.md
│   │   ├── feature_request.md
│   │   └── question.md
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── CODEOWNERS              # Code ownership
│   └── dependabot.yml          # Dependency updates
│
├── docs/                       # Documentation
│   ├── README.md              # Main docs entry
│   ├── user-guide/            # User documentation
│   ├── api/                   # API reference
│   ├── architecture/          # Architecture docs
│   ├── tutorials/             # Tutorials
│   ├── contributing/          # Contributor guides
│   ├── reference/             # Quick reference
│   └── meta/                  # Doc meta & templates
│
├── examples/                   # Example projects & code
│   ├── basic-usage/           # Simple examples
│   ├── custom-provider/       # Custom provider examples
│   ├── custom-tool/           # Custom tool examples
│   └── mcp-servers/           # MCP server examples
│
├── plans/                      # Planning documents
│   ├── ARCHIVED/              # Completed/archived plans
│   └── templates/             # Plan templates
│
├── scripts/                    # Utility scripts
│   ├── dev-setup.sh           # Development setup
│   ├── release.sh             # Release script
│   └── benchmark.py           # Performance benchmarks
│
├── src/
│   └── opencode/              # Main package
│       ├── pyproject.toml     # Package configuration
│       ├── README.md          # Package README
│       ├── CHANGELOG.md       # Package changelog
│       └── src/
│           └── opencode/      # Source code
│
├── .gitignore
├── .pre-commit-config.yaml    # Pre-commit hooks
├── CHANGELOG.md               # Project changelog
├── CONTRIBUTING.md            # Contribution guide
├── LICENSE                    # MIT License
├── README.md                  # Project README
├── SECURITY.md                # Security policy
└── Makefile                   # Common commands
```

---

## Source Code Organization

### Package Structure

```
src/opencode/src/opencode/
├── __init__.py               # Package initialization
├── __main__.py               # Entry point for python -m
├── _version.py               # Version information (generated)
│
├── cli/                      # Command-line interface
│   ├── __init__.py
│   ├── main.py               # Main CLI entry
│   └── commands/             # CLI commands
│       ├── __init__.py
│       ├── auth.py           # Authentication commands
│       ├── config.py         # Configuration commands
│       ├── index.py          # Indexing commands
│       ├── llmchecker.py     # LLM checker commands
│       ├── run.py            # Run commands
│       └── serve.py          # Server commands
│
├── core/                     # Core functionality
│   ├── __init__.py
│   ├── config.py             # Configuration management
│   ├── session.py            # Session management
│   ├── context/              # Context handling
│   │   ├── __init__.py
│   │   ├── checkpoints.py
│   │   ├── mentions.py
│   │   ├── tracker.py
│   │   └── truncation.py
│   ├── modes/                # Agent modes
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── manager.py
│   │   ├── registry.py
│   │   └── modes/
│   ├── orchestration/        # Multi-agent orchestration
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── coordinator.py
│   │   ├── registry.py
│   │   └── router.py
│   ├── rag/                  # RAG pipeline
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── document.py
│   │   ├── embeddings.py
│   │   ├── evaluation.py
│   │   ├── pipeline.py
│   │   ├── query_rewriter.py
│   │   └── retriever.py
│   ├── subagents/            # Subagent system
│   │   ├── __init__.py
│   │   ├── builtin.py
│   │   ├── errors.py
│   │   ├── events.py
│   │   ├── manager.py
│   │   ├── statistics.py
│   │   ├── types.py
│   │   └── validator.py
│   ├── video/                # Video processing
│   │   ├── __init__.py
│   │   ├── audio.py
│   │   └── frames.py
│   └── youtube/              # YouTube integration
│       ├── __init__.py
│       ├── channel.py
│       ├── chunking.py
│       ├── timestamps.py
│       └── transcript.py
│
├── provider/                 # AI model providers
│   ├── __init__.py
│   ├── base.py               # Provider interface
│   ├── anthropic.py          # Claude
│   ├── openai.py             # GPT
│   ├── google.py             # Gemini
│   ├── azure.py              # Azure OpenAI
│   ├── bedrock.py            # AWS Bedrock
│   ├── groq.py               # Groq
│   ├── mistral.py            # Mistral
│   ├── cohere.py             # Cohere
│   ├── xai.py                # xAI
│   ├── perplexity.py         # Perplexity
│   ├── together.py           # Together AI
│   ├── cerebras.py           # Cerebras
│   ├── deepinfra.py          # DeepInfra
│   ├── openrouter.py         # OpenRouter
│   ├── vercel.py             # Vercel AI
│   ├── ollama.py             # Ollama (local)
│   ├── lmstudio.py           # LM Studio (local)
│   └── custom.py             # Custom providers
│
├── router/                   # Model routing
│   ├── __init__.py
│   ├── config.py
│   ├── engine.py
│   ├── profiler.py
│   ├── skills.py
│   └── vram_monitor.py
│
├── tool/                     # Tools for AI
│   ├── __init__.py
│   ├── base.py               # Tool interface
│   ├── apply_patch.py        # Patch application
│   ├── ask_followup.py       # Follow-up questions
│   ├── attempt_completion.py # Completion handling
│   ├── bash.py               # Shell execution
│   ├── batch.py              # Batch operations
│   ├── codesearch.py         # Code search
│   ├── explore.py            # Code exploration
│   ├── file_tools.py         # File operations
│   ├── git.py                # Git operations
│   ├── lsp.py                # LSP integration
│   ├── memory.py             # Memory management
│   ├── multiedit.py          # Multiple edits
│   ├── new_task.py           # Task creation
│   ├── plan.py               # Planning
│   ├── question.py           # Questions
│   ├── skill.py              # Skill execution
│   ├── switch_mode.py        # Mode switching
│   └── task.py               # Task delegation
│
├── mcp/                      # Model Context Protocol
│   ├── __init__.py
│   ├── client.py             # MCP client
│   ├── server.py             # MCP server
│   ├── oauth.py              # OAuth handling
│   └── types.py              # MCP types
│
├── server/                   # HTTP/WebSocket server
│   ├── __init__.py
│   ├── app.py                # FastAPI app
│   ├── graphql/              # GraphQL schema
│   │   ├── __init__.py
│   │   └── schema.py
│   └── routes/               # API routes
│       ├── __init__.py
│       ├── chat.py
│       ├── files.py
│       ├── models.py
│       ├── router.py
│       ├── sessions.py
│       ├── tools.py
│       └── workflow.py
│
├── session/                  # Session handling
│   ├── __init__.py
│   └── compaction.py         # Context compaction
│
├── skills/                   # Skill system
│   ├── __init__.py
│   ├── discovery.py
│   ├── manager.py
│   └── models.py
│
├── db/                       # Database
│   ├── __init__.py
│   ├── connection.py         # DB connection
│   └── models.py             # DB models
│
├── i18n/                     # Internationalization
│   ├── __init__.py
│   ├── manager.py
│   └── locales/              # Locale files
│       ├── en.json
│       ├── es.json
│       ├── ja.json
│       └── zh.json
│
├── llmchecker/               # LLM hardware checker
│   ├── __init__.py
│   ├── calibration/          # Model calibration
│   │   ├── __init__.py
│   │   ├── manager.py
│   │   └── models.py
│   ├── hardware/             # Hardware detection
│   │   ├── __init__.py
│   │   ├── detector.py
│   │   ├── models.py
│   │   └── backends/
│   ├── ollama/               # Ollama integration
│   │   ├── __init__.py
│   │   ├── client.py
│   │   └── models.py
│   └── scoring/              # Model scoring
│       ├── __init__.py
│       ├── engine.py
│       └── models.py
│
├── tui/                      # Terminal UI
│   ├── __init__.py
│   ├── app.py                # Textual app
│   ├── screens/              # TUI screens
│   ├── widgets/              # TUI widgets
│   └── themes/               # UI themes
│
├── web/                      # Web interface
│   ├── __init__.py
│   ├── static/               # Static files
│   └── templates/            # HTML templates
│
├── util/                     # Utilities
│   ├── __init__.py
│   ├── logging.py            # Logging utilities
│   ├── async_helpers.py      # Async utilities
│   └── validation.py         # Validation helpers
│
├── workflow/                 # Workflow engine
│   ├── __init__.py
│   ├── engine.py
│   └── templates/
│
└── tests/                    # Test suite
    ├── __init__.py
    ├── conftest.py
    ├── unit/
    ├── integration/
    ├── providers/
    ├── prompts/
    ├── ollama/
    └── utils/
```

---

## Naming Conventions

### File Naming

| Type | Convention | Example |
|------|------------|---------|
| Python modules | snake_case | `session_manager.py` |
| Python classes | PascalCase | `SessionManager` |
| Functions | snake_case | `create_session()` |
| Constants | UPPER_SNAKE | `MAX_TOKENS` |
| Private members | _leading_underscore | `_internal_method()` |
| Test files | test_*.py | `test_session.py` |
| Fixtures | *_fixture.py or in conftest.py | `provider_fixture.py` |

### Directory Naming

- Use lowercase with hyphens for docs: `user-guide/`
- Use lowercase with underscores for code: `session_manager/`
- Use plural for collections: `providers/`, `tools/`
- Use singular for singletons: `core/`, `main/`

### Module Organization

```python
# Standard import order (enforced by ruff)
# 1. Standard library
import asyncio
from pathlib import Path

# 2. Third-party
import httpx
from pydantic import BaseModel

# 3. Local imports
from opencode.core.config import Config
from opencode.provider.base import Provider
```

---

## Dependency Management

### Dependency Tiers

```toml
[project]
dependencies = [
    # Core - Always required
]

[project.optional-dependencies]
dev = [
    # Development tools
]

server = [
    # Server-specific dependencies
]

rag = [
    # RAG-specific dependencies
]

youtube = [
    # YouTube integration
]

all = [
    # All optional dependencies
]
```

### Dependency Guidelines

1. **Minimize core dependencies**: Keep the base install lightweight
2. **Use extras for optional features**: RAG, YouTube, etc.
3. **Pin major versions**: Allow minor/patch updates
4. **Regular updates**: Monthly dependency review

---

## Version Control Strategy

### Branch Strategy

```
main           # Production-ready code
├── develop    # Integration branch
│   ├── feature/xxx    # Feature branches
│   ├── fix/xxx        # Bug fix branches
│   ├── refactor/xxx   # Refactoring branches
│   └── docs/xxx       # Documentation branches
└── release/x.x        # Release preparation
```

### Branch Naming

- `feature/add-new-provider` - New features
- `fix/session-timeout` - Bug fixes
- `refactor/provider-interface` - Code improvements
- `docs/api-reference` - Documentation
- `chore/update-deps` - Maintenance

### Commit Message Format

```
type(scope): brief description

[optional body]

[optional footer]

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation
- refactor: Code refactoring
- test: Testing
- chore: Maintenance
- perf: Performance
```

---

## Code Quality Standards

### Linting & Formatting

```toml
[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP", "ARG", "SIM", "TCH", "PTH", "ERA", "RUF"]
```

### Type Checking

```toml
[tool.mypy]
python_version = "3.12"
strict = true
plugins = ["pydantic.mypy"]
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff
      - id: ruff-format
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    hooks:
      - id: mypy
  
  - repo: https://github.com/pre-commit/pre-commit-hooks
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
```

---

## Module Interface Design

### Public API Pattern

```python
# __init__.py - Define public API
"""OpenCode - AI Coding Agent."""

from opencode.core.session import Session
from opencode.core.config import Config
from opencode.provider.base import Provider, Message, ModelInfo
from opencode.tool.base import Tool

__all__ = [
    "Session",
    "Config",
    "Provider",
    "Message",
    "ModelInfo",
    "Tool",
]

__version__ = "1.0.0"
```

### Interface Segregation

```python
# Keep interfaces focused and minimal
class Provider(ABC):
    """Provider interface - minimal required methods."""
    
    @property
    @abstractmethod
    def name(self) -> str: ...
    
    @property
    @abstractmethod
    def models(self) -> list[ModelInfo]: ...
    
    @abstractmethod
    async def complete(
        self,
        messages: list[Message],
        model: str,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]: ...
```

---

## Extension Points

### Adding a New Provider

1. Create `src/opencode/provider/new_provider.py`
2. Inherit from `Provider` base class
3. Implement required methods
4. Add to `provider/__init__.py`
5. Add tests in `tests/providers/`
6. Add documentation in `docs/user-guide/providers/`

### Adding a New Tool

1. Create `src/opencode/tool/new_tool.py`
2. Inherit from `Tool` base class
3. Implement required methods
4. Register in `tool/__init__.py`
5. Add tests in `tests/unit/`
6. Add documentation in `docs/user-guide/tools/`

### Adding a New CLI Command

1. Create `src/opencode/cli/commands/new_command.py`
2. Use Typer for command definition
3. Register in `cli/commands/__init__.py`
4. Add tests
5. Update CLI documentation

---

## Configuration Management

### Configuration Hierarchy

```
1. Default values (in code)
2. System config (/etc/opencode/config.toml)
3. User config (~/.config/opencode/config.toml)
4. Project config (./opencode.toml)
5. Environment variables
6. CLI arguments
```

### Configuration Schema

```python
from pydantic import BaseModel
from pydantic_settings import BaseSettings

class ProviderConfig(BaseModel):
    api_key_env: str
    model: str
    base_url: str | None = None
    max_tokens: int = 4096
    temperature: float = 0.7

class Config(BaseSettings):
    default_provider: str = "anthropic"
    providers: dict[str, ProviderConfig] = {}
    
    model_config = SettingsConfigDict(
        env_prefix="OPENCODE_",
        env_file=".env",
    )
```

---

## Testing Organization

### Test Categories

| Category | Location | Marker | Purpose |
|----------|----------|--------|---------|
| Unit | `tests/unit/` | None | Test individual components |
| Integration | `tests/integration/` | `@pytest.mark.integration` | Test component interactions |
| Provider | `tests/providers/` | `@pytest.mark.provider` | Test provider implementations |
| Ollama | `tests/ollama/` | `@pytest.mark.ollama` | Test Ollama integration |
| Prompt | `tests/prompts/` | `@pytest.mark.prompt` | Test prompt accuracy |
| E2E | `tests/e2e/` | `@pytest.mark.e2e` | End-to-end tests |
| Slow | Any | `@pytest.mark.slow` | Long-running tests |

### Test Naming

```python
# Test class naming
class TestSessionManager:
    """Tests for SessionManager."""

# Test method naming
def test_create_session_with_valid_config():
    """Test creating a session with valid configuration."""
    
def test_create_session_raises_on_invalid_config():
    """Test that invalid config raises appropriate error."""
```

---

## Release Process

### Version Numbering

- **Major (X.0.0)**: Breaking changes
- **Minor (1.X.0)**: New features, backward compatible
- **Patch (1.0.X)**: Bug fixes, backward compatible

### Release Checklist

- [ ] Update CHANGELOG.md
- [ ] Update version in `_version.py`
- [ ] Run full test suite
- [ ] Update documentation
- [ ] Create release PR
- [ ] Tag release
- [ ] Build and publish to PyPI
- [ ] Create GitHub release

---

## Maintenance Schedule

| Activity | Frequency | Automation |
|----------|-----------|------------|
| Dependency updates | Weekly | Dependabot |
| Security audit | Weekly | GitHub Security |
| Code quality scan | Per PR | CI/CD |
| Documentation review | Monthly | Manual |
| Performance benchmarks | Monthly | CI/CD |
| Release | As needed | Manual |

---

## Future Considerations

### Scalability

- **Plugin system**: Allow third-party extensions
- **Lazy loading**: Load heavy dependencies on demand
- **Modular packaging**: Split into optional packages

### Growth Planning

- **API stability**: Maintain backward compatibility
- **Deprecation policy**: 2-version deprecation cycle
- **Migration guides**: For breaking changes

---

## Quick Reference

### Makefile Commands

```makefile
.PHONY: install dev test lint format clean

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	pytest src/opencode/tests/

lint:
	ruff check src/

format:
	ruff format src/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
```

### Common Tasks

| Task | Command |
|------|---------|
| Install for development | `make dev` |
| Run tests | `make test` |
| Run linting | `make lint` |
| Format code | `make format` |
| Run specific test | `pytest tests/unit/test_session.py -v` |
| Run tests excluding slow | `pytest -m "not slow"` |

---

*This plan is a living document. Update it as the project evolves.*

*Last updated: 2026-02-21*
