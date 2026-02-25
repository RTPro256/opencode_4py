"""
Context Truncation Strategies

Provides strategies for truncating context when it exceeds limits.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class TruncationStrategy(Enum):
    """Available truncation strategies."""
    OLDEST_FIRST = "oldest_first"
    LEAST_RELEVANT = "least_relevant"
    SMART = "smart"
    PRIORITY = "priority"


@dataclass
class TruncationResult:
    """Result of a truncation operation."""
    original_tokens: int
    truncated_tokens: int
    removed_items: List[str]
    kept_items: List[str]
    strategy_used: TruncationStrategy
    
    @property
    def tokens_saved(self) -> int:
        """Get number of tokens saved."""
        return self.original_tokens - self.truncated_tokens


@dataclass
class ContextItem:
    """An item in the context that can be truncated."""
    id: str
    content: str
    tokens: int
    priority: int = 0  # Higher = more important
    age: int = 0  # Turns since last access
    access_count: int = 1
    item_type: str = "text"  # text, file, message, tool_result
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseTruncationStrategy(ABC):
    """Base class for truncation strategies."""
    
    @abstractmethod
    def truncate(
        self,
        items: List[ContextItem],
        target_tokens: int,
    ) -> Tuple[List[ContextItem], List[str]]:
        """
        Truncate items to fit within target tokens.
        
        Args:
            items: List of context items
            target_tokens: Target token count
            
        Returns:
            Tuple of (kept items, removed item IDs)
        """
        pass


class OldestFirstStrategy(BaseTruncationStrategy):
    """Remove oldest items first."""
    
    def truncate(
        self,
        items: List[ContextItem],
        target_tokens: int,
    ) -> Tuple[List[ContextItem], List[str]]:
        """Remove oldest items first."""
        current_tokens = sum(item.tokens for item in items)
        
        if current_tokens <= target_tokens:
            return items, []
        
        # Sort by age (oldest first)
        sorted_items = sorted(items, key=lambda x: x.age, reverse=True)
        
        kept = []
        removed = []
        
        for item in sorted_items:
            if current_tokens <= target_tokens:
                kept.append(item)
            else:
                current_tokens -= item.tokens
                removed.append(item.id)
        
        return kept, removed


class LeastRelevantStrategy(BaseTruncationStrategy):
    """Remove least relevant items (lowest priority, oldest)."""
    
    def truncate(
        self,
        items: List[ContextItem],
        target_tokens: int,
    ) -> Tuple[List[ContextItem], List[str]]:
        """Remove least relevant items."""
        current_tokens = sum(item.tokens for item in items)
        
        if current_tokens <= target_tokens:
            return items, []
        
        # Sort by relevance score (priority / (age + 1) * access_count)
        def relevance_score(item: ContextItem) -> float:
            return item.priority / ((item.age + 1) * item.access_count)
        
        sorted_items = sorted(items, key=relevance_score)
        
        kept = []
        removed = []
        
        for item in sorted_items:
            if current_tokens <= target_tokens:
                kept.append(item)
            else:
                current_tokens -= item.tokens
                removed.append(item.id)
        
        return kept, removed


class SmartStrategy(BaseTruncationStrategy):
    """
    Smart truncation that preserves important context.
    
    Rules:
    - Always keep system messages
    - Keep recent conversation turns
    - Keep high-priority items
    - Remove old, low-priority items
    """
    
    def __init__(
        self,
        keep_recent_turns: int = 3,
        min_priority_to_keep: int = 5,
    ):
        self.keep_recent_turns = keep_recent_turns
        self.min_priority_to_keep = min_priority_to_keep
    
    def truncate(
        self,
        items: List[ContextItem],
        target_tokens: int,
    ) -> Tuple[List[ContextItem], List[str]]:
        """Smart truncation with rules."""
        current_tokens = sum(item.tokens for item in items)
        
        if current_tokens <= target_tokens:
            return items, []
        
        # Categorize items
        always_keep = []
        candidates = []
        
        for item in items:
            # System messages always kept
            if item.item_type == "system":
                always_keep.append(item)
            # Recent turns kept
            elif item.age < self.keep_recent_turns:
                always_keep.append(item)
            # High priority kept
            elif item.priority >= self.min_priority_to_keep:
                always_keep.append(item)
            else:
                candidates.append(item)
        
        # Calculate tokens for always-keep items
        kept_tokens = sum(item.tokens for item in always_keep)
        
        if kept_tokens > target_tokens:
            # Even always-keep items exceed target, need to trim
            logger.warning(
                f"Always-keep items ({kept_tokens} tokens) exceed target ({target_tokens})"
            )
            # Fall back to oldest-first for always-keep
            return OldestFirstStrategy().truncate(items, target_tokens)
        
        # Sort candidates by relevance
        def relevance_score(item: ContextItem) -> float:
            return item.priority / ((item.age + 1) * max(1, item.access_count))
        
        sorted_candidates = sorted(candidates, key=relevance_score)
        
        kept = list(always_keep)
        removed = []
        
        for item in sorted_candidates:
            if kept_tokens + item.tokens <= target_tokens:
                kept.append(item)
                kept_tokens += item.tokens
            else:
                removed.append(item.id)
        
        return kept, removed


class PriorityStrategy(BaseTruncationStrategy):
    """Remove items based on explicit priority levels."""
    
    def truncate(
        self,
        items: List[ContextItem],
        target_tokens: int,
    ) -> Tuple[List[ContextItem], List[str]]:
        """Remove lowest priority items first."""
        current_tokens = sum(item.tokens for item in items)
        
        if current_tokens <= target_tokens:
            return items, []
        
        # Sort by priority (lowest first), then by age (oldest first)
        sorted_items = sorted(items, key=lambda x: (x.priority, x.age), reverse=True)
        
        kept = []
        removed = []
        
        for item in sorted_items:
            if current_tokens <= target_tokens:
                kept.append(item)
            else:
                current_tokens -= item.tokens
                removed.append(item.id)
        
        return kept, removed


class ContextTruncation:
    """
    Main context truncation manager.
    
    Provides a unified interface for truncating context using
    different strategies.
    
    Example:
        truncation = ContextTruncation(max_tokens=100000)
        
        items = [
            ContextItem(id="1", content="Hello", tokens=10, priority=5),
            ContextItem(id="2", content="World", tokens=20, priority=3),
        ]
        
        result = truncation.truncate(items, target_tokens=15)
    """
    
    _strategies: Dict[TruncationStrategy, BaseTruncationStrategy] = {}
    
    def __init__(
        self,
        max_tokens: int = 100000,
        default_strategy: TruncationStrategy = TruncationStrategy.SMART,
    ):
        """
        Initialize context truncation.
        
        Args:
            max_tokens: Maximum tokens allowed
            default_strategy: Default truncation strategy
        """
        self.max_tokens = max_tokens
        self.default_strategy = default_strategy
        
        # Register strategies
        self._strategies = {
            TruncationStrategy.OLDEST_FIRST: OldestFirstStrategy(),
            TruncationStrategy.LEAST_RELEVANT: LeastRelevantStrategy(),
            TruncationStrategy.SMART: SmartStrategy(),
            TruncationStrategy.PRIORITY: PriorityStrategy(),
        }
    
    def truncate(
        self,
        items: List[ContextItem],
        target_tokens: Optional[int] = None,
        strategy: Optional[TruncationStrategy] = None,
    ) -> TruncationResult:
        """
        Truncate items to fit within target tokens.
        
        Args:
            items: List of context items
            target_tokens: Target token count (defaults to max_tokens)
            strategy: Strategy to use (defaults to default_strategy)
            
        Returns:
            TruncationResult with details
        """
        target = target_tokens or self.max_tokens
        strat = strategy or self.default_strategy
        
        original_tokens = sum(item.tokens for item in items)
        
        if original_tokens <= target:
            return TruncationResult(
                original_tokens=original_tokens,
                truncated_tokens=original_tokens,
                removed_items=[],
                kept_items=[item.id for item in items],
                strategy_used=strat,
            )
        
        strategy_impl = self._strategies.get(strat)
        if not strategy_impl:
            raise ValueError(f"Unknown strategy: {strat}")
        
        kept, removed = strategy_impl.truncate(items, target)
        
        return TruncationResult(
            original_tokens=original_tokens,
            truncated_tokens=sum(item.tokens for item in kept),
            removed_items=removed,
            kept_items=[item.id for item in kept],
            strategy_used=strat,
        )
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Simple estimation: ~4 characters per token.
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        return len(text) // 4
    
    def get_strategy(self, strategy: TruncationStrategy) -> BaseTruncationStrategy:
        """Get a strategy implementation."""
        return self._strategies[strategy]
    
    def register_strategy(
        self,
        strategy: TruncationStrategy,
        implementation: BaseTruncationStrategy,
    ) -> None:
        """Register a custom strategy."""
        self._strategies[strategy] = implementation
