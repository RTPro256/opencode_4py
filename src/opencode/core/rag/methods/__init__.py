"""
RAG Methods Module.

This module provides various RAG (Retrieval-Augmented Generation) method implementations
integrated from multiple open-source projects including OpenRAG and RAG_Techniques.

Available Methods:
- NaiveRAG: Simple retrieval and generation
- AdvancedRAG: RAG with reranking and query enhancement
- AgenticRAG: Agent-based RAG with tool use
- SelfRAG: Self-reflective RAG with quality checks
- CorrectiveRAG: CRAG with error correction
- GraphRAG: Graph-based RAG for entity relationships
- HyDeRAG: Hypothetical Document Embedding
- FusionRAG: Multi-query fusion retrieval
- RerankerRAG: RAG with cross-encoder reranking
- SemanticChunkingRAG: Semantic-aware chunking
- ContextualRetrievalRAG: Context-aware retrieval
- RAPTORRAG: Hierarchical document summarization
- PropositionChunkingRAG: Proposition-based chunking
- HierarchicalIndicesRAG: Hierarchical document indexing
"""

from .base import BaseRAGMethod, RAGMethodConfig, RAGResult, RetrievedDocument

# Import methods lazily to avoid circular imports
__all__ = [
    "BaseRAGMethod",
    "RAGMethodConfig",
    "RAGResult",
    "RetrievedDocument",
    # Methods are imported lazily via __getattr__
]

_METHOD_REGISTRY = {
    "naive": ".naive_rag:NaiveRAG",
    "advanced": ".advanced_rag:AdvancedRAG",
    "agentic": ".agentic_rag:AgenticRAG",
    "self": ".self_rag:SelfRAG",
    "corrective": ".corrective_rag:CorrectiveRAG",
    "graph": ".graph_rag:GraphRAG",
    "hyde": ".hyde:HyDeRAG",
    "fusion": ".fusion_retrieval:FusionRAG",
    "reranker": ".reranker_rag:RerankerRAG",
    "semantic_chunking": ".semantic_chunking:SemanticChunkingRAG",
    "contextual": ".contextual_retrieval:ContextualRetrievalRAG",
    "raptor": ".raptor:RAPTORRAG",
    "proposition": ".proposition_chunking:PropositionChunkingRAG",
    "hierarchical": ".hierarchical_indices:HierarchicalIndicesRAG",
    "simple": ".base:SimpleRAGMethod",
}


def __getattr__(name: str):
    """Lazily import RAG methods on first access."""
    if name in _METHOD_REGISTRY:
        module_path, class_name = _METHOD_REGISTRY[name].split(":")
        import importlib
        module = importlib.import_module(module_path, package=__name__)
        return getattr(module, class_name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def get_available_methods() -> list[str]:
    """Get list of available RAG method names."""
    return list(_METHOD_REGISTRY.keys())


def create_rag_method(
    method_name: str,
    config: "RAGMethodConfig",
) -> "BaseRAGMethod":
    """
    Factory function to create a RAG method instance.

    Args:
        method_name: Name of the RAG method to create
        config: Configuration for the RAG method

    Returns:
        Configured RAG method instance

    Raises:
        ValueError: If method_name is not recognized
    """
    if method_name not in _METHOD_REGISTRY:
        available = ", ".join(get_available_methods())
        raise ValueError(
            f"Unknown RAG method: {method_name}. Available methods: {available}"
        )

    method_class = __getattr__(method_name)
    return method_class(config)
