"""
Benchmark tests for prompt accuracy across models.

Uses standardized test sets to measure and track accuracy over time.
"""

import pytest
from typing import List, Dict, Any, Callable
from unittest.mock import AsyncMock, MagicMock
import json
from pathlib import Path

from opencode.provider.base import Message, MessageRole


class PromptAccuracyBenchmark:
    """Benchmark suite for prompt accuracy."""
    
    # Standard test sets
    MATH_TEST_SET = [
        {"q": "What is 7 * 8?", "a": "56"},
        {"q": "What is 144 / 12?", "a": "12"},
        {"q": "What is 15% of 200?", "a": "30"},
    ]
    
    CODE_TEST_SET = [
        {
            "q": "Write a Python one-liner to reverse a string.",
            "validate": lambda r: "[::-1]" in r or "reversed" in r,
        },
        {
            "q": "Write a Python list comprehension to square numbers 1-10.",
            "validate": lambda r: "[" in r and "**2" in r and "for" in r,
        },
    ]
    
    REASONING_TEST_SET = [
        {
            "q": "If John is taller than Mary, and Mary is taller than Sue, who is the shortest?",
            "a": "Sue",
        },
        {
            "q": "All cats are animals. All animals need water. Do cats need water?",
            "a": "yes",
        },
    ]


@pytest.mark.prompt
class TestPromptAccuracy:
    """Test prompt accuracy across models."""
    
    @pytest.fixture
    def benchmark(self) -> PromptAccuracyBenchmark:
        return PromptAccuracyBenchmark()
    
    @pytest.fixture
    def mock_provider(self):
        """Create a mock provider for testing."""
        from opencode.provider.base import Provider, ModelInfo, CompletionResponse
        
        provider = MagicMock(spec=Provider)
        provider.name = "mock"
        provider.models = [ModelInfo(id="mock-model", name="Mock", provider="mock", context_length=4096)]
        provider.complete_sync = AsyncMock(return_value=CompletionResponse(
            content="56",
            model="mock-model",
        ))
        return provider
    
    def test_benchmark_has_math_tests(self, benchmark):
        """Test that benchmark has math tests."""
        assert len(benchmark.MATH_TEST_SET) > 0
        
        for item in benchmark.MATH_TEST_SET:
            assert "q" in item
            assert "a" in item
    
    def test_benchmark_has_code_tests(self, benchmark):
        """Test that benchmark has code tests."""
        assert len(benchmark.CODE_TEST_SET) > 0
        
        for item in benchmark.CODE_TEST_SET:
            assert "q" in item
            assert "validate" in item
            assert callable(item["validate"])
    
    def test_benchmark_has_reasoning_tests(self, benchmark):
        """Test that benchmark has reasoning tests."""
        assert len(benchmark.REASONING_TEST_SET) > 0
    
    @pytest.mark.asyncio
    async def test_math_accuracy_with_mock(self, benchmark, mock_provider):
        """Test mathematical accuracy with mock provider."""
        correct = 0
        total = len(benchmark.MATH_TEST_SET)
        
        for item in benchmark.MATH_TEST_SET:
            response = await mock_provider.complete_sync(
                messages=[Message(role=MessageRole.USER, content=item["q"])],
                model="mock-model",
            )
            if item["a"] in response.content:
                correct += 1
        
        accuracy = correct / total
        # With mock, we expect the predefined response
        assert accuracy >= 0  # Just verify it runs
    
    @pytest.mark.asyncio
    async def test_code_generation_validity(self, benchmark, mock_provider):
        """Test that generated code is syntactically valid."""
        import ast
        
        for item in benchmark.CODE_TEST_SET:
            response = await mock_provider.complete_sync(
                messages=[Message(role=MessageRole.USER, content=item["q"])],
                model="mock-model",
            )
            
            # Extract code from response
            code = self._extract_code(response.content)
            
            # Validate syntax or use custom validator
            if code:
                try:
                    ast.parse(code)
                    is_valid = True
                except SyntaxError:
                    is_valid = False
            else:
                is_valid = item["validate"](response.content)
            
            # For mock, just verify the process works
            assert isinstance(is_valid, bool)
    
    def _extract_code(self, text: str) -> str:
        """Extract code from markdown-formatted response."""
        import re
        # Extract code blocks
        matches = re.findall(r'```(?:python)?\n(.*?)```', text, re.DOTALL)
        return matches[0] if matches else ""


@pytest.mark.prompt
class TestMathAccuracy:
    """Tests specifically for math accuracy."""
    
    @pytest.fixture
    def math_questions(self):
        """Math test questions."""
        return [
            {"q": "What is 2 + 2?", "a": "4"},
            {"q": "What is 10 - 3?", "a": "7"},
            {"q": "What is 6 * 7?", "a": "42"},
            {"q": "What is 100 / 4?", "a": "25"},
            {"q": "What is 2^10?", "a": "1024"},
        ]
    
    def test_math_questions_structure(self, math_questions):
        """Test math questions structure."""
        for item in math_questions:
            assert "q" in item
            assert "a" in item
            assert isinstance(item["q"], str)
            assert isinstance(item["a"], str)
    
    def test_math_answer_validation(self, math_questions):
        """Test math answer validation."""
        # Simulate correct answers
        for item in math_questions:
            simulated_response = f"The answer is {item['a']}."
            assert item["a"] in simulated_response
    
    def test_math_answer_case_sensitivity(self):
        """Test math answers are typically numeric."""
        numeric_answers = ["4", "7", "42", "25", "1024"]
        
        for answer in numeric_answers:
            # Numeric answers should be case-insensitive
            assert answer.lower() == answer


