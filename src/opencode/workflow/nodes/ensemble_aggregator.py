"""
Ensemble Aggregator Node

Combines outputs from multiple LLM calls into a single response.
"""

import json
import re
import time
from collections import Counter
from typing import Any, Dict, List, Optional
import logging

from opencode.workflow.node import (
    BaseNode,
    NodePort,
    NodeSchema,
    ExecutionContext,
    ExecutionResult,
    PortDataType,
    PortDirection,
)
from opencode.workflow.registry import NodeRegistry

logger = logging.getLogger(__name__)


@NodeRegistry.register("ensemble_aggregator")
class EnsembleAggregatorNode(BaseNode):
    """
    Ensemble Aggregator Node - Combines multiple model outputs.
    
    This node receives outputs from multiple LLM calls and synthesizes
    them into a single, coherent response using various strategies.
    
    Configuration:
        provider: Provider for aggregator model (default: ollama)
        model: Model to use for aggregation (default: llama3.2)
        aggregation_prompt: Prompt template for aggregation
        aggregation_strategy: How to combine (synthesize, vote, best)
        voting_strategy: Voting method when using vote strategy
    
    Strategies:
        - synthesize: Use an LLM to combine responses into one
        - vote: Select the most common response
        - best: Use an LLM to select the best response
    
    Example:
        node = EnsembleAggregatorNode(
            node_id="aggregator",
            config={
                "provider": "ollama",
                "model": "llama3.2",
                "aggregation_strategy": "synthesize",
            }
        )
    """
    
    _schema = NodeSchema(
        node_type="ensemble_aggregator",
        display_name="Ensemble Aggregator",
        description="Combine multiple model outputs into one",
        category="processing",
        icon="merge",
        inputs=[
            NodePort(
                name="responses",
                data_type=PortDataType.ARRAY,
                direction=PortDirection.INPUT,
                required=False,
                description="List of responses from multiple models",
            ),
            NodePort(
                name="input",
                data_type=PortDataType.STRING,
                direction=PortDirection.INPUT,
                required=False,
                description="Original input prompt",
            ),
            NodePort(
                name="model_0_output",
                data_type=PortDataType.STRING,
                direction=PortDirection.INPUT,
                required=False,
                description="Output from model 0",
            ),
            NodePort(
                name="model_1_output",
                data_type=PortDataType.STRING,
                direction=PortDirection.INPUT,
                required=False,
                description="Output from model 1",
            ),
            NodePort(
                name="model_2_output",
                data_type=PortDataType.STRING,
                direction=PortDirection.INPUT,
                required=False,
                description="Output from model 2",
            ),
        ],
        outputs=[
            NodePort(
                name="output",
                data_type=PortDataType.STRING,
                direction=PortDirection.OUTPUT,
                required=True,
                description="Synthesized response",
            ),
            NodePort(
                name="metadata",
                data_type=PortDataType.OBJECT,
                direction=PortDirection.OUTPUT,
                required=False,
                description="Metadata about aggregation",
            ),
        ],
        config_schema={
            "type": "object",
            "properties": {
                "provider": {
                    "type": "string",
                    "default": "ollama",
                    "description": "Provider for aggregator model",
                },
                "model": {
                    "type": "string",
                    "default": "llama3.2",
                    "description": "Model to use for aggregation",
                },
                "aggregation_prompt": {
                    "type": "string",
                    "default": "Synthesize these responses into the best single answer:",
                    "description": "Prompt for synthesis",
                },
                "aggregation_strategy": {
                    "type": "string",
                    "enum": ["synthesize", "vote", "best"],
                    "default": "synthesize",
                    "description": "How to combine responses",
                },
                "voting_strategy": {
                    "type": "string",
                    "enum": ["majority", "weighted", "consensus"],
                    "default": "majority",
                    "description": "Voting method",
                },
            },
        },
        version="1.0.0",
    )
    
    @classmethod
    def get_schema(cls) -> NodeSchema:
        return cls._schema
    
    async def execute(
        self,
        inputs: Dict[str, Any],
        context: ExecutionContext,
    ) -> ExecutionResult:
        """Execute the ensemble aggregation."""
        start_time = time.time()
        
        try:
            # Collect responses from various input formats
            responses = self._collect_responses(inputs)
            original_input = inputs.get("input", "")
            strategy = self.config.get("aggregation_strategy", "synthesize")
            
            if not responses:
                return ExecutionResult(
                    success=False,
                    error="No responses to aggregate",
                )
            
            logger.info(f"Aggregating {len(responses)} responses using '{strategy}' strategy")
            
            # Execute the appropriate strategy
            if strategy == "synthesize":
                result = await self._synthesize(responses, original_input)
            elif strategy == "vote":
                result = await self._vote(responses)
            elif strategy == "best":
                result = await self._select_best(responses, original_input)
            else:
                # Default to synthesize
                result = await self._synthesize(responses, original_input)
            
            duration_ms = (time.time() - start_time) * 1000
            
            return ExecutionResult(
                success=True,
                outputs={
                    "output": result["output"],
                    "metadata": {
                        "strategy": strategy,
                        "input_count": len(responses),
                        "duration_ms": duration_ms,
                        "voting_strategy": self.config.get("voting_strategy", "majority"),
                    },
                },
                duration_ms=duration_ms,
            )
            
        except Exception as e:
            logger.exception(f"Ensemble aggregation failed: {e}")
            return ExecutionResult(
                success=False,
                error=str(e),
            )
    
    def _collect_responses(self, inputs: Dict[str, Any]) -> List[str]:
        """Collect responses from various input formats."""
        responses = []
        
        # Check for explicit responses array
        if "responses" in inputs and inputs["responses"]:
            responses = inputs["responses"]
            if isinstance(responses, str):
                responses = [responses]
            return responses
        
        # Check for model_N_output format
        for key, value in inputs.items():
            if key.startswith("model_") and key.endswith("_output"):
                if value and isinstance(value, str):
                    responses.append(value)
        
        # Also check for output from connected nodes
        for key, value in inputs.items():
            if key not in ["input", "responses"] and isinstance(value, str) and value.strip():
                if value not in responses:
                    responses.append(value)
        
        return responses
    
    async def _synthesize(self, responses: List[str], original_input: str) -> Dict:
        """Synthesize multiple responses into one using an LLM."""
        from opencode.provider.base import Message, MessageRole
        
        provider_name = self.config.get("provider", "ollama")
        model = self.config.get("model", "llama3.2")
        aggregation_prompt = self.config.get(
            "aggregation_prompt",
            "Synthesize these responses into the best single answer:"
        )
        
        # Build prompt with all responses
        prompt = f"{aggregation_prompt}\n\n"
        if original_input:
            prompt += f"Original question: {original_input}\n\n"
        
        for i, response in enumerate(responses):
            prompt += f"Response {i+1}:\n{response}\n\n"
        
        prompt += "Synthesized answer:"
        
        # Call aggregator model
        provider = self._get_provider(provider_name)
        if provider is None:
            # Fallback: return first response
            logger.warning("Provider not available, returning first response")
            return {"output": responses[0]}
        
        try:
            response = await provider.complete_sync(
                messages=[Message(role=MessageRole.USER, content=prompt)],
                model=model,
                temperature=0.3,  # Lower temperature for aggregation
            )
            return {"output": response.content}
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            return {"output": responses[0]}
    
    async def _vote(self, responses: List[str]) -> Dict:
        """Vote on the best response."""
        voting_strategy = self.config.get("voting_strategy", "majority")
        
        if not responses:
            return {"output": ""}
        
        if voting_strategy == "majority":
            # Simple majority voting - most common response wins
            counter = Counter(responses)
            most_common = counter.most_common(1)[0][0]
            logger.info(f"Majority vote selected: {most_common[:50]}...")
            return {"output": most_common}
        
        elif voting_strategy == "weighted":
            # Weighted voting - could be extended with model confidence scores
            # For now, same as majority
            counter = Counter(responses)
            most_common = counter.most_common(1)[0][0]
            return {"output": most_common}
        
        elif voting_strategy == "consensus":
            # Consensus - only return if all agree
            if len(set(responses)) == 1:
                return {"output": responses[0]}
            else:
                # Fall back to majority if no consensus
                counter = Counter(responses)
                most_common = counter.most_common(1)[0][0]
                return {"output": f"[No consensus] {most_common}"}
        
        # Default to majority
        counter = Counter(responses)
        return {"output": counter.most_common(1)[0][0]}
    
    async def _select_best(self, responses: List[str], original_input: str) -> Dict:
        """Select the best response using an evaluator model."""
        from opencode.provider.base import Message, MessageRole
        
        provider_name = self.config.get("provider", "ollama")
        model = self.config.get("model", "llama3.2")
        
        # Build evaluation prompt
        prompt = f"Select the best response to: {original_input}\n\n"
        for i, response in enumerate(responses):
            # Truncate long responses for the prompt
            truncated = response[:500] + "..." if len(response) > 500 else response
            prompt += f"Response {i+1}: {truncated}\n\n"
        prompt += "Which response number (1, 2, 3, etc.) is best? Just give the number."
        
        provider = self._get_provider(provider_name)
        if provider is None:
            return {"output": responses[0]}
        
        try:
            response = await provider.complete_sync(
                messages=[Message(role=MessageRole.USER, content=prompt)],
                model=model,
                temperature=0.1,
            )
            
            # Parse the response number
            match = re.search(r'\d+', response.content)
            if match:
                idx = int(match.group()) - 1
                if 0 <= idx < len(responses):
                    logger.info(f"Best selection chose response {idx + 1}")
                    return {"output": responses[idx]}
        except Exception as e:
            logger.error(f"Best selection failed: {e}")
        
        return {"output": responses[0]}
    
    def _get_provider(self, provider_name: str):
        """Get the LLM provider instance."""
        try:
            from opencode.core.config import Config
            
            if provider_name == "ollama":
                from opencode.provider.ollama import OllamaProvider
                return OllamaProvider()
            elif provider_name == "lmstudio":
                from opencode.provider.lmstudio import LMStudioProvider
                return LMStudioProvider()
            elif provider_name == "openai":
                from opencode.core.config import Config
                config = Config.load()
                from opencode.provider.openai import OpenAIProvider
                api_key = config.get_api_key("openai")
                if api_key:
                    return OpenAIProvider(api_key=api_key)
            elif provider_name == "anthropic":
                from opencode.core.config import Config
                config = Config.load()
                from opencode.provider.anthropic import AnthropicProvider
                api_key = config.get_api_key("anthropic")
                if api_key:
                    return AnthropicProvider(api_key=api_key)
            else:
                logger.warning(f"Unknown provider: {provider_name}")
                return None
        except Exception as e:
            logger.error(f"Failed to load provider {provider_name}: {e}")
            return None
