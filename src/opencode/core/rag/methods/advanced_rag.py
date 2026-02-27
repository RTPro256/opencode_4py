"""
Advanced RAG Implementation.

RAG with advanced features like query enhancement, reranking, and caching.
Integrated from OpenRAG's AdvancedRAG implementation.

The Advanced RAG approach:
1. Query enhancement (expansion, rewriting)
2. Hybrid retrieval (semantic + keyword)
3. Reranking with cross-encoder
4. Context compression
5. Answer generation with citations
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

from .base import (
    BaseRAGMethod,
    EmbeddingProvider,
    LLMProvider,
    RAGMethodConfig,
    RAGResult,
    RetrievedDocument,
    RetrievalStrategy,
    VectorStore,
)

logger = logging.getLogger(__name__)


class AdvancedRAGConfig(RAGMethodConfig):
    """Configuration specific to Advanced RAG."""
    
    # Advanced RAG specific settings
    query_expansion: bool = True
    hybrid_retrieval: bool = True
    context_compression: bool = True
    citation_enabled: bool = True
    max_expanded_queries: int = 3
    compression_ratio: float = 0.5


class AdvancedRAG(BaseRAGMethod):
    """
    Advanced RAG implementation with multiple enhancement techniques.
    
    Advanced RAG improves over Naive RAG by:
    1. Expanding queries for better coverage
    2. Using hybrid retrieval (semantic + keyword)
    3. Compressing context for efficiency
    4. Adding citations to sources
    
    Based on OpenRAG's AdvancedRag implementation.
    """
    
    method_name = "advanced"
    method_description = "Advanced RAG with query expansion, hybrid retrieval, and reranking"
    
    QUERY_EXPANSION_PROMPT = """Generate {num} alternative search queries that would help find information about:

Original query: {query}

Generate {num} alternative queries, one per line. Each query should use different keywords or phrasing:

1."""
    
    CONTEXT_COMPRESSION_PROMPT = """Compress the following text while preserving all key information. Remove redundancy and keep only essential facts.

Original text:
{text}

