"""
Session API routes for OpenCode HTTP server.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from opencode.server.app import get_session_manager


router = APIRouter()


class SessionCreate(BaseModel):
    """Session creation model."""
    project_path: str
    provider: str = "anthropic"
    model: str = "claude-3-5-sonnet-20241022"
    title: Optional[str] = None


class SessionUpdate(BaseModel):
    """Session update model."""
    title: Optional[str] = None
    model: Optional[str] = None


class SessionResponse(BaseModel):
    """Session response model."""
    id: str
    project_path: str
    provider: str
    model: str
    title: Optional[str]
    created_at: str
    updated_at: str


@router.post("/", response_model=SessionResponse)
async def create_session(request: SessionCreate):
    """Create a new session."""
    session_manager = get_session_manager()
    session = await session_manager.create_session(
        project_path=request.project_path,
        provider=request.provider,
        model=request.model,
        title=request.title,
    )
    
    return SessionResponse(
        id=session.id,
        project_path=session.project_path,
        provider=session.provider,
        model=session.model,
        title=session.title,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
    )


@router.get("/", response_model=list[SessionResponse])
async def list_sessions(
    project_path: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """List all sessions."""
    session_manager = get_session_manager()
    sessions = await session_manager.list_sessions(
        project_path=project_path,
        limit=limit,
        offset=offset,
    )
    
    return [
        SessionResponse(
            id=s.id,
            project_path=s.project_path,
            provider=s.provider,
            model=s.model,
            title=s.title,
            created_at=s.created_at.isoformat(),
            updated_at=s.updated_at.isoformat(),
        )
        for s in sessions
    ]


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get a session by ID."""
    session_manager = get_session_manager()
    session = await session_manager.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionResponse(
        id=session.id,
        project_path=session.project_path,
        provider=session.provider,
        model=session.model,
        title=session.title,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
    )


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(session_id: str, request: SessionUpdate):
    """Update a session."""
    session_manager = get_session_manager()
    session = await session_manager.update_session(
        session_id,
        title=request.title,
        model=request.model,
    )
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionResponse(
        id=session.id,
        project_path=session.project_path,
        provider=session.provider,
        model=session.model,
        title=session.title,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
    )


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    session_manager = get_session_manager()
    success = await session_manager.delete_session(session_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"status": "ok"}


@router.post("/{session_id}/export")
async def export_session(session_id: str):
    """Export a session to JSON."""
    session_manager = get_session_manager()
    data = await session_manager.export_session(session_id)
    
    if not data:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return data


@router.post("/import")
async def import_session(data: dict):
    """Import a session from JSON."""
    session_manager = get_session_manager()
    session = await session_manager.import_session(data)
    
    return SessionResponse(
        id=session.id,
        project_path=session.project_path,
        provider=session.provider,
        model=session.model,
        title=session.title,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
    )
