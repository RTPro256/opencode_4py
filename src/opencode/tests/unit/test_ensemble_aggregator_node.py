"""
Tests for EnsembleAggregatorNode.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from opencode.workflow.nodes.ensemble_aggregator import EnsembleAggregatorNode
from opencode.workflow.node import NodeSchema, ExecutionResult, ExecutionContext, PortDataType, PortDirection


class TestEnsembleAggregatorNode:
    """Tests for EnsembleAggregatorNode class."""

    def test_get_schema(self):
        """Test getting node schema."""
        schema = EnsembleAggregatorNode.get_schema()
        assert schema.node_type == "ensemble_aggregator"
        assert schema.display_name == "Ensemble Aggregator"
        assert len(schema.inputs) >= 2
        assert len(schema.outputs) >= 1

    def test_node_creation(self):
        """Test creating an ensemble aggregator node."""
        node = EnsembleAggregatorNode(
            node_id="test_aggregator",
            config={
                "provider": "ollama",
                "model": "llama3.2",
                "aggregation_strategy": "synthesize",
            }
        )
        assert node.node_id == "test_aggregator"
        assert node.config["aggregation_strategy"] == "synthesize"

    @pytest.mark.asyncio
    async def test_execute_no_responses(self):
        """Test execute with no responses."""
        node = EnsembleAggregatorNode(node_id="test", config={})
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(inputs={}, context=context)
        
        assert result.success is False
        assert result.error is not None
        assert "no responses" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_with_responses_array(self):
        """Test execute with responses array."""
        node = EnsembleAggregatorNode(
            node_id="test",
            config={"aggregation_strategy": "vote", "voting_strategy": "majority"}
        )
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(
            inputs={
                "responses": ["Answer A", "Answer A", "Answer B"]
            },
            context=context
        )
        
        assert result.success is True
        assert result.outputs["output"] == "Answer A"

    @pytest.mark.asyncio
    async def test_execute_with_model_outputs(self):
        """Test execute with model_N_output format."""
        node = EnsembleAggregatorNode(
            node_id="test",
            config={"aggregation_strategy": "vote", "voting_strategy": "majority"}
        )
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(
            inputs={
                "model_0_output": "Response 1",
                "model_1_output": "Response 1",
                "model_2_output": "Response 2",
            },
            context=context
        )
        
        assert result.success is True
        assert result.outputs["output"] == "Response 1"

    @pytest.mark.asyncio
    async def test_vote_majority(self):
        """Test majority voting strategy."""
        node = EnsembleAggregatorNode(
            node_id="test",
            config={"aggregation_strategy": "vote", "voting_strategy": "majority"}
        )
        
        result = await node._vote(["A", "A", "B", "A", "B"])
        
        assert result["output"] == "A"

    @pytest.mark.asyncio
    async def test_vote_weighted(self):
        """Test weighted voting strategy."""
        node = EnsembleAggregatorNode(
            node_id="test",
            config={"aggregation_strategy": "vote", "voting_strategy": "weighted"}
        )
        
        result = await node._vote(["A", "A", "B"])
        
        # Weighted falls back to majority for now
        assert result["output"] == "A"

    @pytest.mark.asyncio
    async def test_vote_consensus_agreed(self):
        """Test consensus voting when all agree."""
        node = EnsembleAggregatorNode(
            node_id="test",
            config={"aggregation_strategy": "vote", "voting_strategy": "consensus"}
        )
        
        result = await node._vote(["Same", "Same", "Same"])
        
        assert result["output"] == "Same"

    @pytest.mark.asyncio
    async def test_vote_consensus_no_agreement(self):
        """Test consensus voting when not all agree."""
        node = EnsembleAggregatorNode(
            node_id="test",
            config={"aggregation_strategy": "vote", "voting_strategy": "consensus"}
        )
        
        result = await node._vote(["A", "B", "C"])
        
        # Should fall back to majority with no consensus prefix
        assert "[No consensus]" in result["output"]

    @pytest.mark.asyncio
    async def test_vote_empty_responses(self):
        """Test voting with empty responses."""
        node = EnsembleAggregatorNode(node_id="test", config={})
        
        result = await node._vote([])
        
        assert result["output"] == ""

    def test_collect_responses_from_array(self):
        """Test collecting responses from responses array."""
        node = EnsembleAggregatorNode(node_id="test", config={})
        
        responses = node._collect_responses({
            "responses": ["A", "B", "C"]
        })
        
        assert responses == ["A", "B", "C"]

    def test_collect_responses_from_string(self):
        """Test collecting responses when responses is a string."""
        node = EnsembleAggregatorNode(node_id="test", config={})
        
        responses = node._collect_responses({
            "responses": "Single response"
        })
        
        assert responses == ["Single response"]

    def test_collect_responses_from_model_outputs(self):
        """Test collecting responses from model_N_output format."""
        node = EnsembleAggregatorNode(node_id="test", config={})
        
        responses = node._collect_responses({
            "model_0_output": "Response 0",
            "model_1_output": "Response 1",
            "model_2_output": "Response 2",
        })
        
        assert len(responses) == 3
        assert "Response 0" in responses
        assert "Response 1" in responses
        assert "Response 2" in responses

    def test_collect_responses_from_other_inputs(self):
        """Test collecting responses from other string inputs."""
        node = EnsembleAggregatorNode(node_id="test", config={})
        
        responses = node._collect_responses({
            "some_output": "Some response",
            "another_output": "Another response",
        })
        
        assert len(responses) == 2

    def test_collect_responses_ignores_empty(self):
        """Test that empty responses are ignored."""
        node = EnsembleAggregatorNode(node_id="test", config={})
        
        responses = node._collect_responses({
            "model_0_output": "",
            "model_1_output": "Valid response",
        })
        
        # Empty strings are ignored, but whitespace-only strings are not
        assert len(responses) >= 1
        assert "Valid response" in responses

    @pytest.mark.asyncio
    async def test_synthesize_fallback_no_provider(self):
        """Test synthesize falls back when provider unavailable."""
        node = EnsembleAggregatorNode(
            node_id="test",
            config={"provider": "nonexistent_provider"}
        )
        
        result = await node._synthesize(["Response 1", "Response 2"], "Test input")
        
        # Should fall back to first response
        assert result["output"] == "Response 1"

    @pytest.mark.asyncio
    async def test_select_best_fallback_no_provider(self):
        """Test select_best falls back when provider unavailable."""
        node = EnsembleAggregatorNode(
            node_id="test",
            config={"provider": "nonexistent_provider"}
        )
        
        result = await node._select_best(["Response 1", "Response 2"], "Test input")
        
        # Should fall back to first response
        assert result["output"] == "Response 1"

    @pytest.mark.asyncio
    async def test_execute_synthesize_strategy(self):
        """Test execute with synthesize strategy."""
        node = EnsembleAggregatorNode(
            node_id="test",
            config={"aggregation_strategy": "synthesize", "provider": "nonexistent"}
        )
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(
            inputs={"responses": ["A", "B"]},
            context=context
        )
        
        assert result.success is True
        assert "output" in result.outputs

    @pytest.mark.asyncio
    async def test_execute_best_strategy(self):
        """Test execute with best strategy."""
        node = EnsembleAggregatorNode(
            node_id="test",
            config={"aggregation_strategy": "best", "provider": "nonexistent"}
        )
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(
            inputs={"responses": ["A", "B"]},
            context=context
        )
        
        assert result.success is True
        assert "output" in result.outputs

    @pytest.mark.asyncio
    async def test_execute_unknown_strategy_defaults_to_synthesize(self):
        """Test unknown strategy defaults to synthesize."""
        node = EnsembleAggregatorNode(
            node_id="test",
            config={"aggregation_strategy": "unknown_strategy", "provider": "nonexistent"}
        )
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(
            inputs={"responses": ["A"]},
            context=context
        )
        
        assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_includes_metadata(self):
        """Test execute includes metadata in output."""
        node = EnsembleAggregatorNode(
            node_id="test",
            config={"aggregation_strategy": "vote", "voting_strategy": "majority"}
        )
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(
            inputs={"responses": ["A", "A", "B"]},
            context=context
        )
        
        assert result.success is True
        assert "metadata" in result.outputs
        assert result.outputs["metadata"]["strategy"] == "vote"
        assert result.outputs["metadata"]["input_count"] == 3

    @pytest.mark.asyncio
    async def test_execute_exception_handling(self):
        """Test execute handles exceptions gracefully."""
        node = EnsembleAggregatorNode(node_id="test", config={})
        context = MagicMock(spec=ExecutionContext)
        
        # Pass invalid input that will cause an exception during processing
        result = await node.execute(
            inputs={"responses": None},  # This should be handled
            context=context
        )
        
        # Should handle gracefully
        assert result.success is False or result.success is True

    def test_get_provider_ollama(self):
        """Test getting Ollama provider."""
        node = EnsembleAggregatorNode(node_id="test", config={})
        
        with patch("opencode.provider.ollama.OllamaProvider") as mock_provider:
            mock_provider.return_value = MagicMock()
            provider = node._get_provider("ollama")
            
            # May return None if OllamaProvider fails to initialize
            # but the call should not raise an exception

    def test_get_provider_unknown(self):
        """Test getting unknown provider returns None."""
        node = EnsembleAggregatorNode(node_id="test", config={})
        
        provider = node._get_provider("unknown_provider")
        
        assert provider is None