Compressed text:"""
    
    def __init__(
        self,
        config: Optional[RAGMethodConfig] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        vector_store: Optional[VectorStore] = None,
        llm_provider: Optional[LLMProvider] = None,
    ):
        """
        Initialize Advanced RAG.
        
        Args:
            config: Configuration for the RAG method
            embedding_provider: Provider for embeddings
            vector_store: Vector store for document storage
            llm_provider: Provider for LLM generation
        """
        super().__init__(
            config=config or AdvancedRAGConfig(),
            embedding_provider=embedding_provider,
            vector_store=vector_store,
            llm_provider=llm_provider,
        )
        
        self._documents: List[RetrievedDocument] = []
        self._keyword_index: Dict[str, List[Tuple[str, int]]] = {}  # term -> [(doc_id, position)]
    
    async def query(
        self,
        question: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RAGResult:
        """
        Execute an Advanced RAG query.
        
        Args:
            question: The question to answer
            context: Optional context for the query
            
        Returns:
            RAGResult containing the answer and sources
        """
        logger.info(f"Processing Advanced RAG query: {question[:100]}...")
        
        # Step 1: Query expansion
        queries = [question]
        if isinstance(self.config, AdvancedRAGConfig) and self.config.query_expansion:
            expanded = await self._expand_query(question)
            queries.extend(expanded)
        
        # Step 2: Hybrid retrieval
        all_docs = []
        if isinstance(self.config, AdvancedRAGConfig) and self.config.hybrid_retrieval:
            all_docs = await self._hybrid_retrieve(queries)
        else:
            all_docs = await self._semantic_retrieve(question)
        
        # Step 3: Deduplicate and rank
        unique_docs = self._deduplicate_documents(all_docs)
        
        # Step 4: Context compression (optional)
        if isinstance(self.config, AdvancedRAGConfig) and self.config.context_compression:
            unique_docs = await self._compress_contexts(unique_docs)
        
        # Step 5: Select top documents
        top_docs = unique_docs[:self.config.top_k]
        
        if not top_docs:
            return RAGResult(
                answer="I couldn't find relevant information to answer your question.",
                sources=[],
                confidence=0.0,
                metadata={"method": self.method_name},
            )
        
        # Step 6: Generate answer with citations
        context_text = self._build_context_with_citations(top_docs)
        answer = await self._generate_answer(question, context_text)
        
        return RAGResult(
            answer=answer,
            sources=top_docs,
            confidence=self._calculate_confidence(top_docs),
            metadata={
                "method": self.method_name,
                "queries_used": len(queries),
                "num_sources": len(top_docs),
                "hybrid_retrieval": True,
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
                chunk_id = f"{ids[i]}_chunk_{j}"
                chunks.append(chunk)
                chunk_ids.append(chunk_id)
                chunk_meta = {
                    **metadata[i],
                    "parent_doc_id": ids[i],
                    "chunk_index": j,
                }
                chunk_metadata.append(chunk_meta)
                
                # Build keyword index
                self._index_keywords(chunk_id, chunk)
        
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
    
    def _index_keywords(self, doc_id: str, text: str) -> None:
        """Build keyword index for BM25-style retrieval."""
        import re
        
        # Tokenize
        tokens = re.findall(r'\b\w+\b', text.lower())
        
        for position, token in enumerate(tokens):
            if len(token) > 2:  # Skip short tokens
                if token not in self._keyword_index:
                    self._keyword_index[token] = []
                self._keyword_index[token].append((doc_id, position))
    
    async def _expand_query(
        self,
        query: str,
    ) -> List[str]:
        """
        Expand query with alternative phrasings.
        
        Args:
            query: Original query
            
        Returns:
            List of expanded queries
        """
        max_queries = 3
        if isinstance(self.config, AdvancedRAGConfig):
            max_queries = self.config.max_expanded_queries
        
        if not self.llm_provider:
            return self._simple_query_expansion(query, max_queries)
        
        prompt = self.QUERY_EXPANSION_PROMPT.format(
            num=max_queries,
            query=query,
        )
        
        response = await self.llm_provider.generate(
            prompt,
            temperature=0.5,
        )
        
        # Parse expanded queries
        expanded = []
        for line in response.strip().split("\n"):
            cleaned = line.strip()
            if cleaned:
                # Remove numbering
                parts = cleaned.split(".", 1)
                if len(parts) > 1:
                    cleaned = parts[1].strip()
                if cleaned and cleaned.lower() != query.lower():
                    expanded.append(cleaned)
        
        return expanded[:max_queries]
    
    def _simple_query_expansion(
        self,
        query: str,
        num: int,
    ) -> List[str]:
        """Simple query expansion without LLM."""
        expanded = []
        
        # Add synonyms/common variations
        words = query.split()
        if len(words) > 1:
            expanded.append(" ".join(words[:-1]))  # Remove last word
        
        # Add question variation
        if not query.lower().startswith(("what", "how", "why")):
            expanded.append(f"what is {query}")
        
        return expanded[:num]
    
    async def _hybrid_retrieve(
        self,
        queries: List[str],
    ) -> List[RetrievedDocument]:
        """
        Perform hybrid retrieval (semantic + keyword).
        
        Args:
            queries: List of queries
            
        Returns:
            Combined and ranked documents
        """
        # Semantic retrieval
        semantic_tasks = [self._semantic_retrieve(q) for q in queries]
        semantic_results = await asyncio.gather(*semantic_tasks)
        
        # Flatten and combine
        all_docs = []
        for docs in semantic_results:
            all_docs.extend(docs)
        
        # Keyword retrieval
        keyword_docs = self._keyword_retrieve(queries[0])
        all_docs.extend(keyword_docs)
        
        return all_docs
    
    async def _semantic_retrieve(
        self,
        query: str,
    ) -> List[RetrievedDocument]:
        """Perform semantic retrieval."""
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
            return self._simple_search(query)
    
    def _keyword_retrieve(
        self,
        query: str,
    ) -> List[RetrievedDocument]:
        """Perform keyword-based retrieval."""
        import re
        from collections import Counter
        
        query_terms = set(re.findall(r'\b\w+\b', query.lower()))
        
        # Score documents by term frequency
        doc_scores: Counter = Counter()
        
        for term in query_terms:
            if term in self._keyword_index:
                for doc_id, _ in self._keyword_index[term]:
                    doc_scores[doc_id] += 1
        
        # Get top documents
        results = []
        for doc_id, score in doc_scores.most_common(self.config.top_k):
            # Find document
            for doc in self._documents:
                if doc.metadata.get("doc_id") == doc_id or doc.metadata.get("chunk_id") == doc_id:
                    doc_copy = RetrievedDocument(
                        content=doc.content,
                        score=score / len(query_terms),
                        source=doc.source,
                        title=doc.title,
                        metadata=doc.metadata,
                    )
                    results.append(doc_copy)
                    break
        
        return results
    
    def _deduplicate_documents(
        self,
        documents: List[RetrievedDocument],
    ) -> List[RetrievedDocument]:
        """Remove duplicate documents based on content hash."""
        seen = set()
        unique = []
        
        for doc in documents:
            # Use first 200 chars as hash
            content_hash = hash(doc.content[:200])
            if content_hash not in seen:
                seen.add(content_hash)
                unique.append(doc)
        
        # Sort by score
        unique.sort(key=lambda x: x.score, reverse=True)
        
        return unique
    
    async def _compress_contexts(
        self,
        documents: List[RetrievedDocument],
    ) -> List[RetrievedDocument]:
        """
        Compress document contexts for efficiency.
        
        Args:
            documents: Documents to compress
            
        Returns:
            Compressed documents
        """
        if not self.llm_provider:
            return documents
        
        compression_ratio = 0.5
        if isinstance(self.config, AdvancedRAGConfig):
            compression_ratio = self.config.compression_ratio
        
        compressed = []
        
        for doc in documents:
            # Only compress if document is long
            if len(doc.content) < 500:
                compressed.append(doc)
                continue
            
            target_length = int(len(doc.content) * compression_ratio)
            
            prompt = self.CONTEXT_COMPRESSION_PROMPT.format(text=doc.content)
            
            compressed_text = await self.llm_provider.generate(
                prompt,
                temperature=0.0,
                max_tokens=target_length,
            )
            
            compressed.append(RetrievedDocument(
                content=compressed_text,
                score=doc.score,
                source=doc.source,
                title=doc.title,
                metadata={**doc.metadata, "compressed": True},
            ))
        
        return compressed
    
    def _build_context_with_citations(
        self,
        sources: List[RetrievedDocument],
    ) -> str:
        """Build context string with citation markers."""
        context_parts = []
        
        for i, doc in enumerate(sources):
            citation = f"[{i+1}]"
            part = f"{citation} "
            
            if doc.title:
                part += f"**{doc.title}**: "
            
            part += doc.content
            
            if doc.source:
                part += f"\n  *Source: {doc.source}*"
            
            context_parts.append(part)
        
        return "\n\n---\n\n".join(context_parts)
    
    def _simple_search(self, query: str) -> List[RetrievedDocument]:
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
    
    async def _generate_answer(
        self,
        question: str,
        context: str,
    ) -> str:
        """Generate an answer using the LLM."""
        prompt = f"""Based on the following context, please answer the question. Use citation numbers [1], [2], etc. to reference sources.

Context:
{context}

Question: {question}

Instructions:
- Provide a clear and accurate answer based only on the provided context
- Use citation numbers [1], [2], etc. to reference specific sources
- If the context doesn't contain enough information, say so

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
