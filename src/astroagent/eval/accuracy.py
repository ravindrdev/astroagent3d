"""Accuracy evaluator for verifying agent outputs against known astronomical values."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AccuracyResult:
    """Result of an accuracy check."""

    parameter: str
    expected: float
    actual: float
    tolerance_percent: float
    passed: bool
    deviation_percent: float


@dataclass
class SystemEvaluation:
    """Complete evaluation of agent results for a planetary system."""

    system_name: str
    results: list[AccuracyResult] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        if not self.results:
            return 0.0
        return sum(1 for r in self.results if r.passed) / len(self.results)

    @property
    def all_passed(self) -> bool:
        return all(r.passed for r in self.results)

    def summary(self) -> str:
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        return f"{self.system_name}: {passed}/{total} checks passed ({self.pass_rate:.0%})"


KNOWN_SYSTEMS: dict[str, dict[str, dict[str, float]]] = {
    "TRAPPIST-1": {
        "TRAPPIST-1 b": {
            "orbital_period_days": 1.51087,
            "semi_major_axis_au": 0.01154,
            "mass_earth": 1.374,
            "radius_earth": 1.116,
        },
        "TRAPPIST-1 c": {
            "orbital_period_days": 2.42180,
            "semi_major_axis_au": 0.01580,
            "mass_earth": 1.308,
            "radius_earth": 1.097,
        },
        "TRAPPIST-1 d": {
            "orbital_period_days": 4.04961,
            "semi_major_axis_au": 0.02227,
            "mass_earth": 0.388,
            "radius_earth": 0.788,
        },
        "TRAPPIST-1 e": {
            "orbital_period_days": 6.09956,
            "semi_major_axis_au": 0.02925,
            "mass_earth": 0.692,
            "radius_earth": 0.920,
        },
        "TRAPPIST-1 f": {
            "orbital_period_days": 9.20669,
            "semi_major_axis_au": 0.03849,
            "mass_earth": 1.039,
            "radius_earth": 1.045,
        },
        "TRAPPIST-1 g": {
            "orbital_period_days": 12.35294,
            "semi_major_axis_au": 0.04683,
            "mass_earth": 1.321,
            "radius_earth": 1.129,
        },
        "TRAPPIST-1 h": {
            "orbital_period_days": 18.76760,
            "semi_major_axis_au": 0.06189,
            "mass_earth": 0.326,
            "radius_earth": 0.755,
        },
    },
    "Kepler-442": {
        "Kepler-442 b": {
            "orbital_period_days": 112.3053,
            "semi_major_axis_au": 0.409,
            "radius_earth": 1.34,
        },
    },
    "Proxima Centauri": {
        "Proxima Centauri b": {
            "orbital_period_days": 11.186,
            "semi_major_axis_au": 0.04857,
            "mass_earth": 1.07,
        },
    },
}


class AccuracyEvaluator:
    """Evaluates agent results against known astronomical values.

    Compares orbital parameters returned by the agent with published
    values from peer-reviewed catalogs to verify scientific accuracy.
    """

    def __init__(self, tolerance_percent: float = 5.0) -> None:
        self._tolerance = tolerance_percent

    def evaluate_system(
        self,
        system_name: str,
        agent_planets: list[dict[str, Any]],
    ) -> SystemEvaluation:
        """Compare agent results against known values for a system."""
        evaluation = SystemEvaluation(system_name=system_name)

        known = KNOWN_SYSTEMS.get(system_name, {})
        if not known:
            return evaluation

        for planet_name, expected_params in known.items():
            agent_planet = self._find_planet(planet_name, agent_planets)
            if agent_planet is None:
                evaluation.results.append(
                    AccuracyResult(
                        parameter=f"{planet_name} (missing)",
                        expected=0,
                        actual=0,
                        tolerance_percent=self._tolerance,
                        passed=False,
                        deviation_percent=100.0,
                    )
                )
                continue

            for param, expected_value in expected_params.items():
                actual_value = agent_planet.get(param)
                if actual_value is None:
                    evaluation.results.append(
                        AccuracyResult(
                            parameter=f"{planet_name}.{param}",
                            expected=expected_value,
                            actual=0.0,
                            tolerance_percent=self._tolerance,
                            passed=False,
                            deviation_percent=100.0,
                        )
                    )
                    continue

                deviation = abs(actual_value - expected_value) / expected_value * 100
                passed = deviation <= self._tolerance

                evaluation.results.append(
                    AccuracyResult(
                        parameter=f"{planet_name}.{param}",
                        expected=expected_value,
                        actual=float(actual_value),
                        tolerance_percent=self._tolerance,
                        passed=passed,
                        deviation_percent=round(deviation, 4),
                    )
                )

        return evaluation

    def _find_planet(self, name: str, planets: list[dict[str, Any]]) -> dict[str, Any] | None:
        for p in planets:
            if p.get("name", "").strip().lower() == name.strip().lower():
                return p
        return None
