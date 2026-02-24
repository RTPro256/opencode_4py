"""
Orchestration Router and Intent Classifier

Routes requests to appropriate agents based on intent classification.
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from opencode.core.orchestration.agent import Agent, AgentCapability
from opencode.core.orchestration.registry import AgentRegistry

logger = logging.getLogger(__name__)


class IntentCategory(Enum):
    """Categories of user intents."""
    CODE_GENERATION = "code_generation"
    CODE_MODIFICATION = "code_modification"
    CODE_REVIEW = "code_review"
    DEBUGGING = "debugging"
    REFACTORING = "refactoring"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    ARCHITECTURE = "architecture"
    PLANNING = "planning"
    RESEARCH = "research"
    QUESTION = "question"
    EXPLANATION = "explanation"
    FILE_OPERATION = "file_operation"
    SHELL_COMMAND = "shell_command"
    WEB_SEARCH = "web_search"
    GENERAL = "general"


@dataclass
class Intent:
    """Classified intent from user input."""
    category: IntentCategory
    confidence: float
    keywords: List[str] = field(default_factory=list)
    entities: Dict[str, Any] = field(default_factory=dict)
    sub_intents: List["Intent"] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "category": self.category.value,
            "confidence": self.confidence,
            "keywords": self.keywords,
            "entities": self.entities,
            "sub_intents": [i.to_dict() for i in self.sub_intents],
        }


@dataclass
class RoutingResult:
    """Result of routing decision."""
    agent_id: str
    intent: Intent
    confidence: float
    alternative_agents: List[str] = field(default_factory=list)
    routing_reason: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "intent": self.intent.to_dict(),
            "confidence": self.confidence,
            "alternative_agents": self.alternative_agents,
            "routing_reason": self.routing_reason,
        }


class IntentClassifier:
    """
    Classifies user intents from natural language input.
    
    Uses keyword matching and pattern recognition to determine
    the user's intent.
    
    Example:
        classifier = IntentClassifier()
        intent = classifier.classify("Fix the bug in main.py")
        # Intent(category=DEBUGGING, confidence=0.85)
    """
    
    # Keyword patterns for each intent category
    INTENT_PATTERNS = {
        IntentCategory.CODE_GENERATION: [
            r"\b(create|write|generate|implement|build|make)\b.*\b(code|function|class|module|script)\b",
            r"\bnew\b.*\b(file|class|function|component)\b",
            r"\badd\b.*\bfeature\b",
        ],
        IntentCategory.CODE_MODIFICATION: [
            r"\b(modify|change|update|edit|alter|fix)\b.*\b(code|file|function)\b",
            r"\brefactor\b",
            r"\bimprove\b.*\bcode\b",
        ],
        IntentCategory.CODE_REVIEW: [
            r"\b(review|check|analyze|examine)\b.*\b(code|pr|pull request)\b",
            r"\bcode\s*review\b",
            r"\blook\s*at\b.*\bcode\b",
        ],
        IntentCategory.DEBUGGING: [
            r"\b(debug|fix|solve|resolve|troubleshoot)\b.*\b(bug|error|issue|problem)\b",
            r"\bbug\b",
            r"\berror\b.*\b(in|on|at)\b",
            r"\bnot\s*working\b",
            r"\bcrash(es|ed|ing)\b",
            r"\bexception\b",
        ],
        IntentCategory.REFACTORING: [
            r"\brefactor\b",
            r"\brestructure\b",
            r"\breorganize\b",
            r"\bclean\s*up\b.*\bcode\b",
            r"\bimprove\b.*\bstructure\b",
        ],
        IntentCategory.TESTING: [
            r"\b(test|spec|unit\s*test|integration\s*test)\b",
            r"\bwrite\b.*\btests?\b",
            r"\badd\b.*\bcoverage\b",
        ],
        IntentCategory.DOCUMENTATION: [
            r"\b(document|doc|docs|documentation)\b",
            r"\bwrite\b.*\b(readme|docs|documentation)\b",
            r"\badd\b.*\bcomments?\b",
            r"\bdocument\b.*\b(code|api|function)\b",
        ],
        IntentCategory.ARCHITECTURE: [
            r"\b(architecture|design|structure|pattern)\b",
            r"\bplan\b.*\b(system|architecture|design)\b",
            r"\bhow\s*should\b.*\b(structured|designed|organized)\b",
        ],
        IntentCategory.PLANNING: [
            r"\b(plan|roadmap|strategy|approach)\b",
            r"\bhow\s*to\b.*\b(implement|build|create)\b",
            r"\bbreak\s*down\b.*\b(task|problem)\b",
        ],
        IntentCategory.RESEARCH: [
            r"\b(research|investigate|explore|find\s*out)\b",
            r"\bwhat\s*is\b",
            r"\bhow\s*does\b.*\bwork\b",
            r"\blearn\s*about\b",
        ],
        IntentCategory.QUESTION: [
            r"\?$",
            r"\b(what|why|how|when|where|who|which)\b",
            r"\bcan\s*you\b",
            r"\bcould\s*you\b",
        ],
        IntentCategory.EXPLANATION: [
            r"\b(explain|describe|tell\s*me\s*about)\b",
            r"\bwhat\s*does\b.*\bmean\b",
            r"\bhelp\s*me\s*understand\b",
        ],
        IntentCategory.FILE_OPERATION: [
            r"\b(read|write|create|delete|move|copy|list)\b.*\b(file|directory|folder)\b",
            r"\bopen\b.*\bfile\b",
            r"\bshow\b.*\bfile\b",
        ],
        IntentCategory.SHELL_COMMAND: [
            r"\b(run|execute|start|launch)\b.*\b(command|script|program)\b",
            r"\bin\s*terminal\b",
            r"\bshell\b",
            r"\bbash\b",
        ],
        IntentCategory.WEB_SEARCH: [
            r"\b(search|find|look\s*up)\b.*\b(web|online|internet)\b",
            r"\bgoogle\b",
            r"\bsearch\s*for\b",
        ],
    }
    
    # Capability mapping for intents
    INTENT_CAPABILITY_MAP = {
        IntentCategory.CODE_GENERATION: AgentCapability.CODE_GENERATION,
        IntentCategory.CODE_MODIFICATION: AgentCapability.CODE_GENERATION,
        IntentCategory.CODE_REVIEW: AgentCapability.CODE_REVIEW,
        IntentCategory.DEBUGGING: AgentCapability.DEBUGGING,
        IntentCategory.REFACTORING: AgentCapability.REFACTORING,
        IntentCategory.TESTING: AgentCapability.TESTING,
        IntentCategory.DOCUMENTATION: AgentCapability.DOCUMENTATION,
        IntentCategory.ARCHITECTURE: AgentCapability.ARCHITECTURE,
        IntentCategory.PLANNING: AgentCapability.PLANNING,
        IntentCategory.RESEARCH: AgentCapability.RESEARCH,
        IntentCategory.FILE_OPERATION: AgentCapability.FILE_OPERATIONS,
        IntentCategory.SHELL_COMMAND: AgentCapability.SHELL_EXECUTION,
        IntentCategory.WEB_SEARCH: AgentCapability.WEB_SEARCH,
    }
    
    def __init__(self):
        """Initialize the classifier."""
        self._compiled_patterns = {
            category: [re.compile(p, re.IGNORECASE) for p in patterns]
            for category, patterns in self.INTENT_PATTERNS.items()
        }
    
    def classify(self, text: str) -> Intent:
        """
        Classify the intent of the input text.
        
        Args:
            text: Input text to classify
            
        Returns:
            Classified Intent
        """
        scores: Dict[IntentCategory, float] = {}
        matched_keywords: Dict[IntentCategory, List[str]] = {}
        
        for category, patterns in self._compiled_patterns.items():
            score = 0.0
            keywords = []
            
            for pattern in patterns:
                matches = pattern.findall(text)
                if matches:
                    score += len(matches) * 0.3
                    keywords.extend(matches if isinstance(matches, list) else [matches])
            
            if score > 0:
                scores[category] = min(score, 1.0)
                matched_keywords[category] = keywords
        
        if not scores:
            return Intent(
                category=IntentCategory.GENERAL,
                confidence=0.5,
                keywords=[],
            )
        
        # Get best category
        best_category = max(scores.keys(), key=lambda k: scores[k] or 0)
        confidence = scores[best_category] or 0
        
        # Normalize confidence
        total_score = sum(scores.values())
        if total_score > 0:
            confidence = confidence / total_score
        
        return Intent(
            category=best_category,
            confidence=min(confidence, 1.0),
            keywords=matched_keywords.get(best_category, []),
        )
    
    def get_capability_for_intent(self, intent: Intent) -> Optional[AgentCapability]:
        """
        Get the required capability for an intent.
        
        Args:
            intent: Classified intent
            
        Returns:
            Required capability or None
        """
        return self.INTENT_CAPABILITY_MAP.get(intent.category)


class OrchestrationRouter:
    """
    Routes requests to appropriate agents.
    
    Uses intent classification and agent descriptions to determine
    the best agent for handling a request.
    
    Example:
        registry = AgentRegistry()
        registry.register(code_agent)
        
        router = OrchestrationRouter(registry)
        result = router.route("Fix the bug in main.py")
        # RoutingResult(agent_id="code_agent", intent=Intent(...))
    """
    
    def __init__(
        self,
        registry: AgentRegistry,
        min_confidence: float = 0.5,
    ):
        """
        Initialize the router.
        
        Args:
            registry: Agent registry
            min_confidence: Minimum confidence for routing
        """
        self.registry = registry
        self.min_confidence = min_confidence
        self.classifier = IntentClassifier()
    
    def route(self, prompt: str) -> RoutingResult:
        """
        Route a prompt to the best agent.
        
        Args:
            prompt: User prompt to route
            
        Returns:
            RoutingResult with agent assignment
        """
        # Classify intent
        intent = self.classifier.classify(prompt)
        
        # Get required capability
        capability = self.classifier.get_capability_for_intent(intent)
        
        # Find best agent
        if capability:
            agents = self.registry.find_by_capability(
                capability,
                available_only=True,
            )
        else:
            agents = self.registry.get_available_agents()
        
        if not agents:
            # Fall back to any agent
            agents = self.registry.get_all()
        
        if not agents:
            raise RuntimeError("No agents available for routing")
        
        # Sort by priority and select best
        agents.sort(key=lambda a: a.description.priority, reverse=True)
        best_agent = agents[0]
        
        # Get alternatives
        alternatives = [a.agent_id for a in agents[1:4] if a.agent_id != best_agent.agent_id]
        
        # Build routing reason
        reason = self._build_routing_reason(intent, best_agent)
        
        return RoutingResult(
            agent_id=best_agent.agent_id,
            intent=intent,
            confidence=intent.confidence,
            alternative_agents=alternatives,
            routing_reason=reason,
        )
    
    def _build_routing_reason(self, intent: Intent, agent: Agent) -> str:
        """Build a human-readable routing reason."""
        return (
            f"Routed to {agent.description.name} based on "
            f"{intent.category.value} intent (confidence: {intent.confidence:.2f})"
        )
    
    def route_to_agent(self, agent_id: str) -> Optional[Agent]:
        """
        Get a specific agent by ID.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent or None
        """
        return self.registry.get(agent_id)
    
    def get_routing_suggestions(self, prompt: str) -> List[Dict[str, Any]]:
        """
        Get routing suggestions for a prompt.
        
        Args:
            prompt: User prompt
            
        Returns:
            List of suggested agents with scores
        """
        intent = self.classifier.classify(prompt)
        capability = self.classifier.get_capability_for_intent(intent)
        
        suggestions = []
        
        if capability:
            agents = self.registry.find_by_capability(capability)
        else:
            agents = self.registry.get_all()
        
        for agent in agents:
            suggestions.append({
                "agent_id": agent.agent_id,
                "name": agent.description.name,
                "priority": agent.description.priority,
                "available": agent.is_available,
                "match_score": intent.confidence if agent.is_available else 0,
            })
        
        # Sort by match score and priority
        suggestions.sort(
            key=lambda s: (s["match_score"], s["priority"]),
            reverse=True,
        )
        
        return suggestions
