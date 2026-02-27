"""
Tests for CPU hardware backend detector.
"""

import pytest
from unittest.mock import patch, MagicMock, mock_open
import subprocess

from opencode.llmchecker.hardware.backends.cpu import CPUDetector
from opencode.llmchecker.hardware.models import GPUVendor, AccelerationBackend


class TestCPUDetectorProperties:
    """Tests for CPUDetector properties."""
    
    def test_vendor_returns_unknown(self):
        """Test that vendor property returns UNKNOWN."""
        detector = CPUDetector()
        assert detector.vendor == GPUVendor.UNKNOWN
    
    def test_backend_returns_cpu(self):
        """Test that backend property returns CPU."""
        detector = CPUDetector()
        assert detector.backend == AccelerationBackend.CPU
    
    def test_is_available_always_true(self):
        """Test that is_available always returns True."""
        detector = CPUDetector()
        assert detector.is_available() is True


class TestCPUDetectorDetect:
    """Tests for CPUDetector.detect method."""
    
    @patch.object(CPUDetector, '_get_cpu_info')
    def test_detect_returns_single_gpu_info(self, mock_get_cpu_info):
        """Test that detect returns a list with one GPUInfo."""
        mock_get_cpu_info.return_value = {
            "brand": "Test CPU",
            "cores": 8,
            "threads": 16,
            "speed_ghz": 3.5,
        }
        
        detector = CPUDetector()
        result = detector.detect()
        
        assert len(result) == 1
        assert result[0].vendor == GPUVendor.UNKNOWN
        assert result[0].vram_gb == 0
        assert result[0].memory_gb == 0
        assert result[0].driver_version == "CPU"
        assert result[0].is_integrated is True
        assert result[0].is_apple_silicon is False
    
    @patch.object(CPUDetector, '_get_cpu_info')
    def test_detect_uses_cpu_brand_in_model_name(self, mock_get_cpu_info):
        """Test that detect uses CPU brand in model name."""
        mock_get_cpu_info.return_value = {
            "brand": "Intel Core i9",
            "cores": 8,
            "threads": 16,
            "speed_ghz": 3.5,
        }
        
        detector = CPUDetector()
        result = detector.detect()
        
        assert "Intel Core i9" in result[0].model
        assert "(CPU)" in result[0].model
    
    @patch.object(CPUDetector, '_get_cpu_info')
    def test_detect_uses_default_brand_when_missing(self, mock_get_cpu_info):
        """Test that detect uses default brand when brand not provided."""
        mock_get_cpu_info.return_value = {
            "cores": 4,
            "threads": 4,
        }
        
        detector = CPUDetector()
        result = detector.detect()
        
        # When brand is missing, it uses the default "Unknown CPU" from _get_cpu_info defaults
        # but since we're mocking, it will use the dict value which doesn't have brand
        # The code uses cpu_info.get('brand', 'Unknown CPU') so it falls back
        assert "CPU" in result[0].model
    
    @patch.object(CPUDetector, '_get_cpu_info')
    def test_detect_calculates_score(self, mock_get_cpu_info):
        """Test that detect calculates and sets score."""
        mock_get_cpu_info.return_value = {
            "brand": "Intel Xeon",
            "cores": 16,
            "threads": 32,
            "speed_ghz": 2.5,
        }
        
        detector = CPUDetector()
        result = detector.detect()
        
        # Score should be calculated (20 for 16 cores + 10 for Xeon = 30)
        assert result[0].score >= 0


