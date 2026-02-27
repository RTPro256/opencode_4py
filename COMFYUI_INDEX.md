# ComfyUI_windows_portable Index

> **Self-Knowledge Document for opencode_4py Integration**

## App Overview

- **Name:** ComfyUI_windows_portable
- **Purpose:** A portable Windows distribution of ComfyUI - a powerful and modular stable diffusion GUI and backend
- **Target Users:** AI artists, developers, and researchers using Stable Diffusion workflows
- **Repository:** [ComfyUI GitHub](https://github.com/comfyanonymous/ComfyUI)

## Architecture

### Tech Stack
- **Language:** Python 3.10+ (embedded distribution)
- **Framework:** ComfyUI (node-based workflow system)
- **Key Dependencies:** PyTorch, CUDA, Stable Diffusion models
- **AI Integration:** opencode_4py (embedded in site-packages)

### Directory Structure
```
ComfyUI_windows_portable/
├── ComfyUI/                    # Main ComfyUI application
│   ├── main.py                 # Primary entry point
│   ├── server.py               # Web server
│   ├── nodes.py                # Node definitions
│   ├── comfy/                  # Core ComfyUI library
│   ├── custom_nodes/           # Custom node extensions
│   │   └── ComfyUI-OpenCode_4py/  # opencode_4py integration node
│   └── models/                 # AI models directory
├── python_embeded/             # Embedded Python distribution
│   └── Lib/site-packages/
│       └── opencode/           # opencode_4py package
├── advanced/                   # Advanced launch scripts
├── update/                     # Update scripts
├── opencode.toml               # opencode_4py configuration
├── COMFYUI_INDEX.md            # This file (self-knowledge)
├── OPENCODE_4PY_README.md      # Integration documentation
└── run_*.bat                   # Launch scripts
```

### Entry Points
- **ComfyUI Main:** `ComfyUI/main.py` - Starts the ComfyUI web interface
- **opencode_4py TUI:** `run_opencode_4py.bat` - Launches opencode_4py terminal UI
- **opencode_4py Server:** `run_opencode_4py_server.bat` - Runs opencode_4py as server on port 4096
- **Combined:** `run_comfyui_with_opencode.bat` - Launches both ComfyUI and opencode_4py

## opencode_4py Integration

### Installation Location
- **Site-packages:** `python_embeded/Lib/site-packages/opencode/`
- **Config:** `opencode.toml` (project root)
- **Documentation:** `python_embeded/Lib/site-packages/opencode/README.md`

### Configuration
- **Default Model:** qwen3-coder:30b (Ollama local)
- **Provider:** Ollama (primary), OpenRouter (fallback)
- **Server Port:** 4096
- **Ollama URL:** http://localhost:11434

### Launch Scripts
| Script | Purpose |
|--------|---------|
| `run_opencode_4py.bat` | Launch TUI with pre-flight checks |
| `run_opencode_4py_server.bat` | Run as HTTP server |
| `run_comfyui_with_opencode.bat` | Launch ComfyUI with opencode integration |

## Key Files for AI Context

| File | Purpose | When to Reference |
|------|---------|-------------------|
| `ComfyUI/main.py` | ComfyUI entry point | Understanding startup flow |
| `ComfyUI/server.py` | Web server implementation | API endpoints, routes |
| `ComfyUI/nodes.py` | Node definitions | Available nodes, functionality |
| `opencode.toml` | opencode_4py config | Model settings, providers |
| `check_prerequisites.py` | Pre-flight checks | Troubleshooting setup issues |
| `test_opencode.py` | Integration test | Verifying opencode_4py works |

## Common Workflows

### Starting ComfyUI with opencode_4py
1. Ensure Ollama is running: `ollama serve`
2. Run `run_comfyui_with_opencode.bat`
3. Access ComfyUI at http://127.0.0.1:8188
4. Click "OpenCode" button in ComfyUI interface to launch TUI

### Using opencode_4py TUI
1. Run `run_opencode_4py.bat`
2. Pre-flight checks will verify setup
3. TUI launches if all checks pass
4. Use natural language to interact with AI

### Updating opencode_4py
1. Run `python_embeded\python.exe update_opencode_4py.py`
2. Or manually sync from source with robocopy

### Troubleshooting
1. Run `python_embeded\python.exe check_prerequisites.py`
2. Check GPU detection: `python_embeded\python.exe test_opencode.py`
3. Review RAG troubleshooting: `python_embeded\Lib\site-packages\opencode\RAG\troubleshooting\`

## Constraints and Rules

### Must Do
- Use embedded Python at `python_embeded\python.exe` for all operations
- Keep `opencode.toml` with project-specific model settings
- Run pre-flight checks before launching opencode_4py
- Maintain GPU compatibility (CUDA required for optimal performance)

### Must Not Do
- Do not modify ComfyUI core files unless necessary
- Do not change the embedded Python environment structure
- Do not delete the `python_embeded/Lib/site-packages/opencode/` directory
- Do not override project-specific model configurations during sync

### GPU Requirements
- NVIDIA GPU with CUDA support recommended
- Minimum 8GB VRAM for optimal Stable Diffusion performance
- opencode_4py can run on CPU but performance is reduced

## Synchronized Content

The following content is synchronized from the main opencode_4py project:

| Content | Location | Sync Strategy |
|---------|----------|---------------|
| Core Code | `python_embeded/Lib/site-packages/opencode/` | Full sync |
| README.md | `python_embeded/Lib/site-packages/opencode/README.md` | Copy |
| MISSION.md | `python_embeded/Lib/site-packages/opencode/MISSION.md` | Copy |
| RAG/troubleshooting/ | `python_embeded/Lib/site-packages/opencode/RAG/troubleshooting/` | Full sync |

### Project-Specific (Not Overwritten)
- `opencode.toml` - Configuration with project-specific model settings
- `COMFYUI_INDEX.md` - This self-knowledge document
- `OPENCODE_4PY_README.md` - Integration documentation
- `docs/opencode/` - Project-specific documentation
- `plans/` - Project-specific planning documents

## Related Documentation

- [opencode_4py README](python_embeded/Lib/site-packages/opencode/README.md)
- [opencode_4py MISSION](python_embeded/Lib/site-packages/opencode/MISSION.md)
- [Troubleshooting RAG](python_embeded/Lib/site-packages/opencode/RAG/troubleshooting/README.md)
- [OPENCODE_4PY_README.md](OPENCODE_4PY_README.md)
- [Main Project Plans](../../../plans/)

---

*Created: 2026-02-25*
*Related: [INTEGRATED_APP_INDEX_PLAN.md](../../../plans/INTEGRATED_APP_INDEX_PLAN.md)*
