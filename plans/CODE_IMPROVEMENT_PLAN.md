# Comprehensive Code Improvement Plan for OpenCode Python

This document outlines a comprehensive strategy for code improvement, designed to ensure accuracy, security, and maintainability while accommodating future changes.

> **Related Documents:**
> - [README.md](../README.md) - Project overview and features
> - [MISSION.md](../MISSION.md) - Mission statement and core principles

---

## Executive Summary

**Core Principles:**
1. **Accuracy First** - Correctness over performance
2. **Security Above All** - Security is non-negotiable
3. **Maintainability** - Code should be easy to understand and modify
4. **Future-Proof Design** - Anticipate and accommodate changes

---

## Part 1: Python Code Standards

### 1.1 Type Safety and Static Analysis

**Current State:** Mixed type hint coverage

**Improvement Plan:**

```python
# 1. Enable strict mypy checking
# pyproject.toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_ignores = true
disallow_untyped_defs = true
disallow_any_generics = true
no_implicit_optional = true

# 2. Use TypeGuard for runtime type checking
from typing import TypeGuard, TypeVar

T = TypeVar("T")

def is_valid_response(data: Any) -> TypeGuard[dict[str, Any]]:
    """Runtime type guard for API responses."""
    return isinstance(data, dict) and "content" in data

# 3. Use Protocol for duck typing
from typing import Protocol

class Completer(Protocol):
    """Protocol for completion providers."""
    async def complete(self, messages: list[Message]) -> Response: ...
    async def stream(self, messages: list[Message]) -> AsyncIterator[StreamChunk]: ...
```

**Action Items:**
- [ ] Add `mypy --strict` to CI pipeline
- [ ] Add type hints to all public functions
- [ ] Create Protocol definitions for major interfaces
- [ ] Use TypeGuard for runtime validation of external data

### 1.2 Error Handling Standards

**Current State:** Inconsistent error handling patterns

**Improvement Plan:**

```python
# 1. Create comprehensive exception hierarchy
# src/opencode/core/exceptions.py

class OpenCodeError(Exception):
    """Base exception for all OpenCode errors."""
    def __init__(self, message: str, code: str, details: dict | None = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)

class ProviderError(OpenCodeError):
    """Errors from AI providers."""
    def __init__(self, message: str, provider: str, **kwargs):
        super().__init__(message, code="PROVIDER_ERROR", **kwargs)
        self.provider = provider

class SecurityError(OpenCodeError):
    """Security-related errors."""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, code="SECURITY_ERROR", **kwargs)

class ValidationError(OpenCodeError):
    """Input validation errors."""
    def __init__(self, message: str, field: str, **kwargs):
        super().__init__(message, code="VALIDATION_ERROR", **kwargs)
        self.field = field

# 2. Use result pattern for recoverable errors
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E", bound=OpenCodeError)

@dataclass
class Result(Generic[T, E]):
    """Result type for operations that can fail."""
    value: T | None = None
    error: E | None = None
    
    @property
    def is_ok(self) -> bool:
        return self.error is None
    
    @property
    def is_err(self) -> bool:
        return self.error is not None
    
    def unwrap(self) -> T:
        if self.error:
            raise self.error
        if self.value is None:
            raise ValueError("No value")
        return self.value

# 3. Context managers for resource cleanup
from contextlib import asynccontextmanager

@asynccontextmanager
async def managed_resource(resource: Resource):
    """Ensure proper cleanup of resources."""
    try:
        await resource.initialize()
        yield resource
    finally:
        await resource.cleanup()
```

**Action Items:**
- [ ] Create unified exception hierarchy
- [ ] Implement Result pattern for recoverable errors
- [ ] Add context managers for all resources
- [ ] Document error handling patterns

### 1.3 Async Best Practices

**Current State:** Mixed async/sync patterns

**Improvement Plan:**

