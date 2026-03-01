"""
Multi-agent CLI commands for opencode_4py.

Based on overstory (https://github.com/jayminwest/overstory)

Commands:
- sling: Spawn a worker agent
- init: Initialize orchestration
- stop: Stop an agent
- coordinator: Coordinator commands
- status: Show agent status
- mail: Messaging commands
"""

import typer
from typing import Optional
from rich.console import Console
from rich.table import Table

from opencode.core.multiagent import Coordinator, MultiAgentConfig
from opencode.core.multiagent.models import AgentType, AgentState
from opencode.core.multiagent.messaging import MessageBus
from opencode.core.multiagent.worktree import WorktreeManager

app = typer.Typer(help="Multi-agent orchestration commands")
console = Console()


def get_coordinator() -> Coordinator:
    """Get a coordinator instance."""
    config = MultiAgentConfig()
    message_bus = MessageBus(config.message_db_path)
    worktree_manager = WorktreeManager(config.worktree_base)
    return Coordinator(message_bus=message_bus, worktree_manager=worktree_manager)


@app.command("init")
def init_orchestration(
    force: bool = typer.Option(False, "--force", "-f", help="Force reinitialize"),
):
    """Initialize multi-agent orchestration in the project."""
    # Check if already initialized
    import os
    config = MultiAgentConfig()
    
    if os.path.exists(config.base_dir) and not force:
        console.print(f"[yellow]Already initialized. Use --force to reinitialize.[/yellow]")
        return
    
    # Create directories
    import pathlib
    pathlib.Path(config.base_dir).mkdir(parents=True, exist_ok=True)
    pathlib.Path(config.worktree_base).mkdir(parents=True, exist_ok=True)
    
    console.print(f"[green]Initialized multi-agent orchestration in {config.base_dir}/[/green]")


