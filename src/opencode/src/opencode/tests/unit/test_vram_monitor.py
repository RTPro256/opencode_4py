"""
Tests for VRAM Monitor.

Unit tests for GPU memory monitoring functionality.
"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, mock_open

from opencode.router.vram_monitor import (
    GPUVendor,
    GPUInfo,
    VRAMStatus,
    VRAMMonitor,
)


class TestGPUVendor:
    """Tests for GPUVendor enum."""

    def test_vendor_values(self):
        """Test GPU vendor enum values."""
        assert GPUVendor.NVIDIA == "nvidia"
        assert GPUVendor.AMD == "amd"
        assert GPUVendor.INTEL == "intel"
        assert GPUVendor.APPLE == "apple"
        assert GPUVendor.UNKNOWN == "unknown"

    def test_vendor_string_conversion(self):
        """Test converting vendor to string."""
        assert GPUVendor.NVIDIA.value == "nvidia"
        assert GPUVendor.AMD.value == "amd"


class TestGPUInfo:
    """Tests for GPUInfo dataclass."""

    def test_gpu_info_creation(self):
        """Test creating GPUInfo instance."""
        gpu = GPUInfo(
            index=0,
            vendor=GPUVendor.NVIDIA,
            name="RTX 4090",
            total_memory_mb=24564,
            used_memory_mb=8192,
            free_memory_mb=16372,
            utilization_percent=45.5,
            temperature_c=65.0,
        )
        
        assert gpu.index == 0
        assert gpu.vendor == GPUVendor.NVIDIA
        assert gpu.name == "RTX 4090"
        assert gpu.total_memory_mb == 24564
        assert gpu.used_memory_mb == 8192
        assert gpu.free_memory_mb == 16372
        assert gpu.utilization_percent == 45.5
        assert gpu.temperature_c == 65.0

    def test_gpu_info_without_temperature(self):
        """Test GPUInfo without temperature."""
        gpu = GPUInfo(
            index=1,
            vendor=GPUVendor.AMD,
            name="RX 7900 XTX",
            total_memory_mb=24564,
            used_memory_mb=0,
            free_memory_mb=24564,
            utilization_percent=0.0,
        )
        
        assert gpu.temperature_c is None

    def test_memory_usage_percent(self):
        """Test memory usage percentage calculation."""
        gpu = GPUInfo(
            index=0,
            vendor=GPUVendor.NVIDIA,
            name="RTX 4090",
            total_memory_mb=10000,
            used_memory_mb=2500,
            free_memory_mb=7500,
            utilization_percent=50.0,
        )
        
        assert gpu.memory_usage_percent == 25.0

    def test_memory_usage_percent_full(self):
        """Test memory usage when fully used."""
        gpu = GPUInfo(
            index=0,
            vendor=GPUVendor.NVIDIA,
            name="RTX 4090",
            total_memory_mb=10000,
            used_memory_mb=10000,
            free_memory_mb=0,
            utilization_percent=100.0,
        )
        
        assert gpu.memory_usage_percent == 100.0

    def test_memory_usage_percent_zero_total(self):
        """Test memory usage with zero total memory."""
        gpu = GPUInfo(
            index=0,
            vendor=GPUVendor.UNKNOWN,
            name="Unknown",
            total_memory_mb=0,
            used_memory_mb=0,
            free_memory_mb=0,
            utilization_percent=0.0,
        )
        
        assert gpu.memory_usage_percent == 0.0


class TestVRAMStatus:
    """Tests for VRAMStatus dataclass."""

    def test_vram_status_creation(self):
        """Test creating VRAMStatus instance."""
        gpus = [
            GPUInfo(
                index=0,
                vendor=GPUVendor.NVIDIA,
                name="RTX 4090",
                total_memory_mb=24564,
                used_memory_mb=8192,
                free_memory_mb=16372,
                utilization_percent=45.5,
            ),
            GPUInfo(
                index=1,
                vendor=GPUVendor.NVIDIA,
                name="RTX 4090",
                total_memory_mb=24564,
                used_memory_mb=4096,
                free_memory_mb=20468,
                utilization_percent=25.0,
            ),
        ]
        
        status = VRAMStatus(
            gpus=gpus,
            total_memory_mb=49128,
            total_used_mb=12288,
            total_free_mb=36840,
            timestamp=datetime.utcnow(),
        )
        
        assert len(status.gpus) == 2
        assert status.total_memory_mb == 49128
        assert status.total_used_mb == 12288
        assert status.total_free_mb == 36840

    def test_overall_usage_percent(self):
        """Test overall usage percentage calculation."""
        status = VRAMStatus(
            gpus=[],
            total_memory_mb=10000,
            total_used_mb=3000,
            total_free_mb=7000,
            timestamp=datetime.utcnow(),
        )
        
        assert status.overall_usage_percent == 30.0

    def test_overall_usage_percent_zero_total(self):
        """Test overall usage with zero total memory."""
        status = VRAMStatus(
            gpus=[],
            total_memory_mb=0,
            total_used_mb=0,
            total_free_mb=0,
            timestamp=datetime.utcnow(),
        )
        
        assert status.overall_usage_percent == 0.0

    def test_get_gpu_found(self):
        """Test getting GPU by index when found."""
        gpus = [
            GPUInfo(
                index=0,
                vendor=GPUVendor.NVIDIA,
                name="RTX 4090",
                total_memory_mb=24564,
                used_memory_mb=8192,
                free_memory_mb=16372,
                utilization_percent=45.5,
            ),
            GPUInfo(
                index=1,
                vendor=GPUVendor.NVIDIA,
                name="RTX 4080",
                total_memory_mb=16384,
                used_memory_mb=4096,
                free_memory_mb=12288,
                utilization_percent=25.0,
            ),
        ]
        
        status = VRAMStatus(
            gpus=gpus,
            total_memory_mb=40948,
            total_used_mb=12288,
            total_free_mb=28660,
            timestamp=datetime.utcnow(),
        )
        
        gpu = status.get_gpu(1)
        assert gpu is not None
        assert gpu.name == "RTX 4080"

    def test_get_gpu_not_found(self):
        """Test getting GPU by index when not found."""
        gpus = [
            GPUInfo(
                index=0,
                vendor=GPUVendor.NVIDIA,
                name="RTX 4090",
                total_memory_mb=24564,
                used_memory_mb=8192,
                free_memory_mb=16372,
                utilization_percent=45.5,
            ),
        ]
        
        status = VRAMStatus(
            gpus=gpus,
            total_memory_mb=24564,
            total_used_mb=8192,
            total_free_mb=16372,
            timestamp=datetime.utcnow(),
        )
        
        gpu = status.get_gpu(99)
        assert gpu is None


class TestVRAMMonitor:
    """Tests for VRAMMonitor class."""

    def test_init_auto_detect_true(self):
        """Test initialization with auto_detect=True."""
        with patch.object(VRAMMonitor, '_detect_vendor', return_value=GPUVendor.NVIDIA):
            with patch.object(VRAMMonitor, '_check_availability', return_value=True):
                monitor = VRAMMonitor(auto_detect=True)
                
                assert monitor.vendor == GPUVendor.NVIDIA
                assert monitor.available is True

    def test_init_auto_detect_false(self):
        """Test initialization with auto_detect=False."""
        monitor = VRAMMonitor(auto_detect=False)
        
        assert monitor.vendor == GPUVendor.UNKNOWN
        assert monitor.available is False

    def test_detect_vendor_nvidia(self):
        """Test detecting NVIDIA vendor."""
        with patch('shutil.which') as mock_which:
            mock_which.side_effect = lambda cmd: True if cmd == "nvidia-smi" else None
            
            monitor = VRAMMonitor.__new__(VRAMMonitor)
            vendor = monitor._detect_vendor()
            
            assert vendor == GPUVendor.NVIDIA

    def test_detect_vendor_amd(self):
        """Test detecting AMD vendor."""
        with patch('shutil.which') as mock_which:
            mock_which.side_effect = lambda cmd: True if cmd == "rocm-smi" else None
            
            monitor = VRAMMonitor.__new__(VRAMMonitor)
            vendor = monitor._detect_vendor()
            
            assert vendor == GPUVendor.AMD

    def test_detect_vendor_intel(self):
        """Test detecting Intel vendor."""
        with patch('shutil.which') as mock_which:
            mock_which.side_effect = lambda cmd: True if cmd == "xpu-smi" else None
            
            monitor = VRAMMonitor.__new__(VRAMMonitor)
            vendor = monitor._detect_vendor()
            
            assert vendor == GPUVendor.INTEL

    def test_detect_vendor_apple(self):
        """Test detecting Apple Silicon vendor."""
        with patch('platform.system', return_value="Darwin"):
            with patch('subprocess.run') as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = "Apple M2 Pro"
                mock_run.return_value = mock_result
                
                monitor = VRAMMonitor.__new__(VRAMMonitor)
                vendor = monitor._detect_vendor()
                
                assert vendor == GPUVendor.APPLE

    def test_detect_vendor_unknown(self):
        """Test detecting unknown vendor."""
        with patch('platform.system', return_value="Linux"):
            with patch('shutil.which', return_value=None):
                monitor = VRAMMonitor.__new__(VRAMMonitor)
                vendor = monitor._detect_vendor()
                
                assert vendor == GPUVendor.UNKNOWN

    def test_check_availability_nvidia(self):
        """Test availability check for NVIDIA."""
        with patch('shutil.which', return_value=True):
            monitor = VRAMMonitor.__new__(VRAMMonitor)
            monitor._vendor = GPUVendor.NVIDIA
            
            result = monitor._check_availability()
            assert result is True

    def test_check_availability_amd(self):
        """Test availability check for AMD."""
        with patch('shutil.which', return_value=True):
            monitor = VRAMMonitor.__new__(VRAMMonitor)
            monitor._vendor = GPUVendor.AMD
            
            result = monitor._check_availability()
            assert result is True

    def test_check_availability_intel(self):
        """Test availability check for Intel."""
        with patch('shutil.which', return_value=True):
            monitor = VRAMMonitor.__new__(VRAMMonitor)
            monitor._vendor = GPUVendor.INTEL
            
            result = monitor._check_availability()
            assert result is True

    def test_check_availability_apple(self):
        """Test availability check for Apple."""
        with patch('platform.system', return_value="Darwin"):
            monitor = VRAMMonitor.__new__(VRAMMonitor)
            monitor._vendor = GPUVendor.APPLE
            
            result = monitor._check_availability()
            assert result is True

    def test_check_availability_unknown(self):
        """Test availability check for unknown vendor."""
        monitor = VRAMMonitor.__new__(VRAMMonitor)
        monitor._vendor = GPUVendor.UNKNOWN
        
        result = monitor._check_availability()
        assert result is False

    @pytest.mark.asyncio
    async def test_get_status_not_available(self):
        """Test get_status when monitoring not available."""
        monitor = VRAMMonitor(auto_detect=False)
        
        status = await monitor.get_status()
        
        assert status.gpus == []
        assert status.total_memory_mb == 0
        assert status.total_used_mb == 0
        assert status.total_free_mb == 0

    @pytest.mark.asyncio
    async def test_get_status_nvidia(self):
        """Test get_status for NVIDIA GPUs."""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (
            b"0, RTX 4090, 24564, 8192, 16372, 45, 65\n1, RTX 4080, 16384, 4096, 12288, 25, 60",
            b""
        )
        mock_process.returncode = 0
        
        with patch('shutil.which', return_value=True):
            with patch('asyncio.create_subprocess_exec', return_value=mock_process):
                monitor = VRAMMonitor.__new__(VRAMMonitor)
                monitor._vendor = GPUVendor.NVIDIA
                monitor._available = True
                
                status = await monitor.get_status()
                
                assert len(status.gpus) == 2
                assert status.gpus[0].name == "RTX 4090"
                assert status.gpus[0].temperature_c == 65.0
                assert status.gpus[1].name == "RTX 4080"

    @pytest.mark.asyncio
    async def test_get_status_nvidia_error(self):
        """Test get_status for NVIDIA with error."""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"GPU not found")
        mock_process.returncode = 1
        
        with patch('shutil.which', return_value=True):
            with patch('asyncio.create_subprocess_exec', return_value=mock_process):
                monitor = VRAMMonitor.__new__(VRAMMonitor)
                monitor._vendor = GPUVendor.NVIDIA
                monitor._available = True
                
                status = await monitor.get_status()
                
                assert status.gpus == []

    @pytest.mark.asyncio
    async def test_get_status_amd(self):
        """Test get_status for AMD GPUs."""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (
            b'{"card0": {"Card series": "RX 7900 XTX", "VRAM Total Memory (B)": "25769803776", "VRAM Total Used Memory (B)": "8589934592"}}',
            b""
        )
        mock_process.returncode = 0
        
        with patch('shutil.which', return_value=True):
            with patch('asyncio.create_subprocess_exec', return_value=mock_process):
                monitor = VRAMMonitor.__new__(VRAMMonitor)
                monitor._vendor = GPUVendor.AMD
                monitor._available = True
                
                status = await monitor.get_status()
                
                assert len(status.gpus) == 1
                assert status.gpus[0].vendor == GPUVendor.AMD
                assert status.gpus[0].total_memory_mb == 24576  # 25769803776 / (1024*1024)

    @pytest.mark.asyncio
    async def test_get_status_intel(self):
        """Test get_status for Intel GPUs."""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (
            b"Intel GPU Memory Information\nSome output without memory info",
            b""
        )
        mock_process.returncode = 0
        
        with patch('shutil.which', return_value=True):
            with patch('asyncio.create_subprocess_exec', return_value=mock_process):
                monitor = VRAMMonitor.__new__(VRAMMonitor)
                monitor._vendor = GPUVendor.INTEL
                monitor._available = True
                
                status = await monitor.get_status()
                
                # Intel parsing returns empty GPUs in current implementation
                assert status.gpus == []

    @pytest.mark.asyncio
    async def test_get_status_apple(self):
        """Test get_status for Apple Silicon."""
        mock_process_memsize = AsyncMock()
        mock_process_memsize.communicate.return_value = (b"34359738368", b"")  # 32GB
        mock_process_memsize.returncode = 0
        
        mock_process_vmstat = AsyncMock()
        # Format: "Pages active: 1000000." and "Pages wired: 500000."
        mock_process_vmstat.communicate.return_value = (
            b"Pages active: 1000000.\nPages wired: 500000.",
            b""
        )
        mock_process_vmstat.returncode = 0
        
        with patch('platform.system', return_value="Darwin"):
            with patch('asyncio.create_subprocess_exec') as mock_exec:
                mock_exec.side_effect = [mock_process_memsize, mock_process_vmstat]
                
                monitor = VRAMMonitor.__new__(VRAMMonitor)
                monitor._vendor = GPUVendor.APPLE
                monitor._available = True
                
                status = await monitor.get_status()
                
                assert len(status.gpus) == 1
                assert status.gpus[0].vendor == GPUVendor.APPLE
                assert status.gpus[0].name == "Apple Silicon Unified Memory"
                assert status.gpus[0].total_memory_mb == 32768  # 32GB

    def test_build_status(self):
        """Test building VRAMStatus from GPU list."""
        gpus = [
            GPUInfo(
                index=0,
                vendor=GPUVendor.NVIDIA,
                name="RTX 4090",
                total_memory_mb=24564,
                used_memory_mb=8192,
                free_memory_mb=16372,
                utilization_percent=45.5,
            ),
            GPUInfo(
                index=1,
                vendor=GPUVendor.NVIDIA,
                name="RTX 4080",
                total_memory_mb=16384,
                used_memory_mb=4096,
                free_memory_mb=12288,
                utilization_percent=25.0,
            ),
        ]
        
        monitor = VRAMMonitor.__new__(VRAMMonitor)
        status = monitor._build_status(gpus)
        
        assert status.total_memory_mb == 40948
        assert status.total_used_mb == 12288
        assert status.total_free_mb == 28660
        assert len(status.gpus) == 2

    def test_empty_status(self):
        """Test creating empty VRAMStatus."""
        monitor = VRAMMonitor.__new__(VRAMMonitor)
        status = monitor._empty_status()
        
        assert status.gpus == []
        assert status.total_memory_mb == 0
        assert status.total_used_mb == 0
        assert status.total_free_mb == 0
        assert isinstance(status.timestamp, datetime)

    @pytest.mark.asyncio
    async def test_is_memory_available_true(self):
        """Test is_memory_available when enough memory."""
        monitor = VRAMMonitor.__new__(VRAMMonitor)
        monitor._available = True
        monitor._vendor = GPUVendor.NVIDIA
        
        # Mock get_status to return sufficient memory
        mock_status = VRAMStatus(
            gpus=[GPUInfo(
                index=0,
                vendor=GPUVendor.NVIDIA,
                name="RTX 4090",
                total_memory_mb=24564,
                used_memory_mb=8192,
                free_memory_mb=16372,
                utilization_percent=45.5,
            )],
            total_memory_mb=24564,
            total_used_mb=8192,
            total_free_mb=16372,
            timestamp=datetime.utcnow(),
        )
        
        with patch.object(monitor, 'get_status', return_value=mock_status):
            result = await monitor.is_memory_available(10000)
            assert result is True

    @pytest.mark.asyncio
    async def test_is_memory_available_false(self):
        """Test is_memory_available when not enough memory."""
        monitor = VRAMMonitor.__new__(VRAMMonitor)
        monitor._available = True
        monitor._vendor = GPUVendor.NVIDIA
        
        # Mock get_status to return insufficient memory
        mock_status = VRAMStatus(
            gpus=[GPUInfo(
                index=0,
                vendor=GPUVendor.NVIDIA,
                name="RTX 4090",
                total_memory_mb=24564,
                used_memory_mb=22564,
                free_memory_mb=2000,
                utilization_percent=95.0,
            )],
            total_memory_mb=24564,
            total_used_mb=22564,
            total_free_mb=2000,
            timestamp=datetime.utcnow(),
        )
        
        with patch.object(monitor, 'get_status', return_value=mock_status):
            result = await monitor.is_memory_available(10000)
            assert result is False

    @pytest.mark.asyncio
    async def test_get_recommended_model_size(self):
        """Test getting recommended model size."""
        monitor = VRAMMonitor.__new__(VRAMMonitor)
        monitor._available = True
        monitor._vendor = GPUVendor.NVIDIA
        
        # Mock get_status to return free memory
        mock_status = VRAMStatus(
            gpus=[GPUInfo(
                index=0,
                vendor=GPUVendor.NVIDIA,
                name="RTX 4090",
                total_memory_mb=24564,
                used_memory_mb=8192,
                free_memory_mb=16372,
                utilization_percent=45.5,
            )],
            total_memory_mb=24564,
            total_used_mb=8192,
            total_free_mb=16372,
            timestamp=datetime.utcnow(),
        )
        
        with patch.object(monitor, 'get_status', return_value=mock_status):
            result = await monitor.get_recommended_model_size()
            # Should be 80% of free memory
            assert result == int(16372 * 0.8)

    @pytest.mark.asyncio
    async def test_get_recommended_model_size_no_gpus(self):
        """Test getting recommended model size with no GPUs."""
        monitor = VRAMMonitor.__new__(VRAMMonitor)
        monitor._available = False
        
        mock_status = VRAMStatus(
            gpus=[],
            total_memory_mb=0,
            total_used_mb=0,
            total_free_mb=0,
            timestamp=datetime.utcnow(),
        )
        
        with patch.object(monitor, 'get_status', return_value=mock_status):
            result = await monitor.get_recommended_model_size()
            assert result == 0

    @pytest.mark.asyncio
    async def test_get_status_exception_handling(self):
        """Test exception handling in get_status."""
        monitor = VRAMMonitor.__new__(VRAMMonitor)
        monitor._vendor = GPUVendor.NVIDIA
        monitor._available = True
        
        with patch('asyncio.create_subprocess_exec', side_effect=Exception("Process failed")):
            status = await monitor._get_nvidia_status()
            assert status.gpus == []

    @pytest.mark.asyncio
    async def test_amd_status_exception_handling(self):
        """Test exception handling in AMD status."""
        monitor = VRAMMonitor.__new__(VRAMMonitor)
        monitor._vendor = GPUVendor.AMD
        monitor._available = True
        
        with patch('asyncio.create_subprocess_exec', side_effect=Exception("Process failed")):
            status = await monitor._get_amd_status()
            assert status.gpus == []

    @pytest.mark.asyncio
    async def test_intel_status_exception_handling(self):
        """Test exception handling in Intel status."""
        monitor = VRAMMonitor.__new__(VRAMMonitor)
        monitor._vendor = GPUVendor.INTEL
        monitor._available = True
        
        with patch('asyncio.create_subprocess_exec', side_effect=Exception("Process failed")):
            status = await monitor._get_intel_status()
            assert status.gpus == []

    @pytest.mark.asyncio
    async def test_apple_status_exception_handling(self):
        """Test exception handling in Apple status."""
        monitor = VRAMMonitor.__new__(VRAMMonitor)
        monitor._vendor = GPUVendor.APPLE
        monitor._available = True
        
        with patch('asyncio.create_subprocess_exec', side_effect=Exception("Process failed")):
            status = await monitor._get_apple_status()
            assert status.gpus == []

    def test_vendor_property_with_none(self):
        """Test vendor property when _vendor is None."""
        monitor = VRAMMonitor.__new__(VRAMMonitor)
        monitor._vendor = None
        
        assert monitor.vendor == GPUVendor.UNKNOWN

    @pytest.mark.asyncio
    async def test_get_status_unknown_vendor(self):
        """Test get_status with unknown vendor."""
        monitor = VRAMMonitor.__new__(VRAMMonitor)
        monitor._vendor = GPUVendor.UNKNOWN
        monitor._available = True
        
        status = await monitor.get_status()
        
        assert status.gpus == []
        assert status.total_memory_mb == 0
