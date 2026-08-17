"""Tests for the habitable zone calculator."""

from astroagent.tools.habitable_zone import CalculateHabitableZone


class TestCalculateHabitableZone:
    def setup_method(self):
        self.tool = CalculateHabitableZone()

    def test_solar_habitable_zone(self):
        result = self.tool.execute(star_temp_k=5778, star_luminosity=1.0)
        hz = result["habitable_zone"]["conservative"]
        assert 0.9 < hz["inner_au"] < 1.1
        assert 1.5 < hz["outer_au"] < 2.0

    def test_trappist1_habitable_zone(self):
        result = self.tool.execute(
            star_temp_k=2566,
            star_luminosity=0.000553,
        )
        hz = result["habitable_zone"]["conservative"]
        assert 0.01 < hz["inner_au"] < 0.04
        assert 0.02 < hz["outer_au"] < 0.06

    def test_luminosity_from_radius(self):
        result = self.tool.execute(
            star_temp_k=5778,
            star_radius_solar=1.0,
        )
        assert "habitable_zone" in result
        lum = result["star_luminosity_solar"]
        assert 0.8 < lum < 1.2

    def test_missing_luminosity_and_radius(self):
        result = self.tool.execute(star_temp_k=5778)
        assert "error" in result

    def test_hot_star_wider_hz(self):
        cool = self.tool.execute(star_temp_k=3500, star_luminosity=0.01)
        hot = self.tool.execute(star_temp_k=7000, star_luminosity=5.0)
        cool_outer = cool["habitable_zone"]["conservative"]["outer_au"]
        hot_outer = hot["habitable_zone"]["conservative"]["outer_au"]
        assert hot_outer > cool_outer

    def test_simple_model(self):
        result = self.tool.execute(star_temp_k=5778, star_luminosity=1.0, model="simple")
        hz = result["habitable_zone"]["conservative"]
        assert 0.8 < hz["inner_au"] < 1.2
        assert 1.2 < hz["outer_au"] < 1.8

    def test_tool_schema_format(self):
        schema = self.tool.to_claude_tool()
        assert schema["name"] == "calculate_habitable_zone"
        assert "description" in schema
        assert "input_schema" in schema
