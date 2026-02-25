# Fine-tuning API Reference

> **Module**: `opencode.core.finetuning`

This module provides fine-tuning capabilities for LLMs, including LoRA/QLoRA configuration, dataset preparation, and training workflows.

---

## Overview

The fine-tuning module provides tools for preparing datasets and configuring fine-tuning runs for large language models. It integrates patterns from unsloth and LLM-Fine-tuning projects.

---

## Quick Start

```python
from opencode.core.finetuning import (
    FineTuningConfig,
    LoRAConfig,
    TrainingConfig,
    DatasetPreparer,
    AlpacaFormatter,
)

# Configure fine-tuning
config = FineTuningConfig(
    model_name="meta-llama/Llama-2-7b-hf",
    lora=LoRAConfig(r=16, lora_alpha=32),
    training=TrainingConfig(num_train_epochs=3),
)

# Prepare dataset
preparer = DatasetPreparer()
formatter = AlpacaFormatter()

# Format samples
sample = {
    "instruction": "Explain quantum computing",
    "input": "",
    "output": "Quantum computing uses quantum bits..."
}
formatted = formatter.format_sample(sample)
```

---

## Configuration Classes

### FineTuningConfig

Main configuration for fine-tuning runs.

```python
from opencode.core.finetuning import FineTuningConfig, LoRAConfig, TrainingConfig

config = FineTuningConfig(
    model_name="meta-llama/Llama-2-7b-hf",
    output_dir="./fine-tuned-model",
    lora=LoRAConfig(r=16, lora_alpha=32),
    training=TrainingConfig(num_train_epochs=3),
)
```

#### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `model_name` | str | Required | HuggingFace model name or path |
| `output_dir` | str | "./output" | Output directory for fine-tuned model |
| `lora` | LoRAConfig | LoRAConfig() | LoRA configuration |
| `training` | TrainingConfig | TrainingConfig() | Training configuration |
| `dataset_format` | DatasetFormat | ALPACA | Dataset format |
| `max_seq_length` | int | 512 | Maximum sequence length |
| `load_in_4bit` | bool | True | Load model in 4-bit quantization |
| `device_map` | str | "auto" | Device mapping strategy |

### LoRAConfig

Configuration for LoRA (Low-Rank Adaptation) fine-tuning.

```python
from opencode.core.finetuning import LoRAConfig

lora_config = LoRAConfig(
    r=16,                    # LoRA rank
    lora_alpha=32,           # LoRA alpha parameter
    lora_dropout=0.05,       # Dropout probability
    target_modules=[         # Modules to apply LoRA
        "q_proj",
        "k_proj", 
        "v_proj",
        "o_proj",
    ],
    bias="none",             # Bias type: none, all, lora_only
)
```

#### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `r` | int | 16 | LoRA rank (dimension) |
| `lora_alpha` | int | 32 | LoRA scaling parameter |
| `lora_dropout` | float | 0.05 | Dropout probability |
| `target_modules` | List[str] | ["q_proj", "v_proj"] | Modules to apply LoRA |
| `bias` | str | "none" | Bias type |
| `modules_to_save` | List[str] | None | Modules to save full weights |

### TrainingConfig

Configuration for training parameters.

```python
from opencode.core.finetuning import TrainingConfig

training_config = TrainingConfig(
    num_train_epochs=3,
    per_device_train_batch_size=4,
    per_device_eval_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    warmup_steps=100,
    logging_steps=10,
    save_steps=500,
    eval_steps=500,
)
```

#### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `num_train_epochs` | int | 3 | Number of training epochs |
| `per_device_train_batch_size` | int | 4 | Batch size per device |
| `per_device_eval_batch_size` | int | 4 | Eval batch size per device |
| `gradient_accumulation_steps` | int | 4 | Gradient accumulation steps |
| `learning_rate` | float | 2e-4 | Learning rate |
| `warmup_steps` | int | 100 | Warmup steps |
| `logging_steps` | int | 10 | Steps between logging |
| `save_steps` | int | 500 | Steps between saves |
| `eval_steps` | int | 500 | Steps between evaluations |
| `save_total_limit` | int | 3 | Maximum checkpoints to keep |
| `fp16` | bool | False | Use FP16 training |
| `bf16` | bool | True | Use BF16 training |

---

## Dataset Preparation

### DatasetPreparer

Prepares datasets for fine-tuning.

```python
from opencode.core.finetuning import DatasetPreparer

preparer = DatasetPreparer()

# Load from file
dataset = preparer.load_json("training_data.json")

# Prepare for training
prepared = preparer.prepare(
    dataset,
    formatter=AlpacaFormatter(),
    split_ratio=0.1,  # 10% for validation
)
```

### TrainingSample

Data class for a single training sample.

```python
from opencode.core.finetuning import TrainingSample

sample = TrainingSample(
    instruction="Explain machine learning",
    input="",  # Optional input context
    output="Machine learning is a subset of AI...",
    system="You are a helpful assistant.",  # Optional system prompt
)

# Convert to dict
sample_dict = sample.to_dict()
```

---

## Dataset Formatters

### DatasetFormatter (Base Class)

Abstract base class for dataset formatters.

```python
from opencode.core.finetuning import DatasetFormatter, TrainingSample

class CustomFormatter(DatasetFormatter):
    def format_sample(self, sample: TrainingSample) -> str:
        """Format a single sample for training."""
        return f"### Instruction:\n{sample.instruction}\n\n### Response:\n{sample.output}"
```

### AlpacaFormatter

