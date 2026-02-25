# OpenCode Python

A Python rewrite of [OpenCode](https://github.com/anomalyco/opencode) - an AI-powered code assistant with terminal UI, LSP support, and MCP integration.

## Features

- **Terminal UI**: Rich, interactive terminal interface built with Textual
- **Multiple AI Providers**: Support for Anthropic Claude, OpenAI GPT, Google Gemini, and more
- **LSP Integration**: Code intelligence via Language Server Protocol
- **MCP Support**: Extensible tool system via Model Context Protocol
- **HTTP Server**: REST API and WebSocket endpoints for remote access
- **Session Management**: Persistent conversation history with SQLite database

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

OpenCode uses TOML configuration files. The main config file is located at:

- Linux/macOS: `~/.config/opencode/config.toml`
- Windows: `%APPDATA%\opencode\config.toml`

### Example Configuration

```toml
[provider.anthropic]
api_key = "your-anthropic-api-key"
default_model = "claude-3-5-sonnet-20241022"

[provider.openai]
api_key = "your-openai-api-key"
default_model = "gpt-4o"

[provider.google]
api_key = "your-google-api-key"
default_model = "gemini-2.0-flash-exp"

[settings]
default_provider = "anthropic"
theme = "dark"
max_tokens = 8192
temperature = 0.7

[mcp.servers.filesystem]
command = "mcp-filesystem"
args = ["/path/to/project"]

[mcp.servers.github]
command = "mcp-github"
env = { GITHUB_TOKEN = "your-github-token" }
```

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
opencode upgrade            # Upgrade to latest version
opencode uninstall          # Uninstall OpenCode
```

### RAG Commands

OpenCode includes a privacy-first RAG (Retrieval-Augmented Generation) system:

```bash
# Create a RAG index
opencode rag create troubleshooting --source ./docs

# Query the RAG
opencode rag query troubleshooting "TUI stalls at Thinking"

# Share RAG with community
opencode rag get troubleshooting              # Download from community
opencode rag share troubleshooting            # Share to community
opencode rag list-remote                      # List available RAGs
opencode rag merge target source              # Merge two RAGs
```

See [RAG Sharing Guide](../../docs/RAG_SHARING.md) for details.

## Troubleshooting

OpenCode includes a simplified troubleshooting system that automatically queries a knowledge base of known errors.

### Quick Debug

```bash
# Debug an issue with automatic RAG lookup
opencode debug "TUI stalls at Thinking"

# Troubleshoot alias
opencode troubleshoot "button not appearing"

# Auto-apply fix if found
opencode debug "TUI stalls at Thinking" --fix

# List all known errors
opencode debug errors

# Create debug log
opencode debug log
```

### How It Works

1. **Automatic Logging**: Debug command enables debug logging automatically
2. **RAG Query**: Searches troubleshooting knowledge base for matching errors
3. **Fix Display**: Shows relevant error documents with step-by-step fixes
4. **Confidence Score**: Indicates how closely the error matches your issue

### Example Output

```
$ opencode debug "TUI stalls at Thinking"

Enabling debug logging...
Log file: docs/opencode/logs/debug_2026-02-23.log

Querying troubleshooting RAG...
Found 2 matching errors:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ERR-010: Async Generator Await Error (CRITICAL)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Symptom: TUI stalls at "Thinking..." indefinitely after user sends a message.

Root Cause: The provider.complete() method is an async generator that should
NOT be awaited.

Fix:
  1. Open: opencode/tui/app.py
  2. Find line: async for chunk in await self.provider.complete(...)
  3. Remove 'await': async for chunk in self.provider.complete(...)

Confidence: 95% match

Apply fix? [y/N]
```

### Debug Mode

The debug mode is optimized for troubleshooting:
- Access to RAG tools for querying troubleshooting knowledge
- System prompts guide AI to check known errors first
- Methodical approach: reproduce, isolate, analyze, fix

```bash
# Start TUI in debug mode
opencode run --mode debug
```

## HTTP API

When running the HTTP server, the following endpoints are available:

### Chat

- `POST /api/chat/message` - Send a message
- `POST /api/chat/stream` - Stream a response
- `WebSocket /api/chat/ws/{session_id}` - Real-time chat
- `GET /api/chat/history/{session_id}` - Get chat history

### Sessions

- `GET /api/sessions` - List sessions
- `POST /api/sessions` - Create session
- `GET /api/sessions/{id}` - Get session
- `DELETE /api/sessions/{id}` - Delete session

### Models

- `GET /api/models` - List providers and models
- `GET /api/models/{provider}` - Get provider models

### Tools

- `GET /api/tools` - List available tools
- `POST /api/tools/execute` - Execute a tool
- `GET /api/tools/mcp/list` - List MCP tools

### Files

- `GET /api/files/list` - List directory contents
- `GET /api/files/read` - Read file content
- `POST /api/files/write` - Write file content
- `POST /api/files/search` - Search files

## Architecture

```
opencode/
├── cli/           # CLI commands and entry point
├── core/          # Core business logic (config, sessions)
├── db/            # Database layer (SQLAlchemy async)
├── mcp/           # MCP client implementation
├── provider/      # AI provider implementations
├── server/        # HTTP server (FastAPI)
├── tool/          # Tool implementations
├── tui/           # Terminal UI (Textual)
└── util/          # Utilities (logging, etc.)
```

## Dependencies

### Core
- Python 3.12+
- typer - CLI framework
- textual - Terminal UI
- fastapi - HTTP server
- uvicorn - ASGI server
- sqlalchemy - ORM (async)
- aiosqlite - Async SQLite
- httpx - HTTP client
- pydantic - Data validation

### Optional
- watchdog - File watching
- rich - Rich text output

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
mypy .
```

## License

MIT License - see LICENSE file for details.

## Acknowledgments

This is a Python rewrite of the original [OpenCode](https://github.com/anomalyco/opencode) project by anomalyco. The original project is written in TypeScript and uses Bun runtime.

## Contributing

Contributions are welcome! Please read the contributing guidelines before submitting a pull request.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## Status

This project is under active development. See the [rewrite plan](plans/opencode_python_rewrite_plan.md) for implementation progress.
