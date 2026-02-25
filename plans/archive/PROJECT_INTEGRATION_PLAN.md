# Project Integration Plan: agentic-signal + SmarterRouter → opencode_4py

This document outlines the comprehensive plan for integrating features from multiple projects into the opencode_4py codebase.

> **Related Documents:**
> - [README.md](../../README.md) - Project overview and features
> - [MISSION.md](../../MISSION.md) - Mission statement and core principles

---

## Executive Summary

### Core Integration Projects

| Source Project | Language | Integration Type | Complexity | Status |
|---------------|----------|------------------|------------|--------|
| **agentic-signal** | TypeScript/Deno | Full rewrite to Python | High | Planned |
| **SmarterRouter** | Python | Direct integration | Medium | Planned |
| **llm-checker** | JavaScript/Node.js | Full rewrite to Python | Medium | ✅ Completed |
| **Roo-Code** | TypeScript (VS Code Ext) | Feature extraction + rewrite | Very High | Planned |
| **plano** | Rust + TypeScript | Architecture patterns + rewrite | High | Planned |
| **mistral-vibe** | Python 3.12+ | Direct integration + merge | Medium | Planned |

### All Merge Projects (from merge_projects/)

| # | Project | Description | Integration Area | Status |
|---|---------|-------------|------------------|--------|
| 1 | **ai-factory** | AI factory patterns | Core orchestration | Planned |
| 2 | **balmasi-youtube-rag** | YouTube channel indexing | YouTube/RAG | Planned |
| 3 | **compound-engineering-plugin** | Plugin architecture | Core extensibility | Planned |
| 4 | **get-shit-done** | Task execution patterns | Task execution | Planned |
| 5 | **get-shit-done-2** | Enhanced task execution | Task execution | Planned |
| 6 | **LLM-Fine-tuning** | Fine-tuning integration | LLM training | Planned |
| 7 | **Local-RAG-with-Ollama** | Local RAG patterns | RAG system | Planned |
| 8 | **Locally-Hosted-LM-Research-Assistant** | Research assistant patterns | Research tools | Planned |
| 9 | **mistral-vibe** | Mistral integration, skills system | Provider/Skills | Planned |
| 10 | **MultiModal-RAG-with-Videos** | Multimodal RAG | Video RAG | Planned |
| 11 | **OpenRAG** | Open RAG patterns | RAG system | Planned |
| 12 | **planning-with-files** | File-based planning | Planning tools | Planned |
| 13 | **plano** | Planning patterns, agent orchestration | Orchestration | Planned |
| 14 | **RAG-Project** | RAG project patterns | RAG system | Planned |
| 15 | **RAG_Techniques** | RAG technique collection | RAG system | Planned |
| 16 | **rag-youtube-assistant** | Evaluation + Query rewrite | YouTube/RAG | Planned |
| 17 | **Roo-Code** | VS Code extension patterns | Modes/Tools/Context | Planned |
| 18 | **superpowers** | AI superpowers | Tool enhancements | Planned |
| 19 | **svpino-youtube-rag** | Educational patterns | YouTube/RAG | Planned |
| 20 | **unsloth** | Fine-tuning integration | LLM training | Planned |
| 21 | **youtube-rag** | Timestamped links | YouTube/RAG | Planned |

### Merge Project Folder Naming Convention

**IMPORTANT:** When a merge project has been 100% integrated into opencode_4py:
- Append `--delete` to the folder name in `merge_projects/`
- Example: `merge_projects/Roo-Code/` → `merge_projects/Roo-Code--delete/`
- This indicates the project is fully merged and the folder can be safely removed

**Status Definitions:**
- **Planned** - Not yet started
- **In Progress** - Currently being integrated
- **✅ Completed** - Fully integrated, folder marked with `--delete`
- **Partial** - Some features integrated, more remaining

---

## Part 1: Understanding the Basecode

### 1.1 agentic-signal Architecture Analysis

**Project Type:** Visual AI Workflow Automation Platform

**Technology Stack:**
- **Frontend:** React + TypeScript + Vite + React Flow
- **Backend:** Deno + GraphQL (graphql-yoga)
- **Database:** In-memory/JSON-based workflow storage
- **AI Integration:** Ollama (local LLM)
- **Desktop:** Tauri (Rust-based native wrapper)

**Core Components:**

```
agentic-signal/
├── client/                    # React Frontend
│   └── src/
│       ├── components/
│       │   ├── nodes/         # Workflow node types
│       │   │   ├── BaseNode/          # Base node component
│       │   │   ├── DataSourceNode/    # Data input nodes
│       │   │   ├── LlmProcessNode/    # AI processing nodes
│       │   │   ├── TimerNode/         # Scheduled triggers
│       │   │   ├── HttpNode/          # HTTP request nodes
│       │   │   ├── ToolNode/          # Tool execution nodes
│       │   │   ├── ChartNode/         # Visualization
│       │   │   └── ...                # Other node types
│       │   └── ...
│       ├── services/
│       │   ├── ollamaService.ts       # Ollama API client
│       │   └── graphQLSocketManager.ts # WebSocket management
│       └── hooks/
│           └── useWorkflow.ts         # Workflow state management
│
├── server/                    # Deno Backend
│   ├── main.ts                # GraphQL server entry
│   ├── graphql/
│   │   └── schema.ts          # Schema composition
│   ├── nodes/                 # Node resolvers
│   │   ├── TimerNode/
│   │   └── HttpNode/
│   ├── tools/                 # Tool implementations
│   │   ├── BraveSearchTool/
│   │   ├── DuckDuckGoSearchTool/
│   │   ├── GcalendarFetchEventsTool/
│   │   ├── GdriveFetchFilesTool/
│   │   ├── GmailFetchEmailsTool/
│   │   └── ...
│   └── ws/
│       └── webSocketManager.ts # WebSocket handling
│
└── shared/
    └── constants.ts           # Shared constants
```

**Key Features to Migrate:**

1. **Visual Workflow Builder**
   - Node-based visual programming
   - Drag-and-drop interface
   - Real-time execution visualization
   - Data flow connections

2. **Node Types:**
   - `DataSourceNode` - File/JSON/text input
   - `LlmProcessNode` - AI processing with Ollama
   - `TimerNode` - Scheduled/cron triggers
   - `HttpNode` - HTTP/GraphQL requests
   - `ToolNode` - External tool execution
   - `ChartNode` - Data visualization
   - `DataValidationNode` - Schema validation
   - `JsonReformatterNode` - JSON transformation
   - `GetDataNode` - Data retrieval
   - `DataFlowSpyNode` - Debug/monitoring

