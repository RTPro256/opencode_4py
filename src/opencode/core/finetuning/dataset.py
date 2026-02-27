"""
Dataset Preparation for Fine-tuning.

Utilities for preparing and formatting datasets for fine-tuning.
Integrated from unsloth and LLM-Fine-tuning patterns.
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

from pydantic import BaseModel, Field

from .config import DatasetFormat

logger = logging.getLogger(__name__)


@dataclass
class TrainingSample:
    """A single training sample."""
    instruction: str
    input: Optional[str] = None
    output: str = ""
    system: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "instruction": self.instruction,
            "output": self.output,
        }
        if self.input:
            result["input"] = self.input
        if self.system:
            result["system"] = self.system
        return result


class DatasetFormatter(ABC):
    """Abstract base class for dataset formatters."""
    
    @abstractmethod
    def format_sample(self, sample: TrainingSample) -> str:
        """Format a single sample for training."""
        pass
    
    @abstractmethod
    def format_prompt(
        self,
        instruction: str,
        input: Optional[str] = None,
    ) -> str:
        """Format a prompt for inference."""
        pass


class AlpacaFormatter(DatasetFormatter):
    """Alpaca-style dataset formatter."""
    
    PROMPT_TEMPLATE = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{instruction}

### Input:
{input}

### Response:
{output}"""
    
    PROMPT_TEMPLATE_NO_INPUT = """Below is an instruction that describes a task. Write a response that appropriately completes the request.

### Instruction:
{instruction}

### Response:
{output}"""
    
    def format_sample(self, sample: TrainingSample) -> str:
        """Format sample in Alpaca style."""
        if sample.input:
            return self.PROMPT_TEMPLATE.format(
                instruction=sample.instruction,
                input=sample.input,
                output=sample.output,
            )
        else:
            return self.PROMPT_TEMPLATE_NO_INPUT.format(
                instruction=sample.instruction,
                output=sample.output,
            )
    
    def format_prompt(
        self,
        instruction: str,
        input: Optional[str] = None,
    ) -> str:
        """Format prompt for inference."""
        if input:
            return self.PROMPT_TEMPLATE.format(
                instruction=instruction,
                input=input,
                output="",
            )
        else:
            return self.PROMPT_TEMPLATE_NO_INPUT.format(
                instruction=instruction,
                output="",
            )


class ChatFormatter(DatasetFormatter):
    """Chat-style dataset formatter (OpenAI format)."""
    
    def __init__(
        self,
        system_prompt: Optional[str] = None,
        user_prefix: str = "<|user|>",
        assistant_prefix: str = "<|assistant|%",
        end_token: str = "<|end|>",
    ):
        """Initialize chat formatter."""
        self.system_prompt = system_prompt
        self.user_prefix = user_prefix
        self.assistant_prefix = assistant_prefix
        self.end_token = end_token
    
    def format_sample(self, sample: TrainingSample) -> str:
        """Format sample in chat style."""
        parts = []
        
        if sample.system or self.system_prompt:
            parts.append(f"<|system|>\n{sample.system or self.system_prompt}\n{self.end_token}\n")
        
        parts.append(f"{self.user_prefix}\n{sample.instruction}")
        
        if sample.input:
            parts.append(f"\n{sample.input}")
        
        parts.append(f"\n{self.end_token}\n")
        parts.append(f"{self.assistant_prefix}\n{sample.output}\n{self.end_token}")
        
        return "".join(parts)
    
    def format_prompt(
        self,
        instruction: str,
        input: Optional[str] = None,
    ) -> str:
        """Format prompt for inference."""
        parts = []
        
        if self.system_prompt:
            parts.append(f"<|system|>\n{self.system_prompt}\n{self.end_token}\n")
        
        parts.append(f"{self.user_prefix}\n{instruction}")
        
        if input:
            parts.append(f"\n{input}")
        
        parts.append(f"\n{self.end_token}\n")
        parts.append(f"{self.assistant_prefix}\n")
        
        return "".join(parts)


