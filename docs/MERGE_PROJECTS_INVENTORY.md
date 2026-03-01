# Merge Projects Inventory

> **Purpose**: Comprehensive inventory of all projects in `merge_projects/` for integration into opencode_4py

---

## Executive Summary

| Category | Project Count | Integration Priority | Estimated Complexity |
|----------|---------------|---------------------|---------------------|
| RAG Core | 4 | High | Medium-High |
| YouTube RAG | 5 | Medium | Medium |
| Fine-tuning | 2 | Medium | High |
| Code Assistants | 4 | Medium | Medium |
| Planning Systems | 2 | Low | Low |
| Infrastructure | 4 | Low | Medium |
| Multi-Agent Orchestration | 1 | High | High |
| Memory Management | 1 | High | High |

**Total Projects**: 23

---

## Existing opencode_4py RAG Architecture

The following modules already exist and should be enhanced rather than duplicated:

### Core RAG Modules (`src/opencode/src/opencode/core/rag/`)
- `local_embeddings.py` - Local embedding support (12,619 chars)
- `local_vector_store.py` - Local vector store (17,663 chars)
- `hybrid_search.py` - Hybrid search patterns (14,945 chars)
- `embeddings.py` - Embedding functionality (7,359 chars)
- `retriever.py` - Retrieval logic (5,895 chars)
- `query_rewriter.py` - Query rewriting (8,662 chars)
- `evaluation.py` - RAG evaluation (13,282 chars)
- `pipeline.py` - RAG pipeline (9,368 chars)
- `agent_rag_manager.py` - Agent RAG management (14,721 chars)
- `citations.py` - Citation handling (13,028 chars)
- `document.py` - Document handling (3,922 chars)
- `source_manager.py` - Source management (12,214 chars)
- `config.py` - RAG configuration (6,740 chars)

### YouTube/Media Modules (`src/opencode/src/opencode/core/youtube/`)
- `transcript.py` - Transcript handling (10,235 chars)
- `channel.py` - Channel processing (15,378 chars)
- `chunking.py` - Chunking strategies (10,878 chars)
- `timestamps.py` - Timestamp handling (9,154 chars)

### Video Modules (`src/opencode/src/opencode/core/video/`)
- `audio.py` - Audio processing (12,096 chars)
- `frames.py` - Frame extraction (9,576 chars)

---

## Project Inventories

### 1. Local-RAG-with-Ollama

**Category**: RAG Core (High Priority)

**Description**: Local RAG implementation with Ollama for privacy-first embedding and chat.

**Files**:
| File | Size | Purpose |
|------|------|---------|
| `1_scraping_wikipedia.py` | 4,329 chars | Web scraping with Bright Data API |
| `2_chunking_embedding_ingestion.py` | 3,772 chars | Chunking, embedding, and vector store ingestion |
| `3_chatbot.py` | 4,389 chars | Streamlit chatbot with LangChain agent |
| `example_chunking.py` | 3,919 chars | Chunking examples |
| `example_embedding.py` | 312 chars | Embedding examples |
| `example_retriever.py` | 1,477 chars | Retriever examples |
| `requirements.txt` | 5,126 chars | Dependencies |
| `readme.md` | 1,705 chars | Documentation |

**Key Features**:
- OllamaEmbeddings integration
- ChromaDB vector store
- RecursiveCharacterTextSplitter (chunk_size=1000, overlap=200)
- LangChain agent with tool calling
- Streamlit UI for chatbot

**Dependencies**:
- langchain, langchain-chroma, langchain-ollama, langchain-text-splitters
- chromadb==1.0.9
- ollama==0.4.8
- streamlit==1.45.1

**Integration Target**: Enhance `local_embeddings.py` and `local_vector_store.py`

**Integration Value**: HIGH - Direct alignment with privacy-first RAG goals

---

### 2. OpenRAG

**Category**: RAG Core (High Priority)

**Description**: Comprehensive RAG benchmark tool with 12+ RAG methods implemented.

