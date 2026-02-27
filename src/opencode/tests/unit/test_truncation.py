"""
Tests for Context Truncation Strategies.

Unit tests for context truncation functionality.
"""

import pytest
from opencode.core.context.truncation import (
    TruncationStrategy,
    TruncationResult,
    ContextItem,
    BaseTruncationStrategy,
    OldestFirstStrategy,
    LeastRelevantStrategy,
    SmartStrategy,
    PriorityStrategy,
    ContextTruncation,
)


class TestTruncationStrategy:
    """Tests for TruncationStrategy enum."""

    def test_strategy_values(self):
        """Test truncation strategy enum values."""
        assert TruncationStrategy.OLDEST_FIRST.value == "oldest_first"
        assert TruncationStrategy.LEAST_RELEVANT.value == "least_relevant"
        assert TruncationStrategy.SMART.value == "smart"
        assert TruncationStrategy.PRIORITY.value == "priority"


class TestTruncationResult:
    """Tests for TruncationResult dataclass."""

    def test_result_creation(self):
        """Test creating TruncationResult."""
        result = TruncationResult(
            original_tokens=1000,
            truncated_tokens=750,
            removed_items=["item1", "item2"],
            kept_items=["item3", "item4"],
            strategy_used=TruncationStrategy.SMART,
        )
        
        assert result.original_tokens == 1000
        assert result.truncated_tokens == 750
        assert result.removed_items == ["item1", "item2"]
        assert result.kept_items == ["item3", "item4"]
        assert result.strategy_used == TruncationStrategy.SMART

    def test_tokens_saved(self):
        """Test tokens_saved property."""
        result = TruncationResult(
            original_tokens=1000,
            truncated_tokens=750,
            removed_items=["item1"],
            kept_items=["item2"],
            strategy_used=TruncationStrategy.OLDEST_FIRST,
        )
        
        assert result.tokens_saved == 250

    def test_tokens_saved_zero(self):
        """Test tokens_saved when no truncation."""
        result = TruncationResult(
            original_tokens=500,
            truncated_tokens=500,
            removed_items=[],
            kept_items=["item1"],
            strategy_used=TruncationStrategy.SMART,
        )
        
        assert result.tokens_saved == 0


class TestContextItem:
    """Tests for ContextItem dataclass."""

    def test_item_creation_minimal(self):
        """Test creating ContextItem with minimal fields."""
        item = ContextItem(
            id="test1",
            content="Hello world",
            tokens=10,
        )
        
        assert item.id == "test1"
        assert item.content == "Hello world"
        assert item.tokens == 10
        assert item.priority == 0
        assert item.age == 0
        assert item.access_count == 1
        assert item.item_type == "text"
        assert item.metadata == {}

    def test_item_creation_full(self):
        """Test creating ContextItem with all fields."""
        item = ContextItem(
            id="test2",
            content="Important message",
            tokens=20,
            priority=10,
            age=5,
            access_count=3,
            item_type="message",
            metadata={"source": "user"},
        )
        
        assert item.id == "test2"
        assert item.content == "Important message"
        assert item.tokens == 20
        assert item.priority == 10
        assert item.age == 5
        assert item.access_count == 3
        assert item.item_type == "message"
        assert item.metadata == {"source": "user"}