```python
# 1. Use asyncio.TaskGroup for concurrent operations (Python 3.11+)
async def process_multiple_requests(requests: list[Request]) -> list[Response]:
    """Process requests concurrently with proper error handling."""
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(process_request(r)) for r in requests]
    return [task.result() for task in tasks]

# 2. Implement proper cancellation handling
async def long_running_operation(cancellationToken: asyncio.Event):
    """Operation that respects cancellation."""
    while not cancellationToken.is_set():
        try:
            await do_work()
        except asyncio.CancelledError:
            logger.info("Operation cancelled")
            raise

# 3. Use semaphores for rate limiting
class RateLimitedClient:
    """Client with built-in rate limiting."""
    
    def __init__(self, max_concurrent: int = 10):
        self._semaphore = asyncio.Semaphore(max_concurrent)
    
    async def request(self, *args, **kwargs) -> Response:
        async with self._semaphore:
            return await self._make_request(*args, **kwargs)

# 4. Timeout handling
async def with_timeout(coro, timeout: float, error_message: str = "Operation timed out"):
    """Execute coroutine with timeout."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        raise TimeoutError(error_message)
```

**Action Items:**
- [ ] Convert remaining sync code to async
- [ ] Add proper cancellation handling
- [ ] Implement rate limiting for all external calls
- [ ] Add timeout handling for all I/O operations

---

## Part 2: Security Improvements

### 2.1 Input Validation

**Current State:** Basic validation in some areas

**Improvement Plan:**

```python
# 1. Use Pydantic for all input validation
from pydantic import BaseModel, Field, field_validator, model_validator
import re

class FileWriteRequest(BaseModel):
    """Validated file write request."""
    path: str = Field(..., min_length=1, max_length=4096)
    content: str = Field(..., max_length=10_000_000)  # 10MB limit
    
    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        # Prevent path traversal
        if ".." in v or v.startswith("/"):
            raise ValueError("Invalid path: potential traversal attack")
        return v
    
    @model_validator(mode="after")
    def validate_file_extension(self) -> "FileWriteRequest":
        # Only allow certain extensions
        allowed_extensions = {".py", ".txt", ".md", ".json", ".yaml", ".toml"}
        ext = Path(self.path).suffix.lower()
        if ext and ext not in allowed_extensions:
            raise ValueError(f"File extension '{ext}' not allowed")
        return self

# 2. Sanitize all user inputs
def sanitize_shell_input(input_str: str) -> str:
    """Sanitize input for shell commands."""
    # Remove potentially dangerous characters
    dangerous_chars = {"$", "`", ";", "|", "&", ">", "<", "\n", "\r"}
    return "".join(c for c in input_str if c not in dangerous_chars)

# 3. Validate file paths
from pathlib import Path

def validate_path_in_project(path: str, project_root: Path) -> Path:
    """Ensure path is within project directory."""
    resolved = (project_root / path).resolve()
    if not str(resolved).startswith(str(project_root.resolve())):
        raise SecurityError("Path traversal attempt detected")
    return resolved
```

**Action Items:**
- [ ] Add Pydantic validation to all API endpoints
- [ ] Implement path validation for all file operations
- [ ] Add input sanitization for shell commands
- [ ] Create validation middleware for FastAPI

### 2.2 Secrets Management

**Current State:** Environment variables

**Improvement Plan:**

```python
# 1. Use a secrets manager abstraction
from abc import ABC, abstractmethod
from typing import Optional
import os

class SecretsManager(ABC):
    """Abstract secrets manager."""
    
    @abstractmethod
    async def get_secret(self, key: str) -> Optional[str]:
        """Retrieve a secret value."""
        pass
    
    @abstractmethod
    async def set_secret(self, key: str, value: str) -> None:
        """Store a secret value."""
        pass

class EnvironmentSecretsManager(SecretsManager):
    """Environment-based secrets (development)."""
    
    async def get_secret(self, key: str) -> Optional[str]:
        return os.environ.get(key)
    
    async def set_secret(self, key: str, value: str) -> None:
        os.environ[key] = value

