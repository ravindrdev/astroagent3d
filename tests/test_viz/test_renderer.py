"""Tests for the 3D orbit renderer."""

from astroagent.viz.renderer import OrbitRenderer


class TestOrbitRenderer:
    def setup_method(self):
        self.renderer = OrbitRenderer()

    def test_render_generates_html(self, trappist1_planets):
        html = self.renderer.render(trappist1_planets)
        assert "<!DOCTYPE html>" in html
        assert "three.js" in html.lower() or "THREE" in html
        assert "TRAPPIST-1" in html

    def test_render_includes_all_planets(self, trappist1_planets):
        html = self.renderer.render(trappist1_planets)
        for p in trappist1_planets:
            assert p["name"] in html

    def test_render_includes_habitable_zone(self, trappist1_planets):
        html = self.renderer.render(trappist1_planets, hz_inner_au=0.022, hz_outer_au=0.032)
        assert "hz" in html.lower() or "habitable" in html.lower()

    def test_render_with_empty_planets(self):
        html = self.renderer.render([])
        assert "<!DOCTYPE html>" in html

    def test_render_filters_planets_without_sma(self, trappist1_planets):
        planets = trappist1_planets + [{"name": "No Orbit", "mass_earth": 1.0}]
        html = self.renderer.render(planets)
        assert "No Orbit" not in html

    def test_planet_color_by_temperature(self):
        assert self.renderer._planet_color(1500, 1.0) == "#e24b4a"  # hot
        assert self.renderer._planet_color(250, 1.0) == "#4a90d9"  # temperate
        assert self.renderer._planet_color(50, 1.0) == "#9fd5d1"  # frozen
        assert self.renderer._planet_color(None, 100.0) == "#c4956a"  # gas giant

    def test_detect_system_name(self, trappist1_planets):
        name = self.renderer._detect_system_name(trappist1_planets)
        assert name == "TRAPPIST-1"

    def test_compute_scale_proportional(self, trappist1_planets):
        processed = self.renderer._process_planets(trappist1_planets)
        scale = self.renderer._compute_scale(processed)
        assert scale > 0
        max_radius = max(p["semi_major_axis_au"] * scale for p in processed)
        assert 30 < max_radius < 50
