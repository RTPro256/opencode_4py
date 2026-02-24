# ERR-009: Wrong Provider Method Name

## Metadata
- **Error ID**: ERR-009
- **Category**: Code
- **Severity**: High
- **Status**: Fixed
- **Date Encountered**: 2026-02-23
- **Related Errors**: ERR-007, ERR-010

## Symptom
Error: `AttributeError: 'Provider' object has no attribute 'stream'`

## Root Cause
TUI called `provider.stream()` which doesn't exist. The Provider interface uses `complete()` method, not `stream()`.

## Incorrect Code
```python
async for chunk in provider.stream(messages):
    ...
```

## Fix
Use `provider.complete()` which is the correct Provider interface method:
```python
async for chunk in provider.complete(messages):
    ...
```

## Provider Interface
```python
# From provider/base.py
class Provider(ABC):
    @abstractmethod
    async def complete(
        self,
        messages: list[Message],
        tools: Optional[list[Tool]] = None,
        **kwargs,
    ) -> AsyncGenerator[StreamingResponse, None]:
        """Generate a streaming response."""
        ...
```

## Verification
```python
# Check available methods
from opencode.provider.base import Provider
import inspect

methods = [m for m in dir(Provider) if not m.startswith('_')]
print(methods)  # Should include 'complete', not 'stream'
```

## Lesson Learned
Verify method names in the interface/base class, not just class names.

## Prevention
- Always check the base class/interface for correct method signatures
- Use IDE autocomplete to discover available methods
- Add type hints to catch method name errors at development time