class FileSecretsManager(SecretsManager):
    """File-based secrets (production)."""
    
    def __init__(self, secrets_dir: Path):
        self.secrets_dir = secrets_dir
    
    async def get_secret(self, key: str) -> Optional[str]:
        secret_file = self.secrets_dir / key
        if secret_file.exists():
            return secret_file.read_text().strip()
        return None

# 2. Never log secrets
import logging

class SecretFilter(logging.Filter):
    """Filter to redact secrets from logs."""
    
    SENSITIVE_KEYS = {
        "api_key", "password", "secret", "token", 
        "credential", "auth", "private_key"
    }
    
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        for key in self.SENSITIVE_KEYS:
            # Redact patterns like api_key=xxx or "api_key": "xxx"
            import re
            msg = re.sub(
                rf'({key}\s*[=:]\s*)[^\s,}}]+',
                r'\1[REDACTED]',
                msg,
                flags=re.IGNORECASE
            )
        record.msg = msg
        record.args = ()
        return True

# Apply filter
logging.getLogger().addFilter(SecretFilter())
```

**Action Items:**
- [ ] Implement SecretsManager abstraction
- [ ] Add secret filtering to all loggers
- [ ] Document secrets management best practices
- [ ] Add audit logging for secret access

### 2.3 Dependency Security

**Current State:** Basic dependency management

**Improvement Plan:**

```toml
# 1. Pin all dependencies with hashes
# pyproject.toml

[project.dependencies]
# Use exact versions for security-critical packages
pydantic = "2.5.3"  # Pinned
httpx = "0.27.0"    # Pinned

# 2. Configure dependency scanning
# .github/workflows/security.yml
name: Security Scan

on:
  schedule:
    - cron: '0 0 * * *'  # Daily
  pull_request:

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          severity: 'CRITICAL,HIGH'
      
      - name: Run pip-audit
        run: |
          pip install pip-audit
          pip-audit --strict
```

**Action Items:**
- [ ] Pin all dependency versions
- [ ] Add dependency scanning to CI
- [ ] Set up automated dependency updates (Dependabot)
- [ ] Create security policy document

---

## Part 3: Framework Improvements

### 3.1 FastAPI Best Practices

**Current State:** Basic FastAPI setup

**Improvement Plan:**

```python
# 1. Add request validation middleware
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import time

app = FastAPI()

@app.middleware("http")
async def validate_request_middleware(request: Request, call_next):
    """Validate incoming requests."""
    # Check content length
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > 10_000_000:  # 10MB
        return JSONResponse(
            status_code=413,
            content={"error": "Request too large"}
        )
    
    # Add request ID for tracing
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    request.state.request_id = request_id
    
    start_time = time.time()
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    response.headers["x-response-time"] = f"{time.time() - start_time:.3f}s"
    
    return response

# 2. Use dependency injection for services
from fastapi import Depends

async def get_session_manager() -> SessionManager:
    """Dependency for session manager."""
    return SessionManager()

async def get_current_user(
    authorization: str = Header(None),
    session: SessionManager = Depends(get_session_manager),
) -> User:
    """Dependency for authenticated user."""
    if not authorization:
        raise HTTPException(401, "Not authenticated")
    return await session.validate_token(authorization)

@app.post("/api/chat")
async def chat(
    request: ChatRequest,
    user: User = Depends(get_current_user),
    session: SessionManager = Depends(get_session_manager),
):
    """Authenticated chat endpoint."""
    return await session.chat(user, request)

# 3. Add rate limiting
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/chat")
@limiter.limit("100/minute")
async def chat(request: Request, chat_request: ChatRequest):
    """Rate-limited chat endpoint."""
    pass
```

**Action Items:**
- [ ] Add request validation middleware
- [ ] Implement dependency injection pattern
- [ ] Add rate limiting to all endpoints
- [ ] Add request tracing

### 3.2 SQLAlchemy Best Practices

**Current State:** Basic SQLAlchemy setup

**Improvement Plan:**

```python
# 1. Use async session properly
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