3. **Tool Integrations:**
   - Brave Search API
   - DuckDuckGo Search
   - Google Calendar API
   - Google Drive API
   - Gmail API
   - Weather data fetching
   - CSV/Array utilities
   - DateTime utilities

4. **AI Capabilities:**
   - Ollama integration for local LLMs
   - Structured output with JSON schema
   - Tool calling (function calling)
   - Conversation memory
   - Streaming responses

5. **Real-time Features:**
   - WebSocket subscriptions
   - GraphQL subscriptions
   - Live workflow execution updates

---

### 1.2 SmarterRouter Architecture Analysis

**Project Type:** Intelligent LLM Router/Proxy

**Technology Stack:**
- **Language:** Python 3.12+
- **Framework:** FastAPI
- **Database:** SQLite + SQLAlchemy
- **Monitoring:** Prometheus metrics

**Core Components:**

```
SmarterRouter/
├── main.py                    # FastAPI application entry
├── router/
│   ├── router.py              # Core routing engine
│   ├── profiler.py            # Model performance profiling
│   ├── config.py              # Configuration management
│   ├── database.py            # Database connection
│   ├── models.py              # SQLAlchemy models
│   ├── schemas.py             # Pydantic schemas
│   ├── metrics.py             # Prometheus metrics
│   ├── judge.py               # LLM-as-judge evaluation
│   ├── skills.py              # Skill-based routing
│   ├── vram_monitor.py        # GPU memory monitoring
│   ├── vram_manager.py        # VRAM allocation
│   ├── benchmark_db.py        # Benchmark data
│   ├── benchmark_sync.py      # Sync external benchmarks
│   │
│   ├── backends/              # LLM backend adapters
│   │   ├── base.py            # Abstract backend
│   │   ├── ollama.py          # Ollama backend
│   │   ├── llama_cpp.py       # llama.cpp backend
│   │   └── openai.py          # OpenAI backend
│   │
│   ├── gpu_backends/          # GPU monitoring backends
│   │   ├── nvidia.py          # NVIDIA (nvidia-smi)
│   │   ├── amdgpu.py          # AMD (rocm-smi)
│   │   ├── intel.py           # Intel (xpu-smi)
│   │   └── apple.py           # Apple Silicon
│   │
│   └── providers/             # Benchmark data providers
│       ├── artificial_analysis.py
│       ├── huggingface.py
│       └── lmsys.py
│
└── data/                      # Database storage
```

**Key Features to Integrate:**

1. **Intelligent Model Routing:**
   - Automatic model selection based on prompt analysis
   - Category detection (coding, reasoning, creativity, general)
   - Complexity assessment (simple, medium, hard)
   - Quality vs. speed preference tuning

2. **Model Profiling:**
   - Performance benchmarking
   - Speed/quality scoring
   - Capability detection (vision, tool calling)
   - VRAM requirement estimation

3. **Multi-Backend Support:**
   - Ollama (primary)
   - llama.cpp
   - OpenAI-compatible APIs

4. **VRAM Management:**
   - Multi-GPU support (NVIDIA, AMD, Intel, Apple)
   - Automatic model unloading
   - Memory monitoring

5. **Caching:**
   - Semantic cache for routing decisions
   - Response caching
   - LRU eviction

6. **Metrics & Monitoring:**
   - Prometheus metrics
   - Request tracking
   - Model selection statistics

---

### 1.3 opencode_4py Current Architecture

**Project Type:** AI Coding Agent

**Technology Stack:**
- **Language:** Python 3.12+
- **CLI:** Typer + Rich
- **TUI:** Textual
- **Server:** FastAPI + Uvicorn
- **Database:** SQLite + SQLAlchemy (async)

**Current Structure:**

```
src/opencode/
├── cli/                       # CLI commands
│   └── commands/              # Individual commands
├── core/                      # Core functionality
│   ├── config.py              # Configuration
│   └── session.py             # Session management
├── db/                        # Database layer
│   ├── connection.py
│   └── models.py
├── i18n/                      # Internationalization
├── mcp/                       # MCP protocol
│   ├── client.py
│   ├── server.py
│   └── oauth.py
├── provider/                  # LLM providers
│   ├── base.py
│   ├── anthropic.py
│   ├── openai.py
│   ├── ollama.py
│   └── ...                    # 15+ providers
├── server/                    # HTTP server
│   └── routes/
├── session/                   # Session handling
├── tool/                      # Tool implementations
│   ├── bash.py
│   ├── file_tools.py
│   ├── lsp.py
│   └── ...
├── tui/                       # Terminal UI
└── util/                      # Utilities
```

---

## Part 2: Refactoring Plan - agentic-signal → Python

### 2.1 Migration Strategy

**Approach:** Incremental migration with feature parity

**Phase 1: Core Infrastructure (Week 1-2)**

1. **Workflow Engine Foundation**
   ```python
   # Proposed structure
   src/opencode/workflow/
   ├── __init__.py
   ├── engine.py           # Workflow execution engine
   ├── graph.py            # DAG representation
   ├── executor.py         # Node execution
   └── state.py            # Workflow state management
   ```

2. **Base Node System**
   ```python
   # src/opencode/workflow/node.py
   from abc import ABC, abstractmethod
   from typing import Any, Dict, List
   from pydantic import BaseModel
   
   class NodePort(BaseModel):
       name: str
       data_type: str
       required: bool = True
   
   class BaseNode(ABC):
       def __init__(self, node_id: str, config: Dict[str, Any]):
           self.node_id = node_id
           self.config = config
           self.inputs: Dict[str, Any] = {}
           self.outputs: Dict[str, Any] = {}
       
       @abstractmethod
       async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
           """Execute the node logic"""
           pass
       
       @classmethod
       @abstractmethod
       def get_schema(cls) -> Dict[str, Any]:
           """Return JSON schema for node configuration"""
           pass
   ```

**Phase 2: Node Implementations (Week 3-4)**

1. **DataSourceNode**
   ```python
   # src/opencode/workflow/nodes/data_source.py
   class DataSourceNode(BaseNode):
       """Handles file, JSON, and text data input"""
       async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
           source_type = self.config.get("sourceType")
           if source_type == "file":
               return await self._handle_file_input()
           elif source_type == "json":
               return {"data": json.loads(self.config["jsonData"])}
           # ...
   ```

2. **LlmProcessNode**
   ```python
   # src/opencode/workflow/nodes/llm_process.py
   class LlmProcessNode(BaseNode):
       """AI processing using existing provider system"""
       async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
           provider = self._get_provider()
           response = await provider.chat(
               messages=self._build_messages(inputs),
               model=self.config["model"],
               tools=self._get_tools(),
           )
           return {"output": response.content}
   ```

