"""
Global configuration API routes for OpenCode HTTP server.

Provides endpoints for accessing global configuration and settings.
"""

from __future__ import annotations

from typing import Optional, Any
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


router = APIRouter()


# Models
class GlobalConfig(BaseModel):
    """Global configuration model."""
    version: str = "1.0.0"
    data_dir: str = "~/.local/share/opencode"
    log_level: str = "INFO"
    default_provider: str = "openai"
    default_model: str = "gpt-4"
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 300
    enable_rag: bool = True
    enable_mcp: bool = True
    enable_streaming: bool = True


class GlobalStats(BaseModel):
    """Global statistics model."""
    total_sessions: int = 0
    total_messages: int = 0
    total_tokens_used: int = 0
    active_sessions: int = 0
    uptime_seconds: float = 0.0


class GlobalStatus(BaseModel):
    """Global status model."""
    status: str = "running"
    version: str = "1.0.0"
    database_connected: bool = True
    mcp_connected: bool = False
    providers_available: list[str] = Field(default_factory=list)


# In-memory storage (would be from config in production)
_config = GlobalConfig()
_stats = GlobalStats()
_start_time: float = 0.0


def _get_uptime() -> float:
    """Get server uptime in seconds."""
    import time
    global _start_time
    if _start_time == 0.0:
        _start_time = time.time()
    return time.time() - _start_time


@router.get("", response_model=GlobalConfig)
async def get_global_config() -> GlobalConfig:
    """
    Get global configuration.
    
    Returns:
        Current global configuration
    """
    return _config


@router.patch("", response_model=GlobalConfig)
async def update_global_config(updates: dict[str, Any]) -> GlobalConfig:
    """
    Update global configuration.
    
    Args:
        updates: Configuration updates
        
    Returns:
        Updated configuration
        
    Raises:
        HTTPException: If invalid configuration key
    """
    valid_keys = set(GlobalConfig.model_fields.keys())
    
    for key in updates:
        if key not in valid_keys:
            raise HTTPException(status_code=400, detail=f"Invalid configuration key: {key}")
    
    # Apply updates
    for key, value in updates.items():
        setattr(_config, key, value)
    
    return _config


@router.get("/stats", response_model=GlobalStats)
async def get_global_stats() -> GlobalStats:
    """
    Get global statistics.
    
    Returns:
        Current statistics
    """
    _stats.uptime_seconds = _get_uptime()
    return _stats


@router.get("/status", response_model=GlobalStatus)
async def get_global_status() -> GlobalStatus:
    """
    Get global server status.
    
    Returns:
        Current server status
    """
    return GlobalStatus(
        status="running",
        version=_config.version,
        database_connected=True,
        mcp_connected=False,  # Would check actual MCP status
        providers_available=["openai", "anthropic", "ollama"],
    )


@router.post("/reset", status_code=204)
async def reset_global_stats() -> None:
    """
    Reset global statistics.
    
    This will reset all statistics counters to zero.
    """
    global _stats, _start_time
    _stats = GlobalStats()
    _start_time = 0.0


@router.get("/providers")
async def list_available_providers() -> list[dict[str, Any]]:
    """
    List all available providers and their status.
    
    Returns:
        List of providers with their availability status
    """
    return [
        {"id": "openai", "name": "OpenAI", "available": True, "models": ["gpt-4", "gpt-3.5-turbo"]},
        {"id": "anthropic", "name": "Anthropic", "available": True, "models": ["claude-3-opus", "claude-3-sonnet"]},
        {"id": "ollama", "name": "Ollama", "available": False, "models": []},
        {"id": "azure", "name": "Azure OpenAI", "available": False, "models": []},
        {"id": "google", "name": "Google AI", "available": False, "models": []},
        {"id": "mistral", "name": "Mistral AI", "available": False, "models": []},
        {"id": "groq", "name": "Groq", "available": False, "models": []},
    ]
