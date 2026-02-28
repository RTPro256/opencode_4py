# OpenCode

A Python rewrite of [OpenCode](https://github.com/anomalyco/opencode) - an AI-powered code assistant with terminal UI, LSP support, and MCP integration.

## Overview

OpenCode is a powerful, provider-agnostic AI coding assistant built in Python. It features a rich terminal interface, supports multiple AI providers, and includes advanced features like RAG (Retrieval-Augmented Generation), session management, and extensibility through MCP (Model Context Protocol).

## Quick Links

| Document | Description |
|----------|-------------|
| [Main Package README](src/opencode/README.md) | Python package details, installation, and CLI usage |
| [Documentation Index](docs/README.md) | Comprehensive documentation covering all features |
| [Configuration Presets](config/presets/README.md) | Ready-to-use configuration templates |
| [Examples](examples/README.md) | Code examples for basic usage, RAG, and providers |
| [RAG System](RAG/README.md) | Retrieval-Augmented Generation documentation |
| [Troubleshooting RAG](RAG/troubleshooting/README.md) | Error documentation and diagnosis workflows |

## Features

- **Terminal UI**: Rich, interactive terminal interface built with Textual
- **Multiple AI Providers**: Support for Anthropic Claude, OpenAI GPT, Google Gemini, and more (15+ providers)
- **LSP Integration**: Code intelligence via Language Server Protocol
- **MCP Support**: Extensible tool system via Model Context Protocol
- **HTTP Server**: REST API and WebSocket endpoints for remote access
- **Session Management**: Persistent conversation history with SQLite database
- **Privacy-First RAG**: Local vector storage for knowledge retrieval
- **Troubleshooting System**: Built-in debug agent with error knowledge base
- **Internationalization**: Multi-language support (English, Spanish, Japanese, Chinese)

## Project Structure

```
opencode/
├── src/opencode/           # Main Python package
│   ├── README.md          # Package documentation
│   ├── cli/               # CLI commands
│   ├── core/              # Core business logic
│   ├── provider/          # AI provider implementations
│   ├── server/            # HTTP server (FastAPI)
│   ├── mcp/               # MCP client implementation
│   ├── router/            # Request routing
│   ├── session/           # Session management
│   ├── skills/            # Skill discovery
│   ├── llmchecker/        # LLM calibration & scoring
│   ├── i18n/              # Internationalization
│   ├── rag/               # RAG implementation
│   ├── tool/              # Tool implementations
│   ├── tui/               # Terminal UI
│   └── util/              # Utilities
│
├── docs/                  # Project documentation
│   ├── README.md          # Documentation index
│   ├── STYLE_GUIDE.md     # Code style guide
│   ├── TUTORIAL.md        # Getting started tutorial
│   ├── RAG_SHARING.md     # RAG sharing guide
│   ├── TEST_DISCOVERY.md  # Testing documentation
│   └── api/               # API documentation
│
├── config/                # Configuration files
│   └── presets/           # Configuration templates
│       └── README.md      # Presets guide
│
├── examples/              # Usage examples
│   ├── README.md          # Examples index
│   ├── basic_usage.py     # Basic API usage
│   ├── provider_config.py # Provider configuration
│   └── rag_example.py    # RAG example
│
├── RAG/                   # RAG knowledge bases
│   ├── README.md          # RAG system overview
│   ├── agent_code/        # Code agent RAG
│   ├── plan_testing/     # Testing plan RAG
│   ├── troubleshooting/   # Troubleshooting RAG
│   │   └── README.md     # Troubleshooting guide
│   └── bug_detected/      # Bug detection RAG
│
├── plans/                 # Project planning documents
├── scripts/               # Utility scripts
├── aimodels/              # AI model configurations
└── python_embeded/        # Embedded Python
```

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/opencode-python.git
cd opencode-python

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

For detailed installation instructions, see [src/opencode/README.md](src/opencode/README.md#installation).

## Quick Start

```bash
# Start the TUI
opencode

# Start with a specific model
opencode --model claude-3-5-sonnet-20241022

# Start the HTTP server
opencode serve --port 3000

# Configure API keys
opencode auth set anthropic YOUR_API_KEY
opencode auth set openai YOUR_API_KEY
```

## Configuration

OpenCode uses TOML configuration files. See [Configuration Presets](config/presets/README.md) for ready-to-use templates:

| Preset | Description | Requirements |
|--------|-------------|--------------|
| `claude.toml` | Anthropic Claude configuration | `ANTHROPIC_API_KEY` |
| `openai.toml` | OpenAI GPT configuration | `OPENAI_API_KEY` |
| `local.toml` | Local Ollama configuration | Ollama installed |
| `multi-provider.toml` | Multi-provider setup | Multiple API keys |

### Supported Providers

| Provider | Models | Environment Variable |
|----------|--------|---------------------|
| Anthropic | Claude 4, Claude 3.5 | `ANTHROPIC_API_KEY` |
| OpenAI | GPT-4o, GPT-4, o1, o3 | `OPENAI_API_KEY` |
| Google | Gemini 2.0, Gemini 1.5 | `GOOGLE_API_KEY` |
| Azure | GPT-4, GPT-4o | `AZURE_OPENAI_API_KEY` |
| AWS Bedrock | Claude, Llama, Mistral | AWS credentials |
| Groq | Llama, Mixtral | `GROQ_API_KEY` |
| Mistral | Mistral Large, Codestral | `MISTRAL_API_KEY` |
| Ollama | Local models | (local) |
| LM Studio | Local models | (local) |
| And more... | | |

See [docs/README.md](docs/README.md#providers) for the complete list.

## CLI Commands

```bash
opencode                    # Start TUI (default)
opencode run "prompt"       # Run a single prompt
opencode serve              # Start HTTP server
opencode auth               # Manage API keys
opencode config             # View/edit configuration
opencode models             # List available models
opencode session            # Manage sessions
opencode mcp                # Manage MCP servers
opencode rag                # RAG management commands
opencode debug              # Debug issues with RAG lookup
opencode github             # GitHub sync and repository management
opencode upgrade            # Upgrade to latest version
opencode uninstall          # Uninstall OpenCode
```

## RAG System

OpenCode includes a privacy-first RAG (Retrieval-Augmented Generation) system:

```bash
# Create a RAG index
opencode rag create troubleshooting --source ./docs

# Query the RAG
opencode rag query troubleshooting "TUI stalls at Thinking"

# Share RAG with community
opencode rag share troubleshooting
opencode rag get troubleshooting
opencode rag list-remote
```

See [RAG/README.md](RAG/README.md) for detailed RAG documentation.

## Troubleshooting

OpenCode includes a built-in troubleshooting system with an error knowledge base:

```bash
# Debug an issue with automatic RAG lookup
opencode debug "TUI stalls at Thinking"

# List all known errors
opencode debug errors

# Auto-apply fix if found
opencode debug "TUI stalls at Thinking" --fix
```

The troubleshooting RAG contains 17+ documented errors with solutions. See [RAG/troubleshooting/README.md](RAG/troubleshooting/README.md) for details.

## HTTP API

When running the HTTP server (`opencode serve`), the following endpoints are available:

### Chat
- `POST /api/chat/message` - Send a message
- `POST /api/chat/stream` - Stream a response
- `WebSocket /api/chat/ws/{session_id}` - Real-time chat

### Sessions
- `GET /api/sessions` - List sessions
- `POST /api/sessions` - Create session
- `GET /api/sessions/{id}` - Get session
- `DELETE /api/sessions/{id}` - Delete session

### Tools
- `GET /api/tools` - List available tools
- `POST /api/tools/execute` - Execute a tool

See [docs/README.md](docs/README.md) for the complete API reference.

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .

# Format code
ruff format .

# Type checking
mypy src/opencode
```

## Documentation

| Topic | Documentation |
|-------|---------------|
| Installation | [src/opencode/README.md](src/opencode/README.md#installation) |
| Configuration | [config/presets/README.md](config/presets/README.md) |
| Providers | [docs/README.md](docs/README.md#providers) |
| Tools | [docs/README.md](docs/README.md#tools) |
| RAG | [RAG/README.md](RAG/README.md) |
| Troubleshooting | [RAG/troubleshooting/README.md](RAG/troubleshooting/README.md) |
| API Reference | [docs/README.md](docs/README.md#api-reference) |
| Style Guide | [docs/STYLE_GUIDE.md](docs/STYLE_GUIDE.md) |
| Tutorial | [docs/TUTORIAL.md](docs/TUTORIAL.md) |
| Feature Verification | [docs/FEATURE_VERIFICATION.md](docs/FEATURE_VERIFICATION.md) |
| Bug Detection | [docs/BUG_DETECTION_PROCESS.md](docs/BUG_DETECTION_PROCESS.md) |

## License

MIT License - see LICENSE file for details.

## Acknowledgments

This is a Python rewrite of the original [OpenCode](https://github.com/anomalyco/opencode) project by anomalyco. The original project is written in TypeScript and uses Bun runtime.

## Contributing

Contributions are welcome! Please read the [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a pull request.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## Status

This project is under active development. See [plans/](plans/) for implementation progress and upcoming features.