3. **TimerNode**
   ```python
   # src/opencode/workflow/nodes/timer.py
   from apscheduler.schedulers.asyncio import AsyncIOScheduler
   
   class TimerNode(BaseNode):
       """Scheduled workflow triggers"""
       def __init__(self, *args, **kwargs):
           super().__init__(*args, **kwargs)
           self.scheduler = AsyncIOScheduler()
       
       async def start(self, callback):
           self.scheduler.add_job(
               callback,
               trigger=self._get_trigger(),
               id=self.node_id,
           )
           self.scheduler.start()
   ```

4. **HttpNode**
   ```python
   # src/opencode/workflow/nodes/http.py
   import httpx
   
   class HttpNode(BaseNode):
       """HTTP/GraphQL request handling"""
       async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
           async with httpx.AsyncClient() as client:
               response = await client.request(
                   method=self.config["method"],
                   url=self.config["url"],
                   headers=self.config.get("headers", {}),
                   json=self._build_body(inputs),
               )
               return {"response": response.json()}
   ```

**Phase 3: Tool Integration (Week 5-6)**

1. **Tool Registry Pattern**
   ```python
   # src/opencode/workflow/tools/registry.py
   from typing import Dict, Type
   
   class ToolRegistry:
       _tools: Dict[str, Type['BaseTool']] = {}
       
       @classmethod
       def register(cls, name: str):
           def decorator(tool_class):
               cls._tools[name] = tool_class
               return tool_class
           return decorator
       
       @classmethod
       def get_tool(cls, name: str) -> 'BaseTool':
           return cls._tools[name]()
   ```

2. **Tool Implementations**
   ```python
   # src/opencode/workflow/tools/search.py
   @ToolRegistry.register("brave_search")
   class BraveSearchTool(BaseTool):
       async def execute(self, query: str) -> Dict[str, Any]:
           async with httpx.AsyncClient() as client:
               response = await client.get(
                   "https://api.search.brave.com/res/v1/web/search",
                   headers={"X-Subscription-Token": self.api_key},
                   params={"q": query},
               )
               return response.json()
   ```

**Phase 4: Visual Editor Backend (Week 7-8)**

1. **GraphQL API**
   ```python
   # src/opencode/server/routes/workflow.py
   from strawberry.fastapi import GraphQLRouter
   import strawberry
   
   @strawberry.type
   class WorkflowQuery:
       @strawberry.field
       async def workflow(self, id: str) -> WorkflowType:
           return await workflow_store.get(id)
   
   @strawberry.type
   class WorkflowMutation:
       @strawberry.mutation
       async def create_workflow(self, input: WorkflowInput) -> WorkflowType:
           return await workflow_store.create(input)
   
   @strawberry.type
   class WorkflowSubscription:
       @strawberry.subscription
       async def workflow_execution(self, id: str) -> AsyncGenerator[ExecutionEvent, None]:
           async for event in execution_stream(id):
               yield event
   ```

2. **WebSocket Manager**
   ```python
   # src/opencode/server/websocket.py
   from fastapi import WebSocket
   from typing import Dict, Set
   
   class WorkflowWebSocketManager:
       def __init__(self):
           self.connections: Dict[str, Set[WebSocket]] = {}
       
       async def broadcast(self, workflow_id: str, event: dict):
           for connection in self.connections.get(workflow_id, set()):
               await connection.send_json(event)
   ```

---

### 2.2 TypeScript → Python Mapping

| TypeScript Concept | Python Equivalent |
|-------------------|-------------------|
| `interface` | `pydantic.BaseModel` |
| `type` | `typing.TypeAlias` or `pydantic.BaseModel` |
| `enum` | `enum.Enum` |
| `Promise<T>` | `asyncio.Future[T]` or `Awaitable[T]` |
| `async/await` | `async/await` (same) |
| `Map<K,V>` | `dict[K, V]` |
| `Set<T>` | `set[T]` |
| `Record<K,V>` | `dict[K, V]` |
| `Partial<T>` | `Optional` fields in Pydantic |
| `Omit<T, K>` | Custom model without fields |
| `Record<string, any>` | `Dict[str, Any]` |
| Deno.serve | FastAPI + Uvicorn |
| graphql-yoga | strawberry-graphql |
| React Flow | Custom frontend (keep as-is) |

---

### 2.3 Dependencies to Add

```toml
# pyproject.toml additions
dependencies = [
    # Workflow engine
    "apscheduler>=3.10.0",           # Timer scheduling
    "strawberry-graphql>=0.220.0",   # GraphQL API
    
    # Additional tools
    "aiohttp>=3.9.0",                # HTTP client (alternative to httpx)
    
    # Data validation
    "jsonschema>=4.0.0",             # JSON schema validation
    
    # Visualization (optional)
    "plotly>=5.0.0",                 # Chart generation
]
```

---

## Part 3: Integration Plan - SmarterRouter

### 3.1 Integration Strategy

**Approach:** Modular integration with optional dependency

Since SmarterRouter is already Python, integration is more straightforward:

1. **Copy core modules** to opencode structure
2. **Adapt interfaces** to match opencode patterns
3. **Add as optional feature** behind configuration flag

### 3.2 Module Mapping

```
SmarterRouter/router/           →    src/opencode/router/
├── router.py                        ├── engine.py
├── profiler.py                      ├── profiler.py
├── config.py                        →    merge with core/config.py
├── database.py                      →    use existing db/
├── models.py                        →    add to db/models.py
├── schemas.py                       →    add to provider/schemas.py
├── metrics.py                       ├── metrics.py
├── judge.py                         ├── judge.py
├── skills.py                        ├── skills.py
├── vram_monitor.py                  ├── vram_monitor.py
├── vram_manager.py                  ├── vram_manager.py
├── backends/                        →    extend provider/
│   ├── base.py                      →    provider/base.py
│   ├── ollama.py                    →    merge with provider/ollama.py
│   ├── llama_cpp.py                 →    provider/llama_cpp.py (new)
│   └── openai.py                    →    merge with provider/openai.py
├── gpu_backends/                    ├── gpu/
│   ├── nvidia.py                    │   ├── nvidia.py
│   ├── amdgpu.py                    │   ├── amdgpu.py
│   ├── intel.py                     │   ├── intel.py
│   └── apple.py                     │   └── apple.py
└── providers/                       ├── benchmark/
    ├── artificial_analysis.py       │   ├── artificial_analysis.py
    ├── huggingface.py               │   ├── huggingface.py
    └── lmsys.py                     │   └── lmsys.py
```

