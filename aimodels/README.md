# Local AI Models Directory

This directory stores sharded local AI models for use with opencode_4py's distributed inference system.

## Directory Structure

```
aimodels/
├── model_registry.json     # Index of all available models
├── {model_name}/
│   ├── manifest.json       # Shard metadata
│   ├── shard_000.pt       # Layer shards
│   ├── shard_001.pt
│   └── ...
└── ...
```

## Usage

### Sharding a Model

```bash
# Download and shard a model
opencode local-llm pull TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF
opencode local-llm shard --model tinyllama --num-shards 4
```

### Running Distributed Inference

```python
from opencode.core.distributed import DistributedShardRunner

runner = DistributedShardRunner(
    original_model=model,
    shards_dir="aimodels/tinyllama",
)
output = runner(input_tensor)
```

## Model Registry

The `model_registry.json` tracks all available sharded models:

```json
{
  "models": [
    {
      "name": "tinyllama",
      "path": "tinyllama",
      "num_shards": 4,
      " quantization": "Q4_K_M",
      "vram_requirement": "4GB",
      "created": "2026-02-27"
    }
  ]
}
```

## Requirements

- Models must be in GGUF format for GGUF-based sharding
- PyTorch models can be sharded directly using `split_model_into_shards()`
- Minimum 2GB free disk space per shard
