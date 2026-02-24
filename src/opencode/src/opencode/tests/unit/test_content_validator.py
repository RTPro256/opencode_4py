"""
Tests for Content Validator.

Tests content validation for RAG accuracy.
"""

from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

from opencode.core.rag.validation.content_validator import (
    ContentValidator,
    ValidationResult,
    ValidationType,
    ValidationStatus,
)


class TestValidationType:
    """Tests for ValidationType enum."""

    def test_validation_types(self):
        """Test that all validation types exist."""
        assert ValidationType.TEST == "test"
        assert ValidationType.AI == "ai"
        assert ValidationType.USER == "user"


class TestValidationStatus:
    """Tests for ValidationStatus enum."""

    def test_validation_statuses(self):
        """Test that all validation statuses exist."""
        assert ValidationStatus.PENDING == "pending"
        assert ValidationStatus.VALIDATED == "validated"
        assert ValidationStatus.FALSE == "false"
        assert ValidationStatus.DISPUTED == "disputed"


class TestValidationResult:
    """Tests for ValidationResult model."""

    def test_validation_result_creation(self):
        """Test creating a ValidationResult."""
        result = ValidationResult(
            content_id="val_123",
            content_hash="abc123",
            source_id="doc_456",
            validation_type=ValidationType.TEST,
        )
        assert result.content_id == "val_123"
        assert result.content_hash == "abc123"
        assert result.source_id == "doc_456"
        assert result.validation_type == ValidationType.TEST
        assert result.status == ValidationStatus.PENDING
        assert result.is_valid is True
        assert result.confidence == 1.0

    def test_validation_result_with_all_fields(self):
        """Test creating ValidationResult with all fields."""
        result = ValidationResult(
            content_id="val_123",
            content_hash="abc123",
            source_id="doc_456",
            validation_type=ValidationType.AI,
            status=ValidationStatus.FALSE,
            is_valid=False,
            confidence=0.85,
            reason="Content is incorrect",
            evidence="Test evidence",
            validated_by="test_model",
            metadata={"key": "value"},
        )
        assert result.is_valid is False
        assert result.confidence == 0.85
        assert result.reason == "Content is incorrect"
        assert result.evidence == "Test evidence"
        assert result.validated_by == "test_model"
        assert result.metadata == {"key": "value"}

    def test_validation_result_to_dict(self):
        """Test converting ValidationResult to dictionary."""
        result = ValidationResult(
            content_id="val_123",
            content_hash="abc123",
            source_id="doc_456",
            validation_type=ValidationType.TEST,
            status=ValidationStatus.FALSE,
            is_valid=False,
            reason="Test reason",
            evidence="Test evidence that is quite long and should be truncated",
            validated_by="tester",
        )
        data = result.to_dict()
        assert data["content_id"] == "val_123"
        assert data["validation_type"] == "test"
        assert data["status"] == "false"
        assert data["is_valid"] is False
        # Evidence is truncated to 200 chars if longer
        assert data["evidence"] is not None

    def test_validation_result_to_dict_no_evidence(self):
        """Test to_dict with no evidence."""
        result = ValidationResult(
            content_id="val_123",
            content_hash="abc123",
            source_id="doc_456",
            validation_type=ValidationType.USER,
        )
        data = result.to_dict()
        assert data["evidence"] is None