### 3.3 Integration Points

1. **Provider Enhancement**
   ```python
   # src/opencode/provider/base.py
   class LLMProvider(ABC):
       # Add routing support
       @abstractmethod
       async def get_model_info(self, model: str) -> ModelInfo:
           """Get model capabilities and requirements"""
           pass
       
       @abstractmethod
       async def unload_model(self, model: str) -> None:
           """Unload model from memory"""
           pass
   ```

2. **Router Integration**
   ```python
   # src/opencode/router/engine.py
   from opencode.provider import get_provider
   
   class RouterEngine:
       def __init__(self, config: RouterConfig):
           self.provider = get_provider(config.provider)
           self.profiler = ModelProfiler(self.provider)
           self.cache = SemanticCache()
       
       async def route(self, prompt: str) -> RoutingResult:
           # Analyze prompt
           category = await self._classify_category(prompt)
           complexity = await self._assess_complexity(prompt)
           
           # Select best model
           model = await self._select_model(category, complexity)
           return RoutingResult(model=model, confidence=0.9)
   ```

3. **Configuration Extension**
   ```python
   # src/opencode/core/config.py
   class RouterSettings(BaseModel):
       enabled: bool = False
       provider: str = "ollama"
       quality_preference: float = 0.5  # 0=speed, 1=quality
       pinned_model: str | None = None
       vram_monitoring: bool = True
       cache_enabled: bool = True
   ```

### 3.4 API Endpoints

```python
# src/opencode/server/routes/router.py
from fastapi import APIRouter

router = APIRouter(prefix="/router", tags=["router"])

@router.get("/models")
async def list_available_models():
    """List all available models with capabilities"""
    pass

@router.get("/models/{model}/profile")
async def get_model_profile(model: str):
    """Get detailed model profile"""
    pass

@router.post("/profile")
async def profile_all_models():
    """Run profiling on all models"""
    pass

@router.get("/vram")
async def get_vram_status():
    """Get current VRAM usage"""
    pass

@router.get("/metrics")
async def get_router_metrics():
    """Get routing metrics"""
    pass
```

---

## Part 4: Feature Coverage Matrix

### 4.1 agentic-signal Features

| Feature | Priority | Complexity | Dependencies |
|---------|----------|------------|--------------|
| Workflow Engine | High | High | None |
| DataSourceNode | High | Low | Workflow Engine |
| LlmProcessNode | High | Medium | Provider system |
| TimerNode | Medium | Medium | APScheduler |
| HttpNode | Medium | Low | httpx |
| ToolNode | High | Medium | Tool system |
| ChartNode | Low | Medium | Plotly |
| DataValidationNode | Medium | Low | jsonschema |
| JsonReformatterNode | Low | Low | None |
| Brave Search Tool | Medium | Low | API key |
| DuckDuckGo Tool | Medium | Low | None |
| Google Calendar Tool | Low | High | OAuth |
| Google Drive Tool | Low | High | OAuth |
| Gmail Tool | Low | High | OAuth |
| GraphQL API | High | Medium | strawberry |
| WebSocket Subscriptions | High | Medium | websockets |

### 4.2 SmarterRouter Features

| Feature | Priority | Complexity | Dependencies |
|---------|----------|------------|--------------|
| Model Routing | High | Medium | Provider system |
| Model Profiling | High | High | Database |
| VRAM Monitoring | Medium | Medium | GPU drivers |
| Semantic Cache | Medium | Medium | Embeddings |
| Multi-GPU Support | Low | High | GPU drivers |
| Benchmark Sync | Low | Low | External APIs |
| Prometheus Metrics | Low | Low | prometheus-client |

---

## Part 5: Implementation Timeline

### Phase 1: Foundation (Weeks 1-2)
- [ ] Create workflow module structure
- [ ] Implement BaseNode and NodePort
- [ ] Create WorkflowEngine skeleton
- [ ] Add workflow database models

### Phase 2: Core Nodes (Weeks 3-4)
- [ ] Implement DataSourceNode
- [ ] Implement LlmProcessNode
- [ ] Implement TimerNode
- [ ] Implement HttpNode
- [ ] Add node registry

### Phase 3: Router Integration (Weeks 5-6)
- [ ] Copy SmarterRouter modules
- [ ] Adapt to opencode patterns
- [ ] Integrate with provider system
- [ ] Add VRAM monitoring

### Phase 4: Tools (Weeks 7-8)
- [ ] Implement tool registry
- [ ] Port search tools
- [ ] Port utility tools
- [ ] Add Google API tools (optional)

### Phase 5: API Layer (Weeks 9-10)
- [ ] Add GraphQL endpoints
- [ ] Implement WebSocket subscriptions
- [ ] Create workflow REST API
- [ ] Add router management endpoints

### Phase 6: Testing & Documentation (Weeks 11-12)
- [ ] Unit tests for all components
- [ ] Integration tests
- [ ] API documentation
- [ ] User guide

---

## Part 6: Risk Assessment

### High Risk
1. **Workflow Engine Complexity** - Visual workflow engines are inherently complex
   - Mitigation: Start with simple linear workflows, add branching later

2. **VRAM Monitoring Cross-Platform** - GPU drivers vary significantly
   - Mitigation: Use existing SmarterRouter code, test on multiple platforms

### Medium Risk
1. **OAuth Integration** - Google APIs require complex OAuth flows
   - Mitigation: Use existing MCP OAuth implementation as reference

2. **Performance** - Workflow execution overhead
   - Mitigation: Profile early, optimize hot paths

### Low Risk
1. **API Compatibility** - GraphQL schema design
   - Mitigation: Follow existing patterns from agentic-signal

---

## Part 7: Success Criteria

1. **Feature Parity**
   - All agentic-signal node types functional
   - All SmarterRouter routing features working

2. **Performance**
   - Workflow execution latency < 100ms overhead
   - Routing decision latency < 50ms

3. **Integration**
   - Seamless use with existing opencode features
   - No breaking changes to existing API

4. **Documentation**
   - Complete API reference
   - Usage examples
   - Migration guide for agentic-signal users

---

## Appendix A: File Structure After Integration

