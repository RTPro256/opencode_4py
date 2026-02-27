"""GPU management for multi-model execution.

This module provides GPU allocation and management for running multiple
models across multiple GPUs with VRAM-aware scheduling.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
from enum import Enum
import asyncio

from opencode.router.vram_monitor import VRAMMonitor, VRAMStatus, GPUInfo


class GPUAllocationStrategy(str, Enum):
    """Strategy for allocating GPUs to models."""
    AUTO = "auto"              # Automatically select best available GPU
    ROUND_ROBIN = "round_robin"  # Distribute across GPUs evenly
    PACK = "pack"              # Fill GPUs before using next one
    SPREAD = "spread"          # Spread models across all GPUs
    MANUAL = "manual"          # Use explicitly configured GPU IDs


@dataclass
class GPUAllocation:
    """Represents a GPU allocation for a model."""
    gpu_id: int
    model_id: str
    vram_required_gb: float
    exclusive: bool = True  # If True, GPU is reserved exclusively
    created_at: float = 0.0  # Timestamp of allocation


@dataclass
class GPUManagerConfig:
    """Configuration for GPU manager."""
    strategy: GPUAllocationStrategy = GPUAllocationStrategy.AUTO
    vram_threshold_percent: float = 85.0  # Don't allocate if GPU above this
    allow_shared_gpu: bool = True  # Allow multiple models on same GPU
    auto_unload: bool = True  # Auto-unload models when VRAM is low
    reserved_vram_gb: float = 1.0  # Reserve this much VRAM for system


# Global GPU manager instance
_gpu_manager: Optional["GPUManager"] = None


def get_gpu_manager() -> "GPUManager":
    """Get or create the global GPU manager instance."""
    global _gpu_manager
    if _gpu_manager is None:
        _gpu_manager = GPUManager()
    return _gpu_manager


def reset_gpu_manager() -> None:
    """Reset the global GPU manager (for testing)."""
    global _gpu_manager
    _gpu_manager = None


class GPUManager:
    """
    Manages GPU allocations for multi-model execution.
    
    Features:
    - GPU affinity: Assign specific models to specific GPUs
    - VRAM monitoring: Track VRAM usage per GPU
    - Load balancing: Distribute models across available GPUs
    - Auto-unload: Unload models when VRAM is low
    
    Usage:
        manager = get_gpu_manager()
        
        # Allocate GPU for a model
        gpu_id = await manager.allocate_gpu(
            model_id="llama3.2:70b",
            vram_required_gb=40.0,
            preferred_gpu_id=0,
        )
        
        # Get current status
        status = await manager.get_status()
        
        # Release when done
        await manager.release_gpu("llama3.2:70b")
    """
    
    def __init__(self, config: Optional[GPUManagerConfig] = None):
        self.config = config or GPUManagerConfig()
        self._vram_monitor = VRAMMonitor()
        self._allocations: Dict[str, GPUAllocation] = {}  # model_id -> allocation
        self._gpu_models: Dict[int, Set[str]] = {}  # gpu_id -> set of model_ids
        self._lock = asyncio.Lock()
    
    async def get_available_gpus(self) -> List[GPUInfo]:
        """Get list of available GPUs with current status."""
        status = await self._vram_monitor.get_status()
        return status.gpus
    
    async def allocate_gpu(
        self,
        model_id: str,
        vram_required_gb: Optional[float] = None,
        preferred_gpu_id: Optional[int] = None,
        exclusive: bool = False,
    ) -> Optional[int]:
        """
        Allocate a GPU for a model.
        
        Args:
            model_id: Unique identifier for the model
            vram_required_gb: Estimated VRAM requirement in GB
            preferred_gpu_id: Preferred GPU ID (if strategy allows)
            exclusive: If True, reserve GPU exclusively for this model
            
        Returns:
            Allocated GPU ID, or None if no GPU available
        """
        async with self._lock:
            # Check if already allocated
            if model_id in self._allocations:
                return self._allocations[model_id].gpu_id
            
            status = await self._vram_monitor.get_status()
            
            if not status.gpus:
                return None
            
            # Handle manual strategy with preferred GPU
            if preferred_gpu_id is not None:
                gpu = status.get_gpu(preferred_gpu_id)
                if gpu and self._can_allocate(gpu, vram_required_gb, exclusive):
                    self._record_allocation(model_id, preferred_gpu_id, vram_required_gb, exclusive)
                    return preferred_gpu_id
                # Fall through to strategy selection if preferred not available
            
            # Use strategy to select GPU
            gpu_id = await self._select_gpu(status, vram_required_gb, exclusive)
            if gpu_id is not None:
                self._record_allocation(model_id, gpu_id, vram_required_gb, exclusive)
            return gpu_id
    
    async def release_gpu(self, model_id: str) -> bool:
        """
        Release GPU allocation for a model.
        
        Args:
            model_id: The model ID to release
            
        Returns:
            True if allocation was released, False if not found
        """
        async with self._lock:
            if model_id not in self._allocations:
                return False
            
            allocation = self._allocations.pop(model_id)
            if allocation.gpu_id in self._gpu_models:
                self._gpu_models[allocation.gpu_id].discard(model_id)
                # Clean up empty sets
                if not self._gpu_models[allocation.gpu_id]:
                    del self._gpu_models[allocation.gpu_id]
            
            return True
    
    async def release_all(self) -> int:
        """
        Release all GPU allocations.
        
        Returns:
            Number of allocations released
        """
        async with self._lock:
            count = len(self._allocations)
            self._allocations.clear()
            self._gpu_models.clear()
            return count
    
    async def get_gpu_for_model(self, model_id: str) -> Optional[int]:
        """Get the GPU ID allocated to a model."""
        allocation = self._allocations.get(model_id)
        return allocation.gpu_id if allocation else None
    
    async def get_models_on_gpu(self, gpu_id: int) -> List[str]:
        """Get list of model IDs allocated to a specific GPU."""
        return list(self._gpu_models.get(gpu_id, set()))
    
    def _can_allocate(
        self,
        gpu: GPUInfo,
        vram_required_gb: Optional[float],
        exclusive: bool = False,
    ) -> bool:
        """Check if a GPU can accommodate the allocation."""
        # Check if there's an existing exclusive allocation on this GPU
        if gpu.index in self._gpu_models and self._gpu_models[gpu.index]:
            # Check if any existing allocation is exclusive
            for model_id in self._gpu_models[gpu.index]:
                existing_alloc = self._allocations.get(model_id)
                if existing_alloc and existing_alloc.exclusive:
                    return False
        
        # Check exclusive allocation
        if exclusive and gpu.index in self._gpu_models:
            if self._gpu_models[gpu.index]:
                return False
        
        # Check if shared GPUs are allowed
        if not self.config.allow_shared_gpu and not exclusive:
            if gpu.index in self._gpu_models and self._gpu_models[gpu.index]:
                return False
        
        # Check VRAM threshold
        if gpu.total_memory_mb > 0:
            usage_percent = (gpu.used_memory_mb / gpu.total_memory_mb) * 100
            if usage_percent >= self.config.vram_threshold_percent:
                return False
        
        # Check if enough VRAM
        if vram_required_gb is not None:
            free_gb = gpu.free_memory_mb / 1024
            required_gb = vram_required_gb + self.config.reserved_vram_gb
            if free_gb < required_gb:
                return False
        
        return True
    
    async def _select_gpu(
        self,
        status: VRAMStatus,
        vram_required_gb: Optional[float],
        exclusive: bool = False,
    ) -> Optional[int]:
        """Select best GPU based on strategy."""
        available_gpus = [
            gpu for gpu in status.gpus
            if self._can_allocate(gpu, vram_required_gb, exclusive)
        ]
        
        if not available_gpus:
            return None
        
        if self.config.strategy == GPUAllocationStrategy.AUTO:
            # Select GPU with most free memory
            return max(available_gpus, key=lambda g: g.free_memory_mb).index
        
        elif self.config.strategy == GPUAllocationStrategy.ROUND_ROBIN:
            # Simple round-robin based on number of models per GPU
            gpu_counts = {
                gpu.index: len(self._gpu_models.get(gpu.index, set()))
                for gpu in available_gpus
            }
            min_count = min(gpu_counts.values())
            # Among GPUs with minimum count, pick one with most free memory
            candidates = [g for g in available_gpus if gpu_counts[g.index] == min_count]
            return max(candidates, key=lambda g: g.free_memory_mb).index
        
        elif self.config.strategy == GPUAllocationStrategy.PACK:
            # Fill GPUs in order (GPU 0 first, then GPU 1, etc.)
            return min(available_gpus, key=lambda g: g.index).index
        
        elif self.config.strategy == GPUAllocationStrategy.SPREAD:
            # Spread across GPUs - use least utilized
            return min(available_gpus, key=lambda g: g.utilization_percent).index
        
        elif self.config.strategy == GPUAllocationStrategy.MANUAL:
            # Manual requires preferred_gpu_id, which should have been handled earlier
            # Fall back to first available
            return available_gpus[0].index
        
        return available_gpus[0].index if available_gpus else None
    
    def _record_allocation(
        self,
        model_id: str,
        gpu_id: int,
        vram_required_gb: Optional[float],
        exclusive: bool = False,
    ) -> None:
        """Record a GPU allocation."""
        import time
        self._allocations[model_id] = GPUAllocation(
            gpu_id=gpu_id,
            model_id=model_id,
            vram_required_gb=vram_required_gb or 0.0,
            exclusive=exclusive,
            created_at=time.time(),
        )
        if gpu_id not in self._gpu_models:
            self._gpu_models[gpu_id] = set()
        self._gpu_models[gpu_id].add(model_id)
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current GPU manager status."""
        status = await self._vram_monitor.get_status()
        return {
            "gpus": [
                {
                    "index": gpu.index,
                    "name": gpu.name,
                    "vendor": gpu.vendor.value if hasattr(gpu, 'vendor') else "unknown",
                    "total_memory_mb": gpu.total_memory_mb,
                    "used_memory_mb": gpu.used_memory_mb,
                    "free_memory_mb": gpu.free_memory_mb,
                    "utilization_percent": gpu.utilization_percent,
                    "temperature_c": gpu.temperature_c,
                    "models_loaded": list(self._gpu_models.get(gpu.index, set())),
                }
                for gpu in status.gpus
            ],
            "allocations": {
                model_id: {
                    "gpu_id": alloc.gpu_id,
                    "vram_required_gb": alloc.vram_required_gb,
                    "exclusive": alloc.exclusive,
                    "created_at": alloc.created_at,
                }
                for model_id, alloc in self._allocations.items()
            },
            "strategy": self.config.strategy.value,
            "config": {
                "vram_threshold_percent": self.config.vram_threshold_percent,
                "allow_shared_gpu": self.config.allow_shared_gpu,
                "auto_unload": self.config.auto_unload,
                "reserved_vram_gb": self.config.reserved_vram_gb,
            },
            "total_allocations": len(self._allocations),
            "total_gpus_in_use": len(self._gpu_models),
        }
    
    async def recommend_allocation(
        self,
        models: List[Dict[str, Any]],
    ) -> Dict[str, Optional[int]]:
        """
        Recommend GPU allocations for a list of models.
        
        This is useful for planning ensemble or parallel executions
        without actually allocating.
        
        Args:
            models: List of dicts with 'model_id' and 'vram_required_gb' keys
            
        Returns:
            Dict mapping model_id to recommended GPU ID
        """
        status = await self._vram_monitor.get_status()
        recommendations: Dict[str, Optional[int]] = {}
        
        # Sort models by VRAM requirement (largest first for better packing)
        sorted_models = sorted(
            models,
            key=lambda m: m.get('vram_required_gb', 0),
            reverse=True
        )
        
        # Simulate allocations
        simulated_gpu_vram: Dict[int, float] = {
            gpu.index: gpu.free_memory_mb / 1024
            for gpu in status.gpus
        }
        
        for model_info in sorted_models:
            model_id = model_info.get('model_id')
            if model_id is None:
                continue
            vram_required = model_info.get('vram_required_gb', 0) + self.config.reserved_vram_gb
            
            # Find best GPU
            best_gpu: Optional[int] = None
            best_free = 0.0
            
            for gpu_id, free_vram in simulated_gpu_vram.items():
                if free_vram >= vram_required and free_vram > best_free:
                    best_gpu = gpu_id
                    best_free = free_vram
            
            recommendations[model_id] = best_gpu
            
            if best_gpu is not None:
                # Update simulated VRAM
                simulated_gpu_vram[best_gpu] -= vram_required
        
        return recommendations
    
    async def can_run_parallel(
        self,
        models: List[Dict[str, Any]],
    ) -> bool:
        """
        Check if all models can run in parallel on available GPUs.
        
        Args:
            models: List of dicts with 'model_id' and 'vram_required_gb' keys
            
        Returns:
            True if all models can be allocated simultaneously
        """
        recommendations = await self.recommend_allocation(models)
        return all(gpu_id is not None for gpu_id in recommendations.values())
