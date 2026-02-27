# OpenCode Python

<div align="center">

![OpenCode](https://img.shields.io/badge/OpenCode-Python-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.12+-green?style=for-the-badge&logo=python)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**The open source AI coding agent - Python edition**

[Features](#features) • [Installation](#installation) • [Quick Start](#quick-start) • [Documentation](#documentation)

</div>

---

> 📜 **[Read our Mission Statement](MISSION.md)** - The core principles guiding this project's development.

---

> **👋 A Personal Note from the Creator**
> 
> This project exists because I wanted an open-source AI project to learn from and use in my other projects. I picked Python because... well, have you *seen* the other options? (Just kidding, I love all programming languages equally. Mostly. 👀)
> 
> I'm the type who falls down GitHub rabbit holes at 2 AM, staring at brilliant code like a tourist at the Louvre. This project stands on the shoulders of code giants - if you recognize your patterns here, thank you for being awesome.
> 
> **Your mission, should you choose to accept it:** Fork this repo (keep the name for easy Googling), then personalize it until it's *yours*. Add your own bad jokes. Remove mine. Make it weird. Make it yours. Just remember: with great open source comes great responsibility to share your improvements back. 🚀

---

## Project Structure

| Directory | Purpose |
|-----------|---------|
| `src/` | **Main project** - OpenCode Python source code |
| `for_testing/` | **Testing subproject** - External projects used for testing this project's effectiveness |
| `merge_projects/` | **Migration sources** - Projects being migrated/integrated into this project |
| `aimodels/` | **Local AI models** - Sharded local models for distributed inference |
| `docs/` | **Documentation** - Feature coverage, migration plans, and guides |
| `plans/` | **Planning documents** - Integration plans and architectural decisions |

> 📁 **[See PROJECT_INDEX.md](PROJECT_INDEX.md)** for detailed Python file structure and module purposes.

---

## Overview

OpenCode Python is a complete rewrite of the [OpenCode](https://github.com/anomalyco/opencode) AI coding agent in Python. It provides a powerful, provider-agnostic AI assistant for software development with a beautiful terminal UI, HTTP server, and web interface.

### Why Python?

- **Simpler Deployment**: Single `pip install`, no runtime dependencies like Bun
- **Wider Ecosystem**: Access to Python's extensive ML/AI libraries
- **Easier Debugging**: Python's debugging tools and REPL
- **Lower Barrier**: More developers know Python than TypeScript/Bun

---

## Features

### 🤖 Multi-Provider Support

| Provider | Models |
|----------|--------|
| **Anthropic** | Claude 4, Claude 3.5 Sonnet/Opus |
| **OpenAI** | GPT-4o, GPT-4, o1, o3 |
| **Google** | Gemini 2.0, Gemini 1.5 Pro/Flash |
| **Azure** | GPT-4, GPT-4o |
| **AWS Bedrock** | Claude, Llama, Mistral |
| **Groq** | Llama, Mixtral (fast inference) |
| **Mistral** | Mistral Large, Codestral |
| **xAI** | Grok |
| **Cohere** | Command R+ |
| **Perplexity** | Sonar |
| **Together AI** | Open source models |
| **Cerebras** | Llama (fast inference) |
| **OpenRouter** | 100+ models |
| **Ollama** | Local models |
| **LM Studio** | Local models |

### 🛠️ 21 Built-in Tools

- **File Operations**: read, write, edit, glob, grep, ls, rm
- **Code Analysis**: lsp (definition, references, diagnostics, rename, format)
- **Web**: webfetch, websearch
- **Execution**: bash
- **Planning**: plan, todo, task
- **Advanced**: batch, multiedit, apply_patch, question

### 🔌 MCP Integration

- Connect to MCP servers for extended capabilities
- Act as an MCP server for other applications
- OAuth 2.0 authentication support

### 🌐 Web Interface

- Browser-based chat interface
- REST API with streaming
- WebSocket for real-time updates
- Mobile responsive

### 🌍 Internationalization

Support for 17+ languages:
English, 中文, 日本語, 한국어, Español, Français, Deutsch, Italiano, Português, Русский, العربية, ไทย, and more.

### 💻 Terminal UI

Beautiful TUI built with Textual:
- Chat view with syntax highlighting
- Diff view for code changes
- Session management
- Agent switching (build/plan)

---

## Installation

### From Source

```bash
git clone https://github.com/RTPro256/opencode_4py.git
cd opencode_4py/src/opencode
pip install -e .
```

### Requirements

- Python 3.12 or higher
- pip or uv package manager

---

## Quick Start

### 1. Set API Key

```bash
export ANTHROPIC_API_KEY=your-key-here
# or
export OPENAI_API_KEY=your-key-here
```

### 2. Launch

```bash
# Terminal UI
opencode

# HTTP server
opencode serve --port 4096

# Web interface
opencode web
```

### 3. Use

```
> Read main.py and explain what it does
> Add error handling to the process_data function
> Run the tests and fix any failures
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [README.md](docs/README.md) | Complete documentation |
| [FEATURE_COVERAGE.md](docs/FEATURE_COVERAGE.md) | Feature comparison with original |
| [DOCS_INDEX.md](docs/DOCS_INDEX.md) | Documentation navigation |
| [aimodels/README.md](aimodels/README.md) | Local model storage and sharding |

### Key Topics

- [Configuration](docs/README.md#configuration)
- [Providers](docs/README.md#providers)
- [Tools](docs/README.md#tools)
- [MCP Integration](docs/README.md#mcp-integration)
- [LSP Support](docs/README.md#lsp-support)
- [Web Interface](docs/README.md#web-interface)
- [Example Workflows](docs/README.md#example-workflows)
- [API Reference](docs/README.md#api-reference)
- [Troubleshooting](docs/README.md#troubleshooting)

---

## Example Workflows

### Project Integration Commands

Quick prompts for common integration workflows:

| Command | Purpose | Reference |
|---------|---------|-----------|
| **Merge** | Merge project from `merge_projects/` into opencode_4py | [QUICK_START_COMMANDS.md](plans/QUICK_START_COMMANDS.md) |
| **Integrate** | Add opencode_4py to project in `for_testing/` | [QUICK_START_COMMANDS.md](plans/QUICK_START_COMMANDS.md) |
| **Sync** | Apply opencode_4py changes to `for_testing/` project | [QUICK_START_COMMANDS.md](plans/QUICK_START_COMMANDS.md) |
| **Test** | Begin testing in `for_testing/` environment | [QUICK_START_COMMANDS.md](plans/QUICK_START_COMMANDS.md) |

**Merge a project:**
```
Start merge of [PROJECT_NAME] from merge_projects/ into opencode_4py.
Reference: plans/MERGE_INTEGRATION_PLAN.md
```

**Integrate to project:**
```
Start integration of opencode_4py to [PROJECT_NAME] in for_testing/.
Reference: plans/TARGET_PROJECT_SYNC_PLAN.md
```

**Sync changes:**
```
Sync opencode_4py code changes to [PROJECT_NAME] in for_testing/.
Reference: plans/TARGET_PROJECT_SYNC_PLAN.md
```

**Begin testing:**
```
Begin testing [FEATURE/COMPONENT] code changes to opencode_4py.
Reference: plans/TESTING_PLAN.md
```

### Integrated App Documentation

When opencode_4py is integrated into a host application, the host app should provide a `{APP_NAME}_INDEX.md` file at its root. This document serves as "self-knowledge" for opencode_4py when running within that app.

**For App Developers:**

If you're integrating opencode_4py into your app:

1. Create `{APP_NAME}_INDEX.md` at your project root
2. Document your app's architecture, key files, and workflows
3. Include any constraints or rules for AI assistance
4. Reference the opencode_4py README and MISSION for AI context

**For AI Agents:**

When operating within an integrated app:
- Read the `{APP_NAME}_INDEX.md` first to understand the host context
- Treat the host app's goals as your own goals
- Respect the host app's constraints and rules
- Use the troubleshooting RAG for error resolution

**Example:** See [COMFYUI_INDEX.md](for_testing/as_dependency/ComfyUI_windows_portable/COMFYUI_INDEX.md) for a complete example.

**Reference:** [INTEGRATED_APP_INDEX_PLAN.md](plans/INTEGRATED_APP_INDEX_PLAN.md)

### Code Review

```
> Read main.py
> What are the potential issues?
> Suggest improvements
> Apply the changes
```

### Bug Fixing

```
> Run pytest
> The test_user_creation test is failing
> Find and fix the bug
> Run tests again
```

### Feature Implementation

```
> Plan the implementation of user authentication
> Create the User model
> Add authentication endpoints
> Write tests
```

---

## Configuration

Create `opencode.toml` in your project:

```toml
[provider]
default = "anthropic"

[provider.anthropic]
api_key_env = "ANTHROPIC_API_KEY"
model = "claude-sonnet-4-20250514"

[tools]
bash = true
read = true
write = true
edit = true

[permissions]
bash_allow = ["git status", "pytest"]

[ui]
language = "en"
theme = "dark"
```

---

## Multi-Model Patterns

OpenCode supports multi-model patterns for improved accuracy through model collaboration. This feature allows you to chain multiple AI models together or run them in parallel.

### Available Patterns

| Pattern | Description | Use Case |
|---------|-------------|----------|
| `sequential` | Chain of models refining output | Code generation → Review → Validation |
| `ensemble` | Parallel models with aggregation | Multiple perspectives on same problem |
| `voting` | Models vote on best answer | Consensus-based decisions |

### Configuration

Add to `opencode.toml`:

```toml
[multi_model_patterns.code_review]
pattern = "sequential"
enabled = true

[[multi_model_patterns.code_review.models]]
model = "llama3.2"
provider = "ollama"
system_prompt = "You are a code generator. Generate clean, efficient code."
temperature = 0.8

[[multi_model_patterns.code_review.models]]
model = "mistral:7b"
provider = "ollama"
system_prompt = "You are a code reviewer. Review and improve the code."
temperature = 0.5

[multi_model_patterns.ensemble_analysis]
pattern = "ensemble"
aggregator_model = "llama3.2:70b"

[[multi_model_patterns.ensemble_analysis.models]]
model = "llama3.2"
provider = "ollama"

[[multi_model_patterns.ensemble_analysis.models]]
model = "mistral:7b"
provider = "ollama"
```

### CLI Usage

```bash
# Use named pattern from config
opencode run "Write a function" --multi-model code_review

# Quick sequential pattern with specified models
opencode run "Write a function" --pattern sequential --models llama3.2 --models mistral:7b

# Quick ensemble pattern
opencode run "Analyze this code" --pattern ensemble --models llama3.2 --models mistral:7b --models codellama:7b
```

### REST API

```bash
# List available patterns
curl http://localhost:4096/workflows/multi-model/patterns

# Execute multi-model pattern
curl -X POST http://localhost:4096/workflows/multi-model/execute \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a Python function",
    "pattern_name": "code_review"
  }'

# Ad-hoc pattern execution
curl -X POST http://localhost:4096/workflows/multi-model/execute \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a Python function",
    "pattern": "sequential",
    "models": [
      {"model": "llama3.2", "provider": "ollama"},
      {"model": "mistral:7b", "provider": "ollama"}
    ]
  }'
```

---

## Multi-GPU Support

OpenCode supports multi-GPU configurations for running multiple models in parallel across different GPUs. This is especially useful for ensemble patterns where each model can run on a dedicated GPU.

### GPU Configuration

Add to `opencode.toml`:

```toml
[gpu]
strategy = "auto"              # auto, round_robin, pack, spread, manual
vram_threshold_percent = 85.0  # Don't allocate if GPU above this usage
allow_shared_gpu = true        # Allow multiple models on same GPU
auto_unload = true             # Auto-unload models when VRAM is low
reserved_vram_gb = 1.0         # Reserve VRAM for system

# Multi-model pattern with GPU affinity
[multi_model_patterns.gpu_ensemble]
pattern = "ensemble"
enabled = true

[[multi_model_patterns.gpu_ensemble.models]]
model = "llama3.2:70b"
provider = "ollama"
gpu_id = 0              # Run on GPU 0
vram_required_gb = 40.0 # Estimated VRAM requirement

[[multi_model_patterns.gpu_ensemble.models]]
model = "mistral:7b"
provider = "ollama"
gpu_id = 1              # Run on GPU 1
vram_required_gb = 16.0
```

### GPU Allocation Strategies

| Strategy | Description |
|----------|-------------|
| `auto` | Automatically select GPU with most free memory |
| `round_robin` | Distribute models evenly across GPUs |
| `pack` | Fill GPUs in order (GPU 0 first) |
| `spread` | Use least utilized GPU first |
| `manual` | Use explicitly configured GPU IDs only |

### REST API for GPU Management

```bash
# Get GPU status
curl http://localhost:4096/workflows/gpu/status

# Allocate GPU for a model
curl -X POST http://localhost:4096/workflows/gpu/allocate \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "llama3.2:70b",
    "vram_required_gb": 40.0,
    "preferred_gpu_id": 0
  }'