```
src/opencode/
├── cli/
├── core/
├── db/
├── i18n/
├── mcp/
├── provider/
│   ├── base.py              # Enhanced with routing support
│   ├── ollama.py            # Enhanced with VRAM management
│   ├── llama_cpp.py         # NEW: llama.cpp backend
│   └── ...
├── router/                   # NEW: From SmarterRouter
│   ├── __init__.py
│   ├── engine.py
│   ├── profiler.py
│   ├── judge.py
│   ├── skills.py
│   ├── cache.py
│   ├── vram_monitor.py
│   ├── vram_manager.py
│   ├── metrics.py
│   ├── gpu/
│   │   ├── nvidia.py
│   │   ├── amdgpu.py
│   │   ├── intel.py
│   │   └── apple.py
│   └── benchmark/
│       ├── artificial_analysis.py
│       ├── huggingface.py
│       └── lmsys.py
├── server/
│   └── routes/
│       ├── workflow.py       # NEW: Workflow API
│       └── router.py         # NEW: Router management
├── session/
├── tool/
├── tui/
├── util/
├── workflow/                 # NEW: From agentic-signal
│   ├── __init__.py
│   ├── engine.py
│   ├── graph.py
│   ├── executor.py
│   ├── state.py
│   ├── node.py               # BaseNode
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── data_source.py
│   │   ├── llm_process.py
│   │   ├── timer.py
│   │   ├── http.py
│   │   ├── tool.py
│   │   ├── chart.py
│   │   ├── data_validation.py
│   │   └── json_reformatter.py
│   └── tools/
│       ├── __init__.py
│       ├── registry.py
│       ├── brave_search.py
│       ├── duckduckgo_search.py
│       ├── weather.py
│       ├── csv_array.py
│       └── google/           # Optional Google API tools
│           ├── calendar.py
│           ├── drive.py
│           └── gmail.py
└── web/
```

---

## Appendix B: Configuration Schema

```toml
# opencode.toml

[workflow]
enabled = true
auto_save = true
max_concurrent_executions = 10

[workflow.nodes.data_source]
max_file_size_mb = 100

[workflow.nodes.llm_process]
default_timeout_seconds = 300

[router]
enabled = true
provider = "ollama"
quality_preference = 0.5
pinned_model = null

[router.cache]
enabled = true
max_size = 100
ttl_seconds = 3600

[router.vram]
monitoring = true
auto_unload = true
threshold_percent = 90

[router.profiling]
enabled = true
timeout_seconds = 90
run_on_startup = false
```

---

## Part 4: Integration Plan - llm-checker

### 4.1 Overview

**Project Type:** Intelligent LLM Model Selector & Hardware Analyzer

**Technology Stack:**
- **Language:** JavaScript/Node.js (requires full rewrite to Python)
- **Dependencies:** systeminformation, chalk, commander, inquirer, yaml, zod

**Key Features:**
- Hardware detection (CPU, GPU, memory) with multi-platform support
- Multi-dimensional model scoring (Quality, Speed, Fit, Context)
- Ollama integration with model management
- Calibration system for benchmarking
- Policy-based routing

### 4.2 Module Mapping

```
llm-checker/src/                 →    src/opencode/llmchecker/
├── hardware/                         ├── hardware/
│   ├── detector.js                   │   ├── __init__.py
│   ├── unified-detector.js           │   ├── detector.py
│   ├── profiles.js                   │   ├── profiles.py
│   ├── specs.js                      │   ├── specs.py
│   ├── pc-optimizer.js               │   ├── optimizer.py
│   └── backends/                     │   └── backends/
│       ├── apple-silicon.js          │       ├── __init__.py
│       ├── cpu-detector.js           │       ├── apple.py
│       ├── cuda-detector.js          │       ├── cpu.py
│       ├── intel-detector.js         │       ├── cuda.py
│       └── rocm-detector.js          │       ├── intel.py
├── models/                           │       └── rocm.py
│   ├── scoring-engine.js             ├── scoring/
│   ├── deterministic-selector.js     │   ├── __init__.py
│   ├── intelligent-selector.js       │   ├── engine.py
│   ├── requirements.js               │   ├── selector.py
│   ├── moe-assumptions.js            │   ├── requirements.py
│   └── speculative-decoding-estimator.js│   ├── moe.py
├── ollama/                           │   └── speculative.py
│   ├── client.js                     ├── ollama/
│   ├── manager.js                    │   ├── __init__.py
│   ├── capacity-planner.js           │   ├── client.py
│   └── native-scraper.js             │   ├── manager.py
├── calibration/                      │   ├── capacity.py
│   ├── calibration-manager.js        │   └── scraper.py
│   ├── policy-routing.js             ├── calibration/
│   └── schemas.js                    │   ├── __init__.py
├── policy/                           │   ├── manager.py
│   ├── policy-engine.js              │   ├── routing.py
│   ├── policy-manager.js             │   └── schemas.py
│   └── audit-reporter.js             ├── policy/
├── provenance/                       │   ├── __init__.py
│   └── model-provenance.js           │   ├── engine.py
├── data/                             │   ├── manager.py
│   ├── model-database.js             │   └── audit.py
│   └── sync-manager.js               ├── data/
└── utils/                            │   ├── __init__.py
    ├── config.js                     │   ├── database.py
    ├── formatter.js                  │   └── sync.py
    ├── logger.js                     ├── utils/
    └── token-speed-estimator.js      │   ├── __init__.py
                                      │   ├── config.py
                                      │   ├── formatter.py
                                      │   ├── logger.py
                                      │   └── token_speed.py
```

### 4.3 Integration with Existing Router

The llm-checker features complement and enhance the existing SmarterRouter integration:

| Feature | SmarterRouter | llm-checker | Integration |
|---------|---------------|-------------|-------------|
| Hardware Detection | GPU backends | Full system detection | Merge into unified hardware module |
| Model Selection | Skill-based routing | 4D scoring | Combine approaches |
| VRAM Management | VRAM monitor | Capacity planner | Unified memory management |
| Profiling | Benchmark sync | Calibration | Unified benchmarking |
| Policy | Basic | Full policy engine | Use llm-checker policy system |

### 4.4 New CLI Commands

```bash
# Hardware detection
opencode hw-detect                    # Detect all hardware
opencode hw-detect --json             # JSON output

# Model recommendations
opencode llm-recommend                # Get model recommendations
opencode llm-recommend --category coding
opencode llm-recommend --calibrated

# Ollama management
opencode ollama list                  # List installed models
opencode ollama pull <model>          # Pull a model
opencode ollama run <model> <prompt>  # Run a prompt
opencode ollama benchmark <model>     # Benchmark a model

# Calibration
opencode calibrate --suite ./prompts.jsonl
opencode calibrate --policy-out ./policy.yaml

# Policy
opencode policy init                  # Create policy template
opencode policy validate ./policy.yaml
opencode audit export --format json
```

### 4.5 Dependencies to Add

