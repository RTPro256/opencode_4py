# OpenCode Python Migration Plan

This document provides a comprehensive plan for migrating all features from the original OpenCode (TypeScript/Bun) to the Python rewrite, plus integration of additional projects.

> **Related Documents:**
> - [README.md](../../README.md) - Project overview and features
> - [MISSION.md](../../MISSION.md) - Mission statement and core principles

## Executive Summary

The original OpenCode is a sophisticated AI coding agent built with TypeScript, Bun runtime, SolidJS (TUI), Hono (HTTP), and Drizzle ORM. The Python rewrite aims to achieve feature parity while leveraging Python's ecosystem with Textual (TUI), FastAPI (HTTP), and SQLAlchemy.

**Current Completion: ~98%**

### Integration Sources

| Source Project | Language | Integration Type | Complexity | Status |
|---------------|----------|------------------|------------|--------|
| **OpenCode (Original)** | TypeScript/Bun | Full rewrite to Python | High | ✅ 98% |
| **agentic-signal** | TypeScript/Deno | Full rewrite to Python | High | ✅ Completed |
| **SmarterRouter** | Python | Direct integration | Medium | ✅ Completed |
| **llm-checker** | JavaScript/Node.js | Full rewrite to Python | Medium | ✅ Completed |
| **qwen-code** | TypeScript/Node.js | Feature extraction | High | ✅ Completed |
| **youtube_Rag** | Python | Direct integration | Low | ✅ Completed |
| **balmasi-youtube-rag** | Python | Channel indexing | Medium | ⏳ Planned |
| **MultiModal-RAG-with-Videos** | Python | Multimodal RAG | High | ⏳ Planned |
| **rag-youtube-assistant** | Python | Evaluation + Query rewrite | Medium | ⏳ Planned |
| **svpino-youtube-rag** | Python | Educational patterns | Low | ⏳ Planned |
| **youtube-rag** | Python | Timestamped links | Low | ⏳ Planned |
| **ai-factory** | Python | AI factory patterns | Medium | ⏳ Planned |
| **compound-engineering-plugin** | TypeScript | Plugin architecture | Medium | ⏳ Planned |
| **get-shit-done** | TypeScript | Task execution patterns | Medium | ⏳ Planned |
| **get-shit-done-2** | TypeScript | Enhanced task execution | Medium | ⏳ Planned |
| **Local-RAG-with-Ollama** | Python | Local RAG patterns | Medium | ⏳ Planned |
| **mistral-vibe** | Python | Mistral integration | Low | ⏳ Planned |
| **OpenRAG** | Python | Open RAG patterns | High | ⏳ Planned |
| **planning-with-files** | Python | File-based planning | Low | ⏳ Planned |
| **plano** | Python | Planning patterns | Medium | ⏳ Planned |
| **RAG_Techniques** | Python | RAG technique collection | High | ⏳ Planned |
| **Roo-Code** | TypeScript | VS Code extension patterns | High | ⏳ Planned |
| **superpowers** | Python | AI superpowers | Medium | ⏳ Planned |
| **unsloth** | Python | Fine-tuning integration | High | ⏳ Planned |

### Recent Additions (February 2026)
- **New Providers**: Ollama, Azure OpenAI, OpenRouter, Groq, Mistral, xAI, Cohere, Perplexity, Together AI, AWS Bedrock, Cerebras, DeepInfra, LM Studio, Vercel AI Gateway, Custom Endpoints
- **New Tools**: codesearch, webfetch, websearch, task, plan, todo, skill, apply_patch, batch, multiedit, question, git
- **Provider Coverage**: 18/18 providers (100%)
- **Tool Coverage**: 21/21 tools (100%)
- **LSP Features**: rename, format, completion added
- **MCP Server Mode**: Implemented
- **Configuration Profiles**: Implemented
- **Workflow Engine**: Node-based visual programming (from agentic-signal)
- **Intelligent Router**: Model selection with VRAM management (from SmarterRouter)

---

## Architecture Comparison

| Component | TypeScript | Python |
|-----------|------------|--------|
| Runtime | Bun 1.3+ | Python 3.12+ |
| Language | TypeScript 5.8+ | Python 3.12+ |
| CLI Framework | yargs | typer |
| TUI Framework | SolidJS + opentui | Textual |
| HTTP Framework | Hono | FastAPI |
| Database ORM | Drizzle | SQLAlchemy 2.0 (async) |
| AI SDK | Vercel AI SDK | Direct httpx calls |
| Validation | Zod | Pydantic |
| Package Manager | bun | pip/hatch |

---

## Migration Phases

### Phase 1: Foundation ✅ (COMPLETE)

**Status: 100%**

| Feature | TypeScript File | Python File | Status |
|---------|-----------------|-------------|--------|
| Project Setup | `package.json` | `pyproject.toml` | ✅ |
| Configuration System | `src/config/config.ts` | `src/opencode/core/config.py` | ✅ |
| Logging System | `src/util/log.ts` | `src/opencode/util/log.py` | ✅ |
| Database Layer | `src/storage/` | `src/opencode/db/` | ✅ |
| Error Handling | `src/util/error.ts` | `src/opencode/util/exceptions.py` | ✅ |

**Key Implementations:**
- Pydantic models for configuration validation
- SQLAlchemy async database with SQLite
- Structured logging with rich formatting
- Custom exception hierarchy

---

### Phase 2: Core Infrastructure ✅ (COMPLETE)

**Status: 90%**

#### 2.1 Provider System

| Provider | TypeScript | Python | Priority |
|----------|------------|--------|----------|
| **Anthropic** | `@ai-sdk/anthropic` | `provider/anthropic.py` | ✅ P0 |
| **OpenAI** | `@ai-sdk/openai` | `provider/openai.py` | ✅ P0 |
| **Google Gemini** | `@ai-sdk/google` | `provider/google.py` | ✅ P0 |
| **Azure OpenAI** | `@ai-sdk/azure` | `provider/azure.py` | ✅ P1 |
| **AWS Bedrock** | `@ai-sdk/amazon-bedrock` | `provider/bedrock.py` | ⏳ P1 |
| **OpenRouter** | `@openrouter/ai-sdk-provider` | `provider/openrouter.py` | ✅ P1 |
| **Groq** | `@ai-sdk/groq` | `provider/groq.py` | ✅ P2 |
| **Mistral** | `@ai-sdk/mistral` | `provider/mistral.py` | ✅ P2 |
| **Cohere** | `@ai-sdk/cohere` | `provider/cohere.py` | ⏳ P2 |
| **Cerebras** | `@ai-sdk/cerebras` | `provider/cerebras.py` | ⏳ P2 |
| **DeepInfra** | `@ai-sdk/deepinfra` | `provider/deepinfra.py` | ⏳ P2 |
| **Perplexity** | `@ai-sdk/perplexity` | `provider/perplexity.py` | ⏳ P2 |
| **Together AI** | `@ai-sdk/togetherai` | `provider/togetherai.py` | ⏳ P2 |
| **xAI (Grok)** | `@ai-sdk/xai` | `provider/xai.py` | ✅ P2 |
| **Vercel Gateway** | `@ai-sdk/gateway` | `provider/vercel.py` | ⏳ P2 |
| **GitLab AI** | `@gitlab/gitlab-ai-provider` | `provider/gitlab.py` | ⏳ P3 |
| **GitHub Copilot** | Custom SDK | `provider/copilot.py` | ⏳ P3 |
| **Google Vertex** | `@ai-sdk/google-vertex` | `provider/vertex.py` | ⏳ P2 |
| **Ollama (Local)** | OpenAI-compatible | `provider/ollama.py` | ✅ P1 |
| **LM Studio (Local)** | OpenAI-compatible | `provider/lmstudio.py` | ⏳ P2 |
| **Custom Endpoints** | `@ai-sdk/openai-compatible` | `provider/custom.py` | ⏳ P2 |

