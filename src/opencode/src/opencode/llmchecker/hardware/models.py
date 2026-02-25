"""
Data models for hardware information.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class GPUVendor(Enum):
    """GPU vendor types."""
    NVIDIA = "nvidia"
    AMD = "amd"
    INTEL = "intel"
    APPLE = "apple"
    UNKNOWN = "unknown"


class AccelerationBackend(Enum):
    """Acceleration backend types."""
    CUDA = "cuda"
    ROCM = "rocm"
    OPENCL = "opencl"
    METAL = "metal"
    ONEAPI = "oneapi"
    CPU = "cpu"


class HardwareTier(Enum):
    """Hardware capability tiers."""
    LOW = "low"
    MEDIUM = "medium"
    MEDIUM_HIGH = "medium_high"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class CPUInfo:
    """CPU information."""
    brand: str = "Unknown"
    manufacturer: str = "Unknown"
    family: str = "Unknown"
    model: str = "Unknown"
    architecture: str = "Unknown"
    cores: int = 1
    physical_cores: int = 1
    threads: int = 1
    speed_ghz: float = 0.0
    speed_max_ghz: float = 0.0
    cache_l1d_kb: int = 0
    cache_l1i_kb: int = 0
    cache_l2_kb: int = 0
    cache_l3_kb: int = 0
    score: int = 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "brand": self.brand,
            "manufacturer": self.manufacturer,
            "family": self.family,
            "model": self.model,
            "architecture": self.architecture,
            "cores": self.cores,
            "physical_cores": self.physical_cores,
            "threads": self.threads,
            "speed_ghz": self.speed_ghz,
            "speed_max_ghz": self.speed_max_ghz,
            "cache_l1d_kb": self.cache_l1d_kb,
            "cache_l1i_kb": self.cache_l1i_kb,
            "cache_l2_kb": self.cache_l2_kb,
            "cache_l3_kb": self.cache_l3_kb,
            "score": self.score,
        }


@dataclass
class GPUInfo:
    """GPU information."""
    model: str = "Unknown"
    vendor: GPUVendor = GPUVendor.UNKNOWN
    vram_gb: float = 0.0
    memory_gb: float = 0.0  # Alias for vram_gb
    driver_version: str = "Unknown"
    cuda_version: Optional[str] = None
    rocm_version: Optional[str] = None
    opencl_version: Optional[str] = None
    metal_support: bool = False
    compute_capability: Optional[str] = None
    score: int = 0
    is_integrated: bool = False
    is_apple_silicon: bool = False
    
    def __post_init__(self):
        """Ensure memory_gb is set."""
        if self.memory_gb == 0.0 and self.vram_gb > 0:
            self.memory_gb = self.vram_gb
        if self.vram_gb == 0.0 and self.memory_gb > 0:
            self.vram_gb = self.memory_gb
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "model": self.model,
            "vendor": self.vendor.value,
            "vram_gb": self.vram_gb,
            "memory_gb": self.memory_gb,
            "driver_version": self.driver_version,
            "cuda_version": self.cuda_version,
            "rocm_version": self.rocm_version,
            "opencl_version": self.opencl_version,
            "metal_support": self.metal_support,
            "compute_capability": self.compute_capability,
            "score": self.score,
            "is_integrated": self.is_integrated,
            "is_apple_silicon": self.is_apple_silicon,
        }


@dataclass
class MemoryInfo:
    """System memory information."""
    total_gb: int = 0
    free_gb: int = 0
    used_gb: int = 0
    available_gb: int = 0
    usage_percent: float = 0.0
    swap_total_gb: int = 0
    swap_used_gb: int = 0
    score: int = 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "total_gb": self.total_gb,
            "free_gb": self.free_gb,
            "used_gb": self.used_gb,
            "available_gb": self.available_gb,
            "usage_percent": self.usage_percent,
            "swap_total_gb": self.swap_total_gb,
            "swap_used_gb": self.swap_used_gb,
            "score": self.score,
        }


@dataclass
class SystemInfo:
    """Complete system information."""
    cpu: CPUInfo = field(default_factory=CPUInfo)
    memory: MemoryInfo = field(default_factory=MemoryInfo)
    gpus: list[GPUInfo] = field(default_factory=list)
    os_name: str = "Unknown"
    os_version: str = "Unknown"
    platform: str = "Unknown"
    hostname: str = "Unknown"
    tier: HardwareTier = HardwareTier.LOW
    backend: AccelerationBackend = AccelerationBackend.CPU
    max_model_size_gb: float = 0.0
    unified_memory: bool = False
    timestamp: float = 0.0
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "cpu": self.cpu.to_dict(),
            "memory": self.memory.to_dict(),
            "gpus": [gpu.to_dict() for gpu in self.gpus],
            "os_name": self.os_name,
            "os_version": self.os_version,
            "platform": self.platform,
            "hostname": self.hostname,
            "tier": self.tier.value,
            "backend": self.backend.value,
            "max_model_size_gb": self.max_model_size_gb,
            "unified_memory": self.unified_memory,
            "timestamp": self.timestamp,
        }
    
    def get_best_gpu(self) -> Optional[GPUInfo]:
        """Get the best GPU (highest VRAM/score)."""
        if not self.gpus:
            return None
        return max(self.gpus, key=lambda g: g.vram_gb)
    
    def get_total_vram(self) -> float:
        """Get total VRAM across all GPUs."""
        return sum(gpu.vram_gb for gpu in self.gpus)
    
    def is_apple_silicon(self) -> bool:
        """Check if system is Apple Silicon."""
        return any(gpu.is_apple_silicon for gpu in self.gpus)