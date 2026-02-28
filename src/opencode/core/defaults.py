"""
Centralized default configuration for OpenCode.

This module provides sensible defaults that can be overridden via environment variables.
All project-wide defaults should be defined here to avoid duplication.
"""

import os
from pathlib import Path
from typing import Optional

# =============================================================================
# Local LLM Server URLs
# =============================================================================

# Ollama server URL
# Can be overridden via OLLAMA_HOST or OLLAMA_URL environment variable
def get_ollama_url() -> str:
    """Get Ollama server URL from environment or return default."""
    return os.environ.get("OLLAMA_HOST") or os.environ.get("OLLAMA_URL") or "http://localhost:11434"

OLLAMA_BASE_URL: str = get_ollama_url()
DEFAULT_OLLAMA_URL = "http://localhost:11434"  # Fallback if env not set

# LM Studio server URL
LMSTUDIO_BASE_URL: str = os.environ.get("LMSTUDIO_HOST", "http://localhost:1234")
DEFAULT_LMSTUDIO_URL = "http://localhost:1234"

# =============================================================================
# Default Models
# =============================================================================

# Default embedding model
DEFAULT_EMBEDDING_MODEL: str = os.environ.get("DEFAULT_EMBEDDING_MODEL", "nomic-embed-text")

# Embedding dimensions
DEFAULT_EMBEDDING_DIMENSIONS: int = int(os.environ.get("DEFAULT_EMBEDDING_DIMENSIONS", "768"))

# =============================================================================
# HTTP Timeouts (in seconds)
# =============================================================================

DEFAULT_HTTP_TIMEOUT: float = float(os.environ.get("DEFAULT_HTTP_TIMEOUT", "30.0"))
LLM_TIMEOUT: float = float(os.environ.get("LLM_TIMEOUT", "300.0"))
WEBSEARCH_TIMEOUT: float = float(os.environ.get("WEBSEARCH_TIMEOUT", "30.0"))
EMBEDDING_TIMEOUT: float = float(os.environ.get("EMBEDDING_TIMEOUT", "60.0"))

# =============================================================================
# RAG Configuration
# =============================================================================

# Default chunk size for text splitting
DEFAULT_CHUNK_SIZE: int = int(os.environ.get("DEFAULT_CHUNK_SIZE", "500"))
DEFAULT_CHUNK_OVERLAP: int = int(os.environ.get("DEFAULT_CHUNK_OVERLAP", "50"))

# Default top-k for retrieval
DEFAULT_TOP_K: int = int(os.environ.get("DEFAULT_TOP_K", "5"))

# Default batch size for embeddings
DEFAULT_BATCH_SIZE: int = int(os.environ.get("DEFAULT_BATCH_SIZE", "32"))

# Cache paths
DEFAULT_EMBEDDING_CACHE_PATH: str = os.environ.get(
    "EMBEDDING_CACHE_PATH", 
    "./RAG/.embedding_cache"
)
DEFAULT_VECTOR_STORE_PATH: str = os.environ.get(
    "VECTOR_STORE_PATH",
    "./RAG/.vector_store"
)

# =============================================================================
# OAuth Configuration
# =============================================================================

OAUTH_REDIRECT_URI: str = os.environ.get("OAUTH_REDIRECT_URI", "http://localhost:8080/callback")

# =============================================================================
# API Configuration
# =============================================================================

# Exa AI (web search)
EXA_API_URL: str = os.environ.get("EXA_API_URL", "https://mcp.exa.ai/mcp")
EXA_DEFAULT_NUM_RESULTS: int = int(os.environ.get("EXA_DEFAULT_NUM_RESULTS", "5"))
EXA_MAX_NUM_RESULTS: int = int(os.environ.get("EXA_MAX_NUM_RESULTS", "20"))

# Code search
CODESEARCH_DEFAULT_TOKENS: int = int(os.environ.get("CODESEARCH_DEFAULT_TOKENS", "5000"))
CODESEARCH_MIN_TOKENS: int = int(os.environ.get("CODESEARCH_MIN_TOKENS", "1000"))
CODESEARCH_MAX_TOKENS: int = int(os.environ.get("CODESEARCH_MAX_TOKENS", "10000"))

