# ComfyUI with opencode_4py Integration

This repository contains opencode_4py integration files for ComfyUI.

## Installation

```bash
# 1. Clone the official ComfyUI repository
git clone https://github.com/Comfy-Org/ComfyUI.git

# 2. Clone this integration repository into the ComfyUI folder
cd ComfyUI
git clone https://github.com/RTPro256/comfyui_portable_opencode-4py.git temp_integration
# Move files from temp_integration to current directory
move temp_integration\* .
rmdir temp_integration
```

## Features

- Run ComfyUI with opencode_4py AI agent integration
- Pre-configured scripts for CPU and GPU execution
- Update scripts for ComfyUI and dependencies

## Usage

Run one of the batch files:
- `run_nvidia_gpu.bat` - Run with NVIDIA GPU
- `run_cpu.bat` - Run with CPU only
- `run_opencode_4py.bat` - Run with opencode_4py integration

## Requirements

- Python 3.13+ (included in portable Python distribution)
- NVIDIA GPU with CUDA support (for GPU execution)

## License

See ComfyUI repository for license information.
