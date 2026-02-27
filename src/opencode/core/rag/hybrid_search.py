"""
Hybrid Search for Privacy-First RAG.

Combines semantic (vector) search with keyword (BM25) search for improved accuracy.
"""

import logging
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from .local_vector_store import SearchResult

logger = logging.getLogger(__name__)


class HybridSearchResult(SearchResult):
    """Result from hybrid search with combined scores."""
    
    semantic_score: float = Field(default=0.0, description="Semantic search score")
    keyword_score: float = Field(default=0.0, description="Keyword search score")
    combined_score: float = Field(default=0.0, description="Combined score")


class BM25Index:
    """
    Simple BM25 keyword index for local search.
    
    Implements Okapi BM25 algorithm for text relevance scoring.
    """
    
    def __init__(
        self,
        k1: float = 1.5,
        b: float = 0.75,
    ):
        """
        Initialize BM25 index.
        
        Args:
            k1: BM25 k1 parameter (term frequency saturation)
            b: BM25 b parameter (length normalization)
        """
        self.k1 = k1
        self.b = b
        
        # Index data
        self.doc_ids: List[str] = []
        self.doc_texts: List[str] = []
        self.doc_metadata: List[Dict[str, Any]] = []
        self.doc_lengths: List[int] = []
        
        # Term statistics
        self.term_doc_freq: Counter = Counter()
        self.term_total_freq: Counter = Counter()
        self.avg_doc_length: float = 0.0
        self.total_docs: int = 0
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into terms.
        
        Args:
            text: Text to tokenize
            
        Returns:
            List of tokens
        """
        # Convert to lowercase and split on non-alphanumeric
        text = text.lower()
        tokens = re.findall(r'\b\w+\b', text)
        return tokens
    
    def add_documents(
        self,
        ids: List[str],
        texts: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """
        Add documents to the index.
        
        Args:
            ids: Document IDs
            texts: Document texts
            metadata: Optional metadata
        """
        for i, (doc_id, text) in enumerate(zip(ids, texts)):
            self.doc_ids.append(doc_id)
            self.doc_texts.append(text)
            self.doc_metadata.append(metadata[i] if metadata else {})
            
            # Tokenize and count
            tokens = self._tokenize(text)
            self.doc_lengths.append(len(tokens))
            
            # Update term frequencies
            term_counts = Counter(set(tokens))  # Document frequency (unique terms)
            self.term_doc_freq.update(term_counts)
            self.term_total_freq.update(Counter(tokens))  # Total frequency
        
        # Update statistics
        self.total_docs = len(self.doc_ids)
        self.avg_doc_length = sum(self.doc_lengths) / max(self.total_docs, 1)
    
    def search(
        self,
        query: str,
        top_k: int = 10,
    ) -> List[SearchResult]:
        """
        Search for documents using BM25.
        
        Args:
            query: Query string
            top_k: Number of results to return
            
        Returns:
            List of search results
        """
        if self.total_docs == 0:
            return []
        
        # Tokenize query
        query_terms = self._tokenize(query)
        
        # Calculate BM25 scores for each document
        scores: List[Tuple[int, float]] = []
        
        for doc_idx in range(self.total_docs):
            score = self._bm25_score(doc_idx, query_terms)
            if score > 0:
                scores.append((doc_idx, score))
        
        # Sort by score and get top-k
        scores.sort(key=lambda x: x[1], reverse=True)
        top_results = scores[:top_k]
        
        # Build results
        results = []
        for doc_idx, score in top_results:
            results.append(SearchResult(
                id=self.doc_ids[doc_idx],
                text=self.doc_texts[doc_idx],
                score=score,
                metadata=self.doc_metadata[doc_idx],
            ))
        
        return results
    
    def _bm25_score(self, doc_idx: int, query_terms: List[str]) -> float:
        """
        Calculate BM25 score for a document.
        
        Args:
            doc_idx: Document index
            query_terms: Query terms
            
        Returns:
            BM25 score
        """
        score = 0.0
        doc_length = self.doc_lengths[doc_idx]
        doc_text = self.doc_texts[doc_idx].lower()
        
        for term in query_terms:
            # Term frequency in document
            tf = doc_text.count(term)
            if tf == 0:
                continue
            
            # Document frequency
            df = self.term_doc_freq.get(term, 0)
            if df == 0:
                continue
            
            # IDF (Inverse Document Frequency)
            idf = (
                (self.total_docs - df + 0.5) / (df + 0.5) + 1
            )
            
            # BM25 formula
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (
                1 - self.b + self.b * (doc_length / self.avg_doc_length)
            )
            
            score += idf * (numerator / denominator)
        
        return score
    
    def clear(self) -> None:
        """Clear the index."""
        self.doc_ids = []
        self.doc_texts = []
        self.doc_metadata = []
        self.doc_lengths = []
        self.term_doc_freq = Counter()
        self.term_total_freq = Counter()
        self.avg_doc_length = 0.0
        self.total_docs = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        return {
            "total_docs": self.total_docs,
            "avg_doc_length": self.avg_doc_length,
            "vocabulary_size": len(self.term_doc_freq),
        }


class HybridSearch:
    """
    Combines semantic and keyword search for improved accuracy.
    
    Features:
    - Semantic search using vector embeddings
    - Keyword search using BM25
    - Configurable weighting between methods
    - Re-ranking of combined results
    
    Example:
        ```python
        hybrid = HybridSearch(
            vector_store=local_vector_store,
            semantic_weight=0.7,
            keyword_weight=0.3,
        )
        
        # Index documents
        await hybrid.index_documents(ids, texts, embeddings, metadata)
        
        # Search
        results = await hybrid.search(
            query="search query",
            query_embedding=embedding,
            top_k=10,
        )
        ```
    """
    
    def __init__(
        self,
        vector_store: Any = None,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ):
        """
        Initialize hybrid search.
        
        Args:
            vector_store: Vector store for semantic search
            semantic_weight: Weight for semantic search results
            keyword_weight: Weight for keyword search results
        """
        self.vector_store = vector_store
        self.semantic_weight = semantic_weight
        self.keyword_weight = keyword_weight
        self.keyword_index = BM25Index()
    
    async def index_documents(
        self,
        ids: List[str],
        texts: List[str],
        embeddings: List[List[float]],
        metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """
        Index documents for both semantic and keyword search.
        
        Args:
            ids: Document IDs
            texts: Document texts
            embeddings: Document embeddings
            metadata: Optional metadata
        """
        # Add to vector store
        if self.vector_store:
            await self.vector_store.add(
                ids=ids,
                embeddings=embeddings,
                texts=texts,
                metadata=metadata,
            )
        
        # Add to keyword index
        self.keyword_index.add_documents(
            ids=ids,
            texts=texts,
            metadata=metadata,
        )
    
    async def search(
        self,
        query: str,
        query_embedding: List[float],
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[HybridSearchResult]:
        """
        Perform hybrid search combining semantic and keyword results.
        
        Args:
            query: Query string (for keyword search)
            query_embedding: Query embedding (for semantic search)
            top_k: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of hybrid search results
        """
        # Get more results from each method for better merging
        fetch_k = top_k * 2
        
        # Semantic search
        semantic_results: List[SearchResult] = []
        if self.vector_store:
            semantic_results = await self.vector_store.search(
                query_embedding=query_embedding,
                top_k=fetch_k,
                filter=filter,
            )
        
        # Keyword search
        keyword_results = self.keyword_index.search(
            query=query,
            top_k=fetch_k,
        )
        
        # Merge and re-rank results
        return self._merge_results(
            semantic_results=semantic_results,
            keyword_results=keyword_results,
            top_k=top_k,
        )
    
    def _merge_results(
        self,
        semantic_results: List[SearchResult],
        keyword_results: List[SearchResult],
        top_k: int,
    ) -> List[HybridSearchResult]:
        """
        Merge and re-rank results from both methods.
        
        Args:
            semantic_results: Results from semantic search
            keyword_results: Results from keyword search
            top_k: Number of results to return
            
        Returns:
            Merged and re-ranked results
        """
        # Normalize scores
        semantic_scores = self._normalize_scores([
            r.score for r in semantic_results
        ])
        keyword_scores = self._normalize_scores([
            r.score for r in keyword_results
        ])
        
        # Create score maps
        semantic_map: Dict[str, float] = {
            r.id: s for r, s in zip(semantic_results, semantic_scores)
        }
        keyword_map: Dict[str, float] = {
            r.id: s for r, s in zip(keyword_results, keyword_scores)
        }
        
        # Combine results
        all_ids = set(semantic_map.keys()) | set(keyword_map.keys())
        combined: List[HybridSearchResult] = []
        
        for doc_id in all_ids:
            # Get semantic result
            semantic_result = next(
                (r for r in semantic_results if r.id == doc_id), None
            )
            keyword_result = next(
                (r for r in keyword_results if r.id == doc_id), None
            )
            
            # Get scores
            sem_score = semantic_map.get(doc_id, 0.0)
            kw_score = keyword_map.get(doc_id, 0.0)
            
            # Calculate combined score
            combined_score = (
                self.semantic_weight * sem_score +
                self.keyword_weight * kw_score
            )
            
            # Build result
            result = semantic_result or keyword_result
            if result:
                combined.append(HybridSearchResult(
                    id=result.id,
                    text=result.text,
                    score=combined_score,
                    metadata=result.metadata,
                    semantic_score=sem_score,
                    keyword_score=kw_score,
                    combined_score=combined_score,
                ))
        
        # Sort by combined score
        combined.sort(key=lambda x: x.combined_score, reverse=True)
        
        return combined[:top_k]
    
    def _normalize_scores(self, scores: List[float]) -> List[float]:
        """
        Normalize scores to [0, 1] range.
        
        Args:
            scores: Raw scores
            
        Returns:
            Normalized scores
        """
        if not scores:
            return []
        
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score == min_score:
            return [1.0] * len(scores)
        
        return [
            (s - min_score) / (max_score - min_score)
            for s in scores
        ]
    
    async def delete_documents(self, ids: List[str]) -> None:
        """
        Delete documents from both indexes.
        
        Args:
            ids: Document IDs to delete
        """
        if self.vector_store:
            await self.vector_store.delete(ids)
        
        # Rebuild keyword index without deleted docs
        id_set = set(ids)
        remaining_ids = [
            id for id in self.keyword_index.doc_ids
            if id not in id_set
        ]
        remaining_texts = [
            text for id, text in zip(
                self.keyword_index.doc_ids,
                self.keyword_index.doc_texts
            ) if id not in id_set
        ]
        remaining_metadata = [
            meta for id, meta in zip(
                self.keyword_index.doc_ids,
                self.keyword_index.doc_metadata
            ) if id not in id_set
        ]
        
        self.keyword_index.clear()
        self.keyword_index.add_documents(
            ids=remaining_ids,
            texts=remaining_texts,
            metadata=remaining_metadata,
        )
    
    async def clear(self) -> None:
        """Clear both indexes."""
        if self.vector_store:
            await self.vector_store.clear()
        self.keyword_index.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get search statistics."""
        return {
            "semantic_weight": self.semantic_weight,
            "keyword_weight": self.keyword_weight,
            "keyword_index": self.keyword_index.get_stats(),
            "vector_store": self.vector_store.get_stats() if self.vector_store else None,
        }
