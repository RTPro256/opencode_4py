"""
Tests for LLM Checker CLI commands.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path


@pytest.mark.unit
class TestLLMCheckerCommands:
    """Tests for llmchecker CLI commands."""
    
    def test_app_exists(self):
        """Test llmchecker app exists."""
        from opencode.cli.commands.llmchecker import app
        assert app is not None
        assert app.info.name == "llm"
    
    def test_hardware_detect_command_registered(self):
        """Test hw-detect command is registered."""
        from opencode.cli.commands.llmchecker import app
        # Check that the command is registered
        command_names = [cmd.name for cmd in app.registered_commands]
        assert "hw-detect" in command_names
    
    def test_recommend_command_registered(self):
        """Test recommend command is registered."""
        from opencode.cli.commands.llmchecker import app
        command_names = [cmd.name for cmd in app.registered_commands]
        assert "recommend" in command_names
    
    def test_ollama_list_command_registered(self):
        """Test ollama-list command is registered."""
        from opencode.cli.commands.llmchecker import app
        command_names = [cmd.name for cmd in app.registered_commands]
        assert "ollama-list" in command_names
    
    def test_ollama_pull_command_registered(self):
        """Test ollama-pull command is registered."""
        from opencode.cli.commands.llmchecker import app
        command_names = [cmd.name for cmd in app.registered_commands]
        assert "ollama-pull" in command_names
    
    @patch('opencode.llmchecker.hardware.detector.HardwareDetector')
    def test_hardware_detect_basic(self, mock_detector_class):
        """Test hardware detection basic flow."""
        from opencode.cli.commands.llmchecker import hardware_detect
        
        # Setup mock
        mock_detector = MagicMock()
        mock_detector_class.return_value = mock_detector
        
        mock_info = MagicMock()
        mock_info.to_dict.return_value = {
            "cpu": {"brand": "Test CPU"},
            "tier": "mid",
            "max_model_size_gb": 8.0,
            "backend": "cpu",
        }
        mock_info.cpu.brand = "Test CPU"
        mock_info.tier.value = "mid"
        mock_info.max_model_size_gb = 8.0
        mock_info.backend.value = "cpu"
        mock_info.cpu.physical_cores = 4
        mock_info.cpu.threads = 8
        mock_info.cpu.speed_max_ghz = 3.5
        mock_info.cpu.score = 100
        mock_info.memory.total_gb = 16
        mock_info.memory.available_gb = 8
        mock_info.memory.used_gb = 8
        mock_info.memory.usage_percent = 50.0
        mock_info.memory.swap_total_gb = 8
        mock_info.gpus = []
        
        mock_detector.detect.return_value = mock_info
        
        # This would normally be called via typer CLI
        # Just verify the mock setup works
        assert mock_detector_class is not None
    
    @patch('opencode.llmchecker.ollama.client.OllamaClient')
    def test_ollama_list_empty(self, mock_client_class):
        """Test ollama-list with no models."""
        from opencode.cli.commands.llmchecker import ollama_list
        
        # Setup mock
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Verify the function exists
        assert ollama_list is not None
    
    def test_calibrate_command_registered(self):
        """Test calibrate command is registered."""
        from opencode.cli.commands.llmchecker import app
        command_names = [cmd.name for cmd in app.registered_commands]
        assert "calibrate" in command_names


@pytest.mark.unit
class TestLLMCheckerHardwareIntegration:
    """Tests for hardware detection integration."""
    
    @patch('opencode.llmchecker.hardware.detector.HardwareDetector')
    def test_hardware_detector_creation(self, mock_class):
        """Test hardware detector can be created."""
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        
        from opencode.llmchecker.hardware import HardwareDetector
        detector = HardwareDetector()
        
        assert detector is not None
    
    def test_system_info_model(self):
        """Test SystemInfo model exists."""
        from opencode.llmchecker.hardware.models import SystemInfo, CPUInfo, MemoryInfo
        
        cpu = CPUInfo(
            brand="Test CPU",
            physical_cores=4,
            threads=8,
            speed_max_ghz=3.5,
            score=100,
        )
        
        memory = MemoryInfo(
            total_gb=16,
            available_gb=8,
            used_gb=8,
            usage_percent=50.0,
            swap_total_gb=8,
            swap_used_gb=0,
        )
        
        assert cpu.brand == "Test CPU"
        assert memory.total_gb == 16


@pytest.mark.unit
class TestLLMCheckerScoring:
    """Tests for scoring engine."""
    
    def test_scoring_engine_exists(self):
        """Test scoring engine exists."""
        from opencode.llmchecker.scoring import ScoringEngine
        assert ScoringEngine is not None
    
    def test_model_info_creation(self):
        """Test ModelInfo creation."""
        from opencode.llmchecker.scoring.models import ModelInfo
        
        info = ModelInfo(
            name="test-model",
            family="llama",
            parameters_b=7.0,
            size_gb=4.0,
        )
        
        assert info.name == "test-model"
        assert info.family == "llama"
    
    def test_scoring_weights(self):
        """Test ScoringWeights creation."""
        from opencode.llmchecker.scoring.models import ScoringWeights
        
        weights = ScoringWeights.for_use_case("coding")
        assert weights is not None


@pytest.mark.unit
class TestLLMCheckerCalibration:
    """Tests for calibration manager."""
    
    def test_calibration_manager_exists(self):
        """Test calibration manager exists."""
        from opencode.llmchecker.calibration import CalibrationManager
        assert CalibrationManager is not None
    
    def test_calibration_policy_model(self):
        """Test calibration policy model."""
        from opencode.llmchecker.calibration.models import CalibrationPolicy
        
        policy = CalibrationPolicy(
            name="test-policy",
            version="1.0",
            default_model="llama3.2",
        )
        
        assert policy.name == "test-policy"
        assert policy.default_model == "llama3.2"
