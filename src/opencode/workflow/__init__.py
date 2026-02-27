"""
Workflow Engine Module

This module provides a visual workflow automation platform inspired by agentic-signal.
It enables node-based visual programming with drag-and-drop interface capabilities.

Key Components:
- WorkflowEngine: Orchestrates workflow execution
- BaseNode: Abstract base class for all node types
- NodeRegistry: Registry for node type discovery
- WorkflowGraph: DAG representation of workflows
"""

from opencode.workflow.node import BaseNode, NodePort, NodeSchema
from opencode.workflow.engine import WorkflowEngine
from opencode.workflow.graph import WorkflowGraph, WorkflowEdge, WorkflowNode
from opencode.workflow.state import WorkflowState, ExecutionStatus
from opencode.workflow.registry import NodeRegistry

__all__ = [
    "BaseNode",
    "NodePort",
    "NodeSchema",
    "WorkflowEngine",
    "WorkflowGraph",
    "WorkflowEdge",
    "WorkflowNode",
    "WorkflowState",
    "ExecutionStatus",
    "NodeRegistry",
]
