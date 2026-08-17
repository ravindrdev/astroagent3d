"""Tests for the AstroAgent core."""

from astroagent.tools.base import ToolRegistry
from astroagent.tools.exoplanet_archive import QueryExoplanetArchive
from astroagent.tools.habitable_zone import CalculateHabitableZone


class TestToolRegistry:
    def test_register_and_get(self):
        registry = ToolRegistry()
        tool = CalculateHabitableZone()
        registry.register(tool)
        assert registry.get("calculate_habitable_zone") is tool

    def test_get_unknown_raises(self):
        registry = ToolRegistry()
        import pytest

        with pytest.raises(KeyError):
            registry.get("nonexistent")

    def test_get_claude_tools_format(self):
        registry = ToolRegistry()
        registry.register(CalculateHabitableZone())
        registry.register(QueryExoplanetArchive())
        tools = registry.get_claude_tools()
        assert len(tools) == 2
        for t in tools:
            assert "name" in t
            assert "description" in t
            assert "input_schema" in t

    def test_execute_tool(self):
        registry = ToolRegistry()
        registry.register(CalculateHabitableZone())
        result = registry.execute(
            "calculate_habitable_zone",
            {"star_temp_k": 5778, "star_luminosity": 1.0},
        )
        assert "habitable_zone" in result

    def test_execute_with_json_string(self):
        registry = ToolRegistry()
        registry.register(CalculateHabitableZone())
        import json

        args = json.dumps({"star_temp_k": 5778, "star_luminosity": 1.0})
        result = registry.execute("calculate_habitable_zone", args)
        assert "habitable_zone" in result

    def test_tool_names(self):
        registry = ToolRegistry()
        registry.register(CalculateHabitableZone())
        registry.register(QueryExoplanetArchive())
        assert set(registry.tool_names) == {
            "calculate_habitable_zone",
            "query_exoplanet_archive",
        }

    def test_len(self):
        registry = ToolRegistry()
        assert len(registry) == 0
        registry.register(CalculateHabitableZone())
        assert len(registry) == 1
