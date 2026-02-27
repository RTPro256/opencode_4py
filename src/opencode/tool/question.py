"""
Question tool for asking the user questions during execution.

This tool allows the AI to ask the user questions and receive answers,
enabling interactive workflows where user input is needed.
"""

from typing import Any, Optional
from dataclasses import dataclass, field

from opencode.tool.base import Tool, ToolResult


@dataclass
class QuestionOption:
    """A single option for a question."""
    label: str
    description: str = ""


@dataclass
class QuestionInfo:
    """Information about a question to ask."""
    question: str
    header: str
    options: list[QuestionOption] = field(default_factory=list)
    multiple: bool = False
    custom: bool = True  # Allow typing a custom answer


class QuestionTool(Tool):
    """Tool for asking the user questions."""
    
    @property
    def name(self) -> str:
        return "question"
    
    @property
    def description(self) -> str:
        return """Ask the user questions and wait for their answers.

This tool allows you to interact with the user by asking questions
when you need clarification, confirmation, or input.

Use this tool when:
- You need to clarify ambiguous instructions
- You want to confirm a potentially risky action
- You need user input to proceed
- You want to offer choices to the user

Each question can have:
- A question text (required)
- A short header for display (required, max 30 chars)
- A list of options to choose from
- Multiple selection support
- Custom answer support

Example:
{
  "questions": [
    {
      "question": "Which framework would you like to use?",
      "header": "Framework",
      "options": [
        {"label": "FastAPI", "description": "Modern async web framework"},
        {"label": "Flask", "description": "Lightweight WSGI framework"},
        {"label": "Django", "description": "Full-featured web framework"}
      ]
    }
  ]
}"""
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "questions": {
                    "type": "array",
                    "description": "Questions to ask the user",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "Complete question text",
                            },
                            "header": {
                                "type": "string",
                                "description": "Very short label (max 30 chars)",
                            },
                            "options": {
                                "type": "array",
                                "description": "Available choices",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "label": {
                                            "type": "string",
                                            "description": "Display text (1-5 words, concise)",
                                        },
                                        "description": {
                                            "type": "string",
                                            "description": "Explanation of choice",
                                        },
                                    },
                                    "required": ["label"],
                                },
                            },
                            "multiple": {
                                "type": "boolean",
                                "description": "Allow selecting multiple choices (default: false)",
                            },
                        },
                        "required": ["question", "header"],
                    },
                },
            },
            "required": ["questions"],
        }
    
    async def execute(self, **params: Any) -> ToolResult:
        """Execute the question tool."""
        questions = params.get("questions", [])
        
        if not questions:
            return ToolResult.err("questions array is required and must not be empty")
        
        # In a real implementation, this would integrate with the TUI
        # to display questions and wait for user responses.
        # For now, we'll return a placeholder that indicates the questions
        # were received and would be presented to the user.
        
        # Format questions for display
        formatted_questions = []
        for i, q in enumerate(questions):
            question_text = q.get("question", "")
            header = q.get("header", "")
            options = q.get("options", [])
            multiple = q.get("multiple", False)
            
            formatted = f"\nQ{i+1}: [{header}] {question_text}"
            if options:
                formatted += "\n    Options:"
                for opt in options:
                    label = opt.get("label", "")
                    desc = opt.get("description", "")
                    formatted += f"\n    - {label}"
                    if desc:
                        formatted += f": {desc}"
            if multiple:
                formatted += "\n    (Multiple selections allowed)"
            formatted_questions.append(formatted)
        
        output = f"Questions to ask user ({len(questions)} total):\n"
        output += "\n".join(formatted_questions)
        output += "\n\nNote: In interactive mode, these questions would be presented to the user via the TUI."
        
        # Return placeholder answers
        # In a real implementation, this would wait for user input
        placeholder_answers = []
        for q in questions:
            options = q.get("options", [])
            if options:
                # Return first option as placeholder
                placeholder_answers.append([options[0].get("label", "")])
            else:
                placeholder_answers.append(["User input required"])
        
        return ToolResult.ok(
            output=output,
            metadata={
                "questions": questions,
                "answers": placeholder_answers,
                "note": "In interactive mode, actual user answers would be returned",
            },
        )


class RejectedError(Exception):
    """Raised when the user rejects a question."""
    pass
