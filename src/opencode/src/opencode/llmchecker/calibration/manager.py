"""
Calibration manager for LLM Checker.

Handles model calibration and policy generation.
"""

import os
import json
import uuid
import time
import re
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable, Any

import yaml

from .models import (
    CalibrationResult,
    CalibrationPolicy,
    CalibrationObjective,
    CalibrationStatus,
    PromptSuiteEntry,
    CalibrationRun,
    ModelCalibrationResult,
    RoutingRule,
)
from ..ollama import OllamaClient
from ..hardware import HardwareDetector


class CalibrationManager:
    """Manages model calibration and policy generation.
    
    Provides:
    - Prompt suite parsing
    - Model benchmarking
    - Policy generation
    - Policy loading/saving
    """
    
    def __init__(
        self,
        ollama_client: Optional[OllamaClient] = None,
        hardware_detector: Optional[HardwareDetector] = None,
    ):
        """Initialize calibration manager.
        
        Args:
            ollama_client: Ollama client for running prompts.
            hardware_detector: Hardware detector for system info.
        """
        self.ollama = ollama_client or OllamaClient()
        self.hardware = hardware_detector or HardwareDetector()
    
    def parse_prompt_suite(
        self, 
        suite_path: str | Path,
        cwd: Optional[str] = None
    ) -> list[PromptSuiteEntry]:
        """Parse a prompt suite file.
        
        Supports JSONL format with one JSON object per line.
        
        Args:
            suite_path: Path to prompt suite file.
            cwd: Working directory for relative paths.
            
        Returns:
            List of PromptSuiteEntry objects.
        """
        path = Path(suite_path)
        if not path.is_absolute() and cwd:
            path = Path(cwd) / path
        
        if not path.exists():
            raise FileNotFoundError(f"Prompt suite not found: {path}")
        
        entries = []
        
        with open(path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                
                try:
                    data = json.loads(line)
                    entry = PromptSuiteEntry(
                        prompt=data.get("prompt", ""),
                        task=data.get("task", "general"),
                        expected_output=data.get("expected_output"),
                        quality_check=data.get("quality_check"),
                        timeout_seconds=data.get("timeout_seconds", 120),
                    )
                    entries.append(entry)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON on line {line_num}: {e}")
        
        return entries
    
    async def run_calibration(
        self,
        models: list[str],
        prompt_suite: list[PromptSuiteEntry],
        objective: CalibrationObjective = CalibrationObjective.BALANCED,
        dry_run: bool = False,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> CalibrationResult:
        """Run calibration on models.
        
        Args:
            models: List of model names to calibrate.
            prompt_suite: List of prompts to run.
            objective: Calibration objective.
            dry_run: If True, don't actually run prompts.
            progress_callback: Callback for progress updates.
            
        Returns:
            CalibrationResult with benchmark data.
        """
        calibration_id = str(uuid.uuid4())[:8]
        result = CalibrationResult(
            id=calibration_id,
            objective=objective,
            models=models,
            status=CalibrationStatus.RUNNING,
            hardware_info=self.hardware.detect().to_dict() if self.hardware else {},
        )
        
        start_time = time.time()
        total_prompts = len(models) * len(prompt_suite)
        completed = 0
        
        for model in models:
            model_result = ModelCalibrationResult(model=model)
            
            for entry in prompt_suite:
                if progress_callback:
                    progress_callback(model, completed, total_prompts)
                
                if dry_run:
                    # Simulate a run
                    run = CalibrationRun(
                        model=model,
                        prompt=entry.prompt,
                        task=entry.task,
                        response="[DRY RUN - Simulated response]",
                        tokens_per_second=50.0,
                        total_time_seconds=1.0,
                        tokens_generated=50,
                        quality_score=80.0,
                    )
                else:
                    # Actually run the prompt
                    run = await self._run_prompt(model, entry)
                
                model_result.runs.append(run)
                completed += 1
            
            model_result.calculate_aggregates()
            result.model_results.append(model_result)
        
        result.duration_seconds = time.time() - start_time
        result.status = CalibrationStatus.COMPLETED
        result.determine_best_model()
        
        return result
    
    async def _run_prompt(
        self,
        model: str,
        entry: PromptSuiteEntry,
    ) -> CalibrationRun:
        """Run a single prompt and measure performance.
        
        Args:
            model: Model name.
            entry: Prompt suite entry.
            
        Returns:
            CalibrationRun with results.
        """
        run = CalibrationRun(
            model=model,
            prompt=entry.prompt,
            task=entry.task,
        )
        
        try:
            # Run the prompt
            response = await self.ollama.generate(
                model=model,
                prompt=entry.prompt,
                options={"num_ctx": 4096},
            )
            
            run.response = response.content
            run.tokens_per_second = response.tokens_per_second
            run.total_time_seconds = response.total_time_seconds
            run.prompt_eval_time = response.prompt_eval_duration / 1e9
            run.eval_time = response.eval_duration / 1e9
            run.tokens_generated = response.eval_count
            
            # Check quality
            run.quality_score = self._evaluate_quality(
                response.content,
                entry.expected_output,
                entry.quality_check,
            )
            run.quality_passed = run.quality_score >= 50
            
        except asyncio.TimeoutError:
            run.error = "Timeout"
        except Exception as e:
            run.error = str(e)
        
        return run
    
    def _evaluate_quality(
        self,
        response: str,
        expected: Optional[str],
        quality_check: Optional[dict],
    ) -> float:
        """Evaluate response quality.
        
        Args:
            response: Model response.
            expected: Expected output (if any).
            quality_check: Quality check rules.
            
        Returns:
            Quality score (0-100).
        """
        score = 50.0  # Base score for non-empty response
        
        if not response.strip():
            return 0.0
        
        # Check expected output similarity
        if expected:
            # Simple similarity check
            expected_words = set(expected.lower().split())
            response_words = set(response.lower().split())
            overlap = len(expected_words & response_words)
            total = len(expected_words)
            if total > 0:
                score += (overlap / total) * 30
        
        # Check quality rules
        if quality_check:
            # Regex patterns
            patterns = quality_check.get("patterns", [])
            for pattern in patterns:
                if re.search(pattern, response, re.IGNORECASE):
                    score += 5
            
            # Required keywords
            keywords = quality_check.get("keywords", [])
            response_lower = response.lower()
            for keyword in keywords:
                if keyword.lower() in response_lower:
                    score += 2
            
            # Forbidden patterns
            forbidden = quality_check.get("forbidden", [])
            for pattern in forbidden:
                if re.search(pattern, response, re.IGNORECASE):
                    score -= 10
            
            # Min/max length
            min_length = quality_check.get("min_length")
            max_length = quality_check.get("max_length")
            if min_length and len(response) < min_length:
                score -= 10
            if max_length and len(response) > max_length:
                score -= 5
        
        return max(0, min(100, score))
    
    def generate_policy(
        self,
        result: CalibrationResult,
        name: str = "calibration-policy",
        description: str = "",
    ) -> CalibrationPolicy:
        """Generate a routing policy from calibration results.
        
        Args:
            result: Calibration result.
            name: Policy name.
            description: Policy description.
            
        Returns:
            CalibrationPolicy for routing.
        """
        policy = CalibrationPolicy(
            name=name,
            description=description,
            calibration_id=result.id,
        )
        
        # Group results by task
        task_results: dict[str, list[ModelCalibrationResult]] = {}
        
        for model_result in result.model_results:
            for run in model_result.runs:
                task = run.task
                if task not in task_results:
                    task_results[task] = []
                
                # Create a temporary result for this task
                task_model_result = ModelCalibrationResult(
                    model=model_result.model,
                    avg_tokens_per_second=run.tokens_per_second,
                    avg_quality_score=run.quality_score,
                    success_rate=1.0 if run.error is None else 0.0,
                )
                task_model_result.overall_score = (
                    run.tokens_per_second * 0.4 +
                    run.quality_score * 0.4 +
                    (100 if run.error is None else 0) * 0.2
                )
                task_results[task].append(task_model_result)
        
        # Create rules for each task
        for task, results in task_results.items():
            # Sort by overall score
            sorted_results = sorted(results, key=lambda r: r.overall_score, reverse=True)
            
            if sorted_results:
                best = sorted_results[0]
                rule = RoutingRule(
                    task=task,
                    model=best.model,
                    priority=10,
                )
                policy.rules.append(rule)
        
        # Set default model to overall best
        policy.default_model = result.best_model
        policy.fallback_model = result.models[0] if result.models else ""
        
        return policy
    
    def save_policy(
        self,
        policy: CalibrationPolicy,
        path: str | Path,
        format: str = "yaml",
    ) -> None:
        """Save policy to file.
        
        Args:
            policy: Policy to save.
            path: Output path.
            format: Output format ("yaml" or "json").
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        data = policy.to_dict()
        
        if format.lower() == "yaml":
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        else:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
    
    def load_policy(self, path: str | Path) -> CalibrationPolicy:
        """Load policy from file.
        
        Args:
            path: Path to policy file.
            
        Returns:
            CalibrationPolicy object.
        """
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"Policy file not found: {path}")
        
        with open(path, "r", encoding="utf-8") as f:
            if path.suffix.lower() in (".yaml", ".yml"):
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        
        return CalibrationPolicy.from_dict(data)
    
    def discover_policy(self) -> Optional[CalibrationPolicy]:
        """Discover and load default policy.
        
        Searches in standard locations:
        - ~/.llm-checker/calibration-policy.yaml
        - ~/.llm-checker/calibration-policy.json
        - ./calibration-policy.yaml
        - ./calibration-policy.json
        
        Returns:
            CalibrationPolicy if found, None otherwise.
        """
        search_paths = [
            Path.home() / ".llm-checker" / "calibration-policy.yaml",
            Path.home() / ".llm-checker" / "calibration-policy.json",
            Path.cwd() / "calibration-policy.yaml",
            Path.cwd() / "calibration-policy.json",
        ]
        
        for path in search_paths:
            if path.exists():
                try:
                    return self.load_policy(path)
                except Exception:
                    continue
        
        return None
    
    def save_result(
        self,
        result: CalibrationResult,
        path: str | Path,
    ) -> None:
        """Save calibration result to file.
        
        Args:
            result: Result to save.
            path: Output path.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2)
    
    def load_result(self, path: str | Path) -> CalibrationResult:
        """Load calibration result from file.
        
        Args:
            path: Path to result file.
            
        Returns:
            CalibrationResult object.
        """
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"Result file not found: {path}")
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Reconstruct result
        result = CalibrationResult(
            id=data.get("id", ""),
            objective=CalibrationObjective(data.get("objective", "balanced")),
            models=data.get("models", []),
            best_model=data.get("best_model", ""),
            duration_seconds=data.get("duration_seconds", 0),
            status=CalibrationStatus(data.get("status", "completed")),
            hardware_info=data.get("hardware_info", {}),
        )
        
        # Load model results
        for mr_data in data.get("model_results", []):
            model_result = ModelCalibrationResult(
                model=mr_data.get("model", ""),
                avg_tokens_per_second=mr_data.get("avg_tokens_per_second", 0),
                avg_quality_score=mr_data.get("avg_quality_score", 0),
                avg_total_time=mr_data.get("avg_total_time", 0),
                success_rate=mr_data.get("success_rate", 0),
                overall_score=mr_data.get("overall_score", 0),
            )
            result.model_results.append(model_result)
        
        return result
