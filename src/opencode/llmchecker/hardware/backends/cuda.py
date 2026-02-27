"""
NVIDIA CUDA GPU detection.
"""

import os
import platform
import shutil
import subprocess
from typing import Optional

from ..models import GPUInfo, GPUVendor, AccelerationBackend
from .base import GPUDetector


class CUDADetector(GPUDetector):
    """NVIDIA CUDA GPU detection using nvidia-smi."""
    
    @property
    def vendor(self) -> GPUVendor:
        return GPUVendor.NVIDIA
    
    @property
    def backend(self) -> AccelerationBackend:
        return AccelerationBackend.CUDA
    
    def is_available(self) -> bool:
        """Check if NVIDIA GPU and nvidia-smi are available."""
        # Check if nvidia-smi exists
        if shutil.which("nvidia-smi") is None:
            return False
        
        try:
            # Try to run nvidia-smi
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0 and bool(result.stdout.strip())
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False
    
    def detect(self) -> list[GPUInfo]:
        """Detect NVIDIA GPUs using nvidia-smi."""
        if not self.is_available():
            return []
        
        gpus = []
        
        try:
            # Query GPU information
            query = (
                "index,name,memory.total,driver_version,compute_cap"
            )
            result = subprocess.run(
                ["nvidia-smi", f"--query-gpu={query}", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            
            if result.returncode != 0:
                return []
            
            driver_version = self.get_driver_version()
            cuda_version = self.get_api_version()
            
            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                
                parts = [p.strip() for p in line.split(",")]
                if len(parts) < 3:
                    continue
                
                try:
                    index = int(parts[0])
                    name = parts[1]
                    memory_mb = float(parts[2])
                    compute_cap = parts[4] if len(parts) > 4 else None
                    
                    # Convert MB to GB
                    vram_gb = memory_mb / 1024
                    
                    gpu = GPUInfo(
                        model=name,
                        vendor=GPUVendor.NVIDIA,
                        vram_gb=round(vram_gb, 1),
                        memory_gb=round(vram_gb, 1),
                        driver_version=driver_version or "Unknown",
                        cuda_version=cuda_version,
                        compute_capability=compute_cap,
                        is_integrated=False,
                        is_apple_silicon=False,
                    )
                    gpu.score = self.calculate_gpu_score(gpu)
                    gpus.append(gpu)
                    
                except (ValueError, IndexError) as e:
                    continue
                    
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        
        return gpus
    
    def get_driver_version(self) -> Optional[str]:
        """Get NVIDIA driver version."""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return result.stdout.strip().split("\n")[0].strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        return None
    
    def get_api_version(self) -> Optional[str]:
        """Get CUDA version."""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query=cuda_version", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        
        # Try nvcc as fallback
        if shutil.which("nvcc"):
            try:
                result = subprocess.run(
                    ["nvcc", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    # Parse output like "release 12.1"
                    for line in result.stdout.split("\n"):
                        if "release" in line.lower():
                            parts = line.split()
                            for i, part in enumerate(parts):
                                if part.lower() == "release" and i + 1 < len(parts):
                                    return parts[i + 1].rstrip(",")
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                pass
        
        return None
    
    @staticmethod
    def get_gpu_memory_usage() -> Optional[dict]:
        """Get current GPU memory usage.
        
        Returns:
            Dictionary with 'used_gb', 'free_gb', 'total_gb' or None.
        """
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.used,memory.free,memory.total", 
                 "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split(",")
                if len(parts) >= 3:
                    return {
                        "used_gb": float(parts[0].strip()) / 1024,
                        "free_gb": float(parts[1].strip()) / 1024,
                        "total_gb": float(parts[2].strip()) / 1024,
                    }
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError, ValueError):
            pass
        return None