engine = create_async_engine(
    "sqlite+aiosqlite:///./data.db",
    echo=False,
    pool_pre_ping=True,  # Verify connections
    pool_size=5,
    max_overflow=10,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire after commit
)

# 2. Use repository pattern
from abc import ABC, abstractmethod

class Repository(ABC, Generic[T]):
    """Abstract repository."""
    
    @abstractmethod
    async def get(self, id: str) -> T | None:
        pass
    
    @abstractmethod
    async def save(self, entity: T) -> T:
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        pass

class SessionRepository(Repository[Session]):
    """Session repository implementation."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get(self, id: str) -> Session | None:
        result = await self.session.execute(
            select(SessionModel).where(SessionModel.id == id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def save(self, entity: Session) -> Session:
        model = self._to_model(entity)
        self.session.add(model)
        await self.session.commit()
        return entity

# 3. Add database migrations
# alembic/versions/xxx_add_sessions_table.py
def upgrade():
    op.create_table(
        'sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('title', sa.String(255)),
        sa.Column('messages', sa.JSON()),
    )

def downgrade():
    op.drop_table('sessions')
```

**Action Items:**
- [ ] Implement repository pattern for all entities
- [ ] Add database migrations with Alembic
- [ ] Add connection pooling configuration
- [ ] Add database health checks

### 3.3 Pydantic Model Improvements

**Current State:** Basic Pydantic models

**Improvement Plan:**

```python
# 1. Use model_config for all models
from pydantic import BaseModel, ConfigDict, Field

class Message(BaseModel):
    """Chat message with validation."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        str_min_length=1,
        validate_assignment=True,  # Validate on attribute assignment
        extra="forbid",  # Reject extra fields
    )
    
    role: Literal["user", "assistant", "system"]
    content: str = Field(..., min_length=1, max_length=100000)
    name: str | None = Field(None, pattern=r"^[a-zA-Z0-9_-]+$")

# 2. Use computed fields for derived data
from pydantic import computed_field

class Session(BaseModel):
    """Session with computed fields."""
    
    id: str
    messages: list[Message]
    created_at: datetime
    
    @computed_field
    @property
    def message_count(self) -> int:
        return len(self.messages)
    
    @computed_field
    @property
    def total_tokens(self) -> int:
        return sum(m.tokens for m in self.messages if hasattr(m, 'tokens'))

# 3. Use discriminated unions for polymorphic data
from typing import Annotated
from pydantic import Discriminator

class TextContent(BaseModel):
    type: Literal["text"] = "text"
    text: str

class ImageContent(BaseModel):
    type: Literal["image"] = "image"
    url: str
    alt_text: str | None = None

ContentBlock = Annotated[
    TextContent | ImageContent,
    Discriminator("type"),
]

class RichMessage(BaseModel):
    """Message with rich content."""
    role: str
    content: list[ContentBlock]
```

**Action Items:**
- [ ] Add model_config to all Pydantic models
- [ ] Use computed fields for derived data
- [ ] Implement discriminated unions where appropriate
- [ ] Add model documentation

---

## Part 4: Code Quality Tools

### 4.1 Linting Configuration

```toml
# pyproject.toml

