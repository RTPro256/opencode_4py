# Merge Plan RAG

This RAG index contains information from merge and integration-related plans.

## Source Files

- `plans/MERGE_INTEGRATION_PLAN.md` - Plan for merging 21 external projects
- `plans/TARGET_PROJECT_SYNC_PLAN.md` - Synchronization strategy
- `docs/DOCS_INDEX.md` - Documentation navigation

## Purpose

This RAG enables agents to query merge strategies, integration phases, and project synchronization details without reading the full documents.

## Usage

```bash
# Query merge RAG
opencode rag query --plan merge "What projects are high priority for merge?"

# Use in agent workflow
opencode run "Start merge of Local-RAG-with-Ollama" --plan-rag merge
```

## Generated Files

- `merge-RAG/` - Vector index for similarity search
- `index.json` - Metadata about indexed documents