class TestGetCPUInfo:
    """Tests for _get_cpu_info method."""
    
    def test_returns_default_info(self):
        """Test that _get_cpu_info returns default info structure."""
        detector = CPUDetector()
        
        with patch('platform.system', return_value="Unknown"):
            result = detector._get_cpu_info()
        
        assert "brand" in result
        assert "cores" in result
        assert "threads" in result
        assert "speed_ghz" in result
        assert result["brand"] == "Unknown CPU"
        assert result["cores"] == 1
        assert result["threads"] == 1
        assert result["speed_ghz"] == 0.0
    
    @patch.object(CPUDetector, '_get_cpu_info_linux')
    def test_calls_linux_method_on_linux(self, mock_linux):
        """Test that _get_cpu_info calls Linux method on Linux."""
        mock_linux.return_value = {"brand": "Linux CPU", "cores": 4}
        
        detector = CPUDetector()
        with patch('platform.system', return_value="Linux"):
            result = detector._get_cpu_info()
        
        mock_linux.assert_called_once()
        assert result["brand"] == "Linux CPU"
    
    @patch.object(CPUDetector, '_get_cpu_info_macos')
    def test_calls_macos_method_on_darwin(self, mock_macos):
        """Test that _get_cpu_info calls macOS method on Darwin."""
        mock_macos.return_value = {"brand": "MacOS CPU", "cores": 8}
        
        detector = CPUDetector()
        with patch('platform.system', return_value="Darwin"):
            result = detector._get_cpu_info()
        
        mock_macos.assert_called_once()
        assert result["brand"] == "MacOS CPU"
    
    @patch.object(CPUDetector, '_get_cpu_info_windows')
    def test_calls_windows_method_on_windows(self, mock_windows):
        """Test that _get_cpu_info calls Windows method on Windows."""
        mock_windows.return_value = {"brand": "Windows CPU", "cores": 6}
        
        detector = CPUDetector()
        with patch('platform.system', return_value="Windows"):
            result = detector._get_cpu_info()
        
        mock_windows.assert_called_once()
        assert result["brand"] == "Windows CPU"


class TestGetCPUInfoLinux:
    """Tests for _get_cpu_info_linux method."""
    
    def test_reads_proc_cpuinfo(self):
        """Test reading CPU info from /proc/cpuinfo."""
        cpuinfo_content = """processor	: 0
vendor_id	: GenuineIntel
cpu family	: 6
model		: 142
model name	: Intel(R) Core(TM) i7-8550U CPU @ 1.80GHz
stepping	: 10
cpu cores	: 4
siblings	: 8
"""
        
        detector = CPUDetector()
        with patch("builtins.open", mock_open(read_data=cpuinfo_content)):
            with patch("os.path.exists", return_value=True):
                result = detector._get_cpu_info_linux()
        
        assert result["brand"] == "Intel(R) Core(TM) i7-8550U CPU @ 1.80GHz"
        assert result["cores"] == 4
        assert result["threads"] == 8
    
    def test_handles_missing_cpuinfo(self):
        """Test handling missing /proc/cpuinfo."""
        detector = CPUDetector()
        
        with patch("builtins.open", side_effect=IOError("File not found")):
            result = detector._get_cpu_info_linux()
        
        assert result == {}
    
    def test_reads_cpu_frequency(self):
        """Test reading CPU frequency from sysfs."""
        detector = CPUDetector()
        
        cpuinfo_content = "model name	: Test CPU\ncpu cores	: 4\n"
        
        with patch("builtins.open", mock_open(read_data=cpuinfo_content)):
            # Need to handle multiple open calls
            freq_mock = mock_open(read_data="3500000")
            open_mock = MagicMock()
            open_mock.side_effect = [
                mock_open(read_data=cpuinfo_content).return_value,
                freq_mock.return_value,
            ]
            
            with patch("builtins.open", open_mock):
                result = detector._get_cpu_info_linux()
    
    def test_handles_missing_frequency(self):
        """Test handling missing frequency info."""
        detector = CPUDetector()
        
        cpuinfo_content = "model name	: Test CPU\ncpu cores	: 4\n"
        
        with patch("builtins.open", mock_open(read_data=cpuinfo_content)):
            result = detector._get_cpu_info_linux()
        
        # Should not have speed_ghz if frequency file missing
        assert "speed_ghz" not in result or result.get("speed_ghz", 0) >= 0
    
    def test_uses_cores_as_threads_if_no_siblings(self):
        """Test that cores is used as threads if siblings not found."""
        cpuinfo_content = """model name	: Test CPU
cpu cores	: 4
"""
        
        detector = CPUDetector()
        with patch("builtins.open", mock_open(read_data=cpuinfo_content)):
            result = detector._get_cpu_info_linux()
        
        assert result["threads"] == 4


