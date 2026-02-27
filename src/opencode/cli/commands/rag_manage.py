"""
RAG Management Commands.

Commands for managing RAG indexes (add, status, clear, stats).
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

app = typer.Typer(name="rag-manage", help="RAG management commands")
console = Console()


@app.command("add")
def add_to_rag(
    agent: str = typer.Argument(..., help="Agent name"),
    source: str = typer.Argument(..., help="Source path to add"),
):
    """Add a source to an existing RAG index."""
    console.print(f"[bold blue]Adding source to RAG for agent: {agent}[/]")
    
    async def _add():
        from opencode.core.rag.source_manager import SourceManager
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
        
        # Validate source
        source_path = Path(source)
        if not source_path.exists():
            console.print(f"[red]Error: Source path does not exist: {source}[/]")
            raise typer.Exit(1)
        
        # Initialize components
        embedding_engine = LocalEmbeddingEngine(LocalEmbeddingConfig(
            model=config.get("embedding_model", "nomic-embed-text"),
        ))
        
        vector_store_instance = LocalVectorStore(
            path=str(agent_dir / ".vector_store"),
        )
        
        # Index source
        source_manager = SourceManager()
        documents = await source_manager.index_source(source_path)
        
        for doc in documents:
            embedding = await embedding_engine.embed(doc.content)
            await vector_store_instance.add(doc.id, embedding, doc.metadata)
        
        # Update config
        config["sources"].append(source)
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)
        
        console.print(f"[green]Added {len(documents)} documents from {source}[/]")
    
    asyncio.run(_add())


@app.command("status")
def rag_status(
    agent: str = typer.Argument(..., help="Agent name"),
):
    """Show RAG index status."""
    agent_dir = Path("./RAG") / f"agent_{agent}"
    config_file = agent_dir / "config.json"
    
    if not config_file.exists():
        console.print(f"[red]Error: RAG index not found for agent '{agent}'[/]")
        raise typer.Exit(1)
    
    with open(config_file, "r") as f:
        config = json.load(f)
    
    # Get vector store stats
    vector_dir = agent_dir / ".vector_store"
    doc_count = len(list(vector_dir.glob("*.json"))) if vector_dir.exists() else 0
    
    # Display status
    table = Table(title=f"RAG Status: {agent}")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Agent", config.get("agent", "unknown"))
    table.add_row("Embedding Model", config.get("embedding_model", "unknown"))
    table.add_row("Vector Store", config.get("vector_store", "unknown"))
    table.add_row("Documents", str(doc_count))
    table.add_row("Sources", ", ".join(config.get("sources", [])))
    
    console.print(table)


@app.command("clear")
def clear_rag(
    agent: str = typer.Argument(..., help="Agent name"),
    force: bool = typer.Option(False, "--force", "-f", help="Force clear without confirmation"),
):
    """Clear a RAG index."""
    agent_dir = Path("./RAG") / f"agent_{agent}"
    
    if not agent_dir.exists():
        console.print(f"[red]Error: RAG index not found for agent '{agent}'[/]")
        raise typer.Exit(1)
    
    if not force:
        confirm = typer.confirm(f"Are you sure you want to clear RAG for agent '{agent}'?")
        if not confirm:
            console.print("[yellow]Cancelled[/]")
            return
    
    # Clear vector store
    import shutil
    vector_dir = agent_dir / ".vector_store"
    if vector_dir.exists():
        shutil.rmtree(vector_dir)
    
    console.print(f"[green]Cleared RAG index for agent '{agent}'[/]")


@app.command("stats")
def rag_stats(
    agent: str = typer.Argument(..., help="Agent name"),
):
    """Show detailed RAG statistics."""
    console.print(f"[bold blue]RAG Statistics for agent: {agent}[/]")
    
    async def _stats():
        from opencode.core.rag.local_vector_store import LocalVectorStore
        
        agent_dir = Path("./RAG") / f"agent_{agent}"
        config_file = agent_dir / "config.json"
        
        if not config_file.exists():
            console.print(f"[red]Error: RAG index not found for agent '{agent}'[/]")
            raise typer.Exit(1)
        
        vector_store_instance = LocalVectorStore(
            path=str(agent_dir / ".vector_store"),
        )
        
        stats = await vector_store_instance.get_stats()
        
        # Display stats
        table = Table(title="RAG Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Documents", str(stats.get("total_documents", 0)))
        table.add_row("Total Chunks", str(stats.get("total_chunks", 0)))
        table.add_row("Vector Dimensions", str(stats.get("dimensions", 0)))
        table.add_row("Index Size (MB)", f"{stats.get('size_mb', 0):.2f}")
        
        console.print(table)
    
    asyncio.run(_stats())


if __name__ == "__main__":
    app()