[tool.ruff]
target-version = "py312"
line-length = 100
src = ["src"]

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # Pyflakes
    "I",      # isort
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "UP",     # pyupgrade
    "ARG",    # flake8-unused-arguments
    "SIM",    # flake8-simplify
    "TCH",    # flake8-type-checking
    "PTH",    # flake8-use-pathlib
    "ERA",    # eradicate
    "RUF",    # Ruff-specific rules
    "S",      # flake8-bandit (security)
    "A",      # flake8-builtins
    "COM",    # flake8-commas
    "DTZ",    # flake8-datetimez
    "T10",    # flake8-debugger
    "EXE",    # flake8-executable
    "ISC",    # flake8-implicit-str-concat
    "ICN",    # flake8-import-conventions
    "G",      # flake8-logging-format
    "INP",    # flake8-no-pep420
    "PIE",    # flake8-pie
    "PYI",    # flake8-pyi
    "PT",     # flake8-pytest-style
    "Q",      # flake8-quotes
    "RSE",    # flake8-raise
    "RET",    # flake8-return
    "SLF",    # flake8-self
    "SLOT",   # flake8-slots
    "TID",    # flake8-tidy-imports
    "T20",    # flake8-print
    "PERF",   # Perflint
    "FURB",   # refurb
    "LOG",    # flake8-logging
]

ignore = [
    "E501",   # line too long (handled by formatter)
    "B008",   # do not perform function calls in argument defaults
    "S101",   # assert is fine in tests
    "T201",   # print is fine in CLI
]

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S101", "ARG", "PLR2004"]

[tool.ruff.lint.isort]
known-first-party = ["opencode"]

[tool.ruff.lint.flake8-tidy-imports]
ban-relative-imports = "all"
```

### 4.2 Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-json
      - id: check-added-large-files
        args: ['--maxkb=500']
      - id: check-merge-conflict
      - id: detect-private-key
      - id: debug-statements

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        additional_dependencies:
          - pydantic>=2.0
          - types-PyYAML
        args: [--strict]

  - repo: https://github.com/Lucas-C/pre-commit-hooks-bandit
    rev: v1.0.6
    hooks:
      - id: python-bandit-vulnerability-check
        args: ["-r", "src/", "-ll"]
```

---

## Part 5: Documentation Standards

### 5.1 Code Documentation

```python
# Use Google-style docstrings
def complete(
    self,
    messages: list[Message],
    *,
    model: str,
    temperature: float = 0.7,
    max_tokens: int | None = None,
    tools: list[ToolDefinition] | None = None,
) -> CompletionResponse:
    """Generate a completion for the given messages.
    
    This method sends the conversation history to the AI model and
    returns the generated response. It supports streaming, tool calling,
    and various model parameters.
    
    Args:
        messages: List of conversation messages in chronological order.
            Each message must have a role and content.
        model: The model identifier to use for completion.
            Use list_models() to get available models.
        temperature: Sampling temperature between 0 and 2.
            Higher values produce more random outputs.
            Defaults to 0.7.
        max_tokens: Maximum tokens to generate.
            None means no limit (up to model's context).
        tools: List of tools the model can call.
            Only supported on certain models.
    
    Returns:
        CompletionResponse containing the generated content and metadata.
    
    Raises:
        ProviderError: If the API request fails.
        ValidationError: If the input parameters are invalid.
        TimeoutError: If the request times out.
    
    Example:
        >>> response = await provider.complete(
        ...     messages=[Message(role="user", content="Hello")],
        ...     model="llama3.2:3b",
        ... )
        >>> print(response.content)
        "Hello! How can I help you today?"
    
    Note:
        This method is async and should be awaited.
        For streaming, use the stream() method instead.
    """
    pass
```

### 5.2 Architecture Documentation

```markdown
# Architecture Decision Records (ADRs)

Create ADRs for significant decisions:

## ADR-001: Use Pydantic for All Data Validation

### Status
Accepted

### Context
We need consistent data validation across the codebase.

### Decision
Use Pydantic v2 for all data validation, including:
- API request/response models
- Configuration models
- Internal data structures

### Consequences
- Consistent validation behavior
- Automatic documentation generation
- Type safety with mypy
- Slight performance overhead from validation
```

---

## Part 6: Monitoring and Observability

### 6.1 Structured Logging

```python
# Use structured logging with context
import structlog

def configure_logging():
    """Configure structured logging."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )

# Usage with context
log = structlog.get_logger()

async def process_request(request_id: str, user_id: str):
    structlog.contextvars.bind_contextvars(request_id=request_id, user_id=user_id)
    log.info("Processing request")
    # ... processing ...
    log.info("Request completed", duration_ms=150)
```

