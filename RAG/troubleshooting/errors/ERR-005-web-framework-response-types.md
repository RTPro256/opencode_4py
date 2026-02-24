# ERR-005: Web Framework Response Types

## Metadata
- **Error ID**: ERR-005
- **Category**: Web Integration
- **Severity**: Medium
- **Status**: Fixed
- **Date Encountered**: 2026-02-23
- **Related Errors**: None

## Symptom
Error: `AttributeError: 'dict' object has no attribute 'prepare'`

## Root Cause
aiohttp handlers must return `web.Response` objects, not plain dicts.

## Incorrect Code
```python
async def handle_request(request):
    result = {"status": "ok", "data": {...}}
    return result  # WRONG: plain dict
```

## Fix
Use `web.json_response()` to create proper Response objects:
```python
from aiohttp import web

async def handle_request(request):
    result = {"status": "ok", "data": {...}}
    return web.json_response(result)  # CORRECT
```

## Verification
```bash
# Test the endpoint
curl http://localhost:8182/opencode/start
```

## Lesson Learned
Web framework handlers require proper Response objects.

## Prevention
- Use framework-specific response wrappers
- Add type hints to handler functions
- Write unit tests for API endpoints
