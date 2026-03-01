# OpenCode Python - Interactive Tutorial

Welcome to the OpenCode Python interactive tutorial! This guide will walk you through the key features and capabilities of OpenCode.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Configuration](#configuration)
3. [Using the CLI](#using-the-cli)
4. [RAG (Retrieval-Augmented Generation)](#rag-retrieval-augmented-generation)
5. [Providers and Models](#providers-and-models)
6. [Advanced Features](#advanced-features)

---

## Getting Started

### Installation

```bash
# Clone the repository
git clone https://github.com/RTPro256/opencode_4py.git
cd opencode_4py

# Install in development mode
cd src/opencode
pip install -e .
```

### Verify Installation

```bash
# Check version
opencode --version

# Show help
opencode --help
```

---

## Configuration

### Using the Config Wizard

The easiest way to configure OpenCode is with the interactive wizard:

```bash
opencode config wizard
```

This will guide you through:
1. Setting your default provider
2. Configuring API keys
3. Setting default models
4. Configuring generation settings (max tokens, temperature)
5. Setting up MCP servers (optional)

### Manual Configuration

Configuration is stored in `~/.config/opencode/config.toml`:

```toml
[provider.anthropic]
api_key = "your-api-key"
default_model = "claude-3-5-sonnet-20241022"

[provider.openai]
api_key = "your-api-key"
default_model = "gpt-4o"

[settings]
default_provider = "anthropic"
max_tokens = 8192
temperature = 0.7
theme = "dark"
```

### View Current Configuration

```bash
# Show all configuration
opencode config show

# Get a specific value
opencode config get settings.default_provider

# Set a value
opencode config set settings.temperature 0.5
```

---

## Using the CLI

### Starting a Chat Session

```bash
# Start interactive TUI
opencode run

# Start with a specific model
opencode run --model gpt-4o

# Start with a specific provider
opencode run --provider openai
```

### Keyboard Shortcuts (TUI)

| Key | Action |
|-----|--------|
| `Ctrl+N` | New session |
| `Ctrl+S` | Save session |
| `Ctrl+O` | Open session |
| `Ctrl+M` | Toggle model |
| `Ctrl+Shift+M` | Toggle mode |
| `Ctrl+Q` | Quit |
| `Ctrl+T` | Toggle debug logging |
| `F1` | Help |
| `Escape` | Cancel/Stop |

### Quick Commands (Slash Commands)

In the TUI, you can type these slash commands in the chat input:

| Command | Description |
|---------|-------------|
| `/help` | Show this help |
| `/index` | Show PROJECT_INDEX.md summary |
| `/plans` | Show PLAN_INDEX.md summary |
| `/docs` | Show DOCS_INDEX.md summary |
| `/files` | Show all Python files with summaries |
| `/tools` | Show all available tools |
| `/agents` | Show all available subagents |
| `/mode` | Show/change current mode |
| `/status` | Show system status |
| `/clear` | Clear chat history |
| `/theme` | Toggle theme (dark/light/catppuccin/nord) |

### Modes vs Agents

OpenCode has two distinct concepts:

**Modes** define session-wide behavior:
- `Architect` - Planning and architecture design
- `Ask` - Question answering mode
- `Code` - Code writing/editing (default)
- `Debug` - Debugging and troubleshooting
- `Review` - Code review
- `Orchestrator` - Task orchestration

**Agents** (Subagents) are specialized task-specific workers you can invoke dynamically during conversation. They are different from modes - agents handle specific subtasks while modes control overall AI behavior.

---

## RAG (Retrieval-Augmented Generation)

RAG allows you to create knowledge bases from your documents and query them.

### Creating a RAG Index

```bash
# Create a RAG index for an agent
opencode rag create my-agent --source ./docs --source ./src

# With custom settings
opencode rag create my-agent \
    --source ./docs \
    --model nomic-embed-text \
    --store file \
    --output ./RAG
```

### Querying a RAG Index

```bash
# Query your RAG
opencode rag query my-agent "How do I configure providers?"

# Get more results
opencode rag query my-agent "installation steps" --top-k 10

# JSON output
opencode rag query my-agent "API usage" --format json
```

### Managing RAG Indexes

```bash
# Add more sources
opencode rag add my-agent ./more-docs

# Show status
opencode rag status my-agent

# Show detailed stats
opencode rag stats my-agent

# View audit log
opencode rag audit my-agent --days 30
```

### Content Validation

```bash
# Mark content as false (for regeneration)
opencode rag mark-false my-agent "incorrect content" \
    --source ./docs/guide.md \
    --reason "Outdated information"

# List false content
opencode rag list-false my-agent

# Regenerate index after corrections
opencode rag regenerate my-agent
```

### Community RAG Sharing

```bash
# List available community RAGs
opencode rag list-remote

# Download a community RAG
opencode rag get troubleshooting

# Download from a specific repository
opencode rag get troubleshooting --from user/community-rag

# Merge RAG indexes
opencode rag merge target-agent source-agent
```

---

## Providers and Models

### Supported Providers

| Provider | Models |
|----------|--------|
| Anthropic | Claude 3.5 Sonnet, Claude 3.5 Haiku |
| OpenAI | GPT-4o, GPT-4o-mini |
| Google | Gemini 2.0 Flash |
| Ollama | Llama 3.2, Qwen, and more |
| OpenRouter | Multiple models |
| Groq | Llama, Mixtral |
| Mistral | Mistral, Codestral |

### Using Different Providers

```bash
# List available models
opencode run --list-models

# Use a specific model
opencode run --model claude-3-5-sonnet-20241022

# Use Ollama (local)
opencode run --provider ollama --model llama3.2
```

### Provider Configuration

Each provider can be configured with:

```toml
[provider.anthropic]
api_key = "sk-ant-..."
default_model = "claude-3-5-sonnet-20241022"

[provider.ollama]
# No API key needed for local
base_url = "http://localhost:11434"
default_model = "llama3.2"
```

---

## Advanced Features

### LLM Checker

Validate and score LLM outputs:

```bash
# Run accuracy check
opencode llmchecker check "What is 2+2?" --expected "4"

# Run with confidence scoring
opencode llmchecker score "Explain quantum computing"
```

### Debug Mode

```bash
# Enable verbose logging
opencode run --debug

# View logs
opencode run --view-logs
```

### Session Management

Sessions are automatically saved in your project's `.opencode/sessions/` directory.

```bash
# Sessions are stored with timestamps
# You can resume by checking the session directory
ls .opencode/sessions/
```

### MCP (Model Context Protocol)

Configure MCP servers for extended capabilities:

```toml
[mcp.servers.filesystem]
command = "mcp-filesystem"
args = ["/path/to/project"]

[mcp.servers.github]
command = "mcp-github"
env = { GITHUB_TOKEN = "your-token" }
```

---

## Tips and Best Practices

### 1. Use the Config Wizard for Initial Setup

The wizard ensures all required settings are configured correctly:

```bash
opencode config wizard
```

### 2. Create RAG Indexes for Large Codebases

For projects with extensive documentation:

```bash
opencode rag create project-docs --source ./docs --source ./README.md
```

### 3. Use Appropriate Models for Tasks

- **Code generation**: Claude 3.5 Sonnet, GPT-4o
- **Quick tasks**: Claude 3.5 Haiku, GPT-4o-mini
- **Local/Offline**: Ollama with Llama 3.2

### 4. Enable Debug Logging for Troubleshooting

```bash
# In the TUI, press Ctrl+T to toggle logging
# Or run with debug flag
opencode run --debug
```

### 5. Keep RAG Indexes Updated

When documentation changes:

```bash
opencode rag add my-agent ./updated-docs
# Or regenerate
opencode rag regenerate my-agent
```

---

## Getting Help

- **CLI Help**: `opencode --help` or `opencode <command> --help`
- **TUI Help**: Press `F1` in the TUI
- **Documentation**: Check the `docs/` directory
- **Issues**: https://github.com/RTPro256/opencode_4py/issues

---

## Next Steps

1. Run `opencode config wizard` to set up your configuration
2. Try `opencode run` to start an interactive session
3. Create a RAG index for your project documentation
4. Explore different models and providers

Happy coding with OpenCode!