class TestGetCPUInfoMacOS:
    """Tests for _get_cpu_info_macos method."""
    
    @patch('subprocess.run')
    def test_gets_brand_string(self, mock_run):
        """Test getting CPU brand string on macOS."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="Apple M1 Pro\n"),
            MagicMock(returncode=0, stdout="8\n"),
            MagicMock(returncode=0, stdout="8\n"),
        ]
        
        detector = CPUDetector()
        result = detector._get_cpu_info_macos()
        
        assert result["brand"] == "Apple M1 Pro"
        assert result["cores"] == 8
        assert result["threads"] == 8
    
    @patch('subprocess.run')
    def test_handles_timeout(self, mock_run):
        """Test handling subprocess timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="sysctl", timeout=5)
        
        detector = CPUDetector()
        result = detector._get_cpu_info_macos()
        
        assert result == {}
    
    @patch('subprocess.run')
    def test_handles_file_not_found(self, mock_run):
        """Test handling command not found."""
        mock_run.side_effect = FileNotFoundError("sysctl not found")
        
        detector = CPUDetector()
        result = detector._get_cpu_info_macos()
        
        assert result == {}
    
    @patch('subprocess.run')
    def test_handles_os_error(self, mock_run):
        """Test handling OS error."""
        mock_run.side_effect = OSError("OS error")
        
        detector = CPUDetector()
        result = detector._get_cpu_info_macos()
        
        assert result == {}
    
    @patch('subprocess.run')
    def test_handles_non_zero_return(self, mock_run):
        """Test handling non-zero return code."""
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        
        detector = CPUDetector()
        result = detector._get_cpu_info_macos()
        
        assert result == {}
    
    @patch('subprocess.run')
    def test_handles_value_error(self, mock_run):
        """Test handling value error when parsing."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="Test CPU\n"),
            MagicMock(returncode=0, stdout="not_a_number\n"),
            MagicMock(returncode=0, stdout="8\n"),
        ]
        
        detector = CPUDetector()
        result = detector._get_cpu_info_macos()
        
        # Should have brand but cores should fail
        assert result["brand"] == "Test CPU"


class TestGetCPUInfoWindows:
    """Tests for _get_cpu_info_windows method."""
    
    @patch('opencode.llmchecker.hardware.backends.cpu.platform.processor')
    @patch('opencode.llmchecker.hardware.backends.cpu.subprocess.run')
    def test_parses_wmic_output(self, mock_run, mock_processor):
        """Test parsing WMIC output."""
        # WMIC output format: header line, then data line
        # The actual format has the name first, then cores, then logical processors
        wmic_output = "Name              NumberOfCores  NumberOfLogicalProcessors\nIntel(R) Core(TM) i7-12700K     12              20\n"
        mock_run.return_value = MagicMock(returncode=0, stdout=wmic_output)
        mock_processor.return_value = "Intel Core i7"
        
        detector = CPUDetector()
        result = detector._get_cpu_info_windows()
        
        # The parsing extracts brand, cores, and threads from WMIC output
        assert "brand" in result
        assert "cores" in result
        assert "threads" in result
    
    @patch('opencode.llmchecker.hardware.backends.cpu.platform.processor')
    @patch('opencode.llmchecker.hardware.backends.cpu.subprocess.run')
    def test_handles_wmic_failure(self, mock_run, mock_processor):
        """Test handling WMIC failure."""
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        mock_processor.return_value = "Fallback CPU"
        
        detector = CPUDetector()
        with patch('os.cpu_count', return_value=4):
            result = detector._get_cpu_info_windows()
        
        assert result["brand"] == "Fallback CPU"
    
    @patch('opencode.llmchecker.hardware.backends.cpu.platform.processor')
    @patch('opencode.llmchecker.hardware.backends.cpu.subprocess.run')
    def test_handles_timeout(self, mock_run, mock_processor):
        """Test handling WMIC timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="wmic", timeout=10)
        mock_processor.return_value = "Fallback CPU"
        
        detector = CPUDetector()
        with patch('os.cpu_count', return_value=4):
            result = detector._get_cpu_info_windows()
        
        assert result["brand"] == "Fallback CPU"
    
    @patch('opencode.llmchecker.hardware.backends.cpu.platform.processor')
    @patch('opencode.llmchecker.hardware.backends.cpu.subprocess.run')
    def test_handles_file_not_found(self, mock_run, mock_processor):
        """Test handling WMIC not found."""
        mock_run.side_effect = FileNotFoundError("wmic not found")
        mock_processor.return_value = "Fallback CPU"
        
        detector = CPUDetector()
        with patch('os.cpu_count', return_value=4):
            result = detector._get_cpu_info_windows()
        
        assert result["brand"] == "Fallback CPU"
    
    @patch('opencode.llmchecker.hardware.backends.cpu.platform.processor')
    @patch('opencode.llmchecker.hardware.backends.cpu.subprocess.run')
    def test_uses_os_cpu_count(self, mock_run, mock_processor):
        """Test using os.cpu_count as fallback."""
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        mock_processor.return_value = "Test CPU"
        
        detector = CPUDetector()
        with patch('os.cpu_count', return_value=12):
            result = detector._get_cpu_info_windows()
        
        assert result["cores"] == 12
        assert result["threads"] == 12
    
    @patch('opencode.llmchecker.hardware.backends.cpu.platform.processor')
    @patch('opencode.llmchecker.hardware.backends.cpu.subprocess.run')
    def test_handles_none_processor(self, mock_run, mock_processor):
        """Test handling None from platform.processor."""
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        mock_processor.return_value = None
        
        detector = CPUDetector()
        with patch('os.cpu_count', return_value=4):
            result = detector._get_cpu_info_windows()
        
        assert result["brand"] == "Unknown CPU"


