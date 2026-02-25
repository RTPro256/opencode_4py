# Simplified Troubleshooting UX Plan

## Overview

Enable users to start troubleshooting with simple prompts:
- `debug {text of issue}` - Start debugging session with issue description
- `troubleshoot {text of issue}` - Alias for debug command

> **Navigation:**
> - **Previous:** [INTEGRATION_STATUS.md](INTEGRATION_STATUS.md) - ComfyUI integration
> - **Next:** [FOR_TESTING_UPDATE_PLAN.md](FOR_TESTING_UPDATE_PLAN.md) - TUI troubleshooting

> **Related Documents:**
> - [README.md](../README.md) - Project overview and features
> - [MISSION.md](../MISSION.md) - Mission statement and core principles

## User Experience

### Current Flow (Complex)
1. User encounters issue
2. User enables debug logging manually: `set OPENCODE_LOG_LEVEL=DEBUG`
3. User runs application
4. User reproduces issue
5. User finds log file
6. User queries RAG: `opencode rag query --agent troubleshooting "issue"`
7. User reads error documents
8. User applies fix

### Proposed Flow (Simple)
1. User runs: `opencode debug "TUI stalls at Thinking"`
2. System automatically:
   - Enables debug logging
   - Queries troubleshooting RAG for known issues
   - Displays relevant error documents with fixes
   - Offers to apply fix if found
   - Creates new error document if not found (after resolution)

## Implementation

### CLI Commands

#### `opencode debug <issue>`
```python
@app.command("debug")
def debug_issue(
    issue: str = typer.Argument(..., help="Description of the issue"),
    auto_fix: bool = typer.Option(False, "--fix", "-f", help="Automatically apply fix if found"),
    create_log: bool = typer.Option(True, "--log", "-l", help="Create debug log"),
):
    """
    Start a debugging session for an issue.
    
    Automatically:
    1. Enables debug logging
    2. Queries troubleshooting RAG
    3. Displays relevant error documents
    4. Offers to apply fix if found
    """
```

#### `opencode troubleshoot <issue>`
Alias for `opencode debug`.

### TUI Integration

In the TUI, users can type:
- `/debug TUI stalls at Thinking`
- `/troubleshoot TUI stalls at Thinking`

This triggers the same flow within the interactive session.

### Automatic Actions

1. **Enable Logging**
   ```python
   os.environ["OPENCODE_LOG_LEVEL"] = "DEBUG"
   os.environ["OPENCODE_LOG_FILE"] = str(log_path / "debug_session.log")
   ```

2. **Query RAG**
   ```python
   results = await rag_query(agent="troubleshooting", query=issue)
   ```

3. **Display Results**
   - Show matching error documents
   - Highlight symptoms that match
   - Show fix steps

4. **Offer Fix Application**
   - If `--fix` flag: automatically apply fix
   - Otherwise: prompt user to confirm

5. **Create New Error Document**
   - If no match found: start recording session
   - After resolution: prompt user to document error

## File Structure

```
src/opencode/src/opencode/cli/commands/
├── debug.py              # New debug command
│   ├── debug_issue()     # Main command
│   ├── enable_logging()  # Auto-enable debug logging
│   ├── query_rag()       # Query troubleshooting RAG
│   ├── display_results() # Show matching errors
│   └── apply_fix()       # Apply fix if found
```

## Example Usage

```bash
# Simple debugging
opencode debug "TUI stalls at Thinking"

# With auto-fix
opencode debug "TUI stalls at Thinking" --fix

# Create new error document after resolution
opencode debug "New error message" --new

# In TUI
/debug TUI stalls at Thinking
```

## Output Example

```
$ opencode debug "TUI stalls at Thinking"

Enabling debug logging...
Log file: docs/opencode/logs/debug_session.log

Querying troubleshooting RAG...
Found 2 matching errors:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ERR-010: Async Generator Await Error (CRITICAL)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Symptom: TUI stalls at "Thinking..." indefinitely after user sends a message.

Root Cause: The provider.complete() method is an async generator that should
NOT be awaited.

Fix:
  1. Open: opencode/tui/app.py
  2. Find line: async for chunk in await self.provider.complete(...)
  3. Remove 'await': async for chunk in self.provider.complete(...)

Confidence: 95% match

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Apply fix? [y/N] y

Applying fix...
Fix applied successfully!

Would you like to test the fix? [Y/n] y

Starting TUI...
```

## Next Steps

1. Create `debug.py` command module
2. Add `debug` and `troubleshoot` commands to CLI
3. Add TUI slash command integration
4. Add automatic logging enablement
5. Add RAG query integration
6. Add fix application logic
7. Add new error document creation flow
