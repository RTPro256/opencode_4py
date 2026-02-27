"""
Local LLM Module.

This module provides local LLM management capabilities inspired by igllama:
- GGUF model management
- Local model inference
- OpenAI-compatible API server
- HuggingFace model integration
- GPU acceleration support

Integrated from:
- igllama: Zig-based Ollama alternative for running LLMs locally
"""

from .config import (
    LLMConfig,
    ModelConfig,
    SamplingConfig,
    ServerConfig,
    GGUFMetadata,
    ChatTemplateType,
    GPUMode,
)
from .model_manager import (
    ModelManager,
    ModelInfo,
    ModelSource,
    ModelStatus,
    get_model_manager,
)
from .server import (
    LLMServer,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
)

__all__ = [
    # Config
    "LLMConfig",
    "ModelConfig", 
    "SamplingConfig",
    "ServerConfig",
    "GGUFMetadata",
    "ChatTemplateType",
    "GPUMode",
    # Model Manager
    "ModelManager",
    "ModelInfo",
    "ModelSource",
    "ModelStatus",
    "get_model_manager",
    # Server
    "LLMServer",
    "get_llm_server",
    "ChatCompletionRequest",
    "ChatCompletionResponse",
    "ChatMessage",
]
