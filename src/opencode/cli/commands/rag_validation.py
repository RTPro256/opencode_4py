"""
RAG Validation Commands.

Commands for validating and managing false content in RAG indexes.
"""

import asyncio
import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(name="rag-validation", help="RAG validation commands")
console = Console()


@app.command("mark-false")
def mark_false_content(
    agent: str = typer.Argument(..., help="Agent name"),
    content: str = typer.Argument(..., help="Content to mark as false"),
    source: str = typer.Option(..., "--source", "-s", help="Source path"),
    reason: str = typer.Option(..., "--reason", "-r", help="Reason for marking as false"),
    evidence: Optional[str] = typer.Option(None, "--evidence", "-e", help="Evidence/test results"),
):
    """Mark content as false and trigger regeneration."""
    console.print(f"[bold blue]Marking false content for agent: {agent}[/]")
    
    async def _mark_false():
        from opencode.core.rag.validation.false_content_registry import FalseContentRegistry
        
        # Load registry
        agent_dir = Path("./RAG") / f"agent_{agent}"
        registry_path = agent_dir / ".false_content_registry.json"
        
        registry = FalseContentRegistry(path=str(registry_path))
        
        # Add false content
        record = await registry.add_false_content(
            content=content,
            source_id=source,
            source_path=source,
            reason=reason,
            evidence=evidence,
            marked_by="cli_user",
        )
        
        console.print(f"[green]✓[/] Marked content as false: {record.id}")
        console.print(f"  Reason: {reason}")
        console.print(f"  Source: {source}")
        
        # Show regeneration hint
        console.print(f"\n[yellow]Run 'opencode rag regenerate {agent}' to update the index[/]")
    
    asyncio.run(_mark_false())


@app.command("list-false")
def list_false_content(
    agent: str = typer.Argument(..., help="Agent name"),
    source: Optional[str] = typer.Option(None, "--source", "-s", help="Filter by source"),
    include_removed: bool = typer.Option(False, "--all", "-a", help="Include removed content"),
):
    """List all false content for an agent."""
    console.print(f"[bold blue]False Content for agent: {agent}[/]\n")
    
    async def _list_false():
        from opencode.core.rag.validation.false_content_registry import FalseContentRegistry
        
        # Load registry
        agent_dir = Path("./RAG") / f"agent_{agent}"
        registry_path = agent_dir / ".false_content_registry.json"
        
        if not registry_path.exists():
            console.print("[yellow]No false content registry found[/]")
            return
        
        registry = FalseContentRegistry(path=str(registry_path))
        
        # Get records
        if source:
            records = await registry.get_false_content_by_path(source)
        else:
            records = await registry.get_all_records(include_removed=include_removed)
        
        if not records:
            console.print("[green]No false content found[/]")
            return
        
        # Display records
        table = Table(title=f"False Content ({len(records)} records)")
        table.add_column("ID", style="dim", width=20)
        table.add_column("Source", style="cyan", width=30)
        table.add_column("Reason", style="yellow", width=40)
        table.add_column("Status", style="green", width=10)
        
        for record in records:
            status = "Removed" if record.is_removed else "Pending"
            reason_preview = record.reason[:40] + "..." if len(record.reason) > 40 else record.reason
            
            table.add_row(
                record.id[:20],
                record.source_path[:30],
                reason_preview,
                status,
            )
        
        console.print(table)
        
        # Show stats
        stats = await registry.get_stats()
        console.print(f"\n[dim]Total: {stats['total_records']} | Pending: {stats['pending_removal']} | Removed: {stats['removed']}[/]")
    
    asyncio.run(_list_false())


