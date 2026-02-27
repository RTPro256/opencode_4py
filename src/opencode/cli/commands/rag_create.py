"""
RAG Create Commands.

Commands for creating and initializing RAG indexes.
"""

from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel

app = typer.Typer(name="rag-create", help="RAG creation commands")
console = Console()


@app.command("create")
def create_rag(
    agent: str = typer.Argument(..., help="Agent name to create RAG for"),
    sources: List[str] = typer.Option([], "--source", "-s", help="Source directories to index"),
    embedding_model: str = typer.Option("nomic-embed-text", "--model", "-m", help="Embedding model"),
    vector_store: str = typer.Option("file", "--store", help="Vector store type (memory, file, chroma)"),
    output_dir: str = typer.Option("./RAG", "--output", "-o", help="Output directory"),
):
    """Create a RAG index for an agent."""
    console.print(f"[bold blue]Creating RAG index for agent: {agent}[/]")
    
    async def _create():
        from opencode.core.rag.config import RAGConfig
        from opencode.core.rag.local_embeddings import LocalEmbeddingEngine, LocalEmbeddingConfig
        from opencode.core.rag.local_vector_store import LocalVectorStore
        from opencode.core.rag.source_manager import SourceManager
        from opencode.core.rag.hybrid_search import HybridSearch
        
        # Create output directory
        agent_dir = Path(output_dir) / f"agent_{agent}"
        agent_dir.mkdir(parents=True, exist_ok=True)
        
        # Create config
        config = RAGConfig(
            agent_name=agent,
            embedding_model=embedding_model,
            vector_store_type=vector_store,
            sources=sources,
        )
        
        # Save config
        config_file = agent_dir / "config.json"
        config_file.write_text(config.model_dump_json(indent=2))
        
        # Initialize embedding engine
        embed_config = LocalEmbeddingConfig(model=embedding_model)
        embed_engine = LocalEmbeddingEngine(embed_config)
        
        # Initialize vector store
        store = LocalVectorStore(
            persist_directory=str(agent_dir / "vectors"),
            store_type=vector_store,
        )
        
        # Index sources
        if sources:
            source_manager = SourceManager(sources)
            documents = await source_manager.scan()
            
            for doc in documents:
                embedding = await embed_engine.embed(doc.content)
                await store.add(doc.id, embedding, doc.metadata)
        
        console.print(f"[green]Indexed {len(documents)} documents from {len(sources)} sources[/]")
        
        # Create hybrid search
        hybrid = HybridSearch(store, embed_engine)
        
        console.print(f"[green]RAG index created successfully at {agent_dir}[/]")
        console.print(f"[dim]Run 'opencode rag query {agent} <question>' to search[/]")
    
    import asyncio
    asyncio.run(_create())


if __name__ == "__main__":
    app()