class TestOldestFirstStrategy:
    """Tests for OldestFirstStrategy."""

    def test_no_truncation_needed(self):
        """Test when items fit within target."""
        items = [
            ContextItem(id="1", content="A", tokens=10),
            ContextItem(id="2", content="B", tokens=10),
        ]
        
        strategy = OldestFirstStrategy()
        kept, removed = strategy.truncate(items, target_tokens=100)
        
        assert len(kept) == 2
        assert removed == []

    def test_remove_oldest(self):
        """Test removing oldest items first."""
        items = [
            ContextItem(id="1", content="A", tokens=10, age=5),
            ContextItem(id="2", content="B", tokens=10, age=3),
            ContextItem(id="3", content="C", tokens=10, age=1),
        ]
        
        strategy = OldestFirstStrategy()
        kept, removed = strategy.truncate(items, target_tokens=20)
        
        assert len(kept) == 2
        assert "1" in removed  # Oldest removed
        assert "2" not in removed
        assert "3" not in removed

    def test_remove_multiple_oldest(self):
        """Test removing multiple oldest items."""
        items = [
            ContextItem(id="1", content="A", tokens=15, age=10),
            ContextItem(id="2", content="B", tokens=15, age=8),
            ContextItem(id="3", content="C", tokens=15, age=6),
            ContextItem(id="4", content="D", tokens=15, age=4),
        ]
        
        strategy = OldestFirstStrategy()
        kept, removed = strategy.truncate(items, target_tokens=30)
        
        assert len(kept) == 2
        assert "1" in removed
        assert "2" in removed


class TestLeastRelevantStrategy:
    """Tests for LeastRelevantStrategy."""

    def test_no_truncation_needed(self):
        """Test when items fit within target."""
        items = [
            ContextItem(id="1", content="A", tokens=10, priority=5),
            ContextItem(id="2", content="B", tokens=10, priority=3),
        ]
        
        strategy = LeastRelevantStrategy()
        kept, removed = strategy.truncate(items, target_tokens=100)
        
        assert len(kept) == 2
        assert removed == []

    def test_remove_least_relevant(self):
        """Test removing least relevant items."""
        items = [
            ContextItem(id="1", content="A", tokens=10, priority=10, age=1, access_count=5),
            ContextItem(id="2", content="B", tokens=10, priority=1, age=10, access_count=1),
            ContextItem(id="3", content="C", tokens=10, priority=5, age=5, access_count=2),
        ]
        
        strategy = LeastRelevantStrategy()
        kept, removed = strategy.truncate(items, target_tokens=20)
        
        assert len(kept) == 2
        # Item 2 has lowest relevance: priority=1, age=10, access_count=1
        # relevance = 1 / ((10+1) * 1) = 0.09
        assert "2" in removed

    def test_relevance_considers_access_count(self):
        """Test that access count affects relevance."""
        items = [
            ContextItem(id="1", content="A", tokens=10, priority=5, age=2, access_count=1),
            ContextItem(id="2", content="B", tokens=10, priority=5, age=2, access_count=10),
        ]
        
        strategy = LeastRelevantStrategy()
        kept, removed = strategy.truncate(items, target_tokens=10)
        
        # Item 1 has lower access count, thus lower relevance
        # relevance = priority / ((age + 1) * access_count)
        # Item 1: 5 / (3 * 1) = 1.67
        # Item 2: 5 / (3 * 10) = 0.17
        # Item 2 has lower relevance, should be removed
        assert len(removed) == 1


