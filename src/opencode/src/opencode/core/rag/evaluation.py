"""
RAG Evaluation Module

Provides functionality to evaluate RAG system performance including:
- Retrieval metrics (recall, MRR, NDCG)
- Generation metrics (faithfulness, relevance)
- Ground truth generation
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field
from dataclasses import dataclass
import asyncio

logger = logging.getLogger(__name__)


class RetrievalMetrics(BaseModel):
    """Metrics for retrieval evaluation"""
    recall_at_k: Dict[int, float] = Field(
        default_factory=dict,
        description="Recall@K for different K values"
    )
    mrr: float = Field(default=0.0, description="Mean Reciprocal Rank")
    ndcg: float = Field(default=0.0, description="Normalized Discounted Cumulative Gain")
    precision_at_k: Dict[int, float] = Field(
        default_factory=dict,
        description="Precision@K for different K values"
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "recall_at_k": self.recall_at_k,
            "mrr": self.mrr,
            "ndcg": self.ndcg,
            "precision_at_k": self.precision_at_k,
        }


class GenerationMetrics(BaseModel):
    """Metrics for generation evaluation"""
    faithfulness: float = Field(default=0.0, description="How faithful is the answer to the context")
    relevance: float = Field(default=0.0, description="How relevant is the answer to the query")
    coherence: float = Field(default=0.0, description="How coherent is the answer")
    completeness: float = Field(default=0.0, description="How complete is the answer")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "faithfulness": self.faithfulness,
            "relevance": self.relevance,
            "coherence": self.coherence,
            "completeness": self.completeness,
        }


class EvaluationResult(BaseModel):
    """Complete evaluation result"""
    query: str = Field(..., description="The query being evaluated")
    retrieved_docs: List[str] = Field(default_factory=list, description="Retrieved document IDs")
    generated_answer: str = Field("", description="Generated answer")
    ground_truth: Optional[str] = Field(None, description="Ground truth answer")
    retrieval_metrics: Optional[RetrievalMetrics] = Field(None, description="Retrieval metrics")
    generation_metrics: Optional[GenerationMetrics] = Field(None, description="Generation metrics")
    latency_ms: float = Field(0.0, description="Query latency in milliseconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class GroundTruthEntry(BaseModel):
    """A single ground truth entry"""
    query: str = Field(..., description="The query")
    relevant_docs: List[str] = Field(
        default_factory=list,
        description="List of relevant document IDs"
    )
    answer: Optional[str] = Field(default=None, description="Expected answer")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class RAGEvaluator:
    """
    Evaluate RAG system performance.
    
    Provides methods for:
    - Evaluating retrieval quality
    - Evaluating generation quality
    - Generating ground truth data
    """
    
    def __init__(
        self,
        llm_client: Optional[Any] = None,
        k_values: List[int] = [1, 3, 5, 10],
    ):
        """
        Initialize the evaluator.
        
        Args:
            llm_client: LLM client for generation evaluation
            k_values: K values for recall/precision@K
        """
        self.llm_client = llm_client
        self.k_values = k_values
    
    def evaluate_retrieval(
        self,
        retrieved_ids: List[str],
        relevant_ids: List[str],
    ) -> RetrievalMetrics:
        """
        Evaluate retrieval performance.
        
        Args:
            retrieved_ids: List of retrieved document IDs (ranked)
            relevant_ids: List of relevant document IDs (ground truth)
            
        Returns:
            RetrievalMetrics object
        """
        metrics = RetrievalMetrics()
        
        if not relevant_ids:
            return metrics
        
        relevant_set = set(relevant_ids)
        
        # Calculate Recall@K
        for k in self.k_values:
            if k <= len(retrieved_ids):
                retrieved_at_k = set(retrieved_ids[:k])
                recall = len(retrieved_at_k & relevant_set) / len(relevant_set)
                metrics.recall_at_k[k] = recall
        
        # Calculate MRR
        for i, doc_id in enumerate(retrieved_ids):
            if doc_id in relevant_set:
                metrics.mrr = 1.0 / (i + 1)
                break
        
        # Calculate NDCG
        metrics.ndcg = self._calculate_ndcg(retrieved_ids, relevant_set)
        
        # Calculate Precision@K
        for k in self.k_values:
            if k <= len(retrieved_ids):
                retrieved_at_k = set(retrieved_ids[:k])
                precision = len(retrieved_at_k & relevant_set) / k
                metrics.precision_at_k[k] = precision
        
        return metrics
    
    def _calculate_ndcg(
        self,
        retrieved_ids: List[str],
        relevant_set: set,
    ) -> float:
        """Calculate Normalized Discounted Cumulative Gain"""
        import math
        
        # DCG
        dcg = 0.0
        for i, doc_id in enumerate(retrieved_ids):
            if doc_id in relevant_set:
                dcg += 1.0 / math.log2(i + 2)  # i + 2 because log2(1) = 0
        
        # IDCG (ideal DCG)
        idcg = 0.0
        for i in range(min(len(relevant_set), len(retrieved_ids))):
            idcg += 1.0 / math.log2(i + 2)
        
        if idcg == 0:
            return 0.0
        
        return dcg / idcg
    
    async def evaluate_generation(
        self,
        query: str,
        answer: str,
        context: List[str],
        ground_truth: Optional[str] = None,
    ) -> GenerationMetrics:
        """
        Evaluate generation quality.
        
        Args:
            query: User query
            answer: Generated answer
            context: Retrieved context documents
            ground_truth: Optional ground truth answer
            
        Returns:
            GenerationMetrics object
        """
        metrics = GenerationMetrics()
        
        if self.llm_client:
            # Use LLM for evaluation
            metrics.faithfulness = await self._evaluate_faithfulness(answer, context)
            metrics.relevance = await self._evaluate_relevance(query, answer)
            metrics.coherence = await self._evaluate_coherence(answer)
            
            if ground_truth:
                metrics.completeness = await self._evaluate_completeness(answer, ground_truth)
        else:
            # Simple heuristic evaluation
            metrics.faithfulness = self._heuristic_faithfulness(answer, context)
            metrics.relevance = self._heuristic_relevance(query, answer)
            metrics.coherence = 0.5  # Default
            metrics.completeness = 0.5  # Default
        
        return metrics
    
    async def _evaluate_faithfulness(self, answer: str, context: List[str]) -> float:
        """Evaluate how faithful the answer is to the context"""
        # This would use LLM to evaluate
        # For now, use simple heuristic
        return self._heuristic_faithfulness(answer, context)
    
    async def _evaluate_relevance(self, query: str, answer: str) -> float:
        """Evaluate how relevant the answer is to the query"""
        # This would use LLM to evaluate
        return self._heuristic_relevance(query, answer)
    
    async def _evaluate_coherence(self, answer: str) -> float:
        """Evaluate how coherent the answer is"""
        # This would use LLM to evaluate
        return 0.5
    
    async def _evaluate_completeness(self, answer: str, ground_truth: str) -> float:
        """Evaluate how complete the answer is compared to ground truth"""
        # This would use LLM to evaluate
        return 0.5
    
    def _heuristic_faithfulness(self, answer: str, context: List[str]) -> float:
        """Simple heuristic for faithfulness"""
        if not context:
            return 0.0
        
        combined_context = " ".join(context).lower()
        answer_words = set(answer.lower().split())
        context_words = set(combined_context.split())
        
        if not answer_words:
            return 0.0
        
        overlap = len(answer_words & context_words)
        return min(1.0, overlap / len(answer_words))
    
    def _heuristic_relevance(self, query: str, answer: str) -> float:
        """Simple heuristic for relevance"""
        query_words = set(query.lower().split())
        answer_words = set(answer.lower().split())
        
        if not query_words:
            return 0.0
        
        overlap = len(query_words & answer_words)
        return min(1.0, overlap / len(query_words))
    
    async def generate_ground_truth(
        self,
        documents: List[Dict[str, Any]],
        num_questions: int = 10,
    ) -> List[GroundTruthEntry]:
        """
        Generate ground truth Q&A pairs from documents.
        
        Args:
            documents: List of documents to generate questions from
            num_questions: Number of questions to generate
            
        Returns:
            List of GroundTruthEntry objects
        """
        ground_truth = []
        
        if not self.llm_client:
            logger.warning("No LLM client available for ground truth generation")
            return ground_truth
        
        for doc in documents[:num_questions]:
            # This would use LLM to generate questions
            # For now, create placeholder entries
            entry = GroundTruthEntry(
                query=f"Question about {doc.get('id', 'unknown')}",
                relevant_docs=[doc.get("id", "")],
            )
            ground_truth.append(entry)
        
        return ground_truth
    
    def evaluate_batch(
        self,
        results: List[EvaluationResult],
    ) -> Dict[str, Any]:
        """
        Evaluate a batch of results and compute aggregate metrics.
        
        Args:
            results: List of EvaluationResult objects
            
        Returns:
            Dictionary with aggregate metrics
        """
        if not results:
            return {}
        
        # Aggregate retrieval metrics
        all_recall = {k: [] for k in self.k_values}
        all_precision = {k: [] for k in self.k_values}
        all_mrr = []
        all_ndcg = []
        
        for result in results:
            if result.retrieval_metrics:
                for k, v in result.retrieval_metrics.recall_at_k.items():
                    all_recall[k].append(v)
                for k, v in result.retrieval_metrics.precision_at_k.items():
                    all_precision[k].append(v)
                all_mrr.append(result.retrieval_metrics.mrr)
                all_ndcg.append(result.retrieval_metrics.ndcg)
        
        # Calculate averages
        avg_recall = {k: sum(v) / len(v) if v else 0.0 for k, v in all_recall.items()}
        avg_precision = {k: sum(v) / len(v) if v else 0.0 for k, v in all_precision.items()}
        avg_mrr = sum(all_mrr) / len(all_mrr) if all_mrr else 0.0
        avg_ndcg = sum(all_ndcg) / len(all_ndcg) if all_ndcg else 0.0
        
        # Aggregate generation metrics
        all_faithfulness = []
        all_relevance = []
        all_coherence = []
        all_completeness = []
        
        for result in results:
            if result.generation_metrics:
                all_faithfulness.append(result.generation_metrics.faithfulness)
                all_relevance.append(result.generation_metrics.relevance)
                all_coherence.append(result.generation_metrics.coherence)
                all_completeness.append(result.generation_metrics.completeness)
        
        return {
            "num_queries": len(results),
            "retrieval": {
                "avg_recall_at_k": avg_recall,
                "avg_precision_at_k": avg_precision,
                "avg_mrr": avg_mrr,
                "avg_ndcg": avg_ndcg,
            },
            "generation": {
                "avg_faithfulness": sum(all_faithfulness) / len(all_faithfulness) if all_faithfulness else 0.0,
                "avg_relevance": sum(all_relevance) / len(all_relevance) if all_relevance else 0.0,
                "avg_coherence": sum(all_coherence) / len(all_coherence) if all_coherence else 0.0,
                "avg_completeness": sum(all_completeness) / len(all_completeness) if all_completeness else 0.0,
            },
            "avg_latency_ms": sum(r.latency_ms for r in results) / len(results),
        }
