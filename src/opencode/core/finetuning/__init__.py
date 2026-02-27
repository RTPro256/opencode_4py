"""
Fine-tuning Module.

This module provides fine-tuning capabilities for LLMs, including:
- LoRA/QLoRA fine-tuning (from unsloth)
- Dataset preparation and formatting
- Training workflows and configuration
- Model evaluation and export

Integrated from:
- unsloth: Efficient fine-tuning library
- LLM-Fine-tuning: Training workflows
"""

from .config import FineTuningConfig, LoRAConfig, TrainingConfig, DatasetFormat
from .dataset import (
    DatasetPreparer,
    DatasetFormatter,
    AlpacaFormatter,
    ChatFormatter,
    InstructionFormatter,
    CompletionFormatter,
    TrainingSample,
)

__all__ = [
    "FineTuningConfig",
    "LoRAConfig",
    "TrainingConfig",
    "DatasetPreparer",
    "DatasetFormat",
    "DatasetFormatter",
    "AlpacaFormatter",
    "ChatFormatter",
    "InstructionFormatter",
    "CompletionFormatter",
    "TrainingSample",
]
