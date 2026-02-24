"""
Base GPU detector interface.
"""

from abc import ABC, abstractmethod
from typing import Optional

from ..models import GPUInfo, GPUVendor, AccelerationBackend


class GPUDetector(ABC):
    """Abstract base class for GPU detection."""
    
    @property
    @abstractmethod
    def vendor(self) -> GPUVendor:
        """Get the GPU vendor this detector handles."""
        pass
    
    @property
    @abstractmethod
    def backend(self) -> AccelerationBackend:
        """Get the acceleration backend for this GPU type."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this GPU type is available on the system."""
        pass
    
    @abstractmethod
    def detect(self) -> list[GPUInfo]:
        """Detect all GPUs of this type.
        
        Returns:
            List of GPUInfo objects for detected GPUs.
        """
        pass
    
    def get_driver_version(self) -> Optional[str]:
        """Get the driver version if available.
        
        Returns:
            Driver version string or None if not available.
        """
        return None
    
    def get_api_version(self) -> Optional[str]:
        """Get the API version (CUDA, ROCm, etc.) if available.
        
        Returns:
            API version string or None if not available.
        """
        return None
    
    @staticmethod
    def calculate_gpu_score(gpu: GPUInfo) -> int:
        """Calculate a performance score for a GPU.
        
        Scoring based on:
        - VRAM (most important for LLMs)
        - Compute capability
        - Memory bandwidth (estimated)
        
        Args:
            gpu: GPU info to score.
            
        Returns:
            Integer score from 0-100.
        """
        score = 0
        
        # VRAM scoring (up to 50 points)
        # 24GB+ = 50, 16GB = 40, 12GB = 30, 8GB = 20, 4GB = 10
        vram_gb = gpu.vram_gb
        if vram_gb >= 24:
            score += 50
        elif vram_gb >= 16:
            score += 40 + int((vram_gb - 16) * (10 / 8))
        elif vram_gb >= 12:
            score += 30 + int((vram_gb - 12) * (10 / 4))
        elif vram_gb >= 8:
            score += 20 + int((vram_gb - 8) * (10 / 4))
        elif vram_gb >= 4:
            score += 10 + int((vram_gb - 4) * (10 / 4))
        else:
            score += int(vram_gb * 2.5)
        
        # Vendor bonus (up to 20 points)
        # NVIDIA has best CUDA support, AMD is good with ROCm
        if gpu.vendor == GPUVendor.NVIDIA:
            score += 20
        elif gpu.vendor == GPUVendor.AMD:
            score += 15
        elif gpu.vendor == GPUVendor.APPLE:
            score += 18  # Metal is very efficient
        elif gpu.vendor == GPUVendor.INTEL:
            score += 10
        
        # Compute capability bonus (up to 30 points)
        if gpu.compute_capability:
            try:
                # Parse compute capability like "8.6" or "7.5"
                parts = gpu.compute_capability.split(".")
                if len(parts) >= 2:
                    major = int(parts[0])
                    minor = int(parts[1])
                    # Higher compute capability = better performance
                    # Ampere (8.x) = 30, Turing (7.5) = 25, Volta (7.0) = 20, etc.
                    if major >= 9:
                        score += 30
                    elif major >= 8:
                        score += 25 + minor
                    elif major >= 7:
                        score += 20 + minor
                    elif major >= 6:
                        score += 15 + minor
                    else:
                        score += 10
            except (ValueError, IndexError):
                score += 10
        
        return min(100, score)
