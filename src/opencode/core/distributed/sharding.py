"""
Model Sharding.

Converts a PyTorch model into "shards" — smaller pieces saved as separate files.
Each shard holds a slice of the model's layers, making it easy to load only
what you need, or spread the model across different devices.

Integrated from aimodel_shard project.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

import torch
import torch.nn as nn

logger = logging.getLogger(__name__)


def split_model_into_shards(
    model: nn.Module,
    num_shards: int,
    output_dir: str = "shards",
) -> Dict:
    """
    Splits a model's layers evenly into `num_shards` pieces.
    Saves each shard as a .pt file plus a manifest.json describing them.

    Args:
        model: Any PyTorch nn.Module (your AI model).
        num_shards: How many pieces to split it into.
        output_dir: Folder where shard files will be saved.

    Returns:
        A dict with info about all the shards (also saved as manifest.json).
    """
    os.makedirs(output_dir, exist_ok=True)

    # Get all named layers as a flat list
    all_layers = list(model.named_children())

    if len(all_layers) == 0:
        raise ValueError(
            "Model has no child modules to shard. "
            "Make sure your model uses nn.Sequential or named submodules."
        )

    if num_shards > len(all_layers):
        logger.warning(
            f"Requested {num_shards} shards but model only has "
            f"{len(all_layers)} layers. Using {len(all_layers)} shards instead."
        )
        num_shards = len(all_layers)

    # Divide layers as evenly as possible among shards
    chunk_size = len(all_layers) // num_shards
    remainder = len(all_layers) % num_shards

    manifest = {
        "model_class": type(model).__name__,
        "total_layers": len(all_layers),
        "num_shards": num_shards,
        "shards": [],
    }

    layer_index = 0
    for shard_id in range(num_shards):
        # Give the first `remainder` shards one extra layer
        shard_size = chunk_size + (1 if shard_id < remainder else 0)
        shard_layers = all_layers[layer_index: layer_index + shard_size]
        layer_index += shard_size

        # Build a mini Sequential model for this shard
        shard_module = nn.Sequential()
        layer_names = []
        for name, layer in shard_layers:
            shard_module.add_module(name, layer)
            layer_names.append(name)

        # Save the shard weights
        shard_filename = f"shard_{shard_id:03d}.pt"
        shard_path = os.path.join(output_dir, shard_filename)
        torch.save(shard_module.state_dict(), shard_path)

        shard_info = {
            "shard_id": shard_id,
            "filename": shard_filename,
            "layer_names": layer_names,
            "num_layers": len(layer_names),
            "file_size_bytes": os.path.getsize(shard_path),
        }
        manifest["shards"].append(shard_info)

        logger.info(
            f"Saved shard {shard_id} -> {shard_filename} "
            f"({len(layer_names)} layers, {shard_info['file_size_bytes'] / 1024:.1f} KB)"
        )

    # Save manifest
    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Manifest saved to {manifest_path}")
    logger.info(f"Created {num_shards} shards in '{output_dir}/'")
    return manifest


def get_shard_info(output_dir: str = "shards") -> Dict:
    """
    Reads the manifest.json from a shards folder and returns its contents.
    Useful for inspecting shards before loading them.

    Args:
        output_dir: Directory containing shard files and manifest.json.

    Returns:
        Manifest dictionary with shard information.

    Raises:
        FileNotFoundError: If manifest.json doesn't exist.
    """
    manifest_path = os.path.join(output_dir, "manifest.json")
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(
            f"No manifest.json found in '{output_dir}'. "
            "Did you run split_model_into_shards() first?"
        )
    with open(manifest_path) as f:
        return json.load(f)


def print_shard_summary(output_dir: str = "shards") -> None:
    """
    Prints a human-readable summary of saved shards.

    Args:
        output_dir: Directory containing shard files.
    """
    info = get_shard_info(output_dir)
    total_kb = sum(s["file_size_bytes"] for s in info["shards"]) / 1024
    
    print(f"\n{'=' * 50}")
    print(f"  Model : {info['model_class']}")
    print(f"  Shards: {info['num_shards']}")
    print(f"  Layers: {info['total_layers']} total")
    print(f"  Size  : {total_kb:.1f} KB across all shards")
    print(f"{'=' * 50}")
    for s in info["shards"]:
        print(
            f"  [{s['shard_id']:3d}] {s['filename']}  "
            f"layers={s['layer_names']}  "
            f"({s['file_size_bytes']/1024:.1f} KB)"
        )
    print(f"{'=' * 50}\n")


def load_sharded_model(
    model: nn.Module,
    shards_dir: str,
    device: str = "auto",
) -> "ShardedModelRunner":
    """
    Convenience function to load a sharded model for inference.

    Args:
        model: The original model architecture.
        shards_dir: Directory containing shard files.
        device: Device to load shards on ('cpu', 'cuda', 'auto').

    Returns:
        ShardedModelRunner instance.
    """
    from .runner import ShardedModelRunner
    runner = ShardedModelRunner(model, shards_dir, device=device)
    return runner
