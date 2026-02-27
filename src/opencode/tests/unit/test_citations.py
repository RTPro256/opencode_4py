"""
Tests for Citation System.

Tests citation tracking and formatting for RAG responses.
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from opencode.core.rag.citations import (
    Citation,
    CitationStyle,
    CitationManager,
    format_citation_report,
)


class TestCitation:
    """Tests for Citation model."""

    def test_citation_creation(self):
        """Test creating a Citation."""
        citation = Citation(
            id="cite_1",
            source_id="doc_123",
            source_path="docs/api.md",
        )
        assert citation.id == "cite_1"
        assert citation.source_id == "doc_123"
        assert citation.source_path == "docs/api.md"
        assert citation.source_type == "file"
        assert citation.relevance_score == 0.0

    def test_citation_with_all_fields(self):
        """Test creating Citation with all fields."""
        citation = Citation(
            id="cite_1",
            source_id="doc_123",
            source_path="docs/api.md",
            source_type="markdown",
            snippet="This is a relevant snippet from the document.",
            snippet_start=10,
            snippet_end=50,
            relevance_score=0.95,
            semantic_score=0.9,
            keyword_score=0.8,
            title="API Documentation",
            author="John Doe",
            created_at=datetime(2024, 1, 1),
            metadata={"key": "value"},
        )
        assert citation.source_type == "markdown"
        assert citation.snippet == "This is a relevant snippet from the document."
        assert citation.relevance_score == 0.95
        assert citation.semantic_score == 0.9
        assert citation.keyword_score == 0.8
        assert citation.title == "API Documentation"
        assert citation.author == "John Doe"

    def test_citation_to_dict(self):
        """Test converting Citation to dictionary."""
        citation = Citation(
            id="cite_1",
            source_id="doc_123",
            source_path="docs/api.md",
            snippet="Short snippet",
            relevance_score=0.9,
            title="Test Title",
        )
        data = citation.to_dict()
        assert data["id"] == "cite_1"
        assert data["source_id"] == "doc_123"
        assert data["source_path"] == "docs/api.md"
        assert data["snippet"] == "Short snippet"
        assert data["relevance_score"] == 0.9
        assert data["title"] == "Test Title"

    def test_citation_to_dict_truncates_snippet(self):
        """Test that to_dict truncates long snippets."""
        long_snippet = "x" * 150
        citation = Citation(
            id="cite_1",
            source_id="doc_123",
            source_path="docs/api.md",
            snippet=long_snippet,
        )
        data = citation.to_dict()
        assert len(data["snippet"]) == 103  # 100 + "..."

    def test_format_inline_with_title(self):
        """Test inline formatting with title."""
        citation = Citation(
            id="cite_1",
            source_id="doc_123",
            source_path="docs/api.md",
            title="API Docs",
        )
        result = citation.format_inline()
        assert "[API Docs](docs/api.md)" == result

    def test_format_inline_without_title(self):
        """Test inline formatting without title."""
        citation = Citation(
            id="cite_1",
            source_id="doc_123",
            source_path="docs/api.md",
        )
        result = citation.format_inline()
        assert "[docs/api.md]" == result

    def test_format_footnote(self):
        """Test footnote formatting."""
        citation = Citation(
            id="cite_1",
            source_id="doc_123",
            source_path="docs/api.md",
            title="API Docs",
            relevance_score=0.95,
        )
        result = citation.format_footnote(1)
        assert "[1] docs/api.md" in result
        assert '"API Docs"' in result
        assert "relevance: 0.95" in result

    def test_format_footnote_minimal(self):
        """Test footnote formatting with minimal info."""
        citation = Citation(
            id="cite_1",
            source_id="doc_123",
            source_path="docs/api.md",
        )
        result = citation.format_footnote(1)
        assert "[1] docs/api.md" == result


class TestCitationStyle:
    """Tests for CitationStyle constants."""

    def test_citation_styles(self):
        """Test that all citation styles exist."""
        assert CitationStyle.INLINE == "inline"
        assert CitationStyle.FOOTNOTE == "footnote"
        assert CitationStyle.ENDNOTE == "endnote"
        assert CitationStyle.ACADEMIC == "academic"


class TestCitationManager:
    """Tests for CitationManager class."""

    def test_init_defaults(self):
        """Test CitationManager initialization with defaults."""
        manager = CitationManager()
        assert manager.default_style == CitationStyle.FOOTNOTE
        assert manager.include_snippets is True
        assert manager.max_snippet_length == 200

    def test_init_custom(self):
        """Test CitationManager initialization with custom values."""
        manager = CitationManager(
            default_style=CitationStyle.INLINE,
            include_snippets=False,
            max_snippet_length=100,
        )
        assert manager.default_style == CitationStyle.INLINE
        assert manager.include_snippets is False
        assert manager.max_snippet_length == 100

    def test_build_citations(self):
        """Test building citations from sources."""
        manager = CitationManager()
        
        # Create mock sources with spec to avoid MagicMock comparison issues
        source1 = MagicMock()
        source1.id = "doc_1"
        source1.text = "This is the content of source 1"
        source1.score = 0.9
        source1.semantic_score = 0.8
        source1.keyword_score = 0.7
        source1.metadata = {"source": "docs/1.md", "title": "Doc 1"}
        # Don't set combined_score - delete the attribute
        delattr(source1, 'combined_score')
        
        source2 = MagicMock()
        source2.id = "doc_2"
        source2.text = "Content of source 2"
        source2.score = 0.8
        source2.semantic_score = 0.7
        source2.keyword_score = 0.6
        source2.metadata = {"source": "docs/2.md", "title": "Doc 2"}
        delattr(source2, 'combined_score')
        
        citations = manager.build_citations([source1, source2])
        
        assert len(citations) == 2
        assert citations[0].source_path == "docs/1.md"
        assert citations[1].source_path == "docs/2.md"

    def test_build_citations_with_min_score(self):
        """Test building citations with minimum score filter."""
        manager = CitationManager()
        
        source1 = MagicMock()
        source1.id = "doc_1"
        source1.text = "Content 1"
        source1.score = 0.9
        source1.semantic_score = 0.8
        source1.keyword_score = 0.7
        source1.metadata = {"source": "docs/1.md"}
        delattr(source1, 'combined_score')
        
        source2 = MagicMock()
        source2.id = "doc_2"
        source2.text = "Content 2"
        source2.score = 0.5
        source2.semantic_score = 0.4
        source2.keyword_score = 0.3
        source2.metadata = {"source": "docs/2.md"}
        delattr(source2, 'combined_score')
        
        citations = manager.build_citations([source1, source2], min_score=0.7)
        
        assert len(citations) == 1
        assert citations[0].source_path == "docs/1.md"

    def test_build_citations_with_combined_score(self):
        """Test building citations with combined_score attribute."""
        manager = CitationManager()
        
        source = MagicMock()
        source.id = "doc_1"
        source.text = "Content"
        source.score = 0.5
        source.combined_score = 0.95
        source.semantic_score = 0.9
        source.keyword_score = 0.8
        source.metadata = {"source": "docs/1.md"}
        
        citations = manager.build_citations([source])
        
        assert citations[0].relevance_score == 0.95

    def test_build_citations_without_snippets(self):
        """Test building citations without snippets."""
        manager = CitationManager(include_snippets=False)
        
        source = MagicMock()
        source.id = "doc_1"
        source.text = "Content"
        source.score = 0.9
        source.semantic_score = 0.8
        source.keyword_score = 0.7
        source.metadata = {"source": "docs/1.md"}
        delattr(source, 'combined_score')
        
        citations = manager.build_citations([source])
        
        assert citations[0].snippet is None

    def test_build_citations_truncates_snippet(self):
        """Test that long snippets are truncated."""
        manager = CitationManager(max_snippet_length=50)
        
        source = MagicMock()
        source.id = "doc_1"
        source.text = "x" * 100
        source.score = 0.9
        source.semantic_score = 0.8
        source.keyword_score = 0.7
        source.metadata = {"source": "docs/1.md"}
        delattr(source, 'combined_score')
        
        citations = manager.build_citations([source])
        
        snippet = citations[0].snippet
        assert snippet is not None
        assert len(snippet) == 53  # 50 + "..."

    def test_format_response_with_citations_inline(self):
        """Test formatting response with inline citations."""
        manager = CitationManager()
        
        citations = [
            Citation(id="cite_1", source_id="doc_1", source_path="docs/1.md", title="Doc 1"),
            Citation(id="cite_2", source_id="doc_2", source_path="docs/2.md", title="Doc 2"),
        ]
        
        result = manager.format_response_with_citations(
            response="This is the response.",
            citations=citations,
            style=CitationStyle.INLINE,
        )
        
        assert "This is the response." in result
        assert "**Sources:**" in result
        assert "[Doc 1](docs/1.md)" in result

    def test_format_response_with_citations_footnote(self):
        """Test formatting response with footnote citations."""
        manager = CitationManager()
        
        citations = [
            Citation(id="cite_1", source_id="doc_1", source_path="docs/1.md", title="Doc 1"),
        ]
        
        result = manager.format_response_with_citations(
            response="This is the response.",
            citations=citations,
            style=CitationStyle.FOOTNOTE,
        )
        
        assert "This is the response." in result
        assert "---" in result
        assert "**Sources:**" in result
        assert "[1] docs/1.md" in result

    def test_format_response_with_citations_endnote(self):
        """Test formatting response with endnote citations."""
        manager = CitationManager()
        
        citations = [
            Citation(
                id="cite_1",
                source_id="doc_1",
                source_path="docs/1.md",
                title="Doc 1",
                snippet="This is a snippet from the document.",
            ),
        ]
        
        result = manager.format_response_with_citations(
            response="This is the response.",
            citations=citations,
            style=CitationStyle.ENDNOTE,
        )
        
        assert "This is the response." in result
        assert "**References:**" in result
        assert "[1] docs/1.md" in result

    def test_format_response_with_citations_academic(self):
        """Test formatting response with academic citations."""
        manager = CitationManager()
        
        citations = [
            Citation(
                id="cite_1",
                source_id="doc_1",
                source_path="docs/1.md",
                title="API Documentation",
                author="John Doe",
                created_at=datetime(2024, 1, 15),
            ),
        ]
        
        result = manager.format_response_with_citations(
            response="This is the response.",
            citations=citations,
            style=CitationStyle.ACADEMIC,
        )
        
        assert "This is the response." in result
        assert "**References:**" in result
        assert "John Doe" in result
        assert "(2024)" in result
        assert '"API Documentation."' in result

    def test_format_response_with_citations_academic_no_author(self):
        """Test academic formatting without author."""
        manager = CitationManager()
        
        citations = [
            Citation(
                id="cite_1",
                source_id="doc_1",
                source_path="docs/1.md",
                title="API Documentation",
            ),
        ]
        
        result = manager.format_response_with_citations(
            response="Response",
            citations=citations,
            style=CitationStyle.ACADEMIC,
        )
        
        assert "[Author]" in result
        assert "(n.d.)" in result

    def test_format_response_empty_citations(self):
        """Test formatting response with no citations."""
        manager = CitationManager()
        
        result = manager.format_response_with_citations(
            response="This is the response.",
            citations=[],
        )
        
        assert result == "This is the response."

    def test_format_response_uses_default_style(self):
        """Test that default style is used when not specified."""
        manager = CitationManager(default_style=CitationStyle.INLINE)
        
        citations = [
            Citation(id="cite_1", source_id="doc_1", source_path="docs/1.md"),
        ]
        
        result = manager.format_response_with_citations(
            response="Response",
            citations=citations,
        )
        
        assert "**Sources:**" in result

    def test_format_response_unknown_style_uses_footnote(self):
        """Test that unknown style defaults to footnote."""
        manager = CitationManager()
        
        citations = [
            Citation(id="cite_1", source_id="doc_1", source_path="docs/1.md"),
        ]
        
        result = manager.format_response_with_citations(
            response="Response",
            citations=citations,
            style="unknown_style",
        )
        
        assert "---" in result  # Footnote style marker

    def test_get_source_usage(self):
        """Test getting source usage statistics."""
        manager = CitationManager()
        
        source1 = MagicMock()
        source1.id = "doc_1"
        source1.text = "Content"
        source1.score = 0.9
        source1.semantic_score = 0.8
        source1.keyword_score = 0.7
        source1.metadata = {"source": "docs/1.md"}
        delattr(source1, 'combined_score')
        
        source2 = MagicMock()
        source2.id = "doc_2"
        source2.text = "Content"
        source2.score = 0.9
        source2.semantic_score = 0.8
        source2.keyword_score = 0.7
        source2.metadata = {"source": "docs/1.md"}  # Same source
        delattr(source2, 'combined_score')
        
        manager.build_citations([source1, source2])
        
        usage = manager.get_source_usage()
        assert usage["docs/1.md"] == 2

    def test_get_most_used_sources(self):
        """Test getting most used sources."""
        manager = CitationManager()
        
        for i in range(5):
            source = MagicMock()
            source.id = f"doc_{i}"
            source.text = "Content"
            source.score = 0.9
            source.semantic_score = 0.8
            source.keyword_score = 0.7
            source.metadata = {"source": f"docs/{i % 2}.md"}
            delattr(source, 'combined_score')
            manager.build_citations([source])
        
        most_used = manager.get_most_used_sources(limit=1)
        assert len(most_used) == 1
        assert most_used[0][1] == 3  # docs/0.md or docs/1.md used 3 times

    def test_get_stats(self):
        """Test getting manager statistics."""
        manager = CitationManager(
            default_style=CitationStyle.INLINE,
            include_snippets=False,
        )
        
        source = MagicMock()
        source.id = "doc_1"
        source.text = "Content"
        source.score = 0.9
        source.semantic_score = 0.8
        source.keyword_score = 0.7
        source.metadata = {"source": "docs/1.md"}
        delattr(source, 'combined_score')
        
        manager.build_citations([source])
        
        stats = manager.get_stats()
        assert stats["total_citations"] == 1
        assert stats["unique_sources"] == 1
        assert stats["default_style"] == CitationStyle.INLINE
        assert stats["include_snippets"] is False
        assert "most_used_sources" in stats

    def test_reset_stats(self):
        """Test resetting statistics."""
        manager = CitationManager()
        
        source = MagicMock()
        source.id = "doc_1"
        source.text = "Content"
        source.score = 0.9
        source.semantic_score = 0.8
        source.keyword_score = 0.7
        source.metadata = {"source": "docs/1.md"}
        delattr(source, 'combined_score')
        
        manager.build_citations([source])
        assert manager._citation_count == 1
        
        manager.reset_stats()
        
        assert manager._citation_count == 0
        assert len(manager._source_usage) == 0


class TestFormatCitationReport:
    """Tests for format_citation_report function."""

    def test_format_citation_report(self):
        """Test formatting a citation report."""
        citations = [
            Citation(
                id="cite_1",
                source_id="doc_1",
                source_path="docs/api.md",
                source_type="markdown",
                title="API Documentation",
                relevance_score=0.95,
                snippet="This is a snippet from the API documentation.",
            ),
            Citation(
                id="cite_2",
                source_id="doc_2",
                source_path="src/main.py",
                source_type="code",
                relevance_score=0.85,
            ),
        ]
        
        report = format_citation_report(citations, title="Test Report")
        
        assert "# Test Report" in report
        assert "Total citations: 2" in report
        assert "## Markdown Sources (1)" in report
        assert "## Code Sources (1)" in report
        assert "docs/api.md" in report
        assert "src/main.py" in report
        assert "API Documentation" in report
        assert "Relevance: 0.95" in report

    def test_format_citation_report_empty(self):
        """Test formatting report with no citations."""
        report = format_citation_report([], title="Empty Report")
        
        assert "# Empty Report" in report
        assert "Total citations: 0" in report

    def test_format_citation_report_groups_by_type(self):
        """Test that report groups citations by type."""
        citations = [
            Citation(id="cite_1", source_id="doc_1", source_path="1.md", source_type="markdown"),
            Citation(id="cite_2", source_id="doc_2", source_path="2.md", source_type="markdown"),
            Citation(id="cite_3", source_id="doc_3", source_path="3.py", source_type="code"),
        ]
        
        report = format_citation_report(citations)
        
        assert "## Markdown Sources (2)" in report
        assert "## Code Sources (1)" in report