@app.command("sling")
def sling_agent(
    task_id: str = typer.Argument(..., help="Task ID to work on"),
    capability: str = typer.Option("builder", "--capability", "-c", help="Agent capability (builder, scout, lead, merger)"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Agent name"),
    parent: Optional[str] = typer.Option(None, "--parent", "-p", help="Parent agent ID"),
    skip_worktree: bool = typer.Option(False, "--skip-worktree", help="Skip worktree creation"),
):
    """Spawn a worker agent."""
    coordinator = get_coordinator()
    
    # Map capability to agent type
    capability_map = {
        "builder": AgentType.BUILDER,
        "scout": AgentType.SCOUT,
        "lead": AgentType.LEAD,
        "merger": AgentType.MERGER,
        "reviewer": AgentType.REVIEWER,
    }
    
    agent_type = capability_map.get(capability, AgentType.BUILDER)
    
    if not name:
        name = f"{capability}-{task_id}"
    
    agent = coordinator.spawn_agent(
        agent_type=agent_type,
        name=name,
        task_id=task_id,
        parent_id=parent,
    )
    
    console.print(f"[green]Spawned agent:[/green] {agent.id}")
    console.print(f"  Type: {agent.agent_type}")
    console.print(f"  Task: {task_id}")
    console.print(f"  Worktree: {agent.worktree_path or 'none'}")


@app.command("stop")
def stop_agent(
    agent_id: str = typer.Argument(..., help="Agent ID to stop"),
    clean_worktree: bool = typer.Option(True, "--clean/--no-clean", help="Clean worktree"),
):
    """Stop an agent."""
    coordinator = get_coordinator()
    
    if coordinator.stop_agent(agent_id):
        console.print(f"[green]Stopped agent:[/green] {agent_id}")
    else:
        console.print(f"[red]Agent not found: {agent_id}[/red]")


@app.command("status")
def show_status(
    json_output: bool = typer.Option(False, "--json", help="JSON output"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Show agent status."""
    coordinator = get_coordinator()
    
    status = coordinator.get_status()
    
    if json_output:
        import json
        console.print(json.dumps(status, indent=2))
        return
    
    console.print(f"\n[cyan]Coordinator:[/cyan] {status['coordinator_id']}")
    console.print(f"[cyan]Active Agents:[/cyan] {status['active_agents']}")
    
    # Show by state
    if status['agents_by_state']:
        console.print("\n[yellow]Agents by State:[/yellow]")
        for state, count in status['agents_by_state'].items():
            if count > 0:
                console.print(f"  {state}: {count}")
    
    # Show by type
    if status['agents_by_type']:
        console.print("\n[yellow]Agents by Type:[/yellow]")
        for atype, count in status['agents_by_type'].items():
            if count > 0:
                console.print(f"  {atype}: {count}")
    
    # List active agents
    agents = coordinator.list_agents()
    if agents and verbose:
        table = Table(title="Active Agents")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="white")
        table.add_column("Type", style="green")
        table.add_column("State", style="yellow")
        table.add_column("Task", style="magenta")
        
        for agent in agents:
            table.add_row(
                agent.id,
                agent.name,
                agent.agent_type.value,
                agent.state.value,
                agent.task_id or "-",
            )
        
        console.print(table)


# Coordinator subcommands
coord_app = typer.Typer(help="Coordinator commands")

@app.command("coordinator")
def coordinator_commands():
    """Manage coordinator."""
    pass


@coord_app.command("start")
def start_coordinator():
    """Start the coordinator."""
    import os
    config = MultiAgentConfig()
    
    # Check if coordinator is already running (pid file)
    pid_file = os.path.join(config.base_dir, "coordinator.pid")
    if os.path.exists(pid_file):
        with open(pid_file) as f:
            pid = f.read().strip()
        console.print(f"[yellow]Coordinator already running (PID: {pid})[/yellow]")
        return
    
    console.print("[green]Starting coordinator...[/green]")
    console.print("(Use 'opencode multiagent sling' to spawn agents)")
    console.print(f"[green]Coordinator ready at {config.base_dir}/[/green]")


@coord_app.command("stop")
def stop_coordinator():
    """Stop the coordinator."""
    import os
    config = MultiAgentConfig()
    pid_file = os.path.join(config.base_dir, "coordinator.pid")
    
    if not os.path.exists(pid_file):
        console.print("[yellow]Coordinator not running[/yellow]")
        return
    
    os.remove(pid_file)
    console.print("[green]Coordinator stopped[/green]")


@coord_app.command("status")
def coordinator_status():
    """Show coordinator status."""
    import os
    config = MultiAgentConfig()
    base_dir = config.base_dir
    
    console.print(f"[cyan]Base Directory:[/cyan] {base_dir}")
    console.print(f"[cyan]Worktree Base:[/cyan] {config.worktree_base}")
    console.print(f"[cyan]Message DB:[/cyan] {config.message_db_path}")
    
    # Check if running
    pid_file = os.path.join(base_dir, "coordinator.pid")
    if os.path.exists(pid_file):
        with open(pid_file) as f:
            pid = f.read().strip()
        console.print(f"[green]Status: Running (PID: {pid})[/green]")
    else:
        console.print("[yellow]Status: Not running[/yellow]")


app.add_typer(coord_app, name="coordinator")


# Mail commands
mail_app = typer.Typer(help="Agent messaging commands")


@mail_app.command("send")
def send_message(
    to: str = typer.Option(..., "--to", "-t", help="Recipient agent ID"),
    subject: str = typer.Option(..., "--subject", "-s", help="Message subject"),
    body: str = typer.Option(..., "--body", "-b", help="Message body"),
    msg_type: str = typer.Option("status", "--type", help="Message type (status, question, error)"),
):
    """Send a message to an agent."""
    config = MultiAgentConfig()
    bus = MessageBus(config.message_db_path)
    
    from opencode.core.multiagent.models import MessageType, MessagePriority
    msg_type_map = {
        "status": MessageType.STATUS,
        "question": MessageType.QUESTION,
        "error": MessageType.ERROR,
        "done": MessageType.WORKER_DONE,
    }
    
    msg = bus.send(
        from_agent="cli",
        to_agent=to,
        subject=subject,
        body=body,
        message_type=msg_type_map.get(msg_type, MessageType.STATUS),
    )
    
    console.print(f"[green]Sent message:[/green] {msg.id}")


@mail_app.command("check")
def check_mail(
    agent_id: str = typer.Argument("cli", help="Agent ID to check"),
    inject: bool = typer.Option(False, "--inject", help="Show messages"),
):
    """Check for messages."""
    config = MultiAgentConfig()
    bus = MessageBus(config.message_db_path)
    
    messages = bus.receive(agent_id)
    unread_count = bus.get_unread_count(agent_id)
    
    console.print(f"[cyan]Unread messages:[/cyan] {unread_count}")
    
    if messages and inject:
        for msg in messages[:10]:  # Show first 10
            console.print(f"\n[yellow]From:[/yellow] {msg.from_agent}")
            console.print(f"[yellow]Subject:[/yellow] {msg.subject}")
            console.print(f"[yellow]Body:[/yellow] {msg.body[:200]}...")


app.add_typer(mail_app, name="mail")


# Worktree commands
wt_app = typer.Typer(help="Git worktree management")


@wt_app.command("list")
def list_worktrees():
    """List all worktrees."""
    config = MultiAgentConfig()
    wm = WorktreeManager(config.worktree_base)
    
    worktrees = wm.list_worktrees()
    
    if not worktrees:
        console.print("[yellow]No worktrees found[/yellow]")
        return
    
    table = Table(title="Worktrees")
    table.add_column("Agent ID", style="cyan")
    table.add_column("Branch", style="white")
    table.add_column("Path", style="green")
    table.add_column("Clean", style="yellow")
    
    for wt in worktrees:
        table.add_row(
            wt.agent_id or "unknown",
            wt.branch or "unknown",
            wt.path or "unknown",
            "✓" if wt.is_clean else "✗",
        )
    
    console.print(table)


@wt_app.command("create")
def create_worktree(
    agent_id: str = typer.Argument(..., help="Agent ID"),
    branch: Optional[str] = typer.Option(None, "--branch", "-b", help="Branch name"),
):
    """Create a new worktree."""
    config = MultiAgentConfig()
    wm = WorktreeManager(config.worktree_base)
    
    worktree = wm.create_worktree(agent_id, branch)
    console.print(f"[green]Created worktree:[/green] {worktree.path}")
    console.print(f"  Branch: {worktree.branch}")


@wt_app.command("delete")
def delete_worktree(
    agent_id: str = typer.Argument(..., help="Agent ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Force deletion"),
):
    """Delete a worktree."""
    config = MultiAgentConfig()
    wm = WorktreeManager(config.worktree_base)
    
    wm.remove_worktree(agent_id, force)
    console.print(f"[green]Deleted worktree:[/green] {agent_id}")


@wt_app.command("status")
def worktree_status(
    agent_id: Optional[str] = typer.Argument(None, help="Agent ID (optional)"),
):
    """Show worktree status."""
    config = MultiAgentConfig()
    wm = WorktreeManager(config.worktree_base)
    
    if agent_id:
        worktrees = wm.list_worktrees()
        wt = next((w for w in worktrees if w.agent_id == agent_id), None)
        if wt:
            console.print(f"[cyan]Agent ID:[/cyan] {wt.agent_id}")
            console.print(f"[cyan]Branch:[/cyan] {wt.branch}")
            console.print(f"[cyan]Path:[/cyan] {wt.path}")
            console.print(f"[cyan]Clean:[/cyan] {wt.is_clean}")
        else:
            console.print(f"[red]Worktree not found:[/red] {agent_id}")
    else:
        worktrees = wm.list_worktrees()
        console.print(f"[cyan]Total worktrees:[/cyan] {len(worktrees)}")


app.add_typer(wt_app, name="worktree")


if __name__ == "__main__":
    app()
