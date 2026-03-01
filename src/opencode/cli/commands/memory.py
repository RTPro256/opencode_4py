"""
Memory CLI commands for opencode_4py.

Based on beads (https://github.com/steveyegge/beads)

Commands:
- task create: Create a new task
- task list: List tasks
- task ready: Show ready tasks
- task show: Show task details
- task update: Update a task
- task close: Close a task
- dep add: Add dependency
"""

import typer
from typing import Optional, List
from rich.console import Console
from rich.table import Table

from opencode.core.memory import MemoryGraph, MemoryStore, MemoryConfig
from opencode.core.memory.models import TaskStatus, RelationshipType, RelationshipType

app = typer.Typer(help="Memory management commands")
console = Console()


def get_graph() -> MemoryGraph:
    """Get a memory graph instance."""
    config = MemoryConfig()
    store = MemoryStore(config.get_db_path())
    return MemoryGraph(store)


@app.command("create")
def create_task(
    title: str = typer.Argument(..., help="Task title"),
    description: str = typer.Option("", "--description", "-d", help="Task description"),
    priority: int = typer.Option(2, "--priority", "-p", help="Priority (0=P0 highest, 4=P4 lowest)"),
    parent: Optional[str] = typer.Option(None, "--parent", help="Parent task ID for hierarchical tasks"),
):
    """Create a new task."""
    graph = get_graph()
    task = graph.create_task(
        title=title,
        description=description,
        priority=priority,
        parent_id=parent,
    )
    console.print(f"[green]Created task:[/green] {task.id}")
    console.print(f"  Title: {task.title}")
    console.print(f"  Priority: P{task.priority}")


@app.command("list")
def list_tasks(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status (open, in_progress, closed)"),
    priority: Optional[int] = typer.Option(None, "--priority", "-p", help="Filter by priority"),
    assignee: Optional[str] = typer.Option(None, "--assignee", "-a", help="Filter by assignee"),
):
    """List tasks."""
    graph = get_graph()
    
    status_filter = TaskStatus(status) if status else None
    tasks = graph.list_tasks(status=status_filter, priority=priority, assignee=assignee)
    
    if not tasks:
        console.print("[yellow]No tasks found[/yellow]")
        return
    
    table = Table(title="Tasks")
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Status", style="green")
    table.add_column("Priority", style="yellow")
    table.add_column("Assignee", style="magenta")
    
    for task in tasks:
        table.add_row(
            task.id,
            task.title[:50],
            task.status.value,
            f"P{task.priority}",
            task.assignee or "-",
        )
    
    console.print(table)


@app.command("ready")
def show_ready():
    """Show tasks with no open blockers."""
    graph = get_graph()
    tasks = graph.get_ready_tasks()
    
    if not tasks:
        console.print("[yellow]No ready tasks found[/yellow]")
        return
    
    table = Table(title="Ready Tasks")
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Priority", style="yellow")
    
    for task in tasks:
        table.add_row(task.id, task.title[:50], f"P{task.priority}")
    
    console.print(table)


@app.command("show")
def show_task(
    task_id: str = typer.Argument(..., help="Task ID"),
):
    """Show task details."""
    graph = get_graph()
    task = graph.get_task(task_id)
    
    if not task:
        console.print(f"[red]Task not found: {task_id}[/red]")
        return
    
    console.print(f"\n[cyan]Task:[/cyan] {task.id}")
    console.print(f"  Title: {task.title}")
    console.print(f"  Description: {task.description}")
    console.print(f"  Status: {task.status.value}")
    console.print(f"  Priority: P{task.priority}")
    console.print(f"  Assignee: {task.assignee or 'unassigned'}")
    console.print(f"  Parent: {task.parent_id or 'none'}")
    console.print(f"  Created: {task.created_at}")
    console.print(f"  Updated: {task.updated_at}")
    
    if task.closed_at:
        console.print(f"  Closed: {task.closed_at}")
    
    # Show blockers
    blockers = graph.get_blockers(task_id)
    if blockers:
        console.print(f"\n[yellow]Blockers:[/yellow]")
        for b in blockers:
            console.print(f"  - {b.id}: {b.title} ({b.status.value})")