**Structure**:
```
OpenRAG/
├── backend/
│   ├── methods/
│   │   ├── advanced_rag/         # Advanced RAG with reranking
│   │   ├── agentic_rag/          # Agentic RAG implementation
│   │   ├── agentic_rag_router/   # Router for multiple agents
│   │   ├── contextual_retrieval_rag/
│   │   ├── corrective_rag/       # CRAG implementation
│   │   ├── graph_rag/            # Graph RAG with entity extraction
│   │   ├── merger_rag/           # Merge multiple RAG results
│   │   ├── naive_rag/            # Basic RAG implementation
│   │   ├── query_based_rag/      # Query-based retrieval
│   │   ├── query_reformulation/  # Query transformation
│   │   ├── reranker_rag/         # Reranking RAG
│   │   ├── self_rag/             # Self-reflective RAG
│   │   ├── semantic_chunking_rag/
│   │   └── naive_chatbot/
│   ├── evaluation/               # RAG evaluation framework
│   ├── database/                 # Database classes
│   └── utils/                    # Utilities
├── streamlit_/                   # Streamlit UI
└── infrastructure/               # Docker configs
```

**Key Features**:
- 12+ RAG method implementations
- Multi-provider support (Ollama, VLLM, OpenAI, Mistral)
- Evaluation framework with metrics
- Elasticsearch integration
- Graph RAG with community detection
- Corrective RAG (CRAG)
- Self-RAG with reflection

**Dependencies**:
- Elasticsearch support
- Multiple LLM providers
- Streamlit for UI

**Integration Target**: 
- Create `src/opencode/core/rag/methods/` for RAG method implementations
- Enhance `evaluation.py` with evaluation framework

**Integration Value**: VERY HIGH - Comprehensive RAG method library

---

### 3. RAG-Project

**Category**: RAG Core (High Priority)

**Description**: Simple RAG example project.

**Files**:
| File | Size | Purpose |
|------|------|---------|
| `rag_example.py` | 1,515 chars | Basic RAG example |
| `olympastadion test.py` | 1,710 chars | Test script |
| `README.md` | 7,645 chars | Documentation |

**Integration Value**: LOW - Basic examples, mostly educational

---

### 4. RAG_Techniques

**Category**: RAG Core (High Priority)

**Description**: Collection of 30+ RAG technique notebooks with comprehensive documentation.

**Key Techniques**:
- Adaptive Retrieval
- Agentic RAG
- Context Enrichment Window
- Contextual Chunk Headers
- Contextual Compression
- CRAG (Corrective RAG)
- Dartboard
- Document Augmentation
- Fusion Retrieval
- Graph RAG
- Hierarchical Indices
- HyDe (Hypothetical Document Embedding)
- HyPE (Hypothetical Prompt Embeddings)
- Microsoft GraphRAG
- Multi-model RAG with Captioning
- Multi-model RAG with ColPali
- Proposition Chunking
- Query Transformations
- RAPTOR
- Relevant Segment Extraction
- Reliable RAG
- Reranking
- Retrieval with Feedback Loop
- Self RAG
- Semantic Chunking
- Simple CSV RAG

**Files**:
| Category | Count | Purpose |
|----------|-------|---------|
| Technique Notebooks | 30+ | RAG implementations |
| Evaluation Notebooks | 4 | Evaluation methods |
| Helper Functions | 1 | Utility functions |
| Images | 40+ | Documentation diagrams |

**Integration Target**: Extract patterns into `src/opencode/core/rag/techniques/`

**Integration Value**: VERY HIGH - Comprehensive technique library

---

### 5. balmasi-youtube-rag

**Category**: YouTube RAG (Medium Priority)

**Description**: YouTube RAG with indexing and serving components.

**Files**:
| File | Size | Purpose |
|------|------|---------|
| `src/indexing/assets.py` | 5,553 chars | Asset indexing |
| `src/indexing/embed.py` | 384 chars | Embedding |
| `src/indexing/resources.py` | 774 chars | Resource management |
| `src/indexing/utils.py` | 672 chars | Utilities |
| `src/serving/retrieval.py` | 3,325 chars | Retrieval logic |
| `src/serving/serve.py` | 1,420 chars | Serving |

