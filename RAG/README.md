# RAG Directory

This directory contains agent-specific RAG (Retrieval-Augmented Generation) files.

## Structure

```
RAG/
├── agent_{name}/              # RAG for specific agent
│   ├── RAG/                   # Holds RAG files
│   │   ├── {agent_name}-RAG/  # Generated RAG index
│   │   ├── README-RAG.md      # Information about the RAG
│   │   └── {source_files}/    # Files used to generate RAG
│   └── config.json            # Agent RAG configuration
```

## Usage

### Create RAG for an Agent

```bash
# Create RAG for code agent
opencode rag create --agent code --source ./docs

# Create RAG for architect agent
opencode rag create --agent architect --source ./plans
```

### Query Agent RAG

```bash
# Query code agent's RAG
opencode rag query --agent code "How to implement authentication?"

# Use in multi-model pattern
opencode run "Write a function" --agent code --rag
```

## Agent RAG Types

| Agent | RAG Purpose | Typical Sources |
|-------|-------------|-----------------|
| `code` | Code patterns, best practices | Source code, docs |
| `architect` | Architecture decisions | Plans, ADRs |
| `debug` | Error patterns, solutions | Logs, fixes |
| `ask` | General knowledge | Documentation |

## Configuration

Each agent's RAG can be configured in `config.json`:

```json
{
  "agent": "code",
  "embedding_model": "nomic-embed-text",
  "chunk_size": 512,
  "top_k": 5,
  "sources": ["./src", "./docs"],
  "file_patterns": ["*.py", "*.md"]
}
```

## Generated Files

- `{agent_name}-RAG/` - Vector index for similarity search
- `README-RAG.md` - Auto-generated documentation
- `index.json` - Metadata about indexed documents
