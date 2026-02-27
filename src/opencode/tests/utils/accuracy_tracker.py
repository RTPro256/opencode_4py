"""
Accuracy tracking utilities for test metrics.

Provides functionality to track, store, and analyze accuracy metrics
across test runs for different models and task types.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


@dataclass
class AccuracyMetric:
    """A single accuracy metric measurement."""
    
    name: str
    value: float
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    model: Optional[str] = None
    category: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "value": self.value,
            "timestamp": self.timestamp,
            "model": self.model,
            "category": self.category,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AccuracyMetric":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            value=data["value"],
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
            model=data.get("model"),
            category=data.get("category"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class TestResult:
    """Result of a single test run."""
    
    test_name: str
    passed: bool
    accuracy: Optional[float] = None
    duration_ms: Optional[float] = None
    error_message: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    model: Optional[str] = None
    category: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "test_name": self.test_name,
            "passed": self.passed,
            "accuracy": self.accuracy,
            "duration_ms": self.duration_ms,
            "error_message": self.error_message,
            "timestamp": self.timestamp,
            "model": self.model,
            "category": self.category,
        }


class AccuracyTracker:
    """
    Tracks accuracy metrics across test runs.
    
    Provides functionality to:
    - Record accuracy metrics for different models and categories
    - Calculate aggregate statistics
    - Compare performance across models
    - Persist metrics to JSON files
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize the accuracy tracker.
        
        Args:
            storage_path: Optional path to store metrics JSON file
        """
        self._metrics: list[AccuracyMetric] = []
        self._results: list[TestResult] = []
        self._storage_path = storage_path
    
    def record_metric(
        self,
        name: str,
        value: float,
        model: Optional[str] = None,
        category: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> AccuracyMetric:
        """
        Record an accuracy metric.
        
        Args:
            name: Name of the metric
            value: Accuracy value (0.0 to 1.0)
            model: Model identifier
            category: Category of the metric
            metadata: Additional metadata
            
        Returns:
            The recorded metric
        """
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"Accuracy value must be between 0 and 1, got {value}")
        
        metric = AccuracyMetric(
            name=name,
            value=value,
            model=model,
            category=category,
            metadata=metadata or {},
        )
        self._metrics.append(metric)
        return metric
    
    def record_result(
        self,
        test_name: str,
        passed: bool,
        accuracy: Optional[float] = None,
        duration_ms: Optional[float] = None,
        error_message: Optional[str] = None,
        model: Optional[str] = None,
        category: Optional[str] = None,
    ) -> TestResult:
        """
        Record a test result.
        
        Args:
            test_name: Name of the test
            passed: Whether the test passed
            accuracy: Optional accuracy score
            duration_ms: Test duration in milliseconds
            error_message: Error message if test failed
            model: Model identifier
            category: Category of the test
            
        Returns:
            The recorded result
        """
        result = TestResult(
            test_name=test_name,
            passed=passed,
            accuracy=accuracy,
            duration_ms=duration_ms,
            error_message=error_message,
            model=model,
            category=category,
        )
        self._results.append(result)
        return result
    
    def get_metrics_by_model(self, model: str) -> list[AccuracyMetric]:
        """Get all metrics for a specific model."""
        return [m for m in self._metrics if m.model == model]
    
    def get_metrics_by_category(self, category: str) -> list[AccuracyMetric]:
        """Get all metrics for a specific category."""
        return [m for m in self._metrics if m.category == category]
    
    def get_average_accuracy(
        self,
        model: Optional[str] = None,
        category: Optional[str] = None,
    ) -> float:
        """
        Calculate average accuracy.
        
        Args:
            model: Filter by model (optional)
            category: Filter by category (optional)
            
        Returns:
            Average accuracy value
        """
        metrics = self._metrics
        
        if model:
            metrics = [m for m in metrics if m.model == model]
        if category:
            metrics = [m for m in metrics if m.category == category]
        
        if not metrics:
            return 0.0
        
        return sum(m.value for m in metrics) / len(metrics)
    
    def get_pass_rate(
        self,
        model: Optional[str] = None,
        category: Optional[str] = None,
    ) -> float:
        """
        Calculate test pass rate.
        
        Args:
            model: Filter by model (optional)
            category: Filter by category (optional)
            
        Returns:
            Pass rate (0.0 to 1.0)
        """
        results = self._results
        
        if model:
            results = [r for r in results if r.model == model]
        if category:
            results = [r for r in results if r.category == category]
        
        if not results:
            return 0.0
        
        passed = sum(1 for r in results if r.passed)
        return passed / len(results)
    
    def compare_models(self, category: Optional[str] = None) -> dict[str, float]:
        """
        Compare average accuracy across models.
        
        Args:
            category: Filter by category (optional)
            
        Returns:
            Dictionary mapping model names to average accuracy
        """
        models = set(m.model for m in self._metrics if m.model)
        
        comparison = {}
        for model in models:
            comparison[model] = self.get_average_accuracy(model=model, category=category)
        
        return comparison
    
    def get_summary(self) -> dict[str, Any]:
        """
        Get a summary of all tracked metrics.
        
        Returns:
            Summary dictionary
        """
        models = set(m.model for m in self._metrics if m.model)
        categories = set(m.category for m in self._metrics if m.category)
        
        return {
            "total_metrics": len(self._metrics),
            "total_results": len(self._results),
            "models": list(models),
            "categories": list(categories),
            "overall_accuracy": self.get_average_accuracy(),
            "overall_pass_rate": self.get_pass_rate(),
            "model_comparison": self.compare_models(),
        }
    
    def save(self, path: Optional[Path] = None) -> None:
        """
        Save metrics to a JSON file.
        
        Args:
            path: Path to save to (uses storage_path if not provided)
        """
        save_path = path or self._storage_path
        if not save_path:
            raise ValueError("No storage path provided")
        
        data = {
            "metrics": [m.to_dict() for m in self._metrics],
            "results": [r.to_dict() for r in self._results],
            "summary": self.get_summary(),
        }
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_text(json.dumps(data, indent=2))
    
    def load(self, path: Optional[Path] = None) -> None:
        """
        Load metrics from a JSON file.
        
        Args:
            path: Path to load from (uses storage_path if not provided)
        """
        load_path = path or self._storage_path
        if not load_path:
            raise ValueError("No storage path provided")
        
        if not load_path.exists():
            return
        
        data = json.loads(load_path.read_text())
        
        self._metrics = [AccuracyMetric.from_dict(m) for m in data.get("metrics", [])]
        self._results = [
            TestResult(
                test_name=r["test_name"],
                passed=r["passed"],
                accuracy=r.get("accuracy"),
                duration_ms=r.get("duration_ms"),
                error_message=r.get("error_message"),
                timestamp=r.get("timestamp", datetime.utcnow().isoformat()),
                model=r.get("model"),
                category=r.get("category"),
            )
            for r in data.get("results", [])
        ]
    
    def clear(self) -> None:
        """Clear all tracked metrics and results."""
        self._metrics.clear()
        self._results.clear()


class AccuracyReport:
    """Generates formatted accuracy reports."""
    
    def __init__(self, tracker: AccuracyTracker):
        """
        Initialize the report generator.
        
        Args:
            tracker: AccuracyTracker instance
        """
        self.tracker = tracker
    
    def generate_markdown_report(self) -> str:
        """
        Generate a markdown formatted report.
        
        Returns:
            Markdown formatted report string
        """
        summary = self.tracker.get_summary()
        
        lines = [
            "# Accuracy Report",
            "",
            f"**Generated:** {datetime.utcnow().isoformat()}",
            "",
            "## Summary",
            "",
            f"- Total Metrics: {summary['total_metrics']}",
            f"- Total Results: {summary['total_results']}",
            f"- Overall Accuracy: {summary['overall_accuracy']:.2%}",
            f"- Overall Pass Rate: {summary['overall_pass_rate']:.2%}",
            "",
        ]
        
        if summary["models"]:
            lines.extend([
                "## Model Comparison",
                "",
                "| Model | Average Accuracy |",
                "|-------|-----------------|",
            ])
            
            for model, accuracy in sorted(
                summary["model_comparison"].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                lines.append(f"| {model} | {accuracy:.2%} |")
            
            lines.append("")
        
        if summary["categories"]:
            lines.extend([
                "## Category Breakdown",
                "",
            ])
            
            for category in summary["categories"]:
                avg = self.tracker.get_average_accuracy(category=category)
                lines.append(f"- **{category}:** {avg:.2%}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def generate_json_report(self) -> dict[str, Any]:
        """
        Generate a JSON formatted report.
        
        Returns:
            Dictionary with report data
        """
        return {
            "generated": datetime.utcnow().isoformat(),
            "summary": self.tracker.get_summary(),
            "metrics": [m.to_dict() for m in self.tracker._metrics],
            "results": [r.to_dict() for r in self.tracker._results],
        }