@app.command("regenerate")
def regenerate_rag(
    agent: str = typer.Argument(..., help="Agent name"),
    source: Optional[str] = typer.Option(None, "--source", "-s", help="Regenerate specific source"),
):
    """Regenerate RAG index after content removal."""
    console.print(f"[bold blue]Regenerating RAG for agent: {agent}[/]")
    
    async def _regenerate():
        from opencode.core.rag.validation.false_content_registry import FalseContentRegistry
        from opencode.core.rag.validation.rag_regenerator import RAGRegenerator
        from opencode.core.rag.local_vector_store import LocalVectorStore
        from opencode.core.rag.source_manager import SourceManager
        
        # Load config
        agent_dir = Path("./RAG") / f"agent_{agent}"
        config_file = agent_dir / "config.json"
        
        if not config_file.exists():
            console.print(f"[red]Error: RAG index not found for agent '{agent}'[/]")
            raise typer.Exit(1)
        
        with open(config_file, "r") as f:
            config = json.load(f)
        
        # Initialize components
        registry = FalseContentRegistry(path=str(agent_dir / ".false_content_registry.json"))
        vector_store = LocalVectorStore(
            path=str(agent_dir / ".vector_store"),
            engine=config.get("vector_store", "file"),
        )
        source_manager = SourceManager(
            allowed_sources=config.get("sources", []),
        )
        
        regenerator = RAGRegenerator(
            vector_store=vector_store,
            registry=registry,
            source_manager=source_manager,
        )
        
        # Regenerate
        if source:
            result = await regenerator.regenerate_source(source)
        else:
            results = await regenerator.regenerate_all()
            
            if not results:
                console.print("[green]No false content to regenerate[/]")
                return
            
            # Show summary
            total_removed = sum(r.false_content_removed for r in results)
            total_reindexed = sum(r.documents_reindexed for r in results)
            
            console.print(f"[green]✓[/] Regenerated {len(results)} sources")
            console.print(f"  False content removed: {total_removed}")
            console.print(f"  Documents re-indexed: {total_reindexed}")
            return
        
        if result.success:
            console.print(f"[green]✓[/] Regeneration complete")
            console.print(f"  Documents removed: {result.documents_removed}")
            console.print(f"  Documents re-indexed: {result.documents_reindexed}")
            console.print(f"  False content removed: {result.false_content_removed}")
            console.print(f"  Duration: {result.duration_seconds:.2f}s")
        else:
            console.print(f"[red]Error: {result.error}[/]")
    
    asyncio.run(_regenerate())


@app.command("validate")
def validate_content(
    agent: str = typer.Argument(..., help="Agent name"),
    content: str = typer.Argument(..., help="Content to validate"),
    source: str = typer.Option(..., "--source", "-s", help="Source ID"),
    validation_type: str = typer.Option("user", "--type", "-t", help="Validation type (test, ai, user)"),
    reason: Optional[str] = typer.Option(None, "--reason", "-r", help="Reason for validation"),
):
    """Validate content for accuracy."""
    console.print(f"[bold blue]Validating content for agent: {agent}[/]")
    
    async def _validate():
        from opencode.core.rag.validation.content_validator import ContentValidator, ValidationType
        
        validator = ContentValidator()
        
        # Parse validation type
        val_type = ValidationType(validation_type.lower())
        
        result = await validator.validate_content(
            content=content,
            source_id=source,
            validation_type=val_type,
            reason=reason,
        )
        
        if result.is_valid:
            console.print(f"[green]✓[/] Content is valid")
        else:
            console.print(f"[red]✗[/] Content marked as FALSE")
            console.print(f"  Reason: {result.reason}")
            console.print(f"  Confidence: {result.confidence:.2f}")
            
            # Offer to mark as false
            if typer.confirm("Add to false content registry?"):
                from opencode.core.rag.validation.false_content_registry import FalseContentRegistry
                
                agent_dir = Path("./RAG") / f"agent_{agent}"
                registry = FalseContentRegistry(path=str(agent_dir / ".false_content_registry.json"))
                
                await registry.add_false_content(
                    content=content,
                    source_id=source,
                    source_path=source,
                    reason=reason or "Validation failed",
                    marked_by="cli_user",
                )
                
                console.print("[green]✓[/] Added to false content registry")
    
    asyncio.run(_validate())


if __name__ == "__main__":
    app()
