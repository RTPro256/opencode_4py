"""
Fusion Retrieval RAG Implementation.

Multi-query fusion for improved retrieval coverage.
Integrated from RAG_Techniques.

The Fusion approach:
1. Generate multiple query variations
2. Retrieve documents for each variation
3. Fuse and rank results
4. Generate answer with fused context
"""

import asyncio
import logging
from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .base import (
    BaseRAGMethod,
    EmbeddingProvider,
    LLMProvider,
    RAGMethodConfig,
    RAGResult,
    RetrievedDocument,
    VectorStore,
)

logger = logging.getLogger(__name__)


class FusionRAGConfig(RAGMethodConfig):
    """Configuration specific to Fusion RAG."""
    
    # Fusion specific settings
    num_query_variations: int = 3
    fusion_method: str = "rrf"  # rrf (Reciprocal Rank Fusion) or weighted
    rrf_k: int = 60  # RRF constant
    deduplicate: bool = True
    parallel_retrieval: bool = True


@dataclass
class ScoredDocument:
    """Document with fusion score."""
    document: RetrievedDocument
    rank_scores: List[float]
    fusion_score: float


class FusionRAG(BaseRAGMethod):
    """
    Fusion Retrieval RAG implementation.
    
    Fusion RAG improves retrieval by:
    1. Generating multiple query variations
    2. Retrieving documents for each variation
    3. Fusing results using Reciprocal Rank Fusion (RRF)
    4. Generating answer with diverse context
    
    Based on RAG_Techniques' Fusion Retrieval notebook.
    
    Reference: "Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods"
    https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf
    """
    
    method_name = "fusion"
    method_description = "Multi-query fusion retrieval for improved coverage"
    
    QUERY_VARIATION_PROMPT = """Generate {num} different variations of the following search query. Each variation should use different wording but seek the same information.

Original query: {query}

Generate {num} query variations, one per line:

1."""
    
    def __init__(
        self,
        config: Optional[RAGMethodConfig] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        vector_store: Optional[VectorStore] = None,
        llm_provider: Optional[LLMProvider] = None,
    ):
        """
        Initialize Fusion RAG.
        
        Args:
            config: Configuration for the RAG method
            embedding_provider: Provider for embeddings
            vector_store: Vector store for document storage
            llm_provider: Provider for LLM generation
        """
        super().__init__(
            config=config or FusionRAGConfig(),
            embedding_provider=embedding_provider,
            vector_store=vector_store,
            llm_provider=llm_provider,
        )
        
        self._documents: List[RetrievedDocument] = []
    
    async def query(
        self,
        question: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RAGResult:
        """
        Execute a Fusion RAG query.
        
        Args:
            question: The question to answer
            context: Optional context for the query
            
        Returns:
            RAGResult containing the answer and sources
        """
        logger.info(f"Processing Fusion RAG query: {question[:100]}...")
        
        # Step 1: Generate query variations
        query_variations = await self._generate_query_variations(question)
        query_variations.insert(0, question)  # Include original query
        
        logger.info(f"Generated {len(query_variations)} query variations")
        
        # Step 2: Retrieve documents for each variation
        if isinstance(self.config, FusionRAGConfig) and self.config.parallel_retrieval:
            retrieval_results = await self._parallel_retrieve(query_variations)
        else:
            retrieval_results = await self._sequential_retrieve(query_variations)
        
        # Step 3: Fuse results
        fused_documents = self._fuse_results(retrieval_results)
        
        # Step 4: Select top documents
        top_documents = self._select_top_documents(fused_documents)
        
        if not top_documents:
            return RAGResult(
                answer="I couldn't find relevant information to answer your question.",
                sources=[],
                confidence=0.0,
                metadata={
                    "method": self.method_name,
                    "query_variations": query_variations,
                },
            )
        
        # Step 5: Generate answer
        context_text = self._build_context(top_documents)
        answer = await self._generate_answer(question, context_text)
        
        return RAGResult(
            answer=answer,
            sources=top_documents,
            confidence=self._calculate_confidence(top_documents),
            metadata={
                "method": self.method_name,
                "num_query_variations": len(query_variations),
                "num_sources": len(top_documents),
                "query_variations": query_variations,
            },
        )
    
    async def index_documents(
        self,
        documents: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> int:
        """Index documents for retrieval."""
        import uuid
        
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]
        
        if metadata is None:
            metadata = [{} for _ in documents]
        
        chunks = []
        chunk_metadata = []
        chunk_ids = []
        
        for i, doc in enumerate(documents):
            doc_chunks = self._chunk_document(doc)
            for j, chunk in enumerate(doc_chunks):
                chunks.append(chunk)
                chunk_ids.append(f"{ids[i]}_chunk_{j}")
                chunk_metadata.append({
                    **metadata[i],
                    "parent_doc_id": ids[i],
                    "chunk_index": j,
                })
        
        if self.vector_store and self.embedding_provider:
            embeddings = await self.embedding_provider.embed_texts(
                chunks,
                model=self.config.embedding_model,
            )
            await self.vector_store.add_documents(
                ids=chunk_ids,
                embeddings=embeddings,
                documents=chunks,
                metadata=chunk_metadata,
            )
        else:
            for i, chunk in enumerate(chunks):
                self._documents.append(RetrievedDocument(
                    content=chunk,
                    source=chunk_metadata[i].get("source"),
                    title=chunk_metadata[i].get("title"),
                    metadata=chunk_metadata[i],
                ))
        
        return len(documents)
    
    async def _generate_query_variations(
        self,
        query: str,
    ) -> List[str]:
        """
        Generate variations of the query.
        
        Args:
            query: Original query
            
        Returns:
            List of query variations
        """
        num_variations = 3
        if isinstance(self.config, FusionRAGConfig):
            num_variations = self.config.num_query_variations
        
        if not self.llm_provider:
            # Generate simple variations
            return self._simple_variations(query, num_variations)
        
        prompt = self.QUERY_VARIATION_PROMPT.format(
            num=num_variations,
            query=query,
        )
        
        response = await self.llm_provider.generate(
            prompt,
            temperature=0.7,
        )
        
        # Parse variations from response
        variations = []
        for line in response.strip().split("\n"):
            # Remove numbering
            cleaned = line.strip()
            if cleaned:
                # Remove leading number and period
                parts = cleaned.split(".", 1)
                if len(parts) > 1:
                    cleaned = parts[1].strip()
                if cleaned:
                    variations.append(cleaned)
        
        return variations[:num_variations]
    
    def _simple_variations(
        self,
        query: str,
        num: int,
    ) -> List[str]:
        """Generate simple query variations without LLM."""
        variations = []
        
        # Variation 1: Add question words
        if not query.lower().startswith(("what", "how", "why", "when", "where", "who")):
            variations.append(f"What is {query.lower()}?")
        
        # Variation 2: Rephrase as explanation
        variations.append(f"Explain {query.lower()}")
        
        # Variation 3: Add context request
        variations.append(f"Tell me about {query.lower()}")
        
        return variations[:num]
    
    async def _parallel_retrieve(
        self,
        queries: List[str],
    ) -> List[List[RetrievedDocument]]:
        """
        Retrieve documents for all queries in parallel.
        
        Args:
            queries: List of query variations
            
        Returns:
            List of document lists for each query
        """
        tasks = [self._retrieve_single(q) for q in queries]
        return await asyncio.gather(*tasks)
    
    async def _sequential_retrieve(
        self,
        queries: List[str],
    ) -> List[List[RetrievedDocument]]:
        """
        Retrieve documents for all queries sequentially.
        
        Args:
            queries: List of query variations
            
        Returns:
            List of document lists for each query
        """
        results = []
        for query in queries:
            docs = await self._retrieve_single(query)
            results.append(docs)
        return results
    
    async def _retrieve_single(
        self,
        query: str,
    ) -> List[RetrievedDocument]:
        """Retrieve documents for a single query."""
        if self.vector_store and self.embedding_provider:
            query_embedding = await self.embedding_provider.embed_query(
                query,
                model=self.config.embedding_model,
            )
            return await self.vector_store.search(
                query_embedding,
                top_k=self.config.top_k,
            )
        else:
            return self._keyword_search(query)
    
    def _fuse_results(
        self,
        retrieval_results: List[List[RetrievedDocument]],
    ) -> List[ScoredDocument]:
        """
        Fuse results from multiple retrievals.
        
        Args:
            retrieval_results: Lists of documents from each query
            
        Returns:
            Fused and scored documents
        """
        fusion_method = "rrf"
        rrf_k = 60
        
        if isinstance(self.config, FusionRAGConfig):
            fusion_method = self.config.fusion_method
            rrf_k = self.config.rrf_k
        
        # Track documents by content hash for deduplication
        doc_map: Dict[int, ScoredDocument] = {}
        
        for query_idx, docs in enumerate(retrieval_results):
            for rank, doc in enumerate(docs):
                # Create key for deduplication
                content_key = hash(doc.content[:200])
                
                if content_key not in doc_map:
                    doc_map[content_key] = ScoredDocument(
                        document=doc,
                        rank_scores=[],
                        fusion_score=0.0,
                    )
                
                # Calculate rank score
                if fusion_method == "rrf":
                    rank_score = 1.0 / (rrf_k + rank + 1)
                else:
                    # Weighted by rank
                    rank_score = 1.0 / (rank + 1)
                
                doc_map[content_key].rank_scores.append(rank_score)
        
        # Calculate fusion scores
        for scored_doc in doc_map.values():
            if fusion_method == "rrf":
                scored_doc.fusion_score = sum(scored_doc.rank_scores)
            else:
                # Average of rank scores
                scored_doc.fusion_score = (
                    sum(scored_doc.rank_scores) / len(scored_doc.rank_scores)
                )
        
        # Sort by fusion score
        return sorted(
            doc_map.values(),
            key=lambda x: x.fusion_score,
            reverse=True,
        )
    
    def _select_top_documents(
        self,
        scored_documents: List[ScoredDocument],
    ) -> List[RetrievedDocument]:
        """
        Select top documents from fused results.
        
        Args:
            scored_documents: Fused and scored documents
            
        Returns:
            Top documents
        """
        top_k = self.config.top_k
        
        # Update scores and return documents
        documents = []
        for scored in scored_documents[:top_k]:
            doc = scored.document
            # Update score to fusion score
            doc.score = scored.fusion_score
            documents.append(doc)
        
        return documents
    
    def _keyword_search(self, query: str) -> List[RetrievedDocument]:
        """Simple keyword-based search fallback."""
        query_terms = set(query.lower().split())
        scored_docs = []
        
        for doc in self._documents:
            doc_terms = set(doc.content.lower().split())
            overlap = len(query_terms & doc_terms)
            if overlap > 0:
                score = overlap / len(query_terms)
                scored_docs.append((score, doc))
        
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored_docs[:self.config.top_k]]
    
    def _chunk_document(self, document: str) -> List[str]:
        """Chunk a document into smaller pieces."""
        chunk_size = self.config.chunk_size
        overlap = self.config.chunk_overlap
        
        if len(document) <= chunk_size:
            return [document]
        
        chunks = []
        start = 0
        
        while start < len(document):
            end = start + chunk_size
            chunk = document[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start = end - overlap if end < len(document) else end
        
        return chunks
    
    def _build_context(self, sources: List[RetrievedDocument]) -> str:
        """Build context string from retrieved documents."""
        context_parts = []
        
        for i, doc in enumerate(sources):
            part = f"[Document {i+1}]"
            if doc.title:
                part += f" Title: {doc.title}"
            if doc.source:
                part += f" Source: {doc.source}"
            part += f"\n\n{doc.content}"
            context_parts.append(part)
        
        return "\n\n---\n\n".join(context_parts)
    
    async def _generate_answer(
        self,
        question: str,
        context: str,
    ) -> str:
        """Generate an answer using the LLM."""
        prompt = f"""Based on the following context, please answer the question.

Context:
{context}

Question: {question}

Please provide a clear and accurate answer based only on the provided context.

Answer:"""
        
        if self.llm_provider:
            return await self.llm_provider.generate(
                prompt,
                temperature=self.config.temperature,
            )
        else:
            return f"Based on the retrieved documents:\n\n{context}"
    
    def _calculate_confidence(self, sources: List[RetrievedDocument]) -> float:
        """Calculate confidence score."""
        if not sources:
            return 0.0
        
        avg_score = sum(s.score for s in sources) / len(sources)
        return min(max(avg_score, 0.0), 1.0)
