# Feature Mapping Document

> **Purpose**: Map merge_projects features to opencode_4py architecture

---

## Feature Mapping Matrix

### RAG Methods → Target Modules

| Source Project | Feature | Target Module | Integration Type |
|---------------|---------|---------------|------------------|
| OpenRAG | Naive RAG | `rag/methods/naive_rag.py` | New module |
| OpenRAG | Advanced RAG | `rag/methods/advanced_rag.py` | New module |
| OpenRAG | Agentic RAG | `rag/methods/agentic_rag.py` | New module |
| OpenRAG | Graph RAG | `rag/methods/graph_rag.py` | New module |
| OpenRAG | Self RAG | `rag/methods/self_rag.py` | New module |
| OpenRAG | Corrective RAG | `rag/methods/corrective_rag.py` | New module |
| OpenRAG | Reranker RAG | `rag/methods/reranker_rag.py` | New module |
| OpenRAG | Semantic Chunking | `rag/methods/semantic_chunking.py` | New module |
| OpenRAG | Contextual Retrieval | `rag/methods/contextual_retrieval.py` | New module |
| OpenRAG | Query Reformulation | Enhance `rag/query_rewriter.py` | Enhancement |
| OpenRAG | Evaluation Framework | Enhance `rag/evaluation.py` | Enhancement |
| RAG_Techniques | HyDe | `rag/methods/hyde.py` | New module |
| RAG_Techniques | Fusion Retrieval | `rag/methods/fusion_retrieval.py` | New module |
| RAG_Techniques | RAPTOR | `rag/methods/raptor.py` | New module |
| RAG_Techniques | Proposition Chunking | `rag/methods/proposition_chunking.py` | New module |
| RAG_Techniques | Hierarchical Indices | `rag/methods/hierarchical_indices.py` | New module |
| Local-RAG-with-Ollama | Ollama Embeddings | Enhance `rag/local_embeddings.py` | Enhancement |
| Local-RAG-with-Ollama | ChromaDB Integration | Enhance `rag/local_vector_store.py` | Enhancement |

### YouTube/Media → Target Modules

| Source Project | Feature | Target Module | Integration Type |
|---------------|---------|---------------|------------------|
| balmasi-youtube-rag | Asset Indexing | Enhance `youtube/channel.py` | Enhancement |
| MultiModal-RAG-with-Videos | Frame Extraction | Enhance `video/frames.py` | Enhancement |
| MultiModal-RAG-with-Videos | Multimodal Embeddings | `rag/multimodal_embeddings.py` | New module |

### Fine-tuning → Target Modules

| Source Project | Feature | Target Module | Integration Type |
|---------------|---------|---------------|------------------|
| unsloth | LoRA Fine-tuning | `finetuning/lora.py` | New module |
| unsloth | Dataset Preparation | `finetuning/dataset.py` | New module |
| unsloth | CLI Interface | `cli/commands/finetune.py` | New command |
| LLM-Fine-tuning | Training Workflows | `finetuning/workflows.py` | New module |

### Infrastructure → Target Modules

| Source Project | Feature | Target Module | Integration Type |
|---------------|---------|---------------|------------------|
| ai-factory | Model Factory | `core/model_factory.py` | New module |
| compound-engineering-plugin | Plugin System | `core/plugins.py` | New module |
| mistral-vibe | Mistral Provider | `providers/mistral.py` | New module |

---

## Architecture Integration Plan

### New Directory Structure

```
src/opencode/src/opencode/core/
├── rag/
│   ├── methods/                    # NEW: RAG method implementations
│   │   ├── __init__.py
│   │   ├── base.py                 # Base class for RAG methods
│   │   ├── naive_rag.py            # Simple RAG implementation
│   │   ├── advanced_rag.py         # Advanced RAG with reranking
│   │   ├── agentic_rag.py          # Agent-based RAG
│   │   ├── graph_rag.py            # Graph-based RAG
│   │   ├── self_rag.py             # Self-reflective RAG
│   │   ├── corrective_rag.py       # Corrective RAG (CRAG)
│   │   ├── reranker_rag.py         # Reranking RAG
│   │   ├── semantic_chunking.py    # Semantic chunking
│   │   ├── contextual_retrieval.py # Contextual retrieval
│   │   ├── hyde.py                 # Hypothetical Document Embedding
│   │   ├── fusion_retrieval.py     # Fusion retrieval
│   │   ├── raptor.py               # RAPTOR hierarchical
│   │   ├── proposition_chunking.py # Proposition-based chunking
│   │   └── hierarchical_indices.py # Hierarchical indexing
│   ├── multimodal_embeddings.py    # NEW: Multimodal embeddings
│   └── ... (existing modules)
├── finetuning/                     # NEW: Fine-tuning module
│   ├── __init__.py
│   ├── lora.py                     # LoRA fine-tuning
│   ├── dataset.py                  # Dataset preparation
│   ├── workflows.py                # Training workflows
│   └── config.py                   # Fine-tuning configuration
├── plugins/                        # NEW: Plugin system
│   ├── __init__.py
│   ├── base.py                     # Plugin base class
│   └── manager.py                  # Plugin manager
└── ... (existing modules)
```

---

## Integration Priority by Feature

### Phase 1: Core RAG Methods (Week 1)
1. Create `rag/methods/base.py` - Base class for all RAG methods
2. Create `rag/methods/naive_rag.py` - Simple RAG (from OpenRAG)
3. Create `rag/methods/advanced_rag.py` - Advanced RAG with reranking
4. Create `rag/methods/agentic_rag.py` - Agent-based RAG

### Phase 2: Advanced RAG Methods (Week 2)
1. Create `rag/methods/self_rag.py` - Self-reflective RAG
2. Create `rag/methods/corrective_rag.py` - CRAG implementation
3. Create `rag/methods/graph_rag.py` - Graph-based RAG
4. Create `rag/methods/hyde.py` - HyDe implementation

### Phase 3: Retrieval Enhancements (Week 3)
1. Create `rag/methods/fusion_retrieval.py`
2. Create `rag/methods/reranker_rag.py`
3. Create `rag/methods/semantic_chunking.py`
4. Enhance `rag/query_rewriter.py`

### Phase 4: Fine-tuning Module (Week 4)
1. Create `finetuning/` module structure
2. Implement LoRA fine-tuning from unsloth
3. Create dataset preparation utilities
4. Add CLI commands for fine-tuning

### Phase 5: Infrastructure (Week 5)
1. Create plugin system
2. Add multimodal embeddings
3. Enhance evaluation framework

---

## Code Quality Standards

All integrated code must follow:

1. **Type Hints**: All functions must have complete type annotations
2. **Docstrings**: Google-style docstrings for all public functions/classes
3. **Testing**: Minimum 80% test coverage for new code
4. **Linting**: Pass ruff linting with project settings
5. **Documentation**: Update relevant .md files

---

## Dependency Management

### New Dependencies to Add

```toml
[project.optional-dependencies]
rag-advanced = [
    "langchain-ollama>=0.3.0",
    "langchain-chroma>=0.2.0",
    "chromadb>=1.0.0",
]

finetuning = [
    "unsloth",
    "peft>=0.10.0",
    "bitsandbytes>=0.43.0",
]

multimodal = [
    "transformers>=4.40.0",
    "pillow>=10.0.0",
]
```

---

## Success Criteria

1. All RAG methods have consistent interface via base class
2. All new modules have >80% test coverage
3. Documentation updated for all new features
4. No breaking changes to existing API
5. All integrated code passes linting

---

*Last updated: 2026-02-24*