**TypeScript Source:** `src/provider/provider.ts` (49,674 chars)

**Implementation Notes:**
- Provider interface with streaming support
- Message transformation for different APIs
- Tool/function calling support
- Token counting and cost tracking

#### 2.2 Tool System

| Tool | TypeScript | Python | Status |
|------|------------|--------|--------|
| **bash** | `src/tool/bash.ts` | `tool/bash.py` | ✅ |
| **read** | `src/tool/read.ts` | `tool/read.py` | ✅ |
| **write** | `src/tool/write.ts` | `tool/write.py` | ✅ |
| **edit** | `src/tool/edit.ts` | `tool/edit.py` | ✅ |
| **glob** | `src/tool/glob.ts` | `tool/glob.py` | ✅ |
| **grep** | `src/tool/grep.ts` | `tool/grep.py` | ✅ |
| **ls** | `src/tool/ls.ts` | `tool/ls.py` | ✅ |
| **lsp** | `src/tool/lsp.ts` | `tool/lsp.py` | ✅ |
| **codesearch** | `src/tool/codesearch.ts` | `tool/codesearch.py` | ✅ |
| **task** | `src/tool/task.ts` | `tool/task.py` | ✅ |
| **plan** | `src/tool/plan.ts` | `tool/plan.py` | ⏳ |
| **webfetch** | `src/tool/webfetch.ts` | `tool/webfetch.py` | ✅ |
| **websearch** | `src/tool/websearch.ts` | `tool/websearch.py` | ✅ |
| **apply_patch** | `src/tool/apply_patch.ts` | `tool/apply_patch.py` | ⏳ |
| **batch** | `src/tool/batch.ts` | `tool/batch.py` | ⏳ |
| **multiedit** | `src/tool/multiedit.ts` | `tool/multiedit.py` | ⏳ |
| **todo** | `src/tool/todo.ts` | `tool/todo.py` | ✅ |
| **question** | `src/tool/question.ts` | `tool/question.py` | ⏳ |
| **skill** | `src/tool/skill.ts` | `tool/skill.py` | ⏳ |

**TypeScript Source:** `src/tool/tool.ts` (3,131 chars) + individual tool files

---

### Phase 3: Session & Server ✅ (COMPLETE)

**Status: 95%**

#### 3.1 Session Management

| Feature | TypeScript | Python | Status |
|---------|------------|--------|--------|
| Create Session | `src/session/index.ts` | `db/session.py` | ✅ |
| Message Storage | `src/session/message.ts` | `db/message.py` | ✅ |
| Session Title Generation | `src/session/prompt.ts` | `session/title.py` | ✅ |
| Export/Import | `src/cli/cmd/export.ts` | `cli/session.py` | ✅ |
| Context Compaction | `src/session/compaction.ts` | `session/compaction.py` | ⏳ |
| Message Processing | `src/session/processor.ts` | `session/processor.py` | 🔄 |
| Retry Logic | `src/session/retry.ts` | `session/retry.py` | ⏳ |
| Revert Capability | `src/session/revert.ts` | `session/revert.py` | ⏳ |

**TypeScript Source:** `src/session/` (multiple files, ~150,000 chars total)

#### 3.2 HTTP Server

| Route | TypeScript | Python | Status |
|-------|------------|--------|--------|
| `GET /api/sessions` | `server/routes/session.ts` | `server/routes/session.py` | ✅ |
| `POST /api/sessions` | `server/routes/session.ts` | `server/routes/session.py` | ✅ |
| `GET /api/sessions/{id}` | `server/routes/session.ts` | `server/routes/session.py` | ✅ |
| `DELETE /api/sessions/{id}` | `server/routes/session.ts` | `server/routes/session.py` | ✅ |
| `POST /api/chat/message` | `server/routes/session.ts` | `server/routes/chat.py` | ✅ |
| `POST /api/chat/stream` | `server/routes/session.ts` | `server/routes/chat.py` | ✅ |
| `WebSocket /api/chat/ws` | `server/routes/session.ts` | `server/routes/websocket.py` | ✅ |
| `GET /api/models` | `server/routes/provider.ts` | `server/routes/provider.py` | ✅ |
| `GET /api/tools` | `server/routes/session.ts` | `server/routes/tool.py` | ✅ |
| `POST /api/tools/execute` | `server/routes/session.ts` | `server/routes/tool.py` | ✅ |
| `GET /api/files/list` | `server/routes/file.ts` | `server/routes/file.py` | ✅ |
| `GET /api/files/read` | `server/routes/file.ts` | `server/routes/file.py` | ✅ |
| `POST /api/files/write` | `server/routes/file.ts` | `server/routes/file.py` | ✅ |
| `POST /api/files/search` | `server/routes/file.ts` | `server/routes/file.py` | ✅ |
| `GET /api/config` | `server/routes/config.ts` | `server/routes/config.py` | ✅ |
| `POST /api/config` | `server/routes/config.ts` | `server/routes/config.py` | ✅ |
| `GET /api/mcp` | `server/routes/mcp.ts` | `server/routes/mcp.py` | ✅ |
| `POST /api/mcp/execute` | `server/routes/mcp.ts` | `server/routes/mcp.py` | ✅ |
| `GET /api/permissions` | `server/routes/permission.ts` | `server/routes/permission.py` | 🔄 |
| `POST /api/permissions` | `server/routes/permission.ts` | `server/routes/permission.py` | 🔄 |
| `GET /api/global` | `server/routes/global.ts` | `server/routes/global.py` | ⏳ |
| `GET /api/project` | `server/routes/project.ts` | `server/routes/project.py` | ⏳ |
| `POST /api/question` | `server/routes/question.ts` | `server/routes/question.py` | ⏳ |
| `POST /api/pty` | `server/routes/pty.ts` | `server/routes/pty.py` | ⏳ |
| `GET /api/tui` | `server/routes/tui.ts` | `server/routes/tui.py` | ⏳ |
| `POST /api/experimental/*` | `server/routes/experimental.ts` | `server/routes/experimental.py` | ⏳ |

**TypeScript Source:** `src/server/server.ts` (20,660 chars) + routes

---

### Phase 4: UI & Integration 🔄 (IN PROGRESS)

**Status: 70%**

