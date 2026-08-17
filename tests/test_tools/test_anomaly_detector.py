"""Tests for the anomaly detection tool."""

import numpy as np

from astroagent.tools.anomaly_detector import DetectAnomalies


class TestDetectAnomalies:
    def setup_method(self):
        self.tool = DetectAnomalies()

    def test_detects_outliers_in_noisy_data(self):
        np.random.seed(42)
        flux = list(np.random.normal(1.0, 0.001, 100))
        flux[50] = 0.98
        flux[75] = 1.02

        result = self.tool.execute(flux_values=flux, sigma_threshold=3.0)
        assert result["total_anomalies"] > 0
        outliers = result["sigma_clip"]["outliers"]
        indices = [o["index"] for o in outliers]
        assert 50 in indices or 75 in indices

    def test_no_anomalies_in_flat_data(self):
        flux = [1.0] * 100
        result = self.tool.execute(flux_values=flux)
        assert result["sigma_clip"]["num_outliers"] == 0

    def test_transit_search_finds_dip(self, sample_light_curve):
        flux = [dp["flux"] for dp in sample_light_curve]
        time = [dp["time_bjd"] for dp in sample_light_curve]

        result = self.tool.execute(
            flux_values=flux,
            time_values=time,
            method="both",
        )
        assert "transit_candidates" in result
        assert result["total_anomalies"] > 0

    def test_summary_generation(self):
        np.random.seed(42)
        flux = list(np.random.normal(1.0, 0.001, 200))
        flux[100] = 0.97

        result = self.tool.execute(flux_values=flux, method="both")
        assert isinstance(result["summary"], str)
        assert "Analyzed" in result["summary"]

    def test_sigma_threshold_sensitivity(self):
        np.random.seed(42)
        flux = list(np.random.normal(1.0, 0.001, 200))
        flux[50] = 0.995

        loose = self.tool.execute(flux_values=flux, sigma_threshold=2.0)
        strict = self.tool.execute(flux_values=flux, sigma_threshold=5.0)
        assert loose["sigma_clip"]["num_outliers"] >= strict["sigma_clip"]["num_outliers"]

    def test_tool_schema_format(self):
        schema = self.tool.to_claude_tool()
        assert schema["name"] == "detect_anomalies"
        assert "input_schema" in schema
