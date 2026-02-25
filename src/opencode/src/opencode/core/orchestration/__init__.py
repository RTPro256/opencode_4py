"""
Orchestration Module

Provides multi-agent orchestration and routing capabilities.
"""

from opencode.core.orchestration.agent import Agent, AgentDescription
from opencode.core.orchestration.registry import AgentRegistry
from opencode.core.orchestration.router import OrchestrationRouter, IntentClassifier
from opencode.core.orchestration.coordinator import Coordinator

__all__ = [
    "Agent",
    "AgentDescription",
    "AgentRegistry",
    "OrchestrationRouter",
    "IntentClassifier",
    "Coordinator",
]
