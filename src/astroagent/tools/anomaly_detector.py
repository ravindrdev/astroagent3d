"""Tool to detect anomalies in astronomical time-series data."""

from __future__ import annotations

from typing import Any

import numpy as np
from pydantic import BaseModel, Field

from astroagent.tools.base import AstroTool


class AnomalyDetectorInput(BaseModel):
    """Input schema for anomaly detection."""

    flux_values: list[float] = Field(
        description="List of flux/brightness measurements.",
        min_length=10,
    )
    time_values: list[float] | None = Field(
        default=None,
        description="Corresponding time values (BJD or phase). Same length as flux_values.",
    )
    sigma_threshold: float = Field(
        default=3.0,
        description="Number of standard deviations from the median to flag as anomalous.",
        gt=1.0,
        le=10.0,
    )
    method: str = Field(
        default="sigma_clip",
        description="Detection method: 'sigma_clip' (statistical outlier), "
        "'transit_search' (periodic dip detection), or 'both'.",
    )


class DetectAnomalies(AstroTool):
    name = "detect_anomalies"
    description = (
        "Analyze astronomical time-series data (light curves) for anomalies. "
        "Can detect statistical outliers via sigma-clipping and search for "
        "periodic transit-like dips that may indicate planetary transits. "
        "Returns flagged data points with significance scores."
    )
    input_schema = AnomalyDetectorInput

    def execute(
        self,
        flux_values: list[float],
        time_values: list[float] | None = None,
        sigma_threshold: float = 3.0,
        method: str = "sigma_clip",
    ) -> dict[str, Any]:
        flux = np.array(flux_values)

        time = np.array(time_values) if time_values is not None else np.arange(len(flux), dtype=float)

        results: dict[str, Any] = {
            "total_points": len(flux),
            "baseline_flux": float(np.median(flux)),
            "flux_std": float(np.std(flux)),
        }

        if method in ("sigma_clip", "both"):
            results["sigma_clip"] = _sigma_clip_detection(flux, time, sigma_threshold)

        if method in ("transit_search", "both"):
            results["transit_candidates"] = _transit_search(flux, time)

        anomaly_count = 0
        if "sigma_clip" in results:
            anomaly_count += results["sigma_clip"]["num_outliers"]
        if "transit_candidates" in results:
            anomaly_count += len(results["transit_candidates"])

        results["total_anomalies"] = anomaly_count
        results["summary"] = _generate_summary(results)

        return results


def _sigma_clip_detection(flux: np.ndarray, time: np.ndarray, sigma: float) -> dict[str, Any]:
    """Detect outliers using iterative sigma-clipping."""
    median = np.median(flux)
    std = np.std(flux)

    if std == 0:
        return {"num_outliers": 0, "outliers": [], "clipped_mean": float(median)}

    deviations = np.abs(flux - median) / std
    outlier_mask = deviations > sigma

    outliers = []
    for idx in np.where(outlier_mask)[0]:
        outliers.append(
            {
                "index": int(idx),
                "time": float(time[idx]),
                "flux": float(flux[idx]),
                "deviation_sigma": round(float(deviations[idx]), 2),
                "type": "dip" if flux[idx] < median else "spike",
            }
        )

    outliers.sort(key=lambda x: x["deviation_sigma"], reverse=True)

    clipped_flux = flux[~outlier_mask]
    return {
        "num_outliers": len(outliers),
        "outliers": outliers[:20],
        "clipped_mean": float(np.mean(clipped_flux)) if len(clipped_flux) > 0 else float(median),
        "clipped_std": float(np.std(clipped_flux)) if len(clipped_flux) > 0 else 0.0,
    }


def _transit_search(flux: np.ndarray, time: np.ndarray) -> list[dict[str, Any]]:
    """Search for transit-like dips using a box-fitting approach."""
    median_flux = np.median(flux)
    std_flux = np.std(flux)

    if std_flux == 0 or len(flux) < 20:
        return []

    candidates = []
    window_sizes = [5, 10, 20, 50]

    for window in window_sizes:
        if window >= len(flux) // 2:
            continue

        for start in range(0, len(flux) - window, window // 2):
            segment = flux[start : start + window]
            segment_mean = np.mean(segment)
            depth = (median_flux - segment_mean) / median_flux

            if depth > 0.001 and segment_mean < median_flux - 2 * std_flux:
                candidates.append(
                    {
                        "start_index": int(start),
                        "end_index": int(start + window),
                        "start_time": float(time[start]),
                        "end_time": float(time[min(start + window - 1, len(time) - 1)]),
                        "duration_points": int(window),
                        "depth_ppm": round(float(depth * 1e6), 1),
                        "depth_percent": round(float(depth * 100), 4),
                        "significance_sigma": round(float(abs(segment_mean - median_flux) / std_flux), 2),
                    }
                )

    candidates.sort(key=lambda x: x["significance_sigma"], reverse=True)

    merged: list[dict[str, Any]] = []
    for c in candidates:
        if not any(abs(c["start_index"] - m["start_index"]) < max(c["duration_points"], 10) for m in merged):
            merged.append(c)

    return merged[:10]


def _generate_summary(results: dict[str, Any]) -> str:
    parts = [f"Analyzed {results['total_points']} data points."]

    if "sigma_clip" in results:
        n = results["sigma_clip"]["num_outliers"]
        parts.append(f"Found {n} statistical outlier{'s' if n != 1 else ''}.")

    if "transit_candidates" in results:
        n = len(results["transit_candidates"])
        if n > 0:
            best = results["transit_candidates"][0]
            parts.append(
                f"Detected {n} transit candidate{'s' if n != 1 else ''} — "
                f"strongest at {best['significance_sigma']}σ with depth "
                f"{best['depth_percent']}%."
            )
        else:
            parts.append("No significant transit signals detected.")

    return " ".join(parts)
