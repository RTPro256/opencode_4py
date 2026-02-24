"""
LLM Process Node

Handles AI processing using the existing provider system.
"""

import json
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


@NodeRegistry.register("llm_process")
class LlmProcessNode(BaseNode):
    """
    LLM Process Node - AI processing using the provider system.
    
    This node sends data to an LLM for processing and returns the response.
    It integrates with the existing opencode provider system.
    
    Configuration:
        provider: Provider name (e.g., "ollama", "openai", "anthropic")
        model: Model identifier (e.g., "llama3.2", "gpt-4")
        systemPrompt: System prompt for the LLM
        userPromptTemplate: Template for user prompt (supports {{input}} substitution)
        temperature: Sampling temperature (0.0 - 2.0)
        maxTokens: Maximum tokens to generate
        jsonMode: Whether to request JSON output
    """
    
    _schema = NodeSchema(
        node_type="llm_process",
        display_name="LLM Process",
        description="Process data using an LLM",
        category="processing",
        icon="brain",
        inputs=[
            NodePort(
                name="input",
                data_type=PortDataType.ANY,
                direction=PortDirection.INPUT,
                required=True,
                description="Input data to process",
            ),
            NodePort(
                name="system_prompt",
                data_type=PortDataType.STRING,
                direction=PortDirection.INPUT,
                required=False,
                description="Override system prompt",
            ),
            NodePort(
                name="context",
                data_type=PortDataType.OBJECT,
                direction=PortDirection.INPUT,
                required=False,
                description="Additional context for the LLM",
            ),
        ],
        outputs=[
            NodePort(
                name="output",
                data_type=PortDataType.STRING,
                direction=PortDirection.OUTPUT,
                required=True,
                description="The LLM response text",
            ),
            NodePort(
                name="json",
                data_type=PortDataType.OBJECT,
                direction=PortDirection.OUTPUT,
                required=False,
                description="Parsed JSON response (if jsonMode enabled)",
            ),
            NodePort(
                name="tokens",
                data_type=PortDataType.OBJECT,
                direction=PortDirection.OUTPUT,
                required=False,
                description="Token usage statistics",
            ),
        ],
        config_schema={
            "type": "object",
            "properties": {
                "provider": {
                    "type": "string",
                    "default": "ollama",
                    "description": "LLM provider name",
                },
                "model": {
                    "type": "string",
                    "default": "llama3.2",
                    "description": "Model identifier",
                },
                "systemPrompt": {
                    "type": "string",
                    "default": "You are a helpful assistant.",
                    "description": "System prompt for the LLM",
                },
                "userPromptTemplate": {
                    "type": "string",
                    "default": "{{input}}",
                    "description": "Template for user prompt",
                },
                "temperature": {
                    "type": "number",
                    "default": 0.7,
                    "minimum": 0,
                    "maximum": 2,
                    "description": "Sampling temperature",
                },
                "maxTokens": {
                    "type": "integer",
                    "default": 4096,
                    "description": "Maximum tokens to generate",
                },
                "jsonMode": {
                    "type": "boolean",
                    "default": False,
                    "description": "Request JSON output",
                },
            },
            "required": ["provider", "model"],
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
        """Execute the LLM process node."""
        import time
        start_time = time.time()
        
        try:
            # Get provider
            provider_name = self.config.get("provider", "ollama")
            provider = self._get_provider(provider_name)
            
            if provider is None:
                return ExecutionResult(
                    success=False,
                    error=f"Provider '{provider_name}' not available",
                )
            
            # Build messages
            messages = self._build_messages(inputs)
            
            # Get model parameters
            model = self.config.get("model", "llama3.2")
            temperature = self.config.get("temperature", 0.7)
            max_tokens = self.config.get("maxTokens", 4096)
            json_mode = self.config.get("jsonMode", False)
            
            # Build request options
            kwargs = {
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            
            # Get system prompt
            system_prompt = inputs.get("system_prompt") or self.config.get(
                "systemPrompt", "You are a helpful assistant."
            )
            if system_prompt:
                kwargs["system"] = system_prompt
            
            # Make the LLM request using complete_sync
            response = await provider.complete_sync(
                messages=messages,
                model=model,
                **kwargs
            )
            
            # Extract response content
            output_text = response.content
            
            # Build outputs
            outputs = {
                "output": output_text,
                "tokens": {
                    "prompt": response.usage.input_tokens if response.usage else 0,
                    "completion": response.usage.output_tokens if response.usage else 0,
                    "total": response.usage.total_tokens if response.usage else 0,
                },
            }
            
            # Parse JSON if in json mode
            if json_mode:
                try:
                    outputs["json"] = json.loads(output_text)
                except json.JSONDecodeError:
                    outputs["json"] = None
            
            duration_ms = (time.time() - start_time) * 1000
            return ExecutionResult(
                success=True,
                outputs=outputs,
                duration_ms=duration_ms,
            )
            
        except Exception as e:
            logger.exception(f"LLM process execution failed: {e}")
            return ExecutionResult(
                success=False,
                error=str(e),
            )
    
    def _get_provider(self, provider_name: str):
        """Get the LLM provider instance."""
        try:
            from opencode.core.config import Config
            
            # Load config to get API keys
            config = Config.load()
            
            # Import provider classes directly
            if provider_name == "ollama":
                from opencode.provider.ollama import OllamaProvider
                return OllamaProvider()
            elif provider_name == "openai":
                from opencode.provider.openai import OpenAIProvider
                api_key = config.get_provider_key("openai")
                if not api_key:
                    logger.error("OpenAI API key not configured")
                    return None
                return OpenAIProvider(api_key=api_key)
            elif provider_name == "anthropic":
                from opencode.provider.anthropic import AnthropicProvider
                api_key = config.get_provider_key("anthropic")
                if not api_key:
                    logger.error("Anthropic API key not configured")
                    return None
                return AnthropicProvider(api_key=api_key)
            elif provider_name == "google":
                from opencode.provider.google import GoogleProvider
                api_key = config.get_provider_key("google")
                if not api_key:
                    logger.error("Google API key not configured")
                    return None
                return GoogleProvider(api_key=api_key)
            elif provider_name == "groq":
                from opencode.provider.groq import GroqProvider
                api_key = config.get_provider_key("groq")
                if not api_key:
                    logger.error("Groq API key not configured")
                    return None
                return GroqProvider(api_key=api_key)
            elif provider_name == "mistral":
                from opencode.provider.mistral import MistralProvider
                api_key = config.get_provider_key("mistral")
                if not api_key:
                    logger.error("Mistral API key not configured")
                    return None
                return MistralProvider(api_key=api_key)
            elif provider_name == "lmstudio":
                from opencode.provider.lmstudio import LMStudioProvider
                return LMStudioProvider()
            else:
                logger.warning(f"Unknown provider: {provider_name}")
                return None
        except Exception as e:
            logger.error(f"Failed to load provider {provider_name}: {e}")
            return None
    
    def _build_messages(self, inputs: Dict[str, Any]) -> List:
        """Build the message list for the LLM."""
        from opencode.provider.base import Message, MessageRole
        
        messages = []
        
        # User prompt
        input_data = inputs.get("input", "")
        prompt_template = self.config.get("userPromptTemplate", "{{input}}")
        
        # Substitute template variables
        user_prompt = self._substitute_template(prompt_template, {
            "input": self._format_input(input_data),
            "context": inputs.get("context", {}),
        })
        
        messages.append(Message(
            role=MessageRole.USER,
            content=user_prompt,
        ))
        
        return messages
    
    def _substitute_template(self, template: str, variables: Dict[str, Any]) -> str:
        """Substitute variables in a template string."""
        result = template
        for key, value in variables.items():
            placeholder = "{{" + key + "}}"
            if isinstance(value, (dict, list)):
                value = json.dumps(value, indent=2)
            result = result.replace(placeholder, str(value))
        return result
    
    def _format_input(self, input_data: Any) -> str:
        """Format input data for the prompt."""
        if isinstance(input_data, str):
            return input_data
        elif isinstance(input_data, (dict, list)):
            return json.dumps(input_data, indent=2)
        else:
            return str(input_data)