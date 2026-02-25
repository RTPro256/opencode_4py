"""
Centralized test data management.

Provides test data fixtures, sample data generators, and data
management utilities for consistent testing across the test suite.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


@dataclass
class SamplePrompt:
    """A sample prompt for testing."""
    
    id: str
    content: str
    category: str
    expected_keywords: list[str] = field(default_factory=list)
    difficulty: str = "medium"  # easy, medium, hard
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SampleCode:
    """Sample code for testing."""
    
    id: str
    language: str
    code: str
    description: str
    task_type: str  # generation, completion, refactoring, debugging
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SampleConversation:
    """A sample conversation for testing."""
    
    id: str
    messages: list[dict[str, str]]
    expected_response_keywords: list[str] = field(default_factory=list)
    category: str = "general"
    metadata: dict[str, Any] = field(default_factory=dict)


class TestDataRegistry:
    """
    Registry for test data management.
    
    Provides centralized access to test data with support for:
    - Sample prompts for various categories
    - Sample code snippets
    - Sample conversations
    - Custom test data loading
    """
    
    def __init__(self, data_path: Optional[Path] = None):
        """
        Initialize the test data registry.
        
        Args:
            data_path: Optional path to custom test data directory
        """
        self._data_path = data_path
        self._prompts: dict[str, SamplePrompt] = {}
        self._code_samples: dict[str, SampleCode] = {}
        self._conversations: dict[str, SampleConversation] = {}
        
        # Initialize with default test data
        self._initialize_default_data()
    
    def _initialize_default_data(self) -> None:
        """Initialize with default test data."""
        # Simple Q&A prompts
        self._prompts.update({
            "simple_math": SamplePrompt(
                id="simple_math",
                content="What is 2 + 2?",
                category="math",
                expected_keywords=["4", "four"],
                difficulty="easy",
            ),
            "capital_france": SamplePrompt(
                id="capital_france",
                content="What is the capital of France?",
                category="geography",
                expected_keywords=["Paris", "paris"],
                difficulty="easy",
            ),
            "sky_color": SamplePrompt(
                id="sky_color",
                content="What color is the sky on a clear day?",
                category="general",
                expected_keywords=["blue", "Blue"],
                difficulty="easy",
            ),
            "reasoning_syllogism": SamplePrompt(
                id="reasoning_syllogism",
                content="If all cats are animals, and Fluffy is a cat, is Fluffy an animal?",
                category="reasoning",
                expected_keywords=["yes", "Yes", "animal"],
                difficulty="medium",
            ),
            "code_explain": SamplePrompt(
                id="code_explain",
                content="Explain what this code does: print('Hello, World!')",
                category="code",
                expected_keywords=["print", "output", "Hello", "display"],
                difficulty="easy",
            ),
        })
        
        # Code samples
        self._code_samples.update({
            "python_add_function": SampleCode(
                id="python_add_function",
                language="python",
                code="def add(a, b):\n    return a + b",
                description="A simple function to add two numbers",
                task_type="generation",
            ),
            "python_is_even": SampleCode(
                id="python_is_even",
                language="python",
                code="def is_even(n):\n    return n % 2 == 0",
                description="A function to check if a number is even",
                task_type="generation",
            ),
            "python_factorial": SampleCode(
                id="python_factorial",
                language="python",
                code="def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)",
                description="Recursive factorial function",
                task_type="generation",
            ),
            "javascript_hello": SampleCode(
                id="javascript_hello",
                language="javascript",
                code="function hello(name) {\n    return `Hello, ${name}!`;\n}",
                description="JavaScript greeting function",
                task_type="generation",
            ),
        })
        
        # Conversations
        self._conversations.update({
            "simple_greeting": SampleConversation(
                id="simple_greeting",
                messages=[
                    {"role": "user", "content": "Hello!"},
                ],
                expected_response_keywords=["hello", "hi", "help"],
                category="greeting",
            ),
            "code_request": SampleConversation(
                id="code_request",
                messages=[
                    {"role": "user", "content": "Write a Python function to add two numbers."},
                ],
                expected_response_keywords=["def", "return", "+"],
                category="code",
            ),
            "multi_turn": SampleConversation(
                id="multi_turn",
                messages=[
                    {"role": "user", "content": "What is Python?"},
                    {"role": "assistant", "content": "Python is a programming language."},
                    {"role": "user", "content": "What are its main features?"},
                ],
                expected_response_keywords=["feature", "dynamic", "interpreted"],
                category="general",
            ),
        })
    
    def get_prompt(self, prompt_id: str) -> Optional[SamplePrompt]:
        """
        Get a prompt by ID.
        
        Args:
            prompt_id: The prompt identifier
            
        Returns:
            SamplePrompt or None if not found
        """
        return self._prompts.get(prompt_id)
    
    def get_prompts_by_category(self, category: str) -> list[SamplePrompt]:
        """
        Get all prompts in a category.
        
        Args:
            category: The category to filter by
            
        Returns:
            List of prompts in the category
        """
        return [p for p in self._prompts.values() if p.category == category]
    
    def get_prompts_by_difficulty(self, difficulty: str) -> list[SamplePrompt]:
        """
        Get all prompts with a specific difficulty.
        
        Args:
            difficulty: The difficulty level (easy, medium, hard)
            
        Returns:
            List of prompts with the difficulty
        """
        return [p for p in self._prompts.values() if p.difficulty == difficulty]
    
    def get_code_sample(self, sample_id: str) -> Optional[SampleCode]:
        """
        Get a code sample by ID.
        
        Args:
            sample_id: The code sample identifier
            
        Returns:
            SampleCode or None if not found
        """
        return self._code_samples.get(sample_id)
    
    def get_code_samples_by_language(self, language: str) -> list[SampleCode]:
        """
        Get all code samples in a language.
        
        Args:
            language: The programming language
            
        Returns:
            List of code samples in the language
        """
        return [c for c in self._code_samples.values() if c.language == language]
    
    def get_code_samples_by_task(self, task_type: str) -> list[SampleCode]:
        """
        Get all code samples for a task type.
        
        Args:
            task_type: The task type (generation, completion, etc.)
            
        Returns:
            List of code samples for the task type
        """
        return [c for c in self._code_samples.values() if c.task_type == task_type]
    
    def get_conversation(self, conv_id: str) -> Optional[SampleConversation]:
        """
        Get a conversation by ID.
        
        Args:
            conv_id: The conversation identifier
            
        Returns:
            SampleConversation or None if not found
        """
        return self._conversations.get(conv_id)
    
    def get_conversations_by_category(self, category: str) -> list[SampleConversation]:
        """
        Get all conversations in a category.
        
        Args:
            category: The category to filter by
            
        Returns:
            List of conversations in the category
        """
        return [c for c in self._conversations.values() if c.category == category]
    
    def add_prompt(self, prompt: SamplePrompt) -> None:
        """Add a custom prompt."""
        self._prompts[prompt.id] = prompt
    
    def add_code_sample(self, code: SampleCode) -> None:
        """Add a custom code sample."""
        self._code_samples[code.id] = code
    
    def add_conversation(self, conversation: SampleConversation) -> None:
        """Add a custom conversation."""
        self._conversations[conversation.id] = conversation
    
    def load_from_json(self, path: Path) -> None:
        """
        Load test data from a JSON file.
        
        Args:
            path: Path to the JSON file
        """
        if not path.exists():
            return
        
        data = json.loads(path.read_text())
        
        for prompt_data in data.get("prompts", []):
            prompt = SamplePrompt(
                id=prompt_data["id"],
                content=prompt_data["content"],
                category=prompt_data["category"],
                expected_keywords=prompt_data.get("expected_keywords", []),
                difficulty=prompt_data.get("difficulty", "medium"),
                metadata=prompt_data.get("metadata", {}),
            )
            self._prompts[prompt.id] = prompt
        
        for code_data in data.get("code_samples", []):
            code = SampleCode(
                id=code_data["id"],
                language=code_data["language"],
                code=code_data["code"],
                description=code_data["description"],
                task_type=code_data["task_type"],
                metadata=code_data.get("metadata", {}),
            )
            self._code_samples[code.id] = code
        
        for conv_data in data.get("conversations", []):
            conv = SampleConversation(
                id=conv_data["id"],
                messages=conv_data["messages"],
                expected_response_keywords=conv_data.get("expected_response_keywords", []),
                category=conv_data.get("category", "general"),
                metadata=conv_data.get("metadata", {}),
            )
            self._conversations[conv.id] = conv
    
    def save_to_json(self, path: Path) -> None:
        """
        Save test data to a JSON file.
        
        Args:
            path: Path to save the JSON file
        """
        data = {
            "prompts": [
                {
                    "id": p.id,
                    "content": p.content,
                    "category": p.category,
                    "expected_keywords": p.expected_keywords,
                    "difficulty": p.difficulty,
                    "metadata": p.metadata,
                }
                for p in self._prompts.values()
            ],
            "code_samples": [
                {
                    "id": c.id,
                    "language": c.language,
                    "code": c.code,
                    "description": c.description,
                    "task_type": c.task_type,
                    "metadata": c.metadata,
                }
                for c in self._code_samples.values()
            ],
            "conversations": [
                {
                    "id": c.id,
                    "messages": c.messages,
                    "expected_response_keywords": c.expected_response_keywords,
                    "category": c.category,
                    "metadata": c.metadata,
                }
                for c in self._conversations.values()
            ],
        }
        
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2))
    
    def get_all_categories(self) -> list[str]:
        """Get all unique categories across all data types."""
        categories = set()
        categories.update(p.category for p in self._prompts.values())
        categories.update(c.category for c in self._conversations.values())
        return list(categories)
    
    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about the test data."""
        return {
            "total_prompts": len(self._prompts),
            "total_code_samples": len(self._code_samples),
            "total_conversations": len(self._conversations),
            "categories": self.get_all_categories(),
            "languages": list(set(c.language for c in self._code_samples.values())),
            "difficulties": list(set(p.difficulty for p in self._prompts.values())),
        }


# Global registry instance
_registry: Optional[TestDataRegistry] = None


def get_test_data_registry() -> TestDataRegistry:
    """
    Get the global test data registry.
    
    Returns:
        TestDataRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = TestDataRegistry()
    return _registry


def get_prompt(prompt_id: str) -> Optional[SamplePrompt]:
    """Convenience function to get a prompt from the global registry."""
    return get_test_data_registry().get_prompt(prompt_id)


def get_code_sample(sample_id: str) -> Optional[SampleCode]:
    """Convenience function to get a code sample from the global registry."""
    return get_test_data_registry().get_code_sample(sample_id)


def get_conversation(conv_id: str) -> Optional[SampleConversation]:
    """Convenience function to get a conversation from the global registry."""
    return get_test_data_registry().get_conversation(conv_id)
