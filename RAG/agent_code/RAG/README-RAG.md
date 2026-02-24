# Code Agent RAG

This RAG (Retrieval-Augmented Generation) index is for the **code** agent.

## Purpose

The code agent uses this RAG to:
- Retrieve relevant code patterns
- Find similar implementations
- Access best practices documentation
- Reference coding standards

## Usage

```bash
# Query the code agent RAG
opencode rag query --agent code "How to implement error handling?"

# Add files to the RAG
opencode rag add --agent code ./src/my_module.py

# Rebuild the RAG index
opencode rag rebuild --agent code
```

## Configuration

See `../config.json` for RAG settings.

## Source Files

Place source files in this directory to be indexed:
- Python files (`.py`)
- Markdown docs (`.md`)
- Text files (`.txt`)

## Index Status

- **Created**: Not yet created
- **Documents**: 0
- **Last Updated**: Never

Run `opencode rag create --agent code` to initialize this RAG.
