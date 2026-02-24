"""
Skill Classifier

Classifies prompts into categories and assesses complexity for routing decisions.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

from opencode.router.config import PromptCategory, Complexity

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """Result of prompt classification."""
    category: PromptCategory
    complexity: Complexity
    confidence: float
    indicators: List[str]
    suggested_skills: List[str]


class SkillClassifier:
    """
    Classifies prompts into categories and assesses complexity.
    
    Uses pattern matching and heuristics to determine the type
    and difficulty of a prompt for intelligent routing.
    """
    
    # Patterns for category detection
    CODING_PATTERNS = [
        r'\b(function|class|method|variable|loop|array|object)\b',
        r'\b(def |class |import |from |return |if |else |for |while )\b',
        r'\b(implement|write code|debug|fix bug|refactor)\b',
        r'\b(python|javascript|typescript|java|c\+\+|rust|go)\b',
        r'```[\s\S]*?```',  # Code blocks
        r'\b(api|endpoint|database|query|algorithm)\b',
    ]
    
    REASONING_PATTERNS = [
        r'\b(analyze|reason|explain why|compare|contrast)\b',
        r'\b(logic|argument|premise|conclusion|inference)\b',
        r'\b(cause|effect|relationship|correlation)\b',
        r'\b(pros and cons|advantages|disadvantages)\b',
        r'\b(step by step|systematic|methodical)\b',
    ]
    
    CREATIVE_PATTERNS = [
        r'\b(write|compose|create|generate|imagine)\b',
        r'\b(story|poem|song|script|novel|tale)\b',
        r'\b(creative|imaginative|original|unique)\b',
        r'\b(character|plot|setting|dialogue)\b',
    ]
    
    MATH_PATTERNS = [
        r'\b(calculate|compute|solve|equation|formula)\b',
        r'\b(integral|derivative|matrix|vector|polynomial)\b',
        r'\b(sqrt|sin|cos|tan|log|exp)\b',
        r'\b(proof|theorem|lemma|axiom)\b',
        r'[\d\+\-\*\/\=\^\(\)]+',  # Mathematical expressions
    ]
    
    ANALYSIS_PATTERNS = [
        r'\b(analyze|examine|investigate|study|assess)\b',
        r'\b(data|statistics|metrics|trends|patterns)\b',
        r'\b(report|summary|insight|finding)\b',
        r'\b(performance|benchmark|comparison)\b',
    ]
    
    TRANSLATION_PATTERNS = [
        r'\b(translate|translation|language)\b',
        r'\b(from .* to|into)\b',
        r'\b(english|spanish|french|german|chinese|japanese)\b',
    ]
    
    SUMMARIZATION_PATTERNS = [
        r'\b(summarize|summary|brief|overview|abstract)\b',
        r'\b(key points|main ideas|highlights)\b',
        r'\b(tl;?dr|in short|in brief)\b',
    ]
    
    # Complexity indicators
    SIMPLE_INDICATORS = [
        r'^.{1,50}$',  # Very short prompts
        r'\b(what is|who is|when|where)\b',
        r'\b(define|list|name|give me)\b',
    ]
    
    HARD_INDICATORS = [
        r'\b(complex|complicated|difficult|advanced)\b',
        r'\b(multi[- ]step|comprehensive|detailed)\b',
        r'\b(architecture|design|system|integration)\b',
        r'\b(optimize|performance|scalability)\b',
        r'\b(1000|2000|3000)\+?\s*(words|lines|characters)\b',
    ]
    
    def __init__(self):
        """Initialize the skill classifier."""
        self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for efficiency."""
        self._compiled = {
            'coding': [re.compile(p, re.IGNORECASE) for p in self.CODING_PATTERNS],
            'reasoning': [re.compile(p, re.IGNORECASE) for p in self.REASONING_PATTERNS],
            'creative': [re.compile(p, re.IGNORECASE) for p in self.CREATIVE_PATTERNS],
            'math': [re.compile(p, re.IGNORECASE) for p in self.MATH_PATTERNS],
            'analysis': [re.compile(p, re.IGNORECASE) for p in self.ANALYSIS_PATTERNS],
            'translation': [re.compile(p, re.IGNORECASE) for p in self.TRANSLATION_PATTERNS],
            'summarization': [re.compile(p, re.IGNORECASE) for p in self.SUMMARIZATION_PATTERNS],
            'simple': [re.compile(p, re.IGNORECASE) for p in self.SIMPLE_INDICATORS],
            'hard': [re.compile(p, re.IGNORECASE) for p in self.HARD_INDICATORS],
        }
    
    def classify(self, prompt: str) -> ClassificationResult:
        """
        Classify a prompt into a category and complexity level.
        
        Args:
            prompt: The prompt to classify
            
        Returns:
            ClassificationResult with category, complexity, and confidence
        """
        # Count matches for each category
        category_scores: Dict[str, Tuple[float, List[str]]] = {}
        
        for category in ['coding', 'reasoning', 'creative', 'math', 'analysis', 'translation', 'summarization']:
            score, indicators = self._score_category(prompt, category)
            category_scores[category] = (score, indicators)
        
        # Find best category
        best_category = max(category_scores.items(), key=lambda x: x[1][0])
        category_name = best_category[0]
        category_score = best_category[1][0]
        indicators = best_category[1][1]
        
        # Determine category enum
        category_map = {
            'coding': PromptCategory.CODING,
            'reasoning': PromptCategory.REASONING,
            'creative': PromptCategory.CREATIVE,
            'math': PromptCategory.MATH,
            'analysis': PromptCategory.ANALYSIS,
            'translation': PromptCategory.TRANSLATION,
            'summarization': PromptCategory.SUMMARIZATION,
        }
        
        # Default to general if no strong match
        if category_score < 0.3:
            category = PromptCategory.GENERAL
            confidence = 0.5
        else:
            category = category_map.get(category_name, PromptCategory.GENERAL)
            confidence = min(category_score, 1.0)
        
        # Assess complexity
        complexity = self._assess_complexity(prompt)
        
        # Suggest skills based on category
        suggested_skills = self._suggest_skills(category, complexity)
        
        return ClassificationResult(
            category=category,
            complexity=complexity,
            confidence=confidence,
            indicators=indicators,
            suggested_skills=suggested_skills,
        )
    
    def _score_category(self, prompt: str, category: str) -> Tuple[float, List[str]]:
        """
        Score a prompt against a category.
        
        Returns:
            Tuple of (score, list of matched indicators)
        """
        patterns = self._compiled.get(category, [])
        matches = 0
        indicators = []
        
        for pattern in patterns:
            if pattern.search(prompt):
                matches += 1
                # Extract matched text as indicator
                match = pattern.search(prompt)
                if match:
                    indicators.append(match.group())
        
        # Normalize score
        score = matches / len(patterns) if patterns else 0
        
        # Boost score for multiple matches
        if matches > 2:
            score = min(score * 1.5, 1.0)
        
        return score, indicators
    
    def _assess_complexity(self, prompt: str) -> Complexity:
        """
        Assess the complexity of a prompt.
        
        Args:
            prompt: The prompt to assess
            
        Returns:
            Complexity level
        """
        # Check for simple indicators
        simple_patterns = self._compiled.get('simple', [])
        simple_matches = sum(1 for p in simple_patterns if p.search(prompt))
        
        # Check for hard indicators
        hard_patterns = self._compiled.get('hard', [])
        hard_matches = sum(1 for p in hard_patterns if p.search(prompt))
        
        # Length-based assessment
        length = len(prompt)
        
        # Determine complexity
        if simple_matches >= 2 or length < 50:
            return Complexity.SIMPLE
        elif hard_matches >= 2 or length > 500:
            return Complexity.HARD
        elif hard_matches >= 1 or length > 200:
            return Complexity.MEDIUM
        else:
            return Complexity.SIMPLE
    
    def _suggest_skills(self, category: PromptCategory, complexity: Complexity) -> List[str]:
        """
        Suggest skills based on category and complexity.
        
        Args:
            category: The prompt category
            complexity: The complexity level
            
        Returns:
            List of suggested skill names
        """
        skills = []
        
        # Category-based skills
        if category == PromptCategory.CODING:
            skills.append("code_generation")
            if complexity == Complexity.HARD:
                skills.extend(["code_review", "architecture_design"])
        elif category == PromptCategory.REASONING:
            skills.append("logical_reasoning")
            if complexity == Complexity.HARD:
                skills.append("chain_of_thought")
        elif category == PromptCategory.CREATIVE:
            skills.append("creative_writing")
        elif category == PromptCategory.MATH:
            skills.append("mathematical_reasoning")
        elif category == PromptCategory.ANALYSIS:
            skills.append("data_analysis")
        elif category == PromptCategory.TRANSLATION:
            skills.append("translation")
        elif category == PromptCategory.SUMMARIZATION:
            skills.append("summarization")
        
        return skills
    
    def get_category_description(self, category: PromptCategory) -> str:
        """Get a human-readable description of a category."""
        descriptions = {
            PromptCategory.CODING: "Programming and code-related tasks",
            PromptCategory.REASONING: "Logical reasoning and analysis",
            PromptCategory.CREATIVE: "Creative writing and content generation",
            PromptCategory.GENERAL: "General-purpose tasks",
            PromptCategory.MATH: "Mathematical calculations and proofs",
            PromptCategory.ANALYSIS: "Data analysis and investigation",
            PromptCategory.TRANSLATION: "Language translation",
            PromptCategory.SUMMARIZATION: "Text summarization and condensation",
        }
        return descriptions.get(category, "Unknown category")