```toml
# pyproject.toml additions for llm-checker
dependencies = [
    # Hardware detection
    "psutil>=5.9.0",                  # System information
    "py-cpuinfo>=9.0.0",              # CPU information
    "GPUtil>=1.4.0",                  # NVIDIA GPU detection
    "pyamdgpuinfo>=2.1.0",            # AMD GPU detection (optional)
    
    # Calibration
    "pyyaml>=6.0",                    # YAML parsing
]

# Optional dependencies
[project.optional-dependencies]
llmchecker = [
    "pyamdgpuinfo>=2.1.0",
    "pyintelgpuinfo>=0.1.0",          # Intel GPU (if available)
]
```

### 4.6 Implementation Phases

**Phase 1: Hardware Detection (Week 1)**
- Create hardware detection module
- Implement CPU detection
- Implement GPU detection (NVIDIA, AMD, Intel, Apple)
- Add memory detection

**Phase 2: Scoring Engine (Week 2)**
- Port scoring engine
- Implement 4D scoring (Q, S, F, C)
- Add model database
- Create selector logic

**Phase 3: Ollama Integration (Week 3)**
- Port Ollama client
- Add model management
- Implement capacity planner
- Create model scraper

**Phase 4: Calibration & Policy (Week 4)**
- Port calibration manager
- Implement policy engine
- Add audit reporter
- Create CLI commands

---

## Part 5: Integration Plan - Roo-Code, plano, mistral-vibe

### 5.1 Executive Summary

| Source Project | Language | Integration Type | Complexity | Priority |
|---------------|----------|------------------|------------|----------|
| **Roo-Code** | TypeScript (VS Code Extension) | Feature extraction + Python rewrite | Very High | High |
| **plano** | Rust + TypeScript | Architecture patterns + Python rewrite | High | Medium |
| **mistral-vibe** | Python 3.12+ | Direct integration + Feature merge | Medium | High |

---

### 5.2 Roo-Code Architecture Analysis

**Project Type:** VS Code AI Coding Assistant Extension

**Technology Stack:**
- **Language:** TypeScript
- **Framework:** VS Code Extension API
- **UI:** Webview (React-based)
- **Build:** esbuild, turbo (monorepo)
- **Testing:** vitest

**Core Components:**

```
Roo-Code/src/
├── extension.ts              # Extension entry point
├── core/
│   ├── task/                 # Task execution engine
│   │   └── Task.ts           # Main task orchestration (178k chars!)
│   ├── prompts/              # System prompts and tool definitions
│   │   ├── system.ts         # System prompt generation
│   │   ├── sections/         # Prompt sections (capabilities, rules, etc.)
│   │   └── tools/            # Tool definitions for LLM
│   ├── config/               # Configuration management
│   │   ├── ContextProxy.ts   # Context management
│   │   ├── CustomModesManager.ts  # Custom mode handling
│   │   └── ProviderSettingsManager.ts
│   ├── context-management/   # Context window management
│   ├── checkpoints/          # State checkpointing
│   ├── diff/                 # Diff strategies
│   └── tools/                # Tool implementations
├── services/                 # External services
├── api/                      # API integrations
└── utils/                    # Utilities
```

**Key Features to Extract:**

1. **Mode System**
   - Code Mode: Everyday coding, edits, file operations
   - Architect Mode: Planning, specs, migrations
   - Ask Mode: Fast answers, explanations
   - Debug Mode: Issue tracing, logging, root cause analysis
   - Custom Modes: User-defined specialized modes

2. **Tool System**
   - `read_file` - File reading with range support
   - `write_file` - File writing
   - `edit_file` - Edit with context
   - `search_replace` - Multi-search-replace
   - `apply_diff` / `apply_patch` - Patch application
   - `execute_command` - Shell command execution
   - `list_files` - Directory listing
   - `search_files` - Regex search
   - `codebase_search` - Semantic code search
   - `ask_followup_question` - Interactive questions
   - `attempt_completion` - Task completion
   - `update_todo_list` - Todo management
   - `new_task` - Subagent spawning
   - `switch_mode` - Mode switching
   - `mcp_server` - MCP server management
   - `access_mcp_resource` - MCP resource access

3. **Context Management**
   - File context tracking
   - Context truncation strategies
   - Mention processing (@file, @url)
   - Image mention resolution

4. **Checkpoint System**
   - State serialization
   - Restore points
   - Diff generation

5. **Custom Modes**
   - YAML-based mode definitions
   - Mode-specific prompts
   - Tool filtering per mode
   - Custom instructions

---

### 5.3 plano Architecture Analysis

**Project Type:** AI-Native Proxy Server for Agentic Apps

**Technology Stack:**
- **Core:** Rust (Envoy-based)
- **CLI:** TypeScript/Node.js
- **Config:** YAML-based
- **Deployment:** Docker

**Core Components:**

```
plano/
├── crates/                   # Rust crates
│   ├── llm_gateway/          # LLM request handling
│   ├── prompt_gateway/       # Prompt processing
│   ├── hermesllm/            # LLM integration
│   ├── common/               # Shared utilities
│   └── brightstaff/          # Agent orchestration
├── cli/                      # TypeScript CLI
├── apps/                     # Application deployments
├── config/                   # Configuration files
├── demos/                    # Example implementations
└── packages/                 # NPM packages
```

**Key Features to Extract:**

1. **Agent Orchestration**
   - Multi-agent routing
   - Intent classification
   - Agent descriptions for routing

2. **LLM Routing**
   - Model name routing
   - Alias (semantic name) routing
   - Preference-based routing

3. **Filter Chains**
   - Moderation hooks
   - Memory hooks
   - Jailbreak protection

4. **Agentic Signals**
   - Zero-code capture
   - OTEL traces/metrics
   - Signal extraction

5. **Configuration Pattern**
   ```yaml
   agents:
     - id: agent_name
       url: http://localhost:port
       description: |
         Natural language description for routing
   
   model_providers:
     - model: provider/model-name
       access_key: $ENV_VAR
       default: true
   
   listeners:
     - type: agent
       name: assistant
       port: 8001
       router: model_name
       agents:
         - id: agent_name
           description: Agent description
   ```

---

### 5.4 mistral-vibe Architecture Analysis

**Project Type:** CLI Coding Assistant (Similar to opencode_4py!)

**Technology Stack:**
- **Language:** Python 3.12+
- **CLI:** typer, rich
- **TUI:** textual
- **Package:** uv, flit

**Core Components:**

