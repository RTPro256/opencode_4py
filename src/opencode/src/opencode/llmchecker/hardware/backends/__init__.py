"""
GPU detection backends for different vendors.
"""

from .base import GPUDetector
from .cpu import CPUDetector
from .cuda import CUDADetector
from .rocm import ROCmDetector
from .intel import IntelDetector
from .apple import AppleDetector

__all__ = [
    "GPUDetector",
    "CPUDetector",
    "CUDADetector",
    "ROCmDetector",
    "IntelDetector",
    "AppleDetector",
]
