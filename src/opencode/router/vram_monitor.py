"""
VRAM Monitor

GPU memory monitoring for intelligent model management.
"""

import asyncio
import logging
import platform
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class GPUVendor(str, Enum):
    """GPU vendor types."""
    NVIDIA = "nvidia"
    AMD = "amd"
    INTEL = "intel"
    APPLE = "apple"
    UNKNOWN = "unknown"


@dataclass
class GPUInfo:
    """Information about a GPU."""
    index: int
    vendor: GPUVendor
    name: str
    total_memory_mb: int
    used_memory_mb: int
    free_memory_mb: int
    utilization_percent: float
    temperature_c: Optional[float] = None
    
    @property
    def memory_usage_percent(self) -> float:
        """Calculate memory usage percentage."""
        if self.total_memory_mb <= 0:
            return 0.0
        return (self.used_memory_mb / self.total_memory_mb) * 100


@dataclass
class VRAMStatus:
    """Current VRAM status across all GPUs."""
    gpus: List[GPUInfo]
    total_memory_mb: int
    total_used_mb: int
    total_free_mb: int
    timestamp: datetime
    
    @property
    def overall_usage_percent(self) -> float:
        """Calculate overall memory usage percentage."""
        if self.total_memory_mb <= 0:
            return 0.0
        return (self.total_used_mb / self.total_memory_mb) * 100
    
    def get_gpu(self, index: int) -> Optional[GPUInfo]:
        """Get GPU info by index."""
        for gpu in self.gpus:
            if gpu.index == index:
                return gpu
        return None


