"""
Google Gemini provider implementation.

Supports Gemini 2.0 Flash, Gemini 1.5 Pro, and other Google models.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Optional

import httpx

from opencode.provider.base import (
    Message,
    Provider,
    StreamChunk,
    ToolCall,
    Usage,
)


@dataclass
class GoogleProvider(Provider):
    """
    Google Gemini provider implementation.
    
    Supports:
    - Gemini 2.0 Flash
    - Gemini 1.5 Pro
    - Gemini 1.5 Flash
    """
    
    api_key: str
    model: str = "gemini-2.0-flash-exp"
    base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    max_tokens: int = 8192
    temperature: float = 0.7
    
    # Model pricing (per 1M tokens)
    PRICING = {
        "gemini-2.0-flash-exp": {"input": 0.0, "output": 0.0},
        "gemini-1.5-pro": {"input": 1.25, "output": 5.0},
        "gemini-1.5-flash": {"input": 0.075, "output": 0.3},
        "gemini-1.5-pro-latest": {"input": 1.25, "output": 5.0},
        "gemini-1.5-flash-latest": {"input": 0.075, "output": 0.3},
    }
    
    @property
    def name(self) -> str:
        return "google"
    
    def _get_endpoint(self) -> str:
        """Get the API endpoint for the model."""
        return f"{self.base_url}/models/{self.model}"
    
    def _convert_messages(self, messages: list[dict]) -> list[dict]:
        """Convert messages to Gemini format."""
        contents = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Map roles
            gemini_role = "user" if role in ["user", "system"] else "model"
            
            # Handle system messages
            if role == "system":
                # Prepend system message to first user message
                if contents and contents[0]["role"] == "user":
                    contents[0]["parts"].insert(0, {"text": f"System: {content}\n\n"})
                    continue
            
            contents.append({
                "role": gemini_role,
                "parts": [{"text": content}],
            })
        
        return contents
    
    async def complete(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        **kwargs,
    ) -> Message:
        """Send a completion request to Google Gemini."""
        async with httpx.AsyncClient() as client:
            url = f"{self._get_endpoint()}:generateContent"
            
            # Build request body
            body = {
                "contents": self._convert_messages(messages),
                "generationConfig": {
                    "maxOutputTokens": kwargs.get("max_tokens", self.max_tokens),
                    "temperature": kwargs.get("temperature", self.temperature),
                },
            }
            
            # Add tools if provided
            if tools:
                body["tools"] = self._convert_tools(tools)
            
            # Add system instruction if present
            system_messages = [m for m in messages if m.get("role") == "system"]
            if system_messages:
                body["systemInstruction"] = {
                    "parts": [{"text": system_messages[0].get("content", "")}]
                }
            
            response = await client.post(
                url,
                params={"key": self.api_key},
                json=body,
                headers={"Content-Type": "application/json"},
                timeout=120.0,
            )
            
            if response.status_code != 200:
                raise Exception(f"Google API error: {response.status_code} - {response.text}")
            
            data = response.json()
            
            return self._parse_response(data)
    
    async def stream(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        **kwargs,
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream a completion response from Google Gemini."""
        async with httpx.AsyncClient() as client:
            url = f"{self._get_endpoint()}:streamGenerateContent"
            
            # Build request body
            body = {
                "contents": self._convert_messages(messages),
                "generationConfig": {
                    "maxOutputTokens": kwargs.get("max_tokens", self.max_tokens),
                    "temperature": kwargs.get("temperature", self.temperature),
                },
            }
            
            if tools:
                body["tools"] = self._convert_tools(tools)
            
            async with client.stream(
                "POST",
                url,
                params={"key": self.api_key, "alt": "sse"},
                json=body,
                headers={"Content-Type": "application/json"},
                timeout=120.0,
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise Exception(f"Google API error: {response.status_code}")
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip():
                            try:
                                data = json.loads(data_str)
                                chunk = self._parse_stream_chunk(data)
                                if chunk:
                                    yield chunk
                            except json.JSONDecodeError:
                                continue
    
    def _parse_response(self, data: dict) -> Message:
        """Parse a completion response."""
        candidates = data.get("candidates", [])
        if not candidates:
            return Message(content="", role="assistant")
        
        candidate = candidates[0]
        content_parts = candidate.get("content", {}).get("parts", [])
        
        # Extract text content
        text_content = ""
        tool_calls = []
        
        for part in content_parts:
            if "text" in part:
                text_content += part["text"]
            elif "functionCall" in part:
                fc = part["functionCall"]
                tool_calls.append(ToolCall(
                    id=fc.get("name", ""),  # Google doesn't have IDs
                    name=fc.get("name", ""),
                    arguments=fc.get("args", {}),
                ))
        
        # Extract usage
        usage_metadata = data.get("usageMetadata", {})
        usage = Usage(
            input_tokens=usage_metadata.get("promptTokenCount", 0),
            output_tokens=usage_metadata.get("candidatesTokenCount", 0),
        )
        
        # Calculate cost
        pricing = self.PRICING.get(self.model, {"input": 0, "output": 0})
        cost = (
            usage.input_tokens * pricing["input"] / 1_000_000 +
            usage.output_tokens * pricing["output"] / 1_000_000
        )
        
        return Message(
            content=text_content,
            role="assistant",
            tool_calls=tool_calls if tool_calls else None,
            usage=usage,
            cost=cost,
        )
    
    def _parse_stream_chunk(self, data: dict) -> Optional[StreamChunk]:
        """Parse a streaming chunk."""
        candidates = data.get("candidates", [])
        if not candidates:
            return None
        
        candidate = candidates[0]
        content_parts = candidate.get("content", {}).get("parts", [])
        
        text = ""
        for part in content_parts:
            if "text" in part:
                text += part["text"]
        
        if not text:
            return None
        
        # Check if finished
        finish_reason = candidate.get("finishReason")
        is_done = finish_reason is not None
        
        return StreamChunk(
            content=text,
            is_done=is_done,
        )
    
    def _convert_tools(self, tools: list[dict]) -> dict:
        """Convert tools to Gemini format."""
        function_declarations = []
        
        for tool in tools:
            func = tool.get("function", {})
            params = func.get("parameters", {})
            
            # Convert to Gemini schema format
            function_declarations.append({
                "name": func.get("name", ""),
                "description": func.get("description", ""),
                "parameters": {
                    "type": "object",
                    "properties": params.get("properties", {}),
                    "required": params.get("required", []),
                },
            })
        
        return {"functionDeclarations": function_declarations}
    
    async def count_tokens(self, messages: list[dict]) -> int:
        """Count tokens for messages."""
        async with httpx.AsyncClient() as client:
            url = f"{self._get_endpoint()}:countTokens"
            
            body = {
                "contents": self._convert_messages(messages),
            }
            
            response = await client.post(
                url,
                params={"key": self.api_key},
                json=body,
                timeout=30.0,
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("totalTokens", 0)
            
            return 0
