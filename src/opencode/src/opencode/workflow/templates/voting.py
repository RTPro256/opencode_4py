"""
Voting Workflow Template

Implements multiple models voting on the best answer.
"""

from typing import Any, Dict, List, Optional
import logging

from opencode.workflow.graph import WorkflowGraph, WorkflowNode, WorkflowEdge, WorkflowMetadata

logger = logging.getLogger(__name__)


class VotingTemplate:
    """
    Voting pattern.
    
    Flow:
        Input ─┬→ Model1 ─┐
               ├→ Model2 ─┼→ Voter → Output
               └→ Model3 ─┘
    
    Multiple models process the same input and then vote
    on the best answer. This is useful for:
    - Consensus-based decisions
    - Reducing individual model biases
    - Selecting the best from multiple options
    
    Voting strategies:
    - majority: Select the most common answer
    - weighted: Weight votes by model confidence
    - consensus: Only output if models agree
    
    Example:
        config = MultiModelConfig(
            pattern=MultiModelPattern.VOTING,
            models=[
                ModelStepConfig(model="llama3.2"),
                ModelStepConfig(model="mistral:7b"),
                ModelStepConfig(model="codellama:7b"),
            ],
            voting_strategy="majority",
        )
        template = VotingTemplate(config)
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
                name="Voting",
                description="Multiple models voting on best answer",
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
            
            graph.add_node(WorkflowNode(
                id=node_id,
                node_type="llm_process",
                config={
                    "provider": getattr(model_config, 'provider', 'ollama'),
                    "model": getattr(model_config, 'model', 'llama3.2'),
                    "systemPrompt": getattr(model_config, 'system_prompt', 'You are a helpful assistant.'),
                    "temperature": getattr(model_config, 'temperature', 0.7),
                    "maxTokens": getattr(model_config, 'max_tokens', 4096),
                    "userPromptTemplate": "{{input}}",  # All models receive same input
                }
            ))
            
            # Connect input to each model (parallel execution)
            graph.add_edge(WorkflowEdge(
                source_node_id="input",
                source_port="output",
                target_node_id=node_id,
                target_port="input",
            ))
        
        # Get voting strategy
        voting_strategy = getattr(self.config, 'voting_strategy', 'majority')
        
        # Create voter/aggregator node
        graph.add_node(WorkflowNode(
            id="voter",
            node_type="ensemble_aggregator",
            config={
                "provider": "ollama",
                "model": getattr(model_configs[0], 'model', 'llama3.2') if model_configs else "llama3.2",
                "aggregation_prompt": "Vote on the best response:",
                "aggregation_strategy": "vote",  # Use voting strategy
                "voting_strategy": voting_strategy,
            }
        ))
        
        # Connect all models to voter
        for node_id in model_nodes:
            graph.add_edge(WorkflowEdge(
                source_node_id=node_id,
                source_port="output",
                target_node_id="voter",
                target_port="input",
            ))
        
        # Create output node
        graph.add_node(WorkflowNode(
            id="output",
            node_type="data_source",
            config={
                "source_type": "output",
                "description": "Voted best output",
            }
        ))
        
        # Connect voter to output
        graph.add_edge(WorkflowEdge(
            source_node_id="voter",
            source_port="output",
            target_node_id="output",
            target_port="input",
        ))
        
        logger.info(f"Built voting workflow with {len(model_configs)} models using '{voting_strategy}' strategy")
        
        return graph