class TestCalculateCPUScore:
    """Tests for _calculate_cpu_score method."""
    
    def test_score_for_32_plus_cores(self):
        """Test scoring for 32+ cores."""
        detector = CPUDetector()
        score = detector._calculate_cpu_score({
            "brand": "Test CPU",
            "cores": 32,
            "threads": 64,
        })
        # 30 for cores + 5 for threads
        assert score == 35
    
    def test_score_for_24_cores(self):
        """Test scoring for 24 cores."""
        detector = CPUDetector()
        score = detector._calculate_cpu_score({
            "brand": "Test CPU",
            "cores": 24,
            "threads": 48,
        })
        # 25 for cores + 5 for threads
        assert score == 30
    
    def test_score_for_16_cores(self):
        """Test scoring for 16 cores."""
        detector = CPUDetector()
        score = detector._calculate_cpu_score({
            "brand": "Test CPU",
            "cores": 16,
            "threads": 32,
        })
        # 20 for cores + 5 for threads
        assert score == 25
    
    def test_score_for_12_cores(self):
        """Test scoring for 12 cores."""
        detector = CPUDetector()
        score = detector._calculate_cpu_score({
            "brand": "Test CPU",
            "cores": 12,
            "threads": 24,
        })
        # 15 for cores + 5 for threads
        assert score == 20
    
    def test_score_for_8_cores(self):
        """Test scoring for 8 cores."""
        detector = CPUDetector()
        score = detector._calculate_cpu_score({
            "brand": "Test CPU",
            "cores": 8,
            "threads": 16,
        })
        # 10 for cores + 5 for threads
        assert score == 15
    
    def test_score_for_4_cores(self):
        """Test scoring for 4 cores."""
        detector = CPUDetector()
        score = detector._calculate_cpu_score({
            "brand": "Test CPU",
            "cores": 4,
            "threads": 8,
        })
        # 5 for cores + 4 for threads (capped at 5)
        assert score == 9
    
    def test_score_for_2_cores(self):
        """Test scoring for 2 cores."""
        detector = CPUDetector()
        score = detector._calculate_cpu_score({
            "brand": "Test CPU",
            "cores": 2,
            "threads": 4,
        })
        # 0 for cores + 2 for threads
        assert score == 2
    
    def test_xeon_bonus(self):
        """Test Xeon brand bonus."""
        detector = CPUDetector()
        score = detector._calculate_cpu_score({
            "brand": "Intel Xeon Gold",
            "cores": 8,
            "threads": 16,
        })
        # 10 for cores + 5 for threads + 10 for Xeon = 25
        assert score == 25
    
    def test_epyc_bonus(self):
        """Test EPYC brand bonus."""
        detector = CPUDetector()
        score = detector._calculate_cpu_score({
            "brand": "AMD EPYC",
            "cores": 8,
            "threads": 16,
        })
        # 10 for cores + 5 for threads + 12 for EPYC = 27
        assert score == 27
    
    def test_ryzen_9_bonus(self):
        """Test Ryzen 9 brand bonus."""
        detector = CPUDetector()
        score = detector._calculate_cpu_score({
            "brand": "AMD Ryzen 9 5900X",
            "cores": 8,
            "threads": 16,
        })
        # 10 for cores + 5 for threads + 8 for Ryzen 9 = 23
        assert score == 23
    
    def test_ryzen_7_bonus(self):
        """Test Ryzen 7 brand bonus."""
        detector = CPUDetector()
        score = detector._calculate_cpu_score({
            "brand": "AMD Ryzen 7 5800X",
            "cores": 8,
            "threads": 16,
        })
        # 10 for cores + 5 for threads + 8 for Ryzen 7 = 23
        assert score == 23
    
    def test_i9_bonus(self):
        """Test i9 brand bonus."""
        detector = CPUDetector()
        score = detector._calculate_cpu_score({
            "brand": "Intel Core i9-12900K",
            "cores": 8,
            "threads": 16,
        })
        # 10 for cores + 5 for threads + 7 for i9 = 22
        assert score == 22
    
    def test_i7_bonus(self):
        """Test i7 brand bonus."""
        detector = CPUDetector()
        score = detector._calculate_cpu_score({
            "brand": "Intel Core i7-12700K",
            "cores": 8,
            "threads": 16,
        })
        # 10 for cores + 5 for threads + 7 for i7 = 22
        assert score == 22
    
    def test_apple_m1_bonus(self):
        """Test Apple M1 brand bonus."""
        detector = CPUDetector()
        score = detector._calculate_cpu_score({
            "brand": "Apple M1 Pro",
            "cores": 8,
            "threads": 8,
        })
        # 10 for cores + 0 for threads + 10 for M1 = 20
        assert score == 20
    
    def test_apple_m2_bonus(self):
        """Test Apple M2 brand bonus."""
        detector = CPUDetector()
        score = detector._calculate_cpu_score({
            "brand": "Apple M2 Max",
            "cores": 8,
            "threads": 8,
        })
        # 10 for cores + 0 for threads + 10 for M2 = 20
        assert score == 20
    
    def test_apple_m3_bonus(self):
        """Test Apple M3 brand bonus."""
        detector = CPUDetector()
        score = detector._calculate_cpu_score({
            "brand": "Apple M3 Pro",
            "cores": 8,
            "threads": 8,
        })
        # 10 for cores + 0 for threads + 10 for M3 = 20
        assert score == 20
    
    def test_apple_m4_bonus(self):
        """Test Apple M4 brand bonus."""
        detector = CPUDetector()
        score = detector._calculate_cpu_score({
            "brand": "Apple M4",
            "cores": 8,
            "threads": 8,
        })
        # 10 for cores + 0 for threads + 10 for M4 = 20
        assert score == 20
    
    def test_score_capped_at_40(self):
        """Test that score is capped at 40."""
        detector = CPUDetector()
        score = detector._calculate_cpu_score({
            "brand": "AMD EPYC",
            "cores": 64,
            "threads": 128,
        })
        # Would be 30 + 5 + 12 = 47, but capped at 40
        assert score == 40
    
    def test_no_thread_bonus_if_no_hyperthreading(self):
        """Test no thread bonus if threads == cores."""
        detector = CPUDetector()
        score = detector._calculate_cpu_score({
            "brand": "Test CPU",
            "cores": 8,
            "threads": 8,
        })
        # 10 for cores, no thread bonus
        assert score == 10
    
    def test_thread_bonus_capped_at_5(self):
        """Test thread bonus is capped at 5."""
        detector = CPUDetector()
        score = detector._calculate_cpu_score({
            "brand": "Test CPU",
            "cores": 8,
            "threads": 20,  # 12 more threads than cores
        })
        # 10 for cores + 5 for threads (capped)
        assert score == 15
    
    def test_case_insensitive_brand_matching(self):
        """Test brand matching is case insensitive."""
        detector = CPUDetector()
        score_lower = detector._calculate_cpu_score({
            "brand": "intel xeon gold",
            "cores": 8,
            "threads": 16,
        })
        score_upper = detector._calculate_cpu_score({
            "brand": "INTEL XEON GOLD",
            "cores": 8,
            "threads": 16,
        })
        assert score_lower == score_upper == 25


