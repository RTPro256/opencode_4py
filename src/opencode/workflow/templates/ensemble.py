"""
Ensemble Workflow Template

Implements parallel model execution with aggregation of results.
"""

from typing import Any, Dict, List, Optional
import logging

from opencode.workflow.graph import WorkflowGraph, WorkflowNode, WorkflowEdge, WorkflowMetadata

logger = logging.getLogger(__name__)


class EnsembleTemplate:
    """
    Ensemble pattern.
    
    Flow:
        Input ─┬→ Model1 ─┐
               ├→ Model2 ─┼→ Aggregator → Output
               └→ Model3 ─┘
    
    Multiple models process the same input in parallel,
    then an aggregator model synthesizes the results.
    
    This is useful for:
    - Getting multiple perspectives on the same problem
    - Reducing individual model biases
    - Improving answer quality through synthesis
    
    Example:
        config = MultiModelConfig(
            pattern=MultiModelPattern.ENSEMBLE,
            models=[
                ModelStepConfig(model="llama3.2"),
                ModelStepConfig(model="mistral:7b"),
                ModelStepConfig(model="codellama:7b"),
            ],
            aggregator_model="llama3.2:70b",
        )
        template = EnsembleTemplate(config)
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
                name="Ensemble",
                description="Multiple models with aggregation",
            )
        )
        
        # Create input node
        graph.add_node(WorkflowNode(
            id="input",
            node_type="data_source",
            config={
                "source_type": "input",
                "description": "User input prompt",
            }
        ))
        
        # Create parallel model nodes
        model_nodes = []
        model_configs = self.config.models if hasattr(self.config, 'models') else []
        
        for i, model_config in enumerate(model_configs):
            node_id = f"model_{i}"
            model_nodes.append(node_id)
            
            # Build node config with GPU support
            node_config = {
                "provider": getattr(model_config, 'provider', 'ollama'),
                "model": getattr(model_config, 'model', 'llama3.2'),
                "systemPrompt": getattr(model_config, 'system_prompt', 'You are a helpful assistant.'),
                "temperature": getattr(model_config, 'temperature', 0.7),
                "maxTokens": getattr(model_config, 'max_tokens', 4096),
                "userPromptTemplate": "{{input}}",  # All models receive same input
            }
            
            # Add GPU configuration if specified
            gpu_id = getattr(model_config, 'gpu_id', None)
            if gpu_id is not None:
                node_config["gpu_id"] = gpu_id
            
            vram_required = getattr(model_config, 'vram_required_gb', None)
            if vram_required is not None:
                node_config["vram_required_gb"] = vram_required
            
            exclusive_gpu = getattr(model_config, 'exclusive_gpu', False)
            if exclusive_gpu:
                node_config["exclusive_gpu"] = True
            
            graph.add_node(WorkflowNode(
                id=node_id,
                node_type="llm_process",
                config=node_config
            ))
            
            # Connect input to each model (parallel execution)
            graph.add_edge(WorkflowEdge(
                source_node_id="input",
                source_port="output",
                target_node_id=node_id,
                target_port="input",
            ))
        
        # Determine aggregator model
        aggregator_model = getattr(self.config, 'aggregator_model', None)
        if aggregator_model is None and model_configs:
            # Use first model as default aggregator
            aggregator_model = getattr(model_configs[0], 'model', 'llama3.2')
        
        # Create aggregator node
        graph.add_node(WorkflowNode(
            id="aggregator",
            node_type="ensemble_aggregator",
            config={
                "provider": "ollama",
                "model": aggregator_model,
                "aggregation_prompt": "Synthesize these responses into a single best answer:",
                "aggregation_strategy": "synthesize",
            }
        ))
        
        # Connect all models to aggregator
        for node_id in model_nodes:
            graph.add_edge(WorkflowEdge(
                source_node_id=node_id,
                source_port="output",
                target_node_id="aggregator",
                target_port="input",
            ))
        
        # Create output node
        graph.add_node(WorkflowNode(
            id="output",
            node_type="data_source",
            config={
                "source_type": "output",
                "description": "Synthesized output",
            }
        ))
        
        # Connect aggregator to output
        graph.add_edge(WorkflowEdge(
            source_node_id="aggregator",
            source_port="output",
            target_node_id="output",
            target_port="input",
        ))
        
        logger.info(f"Built ensemble workflow with {len(model_configs)} parallel models")
        
        return graph
