"""Unit tests for the BenchmarkSuite."""

import pytest
from src.benchmark.suite import BenchmarkSuite
from src.benchmark.tasks import BENCHMARK_TASKS


@pytest.mark.asyncio
async def test_benchmark_tasks_count():
    assert len(BENCHMARK_TASKS) == 10


@pytest.mark.asyncio
async def test_benchmark_suite_execution():
    suite = BenchmarkSuite()
    report = await suite.run_all()
    assert report["total_tasks"] == 10
    assert "accuracy_percent" in report
    assert "average_latency_ms" in report
    assert len(report["task_results"]) == 10