#### 4.1 TUI (Terminal User Interface)

| Feature | TypeScript | Python | Status |
|---------|------------|--------|--------|
| Chat View | `cli/cmd/tui/` | `tui/app.py` | ✅ |
| Message List | `cli/cmd/tui/` | `tui/widgets/messages.py` | ✅ |
| Input Box | `cli/cmd/tui/` | `tui/widgets/input.py` | ✅ |
| Tool Output | `cli/cmd/tui/` | `tui/widgets/tools.py` | ✅ |
| Status Bar | `cli/cmd/tui/` | `tui/widgets/status.py` | ✅ |
| Sidebar | `cli/cmd/tui/` | `tui/widgets/sidebar.py` | ✅ |
| Help Panel | `cli/cmd/tui/` | `tui/widgets/help.py` | ✅ |
| File Preview | `cli/cmd/tui/` | `tui/widgets/preview.py` | 🔄 |
| Diff View | `cli/cmd/tui/` | `tui/widgets/diff.py` | ⏳ |
| Agent Switching (Tab) | `cli/cmd/tui/` | `tui/app.py` | ✅ |
| Syntax Highlighting | `cli/cmd/tui/` | `tui/highlight.py` | 🔄 |

**TypeScript Source:** `src/cli/cmd/tui/` (SolidJS components)

#### 4.2 MCP Client

| Feature | TypeScript | Python | Status |
|---------|------------|--------|--------|
| MCP Client | `src/mcp/index.ts` | `mcp/client.py` | ✅ |
| Tool Discovery | `src/mcp/index.ts` | `mcp/client.py` | ✅ |
| Resource Access | `src/mcp/index.ts` | `mcp/client.py` | ✅ |
| Prompt Templates | `src/mcp/index.ts` | `mcp/client.py` | ✅ |
| JSON-RPC over stdio | `src/mcp/index.ts` | `mcp/client.py` | ✅ |
| Multiple Servers | `src/mcp/index.ts` | `mcp/manager.py` | ✅ |
| OAuth Flow | `src/mcp/oauth-provider.ts` | `mcp/oauth.py` | ⏳ |
| MCP Server Mode | `src/mcp/` | `mcp/server.py` | ⏳ |

**TypeScript Source:** `src/mcp/` (46,000+ chars)

#### 4.3 LSP Integration

| Feature | TypeScript | Python | Status |
|---------|------------|--------|--------|
| LSP Client | `src/lsp/client.ts` | `lsp/client.py` | ✅ |
| Go to Definition | `src/lsp/server.ts` | `lsp/features.py` | ✅ |
| Find References | `src/lsp/server.ts` | `lsp/features.py` | ✅ |
| Get Diagnostics | `src/lsp/server.ts` | `lsp/features.py` | ✅ |
| Hover Information | `src/lsp/server.ts` | `lsp/features.py` | ✅ |
| Rename Symbol | `src/lsp/server.ts` | `lsp/features.py` | ⏳ |
| Code Formatting | `src/lsp/server.ts` | `lsp/features.py` | ⏳ |
| Completion | `src/lsp/server.ts` | `lsp/features.py` | ⏳ |

**Language Support:**

| Language | TypeScript | Python | Status |
|----------|------------|--------|--------|
| Python | `pyright/pylsp` | `pyright/pylsp` | ✅ |
| TypeScript/JavaScript | `typescript-language-server` | `typescript-language-server` | ✅ |
| Go | `gopls` | `gopls` | ⏳ |
| Rust | `rust-analyzer` | `rust-analyzer` | ⏳ |
| C/C++ | `clangd` | `clangd` | ⏳ |

**TypeScript Source:** `src/lsp/` (90,000+ chars)

---

### Phase 5: Extended Features ⏳ (PLANNED)

**Status: 20%**

#### 5.1 Additional Providers

**Priority Order:**
1. **Ollama** - Local model support (high demand)
2. **Azure OpenAI** - Enterprise users
3. **OpenRouter** - Unified API access
4. **AWS Bedrock** - Enterprise cloud
5. **Groq** - Fast inference
6. **Mistral** - European AI
7. **xAI (Grok)** - Alternative option
8. **Remaining providers** - Long tail

**Implementation Template:**
```python
# src/opencode/provider/{provider}.py
from opencode.provider.base import BaseProvider, Message, StreamChunk

class {Provider}Provider(BaseProvider):
    async def complete(self, messages: list[Message], **kwargs) -> AsyncIterator[StreamChunk]:
        # Provider-specific implementation
        pass
```

#### 5.2 Advanced Tools

| Tool | Description | Priority |
|------|-------------|----------|
| **codesearch** | Semantic code search using embeddings | P1 |
| **task** | Sub-agent delegation for complex tasks | P1 |
| **webfetch** | Fetch web content | P2 |
| **websearch** | Search the web | P2 |
| **apply_patch** | Apply unified diff patches | P2 |
| **todo** | Task management | P3 |

#### 5.3 Context Compaction

**TypeScript Source:** `src/session/compaction.ts` (8,674 chars)

**Implementation:**
- Summarize old messages when context exceeds limit
- Preserve important context (tool outputs, decisions)
- Generate summary using LLM
- Store compaction history for undo

#### 5.4 Sub-Agent Delegation

**TypeScript Source:** `src/tool/task.ts` (5,503 chars)

**Features:**
- Spawn specialized sub-agents for complex tasks
- `@general` subagent for multi-step searches
- Parallel task execution
- Result aggregation

---

### Phase 6: Polish & Advanced Features ⏳ (PLANNED)

**Status: 10%**

#### 6.1 Web Interface

| Feature | TypeScript | Python | Status |
|---------|------------|--------|--------|
| Web App | `packages/app/` | `web/` | ⏳ |
| Mobile Responsive | `packages/app/` | `web/` | ⏳ |
| Real-time Updates | WebSocket | WebSocket | ⏳ |

**Note:** The TypeScript version uses SolidJS. Python could use:
- FastAPI + Jinja2 templates (simple)
- FastAPI + React/Vue (complex)
- FastAPI + htmx (lightweight)

#### 6.2 Internationalization

**TypeScript:** 17+ languages supported (README translations)

**Python:** Not yet implemented

**Implementation:**
- Use Python's `gettext` or `babel`
- Extract strings from TUI and CLI
- Create translation files

#### 6.3 Advanced LSP Features

| Feature | Description | Priority |
|---------|-------------|----------|
| Rename Symbol | Rename variables/functions across codebase | P1 |
| Code Formatting | Format document with LSP | P2 |
| Completion | Code completion suggestions | P2 |
| Code Actions | Quick fixes and refactoring | P3 |

#### 6.4 Performance Optimization

- Async I/O throughout
- Connection pooling for HTTP
- Caching for LSP results
- Lazy loading for providers
- Streaming response handling

---

## CLI Commands Migration

