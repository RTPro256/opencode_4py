"""
AMD ROCm GPU detection.
"""

import os
import platform
import shutil
import subprocess
from typing import Optional

from ..models import GPUInfo, GPUVendor, AccelerationBackend
from .base import GPUDetector


class ROCmDetector(GPUDetector):
    """AMD ROCm GPU detection using rocm-smi."""
    
    @property
    def vendor(self) -> GPUVendor:
        return GPUVendor.AMD
    
    @property
    def backend(self) -> AccelerationBackend:
        return AccelerationBackend.ROCM
    
    def is_available(self) -> bool:
        """Check if AMD GPU and rocm-smi are available."""
        # Check if rocm-smi exists
        if shutil.which("rocm-smi") is None:
            return False
        
        try:
            # Try to run rocm-smi
            result = subprocess.run(
                ["rocm-smi", "--showid"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0 and "GPU" in result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False
    
    def detect(self) -> list[GPUInfo]:
        """Detect AMD GPUs using rocm-smi."""
        if not self.is_available():
            return []
        
        gpus = []
        
        try:
            # Get GPU list with details
            result = subprocess.run(
                ["rocm-smi", "--showallinfo"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            
            if result.returncode != 0:
                return []
            
            rocm_version = self.get_api_version()
            
            # Parse rocm-smi output
            current_gpu = {}
            gpu_index = 0
            
            for line in result.stdout.split("\n"):
                line = line.strip()
                
                # New GPU section starts
                if line.startswith("GPU") and ":" in line and "firmware" not in line.lower():
                    if current_gpu and "name" in current_gpu:
                        gpu = self._create_gpu_info(current_gpu, gpu_index, rocm_version)
                        if gpu:
                            gpus.append(gpu)
                        gpu_index += 1
                    current_gpu = {}
                
                # Parse key-value pairs
                if ":" in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        key = parts[0].strip().lower()
                        value = parts[1].strip()
                        
                        if "name" in key or "device" in key:
                            current_gpu["name"] = value
                        elif "vram" in key or "memory" in key:
                            current_gpu["vram"] = value
                        elif "driver" in key:
                            current_gpu["driver"] = value
            
            # Don't forget the last GPU
            if current_gpu and "name" in current_gpu:
                gpu = self._create_gpu_info(current_gpu, gpu_index, rocm_version)
                if gpu:
                    gpus.append(gpu)
                    
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        
        return gpus
    
    def _create_gpu_info(
        self, 
        info: dict, 
        index: int, 
        rocm_version: Optional[str]
    ) -> Optional[GPUInfo]:
        """Create GPUInfo from parsed rocm-smi output."""
        name = info.get("name", "Unknown AMD GPU")
        
        # Parse VRAM
        vram_gb = 0.0
        vram_str = info.get("vram", "")
        if vram_str:
            # Parse strings like "16384 MiB" or "16 GB"
            vram_str = vram_str.lower()
            if "gib" in vram_str or "gb" in vram_str:
                vram_gb = float("".join(c for c in vram_str if c.isdigit() or c == "."))
            elif "mib" in vram_str or "mb" in vram_str:
                vram_mb = float("".join(c for c in vram_str if c.isdigit() or c == "."))
                vram_gb = vram_mb / 1024
        
        # Try to get VRAM from name if not found
        if vram_gb == 0:
            vram_gb = self._estimate_vram_from_name(name)
        
        gpu = GPUInfo(
            model=name,
            vendor=GPUVendor.AMD,
            vram_gb=round(vram_gb, 1),
            memory_gb=round(vram_gb, 1),
            driver_version=info.get("driver", "Unknown"),
            rocm_version=rocm_version,
            is_integrated=False,
            is_apple_silicon=False,
        )
        gpu.score = self.calculate_gpu_score(gpu)
        return gpu
    
    def _estimate_vram_from_name(self, name: str) -> float:
        """Estimate VRAM from GPU name."""
        name_lower = name.lower()
        
        # Common AMD GPU VRAM sizes
        vram_map = {
            "rx 7900 xtx": 24.0,
            "rx 7900 xt": 20.0,
            "rx 7900 gre": 16.0,
            "rx 7800 xt": 16.0,
            "rx 7700 xt": 12.0,
            "rx 7600 xt": 16.0,
            "rx 7600": 8.0,
            "rx 6950 xt": 16.0,
            "rx 6900 xt": 16.0,
            "rx 6800 xt": 16.0,
            "rx 6800": 16.0,
            "rx 6750 xt": 12.0,
            "rx 6700 xt": 12.0,
            "rx 6700": 10.0,
            "rx 6650 xt": 8.0,
            "rx 6600 xt": 8.0,
            "rx 6600": 8.0,
            "rx vega 64": 8.0,
            "rx vega 56": 8.0,
            "rx 5700 xt": 8.0,
            "rx 5700": 8.0,
            "rx 5600 xt": 6.0,
            "rx 5500 xt": 8.0,
            "rx 590": 8.0,
            "rx 580": 8.0,
            "rx 570": 4.0,
            "rx 560": 4.0,
        }
        
        for gpu_name, vram in vram_map.items():
            if gpu_name in name_lower:
                return vram
        
        # Default for unknown AMD GPUs
        return 8.0
    
    def get_api_version(self) -> Optional[str]:
        """Get ROCm version."""
        # Try rocm-smi first
        try:
            result = subprocess.run(
                ["rocm-smi", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                # Parse version from output
                for line in result.stdout.split("\n"):
                    if "version" in line.lower():
                        parts = line.split()
                        for part in parts:
                            if part[0].isdigit():
                                return part
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        
        # Try rocminfo
        if shutil.which("rocminfo"):
            try:
                result = subprocess.run(
                    ["rocminfo", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    for line in result.stdout.split("\n"):
                        if "version" in line.lower():
                            parts = line.split()
                            for part in parts:
                                if part[0].isdigit():
                                    return part
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                pass
        
        return None
