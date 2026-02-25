"""
RAG Query Commands.

Commands for querying RAG indexes.
"""

import asyncio
import json
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(name="rag-query", help="RAG query commands")
console = Console()


@app.command("query")
def query_rag(
    agent: str = typer.Argument(..., help="Agent name to query RAG for"),
    query: str = typer.Argument(..., help="Search query"),
    top_k: int = typer.Option(5, "--top", "-t", help="Number of top results"),
    threshold: float = typer.Option(0.0, "--threshold", help="Similarity threshold"),
    output_format: str = typer.Option("text", "--format", "-f", help="Output format (text, json)"),
):
    """Query a RAG index for relevant documents."""
    console.print(f"[bold blue]Querying RAG for agent: {agent}[/]")
    
    async def _query():
        from opencode.core.rag.config import RAGConfig
        from opencode.core.rag.hybrid_search import HybridSearch
        from opencode.core.rag.local_embeddings import LocalEmbeddingEngine, LocalEmbeddingConfig
        from opencode.core.rag.local_vector_store import LocalVectorStore
        
        # Load config
        agent_dir = Path("./RAG") / f"agent_{agent}"
        config_file = agent_dir / "config.json"
        
        if not config_file.exists():
            console.print(f"[red]Error: RAG index not found for agent '{agent}'[/]")
            raise typer.Exit(1)
        
        with open(config_file, "r") as f:
            config = json.load(f)
        
        # Initialize components
        embedding_engine = LocalEmbeddingEngine(LocalEmbeddingConfig(
            model=config.get("embedding_model", "nomic-embed-text"),
        ))
        
        vector_store_instance = LocalVectorStore(
            path=str(agent_dir / ".vector_store"),
        )
        
        hybrid_search = HybridSearch(
            vector_store=vector_store_instance,
        )
        
        # Generate query embedding
        query_embedding = await embedding_engine.embed(query)
        
        # Search
        results = await hybrid_search.search(query_embedding, top_k=top_k)
        
        # Filter by threshold
        filtered_results = [r for r in results if r.score >= threshold]
        
        # Output results
        if output_format == "json":
            output = json.dumps([{
                "content": r.content,
                "score": r.score,
                "source": r.source,
            } for r in filtered_results], indent=2)
            console.print(output)
        else:
            console.print(f"\n[bold green]Found {len(filtered_results)} results:[/]")
            for i, result in enumerate(filtered_results, 1):
                console.print(f"\n{i}. [cyan]{result['source']}[/] (score: {result['score']:.3f})")
                console.print(f"   {result['content'][:200]}...")
    
    asyncio.run(_query())


if __name__ == "__main__":
    app()