```
mistral-vibe/vibe/
├── cli/                      # CLI implementation
│   ├── cli.py                # Main CLI
│   ├── commands.py           # Commands
│   ├── textual_ui/           # Textual TUI
│   │   ├── app.py            # Main app (57k chars!)
│   │   └── widgets/          # UI widgets
│   └── autocompletion/       # Path/command completion
├── core/                     # Core functionality
│   ├── agent_loop.py         # Agent execution loop (39k chars)
│   ├── config.py             # Configuration
│   ├── system_prompt.py      # System prompts
│   ├── types.py              # Type definitions
│   ├── tools/                # Tool implementations
│   │   ├── base.py           # Base tool
│   │   ├── manager.py        # Tool manager
│   │   ├── mcp.py            # MCP integration
│   │   └── builtins/         # Built-in tools
│   ├── llm/                  # LLM backends
│   │   └── backend/          # Provider implementations
│   │       ├── anthropic.py
│   │       ├── mistral.py
│   │       ├── generic.py
│   │       └── vertex.py
│   ├── skills/               # Skills system
│   ├── session/              # Session management
│   └── telemetry/            # Telemetry
└── acp/                      # ACP protocol
    └── acp_agent_loop.py     # ACP agent implementation
```

**Key Features to Extract:**

1. **Skills System**
   - Skill discovery from `.vibe/skills/`
   - Skill parsing and execution
   - Custom slash commands via skills

2. **Agent Loop**
   - Message processing
   - Tool execution
   - Streaming responses

3. **LLM Backends**
   - Mistral backend
   - Anthropic backend
   - Generic OpenAI-compatible
   - Vertex AI

4. **TUI Components**
   - Chat input with completion
   - Message rendering
   - Tool widgets
   - Approval dialogs

5. **Session Management**
   - Session persistence
   - Session migration
   - Session logging

6. **Auto-completion**
   - Path completion
   - Slash command completion
   - Fuzzy matching

---

### 5.5 Integration Strategy

#### 5.5.1 Roo-Code → opencode_4py Migration

**Approach:** Feature extraction with Python rewrite

**Priority 1: Mode System**
```python
# src/opencode/core/modes/
├── __init__.py
├── base.py              # Mode base class
├── manager.py           # Mode manager
├── registry.py          # Mode registry
└── modes/
    ├── __init__.py
    ├── code.py          # Code mode
    ├── architect.py     # Architect mode
    ├── ask.py           # Ask mode
    ├── debug.py         # Debug mode
    └── custom.py        # Custom mode support
```

**Priority 2: Enhanced Tool System**
```python
# Enhance existing src/opencode/tool/
├── base.py              # Enhanced base tool (from Roo-Code pattern)
├── manager.py           # Tool manager with mode filtering
├── registry.py          # Tool registry
└── builtins/
    ├── ask_followup.py  # NEW: Interactive questions
    ├── attempt_completion.py  # NEW: Task completion
    ├── new_task.py      # NEW: Subagent spawning
    └── switch_mode.py   # NEW: Mode switching
```

**Priority 3: Context Management**
```python
# src/opencode/core/context/
├── __init__.py
├── tracker.py           # File context tracking
├── truncation.py        # Context truncation strategies
├── mentions.py          # @mention processing
└── checkpoints.py       # State checkpointing
```

#### 5.5.2 plano → opencode_4py Migration

**Approach:** Architecture patterns + Python implementation

**Priority 1: Agent Orchestration**
```python
# src/opencode/orchestration/
├── __init__.py
├── router.py            # Agent routing
├── intent.py            # Intent classification
├── registry.py          # Agent registry
└── config.py            # Orchestration config
```

**Priority 2: Filter Chains**
```python
# src/opencode/filters/
├── __init__.py
├── chain.py             # Filter chain execution
├── moderation.py        # Moderation filter
├── memory.py            # Memory filter
└── jailbreak.py         # Jailbreak protection
```

**Priority 3: Agentic Signals**
```python
# src/opencode/signals/
├── __init__.py
├── capture.py           # Signal capture
├── traces.py            # OTEL traces
└── metrics.py           # Signal metrics
```

#### 5.5.3 mistral-vibe → opencode_4py Integration

**Approach:** Direct integration with feature merge (both are Python!)

**Priority 1: Skills System**
```python
# src/opencode/skills/
├── __init__.py
├── manager.py           # Skill manager (from mistral-vibe)
├── parser.py            # Skill parsing
├── discovery.py         # Skill discovery
└── models.py            # Skill models
```

**Priority 2: Enhanced LLM Backends**
```python
# Enhance existing src/opencode/provider/
├── mistral.py           # Enhanced from mistral-vibe
├── vertex.py            # NEW: Vertex AI support
└── generic.py           # Generic OpenAI-compatible
```

**Priority 3: TUI Enhancements**
```python
# Enhance existing src/opencode/tui/
├── widgets/
│   ├── chat_input.py    # Enhanced with completion
│   ├── completion.py    # Completion popup
│   └── approval.py      # Approval dialogs
└── completion/
    ├── path.py          # Path completion
    ├── slash.py         # Slash command completion
    └── fuzzy.py         # Fuzzy matching
```

---

### 5.6 Module Mapping Summary

```
Roo-Code/src/core/             →    src/opencode/core/
├── task/Task.ts                    ├── task/executor.py
├── prompts/                        ├── prompts/
│   ├── system.ts                   │   ├── system.py
│   ├── sections/                   │   ├── sections/
│   └── tools/                      │   └── tools/
├── config/CustomModesManager.ts    ├── modes/manager.py
├── context-management/             ├── context/
├── checkpoints/                    ├── checkpoints/
└── tools/                          └── tool/ (enhance existing)

plano/crates/                  →    src/opencode/
├── llm_gateway/                    ├── llm_gateway/
├── prompt_gateway/                 ├── prompt_gateway/
├── brightstaff/                    ├── orchestration/
└── (config patterns)               └── config/ (enhance)

mistral-vibe/vibe/             →    src/opencode/
├── core/skills/                    ├── skills/
├── core/llm/backend/               ├── provider/ (enhance)
├── cli/textual_ui/                 ├── tui/ (enhance)
├── cli/autocompletion/             ├── completion/
└── core/session/                   └── session/ (enhance)
```

---

### 5.7 Feature Coverage Matrix

#### 5.7.1 Roo-Code Features

| Feature | Priority | Complexity | Dependencies | Status |
|---------|----------|------------|--------------|--------|
| Mode System | High | High | None | Planned |
| Custom Modes | High | Medium | Mode System | Planned |
| Tool Filtering | High | Low | Mode System | Planned |
| Context Tracking | High | Medium | None | Planned |
| Checkpoints | Medium | Medium | Context Tracking | Planned |
| Mention Processing | Medium | Low | None | Planned |
| Diff Strategies | Medium | Medium | None | Planned |
| Interactive Questions | High | Low | None | Planned |
| Subagent Spawning | Medium | High | Task System | Planned |

