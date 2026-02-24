# ERR-011: Runtime Logging for Silent Failures

## Metadata
- **Error ID**: ERR-011
- **Category**: Debugging
- **Severity**: Medium
- **Status**: Fixed
- **Date Encountered**: 2026-02-23
- **Related Errors**: ERR-010

## Symptom
TUI stalls without displaying any error message. "Thinking..." displayed indefinitely, no visible error.

## Root Cause
Errors are being silently caught in try/except blocks without proper logging. No visibility into what's happening during processing.

## Fix
Enable debug logging to capture hidden errors:

```batch
REM Enable debug logging - log goes to opencode_4py's docs folder
set OPENCODE_LOG_LEVEL=DEBUG
set OPENCODE_LOG_FILE=%~dp0python_embeded\Lib\site-packages\opencode\docs\opencode_debug.log

REM Run OpenCode
.\python_embeded\python.exe -m opencode run

REM After stall, check log in opencode_4py's docs folder
type python_embeded\Lib\site-packages\opencode\docs\opencode_debug.log
```

## TUI Commands for Logging
- **Ctrl+T**: Toggle debug logging on/off
- **Ctrl+L**: View log files and display instructions for sharing with debugging agent

## Log File Location
The log must be written to opencode_4py's `docs/` folder in the target installation:
```
[PYTHON]/Lib/site-packages/opencode/docs/opencode_debug.log
```

## Log Analysis Points
- "Processing message with model: X" - confirms processing started
- "Calling provider.complete()" - confirms provider call
- "Received X chunks" - confirms response received
- ERROR/exception entries - identify the actual failure

## Lesson Learned
When errors are silently caught, runtime logs are essential for diagnosis. Always enable logging when troubleshooting stalls or hangs.

## Prevention
- Always include logging in try/except blocks
- Provide user-accessible logging controls
- Log key processing milestones
