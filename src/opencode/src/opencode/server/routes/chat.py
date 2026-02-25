"""
Chat API routes for OpenCode HTTP server.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from opencode.server.app import get_session_manager


router = APIRouter()


class ChatMessage(BaseModel):
    """Chat message model."""
    role: str
    content: str


class ChatRequest(BaseModel):
    """Chat request model."""
    session_id: Optional[str] = None
    message: str
    model: Optional[str] = None
    stream: bool = True


class ChatResponse(BaseModel):
    """Chat response model."""
    session_id: str
    message: ChatMessage
    usage: Optional[dict] = None


class SessionCreate(BaseModel):
    """Session creation model."""
    project_path: str
    provider: str = "anthropic"
    model: str = "claude-3-5-sonnet-20241022"


@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    Send a message to the AI.
    
    Creates a new session if session_id is not provided.
    """
    session_manager = get_session_manager()
    
    # Create session if needed
    if not request.session_id:
        session = await session_manager.create_session(
            project_path=".",
            provider="anthropic",
            model=request.model or "claude-3-5-sonnet-20241022",
        )
        session_id = session.id
    else:
        session_id = request.session_id
    
    # Add user message
    await session_manager.add_message(
        session_id,
        role="user",
        content=request.message,
    )
    
    # Get AI response (simplified - would use provider in real implementation)
    response_content = "This is a placeholder response. Implement provider integration."
    
    # Add assistant message
    await session_manager.add_message(
        session_id,
        role="assistant",
        content=response_content,
        model=request.model,
    )
    
    return ChatResponse(
        session_id=session_id,
        message=ChatMessage(role="assistant", content=response_content),
    )


@router.post("/stream")
async def stream_message(request: ChatRequest):
    """
    Stream a message response from the AI.
    """
    
    async def generate():
        """Generate streaming response."""
        # Placeholder streaming
        words = ["This", " is", " a", " streaming", " response", "."]
        for word in words:
            yield f"data: {word}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
    )


@router.websocket("/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time chat.
    
    Provides bidirectional communication for chat messages
    with streaming responses.
    """
    await websocket.accept()
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            
            message = data.get("message", "")
            model = data.get("model", "claude-3-5-sonnet-20241022")
            
            # Add user message
            session_manager = get_session_manager()
            await session_manager.add_message(
                session_id,
                role="user",
                content=message,
            )
            
            # Send acknowledgment
            await websocket.send_json({
                "type": "ack",
                "message": "Processing...",
            })
            
            # Stream response (placeholder)
            response = ""
            words = ["This", " is", " a", " WebSocket", " response", "."]
            for word in words:
                response += word
                await websocket.send_json({
                    "type": "chunk",
                    "content": word,
                })
            
            # Save response
            await session_manager.add_message(
                session_id,
                role="assistant",
                content=response,
                model=model,
            )
            
            # Send completion
            await websocket.send_json({
                "type": "done",
                "message": response,
            })
    
    except WebSocketDisconnect:
        pass


@router.get("/history/{session_id}")
async def get_history(session_id: str, limit: int = 100):
    """Get chat history for a session."""
    session_manager = get_session_manager()
    messages = await session_manager.get_messages(session_id, limit=limit)
    
    return {
        "session_id": session_id,
        "messages": [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ],
    }


@router.delete("/history/{session_id}")
async def clear_history(session_id: str):
    """Clear chat history for a session."""
    session_manager = get_session_manager()
    await session_manager.clear_messages(session_id)
    return {"status": "ok"}
