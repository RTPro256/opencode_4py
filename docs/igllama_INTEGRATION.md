# igllama Integration

> Integration of local LLM management capabilities from igllama project

## Overview

This document describes the integration of igllama features into opencode_4py. igllama is a Zig-based Ollama alternative for running LLMs locally, built on llama.cpp.zig bindings.

## Source Project

- **Project**: [igllama](https://github.com/bkataru/igllama)
- **Language**: Zig
- **License**: MIT

## Integrated Features

### 1. Local LLM Module (`src/opencode/core/llm/`)

Created a new module for local LLM management:

| Component | File | Description |
|-----------|------|-------------|
| Configuration | `config.py` | LLMConfig, ModelConfig, SamplingConfig, ServerConfig |
| Model Manager | `model_manager.py` | ModelManager for downloading/listing GGUF models |
| Server | `server.py` | OpenAI-compatible API server |

### 2. CLI Commands (`src/opencode/cli/commands/local_llm.py`)

New `opencode local-llm` command group:

```bash
# List available models
opencode local-llm list

# Download model from HuggingFace
opencode local-llm pull TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF

# Show model metadata
opencode local-llm show tinyllama-1.1b-chat-v1.0

# Remove a model
opencode local-llm remove tinyllama-1.1b-chat-v1.0

# Start OpenAI-compatible API server
opencode local-llm serve --port 8080

# Run inference
opencode local-llm run --model tinyllama --prompt "Hello!"
```

## Architecture

### Configuration Classes

```python
# Global LLM configuration
config = LLMConfig(
    default_model="tinyllama",
    models_dir=Path.home() / ".cache" / "opencode" / "models",
    gpu_layers=0,
    context_size=4096,
    temperature=0.7,
    server=ServerConfig(host="127.0.0.1", port=8080),
)
```

### Model Management

```python
from opencode.core.llm import ModelManager, get_model_manager

manager = get_model_manager()

# List models
models = manager.list_models()

# Download from HuggingFace
model = await manager.pull_model("TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF")

# Inspect metadata
metadata = manager.inspect_model("tinyllama")

# Remove model
manager.remove_model("tinyllama")
```

### API Server

```python
from opencode.core.llm import get_llm_server

server = get_llm_server()
await server.start()
```

## Supported Features

| Feature | Status | Notes |
|---------|--------|-------|
| GGUF model files | ✅ Implemented | Standard GGUF format |
| HuggingFace integration | ✅ Implemented | Direct download |
| OpenAI-compatible API | ✅ Implemented | /v1/chat/completions |
| Model metadata inspection | ✅ Implemented | Basic GGUF parsing |
| GPU acceleration | 🔄 Placeholder | Requires llama.cpp bindings |
| Chat templates | ✅ Config | Auto-detect + manual |

## Future Enhancements

1. **Local Inference**: Integrate llama.cpp Python bindings for actual inference
2. **GPU Support**: Add CUDA/Metal/Vulkan backend support
3. **Grammar-based Generation**: Implement GBNF constrained generation
4. **Model Quantization**: Add GGUF quantization utilities

## Reference

- Original igllama: https://github.com/bkataru/igllama
- llama.cpp: https://github.com/ggerganov/llama.cpp
- GGUF format: https://github.com/ggerganov/llama.cpp/blob/master/gguf.md