**Integration Target**: Enhance `src/opencode/core/youtube/` modules

**Integration Value**: MEDIUM - YouTube-specific patterns

---

### 6. rag-youtube-assistant

**Category**: YouTube RAG (Medium Priority)

**Description**: YouTube assistant with RAG capabilities.

**Integration Value**: MEDIUM - Video search and timestamp handling

---

### 7. svpino-youtube-rag

**Category**: YouTube RAG (Medium Priority)

**Description**: Alternative YouTube RAG implementation.

**Integration Value**: MEDIUM - Alternative video processing approach

---

### 8. youtube-rag

**Category**: YouTube RAG (Medium Priority)

**Description**: General YouTube RAG implementation.

**Integration Value**: MEDIUM - Video content extraction

---

### 9. MultiModal-RAG-with-Videos

**Category**: YouTube RAG (Medium Priority)

**Description**: Multimodal video RAG with frame extraction.

**Integration Target**: Enhance `src/opencode/core/video/` modules

**Integration Value**: HIGH - Multimodal embeddings and frame extraction

---

### 10. LLM-Fine-tuning

**Category**: Fine-tuning (Medium Priority)

**Description**: LLM fine-tuning utilities and workflows.

**Integration Target**: Create `src/opencode/core/finetuning/` module

**Integration Value**: HIGH - Fine-tuning workflows and dataset preparation

---

### 11. unsloth

**Category**: Fine-tuning (Medium Priority)

**Description**: Efficient fine-tuning library with LoRA support.

**Files**:
| File | Size | Purpose |
|------|------|---------|
| `unsloth-cli.py` | 15,631 chars | CLI for fine-tuning |
| `pyproject.toml` | 78,002 chars | Project configuration |
| `README.md` | 31,722 chars | Documentation |

**Key Features**:
- Efficient fine-tuning
- LoRA/QLoRA support
- CLI interface
- Multiple model support

**Integration Target**: Create `src/opencode/core/finetuning/` module

**Integration Value**: VERY HIGH - Production-ready fine-tuning library

---

### 12. Roo-Code

**Category**: Code Assistants (Medium Priority)

**Description**: Code assistant with IDE integration patterns.

**Integration Target**: Enhance CLI commands and code generation

**Integration Value**: MEDIUM - Code generation patterns

---

### 13. get-shit-done

**Category**: Code Assistants (Medium Priority)

**Description**: Task automation workflow.

**Integration Value**: MEDIUM - Workflow automation patterns

---

### 14. get-shit-done-2

**Category**: Code Assistants (Medium Priority)

**Description**: Enhanced task automation v2.

**Integration Value**: MEDIUM - Enhanced automation patterns

---

### 15. superpowers

**Category**: Code Assistants (Medium Priority)

**Description**: Enhanced capabilities and power user tools.

**Integration Value**: MEDIUM - Advanced features

---

### 16. planning-with-files

**Category**: Planning Systems (Low Priority)

**Description**: File-based planning system.

**Integration Target**: Enhance planning capabilities

**Integration Value**: LOW - Planning persistence patterns

---

### 17. plano

**Category**: Planning Systems (Low Priority)

**Description**: Planning system with task decomposition.

**Integration Value**: LOW - Planning algorithms

---

### 18. ai-factory

**Category**: Infrastructure (Low Priority)

**Description**: AI/ML factory patterns for model management.

**Integration Target**: Enhance provider abstraction

**Integration Value**: MEDIUM - Model factory patterns

---

### 19. compound-engineering-plugin

**Category**: Infrastructure (Low Priority)

**Description**: Plugin architecture system.

**Integration Target**: Enhance plugin system

**Integration Value**: MEDIUM - Plugin extensibility

---

### 20. mistral-vibe

**Category**: Infrastructure (Low Priority)

**Description**: Mistral provider integration.

**Integration Target**: Add Mistral provider support

**Integration Value**: MEDIUM - Provider support

---

### 21. Locally-Hosted-LM-Research-Assistant

**Category**: Infrastructure (Low Priority)

