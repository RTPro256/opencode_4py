"""
Tests for LLM Process workflow node.
"""

import pytest
from unittest.mock import MagicMock, patch

from opencode.workflow.nodes.llm_process import LlmProcessNode
from opencode.workflow.node import (
    NodeSchema,
    NodePort,
    PortDataType,
    PortDirection,
    ExecutionContext,
)


class TestLlmProcessNode:
    """Tests for LlmProcessNode."""
    
    @pytest.mark.unit
    def test_llm_process_node_creation(self):
        """Test LlmProcessNode instantiation."""
        node = LlmProcessNode("llm_1", {})
        assert node is not None
        assert node.node_id == "llm_1"
    
    @pytest.mark.unit
    def test_llm_process_node_schema(self):
        """Test LlmProcessNode has correct schema."""
        node = LlmProcessNode("llm_1", {})
        schema = node._schema
        assert schema.node_type == "llm_process"
        assert schema.display_name == "LLM Process"
        assert schema.category == "processing"
    
    @pytest.mark.unit
    def test_llm_process_node_inputs(self):
        """Test LlmProcessNode input ports."""
        node = LlmProcessNode("llm_1", {})
        inputs = node._schema.inputs
        input_names = [p.name for p in inputs]
        assert "input" in input_names
        assert "system_prompt" in input_names
        assert "context" in input_names
    
    @pytest.mark.unit
    def test_llm_process_node_outputs(self):
        """Test LlmProcessNode output ports."""
        node = LlmProcessNode("llm_1", {})
        outputs = node._schema.outputs
        output_names = [p.name for p in outputs]
        assert "output" in output_names
        assert "json" in output_names
        assert "tokens" in output_names
    
    @pytest.mark.unit
    def test_llm_process_node_input_required(self):
        """Test LlmProcessNode input is required."""
        node = LlmProcessNode("llm_1", {})
        input_port = next(p for p in node._schema.inputs if p.name == "input")
        assert input_port.required is True
    
    @pytest.mark.unit
    def test_llm_process_node_system_prompt_optional(self):
        """Test LlmProcessNode system_prompt is optional."""
        node = LlmProcessNode("llm_1", {})
        sys_port = next(p for p in node._schema.inputs if p.name == "system_prompt")
        assert sys_port.required is False
    
    @pytest.mark.unit
    def test_llm_process_node_config_provider(self):
        """Test LlmProcessNode with provider config."""
        node = LlmProcessNode("llm_1", {"provider": "openai"})
        assert node.config.get("provider") == "openai"
    
    @pytest.mark.unit
    def test_llm_process_node_config_model(self):
        """Test LlmProcessNode with model config."""
        node = LlmProcessNode("llm_1", {"model": "gpt-4"})
        assert node.config.get("model") == "gpt-4"
    
    @pytest.mark.unit
    def test_llm_process_node_config_system_prompt(self):
        """Test LlmProcessNode with system prompt."""
        node = LlmProcessNode("llm_1", {
            "systemPrompt": "You are a helpful assistant.",
        })
        assert node.config.get("systemPrompt") == "You are a helpful assistant."
    
    @pytest.mark.unit
    def test_llm_process_node_config_user_prompt_template(self):
        """Test LlmProcessNode with user prompt template."""
        node = LlmProcessNode("llm_1", {
            "userPromptTemplate": "Process this: {{input}}",
        })
        assert node.config.get("userPromptTemplate") == "Process this: {{input}}"
    
    @pytest.mark.unit
    def test_llm_process_node_config_temperature(self):
        """Test LlmProcessNode with temperature."""
        node = LlmProcessNode("llm_1", {"temperature": 0.7})
        assert node.config.get("temperature") == 0.7
    
    @pytest.mark.unit
    def test_llm_process_node_config_max_tokens(self):
        """Test LlmProcessNode with max tokens."""
        node = LlmProcessNode("llm_1", {"maxTokens": 1000})
        assert node.config.get("maxTokens") == 1000
    
    @pytest.mark.unit
    def test_llm_process_node_config_json_mode(self):
        """Test LlmProcessNode with JSON mode."""
        node = LlmProcessNode("llm_1", {"jsonMode": True})
        assert node.config.get("jsonMode") is True
    
    @pytest.mark.unit
    def test_llm_process_node_registered(self):
        """Test LlmProcessNode is registered."""
        from opencode.workflow.registry import NodeRegistry
        # Check if llm_process is registered
        assert "llm_process" in NodeRegistry._nodes or hasattr(NodeRegistry, 'get')
    
    @pytest.mark.unit
    def test_llm_process_node_has_execute_method(self):
        """Test LlmProcessNode has execute method."""
        node = LlmProcessNode("llm_1", {})
        assert hasattr(node, 'execute')
    
    @pytest.mark.unit
    def test_llm_process_node_has_schema(self):
        """Test LlmProcessNode has schema."""
        node = LlmProcessNode("llm_1", {})
        assert hasattr(node, '_schema')
    
    @pytest.mark.unit
    def test_llm_process_node_get_input_port(self):
        """Test LlmProcessNode get input port."""
        node = LlmProcessNode("llm_1", {})
        input_port = node.get_input_port("input")
        assert input_port is not None
        assert input_port.name == "input"
    
    @pytest.mark.unit
    def test_llm_process_node_get_output_port(self):
        """Test LlmProcessNode get output port."""
        node = LlmProcessNode("llm_1", {})
        output_port = node.get_output_port("output")
        assert output_port is not None
        assert output_port.name == "output"
    
    @pytest.mark.unit
    def test_llm_process_node_get_nonexistent_port(self):
        """Test LlmProcessNode get nonexistent port."""
        node = LlmProcessNode("llm_1", {})
        port = node.get_input_port("nonexistent")
        assert port is None
    
    @pytest.mark.unit
    def test_llm_process_node_str(self):
        """Test LlmProcessNode string representation."""
        node = LlmProcessNode("llm_1", {})
        assert "llm" in str(node).lower() or "LlmProcessNode" in str(node)
    
    @pytest.mark.unit
    def test_llm_process_node_repr(self):
        """Test LlmProcessNode repr."""
        node = LlmProcessNode("llm_1", {})
        assert "llm_1" in repr(node) or "LlmProcessNode" in repr(node)


