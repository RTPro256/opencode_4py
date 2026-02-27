"""
Extended tests for Ensemble Aggregator workflow node to achieve 100% coverage.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from collections import Counter

from opencode.workflow.nodes.ensemble_aggregator import EnsembleAggregatorNode
from opencode.workflow.node import (
    NodeSchema,
    NodePort,
    PortDataType,
    PortDirection,
    ExecutionContext,
)


class TestEnsembleAggregatorNodeCollectResponses:
    """Tests for _collect_responses method."""

    @pytest.mark.unit
    def test_collect_responses_from_responses_array(self):
        """Test collecting responses from explicit responses array."""
        node = EnsembleAggregatorNode("agg_1", {})
        
        inputs = {"responses": ["response1", "response2"]}
        result = node._collect_responses(inputs)
        
        assert result == ["response1", "response2"]

    @pytest.mark.unit
    def test_collect_responses_from_single_string(self):
        """Test collecting responses from single string."""
        node = EnsembleAggregatorNode("agg_1", {})
        
        inputs = {"responses": "single response"}
        result = node._collect_responses(inputs)
        
        assert result == ["single response"]

    @pytest.mark.unit
    def test_collect_responses_from_model_outputs(self):
        """Test collecting responses from model_N_output format."""
        node = EnsembleAggregatorNode("agg_1", {})
        
        inputs = {
            "model_0_output": "response0",
            "model_1_output": "response1",
            "model_2_output": "response2",
        }
        result = node._collect_responses(inputs)
        
        assert "response0" in result
        assert "response1" in result
        assert "response2" in result

    @pytest.mark.unit
    def test_collect_responses_from_other_inputs(self):
        """Test collecting responses from other string inputs."""
        node = EnsembleAggregatorNode("agg_1", {})
        
        inputs = {
            "input": "question",
            "other_output": "some response",
        }
        result = node._collect_responses(inputs)
        
        assert "some response" in result

    @pytest.mark.unit
    def test_collect_responses_empty_model_output(self):
        """Test collecting responses ignores empty model outputs."""
        node = EnsembleAggregatorNode("agg_1", {})
        
        inputs = {
            "model_0_output": "",
            "model_1_output": None,
            "model_2_output": "valid",
        }
        result = node._collect_responses(inputs)
        
        assert result == ["valid"]

    @pytest.mark.unit
    def test_collect_responses_no_duplicates(self):
        """Test collecting responses avoids duplicates."""
        node = EnsembleAggregatorNode("agg_1", {})
        
        inputs = {
            "model_0_output": "same",
            "other_output": "same",
        }
        result = node._collect_responses(inputs)
        
        assert result.count("same") == 1

    @pytest.mark.unit
    def test_collect_responses_empty_inputs(self):
        """Test collecting responses with empty inputs."""
        node = EnsembleAggregatorNode("agg_1", {})
        
        inputs = {}
        result = node._collect_responses(inputs)
        
        assert result == []


class TestEnsembleAggregatorNodeVote:
    """Tests for _vote method."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_vote_majority(self):
        """Test majority voting."""
        node = EnsembleAggregatorNode("agg_1", {"voting_strategy": "majority"})
        
        responses = ["A", "B", "A", "A", "B"]
        result = await node._vote(responses)
        
        assert result["output"] == "A"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_vote_weighted(self):
        """Test weighted voting (falls back to majority)."""
        node = EnsembleAggregatorNode("agg_1", {"voting_strategy": "weighted"})
        
        responses = ["A", "B", "A"]
        result = await node._vote(responses)
        
        assert result["output"] == "A"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_vote_consensus_all_agree(self):
        """Test consensus voting when all agree."""
        node = EnsembleAggregatorNode("agg_1", {"voting_strategy": "consensus"})
        
        responses = ["same", "same", "same"]
        result = await node._vote(responses)
        
        assert result["output"] == "same"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_vote_consensus_no_agreement(self):
        """Test consensus voting when no agreement."""
        node = EnsembleAggregatorNode("agg_1", {"voting_strategy": "consensus"})
        
        responses = ["A", "B", "C"]
        result = await node._vote(responses)
        
        assert "[No consensus]" in result["output"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_vote_empty_responses(self):
        """Test voting with empty responses."""
        node = EnsembleAggregatorNode("agg_1", {})
        
        result = await node._vote([])
        
        assert result["output"] == ""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_vote_unknown_strategy(self):
        """Test voting with unknown strategy defaults to majority."""
        node = EnsembleAggregatorNode("agg_1", {"voting_strategy": "unknown"})
        
        responses = ["A", "B", "A"]
        result = await node._vote(responses)
        
        assert result["output"] == "A"


class TestEnsembleAggregatorNodeSynthesize:
    """Tests for _synthesize method."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_synthesize_no_provider(self):
        """Test synthesize falls back when no provider available."""
        node = EnsembleAggregatorNode("agg_1", {"provider": "unknown_provider"})
        
        responses = ["response1", "response2"]
        result = await node._synthesize(responses, "test question")
        
        assert result["output"] == "response1"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_synthesize_with_provider_error(self):
        """Test synthesize handles provider errors."""
        node = EnsembleAggregatorNode("agg_1", {"provider": "ollama"})
        
        with patch.object(node, '_get_provider', return_value=None):
            responses = ["response1", "response2"]
            result = await node._synthesize(responses, "test question")
            
            assert result["output"] == "response1"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_synthesize_custom_prompt(self):
        """Test synthesize with custom aggregation prompt."""
        node = EnsembleAggregatorNode("agg_1", {
            "provider": "ollama",
            "aggregation_prompt": "Custom prompt:",
        })
        
        mock_provider = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "synthesized"
        mock_provider.complete_sync = AsyncMock(return_value=mock_response)
        
        with patch.object(node, '_get_provider', return_value=mock_provider):
            responses = ["r1", "r2"]
            result = await node._synthesize(responses, "")
            
            assert result["output"] == "synthesized"


class TestEnsembleAggregatorNodeSelectBest:
    """Tests for _select_best method."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_select_best_no_provider(self):
        """Test select_best falls back when no provider available."""
        node = EnsembleAggregatorNode("agg_1", {"provider": "unknown_provider"})
        
        responses = ["response1", "response2"]
        result = await node._select_best(responses, "test question")
        
        assert result["output"] == "response1"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_select_best_with_provider_error(self):
        """Test select_best handles provider errors."""
        node = EnsembleAggregatorNode("agg_1", {"provider": "ollama"})
        
        with patch.object(node, '_get_provider', return_value=None):
            responses = ["response1", "response2"]
            result = await node._select_best(responses, "test question")
            
            assert result["output"] == "response1"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_select_best_truncates_long_responses(self):
        """Test select_best truncates long responses in prompt."""
        node = EnsembleAggregatorNode("agg_1", {"provider": "ollama"})
        
        mock_provider = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "1"
        mock_provider.complete_sync = AsyncMock(return_value=mock_response)
        
        long_response = "x" * 600
        
        with patch.object(node, '_get_provider', return_value=mock_provider):
            responses = [long_response, "short"]
            result = await node._select_best(responses, "test")
            
            assert result["output"] == long_response

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_select_best_parses_response_number(self):
        """Test select_best parses response number correctly."""
        node = EnsembleAggregatorNode("agg_1", {"provider": "ollama"})
        
        mock_provider = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "The best is response 2"
        mock_provider.complete_sync = AsyncMock(return_value=mock_response)
        
        with patch.object(node, '_get_provider', return_value=mock_provider):
            responses = ["first", "second", "third"]
            result = await node._select_best(responses, "test")
            
            assert result["output"] == "second"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_select_best_invalid_index(self):
        """Test select_best handles invalid index."""
        node = EnsembleAggregatorNode("agg_1", {"provider": "ollama"})
        
        mock_provider = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "99"  # Invalid index
        mock_provider.complete_sync = AsyncMock(return_value=mock_response)
        
        with patch.object(node, '_get_provider', return_value=mock_provider):
            responses = ["first", "second"]
            result = await node._select_best(responses, "test")
            
            assert result["output"] == "first"


class TestEnsembleAggregatorNodeGetProvider:
    """Tests for _get_provider method."""

    @pytest.mark.unit
    def test_get_provider_ollama(self):
        """Test getting Ollama provider."""
        node = EnsembleAggregatorNode("agg_1", {})
        
        with patch('opencode.provider.ollama.OllamaProvider') as MockProvider:
            MockProvider.return_value = MagicMock()
            result = node._get_provider("ollama")
            
            assert result is not None

    @pytest.mark.unit
    def test_get_provider_lmstudio(self):
        """Test getting LMStudio provider."""
        node = EnsembleAggregatorNode("agg_1", {})
        
        with patch('opencode.provider.lmstudio.LMStudioProvider') as MockProvider:
            MockProvider.return_value = MagicMock()
            result = node._get_provider("lmstudio")
            
            assert result is not None

    @pytest.mark.unit
    def test_get_provider_openai_with_key(self):
        """Test getting OpenAI provider with API key."""
        node = EnsembleAggregatorNode("agg_1", {})
        
        mock_config = MagicMock()
        mock_config.get_api_key.return_value = "test-key"
        
        with patch('opencode.core.config.Config.load', return_value=mock_config):
            with patch('opencode.provider.openai.OpenAIProvider') as MockProvider:
                MockProvider.return_value = MagicMock()
                result = node._get_provider("openai")
                
                assert result is not None

    @pytest.mark.unit
    def test_get_provider_openai_no_key(self):
        """Test getting OpenAI provider without API key."""
        node = EnsembleAggregatorNode("agg_1", {})
        
        mock_config = MagicMock()
        mock_config.get_api_key.return_value = None
        
        with patch('opencode.core.config.Config.load', return_value=mock_config):
            result = node._get_provider("openai")
            
            assert result is None

    @pytest.mark.unit
    def test_get_provider_anthropic_with_key(self):
        """Test getting Anthropic provider with API key."""
        node = EnsembleAggregatorNode("agg_1", {})
        
        mock_config = MagicMock()
        mock_config.get_api_key.return_value = "test-key"
        
        with patch('opencode.core.config.Config.load', return_value=mock_config):
            with patch('opencode.provider.anthropic.AnthropicProvider') as MockProvider:
                MockProvider.return_value = MagicMock()
                result = node._get_provider("anthropic")
                
                assert result is not None

    @pytest.mark.unit
    def test_get_provider_anthropic_no_key(self):
        """Test getting Anthropic provider without API key."""
        node = EnsembleAggregatorNode("agg_1", {})
        
        mock_config = MagicMock()
        mock_config.get_api_key.return_value = None
        
        with patch('opencode.core.config.Config.load', return_value=mock_config):
            result = node._get_provider("anthropic")
            
            assert result is None

    @pytest.mark.unit
    def test_get_provider_unknown(self):
        """Test getting unknown provider."""
        node = EnsembleAggregatorNode("agg_1", {})
        
        result = node._get_provider("unknown_provider")
        
        assert result is None

    @pytest.mark.unit
    def test_get_provider_import_error(self):
        """Test getting provider with import error."""
        node = EnsembleAggregatorNode("agg_1", {})
        
        with patch('opencode.provider.ollama.OllamaProvider', side_effect=ImportError):
            result = node._get_provider("ollama")
            
            assert result is None


class TestEnsembleAggregatorNodeExecuteFull:
    """Full execution tests for EnsembleAggregatorNode."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_no_responses(self):
        """Test execute with no responses."""
        node = EnsembleAggregatorNode("agg_1", {})
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(inputs={}, context=context)
        
        assert result.success is False
        assert "No responses" in result.error

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_vote_strategy(self):
        """Test execute with vote strategy."""
        node = EnsembleAggregatorNode("agg_1", {"aggregation_strategy": "vote"})
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(
            inputs={"responses": ["A", "B", "A"]},
            context=context
        )
        
        assert result.success is True
        assert result.outputs["output"] == "A"
        assert result.outputs["metadata"]["strategy"] == "vote"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_best_strategy(self):
        """Test execute with best strategy."""
        node = EnsembleAggregatorNode("agg_1", {
            "aggregation_strategy": "best",
            "provider": "unknown",
        })
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(
            inputs={"responses": ["first", "second"], "input": "question"},
            context=context
        )
        
        assert result.success is True
        assert result.outputs["output"] == "first"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_unknown_strategy_defaults_to_synthesize(self):
        """Test execute with unknown strategy defaults to synthesize."""
        node = EnsembleAggregatorNode("agg_1", {
            "aggregation_strategy": "unknown",
            "provider": "unknown",
        })
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(
            inputs={"responses": ["response1", "response2"]},
            context=context
        )
        
        assert result.success is True
        assert result.outputs["output"] == "response1"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_metadata(self):
        """Test execute returns correct metadata."""
        node = EnsembleAggregatorNode("agg_1", {
            "aggregation_strategy": "vote",
            "voting_strategy": "majority",
        })
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(
            inputs={"responses": ["A", "A", "B"]},
            context=context
        )
        
        assert result.success is True
        assert result.outputs["metadata"]["strategy"] == "vote"
        assert result.outputs["metadata"]["input_count"] == 3
        assert result.outputs["metadata"]["voting_strategy"] == "majority"
        assert result.duration_ms >= 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_with_model_outputs(self):
        """Test execute with model_N_output format."""
        node = EnsembleAggregatorNode("agg_1", {"aggregation_strategy": "vote"})
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(
            inputs={
                "model_0_output": "same",
                "model_1_output": "same",
                "model_2_output": "different",
            },
            context=context
        )
        
        assert result.success is True
        assert result.outputs["output"] == "same"
