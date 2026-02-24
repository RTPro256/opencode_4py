# TUI Stall Troubleshooting Plan

> **Related Documents:**
> - [README.md](../README.md) - Project overview and features
> - [MISSION.md](../MISSION.md) - Mission statement and core principles

## Current Issue
The TUI stalls at "Thinking..." after entering "Hello OpenCode" prompt.

## Diagnosis Steps

### Step 1: Check if Ollama is Running
```powershell
# In a PowerShell terminal, run:
curl http://localhost:11434/api/tags
```

**Expected Result:** JSON response listing available models
**If Fails:** Ollama is not running - start it with `ollama serve` or from Start Menu

### Step 2: Check if Required Model is Available
```powershell
# List installed models:
ollama list
```

**Expected Result:** List should include `qwen3-coder:30b`
**If Missing:** Pull the model with `ollama pull qwen3-coder:30b`

### Step 3: Check Debug Logs
The batch file enables debug logging. Check the log file at:
```
for_testing/as_dependency/ComfyUI_windows_portable/python_embeded/Lib/site-packages/opencode/docs/opencode_debug.log
```

Or run with explicit log file:
```batch
cd for_testing\as_dependency\ComfyUI_windows_portable
set OPENCODE_LOG_LEVEL=DEBUG
set OPENCODE_LOG_FILE=%CD%\opencode_debug.log
.\python_embeded\python.exe -m opencode run
```

### Step 4: Test with Available Model
If `qwen3-coder:30b` is not available, modify `opencode.toml` to use an available model:

```toml
# Change default model to one that exists
default_model = "llama3.2:latest"
```

Or use a smaller model for testing:
```powershell
ollama pull llama3.2
```

## Quick Fix Options

### Option A: Start Ollama and Pull Model
```powershell
# Start Ollama (if not running)
ollama serve

# In another terminal, pull the model
ollama pull qwen3-coder:30b
```

### Option B: Use Different Model
Edit `for_testing/as_dependency/ComfyUI_windows_portable/opencode.toml`:
```toml
# Change line 5 from:
default_model = "qwen3-coder:30b"
# To an available model:
default_model = "llama3.2:latest"
```

### Option C: Use Cloud Provider (if API key available)
Set environment variable for OpenRouter:
```batch
set OPENROUTER_API_KEY=your_api_key_here
```

Then edit `opencode.toml`:
```toml
default_model = "z-ai/glm-5:free"
```

## Verification
After applying fix:
1. Run the batch file: `run_comfyui_with_opencode.bat`
2. Click the "🤖 OpenCode" button in ComfyUI
3. Enter "Hello OpenCode" prompt
4. Verify response appears

## Related Error Documents
- [ERR-003: AI Provider Availability](../RAG/troubleshooting/errors/ERR-003-ai-provider-availability.md)
- [ERR-010: Async Generator Await Error](../RAG/troubleshooting/errors/ERR-010-async-generator-await.md)
- [ERR-011: Runtime Logging Silent Failures](../RAG/troubleshooting/errors/ERR-011-runtime-logging-silent-failures.md)
- [PATTERN-001: TUI Stall Diagnosis](../RAG/troubleshooting/patterns/PATTERN-001-tui-stall-diagnosis.md)
