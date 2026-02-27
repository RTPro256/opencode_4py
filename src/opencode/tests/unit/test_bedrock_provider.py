"""
Tests for Bedrock Provider.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import json

from opencode.provider.bedrock import BedrockProvider
from opencode.provider.base import (
    Message,
    MessageRole,
    ToolDefinition,
)


@pytest.mark.unit
class TestBedrockProvider:
    """Tests for BedrockProvider class."""

    def test_provider_creation(self):
        """Test BedrockProvider instantiation."""
        provider = BedrockProvider(
            region="us-east-1",
            access_key="test-key",
            secret_key="test-secret",
        )
        assert provider is not None
        assert provider._region == "us-east-1"

    def test_provider_name(self):
        """Test provider name property."""
        provider = BedrockProvider(
            region="us-east-1",
            access_key="test-key",
            secret_key="test-secret",
        )
        assert provider.name == "bedrock"

    def test_provider_models(self):
        """Test provider models property."""
        provider = BedrockProvider(
            region="us-east-1",
            access_key="test-key",
            secret_key="test-secret",
        )
        models = provider.models
        assert len(models) > 0

    @pytest.mark.asyncio
    async def test_complete_basic(self):
        """Test basic completion."""
        provider = BedrockProvider(
            region="us-east-1",
            access_key="test-key",
            secret_key="test-secret",
        )
        
        # Mock the Bedrock client
        mock_response = {
            "body": MagicMock()
        }
        mock_response["body"].read.return_value = json.dumps({
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [{"text": "Hello!"}]
                }
            },
            "stopReason": "end_turn",
            "usage": {"inputTokens": 10, "outputTokens": 5}
        }).encode()
        
        with patch.object(provider, '_client', create=True) as mock_client:
            mock_client.invoke_model = MagicMock(return_value=mock_response)
            
            messages = [Message(role=MessageRole.USER, content="Hi")]
            chunks = []
            async for chunk in provider.complete(messages, model="anthropic.claude-3-sonnet-20240229-v1:0"):
                chunks.append(chunk)
            
            assert len(chunks) >= 1

    @pytest.mark.asyncio
    async def test_count_tokens(self):
        """Test token counting."""
        provider = BedrockProvider(
            region="us-east-1",
            access_key="test-key",
            secret_key="test-secret",
        )
        
        count = await provider.count_tokens("Hello world!", "anthropic.claude-3-sonnet-20240229-v1:0")
        assert count > 0

    @pytest.mark.asyncio
    async def test_close(self):
        """Test closing the provider."""
        provider = BedrockProvider(
            region="us-east-1",
            access_key="test-key",
            secret_key="test-secret",
        )
        
        # Bedrock client doesn't need explicit close
        await provider.close()
