#!/usr/bin/env python3
"""
RAG (Retrieval-Augmented Generation) example for OpenCode Python.

This example demonstrates how to:
1. Set up a RAG pipeline
2. Index documents
3. Query with context retrieval
"""

import asyncio
from pathlib import Path

# Note: These imports assume opencode is installed
# pip install opencode-python


async def main():
    """Run the RAG example."""
    from opencode.core.rag import RAGPipeline, RAGConfig
    from opencode.core.rag.source_manager import SourceManager
    
    # Configure RAG
    config = RAGConfig(
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        chunk_size=512,
        chunk_overlap=50,
        top_k=5,
    )
    
    # Initialize the pipeline
    pipeline = RAGPipeline(config)
    
    # Index documents from a directory
    docs_path = Path("./docs")
    if docs_path.exists():
        source_manager = SourceManager()
        await source_manager.add_source(str(docs_path))
        
        # Index the documents
        await pipeline.index(source_manager)
        print("Documents indexed successfully!")
    
    # Query with RAG
    query = "How do I configure the provider?"
    response = await pipeline.query(query)
    
    print(f"Query: {query}")
    print(f"Response: {response.answer}")
    print(f"Sources: {response.sources}")


if __name__ == "__main__":
    asyncio.run(main())