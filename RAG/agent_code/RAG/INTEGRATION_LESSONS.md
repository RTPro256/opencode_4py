# Integration Lessons Learned - RAG Knowledge Base

This document captures key lessons learned from integrating opencode_4py into ComfyUI_windows_portable. Use this as a reference for future integrations.

---

## Web Framework Response Types

### aiohttp Handlers Must Return Response Objects

**Problem Pattern:**
```python
# WRONG - Returns dict
@routes.post("/api/endpoint")
async def handler(request):
    return {"status": "success"}
```

**Correct Pattern:**
```python
# CORRECT - Returns web.Response
from aiohttp import web

@routes.post("/api/endpoint")
async def handler(request):
    try:
        result = do_something()
        return web.json_response(result)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)
```

**Key Points:**
- aiohttp handlers must return `web.Response` objects
- Use `web.json_response()` for JSON data
- Use `web.Response(text=...)` for plain text
- Use `web.FileResponse(path)` for files
- Plain dicts, strings, or other objects cause `AttributeError: 'dict' object has no attribute 'prepare'`

---

## CLI Integration Patterns

### Always Verify CLI Structure First

**Problem Pattern:**
```bash
# Assuming CLI has --tui flag
python -m myapp --tui  # May not exist!
```

**Correct Pattern:**
```bash
# First verify CLI structure
python -m myapp --help

# Then use correct subcommands
python -m myapp run  # If 'run' is the correct subcommand
```

**Key Points:**
- Run `--help` before writing launch scripts
- Typer-based CLIs use subcommands, not flags for major modes
- Document the actual CLI structure in integration notes

---

## ORM Syntax Verification

### SQLAlchemy 2.x ForeignKey Syntax

**Problem Pattern:**
```python
# SQLAlchemy 1.x style
ForeignKey("table.id", on_delete="CASCADE")  # Wrong for 2.x
```

**Correct Pattern:**
```python
# SQLAlchemy 2.x style
ForeignKey("table.id", ondelete="CASCADE")  # No underscore
```

**Key Points:**
- SQLAlchemy 2.x uses `ondelete` (no underscore)
- Always check installed version: `import sqlalchemy; print(sqlalchemy.__version__)`
- Migration guides exist for 1.x to 2.x upgrades

---

## Configuration Validation

### Pydantic Required Fields

**Problem Pattern:**
```toml
[models."model-name"]
provider = "ollama"
# Missing model_id field!
```

**Correct Pattern:**
```toml
[models."model-name"]
provider = "ollama"
model_id = "model-name"  # Required by Pydantic ModelConfig
max_tokens = 4096
temperature = 0.7
```

**Key Points:**
- Check Pydantic model class for required fields
- `provider` and `model_id` are typically both required
- Configuration examples should include all required fields

---

## Async Database Dependencies

### SQLAlchemy Async Engine Requirements

**Problem Pattern:**
```python
# Missing async driver
engine = create_async_engine("sqlite+aiosqlite:///db.sqlite")
# Error: ModuleNotFoundError: No module named 'aiosqlite'
```

**Correct Pattern:**
```python
# Ensure async driver is installed
# pip install aiosqlite

# Or add to prerequisites check
required_packages = [
    ("aiosqlite", "Async SQLite driver"),
    ("sqlalchemy", "Database ORM"),
]
```

**Key Points:**
- SQLAlchemy async engines require specific drivers
- `aiosqlite` for SQLite async
- `asyncpg` for PostgreSQL async
- Include in pre-flight checks

---

## Type Safety in Function Calls

### Enum vs String Literals

**Problem Pattern:**
```python
await session_manager.add_message(
    session_id,
    role="user",  # String literal - may cause type errors
    content=message,
)
```

**Correct Pattern:**
```python
from opencode.core.session import MessageRole

await session_manager.add_message(
    session_id,
    role=MessageRole.USER,  # Enum value - type safe
    content=message,
)
```

**Key Points:**
- Use enum values when API expects enum types
- Provides compile-time type checking
- Prevents typos in string literals

---

## Provider Initialization Patterns

### Don't Hardcode Provider Selection

**Problem Pattern:**
```python
# Hardcoded provider
provider = AnthropicProvider(api_key="...")
```

**Correct Pattern:**
```python
# Configuration-driven provider selection
model_config = config.models.get(model_name)
provider_name = model_config.provider

if provider_name == "ollama":
    provider = OllamaClient()
elif provider_name == "anthropic":
    provider = AnthropicProvider(api_key=config.get_provider_config("anthropic").api_key)
```

**Key Points:**
- Use configuration to select providers
- Support multiple provider backends
- Don't pass `model` to provider constructors (pass to completion methods instead)

---

## Dependency Version Warnings

### Suppressing Non-Critical Warnings

**Problem:**
```
RequestsDependencyWarning: urllib3 (2.6.3) doesn't match a supported version!
```

**Solution:**
```bash
# Suppress all warnings
.\python_embeded\python.exe -W ignore -m myapp

# Or in batch file
.\python_embeded\python.exe -W ignore -m myapp run
```

**Key Points:**
- Version warnings often don't affect functionality
- Suppress with `-W ignore` flag
- Only downgrade packages if functionality is broken

---

## Pre-flight Check Pattern

### Comprehensive Prerequisite Verification

```python
def check_prerequisites():
    """Verify all prerequisites before running."""
    checks = []
    
    # Python version
    checks.append(("Python 3.10+", sys.version_info >= (3, 10)))
    
    # Required packages
    for package, desc in required_packages:
        try:
            __import__(package)
            checks.append((f"{package} ({desc})", True))
        except ImportError:
            checks.append((f"{package} ({desc})", False))
    
    # AI Provider availability
    has_ollama = check_ollama()
    has_remote = check_remote_providers()
    checks.append(("AI Provider", has_ollama or has_remote))
    
    # Report and exit if failures
    failures = [name for name, passed in checks if not passed]
    if failures:
        print("Missing prerequisites:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
```

---

## ComfyUI Custom Node Integration

### Required Files for Menu Integration

```
ComfyUI/custom_nodes/MyExtension/
├── __init__.py          # Python backend, API routes
└── js/
    └── extension.js     # JavaScript frontend, menu items
```

### __init__.py Pattern

```python
from aiohttp import web
from server import PromptServer

WEB_DIRECTORY = "js"
NODE_CLASS_MAPPINGS = {}
__all__ = ['NODE_CLASS_MAPPINGS']

@PromptServer.instance.routes.post("/my_extension/action")
async def api_handler(request):
    try:
        result = do_action()
        return web.json_response(result)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)
```

### JavaScript Extension Pattern

```javascript
import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

app.registerExtension({
    name: "MyExtension",
    async setup() {
        // Add menu button
        const menu = document.querySelector(".comfy-menu");
        const button = document.createElement("button");
        button.textContent = "My Extension";
        button.onclick = () => {
            api.fetchApi("/my_extension/action", { method: "POST" });
        };
        menu.append(button);
    }
});
```

---

## Summary Checklist for Integrations

- [ ] Verify CLI structure with `--help`
- [ ] Check ORM version and syntax
- [ ] Verify all Pydantic required fields in config
- [ ] Install async database drivers
- [ ] Use enums instead of string literals
- [ ] Make provider selection configuration-driven
- [ ] Return proper Response objects from web handlers
- [ ] Add pre-flight checks for all dependencies
- [ ] Suppress non-critical warnings with `-W ignore`
- [ ] Test with target-available AI providers
- [ ] Use correct Provider class (not Client class)
- [ ] Use multi-line input widgets for chat interfaces
- [ ] Verify Provider method names (`complete()` not `stream()`)
