"""
Router Module

This module provides intelligent LLM routing capabilities inspired by SmarterRouter.
It enables automatic model selection based on prompt analysis, complexity assessment,
and quality/speed preferences.

Key Components:
- RouterEngine: Core routing engine
- ModelProfiler: Model performance profiling
- VRAMMonitor: GPU memory monitoring
- SemanticCache: Caching for routing decisions
"""

from opencode.router.engine import RouterEngine, RoutingResult
from opencode.router.profiler import ModelProfiler, ModelProfile
from opencode.router.config import RouterConfig
from opencode.router.skills import SkillClassifier

__all__ = [
    "RouterEngine",
    "RoutingResult",
    "ModelProfiler",
    "ModelProfile",
    "RouterConfig",
    "SkillClassifier",
]
