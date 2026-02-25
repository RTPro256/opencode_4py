"""
Fine-tuning Configuration.

Configuration classes for fine-tuning workflows.
Integrated from unsloth and LLM-Fine-tuning patterns.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class FineTuningMethod(str, Enum):
    """Available fine-tuning methods."""
    LORA = "lora"           # Low-Rank Adaptation
    QLORA = "qlora"         # Quantized LoRA
    FULL = "full"           # Full fine-tuning
    PREFIX = "prefix"       # Prefix tuning
    ADAPTER = "adapter"     # Adapter-based


class PrecisionType(str, Enum):
    """Precision types for training."""
    FP32 = "fp32"
    FP16 = "fp16"
    BF16 = "bf16"
    INT8 = "int8"
    INT4 = "int4"


class DatasetFormat(str, Enum):
    """Supported dataset formats."""
    ALPACA = "alpaca"
    SHAREGPT = "sharegpt"
    INSTRUCTION = "instruction"
    COMPLETION = "completion"
    CHAT = "chat"
    CUSTOM = "custom"


class LoRAConfig(BaseModel):
    """Configuration for LoRA fine-tuning."""
    
    # LoRA rank (r)
    r: int = Field(
        default=16,
        ge=1,
        le=256,
        description="LoRA rank - higher values = more parameters",
    )
    
    # LoRA alpha (scaling)
    lora_alpha: int = Field(
        default=16,
        ge=1,
        description="LoRA scaling factor (typically same as r)",
    )
    
    # Dropout
    lora_dropout: float = Field(
        default=0.0,
        ge=0.0,
        le=0.5,
        description="LoRA dropout probability",
    )
    
    # Target modules
    target_modules: List[str] = Field(
        default_factory=lambda: ["q_proj", "k_proj", "v_proj", "o_proj"],
        description="Modules to apply LoRA to",
    )
    
    # Bias handling
    bias: str = Field(
        default="none",
        description="Bias type: none, all, or lora_only",
    )
    
    # Task type
    task_type: str = Field(
        default="CAUSAL_LM",
        description="Task type for LoRA",
    )
    
    # Fan in fan out
    fan_in_fan_out: bool = Field(
        default=False,
        description="Set True for Conv layers",
    )
    
    # Modules to save
    modules_to_save: Optional[List[str]] = Field(
        default=None,
        description="Modules to save in addition to LoRA",
    )
    
    class Config:
        use_enum_values = True


class TrainingConfig(BaseModel):
    """Configuration for training process."""
    
    # Output
    output_dir: str = Field(
        default="./finetuned_model",
        description="Directory to save model and checkpoints",
    )
    
    # Training duration
    num_train_epochs: int = Field(
        default=3,
        ge=1,
        le=100,
        description="Number of training epochs",
    )
    
    max_steps: int = Field(
        default=-1,
        description="Maximum training steps (-1 for epoch-based)",
    )
    
    # Batch size
    per_device_train_batch_size: int = Field(
        default=4,
        ge=1,
        le=128,
        description="Batch size per device",
    )
    
    per_device_eval_batch_size: int = Field(
        default=4,
        ge=1,
        le=128,
        description="Evaluation batch size per device",
    )
    
    gradient_accumulation_steps: int = Field(
        default=4,
        ge=1,
        le=64,
        description="Gradient accumulation steps",
    )
    
    # Learning rate
    learning_rate: float = Field(
        default=2e-4,
        ge=1e-7,
        le=1e-1,
        description="Learning rate",
    )
    
    weight_decay: float = Field(
        default=0.01,
        ge=0.0,
        le=0.1,
        description="Weight decay for regularization",
    )
    
    # Learning rate scheduler
    lr_scheduler_type: str = Field(
        default="cosine",
        description="Learning rate scheduler type",
    )
    
    warmup_ratio: float = Field(
        default=0.03,
        ge=0.0,
        le=0.5,
        description="Warmup ratio",
    )
    
    warmup_steps: int = Field(
        default=0,
        ge=0,
        description="Number of warmup steps",
    )
    
    # Precision
    fp16: bool = Field(
        default=False,
        description="Use FP16 precision",
    )
    
    bf16: bool = Field(
        default=True,
        description="Use BF16 precision (recommended for newer GPUs)",
    )
    
    # Gradient settings
    max_grad_norm: float = Field(
        default=1.0,
        ge=0.0,
        le=10.0,
        description="Maximum gradient norm for clipping",
    )
    
    # Logging
    logging_steps: int = Field(
        default=10,
        ge=1,
        description="Steps between logging",
    )
    
    save_steps: int = Field(
        default=500,
        ge=1,
        description="Steps between saves",
    )
    
    eval_steps: int = Field(
        default=500,
        ge=1,
        description="Steps between evaluations",
    )
    
    save_total_limit: int = Field(
        default=3,
        ge=1,
        description="Maximum number of checkpoints to keep",
    )
    
    # Evaluation
    evaluation_strategy: str = Field(
        default="steps",
        description="Evaluation strategy: no, steps, or epoch",
    )
    
    # Optimizer
    optim: str = Field(
        default="adamw_torch",
        description="Optimizer type",
    )
    
    # Sequence length
    max_seq_length: int = Field(
        default=2048,
        ge=128,
        le=32768,
        description="Maximum sequence length",
    )
    
    # Packing
    packing: bool = Field(
        default=False,
        description="Pack multiple sequences into one",
    )
    
    # Gradient checkpointing
    gradient_checkpointing: bool = Field(
        default=True,
        description="Use gradient checkpointing to save memory",
    )
    
    class Config:
        use_enum_values = True


class FineTuningConfig(BaseModel):
    """Complete configuration for fine-tuning."""
    
    # Model settings
    base_model: str = Field(
        default="unsloth/llama-3-8b-bnb-4bit",
        description="Base model to fine-tune",
    )
    
    model_name: str = Field(
        default="my_finetuned_model",
        description="Name for the fine-tuned model",
    )
    
    # Method
    method: FineTuningMethod = Field(
        default=FineTuningMethod.QLORA,
        description="Fine-tuning method to use",
    )
    
    # Precision
    precision: PrecisionType = Field(
        default=PrecisionType.BF16,
        description="Precision for training",
    )
    
    # Quantization (for QLoRA)
    load_in_4bit: bool = Field(
        default=True,
        description="Load model in 4-bit quantization",
    )
    
    bnb_4bit_compute_dtype: str = Field(
        default="bfloat16",
        description="Compute dtype for 4-bit quantization",
    )
    
    bnb_4bit_quant_type: str = Field(
        default="nf4",
        description="Quantization type: nf4 or fp4",
    )
    
    bnb_4bit_use_double_quant: bool = Field(
        default=True,
        description="Use double quantization",
    )
    
    # LoRA config
    lora_config: LoRAConfig = Field(
        default_factory=LoRAConfig,
        description="LoRA configuration",
    )
    
    # Training config
    training_config: TrainingConfig = Field(
        default_factory=TrainingConfig,
        description="Training configuration",
    )
    
    # Dataset settings
    dataset_path: Optional[str] = Field(
        default=None,
        description="Path to training dataset",
    )
    
    dataset_format: DatasetFormat = Field(
        default=DatasetFormat.ALPACA,
        description="Format of the dataset",
    )
    
    dataset_text_field: str = Field(
        default="text",
        description="Text field name in dataset",
    )
    
    # Validation
    validation_split: float = Field(
        default=0.1,
        ge=0.0,
        le=0.5,
        description="Fraction of data for validation",
    )
    
    # Export settings
    export_to_gguf: bool = Field(
        default=False,
        description="Export model to GGUF format",
    )
    
    export_to_ollama: bool = Field(
        default=False,
        description="Export model for Ollama",
    )
    
    push_to_hub: bool = Field(
        default=False,
        description="Push model to Hugging Face Hub",
    )
    
    hub_model_id: Optional[str] = Field(
        default=None,
        description="Model ID for Hugging Face Hub",
    )
    
    class Config:
        use_enum_values = True
    
    def to_training_arguments(self) -> Dict[str, Any]:
        """Convert to training arguments dict for transformers."""
        tc = self.training_config
        return {
            "output_dir": tc.output_dir,
            "num_train_epochs": tc.num_train_epochs,
            "max_steps": tc.max_steps,
            "per_device_train_batch_size": tc.per_device_train_batch_size,
            "per_device_eval_batch_size": tc.per_device_eval_batch_size,
            "gradient_accumulation_steps": tc.gradient_accumulation_steps,
            "learning_rate": tc.learning_rate,
            "weight_decay": tc.weight_decay,
            "lr_scheduler_type": tc.lr_scheduler_type,
            "warmup_ratio": tc.warmup_ratio,
            "warmup_steps": tc.warmup_steps,
            "fp16": tc.fp16,
            "bf16": tc.bf16,
            "max_grad_norm": tc.max_grad_norm,
            "logging_steps": tc.logging_steps,
            "save_steps": tc.save_steps,
            "eval_steps": tc.eval_steps,
            "save_total_limit": tc.save_total_limit,
            "evaluation_strategy": tc.evaluation_strategy,
            "optim": tc.optim,
            "max_seq_length": tc.max_seq_length,
            "packing": tc.packing,
            "gradient_checkpointing": tc.gradient_checkpointing,
        }