@app.command("update")
def update_task(
    task_id: str = typer.Argument(..., help="Task ID"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="New title"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="New description"),
    claim: bool = typer.Option(False, "--claim", help="Claim the task"),
    assignee: Optional[str] = typer.Option(None, "--assignee", "-a", help="Assignee"),
):
    """Update a task."""
    graph = get_graph()
    task = graph.get_task(task_id)
    
    if not task:
        console.print(f"[red]Task not found: {task_id}[/red]")
        return
    
    if claim:
        if not assignee:
            console.print("[red]--assignee required when using --claim[/red]")
            return
        task = graph.claim_task(task_id, assignee)
        if task:
            console.print(f"[green]Claimed task:[/green] {task.id}")
        else:
            console.print(f"[red]Failed to claim task: {task_id}[/red]")
    else:
        if title:
            task.title = title
        if description:
            task.description = description
        if assignee:
            task.assignee = assignee
        
        task = graph.update_task(task)
        console.print(f"[green]Updated task:[/green] {task.id}")


@app.command("close")
def close_task(
    task_id: str = typer.Argument(..., help="Task ID"),
):
    """Close a task."""
    graph = get_graph()
    task = graph.close_task(task_id)
    
    if task:
        console.print(f"[green]Closed task:[/green] {task.id}")
    else:
        console.print(f"[red]Task not found: {task_id}[/red]")


# Dependency subcommands
dep_app = typer.Typer(help="Manage task dependencies")

@app.command("dep")
@app.command("dependency")
def dependency_commands():
    """Manage task dependencies."""
    pass


@dep_app.command("add")
def add_dependency(
    child_id: str = typer.Argument(..., help="Child task ID"),
    parent_id: str = typer.Argument(..., help="Parent task ID"),
):
    """Add a dependency (child depends on parent)."""
    graph = get_graph()
    
    child = graph.get_task(child_id)
    parent = graph.get_task(parent_id)
    
    if not child:
        console.print(f"[red]Child task not found: {child_id}[/red]")
        return
    if not parent:
        console.print(f"[red]Parent task not found: {parent_id}[/red]")
        return
    
    graph.add_dependency(child_id, parent_id)
    console.print(f"[green]Added dependency:[/green] {child_id} depends on {parent_id}")


@dep_app.command("remove")
def remove_dependency(
    child_id: str = typer.Argument(..., help="Child task ID"),
    parent_id: str = typer.Argument(..., help="Parent task ID"),
):
    """Remove a dependency."""
    graph = get_graph()
    graph.remove_dependency(child_id, parent_id)
    console.print(f"[green]Removed dependency:[/green] {child_id} no longer depends on {parent_id}")


@dep_app.command("list")
def list_dependencies(
    task_id: str = typer.Argument(..., help="Task ID"),
    direction: str = typer.Option("both", "--direction", "-d", 
                                  help="Direction: parents, children, or both"),
):
    """List dependencies for a task."""
    graph = get_graph()
    task = graph.get_task(task_id)
    
    if not task:
        console.print(f"[red]Task not found: {task_id}[/red]")
        return
    
    console.print(f"[cyan]Dependencies for {task_id}:[/cyan]")
    
    if direction in ("parents", "both"):
        parents = graph.get_parents(task_id)
        console.print(f"  [yellow]Parents:[/yellow] {len(parents)}")
        for p in parents:
            console.print(f"    - {p.id}: {p.title}")
    
    if direction in ("children", "both"):
        children = graph.get_children(task_id)
        console.print(f"  [yellow]Children:[/yellow] {len(children)}")
        for c in children:
            console.print(f"    - {c.id}: {c.title}")


@dep_app.command("validate")
def validate_dependencies():
    """Validate all dependencies (check for cycles)."""
    graph = get_graph()
    cycles = graph.detect_cycles()
    
    if cycles:
        console.print("[red]Found dependency cycles:[/red]")
        for cycle in cycles:
            console.print(f"  {' -> '.join(cycle)}")
    else:
        console.print("[green]No dependency cycles found[/green]")


app.add_typer(dep_app, name="dep")
app.add_typer(dep_app, name="dependency")


if __name__ == "__main__":
    app()
