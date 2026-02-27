"""
Self-RAG Implementation.

Self-reflective RAG with quality checks and iterative refinement.
Integrated from OpenRAG and RAG_Techniques.

The Self-RAG approach:
1. Retrieve documents for query
2. Generate answer with self-reflection
3. Check if answer is supported by context
4. Optionally re-retrieve and regenerate
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


class ReflectionResult(str, Enum):
    """Results from self-reflection checks."""
    SUPPORTED = "supported"        # Answer is well-supported by context
    PARTIALLY = "partially"        # Answer is partially supported
    UNSUPPORTED = "unsupported"    # Answer is not supported
    IRRELEVANT = "irrelevant"      # Retrieved context is irrelevant


@dataclass
class ReflectionCheck:
    """Result of a reflection check."""
    result: ReflectionResult
    reason: str
    confidence: float
    needs_retrieval: bool = False
    needs_regeneration: bool = False


class SelfRAGConfig(RAGMethodConfig):
    """Configuration specific to Self-RAG."""
    
    # Self-RAG specific settings
    max_iterations: int = 3
    reflection_enabled: bool = True
    retrieval_feedback: bool = True
    generation_feedback: bool = True
    confidence_threshold: float = 0.7


class SelfRAG(BaseRAGMethod):
    """
    Self-reflective RAG implementation.
    
    Self-RAG improves answer quality by:
    1. Reflecting on retrieved documents' relevance
    2. Checking if generated answer is supported by context
    3. Iteratively refining retrieval and generation
    
    Based on OpenRAG's SelfRagAgent and RAG_Techniques' Self-RAG notebook.
    
    Reference: "Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection"
    https://arxiv.org/abs/2310.11511
    """
    
    method_name = "self"
    method_description = "Self-reflective RAG with quality checks and iterative refinement"
    
    # Reflection prompts
    RELEVANCE_CHECK_PROMPT = """You are a relevance checker. Determine if the following documents are relevant to the question.

Question: {question}

Documents:
{documents}

Is the information in the documents relevant to answering the question?
Answer with:
- RELEVANT: if documents contain information to answer the question
- PARTIALLY_RELEVANT: if documents contain some relevant information but may not be sufficient
- IRRELEVANT: if documents are not related to the question

Provide a brief explanation for your answer.

Answer:"""
    
    SUPPORT_CHECK_PROMPT = """You are a fact-checker. Determine if the answer is supported by the provided context.

Question: {question}

Context:
{context}

Answer to check:
{answer}

Is the answer supported by the context?
Answer with:
- SUPPORTED: if all claims in the answer are supported by the context
- PARTIALLY_SUPPORTED: if some claims are supported but others are not
- UNSUPPORTED: if the answer contains claims not found in the context
- HALLUCINATION: if the answer contradicts the context

Provide a brief explanation for your answer.

