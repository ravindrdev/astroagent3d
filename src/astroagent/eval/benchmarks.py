"""Benchmark suite for evaluating AstroAgent performance."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from astroagent.eval.accuracy import AccuracyEvaluator, SystemEvaluation


@dataclass
class BenchmarkResult:
    """Result of a single benchmark test."""

    name: str
    query: str
    passed: bool
    accuracy: SystemEvaluation | None = None
    duration_seconds: float = 0.0
    error: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkReport:
    """Complete benchmark report."""

    results: list[BenchmarkResult] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        if not self.results:
            return 0.0
        return sum(1 for r in self.results if r.passed) / len(self.results)

    @property
    def total_duration(self) -> float:
        return sum(r.duration_seconds for r in self.results)

    def summary(self) -> str:
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        lines = [
            f"Benchmark Report: {passed}/{total} passed ({self.pass_rate:.0%})",
            f"Total duration: {self.total_duration:.1f}s",
            "",
        ]
        for r in self.results:
            status = "PASS" if r.passed else "FAIL"
            lines.append(f"  [{status}] {r.name} ({r.duration_seconds:.1f}s)")
            if r.error:
                lines.append(f"         Error: {r.error}")
            if r.accuracy:
                lines.append(f"         Accuracy: {r.accuracy.summary()}")
        return "\n".join(lines)


BENCHMARKS = [
    {
        "name": "trappist1_system_query",
        "query": "Query the TRAPPIST-1 system and show all planets",
        "expected_system": "TRAPPIST-1",
        "expected_min_planets": 7,
        "check_accuracy": True,
    },
    {
        "name": "habitable_zone_calculation",
        "query": "Calculate the habitable zone for TRAPPIST-1",
        "expected_tool": "calculate_habitable_zone",
        "check_hz": True,
    },
    {
        "name": "kepler442_query",
        "query": "Find Kepler-442b and tell me about it",
        "expected_system": "Kepler-442",
        "expected_min_planets": 1,
        "check_accuracy": True,
    },
    {
        "name": "light_curve_fetch",
        "query": "Fetch the light curve for TRAPPIST-1 from Kepler",
        "expected_tool": "fetch_light_curve",
        "check_data_points": True,
    },
    {
        "name": "anomaly_detection",
        "query": "Look for transit signals in the TRAPPIST-1 light curve data",
        "expected_tool": "detect_anomalies",
    },
]


class BenchmarkSuite:
    """Run standardized benchmarks against the AstroAgent.

    Tests the agent on known queries where ground truth is available,
    measuring both accuracy and performance.
    """

    def __init__(self, tolerance_percent: float = 5.0) -> None:
        self._evaluator = AccuracyEvaluator(tolerance_percent=tolerance_percent)

    def run_all(self, agent: Any) -> BenchmarkReport:
        """Run all benchmarks against the provided agent."""
        report = BenchmarkReport()
        for bench in BENCHMARKS:
            result = self._run_single(agent, bench)
            report.results.append(result)
        return report

    def run_single(self, agent: Any, benchmark_name: str) -> BenchmarkResult:
        """Run a single named benchmark."""
        bench = next((b for b in BENCHMARKS if b["name"] == benchmark_name), None)
        if bench is None:
            return BenchmarkResult(
                name=benchmark_name,
                query="",
                passed=False,
                error=f"Unknown benchmark: {benchmark_name}",
            )
        return self._run_single(agent, bench)

    def _run_single(self, agent: Any, bench: dict[str, Any]) -> BenchmarkResult:
        start = time.time()
        try:
            response = agent.ask(bench["query"])
            duration = time.time() - start

            passed = True
            accuracy = None
            details: dict[str, Any] = {}

            if bench.get("expected_tool"):
                tool_used = any(s.tool_name == bench["expected_tool"] for s in response.steps if s.type == "tool_call")
                if not tool_used:
                    passed = False
                    details["missing_tool"] = bench["expected_tool"]

            if bench.get("expected_min_planets"):
                archive_data = response.data.get("query_exoplanet_archive", {})
                count = archive_data.get("count", 0)
                if count < bench["expected_min_planets"]:
                    passed = False
                    details["expected_planets"] = bench["expected_min_planets"]
                    details["actual_planets"] = count

            if bench.get("check_accuracy") and bench.get("expected_system"):
                archive_data = response.data.get("query_exoplanet_archive", {})
                planets = archive_data.get("planets", [])
                accuracy = self._evaluator.evaluate_system(bench["expected_system"], planets)
                if not accuracy.all_passed:
                    passed = False

            if bench.get("check_data_points"):
                lc_data = response.data.get("fetch_light_curve", {})
                if not lc_data.get("data_points"):
                    passed = False
                    details["error"] = "No data points returned"

            return BenchmarkResult(
                name=bench["name"],
                query=bench["query"],
                passed=passed,
                accuracy=accuracy,
                duration_seconds=round(duration, 2),
                details=details,
            )

        except Exception as e:
            return BenchmarkResult(
                name=bench["name"],
                query=bench["query"],
                passed=False,
                duration_seconds=round(time.time() - start, 2),
                error=str(e),
            )
