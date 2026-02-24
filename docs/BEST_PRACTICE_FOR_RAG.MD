## Best Practices for RAG: Reduce External Sources, Improve Accuracy & Safety

### Core Strategy: Local-First RAG

| Goal | Implementation |
|------|----------------|
| **No external calls** | Use local embedding model (`nomic-embed-text` via Ollama) |
| **Local vector store** | Chroma, FAISS, or Qdrant on local machine |
| **Curated sources** | Only index verified, approved content |
| **No web fallback** | Disable external search in RAG pipeline |

### Configuration

```toml
[rag]
embedding_model = "nomic-embed-text"
embedding_provider = "ollama"
vector_store = "chroma"
allow_web_search = false
allow_external_apis = false
content_filter = true
```

### Accuracy Techniques

1. **Query rewriting** - Improve retrieval quality
2. **Hybrid search** - Combine keyword + semantic
3. **Re-ranking** - Cross-encoder for precision
4. **Confidence filtering** - Only use high-score results
5. **Citations required** - Track source usage

### Safety Measures

- Content filtering for sensitive patterns
- Source validation (only allowed directories)
- Output sanitization (redact secrets)
- Audit logging of all queries

### File Structure

```
RAG/
├── agent_code/
│   └── RAG/
│       ├── code-RAG/         # Local vector index
│       └── sources/          # Curated, verified content
│           ├── patterns/     # Approved patterns
│           └── standards/    # Coding standards
```

### Benefits

- **Zero external API calls** - Complete privacy
- **Verified sources only** - Improved accuracy
- **Offline capable** - Works without internet
- **Auditable** - Know exactly what sources were used