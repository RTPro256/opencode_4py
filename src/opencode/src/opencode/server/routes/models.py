"""
Models API routes for OpenCode HTTP server.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from opencode.server.app import get_config


router = APIRouter()


class ModelInfo(BaseModel):
    """Model information."""
    id: str
    name: str
    provider: str
    context_length: int
    supports_vision: bool = False
    supports_tools: bool = True
    cost_input: float = 0.0
    cost_output: float = 0.0


class ProviderInfo(BaseModel):
    """Provider information."""
    id: str
    name: str
    models: list[ModelInfo]
    configured: bool = False


# Available models by provider
AVAILABLE_MODELS: dict[str, list[ModelInfo]] = {
    "anthropic": [
        ModelInfo(
            id="claude-3-5-sonnet-20241022",
            name="Claude 3.5 Sonnet",
            provider="anthropic",
            context_length=200000,
            supports_vision=True,
            supports_tools=True,
            cost_input=3.0,
            cost_output=15.0,
        ),
        ModelInfo(
            id="claude-3-5-haiku-20241022",
            name="Claude 3.5 Haiku",
            provider="anthropic",
            context_length=200000,
            supports_vision=True,
            supports_tools=True,
            cost_input=0.8,
            cost_output=4.0,
        ),
        ModelInfo(
            id="claude-3-opus-20240229",
            name="Claude 3 Opus",
            provider="anthropic",
            context_length=200000,
            supports_vision=True,
            supports_tools=True,
            cost_input=15.0,
            cost_output=75.0,
        ),
    ],
    "openai": [
        ModelInfo(
            id="gpt-4o",
            name="GPT-4o",
            provider="openai",
            context_length=128000,
            supports_vision=True,
            supports_tools=True,
            cost_input=5.0,
            cost_output=15.0,
        ),
        ModelInfo(
            id="gpt-4o-mini",
            name="GPT-4o Mini",
            provider="openai",
            context_length=128000,
            supports_vision=True,
            supports_tools=True,
            cost_input=0.15,
            cost_output=0.6,
        ),
        ModelInfo(
            id="gpt-4-turbo",
            name="GPT-4 Turbo",
            provider="openai",
            context_length=128000,
            supports_vision=True,
            supports_tools=True,
            cost_input=10.0,
            cost_output=30.0,
        ),
        ModelInfo(
            id="o1",
            name="o1",
            provider="openai",
            context_length=200000,
            supports_vision=False,
            supports_tools=False,
            cost_input=15.0,
            cost_output=60.0,
        ),
        ModelInfo(
            id="o1-mini",
            name="o1 Mini",
            provider="openai",
            context_length=128000,
            supports_vision=False,
            supports_tools=False,
            cost_input=3.0,
            cost_output=12.0,
        ),
    ],
    "google": [
        ModelInfo(
            id="gemini-2.0-flash",
            name="Gemini 2.0 Flash",
            provider="google",
            context_length=1000000,
            supports_vision=True,
            supports_tools=True,
            cost_input=0.0,
            cost_output=0.0,
        ),
        ModelInfo(
            id="gemini-1.5-pro",
            name="Gemini 1.5 Pro",
            provider="google",
            context_length=2000000,
            supports_vision=True,
            supports_tools=True,
            cost_input=1.25,
            cost_output=5.0,
        ),
    ],
}


@router.get("/")
async def list_providers():
    """List all available providers and their models."""
    config = get_config()
    
    providers = []
    for provider_id, models in AVAILABLE_MODELS.items():
        provider_config = config.get_provider_config(provider_id)
        configured = provider_config is not None and provider_config.api_key is not None
        
        providers.append(ProviderInfo(
            id=provider_id,
            name=provider_id.capitalize(),
            models=models,
            configured=configured,
        ))
    
    return providers


@router.get("/{provider_id}")
async def get_provider_models(provider_id: str):
    """Get models for a specific provider."""
    if provider_id not in AVAILABLE_MODELS:
        return {"error": "Provider not found", "models": []}
    
    config = get_config()
    provider_config = config.get_provider_config(provider_id)
    configured = provider_config is not None and provider_config.api_key is not None
    
    return ProviderInfo(
        id=provider_id,
        name=provider_id.capitalize(),
        models=AVAILABLE_MODELS[provider_id],
        configured=configured,
    )


@router.get("/{provider_id}/{model_id}")
async def get_model_info(provider_id: str, model_id: str):
    """Get information about a specific model."""
    if provider_id not in AVAILABLE_MODELS:
        return {"error": "Provider not found"}
    
    for model in AVAILABLE_MODELS[provider_id]:
        if model.id == model_id:
            return model
    
    return {"error": "Model not found"}
