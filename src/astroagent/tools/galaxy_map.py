"""Tool to query all confirmed exoplanets and map them in 3D galactic coordinates."""

from __future__ import annotations

import math
import time
from typing import Any

import httpx
from pydantic import BaseModel, Field

from astroagent.tools.base import AstroTool

NASA_TAP_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 1.5

GALAXY_COLUMNS = [
    "pl_name",
    "hostname",
    "ra",
    "dec",
    "sy_dist",
    "pl_orbper",
    "pl_orbsmax",
    "pl_rade",
    "pl_bmasse",
    "pl_eqt",
    "disc_year",
    "discoverymethod",
    "st_teff",
    "st_rad",
    "st_lum",
]


class GalaxyMapInput(BaseModel):
    """Input schema for querying all confirmed exoplanets for galaxy mapping."""

    discovery_method: str | None = Field(
        default=None,
        description="Filter by discovery method: 'Transit', 'Radial Velocity', "
        "'Imaging', 'Microlensing'. Leave empty for all methods.",
    )
    min_year: int | None = Field(
        default=None,
        description="Only include planets discovered after this year.",
    )
    max_distance_pc: float | None = Field(
        default=None,
        description="Maximum distance in parsecs. Leave empty for all distances.",
    )
    max_results: int = Field(
        default=6000,
        description="Maximum number of planets to return. Use 6000 for all known exoplanets.",
        ge=1,
        le=10000,
    )


class QueryGalaxyMap(AstroTool):
    name = "query_galaxy_map"
    description = (
        "Query ALL confirmed exoplanets from NASA's archive and return their "
        "3D positions in the Milky Way. Returns right ascension, declination, "
        "and distance for every known exoplanet, converted to Cartesian (x, y, z) "
        "coordinates for 3D galaxy mapping. Use this when the user wants to see "
        "the distribution of all known planets, a galaxy-scale view, or a map "
        "of exoplanet discoveries across the Milky Way."
    )
    input_schema = GalaxyMapInput

    def execute(
        self,
        discovery_method: str | None = None,
        min_year: int | None = None,
        max_distance_pc: float | None = None,
        max_results: int = 6000,
    ) -> dict[str, Any]:
        columns = ", ".join(GALAXY_COLUMNS)
        where_clauses: list[str] = ["ra IS NOT NULL", "dec IS NOT NULL", "sy_dist IS NOT NULL"]

        if discovery_method:
            where_clauses.append(f"discoverymethod = '{_sanitize(discovery_method)}'")
        if min_year:
            where_clauses.append(f"disc_year >= {int(min_year)}")
        if max_distance_pc:
            where_clauses.append(f"sy_dist <= {float(max_distance_pc)}")

        where = f" WHERE {' AND '.join(where_clauses)}"
        query = f"SELECT TOP {int(max_results)} {columns} FROM pscomppars{where} ORDER BY sy_dist"

        last_error = ""
        for attempt in range(MAX_RETRIES):
            try:
                response = httpx.get(
                    NASA_TAP_URL,
                    params={"query": query, "format": "json"},
                    timeout=60.0,
                )
                if response.status_code == 429:
                    time.sleep(RETRY_BACKOFF_BASE ** (attempt + 1))
                    last_error = "Rate limited by NASA API"
                    continue
                response.raise_for_status()
                data = response.json()
                break
            except httpx.HTTPStatusError as e:
                last_error = f"NASA API returned status {e.response.status_code}"
                if e.response.status_code >= 500:
                    time.sleep(RETRY_BACKOFF_BASE ** (attempt + 1))
                    continue
                return {"error": last_error, "planets": [], "stats": {}}
            except httpx.RequestError as e:
                last_error = f"Failed to reach NASA API: {e}"
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BACKOFF_BASE ** (attempt + 1))
                    continue
                return {"error": last_error, "planets": [], "stats": {}}
        else:
            return {
                "error": f"NASA API unavailable after {MAX_RETRIES} retries: {last_error}",
                "planets": [],
                "stats": {},
            }

        planets = _format_galaxy_planets(data)
        stats = _compute_stats(planets)

        return {
            "query": query,
            "count": len(planets),
            "planets": planets,
            "stats": stats,
        }


def _sanitize(value: str) -> str:
    return value.replace("'", "").replace(";", "").replace("--", "")


def _ra_dec_dist_to_xyz(ra_deg: float, dec_deg: float, dist_pc: float) -> tuple[float, float, float]:
    """Convert equatorial coordinates to 3D Cartesian (parsecs)."""
    ra_rad = math.radians(ra_deg)
    dec_rad = math.radians(dec_deg)
    x = dist_pc * math.cos(dec_rad) * math.cos(ra_rad)
    y = dist_pc * math.cos(dec_rad) * math.sin(ra_rad)
    z = dist_pc * math.sin(dec_rad)
    return (round(x, 4), round(y, 4), round(z, 4))


def _format_galaxy_planets(raw_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    planets = []
    for row in raw_data:
        ra = row.get("ra")
        dec = row.get("dec")
        dist = row.get("sy_dist")
        if ra is None or dec is None or dist is None:
            continue

        x, y, z = _ra_dec_dist_to_xyz(float(ra), float(dec), float(dist))

        planets.append(
            {
                "name": row.get("pl_name"),
                "host_star": row.get("hostname"),
                "ra": float(ra),
                "dec": float(dec),
                "distance_pc": float(dist),
                "distance_ly": round(float(dist) * 3.26156, 2),
                "x": x,
                "y": y,
                "z": z,
                "orbital_period_days": row.get("pl_orbper"),
                "semi_major_axis_au": row.get("pl_orbsmax"),
                "radius_earth": row.get("pl_rade"),
                "mass_earth": row.get("pl_bmasse"),
                "equilibrium_temp_k": row.get("pl_eqt"),
                "discovery_year": row.get("disc_year"),
                "discovery_method": row.get("discoverymethod"),
                "star_temp_k": row.get("st_teff"),
                "star_radius_solar": row.get("st_rad"),
                "star_luminosity": row.get("st_lum"),
            }
        )
    return planets


def _compute_stats(planets: list[dict[str, Any]]) -> dict[str, Any]:
    if not planets:
        return {}

    distances = [p["distance_pc"] for p in planets]
    methods: dict[str, int] = {}
    years: dict[int, int] = {}

    for p in planets:
        m = p.get("discovery_method") or "Unknown"
        methods[m] = methods.get(m, 0) + 1
        y = p.get("discovery_year")
        if y is not None:
            years[int(y)] = years.get(int(y), 0) + 1

    return {
        "total_planets": len(planets),
        "nearest_pc": round(min(distances), 2),
        "farthest_pc": round(max(distances), 2),
        "median_distance_pc": round(sorted(distances)[len(distances) // 2], 2),
        "discovery_methods": dict(sorted(methods.items(), key=lambda x: -x[1])),
        "discoveries_by_year": dict(sorted(years.items())),
    }
