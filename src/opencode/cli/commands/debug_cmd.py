"""
Debug CLI Commands for Simplified Troubleshooting.

Provides one-command troubleshooting with automatic logging and RAG query.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm

app = typer.Typer(name="debug", help="Simplified troubleshooting commands")
console = Console()


def enable_debug_logging() -> Path:
    """Enable debug logging and return log file path."""
    from opencode.core.config import Config
    
    # Create logs directory
    config = Config.load()
    log_dir = config.data_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate log filename with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = log_dir / f"debug_{timestamp}.log"
    
    # Set environment variables
    os.environ["OPENCODE_LOG_LEVEL"] = "DEBUG"
    os.environ["OPENCODE_LOG_FILE"] = str(log_file)
    
    return log_file


def query_troubleshooting_rag(issue: str) -> list[dict]:
    """Query the troubleshooting RAG for matching errors."""
    import json
    
    # Try to load RAG config
    rag_config_path = Path("RAG/agent_troubleshooting/config.json")
    if not rag_config_path.exists():
        # Try installed location
        rag_config_path = Path(__file__).parent.parent.parent.parent / "docs/RAG/agent_troubleshooting/config.json"
    
    if not rag_config_path.exists():
        return []
    
    # Simple keyword matching for now
    # In a full implementation, this would use the RAG's semantic search
    troubleshooting_dir = rag_config_path.parent.parent / "troubleshooting"
    errors_dir = troubleshooting_dir / "errors"
    
    if not errors_dir.exists():
        return []
    
    results = []
    issue_lower = issue.lower()
    
    # Keywords to match
    keywords = set(issue_lower.split())
    
    for error_file in errors_dir.glob("ERR-*.md"):
        try:
            content = error_file.read_text(encoding="utf-8").lower()
            
            # Calculate simple relevance score
            score = 0
            for keyword in keywords:
                if keyword in content:
                    score += 1
            
            if score > 0:
                # Extract key information
                lines = content.split("\n")
                title = ""
                symptom = ""
                root_cause = ""
                fix = ""
                
                for i, line in enumerate(lines):
                    if line.startswith("# "):
                        title = line[2:].strip()
                    elif "symptom" in line.lower() and i + 1 < len(lines):
                        symptom = lines[i + 1].strip()
                    elif "root cause" in line.lower() and i + 1 < len(lines):
                        root_cause = lines[i + 1].strip()
                    elif "fix" in line.lower() and i + 1 < len(lines):
                        fix_start = i + 1
                        fix_lines = []
                        for j in range(fix_start, min(fix_start + 10, len(lines))):
                            if lines[j].startswith("## ") or lines[j].startswith("# "):
                                break
                            fix_lines.append(lines[j].strip())
                        fix = "\n".join(fix_lines)
                
                results.append({
                    "file": str(error_file),
                    "title": title,
                    "symptom": symptom,
                    "root_cause": root_cause,
                    "fix": fix,
                    "score": score,
                })
        except Exception:
            continue
    
    # Sort by score
    results.sort(key=lambda x: x["score"], reverse=True)
    
    return results[:5]  # Return top 5 matches


def display_results(results: list[dict], issue: str) -> Optional[dict]:
    """Display matching errors and let user select one."""
    if not results:
        console.print("\n[yellow]No matching errors found in troubleshooting RAG.[/]")
        console.print("Would you like to start a manual debugging session?")
        return None
    
    console.print(f"\n[bold green]Found {len(results)} matching error(s):[/]\n")
    
    for i, result in enumerate(results, 1):
        confidence = min(100, result["score"] * 20)  # Simple confidence calculation
        
        panel_content = f"""
[bold]Symptom:[/bold] {result['symptom'][:100]}...
[bold]Root Cause:[/bold] {result['root_cause'][:100]}...
[bold]Fix:[/bold]
{result['fix'][:300]}...

