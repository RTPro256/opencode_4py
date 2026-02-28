"""
CLI commands for OpenCode.
"""

from opencode.cli.commands.run import run_command
from opencode.cli.commands.serve import serve_command
from opencode.cli.commands.auth import auth_app
from opencode.cli.commands.config import config_app
from opencode.cli.commands.rag import app as rag_app
from opencode.cli.commands.debug_cmd import app as debug_app
from opencode.cli.commands.github import app as github_app

# RAG sub-modules for direct access
from opencode.cli.commands.rag_create import app as rag_create_app
from opencode.cli.commands.rag_query import app as rag_query_app
from opencode.cli.commands.rag_manage import app as rag_manage_app
from opencode.cli.commands.rag_validation import app as rag_validation_app
from opencode.cli.commands.rag_share import app as rag_share_app
from opencode.cli.commands.rag_audit import app as rag_audit_app
from opencode.cli.commands.skills import app as skills_app

__all__ = [
    "run_command",
    "serve_command",
    "auth_app",
    "config_app",
    "rag_app",
    "debug_app",
    "github_app",
    "skills_app",
    "rag_create_app",
    "rag_query_app",
    "rag_manage_app",
    "rag_validation_app",
    "rag_share_app",
    "rag_audit_app",
]
