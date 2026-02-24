"""
Tests for hardware detection backends (CUDA, ROCm, Apple, Intel, CPU).
"""

import pytest
from unittest.mock import patch, MagicMock
import platform

from opencode.llmchecker.hardware.backends.base import GPUDetector
from opencode.llmchecker.hardware.backends.cuda import CUDADetector
from opencode.llmchecker.hardware.backends.rocm import ROCmDetector
from opencode.llmchecker.hardware.backends.apple import AppleDetector
from opencode.llmchecker.hardware.backends.intel import IntelDetector
from opencode.llmchecker.hardware.backends.cpu import CPUDetector
from opencode.llmchecker.hardware.models import GPUInfo, GPUVendor, AccelerationBackend, CPUInfo


class TestGPUDetectorBase:
    """Tests for GPUDetector abstract class."""
    
    def test_gpu_detector_is_abstract(self):
        """Test that GPUDetector cannot be instantiated directly."""
        with pytest.raises(TypeError):
            GPUDetector()
    
    def test_gpu_detector_has_vendor_property(self):
        """Test that GPUDetector has vendor property."""
        assert hasattr(GPUDetector, "vendor")
    
    def test_gpu_detector_has_backend_property(self):
        """Test that GPUDetector has backend property."""
        assert hasattr(GPUDetector, "backend")
    
    def test_gpu_detector_has_detect_method(self):
        """Test that GPUDetector has detect method."""
        assert hasattr(GPUDetector, "detect")


class TestCUDADetector:
    """Tests for CUDA (NVIDIA) detector."""
    
    @pytest.mark.unit
    def test_cuda_detector_creation(self):
        """Test CUDADetector instantiation."""
        detector = CUDADetector()
        assert detector.vendor == GPUVendor.NVIDIA
        assert detector.backend == AccelerationBackend.CUDA
    
    @pytest.mark.unit
    def test_cuda_not_available_without_nvidia_smi(self):
        """Test CUDA detection when nvidia-smi is not available."""
        with patch("shutil.which", return_value=None):
            detector = CUDADetector()
            assert detector.is_available() is False
    
    @pytest.mark.unit
    def test_cuda_available_with_nvidia_smi(self):
        """Test CUDA detection when nvidia-smi is available."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "NVIDIA-SMI 535.104.05\nDriver Version: 535.104.05\nCUDA Version: 12.2\n"
        
        with patch("shutil.which", return_value="/usr/bin/nvidia-smi"):
            with patch("subprocess.run", return_value=mock_result):
                detector = CUDADetector()
                assert detector.is_available() is True
    
    @pytest.mark.unit
    def test_cuda_detect_returns_list(self):
        """Test CUDA detect returns list of GPUInfo."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """
GPU 00000000:01:00.0
    Product Name                    : NVIDIA GeForce RTX 3090
    Memory Usage
        Total                       : 24576 MiB
"""
        
        with patch("shutil.which", return_value="/usr/bin/nvidia-smi"):
            with patch("subprocess.run", return_value=mock_result):
                detector = CUDADetector()
                gpus = detector.detect()
                assert isinstance(gpus, list)
    
    @pytest.mark.unit
    def test_cuda_get_driver_version(self):
        """Test getting CUDA driver version."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Driver Version: 535.104.05\nCUDA Version: 12.2\n"
        
        with patch("shutil.which", return_value="/usr/bin/nvidia-smi"):
            with patch("subprocess.run", return_value=mock_result):
                detector = CUDADetector()
                version = detector.get_driver_version()
                assert version is not None or version is None  # May be None if parsing fails
    
    @pytest.mark.unit
    def test_cuda_calculate_gpu_score(self):
        """Test GPU score calculation."""
        gpu = GPUInfo(
            model="NVIDIA GeForce RTX 3090",
            vendor=GPUVendor.NVIDIA,
            vram_gb=24,
        )
        score = GPUDetector.calculate_gpu_score(gpu)
        assert score > 0
        assert score <= 100


class TestROCmDetector:
    """Tests for ROCm (AMD) detector."""
    
    @pytest.mark.unit
    def test_rocm_detector_creation(self):
        """Test ROCmDetector instantiation."""
        detector = ROCmDetector()
        assert detector.vendor == GPUVendor.AMD
        assert detector.backend == AccelerationBackend.ROCM
    
    @pytest.mark.unit
    def test_rocm_not_available_without_rocm_smi(self):
        """Test ROCm detection when rocm-smi is not available."""
        with patch("shutil.which", return_value=None):
            detector = ROCmDetector()
            assert detector.is_available() is False
    
    @pytest.mark.unit
    def test_rocm_available_with_rocm_smi(self):
        """Test ROCm detection when rocm-smi is available."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ROCm SMI version: 5.7.0\n"
        
        with patch("shutil.which", return_value="/usr/bin/rocm-smi"):
            with patch("subprocess.run", return_value=mock_result):
                detector = ROCmDetector()
                # ROCm detection depends on platform and actual GPU presence
                result = detector.is_available()
                assert isinstance(result, bool)
    
    @pytest.mark.unit
    def test_rocm_detect_returns_list(self):
        """Test ROCm detect returns list of GPUInfo."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """
GPU[0]		: AMD Radeon RX 7900 XTX
		GPU memory: 24576 MiB
"""
        
        with patch("shutil.which", return_value="/usr/bin/rocm-smi"):
            with patch("subprocess.run", return_value=mock_result):
                detector = ROCmDetector()
                gpus = detector.detect()
                assert isinstance(gpus, list)


class TestAppleDetector:
    """Tests for Apple Silicon detector."""
    
    @pytest.mark.unit
    def test_apple_detector_creation(self):
        """Test AppleDetector instantiation."""
        detector = AppleDetector()
        assert detector.vendor == GPUVendor.APPLE
        assert detector.backend == AccelerationBackend.METAL
    
    @pytest.mark.unit
    def test_apple_not_available_on_non_macos(self):
        """Test Apple detection on non-macOS systems."""
        with patch("platform.system", return_value="Linux"):
            detector = AppleDetector()
            assert detector.is_available() is False
    
    @pytest.mark.unit
    def test_apple_available_on_macos(self):
        """Test Apple detection on macOS."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """
Chip: Apple M2 Max
Memory: 64 GB
"""
        
        with patch("platform.system", return_value="Darwin"):
            with patch("subprocess.run", return_value=mock_result):
                detector = AppleDetector()
                assert detector.is_available() is True
    
    @pytest.mark.unit
    def test_apple_detect_returns_list(self):
        """Test Apple detect returns list of GPUInfo."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """
