# OpenCode_4py for ComfyUI_windows_portable

## Quick Start

1. Double-click `run_opencode_4py.bat` to launch the TUI
2. Or run `run_comfyui_with_opencode.bat` for both ComfyUI and OpenCode_4py

## Features

- AI-powered code assistance
- Integration with ComfyUI workflows
- Local LLM support via Ollama
- Multi-GPU support

## Available Launch Scripts

| Script | Purpose |
|--------|---------|
| `run_opencode_4py.bat` | Launch OpenCode_4py TUI |
| `run_opencode_4py_server.bat` | Run as server on port 4096 |
| `run_comfyui_with_opencode.bat` | Launch both ComfyUI and OpenCode_4py |

## Configuration

Edit `opencode.toml` to customize settings.

### Default Settings
- **Default Model:** qwen3-coder:30b
- **Server Port:** 4096
- **Ollama URL:** http://localhost:11434

## Requirements

- Ollama running with models installed
- CUDA-compatible GPU (optional, for acceleration)

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

## File Locations

```
ComfyUI_windows_portable/
├── python_embeded/
│   └── Lib/
│       └── site-packages/
│           └── opencode/        # Main package
│               ├── README.md    # Main project README (synced)
│               ├── MISSION.md   # Main project MISSION (synced)
│               └── RAG/
│                   └── troubleshooting/  # Error docs & patterns (synced)
├── ComfyUI/
│   └── custom_nodes/
│       └── ComfyUI-OpenCode_4py/  # ComfyUI integration
├── docs/
│   └── opencode/
│       ├── README.md           # Project-specific docs
│       ├── sessions/           # Chat sessions
│       └── logs/               # Debug logs
├── plans/
│   ├── README.md               # Plans directory guide
│   ├── UPDATE_OPENCODE_PLAN.md # Update instructions
│   └── UPDATE_UPGRADE_TROUBLESHOOTING_SUBPLAN.md
├── opencode.toml               # Configuration
├── run_opencode_4py.bat        # TUI launcher
├── run_opencode_4py_server.bat # Server launcher
└── run_comfyui_with_opencode.bat # Combined launcher
```

## Synchronization Status

This installation is synchronized with the main opencode_4py project.

### Synced Content (in python_embeded/Lib/site-packages/opencode/)
- **README.md** - Main project README (for AI context)
- **MISSION.md** - Main project MISSION (for AI context)
- **RAG/troubleshooting/** - Error documentation and troubleshooting patterns (23 files)
- **docs/** - Complete documentation (32 files + 2 API docs + 1 archive + 1 sessions)

### Project-Specific (Not Overwritten)
- `opencode.toml` - Configuration with project-specific model settings
- `docs/opencode/` - Project-specific documentation
- `docs/opencode/sessions/` - Session data
- `docs/opencode/logs/` - Log files
- `python_embeded/Lib/site-packages/opencode/plans/` - Complete planning documents (27 files + 5 archive)

## Updating

To update opencode_4py to the latest version:

```powershell
.\python_embeded\python.exe update_opencode_4py.py
```

Or see [plans/UPDATE_OPENCODE_PLAN.md](plans/UPDATE_OPENCODE_PLAN.md) for detailed instructions.

## Support

For more information, see:
- [Main README](../../../../README.md)
- [MISSION.md](../../../../MISSION.md)
- [Troubleshooting RAG](python_embeded/Lib/site-packages/opencode/RAG/troubleshooting/README.md)
- [Documentation Index](python_embeded/Lib/site-packages/opencode/docs/DOCS_INDEX.md)
- [Plans Index](plans/PLAN_INDEX.md)