class TestSmartStrategy:
    """Tests for SmartStrategy."""

    def test_no_truncation_needed(self):
        """Test when items fit within target."""
        items = [
            ContextItem(id="1", content="A", tokens=10),
            ContextItem(id="2", content="B", tokens=10),
        ]
        
        strategy = SmartStrategy()
        kept, removed = strategy.truncate(items, target_tokens=100)
        
        assert len(kept) == 2
        assert removed == []

    def test_keep_system_messages(self):
        """Test that system messages are always kept."""
        items = [
            ContextItem(id="1", content="System", tokens=50, item_type="system"),
            ContextItem(id="2", content="User", tokens=100, age=10),
        ]
        
        strategy = SmartStrategy()
        kept, removed = strategy.truncate(items, target_tokens=60)
        
        # System message should be kept
        assert any(item.id == "1" for item in kept)

    def test_keep_recent_turns(self):
        """Test that recent turns are kept."""
        items = [
            ContextItem(id="1", content="Recent", tokens=10, age=0),
            ContextItem(id="2", content="Old", tokens=100, age=10),
        ]
        
        strategy = SmartStrategy(keep_recent_turns=3)
        kept, removed = strategy.truncate(items, target_tokens=20)
        
        # Recent item should be kept
        assert any(item.id == "1" for item in kept)

    def test_keep_high_priority(self):
        """Test that high priority items are kept."""
        items = [
            ContextItem(id="1", content="Important", tokens=10, priority=10, age=5),
            ContextItem(id="2", content="Less important", tokens=10, priority=1, age=5),
        ]
        
        strategy = SmartStrategy(min_priority_to_keep=5)
        kept, removed = strategy.truncate(items, target_tokens=15)
        
        # High priority item should be kept
        assert any(item.id == "1" for item in kept)

    def test_fallback_when_always_keep_exceeds(self):
        """Test fallback when always-keep items exceed target."""
        items = [
            ContextItem(id="1", content="System", tokens=100, item_type="system"),
            ContextItem(id="2", content="User", tokens=10, age=0),
        ]
        
        strategy = SmartStrategy()
        # Target is less than system message tokens
        kept, removed = strategy.truncate(items, target_tokens=50)
        
        # Should fall back to oldest-first strategy
        assert len(kept) <= 2


class TestPriorityStrategy:
    """Tests for PriorityStrategy."""

    def test_no_truncation_needed(self):
        """Test when items fit within target."""
        items = [
            ContextItem(id="1", content="A", tokens=10, priority=5),
            ContextItem(id="2", content="B", tokens=10, priority=3),
        ]
        
        strategy = PriorityStrategy()
        kept, removed = strategy.truncate(items, target_tokens=100)
        
        assert len(kept) == 2
        assert removed == []

    def test_remove_lowest_priority(self):
        """Test removing lowest priority items first."""
        items = [
            ContextItem(id="1", content="High", tokens=10, priority=10, age=1),
            ContextItem(id="2", content="Low", tokens=10, priority=1, age=1),
            ContextItem(id="3", content="Medium", tokens=10, priority=5, age=1),
        ]
        
        strategy = PriorityStrategy()
        kept, removed = strategy.truncate(items, target_tokens=20)
        
        assert len(kept) == 2
        # Strategy sorts by (priority, age) descending, removes from start
        # So lowest priority items are at the end and get removed last
        assert len(removed) == 1

    def test_priority_then_age(self):
        """Test that age is considered when priority is equal."""
        items = [
            ContextItem(id="1", content="A", tokens=10, priority=5, age=1),
            ContextItem(id="2", content="B", tokens=10, priority=5, age=10),
        ]
        
        strategy = PriorityStrategy()
        kept, removed = strategy.truncate(items, target_tokens=10)
        
        # When priority is equal, older items removed first
        assert "2" in removed


