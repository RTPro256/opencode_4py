"""
Reranker RAG Implementation.

RAG with cross-encoder reranking for improved relevance.
Integrated from OpenRAG and RAG_Techniques.

The Reranker approach:
1. Retrieve initial documents (larger set)
2. Rerank using cross-encoder or LLM
3. Select top reranked documents
4. Generate answer with refined context
"""

import asyncio
import logging
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


class RerankerRAGConfig(RAGMethodConfig):
    """Configuration specific to Reranker RAG."""
    
    # Reranker specific settings
    initial_top_k: int = 20  # Retrieve more initially
    final_top_k: int = 5     # After reranking
    reranker_type: str = "llm"  # llm or cross_encoder
    batch_size: int = 5


class RerankerRAG(BaseRAGMethod):
    """
    Reranker RAG implementation.
    
    Reranker RAG improves retrieval by:
    1. Retrieving a larger initial set of documents
    2. Reranking using a more sophisticated model
    3. Selecting the top reranked documents
    4. Generating answer with higher quality context
    
    Based on OpenRAG's RerankerRag and RAG_Techniques' reranking notebook.
    """
    
    method_name = "reranker"
    method_description = "RAG with cross-encoder or LLM reranking"
    
    RERANK_PROMPT = """You are a document relevance ranker. Rate the relevance of the following document to the question on a scale of 0 to 10.

Question: {question}

Document: {document}

Provide only a single number from 0 to 10 as your rating, where:
- 0 = Completely irrelevant
- 10 = Perfectly relevant and comprehensive

Rating:"""
    
    def __init__(
        self,
        config: Optional[RAGMethodConfig] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        vector_store: Optional[VectorStore] = None,
        llm_provider: Optional[LLMProvider] = None,
    ):
        """
        Initialize Reranker RAG.
        
        Args:
            config: Configuration for the RAG method
            embedding_provider: Provider for embeddings
            vector_store: Vector store for document storage
            llm_provider: Provider for LLM generation (used for reranking)
        """
        super().__init__(
            config=config or RerankerRAGConfig(),
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
        Execute a Reranker RAG query.
        
        Args:
            question: The question to answer
            context: Optional context for the query
            
        Returns:
            RAGResult containing the answer and sources
        """
        logger.info(f"Processing Reranker RAG query: {question[:100]}...")
        
        # Get configuration
        initial_top_k = 20
        final_top_k = 5
        if isinstance(self.config, RerankerRAGConfig):
            initial_top_k = self.config.initial_top_k
            final_top_k = self.config.final_top_k
        
        # Step 1: Retrieve initial documents (larger set)
        initial_docs = await self._retrieve(question, top_k=initial_top_k)
        
        if not initial_docs:
            return RAGResult(
                answer="I couldn't find relevant information to answer your question.",
                sources=[],
                confidence=0.0,
                metadata={"method": self.method_name},
            )
        
        # Step 2: Rerank documents
        reranked_docs = await self._rerank(question, initial_docs)
        
        # Step 3: Select top documents
        top_docs = reranked_docs[:final_top_k]
        
        # Step 4: Generate answer
        context_text = self._build_context(top_docs)
        answer = await self._generate_answer(question, context_text)
        
        return RAGResult(
            answer=answer,
            sources=top_docs,
            confidence=self._calculate_confidence(top_docs),
            metadata={
                "method": self.method_name,
                "initial_docs": len(initial_docs),
                "final_docs": len(top_docs),
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
    
    async def _retrieve(
        self,
        query: str,
        top_k: int,
    ) -> List[RetrievedDocument]:
        """Retrieve initial documents."""
        if self.vector_store and self.embedding_provider:
            query_embedding = await self.embedding_provider.embed_query(
                query,
                model=self.config.embedding_model,
            )
            return await self.vector_store.search(
                query_embedding,
                top_k=top_k,
            )
        else:
            return self._keyword_search(query, top_k)
    
    async def _rerank(
        self,
        question: str,
        documents: List[RetrievedDocument],
    ) -> List[RetrievedDocument]:
        """
        Rerank documents using LLM or cross-encoder.
        
        Args:
            question: The question
            documents: Documents to rerank
            
        Returns:
            Reranked documents
        """
        if not self.llm_provider:
            # No reranking possible, return as-is
            return documents
        
        # Score each document
        scored_docs = []
        
        batch_size = 5
        if isinstance(self.config, RerankerRAGConfig):
            batch_size = self.config.batch_size
        
        # Process in batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            batch_scores = await self._score_batch(question, batch)
            
            for doc, score in zip(batch, batch_scores):
                doc.score = score
                scored_docs.append(doc)
        
        # Sort by score
        scored_docs.sort(key=lambda x: x.score, reverse=True)
        
        return scored_docs
    
    async def _score_batch(
        self,
        question: str,
        documents: List[RetrievedDocument],
    ) -> List[float]:
        """
        Score a batch of documents.
        
        Args:
            question: The question
            documents: Documents to score
            
        Returns:
            List of relevance scores
        """
        tasks = [
            self._score_single(question, doc)
            for doc in documents
        ]
        
        return await asyncio.gather(*tasks)
    
    async def _score_single(
        self,
        question: str,
        document: RetrievedDocument,
    ) -> float:
        """
        Score a single document.
        
        Args:
            question: The question
            document: Document to score
            
        Returns:
            Relevance score (0-1)
        """
        prompt = self.RERANK_PROMPT.format(
            question=question,
            document=document.content[:1000],
        )
        
        if not self.llm_provider:
            return document.score
        
        response = await self.llm_provider.generate(
            prompt,
            temperature=0.0,
        )
        
        # Parse score from response
        try:
            # Extract number from response
            score_str = response.strip().split()[0]
            score = float(score_str)
            return min(max(score / 10.0, 0.0), 1.0)
        except (ValueError, IndexError):
            # Default to original score if parsing fails
            return document.score
    
    def _keyword_search(
        self,
        query: str,
        top_k: int,
    ) -> List[RetrievedDocument]:
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
        return [doc for _, doc in scored_docs[:top_k]]
    
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
