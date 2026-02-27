"""
Main hardware detector that combines all detection backends.
"""

import platform
import socket
import time
from typing import Optional

from .models import (
    SystemInfo,
    CPUInfo,
    GPUInfo,
    MemoryInfo,
    HardwareTier,
    AccelerationBackend,
)
from .backends import (
    CUDADetector,
    ROCmDetector,
    IntelDetector,
    AppleDetector,
    CPUDetector,
)


class HardwareDetector:
    """Main hardware detection class.
    
    Detects CPU, GPU, and memory information across different platforms.
    Supports NVIDIA, AMD, Intel, and Apple Silicon GPUs.
    """
    
    def __init__(self):
        """Initialize hardware detector."""
        self._cache: Optional[SystemInfo] = None
        self._cache_expiry: float = 5 * 60  # 5 minutes
        self._cache_time: float = 0
        
        # Initialize detectors
        self._cuda_detector = CUDADetector()
        self._rocm_detector = ROCmDetector()
        self._intel_detector = IntelDetector()
        self._apple_detector = AppleDetector()
        self._cpu_detector = CPUDetector()
    
    def detect(self, force_refresh: bool = False) -> SystemInfo:
        """Detect system hardware.
        
        Args:
            force_refresh: Force refresh even if cache is valid.
            
        Returns:
            SystemInfo object with all detected hardware.
        """
        # Check cache
        if not force_refresh and self._cache:
            if time.time() - self._cache_time < self._cache_expiry:
                return self._cache
        
        # Detect all components
        cpu = self._detect_cpu()
        memory = self._detect_memory()
        gpus = self._detect_gpus()
        
        # Determine best backend and tier
        backend = self._determine_backend(gpus)
        tier = self._calculate_tier(cpu, memory, gpus)
        max_model_size = self._calculate_max_model_size(memory, gpus)
        
        # Create system info
        system_info = SystemInfo(
            cpu=cpu,
            memory=memory,
            gpus=gpus,
            os_name=platform.system(),
            os_version=platform.version(),
            platform=platform.machine(),
            hostname=socket.gethostname(),
            tier=tier,
            backend=backend,
            max_model_size_gb=max_model_size,
            unified_memory=self._has_unified_memory(gpus),
            timestamp=time.time(),
        )
        
        # Update cache
        self._cache = system_info
        self._cache_time = time.time()
        
        return system_info
    
    def _detect_cpu(self) -> CPUInfo:
        """Detect CPU information."""
        system = platform.system()
        
        if system == "Linux":
            return self._detect_cpu_linux()
        elif system == "Darwin":
            return self._detect_cpu_macos()
        elif system == "Windows":
            return self._detect_cpu_windows()
        else:
            return CPUInfo()
    
    def _detect_cpu_linux(self) -> CPUInfo:
        """Detect CPU on Linux."""
        cpu = CPUInfo()
        
        try:
            with open("/proc/cpuinfo", "r") as f:
                content = f.read()
            
            for line in content.split("\n"):
                if line.startswith("model name"):
                    cpu.brand = line.split(":", 1)[1].strip()
                elif line.startswith("vendor_id"):
                    cpu.manufacturer = line.split(":", 1)[1].strip()
                elif line.startswith("cpu family"):
                    cpu.family = line.split(":", 1)[1].strip()
                elif line.startswith("model") and ":" in line:
                    cpu.model = line.split(":", 1)[1].strip()
                elif line.startswith("cpu cores"):
                    cpu.physical_cores = int(line.split(":", 1)[1].strip())
                elif line.startswith("siblings"):
                    cpu.threads = int(line.split(":", 1)[1].strip())
                elif line.startswith("cache size"):
                    # Parse "16384 KB"
                    cache_str = line.split(":", 1)[1].strip()
                    cache_kb = int("".join(c for c in cache_str if c.isdigit()))
                    cpu.cache_l3_kb = cache_kb
                    
        except (IOError, OSError, ValueError):
            pass
        
        # Get core count if not found
        if cpu.physical_cores == 0:
            try:
                import os
                cpu.physical_cores = os.cpu_count() or 1
                cpu.threads = cpu.physical_cores
            except Exception:
                cpu.physical_cores = 1
                cpu.threads = 1
        
        # Get CPU frequency
        try:
            with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq", "r") as f:
                freq_khz = int(f.read().strip())
                cpu.speed_max_ghz = freq_khz / 1_000_000
        except (IOError, OSError, ValueError):
            pass
        
        # Detect architecture
        cpu.architecture = self._detect_architecture(cpu.brand)
        
        # Calculate score
        cpu.score = self._calculate_cpu_score(cpu)
        
        return cpu
    
    def _detect_cpu_macos(self) -> CPUInfo:
        """Detect CPU on macOS."""
        import subprocess
        
        cpu = CPUInfo()
        
        try:
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                cpu.brand = result.stdout.strip()
                cpu.manufacturer = "Apple" if "Apple" in cpu.brand else "Intel"
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        
        try:
            result = subprocess.run(
                ["sysctl", "-n", "hw.physicalcpu"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                cpu.physical_cores = int(result.stdout.strip())
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError, ValueError):
            pass
        
        try:
            result = subprocess.run(
                ["sysctl", "-n", "hw.logicalcpu"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                cpu.threads = int(result.stdout.strip())
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError, ValueError):
            pass
        
        try:
            result = subprocess.run(
                ["sysctl", "-n", "hw.cpufrequency"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                freq_hz = int(result.stdout.strip())
                cpu.speed_max_ghz = freq_hz / 1_000_000_000
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError, ValueError):
            pass
        
        cpu.architecture = self._detect_architecture(cpu.brand)
        cpu.score = self._calculate_cpu_score(cpu)
        
        return cpu
    
    def _detect_cpu_windows(self) -> CPUInfo:
        """Detect CPU on Windows."""
        import subprocess
        
        cpu = CPUInfo()
        
        try:
            result = subprocess.run(
                ["wmic", "cpu", "get", "name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if len(lines) >= 2:
                    parts = lines[1].split()
                    # Parse the output
                    for i, part in enumerate(parts):
                        if part.isdigit():
                            val = int(part)
                            # MaxClockSpeed is in MHz
                            if val > 1000 and "name" not in lines[0].lower().split()[parts.index(part):parts.index(part)+1]:
                                cpu.speed_max_ghz = val / 1000
                            elif cpu.physical_cores == 0:
                                cpu.physical_cores = val
                            elif cpu.threads == 0:
                                cpu.threads = val
                            # Everything before first number is the name
                            if not cpu.brand:
                                cpu.brand = " ".join(parts[:i])
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        
        if not cpu.brand:
            cpu.brand = platform.processor() or "Unknown CPU"
        
        try:
            import os
            if cpu.physical_cores == 0:
                cpu.physical_cores = os.cpu_count() or 1
            if cpu.threads == 0:
                cpu.threads = cpu.physical_cores
        except Exception:
            pass
        
        cpu.architecture = self._detect_architecture(cpu.brand)
        cpu.score = self._calculate_cpu_score(cpu)
        
        return cpu
    
    def _detect_memory(self) -> MemoryInfo:
        """Detect system memory."""
        memory = MemoryInfo()
        
        try:
            import psutil
            
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            memory.total_gb = int(mem.total / (1024**3))
            memory.available_gb = int(mem.available / (1024**3))
            memory.used_gb = int(mem.used / (1024**3))
            memory.free_gb = int(mem.free / (1024**3))
            memory.usage_percent = mem.percent
            memory.swap_total_gb = int(swap.total / (1024**3))
            memory.swap_used_gb = int(swap.used / (1024**3))
            
        except ImportError:
            # Fallback without psutil
            memory = self._detect_memory_fallback()
        
        memory.score = self._calculate_memory_score(memory)
        
        return memory
    
    def _detect_memory_fallback(self) -> MemoryInfo:
        """Fallback memory detection without psutil."""
        memory = MemoryInfo()
        system = platform.system()
        
        if system == "Linux":
            try:
                with open("/proc/meminfo", "r") as f:
                    content = f.read()
                
                for line in content.split("\n"):
                    if line.startswith("MemTotal:"):
                        # Value is in kB
                        parts = line.split()
                        if len(parts) >= 2:
                            memory.total_gb = int(parts[1]) // (1024 * 1024)
                    elif line.startswith("MemFree:"):
                        parts = line.split()
                        if len(parts) >= 2:
                            memory.free_gb = int(parts[1]) // (1024 * 1024)
                    elif line.startswith("MemAvailable:"):
                        parts = line.split()
                        if len(parts) >= 2:
                            memory.available_gb = int(parts[1]) // (1024 * 1024)
                    elif line.startswith("SwapTotal:"):
                        parts = line.split()
                        if len(parts) >= 2:
                            memory.swap_total_gb = int(parts[1]) // (1024 * 1024)
                    elif line.startswith("SwapFree:"):
                        parts = line.split()
                        if len(parts) >= 2:
                            swap_free = int(parts[1]) // (1024 * 1024)
                            memory.swap_used_gb = memory.swap_total_gb - swap_free
                
                if memory.total_gb > 0:
                    memory.used_gb = memory.total_gb - memory.free_gb
                    memory.usage_percent = (memory.used_gb / memory.total_gb) * 100
                    
            except (IOError, OSError, ValueError):
                pass
        
        elif system == "Darwin":
            import subprocess
            try:
                result = subprocess.run(
                    ["sysctl", "-n", "hw.memsize"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    memory.total_gb = int(int(result.stdout.strip()) / (1024**3))
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError, ValueError):
                pass
        
        return memory
    
    def _detect_gpus(self) -> list[GPUInfo]:
        """Detect all GPUs in the system."""
        gpus = []
        
        # Try each detector in order of preference
        # NVIDIA CUDA
        if self._cuda_detector.is_available():
            gpus.extend(self._cuda_detector.detect())
        
        # AMD ROCm
        if self._rocm_detector.is_available():
            gpus.extend(self._rocm_detector.detect())
        
        # Intel
        if self._intel_detector.is_available():
            gpus.extend(self._intel_detector.detect())
        
        # Apple Silicon
        if self._apple_detector.is_available():
            gpus.extend(self._apple_detector.detect())
        
        # If no GPU found, add CPU fallback
        if not gpus:
            gpus.extend(self._cpu_detector.detect())
        
        return gpus
    
    def _detect_architecture(self, brand: str) -> str:
        """Detect CPU architecture from brand string."""
        brand_lower = brand.lower()
        
        if "apple" in brand_lower:
            return "arm64"
        elif "arm" in brand_lower or "aarch" in brand_lower:
            return "arm64"
        elif "xeon" in brand_lower or "core" in brand_lower or "intel" in brand_lower:
            return "x86_64"
        elif "ryzen" in brand_lower or "epyc" in brand_lower or "amd" in brand_lower:
            return "x86_64"
        else:
            return platform.machine()
    
    def _calculate_cpu_score(self, cpu: CPUInfo) -> int:
        """Calculate CPU performance score."""
        score = 0
        
        # Core count (up to 40 points)
        cores = cpu.physical_cores
        if cores >= 32:
            score += 40
        elif cores >= 24:
            score += 35
        elif cores >= 16:
            score += 30
        elif cores >= 12:
            score += 25
        elif cores >= 8:
            score += 20
        elif cores >= 6:
            score += 15
        elif cores >= 4:
            score += 10
        else:
            score += 5
        
        # Speed bonus (up to 20 points)
        speed = cpu.speed_max_ghz
        if speed >= 4.0:
            score += 20
        elif speed >= 3.5:
            score += 15
        elif speed >= 3.0:
            score += 12
        elif speed >= 2.5:
            score += 8
        elif speed >= 2.0:
            score += 5
        
        # Brand bonus (up to 40 points)
        brand = cpu.brand.lower()
        if "apple" in brand:
            if "m4" in brand:
                score += 40
            elif "m3" in brand:
                score += 35
            elif "m2" in brand:
                score += 30
            elif "m1" in brand:
                score += 25
            else:
                score += 20
        elif "xeon" in brand:
            score += 25
        elif "epyc" in brand:
            score += 28
        elif "ryzen 9" in brand:
            score += 25
        elif "ryzen 7" in brand:
            score += 20
        elif "i9" in brand:
            score += 25
        elif "i7" in brand:
            score += 20
        elif "i5" in brand:
            score += 15
        
        return min(100, score)
    
    def _calculate_memory_score(self, memory: MemoryInfo) -> int:
        """Calculate memory score based on total RAM."""
        total = memory.total_gb
        
        if total >= 128:
            return 100
        elif total >= 64:
            return 85
        elif total >= 32:
            return 70
        elif total >= 24:
            return 55
        elif total >= 16:
            return 45
        elif total >= 8:
            return 30
        else:
            return 15
    
    def _determine_backend(self, gpus: list[GPUInfo]) -> AccelerationBackend:
        """Determine the best acceleration backend."""
        if not gpus:
            return AccelerationBackend.CPU
        
        # Find the best GPU
        best_gpu = max(gpus, key=lambda g: g.score)
        
        # Check for Apple Silicon first (Metal)
        if best_gpu.is_apple_silicon:
            return AccelerationBackend.METAL
        
        # Check vendor
        from .models import GPUVendor
        if best_gpu.vendor == GPUVendor.NVIDIA:
            return AccelerationBackend.CUDA
        elif best_gpu.vendor == GPUVendor.AMD:
            return AccelerationBackend.ROCM
        elif best_gpu.vendor == GPUVendor.INTEL:
            return AccelerationBackend.ONEAPI
        
        return AccelerationBackend.CPU
    
    def _calculate_tier(
        self, 
        cpu: CPUInfo, 
        memory: MemoryInfo, 
        gpus: list[GPUInfo]
    ) -> HardwareTier:
        """Calculate overall hardware tier."""
        # Calculate combined score
        total_score = 0
        
        # CPU contributes 20%
        total_score += cpu.score * 0.2
        
        # Memory contributes 20%
        total_score += memory.score * 0.2
        
        # GPU contributes 60%
        if gpus:
            best_gpu_score = max(g.score for g in gpus)
            total_score += best_gpu_score * 0.6
        else:
            # No GPU means lower tier
            total_score += 20 * 0.6
        
        # Determine tier
        if total_score >= 80:
            return HardwareTier.VERY_HIGH
        elif total_score >= 65:
            return HardwareTier.HIGH
        elif total_score >= 50:
            return HardwareTier.MEDIUM_HIGH
        elif total_score >= 35:
            return HardwareTier.MEDIUM
        else:
            return HardwareTier.LOW
    
    def _calculate_max_model_size(
        self, 
        memory: MemoryInfo, 
        gpus: list[GPUInfo]
    ) -> float:
        """Calculate maximum model size that can fit in memory.
        
        For GPU: Use VRAM with some overhead
        For CPU: Use available system RAM
        For Apple Silicon: Use unified memory
        """
        # Check for Apple Silicon (unified memory)
        for gpu in gpus:
            if gpu.is_apple_silicon:
                # Apple Silicon uses unified memory
                # Reserve 4GB for system, use 75% for model
                available = memory.total_gb - 4
                return max(0, available * 0.75)
        
        # Check for dedicated GPU VRAM
        if gpus:
            best_gpu = max(gpus, key=lambda g: g.vram_gb)
            if best_gpu.vram_gb > 0:
                # Reserve 10% for overhead
                return best_gpu.vram_gb * 0.9
        
        # CPU-only: Use available system RAM
        # Reserve 4GB for system, use 50% for model
        available = memory.available_gb - 4
        return max(0, available * 0.5)
    
    def _has_unified_memory(self, gpus: list[GPUInfo]) -> bool:
        """Check if system has unified memory (Apple Silicon)."""
        return any(gpu.is_apple_silicon for gpu in gpus)
    
    def clear_cache(self) -> None:
        """Clear the hardware detection cache."""
        self._cache = None
        self._cache_time = 0