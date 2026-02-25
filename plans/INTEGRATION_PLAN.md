# OpenCode_4py Integration Plan for ComfyUI_windows_portable

## Executive Summary

This document outlines a comprehensive plan for integrating OpenCode_4py into the ComfyUI_windows_portable distribution. The plan is designed to be executed by RAG systems or developers and does NOT modify the target project's code.

---

## Prerequisites

### System Requirements (Verified ✅)
- **CPU:** Intel Core i9-14900KF (24 cores, 32 threads)
- **GPU:** 2x NVIDIA RTX 4070 SUPER (12GB each)
- **RAM:** Sufficient for AI workloads
- **Storage:** ~3GB additional for OpenCode_4py

### Software Requirements
- **Python:** 3.13 (already embedded)
- **Ollama:** Running with models available
- **CUDA:** 13.0 compatible drivers

---

## Phase 1: Environment Preparation

### Step 1.1: Verify Python Environment
```batch
cd for_testing/as_dependency/ComfyUI_windows_portable
.\python_embeded\python.exe --version
```
**Expected Output:** `Python 3.13.x`

### Step 1.2: Install Missing Dependencies
```batch
.\python_embeded\python.exe -m pip install rich textual tiktoken chromadb sentence-transformers
```

**Packages to Install:**
| Package | Version | Size | Purpose |
|---------|---------|------|---------|
| rich | latest | ~5MB | TUI rendering |
| textual | latest | ~10MB | TUI framework |
| tiktoken | latest | ~2MB | Token counting |
| chromadb | latest | ~50MB | Vector database |
| sentence-transformers | latest | ~100MB | Embeddings |

### Step 1.3: Verify Ollama Connectivity
```batch
curl http://localhost:11434/api/tags
```
**Expected:** JSON response with model list

---

## Phase 2: File Deployment

### Step 2.1: Create Target Directories
```
ComfyUI_windows_portable/
├── python_embeded/
│   └── Lib/
│       └── site-packages/
│           └── opencode/          # NEW: Main package
└── opencode/                       # NEW: Desktop App
    ├── i18n/                       # NEW: Translations
    └── config/                     # NEW: Configuration
```

### Step 2.2: Copy Core Package Files

**Source:** `src/opencode/src/opencode/`
**Destination:** `python_embeded/Lib/site-packages/opencode/`

**Files to Copy:**
```
opencode/
├── __init__.py
├── __main__.py
├── cli/                    # CLI commands
│   ├── __init__.py
│   ├── main.py
│   └── commands/
├── core/                   # Core functionality
│   ├── config.py
│   ├── session.py
│   ├── gpu_manager.py
│   ├── context/
│   ├── modes/
│   ├── orchestration/
│   ├── rag/
│   ├── subagents/
│   └── video/
├── db/                     # Database
├── i18n/                   # Internationalization
├── llmchecker/             # LLM checking
├── mcp/                    # MCP integration
├── provider/               # LLM providers
├── router/                 # Request routing
├── server/                 # HTTP server
├── session/                # Session management
├── skills/                 # Agent skills
├── tool/                   # Tools
├── tui/                    # Terminal UI
├── util/                   # Utilities
├── web/                    # Web interface
└── workflow/               # Workflow engine
```

### Step 2.3: Copy Desktop App Files

**Source:** `src/opencode/src/opencode/tui/`
**Destination:** `opencode/desktop/`

**Files to Copy:**
```
opencode/
├── tui/
│   ├── __init__.py
│   ├── app.py
│   └── widgets/
└── i18n/
    ├── __init__.py
    ├── manager.py
    └── locales/
        ├── en.json
        ├── es.json
        ├── ja.json
        └── zh.json
```

### Step 2.4: Copy Configuration Files

**Source:** `for_testing/as_dependency/ComfyUI_windows_portable/opencode.toml`
**Destination:** Keep in root (already exists)

---

## Phase 3: Launch Script Creation

### Step 3.1: Create OpenCode_4py Launch Script

**File:** `run_opencode_4py.bat`

```batch
@echo off
REM OpenCode_4py Launch Script for ComfyUI_windows_portable
REM This script launches the OpenCode_4py TUI interface

echo Starting OpenCode_4py...
echo.

REM Set environment variables
set OPENCODE_CONFIG=%~dp0opencode.toml
set PYTHONPATH=%~dp0python_embeded\Lib\site-packages

REM Launch OpenCode_4py TUI
cd /d "%~dp0"
.\python_embeded\python.exe -m opencode --tui

echo.
echo OpenCode_4py has exited.
pause
```

### Step 3.2: Create OpenCode_4py Server Script

**File:** `run_opencode_4py_server.bat`

