## Demo

### Kepler-444 Star System
<img width="1912" height="921" alt="Kepler-444 Star System" src="https://github.com/user-attachments/assets/ac1eb105-90d4-4dec-a9ac-19e366423690" />

### 6,000+ Confirmed Exoplanets Mapped in 3D
<img width="1919" height="856" alt="6000+ Confirmed Exoplanets" src="https://github.com/user-attachments/assets/ea8e81cd-04fd-4a6e-9b8d-d4ac972669fc" />

### Full Milky Way View
<img width="1912" height="911" alt="Full Milky Way View" src="https://github.com/user-attachments/assets/7369f991-56c1-427d-8797-1764ae2c5d61" />

### Solar System Tour
https://github.com/user-attachments/assets/435cc217-d157-494f-8d84-327ea2bebaf3

---

# AstroAgent 3D

**Explore every confirmed exoplanet in the Milky Way, in real-time 3D, built on live NASA data.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

---

## What This Is

A WebGL application that plots 6,000+ confirmed exoplanets in 3D space. You can zoom from a full galaxy view down into individual star systems, click on any planet to pull up real orbital data, and ask the built-in AI guide (Pulsar AI) to explain what you're looking at.

One HTML file. No installs. Every planet comes from the NASA Exoplanet Archive, not a static dataset.

## Four Views

1. **Solar System with Moons** - All eight planets with their moons, asteroid belt, habitable zone overlay, and real orbital speeds
2. **Solar System without Moons** - Cleaner view, just the planets
3. **Confirmed Planets in Our Galaxy** - Every confirmed exoplanet plotted at its real RA/Dec position, color-coded by how it was discovered
4. **Our Whole Galaxy (Milky Way)** - The full Milky Way structure with spiral arms and our Sun's location marked

## Features

- **Live NASA data** - Pulls from the [NASA Exoplanet Archive TAP API](https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html) at generation time. Real orbital periods, real discovery methods, real coordinates.
- **Pulsar AI** - Click any planet or star, hit the Pulsar AI button, get 7 facts about it. Powered by Claude Haiku 4.5.
- **Guided tour** - Automated flythrough that visits each planet in the solar system with key facts
- **Search** - Find any planet, star, or black hole across all 6,000+ objects instantly
- **Two-step galaxy exploration** - Click a star to fly near it, click again to enter the system. Double-click to jump straight in.
- **Real orbital mechanics** - Planets move at proportional speeds. Speed up or slow down with the time scale slider. Moons orbit their planets.
- **Proportional zoom** - Scroll speed adapts to how close you are. Get right up next to a moon without overshooting.
- **Responsive layout** - Works on desktop and mobile

## How It Works

### Data Pipeline

Python tools query real astronomical databases at generation time:

| Tool | Source | Purpose |
|------|--------|---------|
| `query_exoplanet_archive` | [NASA Exoplanet Archive](https://exoplanetarchive.ipac.caltech.edu/) | ADQL queries for exoplanet parameters |
| `query_galaxy_map` | NASA Exoplanet Archive | Fetches all confirmed planets with RA/Dec/distance for 3D positioning |
| `fetch_light_curve` | [MAST Archive](https://mast.stsci.edu/) | Kepler and TESS photometry data |
| `calculate_habitable_zone` | Kopparapu et al. 2013 model | Conservative and optimistic HZ boundaries from stellar properties |
| `detect_anomalies` | Built-in | Sigma-clipping outlier detection and transit signal search |
| `search_sdss` | [SDSS DR18](https://www.sdss.org/dr18/) | Cone search and SQL queries for stars, galaxies, quasars |

### 3D Rendering

The visualization lives in a single Jinja2 template (`galaxy_explorer.py`, about 3,800 lines) that outputs one self-contained HTML file. Under the hood:

- Three separate Three.js scenes: solar system, galaxy map, and Milky Way
- RA/Dec coordinates converted to 3D Cartesian positions using spherical math
- 6,000+ planets rendered with `PointsMaterial` for GPU efficiency, colored by discovery method
- Real-time orbital animation with adjustable time scale
- Black holes plotted with gravitational lensing effects
- Shooting stars, lens flares, and atmospheric particles
- Proper `.dispose()` calls on all geometry, materials, and textures so memory stays clean
- Three.js r128

### Pulsar AI

The AI assistant calls the Anthropic API through a lightweight proxy server. It uses Claude Haiku 4.5 with a prompt tuned to always return exactly 7 facts, even for obscure exoplanets with limited documentation. The API key stays on the server and never reaches the browser.

## Quick Start

```bash
git clone https://github.com/ravindrdev/astroagent3d.git
cd astroagent3d

pip install -e ".[dev]"

# Generate the explorer (pulls live data from NASA)
python gen_explorer.py

# Start the server
python server.py

# Open http://localhost:8780
```

You need Python 3.10+ and an internet connection for the NASA API call during generation. After that, the HTML file works offline (except for Pulsar AI, which needs the server running).

Set your Anthropic API key in a `.env` file:
```
ANTHROPIC_API_KEY=your-key-here
```

## Agent Mode (Jupyter)

AstroAgent also runs as a research assistant inside Jupyter notebooks:

```python
from astroagent import AstroAgent

agent = AstroAgent()
result = agent.ask(
    "Query the TRAPPIST-1 system, calculate its habitable zone, "
    "and visualize all planet orbits in 3D"
)
```

The agent uses Claude's tool-use API to pick which tools to call, pulls real data from NASA, runs the calculations, and renders interactive 3D visualizations inline in the notebook.

### Example Notebooks

| Notebook | What It Covers |
|----------|---------------|
| [01_getting_started.ipynb](examples/01_getting_started.ipynb) | First query, basic usage |
| [02_trappist1_exploration.ipynb](examples/02_trappist1_exploration.ipynb) | TRAPPIST-1 deep dive with HZ calculation and 3D viz |
| [03_anomaly_detection.ipynb](examples/03_anomaly_detection.ipynb) | Transit signal detection in light curves |

## Project Structure

```
astroagent-3d/
├── src/astroagent/
│   ├── agent/                # AI agent loop (Claude tool-calling)
│   │   ├── core.py           # AstroAgent class
│   │   └── prompts.py        # System prompt
│   ├── tools/                # 6 astronomy tools (Pydantic schemas, real APIs)
│   │   ├── exoplanet_archive.py   # NASA TAP/ADQL
│   │   ├── galaxy_map.py         # Full exoplanet catalog for 3D mapping
│   │   ├── light_curves.py       # MAST photometry
│   │   ├── habitable_zone.py     # Kopparapu+ 2013 model
│   │   ├── anomaly_detector.py   # Outlier + transit detection
│   │   └── sdss_query.py         # SDSS DR18 catalog
│   ├── viz/                  # Visualization engine
│   │   ├── galaxy_explorer.py    # Main 3D galaxy explorer (Jinja2 template)
│   │   ├── renderer.py          # Three.js scene generator
│   │   └── jupyter_widget.py    # IPython display integration
│   └── eval/                 # Scientific accuracy evaluation
│       ├── accuracy.py       # Ground-truth comparison
│       └── benchmarks.py     # Benchmark suite
├── server.py                 # API proxy server (keeps your key safe)
├── gen_explorer.py           # Script to regenerate galaxy_explorer.html
├── tests/                    # pytest suite
├── examples/                 # Jupyter demo notebooks
└── pyproject.toml            # Python packaging (hatchling)
```

## Tech Stack

- **Three.js r128** for WebGL rendering (3 scenes, real-time animation)
- **Python** data pipeline with Pydantic schemas and real API integrations
- **Jinja2** templating for self-contained HTML generation
- **Claude Haiku 4.5** powers Pulsar AI through a server-side proxy
- **NASA Exoplanet Archive TAP API** for live planetary data
- **MAST and SDSS DR18** for additional astronomical datasets

## Development

```bash
pytest tests/ -m "not slow" -v

ruff check src/ tests/
ruff format src/ tests/
```

## Built By

[Ravindra Devabhaktuni](https://github.com/ravindrdev)

## License

[Apache License 2.0](LICENSE)

## Acknowledgments

- [NASA Exoplanet Archive](https://exoplanetarchive.ipac.caltech.edu/) for planetary data via TAP/ADQL
- [MAST Archive](https://mast.stsci.edu/) for light curve photometry
- [SDSS](https://www.sdss.org/) for sky survey catalog (DR18)
- [Anthropic](https://www.anthropic.com/) for the Claude API
- [Three.js](https://threejs.org/) for WebGL rendering
- [Kopparapu et al. (2013)](https://ui.adsabs.harvard.edu/abs/2013ApJ...765..131K) for the habitable zone model
