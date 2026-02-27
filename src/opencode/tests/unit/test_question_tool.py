"""
Tests for Question tool implementation.
"""

import pytest
from opencode.tool.question import QuestionTool


@pytest.mark.unit
class TestQuestionTool:
    """Tests for QuestionTool class."""
    
    def test_tool_name(self):
        """Test tool name."""
        tool = QuestionTool()
        assert tool.name == "question"
    
    def test_tool_description(self):
        """Test tool has description."""
        tool = QuestionTool()
        assert tool.description is not None
        assert len(tool.description) > 0
    
    def test_tool_parameters(self):
        """Test tool parameters schema."""
        tool = QuestionTool()
        params = tool.parameters
        
        assert "properties" in params
        assert "questions" in params["properties"]
    
    @pytest.mark.asyncio
    async def test_ask_question(self):
        """Test asking a question."""
        tool = QuestionTool()
        
        result = await tool.execute(
            question="What is the capital of France?",
            suggested_answers=["Paris", "London", "Berlin"]
        )
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_question_without_suggested_answers(self):
        """Test asking a question without suggested answers."""
        tool = QuestionTool()
        
        result = await tool.execute(
            question="What would you like to do next?"
        )
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_empty_question(self):
        """Test with empty question."""
        tool = QuestionTool()
        
        result = await tool.execute(question="")
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_question_with_context(self):
        """Test question with context."""
        tool = QuestionTool()
        
        result = await tool.execute(
            question="Which file should I modify?",
            context="We need to fix a bug in the authentication module."
        )
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_question_with_multiple_suggestions(self):
        """Test question with multiple suggested answers."""
        tool = QuestionTool()
        
        result = await tool.execute(
            question="Which approach should we take?",
            suggested_answers=[
                "Option A: Refactor the existing code",
                "Option B: Create a new module",
                "Option C: Use a third-party library"
            ]
        )
        
        assert result is not None
