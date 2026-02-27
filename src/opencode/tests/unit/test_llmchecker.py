"""
Tests for LLM checker module.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from opencode.llmchecker import calibration, hardware, ollama, scoring
from opencode.llmchecker.calibration import manager as calibration_manager, models as calibration_models
from opencode.llmchecker.hardware import detector, models as hardware_models
from opencode.llmchecker.hardware.backends import apple, cpu, cuda, intel, rocm
from opencode.llmchecker.ollama import client, models as ollama_models
from opencode.llmchecker.scoring import engine as scoring_engine, models as scoring_models


@pytest.mark.unit
class TestCalibration:
    """Tests for calibration module."""
    
    def test_calibration_module_exists(self):
        """Test calibration module exists."""
        assert calibration is not None
    
    def test_calibration_manager_exists(self):
        """Test calibration manager exists."""
        assert calibration_manager is not None
    
    def test_calibration_models_exists(self):
        """Test calibration models exists."""
        assert calibration_models is not None


@pytest.mark.unit
class TestHardware:
    """Tests for hardware module."""
    
    def test_hardware_module_exists(self):
        """Test hardware module exists."""
        assert hardware is not None
    
    def test_detector_exists(self):
        """Test detector exists."""
        assert detector is not None
    
    def test_hardware_models_exists(self):
        """Test hardware models exists."""
        assert hardware_models is not None


@pytest.mark.unit
class TestHardwareBackends:
    """Tests for hardware backends."""
    
    def test_apple_backend_exists(self):
        """Test apple backend exists."""
        assert apple is not None
    
    def test_cpu_backend_exists(self):
        """Test cpu backend exists."""
        assert cpu is not None
    
    def test_cuda_backend_exists(self):
        """Test cuda backend exists."""
        assert cuda is not None
    
    def test_intel_backend_exists(self):
        """Test intel backend exists."""
        assert intel is not None
    
    def test_rocm_backend_exists(self):
        """Test rocm backend exists."""
        assert rocm is not None


@pytest.mark.unit
class TestOllamaChecker:
    """Tests for Ollama checker module."""
    
    def test_ollama_module_exists(self):
        """Test ollama module exists."""
        assert ollama is not None
    
    def test_ollama_client_exists(self):
        """Test ollama client exists."""
        assert client is not None
    
    def test_ollama_models_exists(self):
        """Test ollama models exists."""
        assert ollama_models is not None


@pytest.mark.unit
class TestScoring:
    """Tests for scoring module."""
    
    def test_scoring_module_exists(self):
        """Test scoring module exists."""
        assert scoring is not None
    
    def test_scoring_engine_exists(self):
        """Test scoring engine exists."""
        assert scoring_engine is not None
    
    def test_scoring_models_exists(self):
        """Test scoring models exists."""
        assert scoring_models is not None
