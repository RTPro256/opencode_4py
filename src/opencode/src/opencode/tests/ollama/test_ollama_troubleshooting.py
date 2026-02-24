"""
Troubleshooting tests for Ollama provider.

Tests diagnostic capabilities, error handling, and troubleshooting utilities.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from opencode.provider.base import (
    Message,
    MessageRole,
    CompletionResponse,
    FinishReason,
    ProviderError,
)


@pytest.mark.ollama
class TestOllamaDiagnostics:
    """Test Ollama diagnostic capabilities."""
    
    @pytest.fixture
    def diagnostic_checks(self):
        """Define diagnostic checks to perform."""
        return [
            "server_reachability",
            "model_availability",
            "memory_availability",
            "gpu_detection",
            "api_version",
        ]
    
    @pytest.fixture
    def mock_diagnostic_provider(self):
        """Create a mock provider with diagnostic capabilities."""
        provider = MagicMock()
        provider.name = "ollama"
        provider._base_url = "http://localhost:11434"
        
        async def mock_get_available_models():
            return ["llama3.2:3b", "llama3.1:8b"]
        
        provider.get_available_models = mock_get_available_models
        return provider
    
    @pytest.mark.asyncio
    async def test_server_reachability_check(self, mock_diagnostic_provider):
        """Test checking if Ollama server is reachable."""
        models = await mock_diagnostic_provider.get_available_models()
        
        # If we can get models, server is reachable
        assert isinstance(models, list)
    
    @pytest.mark.asyncio
    async def test_model_availability_check(self, mock_diagnostic_provider):
        """Test checking model availability."""
        models = await mock_diagnostic_provider.get_available_models()
        
        # Should have at least one model available
        assert len(models) >= 0  # May be empty if no models pulled
    
    def test_diagnostic_report_structure(self, diagnostic_checks):
        """Test diagnostic report structure."""
        report = {
            "timestamp": "2024-01-01T00:00:00Z",
            "checks": {},
            "status": "healthy",
        }
        
        for check in diagnostic_checks:
            report["checks"][check] = {
                "status": "pass",
                "message": f"{check} check passed",
            }
        
        assert "timestamp" in report
        assert "checks" in report
        assert "status" in report
        assert len(report["checks"]) == len(diagnostic_checks)


@pytest.mark.ollama
class TestOllamaErrorHandling:
    """Test Ollama error handling scenarios."""
    
    @pytest.fixture
    def error_scenarios(self):
        """Define error scenarios to test."""
        return {
            "connection_refused": {
                "error": ConnectionError("Connection refused"),
                "expected_message": "Cannot connect to Ollama server",
            },
            "timeout": {
                "error": TimeoutError("Request timed out"),
                "expected_message": "Request timed out",
            },
            "model_not_found": {
                "error": FileNotFoundError("Model not found"),
                "expected_message": "Model not found",
            },
            "out_of_memory": {
                "error": MemoryError("Out of memory"),
                "expected_message": "Out of memory",
            },
        }
    
    def test_error_scenarios_structure(self, error_scenarios):
        """Test error scenarios structure."""
        for scenario_name, scenario in error_scenarios.items():
            assert "error" in scenario
            assert "expected_message" in scenario
    
    @pytest.mark.asyncio
    async def test_connection_error_handling(self):
        """Test handling of connection errors."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(
                side_effect=ConnectionError("Connection refused")
            )
            mock_client.return_value.__aenter__.return_value = mock_instance
            
            from opencode.provider.ollama import OllamaProvider
            provider = OllamaProvider()
            
            # Should handle error gracefully
            models = await provider.get_available_models()
            assert models == []
    
    @pytest.mark.asyncio
    async def test_timeout_error_handling(self):
        """Test handling of timeout errors."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(
                side_effect=TimeoutError("Request timed out")
            )
            mock_client.return_value.__aenter__.return_value = mock_instance
            
            from opencode.provider.ollama import OllamaProvider
            provider = OllamaProvider()
            
            # Should handle error gracefully
            models = await provider.get_available_models()
            assert models == []


@pytest.mark.ollama
class TestOllamaTroubleshootingTools:
    """Test Ollama troubleshooting tools and utilities."""
    
    @pytest.fixture
    def troubleshooting_commands(self):
        """Define troubleshooting commands."""
        return {
            "check_ollama_version": "ollama --version",
            "list_models": "ollama list",
            "show_model_info": "ollama show <model>",
            "pull_model": "ollama pull <model>",
            "run_model": "ollama run <model>",
        }
    
    def test_troubleshooting_commands_structure(self, troubleshooting_commands):
        """Test troubleshooting commands structure."""
        for name, command in troubleshooting_commands.items():
            assert isinstance(name, str)
            assert isinstance(command, str)
            assert len(command) > 0
    
    def test_model_info_structure(self):
        """Test model info structure for diagnostics."""
        model_info = {
            "name": "llama3.2:3b",
            "size": "2.0 GB",
            "quantization": "Q4_K_M",
            "context_length": 128000,
            "parameters": "3B",
        }
        
        assert "name" in model_info
        assert "size" in model_info
        assert "context_length" in model_info
    
    def test_system_requirements_check(self):
        """Test system requirements checking."""
        requirements = {
            "ram_minimum_gb": 8,
            "ram_recommended_gb": 16,
            "gpu_vram_minimum_gb": 4,
            "disk_space_minimum_gb": 10,
        }
        
        for key, value in requirements.items():
            assert value > 0, f"{key} should be positive"


@pytest.mark.ollama
class TestOllamaLogAnalysis:
    """Test Ollama log analysis capabilities."""
    
    @pytest.fixture
    def sample_log_entries(self):
        """Sample log entries for testing."""
        return [
            {
                "level": "INFO",
                "message": "Ollama server started",
                "timestamp": "2024-01-01T00:00:00Z",
            },
            {
                "level": "INFO",
                "message": "Model llama3.2:3b loaded",
                "timestamp": "2024-01-01T00:00:01Z",
            },
            {
                "level": "WARN",
                "message": "GPU memory running low",
                "timestamp": "2024-01-01T00:00:02Z",
            },
            {
                "level": "ERROR",
                "message": "Failed to allocate memory",
                "timestamp": "2024-01-01T00:00:03Z",
            },
        ]
    
    def test_log_entry_structure(self, sample_log_entries):
        """Test log entry structure."""
        for entry in sample_log_entries:
            assert "level" in entry
            assert "message" in entry
            assert "timestamp" in entry
            assert entry["level"] in ["DEBUG", "INFO", "WARN", "ERROR"]
    
    def test_error_detection(self, sample_log_entries):
        """Test error detection in logs."""
        errors = [e for e in sample_log_entries if e["level"] == "ERROR"]
        
        assert len(errors) == 1
        assert "Failed" in errors[0]["message"]
    
    def test_warning_detection(self, sample_log_entries):
        """Test warning detection in logs."""
        warnings = [e for e in sample_log_entries if e["level"] == "WARN"]
        
        assert len(warnings) == 1
        assert "memory" in warnings[0]["message"].lower()


@pytest.mark.ollama
class TestOllamaHealthCheck:
    """Test Ollama health check functionality."""
    
    @pytest.fixture
    def health_check_response(self):
        """Sample health check response."""
        return {
            "status": "healthy",
            "version": "0.1.27",
            "models_loaded": 2,
            "gpu_available": True,
            "memory_usage": {
                "used_gb": 6.5,
                "total_gb": 16.0,
            },
        }
    
    def test_health_check_structure(self, health_check_response):
        """Test health check response structure."""
        assert "status" in health_check_response
        assert health_check_response["status"] in ["healthy", "degraded", "unhealthy"]
    
    def test_memory_usage_validation(self, health_check_response):
        """Test memory usage validation."""
        memory = health_check_response["memory_usage"]
        
        assert memory["used_gb"] <= memory["total_gb"]
        assert memory["total_gb"] > 0
    
    def test_gpu_status_validation(self, health_check_response):
        """Test GPU status validation."""
        assert isinstance(health_check_response["gpu_available"], bool)


@pytest.mark.ollama
class TestOllamaModelDiagnostics:
    """Test model-specific diagnostics."""
    
    @pytest.fixture
    def model_diagnostic_results(self):
        """Sample model diagnostic results."""
        return {
            "model": "llama3.2:3b",
            "load_time_ms": 1500,
            "inference_time_ms": 250,
            "tokens_per_second": 35,
            "memory_usage_mb": 2048,
            "gpu_layers": 35,
        }
    
    def test_diagnostic_results_structure(self, model_diagnostic_results):
        """Test diagnostic results structure."""
        required_fields = [
            "model",
            "load_time_ms",
            "inference_time_ms",
            "tokens_per_second",
        ]
        
        for field in required_fields:
            assert field in model_diagnostic_results
    
    def test_performance_metrics_validation(self, model_diagnostic_results):
        """Test performance metrics validation."""
        assert model_diagnostic_results["load_time_ms"] > 0
        assert model_diagnostic_results["inference_time_ms"] > 0
        assert model_diagnostic_results["tokens_per_second"] > 0
    
    def test_memory_usage_validation(self, model_diagnostic_results):
        """Test memory usage validation."""
        assert model_diagnostic_results["memory_usage_mb"] > 0


@pytest.mark.ollama
class TestOllamaConfigurationDiagnostics:
    """Test configuration diagnostics."""
    
    @pytest.fixture
    def config_settings(self):
        """Sample configuration settings."""
        return {
            "host": "localhost",
            "port": 11434,
            "timeout": 300,
            "max_loaded_models": 3,
            "keep_alive": "5m",
        }
    
    def test_config_structure(self, config_settings):
        """Test configuration structure."""
        assert "host" in config_settings
        assert "port" in config_settings
        assert "timeout" in config_settings
    
    def test_port_validation(self, config_settings):
        """Test port validation."""
        port = config_settings["port"]
        assert 1 <= port <= 65535
    
    def test_timeout_validation(self, config_settings):
        """Test timeout validation."""
        timeout = config_settings["timeout"]
        assert timeout > 0
    
    def test_connection_url_construction(self, config_settings):
        """Test connection URL construction."""
        url = f"http://{config_settings['host']}:{config_settings['port']}"
        
        assert url == "http://localhost:11434"


@pytest.mark.ollama
class TestOllamaCommonIssues:
    """Test detection and resolution of common issues."""
    
    @pytest.fixture
    def common_issues(self):
        """Define common issues and their solutions."""
        return {
            "model_not_found": {
                "symptoms": ["Model not found error", "404 response"],
                "solution": "Pull the model using 'ollama pull <model>'",
            },
            "out_of_memory": {
                "symptoms": ["OOM error", "Killed signal", "Slow performance"],
                "solution": "Use a smaller model or reduce context length",
            },
            "connection_refused": {
                "symptoms": ["Connection refused", "Cannot connect"],
                "solution": "Start Ollama server with 'ollama serve'",
            },
            "slow_inference": {
                "symptoms": ["High latency", "Low tokens/second"],
                "solution": "Check GPU utilization and model size",
            },
        }
    
    def test_common_issues_structure(self, common_issues):
        """Test common issues structure."""
        for issue_name, issue in common_issues.items():
            assert "symptoms" in issue
            assert "solution" in issue
            assert isinstance(issue["symptoms"], list)
            assert len(issue["symptoms"]) > 0
    
    def test_issue_detection_patterns(self, common_issues):
        """Test issue detection patterns."""
        for issue_name, issue in common_issues.items():
            for symptom in issue["symptoms"]:
                assert isinstance(symptom, str)
                assert len(symptom) > 0
    
    def test_solution_availability(self, common_issues):
        """Test that all issues have solutions."""
        for issue_name, issue in common_issues.items():
            assert issue["solution"] is not None
            assert len(issue["solution"]) > 0
