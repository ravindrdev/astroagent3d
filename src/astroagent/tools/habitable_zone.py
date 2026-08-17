"""Tool to calculate stellar habitable zone boundaries."""

from __future__ import annotations

import math
from typing import Any

from pydantic import BaseModel, Field

from astroagent.tools.base import AstroTool

SOLAR_LUMINOSITY = 3.828e26  # Watts
SOLAR_TEFF = 5778  # Kelvin


class HabitableZoneInput(BaseModel):
    """Input schema for habitable zone calculation."""

    star_temp_k: float = Field(
        description="Effective temperature of the star in Kelvin.",
        gt=2000,
        lt=50000,
    )
    star_luminosity: float | None = Field(
        default=None,
        description="Stellar luminosity relative to the Sun (e.g., 1.0 = solar). "
        "If not provided, will be estimated from temperature and radius.",
    )
    star_radius_solar: float | None = Field(
        default=None,
        description="Stellar radius in solar radii. Used to estimate luminosity if not provided.",
    )
    model: str = Field(
        default="kopparapu",
        description="HZ model: 'kopparapu' (Kopparapu et al. 2013, recommended) or 'simple' (basic flux-based).",
    )


class CalculateHabitableZone(AstroTool):
    name = "calculate_habitable_zone"
    description = (
        "Calculate the habitable zone boundaries for a star based on its temperature "
        "and luminosity. Uses the Kopparapu et al. (2013) model by default. "
        "Returns inner and outer edges in AU where liquid water could exist on a "
        "rocky planet's surface."
    )
    input_schema = HabitableZoneInput

    def execute(
        self,
        star_temp_k: float,
        star_luminosity: float | None = None,
        star_radius_solar: float | None = None,
        model: str = "kopparapu",
    ) -> dict[str, Any]:
        if star_luminosity is None:
            if star_radius_solar is not None:
                star_luminosity = _estimate_luminosity(star_temp_k, star_radius_solar)
            else:
                return {
                    "error": "Either star_luminosity or star_radius_solar must be provided.",
                }

        hz = _kopparapu_hz(star_temp_k, star_luminosity) if model == "kopparapu" else _simple_hz(star_luminosity)

        return {
            "model": model,
            "star_temp_k": star_temp_k,
            "star_luminosity_solar": round(star_luminosity, 6),
            "habitable_zone": {
                "conservative": {
                    "inner_au": round(hz["inner_conservative"], 4),
                    "outer_au": round(hz["outer_conservative"], 4),
                },
                "optimistic": {
                    "inner_au": round(hz["inner_optimistic"], 4),
                    "outer_au": round(hz["outer_optimistic"], 4),
                },
            },
            "description": (
                f"Conservative HZ: {hz['inner_conservative']:.4f} - "
                f"{hz['outer_conservative']:.4f} AU. "
                f"Optimistic HZ: {hz['inner_optimistic']:.4f} - "
                f"{hz['outer_optimistic']:.4f} AU."
            ),
        }


def _estimate_luminosity(temp_k: float, radius_solar: float) -> float:
    """Estimate luminosity from Stefan-Boltzmann law: L/L_sun = (R/R_sun)^2 * (T/T_sun)^4."""
    return (radius_solar**2) * ((temp_k / SOLAR_TEFF) ** 4)


def _kopparapu_hz(temp_k: float, luminosity_solar: float) -> dict[str, float]:
    """Kopparapu et al. (2013) habitable zone boundaries.

    Coefficients from Table 1 of Kopparapu et al. (2013, ApJ, 765, 131).
    """
    t_star = temp_k - 5780.0

    boundaries = {
        "recent_venus": (1.7763, 1.4335e-4, 3.3954e-9, -7.6364e-12, -1.1950e-15),
        "runaway_greenhouse": (1.0385, 1.2456e-4, 1.4612e-8, -7.6345e-12, -1.7511e-15),
        "moist_greenhouse": (1.0146, 8.1884e-5, 1.9394e-9, -4.3618e-12, -6.8260e-16),
        "max_greenhouse": (0.3507, 5.9578e-5, 1.6707e-9, -3.0058e-12, -5.1925e-16),
        "early_mars": (0.3207, 5.4471e-5, 1.5275e-9, -2.1709e-12, -3.8282e-16),
    }

    s_eff = {}
    for name, (s0, a, b, c, d) in boundaries.items():
        s_eff[name] = s0 + a * t_star + b * t_star**2 + c * t_star**3 + d * t_star**4

    sqrt_l = math.sqrt(luminosity_solar)
    distances = {name: sqrt_l / math.sqrt(s) for name, s in s_eff.items()}

    return {
        "inner_optimistic": distances["recent_venus"],
        "inner_conservative": distances["runaway_greenhouse"],
        "outer_conservative": distances["max_greenhouse"],
        "outer_optimistic": distances["early_mars"],
    }


def _simple_hz(luminosity_solar: float) -> dict[str, float]:
    """Simplified habitable zone based on solar flux scaling."""
    sqrt_l = math.sqrt(luminosity_solar)
    return {
        "inner_optimistic": 0.75 * sqrt_l,
        "inner_conservative": 0.95 * sqrt_l,
        "outer_conservative": 1.37 * sqrt_l,
        "outer_optimistic": 1.77 * sqrt_l,
    }
