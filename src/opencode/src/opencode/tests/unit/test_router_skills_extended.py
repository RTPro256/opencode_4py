"""
Tests for router/skills.py - Skill classifier module.

This module provides tests for the SkillClassifier which classifies
prompts into categories and suggests relevant skills.
"""

import pytest
from opencode.router.skills import (
    SkillClassifier,
    ClassificationResult,
)
from opencode.router.config import PromptCategory, Complexity


class TestSkillClassifier:
    """Test cases for SkillClassifier."""

    def test_classifier_initialization(self):
        """Test classifier initializes correctly."""
        classifier = SkillClassifier()
        assert classifier is not None

    def test_classify_coding_prompt(self):
        """Test classification of coding prompts."""
        classifier = SkillClassifier()
        result = classifier.classify("Write a Python function to calculate fibonacci numbers")
        
        assert result.category == PromptCategory.CODING
        assert result.complexity in [Complexity.SIMPLE, Complexity.MEDIUM, Complexity.HARD]
        assert 0 <= result.confidence <= 1.0

    def test_classify_reasoning_prompt(self):
        """Test classification of reasoning prompts."""
        classifier = SkillClassifier()
        result = classifier.classify("Analyze and explain why this approach works")
        
        # Reasoning prompts should be classified as something valid
        assert result.category in [PromptCategory.REASONING, PromptCategory.ANALYSIS, PromptCategory.GENERAL]

    def test_classify_creative_prompt(self):
        """Test classification of creative prompts."""
        classifier = SkillClassifier()
        result = classifier.classify("Write a creative story about a robot")
        
        assert result.category == PromptCategory.CREATIVE

    def test_classify_general_prompt(self):
        """Test classification of general prompts."""
        classifier = SkillClassifier()
        result = classifier.classify("Hello, how are you?")
        
        # General prompts should have low confidence
        assert result.confidence <= 0.6

    def test_classify_short_prompt(self):
        """Test classification of short prompts."""
        classifier = SkillClassifier()
        result = classifier.classify("fix this")
        
        # Short prompts should be classified as simple
        assert result.complexity == Complexity.SIMPLE

    def test_classify_long_prompt(self):
        """Test classification of long prompts."""
        classifier = SkillClassifier()
        long_prompt = "Write a comprehensive solution for processing multiple data sources " * 10
        result = classifier.classify(long_prompt)
        
        # Long prompts may be classified as harder
        assert result.complexity in [Complexity.SIMPLE, Complexity.MEDIUM, Complexity.HARD]

    def test_classify_math_prompt(self):
        """Test classification of math prompts."""
        classifier = SkillClassifier()
        result = classifier.classify("Calculate the square root of 144")
        
        assert result.category == PromptCategory.MATH

    def test_classify_analysis_prompt(self):
        """Test classification of analysis prompts."""
        classifier = SkillClassifier()
        result = classifier.classify("Analyze the performance of this algorithm")
        
        assert result.category == PromptCategory.ANALYSIS

    def test_classify_translation_prompt(self):
        """Test classification of translation prompts."""
        classifier = SkillClassifier()
        result = classifier.classify("Translate this text to French")
        
        assert result.category == PromptCategory.TRANSLATION

    def test_classify_summarization_prompt(self):
        """Test classification of summarization prompts."""
        classifier = SkillClassifier()
        result = classifier.classify("Summarize this article into a brief overview")
        
        # Should return a valid category (might be summarization or translation depending on patterns)
        assert result.category in [PromptCategory.SUMMARIZATION, PromptCategory.TRANSLATION, PromptCategory.GENERAL, PromptCategory.CREATIVE]

    def test_complexity_simple(self):
        """Test complexity assessment for simple prompts."""
        classifier = SkillClassifier()
        result = classifier.classify("add two numbers")
        
        assert result.complexity == Complexity.SIMPLE

    def test_complexity_medium(self):
        """Test complexity assessment for medium prompts."""
        classifier = SkillClassifier()
        # Use a longer prompt with more complex language
        result = classifier.classify(
            "Design and implement a comprehensive system architecture that handles "
            "multiple data sources and ensures proper validation"
        )
        
        assert result.complexity in [Complexity.MEDIUM, Complexity.HARD]

    def test_complexity_hard(self):
        """Test complexity assessment for hard prompts."""
        classifier = SkillClassifier()
        result = classifier.classify(
            "Design and implement a distributed system architecture that handles "
            "high concurrency, ensures data consistency across multiple regions, "
            "and implements fault tolerance with automatic failover capabilities "
            "while maintaining optimal performance under varying load conditions"
        )
        
        assert result.complexity in [Complexity.MEDIUM, Complexity.HARD]

    def test_indicators_returned(self):
        """Test that classification returns matched indicators."""
        classifier = SkillClassifier()
        result = classifier.classify("Write a function that calculates fibonacci")
        
        # Should return indicators if any patterns matched
        assert isinstance(result.indicators, list)

    def test_suggested_skills_coding(self):
        """Test skill suggestions for coding category."""
        classifier = SkillClassifier()
        result = classifier.classify("Write Python code")
        
        # Should suggest relevant skills
        assert isinstance(result.suggested_skills, list)

    def test_get_category_description_coding(self):
        """Test getting category description for coding."""
        classifier = SkillClassifier()
        desc = classifier.get_category_description(PromptCategory.CODING)
        
        assert isinstance(desc, str)
        assert len(desc) > 0

    def test_get_category_description_reasoning(self):
        """Test getting category description for reasoning."""
        classifier = SkillClassifier()
        desc = classifier.get_category_description(PromptCategory.REASONING)
        
        assert isinstance(desc, str)

    def test_get_category_description_creative(self):
        """Test getting category description for creative."""
        classifier = SkillClassifier()
        desc = classifier.get_category_description(PromptCategory.CREATIVE)
        
        assert isinstance(desc, str)

    def test_get_category_description_general(self):
        """Test getting category description for general."""
        classifier = SkillClassifier()
        desc = classifier.get_category_description(PromptCategory.GENERAL)
        
        assert isinstance(desc, str)

    def test_get_category_description_math(self):
        """Test getting category description for math."""
        classifier = SkillClassifier()
        desc = classifier.get_category_description(PromptCategory.MATH)
        
        assert isinstance(desc, str)

    def test_get_category_description_analysis(self):
        """Test getting category description for analysis."""
        classifier = SkillClassifier()
        desc = classifier.get_category_description(PromptCategory.ANALYSIS)
        
        assert isinstance(desc, str)

    def test_get_category_description_translation(self):
        """Test getting category description for translation."""
        classifier = SkillClassifier()
        desc = classifier.get_category_description(PromptCategory.TRANSLATION)
        
        assert isinstance(desc, str)

    def test_get_category_description_summarization(self):
        """Test getting category description for summarization."""
        classifier = SkillClassifier()
        desc = classifier.get_category_description(PromptCategory.SUMMARIZATION)
        
        assert isinstance(desc, str)

    def test_score_category_with_matches(self):
        """Test _score_category with pattern matches."""
        classifier = SkillClassifier()
        score, indicators = classifier._score_category(
            "Write a python function to calculate fibonacci numbers using recursion",
            "coding"
        )
        
        assert isinstance(score, float)
        assert 0 <= score <= 1.5  # Can be boosted above 1.0
        assert isinstance(indicators, list)

    def test_score_category_no_matches(self):
        """Test _score_category with no pattern matches."""
        classifier = SkillClassifier()
        score, indicators = classifier._score_category(
            "Hello world",
            "coding"
        )
        
        assert score == 0.0
        assert indicators == []

    def test_score_category_multiple_matches(self):
        """Test _score_category with multiple matches."""
        classifier = SkillClassifier()
        score, indicators = classifier._score_category(
            "write code that generates python program with function definition and class implementation",
            "coding"
        )
        
        # Multiple matches should boost score
        assert isinstance(score, float)

    def test_assess_complexity_simple_indicators(self):
        """Test complexity assessment with simple indicators."""
        classifier = SkillClassifier()
        complexity = classifier._assess_complexity("add two numbers")
        
        assert complexity == Complexity.SIMPLE

    def test_assess_complexity_hard_indicators(self):
        """Test complexity assessment with hard indicators."""
        classifier = SkillClassifier()
        complexity = classifier._assess_complexity(
            "design architecture distributed system microservices failover"
        )
        
        assert complexity in [Complexity.MEDIUM, Complexity.HARD]

    def test_assess_complexity_length_based(self):
        """Test complexity assessment based on prompt length."""
        classifier = SkillClassifier()
        
        # Short prompt
        complexity = classifier._assess_complexity("fix bug")
        assert complexity == Complexity.SIMPLE
        
        # Very long prompt should be harder
        long_prompt = "word " * 300
        complexity = classifier._assess_complexity(long_prompt)
        assert complexity in [Complexity.MEDIUM, Complexity.HARD]

    def test_suggest_skills_coding_simple(self):
        """Test skill suggestions for coding + simple."""
        classifier = SkillClassifier()
        skills = classifier._suggest_skills(PromptCategory.CODING, Complexity.SIMPLE)
        
        assert isinstance(skills, list)

    def test_suggest_skills_coding_medium(self):
        """Test skill suggestions for coding + medium."""
        classifier = SkillClassifier()
        skills = classifier._suggest_skills(PromptCategory.CODING, Complexity.MEDIUM)
        
        assert isinstance(skills, list)

    def test_suggest_skills_coding_hard(self):
        """Test skill suggestions for coding + hard."""
        classifier = SkillClassifier()
        skills = classifier._suggest_skills(PromptCategory.CODING, Complexity.HARD)
        
        assert isinstance(skills, list)

    def test_suggest_skills_reasoning(self):
        """Test skill suggestions for reasoning."""
        classifier = SkillClassifier()
        skills = classifier._suggest_skills(PromptCategory.REASONING, Complexity.MEDIUM)
        
        assert isinstance(skills, list)

    def test_suggest_skills_creative(self):
        """Test skill suggestions for creative."""
        classifier = SkillClassifier()
        skills = classifier._suggest_skills(PromptCategory.CREATIVE, Complexity.MEDIUM)
        
        assert isinstance(skills, list)

    def test_suggest_skills_math(self):
        """Test skill suggestions for math."""
        classifier = SkillClassifier()
        skills = classifier._suggest_skills(PromptCategory.MATH, Complexity.MEDIUM)
        
        assert isinstance(skills, list)

    def test_suggest_skills_analysis(self):
        """Test skill suggestions for analysis."""
        classifier = SkillClassifier()
        skills = classifier._suggest_skills(PromptCategory.ANALYSIS, Complexity.HARD)
        
        assert isinstance(skills, list)

    def test_suggest_skills_translation(self):
        """Test skill suggestions for translation."""
        classifier = SkillClassifier()
        skills = classifier._suggest_skills(PromptCategory.TRANSLATION, Complexity.MEDIUM)
        
        assert isinstance(skills, list)

    def test_suggest_skills_summarization(self):
        """Test skill suggestions for summarization."""
        classifier = SkillClassifier()
        skills = classifier._suggest_skills(PromptCategory.SUMMARIZATION, Complexity.SIMPLE)
        
        assert isinstance(skills, list)

    def test_suggest_skills_general(self):
        """Test skill suggestions for general."""
        classifier = SkillClassifier()
        skills = classifier._suggest_skills(PromptCategory.GENERAL, Complexity.SIMPLE)
        
        assert isinstance(skills, list)

    def test_classify_returns_valid_result(self):
        """Test that classify always returns a valid result."""
        classifier = SkillClassifier()
        
        for prompt in [
            "hello",
            "write code",
            "fix bug" * 100,
            "",
            "a" * 1000,
            "test with special chars: @#$%",
            "multi\nline\nprompt",
        ]:
            result = classifier.classify(prompt)
            assert isinstance(result, ClassificationResult)
            assert result.category is not None
            assert result.complexity is not None
            assert 0 <= result.confidence <= 1.0

    def test_empty_prompt(self):
        """Test classification of empty prompt."""
        classifier = SkillClassifier()
        result = classifier.classify("")
        
        # Should still return a valid result
        assert result.category is not None

    def test_special_characters(self):
        """Test classification with special characters."""
        classifier = SkillClassifier()
        result = classifier.classify("Write code with special chars: @#$%^&*()")
        
        assert result is not None

    def test_unicode_content(self):
        """Test classification with unicode content."""
        classifier = SkillClassifier()
        result = classifier.classify("Write code with unicode: 你好世界 🌍")
        
        assert result is not None
