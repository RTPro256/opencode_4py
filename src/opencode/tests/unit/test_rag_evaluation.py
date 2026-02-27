"""Tests for RAG Evaluation module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from opencode.core.rag.evaluation import (
    RetrievalMetrics,
    GenerationMetrics,
    EvaluationResult,
    GroundTruthEntry,
    RAGEvaluator,
)


class TestRetrievalMetrics:
    """Tests for RetrievalMetrics."""
    
    def test_default_values(self):
        """Test default values."""
        metrics = RetrievalMetrics()
        assert metrics.recall_at_k == {}
        assert metrics.mrr == 0.0
        assert metrics.ndcg == 0.0
        assert metrics.precision_at_k == {}
    
    def test_custom_values(self):
        """Test custom values."""
        metrics = RetrievalMetrics(
            recall_at_k={1: 0.5, 5: 0.8},
            mrr=0.75,
            ndcg=0.85,
            precision_at_k={1: 0.6, 5: 0.7}
        )
        assert metrics.recall_at_k[1] == 0.5
        assert metrics.mrr == 0.75
        assert metrics.ndcg == 0.85
    
    def test_to_dict(self):
        """Test to_dict method."""
        metrics = RetrievalMetrics(
            recall_at_k={1: 0.5},
            mrr=0.75,
            ndcg=0.85,
            precision_at_k={1: 0.6}
        )
        result = metrics.to_dict()
        
        assert result["recall_at_k"] == {1: 0.5}
        assert result["mrr"] == 0.75
        assert result["ndcg"] == 0.85
        assert result["precision_at_k"] == {1: 0.6}


class TestGenerationMetrics:
    """Tests for GenerationMetrics."""
    
    def test_default_values(self):
        """Test default values."""
        metrics = GenerationMetrics()
        assert metrics.faithfulness == 0.0
        assert metrics.relevance == 0.0
        assert metrics.coherence == 0.0
        assert metrics.completeness == 0.0
    
    def test_custom_values(self):
        """Test custom values."""
        metrics = GenerationMetrics(
            faithfulness=0.9,
            relevance=0.8,
            coherence=0.85,
            completeness=0.75
        )
        assert metrics.faithfulness == 0.9
        assert metrics.relevance == 0.8
    
    def test_to_dict(self):
        """Test to_dict method."""
        metrics = GenerationMetrics(
            faithfulness=0.9,
            relevance=0.8,
            coherence=0.85,
            completeness=0.75
        )
        result = metrics.to_dict()
        
        assert result["faithfulness"] == 0.9
        assert result["relevance"] == 0.8
        assert result["coherence"] == 0.85
        assert result["completeness"] == 0.75


class TestEvaluationResult:
    """Tests for EvaluationResult."""
    
    def test_default_values(self):
        """Test default values."""
        result = EvaluationResult(query="test query")
        assert result.query == "test query"
        assert result.retrieved_docs == []
        assert result.generated_answer == ""
        assert result.ground_truth is None
    
    def test_custom_values(self):
        """Test custom values."""
        result = EvaluationResult(
            query="test query",
            retrieved_docs=["doc1", "doc2"],
            generated_answer="test answer",
            ground_truth="expected answer",
            latency_ms=150.5
        )
        assert result.query == "test query"
        assert result.retrieved_docs == ["doc1", "doc2"]
        assert result.generated_answer == "test answer"
        assert result.ground_truth == "expected answer"
        assert result.latency_ms == 150.5


class TestGroundTruthEntry:
    """Tests for GroundTruthEntry."""
    
    def test_default_values(self):
        """Test default values."""
        entry = GroundTruthEntry(query="test query")
        assert entry.query == "test query"
        assert entry.relevant_docs == []
        assert entry.answer is None
        assert entry.metadata == {}
    
    def test_custom_values(self):
        """Test custom values."""
        entry = GroundTruthEntry(
            query="test query",
            relevant_docs=["doc1", "doc2"],
            answer="expected answer",
            metadata={"source": "test"}
        )
        assert entry.query == "test query"
        assert entry.relevant_docs == ["doc1", "doc2"]
        assert entry.answer == "expected answer"


class TestRAGEvaluator:
    """Tests for RAGEvaluator."""
    
    def test_init(self):
        """Test initialization."""
        evaluator = RAGEvaluator()
        assert evaluator.llm_client is None
        assert evaluator.k_values == [1, 3, 5, 10]
    
    def test_init_custom_k_values(self):
        """Test initialization with custom K values."""
        evaluator = RAGEvaluator(k_values=[1, 2, 3])
        assert evaluator.k_values == [1, 2, 3]
    
    def test_evaluate_retrieval_empty_relevant(self):
        """Test retrieval evaluation with empty relevant IDs."""
        evaluator = RAGEvaluator()
        metrics = evaluator.evaluate_retrieval(
            retrieved_ids=["doc1", "doc2"],
            relevant_ids=[]
        )
        
        assert metrics.mrr == 0.0
        assert metrics.ndcg == 0.0
    
    def test_evaluate_retrieval_perfect_match(self):
        """Test retrieval evaluation with perfect match."""
        evaluator = RAGEvaluator(k_values=[1, 3, 5])
        metrics = evaluator.evaluate_retrieval(
            retrieved_ids=["doc1", "doc2", "doc3"],
            relevant_ids=["doc1", "doc2"]
        )
        
        assert metrics.recall_at_k[1] == 0.5  # 1 of 2 relevant
        assert metrics.recall_at_k[3] == 1.0  # 2 of 2 relevant
        assert metrics.mrr == 1.0  # First doc is relevant
        assert metrics.ndcg > 0
    
    def test_evaluate_retrieval_no_match(self):
        """Test retrieval evaluation with no matches."""
        evaluator = RAGEvaluator(k_values=[1, 3, 5])
        metrics = evaluator.evaluate_retrieval(
            retrieved_ids=["doc3", "doc4", "doc5"],
            relevant_ids=["doc1", "doc2"]
        )
        
        assert metrics.recall_at_k[1] == 0.0
        assert metrics.recall_at_k[3] == 0.0
        assert metrics.mrr == 0.0
    
    def test_evaluate_retrieval_partial_match(self):
        """Test retrieval evaluation with partial match."""
        evaluator = RAGEvaluator(k_values=[1, 3, 5])
        metrics = evaluator.evaluate_retrieval(
            retrieved_ids=["doc3", "doc1", "doc4"],
            relevant_ids=["doc1", "doc2"]
        )
        
        assert metrics.mrr == 0.5  # Found at position 2
        assert metrics.recall_at_k[3] == 0.5  # 1 of 2 relevant
    
    def test_calculate_ndcg(self):
        """Test NDCG calculation."""
        evaluator = RAGEvaluator()
        
        # Perfect ranking
        ndcg = evaluator._calculate_ndcg(
            ["doc1", "doc2"],
            {"doc1", "doc2"}
        )
        assert ndcg > 0.9  # Should be close to 1.0
        
        # Poor ranking
        ndcg = evaluator._calculate_ndcg(
            ["doc3", "doc4", "doc1"],
            {"doc1", "doc2"}
        )
        assert 0 < ndcg < 1
    
    @pytest.mark.asyncio
    async def test_evaluate_generation_no_llm(self):
        """Test generation evaluation without LLM."""
        evaluator = RAGEvaluator()
        metrics = await evaluator.evaluate_generation(
            query="What is Python?",
            answer="Python is a programming language.",
            context=["Python is a popular programming language."]
        )
        
        assert metrics.faithfulness > 0
        assert metrics.relevance > 0
        assert metrics.coherence == 0.5
        assert metrics.completeness == 0.5
    
    @pytest.mark.asyncio
    async def test_evaluate_generation_with_ground_truth(self):
        """Test generation evaluation with ground truth."""
        evaluator = RAGEvaluator()
        metrics = await evaluator.evaluate_generation(
            query="What is Python?",
            answer="Python is a programming language.",
            context=["Python is a popular programming language."],
            ground_truth="Python is a high-level programming language."
        )
        
        assert metrics.faithfulness > 0
        assert metrics.relevance > 0
    
    def test_heuristic_faithfulness(self):
        """Test heuristic faithfulness calculation."""
        evaluator = RAGEvaluator()
        
        # High overlap
        score = evaluator._heuristic_faithfulness(
            "Python is a programming language",
            ["Python is a popular programming language"]
        )
        assert score > 0.5
        
        # No overlap
        score = evaluator._heuristic_faithfulness(
            "Java is great",
            ["Python is a programming language"]
        )
        assert score < 0.5
        
        # Empty context
        score = evaluator._heuristic_faithfulness(
            "Python is great",
            []
        )
        assert score == 0.0
    
    def test_heuristic_relevance(self):
        """Test heuristic relevance calculation."""
        evaluator = RAGEvaluator()
        
        # High overlap
        score = evaluator._heuristic_relevance(
            "What is Python?",
            "Python is a programming language."
        )
        assert score > 0
        
        # No overlap - use words that don't appear in answer
        score = evaluator._heuristic_relevance(
            "Java coffee beans",
            "Python is a programming language."
        )
        assert score == 0.0
        
        # Empty query
        score = evaluator._heuristic_relevance(
            "",
            "Python is a programming language."
        )
        assert score == 0.0
    
    @pytest.mark.asyncio
    async def test_generate_ground_truth_no_llm(self):
        """Test ground truth generation without LLM."""
        evaluator = RAGEvaluator()
        result = await evaluator.generate_ground_truth(
            documents=[{"id": "doc1", "content": "test"}]
        )
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_generate_ground_truth_with_llm(self):
        """Test ground truth generation with LLM."""
        mock_llm = MagicMock()
        evaluator = RAGEvaluator(llm_client=mock_llm)
        
        documents = [
            {"id": "doc1", "content": "Python is a programming language."},
            {"id": "doc2", "content": "JavaScript is also popular."}
        ]
        
        result = await evaluator.generate_ground_truth(documents, num_questions=2)
        
        assert len(result) == 2
        assert result[0].query == "Question about doc1"
    
    def test_evaluate_batch_empty(self):
        """Test batch evaluation with empty results."""
        evaluator = RAGEvaluator()
        result = evaluator.evaluate_batch([])
        
        assert result == {}
    
    def test_evaluate_batch_with_results(self):
        """Test batch evaluation with results."""
        evaluator = RAGEvaluator()
        
        results = [
            EvaluationResult(
                query="query1",
                retrieval_metrics=RetrievalMetrics(
                    recall_at_k={1: 0.5, 3: 0.8},
                    mrr=0.7,
                    ndcg=0.8,
                    precision_at_k={1: 0.6, 3: 0.7}
                ),
                generation_metrics=GenerationMetrics(
                    faithfulness=0.9,
                    relevance=0.8,
                    coherence=0.85,
                    completeness=0.75
                )
            ),
            EvaluationResult(
                query="query2",
                retrieval_metrics=RetrievalMetrics(
                    recall_at_k={1: 0.6, 3: 0.9},
                    mrr=0.8,
                    ndcg=0.85,
                    precision_at_k={1: 0.7, 3: 0.8}
                ),
                generation_metrics=GenerationMetrics(
                    faithfulness=0.85,
                    relevance=0.9,
                    coherence=0.8,
                    completeness=0.7
                )
            )
        ]
        
        result = evaluator.evaluate_batch(results)
        
        assert result["num_queries"] == 2
        assert "retrieval" in result
        assert "generation" in result
        assert result["retrieval"]["avg_mrr"] == 0.75  # (0.7 + 0.8) / 2
    
    def test_evaluate_batch_partial_results(self):
        """Test batch evaluation with partial results."""
        evaluator = RAGEvaluator()
        
        results = [
            EvaluationResult(
                query="query1",
                retrieval_metrics=RetrievalMetrics(mrr=0.7, ndcg=0.8)
            ),
            EvaluationResult(
                query="query2",
                generation_metrics=GenerationMetrics(faithfulness=0.9)
            )
        ]
        
        result = evaluator.evaluate_batch(results)
        
        assert result["num_queries"] == 2
