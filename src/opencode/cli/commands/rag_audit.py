"""
RAG Audit Commands.

Commands for viewing RAG audit logs.
"""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(name="rag-audit", help="RAG audit commands")
console = Console()


@app.command("audit")
def rag_audit(
    agent: str = typer.Argument(..., help="Agent name"),
    days: int = typer.Option(7, "--days", "-d", help="Number of days to show"),
    event_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by event type"),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum entries to show"),
):
    """Show RAG audit log."""
    console.print(f"[bold blue]RAG Audit Log for agent: {agent}[/]\n")
    
    async def _audit():
        from opencode.core.rag.safety.audit_logger import RAGAuditLogger
        
        # Load audit log
        agent_dir = Path("./RAG") / f"agent_{agent}"
        audit_log = agent_dir / "audit.log"
        
        if not audit_log.exists():
            console.print("[yellow]No audit log found[/]")
            return
        
        logger = RAGAuditLogger(path=str(audit_log))
        
        # Get entries
        start_date = datetime.utcnow() - timedelta(days=days)
        entries = await logger.get_entries_by_date(
            start_date=start_date,
            event_type=event_type,
        )
        
        if not entries:
            console.print("[yellow]No audit entries found[/]")
            return
        
        # Display entries
        table = Table(title=f"Audit Entries (last {days} days)")
        table.add_column("Time", style="dim")
        table.add_column("Type", style="cyan")
        table.add_column("Query/Source", style="white")
        table.add_column("Docs", style="green")
        
        for entry in entries[-limit:]:
            query_or_source = entry.query or (entry.sources_used[0] if entry.sources_used else "")
            if query_or_source and len(query_or_source) > 50:
                query_or_source = query_or_source[:50] + "..."
            
            table.add_row(
                entry.timestamp.strftime("%Y-%m-%d %H:%M"),
                entry.event_type,
                query_or_source or "-",
                str(entry.document_count),
            )
        
        console.print(table)
        
        # Show stats
        stats = await logger.get_stats()
        console.print(f"\n[dim]Total entries: {stats['total_entries']}[/]")
    
    asyncio.run(_audit())


if __name__ == "__main__":
    app()