```batch
@echo off
REM OpenCode_4py Server Mode
REM Runs OpenCode_4py as a background server

echo Starting OpenCode_4py Server on port 4096...
echo.

cd /d "%~dp0"
.\python_embeded\python.exe -m opencode serve --port 4096

pause
```

### Step 3.3: Create Combined Launch Script

**File:** `run_comfyui_with_opencode.bat`

```batch
@echo off
REM Launch both ComfyUI and OpenCode_4py

echo Starting ComfyUI with OpenCode_4py integration...
echo.

REM Start ComfyUI in background
start "ComfyUI" .\python_embeded\python.exe -s ComfyUI\main.py --windows-standalone-build

REM Wait for ComfyUI to start
timeout /t 5 /nobreak > nul

REM Start OpenCode_4py
echo Starting OpenCode_4py...
.\python_embeded\python.exe -m opencode --tui

pause
```

---

## Phase 4: Custom Node Wrapper (Optional)

### Step 4.1: Create Custom Node Directory

**Directory:** `ComfyUI/custom_nodes/ComfyUI-OpenCode_4py/`

### Step 4.2: Create Node Init File

**File:** `ComfyUI/custom_nodes/ComfyUI-OpenCode_4py/__init__.py`

```python
"""
ComfyUI-OpenCode_4py: Integration node for OpenCode_4py
"""

import os
import sys
import subprocess
import threading

# Add OpenCode_4py to path
opencode_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                              "python_embeded", "Lib", "site-packages")
if opencode_path not in sys.path:
    sys.path.insert(0, opencode_path)

# Web directory for JavaScript extension
WEB_DIRECTORY = "js"

# Node class mappings (empty - we're just providing menu integration)
NODE_CLASS_MAPPINGS = {}
__all__ = ['NODE_CLASS_MAPPINGS']


def launch_opencode_4py():
    """Launch OpenCode_4py in a separate process."""
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    python_exe = os.path.join(base_path, "python_embeded", "python.exe")
    
    def run():
        subprocess.Popen([python_exe, "-m", "opencode", "--tui"], 
                        cwd=base_path,
                        creationflags=subprocess.CREATE_NEW_CONSOLE)
    
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return "OpenCode_4py launched"


# Register with ComfyUI-Manager if available
try:
    import cm_global
    cm_global.register_api("opencode_4py.launch", launch_opencode_4py)
except ImportError:
    pass
```

### Step 4.3: Create JavaScript Menu Extension

**File:** `ComfyUI/custom_nodes/ComfyUI-OpenCode_4py/js/opencode_menu.js`

```javascript
import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

// Register menu item
app.ui.settings.addSetting({
    id: "opencode_4py.enabled",
    name: "Enable OpenCode_4py Integration",
    type: "boolean",
    defaultValue: true,
});

// Add menu item
app.registerExtension({
    name: "ComfyUI-OpenCode_4py",
    setup() {
        // Add to menu
        const menu = app.menu;
        if (menu) {
            menu.addItem({
                name: "OpenCode_4py",
                callback: () => {
                    // Launch OpenCode_4py
                    fetch("/opencode_4py/launch", { method: "POST" })
                        .then(r => r.json())
                        .then(data => {
                            console.log("OpenCode_4py launched:", data);
                        })
                        .catch(err => {
                            console.error("Failed to launch OpenCode_4py:", err);
                        });
                },
            });
        }
    },
});
```

---

## Phase 5: Configuration

### Step 5.1: Update opencode.toml

**File:** `opencode.toml` (already exists, verify settings)

```toml
# OpenCode Configuration for ComfyUI Integration
# Location: ComfyUI_windows_portable/opencode.toml

# Core settings
default_model = "llama3.2:latest"
default_agent = "build"
log_level = "INFO"

# GPU Configuration
[gpu]
strategy = "auto"
vram_threshold_percent = 95.0
allow_shared_gpu = true
auto_unload = false
reserved_vram_gb = 0.5

# Ollama provider
[providers.ollama]
base_url = "http://localhost:11434"
enabled = true

# Server configuration
[server]
host = "127.0.0.1"
port = 4096
cors_origins = ["http://localhost:*", "http://127.0.0.1:8188"]

# TUI configuration
[tui]
theme = "dark"
show_token_count = true
show_cost = false
compact_mode = false

# ComfyUI integration
[comfyui]
server_url = "http://127.0.0.1:8188"
auto_connect = true
```

### Step 5.2: Create Python Path Configuration

**File:** `python_embeded/opencode.pth`

```
# OpenCode_4py path configuration
../opencode
```

---

## Phase 6: Testing

### Step 6.1: Test Package Import
```batch
.\python_embeded\python.exe -c "import opencode; print(opencode.__version__)"
```

