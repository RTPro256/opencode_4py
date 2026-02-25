# Changelog

All notable changes to OpenCode Python will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-21

### Added

#### Core Features
- Complete Python rewrite of OpenCode AI coding agent
- Terminal UI built with Textual framework
- HTTP server with FastAPI
- Web interface with embedded HTML/CSS/JS
- SQLite database with SQLAlchemy 2.0 async

#### AI Providers (18 total)
- **Anthropic**: Claude 4, Claude 3.5 Sonnet/Opus
- **OpenAI**: GPT-4o, GPT-4, o1, o3
- **Google**: Gemini 2.0, Gemini 1.5 Pro/Flash, Vertex AI
- **Azure OpenAI**: GPT-4, GPT-4o
- **AWS Bedrock**: Claude, Llama, Mistral, Titan
- **Groq**: Llama, Mixtral (fast inference)
- **Mistral**: Mistral Large, Codestral
- **Cohere**: Command R+, Command R
- **xAI**: Grok
- **Perplexity**: Sonar
- **Together AI**: Open source models
- **Cerebras**: Llama (fast inference)
- **DeepInfra**: Various models
- **OpenRouter**: 100+ models unified API
- **Vercel AI Gateway**: Enterprise gateway
- **Ollama**: Local models
- **LM Studio**: Local models
- **Custom Endpoints**: OpenAI-compatible APIs

#### Tools (21 total)
- **bash**: Execute shell commands
- **read**: Read file contents with line numbers
- **write**: Create new files
- **edit**: Edit files using string replacement
- **glob**: Find files by pattern
- **grep**: Search file contents with regex
- **ls**: List directory contents
- **rm**: Remove files and directories
- **lsp**: Language Server Protocol integration
- **codesearch**: Semantic code search (Exa AI)
- **webfetch**: Fetch web content
- **websearch**: Search the web (Exa AI)
- **task**: Sub-agent delegation
- **plan**: Planning mode for complex tasks
- **todo**: Task tracking
- **skill**: Load specialized instructions
- **apply_patch**: Apply structured patches
- **batch**: Execute multiple tools in parallel
- **multiedit**: Multiple edits on single file
- **question**: Ask user questions
- **git**: Git operations (status, diff, commit, etc.)

#### LSP Integration
- Go to Definition
- Find References
- Get Diagnostics
- Hover Information
- Rename Symbol
- Code Formatting
- Code Completion

#### Language Support
- Python (pyright/pylsp)
- TypeScript/JavaScript (typescript-language-server)
- Go (gopls)
- Rust (rust-analyzer)
- C/C++ (clangd)
- Auto-detection from project config

#### MCP (Model Context Protocol)
- MCP Client for connecting to external servers
- MCP Server Mode for exposing tools
- Tool Discovery
- Resource Access
- Prompt Templates
- JSON-RPC over stdio
- Multiple server management
- OAuth 2.0 authentication flow

#### HTTP Server
- REST API endpoints
- WebSocket support
- Server-Sent Events for streaming
- Session management
- File operations
- Configuration management

#### Web Interface
- Browser-based chat interface
- Real-time streaming responses
- Session management
- File browser
- Mobile responsive design
- Dark/light theme

#### Internationalization
- 17+ languages supported
- Auto-detection from system locale
- Translation files in JSON format
- Pluralization support
- Variable interpolation

#### Configuration
- TOML configuration files
- Global and project-level config
- Environment variables
- Multiple profiles
- Schema validation with Pydantic

#### Session Management
- Create/Load/Delete sessions
- Persist messages to SQLite
- Export/Import sessions as JSON
- Auto-generated session titles
- Token tracking
- Context compaction for long conversations

#### Agents
- **build**: Full-access development agent
- **plan**: Read-only analysis agent
- Agent switching with Tab key

#### Permission System
- Tool permission prompts
- Auto-approve patterns
- Session-specific permissions
- Bash command allowlisting
- Read-only mode for plan agent

#### CLI Commands
- `opencode` - Launch TUI
- `opencode serve` - Start HTTP server
- `opencode web` - Open web interface
- `opencode auth` - Manage API keys
- `opencode config` - View/edit configuration
- `opencode models` - List available models
- `opencode session` - Manage sessions
- `opencode mcp` - Manage MCP servers
- `opencode upgrade` - Self-update
- `opencode uninstall` - Remove OpenCode
- `opencode import` - Import sessions
- `opencode export` - Export sessions

### Documentation
- Comprehensive README with feature descriptions
- Feature coverage comparison with original
- Migration plan with implementation details
- API reference
- Example workflows
- Troubleshooting guide

### Technical Details
- Python 3.12+ requirement
- Async/await throughout
- Type hints with Pydantic models
- Streaming responses with AsyncIterator
- Connection pooling with httpx
- Efficient token counting

## [0.1.0] - 2026-01-15

### Added
- Initial project structure
- Basic CLI framework
- Configuration system
- Logging infrastructure
- Database layer setup

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0.0 | 2026-02-21 | Complete feature parity with original |
| 0.1.0 | 2026-01-15 | Initial development version |

---

## Upcoming Features

The following features are being considered for future releases:

- [ ] Desktop application (Tauri-based)
- [ ] Plugin system for custom tools
- [ ] Voice input/output
- [ ] Multi-file editing improvements
- [ ] Code review mode
- [ ] Test generation
- [ ] Documentation generation
- [ ] Performance profiling integration

---

## Migration from TypeScript Version

If you're migrating from the original TypeScript/Bun version:

1. **Configuration files** are compatible (TOML format)
2. **Database schema** is compatible for session import/export
3. **API endpoints** maintain the same structure
4. **Keyboard shortcuts** are consistent
5. **Environment variables** use the same names

See [MIGRATION_PLAN.md](plans/archive/MIGRATION_PLAN.md) for detailed migration instructions.
