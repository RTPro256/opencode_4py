#!/usr/bin/env python3
"""
Basic usage example for OpenCode Python.

This example demonstrates how to:
1. Initialize the OpenCode client
2. Send a simple message to an LLM
3. Handle the response
"""

import asyncio
from opencode import OpenCode


async def main():
    """Run the basic usage example."""
    # Initialize the OpenCode client
    # Configuration is loaded from environment variables or config file
    async with OpenCode() as client:
        # Send a simple message
        response = await client.chat(
            message="Hello! Can you help me with Python programming?",
            model="gpt-4",  # or use your preferred model
        )
        
        print("Response:", response.content)
        print(f"Tokens used: {response.usage.total_tokens}")


if __name__ == "__main__":
    asyncio.run(main())