**Description**: Research assistant with citation management.

**Integration Target**: Enhance research workflows

**Integration Value**: MEDIUM - Research workflows and citations

---

## Integration Priority Matrix

### Sprint 1: High-Value RAG Core
1. **OpenRAG** - Comprehensive RAG methods (VERY HIGH value)
2. **RAG_Techniques** - Technique library (VERY HIGH value)
3. **Local-RAG-with-Ollama** - Local embedding patterns (HIGH value)

### Sprint 2: Fine-tuning
1. **unsloth** - Production fine-tuning (VERY HIGH value)
2. **LLM-Fine-tuning** - Fine-tuning workflows (HIGH value)

### Sprint 3: YouTube/Multimodal
1. **MultiModal-RAG-with-Videos** - Multimodal support (HIGH value)
2. **balmasi-youtube-rag** - YouTube patterns (MEDIUM value)

### Sprint 4: Infrastructure
1. **ai-factory** - Model factory (MEDIUM value)
2. **compound-engineering-plugin** - Plugin system (MEDIUM value)

### Sprint 5: Low Priority
1. **RAG-Project** - Basic examples (LOW value)
2. **planning-with-files** - Planning (LOW value)
3. **plano** - Planning (LOW value)

---

## Dependency Analysis

### New Dependencies Required

From Local-RAG-with-Ollama:
- langchain-ollama>=0.3.0
- langchain-chroma>=0.2.0
- chromadb>=1.0.0

From OpenRAG:
- elasticsearch (optional)
- streamlit (optional, for UI)

From unsloth:
- unsloth library
- Additional GPU dependencies

### Existing Dependencies (Already in pyproject.toml)
- langchain
- langchain-core
- langchain-text-splitters
- numpy
- pydantic

---

## 22. overstory

**Category**: Multi-Agent Orchestration (High Priority)

**Description**: Multi-agent orchestration for AI coding agents.

**Location**: `merge_projects/overstory/`

**Language**: TypeScript (Bun runtime)

**Files**:
| File | Size | Purpose |
|------|------|---------|
| `src/commands/*.ts` | 50+ files | CLI commands |
| `src/agents/*.ts` | 10+ files | Agent definitions |
| `src/mail/*.ts` | 5 files | Inter-agent messaging |
| `src/worktree/*.ts` | 3 files | Git worktree management |
| `src/merge/*.ts` | 3 files | Branch merge logic |
| `src/watchdog/*.ts` | 4 files | Fleet health monitoring |
| `agents/*.md` | 8 files | Agent prompt templates |

**Key Features**:
- Multi-agent coordination hierarchy (Coordinator → Supervisor → Workers)
- SQLite-based mail system for inter-agent messaging
- Git worktree isolation for agent workspaces
- 4-tier conflict resolution for branch merging
- Watchdog daemon (Tier 0 mechanical, Tier 1 AI-assisted, Tier 2 monitor)
- Runtime adapters (Claude Code, Pi, Copilot, Codex)
- 30+ CLI commands for orchestration

**Dependencies**:
- Bun runtime
- tmux
- git
- SQLite

**Integration Target**: Create `src/opencode/core/multiagent/`

**Integration Value**: HIGH - Enables multi-agent self-improvement capabilities

---

## 23. beads

**Category**: Memory Management (High Priority)

**Description**: Distributed, git-backed graph issue tracker for AI agents.

**Location**: `merge_projects/beads/`

**Language**: Go

**Files**:
| File | Size | Purpose |
|------|------|---------|
| `cmd/bd/*.go` | 80+ files | CLI commands |
| `internal/beads/*.go` | 10+ files | Core logic |
| `internal/formula/*.go` | 8 files | Expression parsing |
| `internal/linear/*.go` | 6 files | Issue tracking |
| `internal/molecules/*.go` | 3 files | Molecule types |
| `docs/*.md` | 30+ files | Documentation |