class InstructionFormatter(DatasetFormatter):
    """Simple instruction-output formatter."""
    
    def __init__(
        self,
        instruction_prefix: str = "### Instruction:\n",
        response_prefix: str = "### Response:\n",
    ):
        """Initialize instruction formatter."""
        self.instruction_prefix = instruction_prefix
        self.response_prefix = response_prefix
    
    def format_sample(self, sample: TrainingSample) -> str:
        """Format sample in instruction style."""
        text = f"{self.instruction_prefix}{sample.instruction}\n\n"
        
        if sample.input:
            text += f"### Input:\n{sample.input}\n\n"
        
        text += f"{self.response_prefix}{sample.output}"
        
        return text
    
    def format_prompt(
        self,
        instruction: str,
        input: Optional[str] = None,
    ) -> str:
        """Format prompt for inference."""
        text = f"{self.instruction_prefix}{instruction}\n\n"
        
        if input:
            text += f"### Input:\n{input}\n\n"
        
        text += f"{self.response_prefix}"
        
        return text


class CompletionFormatter(DatasetFormatter):
    """Completion-style formatter for text completion tasks."""
    
    def format_sample(self, sample: TrainingSample) -> str:
        """Format sample for completion."""
        if sample.input:
            return f"{sample.input}\n\n{sample.instruction}\n{sample.output}"
        return f"{sample.instruction}\n{sample.output}"
    
    def format_prompt(
        self,
        instruction: str,
        input: Optional[str] = None,
    ) -> str:
        """Format prompt for inference."""
        if input:
            return f"{input}\n\n{instruction}\n"
        return f"{instruction}\n"


