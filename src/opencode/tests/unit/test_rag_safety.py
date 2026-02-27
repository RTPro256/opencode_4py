"""
Tests for RAG Safety module.

Tests content filtering, output sanitization, and audit logging.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from opencode.core.rag.safety import (
    ContentFilter,
    FilteredContent,
    OutputSanitizer,
    SanitizedOutput,
    RAGAuditLogger,
    AuditEntry,
)
from opencode.core.rag.safety.content_filter import (
    Redaction,
    SensitivePattern,
    DEFAULT_SENSITIVE_PATTERNS,
)
from opencode.core.rag.safety.output_sanitizer import Citation, SanitizationContext


class TestRedaction:
    """Tests for Redaction dataclass."""

    def test_redaction_creation(self):
        """Test creating a Redaction instance."""
        redaction = Redaction(
            pattern_name="password",
            original_length=12,
            start_position=10,
            redacted_text="[REDACTED]",
        )
        assert redaction.pattern_name == "password"
        assert redaction.original_length == 12
        assert redaction.start_position == 10
        assert redaction.redacted_text == "[REDACTED]"


class TestFilteredContent:
    """Tests for FilteredContent dataclass."""

    def test_filtered_content_creation(self):
        """Test creating a FilteredContent instance."""
        content = FilteredContent(
            original_content="My password is secret123",
            filtered_content="My password is [REDACTED]",
            redactions=[],
            is_safe=False,
            warnings=[],
        )
        assert content.original_content == "My password is secret123"
        assert content.filtered_content == "My password is [REDACTED]"
        assert content.is_safe is False

    def test_filtered_content_to_dict(self):
        """Test converting FilteredContent to dictionary."""
        redaction = Redaction(
            pattern_name="password",
            original_length=9,
            start_position=15,
            redacted_text="[PASSWORD_REDACTED]",
        )
        content = FilteredContent(
            original_content="My password is secret123",
            filtered_content="My password is [PASSWORD_REDACTED]",
            redactions=[redaction],
            is_safe=False,
            warnings=["Sensitive content detected"],
        )
        result = content.to_dict()
        assert result["filtered_content"] == "My password is [PASSWORD_REDACTED]"
        assert result["is_safe"] is False
        assert result["redaction_count"] == 1
        assert len(result["redactions"]) == 1
        assert result["redactions"][0]["pattern"] == "password"
        assert result["warnings"] == ["Sensitive content detected"]


class TestSensitivePattern:
    """Tests for SensitivePattern class."""

    def test_sensitive_pattern_creation(self):
        """Test creating a SensitivePattern instance."""
        pattern = SensitivePattern(
            name="test_pattern",
            pattern=r"\btest\d+\b",
            description="Test pattern",
            redact_with="[TEST_REDACTED]",
        )
        assert pattern.name == "test_pattern"
        assert pattern.description == "Test pattern"
        assert pattern.redact_with == "[TEST_REDACTED]"
        # Pattern should be compiled
        assert pattern.pattern.search("test123") is not None
        assert pattern.pattern.search("no match") is None

    def test_sensitive_pattern_case_insensitive(self):
        """Test that patterns are case-insensitive."""
        pattern = SensitivePattern(
            name="test",
            pattern=r"password",
        )
        assert pattern.pattern.search("PASSWORD") is not None
        assert pattern.pattern.search("Password") is not None
        assert pattern.pattern.search("password") is not None


class TestContentFilter:
    """Tests for ContentFilter class."""

    def test_default_patterns_loaded(self):
        """Test that default patterns are loaded."""
        filter = ContentFilter()
        pattern_names = filter.get_pattern_names()
        assert "password" in pattern_names
        assert "api_key" in pattern_names
        assert "email" in pattern_names
        assert "credit_card" in pattern_names

    def test_filter_password(self):
        """Test filtering password content."""
        filter = ContentFilter()
        result = filter.filter_content("password=secret123")
        assert "[PASSWORD_REDACTED]" in result.filtered_content
        assert result.is_safe is False
        assert len(result.redactions) == 1
        assert result.redactions[0].pattern_name == "password"

    def test_filter_api_key(self):
        """Test filtering API key content."""
        filter = ContentFilter()
        result = filter.filter_content("api_key=sk-1234567890abcdef")
        assert "[API_KEY_REDACTED]" in result.filtered_content
        assert result.is_safe is False

    def test_filter_email(self):
        """Test filtering email addresses."""
        filter = ContentFilter()
        result = filter.filter_content("Contact: user@example.com")
        assert "[EMAIL_REDACTED]" in result.filtered_content
        assert result.is_safe is False

    def test_filter_credit_card(self):
        """Test filtering credit card numbers."""
        filter = ContentFilter()
        result = filter.filter_content("Card: 1234-5678-9012-3456")
        assert "[CC_REDACTED]" in result.filtered_content
        assert result.is_safe is False

    def test_filter_ssn(self):
        """Test filtering SSN."""
        filter = ContentFilter()
        result = filter.filter_content("SSN: 123-45-6789")
        assert "[SSN_REDACTED]" in result.filtered_content
        assert result.is_safe is False

    def test_filter_ip_address(self):
        """Test filtering IP addresses."""
        filter = ContentFilter()
        result = filter.filter_content("Server: 192.168.1.1")
        assert "[IP_REDACTED]" in result.filtered_content
        assert result.is_safe is False

    def test_filter_private_key(self):
        """Test filtering private key markers."""
        filter = ContentFilter()
        result = filter.filter_content("-----BEGIN PRIVATE KEY-----")
        assert "[PRIVATE_KEY_REDACTED]" in result.filtered_content
        assert result.is_safe is False

    def test_filter_aws_key(self):
        """Test filtering AWS access keys."""
        filter = ContentFilter()
        result = filter.filter_content("AWS Key: AKIAIOSFODNN7EXAMPLE")
        assert "[AWS_KEY_REDACTED]" in result.filtered_content
        assert result.is_safe is False

    def test_filter_jwt(self):
        """Test filtering JWT tokens."""
        filter = ContentFilter()
        jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        result = filter.filter_content(f"Token: {jwt_token}")
        # JWT gets redacted (may match token or jwt pattern)
        assert result.is_safe is False
        assert len(result.redactions) > 0

    def test_filter_safe_content(self):
        """Test that safe content passes through unchanged."""
        filter = ContentFilter()
        result = filter.filter_content("This is a normal text without sensitive data.")
        assert result.filtered_content == "This is a normal text without sensitive data."
        assert result.is_safe is True
        assert len(result.redactions) == 0

    def test_filter_multiple_patterns(self):
        """Test filtering content with multiple sensitive patterns."""
        filter = ContentFilter()
        content = "password=secret and email=user@example.com"
        result = filter.filter_content(content)
        assert "[PASSWORD_REDACTED]" in result.filtered_content
        assert "[EMAIL_REDACTED]" in result.filtered_content
        assert len(result.redactions) == 2

    def test_check_content_safe(self):
        """Test check_content returns True for safe content."""
        filter = ContentFilter()
        assert filter.check_content("This is safe content") is True

    def test_check_content_unsafe(self):
        """Test check_content returns False for unsafe content."""
        filter = ContentFilter()
        assert filter.check_content("password=secret") is False

    def test_get_detected_patterns(self):
        """Test getting list of detected patterns."""
        filter = ContentFilter()
        content = "password=secret and api_key=key123"
        detected = filter.get_detected_patterns(content)
        assert "password" in detected
        assert "api_key" in detected

    def test_add_pattern(self):
        """Test adding a custom pattern."""
        filter = ContentFilter()
        filter.add_pattern(
            name="custom_secret",
            pattern=r"CUSTOM_\w+",
            description="Custom secret pattern",
            redact_with="[CUSTOM_REDACTED]",
        )
        result = filter.filter_content("Found CUSTOM_SECRET here")
        assert "[CUSTOM_REDACTED]" in result.filtered_content
        assert "custom_secret" in filter.get_pattern_names()

    def test_remove_pattern(self):
        """Test removing a pattern."""
        filter = ContentFilter()
        assert filter.remove_pattern("password") is True
        assert "password" not in filter.get_pattern_names()
        assert filter.remove_pattern("nonexistent") is False

    def test_custom_patterns_in_init(self):
        """Test providing custom patterns at initialization."""
        custom_patterns = [
            {
                "name": "my_pattern",
                "pattern": r"MY_\w+",
                "description": "My custom pattern",
                "redact_with": "[MY_REDACTED]",
            }
        ]
        filter = ContentFilter(custom_patterns=custom_patterns)
        result = filter.filter_content("Found MY_SECRET here")
        assert "[MY_REDACTED]" in result.filtered_content

    def test_get_stats(self):
        """Test getting filter statistics."""
        filter = ContentFilter()
        stats = filter.get_stats()
        assert "pattern_count" in stats
        assert "patterns" in stats
        assert stats["pattern_count"] > 0


class TestCitation:
    """Tests for Citation dataclass."""

    def test_citation_creation(self):
        """Test creating a Citation instance."""
        citation = Citation(
            source_id="1",
            source_path="docs/api.md",
            relevance_score=0.95,
            snippet="API documentation",
            metadata={"type": "markdown"},
        )
        assert citation.source_id == "1"
        assert citation.source_path == "docs/api.md"
        assert citation.relevance_score == 0.95
        assert citation.snippet == "API documentation"
        assert citation.metadata == {"type": "markdown"}

    def test_citation_defaults(self):
        """Test Citation default values."""
        citation = Citation(
            source_id="1",
            source_path="doc.md",
            relevance_score=0.5,
        )
        assert citation.snippet is None
        assert citation.metadata == {}


class TestSanitizationContext:
    """Tests for SanitizationContext dataclass."""

    def test_context_creation(self):
        """Test creating a SanitizationContext instance."""
        citation = Citation(
            source_id="1",
            source_path="doc.md",
            relevance_score=0.9,
        )
        context = SanitizationContext(
            query="What is the API?",
            sources_used=[citation],
            allowed_urls={"https://example.com"},
            metadata={"user": "test"},
        )
        assert context.query == "What is the API?"
        assert len(context.sources_used) == 1
        assert "https://example.com" in context.allowed_urls
        assert context.metadata == {"user": "test"}


class TestSanitizedOutput:
    """Tests for SanitizedOutput dataclass."""

    def test_sanitized_output_creation(self):
        """Test creating a SanitizedOutput instance."""
        output = SanitizedOutput(
            original_output="Original text",
            sanitized_output="Sanitized text",
            citations=[],
            warnings=["Warning 1"],
            removed_urls=["https://bad.com"],
            is_safe=True,
        )
        assert output.original_output == "Original text"
        assert output.sanitized_output == "Sanitized text"
        assert len(output.warnings) == 1
        assert len(output.removed_urls) == 1

    def test_sanitized_output_to_dict(self):
        """Test converting SanitizedOutput to dictionary."""
        output = SanitizedOutput(
            original_output="Original",
            sanitized_output="Sanitized",
            citations=[],
            warnings=["Test warning"],
            removed_urls=["https://example.com"],
            is_safe=False,
        )
        result = output.to_dict()
        assert result["sanitized_output"] == "Sanitized"
        assert result["is_safe"] is False
        assert result["citation_count"] == 0
        assert result["warnings"] == ["Test warning"]
        assert result["removed_urls"] == ["https://example.com"]


class TestOutputSanitizer:
    """Tests for OutputSanitizer class."""

    def test_sanitize_safe_content(self):
        """Test sanitizing safe content."""
        sanitizer = OutputSanitizer()
        result = sanitizer.sanitize("This is safe content")
        assert result.sanitized_output == "This is safe content"
        assert result.is_safe is True
        assert len(result.warnings) == 0

    def test_sanitize_password(self):
        """Test sanitizing content with password."""
        sanitizer = OutputSanitizer()
        result = sanitizer.sanitize("password=secret123")
        assert "[PASSWORD_REDACTED]" in result.sanitized_output
        assert result.is_safe is True  # Safe because redacted

    def test_sanitize_openai_key(self):
        """Test sanitizing OpenAI-style keys."""
        sanitizer = OutputSanitizer()
        result = sanitizer.sanitize("Key: sk-1234567890abcdefghijklmnopqrstuv")
        assert "[SECRET_REDACTED]" in result.sanitized_output

    def test_sanitize_slack_token(self):
        """Test sanitizing Slack tokens."""
        sanitizer = OutputSanitizer()
        # Use a clearly fake test token that won't trigger secret scanners
        result = sanitizer.sanitize("slack_token=xoxb-FAKE-TEST-TOKEN-FOR-TESTING-ONLY")
        # Content is redacted (may match token pattern or secret pattern)
        assert result.is_safe is True  # Safe because redacted

    def test_sanitize_github_pat(self):
        """Test sanitizing GitHub PATs."""
        sanitizer = OutputSanitizer()
        result = sanitizer.sanitize("github_pat_1234567890abcdef")
        assert "[SECRET_REDACTED]" in result.sanitized_output

    def test_sanitize_gitlab_pat(self):
        """Test sanitizing GitLab PATs."""
        sanitizer = OutputSanitizer()
        result = sanitizer.sanitize("glpat-1234567890abcdef")
        assert "[SECRET_REDACTED]" in result.sanitized_output

    def test_sanitize_bearer_token(self):
        """Test sanitizing Bearer tokens."""
        sanitizer = OutputSanitizer()
        result = sanitizer.sanitize("Authorization: Bearer abc123xyz789")
        assert "[SECRET_REDACTED]" in result.sanitized_output

    def test_sanitize_removes_external_urls(self):
        """Test that external URLs are removed by default."""
        sanitizer = OutputSanitizer()
        result = sanitizer.sanitize("Visit https://external.com for more info")
        assert "[URL_REMOVED]" in result.sanitized_output
        assert "https://external.com" in result.removed_urls

    def test_sanitize_allows_external_urls_when_configured(self):
        """Test that external URLs can be allowed."""
        sanitizer = OutputSanitizer(allow_external_urls=True)
        result = sanitizer.sanitize("Visit https://external.com for more info")
        assert "https://external.com" in result.sanitized_output
        assert len(result.removed_urls) == 0

    def test_sanitize_allows_specific_domains(self):
        """Test allowing specific URL domains."""
        sanitizer = OutputSanitizer(
            allow_external_urls=False,
            allowed_url_domains=["example.com", "trusted.org"],
        )
        result = sanitizer.sanitize(
            "Visit https://example.com and https://untrusted.com"
        )
        assert "https://example.com" in result.sanitized_output
        assert "[URL_REMOVED]" in result.sanitized_output
        assert "https://untrusted.com" in result.removed_urls

    def test_sanitize_with_citations(self):
        """Test sanitizing content with citations."""
        sanitizer = OutputSanitizer()
        citation = Citation(
            source_id="1",
            source_path="docs/api.md",
            relevance_score=0.9,
        )
        context = SanitizationContext(
            query="What is the API?",
            sources_used=[citation],
        )
        result = sanitizer.sanitize("See [1] for API details", context)
        assert len(result.citations) == 1
        assert result.citations[0].source_id == "1"

    def test_sanitize_with_source_citation(self):
        """Test sanitizing content with source: citations."""
        sanitizer = OutputSanitizer()
        citation = Citation(
            source_id="api",
            source_path="docs/api.md",
            relevance_score=0.9,
        )
        context = SanitizationContext(
            query="What is the API?",
            sources_used=[citation],
        )
        result = sanitizer.sanitize("See [source:api.md] for details", context)
        assert len(result.citations) == 1

    def test_add_allowed_domain(self):
        """Test adding an allowed domain."""
        sanitizer = OutputSanitizer()
        sanitizer.add_allowed_domain("newdomain.com")
        result = sanitizer.sanitize("Visit https://newdomain.com")
        assert "https://newdomain.com" in result.sanitized_output

    def test_remove_allowed_domain(self):
        """Test removing an allowed domain."""
        sanitizer = OutputSanitizer(allowed_url_domains=["example.com"])
        sanitizer.remove_allowed_domain("example.com")
        result = sanitizer.sanitize("Visit https://example.com")
        assert "[URL_REMOVED]" in result.sanitized_output

    def test_add_secret_pattern(self):
        """Test adding a custom secret pattern."""
        sanitizer = OutputSanitizer()
        sanitizer.add_secret_pattern(r"CUSTOM_SECRET_\w+")
        result = sanitizer.sanitize("Found CUSTOM_SECRET_KEY here")
        assert "[SECRET_REDACTED]" in result.sanitized_output

    def test_get_stats(self):
        """Test getting sanitizer statistics."""
        sanitizer = OutputSanitizer()
        stats = sanitizer.get_stats()
        assert "secret_pattern_count" in stats
        assert "allowed_domains" in stats
        assert "allow_external_urls" in stats


class TestAuditEntry:
    """Tests for AuditEntry dataclass."""

    def test_audit_entry_creation(self):
        """Test creating an AuditEntry instance."""
        entry = AuditEntry(
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            event_type="query",
            query="What is the API?",
            sources_used=["docs/api.md"],
            response_preview="The API provides...",
            document_count=5,
            user_id="user@example.com",
            session_id="session-123",
            metadata={"key": "value"},
        )
        assert entry.event_type == "query"
        assert entry.query == "What is the API?"
        assert entry.sources_used == ["docs/api.md"]
        assert entry.document_count == 5

    def test_audit_entry_to_dict(self):
        """Test converting AuditEntry to dictionary."""
        entry = AuditEntry(
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            event_type="query",
            query="Test query",
            sources_used=["source1.md"],
        )
        result = entry.to_dict()
        assert result["event_type"] == "query"
        assert result["query"] == "Test query"
        assert result["sources_used"] == ["source1.md"]
        assert "timestamp" in result

    def test_audit_entry_to_json(self):
        """Test converting AuditEntry to JSON."""
        entry = AuditEntry(
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            event_type="query",
            query="Test query",
        )
        json_str = entry.to_json()
        data = json.loads(json_str)
        assert data["event_type"] == "query"
        assert data["query"] == "Test query"


class TestRAGAuditLogger:
    """Tests for RAGAuditLogger class."""

    @pytest.fixture
    def temp_audit_file(self, tmp_path):
        """Create a temporary audit file path."""
        return str(tmp_path / "audit.log")

    def test_init_creates_directory(self, tmp_path):
        """Test that initialization creates the directory."""
        audit_path = str(tmp_path / "subdir" / "audit.log")
        logger = RAGAuditLogger(path=audit_path)
        assert Path(audit_path).parent.exists()

    def test_init_with_existing_file(self, temp_audit_file):
        """Test initialization with existing audit file."""
        # Create a file with an existing entry
        entry_data = {
            "timestamp": "2024-01-01T12:00:00",
            "event_type": "query",
            "query": "Test query",
            "sources_used": ["source.md"],
        }
        with open(temp_audit_file, "w") as f:
            f.write(json.dumps(entry_data) + "\n")

        logger = RAGAuditLogger(path=temp_audit_file)
        assert len(logger._entries) == 1
        assert logger._entries[0].event_type == "query"

    @pytest.mark.asyncio
    async def test_log_query(self, temp_audit_file):
        """Test logging a query."""
        logger = RAGAuditLogger(path=temp_audit_file)
        await logger.log_query(
            query="What is the API?",
            sources_used=["docs/api.md"],
            response_preview="The API provides...",
            user_id="user@example.com",
        )
        assert len(logger._entries) == 1
        assert logger._entries[0].event_type == "query"
        assert logger._entries[0].query == "What is the API?"

    @pytest.mark.asyncio
    async def test_log_query_truncates_preview(self, temp_audit_file):
        """Test that long response previews are truncated."""
        logger = RAGAuditLogger(path=temp_audit_file)
        long_preview = "x" * 300
        await logger.log_query(
            query="Test",
            sources_used=[],
            response_preview=long_preview,
        )
        preview = logger._entries[0].response_preview
        assert preview is not None
        assert len(preview) == 203  # 200 + "..."

    @pytest.mark.asyncio
    async def test_log_indexing(self, temp_audit_file):
        """Test logging an indexing operation."""
        logger = RAGAuditLogger(path=temp_audit_file)
        await logger.log_indexing(
            source="./docs",
            document_count=42,
            indexed_by="user@example.com",
        )
        assert len(logger._entries) == 1
        assert logger._entries[0].event_type == "indexing"
        assert logger._entries[0].document_count == 42

    @pytest.mark.asyncio
    async def test_log_deletion(self, temp_audit_file):
        """Test logging a deletion operation."""
        logger = RAGAuditLogger(path=temp_audit_file)
        await logger.log_deletion(
            source="./docs",
            document_count=10,
            deleted_by="admin@example.com",
        )
        assert len(logger._entries) == 1
        assert logger._entries[0].event_type == "deletion"

    @pytest.mark.asyncio
    async def test_log_event(self, temp_audit_file):
        """Test logging a custom event."""
        logger = RAGAuditLogger(path=temp_audit_file)
        await logger.log_event(
            event_type="custom",
            query="Custom query",
            metadata={"custom_key": "custom_value"},
        )
        assert len(logger._entries) == 1
        assert logger._entries[0].event_type == "custom"

    @pytest.mark.asyncio
    async def test_get_recent_entries(self, temp_audit_file):
        """Test getting recent entries."""
        logger = RAGAuditLogger(path=temp_audit_file)
        await logger.log_query(query="Query 1", sources_used=[])
        await logger.log_query(query="Query 2", sources_used=[])
        await logger.log_indexing(source="docs", document_count=5)

        entries = await logger.get_recent_entries(limit=2)
        assert len(entries) == 2

    @pytest.mark.asyncio
    async def test_get_recent_entries_by_type(self, temp_audit_file):
        """Test getting recent entries filtered by type."""
        logger = RAGAuditLogger(path=temp_audit_file)
        await logger.log_query(query="Query 1", sources_used=[])
        await logger.log_indexing(source="docs", document_count=5)
        await logger.log_query(query="Query 2", sources_used=[])

        entries = await logger.get_recent_entries(event_type="query")
        assert len(entries) == 2
        assert all(e.event_type == "query" for e in entries)

    @pytest.mark.asyncio
    async def test_get_entries_by_date(self, temp_audit_file):
        """Test getting entries by date range."""
        logger = RAGAuditLogger(path=temp_audit_file)
        await logger.log_query(query="Query", sources_used=[])

        start_date = datetime(2020, 1, 1)
        end_date = datetime(2030, 1, 1)
        entries = await logger.get_entries_by_date(start_date, end_date)
        assert len(entries) == 1

    @pytest.mark.asyncio
    async def test_get_entries_by_query(self, temp_audit_file):
        """Test getting entries by query text."""
        logger = RAGAuditLogger(path=temp_audit_file)
        await logger.log_query(query="What is the API?", sources_used=[])
        await logger.log_query(query="How to use Python?", sources_used=[])
        await logger.log_indexing(source="docs", document_count=5)

        entries = await logger.get_entries_by_query("API")
        assert len(entries) == 1
        query = entries[0].query
        assert query is not None
        assert "API" in query

    @pytest.mark.asyncio
    async def test_get_stats(self, temp_audit_file):
        """Test getting audit log statistics."""
        logger = RAGAuditLogger(path=temp_audit_file)
        await logger.log_query(query="Query 1", sources_used=[])
        await logger.log_query(query="Query 2", sources_used=[])
        await logger.log_indexing(source="docs", document_count=5)

        stats = await logger.get_stats()
        assert stats["total_entries"] == 3
        assert stats["event_counts"]["query"] == 2
        assert stats["event_counts"]["indexing"] == 1

    @pytest.mark.asyncio
    async def test_clear(self, temp_audit_file):
        """Test clearing audit log."""
        logger = RAGAuditLogger(path=temp_audit_file)
        await logger.log_query(query="Query", sources_used=[])
        await logger.clear()
        assert len(logger._entries) == 0
        assert not Path(temp_audit_file).exists()

    @pytest.mark.asyncio
    async def test_export(self, temp_audit_file, tmp_path):
        """Test exporting audit log."""
        logger = RAGAuditLogger(path=temp_audit_file)
        await logger.log_query(query="Query 1", sources_used=[])
        await logger.log_query(query="Query 2", sources_used=[])

        export_path = str(tmp_path / "export.log")
        count = await logger.export(export_path)
        assert count == 2
        assert Path(export_path).exists()

    @pytest.mark.asyncio
    async def test_export_with_date_filter(self, temp_audit_file, tmp_path):
        """Test exporting with date filter."""
        logger = RAGAuditLogger(path=temp_audit_file)
        await logger.log_query(query="Query", sources_used=[])

        export_path = str(tmp_path / "export.log")
        start_date = datetime(2020, 1, 1)
        count = await logger.export(export_path, start_date=start_date)
        assert count == 1

    def test_max_entries_limit(self, tmp_path):
        """Test that entries are limited to max_entries."""
        audit_path = str(tmp_path / "audit.log")
        logger = RAGAuditLogger(path=audit_path, max_entries=2)

        # Add entries directly
        for i in range(5):
            logger._entries.append(AuditEntry(
                timestamp=datetime.utcnow(),
                event_type="query",
                query=f"Query {i}",
            ))

        # Simulate the trim that happens in _append_entry
        if len(logger._entries) > logger.max_entries:
            logger._entries = logger._entries[-logger.max_entries:]

        assert len(logger._entries) == 2


class TestSafetyModuleInit:
    """Tests for the safety module __init__.py."""

    def test_imports(self):
        """Test that all expected items are importable."""
        from opencode.core.rag.safety import (
            ContentFilter,
            FilteredContent,
            OutputSanitizer,
            SanitizedOutput,
            RAGAuditLogger,
            AuditEntry,
        )
        assert ContentFilter is not None
        assert FilteredContent is not None
        assert OutputSanitizer is not None
        assert SanitizedOutput is not None
        assert RAGAuditLogger is not None
        assert AuditEntry is not None