**Key Features**:
- Dolt-backed version-controlled SQL database
- Task dependency graph with zero-conflict hash IDs
- Memory compaction (semantic "memory decay")
- Graph links (relates_to, duplicates, supersedes, replies_to)
- Hierarchical IDs (Epic → Task → Sub-task)
- Stealth mode for local-only usage
- Contributor vs Maintainer workflow

**Dependencies**:
- Go runtime
- Dolt (SQL database)
- git

**Integration Target**: Create `src/opencode/core/memory/`

**Integration Value**: VERY HIGH - Enables persistent structured memory for self-improvement

---

## Integration Priority Matrix

### Sprint 1: Memory Management (beads) ✅ COMPLETE
1. **beads** - Structured memory with task graph - ✅ INTEGRATED

### Sprint 2: Multi-Agent Orchestration (overstory) ✅ COMPLETE
1. **overstory** - Multi-agent coordination - ✅ INTEGRATED (HIGH value)

---

## Dependency Analysis

### New Dependencies Required

From beads:
- Dolt SQL database (optional - can use SQLite fallback)

From overstory:
- tmux (for worktree sessions)
- git (for branch management)
- SQLite (for messaging - already in use)

### Existing Dependencies (Already in pyproject.toml)
- sqlite3 (via aiosqlite)
- gitpython

---

## Risk Assessment

### High Risk
- **License compatibility**: Review all licenses before integration
- **Dependency conflicts**: Test in isolated environment
- **Code quality**: Apply linting before merge
- **Language porting (TypeScript/Go)**: High effort required for porting

### Medium Risk
- **Feature overlap**: Document and consolidate duplicates
- **Breaking changes**: Maintain backward compatibility
- **New dependencies**: Dolt, tmux may be required

### Low Risk
- **Documentation gaps**: Create docs during integration
- **Style inconsistencies**: Apply automated formatting

---

## Next Steps

1. ✅ Complete inventory (this document)
2. ✅ Create feature mapping document
3. ✅ Begin RAG integration (Phases 1-7) - COMPLETE
4. ✅ Begin beads integration (Sprint 1 - Memory Management) - COMPLETE
5. ✅ Begin overstory integration (Sprint 2 - Multi-Agent Orchestration) - COMPLETE
6. ✅ Add tests for integrated features
7. ✅ Update documentation

---

## Implementation Status

✅ **All major components have been implemented!**

### Completed Components

#### Phase 1-2: Workflow Engine (✅ Already Implemented)
- `workflow/__init__.py` - Module exports
- `workflow/node.py` - BaseNode, NodePort, NodeSchema, ExecutionContext
- `workflow/engine.py` - WorkflowEngine with execution, streaming, events
- `workflow/graph.py` - WorkflowGraph, WorkflowNode, WorkflowEdge
- `workflow/state.py` - WorkflowState, ExecutionStatus
- `workflow/registry.py` - NodeRegistry

#### Phase 2: Core Nodes (✅ Already Implemented)
- `workflow/nodes/data_source.py` - DataSourceNode
- `workflow/nodes/llm_process.py` - LlmProcessNode
- `workflow/nodes/timer.py` - TimerNode
- `workflow/nodes/http.py` - HttpNode
- `workflow/nodes/tool.py` - ToolNode
- `workflow/nodes/data_validation.py` - DataValidationNode
- `workflow/nodes/json_reformatter.py` - JsonReformatterNode
- `workflow/nodes/chart.py` - ChartNode

#### Phase 3: Router Integration (✅ Already Implemented)
- `router/__init__.py` - Module exports
- `router/engine.py` - RouterEngine, RoutingResult, SemanticCache
- `router/config.py` - RouterConfig, ModelConfig
- `router/profiler.py` - ModelProfiler
- `router/skills.py` - SkillClassifier
- `router/vram_monitor.py` - VRAMMonitor

#### Phase 4: Workflow Tools (✅ NEW)
- `workflow/tools/__init__.py` - Module exports
- `workflow/tools/registry.py` - ToolRegistry, BaseTool, ToolResult
- `workflow/tools/brave_search.py` - BraveSearchTool
- `workflow/tools/duckduckgo_search.py` - DuckDuckGoSearchTool
- `workflow/tools/weather.py` - WeatherTool
- `workflow/tools/csv_array.py` - CsvArrayTool

