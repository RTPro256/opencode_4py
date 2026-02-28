"""
OpenCode Project Summary
=========================

This module provides a programmatic summary of the OpenCode project,
extracted from README.md for use in code, tests, and documentation.

Project: OpenCode
Type: AI-powered code assistant with terminal UI
Language: Python
License: MIT

OVERVIEW
--------
OpenCode is a powerful, provider-agnostic AI coding assistant built in Python.
It features a rich terminal interface, supports multiple AI providers, and includes
advanced features like RAG (Retrieval-Augmented Generation), session management,
and extensibility through MCP (Model Context Protocol).

FEATURES
--------
- Terminal UI: Rich, interactive terminal interface built with Textual
- Multiple AI Providers: Support for Anthropic Claude, OpenAI GPT, Google Gemini,
  and more (15+ providers)
- LSP Integration: Code intelligence via Language Server Protocol
- MCP Support: Extensible tool system via Model Context Protocol
- HTTP Server: REST API and WebSocket endpoints for remote access
- Session Management: Persistent conversation history with SQLite database
- Privacy-First RAG: Local vector storage for knowledge retrieval
- Troubleshooting System: Built-in debug agent with error knowledge base
- Internationalization: Multi-language support (English, Spanish, Japanese, Chinese)

SUPPORTED PROVIDERS
-------------------
| Provider   | Models                              | Environment Variable    |
|------------|-------------------------------------|------------------------|
| Anthropic  | Claude 4, Claude 3.5                | ANTHROPIC_API_KEY      |
| OpenAI     | GPT-4o, GPT-4, o1, o3              | OPENAI_API_KEY         |
| Google     | Gemini 2.0, Gemini 1.5              | GOOGLE_API_KEY         |
| Azure      | GPT-4, GPT-4o                      | AZURE_OPENAI_API_KEY   |
| AWS Bedrock| Claude, Llama, Mistral             | AWS credentials        |
| Groq       | Llama, Mixtral                     | GROQ_API_KEY           |
| Mistral    | Mistral Large, Codestral           | MISTRAL_API_KEY        |
| Ollama     | Local models                       | (local)                |
| LM Studio  | Local models                       | (local)                |

CLI COMMANDS
------------
- opencode                    # Start TUI (default)
- opencode run "prompt"       # Run a single prompt
- opencode serve              # Start HTTP server
- opencode auth               # Manage API keys
- opencode config             # View/edit configuration
- opencode models             # List available models
- opencode session            # Manage sessions
- opencode mcp                # Manage MCP servers
- opencode rag                # RAG management commands
- opencode debug              # Debug issues with RAG lookup
- opencode github             # GitHub sync and repository management
- opencode upgrade            # Upgrade to latest version
- opencode uninstall          # Uninstall OpenCode

API ENDPOINTS
-------------
Chat:
- POST /api/chat/message - Send a message
- POST /api/chat/stream - Stream a response
- WebSocket /api/chat/ws/{session_id} - Real-time chat

Sessions:
- GET /api/sessions - List sessions
- POST /api/sessions - Create session
- GET /api/sessions/{id} - Get session
- DELETE /api/sessions/{id} - Delete session

Tools:
- GET /api/tools - List available tools
- POST /api/tools/execute - Execute a tool

PROJECT STRUCTURE
-----------------
opencode/
├── src/opencode/           # Main Python package
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
├── docs/                  # Project documentation
├── config/                # Configuration files
├── examples/              # Usage examples
├── RAG/                   # RAG knowledge bases
├── plans/                 # Project planning documents
└── scripts/               # Utility scripts

STATUS
------
This project is under active development. See plans/ for implementation
progress and upcoming features.

RELATED DOCUMENTS
-----------------
- MISSION.md - Core principles, purpose, and values that guide development
"""

# Version info
__version__ = "1.0.0"
__project__ = "OpenCode"
__description__ = "AI-powered code assistant with terminal UI, LSP support, and MCP integration"

# Core features as constants
FEATURES = {
    "terminal_ui": "Rich, interactive terminal interface built with Textual",
    "multiple_providers": "Support for Anthropic Claude, OpenAI GPT, Google Gemini, and more (15+ providers)",
    "lsp_integration": "Code intelligence via Language Server Protocol",
    "mcp_support": "Extensible tool system via Model Context Protocol",
    "http_server": "REST API and WebSocket endpoints for remote access",
    "session_management": "Persistent conversation history with SQLite database",
    "privacy_first_rag": "Local vector storage for knowledge retrieval",
    "troubleshooting_system": "Built-in debug agent with error knowledge base",
    "internationalization": "Multi-language support (English, Spanish, Japanese, Chinese)",
}

# Supported providers
PROVIDERS = {
    "anthropic": {"env_var": "ANTHROPIC_API_KEY", "models": ["Claude 4", "Claude 3.5"]},
    "openai": {"env_var": "OPENAI_API_KEY", "models": ["GPT-4o", "GPT-4", "o1", "o3"]},
    "google": {"env_var": "GOOGLE_API_KEY", "models": ["Gemini 2.0", "Gemini 1.5"]},
    "azure": {"env_var": "AZURE_OPENAI_API_KEY", "models": ["GPT-4", "GPT-4o"]},
    "aws_bedrock": {"env_var": "AWS credentials", "models": ["Claude", "Llama", "Mistral"]},
    "groq": {"env_var": "GROQ_API_KEY", "models": ["Llama", "Mixtral"]},
    "mistral": {"env_var": "MISTRAL_API_KEY", "models": ["Mistral Large", "Codestral"]},
    "ollama": {"env_var": "(local)", "models": ["Local models"]},
    "lm_studio": {"env_var": "(local)", "models": ["Local models"]},
}

# CLI commands
CLI_COMMANDS = {
    "start": "opencode",
    "run": 'opencode run "prompt"',
    "serve": "opencode serve",
    "auth": "opencode auth",
    "config": "opencode config",
    "models": "opencode models",
    "session": "opencode session",
    "mcp": "opencode mcp",
    "rag": "opencode rag",
    "debug": "opencode debug",
    "github": "opencode github",
    "upgrade": "opencode upgrade",
    "uninstall": "opencode uninstall",
}

# API endpoints
API_ENDPOINTS = {
    "chat_message": "POST /api/chat/message",
    "chat_stream": "POST /api/chat/stream",
    "chat_ws": "WebSocket /api/chat/ws/{session_id}",
    "sessions_list": "GET /api/sessions",
    "sessions_create": "POST /api/sessions",
    "sessions_get": "GET /api/sessions/{id}",
    "sessions_delete": "DELETE /api/sessions/{id}",
    "tools_list": "GET /api/tools",
    "tools_execute": "POST /api/tools/execute",
}