### 6.2 Metrics Collection

```python
# Use Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge

REQUEST_COUNT = Counter(
    'opencode_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'opencode_request_latency_seconds',
    'Request latency in seconds',
    ['method', 'endpoint']
)

ACTIVE_SESSIONS = Gauge(
    'opencode_active_sessions',
    'Number of active sessions'
)

# Middleware for metrics
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code,
    ).inc()
    
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path,
    ).observe(time.time() - start_time)
    
    return response
```

---

## Part 7: Future-Proofing Guidelines

### 7.1 Version Compatibility

```python
# Use version guards for new features
import sys

if sys.version_info >= (3, 12):
    # Use Python 3.12+ features
    from typing import override
else:
    # Fallback for older versions
    def override(func):
        return func

# Use feature detection for optional dependencies
try:
    import tiktoken
    HAS_TIKTOKEN = True
except ImportError:
    HAS_TIKTOKEN = False

def count_tokens(text: str) -> int:
    """Count tokens, using best available method."""
    if HAS_TIKTOKEN:
        return len(tiktoken.get_encoding("cl100k_base").encode(text))
    else:
        # Fallback: approximate with word count
        return len(text.split()) * 1.3
```

### 7.2 Deprecation Policy

```python
# Use deprecation warnings properly
import warnings
from typing import Callable

def deprecated(
    message: str,
    version: str,
    removal_version: str,
) -> Callable:
    """Decorator for deprecated functions."""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"{func.__name__} is deprecated since version {version}. "
                f"It will be removed in version {removal_version}. "
                f"{message}",
                DeprecationWarning,
                stacklevel=2,
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator

@deprecated("Use new_function() instead", "1.5.0", "2.0.0")
def old_function():
    """This function is deprecated."""
    pass
```

### 7.3 Configuration Migration

```python
# Handle configuration changes gracefully
class ConfigMigrator:
    """Migrate configuration between versions."""
    
    MIGRATIONS = {
        # (from_version, to_version): migration_function
        ("1.0", "1.1"): migrate_1_0_to_1_1,
        ("1.1", "1.2"): migrate_1_1_to_1_2,
    }
    
    def migrate(self, config: dict, from_version: str, to_version: str) -> dict:
        """Migrate configuration from one version to another."""
        current = from_version
        while current != to_version:
            key = (current, self._next_version(current))
            if key in self.MIGRATIONS:
                config = self.MIGRATIONS[key](config)
                current = key[1]
            else:
                raise ValueError(f"No migration path from {current} to {to_version}")
        return config
```

---

## Summary

### Priority Matrix

| Priority | Area | Impact | Effort |
|----------|------|--------|--------|
| P0 | Security - Input Validation | Critical | Medium |
| P0 | Security - Secrets Management | Critical | Low |
| P0 | Error Handling Standardization | High | Medium |
| P1 | Type Safety (mypy strict) | High | High |
| P1 | Async Best Practices | High | Medium |
| P1 | Structured Logging | High | Low |
| P2 | Repository Pattern | Medium | Medium |
| P2 | Metrics Collection | Medium | Low |
| P3 | Documentation Standards | Medium | Medium |

### Implementation Timeline

1. **Week 1-2**: Security improvements (P0)
2. **Week 3-4**: Error handling and type safety (P0-P1)
3. **Week 5-6**: Async improvements and logging (P1)
4. **Week 7-8**: Repository pattern and metrics (P2)
5. **Ongoing**: Documentation and deprecation handling

### Success Metrics

- **Security**: Zero critical/high vulnerabilities in dependency scans
- **Accuracy**: 100% type coverage with mypy strict mode
- **Maintainability**: Code coverage > 80%
- **Reliability**: Error rate < 0.1% for all operations