[dim]Confidence: {confidence}% match[/dim]
"""
        console.print(Panel(
            panel_content,
            title=f"[bold]{result['title']}[/]",
            border_style="blue" if i == 1 else "dim",
        ))
        console.print()
    
    # Return best match
    return results[0]


def start_debug_session(issue: str, log_file: Path) -> None:
    """Start an interactive debugging session."""
    console.print(f"\n[bold]Starting debug session for:[/] {issue}")
    console.print(f"[dim]Log file: {log_file}[/dim]")
    console.print("\n[bold]Debugging steps:[/]")
    console.print("1. Reproduce the issue")
    console.print("2. Check the log file for errors")
    console.print("3. Apply the suggested fix")
    console.print("4. Test the fix")
    console.print("\nPress Ctrl+C to end the session\n")


@app.command("debug")
def debug_issue(
    issue: str = typer.Argument(..., help="Description of the issue to debug"),
    auto_fix: bool = typer.Option(False, "--fix", "-f", help="Automatically apply fix if found"),
    no_log: bool = typer.Option(False, "--no-log", help="Skip creating debug log"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
):
    """
    Start a debugging session for an issue.
    
    Automatically:
    1. Enables debug logging
    2. Queries troubleshooting RAG for known issues
    3. Displays relevant error documents with fixes
    4. Offers guidance for resolution
    
    Example:
        opencode debug "TUI stalls at Thinking"
        opencode debug "button not appearing" --fix
    """
    console.print(Panel(
        f"[bold]Debug Session[/]\nIssue: {issue}",
        border_style="red",
    ))
    
    # Step 1: Enable logging
    if not no_log:
        console.print("\n[bold]Step 1:[/] Enabling debug logging...")
        log_file = enable_debug_logging()
        console.print(f"[green]Log file:[/] {log_file}")
    else:
        log_file = None
        console.print("\n[dim]Skipping log creation (--no-log)[/]")
    
    # Step 2: Query RAG
    console.print("\n[bold]Step 2:[/] Querying troubleshooting RAG...")
    results = query_troubleshooting_rag(issue)
    
    # Step 3: Display results
    console.print("\n[bold]Step 3:[/] Analyzing results...")
    best_match = display_results(results, issue)
    
    if best_match:
        if auto_fix:
            console.print("\n[bold]Auto-fix mode:[/] Please apply the fix manually:")
            console.print(best_match["fix"])
        else:
            if Confirm.ask("\nWould you like to apply this fix?"):
                console.print("\n[bold]Fix steps:[/]")
                console.print(best_match["fix"])
                
                if Confirm.ask("\nFix applied. Test the fix now?"):
                    console.print("\n[bold]Starting test...[/]")
                    # Could launch TUI here for testing
    else:
        console.print("\n[bold]Manual debugging required.[/]")
        console.print("1. Check the log file for errors")
        console.print("2. Search the codebase for related code")
        console.print("3. Document the error after resolution")
    
    # Step 4: Start session
    if log_file:
        start_debug_session(issue, log_file)


@app.command("troubleshoot")
def troubleshoot_issue(
    issue: str = typer.Argument(..., help="Description of the issue to troubleshoot"),
    auto_fix: bool = typer.Option(False, "--fix", "-f", help="Automatically apply fix if found"),
    no_log: bool = typer.Option(False, "--no-log", help="Skip creating debug log"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
):
    """
    Alias for 'debug' command. Start a troubleshooting session.
    
    Example:
        opencode troubleshoot "TUI stalls at Thinking"
    """
    debug_issue(issue, auto_fix, no_log, verbose)


@app.command("log")
def create_debug_log(
    name: str = typer.Argument("session", help="Name for the log file"),
):
    """
    Create a debug log file for troubleshooting.
    
    Sets OPENCODE_LOG_LEVEL=DEBUG and OPENCODE_LOG_FILE.
    """
    log_file = enable_debug_logging()
    console.print(f"[green]Debug logging enabled:[/] {log_file}")
    console.print("\nRun your application now. Errors will be logged to this file.")


@app.command("errors")
def list_known_errors():
    """
    List all known errors in the troubleshooting RAG.
    """
    console.print("\n[bold]Known Errors in Troubleshooting RAG:[/]\n")
    
    # Try to find errors directory
    errors_dirs = [
        Path("RAG/troubleshooting/errors"),
        Path(__file__).parent.parent.parent.parent / "docs/RAG/troubleshooting/errors",
    ]
    
    errors_dir = None
    for d in errors_dirs:
        if d.exists():
            errors_dir = d
            break
    
    if not errors_dir:
        console.print("[red]No troubleshooting RAG found.[/]")
        console.print("Run 'opencode rag create troubleshooting' to create one.")
        return
    
    # List errors
    table = Table(title="Known Errors")
    table.add_column("Error ID", style="cyan")
    table.add_column("Title", style="green")
    table.add_column("Severity", style="yellow")
    
    for error_file in sorted(errors_dir.glob("ERR-*.md")):
        try:
            content = error_file.read_text(encoding="utf-8")
            lines = content.split("\n")
            
            title = ""
            severity = "Medium"
            
            for line in lines:
                if line.startswith("# "):
                    title = line[2:].strip()
                elif "severity" in line.lower() and "critical" in line.lower():
                    severity = "Critical"
                elif "severity" in line.lower() and "high" in line.lower():
                    severity = "High"
                elif "severity" in line.lower() and "low" in line.lower():
                    severity = "Low"
            
            error_id = error_file.stem
            table.add_row(error_id, title[:50], severity)
        except Exception:
            continue
    
    console.print(table)


if __name__ == "__main__":
    app()
