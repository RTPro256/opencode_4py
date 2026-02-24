"""
Tests for CalibrationManager.

Unit tests for the LLM checker calibration manager.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
import tempfile
import json

from opencode.llmchecker.calibration.manager import CalibrationManager
from opencode.llmchecker.calibration.models import (
    CalibrationResult,
    CalibrationPolicy,
    CalibrationObjective,
    CalibrationStatus,
    PromptSuiteEntry,
    CalibrationRun,
    ModelCalibrationResult,
    RoutingRule,
)


class TestCalibrationManager:
    """Tests for CalibrationManager class."""
    
    @pytest.fixture
    def mock_ollama_client(self):
        """Create a mock Ollama client."""
        client = MagicMock()
        client.generate = AsyncMock()
        return client
    
    @pytest.fixture
    def mock_hardware_detector(self):
        """Create a mock hardware detector."""
        detector = MagicMock()
        hardware_info = MagicMock()
        hardware_info.to_dict.return_value = {"cpu": "test", "gpu": "test"}
        detector.detect.return_value = hardware_info
        return detector
    
    @pytest.fixture
    def manager(self, mock_ollama_client, mock_hardware_detector):
        """Create a manager instance with mocked dependencies."""
        return CalibrationManager(
            ollama_client=mock_ollama_client,
            hardware_detector=mock_hardware_detector
        )
    
    @pytest.fixture
    def sample_prompt_suite(self, tmp_path):
        """Create a sample prompt suite file."""
        suite_path = tmp_path / "test_suite.jsonl"
        entries = [
            {"prompt": "What is 2+2?", "task": "math", "expected_output": "4"},
            {"prompt": "Write a hello world program", "task": "code"},
            {"prompt": "Explain quantum physics", "task": "general"},
        ]
        with open(suite_path, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")
        return suite_path


class TestCalibrationManagerInit(TestCalibrationManager):
    """Tests for CalibrationManager initialization."""
    
    def test_init_with_clients(self, mock_ollama_client, mock_hardware_detector):
        """Test initialization with provided clients."""
        manager = CalibrationManager(
            ollama_client=mock_ollama_client,
            hardware_detector=mock_hardware_detector
        )
        assert manager.ollama is mock_ollama_client
        assert manager.hardware is mock_hardware_detector
    
    def test_init_creates_defaults(self):
        """Test initialization creates default clients."""
        manager = CalibrationManager()
        assert manager.ollama is not None
        assert manager.hardware is not None


class TestParsePromptSuite(TestCalibrationManager):
    """Tests for parse_prompt_suite method."""
    
    def test_parse_valid_suite(self, manager, sample_prompt_suite):
        """Test parsing a valid prompt suite."""
        entries = manager.parse_prompt_suite(sample_prompt_suite)
        assert len(entries) == 3
        assert entries[0].prompt == "What is 2+2?"
        assert entries[0].task == "math"
        assert entries[1].prompt == "Write a hello world program"
        assert entries[2].task == "general"
    
    def test_parse_nonexistent_file(self, manager):
        """Test parsing a nonexistent file."""
        with pytest.raises(FileNotFoundError):
            manager.parse_prompt_suite("/nonexistent/path.jsonl")
    
    def test_parse_with_cwd(self, manager, sample_prompt_suite, tmp_path):
        """Test parsing with relative path and cwd."""
        # Use relative path with cwd
        relative_path = "test_suite.jsonl"
        entries = manager.parse_prompt_suite(relative_path, cwd=str(tmp_path))
        assert len(entries) == 3
    
    def test_parse_empty_lines_and_comments(self, manager, tmp_path):
        """Test parsing file with empty lines and comments."""
        suite_path = tmp_path / "suite_with_comments.jsonl"
        with open(suite_path, "w") as f:
            f.write("# This is a comment\n")
            f.write("\n")
            f.write(json.dumps({"prompt": "test"}) + "\n")
            f.write("\n")
            f.write("# Another comment\n")
            f.write(json.dumps({"prompt": "test2"}) + "\n")
        
        entries = manager.parse_prompt_suite(suite_path)
        assert len(entries) == 2
    
    def test_parse_invalid_json(self, manager, tmp_path):
        """Test parsing file with invalid JSON."""
        suite_path = tmp_path / "invalid.jsonl"
        with open(suite_path, "w") as f:
            f.write('{"prompt": "valid"}\n')
            f.write("{invalid json}\n")
        
        with pytest.raises(ValueError) as exc_info:
            manager.parse_prompt_suite(suite_path)
        assert "Invalid JSON" in str(exc_info.value)
    
    def test_parse_default_values(self, manager, tmp_path):
        """Test parsing uses default values."""
        suite_path = tmp_path / "minimal.jsonl"
        with open(suite_path, "w") as f:
            f.write('{"prompt": "test"}\n')
        
        entries = manager.parse_prompt_suite(suite_path)
        assert entries[0].task == "general"
        assert entries[0].timeout_seconds == 120


class TestRunCalibration(TestCalibrationManager):
    """Tests for run_calibration method."""
    
    @pytest.mark.asyncio
    async def test_run_calibration_dry_run(self, manager):
        """Test calibration in dry run mode."""
        prompt_suite = [
            PromptSuiteEntry(prompt="Test prompt 1", task="test"),
            PromptSuiteEntry(prompt="Test prompt 2", task="test"),
        ]
        
        result = await manager.run_calibration(
            models=["model1", "model2"],
            prompt_suite=prompt_suite,
            dry_run=True
        )
        
        assert result.status == CalibrationStatus.COMPLETED
        assert len(result.model_results) == 2
        assert result.duration_seconds >= 0
    
    @pytest.mark.asyncio
    async def test_run_calibration_with_progress(self, manager):
        """Test calibration with progress callback."""
        prompt_suite = [
            PromptSuiteEntry(prompt="Test", task="test"),
        ]
        
        progress_calls = []
        def progress_callback(model, completed, total):
            progress_calls.append((model, completed, total))
        
        await manager.run_calibration(
            models=["model1"],
            prompt_suite=prompt_suite,
            dry_run=True,
            progress_callback=progress_callback
        )
        
        assert len(progress_calls) == 1
    
    @pytest.mark.asyncio
    async def test_run_calibration_sets_best_model(self, manager):
        """Test calibration determines best model."""
        prompt_suite = [
            PromptSuiteEntry(prompt="Test", task="test"),
        ]
        
        result = await manager.run_calibration(
            models=["model1", "model2"],
            prompt_suite=prompt_suite,
            dry_run=True
        )
        
        assert result.best_model is not None
    
    @pytest.mark.asyncio
    async def test_run_calibration_with_objective(self, manager):
        """Test calibration with specific objective."""
        prompt_suite = [
            PromptSuiteEntry(prompt="Test", task="test"),
        ]
        
        result = await manager.run_calibration(
            models=["model1"],
            prompt_suite=prompt_suite,
            objective=CalibrationObjective.SPEED,
            dry_run=True
        )
        
        assert result.objective == CalibrationObjective.SPEED
    
    @pytest.mark.asyncio
    async def test_run_calibration_real_run(self, manager, mock_ollama_client):
        """Test calibration with real Ollama calls."""
        # Mock the generate response
        mock_response = MagicMock()
        mock_response.content = "Test response"
        mock_response.tokens_per_second = 50.0
        mock_response.total_time = 1.0
        mock_response.prompt_eval_count = 10
        mock_response.eval_count = 20
        mock_ollama_client.generate.return_value = mock_response
        
        prompt_suite = [
            PromptSuiteEntry(prompt="Test", task="test"),
        ]
        
        result = await manager.run_calibration(
            models=["model1"],
            prompt_suite=prompt_suite,
            dry_run=False
        )
        
        assert result.status == CalibrationStatus.COMPLETED
        mock_ollama_client.generate.assert_called_once()


class TestGeneratePolicy(TestCalibrationManager):
    """Tests for generate_policy method."""
    
    def test_generate_policy_from_result(self, manager):
        """Test generating policy from calibration result."""
        result = CalibrationResult(
            id="test123",
            objective=CalibrationObjective.BALANCED,
            models=["model1", "model2"],
            status=CalibrationStatus.COMPLETED,
            best_model="model1",
        )
        
        policy = manager.generate_policy(result)
        
        assert policy.default_model == "model1"
    
    def test_generate_policy_with_routing_rules(self, manager):
        """Test generating policy with routing rules."""
        result = CalibrationResult(
            id="test123",
            objective=CalibrationObjective.BALANCED,
            models=["model1", "model2"],
            status=CalibrationStatus.COMPLETED,
            best_model="model1",
        )
        
        # Add model results with task-specific performance
        model_result = ModelCalibrationResult(model="model1")
        model_result.runs = [
            CalibrationRun(model="model1", prompt="test", task="code", quality_score=90.0),
            CalibrationRun(model="model1", prompt="test", task="math", quality_score=70.0),
        ]
        result.model_results.append(model_result)
        
        policy = manager.generate_policy(result)
        
        assert policy.default_model == "model1"


class TestSaveLoadPolicy(TestCalibrationManager):
    """Tests for save_policy and load_policy methods."""
    
    def test_save_policy(self, manager, tmp_path):
        """Test saving policy to file."""
        policy = CalibrationPolicy(
            default_model="model1",
            name="test-policy"
        )
        
        policy_path = tmp_path / "policy.yaml"
        manager.save_policy(policy, policy_path)
        
        assert policy_path.exists()
    
    def test_load_policy(self, manager, tmp_path):
        """Test loading policy from file."""
        # First save a policy
        policy = CalibrationPolicy(
            default_model="model1",
            name="test-policy"
        )
        
        policy_path = tmp_path / "policy.yaml"
        manager.save_policy(policy, policy_path)
        
        # Then load it
        loaded = manager.load_policy(policy_path)
        
        assert loaded.default_model == "model1"
        assert loaded.name == "test-policy"
    
    def test_load_nonexistent_policy(self, manager):
        """Test loading nonexistent policy."""
        with pytest.raises(FileNotFoundError):
            manager.load_policy("/nonexistent/policy.yaml")


class TestPromptSuiteEntry:
    """Tests for PromptSuiteEntry model."""
    
    def test_create_entry(self):
        """Test creating a prompt suite entry."""
        entry = PromptSuiteEntry(
            prompt="Test prompt",
            task="test",
            expected_output="expected",
            quality_check={"pattern": r"\d+"},
            timeout_seconds=60
        )
        assert entry.prompt == "Test prompt"
        assert entry.task == "test"
        assert entry.expected_output == "expected"
    
    def test_entry_defaults(self):
        """Test entry default values."""
        entry = PromptSuiteEntry(prompt="Test")
        assert entry.task == "general"
        assert entry.timeout_seconds == 120
        assert entry.expected_output is None


class TestCalibrationRun:
    """Tests for CalibrationRun model."""
    
    def test_create_run(self):
        """Test creating a calibration run."""
        run = CalibrationRun(
            model="model1",
            prompt="Test prompt",
            task="test",
            response="Test response",
            tokens_per_second=50.0,
            total_time_seconds=1.0,
            tokens_generated=50,
            quality_score=80.0
        )
        assert run.model == "model1"
        assert run.tokens_per_second == 50.0
        assert run.quality_score == 80.0
    
    def test_run_defaults(self):
        """Test run default values."""
        run = CalibrationRun(model="model1", prompt="test", task="test")
        assert run.response == ""
        assert run.tokens_per_second == 0.0
        assert run.quality_score == 0.0


class TestModelCalibrationResult:
    """Tests for ModelCalibrationResult model."""
    
    def test_create_result(self):
        """Test creating a model calibration result."""
        result = ModelCalibrationResult(model="model1")
        assert result.model == "model1"
        assert result.runs == []
    
    def test_calculate_aggregates(self):
        """Test calculating aggregate statistics."""
        result = ModelCalibrationResult(model="model1")
        result.runs = [
            CalibrationRun(model="model1", prompt="test", task="test", 
                          tokens_per_second=50.0, quality_score=80.0),
            CalibrationRun(model="model1", prompt="test", task="test",
                          tokens_per_second=60.0, quality_score=90.0),
        ]
        
        result.calculate_aggregates()
        
        assert result.avg_tokens_per_second == 55.0
        assert result.avg_quality_score == 85.0


class TestCalibrationResult:
    """Tests for CalibrationResult model."""
    
    def test_create_result(self):
        """Test creating a calibration result."""
        result = CalibrationResult(
            id="test123",
            objective=CalibrationObjective.BALANCED,
            models=["model1"],
            status=CalibrationStatus.RUNNING
        )
        assert result.id == "test123"
        assert result.status == CalibrationStatus.RUNNING
    
    def test_determine_best_model(self):
        """Test determining best model."""
        result = CalibrationResult(
            id="test123",
            objective=CalibrationObjective.BALANCED,
            models=["model1", "model2"],
            status=CalibrationStatus.COMPLETED
        )
        
        # Add results with different overall scores
        model1_result = ModelCalibrationResult(model="model1")
        model1_result.overall_score = 50.0
        
        model2_result = ModelCalibrationResult(model="model2")
        model2_result.overall_score = 90.0
        
        result.model_results = [model1_result, model2_result]
        result.determine_best_model()
        
        # model2 has higher overall score
        assert result.best_model == "model2"


class TestCalibrationPolicy:
    """Tests for CalibrationPolicy model."""
    
    def test_create_policy(self):
        """Test creating a calibration policy."""
        policy = CalibrationPolicy(
            default_model="model1",
            name="test-policy"
        )
        assert policy.default_model == "model1"
        assert policy.name == "test-policy"
    
    def test_policy_with_rules(self):
        """Test policy with routing rules."""
        policy = CalibrationPolicy(
            default_model="model1",
            rules=[
                RoutingRule(task="code", model="code-model"),
                RoutingRule(task="math", model="math-model"),
            ]
        )
        assert len(policy.rules) == 2
    
    def test_get_model_for_task(self):
        """Test getting model for specific task."""
        policy = CalibrationPolicy(
            default_model="default-model",
            rules=[
                RoutingRule(task="code", model="code-model"),
            ]
        )
        
        assert policy.get_model_for_task("code") == "code-model"
        assert policy.get_model_for_task("other") == "default-model"


class TestRoutingRule:
    """Tests for RoutingRule model."""
    
    def test_create_rule(self):
        """Test creating a routing rule."""
        rule = RoutingRule(task="code", model="code-model")
        assert rule.task == "code"
        assert rule.model == "code-model"
    
    def test_rule_with_conditions(self):
        """Test rule with conditions."""
        rule = RoutingRule(
            task="code",
            model="fast-model",
            conditions={"max_tokens": 100}
        )
        assert rule.conditions == {"max_tokens": 100}