| Command | TypeScript | Python | Status |
|---------|------------|--------|--------|
| `opencode` (TUI) | `cli/cmd/run.ts` | `cli/main.py` | ✅ |
| `opencode run <dir>` | `cli/cmd/run.ts` | `cli/main.py` | ✅ |
| `opencode serve` | `cli/cmd/serve.ts` | `cli/main.py` | ✅ |
| `opencode auth` | `cli/cmd/auth.ts` | `cli/main.py` | ✅ |
| `opencode config` | `cli/cmd/` | `cli/main.py` | ✅ |
| `opencode models` | `cli/cmd/models.ts` | `cli/main.py` | ✅ |
| `opencode session` | `cli/cmd/session.ts` | `cli/main.py` | ✅ |
| `opencode mcp` | `cli/cmd/mcp.ts` | `cli/main.py` | ✅ |
| `opencode upgrade` | `cli/cmd/upgrade.ts` | `cli/main.py` | ✅ |
| `opencode uninstall` | `cli/cmd/uninstall.ts` | `cli/main.py` | ✅ |
| `opencode import` | `cli/cmd/import.ts` | `cli/main.py` | ✅ |
| `opencode export` | `cli/cmd/export.ts` | `cli/main.py` | ✅ |
| `opencode web` | `cli/cmd/web.ts` | `cli/main.py` | ⏳ |
| `opencode attach` | `cli/cmd/tui/attach.ts` | `cli/main.py` | ⏳ |
| `opencode github` | `cli/cmd/github.ts` | `cli/main.py` | ⏳ |
| `opencode pr` | `cli/cmd/pr.ts` | `cli/main.py` | ⏳ |
| `opencode stats` | `cli/cmd/stats.ts` | `cli/main.py` | ⏳ |
| `opencode db` | `cli/cmd/db.ts` | `cli/main.py` | ⏳ |
| `opencode acp` | `cli/cmd/acp.ts` | `cli/main.py` | ⏳ |
| `opencode debug` | `cli/cmd/debug/` | `cli/main.py` | ⏳ |
| `opencode generate` | `cli/cmd/generate.ts` | `cli/main.py` | ⏳ |

---

## Configuration Migration

### TypeScript Configuration (`opencode.toml`)

```toml
[provider]
anthropic = { api_key = "..." }
openai = { api_key = "..." }

[agent.build]
model = "claude-3-5-sonnet"

[permission]
bash = { allow = ["git", "npm", "pip"] }
```

### Python Configuration (Compatible)

The Python version maintains TOML compatibility with the same schema.

**TypeScript Source:** `src/config/config.ts` (58,249 chars)

---

## Database Schema Migration

The Python version uses the same SQLite schema for compatibility:

- `session` - Session metadata
- `message` - Message history
- `tool_call` - Tool execution records
- `permission` - Permission decisions

**Migration Script:** `src/storage/json-migration.ts` handles JSON to SQLite migration

---

## Testing Strategy

### Unit Tests
- Provider implementations
- Tool execution
- Message transformation
- Configuration parsing

### Integration Tests
- End-to-end chat flow
- Tool execution in context
- MCP server communication
- LSP features

### Manual Testing
- TUI responsiveness
- Multi-provider switching
- Long-running sessions
- Error recovery

---

## Migration Priority Matrix

| Priority | Features | Effort | Impact |
|----------|----------|--------|--------|
| P0 | Core providers (Anthropic, OpenAI, Google) | Medium | Critical |
| P1 | Additional providers (Ollama, Azure, Bedrock) | High | High |
| P1 | Context compaction | Medium | High |
| P1 | Sub-agent delegation | High | High |
| P2 | Web interface | High | Medium |
| P2 | Advanced LSP features | Medium | Medium |
| P2 | Additional tools (webfetch, websearch) | Low | Medium |
| P3 | Internationalization | Medium | Low |
| P3 | Desktop app | N/A | Not planned |

---

## Not Planned for Python Version

The following features are **not planned** for the Python rewrite:

1. **Desktop Application** - The TypeScript version uses Tauri for native desktop apps. Python will focus on CLI/TUI and HTTP server.

2. **GitHub-specific Commands** - `opencode github` and `opencode pr` are GitHub-specific integrations that may be added as plugins later.

3. **ACP (Agent Client Protocol)** - Specialized protocol support, low priority.

---

## Development Roadmap

### Q1 2026
- [ ] Complete remaining core tools
- [ ] Add Ollama provider
- [ ] Implement context compaction
- [ ] Add Azure OpenAI provider

### Q2 2026
- [ ] Add remaining AI providers
- [ ] Implement sub-agent delegation
- [ ] Add web interface
- [ ] Advanced LSP features

### Q3 2026
- [ ] Performance optimization
- [ ] Internationalization
- [ ] Plugin system
- [ ] Extended tool library

### Q4 2026
- [ ] Stability and polish
- [ ] Documentation
- [ ] Community building
- [ ] Release 1.0

---

## Contributing

To contribute to the migration:

1. Check this document for unimplemented features
2. Review the TypeScript source in `opencode_repo/packages/opencode/src/`
3. Create corresponding Python implementation in `src/opencode/`
4. Follow the existing patterns and architecture
5. Add tests for new functionality
6. Submit a pull request

---

## Part 7: qwen-code Integration

**Source Project:** `merge_projects/qwen-code-no-telemetry/`

**Project Type:** Terminal-based AI Coding Agent (TypeScript/Node.js)

**Technology Stack:**
- **Runtime:** Node.js 20+
- **Language:** TypeScript 5.8+
- **CLI Framework:** yargs + Ink (React-based TUI)
- **Build:** esbuild
- **Testing:** Vitest

**Overview:**

Qwen Code is an open-source AI agent for the terminal, optimized for Qwen3-Coder. It's based on Google's Gemini CLI with adaptations for Qwen models. The project offers several unique features worth integrating:

### 7.1 Key Features to Integrate

| Feature | Source Location | Python Target | Priority | Status |
|---------|-----------------|---------------|----------|--------|
| **Subagents System** | `packages/core/src/subagents/` | `core/subagents/` | P0 | ⏳ |
| **Memory Tool** | `packages/core/src/tools/memoryTool.ts` | `tool/memory.py` | P1 | ⏳ |
| **Todo Write Tool** | `packages/core/src/tools/todoWrite.ts` | `tool/todo.py` | P1 | ✅ |
| **Web Fetch Tool** | `packages/core/src/tools/web-fetch.ts` | `tool/webfetch.py` | P1 | ✅ |
| **Web Search Tool** | `packages/core/src/tools/web-search/` | `tool/websearch.py` | P1 | ✅ |
| **Skill System** | `packages/core/src/skills/` | `skills/` | P1 | ✅ |
| **MCP Client** | `packages/core/src/tools/mcp-*.ts` | `mcp/client.py` | P0 | ✅ |
| **LSP Integration** | `packages/core/src/lsp/` | `tool/lsp.py` | P1 | ✅ |
| **Plan Mode** | `packages/core/src/tools/exitPlanMode.ts` | `tool/plan.py` | P1 | ✅ |

### 7.2 Subagents Architecture

The subagents system is a key differentiator, allowing specialized AI assistants:

```typescript
// From qwen-code subagents/types.ts
interface SubagentConfig {
  name: string;              // Unique identifier
  description: string;       // When to use this agent
  prompt: PromptConfig;      // System prompt configuration
  model?: ModelConfig;       // Model selection
  tools?: ToolConfig;        // Tool access control
  run?: RunConfig;           // Execution settings
}
```

**Python Implementation Plan:**

```python
# src/opencode/core/subagents/__init__.py
from pydantic import BaseModel
from typing import Optional, List

class SubagentConfig(BaseModel):
    name: str
    description: str
    prompt: str
    model: Optional[str] = None
    tools: Optional[List[str]] = None
    auto_approve: bool = False
    
class SubagentManager:
    """Manages file-based subagent configurations"""
    
    async def list_subagents(self, level: str = "all") -> List[SubagentConfig]:
        """List available subagents from project and user levels"""
        pass
    
    async def create_subagent(self, config: SubagentConfig, level: str = "project") -> None:
        """Create a new subagent configuration"""
        pass
    
    async def run_subagent(self, name: str, task: str) -> SubagentResult:
        """Execute a task using a specific subagent"""
        pass
```

### 7.3 Memory Tool

The memory tool provides persistent memory across sessions:

```typescript
// From qwen-code memoryTool.ts
// Operations: save, get, list, delete, switch (project/global scope)
```

**Python Implementation:**

```python
# src/opencode/tool/memory.py
class MemoryTool(BaseTool):
    """Persistent memory storage for sessions"""
    
    async def save(self, key: str, value: str, scope: str = "project") -> None:
        """Save a memory entry"""
        pass
    
    async def get(self, key: str, scope: str = "project") -> Optional[str]:
        """Retrieve a memory entry"""
        pass
    
    async def list(self, scope: str = "all") -> List[MemoryEntry]:
        """List all memory entries"""
        pass
```

### 7.4 Authentication Features

Qwen Code supports multiple authentication methods:

| Method | Description | Python Target |
|--------|-------------|---------------|
| **Qwen OAuth** | Free tier with 1,000 requests/day | `provider/qwen.py` |
| **API Key** | OpenAI/Anthropic/Gemini compatible | ✅ Already implemented |
| **DashScope** | Alibaba Cloud integration | `provider/dashscope.py` |

### 7.5 IDE Integrations

| IDE | Source | Python Target | Status |
|-----|--------|---------------|--------|
| **VS Code** | `packages/vscode-ide-companion/` | N/A (extension) | ⏳ |
| **Zed** | `packages/zed-extension/` | N/A (extension) | ⏳ |
| **JetBrains** | Documentation only | N/A | ⏳ |

### 7.6 TypeScript SDK

The SDK provides programmatic access:

```typescript
// packages/sdk-typescript/
import { QwenCode } from '@qwen-code/sdk';

const client = new QwenCode();
const response = await client.chat('Hello!');
```

**Python SDK equivalent could be:**

```python
# src/opencode/sdk/__init__.py
from opencode.core.session import Session

class OpenCodeSDK:
    def __init__(self, provider: str = "openai"):
        self.session = Session(provider=provider)
    
    async def chat(self, message: str) -> str:
        return await self.session.send_message(message)
```

### 7.7 Dependencies to Consider

```toml
# From qwen-code package.json
dependencies = [
    # Already have most dependencies
    # Unique additions:
    "youtube-transcript-api",  # For YouTube RAG integration
    "qrcode-terminal",         # For OAuth QR code display
]
```

---

## Part 8: youtube_Rag Integration

**Source Project:** `merge_projects/youtube_Rag/`

**Project Type:** YouTube Video RAG (Retrieval-Augmented Generation) Assistant

**Technology Stack:**
- **Language:** Python 3.x
- **LLM:** Google Gemini (via API), Ollama (local)
- **Embeddings:** Ollama (nomic-embed-text)
- **Transcripts:** youtube-transcript-api

**Overview:**

A specialized RAG system for querying YouTube video content. It fetches video transcripts, creates embeddings, and enables natural language Q&A about video content.

### 8.1 Core Components

| Component | Source File | Python Target | Priority | Status |
|-----------|-------------|---------------|----------|--------|
| **Transcript Fetcher** | `main.py` | `tool/youtube.py` | P2 | ⏳ |
| **Embedding Engine** | `main.py` | `util/embeddings.py` | P2 | ⏳ |
| **RAG Pipeline** | `main.py` | `core/rag/` | P2 | ⏳ |
| **Cosine Similarity** | `main.py` | `util/similarity.py` | P2 | ⏳ |

### 8.2 Architecture Analysis

```python
# From youtube_Rag/main.py
class YoutubeRagAssistant:
    def __init__(self, url: str):
        self._url = url
        self._dataframe, self._summary = self.__initiate_dataframe_and_get_summary()
    
    def __fetch_transcript(self, url: str) -> list[dict]:
        """Fetch YouTube video transcript"""
        video_id = extract_video_id(url)
        yt_api = YouTubeTranscriptApi()
        return yt_api.fetch(video_id)
    
    def __merge_chunks(self, transcript: list[dict], group_chunk_num: int = 6):
        """Group transcript chunks for better context"""
        # Merges small chunks into larger context-preserving chunks
        pass
    
    def __create_embeddings(self, transcript: list[dict]):
        """Create embeddings using Ollama nomic-embed-text"""
        embeddings = ollama.embed(model="nomic-embed-text", input=arr_text)
        return transcript_with_embeddings
    
    def __fetch_relevant_metadata(self, user_query: str, dataframe, top_result=3):
        """Find most relevant chunks using cosine similarity"""
        embedded_query = embed_query(user_query)
        similarity = cosine_similarity(embeddings, [embedded_query])
        return top_similar_chunks
    
    def __LLM_response(self, query, metadata, summary):
        """Generate response using LLM with context"""
        prompt = f"query: {query}\ndata: {metadata}"
        return llm.generate(prompt)
```

### 8.3 Integration Plan

**Phase 1: YouTube Tool**

```python
# src/opencode/tool/youtube.py
from youtube_transcript_api import YouTubeTranscriptApi
from typing import Optional, List
import re

class YouTubeTranscriptTool(BaseTool):
    """Fetch and process YouTube video transcripts"""
    
    name = "youtube_transcript"
    description = "Fetch transcript from a YouTube video for analysis"
    
    async def execute(self, url: str, language: str = "en") -> dict:
        """
        Fetch transcript from YouTube video.
        
        Args:
            url: YouTube video URL
            language: Preferred transcript language
            
        Returns:
            Transcript with metadata (text, timestamps, duration)
        """
        video_id = self._extract_video_id(url)
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
        return {
            "video_id": video_id,
            "transcript": transcript,
            "full_text": " ".join(chunk["text"] for chunk in transcript)
        }
    
    def _extract_video_id(self, url: str) -> str:
        """Extract video ID from various YouTube URL formats"""
        patterns = [
            r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
            r"(?:embed\/)([0-9A-Za-z_-]{11})",
            r"(?:youtu\.be\/)([0-9A-Za-z_-]{11})"
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        raise ValueError(f"Invalid YouTube URL: {url}")
```