### Step 6.2: Test TUI Launch
```batch
.\python_embeded\python.exe -m opencode --help
```

### Step 6.3: Test Server Mode
```batch
.\python_embeded\python.exe -m opencode serve --port 4096
```

### Step 6.4: Test Ollama Integration
```batch
.\python_embeded\python.exe -c "from opencode.llmchecker.ollama import OllamaClient; c = OllamaClient(); print(c.list_models())"
```

### Step 6.5: Test GPU Detection
```batch
.\python_embeded\python.exe -c "from opencode.core.gpu_manager import GPUManager; g = GPUManager(); print(g.detect_gpus())"
```

---

## Phase 7: Documentation

### Step 7.1: Create User Guide

**File:** `OPENCODE_4PY_README.md`

```markdown
# OpenCode_4py for ComfyUI_windows_portable

## Quick Start

1. Double-click `run_opencode_4py.bat` to launch the TUI
2. Or run `run_comfyui_with_opencode.bat` for both ComfyUI and OpenCode_4py

## Features

- AI-powered code assistance
- Integration with ComfyUI workflows
- Local LLM support via Ollama
- Multi-GPU support

## Configuration

Edit `opencode.toml` to customize settings.

## Troubleshooting

### OpenCode_4py won't start
- Ensure Ollama is running: `ollama serve`
- Check Python dependencies: `.\python_embeded\python.exe -m pip list`

### GPU not detected
- Update NVIDIA drivers
- Check CUDA installation

### Models not found
- Pull models: `ollama pull llama3.2`
- Check Ollama is running on port 11434
```

---

## Rollback Plan

### If Integration Fails

1. **Remove added files:**
   - Delete `python_embeded/Lib/site-packages/opencode/`
   - Delete `opencode/` directory
   - Delete `run_opencode_4py.bat`
   - Delete `ComfyUI/custom_nodes/ComfyUI-OpenCode_4py/` (if created)

2. **Remove added packages:**
   ```batch
   .\python_embeded\python.exe -m pip uninstall rich textual tiktoken chromadb sentence-transformers -y
   ```

3. **Restore original state:**
   - No modifications were made to existing ComfyUI files
   - Original `opencode.toml` can be kept or deleted

---

## File Manifest

### Files Created by This Plan

| File | Purpose | Size |
|------|---------|------|
| `run_opencode_4py.bat` | Launch script | ~500 bytes |
| `run_opencode_4py_server.bat` | Server launch | ~300 bytes |
| `run_comfyui_with_opencode.bat` | Combined launch | ~400 bytes |
| `python_embeded/Lib/site-packages/opencode/` | Main package | ~2MB |
| `opencode/i18n/` | Translations | ~50KB |
| `OPENCODE_4PY_README.md` | User guide | ~2KB |
| `ComfyUI/custom_nodes/ComfyUI-OpenCode_4py/` | Custom node (optional) | ~5KB |

### Files NOT Modified

- All ComfyUI core files
- All python_embeded existing files
- All ComfyUI-Manager files
- Existing opencode.toml (only read, not modified)

---

## Success Criteria

1. ✅ OpenCode_4py TUI launches successfully
2. ✅ Ollama models are accessible
3. ✅ GPU detection works
4. ✅ ComfyUI continues to function normally
5. ✅ Both systems can run simultaneously
6. ✅ No modifications to existing ComfyUI code

---

## Timeline Estimate

| Phase | Duration |
|-------|----------|
| Phase 1: Environment Prep | 15 minutes |
| Phase 2: File Deployment | 10 minutes |
| Phase 3: Launch Scripts | 5 minutes |
| Phase 4: Custom Node (Optional) | 15 minutes |
| Phase 5: Configuration | 5 minutes |
| Phase 6: Testing | 15 minutes |
| Phase 7: Documentation | 10 minutes |
| **Total** | **~75 minutes** |

---

## Appendix: Command Reference

### OpenCode_4py CLI Commands

```batch
# Launch TUI
.\python_embeded\python.exe -m opencode --tui

# Launch server
.\python_embeded\python.exe -m opencode serve --port 4096

# Run specific agent
.\python_embeded\python.exe -m opencode run --agent build

# Check configuration
.\python_embeded\python.exe -m opencode config show

# List available models
.\python_embeded\python.exe -m opencode models list

# RAG operations
.\python_embeded\python.exe -m opencode rag index --path ./docs
.\python_embeded\python.exe -m opencode rag query "search term"
```

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `OPENCODE_CONFIG` | Config file path | `./opencode.toml` |
| `OPENCODE_LOG_LEVEL` | Logging level | `INFO` |
| `OLLAMA_HOST` | Ollama server URL | `http://localhost:11434` |
