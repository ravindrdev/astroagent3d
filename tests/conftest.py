"""Shared fixtures for AstroAgent tests."""

from __future__ import annotations

import pytest


@pytest.fixture
def trappist1_planets() -> list[dict]:
    """Real TRAPPIST-1 system data for testing."""
    return [
        {
            "name": "TRAPPIST-1 b",
            "host_star": "TRAPPIST-1",
            "orbital_period_days": 1.51087,
            "semi_major_axis_au": 0.01154,
            "eccentricity": 0.00622,
            "mass_earth": 1.374,
            "radius_earth": 1.116,
            "equilibrium_temp_k": 400,
            "star_temp_k": 2566,
            "star_radius_solar": 0.1192,
            "star_mass_solar": 0.0898,
            "discovery_method": "Transit",
        },
        {
            "name": "TRAPPIST-1 c",
            "host_star": "TRAPPIST-1",
            "orbital_period_days": 2.42180,
            "semi_major_axis_au": 0.01580,
            "eccentricity": 0.00654,
            "mass_earth": 1.308,
            "radius_earth": 1.097,
            "equilibrium_temp_k": 342,
            "star_temp_k": 2566,
            "star_radius_solar": 0.1192,
            "discovery_method": "Transit",
        },
        {
            "name": "TRAPPIST-1 d",
            "host_star": "TRAPPIST-1",
            "orbital_period_days": 4.04961,
            "semi_major_axis_au": 0.02227,
            "eccentricity": 0.00837,
            "mass_earth": 0.388,
            "radius_earth": 0.788,
            "equilibrium_temp_k": 288,
            "star_temp_k": 2566,
            "star_radius_solar": 0.1192,
            "discovery_method": "Transit",
        },
        {
            "name": "TRAPPIST-1 e",
            "host_star": "TRAPPIST-1",
            "orbital_period_days": 6.09956,
            "semi_major_axis_au": 0.02925,
            "eccentricity": 0.00510,
            "mass_earth": 0.692,
            "radius_earth": 0.920,
            "equilibrium_temp_k": 251,
            "star_temp_k": 2566,
            "star_radius_solar": 0.1192,
            "discovery_method": "Transit",
        },
        {
            "name": "TRAPPIST-1 f",
            "host_star": "TRAPPIST-1",
            "orbital_period_days": 9.20669,
            "semi_major_axis_au": 0.03849,
            "eccentricity": 0.01007,
            "mass_earth": 1.039,
            "radius_earth": 1.045,
            "equilibrium_temp_k": 219,
            "star_temp_k": 2566,
            "star_radius_solar": 0.1192,
            "discovery_method": "Transit",
        },
        {
            "name": "TRAPPIST-1 g",
            "host_star": "TRAPPIST-1",
            "orbital_period_days": 12.35294,
            "semi_major_axis_au": 0.04683,
            "eccentricity": 0.00208,
            "mass_earth": 1.321,
            "radius_earth": 1.129,
            "equilibrium_temp_k": 199,
            "star_temp_k": 2566,
            "star_radius_solar": 0.1192,
            "discovery_method": "Transit",
        },
        {
            "name": "TRAPPIST-1 h",
            "host_star": "TRAPPIST-1",
            "orbital_period_days": 18.76760,
            "semi_major_axis_au": 0.06189,
            "eccentricity": 0.00567,
            "mass_earth": 0.326,
            "radius_earth": 0.755,
            "equilibrium_temp_k": 173,
            "star_temp_k": 2566,
            "star_radius_solar": 0.1192,
            "discovery_method": "Transit",
        },
    ]


@pytest.fixture
def sample_light_curve() -> list[dict[str, float]]:
    """Sample light curve data with a synthetic transit dip."""
    import numpy as np

    np.random.seed(42)
    n = 500
    time = np.linspace(0, 10, n)
    flux = 1.0 + np.random.normal(0, 0.001, n)

    transit_center = 5.0
    transit_width = 0.3
    transit_depth = 0.005
    transit_mask = np.abs(time - transit_center) < transit_width
    flux[transit_mask] -= transit_depth

    return [{"time_bjd": float(t), "flux": float(f), "flux_err": 0.001} for t, f in zip(time, flux, strict=False)]