**Phase 2: RAG Pipeline**

```python
# src/opencode/core/rag/__init__.py
from pydantic import BaseModel
from typing import List, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class RAGConfig(BaseModel):
    """RAG pipeline configuration"""
    embedding_model: str = "nomic-embed-text"
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k: int = 3

class RAGPipeline:
    """Retrieval-Augmented Generation pipeline"""
    
    def __init__(self, config: RAGConfig = None):
        self.config = config or RAGConfig()
        self.documents: List[dict] = []
        self.embeddings: Optional[np.ndarray] = None
    
    async def add_document(self, text: str, metadata: dict = None):
        """Add a document to the RAG index"""
        chunks = self._chunk_text(text)
        for chunk in chunks:
            embedding = await self._embed(chunk)
            self.documents.append({
                "text": chunk,
                "embedding": embedding,
                "metadata": metadata or {}
            })
    
    async def query(self, query: str, top_k: int = None) -> List[dict]:
        """Find most relevant documents for query"""
        query_embedding = await self._embed(query)
        similarities = cosine_similarity(
            [doc["embedding"] for doc in self.documents],
            [query_embedding]
        )
        top_indices = similarities.argsort()[-(top_k or self.config.top_k):][::-1]
        return [self.documents[i] for i in top_indices]
    
    def _chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []
        for i in range(0, len(words), self.config.chunk_size - self.config.chunk_overlap):
            chunk = " ".join(words[i:i + self.config.chunk_size])
            chunks.append(chunk)
        return chunks
    
    async def _embed(self, text: str) -> np.ndarray:
        """Create embedding using configured model"""
        # Use Ollama or other embedding provider
        pass
```

### 8.4 Dependencies to Add

```toml
# pyproject.toml additions
dependencies = [
    # YouTube RAG
    "youtube-transcript-api>=0.6.0",
    "scikit-learn>=1.3.0",  # For cosine similarity
]
```

### 8.5 Usage Example

```python
# Example usage after integration
from opencode.tool.youtube import YouTubeTranscriptTool
from opencode.core.rag import RAGPipeline

# Fetch transcript
yt_tool = YouTubeTranscriptTool()
transcript = await yt_tool.execute("https://youtu.be/example")

# Create RAG index
rag = RAGPipeline()
await rag.add_document(transcript["full_text"], {"video_id": transcript["video_id"]})

# Query
results = await rag.query("What is the main topic?")
```

---

## Part 9: balmasi-youtube-rag Integration

**Source Project:** `merge_projects/balmasi-youtube-rag/`

**Project Type:** YouTube Channel Persona RAG

**Technology Stack:**
- **Language:** Python 3.10-3.12
- **Orchestration:** Dagster
- **Vector DB:** Pinecone (serverless)
- **LLM:** OpenAI
- **Serving:** LangServe
- **Transcripts:** youtube-transcript-api

**Overview:**

A sophisticated RAG system that creates a "persona" chatbot from a YouTube creator's entire channel. It indexes all video transcripts and enables natural language Q&A about the creator's content.

### 9.1 Key Features

| Feature | Source Location | Python Target | Priority | Status |
|---------|-----------------|---------------|----------|--------|
| **Channel Indexing** | `src/indexing/assets.py` | `core/youtube/channel.py` | P2 | ⏳ |
| **Dagster Orchestration** | `src/indexing/__init__.py` | `core/youtube/jobs.py` | P3 | ⏳ |
| **Pinecone Integration** | `src/indexing/resources.py` | `core/rag/vector_stores/pinecone.py` | P2 | ⏳ |
| **LangServe Endpoint** | `src/serving/serve.py` | `server/routes/youtube.py` | P3 | ⏳ |
| **Retrieval System** | `src/serving/retrieval.py` | `core/youtube/retrieval.py` | P2 | ⏳ |

### 9.2 Architecture Highlights

```python
# From balmasi-youtube-rag/src/indexing/assets.py
# Dagster assets for incremental indexing

@asset
def video_ids(context, youtube_client, channel_handle: str) -> list[str]:
    """Fetch all video IDs from a YouTube channel"""
    pass

@asset
def transcripts(context, video_ids: list[str]) -> list[dict]:
    """Fetch transcripts for all videos"""
    pass

@asset
def embeddings(context, transcripts: list[dict]) -> list[dict]:
    """Create and store embeddings in Pinecone"""
    pass
```

### 9.3 Integration Plan

```python
# src/opencode/core/youtube/channel.py
from pydantic import BaseModel
from typing import Optional, List
import asyncio

class YouTubeChannelIndexer:
    """Index entire YouTube channels for RAG"""
    
    def __init__(self, channel_handle: str, vector_store: str = "chroma"):
        self.channel_handle = channel_handle
        self.vector_store = vector_store
    
    async def fetch_video_ids(self) -> List[str]:
        """Fetch all video IDs from channel"""
        pass
    
    async def index_channel(self, incremental: bool = True) -> int:
        """Index all videos, optionally only new ones"""
        pass
    
    async def get_channel_stats(self) -> dict:
        """Get indexing statistics"""
        pass
```

### 9.4 Dependencies

```toml
dependencies = [
    # YouTube channel indexing
    "google-api-python-client>=2.116.0",  # YouTube Data API
    "pinecone-client>=3.0.0",             # Pinecone vector store
]
```

---

## Part 10: MultiModal-RAG-with-Videos Integration

**Source Project:** `merge_projects/MultiModal-RAG-with-Videos/`

**Project Type:** MultiModal Video RAG (Visual + Text)

**Technology Stack:**
- **Language:** Python 3.x
- **Framework:** Streamlit
- **LLM:** OpenAI GPT-4-turbo (multimodal)
- **Vector DB:** LanceDB
- **Video Processing:** MoviePy, pytube
- **Audio:** SpeechRecognition (Whisper)

**Overview:**

An advanced multimodal RAG system that processes both visual frames and audio transcripts from YouTube videos. It can answer questions about visual content shown in videos, not just spoken content.

### 10.1 Key Features

| Feature | Source Location | Python Target | Priority | Status |
|---------|-----------------|---------------|----------|--------|
| **Frame Extraction** | `app.py:video_to_images()` | `core/video/frames.py` | P2 | ⏳ |
| **Audio Extraction** | `app.py:video_to_audio()` | `core/video/audio.py` | P2 | ⏳ |
| **Whisper Transcription** | `app.py:audio_to_text()` | `core/video/transcribe.py` | P2 | ⏳ |
| **Multimodal Index** | `app.py:MultiModalVectorStoreIndex` | `core/rag/multimodal.py` | P2 | ⏳ |
| **LanceDB Integration** | `app.py` | `core/rag/vector_stores/lancedb.py` | P2 | ⏳ |

### 10.2 Architecture Highlights

