# ERR-012: Missing Parameter in __init__

## Metadata
- **Error ID**: ERR-012
- **Category**: Code
- **Severity**: Medium
- **Status**: Fixed
- **Date Encountered**: 2026-02-23
- **Related Errors**: None

## Symptom
Error: `TypeError: OpenCodeApp.__init__() got an unexpected keyword argument 'sandbox_root'`

## Root Cause
The `launch_tui()` function in `run.py` passes `sandbox_root` parameter to `OpenCodeApp`, but the `__init__` method didn't accept this parameter.

## Incorrect Code
```python
# In app.py
class OpenCodeApp(App):
    def __init__(
        self,
        config: Config,
        session_manager: SessionManager,
        tool_registry: ToolRegistry,
        mcp_client: Optional[MCPClient] = None,
        # sandbox_root parameter missing!
    ) -> None:
        ...
```

## Fix
Add `sandbox_root: Optional[Path] = None` parameter to `OpenCodeApp.__init__()`:

```python
# In app.py
class OpenCodeApp(App):
    def __init__(
        self,
        config: Config,
        session_manager: SessionManager,
        tool_registry: ToolRegistry,
        mcp_client: Optional[MCPClient] = None,
        sandbox_root: Optional[Path] = None,  # Added this parameter
        ...
    ) -> None:
        ...
        self.sandbox_root = sandbox_root
```

## Verification
```python
# Test that the parameter is accepted
from opencode.tui.app import OpenCodeApp
import inspect

sig = inspect.signature(OpenCodeApp.__init__)
params = list(sig.parameters.keys())
assert 'sandbox_root' in params
```

## Lesson Learned
When integrating code from different sources, verify that function signatures match. Check all callers when modifying `__init__` signatures.

## Prevention
- Use type hints and static analysis to catch signature mismatches
- Check all callers when modifying function signatures
- Add integration tests that exercise the full initialization path
