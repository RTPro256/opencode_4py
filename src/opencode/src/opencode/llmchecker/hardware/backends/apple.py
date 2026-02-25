"""
Apple Silicon GPU detection.
"""

import os
import platform
import subprocess
from typing import Optional

from ..models import GPUInfo, GPUVendor, AccelerationBackend
from .base import GPUDetector


class AppleDetector(GPUDetector):
    """Apple Silicon GPU detection using system_profiler and sysctl."""
    
    @property
    def vendor(self) -> GPUVendor:
        return GPUVendor.APPLE
    
    @property
    def backend(self) -> AccelerationBackend:
        return AccelerationBackend.METAL
    
    def is_available(self) -> bool:
        """Check if Apple Silicon is available."""
        # Only available on macOS
        if platform.system() != "Darwin":
            return False
        
        # Check for Apple Silicon
        try:
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                cpu_brand = result.stdout.strip()
                # Apple Silicon chips have "Apple" in the brand string
                return "Apple" in cpu_brand
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        
        # Alternative check using uname -m
        try:
            result = subprocess.run(
                ["uname", "-m"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                arch = result.stdout.strip()
                # arm64 indicates Apple Silicon
                return arch == "arm64"
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        
        return False
    
    def detect(self) -> list[GPUInfo]:
        """Detect Apple Silicon GPU."""
        if not self.is_available():
            return []
        
        gpus = []
        
        # Get chip name
        chip_name = self._get_chip_name()
        
        # Get unified memory
        memory_gb = self._get_unified_memory()
        
        # Get GPU core count
        gpu_cores = self._get_gpu_cores()
        
        gpu = GPUInfo(
            model=f"{chip_name} GPU",
            vendor=GPUVendor.APPLE,
            vram_gb=memory_gb,  # Unified memory
            memory_gb=memory_gb,
            driver_version=self.get_driver_version() or "Metal",
            metal_support=True,
            is_integrated=True,
            is_apple_silicon=True,
        )
        gpu.score = self._calculate_apple_gpu_score(chip_name, memory_gb, gpu_cores)
        gpus.append(gpu)
        
        return gpus
    
    def _get_chip_name(self) -> str:
        """Get the Apple Silicon chip name."""
        try:
            # Try system_profiler
            result = subprocess.run(
                ["system_profiler", "SPHardwareDataType"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "Chip" in line:
                        # Parse "Chip: Apple M1 Pro" or similar
                        parts = line.split(":")
                        if len(parts) >= 2:
                            chip = parts[1].strip()
                            if chip:
                                return chip
                    elif "Processor Name" in line:
                        parts = line.split(":")
                        if len(parts) >= 2:
                            chip = parts[1].strip()
                            if chip:
                                return chip
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        
        # Fallback to sysctl
        try:
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        
        return "Apple Silicon"
    
    def _get_unified_memory(self) -> float:
        """Get unified memory size in GB."""
        try:
            result = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                bytes_mem = int(result.stdout.strip())
                return bytes_mem / (1024**3)
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError, ValueError):
            pass
        
        # Fallback to system_profiler
        try:
            result = subprocess.run(
                ["system_profiler", "SPHardwareDataType"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "Memory" in line:
                        parts = line.split(":")
                        if len(parts) >= 2:
                            mem_str = parts[1].strip()
                            # Parse "16 GB" or "32 GB"
                            if "GB" in mem_str:
                                num = "".join(c for c in mem_str if c.isdigit() or c == ".")
                                return float(num)
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError, ValueError):
            pass
        
        return 8.0  # Default assumption
    
    def _get_gpu_cores(self) -> int:
        """Get GPU core count."""
        try:
            result = subprocess.run(
                ["system_profiler", "SPDisplaysDataType"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "Total Number of Cores" in line:
                        parts = line.split(":")
                        if len(parts) >= 2:
                            cores_str = parts[1].strip()
                            return int("".join(c for c in cores_str if c.isdigit()))
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError, ValueError):
            pass
        
        return 0
    
    def _calculate_apple_gpu_score(self, chip_name: str, memory_gb: float, gpu_cores: int) -> int:
        """Calculate performance score for Apple Silicon GPU."""
        score = 0
        
        # Base score from chip generation
        chip_lower = chip_name.lower()
        if "m4" in chip_lower:
            score += 35
        elif "m3" in chip_lower:
            score += 30
        elif "m2" in chip_lower:
            score += 25
        elif "m1" in chip_lower:
            score += 20
        else:
            score += 15
        
        # Chip tier bonus
        if "ultra" in chip_lower:
            score += 25
        elif "max" in chip_lower:
            score += 18
        elif "pro" in chip_lower:
            score += 12
        else:
            score += 5
        
        # Memory bonus (unified memory is very efficient for LLMs)
        if memory_gb >= 64:
            score += 25
        elif memory_gb >= 32:
            score += 18
        elif memory_gb >= 24:
            score += 12
        elif memory_gb >= 16:
            score += 8
        elif memory_gb >= 8:
            score += 5
        
        # GPU core bonus
        if gpu_cores >= 40:
            score += 15
        elif gpu_cores >= 32:
            score += 12
        elif gpu_cores >= 20:
            score += 8
        elif gpu_cores >= 10:
            score += 5
        
        return min(100, score)
    
    def get_driver_version(self) -> Optional[str]:
        """Get Metal version."""
        try:
            result = subprocess.run(
                ["system_profiler", "SPDisplaysDataType"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "Metal" in line:
                        parts = line.split(":")
                        if len(parts) >= 2:
                            return parts[1].strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        
        return None
    
    @staticmethod
    def get_memory_pressure() -> Optional[dict]:
        """Get memory pressure information.
        
        Returns:
            Dictionary with 'system_wide', 'apps', 'wired' percentages or None.
        """
        try:
            result = subprocess.run(
                ["vm_stat"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                # Parse vm_stat output
                pages_free = 0
                pages_active = 0
                pages_inactive = 0
                pages_wired = 0
                page_size = 4096  # Default page size
                
                for line in result.stdout.split("\n"):
                    if "page size of" in line:
                        page_size = int("".join(c for c in line if c.isdigit()))
                    elif "Pages free" in line:
                        pages_free = int("".join(c for c in line.split(":")[1] if c.isdigit()))
                    elif "Pages active" in line:
                        pages_active = int("".join(c for c in line.split(":")[1] if c.isdigit()))
                    elif "Pages inactive" in line:
                        pages_inactive = int("".join(c for c in line.split(":")[1] if c.isdigit()))
                    elif "Pages wired down" in line:
                        pages_wired = int("".join(c for c in line.split(":")[1] if c.isdigit()))
                
                total = pages_free + pages_active + pages_inactive + pages_wired
                if total > 0:
                    return {
                        "free_percent": (pages_free / total) * 100,
                        "active_percent": (pages_active / total) * 100,
                        "inactive_percent": (pages_inactive / total) * 100,
                        "wired_percent": (pages_wired / total) * 100,
                    }
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError, ValueError):
            pass
        
        return None