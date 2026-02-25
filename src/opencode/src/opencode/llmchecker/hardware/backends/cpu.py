"""
CPU detection and fallback for systems without GPU.
"""

import os
import platform
import subprocess
from typing import Optional

from ..models import GPUInfo, GPUVendor, AccelerationBackend
from .base import GPUDetector


class CPUDetector(GPUDetector):
    """CPU detection and fallback for systems without dedicated GPU."""
    
    @property
    def vendor(self) -> GPUVendor:
        return GPUVendor.UNKNOWN
    
    @property
    def backend(self) -> AccelerationBackend:
        return AccelerationBackend.CPU
    
    def is_available(self) -> bool:
        """CPU is always available."""
        return True
    
    def detect(self) -> list[GPUInfo]:
        """Return CPU info as a fallback 'GPU'.
        
        This allows the system to work even without a dedicated GPU,
        using CPU for inference.
        """
        cpu_info = self._get_cpu_info()
        
        # Create a CPU "GPU" entry for systems without dedicated GPU
        gpu = GPUInfo(
            model=f"{cpu_info.get('brand', 'CPU')} (CPU)",
            vendor=GPUVendor.UNKNOWN,
            vram_gb=0,  # CPU uses system RAM
            memory_gb=0,
            driver_version="CPU",
            is_integrated=True,
            is_apple_silicon=False,
        )
        gpu.score = self._calculate_cpu_score(cpu_info)
        
        return [gpu]
    
    def _get_cpu_info(self) -> dict:
        """Get CPU information."""
        info = {
            "brand": "Unknown CPU",
            "cores": 1,
            "threads": 1,
            "speed_ghz": 0.0,
        }
        
        system = platform.system()
        
        if system == "Linux":
            info.update(self._get_cpu_info_linux())
        elif system == "Darwin":
            info.update(self._get_cpu_info_macos())
        elif system == "Windows":
            info.update(self._get_cpu_info_windows())
        
        return info
    
    def _get_cpu_info_linux(self) -> dict:
        """Get CPU info on Linux."""
        info = {}
        
        # Read from /proc/cpuinfo
        try:
            with open("/proc/cpuinfo", "r") as f:
                content = f.read()
                
            model_name = None
            cores = 0
            siblings = 0
            
            for line in content.split("\n"):
                if line.startswith("model name"):
                    model_name = line.split(":", 1)[1].strip()
                elif line.startswith("cpu cores"):
                    cores = int(line.split(":", 1)[1].strip())
                elif line.startswith("siblings"):
                    siblings = int(line.split(":", 1)[1].strip())
            
            if model_name:
                info["brand"] = model_name
            if cores:
                info["cores"] = cores
            if siblings:
                info["threads"] = siblings
            elif cores:
                info["threads"] = cores
                
        except (IOError, OSError):
            pass
        
        # Get CPU frequency
        try:
            with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq", "r") as f:
                freq_khz = int(f.read().strip())
                info["speed_ghz"] = freq_khz / 1_000_000
        except (IOError, OSError, ValueError):
            pass
        
        return info
    
    def _get_cpu_info_macos(self) -> dict:
        """Get CPU info on macOS."""
        info = {}
        
        try:
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                info["brand"] = result.stdout.strip()
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
                info["cores"] = int(result.stdout.strip())
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
                info["threads"] = int(result.stdout.strip())
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError, ValueError):
            pass
        
        return info
    
    def _get_cpu_info_windows(self) -> dict:
        """Get CPU info on Windows."""
        info = {}
        
        try:
            result = subprocess.run(
                ["wmic", "cpu", "get", "name,NumberOfCores,NumberOfLogicalProcessors"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if len(lines) >= 2:
                    parts = lines[1].split()
                    if len(parts) >= 3:
                        # Name might have spaces, so we need to be careful
                        # Format: Name NumberOfCores NumberOfLogicalProcessors
                        # Find the numeric parts
                        for i, part in enumerate(parts):
                            if part.isdigit():
                                info["cores"] = int(part)
                                if i + 1 < len(parts) and parts[i + 1].isdigit():
                                    info["threads"] = int(parts[i + 1])
                                # Everything before this is the name
                                info["brand"] = " ".join(parts[:i])
                                break
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        
        # Fallback using platform
        if "brand" not in info:
            info["brand"] = platform.processor() or "Unknown CPU"
        
        try:
            import os
            info["cores"] = os.cpu_count() or 1
            info["threads"] = info["cores"]
        except Exception:
            pass
        
        return info
    
    def _calculate_cpu_score(self, cpu_info: dict) -> int:
        """Calculate CPU performance score for inference.
        
        CPUs are scored lower than GPUs for LLM inference,
        but high-core-count CPUs can still be useful.
        """
        score = 0
        
        cores = cpu_info.get("cores", 1)
        threads = cpu_info.get("threads", cores)
        brand = cpu_info.get("brand", "").lower()
        
        # Core count scoring (up to 30 points)
        if cores >= 32:
            score += 30
        elif cores >= 24:
            score += 25
        elif cores >= 16:
            score += 20
        elif cores >= 12:
            score += 15
        elif cores >= 8:
            score += 10
        elif cores >= 4:
            score += 5
        
        # Thread bonus
        if threads > cores:
            score += min(5, threads - cores)
        
        # CPU brand bonus
        if "xeon" in brand:
            score += 10
        elif "epyc" in brand:
            score += 12
        elif "ryzen 9" in brand or "ryzen 7" in brand:
            score += 8
        elif "i9" in brand or "i7" in brand:
            score += 7
        elif "m1" in brand or "m2" in brand or "m3" in brand or "m4" in brand:
            score += 10  # Apple Silicon is efficient
        
        # CPU is always slower than GPU for LLMs
        # Cap at 40 to ensure GPUs are preferred
        return min(40, score)
    
    @staticmethod
    def get_cpu_usage() -> Optional[dict]:
        """Get CPU usage information.
        
        Returns:
            Dictionary with 'percent' usage or None.
        """
        try:
            import psutil
            return {"percent": psutil.cpu_percent(interval=0.1)}
        except ImportError:
            pass
        
        # Fallback for Linux
        if platform.system() == "Linux":
            try:
                with open("/proc/stat", "r") as f:
                    line = f.readline()
                    parts = line.split()
                    if len(parts) >= 5:
                        # Calculate CPU usage from /proc/stat
                        # user, nice, system, idle, iowait
                        user = int(parts[1])
                        nice = int(parts[2])
                        system = int(parts[3])
                        idle = int(parts[4])
                        total = user + nice + system + idle
                        if total > 0:
                            used = user + nice + system
                            return {"percent": (used / total) * 100}
            except (IOError, OSError, ValueError):
                pass
        
        return None