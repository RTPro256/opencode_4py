# ERR-010: Async Generator Await Error

**Severity:** CRITICAL
**Category:** Code Error
**First Documented:** 2026-02-23
**Source:** ComfyUI Integration

## Symptoms

- TUI stalls at "Thinking..." indefinitely after user sends a message
- No visible error message in the UI
- Log shows `Received X chunks, response length: Y` but UI doesn't update

## Root Cause

The `provider.complete()` method is an **async generator** (uses `yield`), not a coroutine. Async generators return an async generator object immediately when called - they should NOT be awaited.

When you use `await` on an async generator, Python raises:
```
TypeError: object async_generator can't be used in 'await' expression
```

This error is silently caught by the `except Exception` block, leaving the TUI stuck at "Thinking...".

## Diagnosis

1. Check the log file for any TypeError entries
2. Look for `async for chunk in await self.provider.complete(...)` pattern in code
3. Verify the `complete()` method signature in the provider base class

## Fix

**Incorrect Code:**
```python
async for chunk in await self.provider.complete(...):  # WRONG
```

**Correct Code:**
```python
async for chunk in self.provider.complete(...):  # CORRECT
```

## Code Example

**Before (Incorrect):**
```python
async for chunk in await self.provider.complete(
    provider_messages, 
    model=self.current_model,
):
    if chunk.delta:
        full_response += chunk.delta
```

**After (Correct):**
```python
async for chunk in self.provider.complete(
    provider_messages, 
    model=self.current_model,
):
    if chunk.delta:
        full_response += chunk.delta
```

## Technical Explanation

| Concept | Description |
|---------|-------------|
| **Async Generator** | Function using `yield` inside `async def` |
| **Returns** | Async generator object (immediately) |
| **Iteration** | Use `async for` directly on the returned object |
| **Await** | NOT needed - the generator object is not awaitable |

## Related Errors

- [ERR-014: Reactive Property Watch Missing](ERR-014-reactive-property-watch-missing.md) - Similar symptom (UI not updating)
- [ERR-011: Runtime Logging Silent Failures](ERR-011-runtime-logging-silent-failures.md) - How to diagnose silent errors

## Prevention

1. Always check the base class implementation for correct usage patterns
2. Reference: `provider/base.py` shows correct usage
3. Remember: `async for` handles the async iteration protocol automatically
