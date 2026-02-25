"""
Hardware detection module for LLM Checker.

Provides system information detection including CPU, GPU, memory,
and acceleration backends.
"""

from .detector import HardwareDetector
from .models import SystemInfo, CPUInfo, GPUInfo, MemoryInfo
from .backends import (
    GPUDetector,
    CUDADetector,
    ROCmDetector,
    IntelDetector,
    AppleDetector,
    CPUDetector,
)

__all__ = [
    "HardwareDetector",
    "SystemInfo",
    "CPUInfo", 
    "GPUInfo",
    "MemoryInfo",
    "GPUDetector",
    "CUDADetector",
    "ROCmDetector",
    "IntelDetector",
    "AppleDetector",
    "CPUDetector",
]
