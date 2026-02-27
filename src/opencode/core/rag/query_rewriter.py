"""
Query Rewriting for RAG

Provides functionality to rewrite and expand queries for better retrieval.
Implements techniques like HyDE (Hypothetical Document Embeddings) and
query expansion.
"""

import logging
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import asyncio

logger = logging.getLogger(__name__)


class QueryRewriteResult(BaseModel):
    """Result of query rewriting"""
    original_query: str = Field(..., description="Original user query")
    rewritten_queries: List[str] = Field(
        default_factory=list,
        description="Rewritten query variations"
    )
    hypothetical_document: Optional[str] = Field(
        default=None,
        description="Generated hypothetical document (HyDE)"
    )
    expansion_terms: List[str] = Field(
        default_factory=list,
        description="Expanded search terms"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    def get_all_queries(self) -> List[str]:
        """Get all query variations including original"""
        queries = [self.original_query] + self.rewritten_queries
        return list(dict.fromkeys(queries))  # Remove duplicates, preserve order


class QueryRewriter:
    """
    Rewrite queries for improved retrieval.
    
    Techniques:
    - Query expansion: Generate related queries
    - HyDE: Generate hypothetical document
    - Synonym expansion: Add synonyms and related terms
    """
    
    def __init__(
        self,
        llm_client: Optional[Any] = None,
        expansion_count: int = 3,
        use_hyde: bool = True,
    ):
        """
        Initialize the query rewriter.
        
        Args:
            llm_client: LLM client for generating rewrites
            expansion_count: Number of query expansions to generate
            use_hyde: Whether to use HyDE technique
        """
        self.llm_client = llm_client
        self.expansion_count = expansion_count
        self.use_hyde = use_hyde
    
    async def rewrite(self, query: str) -> QueryRewriteResult:
        """
        Rewrite a query for better retrieval.
        
        Args:
            query: Original user query
            
        Returns:
            QueryRewriteResult with rewritten queries
        """
        result = QueryRewriteResult(original_query=query)
        
        if self.llm_client:
            # Generate query expansions
            result.rewritten_queries = await self._expand_query(query)
            
            # Generate hypothetical document
            if self.use_hyde:
                result.hypothetical_document = await self._generate_hyde(query)
        else:
            # Simple rule-based rewriting
            result.rewritten_queries = self._simple_rewrite(query)
        
        return result
    
    async def _expand_query(self, query: str) -> List[str]:
        """Generate query expansions using LLM"""
        prompt = f"""Generate {self.expansion_count} different ways to ask the following question. 
Each variation should use different words but seek the same information.
Return only the questions, one per line.

Question: {query}

Variations:"""
        
        try:
            # This would use the LLM client
            # For now, return simple variations
            return self._simple_rewrite(query)
        except Exception as e:
            logger.error(f"Error expanding query: {e}")
            return []
    
    async def _generate_hyde(self, query: str) -> Optional[str]:
        """Generate hypothetical document for HyDE retrieval"""
        prompt = f"""Write a hypothetical document that would answer the following question.
The document should be informative and contain the key information needed to answer the question.

Question: {query}

Hypothetical Document:"""
        
        try:
            # This would use the LLM client
            # For now, return None
            return None
        except Exception as e:
            logger.error(f"Error generating HyDE: {e}")
            return None
    
    def _simple_rewrite(self, query: str) -> List[str]:
        """Simple rule-based query rewriting"""
        variations = []
        
        # Add question variations
        if not query.startswith(("what", "how", "why", "when", "where", "who")):
            variations.append(f"what is {query}")
            variations.append(f"how does {query} work")
        
        # Remove question words
        words = query.lower().split()
        if words and words[0] in ("what", "how", "why", "when", "where", "who", "is", "are", "do", "does"):
            variations.append(" ".join(words[1:]))
        
        return variations[:self.expansion_count]
    
    def expand_with_synonyms(self, query: str) -> List[str]:
        """Expand query with synonyms (requires external synonym database)"""
        # This would integrate with a synonym database
        # For now, return the original query
        return [query]


class HyDEGenerator:
    """
    Generate Hypothetical Document Embeddings (HyDE).
    
    HyDE generates a hypothetical document that would answer the query,
    then uses that document for retrieval instead of the query itself.
    """
    
    def __init__(
        self,
        llm_client: Optional[Any] = None,
        document_style: str = "informative",
    ):
        """
        Initialize HyDE generator.
        
        Args:
            llm_client: LLM client for generation
            document_style: Style of hypothetical document
        """
        self.llm_client = llm_client
        self.document_style = document_style
    
    async def generate(self, query: str) -> str:
        """
        Generate a hypothetical document for the query.
        
        Args:
            query: User query
            
        Returns:
            Hypothetical document text
        """
        style_prompts = {
            "informative": "Write an informative document that answers the question.",
            "conversational": "Write a conversational explanation that answers the question.",
            "technical": "Write a technical document that explains the answer.",
        }
        
        style_instruction = style_prompts.get(self.document_style, style_prompts["informative"])
        
        prompt = f"""{style_instruction}

Question: {query}

Document:"""
        
        if self.llm_client:
            # Use LLM to generate
            try:
                # This would call the LLM
                pass
            except Exception as e:
                logger.error(f"Error generating HyDE document: {e}")
        
        # Return a placeholder
        return f"[Hypothetical document answering: {query}]"


class QueryDecomposer:
    """
    Decompose complex queries into simpler sub-queries.
    
    Useful for multi-hop reasoning and complex questions.
    """
    
    def __init__(self, llm_client: Optional[Any] = None):
        """
        Initialize query decomposer.
        
        Args:
            llm_client: LLM client for decomposition
        """
        self.llm_client = llm_client
    
    async def decompose(self, query: str) -> List[str]:
        """
        Decompose a complex query into sub-queries.
        
        Args:
            query: Complex user query
            
        Returns:
            List of simpler sub-queries
        """
        prompt = f"""Break down the following complex question into simpler sub-questions.
Each sub-question should be answerable independently.
Return only the sub-questions, one per line.

Question: {query}

Sub-questions:"""
        
        if self.llm_client:
            try:
                # This would call the LLM
                pass
            except Exception as e:
                logger.error(f"Error decomposing query: {e}")
        
        # Return original query if decomposition fails
        return [query]
    
    def is_complex(self, query: str) -> bool:
        """Determine if a query is complex enough to decompose"""
        # Simple heuristics for complexity
        complex_indicators = [
            " and ", " or ", " but ",
            "compare", "contrast", "difference between",
            "multiple", "various", "several",
        ]
        
        query_lower = query.lower()
        return any(indicator in query_lower for indicator in complex_indicators)
