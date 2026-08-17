"""Tool to query the Sloan Digital Sky Survey (SDSS) catalog."""

from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel, Field

from astroagent.tools.base import AstroTool

SDSS_API_URL = "https://skyserver.sdss.org/dr18/SkyServerWS"


class SDSSInput(BaseModel):
    """Input schema for SDSS queries."""

    ra: float | None = Field(
        default=None,
        description="Right ascension in degrees (0-360).",
        ge=0,
        le=360,
    )
    dec: float | None = Field(
        default=None,
        description="Declination in degrees (-90 to 90).",
        ge=-90,
        le=90,
    )
    radius_arcmin: float = Field(
        default=2.0,
        description="Search radius in arcminutes.",
        gt=0,
        le=30,
    )
    object_type: str | None = Field(
        default=None,
        description="Object type filter: 'STAR', 'GALAXY', 'QSO' (quasar).",
    )
    sql_query: str | None = Field(
        default=None,
        description="Custom SDSS SQL query. Advanced — overrides other parameters. "
        "Use CasJobs-style SQL against SDSS DR18 tables.",
    )
    max_results: int = Field(
        default=50,
        description="Maximum number of results.",
        ge=1,
        le=500,
    )


class SearchSDSS(AstroTool):
    name = "search_sdss"
    description = (
        "Search the Sloan Digital Sky Survey (SDSS DR18) catalog for astronomical "
        "objects. Query by sky coordinates (RA/Dec) with a search radius, or use "
        "custom SQL for advanced queries. Returns photometric data (ugriz magnitudes), "
        "spectral classifications, and object properties."
    )
    input_schema = SDSSInput

    def execute(
        self,
        ra: float | None = None,
        dec: float | None = None,
        radius_arcmin: float = 2.0,
        object_type: str | None = None,
        sql_query: str | None = None,
        max_results: int = 50,
    ) -> dict[str, Any]:
        if sql_query:
            return self._run_sql_query(sql_query, max_results)
        elif ra is not None and dec is not None:
            return self._cone_search(ra, dec, radius_arcmin, object_type, max_results)
        else:
            return {"error": "Provide either (ra, dec) for a cone search or sql_query for custom SQL."}

    def _cone_search(
        self,
        ra: float,
        dec: float,
        radius: float,
        object_type: str | None,
        max_results: int,
    ) -> dict[str, Any]:
        type_filter = ""
        if object_type:
            type_filter = f"AND type = '{_sanitize(object_type.upper())}'"

        query = (
            f"SELECT TOP {int(max_results)} "
            f"objID, ra, dec, u, g, r, i, z, type, class, subClass, redshift "
            f"FROM PhotoObj AS p "
            f"JOIN dbo.fGetNearbyObjEq({ra}, {dec}, {radius}) AS n ON p.objID = n.objID "
            f"{type_filter} "
            f"ORDER BY n.distance"
        )
        return self._run_sql_query(query, max_results)

    def _run_sql_query(self, query: str, max_results: int) -> dict[str, Any]:
        try:
            response = httpx.get(
                f"{SDSS_API_URL}/SearchTools/SqlSearch",
                params={"cmd": query, "format": "json"},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            return {"error": f"SDSS API returned status {e.response.status_code}", "objects": []}
        except httpx.RequestError as e:
            return {"error": f"Failed to reach SDSS API: {e}", "objects": []}

        rows = data[0].get("Rows", []) if isinstance(data, list) and data else []
        objects = _format_sdss_objects(rows)
        return {
            "query": query,
            "count": len(objects),
            "objects": objects[:max_results],
        }


def _sanitize(value: str) -> str:
    return value.replace("'", "").replace(";", "").replace("--", "")


def _format_sdss_objects(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    objects = []
    for row in rows:
        obj = {
            "object_id": row.get("objID"),
            "ra_deg": row.get("ra"),
            "dec_deg": row.get("dec"),
            "magnitudes": {
                "u": row.get("u"),
                "g": row.get("g"),
                "r": row.get("r"),
                "i": row.get("i"),
                "z": row.get("z"),
            },
            "type": row.get("type"),
            "classification": row.get("class"),
            "sub_class": row.get("subClass"),
            "redshift": row.get("redshift"),
        }
        objects.append(obj)
    return objects
