#!/usr/bin/env python3
"""
Provider configuration example for OpenCode Python.

This example demonstrates how to:
1. Configure different LLM providers
2. Use environment variables for API keys
3. Switch between providers
"""

import asyncio
import os

# Note: These imports assume opencode is installed
# pip install opencode-python


async def use_openai():
    """Example using OpenAI provider."""
    from opencode.provider.openai import OpenAIProvider
    
    provider = OpenAIProvider(
        api_key=os.environ.get("OPENAI_API_KEY"),
        model="gpt-4",
    )
    
    response = await provider.complete(
        prompt="Explain async/await in Python in one paragraph."
    )
    print(f"OpenAI Response: {response}")


async def use_anthropic():
    """Example using Anthropic provider."""
    from opencode.provider.anthropic import AnthropicProvider
    
    provider = AnthropicProvider(
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
        model="claude-3-opus-20240229",
    )
    
    response = await provider.complete(
        prompt="Explain async/await in Python in one paragraph."
    )
    print(f"Anthropic Response: {response}")


async def use_ollama():
    """Example using local Ollama provider."""
    from opencode.provider.ollama import OllamaProvider
    
    provider = OllamaProvider(
        base_url="http://localhost:11434",
        model="llama2",
    )
    
    response = await provider.complete(
        prompt="Explain async/await in Python in one paragraph."
    )
    print(f"Ollama Response: {response}")


async def main():
    """Run provider examples."""
    print("=== OpenAI Provider ===")
    if os.environ.get("OPENAI_API_KEY"):
        await use_openai()
    else:
        print("Set OPENAI_API_KEY to test OpenAI provider")
    
    print("\n=== Anthropic Provider ===")
    if os.environ.get("ANTHROPIC_API_KEY"):
        await use_anthropic()
    else:
        print("Set ANTHROPIC_API_KEY to test Anthropic provider")
    
    print("\n=== Ollama Provider (Local) ===")
    try:
        await use_ollama()
    except Exception as e:
        print(f"Ollama not available: {e}")


if __name__ == "__main__":
    asyncio.run(main())