Formats datasets in Alpaca style.

```python
from opencode.core.finetuning import AlpacaFormatter, TrainingSample

formatter = AlpacaFormatter()

sample = TrainingSample(
    instruction="Explain quantum computing",
    input="Focus on superposition",
    output="Quantum computing leverages superposition..."
)

formatted = formatter.format_sample(sample)
```

**Output format:**
```
### Instruction:
Explain quantum computing

### Input:
Focus on superposition

### Response:
Quantum computing leverages superposition...
```

### ChatFormatter

Formats datasets in OpenAI chat format.

```python
from opencode.core.finetuning import ChatFormatter, TrainingSample

formatter = ChatFormatter()

sample = TrainingSample(
    instruction="What is Python?",
    output="Python is a programming language..."
)

formatted = formatter.format_sample(sample)
```

**Output format:**
```json
{
  "messages": [
    {"role": "user", "content": "What is Python?"},
    {"role": "assistant", "content": "Python is a programming language..."}
  ]
}
```

### InstructionFormatter

Simple instruction-output formatter.

```python
from opencode.core.finetuning import InstructionFormatter, TrainingSample

formatter = InstructionFormatter()

sample = TrainingSample(
    instruction="Translate to French",
    output="Bonjour"
)

formatted = formatter.format_sample(sample)
```

**Output format:**
```
Instruction: Translate to French
Output: Bonjour
```

### CompletionFormatter

Formats for text completion tasks.

```python
from opencode.core.finetuning import CompletionFormatter, TrainingSample

formatter = CompletionFormatter()

sample = TrainingSample(
    instruction="The capital of France is",
    output=" Paris."
)

formatted = formatter.format_sample(sample)
```

---

## Enums

### DatasetFormat

```python
from opencode.core.finetuning import DatasetFormat

class DatasetFormat(str, Enum):
    ALPACA = "alpaca"           # Alpaca instruction format
    CHAT = "chat"               # OpenAI chat format
    INSTRUCTION = "instruction" # Simple instruction format
    COMPLETION = "completion"   # Text completion format
    SHAREGPT = "sharegpt"       # ShareGPT format
```

---

## Examples

### Complete Fine-tuning Workflow

```python
from opencode.core.finetuning import (
    FineTuningConfig,
    LoRAConfig,
    TrainingConfig,
    DatasetPreparer,
    AlpacaFormatter,
    TrainingSample,
)

# 1. Configure fine-tuning
config = FineTuningConfig(
    model_name="meta-llama/Llama-2-7b-hf",
    output_dir="./my-fine-tuned-model",
    lora=LoRAConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    ),
    training=TrainingConfig(
        num_train_epochs=3,
        per_device_train_batch_size=4,
        learning_rate=2e-4,
    ),
)

# 2. Prepare dataset
samples = [
    TrainingSample(
        instruction="What is AI?",
        output="AI stands for Artificial Intelligence..."
    ),
    TrainingSample(
        instruction="Explain machine learning",
        output="Machine learning is a subset of AI..."
    ),
]

preparer = DatasetPreparer()
formatter = AlpacaFormatter()

# Format samples
formatted_data = [formatter.format_sample(s) for s in samples]

# 3. Save for training
preparer.save_json(formatted_data, "training_data.json")

print(f"Prepared {len(formatted_data)} samples for fine-tuning")
print(f"Model: {config.model_name}")
print(f"Output: {config.output_dir}")
```

### Loading and Converting Datasets

```python
from opencode.core.finetuning import DatasetPreparer, AlpacaFormatter, ChatFormatter

preparer = DatasetPreparer()

# Load from JSON
alpaca_data = preparer.load_json("alpaca_data.json")

# Convert to chat format
chat_formatter = ChatFormatter()
alpaca_formatter = AlpacaFormatter()

converted = []
for sample in alpaca_data:
    # Parse and reformat
    training_sample = TrainingSample(
        instruction=sample["instruction"],
        input=sample.get("input", ""),
        output=sample["output"],
    )
    converted.append(chat_formatter.format_sample(training_sample))

# Save converted data
preparer.save_json(converted, "chat_data.json")
```

---

## Integration with Training Libraries

### Using with Unsloth

```python
# Note: Requires unsloth package installed
# pip install unsloth

from opencode.core.finetuning import FineTuningConfig, LoRAConfig

config = FineTuningConfig(
    model_name="unsloth/llama-3-8b-bnb-4bit",
    lora=LoRAConfig(r=16, lora_alpha=16),
    load_in_4bit=True,
)

# The config can be passed to unsloth training functions
# See unsloth documentation for training loop
```

### Using with HuggingFace TRL

```python
from opencode.core.finetuning import TrainingConfig

config = TrainingConfig(
    num_train_epochs=3,
    per_device_train_batch_size=4,
    learning_rate=2e-4,
)

# Convert to TrainingArguments
from transformers import TrainingArguments

training_args = TrainingArguments(
    output_dir="./output",
    num_train_epochs=config.num_train_epochs,
    per_device_train_batch_size=config.per_device_train_batch_size,
    learning_rate=config.learning_rate,
)
```

---

## See Also

- [RAG Methods API](rag-methods-api.md) - RAG methods reference
- [USER_ACCEPTANCE_TESTING.md](../../plans/USER_ACCEPTANCE_TESTING.md) - UAT test scenarios
- [DOCUMENTATION_PLAN.md](../../plans/DOCUMENTATION_PLAN.md) - Documentation standards

---

*Last updated: 2026-02-24*