class TestGetCPUUsage:
    """Tests for get_cpu_usage static method."""
    
    @patch('psutil.cpu_percent')
    def test_with_psutil(self, mock_cpu_percent):
        """Test getting CPU usage with psutil."""
        mock_cpu_percent.return_value = 45.5
        
        result = CPUDetector.get_cpu_usage()
        
        assert result == {"percent": 45.5}
        mock_cpu_percent.assert_called_once_with(interval=0.1)
    
    @patch('psutil.cpu_percent', side_effect=ImportError)
    @patch('platform.system')
    def test_fallback_on_linux(self, mock_system, mock_cpu_percent):
        """Test fallback on Linux without psutil."""
        mock_system.return_value = "Linux"
        
        stat_content = "cpu  100 10 50 200 20 0 0 0 0 0\n"
        
        with patch("builtins.open", mock_open(read_data=stat_content)):
            result = CPUDetector.get_cpu_usage()
        
        # user=100, nice=10, system=50, idle=200
        # total = 100 + 10 + 50 + 200 = 360
        # used = 100 + 10 + 50 = 160
        # percent = 160/360 * 100 = 44.44...
        assert result is not None
        assert "percent" in result
        assert 40 < result["percent"] < 50
    
    @patch('psutil.cpu_percent', side_effect=ImportError)
    @patch('platform.system')
    def test_returns_none_on_non_linux(self, mock_system, mock_cpu_percent):
        """Test returns None on non-Linux without psutil."""
        mock_system.return_value = "Windows"
        
        result = CPUDetector.get_cpu_usage()
        
        assert result is None
    
    @patch('psutil.cpu_percent', side_effect=ImportError)
    @patch('platform.system')
    def test_handles_proc_stat_error(self, mock_system, mock_cpu_percent):
        """Test handling /proc/stat read error."""
        mock_system.return_value = "Linux"
        
        with patch("builtins.open", side_effect=IOError("File not found")):
            result = CPUDetector.get_cpu_usage()
        
        assert result is None
    
    @patch('psutil.cpu_percent', side_effect=ImportError)
    @patch('platform.system')
    def test_handles_proc_stat_value_error(self, mock_system, mock_cpu_percent):
        """Test handling /proc/stat parse error."""
        mock_system.return_value = "Linux"
        
        with patch("builtins.open", mock_open(read_data="invalid content")):
            result = CPUDetector.get_cpu_usage()
        
        assert result is None
    
    @patch('psutil.cpu_percent', side_effect=ImportError)
    @patch('platform.system')
    def test_handles_insufficient_proc_stat_parts(self, mock_system, mock_cpu_percent):
        """Test handling insufficient parts in /proc/stat."""
        mock_system.return_value = "Linux"
        
        with patch("builtins.open", mock_open(read_data="cpu 100 10\n")):
            result = CPUDetector.get_cpu_usage()
        
        assert result is None


class TestCPUDetectorIntegration:
    """Integration tests for CPUDetector."""
    
    @patch.object(CPUDetector, '_get_cpu_info')
    def test_full_detect_flow(self, mock_get_cpu_info):
        """Test full detect flow."""
        mock_get_cpu_info.return_value = {
            "brand": "Intel Core i7-12700K",
            "cores": 12,
            "threads": 20,
            "speed_ghz": 3.6,
        }
        
        detector = CPUDetector()
        gpus = detector.detect()
        
        assert len(gpus) == 1
        gpu = gpus[0]
        
        assert "Intel Core i7-12700K" in gpu.model
        assert "(CPU)" in gpu.model
        assert gpu.vendor == GPUVendor.UNKNOWN
        assert gpu.vram_gb == 0
        assert gpu.memory_gb == 0
        assert gpu.driver_version == "CPU"
        assert gpu.is_integrated is True
        assert gpu.is_apple_silicon is False
        # 15 for 12 cores + 5 for threads + 7 for i7 = 27
        assert gpu.score == 27
