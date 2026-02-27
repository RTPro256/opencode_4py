"""
Tests for multi-model configuration and execution.

Unit tests for the multi-model pattern implementation.
"""

import pytest
from opencode.core.config import (
    MultiModelConfig,
    MultiModelPattern,
    ModelStepConfig,
    Config,
)


class TestMultiModelPattern:
    """Tests for multi-model pattern enum."""
    
    def test_pattern_values(self):
        """Test pattern enum values."""
        assert MultiModelPattern.SEQUENTIAL.value == "sequential"
        assert MultiModelPattern.ENSEMBLE.value == "ensemble"
        assert MultiModelPattern.VOTING.value == "voting"
        assert MultiModelPattern.SPECIALIZED.value == "specialized"
    
    def test_pattern_from_string(self):
        """Test creating pattern from string."""
        assert MultiModelPattern("sequential") == MultiModelPattern.SEQUENTIAL
        assert MultiModelPattern("ensemble") == MultiModelPattern.ENSEMBLE


class TestModelStepConfig:
    """Tests for model step configuration."""
    
    def test_basic_config(self):
        """Test basic model step configuration."""
        config = ModelStepConfig(
            model="llama3.2",
            provider="ollama",
        )
        assert config.model == "llama3.2"
        assert config.provider == "ollama"
        assert config.temperature == 0.7  # default
        assert config.max_tokens == 4096  # default
    
    def test_full_config(self):
        """Test full model step configuration."""
        config = ModelStepConfig(
            model="mistral:7b",
            provider="ollama",
            system_prompt="You are a code reviewer.",
            temperature=0.5,
            max_tokens=8192,
        )
        assert config.model == "mistral:7b"
        assert config.provider == "ollama"
        assert config.system_prompt == "You are a code reviewer."
        assert config.temperature == 0.5
        assert config.max_tokens == 8192


class TestMultiModelConfig:
    """Tests for multi-model configuration."""
    
    def test_sequential_config(self):
        """Test sequential pattern configuration."""
        config = MultiModelConfig(
            pattern=MultiModelPattern.SEQUENTIAL,
            models=[
                ModelStepConfig(model="llama3.2"),
                ModelStepConfig(model="mistral:7b"),
            ],
        )
        assert config.pattern == MultiModelPattern.SEQUENTIAL
        assert len(config.models) == 2
        assert config.enabled is True
    
    def test_ensemble_config(self):
        """Test ensemble pattern configuration."""
        config = MultiModelConfig(
            pattern=MultiModelPattern.ENSEMBLE,
            models=[
                ModelStepConfig(model="llama3.2"),
                ModelStepConfig(model="mistral:7b"),
            ],
            aggregator_model="llama3.2:70b",
        )
        assert config.pattern == MultiModelPattern.ENSEMBLE
        assert config.aggregator_model == "llama3.2:70b"
    
    def test_voting_config(self):
        """Test voting pattern configuration."""
        config = MultiModelConfig(
            pattern=MultiModelPattern.VOTING,
            models=[
                ModelStepConfig(model="llama3.2"),
                ModelStepConfig(model="mistral:7b"),
            ],
            voting_strategy="majority",
        )
        assert config.pattern == MultiModelPattern.VOTING
        assert config.voting_strategy == "majority"


class TestSequentialTemplate:
    """Tests for sequential refinement template."""
    
    def test_template_import(self):
        """Test importing sequential template."""
        from opencode.workflow.templates.sequential import SequentialRefinementTemplate
        assert SequentialRefinementTemplate is not None
    
    def test_template_build(self):
        """Test building sequential template."""
        from opencode.workflow.templates.sequential import SequentialRefinementTemplate
        
        config = MultiModelConfig(
            pattern=MultiModelPattern.SEQUENTIAL,
            models=[
                ModelStepConfig(model="llama3.2", provider="ollama"),
                ModelStepConfig(model="mistral:7b", provider="ollama"),
            ],
        )
        
        template = SequentialRefinementTemplate(config)
        graph = template.build()
        
        assert graph is not None
        assert len(graph.nodes) > 0
        assert "input" in graph.nodes
        assert "output" in graph.nodes