#### Phase 5: API Layer (✅ Already Implemented + NEW)
- `server/routes/workflow.py` - Workflow REST API + WebSocket
- `server/routes/router.py` - Router management API
- `server/graphql/__init__.py` - GraphQL module
- `server/graphql/schema.py` - GraphQL schema with Query, Mutation, Subscription

#### llm-checker Module (✅ Already Implemented)
- `llmchecker/hardware/` - Hardware detection with backends
- `llmchecker/scoring/` - Scoring engine
- `llmchecker/ollama/` - Ollama client
- `llmchecker/calibration/` - Calibration manager

#### Mode System (✅ NEW)
- `core/modes/__init__.py` - Module exports
- `core/modes/base.py` - Mode, ModeConfig, ModeToolAccess
- `core/modes/registry.py` - ModeRegistry
- `core/modes/manager.py` - ModeManager
- `core/modes/modes/code.py` - CodeMode
- `core/modes/modes/architect.py` - ArchitectMode
- `core/modes/modes/ask.py` - AskMode
- `core/modes/modes/debug.py` - DebugMode

#### Skills System (✅ NEW)
- `skills/__init__.py` - Module exports
- `skills/models.py` - Skill, SkillConfig, SkillResult, SkillExecutionContext
- `skills/discovery.py` - SkillDiscovery, skill decorator
- `skills/manager.py` - SkillManager

#### Context & Checkpoints (✅ NEW)
- `core/context/__init__.py` - Module exports
- `core/context/tracker.py` - ContextTracker, FileContext
- `core/context/truncation.py` - ContextTruncation, strategies
- `core/context/mentions.py` - MentionProcessor
- `core/context/checkpoints.py` - CheckpointManager, Checkpoint

#### Orchestration Layer (✅ NEW)
- `core/orchestration/__init__.py` - Module exports
- `core/orchestration/agent.py` - Agent, AgentDescription, AgentTask
- `core/orchestration/registry.py` - AgentRegistry
- `core/orchestration/router.py` - OrchestrationRouter, IntentClassifier
- `core/orchestration/coordinator.py` - Coordinator

#### TUI Enhancements (✅ NEW)
- `tui/widgets/completion.py` - CompletionWidget, CompletionManager
- `tui/widgets/approval.py` - ApprovalDialog, ApprovalManager

#### Memory Module (beads) (✅ COMPLETE)
- `core/memory/__init__.py` - Module exports
- `core/memory/models.py` - Task, Message, Relationship models
- `core/memory/ids.py` - Zero-conflict hash ID generation
- `core/memory/store.py` - SQLite storage backend
- `core/memory/graph.py` - Graph operations
- `core/memory/config.py` - Configuration

#### Multi-Agent Module (overstory) (✅ COMPLETE)
- `core/multiagent/__init__.py` - Module exports
- `core/multiagent/models.py` - Agent models
- `core/multiagent/messaging.py` - SQLite message bus
- `core/multiagent/worktree.py` - Git worktree management
- `core/multiagent/coordinator.py` - Agent coordination
- `core/multiagent/config.py` - Configuration

---

## Implementation Summary

| Component | Status | Files Created |
|-----------|--------|---------------|
| Workflow Engine | ✅ Complete | 8 files |
| Router Integration | ✅ Complete | 5 files |
| Workflow Tools | ✅ Complete | 5 files |
| GraphQL API | ✅ Complete | 2 files |
| Mode System | ✅ Complete | 7 files |
| Skills System | ✅ Complete | 4 files |
| Enhanced Tools | ✅ Complete | 4 files |
| Context & Checkpoints | ✅ Complete | 5 files |
| Orchestration Layer | ✅ Complete | 5 files |
| TUI Enhancements | ✅ Complete | 2 files |
| Memory Module (beads) | ✅ Complete | 6 files |
| Multi-Agent Module (overstory) | ✅ Complete | 6 files |

**Total: 55+ files implemented**

---

*Last updated: 2026-03-01*
