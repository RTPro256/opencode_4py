"""Tests for QuestionTool."""

import pytest
from unittest.mock import MagicMock, patch

from opencode.tool.question import QuestionTool, QuestionOption, QuestionInfo, RejectedError
from opencode.tool.base import ToolResult


class TestQuestionOption:
    """Tests for QuestionOption dataclass."""
    
    def test_question_option_creation(self):
        """Test creating a question option."""
        opt = QuestionOption(label="Yes", description="Confirm action")
        assert opt.label == "Yes"
        assert opt.description == "Confirm action"
    
    def test_question_option_default_description(self):
        """Test question option with default description."""
        opt = QuestionOption(label="No")
        assert opt.label == "No"
        assert opt.description == ""


class TestQuestionInfo:
    """Tests for QuestionInfo dataclass."""
    
    def test_question_info_creation(self):
        """Test creating question info."""
        info = QuestionInfo(
            question="Do you want to proceed?",
            header="Confirm"
        )
        assert info.question == "Do you want to proceed?"
        assert info.header == "Confirm"
        assert info.options == []
        assert info.multiple is False
        assert info.custom is True
    
    def test_question_info_with_options(self):
        """Test question info with options."""
        options = [
            QuestionOption(label="Yes"),
            QuestionOption(label="No")
        ]
        info = QuestionInfo(
            question="Continue?",
            header="Choice",
            options=options,
            multiple=True,
            custom=False
        )
        assert len(info.options) == 2
        assert info.multiple is True
        assert info.custom is False


class TestQuestionTool:
    """Tests for QuestionTool class."""
    
    def test_name(self):
        """Test tool name."""
        tool = QuestionTool()
        assert tool.name == "question"
    
    def test_description(self):
        """Test tool description."""
        tool = QuestionTool()
        assert "question" in tool.description.lower()
        assert "user" in tool.description.lower()
    
    def test_parameters(self):
        """Test tool parameters schema."""
        tool = QuestionTool()
        params = tool.parameters
        
        assert params["type"] == "object"
        assert "questions" in params["properties"]
        assert params["required"] == ["questions"]
    
    @pytest.mark.asyncio
    async def test_execute_empty_questions(self):
        """Test executing with empty questions."""
        tool = QuestionTool()
        result = await tool.execute(questions=[])
        
        assert result.success is False
        assert result.error is not None
        assert "required" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_execute_single_question(self):
        """Test executing with single question."""
        tool = QuestionTool()
        result = await tool.execute(
            questions=[
                {
                    "question": "Do you want to proceed?",
                    "header": "Confirm"
                }
            ]
        )
        
        assert result.success is True
        assert "1 total" in result.output
        assert "Do you want to proceed?" in result.output
    
    @pytest.mark.asyncio
    async def test_execute_question_with_options(self):
        """Test executing question with options."""
        tool = QuestionTool()
        result = await tool.execute(
            questions=[
                {
                    "question": "Which framework?",
                    "header": "Framework",
                    "options": [
                        {"label": "FastAPI", "description": "Modern async"},
                        {"label": "Flask", "description": "Lightweight"}
                    ]
                }
            ]
        )
        
        assert result.success is True
        assert "FastAPI" in result.output
        assert "Flask" in result.output
        assert "Modern async" in result.output
    
    @pytest.mark.asyncio
    async def test_execute_multiple_questions(self):
        """Test executing multiple questions."""
        tool = QuestionTool()
        result = await tool.execute(
            questions=[
                {"question": "Question 1?", "header": "Q1"},
                {"question": "Question 2?", "header": "Q2"}
            ]
        )
        
        assert result.success is True
        assert "2 total" in result.output
        assert "Q1:" in result.output
        assert "Q2:" in result.output
    
    @pytest.mark.asyncio
    async def test_execute_multiple_selection(self):
        """Test question with multiple selection."""
        tool = QuestionTool()
        result = await tool.execute(
            questions=[
                {
                    "question": "Select features:",
                    "header": "Features",
                    "options": [
                        {"label": "Auth"},
                        {"label": "API"}
                    ],
                    "multiple": True
                }
            ]
        )
        
        assert result.success is True
        assert "Multiple selections allowed" in result.output
    
    @pytest.mark.asyncio
    async def test_execute_returns_placeholder_answers(self):
        """Test that execute returns placeholder answers."""
        tool = QuestionTool()
        result = await tool.execute(
            questions=[
                {
                    "question": "Choose one:",
                    "header": "Choice",
                    "options": [
                        {"label": "Option A"},
                        {"label": "Option B"}
                    ]
                }
            ]
        )
        
        assert result.success is True
        assert "answers" in result.metadata
        # First option should be returned as placeholder
        assert result.metadata["answers"][0][0] == "Option A"
    
    @pytest.mark.asyncio
    async def test_execute_no_options_returns_placeholder(self):
        """Test that questions without options return placeholder."""
        tool = QuestionTool()
        result = await tool.execute(
            questions=[
                {
                    "question": "Enter your name:",
                    "header": "Name"
                }
            ]
        )
        
        assert result.success is True
        assert result.metadata["answers"][0][0] == "User input required"


class TestRejectedError:
    """Tests for RejectedError exception."""
    
    def test_rejected_error_creation(self):
        """Test creating RejectedError."""
        error = RejectedError("User rejected the question")
        assert str(error) == "User rejected the question"
    
    def test_rejected_error_is_exception(self):
        """Test that RejectedError is an Exception."""
        error = RejectedError()
        assert isinstance(error, Exception)
