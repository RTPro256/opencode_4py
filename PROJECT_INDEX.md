# OpenCode Python - Project Index

> **Navigation Hub** - Quick access to project overview and structure

---

## Quick Links

| Resource | Description |
|----------|-------------|
| [README.md](README.md) | Project overview and quick start |
| [TODO.md](TODO.md) | Task tracking and pending work |
| [CHANGELOG.md](CHANGELOG.md) | Version history and changes |
| [PLAN_INDEX.md](plans/PLAN_INDEX.md) | All plans and project tracking |
| [DOCS_INDEX.md](docs/DOCS_INDEX.md) | Documentation navigation |

---

## Project Overview

OpenCode Python is an AI-powered coding assistant built with Python, featuring:
- **TUI (Terminal User Interface)**: Interactive terminal interface
- **RAG (Retrieval-Augmented Generation)**: Local knowledge base integration
- **Multi-Provider Support**: Anthropic, OpenAI, Ollama, and more
- **Tool System**: File operations, code analysis, shell execution
- **Agent System**: Multi-agent orchestration with mode switching

---

## Directory Structure

```
opencode_4py/
├── src/opencode/src/opencode/   # Main source code
│   ├── cli/                     # CLI commands
│   │   └── commands/            # Command modules (rag, config, debug, etc.)
│   ├── core/                    # Core functionality
│   │   ├── modes/               # Mode implementations (code, debug, ask, etc.)
│   │   ├── orchestration/       # Agent orchestration
│   │   ├── providers/           # AI provider integrations
│   │   ├── rag/                 # RAG implementation
│   │   ├── skills/              # Built-in skills
│   │   └── tools/               # Tool implementations
│   ├── tui/                     # Terminal UI
│   │   ├── widgets/             # UI widgets
│   │   ├── quick_commands.py    # Quick slash commands
│   │   └── app.py               # Main TUI application
│   ├── provider/                # Provider implementations
│   └── ...
├── docs/                        # Documentation
├── plans/                       # Project plans
├── RAG/                        # RAG data and troubleshooting
├── config/                     # Configuration presets
└── examples/                   # Usage examples
```

---

## Key Source Files

### CLI Commands

| File | Purpose | Lines |
|------|---------|-------|
| `cli/commands/rag.py` | RAG command aggregator | 71 |
| `cli/commands/debug_cmd.py` | Debug/troubleshoot commands | ~250 |
| `cli/commands/config.py` | Configuration management | ~350 |
| `cli/commands/github.py` | GitHub integration | ~600 |

### Core Modules

| File | Purpose | Status |
|------|---------|--------|
| `core/orchestration/agent.py` | Agent base class | Complete |
| `core/tools/base.py` | Tool base class | Complete |
| `core/rag/local_embeddings.py` | Local embedding generation | Complete |
| `core/modes/manager.py` | Mode management | Complete |

### TUI

| File | Purpose | Lines |
|------|---------|-------|
| `tui/app.py` | Main TUI application | 1026 |
| `tui/quick_commands.py` | Slash commands | 454 |

---

## Modes

OpenCode operates in different modes that control AI behavior:

| Mode | Purpose |
|------|---------|
| `code` | Code writing/editing (default) |
| `ask` | Question answering |
| `debug` | Debugging and troubleshooting |
| `architect` | Planning and architecture |
| `review` | Code review |
| `orchestrator` | Task orchestration |

---

## Providers

Supported AI providers:

| Provider | Models | Status |
|----------|--------|--------|
| Anthropic | Claude 3.5 Sonnet, Haiku | ✅ |
| OpenAI | GPT-4o, GPT-4o-mini | ✅ |
| Ollama | Llama, Qwen, etc. | ✅ |
| Google | Gemini 2.0 Flash | ✅ |
| OpenRouter | Multiple | ✅ |
| Groq | Llama, Mixtral | ✅ |

---

## RAG System

### Error Documentation

17 documented errors in [`RAG/troubleshooting/errors/`](RAG/troubleshooting/errors/):

- ERR-001 to ERR-017: Common integration errors with fixes

### RAG Methods

9 RAG methods implemented:
- NaiveRAG, SelfRAG, AgenticRAG, CorrectiveRAG
- HyDE, FusionRetrieval, GraphRAG, RerankerRAG, AdvancedRAG

---

## Quick Commands (TUI)

In the TUI, use these slash commands:

```
/help    - Show all commands
/index   - Show PROJECT_INDEX.md
/plans   - Show PLAN_INDEX.md
/docs    - Show DOCS_INDEX.md
/files   - List Python files
/tools   - Show available tools
/agents  - Show agents
/mode    - Show/change mode
/status  - Show system status
/clear   - Clear chat
/theme   - Change theme
```

---

## Configuration

Configuration is stored in `~/.config/opencode/config.toml` or use presets in [`config/presets/`](config/presets/):

- `claude.toml` - Anthropic configuration
- `openai.toml` - OpenAI configuration
- `local.toml` - Ollama local setup
- `multi-provider.toml` - Multi-provider setup

---

## Testing

Testing infrastructure in [`plans/TESTING_PLAN.md`](plans/TESTING_PLAN.md):
- Unit tests
- Integration tests
- UAT (User Acceptance Testing)

---

## Recent Updates

- ✅ Debug command implemented (`opencode debug "issue"`)
- ✅ TUI quick commands updated
- ✅ 17 RAG errors documented
- ✅ Local embedding support
- ✅ Privacy-first RAG architecture

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

---

*Last updated: 2026-03-01*