#### 5.7.2 plano Features

| Feature | Priority | Complexity | Dependencies | Status |
|---------|----------|------------|--------------|--------|
| Agent Routing | Medium | High | None | Planned |
| Intent Classification | Medium | High | LLM | Planned |
| Filter Chains | Medium | Medium | None | Planned |
| Moderation | Medium | Medium | Filter Chains | Planned |
| Agentic Signals | Low | Medium | OTEL | Planned |
| YAML Config Pattern | High | Low | None | Planned |

#### 5.7.3 mistral-vibe Features

| Feature | Priority | Complexity | Dependencies | Status |
|---------|----------|------------|--------------|--------|
| Skills System | High | Medium | None | Planned |
| Skill Discovery | High | Low | Skills System | Planned |
| Mistral Backend | Medium | Low | Provider system | Planned |
| Vertex AI Backend | Low | Medium | GCP credentials | Planned |
| Path Completion | High | Low | None | Planned |
| Slash Commands | High | Low | Skills System | Planned |
| Session Migration | Medium | Low | Session system | Planned |
| Approval Dialogs | Medium | Low | TUI | Planned |

---

### 5.8 Implementation Timeline

#### Phase 1: Mode System (Weeks 1-2)
- [ ] Create mode base class and registry
- [ ] Implement Code, Architect, Ask, Debug modes
- [ ] Add custom mode support with YAML definitions
- [ ] Integrate mode-specific tool filtering
- [ ] Add mode switching CLI command

#### Phase 2: Skills System (Weeks 3-4)
- [ ] Port skill manager from mistral-vibe
- [ ] Implement skill discovery
- [ ] Add skill parsing
- [ ] Create built-in skills
- [ ] Integrate with slash commands

#### Phase 3: Context & Checkpoints (Weeks 5-6)
- [ ] Implement file context tracking
- [ ] Add context truncation strategies
- [ ] Create checkpoint system
- [ ] Add mention processing
- [ ] Implement restore functionality

#### Phase 4: Enhanced Tools (Weeks 7-8)
- [ ] Add ask_followup_question tool
- [ ] Add attempt_completion tool
- [ ] Add new_task (subagent) tool
- [ ] Enhance existing tools with mode awareness
- [ ] Add tool result validation

#### Phase 5: Orchestration (Weeks 9-10)
- [ ] Implement agent registry
- [ ] Add intent classification
- [ ] Create filter chain system
- [ ] Add moderation filters
- [ ] Implement agent routing

#### Phase 6: TUI Enhancements (Weeks 11-12)
- [ ] Add path auto-completion
- [ ] Add slash command completion
- [ ] Implement approval dialogs
- [ ] Add completion popup
- [ ] Enhance message rendering

#### Phase 7: Integration & Testing (Weeks 13-14)
- [ ] Integration testing
- [ ] Documentation
- [ ] CLI command updates
- [ ] Configuration schema updates
- [ ] Migration guide

---

### 5.9 Dependencies to Add

```toml
# pyproject.toml additions
dependencies = [
    # Mode system
    "pyyaml>=6.0",                    # YAML mode definitions
    
    # Skills system
    "watchfiles>=0.20.0",             # File watching for skill discovery
    
    # Completion
    "fuzzywuzzy>=0.18.0",             # Fuzzy matching
    "python-Levenshtein>=0.21.0",     # Fast string matching
    
    # Orchestration
    "opentelemetry-api>=1.20.0",      # OTEL traces
    "opentelemetry-sdk>=1.20.0",      # OTEL SDK
    
    # Vertex AI (optional)
    "google-cloud-aiplatform>=1.30.0",  # Vertex AI
]

[project.optional-dependencies]
orchestration = [
    "opentelemetry-exporter-otlp>=1.20.0",
]
vertex = [
    "google-cloud-aiplatform>=1.30.0",
]
```

---

### 5.10 Configuration Schema Extension

```toml
# opencode.toml extensions

[modes]
default = "code"
custom_dir = "~/.opencode/modes"

[modes.code]
description = "Everyday coding, edits, and file operations"
tools = ["all"]
system_prompt_suffix = ""

[modes.architect]
description = "Plan systems, specs, and migrations"
tools = ["read_file", "write_file", "search_files", "ask_followup_question"]
system_prompt_suffix = "Focus on planning and documentation."

[modes.ask]
description = "Fast answers and explanations"
tools = ["read_file", "search_files", "ask_followup_question"]
system_prompt_suffix = "Be concise and direct."

[modes.debug]
description = "Trace issues and isolate root causes"
tools = ["read_file", "execute_command", "search_files", "ask_followup_question"]
system_prompt_suffix = "Focus on systematic debugging."

[skills]
enabled = true
discovery_dir = ".vibe/skills"
auto_reload = true

[orchestration]
enabled = false
default_router = "intent"

[orchestration.agents]
# Define custom agents

[checkpoints]
enabled = true
auto_save = true
max_checkpoints = 10

[completion]
enabled = true
fuzzy_match = true
path_completion = true
slash_commands = true
```

---

### 5.11 Risk Assessment

#### High Risk
1. **Mode System Complexity** - Modes affect all aspects of the system
   - Mitigation: Start with simple mode switching, add complexity incrementally

2. **Subagent Spawning** - Task isolation and state management
   - Mitigation: Use existing session system, add isolation layer

#### Medium Risk
1. **Skills System Integration** - Discovery and parsing edge cases
   - Mitigation: Port proven code from mistral-vibe

2. **Orchestration Overhead** - Additional latency for routing
   - Mitigation: Make orchestration optional, cache routing decisions

#### Low Risk
1. **TUI Enhancements** - Textual is already integrated
   - Mitigation: Incremental additions to existing TUI

2. **Configuration Schema** - Backward compatible additions
   - Mitigation: Use sensible defaults, validate on load

---

### 5.12 Success Criteria

1. **Mode System**
   - All 4 default modes functional
   - Custom mode YAML loading working
   - Mode-specific tool filtering operational
   - Mode switching via CLI and tool

2. **Skills System**
   - Skill discovery from `.vibe/skills/`
   - Skill execution via slash commands
   - Custom skill creation documented

3. **Context & Checkpoints**
   - File context tracking accurate
   - Checkpoint save/restore working
   - Mention processing functional

4. **Orchestration**
   - Agent routing operational
   - Filter chains executable
   - Configuration-driven setup

5. **Integration**
   - No breaking changes to existing API
   - All existing features continue working
   - Documentation complete

---

*Document Version: 1.2*
*Created: 2026-02-21*
*Last Updated: 2026-02-21*
