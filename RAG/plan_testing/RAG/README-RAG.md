# Testing Plan RAG

This RAG index contains information from testing-related plans and documentation.

## Source Files

- `plans/TESTING_PLAN.md` - Main testing strategy and coverage goals
- `plans/FOR_TESTING_PLAN.md` - Testing infrastructure setup
- `docs/TESTING_STATUS.md` - Current test coverage and status

## Purpose

This RAG enables agents to query testing strategies, coverage requirements, and testing infrastructure details without reading the full documents.

## Usage

```bash
# Query testing RAG
opencode rag query --plan testing "What is the test coverage goal?"

# Use in agent workflow
opencode run "Write tests for this feature" --plan-rag testing
```

## Generated Files

- `testing-RAG/` - Vector index for similarity search
- `index.json` - Metadata about indexed documents
