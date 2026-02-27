"""
Router API Routes

FastAPI routes for intelligent LLM router management.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from opencode.router.engine import RouterEngine, RoutingResult
from opencode.router.config import RouterConfig, QualityPreference
from opencode.router.profiler import ModelProfile
from opencode.router.vram_monitor import VRAMMonitor, VRAMStatus

router = APIRouter(prefix="/router", tags=["router"])

# Global instances
_engine: Optional[RouterEngine] = None
_vram_monitor: Optional[VRAMMonitor] = None


def get_engine() -> RouterEngine:
    """Get or create the router engine."""
    global _engine
    if _engine is None:
        _engine = RouterEngine()
    return _engine


def get_vram_monitor() -> VRAMMonitor:
    """Get or create the VRAM monitor."""
    global _vram_monitor
    if _vram_monitor is None:
        _vram_monitor = VRAMMonitor()
    return _vram_monitor


# Request/Response Models
class RouteRequest(BaseModel):
    """Request to route a prompt."""
    prompt: str
    context: Optional[Dict[str, Any]] = None


class UpdateConfigRequest(BaseModel):
    """Request to update router configuration."""
    enabled: Optional[bool] = None
    quality_preference: Optional[str] = None
    pinned_model: Optional[str] = None
    fallback_model: Optional[str] = None
    cache_enabled: Optional[bool] = None
    vram_monitoring: Optional[bool] = None


class RegisterModelRequest(BaseModel):
    """Request to register a model."""
    model_id: str
    provider: str
    supports_tools: bool = False
    supports_vision: bool = False
    vram_required_gb: Optional[float] = None
    context_length: int = 4096


# Routes
@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """Get router status and statistics."""
    engine = get_engine()
    return engine.get_stats()


@router.post("/route")
async def route_prompt(request: RouteRequest) -> Dict[str, Any]:
    """Route a prompt to the best model."""
    engine = get_engine()
    result = await engine.route(request.prompt, request.context)
    return result.to_dict()


@router.get("/models")
async def list_models() -> List[Dict[str, Any]]:
    """List all registered models."""
    engine = get_engine()
    models = engine.list_models()
    return [
        {
            "model_id": m.model_id,
            "provider": m.provider,
            "supports_tools": m.supports_tools,
            "supports_vision": m.supports_vision,
            "context_length": m.context_length,
            "speed_score": m.speed_score,
            "quality_score": m.quality_score,
            "is_loaded": m.is_loaded,
        }
        for m in models
    ]


@router.post("/models")
async def register_model(request: RegisterModelRequest) -> Dict[str, str]:
    """Register a new model."""
    from opencode.router.config import ModelConfig
    
    engine = get_engine()
    
    config = ModelConfig(
        model_id=request.model_id,
        provider=request.provider,
        supports_tools=request.supports_tools,
        supports_vision=request.supports_vision,
        vram_required_gb=request.vram_required_gb,
        context_length=request.context_length,
    )
    
    engine.register_model(config)
    
    return {"status": "registered", "model_id": request.model_id}


@router.delete("/models/{model_id}")
async def unregister_model(model_id: str) -> Dict[str, str]:
    """Unregister a model."""
    engine = get_engine()
    
    if not engine.unregister_model(model_id):
        raise HTTPException(status_code=404, detail="Model not found")
    
    return {"status": "unregistered"}


@router.get("/models/{model_id}/profile")
async def get_model_profile(model_id: str) -> Dict[str, Any]:
    """Get the profile for a model."""
    engine = get_engine()
    profile = engine.profiler.get_profile(model_id)
    
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return {
        "model_id": profile.model_id,
        "provider": profile.provider,
        "avg_latency_ms": profile.avg_latency_ms,
        "tokens_per_second": profile.tokens_per_second,
        "coding_score": profile.coding_score,
        "reasoning_score": profile.reasoning_score,
        "creative_score": profile.creative_score,
        "math_score": profile.math_score,
        "overall_quality": profile.overall_quality,
        "profiled_at": profile.profiled_at.isoformat() if profile.profiled_at else None,
    }


@router.post("/profile")
async def profile_all_models() -> Dict[str, Any]:
    """Profile all registered models."""
    engine = get_engine()
    profiles = await engine.profile_models()
    
    return {
        "profiled": len(profiles),
        "models": list(profiles.keys()),
    }


@router.get("/config")
async def get_config() -> Dict[str, Any]:
    """Get current router configuration."""
    engine = get_engine()
    config = engine.config
    return {
        "enabled": config.enabled,
        "provider": config.provider,
        "quality_preference": config.quality_preference,
        "pinned_model": config.pinned_model,
        "fallback_model": config.fallback_model,
        "cache_enabled": config.cache_enabled,
        "vram_monitoring": config.vram_monitoring,
        "auto_unload": config.auto_unload,
        "profiling_enabled": config.profiling_enabled,
    }


@router.put("/config")
async def update_config(request: UpdateConfigRequest) -> Dict[str, Any]:
    """Update router configuration."""
    engine = get_engine()
    config = engine.config
    
    if request.enabled is not None:
        config.enabled = request.enabled
    if request.quality_preference is not None:
        config.quality_preference = QualityPreference(request.quality_preference)
    if request.pinned_model is not None:
        config.pinned_model = request.pinned_model
    if request.fallback_model is not None:
        config.fallback_model = request.fallback_model
    if request.cache_enabled is not None:
        config.cache_enabled = request.cache_enabled
    if request.vram_monitoring is not None:
        config.vram_monitoring = request.vram_monitoring
    
    return {"status": "updated"}


@router.get("/vram")
async def get_vram_status() -> Dict[str, Any]:
    """Get current VRAM status."""
    monitor = get_vram_monitor()
    status = await monitor.get_status()
    
    return {
        "available": monitor.available,
        "vendor": monitor.vendor.value,
        "gpus": [
            {
                "index": gpu.index,
                "name": gpu.name,
                "total_memory_mb": gpu.total_memory_mb,
                "used_memory_mb": gpu.used_memory_mb,
                "free_memory_mb": gpu.free_memory_mb,
                "utilization_percent": gpu.utilization_percent,
                "temperature_c": gpu.temperature_c,
            }
            for gpu in status.gpus
        ],
        "total_memory_mb": status.total_memory_mb,
        "total_used_mb": status.total_used_mb,
        "total_free_mb": status.total_free_mb,
        "overall_usage_percent": status.overall_usage_percent,
        "timestamp": status.timestamp.isoformat(),
    }


@router.get("/vram/recommend")
async def get_recommended_model_size() -> Dict[str, Any]:
    """Get recommended maximum model size based on available VRAM."""
    monitor = get_vram_monitor()
    recommended_mb = await monitor.get_recommended_model_size()
    
    return {
        "recommended_size_mb": recommended_mb,
        "recommended_size_gb": recommended_mb / 1024,
    }


@router.post("/cache/clear")
async def clear_cache() -> Dict[str, str]:
    """Clear the routing cache."""
    engine = get_engine()
    engine.cache.clear()
    return {"status": "cleared"}


@router.get("/categories")
async def list_categories() -> List[Dict[str, str]]:
    """List all prompt categories."""
    from opencode.router.config import PromptCategory
    from opencode.router.skills import SkillClassifier
    
    classifier = SkillClassifier()
    
    return [
        {
            "id": cat.value,
            "description": classifier.get_category_description(cat),
        }
        for cat in PromptCategory
    ]