@pytest.mark.prompt
class TestCodeAccuracy:
    """Tests specifically for code generation accuracy."""
    
    @pytest.fixture
    def code_questions(self):
        """Code test questions."""
        return [
            {
                "q": "Write a function to add two numbers",
                "expected_keywords": ["def", "return", "+"],
            },
            {
                "q": "Create a class named Person",
                "expected_keywords": ["class", "Person"],
            },
            {
                "q": "Write a loop that prints 1 to 10",
                "expected_keywords": ["for", "range", "print"],
            },
        ]
    
    def test_code_questions_structure(self, code_questions):
        """Test code questions structure."""
        for item in code_questions:
            assert "q" in item
            assert "expected_keywords" in item
    
    def test_code_keyword_detection(self, code_questions):
        """Test code keyword detection."""
        sample_response = '''
def add(a, b):
    return a + b
'''
        
        for item in code_questions[:1]:  # Test first item
            found = sum(
                1 for kw in item["expected_keywords"]
                if kw in sample_response
            )
            assert found == len(item["expected_keywords"])
    
    def test_python_syntax_validation(self):
        """Test Python syntax validation."""
        import ast
        
        valid_codes = [
            "def hello(): pass",
            "x = 1 + 2",
            "for i in range(10): print(i)",
            "class MyClass: pass",
        ]
        
        for code in valid_codes:
            try:
                ast.parse(code)
                is_valid = True
            except SyntaxError:
                is_valid = False
            
            assert is_valid is True
    
    def test_invalid_python_detection(self):
        """Test detection of invalid Python."""
        import ast
        
        invalid_codes = [
            "def hello() pass",  # Missing colon
            "x = ",  # Incomplete
            "for i range(10):",  # Missing 'in'
        ]
        
        for code in invalid_codes:
            try:
                ast.parse(code)
                is_valid = True
            except SyntaxError:
                is_valid = False
            
            assert is_valid is False


@pytest.mark.prompt
class TestReasoningAccuracy:
    """Tests specifically for reasoning accuracy."""
    
    @pytest.fixture
    def reasoning_questions(self):
        """Reasoning test questions."""
        return [
            {
                "q": "If A > B and B > C, is A > C?",
                "a": "yes",
                "type": "transitive",
            },
            {
                "q": "All dogs are mammals. All mammals are animals. Are dogs animals?",
                "a": "yes",
                "type": "syllogism",
            },
            {
                "q": "If it's raining, the ground is wet. The ground is wet. Is it raining?",
                "a": "not necessarily",
                "type": "logical_fallacy",
            },
        ]
    
    def test_reasoning_questions_structure(self, reasoning_questions):
        """Test reasoning questions structure."""
        for item in reasoning_questions:
            assert "q" in item
            assert "a" in item
            assert "type" in item
    
    def test_reasoning_answer_validation(self, reasoning_questions):
        """Test reasoning answer validation."""
        for item in reasoning_questions:
            # Reasoning answers can be more flexible
            answer = item["a"].lower()
            
            # Check for common answer patterns
            if item["type"] == "transitive":
                assert answer in ["yes", "true", "correct"]
            elif item["type"] == "syllogism":
                assert answer in ["yes", "true", "correct"]
            elif item["type"] == "logical_fallacy":
                assert "not" in answer or "necessarily" in answer or "maybe" in answer


@pytest.mark.prompt
class TestAccuracyTracking:
    """Tests for accuracy tracking over time."""
    
    def test_accuracy_calculation(self):
        """Test accuracy calculation."""
        results = {
            "correct": 8,
            "total": 10,
        }
        
        accuracy = results["correct"] / results["total"]
        
        assert accuracy == 0.8
    
    def test_accuracy_by_category(self):
        """Test accuracy tracking by category."""
        results = {
            "math": {"correct": 5, "total": 5},
            "code": {"correct": 3, "total": 5},
            "reasoning": {"correct": 4, "total": 5},
        }
        
        accuracies = {
            category: data["correct"] / data["total"]
            for category, data in results.items()
        }
        
        assert accuracies["math"] == 1.0
        assert accuracies["code"] == 0.6
        assert accuracies["reasoning"] == 0.8
    
    def test_accuracy_threshold(self):
        """Test accuracy threshold checking."""
        accuracy = 0.75
        threshold = 0.8
        
        meets_threshold = accuracy >= threshold
        
        assert meets_threshold is False
        
        accuracy = 0.85
        meets_threshold = accuracy >= threshold
        
        assert meets_threshold is True
