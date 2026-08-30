"""Benchmark Suite runner evaluating candidate models against the canonical tasks."""

import time
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from src.models.base import ModelProvider
from src.models.ollama import OllamaProvider
from src.models.mock import MockModelProvider
from src.benchmark.tasks import BENCHMARK_TASKS
from src.config import settings

logger = logging.getLogger(__name__)


class BenchmarkSuite:
    """Evaluates a model provider against the 10 domain benchmark tasks."""

    def __init__(self, provider: Optional[ModelProvider] = None):
        self.provider = provider or MockModelProvider()

    async def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single benchmark task and record metrics."""
        category = task.get("category", "reasoning")
        start = time.perf_counter()

        if category == "classification":
            labels = task.get("labels", ["true", "false"])
            res = await self.provider.classify(text=task["prompt"], labels=labels)
            content = res.label
            passed = res.label == task.get("expected_label")
        else:
            res = await self.provider.complete(prompt=task["prompt"], max_tokens=256)
            content = res.content
            exp_keywords = task.get("expected_keywords", [])
            content_lower = content.lower()
            keyword_matches = sum(1 for kw in exp_keywords if kw.lower() in content_lower)
            passed = keyword_matches >= 1 if exp_keywords else True

        latency_ms = (time.perf_counter() - start) * 1000.0

        return {
            "task_id": task["id"],
            "task_name": task["name"],
            "category": category,
            "passed": passed,
            "latency_ms": round(latency_ms, 2),
            "output_preview": content[:120],
        }

    async def run_all(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Run all 10 canonical benchmark tasks and generate a summary report."""
        if model_name and not isinstance(self.provider, MockModelProvider):
            self.provider = OllamaProvider(model_name=model_name)

        results: List[Dict[str, Any]] = []
        total_latency = 0.0
        passed_count = 0

        for task in BENCHMARK_TASKS:
            task_res = await self.run_task(task)
            results.append(task_res)
            total_latency += task_res["latency_ms"]
            if task_res["passed"]:
                passed_count = passed_count + 1

        avg_latency = round(total_latency / len(BENCHMARK_TASKS), 2) if BENCHMARK_TASKS else 0.0
        accuracy = round((passed_count / len(BENCHMARK_TASKS)) * 100.0, 1) if BENCHMARK_TASKS else 0.0

        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model_tested": getattr(self.provider, "model_name", "unknown"),
            "total_tasks": len(BENCHMARK_TASKS),
            "passed_tasks": passed_count,
            "accuracy_percent": accuracy,
            "average_latency_ms": avg_latency,
            "task_results": results,
        }

        # Persist report to data/benchmarks
        try:
            report_file = settings.benchmark_dir / f"benchmark_{int(time.time())}.json"
            report_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
            report["saved_report_path"] = str(report_file)
        except Exception as e:
            logger.warning("Could not save benchmark report file: %s", e)

        return report