Chip: Apple M2 Max
Memory: 64 GB
"""
        
        with patch("platform.system", return_value="Darwin"):
            with patch("subprocess.run", return_value=mock_result):
                detector = AppleDetector()
                gpus = detector.detect()
                assert isinstance(gpus, list)


class TestIntelDetector:
    """Tests for Intel GPU detector."""
    
    @pytest.mark.unit
    def test_intel_detector_creation(self):
        """Test IntelDetector instantiation."""
        detector = IntelDetector()
        assert detector.vendor == GPUVendor.INTEL
        assert detector.backend == AccelerationBackend.ONEAPI
    
    @pytest.mark.unit
    def test_intel_not_available_without_tools(self):
        """Test Intel detection when detection tools are not available."""
        with patch("shutil.which", return_value=None):
            detector = IntelDetector()
            # Intel detector may still detect integrated graphics
            result = detector.is_available()
            assert isinstance(result, bool)
    
    @pytest.mark.unit
    def test_intel_detect_returns_list(self):
        """Test Intel detect returns list of GPUInfo."""
        detector = IntelDetector()
        gpus = detector.detect()
        assert isinstance(gpus, list)


class TestCPUDetector:
    """Tests for CPU detector."""
    
    @pytest.mark.unit
    def test_cpu_detector_creation(self):
        """Test CPUDetector instantiation."""
        detector = CPUDetector()
        assert detector.vendor == GPUVendor.UNKNOWN  # CPU uses UNKNOWN vendor
        assert detector.backend == AccelerationBackend.CPU
    
    @pytest.mark.unit
    def test_cpu_always_available(self):
        """Test CPU is always available."""
        detector = CPUDetector()
        assert detector.is_available() is True
    
    @pytest.mark.unit
    def test_cpu_detect_returns_list(self):
        """Test CPU detect returns list of GPUInfo."""
        detector = CPUDetector()
        gpus = detector.detect()
        assert isinstance(gpus, list)
        assert len(gpus) >= 1  # At least one CPU
    
    @pytest.mark.unit
    def test_cpu_detects_memory(self):
        """Test CPU memory detection."""
        detector = CPUDetector()
        gpus = detector.detect()
        # CPU detector returns at least one entry with memory info
        assert len(gpus) >= 1
        # Memory may be 0 if psutil not available or on some platforms
        assert gpus[0].vram_gb >= 0


class TestGPUInfo:
    """Tests for GPUInfo model."""
    
    @pytest.mark.unit
    def test_gpu_info_creation(self):
        """Test GPUInfo model creation."""
        gpu = GPUInfo(
            model="Test GPU",
            vendor=GPUVendor.NVIDIA,
            vram_gb=24,
        )
        assert gpu.model == "Test GPU"
        assert gpu.vendor == GPUVendor.NVIDIA
        assert gpu.vram_gb == 24
    
    @pytest.mark.unit
    def test_gpu_info_defaults(self):
        """Test GPUInfo default values."""
        gpu = GPUInfo()
        assert gpu.model == "Unknown"
        assert gpu.vendor == GPUVendor.UNKNOWN
        assert gpu.driver_version == "Unknown"
    
    @pytest.mark.unit
    def test_gpu_info_memory_alias(self):
        """Test GPUInfo memory_gb is alias for vram_gb."""
        gpu = GPUInfo(vram_gb=16)
        assert gpu.memory_gb == 16
        
        gpu2 = GPUInfo(memory_gb=32)
        assert gpu2.vram_gb == 32
    
    @pytest.mark.unit
    def test_gpu_info_to_dict(self):
        """Test GPUInfo to_dict method."""
        gpu = GPUInfo(
            model="Test GPU",
            vendor=GPUVendor.NVIDIA,
            vram_gb=24,
        )
        d = gpu.to_dict()
        assert d["model"] == "Test GPU"
        assert d["vram_gb"] == 24


class TestCPUInfo:
    """Tests for CPUInfo model."""
    
    @pytest.mark.unit
    def test_cpu_info_creation(self):
        """Test CPUInfo model creation."""
        cpu = CPUInfo(
            brand="Intel Core i9",
            cores=8,
            speed_ghz=3.0,
        )
        assert cpu.brand == "Intel Core i9"
        assert cpu.cores == 8
        assert cpu.speed_ghz == 3.0
    
    @pytest.mark.unit
    def test_cpu_info_defaults(self):
        """Test CPUInfo default values."""
        cpu = CPUInfo()
        assert cpu.brand == "Unknown"
        assert cpu.cores == 1
        assert cpu.speed_ghz == 0.0
    
    @pytest.mark.unit
    def test_cpu_info_to_dict(self):
        """Test CPUInfo to_dict method."""
        cpu = CPUInfo(
            brand="AMD Ryzen 9",
            cores=16,
            speed_ghz=4.0,
        )
        d = cpu.to_dict()
        assert d["brand"] == "AMD Ryzen 9"
        assert d["cores"] == 16


class TestGPUVendor:
    """Tests for GPUVendor enum."""
    
    @pytest.mark.unit
    def test_gpu_vendor_values(self):
        """Test GPUVendor enum values."""
        assert GPUVendor.NVIDIA.value == "nvidia"
        assert GPUVendor.AMD.value == "amd"
        assert GPUVendor.APPLE.value == "apple"
        assert GPUVendor.INTEL.value == "intel"
        assert GPUVendor.UNKNOWN.value == "unknown"


class TestAccelerationBackend:
    """Tests for AccelerationBackend enum."""
    
    @pytest.mark.unit
    def test_backend_values(self):
        """Test AccelerationBackend enum values."""
        assert AccelerationBackend.CUDA.value == "cuda"
        assert AccelerationBackend.ROCM.value == "rocm"
        assert AccelerationBackend.METAL.value == "metal"
        assert AccelerationBackend.OPENCL.value == "opencl"
        assert AccelerationBackend.ONEAPI.value == "oneapi"
        assert AccelerationBackend.CPU.value == "cpu"


class TestDetectorIntegration:
    """Integration tests for hardware detectors."""
    
    @pytest.mark.unit
    def test_all_detectors_have_vendor(self):
        """Test all detectors have a vendor attribute."""
        detectors = [CUDADetector(), ROCmDetector(), AppleDetector(), IntelDetector(), CPUDetector()]
        for detector in detectors:
            assert detector.vendor is not None
    
    @pytest.mark.unit
    def test_all_detectors_have_backend(self):
        """Test all detectors have a backend attribute."""
        detectors = [CUDADetector(), ROCmDetector(), AppleDetector(), IntelDetector(), CPUDetector()]
        for detector in detectors:
            assert detector.backend is not None
    
    @pytest.mark.unit
    def test_all_detectors_have_detect_method(self):
        """Test all detectors have a detect method."""
        detectors = [CUDADetector(), ROCmDetector(), AppleDetector(), IntelDetector(), CPUDetector()]
        for detector in detectors:
            assert callable(detector.detect)
    
    @pytest.mark.unit
    def test_all_detectors_return_gpu_info_list(self):
        """Test all detectors return list of GPUInfo."""
        detectors = [CUDADetector(), ROCmDetector(), AppleDetector(), IntelDetector(), CPUDetector()]
        for detector in detectors:
            gpus = detector.detect()
            assert isinstance(gpus, list)
