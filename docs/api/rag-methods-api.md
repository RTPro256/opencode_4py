# RAG Methods API Reference

> **Module**: `opencode.core.rag.methods`

This module provides various RAG (Retrieval-Augmented Generation) method implementations integrated from OpenRAG and RAG_Techniques.

---

## Overview

The RAG methods module provides a unified interface for different retrieval-augmented generation strategies. Each method implements the `BaseRAGMethod` abstract class and provides unique retrieval and generation capabilities.

---

## Quick Start

```python
from opencode.core.rag.methods import create_rag_method, RAGMethodConfig

# Create a RAG method
config = RAGMethodConfig(top_k=5)
rag = create_rag_method("hyde", config)

# Index documents
await rag.index_documents(["Document 1 content", "Document 2 content"])

# Query
result = await rag.query("What is the main topic?")
print(result.answer)
```

---

## Core Classes

### BaseRAGMethod

Abstract base class for all RAG methods.

```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

class BaseRAGMethod(ABC):
    """Abstract base class for RAG methods."""
    
    @abstractmethod
    async def query(
        self, 
        question: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> "RAGResult":
        """Execute a query against the indexed documents."""
        pass
    
    @abstractmethod
    async def index_documents(
        self,
        documents: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> int:
        """Index documents for retrieval."""
        pass
```

### RAGMethodConfig

Configuration for RAG methods using Pydantic.

```python
from pydantic import BaseModel, Field
from opencode.core.rag.methods import RAGMethodConfig

config = RAGMethodConfig(
    top_k=10,                          # Number of documents to retrieve
    similarity_threshold=0.7,          # Minimum similarity score
    retrieval_strategy="hybrid",       # semantic, keyword, hybrid, graph
    chunk_size=512,                    # Document chunk size
    chunk_overlap=50,                  # Overlap between chunks
)
```

#### Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `top_k` | int | 5 | Number of documents to retrieve |
| `similarity_threshold` | float | 0.0 | Minimum similarity score (0.0-1.0) |
| `retrieval_strategy` | RetrievalStrategy | SEMANTIC | Strategy for document retrieval |
| `chunk_size` | int | 512 | Size of document chunks |
| `chunk_overlap` | int | 50 | Overlap between chunks |
| `chunking_strategy` | ChunkingStrategy | RECURSIVE | Strategy for chunking documents |
| `enable_reranking` | bool | False | Enable cross-encoder reranking |
| `rerank_top_k` | int | 3 | Documents to return after reranking |

### RAGResult

Result from a RAG query.

```python
from opencode.core.rag.methods import RAGResult, RetrievedDocument

result = RAGResult(
    answer="The main topic is machine learning.",
    sources=[
        RetrievedDocument(
            content="Document content...",
            metadata={"source": "doc1.pdf"},
            score=0.95,
        )
    ],
    confidence=0.85,
    metadata={"query_time_ms": 150}
)
```

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `answer` | str | Generated answer to the query |
| `sources` | List[RetrievedDocument] | Source documents used |
| `confidence` | float | Confidence score (0.0-1.0) |
| `metadata` | Dict[str, Any] | Additional metadata |

### RetrievedDocument

A retrieved document with metadata.

```python
from opencode.core.rag.methods import RetrievedDocument

doc = RetrievedDocument(
    content="Document text content...",
    metadata={"source": "file.pdf", "page": 1},
    score=0.92,
    chunk_id="chunk_001"
)
```

---

## Available Methods

### NaiveRAG

Simple retrieval and generation without advanced features.

```python
from opencode.core.rag.methods import create_rag_method

rag = create_rag_method("naive", config)
```

**Best for**: Simple use cases, baseline comparisons.

### HyDeRAG (Hypothetical Document Embedding)

Generates hypothetical documents to improve retrieval.

```python
rag = create_rag_method("hyde", config)
```

**Best for**: Queries that differ from document language, ambiguous queries.

### SelfRAG

Self-reflective RAG with quality checks on retrieved documents.

```python
rag = create_rag_method("self", config)
```

**Best for**: High-accuracy requirements, factual queries.

### CorrectiveRAG (CRAG)

Corrects errors in retrieval and generation.

```python
rag = create_rag_method("corrective", config)
```

**Best for**: Error-prone domains, medical/legal applications.

