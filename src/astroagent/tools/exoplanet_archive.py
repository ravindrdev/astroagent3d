"""Tool to query NASA's Exoplanet Archive via the TAP API."""

from __future__ import annotations

import time
from typing import Any

import httpx
from pydantic import BaseModel, Field

from astroagent.tools.base import AstroTool

NASA_TAP_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 1.5

PLANET_COLUMNS = [
    "pl_name",
    "hostname",
    "ra",
    "dec",
    "sy_dist",
    "pl_orbper",
    "pl_orbsmax",
    "pl_orbeccen",
    "pl_orbincl",
    "pl_bmasse",
    "pl_rade",
    "pl_eqt",
    "pl_insol",
    "disc_year",
    "discoverymethod",
    "st_teff",
    "st_rad",
    "st_mass",
    "st_lum",
]


class ExoplanetArchiveInput(BaseModel):
    """Input schema for querying the NASA Exoplanet Archive."""

    star_name: str | None = Field(
        default=None,
        description="Host star name to search for (e.g., 'TRAPPIST-1', 'Kepler-442'). "
        "Leave empty to search by other criteria.",
    )
    planet_name: str | None = Field(
        default=None,
        description="Specific planet name (e.g., 'TRAPPIST-1 e', 'Kepler-442b').",
    )
    discovery_method: str | None = Field(
        default=None,
        description="Filter by discovery method: 'Transit', 'Radial Velocity', 'Imaging', 'Microlensing', etc.",
    )
    min_year: int | None = Field(
        default=None,
        description="Minimum discovery year.",
    )
    max_year: int | None = Field(
        default=None,
        description="Maximum discovery year.",
    )
    max_results: int = Field(
        default=50,
        description="Maximum number of results to return.",
        ge=1,
        le=500,
    )


class QueryExoplanetArchive(AstroTool):
    name = "query_exoplanet_archive"
    description = (
        "Query NASA's Exoplanet Archive for confirmed exoplanet data. "
        "Returns planetary parameters including orbital period, semi-major axis, "
        "mass, radius, equilibrium temperature, and host star properties. "
        "You can search by star name, planet name, discovery method, or year."
    )
    input_schema = ExoplanetArchiveInput

    def execute(
        self,
        star_name: str | None = None,
        planet_name: str | None = None,
        discovery_method: str | None = None,
        min_year: int | None = None,
        max_year: int | None = None,
        max_results: int = 50,
    ) -> dict[str, Any]:
        columns = ", ".join(PLANET_COLUMNS)
        where_clauses: list[str] = []

        if star_name:
            where_clauses.append(f"hostname LIKE '%{_sanitize(star_name)}%'")
        if planet_name:
            where_clauses.append(f"pl_name LIKE '%{_sanitize(planet_name)}%'")
        if discovery_method:
            where_clauses.append(f"discoverymethod = '{_sanitize(discovery_method)}'")
        if min_year:
            where_clauses.append(f"disc_year >= {int(min_year)}")
        if max_year:
            where_clauses.append(f"disc_year <= {int(max_year)}")

        where = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        query = f"SELECT TOP {int(max_results)} {columns} FROM pscomppars{where} ORDER BY hostname, pl_name"

        last_error = ""
        for attempt in range(MAX_RETRIES):
            try:
                response = httpx.get(
                    NASA_TAP_URL,
                    params={"query": query, "format": "json"},
                    timeout=30.0,
                )
                if response.status_code == 429:
                    wait = RETRY_BACKOFF_BASE ** (attempt + 1)
                    time.sleep(wait)
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
                return {"error": last_error, "planets": []}
            except httpx.RequestError as e:
                last_error = f"Failed to reach NASA API: {e}"
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BACKOFF_BASE ** (attempt + 1))
                    continue
                return {"error": last_error, "planets": []}
        else:
            return {"error": f"NASA API unavailable after {MAX_RETRIES} retries: {last_error}", "planets": []}

        planets = _format_planets(data)
        return {
            "query": query,
            "count": len(planets),
            "planets": planets,
        }


def _sanitize(value: str) -> str:
    """Remove characters that could break ADQL queries."""
    return value.replace("'", "").replace(";", "").replace("--", "")


def _format_planets(raw_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Format raw API response into clean planet records."""
    planets = []
    for row in raw_data:
        planet = {
            "name": row.get("pl_name"),
            "host_star": row.get("hostname"),
            "ra": row.get("ra"),
            "dec": row.get("dec"),
            "distance_pc": row.get("sy_dist"),
            "orbital_period_days": row.get("pl_orbper"),
            "semi_major_axis_au": row.get("pl_orbsmax"),
            "eccentricity": row.get("pl_orbeccen"),
            "inclination_deg": row.get("pl_orbincl"),
            "mass_earth": row.get("pl_bmasse"),
            "radius_earth": row.get("pl_rade"),
            "equilibrium_temp_k": row.get("pl_eqt"),
            "insolation_flux": row.get("pl_insol"),
            "discovery_year": row.get("disc_year"),
            "discovery_method": row.get("discoverymethod"),
            "star_temp_k": row.get("st_teff"),
            "star_radius_solar": row.get("st_rad"),
            "star_mass_solar": row.get("st_mass"),
            "star_luminosity_log": row.get("st_lum"),
        }
        planets.append(planet)
    return planets
