"""
Corrective RAG (CRAG) Implementation.

RAG with error correction and knowledge refinement.
Integrated from OpenRAG's CRAG implementation.

The CRAG approach:
1. Retrieve documents for query
2. Evaluate document relevance
3. Correct/rewrite if needed
4. Generate answer with refined context
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

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


class DocumentAction(str, Enum):
    """Actions for document handling in CRAG."""
    KEEP = "keep"           # Document is relevant
    DISCARD = "discard"     # Document is irrelevant
    REWRITE = "rewrite"     # Document needs refinement


@dataclass
class DocumentEvaluation:
    """Result of document evaluation."""
    action: DocumentAction
    relevance_score: float
    reason: str


class CorrectiveRAGConfig(RAGMethodConfig):
    """Configuration specific to Corrective RAG."""
    
    # CRAG specific settings
    relevance_threshold: float = 0.5
    max_corrections: int = 2
    web_search_fallback: bool = False
    rewrite_irrelevant: bool = True


class CorrectiveRAG(BaseRAGMethod):
    """
    Corrective RAG implementation.
    
    CRAG improves retrieval quality by:
    1. Evaluating retrieved documents for relevance
    2. Discarding irrelevant documents
    3. Optionally rewriting queries for better retrieval
    4. Using fallback strategies when needed
    
    Based on OpenRAG's CragAgent implementation.
    
    Reference: "Corrective Retrieval Augmented Generation"
    https://arxiv.org/abs/2401.15884
    """
    
    method_name = "corrective"
    method_description = "Corrective RAG with document evaluation and refinement"
    
    EVALUATION_PROMPT = """You are a document relevance evaluator. Determine if the following document is relevant to the question.

Question: {question}

Document: {document}

Evaluate the document's relevance:
- RELEVANT: Document directly addresses the question
- PARTIALLY_RELEVANT: Document contains some useful information
- IRRELEVANT: Document is not related to the question

Provide your evaluation and a brief reason.

Evaluation:"""
    
    REWRITE_PROMPT = """You are a query optimizer. The original query did not retrieve relevant documents. Rewrite the query to be more specific and likely to retrieve relevant information.

Original query: {query}

Retrieved documents (were not relevant):
{documents}