### GraphRAG

Graph-based retrieval for entity relationships.

```python
rag = create_rag_method("graph", config)
```

**Best for**: Knowledge graphs, entity-centric queries.

### FusionRAG

Multi-query fusion retrieval for comprehensive results.

```python
rag = create_rag_method("fusion", config)
```

**Best for**: Complex queries, multi-faceted questions.

### RerankerRAG

Cross-encoder reranking for improved relevance.

```python
rag = create_rag_method("reranker", config)
```

**Best for**: High-precision retrieval, relevance-critical applications.

### AdvancedRAG

Query expansion and hybrid retrieval.

```python
rag = create_rag_method("advanced", config)
```

**Best for**: General-purpose advanced retrieval.

### AgenticRAG

Agent-based RAG with tool use capabilities.

```python
rag = create_rag_method("agentic", config)
```

**Best for**: Complex workflows, multi-step reasoning.

---

## Factory Functions

### create_rag_method()

Factory function to create a RAG method instance.

```python
def create_rag_method(
    method_name: str,
    config: RAGMethodConfig,
) -> BaseRAGMethod:
    """
    Create a RAG method instance.
    
    Args:
        method_name: Name of the RAG method
        config: Configuration for the method
        
    Returns:
        Configured RAG method instance
        
    Raises:
        ValueError: If method_name is not recognized
    """
```

### get_available_methods()

Get list of available RAG method names.

```python
from opencode.core.rag.methods import get_available_methods

methods = get_available_methods()
# ['naive', 'advanced', 'agentic', 'self', 'corrective', 
#  'graph', 'hyde', 'fusion', 'reranker', ...]
```

---

## Enums

### RetrievalStrategy

```python
from opencode.core.rag.methods.base import RetrievalStrategy

class RetrievalStrategy(str, Enum):
    SEMANTIC = "semantic"   # Vector similarity search
    KEYWORD = "keyword"     # BM25 keyword search
    HYBRID = "hybrid"       # Combined semantic + keyword
    GRAPH = "graph"         # Graph-based retrieval
```

### ChunkingStrategy

```python
from opencode.core.rag.methods.base import ChunkingStrategy

class ChunkingStrategy(str, Enum):
    FIXED = "fixed"               # Fixed-size chunks
    RECURSIVE = "recursive"       # Recursive character splitting
    SEMANTIC = "semantic"         # Semantic-aware chunking
    PROPOSITION = "proposition"   # Proposition-based chunking
    HIERARCHICAL = "hierarchical" # Hierarchical summarization
```

---

## Examples

### Basic Usage

```python
import asyncio
from opencode.core.rag.methods import create_rag_method, RAGMethodConfig

async def main():
    # Configure
    config = RAGMethodConfig(
        top_k=5,
        retrieval_strategy="semantic"
    )
    
    # Create method
    rag = create_rag_method("naive", config)
    
    # Index documents
    documents = [
        "Python is a programming language.",
        "Machine learning uses algorithms to learn from data.",
        "RAG combines retrieval with generation."
    ]
    await rag.index_documents(documents)
    
    # Query
    result = await rag.query("What is Python?")
    print(result.answer)
    print(f"Confidence: {result.confidence}")
    print(f"Sources: {len(result.sources)}")

asyncio.run(main())
```

### Comparing Methods

```python
from opencode.core.rag.methods import create_rag_method, RAGMethodConfig

config = RAGMethodConfig(top_k=5)
methods = ["naive", "hyde", "self", "fusion"]

for method_name in methods:
    rag = create_rag_method(method_name, config)
    result = await rag.query("What is machine learning?")
    print(f"{method_name}: {result.answer[:100]}...")
```

---

## Error Handling

```python
from opencode.core.rag.methods import create_rag_method, RAGMethodConfig

try:
    rag = create_rag_method("invalid_method", config)
except ValueError as e:
    print(f"Unknown method: {e}")
```

---

## See Also

- [Fine-tuning API](finetuning-api.md) - Fine-tuning module reference
- [USER_ACCEPTANCE_TESTING.md](../../plans/USER_ACCEPTANCE_TESTING.md) - UAT test scenarios
- [TESTING_PLAN.md](../../plans/TESTING_PLAN.md) - Testing strategy

---

*Last updated: 2026-02-24*
