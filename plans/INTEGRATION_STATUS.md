# OpenCode_4py Integration Status

## Integration Target: ComfyUI_windows_portable

**Date:** 2026-02-23
**Status:** Analysis Complete - Ready for Integration Planning

> **Related Documents:**
> - [README.md](../README.md) - Project overview and features
> - [MISSION.md](../MISSION.md) - Mission statement and core principles

---

## 1. System Resources Check ✅

### CPU Resources
- **Processor:** Intel(R) Core(TM) i9-14900KF
- **Cores:** 24 physical cores
- **Logical Processors:** 32 threads
- **Assessment:** Excellent for AI workloads - sufficient for running multiple models

### GPU Resources
- **GPU 1:** NVIDIA GeForce RTX 4070 SUPER (12,282 MiB VRAM)
- **GPU 2:** NVIDIA GeForce RTX 4070 SUPER (12,282 MiB VRAM)
- **Driver Version:** 591.74
- **Assessment:** Dual GPU setup ideal for model distribution and parallel processing

### Network Resources
- **Internet Connectivity:** ✅ Connected (14ms latency to Google)
- **Local Services:** Ollama running on localhost:11434

### Ollama Models Available (14 models)
| Model | Size | Parameter Count | Quantization |
|-------|------|-----------------|--------------|
| llama3.2:3b | 2.0 GB | 3.2B | Q4_K_M |
| llama3.3:70b | 42.5 GB | 70.6B | Q4_K_M |
| deepseek-coder-v2:16b | 8.9 GB | 15.7B | Q4_0 |
| deepseek-coder:33b | 18.8 GB | 33B | Q4_0 |
| qwen3-coder:30b | 18.6 GB | 30.5B | Q4_K_M |
| qwen3-coder-next:q4_K_M | 51.7 GB | 79.7B | Q4_K_M |
| deepseek-r1:32b | 19.9 GB | 32.8B | Q4_K_M |
| glm-4.7-flash:q8_0 | 31.8 GB | 29.9B | Q8_0 |
| qwen3:32b | 20.2 GB | 32.8B | Q4_K_M |
| deepseek-coder:33b-instruct-q5_K_M | 23.5 GB | 33B | Q5_K_M |
| llama3.1:8b-instruct-q8_0 | 8.5 GB | 8.0B | Q8_0 |
| gpt-oss:20b | 13.8 GB | 20.9B | MXFP4 |
| glm-5:cloud | Remote | - | - |
| llama3.2:3b-instruct-q8_0 | 3.4 GB | 3.2B | Q8_0 |

---

## 2. Target Project Analysis ✅

### Directory Structure
```
ComfyUI_windows_portable/
├── python_embeded/          # Python 3.13 embedded environment
│   ├── python.exe           # Main Python executable
│   ├── python313.dll        # Python runtime
│   ├── python313.zip        # Standard library
│   ├── Lib/site-packages/   # Installed packages
│   └── Scripts/             # Pip scripts
├── ComfyUI/                 # Main ComfyUI application
│   ├── main.py              # Entry point
│   ├── server.py            # Web server
│   ├── nodes.py             # Node definitions
│   ├── custom_nodes/        # Extension location
│   │   └── ComfyUI-Manager/ # Package manager
│   └── app/                 # Application modules
├── run_nvidia_gpu.bat       # GPU launch script
├── run_cpu.bat              # CPU launch script
└── opencode.toml            # OpenCode config (already present!)
```

### Key Findings

1. **Python Environment:** Python 3.13 embedded
   - Path configuration in `python313._pth`
   - Already includes: `../ComfyUI` in path
   - Has `site` module enabled

2. **Existing Configuration:** `opencode.toml` already exists in target directory
   - Pre-configured for Ollama integration
   - GPU settings optimized
   - Server port: 4096

3. **ComfyUI-Manager:** Full package manager present
   - Located at: `custom_nodes/ComfyUI-Manager/`
   - Has JS frontend components
   - Has Python backend (`manager_server.py`, `manager_core.py`)

---

## 3. Python Environment Analysis ✅

