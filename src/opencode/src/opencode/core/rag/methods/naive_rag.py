"""
Naive RAG Implementation.

A simple but effective RAG method with basic retrieval and generation.
Integrated from OpenRAG's NaiveRagAgent.

This is the foundational RAG approach:
1. Index documents with chunking
2. Embed query
3. Retrieve similar chunks
4. Generate answer with context
"""

import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional

from .base import (
    BaseRAGMethod,
    ChunkingStrategy,
    EmbeddingProvider,
    LLMProvider,
    RAGMethodConfig,
    RAGResult,
    RetrievedDocument,
    RetrievalStrategy,
    VectorStore,
)

logger = logging.getLogger(__name__)


class NaiveRAGConfig(RAGMethodConfig):
    """Configuration specific to Naive RAG."""
    
    # Naive RAG specific settings
    include_source_in_response: bool = True
    max_context_length: int = 4000
    separator: str = "\n\n---\n\n"


class NaiveRAG(BaseRAGMethod):
    """
    Naive RAG implementation.
    
    This is the simplest form of RAG that:
    1. Chunks documents into fixed-size pieces
    2. Embeds chunks using the configured embedding model
    3. Retrieves top-k similar chunks for a query
    4. Generates an answer using the retrieved context
    
    Based on OpenRAG's NaiveRagAgent implementation.
    """
    
    method_name = "naive"
    method_description = "Simple RAG with basic retrieval and generation"
    
    def __init__(
        self,
        config: Optional[RAGMethodConfig] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        vector_store: Optional[VectorStore] = None,
        llm_provider: Optional[LLMProvider] = None,
    ):
        """
        Initialize Naive RAG.
        
        Args:
            config: Configuration for the RAG method
            embedding_provider: Provider for embeddings
            vector_store: Vector store for document storage
            llm_provider: Provider for LLM generation
        """
        super().__init__(
            config=config or NaiveRAGConfig(),
            embedding_provider=embedding_provider,
            vector_store=vector_store,
            llm_provider=llm_provider,
        )
        
        # In-memory document store for fallback
        self._documents: List[RetrievedDocument] = []
        self._embeddings: List[List[float]] = []
    
    async def query(
        self,
        question: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RAGResult:
        """
        Execute a Naive RAG query.
        
        Args:
            question: The question to answer
            context: Optional context for the query
            
        Returns:
            RAGResult containing the answer and sources
        """
        logger.info(f"Processing query: {question[:100]}...")
        
        # Step 1: Retrieve relevant documents
        sources = await self._retrieve(question)
        
        if not sources:
            return RAGResult(
                answer="I don't have any relevant information to answer your question.",
                sources=[],
                confidence=0.0,
                metadata={"method": self.method_name, "no_sources": True},
            )
        
        # Step 2: Build context from sources
        context_text = self._build_context(sources)
        
        # Step 3: Generate answer
        answer = await self._generate_answer(question, context_text)
        
        # Step 4: Calculate confidence
        confidence = self._calculate_confidence(sources)
        
        return RAGResult(
            answer=answer,
            sources=sources,
            confidence=confidence,
            metadata={
                "method": self.method_name,
                "num_sources": len(sources),
                "context_length": len(context_text),
            },
        )
    
    async def index_documents(
        self,
        documents: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> int:
        """
        Index documents for retrieval.
        
        Args:
            documents: List of document texts
            metadata: Optional metadata for each document
            ids: Optional IDs for each document
            
        Returns:
            Number of documents indexed
        """
        logger.info(f"Indexing {len(documents)} documents...")
        
        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]
        
        # Prepare metadata
        if metadata is None:
            metadata = [{} for _ in documents]
        
        # Chunk documents
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
                    "total_chunks": len(doc_chunks),
                })
        
        logger.info(f"Created {len(chunks)} chunks from {len(documents)} documents")
        
        # Index chunks
        if self.vector_store and self.embedding_provider:
            # Use vector store
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
            # Fallback to in-memory storage
            for i, chunk in enumerate(chunks):
                self._documents.append(RetrievedDocument(
                    content=chunk,
                    source=chunk_metadata[i].get("source"),
                    title=chunk_metadata[i].get("title"),
                    metadata=chunk_metadata[i],
                ))
        
        return len(documents)
    
    async def _retrieve(self, query: str) -> List[RetrievedDocument]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: The query string
            
        Returns:
            List of retrieved documents
        """
        if self.vector_store and self.embedding_provider:
            # Use vector store for retrieval
            query_embedding = await self.embedding_provider.embed_query(
                query,
                model=self.config.embedding_model,
            )
            
            results = await self.vector_store.search(
                query_embedding,
                top_k=self.config.top_k,
            )
            
            return results
        else:
            # Fallback to simple keyword search
            return self._keyword_search(query)
    
    def _keyword_search(self, query: str) -> List[RetrievedDocument]:
        """
        Simple keyword-based search fallback.
        
        Args:
            query: The query string
            
        Returns:
            List of retrieved documents
        """
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
        """
        Chunk a document into smaller pieces.
        
        Args:
            document: The document text
            
        Returns:
            List of document chunks
        """
        chunk_size = self.config.chunk_size
        overlap = self.config.chunk_overlap
        
        if len(document) <= chunk_size:
            return [document]
        
        chunks = []
        start = 0
        
        while start < len(document):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(document):
                # Look for sentence boundary within last 100 chars
                boundary = document.rfind(".", start, end)
                if boundary > start + chunk_size // 2:
                    end = boundary + 1
            
            chunk = document[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap if end < len(document) else end
        
        return chunks
    
    def _build_context(self, sources: List[RetrievedDocument]) -> str:
        """
        Build context string from retrieved documents.
        
        Args:
            sources: List of retrieved documents
            
        Returns:
            Context string for generation
        """
        if isinstance(self.config, NaiveRAGConfig):
            separator = self.config.separator
            max_length = self.config.max_context_length
        else:
            separator = "\n\n---\n\n"
            max_length = 4000
        
        context_parts = []
        current_length = 0
        
        for i, doc in enumerate(sources):
            part = f"[Document {i+1}]"
            if doc.title:
                part += f" Title: {doc.title}"
            if doc.source:
                part += f" Source: {doc.source}"
            part += f"\n\n{doc.content}"
            
            if current_length + len(part) > max_length:
                break
            
            context_parts.append(part)
            current_length += len(part)
        
        return separator.join(context_parts)
    
    async def _generate_answer(
        self,
        question: str,
        context: str,
    ) -> str:
        """
        Generate an answer using the LLM.
        
        Args:
            question: The question to answer
            context: The context from retrieved documents
            
        Returns:
            Generated answer
        """
        prompt = self._build_prompt(question, context)
        
        if self.llm_provider:
            return await self.llm_provider.generate(
                prompt,
                temperature=self.config.temperature,
            )
        else:
            # Fallback: return context
            return f"Based on the retrieved documents:\n\n{context}"
    
    def _build_prompt(self, question: str, context: str) -> str:
        """
        Build the generation prompt.
        
        Args:
            question: The question to answer
            context: The context from retrieved documents
            
        Returns:
            Formatted prompt string
        """
        return f"""You are a helpful assistant. Answer the question based on the provided context.

Context:
{context}

Question: {question}

Instructions:
- Provide a clear and accurate answer based only on the provided context
- If the context doesn't contain enough information, say so
- Cite sources when possible using [Document X] notation
- Be concise but comprehensive

Answer:"""
    
    def _calculate_confidence(self, sources: List[RetrievedDocument]) -> float:
        """
        Calculate confidence score based on retrieval quality.
        
        Args:
            sources: List of retrieved documents
            
        Returns:
            Confidence score between 0 and 1
        """
        if not sources:
            return 0.0
        
        # Base confidence on number and scores of sources
        num_sources = len(sources)
        avg_score = sum(s.score for s in sources) / num_sources if sources else 0
        
        # More sources = higher confidence (up to a point)
        source_factor = min(num_sources / self.config.top_k, 1.0)
        
        # Combine factors
        confidence = (avg_score * 0.6 + source_factor * 0.4)
        
        return min(max(confidence, 0.0), 1.0)
