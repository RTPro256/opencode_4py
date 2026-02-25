"""
Unit tests for Hardware Detector implementation.
"""

import pytest
from unittest.mock import patch, MagicMock, mock_open
import platform
import time

from opencode.llmchecker.hardware.detector import HardwareDetector
from opencode.llmchecker.hardware.models import (
    SystemInfo,
    CPUInfo,
    GPUInfo,
    MemoryInfo,
    HardwareTier,
    AccelerationBackend,
    GPUVendor,
)


class TestHardwareDetector:
    """Tests for HardwareDetector class."""

    @pytest.fixture
    def detector(self):
        """Create a HardwareDetector instance."""
        return HardwareDetector()

    def test_detector_initialization(self, detector):
        """Test detector initializes correctly."""
        assert detector._cache is None
        assert detector._cache_expiry == 5 * 60
        assert detector._cache_time == 0
        assert detector._cuda_detector is not None
        assert detector._rocm_detector is not None
        assert detector._intel_detector is not None
        assert detector._apple_detector is not None
        assert detector._cpu_detector is not None

    def test_detect_caches_result(self, detector):
        """Test that detect caches the result."""
        with patch.object(detector, '_detect_cpu', return_value=CPUInfo()):
            with patch.object(detector, '_detect_memory', return_value=MemoryInfo()):
                with patch.object(detector, '_detect_gpus', return_value=[]):
                    result1 = detector.detect()
                    result2 = detector.detect()
                    
                    assert result1 is result2
                    assert detector._cache is not None

    def test_detect_force_refresh(self, detector):
        """Test that force_refresh bypasses cache."""
        with patch.object(detector, '_detect_cpu', return_value=CPUInfo()) as mock_cpu:
            with patch.object(detector, '_detect_memory', return_value=MemoryInfo()):
                with patch.object(detector, '_detect_gpus', return_value=[]):
                    detector.detect()
                    first_call_count = mock_cpu.call_count
                    
                    detector.detect(force_refresh=True)
                    
                    assert mock_cpu.call_count > first_call_count

    def test_detect_cache_expiry(self, detector):
        """Test that cache expires after timeout."""
        with patch.object(detector, '_detect_cpu', return_value=CPUInfo()) as mock_cpu:
            with patch.object(detector, '_detect_memory', return_value=MemoryInfo()):
                with patch.object(detector, '_detect_gpus', return_value=[]):
                    detector.detect()
                    first_call_count = mock_cpu.call_count
                    
                    # Simulate cache expiry
                    detector._cache_time = time.time() - detector._cache_expiry - 1
                    
                    detector.detect()
                    
                    assert mock_cpu.call_count > first_call_count


class TestHardwareDetectorCPU:
    """Tests for CPU detection."""

    @pytest.fixture
    def detector(self):
        """Create a HardwareDetector instance."""
        return HardwareDetector()

    def test_detect_cpu_windows(self, detector):
        """Test CPU detection on Windows."""
        with patch('platform.system', return_value='Windows'):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout="Name NumberOfCores NumberOfLogicalProcessors MaxClockSpeed\nIntel Core i7 8 16 3000\n"
                )
                cpu = detector._detect_cpu()
                
                assert isinstance(cpu, CPUInfo)

    def test_detect_cpu_macos(self, detector):
        """Test CPU detection on macOS."""
        with patch('platform.system', return_value='Darwin'):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout="Apple M1 Pro")
                cpu = detector._detect_cpu()
                
                assert isinstance(cpu, CPUInfo)

    def test_detect_cpu_linux(self, detector):
        """Test CPU detection on Linux."""
        cpuinfo_content = """
model name	: AMD Ryzen 9 5900X
vendor_id	: AuthenticAMD
cpu cores	: 12
siblings	: 24
cache size	: 32768 KB
"""
        with patch('platform.system', return_value='Linux'):
            with patch('builtins.open', mock_open(read_data=cpuinfo_content)):
                with patch('os.cpu_count', return_value=24):
                    cpu = detector._detect_cpu()
                    
                    assert isinstance(cpu, CPUInfo)

    def test_detect_cpu_unknown_platform(self, detector):
        """Test CPU detection on unknown platform."""
        with patch('platform.system', return_value='Unknown'):
            cpu = detector._detect_cpu()
            
            assert isinstance(cpu, CPUInfo)


