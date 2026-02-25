"""
Tests for prompt comparison across different AI models.

These tests evaluate how different models respond to the same prompts,
helping identify model-specific behaviors and prompt engineering needs.
"""

import pytest
from typing import Dict, List, Any
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock
import asyncio

from opencode.provider.base import Message, MessageRole


@dataclass
class PromptComparisonResult:
    """Result of comparing a prompt across models."""
    prompt: str
    model_responses: Dict[str, str]
    similarity_scores: Dict[str, float]
    accuracy_scores: Dict[str, float]
    latency_ms: Dict[str, float]
    errors: Dict[str, str]


@pytest.mark.prompt
class TestPromptComparison:
    """Compare prompts across different AI models."""
    
    @pytest.fixture
    def comparison_prompts(self) -> List[Dict[str, Any]]:
        """Prompts to use for comparison testing."""
        return [
            {
                "id": "math_simple",
                "prompt": "What is 15 * 17? Show your work.",
                "expected_contains": ["255", "15", "17"],
            },
            {
                "id": "code_generation",
                "prompt": "Write a Python function that checks if a string is a palindrome.",
                "expected_contains": ["def", "return", "palindrome"],
            },
            {
                "id": "reasoning",
                "prompt": "If it takes 5 machines 5 minutes to make 5 widgets, how long would it take 100 machines to make 100 widgets?",
                "expected_contains": ["5 minutes", "5"],
            },
            {
                "id": "explanation",
                "prompt": "Explain the difference between a list and a tuple in Python.",
                "expected_contains": ["mutable", "immutable", "list", "tuple"],
            },
        ]
    
    @pytest.fixture
    def mock_providers(self):
        """Create mock providers for testing."""
        from opencode.provider.base import Provider, ModelInfo
        
        providers = {}
        
        # Mock Ollama provider
        ollama = MagicMock(spec=Provider)
        ollama.name = "ollama"
        ollama.models = [ModelInfo(id="llama3.2:3b", name="Llama 3.2", provider="ollama", context_length=4096)]
        ollama.complete_sync = AsyncMock(return_value=MagicMock(content="Mock response from Ollama"))
        providers["ollama"] = ollama
        
        return providers
    
    def test_comparison_result_creation(self):
        """Test creating a comparison result."""
        result = PromptComparisonResult(
            prompt="Test prompt",
            model_responses={"ollama": "Response 1", "openai": "Response 2"},
            similarity_scores={"ollama": 0.8, "openai": 0.9},
            accuracy_scores={"ollama": 1.0, "openai": 1.0},
            latency_ms={"ollama": 100.0, "openai": 200.0},
            errors={},
        )
        
        assert result.prompt == "Test prompt"
        assert len(result.model_responses) == 2
    
    def test_expected_contains_validation(self, comparison_prompts):
        """Test validation of expected content in responses."""
        for prompt_data in comparison_prompts:
            # Simulate a response
            response = "255 is the answer. 15 times 17 equals 255."
            
            # Check if expected content is present
            found = sum(
                1 for exp in prompt_data["expected_contains"]
                if exp.lower() in response.lower()
            )
            
            if prompt_data["id"] == "math_simple":
                assert found >= 1  # At least one expected term found
    
    @pytest.mark.asyncio
    async def test_compare_simple_prompt_mock(self, mock_providers, comparison_prompts):
        """Test comparing simple prompts with mock providers."""
        results = []
        
        for prompt_data in comparison_prompts[:1]:  # Test first prompt only
            responses = {}
            
            for name, provider in mock_providers.items():
                try:
                    response = await provider.complete_sync(
                        messages=[Message(role=MessageRole.USER, content=prompt_data["prompt"])],
                        model=provider.models[0].id,
                    )
                    responses[name] = response.content
                except Exception as e:
                    responses[name] = f"Error: {str(e)}"
            
            results.append({
                "prompt_id": prompt_data["id"],
                "responses": responses,
            })
        
        assert len(results) == 1
        assert "ollama" in results[0]["responses"]
    
    @pytest.mark.asyncio
    async def test_compare_code_prompts_mock(self, mock_providers):
        """Test comparing code generation prompts."""
        prompt = "Write a Python function to sort a list of dictionaries by a specific key."
        
        responses = {}
        for name, provider in mock_providers.items():
            response = await provider.complete_sync(
                messages=[Message(role=MessageRole.USER, content=prompt)],
                model=provider.models[0].id,
            )
            responses[name] = response.content
        
        # All providers should return something
        for name, response in responses.items():
            assert response is not None


@pytest.mark.prompt
class TestPromptAccuracyMetrics:
    """Tests for prompt accuracy metrics."""
    
    def test_calculate_accuracy_score(self):
        """Test calculating accuracy score."""
        response = "The answer is 255. 15 multiplied by 17 equals 255."
        expected = ["255", "15", "17"]
        
        found = sum(1 for exp in expected if exp.lower() in response.lower())
        score = found / len(expected)
        
        assert score == 1.0
    
    def test_partial_accuracy_score(self):
        """Test partial accuracy score."""
        response = "The answer is 255."
        expected = ["255", "15", "17"]
        
        found = sum(1 for exp in expected if exp.lower() in response.lower())
        score = found / len(expected)
        
        assert score == 1/3
    
    def test_zero_accuracy_score(self):
        """Test zero accuracy score."""
        response = "I don't know the answer."
        expected = ["255", "15", "17"]
        
        found = sum(1 for exp in expected if exp.lower() in response.lower())
        score = found / len(expected)
        
        assert score == 0.0
    
    def test_case_insensitive_matching(self):
        """Test case-insensitive matching."""
        response = "The answer is TWO HUNDRED FIFTY-FIVE."
        expected = ["255", "two hundred fifty-five"]
        
        found = sum(1 for exp in expected if exp.lower() in response.lower())
        
        assert found >= 1