Answer:"""
    
    def __init__(
        self,
        config: Optional[RAGMethodConfig] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        vector_store: Optional[VectorStore] = None,
        llm_provider: Optional[LLMProvider] = None,
    ):
        """
        Initialize Self-RAG.
        
        Args:
            config: Configuration for the RAG method
            embedding_provider: Provider for embeddings
            vector_store: Vector store for document storage
            llm_provider: Provider for LLM generation
        """
        super().__init__(
            config=config or SelfRAGConfig(),
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
        Execute a Self-RAG query with iterative refinement.
        
        Args:
            question: The question to answer
            context: Optional context for the query
            
        Returns:
            RAGResult containing the answer and sources
        """
        logger.info(f"Processing Self-RAG query: {question[:100]}...")
        
        max_iterations = 3
        if isinstance(self.config, SelfRAGConfig):
            max_iterations = self.config.max_iterations
        
        best_result: Optional[RAGResult] = None
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            logger.info(f"Self-RAG iteration {iteration}/{max_iterations}")
            
            # Step 1: Retrieve documents
            sources = await self._retrieve(question)
            
            # Step 2: Check relevance (if enabled)
            if self._should_check_relevance():
                relevance = await self._check_relevance(question, sources)
                
                if relevance.result == ReflectionResult.IRRELEVANT:
                    logger.info("Retrieved documents irrelevant, trying different query")
                    # Could implement query reformulation here
                    if iteration < max_iterations:
                        continue
            
            # Step 3: Generate answer
            context_text = self._build_context(sources)
            answer = await self._generate_answer(question, context_text)
            
            # Step 4: Check support (if enabled)
            if self._should_check_support():
                support = await self._check_support(question, context_text, answer)
                
                if support.result == ReflectionResult.UNSUPPORTED:
                    logger.info("Answer not supported by context, regenerating")
                    
                    if iteration < max_iterations:
                        # Try again with more context or different approach
                        continue
                
                # Track reflection result
                reflection_passed = support.result == ReflectionResult.SUPPORTED
                reflection_reason = support.reason
            else:
                reflection_passed = True
                reflection_reason = "Reflection checks disabled"
            
            # Create result
            result = RAGResult(
                answer=answer,
                sources=sources,
                confidence=self._calculate_confidence(sources),
                metadata={
                    "method": self.method_name,
                    "iteration": iteration,
                    "num_sources": len(sources),
                },
                self_reflection_passed=reflection_passed,
                reflection_reason=reflection_reason,
            )
            
            # Keep best result
            if best_result is None or result.confidence > best_result.confidence:
                best_result = result
            
            # Check if we have a good enough result
            confidence_threshold = 0.7
            if isinstance(self.config, SelfRAGConfig):
                confidence_threshold = self.config.confidence_threshold
            
            if result.confidence >= confidence_threshold and reflection_passed:
                logger.info("Self-RAG achieved satisfactory result")
                break
        
        return best_result or RAGResult(
            answer="Unable to generate a confident answer.",
            sources=[],
            confidence=0.0,
            metadata={"method": self.method_name, "failed": True},
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
    
    def _should_check_relevance(self) -> bool:
        """Check if relevance checking is enabled."""
        if isinstance(self.config, SelfRAGConfig):
            return self.config.reflection_enabled and self.config.retrieval_feedback
        return False
    
    def _should_check_support(self) -> bool:
        """Check if support checking is enabled."""
        if isinstance(self.config, SelfRAGConfig):
            return self.config.reflection_enabled and self.config.generation_feedback
        return False
    
    async def _retrieve(self, query: str) -> List[RetrievedDocument]:
        """Retrieve relevant documents."""
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
    
    async def _check_relevance(
        self,
        question: str,
        sources: List[RetrievedDocument],
    ) -> ReflectionCheck:
        """Check if retrieved documents are relevant to the question."""
        if not self.llm_provider or not sources:
            return ReflectionCheck(
                result=ReflectionResult.PARTIALLY,
                reason="Cannot check relevance without LLM or sources",
                confidence=0.5,
            )
        
        documents_text = "\n\n".join(
            f"[Doc {i+1}]: {doc.content[:500]}"
            for i, doc in enumerate(sources)
        )
        
        prompt = self.RELEVANCE_CHECK_PROMPT.format(
            question=question,
            documents=documents_text,
        )
        
        response = await self.llm_provider.generate(
            prompt,
            temperature=0.0,
        )
        
        return self._parse_relevance_response(response)
    
    async def _check_support(
        self,
        question: str,
        context: str,
        answer: str,
    ) -> ReflectionCheck:
        """Check if the answer is supported by the context."""
        if not self.llm_provider:
            return ReflectionCheck(
                result=ReflectionResult.PARTIALLY,
                reason="Cannot check support without LLM",
                confidence=0.5,
            )
        
        prompt = self.SUPPORT_CHECK_PROMPT.format(
            question=question,
            context=context[:2000],
            answer=answer,
        )
        
        response = await self.llm_provider.generate(
            prompt,
            temperature=0.0,
        )
        
        return self._parse_support_response(response)
    
    def _parse_relevance_response(self, response: str) -> ReflectionCheck:
        """Parse relevance check response."""
        response_lower = response.lower()
        
        if "relevant" in response_lower and "irrelevant" not in response_lower:
            if "partially" in response_lower:
                return ReflectionCheck(
                    result=ReflectionResult.PARTIALLY,
                    reason=response,
                    confidence=0.6,
                    needs_retrieval=True,
                )
            return ReflectionCheck(
                result=ReflectionResult.SUPPORTED,
                reason=response,
                confidence=0.9,
            )
        else:
            return ReflectionCheck(
                result=ReflectionResult.IRRELEVANT,
                reason=response,
                confidence=0.3,
                needs_retrieval=True,
            )
    
    def _parse_support_response(self, response: str) -> ReflectionCheck:
        """Parse support check response."""
        response_lower = response.lower()
        
        if "supported" in response_lower and "unsupported" not in response_lower:
            if "partially" in response_lower:
                return ReflectionCheck(
                    result=ReflectionResult.PARTIALLY,
                    reason=response,
                    confidence=0.6,
                    needs_regeneration=True,
                )
            return ReflectionCheck(
                result=ReflectionResult.SUPPORTED,
                reason=response,
                confidence=0.9,
            )
        elif "hallucination" in response_lower:
            return ReflectionCheck(
                result=ReflectionResult.UNSUPPORTED,
                reason=response,
                confidence=0.2,
                needs_regeneration=True,
            )
        else:
            return ReflectionCheck(
                result=ReflectionResult.UNSUPPORTED,
                reason=response,
                confidence=0.3,
                needs_regeneration=True,
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

Instructions:
- Provide a clear and accurate answer based ONLY on the provided context
- Do not add information not present in the context
- If the context doesn't contain enough information, say so
- Cite sources using [Document X] notation

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