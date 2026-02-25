# Troubleshooting Agent RAG

This RAG index contains troubleshooting patterns and error solutions for the debug agent.

## Source Files

- `RAG/troubleshooting/errors/` - Known error types (ERR-001 to ERR-017)
- `RAG/troubleshooting/patterns/` - Diagnosis patterns (PATTERN-001 to PATTERN-003)
- `RAG/troubleshooting/workflows/` - Troubleshooting workflows (WORKFLOW-001 to WORKFLOW-002)

## Purpose

This RAG enables the debug agent to:
1. Match current errors against known patterns
2. Retrieve solutions from past troubleshooting
3. Follow established diagnosis workflows

## Usage

```bash
# Query troubleshooting RAG
opencode rag query --agent troubleshooting "TUI stalls at Thinking"

# Use in debug workflow
opencode run "Debug this error" --agent debug --rag
```

## Error Categories

| Category | Errors | Description |
|----------|--------|-------------|
| CLI | ERR-001 | Command structure issues |
| Database | ERR-002 | SQLAlchemy syntax |
| Provider | ERR-003, ERR-007, ERR-009 | AI provider issues |
| Preflight | ERR-004 | Missing preflight checks |
| Web | ERR-005 | Framework response types |
| Dependencies | ERR-006 | Version warnings |
| TUI | ERR-008, ERR-016, ERR-017 | UI widget issues |
| Async | ERR-010 | Generator await issues |
| Logging | ERR-011 | Silent failures |
| Config | ERR-012, ERR-013 | Parameter and storage issues |
| Reactive | ERR-014 | Property watch issues |
| Environment | ERR-015 | Installed vs source mismatch |

## Generated Files

- `troubleshooting-RAG/` - Vector index for similarity search
- `index.json` - Metadata about indexed documents
