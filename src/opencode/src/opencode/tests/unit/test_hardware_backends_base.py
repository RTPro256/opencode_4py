"""
Tests for llmchecker/hardware/backends/base.py

Tests for GPUDetector abstract base class and calculate_gpu_score function.
"""

import pytest
from unittest.mock import MagicMock
from typing import Optional

from opencode.llmchecker.hardware.backends.base import GPUDetector
from opencode.llmchecker.hardware.models import GPUInfo, GPUVendor, AccelerationBackend


class ConcreteGPUDetector(GPUDetector):
    """Concrete implementation of GPUDetector for testing."""
    
    @property
    def vendor(self) -> GPUVendor:
        return GPUVendor.NVIDIA
    
    @property
    def backend(self) -> AccelerationBackend:
        return AccelerationBackend.CUDA
    
    def is_available(self) -> bool:
        return True
    
    def detect(self) -> list[GPUInfo]:
        return [
            GPUInfo(
                model="Test GPU",
                vendor=GPUVendor.NVIDIA,
                vram_gb=8,
                compute_capability="8.6",
            )
        ]
    
    def get_driver_version(self) -> Optional[str]:
        return "535.104.05"
    
    def get_api_version(self) -> Optional[str]:
        return "12.2"


class MinimalGPUDetector(GPUDetector):
    """Minimal implementation without overriding optional methods."""
    
    @property
    def vendor(self) -> GPUVendor:
        return GPUVendor.AMD
    
    @property
    def backend(self) -> AccelerationBackend:
        return AccelerationBackend.ROCM
    
    def is_available(self) -> bool:
        return False
    
    def detect(self) -> list[GPUInfo]:
        return []


class TestGPUDetector:
    """Tests for GPUDetector abstract base class."""
    
    def test_vendor_property(self):
        """Test vendor property returns correct value."""
        detector = ConcreteGPUDetector()
        assert detector.vendor == GPUVendor.NVIDIA
    
    def test_backend_property(self):
        """Test backend property returns correct value."""
        detector = ConcreteGPUDetector()
        assert detector.backend == AccelerationBackend.CUDA
    
    def test_is_available(self):
        """Test is_available method."""
        detector = ConcreteGPUDetector()
        assert detector.is_available() is True
        
        minimal = MinimalGPUDetector()
        assert minimal.is_available() is False
    
    def test_detect(self):
        """Test detect method returns GPU list."""
        detector = ConcreteGPUDetector()
        gpus = detector.detect()
        
        assert len(gpus) == 1
        assert gpus[0].model == "Test GPU"
    
    def test_get_driver_version_overridden(self):
        """Test get_driver_version when overridden."""
        detector = ConcreteGPUDetector()
        assert detector.get_driver_version() == "535.104.05"
    
    def test_get_driver_version_default(self):
        """Test get_driver_version default returns None."""
        detector = MinimalGPUDetector()
        assert detector.get_driver_version() is None
    
    def test_get_api_version_overridden(self):
        """Test get_api_version when overridden."""
        detector = ConcreteGPUDetector()
        assert detector.get_api_version() == "12.2"
    
    def test_get_api_version_default(self):
        """Test get_api_version default returns None."""
        detector = MinimalGPUDetector()
        assert detector.get_api_version() is None


