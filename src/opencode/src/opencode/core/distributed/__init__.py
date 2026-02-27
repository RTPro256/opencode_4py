"""
Distributed Computing Module.

Provides model sharding and distributed inference capabilities:
- Split PyTorch models into shards
- Load shards with memory-efficient mode
- Run distributed inference across multiple GPUs/CPU

Integrated from:
- aimodel_shard: AI Model Shards library
"""

from .sharding import split_model_into_shards, get_shard_info, print_shard_summary
from .runner import ShardedModelRunner
from .multi_gpu import DistributedShardRunner, detect_available_devices, assign_shards_to_devices

__all__ = [
    # Sharding
    "split_model_into_shards",
    "get_shard_info",
    "print_shard_summary",
    # Runner
    "ShardedModelRunner",
    # Multi-GPU
    "DistributedShardRunner",
    "detect_available_devices",
    "assign_shards_to_devices",
]