class TestHardwareDetectorMemory:
    """Tests for memory detection."""

    @pytest.fixture
    def detector(self):
        """Create a HardwareDetector instance."""
        return HardwareDetector()

    def test_detect_memory_windows(self, detector):
        """Test memory detection on Windows."""
        with patch('platform.system', return_value='Windows'):
            with patch('psutil.virtual_memory') as mock_vm:
                mock_vm.return_value = MagicMock(
                    total=32 * 1024**3,
                    available=16 * 1024**3,
                    used=16 * 1024**3,
                    percent=50.0
                )
                with patch('psutil.swap_memory') as mock_swap:
                    mock_swap.return_value = MagicMock(total=8 * 1024**3)
                    
                    memory = detector._detect_memory()
                    
                    assert isinstance(memory, MemoryInfo)

    def test_detect_memory_linux(self, detector):
        """Test memory detection on Linux."""
        meminfo_content = """
MemTotal:       32768000 kB
MemFree:        16000000 kB
MemAvailable:   24000000 kB
SwapTotal:       8192000 kB
SwapFree:        8000000 kB
"""
        with patch('platform.system', return_value='Linux'):
            with patch('builtins.open', mock_open(read_data=meminfo_content)):
                memory = detector._detect_memory()
                
                assert isinstance(memory, MemoryInfo)


class TestHardwareDetectorGPU:
    """Tests for GPU detection."""

    @pytest.fixture
    def detector(self):
        """Create a HardwareDetector instance."""
        return HardwareDetector()

    def test_detect_gpus_with_cuda(self, detector):
        """Test GPU detection with CUDA GPU."""
        mock_gpu = GPUInfo(
            model="NVIDIA RTX 3080",
            vendor=GPUVendor.NVIDIA,
            vram_gb=10.0,
        )
        
        # Mock all detectors - need to mock is_available() too
        with patch.object(detector._cuda_detector, 'is_available', return_value=True):
            with patch.object(detector._cuda_detector, 'detect', return_value=[mock_gpu]):
                with patch.object(detector._rocm_detector, 'is_available', return_value=False):
                    with patch.object(detector._intel_detector, 'is_available', return_value=False):
                        with patch.object(detector._apple_detector, 'is_available', return_value=False):
                            gpus = detector._detect_gpus()
                            
                            assert len(gpus) >= 1
                            assert any(g.model == "NVIDIA RTX 3080" for g in gpus)

    def test_detect_gpus_with_rocm(self, detector):
        """Test GPU detection with AMD GPU."""
        mock_gpu = GPUInfo(
            model="AMD RX 6800 XT",
            vendor=GPUVendor.AMD,
            vram_gb=16.0,
        )
        
        with patch.object(detector._cuda_detector, 'is_available', return_value=False):
            with patch.object(detector._rocm_detector, 'is_available', return_value=True):
                with patch.object(detector._rocm_detector, 'detect', return_value=[mock_gpu]):
                    with patch.object(detector._intel_detector, 'is_available', return_value=False):
                        with patch.object(detector._apple_detector, 'is_available', return_value=False):
                            gpus = detector._detect_gpus()
                            
                            assert len(gpus) >= 1
                            assert any(g.vendor == GPUVendor.AMD for g in gpus)

    def test_detect_gpus_with_apple(self, detector):
        """Test GPU detection with Apple Silicon."""
        mock_gpu = GPUInfo(
            model="Apple M1 Pro GPU",
            vendor=GPUVendor.APPLE,
            vram_gb=16.0,
            is_apple_silicon=True,
        )
        
        with patch.object(detector._cuda_detector, 'is_available', return_value=False):
            with patch.object(detector._rocm_detector, 'is_available', return_value=False):
                with patch.object(detector._intel_detector, 'is_available', return_value=False):
                    with patch.object(detector._apple_detector, 'is_available', return_value=True):
                        with patch.object(detector._apple_detector, 'detect', return_value=[mock_gpu]):
                            gpus = detector._detect_gpus()
                            
                            assert len(gpus) >= 1
                            assert any(g.is_apple_silicon for g in gpus)