# =============================================================================
# Web Fetch Configuration
# =============================================================================

MAX_RESPONSE_SIZE: int = int(os.environ.get("MAX_RESPONSE_SIZE", str(5 * 1024 * 1024)))  # 5MB
WEBFETCH_DEFAULT_TIMEOUT: float = float(os.environ.get("WEBFETCH_DEFAULT_TIMEOUT", "30.0"))
WEBFETCH_MAX_TIMEOUT: float = float(os.environ.get("WEBFETCH_MAX_TIMEOUT", "120.0"))

# =============================================================================
# Server Configuration
# =============================================================================

DEFAULT_SERVER_HOST: str = os.environ.get("DEFAULT_SERVER_HOST", "127.0.0.1")
DEFAULT_SERVER_PORT: int = int(os.environ.get("DEFAULT_SERVER_PORT", "8080"))
DEFAULT_SERVER_TIMEOUT: int = int(os.environ.get("DEFAULT_SERVER_TIMEOUT", "300"))

# =============================================================================
# Editor Configuration
# =============================================================================

DEFAULT_EDITOR: str = os.environ.get("EDITOR", "nano")

# =============================================================================
# Community RAG Configuration
# =============================================================================

DEFAULT_COMMUNITY_REPO: str = os.environ.get(
    "DEFAULT_COMMUNITY_REPO", 
    "RTPro256/opencode_4py"
)
GITHUB_API_BASE: str = os.environ.get("GITHUB_API_BASE", "https://api.github.com")

# =============================================================================
# VRAM/Routing Configuration
# =============================================================================

VRAM_THRESHOLD_PERCENT: float = float(os.environ.get("VRAM_THRESHOLD_PERCENT", "90.0"))
ROUTING_CACHE_MAX_SIZE: int = int(os.environ.get("ROUTING_CACHE_MAX_SIZE", "100"))
ROUTING_CACHE_TTL: int = int(os.environ.get("ROUTING_CACHE_TTL", "3600"))
ROUTING_PROFILING_TIMEOUT: int = int(os.environ.get("ROUTING_PROFILING_TIMEOUT", "90"))

# =============================================================================
# Subagent Configuration
# =============================================================================

DEFAULT_MAX_ROUNDS: int = int(os.environ.get("DEFAULT_MAX_ROUNDS", "10"))
DEFAULT_SUBAGENT_TIMEOUT: int = int(os.environ.get("DEFAULT_SUBAGENT_TIMEOUT", "300"))
DEFAULT_MAX_RETRIES: int = int(os.environ.get("DEFAULT_MAX_RETRIES", "3"))

# =============================================================================
# YouTube Chunking Configuration
# =============================================================================

YOUTUBE_CHUNK_SIZE: int = int(os.environ.get("YOUTUBE_CHUNK_SIZE", "10"))
YOUTUBE_TARGET_DURATION: float = float(os.environ.get("YOUTUBE_TARGET_DURATION", "30.0"))
YOUTUBE_MIN_CHUNK_SIZE: int = int(os.environ.get("YOUTUBE_MIN_CHUNK_SIZE", "1"))
YOUTUBE_MAX_CHUNK_SIZE: int = int(os.environ.get("YOUTUBE_MAX_CHUNK_SIZE", "20"))

# =============================================================================
# Skill Library Configuration
# =============================================================================

DEFAULT_VAULT_DIR: Path = Path(os.environ.get("SKILL_VAULT_DIR", "~/.opencode-skill-libraries"))

# =============================================================================
# Fine-tuning Configuration (Defaults)
# =============================================================================

DEFAULT_FINETUNE_RANK: int = int(os.environ.get("DEFAULT_FINETUNE_RANK", "16"))
DEFAULT_FINETUNE_LORA_ALPHA: int = int(os.environ.get("DEFAULT_FINETUNE_LORA_ALPHA", "16"))
DEFAULT_FINETUNE_LEARNING_RATE: float = float(os.environ.get("DEFAULT_FINETUNE_LEARNING_RATE", "2e-4"))
DEFAULT_FINETUNE_CONTEXT_LENGTH: int = int(os.environ.get("DEFAULT_FINETUNE_CONTEXT_LENGTH", "2048"))
