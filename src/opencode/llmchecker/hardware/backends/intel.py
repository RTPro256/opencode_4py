"""
Intel GPU detection (Arc, integrated graphics).
"""

import os
import platform
import shutil
import subprocess
from typing import Optional

from ..models import GPUInfo, GPUVendor, AccelerationBackend
from .base import GPUDetector


class IntelDetector(GPUDetector):
    """Intel GPU detection using various methods."""
    
    @property
    def vendor(self) -> GPUVendor:
        return GPUVendor.INTEL
    
    @property
    def backend(self) -> AccelerationBackend:
        return AccelerationBackend.ONEAPI
    
    def is_available(self) -> bool:
        """Check if Intel GPU is available."""
        # Check for Intel GPUs on Linux
        if platform.system() == "Linux":
            # Check for Intel GPU in sysfs
            if os.path.exists("/sys/class/drm"):
                for entry in os.listdir("/sys/class/drm"):
                    if entry.startswith("card"):
                        device_path = f"/sys/class/drm/{entry}/device/vendor"
                        if os.path.exists(device_path):
                            try:
                                with open(device_path, "r") as f:
                                    vendor_id = f.read().strip()
                                    # Intel vendor ID is 0x8086
                                    if vendor_id == "0x8086":
                                        return True
                            except (IOError, OSError):
                                continue
        
        # Check for xpu-smi (Intel GPU management tool)
        if shutil.which("xpu-smi"):
            try:
                result = subprocess.run(
                    ["xpu-smi", "discovery"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                return result.returncode == 0 and bool(result.stdout.strip())
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                pass
        
        # Check for level-zero loader
        if shutil.which("sycl-ls"):
            try:
                result = subprocess.run(
                    ["sycl-ls"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                return "ext_oneapi_level_zero" in result.stdout
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                pass
        
        return False
    
    def detect(self) -> list[GPUInfo]:
        """Detect Intel GPUs."""
        if not self.is_available():
            return []
        
        gpus = []
        
        # Try xpu-smi first
        xpu_gpus = self._detect_with_xpu_smi()
        if xpu_gpus:
            gpus.extend(xpu_gpus)
        
        # Fallback to sysfs on Linux
        if not gpus and platform.system() == "Linux":
            sysfs_gpus = self._detect_with_sysfs()
            gpus.extend(sysfs_gpus)
        
        return gpus
    
    def _detect_with_xpu_smi(self) -> list[GPUInfo]:
        """Detect Intel GPUs using xpu-smi."""
        gpus = []
        
        if not shutil.which("xpu-smi"):
            return gpus
        
        try:
            result = subprocess.run(
                ["xpu-smi", "discovery"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            
            if result.returncode != 0:
                return gpus
            
            # Parse xpu-smi output
            for line in result.stdout.split("\n"):
                if "Device" in line and "Name" in line:
                    # Parse device info
                    parts = line.split("|")
                    if len(parts) >= 3:
                        name = parts[2].strip()
                        gpu = GPUInfo(
                            model=name,
                            vendor=GPUVendor.INTEL,
                            vram_gb=self._estimate_vram_from_name(name),
                            driver_version=self.get_driver_version() or "Unknown",
                            is_integrated="Arc" not in name,
                            is_apple_silicon=False,
                        )
                        gpu.score = self.calculate_gpu_score(gpu)
                        gpus.append(gpu)
                        
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        
        return gpus
    
    def _detect_with_sysfs(self) -> list[GPUInfo]:
        """Detect Intel GPUs using Linux sysfs."""
        gpus = []
        
        drm_path = "/sys/class/drm"
        if not os.path.exists(drm_path):
            return gpus
        
        for entry in os.listdir(drm_path):
            if not entry.startswith("card"):
                continue
            
            card_path = os.path.join(drm_path, entry)
            device_path = os.path.join(card_path, "device")
            vendor_path = os.path.join(device_path, "vendor")
            
            if not os.path.exists(vendor_path):
                continue
            
            try:
                with open(vendor_path, "r") as f:
                    vendor_id = f.read().strip()
                    if vendor_id != "0x8086":
                        continue
                
                # Get device name
                name = self._get_intel_gpu_name(card_path)
                
                # Get VRAM if available
                vram_gb = self._get_vram_from_sysfs(card_path)
                if vram_gb == 0:
                    vram_gb = self._estimate_vram_from_name(name)
                
                gpu = GPUInfo(
                    model=name,
                    vendor=GPUVendor.INTEL,
                    vram_gb=vram_gb,
                    memory_gb=vram_gb,
                    driver_version=self.get_driver_version() or "Unknown",
                    is_integrated="Arc" not in name and "Iris" in name,
                    is_apple_silicon=False,
                )
                gpu.score = self.calculate_gpu_score(gpu)
                gpus.append(gpu)
                
            except (IOError, OSError):
                continue
        
        return gpus
    
    def _get_intel_gpu_name(self, card_path: str) -> str:
        """Get Intel GPU name from sysfs."""
        # Try to get the device name
        device_path = os.path.join(card_path, "device")
        
        # Check for device ID
        device_id_path = os.path.join(device_path, "device")
        if os.path.exists(device_id_path):
            try:
                with open(device_id_path, "r") as f:
                    device_id = f.read().strip()
                    return self._device_id_to_name(device_id)
            except (IOError, OSError):
                pass
        
        return "Intel GPU"
    
    def _device_id_to_name(self, device_id: str) -> str:
        """Convert Intel device ID to GPU name."""
        # Common Intel GPU device IDs
        device_map = {
            "0x5690": "Intel Arc A770",
            "0x5691": "Intel Arc A750",
            "0x5692": "Intel Arc A580",
            "0x5693": "Intel Arc A380",
            "0x5694": "Intel Arc A310",
            "0x56A0": "Intel Arc A770M",
            "0x56A1": "Intel Arc A730M",
            "0x56A2": "Intel Arc A550M",
            "0x56A3": "Intel Arc A370M",
            "0x56A4": "Intel Arc A350M",
            # Integrated graphics
            "0x4680": "Intel UHD Graphics 770",
            "0x4682": "Intel UHD Graphics 770",
            "0x4690": "Intel UHD Graphics 770",
            "0x9A40": "Intel Iris Xe Graphics",
            "0x9A49": "Intel Iris Xe Graphics",
            "0x9A59": "Intel Iris Xe Graphics",
            "0x9A60": "Intel UHD Graphics",
            "0x9A68": "Intel UHD Graphics",
            "0x9A70": "Intel UHD Graphics",
            "0x9B40": "Intel UHD Graphics 620",
            "0x9B41": "Intel UHD Graphics 620",
        }
        
        return device_map.get(device_id, f"Intel GPU ({device_id})")
    
    def _get_vram_from_sysfs(self, card_path: str) -> float:
        """Get VRAM from sysfs."""
        # Try different VRAM info paths
        vram_paths = [
            os.path.join(card_path, "device", "mem_info_vram_total"),
            os.path.join(card_path, "device", "mem_info_vis_vram_total"),
        ]
        
        for path in vram_paths:
            if os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        vram_bytes = int(f.read().strip())
                        return vram_bytes / (1024**3)  # Convert to GB
                except (IOError, OSError, ValueError):
                    continue
        
        return 0.0
    
    def _estimate_vram_from_name(self, name: str) -> float:
        """Estimate VRAM from GPU name."""
        name_lower = name.lower()
        
        # Intel Arc discrete GPUs
        if "a770" in name_lower:
            return 16.0
        elif "a750" in name_lower:
            return 8.0
        elif "a580" in name_lower:
            return 8.0
        elif "a380" in name_lower:
            return 6.0
        elif "a310" in name_lower:
            return 4.0
        elif "a770m" in name_lower:
            return 16.0
        elif "a730m" in name_lower:
            return 12.0
        elif "a550m" in name_lower:
            return 8.0
        elif "a370m" in name_lower:
            return 4.0
        elif "a350m" in name_lower:
            return 4.0
        
        # Integrated graphics - use shared memory
        # Return 0 to indicate shared memory
        return 0.0
    
    def get_driver_version(self) -> Optional[str]:
        """Get Intel GPU driver version."""
        # Try xpu-smi
        if shutil.which("xpu-smi"):
            try:
                result = subprocess.run(
                    ["xpu-smi", "version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    for line in result.stdout.split("\n"):
                        if "driver" in line.lower() or "version" in line.lower():
                            parts = line.split()
                            for part in parts:
                                if part[0].isdigit():
                                    return part
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                pass
        
        # Try i915 module version on Linux
        if platform.system() == "Linux":
            try:
                with open("/sys/module/i915/version", "r") as f:
                    return f.read().strip()
            except (IOError, OSError):
                pass
        
        return None