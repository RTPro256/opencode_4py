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
├── plan_{name}/               # RAG for specific plan
│   ├── RAG/                   # Holds RAG files
│   │   ├── {plan_name}-RAG/   # Generated RAG index
│   │   ├── README-RAG.md      # Information about the RAG
│   │   └── {source_files}/    # Files used to generate RAG
│   └── config.json            # Plan RAG configuration
├── bug_detected/              # Auto-populated on bug/error detection
│   ├── RAG/                   # Holds RAG files
│   │   ├── bug_detected-RAG/  # Generated RAG index
│   │   ├── README-RAG.md      # Information about the RAG
│   │   ├── errors/            # Individual error records
│   │   └── solutions/         # Linked solutions
│   └── config.json            # Bug detection configuration
└── troubleshooting/           # Error documentation and patterns
    ├── errors/                # Known error types
    ├── patterns/              # Diagnosis patterns
    └── workflows/             # Troubleshooting workflows
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

## Plan RAG Types

| Plan | RAG Purpose | Typical Sources |
|------|-------------|-----------------|
| `testing` | Testing strategies, coverage | TESTING_PLAN.md, TEST_STATUS.md |
| `merge` | Integration phases, priorities | MERGE_INTEGRATION_PLAN.md |
| `custom` | User-defined plan | Any plan documents |

## Bug Detection RAG

The `bug_detected/` RAG is automatically populated when opencode_4py detects errors:

| Trigger | Description |
|---------|-------------|
| `test_failure` | pytest test fails |
| `lint_error` | ruff/mypy error |
| `runtime_exception` | Unhandled exception |
| `type_error` | Type mismatch |
| `import_error` | Module not found |

```bash
# Query detected bugs
opencode rag query --bug "ModuleNotFoundError"

# Auto-queries happen when errors are detected
```

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
