"""
Sequential Refinement Workflow Template

Implements a chain of models where each model refines the output of the previous one.
"""

from typing import Any, Dict, List, Optional
import logging

from opencode.workflow.graph import WorkflowGraph, WorkflowNode, WorkflowEdge, WorkflowMetadata

logger = logging.getLogger(__name__)


class SequentialRefinementTemplate:
    """
    Sequential refinement pattern.
    
    Flow: Input → Model1 → Model2 → Model3 → Output
    
    Each model receives the output from the previous model
    and refines/improves it. This is useful for:
    - Code generation → Review → Validation
    - Draft → Edit → Polish
    - Generate → Test → Fix
    
    Example:
        config = MultiModelConfig(
            pattern=MultiModelPattern.SEQUENTIAL,
            models=[
                ModelStepConfig(model="llama3.2", system_prompt="Generate code"),
                ModelStepConfig(model="mistral:7b", system_prompt="Review code"),
            ],
        )
        template = SequentialRefinementTemplate(config)
        graph = template.build()
    """
    
    def __init__(self, config: Any) -> None:
        """
        Initialize the template.
        
        Args:
            config: MultiModelConfig instance
        """
        self.config = config
    
    def build(self) -> WorkflowGraph:
        """
        Build the workflow graph from configuration.
        
        Returns:
            WorkflowGraph ready for execution
        """
        graph = WorkflowGraph(
            metadata=WorkflowMetadata(
                name="Sequential Refinement",
                description="Chain of models refining output",
            )
        )
        
        # Create input node (passes through the user's input)
        graph.add_node(WorkflowNode(
            id="input",
            node_type="data_source",
            config={
                "source_type": "input",
                "description": "User input prompt",
            }
        ))
        
        # Create model nodes in sequence
        prev_node_id = "input"
        model_configs = self.config.models if hasattr(self.config, 'models') else []
        
        for i, model_config in enumerate(model_configs):
            node_id = f"model_{i}"
            
            # Build the prompt template based on position
            if i == 0:
                # First model receives original input
                user_prompt_template = "{{input}}"
            else:
                # Subsequent models receive previous output
                user_prompt_template = "{{" + prev_node_id + ".output}}"
            
            graph.add_node(WorkflowNode(
                id=node_id,
                node_type="llm_process",
                config={
                    "provider": getattr(model_config, 'provider', 'ollama'),
                    "model": getattr(model_config, 'model', 'llama3.2'),
                    "systemPrompt": getattr(model_config, 'system_prompt', 'You are a helpful assistant.'),
                    "temperature": getattr(model_config, 'temperature', 0.7),
                    "maxTokens": getattr(model_config, 'max_tokens', 4096),
                    "userPromptTemplate": user_prompt_template,
                }
            ))
            
            # Connect to previous node
            graph.add_edge(WorkflowEdge(
                source_node_id=prev_node_id,
                source_port="output",
                target_node_id=node_id,
                target_port="input",
            ))
            
            prev_node_id = node_id
        
        # Create output node (final result)
        graph.add_node(WorkflowNode(
            id="output",
            node_type="data_source",
            config={
                "source_type": "output",
                "description": "Final refined output",
            }
        ))
        
        # Connect last model to output
        graph.add_edge(WorkflowEdge(
            source_node_id=prev_node_id,
            source_port="output",
            target_node_id="output",
            target_port="input",
        ))
        
        logger.info(f"Built sequential refinement workflow with {len(model_configs)} models")
        
        return graph