class DatasetPreparer:
    """
    Prepares datasets for fine-tuning.
    
    Handles loading, formatting, and splitting datasets
    for training and validation.
    """
    
    FORMATTERS = {
        DatasetFormat.ALPACA: AlpacaFormatter,
        DatasetFormat.CHAT: ChatFormatter,
        DatasetFormat.INSTRUCTION: InstructionFormatter,
        DatasetFormat.COMPLETION: CompletionFormatter,
    }
    
    def __init__(
        self,
        format: DatasetFormat = DatasetFormat.ALPACA,
        formatter: Optional[DatasetFormatter] = None,
        **formatter_kwargs,
    ):
        """
        Initialize dataset preparer.
        
        Args:
            format: Dataset format to use
            formatter: Custom formatter instance
            **formatter_kwargs: Arguments for formatter initialization
        """
        self.format = format
        
        if formatter:
            self.formatter = formatter
        elif format in self.FORMATTERS:
            formatter_class = self.FORMATTERS[format]
            self.formatter = formatter_class(**formatter_kwargs)
        else:
            raise ValueError(f"Unknown format: {format}")
    
    def load_json(
        self,
        path: Union[str, Path],
        text_field: str = "text",
    ) -> List[Dict[str, Any]]:
        """
        Load dataset from JSON file.
        
        Args:
            path: Path to JSON file
            text_field: Field containing text (for simple formats)
            
        Returns:
            List of samples
        """
        path = Path(path)
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Handle different JSON structures
        if isinstance(data, dict):
            if "data" in data:
                data = data["data"]
            elif "samples" in data:
                data = data["samples"]
            elif "train" in data:
                data = data["train"]
        
        return data if isinstance(data, list) else [data]
    
    def load_jsonl(
        self,
        path: Union[str, Path],
    ) -> List[Dict[str, Any]]:
        """
        Load dataset from JSONL file.
        
        Args:
            path: Path to JSONL file
            
        Returns:
            List of samples
        """
        path = Path(path)
        samples = []
        
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    samples.append(json.loads(line))
        
        return samples
    
    def load_csv(
        self,
        path: Union[str, Path],
        instruction_col: str = "instruction",
        input_col: Optional[str] = "input",
        output_col: str = "output",
    ) -> List[Dict[str, Any]]:
        """
        Load dataset from CSV file.
        
        Args:
            path: Path to CSV file
            instruction_col: Column name for instructions
            input_col: Column name for inputs
            output_col: Column name for outputs
            
        Returns:
            List of samples
        """
        import csv
        
        path = Path(path)
        samples = []
        
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sample = {
                    "instruction": row.get(instruction_col, ""),
                    "output": row.get(output_col, ""),
                }
                if input_col and input_col in row:
                    sample["input"] = row[input_col]
                samples.append(sample)
        
        return samples
    
    def prepare_samples(
        self,
        data: List[Dict[str, Any]],
    ) -> List[TrainingSample]:
        """
        Convert raw data to TrainingSample objects.
        
        Args:
            data: Raw data samples
            
        Returns:
            List of TrainingSample objects
        """
        samples = []
        
        for item in data:
            # Handle different field names
            instruction = (
                item.get("instruction") or
                item.get("prompt") or
                item.get("question") or
                item.get("input", "")
            )
            
            output = (
                item.get("output") or
                item.get("response") or
                item.get("answer") or
                item.get("completion", "")
            )
            
            input_text = (
                item.get("input") if "instruction" in item else
                None
            )
            
            system = item.get("system") or item.get("system_prompt")
            
            samples.append(TrainingSample(
                instruction=instruction,
                input=input_text,
                output=output,
                system=system,
            ))
        
        return samples
    
    def format_dataset(
        self,
        samples: List[TrainingSample],
    ) -> List[str]:
        """
        Format all samples for training.
        
        Args:
            samples: Training samples
            
        Returns:
            List of formatted text strings
        """
        return [self.formatter.format_sample(s) for s in samples]
    
    def split_dataset(
        self,
        samples: List[TrainingSample],
        validation_split: float = 0.1,
        shuffle: bool = True,
        seed: int = 42,
    ) -> tuple[List[TrainingSample], List[TrainingSample]]:
        """
        Split dataset into train and validation sets.
        
        Args:
            samples: Training samples
            validation_split: Fraction for validation
            shuffle: Whether to shuffle before splitting
            seed: Random seed for reproducibility
            
        Returns:
            Tuple of (train_samples, val_samples)
        """
        import random
        
        if shuffle:
            random.seed(seed)
            samples = samples.copy()
            random.shuffle(samples)
        
        split_idx = int(len(samples) * (1 - validation_split))
        
        return samples[:split_idx], samples[split_idx:]
    
    def prepare_for_training(
        self,
        data: Union[str, Path, List[Dict[str, Any]]],
        validation_split: float = 0.1,
        **load_kwargs,
    ) -> tuple[List[str], Optional[List[str]]]:
        """
        Full pipeline to prepare data for training.
        
        Args:
            data: Path to data file or list of samples
            validation_split: Fraction for validation
            **load_kwargs: Additional arguments for loading
            
        Returns:
            Tuple of (train_texts, val_texts)
        """
        # Load data if path provided
        if isinstance(data, (str, Path)):
            path = Path(data)
            if path.suffix == ".jsonl":
                raw_data = self.load_jsonl(path)
            elif path.suffix == ".json":
                raw_data = self.load_json(path, **load_kwargs)
            elif path.suffix == ".csv":
                raw_data = self.load_csv(path, **load_kwargs)
            else:
                raise ValueError(f"Unsupported file format: {path.suffix}")
        else:
            raw_data = data
        
        # Convert to samples
        samples = self.prepare_samples(raw_data)
        
        # Split
        train_samples, val_samples = self.split_dataset(
            samples,
            validation_split=validation_split,
        )
        
        # Format
        train_texts = self.format_dataset(train_samples)
        val_texts = self.format_dataset(val_samples) if val_samples else None
        
        logger.info(
            f"Prepared {len(train_texts)} training samples, "
            f"{len(val_texts) if val_texts else 0} validation samples"
        )
        
        return train_texts, val_texts
    
    def save_dataset(
        self,
        samples: List[str],
        output_path: Union[str, Path],
        format: str = "jsonl",
    ) -> None:
        """
        Save formatted dataset to file.
        
        Args:
            samples: Formatted text samples
            output_path: Output file path
            format: Output format (jsonl or txt)
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "jsonl":
            with open(output_path, "w", encoding="utf-8") as f:
                for sample in samples:
                    json.dump({"text": sample}, f, ensure_ascii=False)
                    f.write("\n")
        else:
            with open(output_path, "w", encoding="utf-8") as f:
                for sample in samples:
                    f.write(sample)
                    f.write("\n\n")
        
        logger.info(f"Saved {len(samples)} samples to {output_path}")
