"""
RAG CLI Commands for Privacy-First RAG.

Provides command-line interface for RAG management.
This module re-exports commands from focused submodules.

Commands are organized into the following modules:
- rag_create: Commands for creating RAG indexes
- rag_query: Commands for querying RAG indexes
- rag_manage: Commands for managing RAG indexes (add, status, clear, stats)
- rag_validation: Commands for validating content (mark-false, list-false, regenerate, validate)
- rag_share: Commands for sharing RAG indexes (get, share, list-remote, merge)
- rag_audit: Commands for audit logs
"""

import typer
from rich.console import Console

# Import sub-apps
from opencode.cli.commands.rag_create import app as create_app
from opencode.cli.commands.rag_query import app as query_app
from opencode.cli.commands.rag_manage import app as manage_app
from opencode.cli.commands.rag_validation import app as validation_app
from opencode.cli.commands.rag_share import app as share_app
from opencode.cli.commands.rag_audit import app as audit_app

app = typer.Typer(name="rag", help="RAG management commands")
console = Console()

# Register all sub-apps
app.add_typer(create_app, name="create")
app.add_typer(query_app, name="query")
app.add_typer(manage_app, name="manage")
app.add_typer(validation_app, name="validation")
app.add_typer(share_app, name="share")
app.add_typer(audit_app, name="audit")

# Also add commands directly for convenience (common commands)
# These are registered directly on the main app for easier access
from opencode.cli.commands.rag_create import create_rag
from opencode.cli.commands.rag_query import query_rag
from opencode.cli.commands.rag_manage import (
    add_to_rag,
    rag_status,
    clear_rag,
    rag_stats,
)
from opencode.cli.commands.rag_validation import (
    mark_false_content,
    list_false_content,
    regenerate_rag,
    validate_content,
)
from opencode.cli.commands.rag_share import (
    get_community_rag,
    share_rag,
    list_remote_rags,
    merge_rags,
)
from opencode.cli.commands.rag_audit import rag_audit

# Register commands directly on main app for convenience
app.command("create")(create_rag)
app.command("query")(query_rag)
app.command("add")(add_to_rag)
app.command("status")(rag_status)
app.command("clear")(clear_rag)
app.command("stats")(rag_stats)
app.command("mark-false")(mark_false_content)
app.command("list-false")(list_false_content)
app.command("regenerate")(regenerate_rag)
app.command("validate")(validate_content)
app.command("get")(get_community_rag)
app.command("share")(share_rag)
app.command("list-remote")(list_remote_rags)
app.command("merge")(merge_rags)
app.command("audit")(rag_audit)


if __name__ == "__main__":
    app()
