"""Tests for Query Rewriter module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from opencode.core.rag.query_rewriter import (
    QueryRewriteResult,
    QueryRewriter,
    HyDEGenerator,
    QueryDecomposer,
)


class TestQueryRewriteResult:
    """Tests for QueryRewriteResult."""
    
    def test_default_values(self):
        """Test default values."""
        result = QueryRewriteResult(original_query="test query")
        assert result.original_query == "test query"
        assert result.rewritten_queries == []
        assert result.hypothetical_document is None
        assert result.expansion_terms == []
        assert result.metadata == {}
    
    def test_custom_values(self):
        """Test custom values."""
        result = QueryRewriteResult(
            original_query="test query",
            rewritten_queries=["query 1", "query 2"],
            hypothetical_document="hypothetical doc",
            expansion_terms=["term1", "term2"],
            metadata={"key": "value"}
        )
        assert result.original_query == "test query"
        assert result.rewritten_queries == ["query 1", "query 2"]
        assert result.hypothetical_document == "hypothetical doc"
    
    def test_get_all_queries(self):
        """Test get_all_queries method."""
        result = QueryRewriteResult(
            original_query="original",
            rewritten_queries=["rewrite1", "rewrite2"]
        )
        queries = result.get_all_queries()
        
        assert queries == ["original", "rewrite1", "rewrite2"]
    
    def test_get_all_queries_deduplicates(self):
        """Test that get_all_queries removes duplicates."""
        result = QueryRewriteResult(
            original_query="original",
            rewritten_queries=["original", "rewrite1", "rewrite1"]
        )
        queries = result.get_all_queries()
        
        assert queries == ["original", "rewrite1"]


class TestQueryRewriter:
    """Tests for QueryRewriter."""
    
    def test_init(self):
        """Test initialization."""
        rewriter = QueryRewriter()
        assert rewriter.llm_client is None
        assert rewriter.expansion_count == 3
        assert rewriter.use_hyde is True
    
    def test_init_custom(self):
        """Test initialization with custom values."""
        mock_llm = MagicMock()
        rewriter = QueryRewriter(
            llm_client=mock_llm,
            expansion_count=5,
            use_hyde=False
        )
        assert rewriter.llm_client == mock_llm
        assert rewriter.expansion_count == 5
        assert rewriter.use_hyde is False
    
    @pytest.mark.asyncio
    async def test_rewrite_no_llm(self):
        """Test rewrite without LLM client."""
        rewriter = QueryRewriter()
        result = await rewriter.rewrite("Python programming")
        
        assert result.original_query == "Python programming"
        assert len(result.rewritten_queries) > 0
        assert result.hypothetical_document is None
    
    @pytest.mark.asyncio
    async def test_rewrite_with_llm_no_hyde(self):
        """Test rewrite with LLM but HyDE disabled."""
        mock_llm = MagicMock()
        rewriter = QueryRewriter(llm_client=mock_llm, use_hyde=False)
        result = await rewriter.rewrite("Python programming")
        
        assert result.original_query == "Python programming"
        # Should use simple rewrite since LLM calls are not implemented
        assert len(result.rewritten_queries) > 0
    
    @pytest.mark.asyncio
    async def test_rewrite_with_llm_with_hyde(self):
        """Test rewrite with LLM and HyDE enabled."""
        mock_llm = MagicMock()
        rewriter = QueryRewriter(llm_client=mock_llm, use_hyde=True)
        result = await rewriter.rewrite("Python programming")
        
        assert result.original_query == "Python programming"
        # HyDE returns None since not implemented
        assert result.hypothetical_document is None
    
    def test_simple_rewrite_non_question(self):
        """Test simple rewrite for non-question query."""
        rewriter = QueryRewriter(expansion_count=3)
        variations = rewriter._simple_rewrite("Python programming")
        
        assert "what is Python programming" in variations
        assert "how does Python programming work" in variations
    
    def test_simple_rewrite_question(self):
        """Test simple rewrite for question query."""
        rewriter = QueryRewriter(expansion_count=3)
        variations = rewriter._simple_rewrite("What is Python")
        
        # Should remove question word (output is lowercase)
        assert "is python" in variations
    
    def test_simple_rewrite_how_question(self):
        """Test simple rewrite for 'how' question."""
        rewriter = QueryRewriter(expansion_count=3)
        variations = rewriter._simple_rewrite("How does Python work")
        
        # Output is lowercase
        assert "does python work" in variations
    
    def test_simple_rewrite_respects_count(self):
        """Test that simple rewrite respects expansion count."""
        rewriter = QueryRewriter(expansion_count=1)
        variations = rewriter._simple_rewrite("Python programming")
        
        assert len(variations) <= 1
    
    def test_expand_with_synonyms(self):
        """Test expand_with_synonyms returns original query."""
        rewriter = QueryRewriter()
        result = rewriter.expand_with_synonyms("test query")
        
        assert result == ["test query"]


class TestHyDEGenerator:
    """Tests for HyDEGenerator."""
    
    def test_init(self):
        """Test initialization."""
        generator = HyDEGenerator()
        assert generator.llm_client is None
        assert generator.document_style == "informative"
    
    def test_init_custom_style(self):
        """Test initialization with custom style."""
        generator = HyDEGenerator(document_style="technical")
        assert generator.document_style == "technical"
    
    @pytest.mark.asyncio
    async def test_generate_no_llm(self):
        """Test generate without LLM client."""
        generator = HyDEGenerator()
        result = await generator.generate("What is Python?")
        
        assert "What is Python?" in result
        assert "Hypothetical document" in result
    
    @pytest.mark.asyncio
    async def test_generate_informative_style(self):
        """Test generate with informative style."""
        generator = HyDEGenerator(document_style="informative")
        result = await generator.generate("What is Python?")
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_generate_conversational_style(self):
        """Test generate with conversational style."""
        generator = HyDEGenerator(document_style="conversational")
        result = await generator.generate("What is Python?")
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_generate_technical_style(self):
        """Test generate with technical style."""
        generator = HyDEGenerator(document_style="technical")
        result = await generator.generate("What is Python?")
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_generate_unknown_style(self):
        """Test generate with unknown style defaults to informative."""
        generator = HyDEGenerator(document_style="unknown")
        result = await generator.generate("What is Python?")
        
        assert result is not None


class TestQueryDecomposer:
    """Tests for QueryDecomposer."""
    
    def test_init(self):
        """Test initialization."""
        decomposer = QueryDecomposer()
        assert decomposer.llm_client is None
    
    def test_init_with_llm(self):
        """Test initialization with LLM client."""
        mock_llm = MagicMock()
        decomposer = QueryDecomposer(llm_client=mock_llm)
        assert decomposer.llm_client == mock_llm
    
    @pytest.mark.asyncio
    async def test_decompose_no_llm(self):
        """Test decompose without LLM client."""
        decomposer = QueryDecomposer()
        result = await decomposer.decompose("What is Python?")
        
        # Returns original query when no LLM
        assert result == ["What is Python?"]
    
    @pytest.mark.asyncio
    async def test_decompose_with_llm(self):
        """Test decompose with LLM client."""
        mock_llm = MagicMock()
        decomposer = QueryDecomposer(llm_client=mock_llm)
        result = await decomposer.decompose("What is Python?")
        
        # LLM not implemented, returns original
        assert result == ["What is Python?"]
    
    def test_is_complex_with_and(self):
        """Test is_complex with 'and' indicator."""
        decomposer = QueryDecomposer()
        
        assert decomposer.is_complex("What is Python and Java?") is True
        assert decomposer.is_complex("Python is great") is False
    
    def test_is_complex_with_or(self):
        """Test is_complex with 'or' indicator."""
        decomposer = QueryDecomposer()
        
        assert decomposer.is_complex("Should I use Python or Java?") is True
    
    def test_is_complex_with_compare(self):
        """Test is_complex with 'compare' indicator."""
        decomposer = QueryDecomposer()
        
        assert decomposer.is_complex("Compare Python and Java") is True
    
    def test_is_complex_with_contrast(self):
        """Test is_complex with 'contrast' indicator."""
        decomposer = QueryDecomposer()
        
        assert decomposer.is_complex("Contrast Python with Java") is True
    
    def test_is_complex_with_difference(self):
        """Test is_complex with 'difference between' indicator."""
        decomposer = QueryDecomposer()
        
        assert decomposer.is_complex("What is the difference between Python and Java?") is True
    
    def test_is_complex_simple_query(self):
        """Test is_complex with simple query."""
        decomposer = QueryDecomposer()
        
        assert decomposer.is_complex("What is Python?") is False
        assert decomposer.is_complex("How does Python work?") is False
    
    def test_is_complex_case_insensitive(self):
        """Test is_complex is case insensitive."""
        decomposer = QueryDecomposer()
        
        assert decomposer.is_complex("COMPARE Python and Java") is True
        assert decomposer.is_complex("What Is Python AND Java?") is True