# Release GPU allocation
curl -X POST http://localhost:4096/workflows/gpu/release \
  -H "Content-Type: application/json" \
  -d '{"model_id": "llama3.2:70b"}'

# Get allocation recommendations
curl -X POST http://localhost:4096/workflows/gpu/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "models": [
      {"model_id": "llama3.2:70b", "vram_required_gb": 40.0},
      {"model_id": "mistral:7b", "vram_required_gb": 16.0}
    ]
  }'
```

---

## Development

```bash
# Clone
git clone https://github.com/RTPro256/opencode_4py.git
cd opencode_4py

# Create venv
python -m venv .venv
source .venv/bin/activate

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/
```

---

## Project Structure

```
opencode_4py/
├── src/opencode/
│   ├── cli/           # CLI commands
│   ├── core/          # Core logic (session, config)
│   ├── providers/     # AI providers
│   ├── tools/         # Built-in tools
│   ├── lsp/           # Language server integration
│   ├── mcp/           # MCP client/server
│   ├── tui/           # Terminal UI (Textual)
│   ├── web/           # Web interface (FastAPI)
│   ├── i18n/          # Internationalization
│   └── git/           # Git integration
├── docs/              # Documentation
├── tests/             # Test suite
└── pyproject.toml     # Project config
```

---

## Comparison with Original

| Feature | TypeScript | Python |
|---------|------------|--------|
| CLI Commands | ✅ | ✅ |
| Terminal UI | ✅ | ✅ |
| AI Providers | 18 | 18 |
| Tools | 21 | 21 |
| LSP Support | ✅ | ✅ |
| MCP Client | ✅ | ✅ |
| MCP Server | ✅ | ✅ |
| HTTP Server | ✅ | ✅ |
| Web Interface | ✅ | ✅ |
| Desktop App | ✅ | ❌ |
| i18n | 17+ | 17+ |

See [FEATURE_COVERAGE.md](docs/FEATURE_COVERAGE.md) for detailed comparison.

---

## Contributing

Contributions are welcome! Please:

1. Check [FEATURE_COVERAGE.md](docs/FEATURE_COVERAGE.md) for unimplemented features
2. Review [DOCS_INDEX.md](docs/DOCS_INDEX.md) for documentation structure
3. Submit a pull request

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- Original [OpenCode](https://github.com/anomalyco/opencode) team for the inspiration
- [Anthropic](https://anthropic.com) for Claude
- [Textual](https://textual.textualize.io/) for the TUI framework
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework

---

<div align="center">

**[Getting Started](docs/README.md#quick-start)** • **[Documentation](docs/README.md)** • **[Report Bug](https://github.com/RTPro256/opencode_4py/issues)**

</div>
