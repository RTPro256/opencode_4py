"""
Multi-GPU Distributed Runner.

Automatically detects available compute resources (CPU cores, GPUs)
and distributes shards across them for parallel processing.

Integrated from aimodel_shard project.
"""

import json
import logging
import os
import time
from typing import Dict, List, Optional

import torch
import torch.nn as nn

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Resource Detection
# ──────────────────────────────────────────────


def detect_available_devices() -> List[str]:
    """
    Returns a list of all usable compute devices on this machine.
    Example: ['cuda:0', 'cuda:1', 'cpu']
    """
    devices = []

    # Check for NVIDIA GPUs
    if torch.cuda.is_available():
        for i in range(torch.cuda.device_count()):
            devices.append(f"cuda:{i}")
            props = torch.cuda.get_device_properties(i)
            logger.info(
                f"GPU {i}: {props.name} ({props.total_memory // 1024**2} MB VRAM)"
            )

    # Check for Apple Silicon GPU (MPS)
    if torch.backends.mps.is_available():
        devices.append("mps")
        logger.info("Apple Silicon GPU (MPS) available")

    # Always include CPU as a fallback
    import multiprocessing
    cpu_cores = multiprocessing.cpu_count() or 1
    devices.append("cpu")
    logger.info(f"CPU available ({cpu_cores} cores)")

    return devices


def assign_shards_to_devices(
    num_shards: int,
    devices: List[str],
) -> Dict[int, str]:
    """
    Maps each shard ID to a device, spreading them as evenly as possible.
    GPUs get priority (shards fill GPUs first, then overflow to CPU).

    Args:
        num_shards: Number of shards to assign.
        devices: List of available devices.

    Returns:
        Dictionary mapping shard_id to device string.
        e.g., {0: 'cuda:0', 1: 'cuda:0', 2: 'cuda:1', 3: 'cpu'}
    """
    assignment = {}
    for shard_id in range(num_shards):
        device = devices[shard_id % len(devices)]
        assignment[shard_id] = device
    return assignment


# ──────────────────────────────────────────────
# Distributed Runner
# ──────────────────────────────────────────────


class DistributedShardRunner:
    """
    Loads shards onto different devices and runs inference
    in a pipelined fashion across all available hardware.

    Pipeline mode (default):
        Data flows shard-by-shard like an assembly line.
        Each shard runs on its assigned device, passing its output
        to the next shard's device automatically.

    Useful when:
        - Your model is too big to fit on a single GPU
        - You have multiple GPUs and want to use all of them
        - You want to mix CPU + GPU
    """

    def __init__(
        self,
        original_model: nn.Module,
        shards_dir: str = "shards",
        devices: Optional[List[str]] = None,
    ):
        """
        Args:
            original_model: The model architecture to shard.
            shards_dir: Folder containing saved shards + manifest.json.
            devices: List of devices to use. None = auto-detect all.
        """
        self.shards_dir = shards_dir
        self.original_model = original_model
        self.manifest = self._load_manifest()
        num_shards = self.manifest["num_shards"]

        logger.info("Detecting available compute resources...")
        self.devices = devices if devices else detect_available_devices()

        logger.info(f"Assigning {num_shards} shards to {len(self.devices)} device(s)...")
        self.assignment = assign_shards_to_devices(num_shards, self.devices)
        for shard_id, device in self.assignment.items():
            logger.debug(f"Shard {shard_id} -> {device}")

        logger.info("Loading shards onto assigned devices...")
        self.shards = self._load_all_shards()
        logger.info("All shards loaded and ready.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Run input through all shards in order across multiple devices.
        Data moves between devices automatically as needed.

        Args:
            x: Input tensor.

        Returns:
            Final output tensor (on CPU).
        """
        logger.info(
            f"Running distributed inference ({len(self.shards)} shards, "
            f"{len(self.devices)} device(s))..."
        )
        start = time.perf_counter()

        for shard_id, shard_module in enumerate(self.shards):
            device = self.assignment[shard_id]

            # Move tensor to this shard's device
            x = x.to(device)

            with torch.no_grad():
                x = shard_module(x)

            logger.debug(f"Shard {shard_id} [{device}] -> shape {tuple(x.shape)}")

        elapsed = time.perf_counter() - start
        logger.info(f"Done in {elapsed:.3f}s | Output on: {x.device}")

        # Return result on CPU for easy use
        return x.cpu()

    def __call__(self, x: torch.Tensor) -> torch.Tensor:
        return self.forward(x)

    def benchmark(self, x: torch.Tensor, runs: int = 5) -> Dict:
        """
        Runs inference multiple times and reports timing stats.
        Useful for comparing different shard/device configurations.
        """
        logger.info(f"Benchmarking ({runs} runs)...")
        times = []
        for i in range(runs):
            start = time.perf_counter()
            _ = self.forward(x.clone())
            times.append(time.perf_counter() - start)

        stats = {
            "runs": runs,
            "mean_s": sum(times) / len(times),
            "min_s": min(times),
            "max_s": max(times),
            "times": times,
        }
        logger.info(f"Mean: {stats['mean_s']*1000:.1f}ms")
        logger.info(f"Min: {stats['min_s']*1000:.1f}ms")
        logger.info(f"Max: {stats['max_s']*1000:.1f}ms")
        return stats

    def device_summary(self) -> None:
        """Print which shards are on which devices."""
        summary: Dict[str, List[int]] = {}
        for shard_id, device in self.assignment.items():
            summary.setdefault(device, []).append(shard_id)
        print("\nDevice -> Shard Assignment:")
        for device, shard_ids in summary.items():
            print(f"  {device:12s}: shards {shard_ids}")
        print()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_manifest(self) -> dict:
        path = os.path.join(self.shards_dir, "manifest.json")
        with open(path) as f:
            return json.load(f)

    def _build_shard_module(self, shard_id: int) -> nn.Sequential:
        shard_info = self.manifest["shards"][shard_id]
        module = nn.Sequential()
        for name in shard_info["layer_names"]:
            layer = dict(self.original_model.named_children())[name]
            module.add_module(name, layer)
        return module

    def _load_all_shards(self) -> List[nn.Sequential]:
        shard_modules = []
        for shard_id in range(self.manifest["num_shards"]):
            info = self.manifest["shards"][shard_id]
            path = os.path.join(self.shards_dir, info["filename"])
            device = self.assignment[shard_id]
            module = self._build_shard_module(shard_id)
            state_dict = torch.load(path, map_location=device)
            module.load_state_dict(state_dict)
            module.to(device)
            module.eval()
            shard_modules.append(module)
            logger.debug(f"Shard {shard_id} -> {device}")
        return shard_modules