```python
# From MultiModal-RAG-with-Videos/app.py
def video_to_images(video_path, output_folder):
    """Extract frames from video at 0.5 fps"""
    clip = VideoFileClip(video_path)
    clip.write_images_sequence(os.path.join(output_folder, "frame%04d.png"), fps=0.5)

def video_to_audio(video_path, output_audio_path):
    """Extract audio from video"""
    clip = VideoFileClip(video_path)
    audio = clip.audio
    audio.write_audiofile(output_audio_path)

def audio_to_text(audio_path):
    """Transcribe audio using Whisper"""
    recognizer = sr.Recognizer()
    audio = sr.AudioFile(audio_path)
    with audio as source:
        audio_data = recognizer.record(source)
        return recognizer.recognize_whisper(audio_data)
```

### 10.3 Integration Plan

```python
# src/opencode/core/video/frames.py
from pathlib import Path
from typing import List
import asyncio

class FrameExtractor:
    """Extract key frames from videos for multimodal RAG"""
    
    def __init__(self, fps: float = 0.5):
        self.fps = fps
    
    async def extract_frames(self, video_path: str, output_dir: str) -> List[str]:
        """Extract frames from video file"""
        pass
    
    async def extract_key_frames(self, video_path: str) -> List[dict]:
        """Extract only key frames with significant changes"""
        pass

# src/opencode/core/rag/multimodal.py
class MultiModalRAGPipeline:
    """RAG pipeline supporting both text and images"""
    
    async def add_video(self, video_path: str) -> None:
        """Process and index a video (frames + audio)"""
        frames = await self.frame_extractor.extract_frames(video_path)
        transcript = await self.transcriber.transcribe(video_path)
        await self.index.add_images(frames)
        await self.index.add_text(transcript)
    
    async def query(self, question: str) -> MultiModalResult:
        """Query with multimodal retrieval"""
        pass
```

### 10.4 Dependencies

```toml
dependencies = [
    # Multimodal video processing
    "moviepy>=1.0.3",
    "SpeechRecognition>=3.10.0",
    "lancedb>=0.3.0",
    "llama-index-core>=0.10.0",
    "llama-index-vector-stores-lancedb>=0.1.0",
]
```

---

## Part 11: rag-youtube-assistant Integration

**Source Project:** `merge_projects/rag-youtube-assistant/`

**Project Type:** Full-Featured YouTube RAG Assistant

**Technology Stack:**
- **Language:** Python 3.x
- **Framework:** Streamlit
- **Database:** SQLite + Elasticsearch
- **LLM:** Ollama (local)
- **Evaluation:** Custom RAG evaluation framework

**Overview:**

A comprehensive YouTube RAG system with advanced features like query rewriting, ground truth generation, RAG evaluation metrics, and a complete web UI with Docker deployment.

### 11.1 Key Features

| Feature | Source Location | Python Target | Priority | Status |
|---------|-----------------|---------------|----------|--------|
| **Transcript Extractor** | `app/transcript_extractor.py` | `core/youtube/transcript.py` | P2 | ⏳ |
| **Query Rewriter** | `app/query_rewriter.py` | `core/rag/query_rewriter.py` | P2 | ⏳ |
| **RAG Evaluation** | `app/evaluation.py` | `core/rag/evaluation.py` | P2 | ⏳ |
| **Ground Truth Gen** | `app/generate_ground_truth.py` | `core/rag/ground_truth.py` | P3 | ⏳ |
| **MinSearch** | `app/minsearch.py` | `core/rag/minsearch.py` | P3 | ⏳ |
| **Elasticsearch Handler** | `app/elasticsearch_handler.py` | `core/rag/vector_stores/elasticsearch.py` | P2 | ⏳ |

### 11.2 Architecture Highlights

```python
# From rag-youtube-assistant/app/rag.py
RAG_PROMPT_TEMPLATE = """
You are an AI assistant analyzing YouTube video transcripts. Your task is to answer questions based on the provided transcript context.

Context from transcript:
{context}

User Question: {question}

Please provide a clear, concise answer based only on the information given in the context.
"""

class RAGSystem:
    def __init__(self, data_processor):
        self.data_processor = data_processor
        self.model = os.getenv('OLLAMA_MODEL', 'phi3')
    
    def query(self, user_query, search_method='hybrid', index_name=None):
        """Query with hybrid search (keyword + semantic)"""
        relevant_docs = self.data_processor.search(
            user_query, num_results=3, method=search_method, index_name=index_name
        )
        prompt = self.get_prompt(user_query, relevant_docs)
        return ollama.chat(model=self.model, messages=[{"role": "user", "content": prompt}])
```

### 11.3 Integration Plan

```python
# src/opencode/core/rag/query_rewriter.py
from pydantic import BaseModel
from typing import Optional

class QueryRewriter:
    """Rewrite queries for better retrieval"""
    
    async def expand_query(self, query: str) -> list[str]:
        """Generate multiple query variations"""
        pass
    
    async def hyde_query(self, query: str) -> str:
        """Generate hypothetical document for HyDE retrieval"""
        pass

# src/opencode/core/rag/evaluation.py
class RAGEvaluator:
    """Evaluate RAG system performance"""
    
    async def generate_ground_truth(self, documents: list[dict]) -> list[dict]:
        """Generate ground truth Q&A pairs"""
        pass
    
    async def evaluate_retrieval(self, queries: list[dict]) -> dict:
        """Calculate retrieval metrics (recall, MRR, etc.)"""
        pass
    
    async def evaluate_generation(self, responses: list[dict]) -> dict:
        """Calculate generation metrics (faithfulness, relevance)"""
        pass
```

### 11.4 Dependencies

```toml
dependencies = [
    # RAG evaluation
    "elasticsearch>=8.0.0",
    "minsearch>=0.1.0",  # Lightweight search
]
```

---

## Part 12: svpino-youtube-rag Integration

**Source Project:** `merge_projects/svpino-youtube-rag/`

**Project Type:** Educational RAG Implementation

**Technology Stack:**
- **Language:** Python 3.x
- **Format:** Jupyter Notebook
- **Vector DB:** Pinecone
- **LLM:** OpenAI
- **Transcription:** OpenAI Whisper

**Overview:**

A step-by-step educational implementation of a RAG application from scratch. While simple, it provides clear patterns for building RAG systems with Pinecone and OpenAI.

### 12.1 Key Features

| Feature | Source Location | Python Target | Priority | Status |
|---------|-----------------|---------------|----------|--------|
| **Pinecone Setup** | `rag.ipynb` | `core/rag/vector_stores/pinecone.py` | P2 | ⏳ |
| **Whisper Transcription** | `requirements.txt` | `core/video/transcribe.py` | P2 | ⏳ |
| **Simple RAG Chain** | `rag.ipynb` | `core/rag/chains.py` | P3 | ⏳ |

### 12.2 Architecture Highlights

The notebook demonstrates:
1. Audio extraction from YouTube videos
2. Transcription using OpenAI Whisper
3. Text chunking and embedding
4. Pinecone vector storage
5. Query and retrieval with OpenAI

### 12.3 Integration Value

This project provides:
- Clear, documented RAG patterns
- Pinecone integration examples
- Whisper transcription workflow
- Educational reference for RAG concepts

---

## Part 13: youtube-rag Integration

