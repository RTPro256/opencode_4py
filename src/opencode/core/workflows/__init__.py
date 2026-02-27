"""
Workflows module for opencode_4py.

This module provides workflow automation patterns inspired by get-shit-done project.
Workflows are multi-step processes that coordinate skills and tools.
"""

from .base import Workflow, WorkflowRegistry, WorkflowResult, WorkflowStep
from .executor import ExecutorWorkflow
from .verifier import VerifierWorkflow

__all__ = [
    "Workflow",
    "WorkflowRegistry",
    "WorkflowResult",
    "WorkflowStep",
    "ExecutorWorkflow",
    "VerifierWorkflow",
]
