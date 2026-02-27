"""
LLM Configuration.

Configuration classes for local LLM management.
Inspired by igllama's config.zig implementation.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class ChatTemplateType(str, Enum):
    """Supported chat templates."""
    AUTO = "auto"
    CHATML = "chatml"
    LLAMA3 = "llama3"
    MISTRAL = "mistral"
    QWEN = "qwen"
    PHI = "phi"
    GEMMA = "gemma"
    DOLPHIN = "dolphin"
    VICUNA = "vicuna"
    OPENCHAT = "openchat"
    CAUSAL_LM = "causal_lm"


class QuantizationType(str, Enum):
    """GGUF quantization types."""
    Q2_K = "q2_k"
    Q3_K_S = "q3_k_s"
    Q3_K_M = "q3_k_m"
    Q3_K_L = "q3_k_l"
    Q4_0 = "q4_0"
    Q4_1 = "q4_1"
    Q4_K_S = "q4_k_s"
    Q4_K_M = "q4_k_m"
    Q4_K_L = "q4_k_l"
    Q5_0 = "q5_0"
    Q5_1 = "q5_1"
    Q5_K_S = "q5_k_s"
    Q5_K_M = "q5_k_m"
    Q6_K = "q6_k"
    Q8_0 = "q8_0"
    F16 = "f16"
    F32 = "f32"


class GPUMode(str, Enum):
    """GPU acceleration mode."""
    NONE = "none"
    CUDA = "cuda"
    METAL = "metal"
    VULKAN = "vulkan"
    OPENCL = "opencl"


class ModelSource(str, Enum):
    """Model source location."""
    LOCAL = "local"
    HUGGINGFACE = "huggingface"
    OLLAMA = "ollama"


class SamplingConfig(BaseModel):
    """Sampling parameters for text generation."""
    
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature (higher = more creative)",
    )
    
    top_p: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling threshold",
    )
    
    top_k: int = Field(
        default=40,
        ge=1,
        description="Top-k sampling parameter",
    )
    
    repeat_penalty: float = Field(
        default=1.1,
        ge=0.0,
        description="Repetition penalty",
    )
    
    seed: Optional[int] = Field(
        default=None,
        description="Random seed for reproducibility",
    )
    
    max_tokens: int = Field(
        default=2048,
        ge=1,
        le=8192,
        description="Maximum tokens to generate",
    )
    
    stop_sequences: List[str] = Field(
        default_factory=list,
        description="Stop sequences to end generation",
    )


class ServerConfig(BaseModel):
    """API server configuration."""
    
    host: str = Field(
        default="127.0.0.1",
        description="Server host address",
    )
    
    port: int = Field(
        default=8080,
        ge=1024,
        le=65535,
        description="Server port",
    )
    
    cors_origins: List[str] = Field(
        default_factory=lambda: ["*"],
        description="CORS allowed origins",
    )
    
    max_connections: int = Field(
        default=10,
        ge=1,
        description="Maximum concurrent connections",
    )
    
    timeout: int = Field(
        default=300,
        ge=0,
        description="Request timeout in seconds",
    )


class ModelConfig(BaseModel):
    """Per-model configuration."""
    
    # Model identification
    name: str = Field(
        description="Model display name",
    )
    
    path: Path = Field(
        description="Path to GGUF model file",
    )
    
    source: ModelSource = Field(
        default=ModelSource.LOCAL,
        description="Model source location",
    )
    
    # Model overrides (null means use global default)
    gpu_layers: Optional[int] = Field(
        default=None,
        ge=0,
        description="Number of GPU layers to offload",
    )
    
    context_size: Optional[int] = Field(
        default=None,
        ge=128,
        le=128000,
        description="Context window size",
    )
    
    chat_template: Optional[ChatTemplateType] = Field(
        default=None,
        description="Chat template to use",
    )
    
    system_prompt: Optional[str] = Field(
        default=None,
        description="System prompt override",
    )
    
    # Sampling overrides
    temperature: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="Temperature override",
    )
    
    top_p: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Top-p override",
    )
    
    top_k: Optional[int] = Field(
        default=None,
        ge=1,
        description="Top-k override",
    )
    
    # Grammar file
    grammar_file: Optional[Path] = Field(
        default=None,
        description="GBNF grammar file for constrained generation",
    )


class LLMConfig(BaseModel):
    """Global LLM configuration."""
    
    # Model defaults
    default_model: Optional[str] = Field(
        default=None,
        description="Default model name",
    )
    
    models_dir: Path = Field(
        default_factory=lambda: Path.home() / ".cache" / "opencode" / "models",
        description="Directory for cached models",
    )
    
    gpu_layers: int = Field(
        default=0,
        ge=0,
        description="Default GPU layers (0 = CPU only)",
    )
    
    context_size: Optional[int] = Field(
        default=4096,
        ge=128,
        le=128000,
        description="Default context window size",
    )
    
    max_tokens: int = Field(
        default=2048,
        ge=1,
        le=8192,
        description="Default max tokens",
    )
    
    # GPU settings
    gpu_mode: GPUMode = Field(
        default=GPUMode.NONE,
        description="GPU acceleration mode",
    )
    
    # Sampling defaults
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Default temperature",
    )
    
    top_p: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Default top-p",
    )
    
    top_k: int = Field(
        default=40,
        ge=1,
        description="Default top-k",
    )
    
    repeat_penalty: float = Field(
        default=1.1,
        ge=0.0,
        description="Default repeat penalty",
    )
    
    # Chat defaults
    system_prompt: str = Field(
        default="You are a helpful assistant.",
        description="Default system prompt",
    )
    
    chat_template: ChatTemplateType = Field(
        default=ChatTemplateType.AUTO,
        description="Default chat template",
    )
    
    # Server defaults
    server: ServerConfig = Field(
        default_factory=ServerConfig,
        description="API server configuration",
    )
    
    # Model aliases (name -> path mapping)
    aliases: Dict[str, str] = Field(
        default_factory=dict,
        description="Model name aliases",
    )


class GGUFMetadata(BaseModel):
    """GGUF model file metadata."""
    
    # Model architecture
    architecture: Optional[str] = None
    model_type: Optional[str] = None
    quantization_version: Optional[int] = None
    
    # Tokenizer
    tokenizer: Optional[str] = None
    tokenizer_probs: Optional[str] = None
    vocab_size: Optional[int] = None
    
    # Context
    context_size: Optional[int] = None
    embedding_size: Optional[int] = None
    
    # Attention
    attention_head_count: Optional[int] = None
    attention_head_count_kv: Optional[int] = None
    attention_layer_norm_rms_epsilon: Optional[float] = None
    
    # Feed-forward
    feed_forward_dim: Optional[int] = None
    
    # File info
    file_size: Optional[int] = None
    quantization_type: Optional[QuantizationType] = None
    
    @classmethod
    def from_gguf_file(cls, path: Path) -> "GGUFMetadata":
        """
        Parse GGUF metadata from a model file.
        
        Note: This requires gguf-parser library.
        For now, returns a basic metadata object.
        """
        # TODO: Implement actual GGUF parsing using gguf-parser
        return cls(
            architecture="unknown",
            context_size=4096,
            vocab_size=32000,
        )
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information as dictionary."""
        return self.model_dump(exclude_none=True)