**Source Project:** `merge_projects/youtube-rag/`

**Project Type:** Lightweight YouTube RAG with Timestamps

**Technology Stack:**
- **Language:** Python 3.x
- **Framework:** Flask
- **Vector DB:** ChromaDB
- **Embeddings:** FastEmbed (BAAI/bge-small-en-v1.5)
- **LLM:** Groq (Llama3-70b)

**Overview:**

A lightweight Flask-based YouTube RAG that provides timestamped YouTube links to exact moments in videos where answers are discussed. Uses efficient FastEmbed embeddings and ChromaDB.

### 13.1 Key Features

| Feature | Source Location | Python Target | Priority | Status |
|---------|-----------------|---------------|----------|--------|
| **FastEmbed Integration** | `embed_upload.py` | `core/rag/embeddings/fastembed.py` | P2 | ⏳ |
| **ChromaDB Integration** | `embed_upload.py` | `core/rag/vector_stores/chroma.py` | P2 | ⏳ |
| **Timestamped Links** | `retrieve_create.py` | `core/youtube/timestamps.py` | P2 | ⏳ |
| **Transcript Chunking** | `embed_upload.py` | `core/youtube/chunking.py` | P2 | ⏳ |

### 13.2 Architecture Highlights

```python
# From youtube-rag/embed_upload.py
def get_combined_transcript(video_id, chunk_size=10):
    """Fetch and chunk transcript with timestamps"""
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    
    combined_transcript = [
        {
            "text": " ".join([item["text"] for item in transcript[i:i+chunk_size]]),
            "start": "{:.2f}".format(transcript[i]["start"]),
            "duration": "{:.2f}".format(sum([item["duration"] for item in transcript[i:i+chunk_size]]))
        }
        for i in range(0, len(transcript), chunk_size)
    ]
    return combined_transcript

def initialize_vector_store(chromadb_path="chromadb/"):
    """Initialize FastEmbed + ChromaDB"""
    embeddings = FastEmbedEmbeddings(
        model_name="BAAI/bge-small-en-v1.5",
        batch_size=512,
        parallel=2,
        threads=4
    )
    return Chroma(
        collection_name="example_collection",
        embedding_function=embeddings,
        persist_directory=chromadb_path
    )
```

### 13.3 Integration Plan

```python
# src/opencode/core/youtube/timestamps.py
from pydantic import BaseModel
from typing import List

class TimestampedResult(BaseModel):
    """Search result with YouTube timestamp"""
    text: str
    start_time: float
    duration: float
    video_id: str
    youtube_url: str  # Direct link with timestamp

class TimestampGenerator:
    """Generate timestamped YouTube links"""
    
    def create_timestamp_url(self, video_id: str, start_time: float) -> str:
        """Create YouTube URL with timestamp"""
        return f"https://www.youtube.com/watch?v={video_id}&t={int(start_time)}s"
    
    def format_results_with_timestamps(self, results: List[dict], video_id: str) -> List[TimestampedResult]:
        """Add timestamped URLs to search results"""
        return [
            TimestampedResult(
                text=r["text"],
                start_time=r["start"],
                duration=r["duration"],
                video_id=video_id,
                youtube_url=self.create_timestamp_url(video_id, r["start"])
            )
            for r in results
        ]

# src/opencode/core/rag/embeddings/fastembed.py
class FastEmbedEngine:
    """FastEmbed embedding engine for efficient local embeddings"""
    
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self.model_name = model_name
    
    async def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """Embed multiple documents efficiently"""
        pass
    
    async def embed_query(self, query: str) -> List[float]:
        """Embed a single query"""
        pass
```

### 13.4 Dependencies

```toml
dependencies = [
    # FastEmbed for efficient local embeddings
    "fastembed>=0.1.0",
    # ChromaDB vector store
    "chromadb>=0.4.0",
    # Groq for fast inference
    # (already have groq provider)
]
```

---

## YouTube RAG Integration Summary

| Project | Key Contribution | Vector Store | Embeddings | Priority |
|---------|------------------|--------------|------------|----------|
| **balmasi-youtube-rag** | Channel-level indexing | Pinecone | OpenAI | P2 |
| **MultiModal-RAG-with-Videos** | Visual + text RAG | LanceDB | OpenAI | P2 |
| **rag-youtube-assistant** | Evaluation + Query rewriting | Elasticsearch | Ollama | P2 |
| **svpino-youtube-rag** | Educational patterns | Pinecone | OpenAI | P3 |
| **youtube-rag** | Timestamped links + FastEmbed | ChromaDB | FastEmbed | P2 |

### Unified YouTube RAG Architecture

```python
# Proposed unified interface
# src/opencode/core/youtube/__init__.py

class YouTubeRAGSystem:
    """Unified YouTube RAG with multiple backends"""
    
    def __init__(
        self,
        vector_store: str = "chroma",  # chroma, pinecone, lancedb, elasticsearch
        embedding_model: str = "fastembed",  # fastembed, ollama, openai
        llm_provider: str = "ollama"  # ollama, openai, groq
    ):
        self.vector_store = self._init_vector_store(vector_store)
        self.embeddings = self._init_embeddings(embedding_model)
        self.llm = self._init_llm(llm_provider)
    
    async def index_video(self, video_url: str, include_frames: bool = False):
        """Index a single video"""
        pass
    
    async def index_channel(self, channel_handle: str):
        """Index entire channel"""
        pass
    
    async def query(self, question: str, return_timestamps: bool = True):
        """Query with optional timestamped results"""
        pass
```

---

## File Reference

### TypeScript Source Structure

```
opencode_repo/packages/opencode/src/
├── index.ts              # CLI entry point
├── agent/                # Agent definitions
├── auth/                 # Authentication
├── bus/                  # Event bus
├── cli/                  # CLI commands
│   └── cmd/              # Command implementations
│       └── tui/          # TUI components
├── config/               # Configuration
├── file/                 # File utilities
├── flag/                 # Feature flags
├── global/               # Global state
├── installation/         # Version info
├── lsp/                  # LSP integration
├── mcp/                  # MCP client
├── permission/           # Permission system
├── plugin/               # Plugin system
├── project/              # Project management
├── provider/             # AI providers
├── pty/                  # Pseudo-terminal
├── question/             # Question handling
├── scheduler/            # Task scheduling
├── server/               # HTTP server
│   └── routes/           # API routes
├── session/              # Session management
├── share/                # Sharing features
├── shell/                # Shell integration
├── skill/                # Skill system
├── snapshot/             # State snapshots
├── storage/              # Data persistence
├── tool/                 # Tool implementations
├── util/                 # Utilities
└── worktree/             # Git worktree
```

### Python Target Structure

```
src/opencode/src/opencode/
├── __init__.py
├── __main__.py
├── cli/                  # CLI commands
├── core/                 # Core functionality
├── db/                   # Database layer
├── mcp/                  # MCP client
├── provider/             # AI providers
├── server/               # HTTP server
├── tool/                 # Tool implementations
├── tui/                  # TUI components
└── util/                 # Utilities
```

---

*Last updated: 2026-02-21*