class TestCalculateGPUScore:
    """Tests for GPUDetector.calculate_gpu_score static method."""
    
    def test_vram_scoring_24gb_plus(self):
        """Test VRAM scoring for 24GB+ GPUs."""
        gpu = GPUInfo(
            model="RTX 4090",
            vendor=GPUVendor.NVIDIA,
            vram_gb=24,
        )
        score = GPUDetector.calculate_gpu_score(gpu)
        # 24GB+ = 50 VRAM points + 20 NVIDIA bonus = 70 minimum
        assert score >= 70
    
    def test_vram_scoring_16gb(self):
        """Test VRAM scoring for 16GB GPUs."""
        gpu = GPUInfo(
            model="RTX 4080",
            vendor=GPUVendor.NVIDIA,
            vram_gb=16,
        )
        score = GPUDetector.calculate_gpu_score(gpu)
        # 16GB = 40 VRAM points + 20 NVIDIA bonus = 60 minimum
        assert score >= 60
    
    def test_vram_scoring_12gb(self):
        """Test VRAM scoring for 12GB GPUs."""
        gpu = GPUInfo(
            model="RTX 4070",
            vendor=GPUVendor.NVIDIA,
            vram_gb=12,
        )
        score = GPUDetector.calculate_gpu_score(gpu)
        # 12GB = 30 VRAM points + 20 NVIDIA bonus = 50 minimum
        assert score >= 50
    
    def test_vram_scoring_8gb(self):
        """Test VRAM scoring for 8GB GPUs."""
        gpu = GPUInfo(
            model="RTX 3070",
            vendor=GPUVendor.NVIDIA,
            vram_gb=8,
        )
        score = GPUDetector.calculate_gpu_score(gpu)
        # 8GB = 20 VRAM points + 20 NVIDIA bonus = 40 minimum
        assert score >= 40
    
    def test_vram_scoring_4gb(self):
        """Test VRAM scoring for 4GB GPUs."""
        gpu = GPUInfo(
            model="GTX 1650",
            vendor=GPUVendor.NVIDIA,
            vram_gb=4,
        )
        score = GPUDetector.calculate_gpu_score(gpu)
        # 4GB = 10 VRAM points + 20 NVIDIA bonus = 30 minimum
        assert score >= 30
    
    def test_vram_scoring_below_4gb(self):
        """Test VRAM scoring for GPUs below 4GB."""
        gpu = GPUInfo(
            model="Low-end GPU",
            vendor=GPUVendor.NVIDIA,
            vram_gb=2,
        )
        score = GPUDetector.calculate_gpu_score(gpu)
        # 2GB = 5 VRAM points + 20 NVIDIA bonus = 25 minimum
        assert score >= 20
    
    def test_vendor_bonus_nvidia(self):
        """Test vendor bonus for NVIDIA."""
        gpu_nvidia = GPUInfo(
            model="NVIDIA GPU",
            vendor=GPUVendor.NVIDIA,
            vram_gb=8,
        )
        gpu_other = GPUInfo(
            model="Other GPU",
            vendor=GPUVendor.INTEL,
            vram_gb=8,
        )
        
        score_nvidia = GPUDetector.calculate_gpu_score(gpu_nvidia)
        score_other = GPUDetector.calculate_gpu_score(gpu_other)
        
        # NVIDIA should get 20 bonus, Intel gets 10
        assert score_nvidia > score_other
    
    def test_vendor_bonus_amd(self):
        """Test vendor bonus for AMD."""
        gpu = GPUInfo(
            model="AMD GPU",
            vendor=GPUVendor.AMD,
            vram_gb=8,
        )
        score = GPUDetector.calculate_gpu_score(gpu)
        # 8GB = 20 VRAM points + 15 AMD bonus = 35 minimum
        assert score >= 35
    
    def test_vendor_bonus_apple(self):
        """Test vendor bonus for Apple."""
        gpu = GPUInfo(
            model="Apple GPU",
            vendor=GPUVendor.APPLE,
            vram_gb=8,
        )
        score = GPUDetector.calculate_gpu_score(gpu)
        # 8GB = 20 VRAM points + 18 Apple bonus = 38 minimum
        assert score >= 38
    
    def test_vendor_bonus_intel(self):
        """Test vendor bonus for Intel."""
        gpu = GPUInfo(
            model="Intel GPU",
            vendor=GPUVendor.INTEL,
            vram_gb=8,
        )
        score = GPUDetector.calculate_gpu_score(gpu)
        # 8GB = 20 VRAM points + 10 Intel bonus = 30 minimum
        assert score >= 30
    
    def test_compute_capability_major_9_plus(self):
        """Test compute capability bonus for major version 9+."""
        gpu = GPUInfo(
            model="RTX 5090",
            vendor=GPUVendor.NVIDIA,
            vram_gb=32,
            compute_capability="9.0",
        )
        score = GPUDetector.calculate_gpu_score(gpu)
        # Major 9+ = 30 compute points
        assert score >= 90  # High score expected
    
    def test_compute_capability_major_8(self):
        """Test compute capability bonus for major version 8."""
        gpu = GPUInfo(
            model="RTX 4090",
            vendor=GPUVendor.NVIDIA,
            vram_gb=24,
            compute_capability="8.9",
        )
        score = GPUDetector.calculate_gpu_score(gpu)
        # Major 8 = 25 + minor points
        assert score >= 85
    
    def test_compute_capability_major_7(self):
        """Test compute capability bonus for major version 7."""
        gpu = GPUInfo(
            model="RTX 3090",
            vendor=GPUVendor.NVIDIA,
            vram_gb=24,
            compute_capability="7.5",
        )
        score = GPUDetector.calculate_gpu_score(gpu)
        # Major 7 = 20 + minor points
        assert score >= 80
    
    def test_compute_capability_major_6(self):
        """Test compute capability bonus for major version 6."""
        gpu = GPUInfo(
            model="GTX 1080",
            vendor=GPUVendor.NVIDIA,
            vram_gb=8,
            compute_capability="6.1",
        )
        score = GPUDetector.calculate_gpu_score(gpu)
        # Major 6 = 15 + minor points
        assert score >= 50
    
    def test_compute_capability_major_5_and_below(self):
        """Test compute capability bonus for major version 5 and below."""
        gpu = GPUInfo(
            model="Old GPU",
            vendor=GPUVendor.NVIDIA,
            vram_gb=8,
            compute_capability="5.0",
        )
        score = GPUDetector.calculate_gpu_score(gpu)
        # Major < 6 = 10 points
        assert score >= 45
    
    def test_compute_capability_invalid_format(self):
        """Test compute capability with invalid format."""
        gpu = GPUInfo(
            model="GPU with bad compute",
            vendor=GPUVendor.NVIDIA,
            vram_gb=8,
            compute_capability="invalid",
        )
        score = GPUDetector.calculate_gpu_score(gpu)
        # Should still work, just get 10 points for compute
        assert score >= 40
    
    def test_compute_capability_none(self):
        """Test compute capability when None."""
        gpu = GPUInfo(
            model="GPU without compute capability",
            vendor=GPUVendor.NVIDIA,
            vram_gb=8,
            compute_capability=None,
        )
        score = GPUDetector.calculate_gpu_score(gpu)
        # No compute bonus
        assert score >= 40
    
    def test_score_capped_at_100(self):
        """Test that score is capped at 100."""
        gpu = GPUInfo(
            model="Super GPU",
            vendor=GPUVendor.NVIDIA,
            vram_gb=48,
            compute_capability="9.9",
        )
        score = GPUDetector.calculate_gpu_score(gpu)
        assert score <= 100
    
    def test_score_with_all_bonuses(self):
        """Test score with all possible bonuses."""
        gpu = GPUInfo(
            model="RTX 4090",
            vendor=GPUVendor.NVIDIA,
            vram_gb=24,
            compute_capability="8.9",
        )
        score = GPUDetector.calculate_gpu_score(gpu)
        # 24GB = 50 VRAM + 20 NVIDIA + 25+9 compute = 100+ (capped at 100)
        assert score == 100
    
    def test_score_between_16_and_24_gb(self):
        """Test VRAM scoring between 16GB and 24GB."""
        gpu = GPUInfo(
            model="20GB GPU",
            vendor=GPUVendor.NVIDIA,
            vram_gb=20,
        )
        score = GPUDetector.calculate_gpu_score(gpu)
        # Should get partial points between 16GB and 24GB
        assert score >= 60  # More than 16GB base
    
    def test_score_between_12_and_16_gb(self):
        """Test VRAM scoring between 12GB and 16GB."""
        gpu = GPUInfo(
            model="14GB GPU",
            vendor=GPUVendor.NVIDIA,
            vram_gb=14,
        )
        score = GPUDetector.calculate_gpu_score(gpu)
        # Should get partial points between 12GB and 16GB
        assert score >= 50  # More than 12GB base
    
    def test_score_between_8_and_12_gb(self):
        """Test VRAM scoring between 8GB and 12GB."""
        gpu = GPUInfo(
            model="10GB GPU",
            vendor=GPUVendor.NVIDIA,
            vram_gb=10,
        )
        score = GPUDetector.calculate_gpu_score(gpu)
        # Should get partial points between 8GB and 12GB
        assert score >= 40  # More than 8GB base
    
    def test_score_between_4_and_8_gb(self):
        """Test VRAM scoring between 4GB and 8GB."""
        gpu = GPUInfo(
            model="6GB GPU",
            vendor=GPUVendor.NVIDIA,
            vram_gb=6,
        )
        score = GPUDetector.calculate_gpu_score(gpu)
        # Should get partial points between 4GB and 8GB
        assert score >= 30  # More than 4GB base
    
    def test_compute_capability_with_single_part(self):
        """Test compute capability with only major version."""
        gpu = GPUInfo(
            model="GPU",
            vendor=GPUVendor.NVIDIA,
            vram_gb=8,
            compute_capability="8",
        )
        score = GPUDetector.calculate_gpu_score(gpu)
        # Should handle gracefully (ValueError/IndexError caught)
        assert score >= 40
    
    def test_compute_capability_with_extra_parts(self):
        """Test compute capability with extra parts."""
        gpu = GPUInfo(
            model="GPU",
            vendor=GPUVendor.NVIDIA,
            vram_gb=8,
            compute_capability="8.6.1",
        )
        score = GPUDetector.calculate_gpu_score(gpu)
        # Should use first two parts
        assert score >= 50


class TestGPUDetectorIntegration:
    """Integration tests for GPUDetector."""
    
    def test_full_detection_workflow(self):
        """Test a complete detection workflow."""
        detector = ConcreteGPUDetector()
        
        # Check availability
        assert detector.is_available()
        
        # Detect GPUs
        gpus = detector.detect()
        assert len(gpus) == 1
        
        # Get versions
        driver = detector.get_driver_version()
        api = detector.get_api_version()
        
        assert driver is not None
        assert api is not None
        
        # Calculate score for detected GPU
        score = GPUDetector.calculate_gpu_score(gpus[0])
        assert 0 <= score <= 100
    
    def test_minimal_detector_workflow(self):
        """Test workflow with minimal detector."""
        detector = MinimalGPUDetector()
        
        assert detector.vendor == GPUVendor.AMD
        assert detector.backend == AccelerationBackend.ROCM
        assert detector.is_available() is False
        assert detector.detect() == []
        assert detector.get_driver_version() is None
        assert detector.get_api_version() is None
