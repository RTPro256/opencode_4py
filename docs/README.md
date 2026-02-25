# OpenCode Python - Documentation

OpenCode Python is a complete rewrite of the OpenCode AI coding agent in Python. It provides a powerful, provider-agnostic AI assistant for software development.

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [Features](#features)
5. [Providers](#providers)
6. [Tools](#tools)
7. [MCP Integration](#mcp-integration)
8. [LSP Support](#lsp-support)
9. [Web Interface](#web-interface)
10. [Internationalization](#internationalization)
11. [Example Workflows](#example-workflows)
12. [API Reference](#api-reference)
13. [Troubleshooting](#troubleshooting)

---

## Installation

### Requirements

- Python 3.12 or higher
- pip or uv package manager

### Install from PyPI

```bash
pip install opencode-ai
```

### Install from Source

```bash
git clone https://github.com/RTPro256/opencode_4py.git
cd opencode_4py
pip install -e .
```

### Development Setup

```bash
# Clone the repository
git clone https://github.com/RTPro256/opencode_4py.git
cd opencode_4py

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check src/

# All tests
pytest src/opencode/tests/

# Unit tests only
pytest src/opencode/tests/unit/

# Skip slow tests
pytest -m "not slow"

# Run Ollama tests (requires Ollama running)
pytest -m ollama
```

---

## Quick Start

### 1. Set Up API Key

```bash
# Set your API key (choose one)
export ANTHROPIC_API_KEY=your-key-here  # For Claude
export OPENAI_API_KEY=your-key-here      # For GPT
export GOOGLE_API_KEY=your-key-here      # For Gemini
```

### 2. Launch OpenCode

```bash
# Launch in current directory
opencode

# Launch in specific directory
opencode /path/to/project

# Start HTTP server
opencode serve --port 4096

# Open web interface
opencode web
```

### 3. Basic Usage

Once launched, you can interact with OpenCode using natural language:

```
> Read the main.py file and explain what it does

> Add error handling to the process_data function

> Find all TODO comments in the codebase

> Run the tests and fix any failures
```

---

## Configuration

### Configuration File

OpenCode uses TOML configuration files. Create `opencode.toml` in your project root:

```toml
# opencode.toml

[provider]
default = "anthropic"

[provider.anthropic]
api_key_env = "ANTHROPIC_API_KEY"
model = "claude-sonnet-4-20250514"

[provider.openai]
api_key_env = "OPENAI_API_KEY"
model = "gpt-4o"

[tools]
# Enable/disable specific tools
bash = true
read = true
write = true
edit = true
websearch = true

[permissions]
# Auto-approve safe commands
bash_allow = ["git status", "git log", "ls", "cat"]

[mcp]
# MCP server configurations
servers = ["filesystem", "github"]

[ui]
theme = "dark"
language = "en"
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `OPENAI_API_KEY` | OpenAI API key |
| `GOOGLE_API_KEY` | Google API key |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint |
| `AWS_ACCESS_KEY_ID` | AWS access key for Bedrock |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key for Bedrock |
| `AWS_REGION` | AWS region (default: us-east-1) |
| `GROQ_API_KEY` | Groq API key |
| `MISTRAL_API_KEY` | Mistral API key |
| `COHERE_API_KEY` | Cohere API key |
| `XAI_API_KEY` | xAI API key |
| `PERPLEXITY_API_KEY` | Perplexity API key |
| `TOGETHER_API_KEY` | Together AI API key |
| `CEREBRAS_API_KEY` | Cerebras API key |
| `DEEPINFRA_API_KEY` | DeepInfra API key |
| `OPENROUTER_API_KEY` | OpenRouter API key |
| `OPENCODE_CONFIG` | Custom config file path |
| `OPENCODE_DATA_DIR` | Custom data directory |
| `OPENCODE_SERVER_PASSWORD` | HTTP server password |

### Configuration Profiles

Create multiple profiles for different environments:

```toml
# opencode.toml

[profiles.development]
provider = "anthropic"
model = "claude-sonnet-4-20250514"

[profiles.production]
provider = "openai"
model = "gpt-4o"

[profiles.local]
provider = "ollama"
model = "llama3.2"
base_url = "http://localhost:11434"
```

Switch profiles:

```bash
opencode --profile development
```

---

## Features

### Terminal UI (TUI)

OpenCode provides a rich terminal interface built with Textual:

- **Chat View**: Message history with syntax highlighting
- **Input Box**: Multiline input with auto-completion
- **Tool Output**: Formatted tool results with expandable sections
- **File Preview**: View files with syntax highlighting
- **Diff View**: Side-by-side diff for code changes
- **Status Bar**: Session info, model, token usage
- **Sidebar**: Session/project navigation
- **Help Panel**: Keyboard shortcuts

#### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Tab` | Switch agent (build/plan) |
| `Ctrl+N` | New session |
| `Ctrl+S` | Save session |
| `Ctrl+Q` | Quit |
| `Ctrl+H` | Toggle help |
| `Ctrl+P` | Command palette |
| `Ctrl+L` | Clear chat |
| `↑/↓` | Navigate history |
| `Esc` | Cancel action |

### Agents

OpenCode includes two built-in agents:

#### Build Agent (Default)
- Full access to all tools
- Can read, write, and execute commands
- Best for development work

#### Plan Agent
- Read-only access
- Cannot modify files
- Asks permission before running commands
- Best for code exploration and planning

Switch agents with `Tab` key or:

```
> @plan Analyze the architecture of this project
> @build Implement the suggested changes
```

### Session Management

Sessions are automatically saved and can be resumed:

```bash
# List sessions
opencode session list

# Resume session
opencode session resume <session-id>

# Export session
opencode export <session-id> -o session.json

# Import session
opencode import session.json
```

#### Session Storage Location

Session files are stored in JSON format with the naming convention:
`session_{YYYY-MM-DD_HH-MM-SS}_{short_id}.json`

| Setting | Session Location |
|---------|-----------------|
| `project_dir` configured in `opencode.toml` | `{project_dir}/docs/opencode/sessions/` |
| Running from project root | `./docs/sessions/` |
| No `project_dir` setting | `~/.local/share/opencode/sessions/` |

**Example session filename:** `session_2026-02-23_12-07-27_ea99a867.json`

**TUI Keyboard Shortcuts:**
- `Ctrl+S` - Save current session (auto-saved by default)
- `Ctrl+N` - New session
- `Ctrl+O` - Open session browser

### Context Compaction

OpenCode automatically compacts conversation history when it exceeds the context limit:

- Summarizes old messages
- Preserves important context
- Maintains conversation continuity

---

## Providers

### Supported Providers

| Provider | Models | API Key Env |
|----------|--------|-------------|
| Anthropic | Claude 4, Claude 3.5 | `ANTHROPIC_API_KEY` |
| OpenAI | GPT-4o, GPT-4, o1, o3 | `OPENAI_API_KEY` |
| Google | Gemini 2.0, Gemini 1.5 | `GOOGLE_API_KEY` |
| Azure | GPT-4, GPT-4o | `AZURE_OPENAI_API_KEY` |
| AWS Bedrock | Claude, Llama, Mistral | AWS credentials |
| Groq | Llama, Mixtral | `GROQ_API_KEY` |
| Mistral | Mistral Large, Codestral | `MISTRAL_API_KEY` |
| Cohere | Command R+ | `COHERE_API_KEY` |
| xAI | Grok | `XAI_API_KEY` |
| Perplexity | Sonar | `PERPLEXITY_API_KEY` |
| Together AI | Open models | `TOGETHER_API_KEY` |
| Cerebras | Llama | `CEREBRAS_API_KEY` |
| DeepInfra | Various | `DEEPINFRA_API_KEY` |
| OpenRouter | All models | `OPENROUTER_API_KEY` |
| Ollama | Local models | (local) |
| LM Studio | Local models | (local) |

### Provider Configuration

```toml
[provider.anthropic]
api_key_env = "ANTHROPIC_API_KEY"
model = "claude-sonnet-4-20250514"
max_tokens = 4096
temperature = 0.7

[provider.openai]
api_key_env = "OPENAI_API_KEY"
model = "gpt-4o"
max_tokens = 4096

[provider.ollama]
base_url = "http://localhost:11434"
model = "llama3.2"

[provider.custom]
name = "My Custom Provider"
base_url = "https://api.example.com/v1"
api_key_env = "CUSTOM_API_KEY"
model = "custom-model"
```

### Switching Providers

```
> Switch to Claude
> Use GPT-4o for this conversation
> Use local model llama3.2
```

---

## Tools

OpenCode provides 21 built-in tools for file operations, code analysis, and more.

### File Operations

#### read
Read file contents with line numbers:

```
> Read src/main.py
> Read lines 50-100 of config.py
```

#### write
Create new files:

```
> Create a new file utils/helpers.py with utility functions
```

#### edit
Edit files using string replacement:

```
> Replace "old_function" with "new_function" in main.py
```

#### glob
Find files by pattern:

```
> Find all Python files
> Find **/*.test.ts
```

#### grep
Search file contents:

```
> Search for "TODO" in all files
> Find usages of "process_data" function
```

#### ls
List directory contents:

```
> List files in src/
> Show directory tree
```

#### rm
Remove files or directories:

```
> Delete the temp directory
> Remove old_config.yaml
```

### Code Analysis

#### lsp
Language Server Protocol integration:

```
> Go to definition of "process_data"
> Find all references to "User" class
> Get diagnostics for main.py
> Rename "oldName" to "newName"
> Format this file
```

#### codesearch
Semantic code search using Exa AI:

```
> Search for authentication logic
> Find code similar to this pattern
```

### Web & Search

#### webfetch
Fetch web content:

```
> Fetch https://example.com/api/docs
> Get the content of that URL
```

#### websearch
Search the web:

```
> Search for Python asyncio best practices
> Find documentation for FastAPI dependency injection
```

### Execution

#### bash
Execute shell commands:

```
> Run pytest
> Execute: git status
> Run npm install
```

### Planning & Tasks

#### plan
Planning mode for complex tasks:

```
> Plan the implementation of user authentication
> Create a plan for refactoring the database layer
```

#### todo
Task tracking:

```
> Add todo: Fix the failing test
> Show my tasks
> Mark task 1 as complete
```

### Advanced

#### task
Sub-agent delegation:

```
> Use task agent to search for all API endpoints
> Delegate: Find all uses of deprecated functions
```

#### batch
Execute multiple tools in parallel:

```
> Read all Python files in src/
> Search for "import" in all files
```

#### multiedit
Multiple edits on a single file:

```
> Replace all occurrences of "foo" with "bar" in config.py
```

#### apply_patch
Apply structured patches:

```
> Apply this diff to main.py
```

#### question
Ask user questions:

```
> Ask the user which file to modify
```

---

## MCP Integration

Model Context Protocol (MCP) allows OpenCode to connect to external tools and services.

### Configuring MCP Servers

```toml
[mcp.servers.filesystem]
command = "mcp-filesystem"
args = ["/path/to/project"]

[mcp.servers.github]
command = "mcp-github"
env = { GITHUB_TOKEN = "your-token" }

[mcp.servers.postgres]
command = "mcp-postgres"
args = ["postgresql://localhost/mydb"]
```

### Using MCP Tools

MCP tools are automatically discovered and available:

```
> List MCP tools
> Use filesystem tool to read /project/file.txt
> Query the database with postgres tool
```

### MCP Server Mode

OpenCode can act as an MCP server:

```bash
opencode mcp serve
```

Configure in Claude Desktop or other MCP clients:

```json
{
  "mcpServers": {
    "opencode": {
      "command": "opencode",
      "args": ["mcp", "serve"]
    }
  }
}
```

### OAuth for MCP

OpenCode supports OAuth 2.0 authentication for MCP servers:

```bash
# Start OAuth flow
opencode mcp auth github

# List authenticated servers
opencode mcp auth list
```

---

## LSP Support

OpenCode integrates with Language Server Protocol for intelligent code features.

### Supported Languages

| Language | Language Server |
|----------|----------------|
| Python | pyright, pylsp |
| TypeScript/JavaScript | typescript-language-server |
| Go | gopls |
| Rust | rust-analyzer |
| C/C++ | clangd |

### LSP Features

- **Go to Definition**: Jump to symbol definition
- **Find References**: Find all usages of a symbol
- **Diagnostics**: Real-time error detection
- **Hover**: Type information and documentation
- **Rename**: Rename symbols across the codebase
- **Format**: Code formatting
- **Completion**: Code completion suggestions

### Using LSP

```
> Go to definition of "User" class
> Find all references to "process_data"
> What are the errors in main.py?
> Rename "oldName" to "newName"
> Format this file
> Show completions at line 50
```

### LSP Configuration

```toml
[lsp]
auto_start = true
timeout = 30

[lsp.python]
server = "pyright"
command = ["pyright-langserver", "--stdio"]

[lsp.typescript]
server = "typescript-language-server"
command = ["typescript-language-server", "--stdio"]

[lsp.go]
server = "gopls"
command = ["gopls", "serve"]

[lsp.rust]
server = "rust-analyzer"
command = ["rust-analyzer"]

[lsp.cpp]
server = "clangd"
command = ["clangd"]
```

---

## Web Interface

OpenCode includes a web interface for browser-based access.

### Starting the Web Interface

```bash
# Start server and open web interface
opencode web

# Start server on custom port
opencode serve --port 8080

# Start with authentication
OPENCODE_SERVER_PASSWORD=secret opencode serve
```

### Web Features

- **Chat Interface**: Real-time chat with streaming responses
- **Session Management**: Create, list, and delete sessions
- **File Browser**: Browse project files
- **Settings**: Configure providers and tools
- **Mobile Responsive**: Works on mobile devices

### REST API

The HTTP server provides a REST API:

```bash
# List sessions
curl http://localhost:4096/api/sessions

# Create session
curl -X POST http://localhost:4096/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"title": "My Session"}'

# Send message
curl -X POST http://localhost:4096/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"session_id": "xxx", "message": "Hello!"}'

# Stream response
curl -N http://localhost:4096/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"session_id": "xxx", "message": "Explain this code"}'
```

### WebSocket API

For real-time updates:

```javascript
const ws = new WebSocket('ws://localhost:4096/api/chat/ws');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'message',
    session_id: 'xxx',
    content: 'Hello!'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.content);
};
```

---

## Internationalization

OpenCode supports 17+ languages with automatic detection.

### Supported Languages

| Code | Language |
|------|----------|
| en | English |
| zh | 中文 (Simplified Chinese) |
| zht | 繁體中文 (Traditional Chinese) |
| ja | 日本語 (Japanese) |
| ko | 한국어 (Korean) |
| es | Español (Spanish) |
| fr | Français (French) |
| de | Deutsch (German) |
| it | Italiano (Italian) |
| pt | Português (Portuguese) |
| ru | Русский (Russian) |
| ar | العربية (Arabic) |
| th | ไทย (Thai) |
| vi | Tiếng Việt (Vietnamese) |
| pl | Polski (Polish) |
| nl | Nederlands (Dutch) |
| tr | Türkçe (Turkish) |

### Setting Language

```bash
# Set language via environment
export OPENCODE_LANGUAGE=zh

# Or in config
[ui]
language = "ja"
```

### Adding Translations

Translations are stored in `src/opencode/i18n/locales/`:

```json
// en.json
{
  "app.title": "OpenCode",
  "chat.placeholder": "Type a message...",
  "error.not_found": "File not found"
}
```

---

## Example Workflows

### 1. Code Review

```
> Read the main.py file
> What are the potential issues in this code?
> Suggest improvements for error handling
> Apply the suggested changes
```

### 2. Bug Fixing

```
> Run the tests
> The test test_user_creation is failing. Read the test file.
> Find the User class and check the create method
> Fix the bug in the create method
> Run the tests again
```

### 3. Feature Implementation

```
> I need to add user authentication. Plan the implementation.
> Create the User model in models/user.py
> Create the authentication endpoints
> Add tests for the authentication flow
> Run the tests and fix any issues
```

### 4. Code Exploration

```
> @plan Explore the project structure
> What design patterns are used?
> Find all API endpoints
> Document the architecture
```

### 5. Refactoring

```
> Find all uses of the deprecated function old_process
> Create a plan to migrate to new_process
> Update all usages
> Remove the deprecated function
> Run tests to verify
```

### 6. Documentation

```
> Read all Python files in src/
> Generate API documentation
> Create a README for the utils module
> Add docstrings to functions missing them
```

### 7. Git Operations

```
> What files have been modified?
> Show me the diff for main.py
> Create a commit with message "Add user authentication"
> Push to origin
```

### 8. Web Development

```
> Create a FastAPI endpoint for user registration
> Add input validation using Pydantic
> Write tests for the endpoint
> Add API documentation
```

---

## API Reference

### CLI Commands

```bash
opencode [OPTIONS] [DIRECTORY]

Options:
  --profile TEXT     Use specific configuration profile
  --model TEXT       Override default model
  --provider TEXT    Override default provider
  --port INTEGER     Port for HTTP server (default: 4096)
  --no-server        Don't start HTTP server
  --help             Show help message

Commands:
  serve              Start HTTP server
  web                Start web interface
  auth               Manage API keys
  config             View/edit configuration
  models             List available models
  session            Manage sessions
  mcp                Manage MCP servers
  upgrade            Self-update
  uninstall          Remove OpenCode
  import             Import sessions
  export             Export sessions
```

### Python API

```python
from opencode import OpenCode, Provider, Tool

# Initialize
async with OpenCode() as oc:
    # Set provider
    oc.set_provider("anthropic", api_key="...")
    
    # Send message
    response = await oc.chat("Hello!")
    print(response.content)
    
    # Use tools
    result = await oc.execute_tool("read", {"path": "main.py"})
    print(result.content)
    
    # Stream response
    async for chunk in oc.chat_stream("Explain this code"):
        print(chunk.content, end="")
```

---

## Troubleshooting

### Common Issues

#### API Key Not Found

```
Error: ANTHROPIC_API_KEY not found
```

Solution: Set the environment variable or configure in `opencode.toml`:

```bash
export ANTHROPIC_API_KEY=your-key
```

#### LSP Server Not Starting

```
Error: Failed to start language server
```

Solution: Install the language server:

```bash
# Python
pip install pyright

# TypeScript
npm install -g typescript-language-server

# Go
go install golang.org/x/tools/gopls@latest

# Rust
rustup component add rust-analyzer
```

#### MCP Server Connection Failed

```
Error: Failed to connect to MCP server
```

Solution: Check the server command and ensure it's installed:

```bash
# Install MCP server
npm install -g @modelcontextprotocol/server-filesystem
```

#### Permission Denied

```
Error: Permission denied for bash command
```

Solution: Add the command to the allowlist:

```toml
[permissions]
bash_allow = ["git status", "npm run test"]
```

### Debug Mode

Enable debug logging:

```bash
export OPENCODE_LOG_LEVEL=DEBUG
opencode
```

### Getting Help

- GitHub Issues: https://github.com/RTPro256/opencode_4py/issues
- Documentation: https://github.com/RTPro256/opencode_4py/docs

---

## License

MIT License - See [LICENSE](LICENSE) for details.