### Embedded Python Details
- **Version:** Python 3.13
- **Architecture:** Windows x64
- **Path Configuration:** 
  - `../ComfyUI` (relative path to main app)
  - `python313.zip` (standard library)
  - `.` (current directory)

### Key Installed Packages
| Package | Version | Purpose |
|---------|---------|---------|
| torch | 2.10.0+cu130 | PyTorch with CUDA 13.0 |
| transformers | 5.0.0 | HuggingFace transformers |
| numpy | 2.4.1 | Numerical computing |
| scipy | 1.17.0 | Scientific computing |
| pillow | 12.1.0 | Image processing |
| aiohttp | 3.13.3 | Async HTTP |
| pydantic | 2.12.5 | Data validation |
| sqlalchemy | 2.0.46 | Database ORM |
| requests | 2.32.5 | HTTP client |
| pyyaml | 6.0.3 | YAML parsing |

### Missing Dependencies for OpenCode_4py
The following packages may need to be installed:
- `rich` (for TUI)
- `textual` (for TUI framework)
- `httpx` (already present)
- `tiktoken` (for token counting)
- `chromadb` (for RAG vector store)

---

## 4. Integration Points Identified ✅

### Point 1: Initial Startup CLI Script
**Location:** Root directory batch files
**Current Files:**
- `run_nvidia_gpu.bat` - Launches ComfyUI with GPU
- `run_cpu.bat` - Launches ComfyUI with CPU

**Integration Approach:**
Create `run_opencode_4py.bat` to launch OpenCode_4py TUI:
```batch
@echo off
.\python_embeded\python.exe -m opencode --tui
pause
```

### Point 2: Menu Item Integration
**Location:** ComfyUI-Manager JavaScript
**Files:**
- `ComfyUI/custom_nodes/ComfyUI-Manager/js/comfyui-manager.js`

**Integration Approach:**
Add menu item via JavaScript extension that opens terminal with OpenCode_4py

### Point 3: Manager Features
**Location:** ComfyUI-Manager Python backend
**Files:**
- `manager_server.py` - API endpoints
- `manager_core.py` - Core functionality

**Integration Approach:**
Leverage existing infrastructure for:
- Model management
- Package installation
- Configuration management

### Point 4: Custom Nodes (Optional)
**Location:** `ComfyUI/custom_nodes/`
**Consideration:** OpenCode_4py is large and complex
**Recommendation:** Create lightweight wrapper node instead of full integration

---

## 5. Ideal Location for OpenCode_4py Files

### Recommended Structure
```
ComfyUI_windows_portable/
├── python_embeded/
│   └── Lib/site-packages/opencode/  # Main package location
├── ComfyUI/
│   └── custom_nodes/
│       └── ComfyUI-OpenCode_4py/    # Optional custom node wrapper
└── opencode/                         # Desktop App files
    ├── i18n/                         # Translations
    └── config/                       # Configuration
```

### Files to Include
1. **Core Package (site-packages):**
   - All `src/opencode/src/opencode/` contents
   
2. **Desktop App:**
   - TUI application
   - Configuration files
   
3. **i18n:**
   - `src/opencode/src/opencode/i18n/` contents

---

## 6. Next Steps

1. [ ] Create detailed integration plan
2. [ ] Test Python 3.13 compatibility
3. [ ] Install missing dependencies
4. [ ] Create launch scripts
5. [ ] Create custom node wrapper (optional)
6. [ ] Test integration

---

## Appendix: Raw Data

### CPU Info
```
Name=Intel(R) Core(TM) i9-14900KF
NumberOfCores=24
NumberOfLogicalProcessors=32
```

### GPU Info
```
name, memory.total [MiB], driver_version
NVIDIA GeForce RTX 4070 SUPER, 12282 MiB, 591.74
NVIDIA GeForce RTX 4070 SUPER, 12282 MiB, 591.74
```

### Python Path Configuration (python313._pth)
```
../ComfyUI
python313.zip
.

# Uncomment to run site.main() automatically
#import site
import site
```
