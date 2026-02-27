"""
Sharded Model Runner.

Loads model shards from disk and runs data through them in sequence.
Think of it like an assembly line: each shard processes the data and
passes its output to the next shard.

Integrated from aimodel_shard project.
"""

import json
import logging
import os
from typing import List, Optional

import torch
import torch.nn as nn

logger = logging.getLogger(__name__)


class ShardedModelRunner:
    """
    Loads shards one at a time (or all at once) and runs inference.

    Memory-efficient mode: loads each shard, runs it, then unloads it
    before loading the next one. Great for large models on small machines.

    Fast mode: loads all shards into memory upfront for quicker inference.
    """

    def __init__(
        self,
        original_model: nn.Module,
        shards_dir: str = "shards",
        memory_efficient: bool = False,
        device: str = "auto",
    ):
        """
        Args:
            original_model: The same model architecture you sharded.
                            (We need it to know the layer structure.)
            shards_dir: Folder containing shard .pt files + manifest.json
            memory_efficient: If True, loads/unloads shards one at a time.
                              If False, loads everything upfront (faster).
            device: 'cpu', 'cuda', 'mps', or 'auto' (auto-detects).
        """
        self.shards_dir = shards_dir
        self.memory_efficient = memory_efficient
        self.device = self._resolve_device(device)
        self.manifest = self._load_manifest()
        self.original_model = original_model

        self._shard_modules: List[Optional[nn.Sequential]] = [
            None
        ] * self.manifest["num_shards"]

        if not memory_efficient:
            logger.info(f"Pre-loading all {self.manifest['num_shards']} shards onto {self.device}...")
            self._preload_all_shards()
        else:
            logger.info("Memory-efficient mode: shards will load on demand.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Runs input `x` through every shard in order.
        This is your main inference function.

        Args:
            x: Input tensor (e.g. an image batch or token embeddings).

        Returns:
            Output tensor after passing through all shards.
        """
        logger.info(f"Running inference through {self.manifest['num_shards']} shards...")

        for shard_id in range(self.manifest["num_shards"]):
            shard = self._get_shard(shard_id)
            shard.eval()

            with torch.no_grad():
                x = shard(x.to(self.device))

            logger.debug(f"Shard {shard_id} -> output shape: {tuple(x.shape)}")

            # If memory efficient, unload after use
            if self.memory_efficient:
                self._unload_shard(shard_id)

        logger.info("Inference complete!")
        return x

    def __call__(self, x: torch.Tensor) -> torch.Tensor:
        """Makes the runner callable like a normal model: output = runner(input)"""
        return self.forward(x)

    def load_shard(self, shard_id: int) -> nn.Sequential:
        """Manually load a single shard by its ID."""
        return self._get_shard(shard_id)

    def unload_all(self):
        """Free all shard memory."""
        for i in range(len(self._shard_modules)):
            self._unload_shard(i)
        logger.info("All shards unloaded from memory.")

    def info(self) -> None:
        """Print a summary of the loaded shards."""
        print(f"\nShardedModelRunner")
        print(f"  Device          : {self.device}")
        print(f"  Shards dir      : {self.shards_dir}")
        print(f"  Num shards      : {self.manifest['num_shards']}")
        print(f"  Memory efficient: {self.memory_efficient}")
        loaded = sum(1 for s in self._shard_modules if s is not None)
        print(f"  Shards in memory: {loaded}\n")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _resolve_device(self, device: str) -> str:
        if device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif torch.backends.mps.is_available():
                return "mps"
            else:
                return "cpu"
        return device

    def _load_manifest(self) -> dict:
        path = os.path.join(self.shards_dir, "manifest.json")
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"manifest.json not found in '{self.shards_dir}'. "
                "Run model_sharder.split_model_into_shards() first."
            )
        with open(path) as f:
            return json.load(f)

    def _build_shard_module(self, shard_id: int) -> nn.Sequential:
        """Reconstruct the nn.Sequential for a given shard from the original model."""
        shard_info = self.manifest["shards"][shard_id]
        module = nn.Sequential()
        for name in shard_info["layer_names"]:
            layer = dict(self.original_model.named_children())[name]
            module.add_module(name, layer)
        return module

    def _get_shard(self, shard_id: int) -> nn.Sequential:
        """Return a shard, loading it from disk if needed."""
        if self._shard_modules[shard_id] is None:
            self._load_shard(shard_id)
        return self._shard_modules[shard_id]

    def _load_shard(self, shard_id: int) -> None:
        shard_info = self.manifest["shards"][shard_id]
        shard_path = os.path.join(self.shards_dir, shard_info["filename"])

        module = self._build_shard_module(shard_id)
        state = torch.load(shard_path, map_location=self.device)
        module.load_state_dict(state)
        module.to(self.device)
        module.eval()

        self._shard_modules[shard_id] = module
        logger.debug(f"Loaded shard {shard_id} from {shard_info['filename']}")

    def _unload_shard(self, shard_id: int) -> None:
        self._shard_modules[shard_id] = None

    def _preload_all_shards(self) -> None:
        for shard_id in range(self.manifest["num_shards"]):
            self._load_shard(shard_id)
        logger.info("All shards loaded.")
