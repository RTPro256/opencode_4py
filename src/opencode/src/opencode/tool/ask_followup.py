"""
Ask Follow-up Question Tool

Interactive tool for asking clarifying questions during task execution.
"""

import logging
from typing import Any, Dict, List
from pydantic import BaseModel, Field

from opencode.tool.base import Tool, ToolResult

logger = logging.getLogger(__name__)


class FollowupQuestion(BaseModel):
    """A follow-up question with suggested answers."""
    question: str = Field(..., description="The question to ask")
    suggestions: List[str] = Field(default_factory=list, description="Suggested answers")
    allow_free_input: bool = Field(default=True, description="Allow free-form input")


class AskFollowupQuestionTool(Tool):
    """
    Tool for asking follow-up questions during task execution.
    
    This tool allows the AI to ask clarifying questions when it needs
    more information to proceed with a task.
    
    Example:
        result = await tool.execute({
            "question": "Which file should I modify?",
            "suggestions": ["config.py", "main.py", "Both files"]
        })
    """
    
    @property
    def name(self) -> str:
        return "ask_followup_question"
    
    @property
    def description(self) -> str:
        return "Ask a follow-up question to clarify requirements"
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The question to ask the user",
                },
                "suggestions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Suggested answers (2-4 options recommended)",
                },
                "allow_free_input": {
                    "type": "boolean",
                    "description": "Whether to allow free-form input",
                    "default": True,
                },
            },
            "required": ["question"],
        }
    
    async def execute(self, **params: Any) -> ToolResult:
        """
        Execute the ask follow-up question tool.
        
        Args:
            **params: Tool parameters including:
                - question: The question to ask
                - suggestions: List of suggested answers
                - allow_free_input: Whether to allow free-form input
            
        Returns:
            ToolResult with the question details
        """
        question = params.get("question")
        if not question:
            return ToolResult.err("Required parameter 'question' is missing")
        
        suggestions = params.get("suggestions", [])
        allow_free_input = params.get("allow_free_input", True)
        
        # Validate suggestions
        if suggestions and len(suggestions) > 10:
            return ToolResult.err("Too many suggestions (max 10)")
        
        # Create question object
        followup = FollowupQuestion(
            question=question,
            suggestions=suggestions,
            allow_free_input=allow_free_input,
        )
        
        # Format output
        output = f"Question: {question}"
        if suggestions:
            output += f"\n\nSuggested answers:\n"
            for i, suggestion in enumerate(suggestions, 1):
                output += f"  {i}. {suggestion}\n"
        
        # Return the question for the UI to handle
        return ToolResult.ok(
            output=output,
            metadata={
                "type": "followup_question",
                "question": followup.question,
                "suggestions": followup.suggestions,
                "allow_free_input": followup.allow_free_input,
                "requires_user_input": True,
                "suggestion_count": len(suggestions),
            },
        )
