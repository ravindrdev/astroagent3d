"""Tests for the NASA Exoplanet Archive tool."""

from unittest.mock import patch

import pytest

from astroagent.tools.exoplanet_archive import QueryExoplanetArchive, _format_planets, _sanitize


class TestQueryExoplanetArchive:
    def setup_method(self):
        self.tool = QueryExoplanetArchive()

    def test_sanitize_removes_injection(self):
        assert "'" not in _sanitize("TRAPPIST-1'; DROP TABLE--")
        assert "--" not in _sanitize("test--injection")
        assert ";" not in _sanitize("test;injection")

    def test_format_planets_handles_empty(self):
        assert _format_planets([]) == []

    def test_format_planets_extracts_fields(self):
        raw = [
            {
                "pl_name": "TRAPPIST-1 b",
                "hostname": "TRAPPIST-1",
                "pl_orbper": 1.51,
                "pl_orbsmax": 0.01154,
                "pl_bmasse": 1.374,
                "pl_rade": 1.116,
            }
        ]
        result = _format_planets(raw)
        assert len(result) == 1
        assert result[0]["name"] == "TRAPPIST-1 b"
        assert result[0]["orbital_period_days"] == 1.51
        assert result[0]["semi_major_axis_au"] == 0.01154

    def test_tool_schema_format(self):
        schema = self.tool.to_claude_tool()
        assert schema["name"] == "query_exoplanet_archive"
        assert "description" in schema
        assert "input_schema" in schema
        assert "properties" in schema["input_schema"]

    @patch("astroagent.tools.exoplanet_archive.httpx.get")
    def test_handles_api_error(self, mock_get):
        import httpx

        mock_get.side_effect = httpx.RequestError("Connection failed")
        result = self.tool.execute(star_name="TRAPPIST-1")
        assert "error" in result
        assert result["planets"] == []

    @pytest.mark.slow
    def test_real_trappist1_query(self):
        result = self.tool.execute(star_name="TRAPPIST-1")
        assert result["count"] >= 7
        names = [p["name"] for p in result["planets"]]
        assert any("TRAPPIST-1 b" in n for n in names)
