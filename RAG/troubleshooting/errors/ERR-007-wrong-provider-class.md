# ERR-007: Wrong Provider Class

## Metadata
- **Error ID**: ERR-007
- **Category**: Code
- **Severity**: High
- **Status**: Fixed
- **Date Encountered**: 2026-02-23
- **Related Errors**: ERR-009

## Symptom
Error: `AttributeError: 'OllamaClient' object has no attribute 'stream'`

## Root Cause
TUI app used `OllamaClient` instead of `OllamaProvider`. The `OllamaClient` is a low-level HTTP client, while `OllamaProvider` implements the Provider interface with the `complete()` method.

## Incorrect Code
```python
from opencode.llmchecker.ollama.client import OllamaClient

provider = OllamaClient(host="http://localhost:11434")
async for chunk in provider.complete(...):  # WRONG: OllamaClient has no complete()
    ...
```

## Fix
Use `OllamaProvider` from `provider/ollama.py` which implements Provider interface:
```python
from opencode.provider.ollama import OllamaProvider

provider = OllamaProvider(model="llama3.2")
async for chunk in provider.complete(...):  # CORRECT
    ...
```

## Verification
```python
# Check the class hierarchy
from opencode.provider.base import Provider
from opencode.provider.ollama import OllamaProvider

provider = OllamaProvider(model="llama3.2")
assert isinstance(provider, Provider)  # Should be True
```

## Lesson Learned
Verify which class implements the required interface (Provider ABC).

## Prevention
- Check base class/interface before using a class
- Use type hints to catch interface mismatches
- Document the difference between Client and Provider classes
