"""
Context compaction for session management.

This module provides functionality to compact conversation history when
the context window is approaching its limit. It summarizes old messages
to preserve important context while reducing token count.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


# Constants
COMPACTION_BUFFER = 20_000  # Tokens to reserve before context limit
PRUNE_MINIMUM = 20_000  # Minimum tokens to prune
PRUNE_PROTECT = 40_000  # Protect recent tool calls up to this many tokens
PRUNE_PROTECTED_TOOLS = ["skill"]  # Tools whose outputs should not be pruned


@dataclass
class CompactionConfig:
    """Configuration for context compaction."""
    
    auto: bool = True  # Automatically compact when approaching limit
    reserved: Optional[int] = None  # Reserved tokens (default: COMPACTION_BUFFER)
    prune: bool = True  # Enable pruning of old tool outputs
    

@dataclass
class CompactionResult:
    """Result of a compaction operation."""
    
    success: bool
    tokens_before: int
    tokens_after: int
    messages_compacted: int
    summary: Optional[str] = None
    error: Optional[str] = None
    

@dataclass
class CompactionSummary:
    """
    Summary generated during compaction.
    
    This is the structured summary that replaces old messages,
    providing context for the next agent to continue work.
    """
    
    goal: str
    instructions: list[str] = field(default_factory=list)
    discoveries: list[str] = field(default_factory=list)
    accomplished: list[str] = field(default_factory=list)
    relevant_files: list[str] = field(default_factory=list)
    
    def to_prompt(self) -> str:
        """Convert summary to a prompt for the next agent."""
        sections = [
            "## Goal",
            self.goal,
            "",
            "## Instructions",
        ]
        
        for instruction in self.instructions:
            sections.append(f"- {instruction}")
        
        sections.extend([
            "",
            "## Discoveries",
        ])
        
        for discovery in self.discoveries:
            sections.append(f"- {discovery}")
        
        sections.extend([
            "",
            "## Accomplished",
        ])
        
        for item in self.accomplished:
            sections.append(f"- {item}")
        
        sections.extend([
            "",
            "## Relevant files / directories",
        ])
        
        for file in self.relevant_files:
            sections.append(f"- {file}")
        
        return "\n".join(sections)


# Default compaction prompt template
COMPACTION_PROMPT = """Provide a detailed prompt for continuing our conversation above.
Focus on information that would be helpful for continuing the conversation, including what we did, what we're doing, which files we're working on, and what we're going to do next.
The summary that you construct will be used so that another agent can read it and continue the work.

When constructing the summary, try to stick to this template:
---
## Goal

[What goal(s) is the user trying to accomplish?]

## Instructions

- [What important instructions did the user give you that are relevant]
- [If there is a plan or spec, include information about it so next agent can continue using it]

## Discoveries

[What notable things were learned during this conversation that would be useful for the next agent to know when continuing the work]

## Accomplished

[What work has been completed, what work is still in progress, and what work is left?]

## Relevant files / directories

[Construct a structured list of relevant files that have been read, edited, or created that pertain to the task at hand. If all the files in a directory are relevant, include the path to the directory.]
---"""


def is_overflow(
    tokens_used: int,
    context_limit: int,
    max_output_tokens: int,
    config: Optional[CompactionConfig] = None,
) -> bool:
    """
    Check if the session is approaching context overflow.
    
    Args:
        tokens_used: Total tokens used in the session
        context_limit: Maximum context length for the model
        max_output_tokens: Maximum output tokens for the model
        config: Compaction configuration
        
    Returns:
        True if compaction should be triggered
    """
    config = config or CompactionConfig()
    
    if not config.auto:
        return False
    
    if context_limit == 0:
        return False
    
    reserved = config.reserved or min(COMPACTION_BUFFER, max_output_tokens)
    
    # Calculate usable context
    usable = context_limit - reserved
    
    return tokens_used >= usable


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text.
    
    Simple estimation: ~4 characters per token.
    For accurate counting, use tiktoken or model-specific tokenizer.
    """
    return len(text) // 4


