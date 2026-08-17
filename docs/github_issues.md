# Pre-built GitHub Issues

Create these issues after pushing the repo to GitHub.
Use the labels: `enhancement`, `bug`, `good-first-issue`, `documentation`, `help-wanted`.

---

## Enhancement Issues

### 1. Add support for binary star systems
**Labels:** `enhancement`, `help-wanted`

Binary and multiple star systems (e.g., Kepler-16, Tatooine-like planets) have complex orbital dynamics. The current `OrbitRenderer` assumes single-star systems.

**Requirements:**
- Support rendering 2 stars orbiting a common barycenter
- Render circumbinary planet orbits (P-type) and circumstellar orbits (S-type)
- Update `query_exoplanet_archive` to flag binary host stars

### 2. Add TESS Candidate search tool
**Labels:** `enhancement`, `good-first-issue`

Add a tool to search the TESS Objects of Interest (TOI) catalog for unconfirmed planet candidates, not just confirmed exoplanets.

**API:** https://exoplanetarchive.ipac.caltech.edu/docs/TOI.html

### 3. Interactive habitable zone comparison view
**Labels:** `enhancement`

Add a visualization mode that renders multiple planetary systems side-by-side with normalized habitable zones, so researchers can visually compare system architectures.

### 4. Add stellar spectral classification tool
**Labels:** `enhancement`, `good-first-issue`

Add a tool that classifies stars by spectral type (O, B, A, F, G, K, M) from their effective temperature, and provides context about what that means for habitability.

### 5. Export 3D scene to glTF format
**Labels:** `enhancement`

Allow researchers to export the Three.js scene as a .glTF file for use in presentations, papers, or other 3D software.

### 6. Add radial velocity data integration
**Labels:** `enhancement`, `help-wanted`

Integrate radial velocity measurement data from archives to complement transit observations. RV data provides mass constraints that transit data alone cannot.

### 7. Phase-folded transit plot in visualization
**Labels:** `enhancement`

When the agent detects a periodic transit signal, automatically generate a phase-folded plot that stacks all transits at the same phase for clearer visualization.

---

## Documentation Issues

### 8. Add API reference documentation
**Labels:** `documentation`, `good-first-issue`

Generate API docs from docstrings using mkdocs + mkdocstrings. Deploy to GitHub Pages.

### 9. Write tutorial: "Finding Your First Exoplanet"
**Labels:** `documentation`, `help-wanted`

A narrative tutorial notebook that walks a newcomer through using AstroAgent to discover and characterize an exoplanet, explaining the astronomy concepts along the way.

---

## Bug / Improvement Issues

### 10. Handle NASA API rate limiting gracefully
**Labels:** `bug`

The NASA Exoplanet Archive API has rate limits. Currently, hitting the limit returns an opaque error. Should detect 429 responses and implement exponential backoff.

### 11. Light curve tool should support phase folding
**Labels:** `enhancement`

When the orbital period is known, the light curve tool should support returning phase-folded data (all transits stacked at the same phase).

### 12. Improve 3D performance for systems with 8+ planets
**Labels:** `bug`, `good-first-issue`

The orbit animation can lag on older hardware when rendering many planets. Consider using instanced rendering or reducing geometry complexity for distant planets.
