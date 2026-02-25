# Best Practices for RAG: Reduce External Sources, Improve Accuracy & Safety

> **Navigation:** [BUG_DETECTION_PROCESS.md](BUG_DETECTION_PROCESS.md) - Bug detection process | [RAG_SHARING.md](RAG_SHARING.md) - RAG sharing guide

---

## Core Strategy: Local-First RAG

| Goal | Implementation |
|------|----------------|
| **No external calls** | Use local embedding model (`nomic-embed-text` via Ollama) |
| **Local vector store** | Chroma, FAISS, or Qdrant on local machine |
| **Curated sources** | Only index verified, approved content |
| **No web fallback** | Disable external search in RAG pipeline |

---

## Configuration

```toml
[rag]
embedding_model = "nomic-embed-text"
embedding_provider = "ollama"
vector_store = "chroma"
allow_web_search = false
allow_external_apis = false
content_filter = true
```

---

## Accuracy Techniques

1. **Query rewriting** - Improve retrieval quality
2. **Hybrid search** - Combine keyword + semantic
3. **Re-ranking** - Cross-encoder for precision
4. **Confidence filtering** - Only use high-score results
5. **Citations required** - Track source usage

---

## Safety Measures

- Content filtering for sensitive patterns
- Source validation (only allowed directories)
- Output sanitization (redact secrets)
- Audit logging of all queries

---

## RAG Directory Structure

```
RAG/
## Overview

The RAG directory contains agent-specific and purpose-specific RAG indexes:

| Directory | Purpose | Auto-Populated |
|-----------|---------|----------------|
| `agent_code/` | Code patterns, best practices | No |
| `agent_troubleshooting/` | Error patterns, solutions | No |
| `bug_detected/` | Detected bugs and failures | Yes |
| `plan_merge/` | Merge integration knowledge | No |
| `plan_testing/` | Testing strategies | No |
| `troubleshooting/` | Error documentation, patterns | No |
```

---

## Bug Detection RAG

The `bug_detected/` RAG is automatically populated when errors are detected:

### Detection Triggers

| Trigger | Description |
|---------|-------------|
| `test_failure` | pytest test fails |
| `lint_error` | ruff/mypy error |
| `runtime_exception` | Unhandled exception |
| `type_error` | Type mismatch |
| `import_error` | Module not found |
| `prompt_quality_issue` | Prompt produces poor outputs |

### Prompt Quality Criteria

A prompt has a quality issue when it:
- Produces incorrect outputs
- Fails format requirements
- Is ambiguous
- Lacks context
- Is verbose
- Is unclear

> See [BUG_DETECTION_PROCESS.md](BUG_DETECTION_PROCESS.md) for full documentation.

---

## Document Types

### Error Documents (ERR-XXX)

Located in `RAG/troubleshooting/errors/`:
- Known error patterns with solutions
- Prevention strategies
- Related errors

### Bug Documents (BUG-XXX)

Located in `RAG/bug_detected/RAG/errors/`:
- Specific instances of detected issues
- Includes prompt quality issues
- Linked to affected components

---

## Benefits

- **Zero external API calls** - Complete privacy
- **Verified sources only** - Improved accuracy
- **Offline capable** - Works without internet
- **Auditable** - Know exactly what sources were used
- **Self-improving** - Bug detection feeds back into RAG

---

## Related Documentation

- [BUG_DETECTION_PROCESS.md](BUG_DETECTION_PROCESS.md) - Bug detection and RAG documentation process
- [RAG_SHARING.md](RAG_SHARING.md) - Share and sync RAG knowledge bases
- [RAG/README.md](../RAG/README.md) - RAG system overview
- [RAG/troubleshooting/README.md](../RAG/troubleshooting/README.md) - Troubleshooting guide

---

*Last updated: 2026-02-25*