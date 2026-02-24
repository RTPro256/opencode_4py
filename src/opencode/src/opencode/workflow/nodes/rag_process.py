"""RAG Process Node for retrieval-augmented generation.

This node integrates the RAG pipeline with the workflow engine,
enabling context-aware multi-model patterns.
"""

from typing import Any, Dict, List, Optional
import logging

from opencode.workflow.state import NodeExecutionState, ExecutionStatus

logger = logging.getLogger(__name__)


class RAGProcessNode:
    """
    Node that retrieves relevant documents using RAG.
    
    This node:
    1. Takes a query from input
    2. Retrieves relevant documents from the RAG pipeline
    3. Returns context for use by LLM nodes
    
    Configuration options:
        - collection: Document collection to search
        - top_k: Number of documents to retrieve (default: 5)
        - min_similarity: Minimum similarity score (default: 0.7)
        - query_rewriting: Enable query rewriting (default: False)
        - query_rewriting_method: Method to use - hyde, expansion, rewrite
    
    Example:
        node = RAGProcessNode("rag_1", {
            "collection": "project_docs",
            "top_k": 5,
            "min_similarity": 0.7,
            "query_rewriting": True,
            "query_rewriting_method": "hyde",
        })
        
        result = await node.execute({"query": "How to implement authentication?"})
        # result["context"] contains retrieved documents
        # result["documents"] contains document metadata
    """
    
    node_type = "rag_process"
    
    def __init__(self, node_id: str, config: Dict[str, Any]):
        """Initialize the RAG process node."""
        self.node_id = node_id
        self.config = config
        self._rag_pipeline = None
    
    def _get_rag_pipeline(self) -> Any:
        """Lazy-load RAG pipeline."""
        if self._rag_pipeline is None:
            from opencode.core.rag import RAGPipeline, RAGConfig
            
            rag_config = RAGConfig(
                top_k=self.config.get("top_k", 5),
                min_similarity=self.config.get("min_similarity", 0.7),
            )
            self._rag_pipeline = RAGPipeline(rag_config)
        return self._rag_pipeline
    
    async def execute(self, context: Dict[str, Any]) -> NodeExecutionState:
        """
        Execute RAG retrieval.
        
        Args:
            context: Must contain 'query' or 'input' key
            
        Returns:
            NodeExecutionState with:
                - outputs["context"]: Retrieved documents as text
                - outputs["documents"]: List of document metadata
                - outputs["query"]: Original or rewritten query
                - outputs["document_count"]: Number of documents retrieved
        """
        state = NodeExecutionState(node_id=self.node_id)
        state.start()
        
        try:
            # Get query from context
            query = context.get("query") or context.get("input", "")
            
            if not query:
                state.complete({
                    "context": "",
                    "documents": [],
                    "query": "",
                    "document_count": 0,
                })
                return state
            
            rag_pipeline = self._get_rag_pipeline()
            
            # Optional query rewriting
            if self.config.get("query_rewriting", False):
                try:
                    rewritten = await self._rewrite_query(query)
                    if rewritten:
                        query = rewritten
                        logger.info(f"Query rewritten: {query}")
                except Exception as e:
                    logger.warning(f"Query rewriting failed: {e}")
            
            # Retrieve documents
            documents = await self._retrieve_documents(query, rag_pipeline)
            
            # Format context
            context_text = self._format_context(documents)
            
            state.complete({
                "context": context_text,
                "documents": [self._doc_to_dict(doc) for doc in documents],
                "query": query,
                "document_count": len(documents),
            })
            
            logger.info(f"RAG retrieved {len(documents)} documents for query")
            
        except Exception as e:
            state.fail(str(e))
            logger.error(f"RAG retrieval failed: {e}")
        
        return state
    
    async def _rewrite_query(self, query: str) -> Optional[str]:
        """Rewrite the query using the configured method."""
        method = self.config.get("query_rewriting_method", "hyde")
        use_hyde = method == "hyde"
        
        try:
            from opencode.core.rag import QueryRewriter
            
            rewriter = QueryRewriter(use_hyde=use_hyde)
            result = await rewriter.rewrite(query)
            
            # Get the best rewritten query
            if result.rewritten_queries:
                return result.rewritten_queries[0]
            elif result.hypothetical_document:
                # For HyDE, use the hypothetical document as context
                return query  # Return original, but HyDE doc will be used for retrieval
            elif isinstance(result, str):
                return result
            
        except ImportError:
            logger.warning("QueryRewriter not available")
        except Exception as e:
            logger.warning(f"Query rewriting error: {e}")
        
        return None
    
    async def _retrieve_documents(self, query: str, pipeline: Any) -> List[Any]:
        """Retrieve documents from the RAG pipeline."""
        top_k = self.config.get("top_k", 5)
        threshold = self.config.get("min_similarity", 0.7)
        
        try:
            # Try the retrieve method
            if hasattr(pipeline, 'retrieve'):
                return await pipeline.retrieve(
                    query,
                    top_k=top_k,
                    min_similarity=threshold,
                )
            # Fallback to retriever
            elif hasattr(pipeline, 'retriever'):
                return await pipeline.retriever.retrieve(
                    query,
                    top_k=top_k,
                )
        except Exception as e:
            logger.error(f"Document retrieval error: {e}")
        
        return []
    
    def _format_context(self, documents: List[Any]) -> str:
        """Format retrieved documents into context string."""
        if not documents:
            return ""
        
        parts = []
        for i, doc in enumerate(documents, 1):
            content = getattr(doc, 'content', str(doc))
            metadata = getattr(doc, 'metadata', {})
            source = metadata.get('source', f'Document {i}')
            
            parts.append(f"[{source}]\n{content}")
        
        return "\n\n".join(parts)
    
    def _doc_to_dict(self, doc: Any) -> Dict[str, Any]:
        """Convert document to dictionary."""
        if hasattr(doc, 'to_dict'):
            return doc.to_dict()
        elif hasattr(doc, 'model_dump'):
            return doc.model_dump()
        elif hasattr(doc, '__dict__'):
            return {
                'content': getattr(doc, 'content', ''),
                'metadata': getattr(doc, 'metadata', {}),
                'score': getattr(doc, 'score', 0.0),
            }
        else:
            return {'content': str(doc)}
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get the node schema for the registry."""
        return {
            "node_type": cls.node_type,
            "display_name": "RAG Process",
            "description": "Retrieve documents using RAG for context-aware generation",
            "category": "retrieval",
            "inputs": [
                {"name": "query", "type": "string", "required": True, "description": "Search query"},
                {"name": "input", "type": "string", "required": False, "description": "Alternative query input"},
            ],
            "outputs": [
                {"name": "context", "type": "string", "description": "Retrieved documents as text"},
                {"name": "documents", "type": "array", "description": "List of document metadata"},
                {"name": "query", "type": "string", "description": "Original or rewritten query"},
                {"name": "document_count", "type": "integer", "description": "Number of documents retrieved"},
            ],
            "config": {
                "collection": {
                    "type": "string",
                    "default": "default",
                    "description": "Document collection to search",
                },
                "top_k": {
                    "type": "integer",
                    "default": 5,
                    "description": "Number of documents to retrieve",
                },
                "min_similarity": {
                    "type": "float",
                    "default": 0.7,
                    "description": "Minimum similarity score",
                },
                "query_rewriting": {
                    "type": "boolean",
                    "default": False,
                    "description": "Enable query rewriting",
                },
                "query_rewriting_method": {
                    "type": "string",
                    "default": "hyde",
                    "enum": ["hyde", "expansion", "rewrite"],
                    "description": "Query rewriting method",
                },
            },
        }