Rewritten query:"""
    
    def __init__(
        self,
        config: Optional[RAGMethodConfig] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        vector_store: Optional[VectorStore] = None,
        llm_provider: Optional[LLMProvider] = None,
    ):
        """
        Initialize Corrective RAG.
        
        Args:
            config: Configuration for the RAG method
            embedding_provider: Provider for embeddings
            vector_store: Vector store for document storage
            llm_provider: Provider for LLM generation
        """
        super().__init__(
            config=config or CorrectiveRAGConfig(),
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
        Execute a Corrective RAG query.
        
        Args:
            question: The question to answer
            context: Optional context for the query
            
        Returns:
            RAGResult containing the answer and sources
        """
        logger.info(f"Processing CRAG query: {question[:100]}...")
        
        max_corrections = 2
        if isinstance(self.config, CorrectiveRAGConfig):
            max_corrections = self.config.max_corrections
        
        current_query = question
        correction_count = 0
        
        while correction_count <= max_corrections:
            # Step 1: Retrieve documents
            raw_sources = await self._retrieve(current_query)
            
            # Step 2: Evaluate documents
            evaluated_sources = await self._evaluate_documents(question, raw_sources)
            
            # Step 3: Filter to relevant documents
            relevant_sources = [
                doc for doc, eval in evaluated_sources
                if eval.action != DocumentAction.DISCARD
            ]
            
            # Check if we have enough relevant documents
            if relevant_sources:
                # Step 4: Generate answer
                context_text = self._build_context(relevant_sources)
                answer = await self._generate_answer(question, context_text)
                
                return RAGResult(
                    answer=answer,
                    sources=relevant_sources,
                    confidence=self._calculate_confidence(relevant_sources),
                    metadata={
                        "method": self.method_name,
                        "num_sources": len(relevant_sources),
                        "corrections_made": correction_count,
                    },
                    correction_applied=correction_count > 0,
                    correction_type="query_rewrite" if correction_count > 0 else None,
                )
            
            # No relevant documents - try correction
            correction_count += 1
            
            if correction_count <= max_corrections:
                logger.info(f"No relevant documents, attempting correction {correction_count}")
                current_query = await self._rewrite_query(question, raw_sources)
        
        # Failed to find relevant documents
        return RAGResult(
            answer="I couldn't find relevant information to answer your question.",
            sources=[],
            confidence=0.0,
            metadata={
                "method": self.method_name,
                "failed": True,
                "corrections_attempted": correction_count,
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
    
    async def _retrieve(self, query: str) -> List[RetrievedDocument]:
        """Retrieve documents for query."""
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
    
    async def _evaluate_documents(
        self,
        question: str,
        documents: List[RetrievedDocument],
    ) -> List[tuple[RetrievedDocument, DocumentEvaluation]]:
        """
        Evaluate documents for relevance.
        
        Args:
            question: The question
            documents: Retrieved documents
            
        Returns:
            List of (document, evaluation) tuples
        """
        results = []
        
        for doc in documents:
            evaluation = await self._evaluate_single_document(question, doc)
            results.append((doc, evaluation))
        
        return results
    
    async def _evaluate_single_document(
        self,
        question: str,
        document: RetrievedDocument,
    ) -> DocumentEvaluation:
        """Evaluate a single document for relevance."""
        # If no LLM, use simple heuristic
        if not self.llm_provider:
            return self._heuristic_evaluation(question, document)
        
        prompt = self.EVALUATION_PROMPT.format(
            question=question,
            document=document.content[:1000],
        )
        
        response = await self.llm_provider.generate(
            prompt,
            temperature=0.0,
        )
        
        return self._parse_evaluation(response, document.score)
    
    def _heuristic_evaluation(
        self,
        question: str,
        document: RetrievedDocument,
    ) -> DocumentEvaluation:
        """Simple heuristic-based document evaluation."""
        question_terms = set(question.lower().split())
        doc_terms = set(document.content.lower().split())
        
        overlap = len(question_terms & doc_terms)
        relevance = overlap / len(question_terms) if question_terms else 0
        
        threshold = 0.5
        if isinstance(self.config, CorrectiveRAGConfig):
            threshold = self.config.relevance_threshold
        
        if relevance >= threshold:
            return DocumentEvaluation(
                action=DocumentAction.KEEP,
                relevance_score=relevance,
                reason=f"Keyword overlap: {overlap} terms",
            )
        elif relevance >= threshold / 2:
            return DocumentEvaluation(
                action=DocumentAction.REWRITE,
                relevance_score=relevance,
                reason=f"Partial keyword overlap: {overlap} terms",
            )
        else:
            return DocumentEvaluation(
                action=DocumentAction.DISCARD,
                relevance_score=relevance,
                reason="Insufficient keyword overlap",
            )
    
    def _parse_evaluation(
        self,
        response: str,
        base_score: float,
    ) -> DocumentEvaluation:
        """Parse LLM evaluation response."""
        response_lower = response.lower()
        
        if "relevant" in response_lower and "irrelevant" not in response_lower:
            if "partially" in response_lower:
                return DocumentEvaluation(
                    action=DocumentAction.REWRITE,
                    relevance_score=0.5,
                    reason=response,
                )
            return DocumentEvaluation(
                action=DocumentAction.KEEP,
                relevance_score=max(base_score, 0.8),
                reason=response,
            )
        else:
            return DocumentEvaluation(
                action=DocumentAction.DISCARD,
                relevance_score=0.2,
                reason=response,
            )
    
    async def _rewrite_query(
        self,
        original_query: str,
        failed_documents: List[RetrievedDocument],
    ) -> str:
        """
        Rewrite the query for better retrieval.
        
        Args:
            original_query: The original query
            failed_documents: Documents that were not relevant
            
        Returns:
            Rewritten query
        """
        if not self.llm_provider:
            # Simple fallback: add more specific terms
            return f"{original_query} detailed explanation"
        
        docs_text = "\n".join(
            f"- {doc.content[:200]}"
            for doc in failed_documents[:3]
        )
        
        prompt = self.REWRITE_PROMPT.format(
            query=original_query,
            documents=docs_text,
        )
        
        return await self.llm_provider.generate(
            prompt,
            temperature=0.3,
        )
    
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
