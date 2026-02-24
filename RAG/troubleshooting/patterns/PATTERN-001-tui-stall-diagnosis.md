# PATTERN-001: TUI Stall Diagnosis

## Metadata
- **Pattern ID**: PATTERN-001
- **Category**: Diagnosis Pattern
- **Applies To**: TUI application stalls, hangs, or freezes

## Symptoms
- TUI displays "Thinking..." indefinitely
- No response appears after user sends a message
- No visible error message
- Application appears frozen

## Diagnosis Steps

### Step 1: Enable Debug Logging
```batch
set OPENCODE_LOG_LEVEL=DEBUG
set OPENCODE_LOG_FILE=%~dp0python_embeded\Lib\site-packages\opencode\docs\opencode_debug.log
```

### Step 2: Reproduce the Stall
1. Run the application
2. Send a message that causes the stall
3. Wait 10-30 seconds
4. Check the log file

### Step 3: Analyze Log for Key Indicators

| Log Entry | Indicates |
|-----------|-----------|
| "Processing message with model: X" | Processing started |
| "Calling provider.complete()" | Provider call initiated |
| "Received X chunks" | Response received |
| ERROR/exception | Actual failure point |
| No entries after "Calling provider.complete()" | Provider issue |

### Step 4: Check Common Causes

1. **Async Generator Await Error (ERR-010)**
   - Look for: `TypeError: object async_generator can't be used in 'await' expression`
   - Fix: Remove `await` before `provider.complete()`

2. **Reactive Property Watch Missing (ERR-014)**
   - Look for: Log shows chunks received but UI not updating
   - Fix: Add `watch_message_content()` method

3. **Provider Connection Issue (ERR-003)**
   - Look for: Connection refused, timeout errors
   - Fix: Verify Ollama is running

## Related Errors
- ERR-010: Async Generator Await Error
- ERR-014: Reactive Property Watch Missing
- ERR-003: AI Provider Availability
- ERR-011: Runtime Logging Silent Failures

## Prevention
- Always include logging at key processing milestones
- Use type hints to catch async/await errors at development time
- Test with debug logging enabled during development