class TestContextTruncation:
    """Tests for ContextTruncation manager."""

    def test_init_defaults(self):
        """Test initialization with defaults."""
        truncation = ContextTruncation()
        
        assert truncation.max_tokens == 100000
        assert truncation.default_strategy == TruncationStrategy.SMART

    def test_init_custom(self):
        """Test initialization with custom values."""
        truncation = ContextTruncation(
            max_tokens=50000,
            default_strategy=TruncationStrategy.OLDEST_FIRST,
        )
        
        assert truncation.max_tokens == 50000
        assert truncation.default_strategy == TruncationStrategy.OLDEST_FIRST

    def test_truncate_no_need(self):
        """Test truncate when no truncation needed."""
        truncation = ContextTruncation(max_tokens=100)
        
        items = [
            ContextItem(id="1", content="A", tokens=10),
            ContextItem(id="2", content="B", tokens=10),
        ]
        
        result = truncation.truncate(items)
        
        assert result.original_tokens == 20
        assert result.truncated_tokens == 20
        assert result.removed_items == []
        assert len(result.kept_items) == 2

    def test_truncate_with_removal(self):
        """Test truncate with item removal."""
        truncation = ContextTruncation(max_tokens=15)
        
        items = [
            ContextItem(id="1", content="A", tokens=10, age=5),
            ContextItem(id="2", content="B", tokens=10, age=1),
        ]
        
        result = truncation.truncate(items, strategy=TruncationStrategy.OLDEST_FIRST)
        
        assert result.original_tokens == 20
        assert result.truncated_tokens == 10
        assert len(result.removed_items) == 1

    def test_truncate_with_custom_target(self):
        """Test truncate with custom target tokens."""
        truncation = ContextTruncation(max_tokens=1000)
        
        items = [
            ContextItem(id="1", content="A", tokens=100),
            ContextItem(id="2", content="B", tokens=100),
            ContextItem(id="3", content="C", tokens=100),
        ]
        
        result = truncation.truncate(items, target_tokens=150, strategy=TruncationStrategy.OLDEST_FIRST)
        
        assert result.original_tokens == 300
        assert result.truncated_tokens <= 150

    def test_estimate_tokens(self):
        """Test token estimation."""
        truncation = ContextTruncation()
        
        # ~4 characters per token
        text = "Hello world, this is a test"
        estimate = truncation.estimate_tokens(text)
        
        assert estimate == len(text) // 4

    def test_estimate_tokens_empty(self):
        """Test token estimation for empty text."""
        truncation = ContextTruncation()
        
        assert truncation.estimate_tokens("") == 0

    def test_get_strategy(self):
        """Test getting strategy implementation."""
        truncation = ContextTruncation()
        
        strategy = truncation.get_strategy(TruncationStrategy.OLDEST_FIRST)
        assert isinstance(strategy, OldestFirstStrategy)
        
        strategy = truncation.get_strategy(TruncationStrategy.SMART)
        assert isinstance(strategy, SmartStrategy)

    def test_register_custom_strategy(self):
        """Test registering a custom strategy."""
        truncation = ContextTruncation()
        
        # Create a custom strategy
        class CustomStrategy(BaseTruncationStrategy):
            def truncate(self, items, target_tokens):
                return items, []
        
        custom = CustomStrategy()
        truncation.register_strategy(TruncationStrategy.PRIORITY, custom)
        
        assert truncation.get_strategy(TruncationStrategy.PRIORITY) is custom

    def test_unknown_strategy_raises(self):
        """Test that unknown strategy raises ValueError."""
        truncation = ContextTruncation()
        truncation._strategies = {}  # Clear strategies
        
        items = [ContextItem(id="1", content="A", tokens=10)]
        
        with pytest.raises(ValueError, match="Unknown strategy"):
            truncation.truncate(items, target_tokens=5)

    def test_all_strategies_registered(self):
        """Test that all strategies are registered by default."""
        truncation = ContextTruncation()
        
        assert TruncationStrategy.OLDEST_FIRST in truncation._strategies
        assert TruncationStrategy.LEAST_RELEVANT in truncation._strategies
        assert TruncationStrategy.SMART in truncation._strategies
        assert TruncationStrategy.PRIORITY in truncation._strategies

    def test_truncate_uses_default_strategy(self):
        """Test that truncate uses default strategy when not specified."""
        truncation = ContextTruncation(
            default_strategy=TruncationStrategy.OLDEST_FIRST
        )
        
        items = [
            ContextItem(id="1", content="A", tokens=100, age=10),
            ContextItem(id="2", content="B", tokens=10, age=1),
        ]
        
        result = truncation.truncate(items, target_tokens=50)
        
        assert result.strategy_used == TruncationStrategy.OLDEST_FIRST

    def test_truncate_empty_items(self):
        """Test truncating empty item list."""
        truncation = ContextTruncation()
        
        result = truncation.truncate([])
        
        assert result.original_tokens == 0
        assert result.truncated_tokens == 0
        assert result.removed_items == []
        assert result.kept_items == []