class VRAMMonitor:
    """
    GPU memory monitor.
    
    Monitors VRAM usage across multiple GPU vendors:
    - NVIDIA (via nvidia-smi)
    - AMD (via rocm-smi)
    - Intel (via xpu-smi)
    - Apple Silicon (via system APIs)
    
    Example:
        monitor = VRAMMonitor()
        status = await monitor.get_status()
        print(f"VRAM usage: {status.overall_usage_percent:.1f}%")
    """
    
    def __init__(self, auto_detect: bool = True):
        """
        Initialize the VRAM monitor.
        
        Args:
            auto_detect: Whether to auto-detect GPU vendor
        """
        self._vendor: Optional[GPUVendor] = None
        self._available = False
        
        if auto_detect:
            self._vendor = self._detect_vendor()
            self._available = self._check_availability()
    
    def _detect_vendor(self) -> GPUVendor:
        """Detect the GPU vendor."""
        system = platform.system()
        
        # Check for Apple Silicon
        if system == "Darwin":
            try:
                result = subprocess.run(
                    ["sysctl", "-n", "machdep.cpu.brand_string"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0 and "Apple" in result.stdout:
                    return GPUVendor.APPLE
            except Exception:
                pass
        
        # Check for NVIDIA
        if shutil.which("nvidia-smi"):
            return GPUVendor.NVIDIA
        
        # Check for AMD
        if shutil.which("rocm-smi"):
            return GPUVendor.AMD
        
        # Check for Intel
        if shutil.which("xpu-smi"):
            return GPUVendor.INTEL
        
        return GPUVendor.UNKNOWN
    
    def _check_availability(self) -> bool:
        """Check if monitoring is available for the detected vendor."""
        if self._vendor == GPUVendor.NVIDIA:
            return shutil.which("nvidia-smi") is not None
        elif self._vendor == GPUVendor.AMD:
            return shutil.which("rocm-smi") is not None
        elif self._vendor == GPUVendor.INTEL:
            return shutil.which("xpu-smi") is not None
        elif self._vendor == GPUVendor.APPLE:
            return platform.system() == "Darwin"
        
        return False
    
    @property
    def vendor(self) -> GPUVendor:
        """Get the detected GPU vendor."""
        return self._vendor or GPUVendor.UNKNOWN
    
    @property
    def available(self) -> bool:
        """Check if VRAM monitoring is available."""
        return self._available
    
    async def get_status(self) -> VRAMStatus:
        """
        Get current VRAM status.
        
        Returns:
            VRAMStatus with current memory information
        """
        if not self._available:
            return VRAMStatus(
                gpus=[],
                total_memory_mb=0,
                total_used_mb=0,
                total_free_mb=0,
                timestamp=datetime.utcnow(),
            )
        
        if self._vendor == GPUVendor.NVIDIA:
            return await self._get_nvidia_status()
        elif self._vendor == GPUVendor.AMD:
            return await self._get_amd_status()
        elif self._vendor == GPUVendor.INTEL:
            return await self._get_intel_status()
        elif self._vendor == GPUVendor.APPLE:
            return await self._get_apple_status()
        
        return VRAMStatus(
            gpus=[],
            total_memory_mb=0,
            total_used_mb=0,
            total_free_mb=0,
            timestamp=datetime.utcnow(),
        )
    
    async def _get_nvidia_status(self) -> VRAMStatus:
        """Get VRAM status for NVIDIA GPUs."""
        try:
            result = await asyncio.create_subprocess_exec(
                "nvidia-smi",
                "--query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu",
                "--format=csv,noheader,nounits",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode != 0:
                logger.error(f"nvidia-smi error: {stderr.decode()}")
                return self._empty_status()
            
            gpus = []
            for line in stdout.decode().strip().split("\n"):
                if not line.strip():
                    continue
                
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 6:
                    gpu = GPUInfo(
                        index=int(parts[0]),
                        vendor=GPUVendor.NVIDIA,
                        name=parts[1],
                        total_memory_mb=int(float(parts[2])),
                        used_memory_mb=int(float(parts[3])),
                        free_memory_mb=int(float(parts[4])),
                        utilization_percent=float(parts[5]),
                        temperature_c=float(parts[6]) if len(parts) > 6 else None,
                    )
                    gpus.append(gpu)
            
            return self._build_status(gpus)
            
        except Exception as e:
            logger.error(f"Failed to get NVIDIA status: {e}")
            return self._empty_status()
    
    async def _get_amd_status(self) -> VRAMStatus:
        """Get VRAM status for AMD GPUs."""
        try:
            result = await asyncio.create_subprocess_exec(
                "rocm-smi",
                "--showmeminfo",
                "vram",
                "--json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode != 0:
                logger.error(f"rocm-smi error: {stderr.decode()}")
                return self._empty_status()
            
            import json
            data = json.loads(stdout.decode())
            
            gpus = []
            for card_id, card_data in data.items():
                if isinstance(card_data, dict):
                    gpu = GPUInfo(
                        index=int(card_id.replace("card", "")),
                        vendor=GPUVendor.AMD,
                        name=card_data.get("Card series", "AMD GPU"),
                        total_memory_mb=int(card_data.get("VRAM Total Memory (B)", 0)) // (1024 * 1024),
                        used_memory_mb=int(card_data.get("VRAM Total Used Memory (B)", 0)) // (1024 * 1024),
                        free_memory_mb=0,
                        utilization_percent=0.0,
                    )
                    gpu.free_memory_mb = gpu.total_memory_mb - gpu.used_memory_mb
                    gpus.append(gpu)
            
            return self._build_status(gpus)
            
        except Exception as e:
            logger.error(f"Failed to get AMD status: {e}")
            return self._empty_status()
    
    async def _get_intel_status(self) -> VRAMStatus:
        """Get VRAM status for Intel GPUs."""
        try:
            result = await asyncio.create_subprocess_exec(
                "xpu-smi",
                "dump",
                "-m",
                "-1",
                "-i",
                "0",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode != 0:
                logger.error(f"xpu-smi error: {stderr.decode()}")
                return self._empty_status()
            
            # Parse xpu-smi output
            gpus = []
            lines = stdout.decode().strip().split("\n")
            
            for line in lines:
                if "Memory" in line or "VRAM" in line:
                    # Parse memory information
                    pass
            
            return self._build_status(gpus)
            
        except Exception as e:
            logger.error(f"Failed to get Intel status: {e}")
            return self._empty_status()
    
    async def _get_apple_status(self) -> VRAMStatus:
        """Get memory status for Apple Silicon."""
        try:
            # Get total memory
            result = await asyncio.create_subprocess_exec(
                "sysctl",
                "-n",
                "hw.memsize",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await result.communicate()
            total_memory_mb = int(stdout.decode().strip()) // (1024 * 1024)
            
            # Get used memory via vm_stat
            result = await asyncio.create_subprocess_exec(
                "vm_stat",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await result.communicate()
            
            # Parse vm_stat output
            page_size = 4096  # Default page size
            used_pages = 0
            
            for line in stdout.decode().split("\n"):
                if "page size of" in line:
                    page_size = int(line.split()[-2])
                elif "Pages active" in line or "Pages wired" in line:
                    used_pages += int(line.split(":")[1].strip().rstrip("."))
            
            used_memory_mb = (used_pages * page_size) // (1024 * 1024)
            free_memory_mb = total_memory_mb - used_memory_mb
            
            gpu = GPUInfo(
                index=0,
                vendor=GPUVendor.APPLE,
                name="Apple Silicon Unified Memory",
                total_memory_mb=total_memory_mb,
                used_memory_mb=used_memory_mb,
                free_memory_mb=free_memory_mb,
                utilization_percent=(used_memory_mb / total_memory_mb) * 100 if total_memory_mb > 0 else 0,
            )
            
            return self._build_status([gpu])
            
        except Exception as e:
            logger.error(f"Failed to get Apple status: {e}")
            return self._empty_status()
    
    def _build_status(self, gpus: List[GPUInfo]) -> VRAMStatus:
        """Build VRAMStatus from GPU list."""
        total_memory = sum(g.total_memory_mb for g in gpus)
        total_used = sum(g.used_memory_mb for g in gpus)
        total_free = sum(g.free_memory_mb for g in gpus)
        
        return VRAMStatus(
            gpus=gpus,
            total_memory_mb=total_memory,
            total_used_mb=total_used,
            total_free_mb=total_free,
            timestamp=datetime.utcnow(),
        )
    
    def _empty_status(self) -> VRAMStatus:
        """Return an empty VRAM status."""
        return VRAMStatus(
            gpus=[],
            total_memory_mb=0,
            total_used_mb=0,
            total_free_mb=0,
            timestamp=datetime.utcnow(),
        )
    
    async def is_memory_available(self, required_mb: int) -> bool:
        """
        Check if enough VRAM is available.
        
        Args:
            required_mb: Required memory in MB
            
        Returns:
            True if enough memory is available
        """
        status = await self.get_status()
        return status.total_free_mb >= required_mb
    
    async def get_recommended_model_size(self) -> int:
        """
        Get recommended maximum model size based on available VRAM.
        
        Returns:
            Recommended size in MB
        """
        status = await self.get_status()
        
        if not status.gpus:
            return 0
        
        # Use 80% of free memory as safe limit
        return int(status.total_free_mb * 0.8)