class TestEnsembleTemplate:
    """Tests for ensemble template."""
    
    def test_template_import(self):
        """Test importing ensemble template."""
        from opencode.workflow.templates.ensemble import EnsembleTemplate
        assert EnsembleTemplate is not None
    
    def test_template_build(self):
        """Test building ensemble template."""
        from opencode.workflow.templates.ensemble import EnsembleTemplate
        
        config = MultiModelConfig(
            pattern=MultiModelPattern.ENSEMBLE,
            models=[
                ModelStepConfig(model="llama3.2"),
                ModelStepConfig(model="mistral:7b"),
            ],
            aggregator_model="llama3.2:70b",
        )
        
        template = EnsembleTemplate(config)
        graph = template.build()
        
        assert graph is not None
        assert "aggregator" in graph.nodes


class TestVotingTemplate:
    """Tests for voting template."""
    
    def test_template_import(self):
        """Test importing voting template."""
        from opencode.workflow.templates.voting import VotingTemplate
        assert VotingTemplate is not None
    
    def test_template_build(self):
        """Test building voting template."""
        from opencode.workflow.templates.voting import VotingTemplate
        
        config = MultiModelConfig(
            pattern=MultiModelPattern.VOTING,
            models=[
                ModelStepConfig(model="llama3.2"),
                ModelStepConfig(model="mistral:7b"),
            ],
            voting_strategy="majority",
        )
        
        template = VotingTemplate(config)
        graph = template.build()
        
        assert graph is not None
        assert "voter" in graph.nodes


class TestEnsembleAggregatorNode:
    """Tests for ensemble aggregator node."""
    
    def test_node_import(self):
        """Test importing ensemble aggregator node."""
        from opencode.workflow.nodes.ensemble_aggregator import EnsembleAggregatorNode
        assert EnsembleAggregatorNode is not None
    
    def test_node_schema(self):
        """Test node schema."""
        from opencode.workflow.nodes.ensemble_aggregator import EnsembleAggregatorNode
        
        schema = EnsembleAggregatorNode.get_schema()
        assert schema.node_type == "ensemble_aggregator"
        assert schema.display_name == "Ensemble Aggregator"
    
    @pytest.mark.asyncio
    async def test_vote_strategy(self):
        """Test voting aggregation strategy."""
        from opencode.workflow.nodes.ensemble_aggregator import EnsembleAggregatorNode
        
        node = EnsembleAggregatorNode(
            node_id="test",
            config={"aggregation_strategy": "vote"}
        )
        
        # Cast to access the internal method
        result = await node._vote(["answer1", "answer2", "answer1"])  # type: ignore
        assert result["output"] == "answer1"
    
    @pytest.mark.asyncio
    async def test_vote_strategy_empty(self):
        """Test voting with empty responses."""
        from opencode.workflow.nodes.ensemble_aggregator import EnsembleAggregatorNode
        
        node = EnsembleAggregatorNode(
            node_id="test",
            config={"aggregation_strategy": "vote"}
        )
        
        # Cast to access the internal method
        result = await node._vote([])  # type: ignore
        assert result["output"] == ""


class TestGetTemplate:
    """Tests for template registry."""
    
    def test_get_template_sequential(self):
        """Test getting sequential template."""
        from opencode.workflow.templates import get_template
        
        config = MultiModelConfig(
            pattern=MultiModelPattern.SEQUENTIAL,
            models=[ModelStepConfig(model="llama3.2")],
        )
        
        graph = get_template("sequential", config)
        assert graph is not None
    
    def test_get_template_ensemble(self):
        """Test getting ensemble template."""
        from opencode.workflow.templates import get_template
        
        config = MultiModelConfig(
            pattern=MultiModelPattern.ENSEMBLE,
            models=[ModelStepConfig(model="llama3.2")],
        )
        
        graph = get_template("ensemble", config)
        assert graph is not None
    
    def test_get_template_invalid(self):
        """Test getting invalid template."""
        from opencode.workflow.templates import get_template
        
        config = MultiModelConfig(
            pattern=MultiModelPattern.SEQUENTIAL,
            models=[ModelStepConfig(model="llama3.2")],
        )
        
        with pytest.raises(ValueError):
            get_template("invalid_template", config)
