# Python_Essentials Agent RAG

This RAG (Retrieval-Augmented Generation) index is for the **python_essentials** agent.

## Purpose

Python Essentials for AI Agents - YouTube video transcript

## Configuration

- **Embedding Model**: nomic-embed-text
- **Chunk Size**: 512
- **Top K**: 5
- **Min Similarity**: 0.7

## Usage

```bash
# Query this RAG
opencode rag query --agent python_essentials "your query"

# Add files
opencode rag add --agent python_essentials ./path/to/files

# Rebuild index
opencode rag rebuild --agent python_essentials
```

## Status

- **Created**: 2026-02-27T12:11:54.319711
- **Documents**: 0
- **Last Updated**: 2026-02-27T12:11:54.319717
