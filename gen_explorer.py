"""Regenerate galaxy_explorer.html from the template + NASA data."""
import os
import sys
sys.path.insert(0, r"C:\Users\ravin\Documents\astroagent-3d\src")

env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

from astroagent.tools.galaxy_map import QueryGalaxyMap
from astroagent.viz.galaxy_explorer import GalaxyExplorer

print("Fetching exoplanets from NASA...")
tool = QueryGalaxyMap()
result = tool.execute()
planets = result["planets"]
stats = result["stats"]
print(f"Got {len(planets)} exoplanets")

api_key = os.environ.get("ANTHROPIC_API_KEY", "")
if api_key:
    print("Embedding API key from ANTHROPIC_API_KEY env var")
else:
    print("No ANTHROPIC_API_KEY env var found — Pulsar AI will ask for key on first use")

explorer = GalaxyExplorer()
out = explorer.render_to_file(
    planets,
    r"C:\Users\ravin\Documents\astroagent-3d\galaxy_explorer.html",
    stats=stats,
    api_key=api_key,
)
print(f"Written to {out}")
