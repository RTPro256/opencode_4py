# aimodel_shard Integration

> Integration of model sharding capabilities from aimodel_shard project

## Overview

This document describes the integration of aimodel_shard features into opencode_4py. aimodel_shard provides PyTorch model sharding capabilities for distributed inference.

## Source Project

- **Project**: aimodel_shard
- **Language**: Python
- **License**: Not specified

## Integrated Features

### Distributed Module (`src/opencode/core/distributed/`)

Created a new module for distributed computing:

| Component | File | Description |
|-----------|------|-------------|
| Sharding | `sharding.py` | Split models into shards |
| Runner | `runner.py` | Load and run sharded inference |
| Multi-GPU | `multi_gpu.py` | Distributed inference across devices |

### Usage Examples

```python
from opencode.core.distributed import (
    split_model_into_shards,
    ShardedModelRunner,
    DistributedShardRunner,
)

# Split a model into shards
manifest = split_model_into_shards(
    model=my_model,
    num_shards=4,
    output_dir="./shards",
)

# Simple mode - load all shards upfront (faster)
runner = ShardedModelRunner(
    original_model=my_model,
    shards_dir="./shards",
    memory_efficient=False,
    device="cuda",
)
output = runner(input_tensor)

# Memory-efficient mode - load shards on demand
runner = ShardedModelRunner(
    original_model=my_model,
    shards_dir="./shards",
    memory_efficient=True,  # Low RAM usage
)

# Distributed mode - use multiple GPUs
dist_runner = DistributedShardRunner(
    original_model=my_model,
    shards_dir="./shards",
    devices=None,  # Auto-detect
)
output = dist_runner(input_tensor)
```

## Three Modes

| Mode | When to use | Memory | Speed |
|------|-------------|--------|-------|
| **Simple** | Small models, plenty of RAM | Higher | Fastest |
| **Memory-efficient** | Large models, limited RAM | Lower | Slower |
| **Distributed** | Multiple GPUs or mixed hardware | Spread | Parallel |

## Architecture

### Device Detection

The module automatically detects available compute resources:

```python
from opencode.core.distributed import detect_available_devices

devices = detect_available_devices()
# Returns: ['cuda:0', 'cuda:1', 'cpu'] or similar
```

### Shard Assignment

Shards are assigned round-robin across available devices:

```python
from opencode.core.distributed import assign_shards_to_devices

assignment = assign_shards_to_devices(num_shards=4, devices=['cuda:0', 'cuda:1'])
# Returns: {0: 'cuda:0', 1: 'cuda:1', 2: 'cuda:0', 3: 'cuda:1'}
```

## Integration with Local LLM

This module complements the existing `core/llm` module for handling large models:

1. **Sharding Large Models**: Split large GGUF models into shards
2. **Multi-GPU Inference**: Distribute shards across available GPUs
3. **Memory Efficiency**: Load/unload shards on demand for limited VRAM

## Future Enhancements

1. **Integration with llm module**: Add sharding commands to local-llm CLI
2. **GGUF Support**: Native GGUF model sharding
3. **Benchmarking**: Performance comparison tools

## Reference

- Original aimodel_shard: See `merge_projects/aimodel_shard/`