@pytest.mark.prompt
class TestPromptSimilarityMetrics:
    """Tests for prompt similarity metrics."""
    
    def test_response_similarity(self):
        """Test response similarity calculation."""
        response1 = "Python is a programming language."
        response2 = "Python is a popular programming language."
        
        # Simple word overlap similarity
        words1 = set(response1.lower().split())
        words2 = set(response2.lower().split())
        
        overlap = len(words1 & words2)
        union = len(words1 | words2)
        
        similarity = overlap / union if union > 0 else 0
        
        assert similarity > 0.5
    
    def test_identical_responses(self):
        """Test identical responses have perfect similarity."""
        response = "This is a test response."
        
        words = set(response.lower().split())
        overlap = len(words & words)
        union = len(words | words)
        
        similarity = overlap / union
        
        assert similarity == 1.0


@pytest.mark.prompt
class TestPromptCategories:
    """Tests for different prompt categories."""
    
    def test_math_prompt_category(self):
        """Test math prompt category."""
        math_prompts = [
            "What is 2 + 2?",
            "Calculate 15 * 17",
            "What is the square root of 144?",
        ]
        
        for prompt in math_prompts:
            # Math prompts should contain numbers or math operations
            has_math = any(c.isdigit() for c in prompt) or any(
                op in prompt for op in ["+", "-", "*", "/", "calculate", "square"]
            )
            assert has_math
    
    def test_code_prompt_category(self):
        """Test code prompt category."""
        code_prompts = [
            "Write a Python function to sort a list",
            "Create a class for a bank account",
            "Implement a binary search algorithm",
        ]
        
        code_keywords = ["function", "class", "implement", "write", "create", "code", "algorithm"]
        
        for prompt in code_prompts:
            has_code = any(kw in prompt.lower() for kw in code_keywords)
            assert has_code
    
    def test_reasoning_prompt_category(self):
        """Test reasoning prompt category."""
        reasoning_prompts = [
            "If all roses are flowers, and some flowers are red...",
            "Explain why the sky is blue",
            "What would happen if gravity stopped working?",
        ]
        
        reasoning_keywords = ["if", "why", "explain", "because", "would happen", "reasoning"]
        
        for prompt in reasoning_prompts:
            has_reasoning = any(kw in prompt.lower() for kw in reasoning_keywords)
            assert has_reasoning


@pytest.mark.prompt
class TestPromptBenchmarkSets:
    """Tests for standardized benchmark sets."""
    
    @pytest.fixture
    def math_benchmark(self) -> List[Dict[str, Any]]:
        """Math benchmark test set."""
        return [
            {"q": "What is 7 * 8?", "a": "56"},
            {"q": "What is 144 / 12?", "a": "12"},
            {"q": "What is 15% of 200?", "a": "30"},
        ]
    
    @pytest.fixture
    def code_benchmark(self) -> List[Dict[str, Any]]:
        """Code benchmark test set."""
        return [
            {
                "q": "Write a Python one-liner to reverse a string.",
                "validate": lambda r: "[::-1]" in r or "reversed" in r,
            },
            {
                "q": "Write a Python list comprehension to square numbers 1-10.",
                "validate": lambda r: "[" in r and "**2" in r and "for" in r,
            },
        ]
    
    def test_math_benchmark_structure(self, math_benchmark):
        """Test math benchmark structure."""
        for item in math_benchmark:
            assert "q" in item
            assert "a" in item
            assert isinstance(item["q"], str)
            assert isinstance(item["a"], str)
    
    def test_code_benchmark_structure(self, code_benchmark):
        """Test code benchmark structure."""
        for item in code_benchmark:
            assert "q" in item
            assert "validate" in item
            assert callable(item["validate"])
    
    def test_code_validator_function(self, code_benchmark):
        """Test code validator functions."""
        # Test the first validator
        valid_response = "Use s[::-1] to reverse a string"
        invalid_response = "Use a loop to reverse"
        
        assert code_benchmark[0]["validate"](valid_response) is True
        assert code_benchmark[0]["validate"](invalid_response) is False


@pytest.mark.prompt
class TestPromptResponseValidation:
    """Tests for prompt response validation."""
    
    def test_code_syntax_validation(self):
        """Test code syntax validation."""
        import ast
        
        valid_code = "def hello():\n    return 'Hello'"
        invalid_code = "def hello()\n    return 'Hello'"
        
        try:
            ast.parse(valid_code)
            is_valid = True
        except SyntaxError:
            is_valid = False
        
        assert is_valid is True
        
        try:
            ast.parse(invalid_code)
            is_valid = True
        except SyntaxError:
            is_valid = False
        
        assert is_valid is False
    
    def test_extract_code_from_markdown(self):
        """Test extracting code from markdown."""
        import re
        
        response = '''Here's the code:

```python
def hello():
    print("Hello, world!")
```

Hope that helps!'''
        
        matches = re.findall(r'```(?:python)?\n(.*?)```', response, re.DOTALL)
        
        assert len(matches) == 1
        assert "def hello" in matches[0]
    
    def test_json_response_validation(self):
        """Test JSON response validation."""
        import json
        
        valid_json = '{"name": "test", "value": 123}'
        invalid_json = '{"name": "test", value: 123}'
        
        try:
            json.loads(valid_json)
            is_valid = True
        except json.JSONDecodeError:
            is_valid = False
        
        assert is_valid is True
        
        try:
            json.loads(invalid_json)
            is_valid = True
        except json.JSONDecodeError:
            is_valid = False
        
        assert is_valid is False