class TestContentValidator:
    """Tests for ContentValidator class."""

    def test_init_defaults(self):
        """Test ContentValidator initialization with defaults."""
        validator = ContentValidator()
        assert validator.min_confidence == 0.7
        assert validator.require_evidence is True

    def test_init_custom(self):
        """Test ContentValidator initialization with custom values."""
        validator = ContentValidator(min_confidence=0.9, require_evidence=False)
        assert validator.min_confidence == 0.9
        assert validator.require_evidence is False

    def test_hash_content(self):
        """Test content hashing."""
        validator = ContentValidator()
        hash1 = validator._hash_content("test content")
        hash2 = validator._hash_content("test content")
        hash3 = validator._hash_content("different content")
        
        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 16

    @pytest.mark.asyncio
    async def test_validate_content_test_type(self):
        """Test validating content with TEST type."""
        validator = ContentValidator()
        result = await validator.validate_content(
            content="The function returns a string",
            source_id="doc_123",
            validation_type=ValidationType.TEST,
            reason="Test failed",
            evidence="Expected int, got str",
        )
        assert result.is_valid is False
        assert result.status == ValidationStatus.FALSE
        assert result.validation_type == ValidationType.TEST

    @pytest.mark.asyncio
    async def test_validate_content_ai_type_valid(self):
        """Test validating content with AI type - valid result."""
        validator = ContentValidator(min_confidence=0.7)
        result = await validator.validate_content(
            content="The function returns an integer",
            source_id="doc_123",
            validation_type=ValidationType.AI,
            confidence=0.9,
            validated_by="gpt-4",
        )
        # AI validation with high confidence and no reason = valid
        assert result.is_valid is True
        assert result.status == ValidationStatus.VALIDATED

    @pytest.mark.asyncio
    async def test_validate_content_ai_type_invalid(self):
        """Test validating content with AI type - invalid result."""
        validator = ContentValidator(min_confidence=0.7)
        result = await validator.validate_content(
            content="The function returns a string",
            source_id="doc_123",
            validation_type=ValidationType.AI,
            reason="Content appears incorrect",
            confidence=0.9,
            validated_by="gpt-4",
        )
        # AI validation with reason = invalid
        assert result.is_valid is False
        assert result.status == ValidationStatus.FALSE

    @pytest.mark.asyncio
    async def test_validate_content_ai_type_low_confidence(self):
        """Test validating content with AI type - low confidence."""
        validator = ContentValidator(min_confidence=0.7)
        result = await validator.validate_content(
            content="The function returns something",
            source_id="doc_123",
            validation_type=ValidationType.AI,
            confidence=0.5,
            validated_by="gpt-4",
        )
        # Low confidence = invalid
        assert result.is_valid is False

    @pytest.mark.asyncio
    async def test_validate_content_user_type_valid(self):
        """Test validating content with USER type - valid."""
        validator = ContentValidator()
        result = await validator.validate_content(
            content="The function returns an integer",
            source_id="doc_123",
            validation_type=ValidationType.USER,
            reason="This looks correct",
            validated_by="user@example.com",
        )
        assert result.is_valid is True
        assert result.status == ValidationStatus.VALIDATED

    @pytest.mark.asyncio
    async def test_validate_content_user_type_false(self):
        """Test validating content with USER type - false."""
        validator = ContentValidator()
        result = await validator.validate_content(
            content="The function returns a string",
            source_id="doc_123",
            validation_type=ValidationType.USER,
            reason="This is false information",
            validated_by="user@example.com",
        )
        assert result.is_valid is False
        assert result.status == ValidationStatus.FALSE

    @pytest.mark.asyncio
    async def test_mark_false_content(self):
        """Test marking content as false."""
        validator = ContentValidator()
        result = await validator.mark_false_content(
            content="Incorrect statement",
            source_id="doc_123",
            reason="This is false information",
            evidence="Test evidence",
            marked_by="admin@example.com",
        )
        assert result.is_valid is False
        assert result.status == ValidationStatus.FALSE
        assert result.validation_type == ValidationType.USER

    @pytest.mark.asyncio
    async def test_validate_from_test_failure(self):
        """Test validating from test failure."""
        validator = ContentValidator()
        result = await validator.validate_from_test_failure(
            content="The function returns a string",
            source_id="doc_123",
            test_name="test_return_type",
            test_output="AssertionError: Expected int, got str",
        )
        assert result.is_valid is False
        assert result.validation_type == ValidationType.TEST
        assert result.reason is not None
        assert "test_return_type" in result.reason
        assert result.evidence is not None
        assert "AssertionError" in result.evidence

    @pytest.mark.asyncio
    async def test_validate_from_ai_detection(self):
        """Test validating from AI detection."""
        validator = ContentValidator()
        result = await validator.validate_from_ai_detection(
            content="The API returns JSON",
            source_id="doc_123",
            ai_model="gpt-4",
            ai_reasoning="The API actually returns XML",
            confidence=0.95,
        )
        assert result.validation_type == ValidationType.AI
        assert result.validated_by == "gpt-4"
        assert result.confidence == 0.95

    @pytest.mark.asyncio
    async def test_validation_history(self):
        """Test validation history tracking."""
        validator = ContentValidator()
        
        # Add multiple validations
        await validator.validate_content(
            content="Content 1",
            source_id="doc_1",
            validation_type=ValidationType.TEST,
        )
        await validator.validate_content(
            content="Content 2",
            source_id="doc_2",
            validation_type=ValidationType.AI,
        )
        await validator.validate_content(
            content="Content 3",
            source_id="doc_1",
            validation_type=ValidationType.USER,
        )
        
        history = validator.get_validation_history()
        assert len(history) == 3

    @pytest.mark.asyncio
    async def test_validation_history_filter_by_source(self):
        """Test validation history filtered by source."""
        validator = ContentValidator()
        
        await validator.validate_content(
            content="Content 1",
            source_id="doc_1",
            validation_type=ValidationType.TEST,
        )
        await validator.validate_content(
            content="Content 2",
            source_id="doc_2",
            validation_type=ValidationType.AI,
        )
        
        history = validator.get_validation_history(source_id="doc_1")
        assert len(history) == 1
        assert history[0].source_id == "doc_1"

    @pytest.mark.asyncio
    async def test_validation_history_filter_by_type(self):
        """Test validation history filtered by type."""
        validator = ContentValidator()
        
        await validator.validate_content(
            content="Content 1",
            source_id="doc_1",
            validation_type=ValidationType.TEST,
        )
        await validator.validate_content(
            content="Content 2",
            source_id="doc_2",
            validation_type=ValidationType.AI,
        )
        
        history = validator.get_validation_history(validation_type=ValidationType.TEST)
        assert len(history) == 1
        assert history[0].validation_type == ValidationType.TEST

    @pytest.mark.asyncio
    async def test_validation_history_limit(self):
        """Test validation history with limit."""
        validator = ContentValidator()
        
        for i in range(10):
            await validator.validate_content(
                content=f"Content {i}",
                source_id=f"doc_{i}",
                validation_type=ValidationType.TEST,
            )
        
        history = validator.get_validation_history(limit=5)
        assert len(history) == 5

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test getting validator statistics."""
        validator = ContentValidator()
        
        # Add validations with different results
        await validator.validate_content(
            content="Valid content",
            source_id="doc_1",
            validation_type=ValidationType.AI,
            confidence=0.9,
        )
        await validator.validate_content(
            content="Invalid content",
            source_id="doc_2",
            validation_type=ValidationType.TEST,
        )
        await validator.validate_content(
            content="User validated",
            source_id="doc_3",
            validation_type=ValidationType.USER,
        )
        
        stats = validator.get_stats()
        assert stats["total_validations"] == 3
        assert stats["valid_content"] == 2  # AI (valid) + USER (valid)
        assert stats["false_content"] == 1  # TEST (invalid)
        assert "false_rate" in stats
        assert "by_type" in stats
        assert stats["by_type"]["test"] == 1
        assert stats["by_type"]["ai"] == 1
        assert stats["by_type"]["user"] == 1

    @pytest.mark.asyncio
    async def test_get_stats_empty(self):
        """Test getting stats with no validations."""
        validator = ContentValidator()
        stats = validator.get_stats()
        assert stats["total_validations"] == 0
        assert stats["false_rate"] == 0

    @pytest.mark.asyncio
    async def test_content_id_generation(self):
        """Test that content IDs are generated consistently."""
        validator = ContentValidator()
        
        result1 = await validator.validate_content(
            content="Same content",
            source_id="doc_1",
            validation_type=ValidationType.TEST,
        )
        result2 = await validator.validate_content(
            content="Same content",
            source_id="doc_2",
            validation_type=ValidationType.AI,
        )
        
        # Same content should generate same ID
        assert result1.content_id == result2.content_id
        assert result1.content_hash == result2.content_hash
