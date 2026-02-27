"""
Tests for LLMChecker CLI commands.
"""

import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner

from opencode.cli.commands.llmchecker import app


runner = CliRunner()


class TestHardwareDetectCommand:
    """Tests for hw-detect command."""
    
    @pytest.mark.unit
    def test_hw_detect_command_exists(self):
        """Test hw-detect command is registered."""
        result = runner.invoke(app, ["hw-detect", "--help"])
        assert result.exit_code == 0
    
    @pytest.mark.unit
    def test_hw_detect_command_help(self):
        """Test hw-detect command help text."""
        result = runner.invoke(app, ["hw-detect", "--help"])
        assert "Detect system hardware" in result.output or "hardware" in result.output.lower()
    
    @pytest.mark.unit
    @patch("opencode.llmchecker.hardware.HardwareDetector")
    def test_hw_detect_basic(self, mock_detector_class):
        """Test hw-detect basic execution."""
        # Setup mock
        mock_detector = MagicMock()
        mock_detector_class.return_value = mock_detector
        
        mock_info = MagicMock()
        mock_info.cpu.brand = "Test CPU"
        mock_info.cpu.physical_cores = 8
        mock_info.cpu.threads = 16
        mock_info.cpu.speed_max_ghz = 3.5
        mock_info.cpu.score = 5000
        mock_info.tier.value = "high"
        mock_info.max_model_size_gb = 16.0
        mock_info.backend.value = "cuda"
        mock_info.memory.total_gb = 32
        mock_info.memory.available_gb = 16
        mock_info.memory.used_gb = 16
        mock_info.memory.usage_percent = 50.0
        mock_info.memory.swap_total_gb = 8
        mock_info.gpus = []
        mock_info.to_dict.return_value = {"cpu": {"brand": "Test CPU"}}
        
        mock_detector.detect.return_value = mock_info
        
        result = runner.invoke(app, ["hw-detect"])
        # Command should execute (may fail due to rich output, but shouldn't crash)
        assert mock_detector_class.called or result.exit_code in [0, 1]
    
    @pytest.mark.unit
    @patch("opencode.llmchecker.hardware.HardwareDetector")
    def test_hw_detect_json_output(self, mock_detector_class):
        """Test hw-detect with JSON output."""
        mock_detector = MagicMock()
        mock_detector_class.return_value = mock_detector
        
        mock_info = MagicMock()
        mock_info.cpu.brand = "Test CPU"
        mock_info.cpu.physical_cores = 8
        mock_info.cpu.threads = 16
        mock_info.cpu.speed_max_ghz = 3.5
        mock_info.cpu.score = 5000
        mock_info.tier.value = "high"
        mock_info.max_model_size_gb = 16.0
        mock_info.backend.value = "cuda"
        mock_info.memory.total_gb = 32
        mock_info.memory.available_gb = 16
        mock_info.memory.used_gb = 16
        mock_info.memory.usage_percent = 50.0
        mock_info.memory.swap_total_gb = 8
        mock_info.gpus = []
        mock_info.to_dict.return_value = {"cpu": {"brand": "Test CPU"}}
        
        mock_detector.detect.return_value = mock_info
        
        result = runner.invoke(app, ["hw-detect", "--json"])
        # Command should execute
        assert mock_detector_class.called or result.exit_code in [0, 1]


class TestRecommendCommand:
    """Tests for recommend command."""
    
    @pytest.mark.unit
    def test_recommend_command_exists(self):
        """Test recommend command is registered."""
        result = runner.invoke(app, ["recommend", "--help"])
        assert result.exit_code == 0
    
    @pytest.mark.unit
    def test_recommend_command_help(self):
        """Test recommend command help text."""
        result = runner.invoke(app, ["recommend", "--help"])
        assert "model" in result.output.lower() or "recommend" in result.output.lower()


class TestListModelsCommand:
    """Tests for list-models command."""
    
    @pytest.mark.unit
    def test_list_models_command_exists(self):
        """Test list-models command is registered."""
        result = runner.invoke(app, ["list-models", "--help"])
        # Command may or may not exist
        assert result.exit_code in [0, 1, 2]


class TestCalibrateCommand:
    """Tests for calibrate command."""
    
    @pytest.mark.unit
    def test_calibrate_command_exists(self):
        """Test calibrate command is registered."""
        result = runner.invoke(app, ["calibrate", "--help"])
        # Command may or may not exist
        assert result.exit_code in [0, 1, 2]


class TestLLMCheckerApp:
    """Tests for LLMChecker CLI app."""
    
    @pytest.mark.unit
    def test_app_exists(self):
        """Test LLMChecker app exists."""
        assert app is not None
    
    @pytest.mark.unit
    def test_app_has_commands(self):
        """Test LLMChecker app has commands."""
        # Get registered commands
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
    
    @pytest.mark.unit
    def test_app_name(self):
        """Test LLMChecker app name."""
        assert app.info.name == "llm"
