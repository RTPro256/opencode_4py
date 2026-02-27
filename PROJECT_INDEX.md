# OpenCode Python - Complete Documentation

## Project Overview

OpenCode Python is an open-source AI coding agent - a complete rewrite of the original [OpenCode](https://github.com/anomalyco/opencode) project in Python. It provides a provider-agnostic AI assistant for software development with a terminal UI, HTTP server, and web interface.

**Version:** 1.0.0 | **Python:** 3.12+ | **License:** MIT

---

## Key Features

### 🤖 Multi-Provider Support (15+ Providers)

| Provider | Models |
|----------|--------|
| Anthropic | Claude 4, Claude 3.5 Sonnet/Opus |
| OpenAI | GPT-4o, GPT-4, o1, o3 |
| Google | Gemini 2.0, Gemini 1.5 Pro/Flash |
| Azure | GPT-4, GPT-4o |
| AWS Bedrock | Claude, Llama, Mistral |
| Groq | Llama, Mixtral (fast inference) |
| Mistral | Mistral Large, Codestral |
| xAI | Grok |
| Cohere | Command R+ |
| Perplexity | Sonar |
| Together AI | Open source models |
| Cerebras | Llama (fast inference) |
| OpenRouter | 100+ models |
| Ollama | Local models |
| LM Studio | Local models |

### 🛠️ 21 Built-in Tools
- **File Operations**: read, write, edit, glob, grep, ls, rm
- **Code Analysis**: lsp (definition, references, diagnostics, rename, format)
- **Web**: webfetch, websearch
- **Execution**: bash
- **Planning**: plan, todo, task
- **Advanced**: batch, multiedit, apply_patch, question

### 🔌 MCP Integration - Connect to MCP servers, act as MCP server, OAuth 2.0 support
### 🌍 Internationalization - 17+ languages
### 💻 Terminal UI - Chat view, diff view, session management, agent switching
### 🌐 Web Interface - REST API, streaming, WebSocket, mobile responsive
### ⚡ Multi-Model Patterns - Sequential, Ensemble, Voting
### 🚀 Multi-GPU Support - auto, round_robin, pack, spread, manual strategies

---

## Python File Structure & Purposes

### CLI Commands ([`cli/commands/`](src/opencode/src/opencode/cli/commands/))

| File | Purpose |
|------|---------|
| [`main.py`](src/opencode/src/opencode/cli/main.py) | Main CLI application using Typer |
| [`auth.py`](src/opencode/src/opencode/cli/commands/auth.py) | Authentication and OAuth management |
| [`config.py`](src/opencode/src/opencode/cli/commands/config.py) | Configuration management and presets |
| [`debug_cmd.py`](src/opencode/src/opencode/cli/commands/debug_cmd.py) | Debugging and troubleshooting |
| [`github.py`](src/opencode/src/opencode/cli/commands/github.py) | GitHub integration |
| [`index.py`](src/opencode/src/opencode/cli/commands/index.py) | Project indexing |
| [`llmchecker.py`](src/opencode/src/opencode/cli/commands/llmchecker.py) | LLM model checking |
| [`rag.py`](src/opencode/src/opencode/cli/commands/rag.py) | RAG main commands |
| [`rag_create.py`](src/opencode/src/opencode/cli/commands/rag_create.py) | RAG knowledge base creation |
| [`rag_manage.py`](src/opencode/src/opencode/cli/commands/rag_manage.py) | RAG management |
| [`rag_query.py`](src/opencode/src/opencode/cli/commands/rag_query.py) | RAG queries |
| [`rag_share.py`](src/opencode/src/opencode/cli/commands/rag_share.py) | RAG sharing |
| [`rag_audit.py`](src/opencode/src/opencode/cli/commands/rag_audit.py) | RAG auditing |
| [`rag_validation.py`](src/opencode/src/opencode/cli/commands/rag_validation.py) | RAG validation |
| [`run.py`](src/opencode/src/opencode/cli/commands/run.py) | AI-assisted run commands |
| [`serve.py`](src/opencode/src/opencode/cli/commands/serve.py) | HTTP server startup |
| [`model_picker.py`](src/opencode/src/opencode/cli/commands/model_picker.py) | Interactive model picker |

### Core Modules ([`core/`](src/opencode/src/opencode/core/))

| File | Purpose |
|------|---------|
| [`config.py`](src/opencode/src/opencode/core/config.py) | Configuration management |
| [`session.py`](src/opencode/src/opencode/core/session.py) | Session state management |
| [`sandbox.py`](src/opencode/src/opencode/core/sandbox.py) | File system sandboxing |
| [`gpu_manager.py`](src/opencode/src/opencode/core/gpu_manager.py) | Multi-GPU allocation |

#### Context ([`core/context/`](src/opencode/src/opencode/core/context/))
- [`checkpoints.py`](src/opencode/src/opencode/core/context/checkpoints.py) - Conversation checkpointing
- [`mentions.py`](src/opencode/src/opencode/core/context/mentions.py) - @mention tracking
- [`tracker.py`](src/opencode/src/opencode/core/context/tracker.py) - Context state tracking
- [`truncation.py`](src/opencode/src/opencode/core/context/truncation.py) - Context truncation

#### Modes ([`core/modes/`](src/opencode/src/opencode/core/modes/))
- [`base.py`](src/opencode/src/opencode/core/modes/base.py) - Base mode class
- [`manager.py`](src/opencode/src/opencode/core/modes/manager.py) - Mode management
- [`registry.py`](src/opencode/src/opencode/core/modes/registry.py) - Mode registration
- **Mode implementations**: [`architect.py`](src/opencode/src/opencode/core/modes/modes/architect.py), [`ask.py`](src/opencode/src/opencode/core/modes/modes/ask.py), [`code.py`](src/opencode/src/opencode/core/modes/modes/code.py), [`debug.py`](src/opencode/src/opencode/core/modes/modes/debug.py), [`orchestrator.py`](src/opencode/src/opencode/core/modes/modes/orchestrator.py), [`review.py`](src/opencode/src/opencode/core/modes/modes/review.py), [`updater.py`](src/opencode/src/opencode/core/modes/modes/updater.py)

#### Multi-AI Providers ([`core/providers/`](src/opencode/src/opencode/core/providers/))
- [`base.py`](src/opencode/src/opencode/core/providers/base.py) - BaseProvider abstract class
- [`client.py`](src/opencode/src/opencode/core/providers/client.py) - MultiAIClient main class
- [`usage_tracker.py`](src/opencode/src/opencode/core/providers/usage_tracker.py) - Local usage tracking
- **Provider implementations**: [`openai_provider.py`](src/opencode/src/opencode/core/providers/openai_provider.py), [`google_provider.py`](src/opencode/src/opencode/core/providers/google_provider.py), [`anthropic_provider.py`](src/opencode/src/opencode/core/providers/anthropic_provider.py), [`ollama_provider.py`](src/opencode/src/opencode/core/providers/ollama_provider.py), [`groq_provider.py`](src/opencode/src/opencode/core/providers/groq_provider.py), [`huggingface_provider.py`](src/opencode/src/opencode/core/providers/huggingface_provider.py), [`openrouter_provider.py`](src/opencode/src/opencode/core/providers/openrouter_provider.py), [`github_provider.py`](src/opencode/src/opencode/core/providers/github_provider.py)

#### Orchestration ([`core/orchestration/`](src/opencode/src/opencode/core/orchestration/))
- [`agent.py`](src/opencode/src/opencode/core/orchestration/agent.py) - Agent implementation
- [`coordinator.py`](src/opencode/src/opencode/core/orchestration/coordinator.py) - Task coordination
- [`registry.py`](src/opencode/src/opencode/core/orchestration/registry.py) - Agent registry
- [`router.py`](src/opencode/src/opencode/core/orchestration/router.py) - Request routing

### LLM Providers ([`provider/`](src/opencode/src/opencode/provider/))

| File | Provider |
|------|----------|
| [`base.py`](src/opencode/src/opencode/provider/base.py) | Abstract base class |
| [`anthropic.py`](src/opencode/src/opencode/provider/anthropic.py) | Anthropic Claude |
| [`openai.py`](src/opencode/src/opencode/provider/openai.py) | OpenAI GPT |
| [`google.py`](src/opencode/src/opencode/provider/google.py) | Google Gemini |
| [`azure.py`](src/opencode/src/opencode/provider/azure.py) | Azure OpenAI |
| [`bedrock.py`](src/opencode/src/opencode/provider/bedrock.py) | AWS Bedrock |
| [`groq.py`](src/opencode/src/opencode/provider/groq.py) | Groq |
| [`mistral.py`](src/opencode/src/opencode/provider/mistral.py) | Mistral |
| [`xai.py`](src/opencode/src/opencode/provider/xai.py) | xAI Grok |
| [`cohere.py`](src/opencode/src/opencode/provider/cohere.py) | Cohere |
| [`perplexity.py`](src/opencode/src/opencode/provider/perplexity.py) | Perplexity |
| [`together.py`](src/opencode/src/opencode/provider/together.py) | Together AI |
| [`cerebras.py`](src/opencode/src/opencode/provider/cerebras.py) | Cerebras |
| [`openrouter.py`](src/opencode/src/opencode/provider/openrouter.py) | OpenRouter |
| [`ollama.py`](src/opencode/src/opencode/provider/ollama.py) | Ollama (local) |
| [`lmstudio.py`](src/opencode/src/opencode/provider/lmstudio.py) | LM Studio (local) |
| [`custom.py`](src/opencode/src/opencode/provider/custom.py) | Custom provider |

### Tools ([`tool/`](src/opencode/src/opencode/tool/))

| File | Purpose |
|------|---------|
| [`base.py`](src/opencode/src/opencode/tool/base.py) | Base tool interface |
| [`bash.py`](src/opencode/src/opencode/tool/bash.py) | Shell commands |
| [`apply_patch.py`](src/opencode/src/opencode/tool/apply_patch.py) | Apply patches |
| [`batch.py`](src/opencode/src/opencode/tool/batch.py) | Batch operations |
| [`explore.py`](src/opencode/src/opencode/tool/explore.py) | Project exploration |
| [`question.py`](src/opencode/src/opencode/tool/question.py) | Ask questions |
| [`webfetch.py`](src/opencode/src/opencode/tool/webfetch.py) | Fetch web content |
| [`websearch.py`](src/opencode/src/opencode/tool/websearch.py) | Web search |
| [`youtube.py`](src/opencode/src/opencode/tool/youtube.py) | YouTube analysis |

### Server & Web ([`server/`](src/opencode/src/opencode/server/) & [`web/`](src/opencode/src/opencode/web/))

| File | Purpose |
|------|---------|
| [`server/app.py`](src/opencode/src/opencode/server/app.py) | FastAPI server |
| [`server/routes/chat.py`](src/opencode/src/opencode/server/routes/chat.py) | Chat API |
| [`server/routes/files.py`](src/opencode/src/opencode/server/routes/files.py) | Files API |
| [`server/routes/sessions.py`](src/opencode/src/opencode/server/routes/sessions.py) | Sessions API |
| [`server/routes/workflow.py`](src/opencode/src/opencode/server/routes/workflow.py) | Workflow API |
| [`server/graphql/schema.py`](src/opencode/src/opencode/server/graphql/schema.py) | GraphQL schema |
| [`web/app.py`](src/opencode/src/opencode/web/app.py) | Browser UI |

### TUI ([`tui/`](src/opencode/src/opencode/tui/))

| File | Purpose |
|------|---------|
| [`app.py`](src/opencode/src/opencode/tui/app.py) | Main TUI application |
| [`widgets/chat.py`](src/opencode/src/opencode/tui/widgets/chat.py) | Chat widget |
| [`widgets/input.py`](src/opencode/src/opencode/tui/widgets/input.py) | Input widget |
| [`widgets/sidebar.py`](src/opencode/src/opencode/tui/widgets/sidebar.py) | Sidebar |
| [`widgets/completion.py`](src/opencode/src/opencode/tui/widgets/completion.py) | Completion display |
| [`widgets/approval.py`](src/opencode/src/opencode/tui/widgets/approval.py) | Approval dialogs |

### MCP ([`mcp/`](src/opencode/src/opencode/mcp/))
- [`client.py`](src/opencode/src/opencode/mcp/client.py) - MCP client
- [`server.py`](src/opencode/src/opencode/mcp/server.py) - MCP server
- [`oauth.py`](src/opencode/src/opencode/mcp/oauth.py) - OAuth 2.0
- [`types.py`](src/opencode/src/opencode/mcp/types.py) - Type definitions

### Workflow ([`workflow/`](src/opencode/src/opencode/workflow/))
- [`engine.py`](src/opencode/src/opencode/workflow/engine.py) - Execution engine
- [`graph.py`](src/opencode/src/opencode/workflow/graph.py) - Graph representation
- [`node.py`](src/opencode/src/opencode/workflow/node.py) - Base node
- [`models.py`](src/opencode/src/opencode/workflow/models.py) - Data models
- [`nodes/chart.py`](src/opencode/src/opencode/workflow/nodes/chart.py) - Chart node
- [`nodes/data_source.py`](src/opencode/src/opencode/workflow/nodes/data_source.py) - Data source
- [`nodes/ensemble_aggregator.py`](src/opencode/src/opencode/workflow/nodes/ensemble_aggregator.py) - Ensemble

---

## Quick Start

```bash
# Install
git clone https://github.com/RTPro256/opencode_4py.git
cd opencode_4py/src/opencode
pip install -e .

# Set API key
export ANTHROPIC_API_KEY=your-key-here

# Launch
opencode                    # Terminal UI
opencode serve --port 4096  # HTTP server
opencode web               # Web interface
```