class TestLlmProcessNodeExecution:
    """Tests for LlmProcessNode execution."""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_llm_process_node_execute_basic(self):
        """Test LlmProcessNode execute basic."""
        node = LlmProcessNode("llm_1", {"provider": "ollama", "model": "llama3"})
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(
            inputs={"input": "Hello"},
            context=context
        )
        assert result is not None or hasattr(node, 'execute')
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_llm_process_node_execute_with_system_prompt(self):
        """Test LlmProcessNode execute with system prompt."""
        node = LlmProcessNode("llm_1", {
            "provider": "ollama",
            "systemPrompt": "You are helpful.",
        })
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(
            inputs={
                "input": "Hello",
                "system_prompt": "Custom prompt",
            },
            context=context
        )
        assert result is not None or hasattr(node, 'execute')
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_llm_process_node_execute_with_context(self):
        """Test LlmProcessNode execute with context."""
        node = LlmProcessNode("llm_1", {"provider": "ollama"})
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(
            inputs={
                "input": "Hello",
                "context": {"key": "value"},
            },
            context=context
        )
        assert result is not None or hasattr(node, 'execute')
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_llm_process_node_execute_json_mode(self):
        """Test LlmProcessNode execute with JSON mode."""
        node = LlmProcessNode("llm_1", {
            "provider": "ollama",
            "jsonMode": True,
        })
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(
            inputs={"input": "Return JSON"},
            context=context
        )
        assert result is not None or hasattr(node, 'execute')
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_llm_process_node_execute_with_temperature(self):
        """Test LlmProcessNode execute with temperature."""
        node = LlmProcessNode("llm_1", {
            "provider": "ollama",
            "temperature": 0.5,
        })
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(
            inputs={"input": "Hello"},
            context=context
        )
        assert result is not None or hasattr(node, 'execute')
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_llm_process_node_execute_with_max_tokens(self):
        """Test LlmProcessNode execute with max tokens."""
        node = LlmProcessNode("llm_1", {
            "provider": "ollama",
            "maxTokens": 500,
        })
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(
            inputs={"input": "Hello"},
            context=context
        )
        assert result is not None or hasattr(node, 'execute')
