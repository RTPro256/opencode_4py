"""
HyDe (Hypothetical Document Embedding) RAG Implementation.

Generates hypothetical documents to improve retrieval accuracy.
Integrated from RAG_Techniques.

The HyDe approach:
1. Generate a hypothetical answer to the query
2. Embed the hypothetical document
3. Retrieve similar real documents
4. Generate final answer with retrieved context
"""

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


class HyDeConfig(RAGMethodConfig):
    """Configuration specific to HyDe RAG."""
    
    # HyDe specific settings
    num_hypothetical_docs: int = 1
    hypothetical_max_tokens: int = 500
    include_original_query: bool = True
    combine_strategy: str = "average"  # average, max, or concat


class HyDeRAG(BaseRAGMethod):
    """
    Hypothetical Document Embedding (HyDe) RAG implementation.
    
    HyDe improves retrieval by:
    1. Generating a hypothetical answer to the query
    2. Using the hypothetical document's embedding for retrieval
    3. This bridges the gap between query and document space
    
    Based on RAG_Techniques HyDe implementation.
    
    Reference: "Precise Zero-Shot Dense Retrieval without Relevance Labels"
    https://arxiv.org/abs/2212.10496
    """
    
    method_name = "hyde"
    method_description = "Hypothetical Document Embedding for improved retrieval"
    
    # Prompt templates for hypothetical document generation
    HYPOTHETICAL_PROMPTS = {
        "default": """Generate a detailed answer to the following question. The answer should be informative and comprehensive, as if it were written by an expert.

Question: {question}

Write a detailed answer (around 200-300 words):""",

        "scientific": """Generate a scientific explanation answering the following question. Include relevant facts, mechanisms, and evidence.

Question: {question}

Scientific explanation:""",

        "technical": """Generate a technical document answering the following question. Include code examples, architecture details, and best practices where relevant.

Question: {question}

Technical documentation:""",
    }
    
    def __init__(
        self,
        config: Optional[RAGMethodConfig] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        vector_store: Optional[VectorStore] = None,
        llm_provider: Optional[LLMProvider] = None,
    ):
        """
        Initialize HyDe RAG.
        
        Args:
            config: Configuration for the RAG method
            embedding_provider: Provider for embeddings
            vector_store: Vector store for document storage
            llm_provider: Provider for LLM generation
        """
        super().__init__(
            config=config or HyDeConfig(),
            embedding_provider=embedding_provider,
            vector_store=vector_store,
            llm_provider=llm_provider,
        )
        
        # In-memory document store for fallback
        self._documents: List[RetrievedDocument] = []
    
    async def query(
        self,
        question: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RAGResult:
        """
        Execute a HyDe RAG query.
        
        Args:
            question: The question to answer
            context: Optional context for the query
            
        Returns:
            RAGResult containing the answer and sources
        """
        logger.info(f"Processing HyDe query: {question[:100]}...")
        
        # Step 1: Generate hypothetical document(s)
        hypothetical_docs = await self._generate_hypothetical_documents(question)
        logger.info(f"Generated {len(hypothetical_docs)} hypothetical documents")
        
        # Step 2: Embed hypothetical documents
        if self.embedding_provider:
            hypothetical_embeddings = await self.embedding_provider.embed_texts(
                hypothetical_docs,
                model=self.config.embedding_model,
            )
            
            # Combine embeddings based on strategy
            combined_embedding = self._combine_embeddings(hypothetical_embeddings)
            
            # Optionally include original query embedding
            if isinstance(self.config, HyDeConfig) and self.config.include_original_query:
                query_embedding = await self.embedding_provider.embed_query(
                    question,
                    model=self.config.embedding_model,
                )
                combined_embedding = self._average_embeddings(
                    [combined_embedding, query_embedding]
                )
        else:
            combined_embedding = None
        
        # Step 3: Retrieve using combined embedding
        if self.vector_store and combined_embedding:
            sources = await self.vector_store.search(
                combined_embedding,
                top_k=self.config.top_k,
            )
        else:
            # Fallback to keyword search on hypothetical docs
            sources = self._keyword_search(" ".join(hypothetical_docs))
        
        if not sources:
            return RAGResult(
                answer="I don't have any relevant information to answer your question.",
                sources=[],
                confidence=0.0,
                metadata={
                    "method": self.method_name,
                    "no_sources": True,
                    "hypothetical_docs": hypothetical_docs,
                },
            )
        
        # Step 4: Generate final answer
        context_text = self._build_context(sources)
        answer = await self._generate_answer(question, context_text)
        
        return RAGResult(
            answer=answer,
            sources=sources,
            confidence=self._calculate_confidence(sources),
            metadata={
                "method": self.method_name,
                "num_sources": len(sources),
                "hypothetical_docs": hypothetical_docs,
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
        import uuid
        
        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]
        
        # Prepare metadata
        if metadata is None:
            metadata = [{} for _ in documents]
        
        # Chunk and index
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
    
    async def _generate_hypothetical_documents(
        self,
        question: str,
    ) -> List[str]:
        """
        Generate hypothetical documents for the query.
        
        Args:
            question: The question to answer
            
        Returns:
            List of hypothetical document texts
        """
        if not self.llm_provider:
            # Fallback: use question as hypothetical doc
            return [question]
        
        num_docs = 1
        max_tokens = 500
        
        if isinstance(self.config, HyDeConfig):
            num_docs = self.config.num_hypothetical_docs
            max_tokens = self.config.hypothetical_max_tokens
        
        hypothetical_docs = []
        
        for i in range(num_docs):
            prompt = self.HYPOTHETICAL_PROMPTS["default"].format(
                question=question
            )
            
            doc = await self.llm_provider.generate(
                prompt,
                temperature=0.7,  # Higher temperature for diversity
                max_tokens=max_tokens,
            )
            
            hypothetical_docs.append(doc.strip())
        
        return hypothetical_docs
    
    def _combine_embeddings(
        self,
        embeddings: List[List[float]],
    ) -> List[float]:
        """
        Combine multiple embeddings into one.
        
        Args:
            embeddings: List of embedding vectors
            
        Returns:
            Combined embedding vector
        """
        if not embeddings:
            return []
        
        if len(embeddings) == 1:
            return embeddings[0]
        
        strategy = "average"
        if isinstance(self.config, HyDeConfig):
            strategy = self.config.combine_strategy
        
        if strategy == "average":
            return self._average_embeddings(embeddings)
        elif strategy == "max":
            return self._max_pool_embeddings(embeddings)
        else:
            # Default to average
            return self._average_embeddings(embeddings)
    
    def _average_embeddings(
        self,
        embeddings: List[List[float]],
    ) -> List[float]:
        """Average multiple embeddings."""
        if not embeddings:
            return []
        
        n = len(embeddings)
        dim = len(embeddings[0])
        result = [0.0] * dim
        
        for emb in embeddings:
            for i in range(dim):
                result[i] += emb[i]
        
        return [x / n for x in result]
    
    def _max_pool_embeddings(
        self,
        embeddings: List[List[float]],
    ) -> List[float]:
        """Max-pool multiple embeddings."""
        if not embeddings:
            return []
        
        dim = len(embeddings[0])
        result = list(embeddings[0])
        
        for emb in embeddings[1:]:
            for i in range(dim):
                result[i] = max(result[i], emb[i])
        
        return result
    
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
If the context doesn't contain enough information, say so.

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
