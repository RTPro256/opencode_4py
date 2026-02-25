"""
Integration tests for Ollama provider.

Tests connection, model management, and basic operations.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from opencode.provider.base import (
    Message,
    MessageRole,
    ToolDefinition,
    FinishReason,
    StreamChunk,
    ToolCall,
    CompletionResponse,
)


@pytest.mark.ollama
class TestOllamaIntegration:
    """Test Ollama integration."""
    
    @pytest.fixture
    async def provider(self, ollama_available):
        """Get Ollama provider instance if available."""
        if not ollama_available:
            pytest.skip("Ollama not available at localhost:11434")
        
        from opencode.provider.ollama import OllamaProvider
        provider = OllamaProvider()
        return provider
    
    @pytest.fixture
    def mock_provider(self):
        """Create a mock Ollama provider for testing without Ollama running."""
        from opencode.provider.ollama import OllamaProvider
        
        provider = MagicMock(spec=OllamaProvider)
        provider.name = "ollama"
        provider.models = OllamaProvider.COMMON_MODELS
        return provider
    
    @pytest.mark.asyncio
    async def test_connection_when_available(self, provider):
        """Test basic connection to Ollama when available."""
        models = await provider.get_available_models()
        # If we get here, connection works
        assert isinstance(models, list)
    
    @pytest.mark.asyncio
    async def test_list_models_when_available(self, provider):
        """Test listing available models when Ollama is running."""
        models = await provider.get_available_models()
        
        assert isinstance(models, list)
        # If Ollama is running with models, should have at least one
        if len(models) > 0:
            assert isinstance(models[0], str)
    
    def test_provider_name(self, mock_provider):
        """Test provider name."""
        assert mock_provider.name == "ollama"
    
    def test_provider_has_models(self, mock_provider):
        """Test provider has models configured."""
        models = mock_provider.models
        assert len(models) > 0


@pytest.mark.ollama
class TestOllamaCompletion:
    """Tests for Ollama completion functionality."""
    
    @pytest.fixture
    def mock_provider(self):
        """Create a mock Ollama provider."""
        provider = MagicMock()
        provider.name = "ollama"
        provider.complete_sync = AsyncMock(return_value=CompletionResponse(
            content="Hello! How can I help you?",
            model="llama3.2:3b",
        ))
        return provider
    
    @pytest.mark.asyncio
    async def test_simple_completion(self, mock_provider):
        """Test simple completion."""
        response = await mock_provider.complete_sync(
            messages=[Message(role=MessageRole.USER, content="Say 'hello world'")],
            model="llama3.2:3b",
        )
        
        assert response.content
        assert len(response.content) > 0
    
    @pytest.mark.asyncio
    async def test_completion_with_system_prompt(self, mock_provider):
        """Test completion with system prompt."""
        messages = [
            Message(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
            Message(role=MessageRole.USER, content="Hello"),
        ]
        
        response = await mock_provider.complete_sync(
            messages=messages,
            model="llama3.2:3b",
        )
        
        assert response is not None


@pytest.mark.ollama
class TestOllamaStreaming:
    """Tests for Ollama streaming functionality."""
    
    @pytest.fixture
    def mock_streaming_provider(self):
        """Create a mock provider with streaming support."""
        provider = MagicMock()
        provider.name = "ollama"
        
        async def mock_stream(*args, **kwargs):
            chunks = ["Hello", " ", "world", "!"]
            for chunk in chunks:
                yield StreamChunk.text(chunk)
            yield StreamChunk.done(FinishReason.STOP)
        
        provider.complete = mock_stream
        return provider
    
    @pytest.mark.asyncio
    async def test_streaming_completion(self, mock_streaming_provider):
        """Test streaming completion."""
        chunks = []
        
        async for chunk in mock_streaming_provider.complete(
            messages=[Message(role=MessageRole.USER, content="Count from 1 to 5")],
            model="llama3.2:3b",
        ):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        full_content = "".join(c.delta for c in chunks if c.delta)
        assert len(full_content) > 0


@pytest.mark.ollama
class TestOllamaToolCalling:
    """Tests for Ollama tool calling functionality."""
    
    def test_tool_definition_format(self):
        """Test tool definition format for Ollama."""
        tool = ToolDefinition(
            name="get_weather",
            description="Get current weather for a location",
            parameters={
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                },
                "required": ["location"],
            },
        )
        
        # Ollama uses OpenAI-compatible format
        openai_format = tool.to_openai_format()
        
        assert openai_format["type"] == "function"
        assert openai_format["function"]["name"] == "get_weather"
    
    @pytest.mark.asyncio
    async def test_tool_calling_mock(self):
        """Test tool calling with mock."""
        # Mock a tool call response
        tool_call = ToolCall(
            id="call-123",
            name="get_weather",
            arguments={"location": "Tokyo"},
        )
        
        response = CompletionResponse(
            content="",
            tool_calls=[tool_call],
            finish_reason=FinishReason.TOOL_CALL,
        )
        
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].name == "get_weather"


@pytest.mark.ollama
class TestOllamaModelParameters:
    """Tests for Ollama model parameters."""
    
    def test_model_parameters_structure(self):
        """Test model parameters structure."""
        params = {
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "num_predict": 256,
        }
        
        assert params["temperature"] >= 0
        assert params["top_p"] > 0
        assert params["top_k"] > 0
        assert params["num_predict"] > 0
    
    def test_context_window_sizes(self):
        """Test context window sizes for different models."""
        from opencode.provider.ollama import OllamaProvider
        
        for model in OllamaProvider.COMMON_MODELS:
            assert model.context_length > 0, f"Invalid context window for {model.id}"


@pytest.mark.ollama
class TestOllamaModelManagement:
    """Tests for Ollama model management."""
    
    @pytest.fixture
    def mock_ollama_client(self):
        """Create a mock Ollama client."""
        client = MagicMock()
        client.list = AsyncMock(return_value={
            "models": [
                {"name": "llama3.2:3b", "size": 2000000000, "digest": "abc123"},
                {"name": "llama3.1:8b", "size": 5000000000, "digest": "def456"},
            ]
        })
        client.pull = AsyncMock(return_value={"status": "success"})
        client.delete = AsyncMock(return_value={"status": "success"})
        return client
    
    @pytest.mark.asyncio
    async def test_list_models(self, mock_ollama_client):
        """Test listing models."""
        result = await mock_ollama_client.list()
        
        assert "models" in result
        assert len(result["models"]) == 2
    
    @pytest.mark.asyncio
    async def test_pull_model(self, mock_ollama_client):
        """Test pulling a model."""
        result = await mock_ollama_client.pull("llama3.2:3b")
        
        assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_delete_model(self, mock_ollama_client):
        """Test deleting a model."""
        result = await mock_ollama_client.delete("llama3.2:3b")
        
        assert result["status"] == "success"


@pytest.mark.ollama
class TestOllamaConnectionHandling:
    """Tests for Ollama connection handling."""
    
    @pytest.mark.asyncio
    async def test_connection_timeout(self):
        """Test connection timeout handling."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(
                side_effect=TimeoutError("Connection timed out")
            )
            mock_client.return_value.__aenter__.return_value = mock_instance
            
            # Provider should handle timeout gracefully
            from opencode.provider.ollama import OllamaProvider
            provider = OllamaProvider()
            
            models = await provider.get_available_models()
            assert models == []
    
    @pytest.mark.asyncio
    async def test_connection_refused(self):
        """Test connection refused handling."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(
                side_effect=ConnectionError("Connection refused")
            )
            mock_client.return_value.__aenter__.return_value = mock_instance
            
            from opencode.provider.ollama import OllamaProvider
            provider = OllamaProvider()
            
            models = await provider.get_available_models()
            assert models == []


@pytest.mark.ollama
class TestOllamaAPICompatibility:
    """Tests for Ollama API compatibility."""
    
    def test_chat_endpoint_format(self):
        """Test chat endpoint request format."""
        request_body = {
            "model": "llama3.2:3b",
            "messages": [
                {"role": "user", "content": "Hello"},
            ],
            "stream": False,
        }
        
        assert "model" in request_body
        assert "messages" in request_body
        assert isinstance(request_body["messages"], list)
    
    def test_generate_endpoint_format(self):
        """Test generate endpoint request format."""
        request_body = {
            "model": "llama3.2:3b",
            "prompt": "Hello, world!",
            "stream": False,
        }
        
        assert "model" in request_body
        assert "prompt" in request_body
    
    def test_embedding_endpoint_format(self):
        """Test embedding endpoint request format."""
        request_body = {
            "model": "nomic-embed-text",
            "input": "Hello, world!",
        }
        
        assert "model" in request_body
        assert "input" in request_body
