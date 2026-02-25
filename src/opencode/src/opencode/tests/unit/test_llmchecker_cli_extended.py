"""
Extended tests for LLM Checker CLI commands.

Tests all CLI commands with mocked dependencies.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import tempfile
import json


@pytest.fixture
def mock_hardware_detector():
    """Mock HardwareDetector."""
    with patch("opencode.llmchecker.hardware.HardwareDetector") as mock:
        detector = MagicMock()
        
        # Create mock system info
        system_info = MagicMock()
        system_info.cpu.brand = "Test CPU"
        system_info.cpu.physical_cores = 8
        system_info.cpu.threads = 16
        system_info.cpu.speed_max_ghz = 3.5
        system_info.cpu.score = 5000
        system_info.tier.value = "mid"
        system_info.max_model_size_gb = 8.0
        system_info.backend.value = "cuda"
        
        system_info.memory.total_gb = 32
        system_info.memory.available_gb = 16
        system_info.memory.used_gb = 16
        system_info.memory.usage_percent = 50.0
        system_info.memory.swap_total_gb = 8
        
        system_info.gpus = []
        
        system_info.to_dict.return_value = {
            "cpu": {"brand": "Test CPU"},
            "tier": "mid",
            "max_model_size_gb": 8.0,
            "backend": "cuda",
        }
        
        detector.detect.return_value = system_info
        mock.return_value = detector
        yield detector


@pytest.fixture
def mock_ollama_client():
    """Mock OllamaClient."""
    with patch("opencode.llmchecker.ollama.OllamaClient") as mock:
        client = MagicMock()
        
        # Mock model
        model = MagicMock()
        model.name = "llama3.2:3b"
        model.family = "llama"
        model.parameters_b = 3.2
        model.size_gb = 2.0
        model.parameter_size = "3B"
        model.quantization_level = "Q4_0"
        model.to_dict.return_value = {
            "name": "llama3.2:3b",
            "family": "llama",
            "size_gb": 2.0,
        }
        
        # Setup async methods
        client.list_models = AsyncMock(return_value=[model])
        client.check_availability = AsyncMock(return_value={"available": True})
        client.pull_model = AsyncMock()
        client.generate = AsyncMock()
        client.is_huggingface_model = MagicMock(return_value=False)
        client._normalize_model_name = MagicMock(return_value="llama3.2:3b")
        
        mock.return_value = client
        yield client


@pytest.fixture
def mock_calibration_manager():
    """Mock CalibrationManager."""
    with patch("opencode.llmchecker.calibration.CalibrationManager") as mock:
        manager = MagicMock()
        
        # Mock policy
        policy = MagicMock()
        policy.name = "test-policy"
        policy.default_model = "llama3.2:3b"
        policy.calibration_id = "test-123"
        policy.rules = []
        policy.get_model_for_task.return_value = "llama3.2:3b"
        
        manager.load_policy.return_value = policy
        manager.discover_policy.return_value = policy
        manager.save_policy = MagicMock()
        
        # Mock calibration result
        result = MagicMock()
        result.best_model = "llama3.2:3b"
        result.duration_seconds = 10.0
        result.model_results = []
        
        manager.run_calibration = AsyncMock(return_value=result)
        manager.parse_prompt_suite.return_value = [{"prompt": "test"}]
        manager.generate_policy.return_value = policy
        manager.save_result = MagicMock()
        
        mock.return_value = manager
        yield manager


class TestHardwareDetectCommand:
    """Tests for hw-detect command."""
    
    def test_hardware_detect_default(self, mock_hardware_detector):
        """Test hardware detection with default output."""
        from typer.testing import CliRunner
        from opencode.cli.commands.llmchecker import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["hw-detect"])
        
        assert result.exit_code == 0
        assert "Test CPU" in result.output or "System Summary" in result.output
    
    def test_hardware_detect_json_output(self, mock_hardware_detector):
        """Test hardware detection with JSON output."""
        from typer.testing import CliRunner
        from opencode.cli.commands.llmchecker import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["hw-detect", "--json"])
        
        assert result.exit_code == 0
    
    def test_hardware_detect_force_refresh(self, mock_hardware_detector):
        """Test hardware detection with force refresh."""
        from typer.testing import CliRunner
        from opencode.cli.commands.llmchecker import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["hw-detect", "--force"])
        
        assert result.exit_code == 0
        mock_hardware_detector.detect.assert_called_once_with(force_refresh=True)


class TestRecommendCommand:
    """Tests for recommend command."""
    
    def test_recommend_models_default(self, mock_hardware_detector, mock_ollama_client):
        """Test model recommendations with default settings."""
        from typer.testing import CliRunner
        from opencode.cli.commands.llmchecker import app
        from opencode.llmchecker.scoring import ScoringEngine
        
        with patch.object(ScoringEngine, "score_models") as mock_score:
            score_result = MagicMock()
            score_result.get_top_n.return_value = []
            mock_score.return_value = score_result
            
            runner = CliRunner()
            result = runner.invoke(app, ["recommend"])
            
            assert result.exit_code == 0
    
    def test_recommend_models_json_output(self, mock_hardware_detector, mock_ollama_client):
        """Test model recommendations with JSON output."""
        from typer.testing import CliRunner
        from opencode.cli.commands.llmchecker import app
        from opencode.llmchecker.scoring import ScoringEngine
        
        with patch.object(ScoringEngine, "score_models") as mock_score:
            score_result = MagicMock()
            score_result.get_top_n.return_value = []
            mock_score.return_value = score_result
            
            runner = CliRunner()
            result = runner.invoke(app, ["recommend", "--json"])
            
            assert result.exit_code == 0
    
    def test_recommend_models_with_category(self, mock_hardware_detector, mock_ollama_client):
        """Test model recommendations with specific category."""
        from typer.testing import CliRunner
        from opencode.cli.commands.llmchecker import app
        from opencode.llmchecker.scoring import ScoringEngine, ScoringWeights
        
        with patch.object(ScoringEngine, "score_models") as mock_score:
            score_result = MagicMock()
            score_result.get_top_n.return_value = []
            mock_score.return_value = score_result
            
            with patch.object(ScoringWeights, "for_use_case") as mock_weights:
                mock_weights.return_value = MagicMock()
                
                runner = CliRunner()
                result = runner.invoke(app, ["recommend", "--category", "coding"])
                
                assert result.exit_code == 0
    
    def test_recommend_models_no_models(self, mock_hardware_detector):
        """Test recommendations when no models installed."""
        from typer.testing import CliRunner
        from opencode.cli.commands.llmchecker import app
        
        with patch("opencode.llmchecker.ollama.OllamaClient") as mock:
            client = MagicMock()
            client.list_models = AsyncMock(return_value=[])
            mock.return_value = client
            
            runner = CliRunner()
            result = runner.invoke(app, ["recommend"])
            
            assert result.exit_code == 0
            assert "No models found" in result.output


class TestOllamaListCommand:
    """Tests for ollama-list command."""
    
    def test_ollama_list_default(self, mock_ollama_client):
        """Test listing Ollama models."""
        from typer.testing import CliRunner
        from opencode.cli.commands.llmchecker import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["ollama-list"])
        
        assert result.exit_code == 0
    
    def test_ollama_list_json_output(self, mock_ollama_client):
        """Test listing Ollama models with JSON output."""
        from typer.testing import CliRunner
        from opencode.cli.commands.llmchecker import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["ollama-list", "--json"])
        
        assert result.exit_code == 0
    
    def test_ollama_list_not_available(self):
        """Test listing when Ollama not available."""
        from typer.testing import CliRunner
        from opencode.cli.commands.llmchecker import app
        
        with patch("opencode.llmchecker.ollama.OllamaClient") as mock:
            client = MagicMock()
            client.check_availability = AsyncMock(return_value={"available": False, "error": "Connection refused"})
            mock.return_value = client
            
            runner = CliRunner()
            result = runner.invoke(app, ["ollama-list"])
            
            assert result.exit_code == 0
            assert "not available" in result.output.lower()
    
    def test_ollama_list_no_models(self):
        """Test listing when no models installed."""
        from typer.testing import CliRunner
        from opencode.cli.commands.llmchecker import app
        
        with patch("opencode.llmchecker.ollama.OllamaClient") as mock:
            client = MagicMock()
            client.check_availability = AsyncMock(return_value={"available": True})
            client.list_models = AsyncMock(return_value=[])
            mock.return_value = client
            
            runner = CliRunner()
            result = runner.invoke(app, ["ollama-list"])
            
            assert result.exit_code == 0
            assert "No models" in result.output


class TestOllamaPullCommand:
    """Tests for ollama-pull command."""
    
    def test_ollama_pull_standard_model(self):
        """Test pulling a standard Ollama model."""
        from typer.testing import CliRunner
        from opencode.cli.commands.llmchecker import app
        
        # Create a proper async generator mock that returns an async iterator
        class AsyncGenMock:
            def __init__(self):
                self.items = [MagicMock(status="success", total=100, percent=100.0)]
                self.index = 0
            
            def __aiter__(self):
                return self
            
            async def __anext__(self):
                if self.index >= len(self.items):
                    raise StopAsyncIteration
                item = self.items[self.index]
                self.index += 1
                return item
        
        # Create mock client with proper async generator
        mock_client = MagicMock()
        mock_client.is_huggingface_model.return_value = False
        mock_client.pull_model.return_value = AsyncGenMock()
        
        with patch("opencode.llmchecker.ollama.OllamaClient", return_value=mock_client):
            runner = CliRunner()
            result = runner.invoke(app, ["ollama-pull", "llama3.2:3b"])
            
            assert result.exit_code == 0
    
    def test_ollama_pull_huggingface_model(self):
        """Test pulling a Hugging Face model."""
        from typer.testing import CliRunner
        from opencode.cli.commands.llmchecker import app
        
        # Create a proper async generator mock that returns an async iterator
        class AsyncGenMock:
            def __init__(self):
                self.items = [MagicMock(status="success", total=100, percent=100.0)]
                self.index = 0
            
            def __aiter__(self):
                return self
            
            async def __anext__(self):
                if self.index >= len(self.items):
                    raise StopAsyncIteration
                item = self.items[self.index]
                self.index += 1
                return item
        
        # Create mock client with proper async generator
        mock_client = MagicMock()
        mock_client.is_huggingface_model.return_value = True
        mock_client.parse_huggingface_model.return_value = {
            "full_name": "user/repo",
            "quantization": "q4_0",
        }
        mock_client.pull_model.return_value = AsyncGenMock()
        
        with patch("opencode.llmchecker.ollama.OllamaClient", return_value=mock_client):
            runner = CliRunner()
            result = runner.invoke(app, ["ollama-pull", "hf.co/user/repo"])
            
            assert result.exit_code == 0


class TestOllamaRunCommand:
    """Tests for ollama-run command."""
    
    def test_ollama_run_standard_model(self, mock_ollama_client):
        """Test running a standard Ollama model."""
        from typer.testing import CliRunner
        from opencode.cli.commands.llmchecker import app
        
        response = MagicMock()
        response.content = "Test response"
        response.tokens_per_second = 50.0
        response.total_time_seconds = 1.0
        mock_ollama_client.generate.return_value = response
        
        runner = CliRunner()
        result = runner.invoke(app, ["ollama-run", "llama3.2:3b", "Hello"])
        
        assert result.exit_code == 0
    
    def test_ollama_run_huggingface_model(self, mock_ollama_client):
        """Test running a Hugging Face model."""
        from typer.testing import CliRunner
        from opencode.cli.commands.llmchecker import app
        
        mock_ollama_client.is_huggingface_model.return_value = True
        mock_ollama_client.parse_huggingface_model.return_value = {
            "full_name": "user/repo",
        }
        
        response = MagicMock()
        response.content = "Test response"
        response.tokens_per_second = 50.0
        response.total_time_seconds = 1.0
        mock_ollama_client.generate.return_value = response
        
        runner = CliRunner()
        result = runner.invoke(app, ["ollama-run", "hf.co/user/repo", "Hello"])
        
        assert result.exit_code == 0


class TestCalibrateCommand:
    """Tests for calibrate command."""
    
    def test_calibrate_dry_run(self, mock_calibration_manager):
        """Test calibration dry run."""
        from typer.testing import CliRunner
        from opencode.cli.commands.llmchecker import app
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write('{"prompt": "test"}\n')
            suite_path = f.name
        
        try:
            runner = CliRunner()
            result = runner.invoke(app, [
                "calibrate",
                "--suite", suite_path,
                "--model", "llama3.2:3b",
                "--dry-run",
            ])
            
            assert result.exit_code == 0
        finally:
            Path(suite_path).unlink(missing_ok=True)
    
    def test_calibrate_with_output(self, mock_calibration_manager):
        """Test calibration with output file."""
        from typer.testing import CliRunner
        from opencode.cli.commands.llmchecker import app
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write('{"prompt": "test"}\n')
            suite_path = f.name
        
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            output_path = f.name
        
        try:
            runner = CliRunner()
            result = runner.invoke(app, [
                "calibrate",
                "--suite", suite_path,
                "--model", "llama3.2:3b",
                "--output", output_path,
            ])
            
            assert result.exit_code == 0
        finally:
            Path(suite_path).unlink(missing_ok=True)
            Path(output_path).unlink(missing_ok=True)
    
    def test_calibrate_with_policy_output(self, mock_calibration_manager):
        """Test calibration with policy output."""
        from typer.testing import CliRunner
        from opencode.cli.commands.llmchecker import app
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write('{"prompt": "test"}\n')
            suite_path = f.name
        
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            policy_path = f.name
        
        try:
            runner = CliRunner()
            result = runner.invoke(app, [
                "calibrate",
                "--suite", suite_path,
                "--model", "llama3.2:3b",
                "--policy-out", policy_path,
            ])
            
            assert result.exit_code == 0
        finally:
            Path(suite_path).unlink(missing_ok=True)
            Path(policy_path).unlink(missing_ok=True)
    
    def test_calibrate_invalid_suite(self):
        """Test calibration with invalid prompt suite."""
        from typer.testing import CliRunner
        from opencode.cli.commands.llmchecker import app
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write("invalid json\n")
            suite_path = f.name
        
        try:
            runner = CliRunner()
            result = runner.invoke(app, [
                "calibrate",
                "--suite", suite_path,
                "--model", "llama3.2:3b",
            ])
            
            # Should fail with invalid suite
            assert result.exit_code != 0
        finally:
            Path(suite_path).unlink(missing_ok=True)


class TestPolicyCommand:
    """Tests for policy command."""
    
    def test_policy_init(self):
        """Test initializing a new policy."""
        from typer.testing import CliRunner
        from opencode.cli.commands.llmchecker import app
        
        with tempfile.TemporaryDirectory() as tmpdir:
            policy_path = Path(tmpdir) / "policy.yaml"
            
            runner = CliRunner()
            result = runner.invoke(app, ["policy", "init", str(policy_path)])
            
            assert result.exit_code == 0
    
    def test_policy_validate(self, mock_calibration_manager):
        """Test validating a policy."""
        from typer.testing import CliRunner
        from opencode.cli.commands.llmchecker import app
        
        with tempfile.TemporaryDirectory() as tmpdir:
            policy_path = Path(tmpdir) / "policy.yaml"
            policy_path.touch()
            
            runner = CliRunner()
            result = runner.invoke(app, ["policy", "validate", str(policy_path)])
            
            assert result.exit_code == 0
    
    def test_policy_validate_no_path(self):
        """Test validating without specifying a path."""
        from typer.testing import CliRunner
        from opencode.cli.commands.llmchecker import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["policy", "validate"])
        
        assert result.exit_code != 0
    
    def test_policy_show(self, mock_calibration_manager):
        """Test showing current policy."""
        from typer.testing import CliRunner
        from opencode.cli.commands.llmchecker import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["policy", "show"])
        
        assert result.exit_code == 0
    
    def test_policy_show_no_policy(self):
        """Test showing when no policy exists."""
        from typer.testing import CliRunner
        from opencode.cli.commands.llmchecker import app
        
        with patch("opencode.llmchecker.calibration.CalibrationManager") as mock:
            manager = MagicMock()
            manager.discover_policy.return_value = None
            mock.return_value = manager
            
            runner = CliRunner()
            result = runner.invoke(app, ["policy", "show"])
            
            assert result.exit_code == 0
            assert "No policy found" in result.output
    
    def test_policy_unknown_action(self):
        """Test unknown policy action."""
        from typer.testing import CliRunner
        from opencode.cli.commands.llmchecker import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["policy", "unknown"])
        
        assert result.exit_code != 0


class TestCLIIntegration:
    """Integration tests for CLI commands."""
    
    def test_app_help(self):
        """Test CLI app help."""
        from typer.testing import CliRunner
        from opencode.cli.commands.llmchecker import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert "hw-detect" in result.output
        assert "recommend" in result.output
        assert "ollama-list" in result.output
    
    def test_command_help(self):
        """Test individual command help."""
        from typer.testing import CliRunner
        from opencode.cli.commands.llmchecker import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["hw-detect", "--help"])
        
        assert result.exit_code == 0
        assert "Detect system hardware" in result.output