async def prune_tool_outputs(
    messages: list[dict[str, Any]],
    config: Optional[CompactionConfig] = None,
) -> tuple[list[dict[str, Any]], int]:
    """
    Prune old tool outputs from messages.
    
    Goes backwards through messages until there are PRUNE_PROTECT tokens
    worth of tool calls, then marks older tool outputs for compaction.
    
    Args:
        messages: List of messages to prune
        config: Compaction configuration
        
    Returns:
        Tuple of (pruned messages, tokens pruned)
    """
    config = config or CompactionConfig()
    
    if not config.prune:
        return messages, 0
    
    total = 0
    pruned = 0
    to_prune = []
    turns = 0
    
    # Iterate backwards through messages
    for msg_index in range(len(messages) - 1, -1, -1):
        msg = messages[msg_index]
        
        # Count turns (user messages)
        if msg.get("role") == "user":
            turns += 1
        
        # Skip recent turns
        if turns < 2:
            continue
        
        # Stop at existing summary
        if msg.get("role") == "assistant" and msg.get("summary"):
            break
        
        # Check for tool outputs
        parts = msg.get("parts", [])
        for part_index in range(len(parts) - 1, -1, -1):
            part = parts[part_index]
            
            if part.get("type") == "tool":
                tool_name = part.get("tool", "")
                
                # Skip protected tools
                if tool_name in PRUNE_PROTECTED_TOOLS:
                    continue
                
                # Skip already compacted
                if part.get("state", {}).get("time", {}).get("compacted"):
                    break
                
                # Estimate tokens
                output = part.get("state", {}).get("output", "")
                estimate = estimate_tokens(output)
                total += estimate
                
                if total > PRUNE_PROTECT:
                    pruned += estimate
                    to_prune.append(part)
    
    # Apply pruning if above minimum
    if pruned > PRUNE_MINIMUM:
        for part in to_prune:
            if "state" not in part:
                part["state"] = {}
            if "time" not in part["state"]:
                part["state"]["time"] = {}
            part["state"]["time"]["compacted"] = datetime.now().timestamp()
        
        return messages, pruned
    
    return messages, 0


async def compact_session(
    messages: list[dict[str, Any]],
    model_id: str,
    provider_id: str,
    context_limit: int,
    max_output_tokens: int,
    config: Optional[CompactionConfig] = None,
) -> CompactionResult:
    """
    Compact a session's message history.
    
    This function:
    1. Checks if compaction is needed
    2. Prunes old tool outputs
    3. Generates a summary of old messages
    4. Replaces old messages with the summary
    
    Args:
        messages: List of messages to compact
        model_id: Model ID being used
        provider_id: Provider ID being used
        context_limit: Maximum context length
        max_output_tokens: Maximum output tokens
        config: Compaction configuration
        
    Returns:
        CompactionResult with details of the operation
    """
    config = config or CompactionConfig()
    
    # Estimate current token usage
    total_tokens = sum(
        estimate_tokens(str(msg)) for msg in messages
    )
    
    # Check if compaction needed
    if not is_overflow(total_tokens, context_limit, max_output_tokens, config):
        return CompactionResult(
            success=False,
            tokens_before=total_tokens,
            tokens_after=total_tokens,
            messages_compacted=0,
            error="Compaction not needed",
        )
    
    # Prune tool outputs first
    messages, pruned_tokens = await prune_tool_outputs(messages, config)
    
    # In a full implementation, this would:
    # 1. Create a compaction agent
    # 2. Send old messages to the model with compaction prompt
    # 3. Generate a summary
    # 4. Replace old messages with the summary
    
    # Placeholder for the summary generation
    summary = CompactionSummary(
        goal="Continue the previous task",
        instructions=["Review the conversation history for context"],
        discoveries=[],
        accomplished=["Previous messages compacted"],
        relevant_files=[],
    )
    
    return CompactionResult(
        success=True,
        tokens_before=total_tokens,
        tokens_after=total_tokens - pruned_tokens,
        messages_compacted=len(messages),
        summary=summary.to_prompt(),
    )