class TestHardwareDetectorBackend:
    """Tests for backend determination."""

    @pytest.fixture
    def detector(self):
        """Create a HardwareDetector instance."""
        return HardwareDetector()

    def test_determine_backend_cuda(self, detector):
        """Test backend determination with CUDA GPU."""
        gpus = [GPUInfo(model="RTX 3080", vendor=GPUVendor.NVIDIA, vram_gb=10.0)]
        
        backend = detector._determine_backend(gpus)
        
        assert backend == AccelerationBackend.CUDA

    def test_determine_backend_rocm(self, detector):
        """Test backend determination with AMD GPU."""
        gpus = [GPUInfo(model="RX 6800", vendor=GPUVendor.AMD, vram_gb=16.0)]
        
        backend = detector._determine_backend(gpus)
        
        assert backend == AccelerationBackend.ROCM

    def test_determine_backend_metal(self, detector):
        """Test backend determination with Apple GPU."""
        gpus = [GPUInfo(model="M1 Pro", vendor=GPUVendor.APPLE, vram_gb=16.0, is_apple_silicon=True)]
        
        backend = detector._determine_backend(gpus)
        
        assert backend == AccelerationBackend.METAL

    def test_determine_backend_cpu(self, detector):
        """Test backend determination with no GPU."""
        backend = detector._determine_backend([])
        
        assert backend == AccelerationBackend.CPU


class TestHardwareDetectorTier:
    """Tests for tier calculation."""

    @pytest.fixture
    def detector(self):
        """Create a HardwareDetector instance."""
        return HardwareDetector()

    def test_calculate_tier_high(self, detector):
        """Test tier calculation for high-end system."""
        # CPU score is 0-100, memory score is 0-100, GPU score is 0-100
        # Total = cpu*0.2 + memory*0.2 + gpu*0.6
        cpu = CPUInfo(brand="AMD Ryzen 9 5900X", physical_cores=12, threads=24, score=80)
        memory = MemoryInfo(total_gb=64, available_gb=32, score=85)
        gpus = [GPUInfo(model="RTX 4090", vendor=GPUVendor.NVIDIA, vram_gb=24.0, score=90)]
        
        tier = detector._calculate_tier(cpu, memory, gpus)
        
        # Total = 80*0.2 + 85*0.2 + 90*0.6 = 16 + 17 + 54 = 87 -> VERY_HIGH
        assert tier in [HardwareTier.HIGH, HardwareTier.VERY_HIGH]

    def test_calculate_tier_low(self, detector):
        """Test tier calculation for low-end system."""
        # Low scores to get LOW or MEDIUM tier
        # Total = cpu*0.2 + memory*0.2 + 20*0.6 (no GPU fallback)
        cpu = CPUInfo(brand="Intel Celeron", physical_cores=2, threads=2, score=10)
        memory = MemoryInfo(total_gb=4, available_gb=2, score=15)
        gpus = []
        
        tier = detector._calculate_tier(cpu, memory, gpus)
        
        # Total = 10*0.2 + 15*0.2 + 20*0.6 = 2 + 3 + 12 = 17 -> LOW
        assert tier in [HardwareTier.LOW, HardwareTier.MEDIUM]


class TestHardwareDetectorMaxModelSize:
    """Tests for max model size calculation."""

    @pytest.fixture
    def detector(self):
        """Create a HardwareDetector instance."""
        return HardwareDetector()

    def test_calculate_max_model_size_with_gpu(self, detector):
        """Test max model size with GPU."""
        memory = MemoryInfo(total_gb=32, available_gb=16)
        gpus = [GPUInfo(model="RTX 3080", vendor=GPUVendor.NVIDIA, vram_gb=10.0)]
        
        max_size = detector._calculate_max_model_size(memory, gpus)
        
        assert max_size > 0

    def test_calculate_max_model_size_no_gpu(self, detector):
        """Test max model size without GPU."""
        memory = MemoryInfo(total_gb=16, available_gb=8)
        gpus = []
        
        max_size = detector._calculate_max_model_size(memory, gpus)
        
        assert max_size > 0


