"""
Content Validator for Privacy-First RAG.

Validates RAG content for accuracy through multiple methods:
- Test-based validation: Content fails tests
- AI-based validation: Model determines content is incorrect
- User-accepted corrections: User confirms false content
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ValidationType(str, Enum):
    """Types of content validation."""
    TEST = "test"  # Content failed tests
    AI = "ai"  # AI model determined incorrect
    USER = "user"  # User confirmed as false


class ValidationStatus(str, Enum):
    """Status of validation."""
    PENDING = "pending"
    VALIDATED = "validated"
    FALSE = "false"
    DISPUTED = "disputed"


class ValidationResult(BaseModel):
    """Result of content validation."""
    
    content_id: str = Field(..., description="ID of validated content")
    content_hash: str = Field(..., description="Hash of content")
    source_id: str = Field(..., description="Source document ID")
    
    validation_type: ValidationType = Field(..., description="Type of validation")
    status: ValidationStatus = Field(default=ValidationStatus.PENDING, description="Validation status")
    
    is_valid: bool = Field(default=True, description="Whether content is valid")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence in result")
    
    reason: Optional[str] = Field(default=None, description="Reason for validation result")
    evidence: Optional[str] = Field(default=None, description="Evidence supporting result")
    
    validated_at: datetime = Field(default_factory=datetime.utcnow, description="When validated")
    validated_by: Optional[str] = Field(default=None, description="Who/what validated")
    
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content_id": self.content_id,
            "content_hash": self.content_hash,
            "source_id": self.source_id,
            "validation_type": self.validation_type.value,
            "status": self.status.value,
            "is_valid": self.is_valid,
            "confidence": self.confidence,
            "reason": self.reason,
            "evidence": self.evidence[:200] if self.evidence else None,
            "validated_at": self.validated_at.isoformat(),
            "validated_by": self.validated_by,
        }


class ContentValidator:
    """
    Validates RAG content for accuracy.
    
    Detection methods:
    - Test-based validation: Content fails tests
    - AI-based validation: Model determines content is incorrect
    - User-accepted corrections: User confirms false content
    
    Example:
        ```python
        validator = ContentValidator()
        
        # Validate content from test failure
        result = await validator.validate_content(
            content="The function returns a string",
            source_id="doc_123",
            validation_type=ValidationType.TEST,
            evidence="Test test_return_type failed: expected int, got str",
        )
        
        if not result.is_valid:
            # Mark as false content
            await registry.add_false_content(...)
        ```
    """
    
    def __init__(
        self,
        min_confidence: float = 0.7,
        require_evidence: bool = True,
    ):
        """
        Initialize content validator.
        
        Args:
            min_confidence: Minimum confidence to mark as false
            require_evidence: Whether evidence is required
        """
        self.min_confidence = min_confidence
        self.require_evidence = require_evidence
        
        # Track validation history
        self._validation_history: List[ValidationResult] = []
    
    def _hash_content(self, content: str) -> str:
        """Generate hash for content."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    async def validate_content(
        self,
        content: str,
        source_id: str,
        validation_type: ValidationType,
        reason: Optional[str] = None,
        evidence: Optional[str] = None,
        validated_by: Optional[str] = None,
        confidence: float = 1.0,
    ) -> ValidationResult:
        """
        Validate content and return result.
        
        Args:
            content: Content to validate
            source_id: Source document ID
            validation_type: Type of validation
            reason: Reason for validation
            evidence: Evidence supporting validation
            validated_by: Who/what performed validation
            confidence: Confidence in result
            
        Returns:
            ValidationResult
        """
        content_hash = self._hash_content(content)
        content_id = f"val_{content_hash}"
        
        # Determine if content is valid based on evidence
        is_valid = True
        
        if validation_type == ValidationType.TEST:
            # Test failures indicate false content
            is_valid = False
            
        elif validation_type == ValidationType.AI:
            # AI validation requires confidence check
            is_valid = confidence >= self.min_confidence and not reason
            
        elif validation_type == ValidationType.USER:
            # User confirmation is definitive
            is_valid = not reason or "false" not in reason.lower()
        
        # Create result
        result = ValidationResult(
            content_id=content_id,
            content_hash=content_hash,
            source_id=source_id,
            validation_type=validation_type,
            status=ValidationStatus.VALIDATED if is_valid else ValidationStatus.FALSE,
            is_valid=is_valid,
            confidence=confidence,
            reason=reason,
            evidence=evidence,
            validated_by=validated_by,
        )
        
        # Store in history
        self._validation_history.append(result)
        
        logger.info(
            f"Content validation: {content_id} - "
            f"{'VALID' if is_valid else 'FALSE'} "
            f"(type={validation_type.value}, confidence={confidence:.2f})"
        )
        
        return result
    
    async def mark_false_content(
        self,
        content: str,
        source_id: str,
        reason: str,
        evidence: Optional[str] = None,
        marked_by: Optional[str] = None,
    ) -> ValidationResult:
        """
        Mark content as false.
        
        Args:
            content: Content to mark as false
            source_id: Source document ID
            reason: Reason for marking as false
            evidence: Evidence supporting the marking
            marked_by: Who marked it as false
            
        Returns:
            ValidationResult with FALSE status
        """
        return await self.validate_content(
            content=content,
            source_id=source_id,
            validation_type=ValidationType.USER,
            reason=reason,
            evidence=evidence,
            validated_by=marked_by,
            confidence=1.0,
        )
    
    async def validate_from_test_failure(
        self,
        content: str,
        source_id: str,
        test_name: str,
        test_output: str,
    ) -> ValidationResult:
        """
        Validate content based on test failure.
        
        Args:
            content: Content that may be false
            source_id: Source document ID
            test_name: Name of failed test
            test_output: Test output/error message
            
        Returns:
            ValidationResult
        """
        return await self.validate_content(
            content=content,
            source_id=source_id,
            validation_type=ValidationType.TEST,
            reason=f"Test '{test_name}' failed",
            evidence=test_output,
            validated_by="test_runner",
        )
    
    async def validate_from_ai_detection(
        self,
        content: str,
        source_id: str,
        ai_model: str,
        ai_reasoning: str,
        confidence: float,
    ) -> ValidationResult:
        """
        Validate content based on AI detection.
        
        Args:
            content: Content that AI detected as potentially false
            source_id: Source document ID
            ai_model: AI model that detected the issue
            ai_reasoning: AI's reasoning for the detection
            confidence: AI's confidence in the detection
            
        Returns:
            ValidationResult
        """
        return await self.validate_content(
            content=content,
            source_id=source_id,
            validation_type=ValidationType.AI,
            reason=ai_reasoning,
            evidence=f"Detected by {ai_model}",
            validated_by=ai_model,
            confidence=confidence,
        )
    
    def get_validation_history(
        self,
        source_id: Optional[str] = None,
        validation_type: Optional[ValidationType] = None,
        limit: int = 100,
    ) -> List[ValidationResult]:
        """
        Get validation history.
        
        Args:
            source_id: Filter by source ID
            validation_type: Filter by validation type
            limit: Maximum results to return
            
        Returns:
            List of validation results
        """
        results = self._validation_history
        
        if source_id:
            results = [r for r in results if r.source_id == source_id]
        
        if validation_type:
            results = [r for r in results if r.validation_type == validation_type]
        
        return results[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get validator statistics.
        
        Returns:
            Statistics dictionary
        """
        total = len(self._validation_history)
        valid = sum(1 for r in self._validation_history if r.is_valid)
        false = total - valid
        
        by_type: Dict[str, int] = {}
        for result in self._validation_history:
            key = result.validation_type.value
            by_type[key] = by_type.get(key, 0) + 1
        
        return {
            "total_validations": total,
            "valid_content": valid,
            "false_content": false,
            "false_rate": false / total if total > 0 else 0,
            "by_type": by_type,
        }
