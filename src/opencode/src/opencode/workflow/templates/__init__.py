"""
Built-in workflow templates for multi-model patterns.

This module provides pre-built workflow templates that can be used
to quickly set up multi-model execution patterns.
"""

from opencode.workflow.templates.sequential import SequentialRefinementTemplate
from opencode.workflow.templates.ensemble import EnsembleTemplate
from opencode.workflow.templates.voting import VotingTemplate

__all__ = [
    "SequentialRefinementTemplate",
    "EnsembleTemplate",
    "VotingTemplate",
    "get_template",
    "BUILTIN_TEMPLATES",
]

BUILTIN_TEMPLATES = {
    "sequential": SequentialRefinementTemplate,
    "sequential_refinement": SequentialRefinementTemplate,
    "ensemble": EnsembleTemplate,
    "voting": VotingTemplate,
}


def get_template(name: str, config) -> "WorkflowGraph":
    """
    Get a workflow template by name with configuration.
    
    Args:
        name: Template name (sequential, ensemble, voting)
        config: MultiModelConfig instance
        
    Returns:
        WorkflowGraph ready for execution
        
    Raises:
        ValueError: If template name is unknown
    """
    template_class = BUILTIN_TEMPLATES.get(name)
    if template_class:
        return template_class(config).build()
    raise ValueError(f"Unknown template: {name}. Available: {list(BUILTIN_TEMPLATES.keys())}")