class TestHardwareDetectorUnifiedMemory:
    """Tests for unified memory detection."""

    @pytest.fixture
    def detector(self):
        """Create a HardwareDetector instance."""
        return HardwareDetector()

    def test_has_unified_memory_apple(self, detector):
        """Test unified memory with Apple GPU."""
        gpus = [GPUInfo(model="M1 Pro", vendor=GPUVendor.APPLE, vram_gb=16.0, is_apple_silicon=True)]
        
        result = detector._has_unified_memory(gpus)
        
        assert result is True

    def test_has_unified_memory_nvidia(self, detector):
        """Test unified memory with NVIDIA GPU."""
        gpus = [GPUInfo(model="RTX 3080", vendor=GPUVendor.NVIDIA, vram_gb=10.0)]
        
        result = detector._has_unified_memory(gpus)
        
        assert result is False


class TestHardwareDetectorArchitecture:
    """Tests for architecture detection."""

    @pytest.fixture
    def detector(self):
        """Create a HardwareDetector instance."""
        return HardwareDetector()

    def test_detect_architecture_apple(self, detector):
        """Test architecture detection for Apple Silicon."""
        arch = detector._detect_architecture("Apple M1 Pro")
        
        assert "apple" in arch.lower() or "arm" in arch.lower()

    def test_detect_architecture_intel(self, detector):
        """Test architecture detection for Intel."""
        arch = detector._detect_architecture("Intel Core i7-10700K")
        
        assert "x86" in arch.lower() or "intel" in arch.lower()

    def test_detect_architecture_amd(self, detector):
        """Test architecture detection for AMD."""
        arch = detector._detect_architecture("AMD Ryzen 9 5900X")
        
        assert "x86" in arch.lower() or "amd" in arch.lower()


class TestHardwareDetectorCPUScore:
    """Tests for CPU score calculation."""

    @pytest.fixture
    def detector(self):
        """Create a HardwareDetector instance."""
        return HardwareDetector()

    def test_calculate_cpu_score_high_end(self, detector):
        """Test CPU score for high-end CPU."""
        cpu = CPUInfo(
            brand="AMD Ryzen 9 5900X",
            physical_cores=12,
            threads=24,
            speed_max_ghz=4.8,
            cache_l3_kb=32768,
        )
        
        score = detector._calculate_cpu_score(cpu)
        
        assert score > 0

    def test_calculate_cpu_score_low_end(self, detector):
        """Test CPU score for low-end CPU."""
        cpu = CPUInfo(
            brand="Intel Celeron",
            physical_cores=2,
            threads=2,
            speed_max_ghz=2.0,
            cache_l3_kb=2048,
        )
        
        score = detector._calculate_cpu_score(cpu)
        
        assert score > 0


class TestHardwareDetectorIntegration:
    """Integration tests for HardwareDetector."""

    @pytest.fixture
    def detector(self):
        """Create a HardwareDetector instance."""
        return HardwareDetector()

    def test_detect_returns_system_info(self, detector):
        """Test that detect returns a complete SystemInfo object."""
        with patch.object(detector, '_detect_cpu', return_value=CPUInfo(brand="Test CPU")):
            with patch.object(detector, '_detect_memory', return_value=MemoryInfo(total_gb=16)):
                with patch.object(detector, '_detect_gpus', return_value=[]):
                    result = detector.detect()
                    
                    assert isinstance(result, SystemInfo)
                    assert result.cpu.brand == "Test CPU"
                    assert result.memory.total_gb == 16
                    assert result.gpus == []
                    assert result.os_name is not None
                    assert result.tier is not None
                    assert result.backend is not None

    def test_detect_populates_all_fields(self, detector):
        """Test that detect populates all SystemInfo fields."""
        with patch.object(detector, '_detect_cpu', return_value=CPUInfo()):
            with patch.object(detector, '_detect_memory', return_value=MemoryInfo()):
                with patch.object(detector, '_detect_gpus', return_value=[]):
                    result = detector.detect()
                    
                    assert result.cpu is not None
                    assert result.memory is not None
                    assert result.gpus is not None
                    assert result.os_name is not None
                    assert result.os_version is not None
                    assert result.platform is not None
                    assert result.hostname is not None
                    assert result.tier is not None
                    assert result.backend is not None
                    assert result.max_model_size_gb >= 0
                    assert result.timestamp > 0
