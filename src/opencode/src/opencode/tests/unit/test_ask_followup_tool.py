"""Tests for Ask Follow-up Question Tool."""

import pytest

from opencode.tool.ask_followup import AskFollowupQuestionTool, FollowupQuestion
from opencode.tool.base import ToolResult


class TestFollowupQuestion:
    """Tests for FollowupQuestion model."""

    def test_creation(self):
        """Test creating a follow-up question."""
        question = FollowupQuestion(
            question="Which file?",
            suggestions=["file1.py", "file2.py"],
            allow_free_input=True
        )
        
        assert question.question == "Which file?"
        assert question.suggestions == ["file1.py", "file2.py"]
        assert question.allow_free_input is True

    def test_default_allow_free_input(self):
        """Test default allow_free_input is True."""
        question = FollowupQuestion(question="Test?")
        
        assert question.allow_free_input is True

    def test_default_suggestions(self):
        """Test default suggestions is empty list."""
        question = FollowupQuestion(question="Test?")
        
        assert question.suggestions == []


class TestAskFollowupQuestionTool:
    """Tests for AskFollowupQuestionTool."""

    def test_name(self):
        """Test tool name."""
        tool = AskFollowupQuestionTool()
        
        assert tool.name == "ask_followup_question"

    def test_description(self):
        """Test tool description."""
        tool = AskFollowupQuestionTool()
        
        assert "question" in tool.description.lower()

    def test_parameters(self):
        """Test tool parameters schema."""
        tool = AskFollowupQuestionTool()
        
        params = tool.parameters
        
        assert params["type"] == "object"
        assert "question" in params["properties"]
        assert "suggestions" in params["properties"]
        assert "allow_free_input" in params["properties"]
        assert "question" in params["required"]

    @pytest.mark.asyncio
    async def test_execute_basic(self):
        """Test basic execution."""
        tool = AskFollowupQuestionTool()
        
        result = await tool.execute(question="What should I do?")
        
        assert result.success is True
        assert "What should I do?" in result.output

    @pytest.mark.asyncio
    async def test_execute_with_suggestions(self):
        """Test execution with suggestions."""
        tool = AskFollowupQuestionTool()
        
        result = await tool.execute(
            question="Which file?",
            suggestions=["main.py", "test.py", "config.py"]
        )
        
        assert result.success is True
        assert "Suggested answers" in result.output
        assert "main.py" in result.output
        assert "test.py" in result.output

    @pytest.mark.asyncio
    async def test_execute_missing_question(self):
        """Test execution with missing question."""
        tool = AskFollowupQuestionTool()
        
        result = await tool.execute()
        
        assert result.success is False
        assert "missing" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_too_many_suggestions(self):
        """Test execution with too many suggestions."""
        tool = AskFollowupQuestionTool()
        
        suggestions = [f"option{i}" for i in range(11)]
        result = await tool.execute(
            question="Pick one",
            suggestions=suggestions
        )
        
        assert result.success is False
        assert "too many" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_allow_free_input_false(self):
        """Test execution with allow_free_input=False."""
        tool = AskFollowupQuestionTool()
        
        result = await tool.execute(
            question="Pick one",
            suggestions=["A", "B"],
            allow_free_input=False
        )
        
        assert result.success is True
        assert result.metadata["allow_free_input"] is False

    @pytest.mark.asyncio
    async def test_metadata(self):
        """Test result metadata."""
        tool = AskFollowupQuestionTool()
        
        result = await tool.execute(
            question="Test question",
            suggestions=["A", "B"]
        )
        
        assert result.metadata["type"] == "followup_question"
        assert result.metadata["question"] == "Test question"
        assert result.metadata["suggestions"] == ["A", "B"]

    @pytest.mark.asyncio
    async def test_max_suggestions_allowed(self):
        """Test that 10 suggestions is allowed."""
        tool = AskFollowupQuestionTool()
        
        suggestions = [f"option{i}" for i in range(10)]
        result = await tool.execute(
            question="Pick one",
            suggestions=suggestions
        )
        
        assert result.success is True
