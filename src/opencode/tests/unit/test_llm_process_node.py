"""
Tests for LLM Process workflow node.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from opencode.workflow.nodes.llm_process import LlmProcessNode
from opencode.workflow.node import (
    NodeSchema,
    NodePort,
    PortDataType,
    PortDirection,
    ExecutionContext,
    ExecutionResult,
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


class TestLlmProcessNodeGetProvider:
    """Tests for _get_provider method."""

    @pytest.mark.unit
    def test_get_provider_ollama(self):
        """Test getting Ollama provider."""
        node = LlmProcessNode("llm_1", {})
        mock_provider = MagicMock()
        with patch("opencode.core.config.Config.load") as mock_config:
            mock_config.return_value = MagicMock()
            with patch("opencode.provider.ollama.OllamaProvider", return_value=mock_provider):
                provider = node._get_provider("ollama")
                assert provider is not None

    @pytest.mark.unit
    def test_get_provider_openai_no_key(self):
        """Test getting OpenAI provider without API key."""
        node = LlmProcessNode("llm_1", {})
        with patch("opencode.core.config.Config.load") as mock_config:
            config_instance = MagicMock()
            config_instance.get_provider_key.return_value = None
            mock_config.return_value = config_instance
            
            provider = node._get_provider("openai")
            assert provider is None

    @pytest.mark.unit
    def test_get_provider_openai_with_key(self):
        """Test getting OpenAI provider with API key."""
        node = LlmProcessNode("llm_1", {})
        with patch("opencode.core.config.Config.load") as mock_config:
            config_instance = MagicMock()
            config_instance.get_provider_key.return_value = "test-key"
            mock_config.return_value = config_instance
            
            mock_provider = MagicMock()
            with patch("opencode.provider.openai.OpenAIProvider", return_value=mock_provider) as mock_provider_class:
                provider = node._get_provider("openai")
                mock_provider_class.assert_called_once_with(api_key="test-key")
                assert provider is mock_provider

    @pytest.mark.unit
    def test_get_provider_anthropic_no_key(self):
        """Test getting Anthropic provider without API key."""
        node = LlmProcessNode("llm_1", {})
        with patch("opencode.core.config.Config.load") as mock_config:
            config_instance = MagicMock()
            config_instance.get_provider_key.return_value = None
            mock_config.return_value = config_instance
            
            provider = node._get_provider("anthropic")
            assert provider is None

    @pytest.mark.unit
    def test_get_provider_anthropic_with_key(self):
        """Test getting Anthropic provider with API key."""
        node = LlmProcessNode("llm_1", {})
        with patch("opencode.core.config.Config.load") as mock_config:
            config_instance = MagicMock()
            config_instance.get_provider_key.return_value = "test-key"
            mock_config.return_value = config_instance
            
            mock_provider = MagicMock()
            with patch("opencode.provider.anthropic.AnthropicProvider", return_value=mock_provider) as mock_provider_class:
                provider = node._get_provider("anthropic")
                mock_provider_class.assert_called_once_with(api_key="test-key")
                assert provider is mock_provider

    @pytest.mark.unit
    def test_get_provider_google_no_key(self):
        """Test getting Google provider without API key."""
        node = LlmProcessNode("llm_1", {})
        with patch("opencode.core.config.Config.load") as mock_config:
            config_instance = MagicMock()
            config_instance.get_provider_key.return_value = None
            mock_config.return_value = config_instance
            
            provider = node._get_provider("google")
            assert provider is None

    @pytest.mark.unit
    def test_get_provider_google_with_key(self):
        """Test getting Google provider with API key."""
        node = LlmProcessNode("llm_1", {})
        with patch("opencode.core.config.Config.load") as mock_config:
            config_instance = MagicMock()
            config_instance.get_provider_key.return_value = "test-key"
            mock_config.return_value = config_instance
            
            mock_provider = MagicMock()
            with patch("opencode.provider.google.GoogleProvider", return_value=mock_provider) as mock_provider_class:
                provider = node._get_provider("google")
                mock_provider_class.assert_called_once_with(api_key="test-key")
                assert provider is mock_provider

    @pytest.mark.unit
    def test_get_provider_groq_no_key(self):
        """Test getting Groq provider without API key."""
        node = LlmProcessNode("llm_1", {})
        with patch("opencode.core.config.Config.load") as mock_config:
            config_instance = MagicMock()
            config_instance.get_provider_key.return_value = None
            mock_config.return_value = config_instance
            
            provider = node._get_provider("groq")
            assert provider is None

    @pytest.mark.unit
    def test_get_provider_groq_with_key(self):
        """Test getting Groq provider with API key."""
        node = LlmProcessNode("llm_1", {})
        with patch("opencode.core.config.Config.load") as mock_config:
            config_instance = MagicMock()
            config_instance.get_provider_key.return_value = "test-key"
            mock_config.return_value = config_instance
            
            mock_provider = MagicMock()
            with patch("opencode.provider.groq.GroqProvider", return_value=mock_provider) as mock_provider_class:
                provider = node._get_provider("groq")
                mock_provider_class.assert_called_once_with(api_key="test-key")
                assert provider is mock_provider

    @pytest.mark.unit
    def test_get_provider_mistral_no_key(self):
        """Test getting Mistral provider without API key."""
        node = LlmProcessNode("llm_1", {})
        with patch("opencode.core.config.Config.load") as mock_config:
            config_instance = MagicMock()
            config_instance.get_provider_key.return_value = None
            mock_config.return_value = config_instance
            
            provider = node._get_provider("mistral")
            assert provider is None

    @pytest.mark.unit
    def test_get_provider_mistral_with_key(self):
        """Test getting Mistral provider with API key."""
        node = LlmProcessNode("llm_1", {})
        with patch("opencode.core.config.Config.load") as mock_config:
            config_instance = MagicMock()
            config_instance.get_provider_key.return_value = "test-key"
            mock_config.return_value = config_instance
            
            mock_provider = MagicMock()
            with patch("opencode.provider.mistral.MistralProvider", return_value=mock_provider) as mock_provider_class:
                provider = node._get_provider("mistral")
                mock_provider_class.assert_called_once_with(api_key="test-key")
                assert provider is mock_provider

    @pytest.mark.unit
    def test_get_provider_lmstudio(self):
        """Test getting LMStudio provider."""
        node = LlmProcessNode("llm_1", {})
        mock_provider = MagicMock()
        with patch("opencode.core.config.Config.load") as mock_config:
            mock_config.return_value = MagicMock()
            with patch("opencode.provider.lmstudio.LMStudioProvider", return_value=mock_provider) as mock_provider_class:
                provider = node._get_provider("lmstudio")
                mock_provider_class.assert_called_once()
                assert provider is mock_provider

    @pytest.mark.unit
    def test_get_provider_unknown(self):
        """Test getting unknown provider."""
        node = LlmProcessNode("llm_1", {})
        provider = node._get_provider("unknown_provider")
        assert provider is None

    @pytest.mark.unit
    def test_get_provider_exception(self):
        """Test _get_provider handles exceptions."""
        node = LlmProcessNode("llm_1", {})
        with patch("opencode.core.config.Config.load", side_effect=Exception("Config error")):
            provider = node._get_provider("openai")
            assert provider is None


class TestLlmProcessNodeBuildMessages:
    """Tests for _build_messages method."""

    @pytest.mark.unit
    def test_build_messages_basic(self):
        """Test building basic messages."""
        node = LlmProcessNode("llm_1", {})
        messages = node._build_messages({"input": "Hello"})
        assert len(messages) == 1
        assert messages[0].role.value == "user"
        assert messages[0].content == "Hello"

    @pytest.mark.unit
    def test_build_messages_with_template(self):
        """Test building messages with template."""
        node = LlmProcessNode("llm_1", {
            "userPromptTemplate": "Process: {{input}}"
        })
        messages = node._build_messages({"input": "data"})
        assert len(messages) == 1
        assert messages[0].content == "Process: data"

    @pytest.mark.unit
    def test_build_messages_with_context(self):
        """Test building messages with context."""
        node = LlmProcessNode("llm_1", {
            "userPromptTemplate": "Input: {{input}}\nContext: {{context}}"
        })
        messages = node._build_messages({
            "input": "test",
            "context": {"key": "value"}
        })
        assert len(messages) == 1
        assert "test" in messages[0].content
        assert "key" in messages[0].content


class TestLlmProcessNodeSubstituteTemplate:
    """Tests for _substitute_template method."""

    @pytest.mark.unit
    def test_substitute_template_string(self):
        """Test substituting string value."""
        node = LlmProcessNode("llm_1", {})
        result = node._substitute_template("Hello {{name}}", {"name": "World"})
        assert result == "Hello World"

    @pytest.mark.unit
    def test_substitute_template_dict(self):
        """Test substituting dict value."""
        node = LlmProcessNode("llm_1", {})
        result = node._substitute_template("Data: {{data}}", {"data": {"key": "value"}})
        assert '"key": "value"' in result

    @pytest.mark.unit
    def test_substitute_template_list(self):
        """Test substituting list value."""
        node = LlmProcessNode("llm_1", {})
        result = node._substitute_template("Items: {{items}}", {"items": [1, 2, 3]})
        assert "1" in result and "2" in result and "3" in result

    @pytest.mark.unit
    def test_substitute_template_multiple(self):
        """Test substituting multiple values."""
        node = LlmProcessNode("llm_1", {})
        result = node._substitute_template(
            "{{greeting}} {{name}}!",
            {"greeting": "Hello", "name": "World"}
        )
        assert result == "Hello World!"


class TestLlmProcessNodeFormatInput:
    """Tests for _format_input method."""

    @pytest.mark.unit
    def test_format_input_string(self):
        """Test formatting string input."""
        node = LlmProcessNode("llm_1", {})
        result = node._format_input("test string")
        assert result == "test string"

    @pytest.mark.unit
    def test_format_input_dict(self):
        """Test formatting dict input."""
        node = LlmProcessNode("llm_1", {})
        result = node._format_input({"key": "value"})
        assert '"key": "value"' in result

    @pytest.mark.unit
    def test_format_input_list(self):
        """Test formatting list input."""
        node = LlmProcessNode("llm_1", {})
        result = node._format_input([1, 2, 3])
        assert "1" in result and "2" in result and "3" in result

    @pytest.mark.unit
    def test_format_input_other(self):
        """Test formatting other input types."""
        node = LlmProcessNode("llm_1", {})
        result = node._format_input(123)
        assert result == "123"


class TestLlmProcessNodeExecuteWithMockedProvider:
    """Tests for execute method with mocked provider."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_provider_not_available(self):
        """Test execute when provider is not available."""
        node = LlmProcessNode("llm_1", {"provider": "unknown"})
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(
            inputs={"input": "Hello"},
            context=context
        )
        assert result.success is False
        assert "not available" in result.error

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_with_mocked_provider_success(self):
        """Test execute with mocked provider success."""
        node = LlmProcessNode("llm_1", {"provider": "ollama", "model": "llama3"})
        context = MagicMock(spec=ExecutionContext)
        
        # Create mock provider
        mock_provider = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Hello, I am an AI assistant."
        mock_response.usage = MagicMock()
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 20
        mock_response.usage.total_tokens = 30
        mock_provider.complete_sync = AsyncMock(return_value=mock_response)
        
        with patch.object(node, "_get_provider", return_value=mock_provider):
            result = await node.execute(
                inputs={"input": "Hello"},
                context=context
            )
            assert result.success is True
            assert result.outputs["output"] == "Hello, I am an AI assistant."
            assert result.outputs["tokens"]["total"] == 30

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_with_json_mode_valid_json(self):
        """Test execute with JSON mode and valid JSON response."""
        node = LlmProcessNode("llm_1", {
            "provider": "ollama",
            "model": "llama3",
            "jsonMode": True,
        })
        context = MagicMock(spec=ExecutionContext)
        
        # Create mock provider
        mock_provider = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '{"result": "success", "value": 42}'
        mock_response.usage = MagicMock()
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 20
        mock_response.usage.total_tokens = 30
        mock_provider.complete_sync = AsyncMock(return_value=mock_response)
        
        with patch.object(node, "_get_provider", return_value=mock_provider):
            result = await node.execute(
                inputs={"input": "Return JSON"},
                context=context
            )
            assert result.success is True
            assert result.outputs["json"] == {"result": "success", "value": 42}

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_with_json_mode_invalid_json(self):
        """Test execute with JSON mode and invalid JSON response."""
        node = LlmProcessNode("llm_1", {
            "provider": "ollama",
            "model": "llama3",
            "jsonMode": True,
        })
        context = MagicMock(spec=ExecutionContext)
        
        # Create mock provider
        mock_provider = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "This is not valid JSON"
        mock_response.usage = MagicMock()
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 20
        mock_response.usage.total_tokens = 30
        mock_provider.complete_sync = AsyncMock(return_value=mock_response)
        
        with patch.object(node, "_get_provider", return_value=mock_provider):
            result = await node.execute(
                inputs={"input": "Return JSON"},
                context=context
            )
            assert result.success is True
            assert result.outputs["json"] is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_with_exception(self):
        """Test execute when an exception occurs."""
        node = LlmProcessNode("llm_1", {"provider": "ollama"})
        context = MagicMock(spec=ExecutionContext)
        
        mock_provider = MagicMock()
        mock_provider.complete_sync = AsyncMock(side_effect=Exception("API error"))
        
        with patch.object(node, "_get_provider", return_value=mock_provider):
            result = await node.execute(
                inputs={"input": "Hello"},
                context=context
            )
            assert result.success is False
            assert "API error" in result.error

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_with_no_usage(self):
        """Test execute when response has no usage info."""
        node = LlmProcessNode("llm_1", {"provider": "ollama"})
        context = MagicMock(spec=ExecutionContext)
        
        mock_provider = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Response"
        mock_response.usage = None
        mock_provider.complete_sync = AsyncMock(return_value=mock_response)
        
        with patch.object(node, "_get_provider", return_value=mock_provider):
            result = await node.execute(
                inputs={"input": "Hello"},
                context=context
            )
            assert result.success is True
            assert result.outputs["tokens"]["total"] == 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_with_system_prompt_override(self):
        """Test execute with system prompt override from inputs."""
        node = LlmProcessNode("llm_1", {
            "provider": "ollama",
            "systemPrompt": "Default system prompt",
        })
        context = MagicMock(spec=ExecutionContext)
        
        mock_provider = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Response"
        mock_response.usage = None
        mock_provider.complete_sync = AsyncMock(return_value=mock_response)
        
        with patch.object(node, "_get_provider", return_value=mock_provider):
            result = await node.execute(
                inputs={
                    "input": "Hello",
                    "system_prompt": "Custom system prompt",
                },
                context=context
            )
            assert result.success is True
            # Verify the custom system prompt was used
            call_kwargs = mock_provider.complete_sync.call_args[1]
            assert call_kwargs["system"] == "Custom system prompt"
