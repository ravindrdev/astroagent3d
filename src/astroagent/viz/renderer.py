"""Generate Three.js 3D orbit visualizations from planetary data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jinja2 import Template


class OrbitRenderer:
    """Renders interactive 3D orbital visualizations using Three.js.

    Takes planetary system data (orbital parameters, masses, radii)
    and generates a self-contained HTML page with an interactive
    Three.js scene showing orbits, planets, habitable zones, and
    clickable info cards.
    """

    PLANET_COLORS = {
        "hot": "#e24b4a",
        "warm": "#d85a30",
        "temperate": "#4a90d9",
        "cold": "#7ec8e3",
        "frozen": "#9fd5d1",
        "gas_giant": "#c4956a",
        "default": "#85B7EB",
    }

    def render(
        self,
        planets: list[dict[str, Any]],
        hz_inner_au: float | None = None,
        hz_outer_au: float | None = None,
        title: str | None = None,
    ) -> str:
        """Generate a complete HTML page with Three.js 3D orbit visualization."""
        system_name = self._detect_system_name(planets)
        if title is None:
            title = f"{system_name} — 3D Orbital View"

        processed = self._process_planets(planets)

        scale = self._compute_scale(processed)

        scene_data = {
            "title": title,
            "system_name": system_name,
            "planets": processed,
            "scale_au_to_units": scale,
            "hz_inner": hz_inner_au * scale if hz_inner_au else None,
            "hz_outer": hz_outer_au * scale if hz_outer_au else None,
            "star": self._infer_star(planets),
        }

        template = Template(self._get_template())
        return template.render(**scene_data, scene_json=json.dumps(scene_data, default=str))

    def render_to_file(
        self,
        planets: list[dict[str, Any]],
        output_path: str | Path,
        **kwargs: Any,
    ) -> Path:
        """Render and save to an HTML file."""
        html = self.render(planets, **kwargs)
        path = Path(output_path)
        path.write_text(html, encoding="utf-8")
        return path

    def _detect_system_name(self, planets: list[dict[str, Any]]) -> str:
        if planets:
            host = planets[0].get("host_star") or planets[0].get("hostname", "")
            if host:
                return str(host)
            name = planets[0].get("name", "")
            if name:
                parts = str(name).rsplit(" ", 1)
                return parts[0] if len(parts) > 1 else name
        return "Unknown System"

    def _process_planets(self, planets: list[dict[str, Any]]) -> list[dict[str, Any]]:
        processed = []
        for p in planets:
            sma = p.get("semi_major_axis_au")
            if sma is None:
                continue

            temp = p.get("equilibrium_temp_k")
            color = self._planet_color(temp, p.get("mass_earth"))
            radius_display = max(0.3, min(2.0, (p.get("radius_earth") or 1.0) * 0.5))

            processed.append(
                {
                    "name": p.get("name", "Unknown"),
                    "semi_major_axis_au": float(sma),
                    "eccentricity": float(p.get("eccentricity") or 0.0),
                    "orbital_period_days": p.get("orbital_period_days"),
                    "mass_earth": p.get("mass_earth"),
                    "radius_earth": p.get("radius_earth"),
                    "equilibrium_temp_k": temp,
                    "inclination_deg": p.get("inclination_deg") or 90.0,
                    "color": color,
                    "radius_display": radius_display,
                    "discovery_method": p.get("discovery_method"),
                }
            )
        processed.sort(key=lambda x: x["semi_major_axis_au"])
        return processed

    def _planet_color(self, temp_k: float | None, mass_earth: float | None) -> str:
        if mass_earth and mass_earth > 50:
            return self.PLANET_COLORS["gas_giant"]
        if temp_k is None:
            return self.PLANET_COLORS["default"]
        if temp_k > 1000:
            return self.PLANET_COLORS["hot"]
        if temp_k > 400:
            return self.PLANET_COLORS["warm"]
        if temp_k > 200:
            return self.PLANET_COLORS["temperate"]
        if temp_k > 100:
            return self.PLANET_COLORS["cold"]
        return self.PLANET_COLORS["frozen"]

    def _compute_scale(self, planets: list[dict[str, Any]]) -> float:
        if not planets:
            return 100.0
        max_sma = max(p["semi_major_axis_au"] for p in planets)
        if max_sma <= 0:
            return 100.0
        return 40.0 / max_sma

    def _infer_star(self, planets: list[dict[str, Any]]) -> dict[str, Any]:
        if not planets:
            return {"temp_k": 5778, "radius_solar": 1.0, "color": "#fff5e0"}
        p = planets[0]
        temp = p.get("star_temp_k") or 5778
        radius = p.get("star_radius_solar") or 1.0

        if temp > 7500:
            color = "#cad8ff"
        elif temp > 6000:
            color = "#fff5e0"
        elif temp > 5000:
            color = "#ffd27d"
        elif temp > 3500:
            color = "#ff6b35"
        else:
            color = "#ff4500"

        return {
            "temp_k": temp,
            "radius_solar": radius,
            "color": color,
            "display_radius": max(1.0, min(4.0, radius * 2.0)),
        }

    def _get_template(self) -> str:
        template_path = Path(__file__).parent / "templates" / "orbit_viewer.html"
        if template_path.exists():
            return template_path.read_text(encoding="utf-8")
        return _FALLBACK_TEMPLATE


_FALLBACK_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{{ title }}</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0e27;color:#fff;font-family:system-ui,sans-serif;overflow:hidden}
#canvas-container{width:100vw;height:100vh;position:relative}
canvas{display:block}
#controls{position:absolute;bottom:20px;left:50%;transform:translateX(-50%);
display:flex;gap:8px;z-index:10}
.btn{padding:6px 14px;border-radius:6px;border:1px solid rgba(255,255,255,0.2);
background:rgba(10,14,39,0.8);color:#fff;cursor:pointer;font-size:12px;
backdrop-filter:blur(10px);transition:all .2s}
.btn:hover,.btn.active{border-color:rgba(100,160,255,0.5);background:rgba(30,50,100,0.6)}
#info-card{position:absolute;top:20px;right:20px;background:rgba(10,14,39,0.9);
border:1px solid rgba(255,255,255,0.1);border-radius:12px;padding:16px 20px;
min-width:200px;display:none;backdrop-filter:blur(10px);z-index:10}
#info-card.show{display:block}
#info-card h3{font-size:16px;margin-bottom:10px;font-weight:500}
.info-row{display:flex;justify-content:space-between;padding:3px 0;font-size:13px}
.info-label{color:rgba(255,255,255,0.5)}
.info-value{color:#a5d6ff;font-family:monospace}
#title-bar{position:absolute;top:20px;left:20px;z-index:10}
#title-bar h1{font-size:18px;font-weight:500}
#title-bar p{font-size:12px;color:rgba(255,255,255,0.5);margin-top:4px}
#speed-control{position:absolute;bottom:60px;left:50%;transform:translateX(-50%);
display:flex;align-items:center;gap:10px;z-index:10;font-size:12px;
color:rgba(255,255,255,0.6)}
#speed-slider{width:120px;accent-color:#4a90d9}
</style>
</head>
<body>
<div id="canvas-container">
  <div id="title-bar"><h1>{{ system_name }}</h1><p>Interactive 3D orbital visualization — real NASA data</p></div>
  <div id="info-card"><h3 id="card-name"></h3><div id="card-body"></div></div>
  <div id="speed-control">
    <span>Speed</span>
    <input type="range" id="speed-slider" min="0" max="5" step="0.1" value="1"/>
    <span id="speed-label">1x</span>
  </div>
  <div id="controls">
    <button class="btn active" id="btn-orbits">Orbits</button>
    <button class="btn active" id="btn-hz">Habitable zone</button>
    <button class="btn active" id="btn-labels">Labels</button>
    <button class="btn" id="btn-pause">Pause</button>
  </div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
const SCENE_DATA = {{ scene_json }};
const P = SCENE_DATA.planets;
const SCALE = SCENE_DATA.scale_au_to_units;

let scene, camera, renderer, controls;
let planetMeshes = [], orbitLines = [], labelSprites = [];
let hzMesh = null, paused = false, speedMul = 1;
let showOrbits = true, showHZ = true, showLabels = true;

function init() {
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(60, window.innerWidth/window.innerHeight, 0.1, 1000);
  camera.position.set(30, 40, 50);
  camera.lookAt(0, 0, 0);

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(window.devicePixelRatio);
  document.getElementById('canvas-container').appendChild(renderer.domElement);

  scene.add(new THREE.AmbientLight(0x404040, 0.5));
  const pointLight = new THREE.PointLight(0xffffff, 2, 200);
  scene.add(pointLight);

  // Star
  const starColor = new THREE.Color(SCENE_DATA.star.color);
  const starGeo = new THREE.SphereGeometry(SCENE_DATA.star.display_radius, 32, 32);
  const starMat = new THREE.MeshBasicMaterial({ color: starColor });
  const starMesh = new THREE.Mesh(starGeo, starMat);
  scene.add(starMesh);

  // Star glow
  const glowGeo = new THREE.SphereGeometry(SCENE_DATA.star.display_radius * 1.8, 32, 32);
  const glowMat = new THREE.MeshBasicMaterial({
    color: starColor, transparent: true, opacity: 0.15
  });
  scene.add(new THREE.Mesh(glowGeo, glowMat));

  // Planets
  P.forEach((p, i) => {
    const r = p.semi_major_axis_au * SCALE;
    const pColor = new THREE.Color(p.color);

    // Orbit ring
    const curve = new THREE.EllipseCurve(0, 0, r, r * (1 - (p.eccentricity || 0)), 0, 2*Math.PI, false, 0);
    const pts = curve.getPoints(128);
    const orbitGeo = new THREE.BufferGeometry().setFromPoints(
      pts.map(pt => new THREE.Vector3(pt.x, 0, pt.y))
    );
    const orbitLine = new THREE.Line(orbitGeo, new THREE.LineBasicMaterial({
      color: 0xffffff, transparent: true, opacity: 0.15
    }));
    scene.add(orbitLine);
    orbitLines.push(orbitLine);

    // Planet sphere
    const planetGeo = new THREE.SphereGeometry(p.radius_display, 16, 16);
    const planetMat = new THREE.MeshStandardMaterial({
      color: pColor, roughness: 0.7, metalness: 0.1
    });
    const mesh = new THREE.Mesh(planetGeo, planetMat);
    mesh.userData = { index: i, ...p };
    scene.add(mesh);
    planetMeshes.push({ mesh, radius: r, angle: Math.random() * Math.PI * 2, speed: p.orbital_period_days ? (0.02 / p.orbital_period_days) : 0.01, ecc: p.eccentricity || 0 });

    // Label
    const canvas = document.createElement('canvas');
    canvas.width = 256; canvas.height = 64;
    const ctx = canvas.getContext('2d');
    ctx.font = '24px system-ui';
    ctx.fillStyle = '#ffffff';
    ctx.textAlign = 'center';
    ctx.fillText(p.name.split(' ').pop(), 128, 40);
    const tex = new THREE.CanvasTexture(canvas);
    const spriteMat = new THREE.SpriteMaterial({ map: tex, transparent: true, opacity: 0.8 });
    const sprite = new THREE.Sprite(spriteMat);
    sprite.scale.set(6, 1.5, 1);
    scene.add(sprite);
    labelSprites.push(sprite);
  });

  // Habitable zone
  if (SCENE_DATA.hz_inner && SCENE_DATA.hz_outer) {
    const hzGeo = new THREE.RingGeometry(SCENE_DATA.hz_inner, SCENE_DATA.hz_outer, 64);
    const hzMat = new THREE.MeshBasicMaterial({
      color: 0x22c55e, transparent: true, opacity: 0.08, side: THREE.DoubleSide
    });
    hzMesh = new THREE.Mesh(hzGeo, hzMat);
    hzMesh.rotation.x = -Math.PI / 2;
    scene.add(hzMesh);
  }

  // Starfield background
  const starFieldGeo = new THREE.BufferGeometry();
  const starPositions = [];
  for (let i = 0; i < 2000; i++) {
    starPositions.push((Math.random() - 0.5) * 400, (Math.random() - 0.5) * 400, (Math.random() - 0.5) * 400);
  }
  starFieldGeo.setAttribute('position', new THREE.Float32BufferAttribute(starPositions, 3));
  scene.add(new THREE.Points(starFieldGeo, new THREE.PointsMaterial({ color: 0xffffff, size: 0.3 })));

  // Mouse interaction
  const raycaster = new THREE.Raycaster();
  const mouse = new THREE.Vector2();
  renderer.domElement.addEventListener('click', (e) => {
    mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
    mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
    raycaster.setFromCamera(mouse, camera);
    const hits = raycaster.intersectObjects(planetMeshes.map(p => p.mesh));
    if (hits.length > 0) showInfoCard(hits[0].object.userData);
    else document.getElementById('info-card').classList.remove('show');
  });

  // Simple orbit controls
  let isDragging = false, prevX = 0, prevY = 0;
  let theta = Math.PI/4, phi = Math.PI/4, dist = 70;
  renderer.domElement.addEventListener('mousedown', e => { isDragging = true; prevX = e.clientX; prevY = e.clientY; });
  renderer.domElement.addEventListener('mousemove', e => {
    if (!isDragging) return;
    theta -= (e.clientX - prevX) * 0.005;
    phi = Math.max(0.1, Math.min(Math.PI/2 - 0.01, phi - (e.clientY - prevY) * 0.005));
    prevX = e.clientX; prevY = e.clientY;
    updateCamera();
  });
  renderer.domElement.addEventListener('mouseup', () => isDragging = false);
  renderer.domElement.addEventListener('wheel', e => {
    dist = Math.max(15, Math.min(200, dist + e.deltaY * 0.05));
    updateCamera();
  });
  function updateCamera() {
    camera.position.set(dist*Math.sin(theta)*Math.cos(phi), dist*Math.sin(phi), dist*Math.cos(theta)*Math.cos(phi));
    camera.lookAt(0, 0, 0);
  }
  updateCamera();

  // Controls
  document.getElementById('btn-pause').addEventListener('click', function() {
    paused = !paused; this.textContent = paused ? 'Play' : 'Pause';
    this.classList.toggle('active');
  });
  document.getElementById('btn-orbits').addEventListener('click', function() {
    showOrbits = !showOrbits; this.classList.toggle('active');
    orbitLines.forEach(l => l.visible = showOrbits);
  });
  document.getElementById('btn-hz').addEventListener('click', function() {
    showHZ = !showHZ; this.classList.toggle('active');
    if (hzMesh) hzMesh.visible = showHZ;
  });
  document.getElementById('btn-labels').addEventListener('click', function() {
    showLabels = !showLabels; this.classList.toggle('active');
    labelSprites.forEach(s => s.visible = showLabels);
  });
  document.getElementById('speed-slider').addEventListener('input', function() {
    speedMul = parseFloat(this.value);
    document.getElementById('speed-label').textContent = speedMul.toFixed(1) + 'x';
  });

  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });
}

function showInfoCard(data) {
  const card = document.getElementById('info-card');
  document.getElementById('card-name').textContent = data.name;
  const rows = [
    ['Mass', data.mass_earth ? data.mass_earth.toFixed(3) + ' M⊕' : '—'],
    ['Radius', data.radius_earth ? data.radius_earth.toFixed(3) + ' R⊕' : '—'],
    ['Period', data.orbital_period_days ? data.orbital_period_days.toFixed(3) + ' days' : '—'],
    ['Semi-major axis', data.semi_major_axis_au.toFixed(5) + ' AU'],
    ['Eccentricity', (data.eccentricity || 0).toFixed(4)],
    ['Eq. temperature', data.equilibrium_temp_k ? data.equilibrium_temp_k.toFixed(0) + ' K' : '—'],
    ['Discovery', data.discovery_method || '—'],
  ];
  document.getElementById('card-body').innerHTML = rows.map(
    ([l, v]) => `<div class="info-row"><span class="info-label">${l}</span><span class="info-value">${v}</span></div>`
  ).join('');
  card.classList.add('show');
}

function animate() {
  requestAnimationFrame(animate);
  if (!paused) {
    planetMeshes.forEach((p, i) => {
      p.angle += p.speed * speedMul;
      const r = p.radius * (1 - p.ecc * Math.cos(p.angle));
      p.mesh.position.set(Math.cos(p.angle) * r, 0, Math.sin(p.angle) * r);
      if (labelSprites[i]) {
        labelSprites[i].position.set(p.mesh.position.x, p.mesh.position.y + p.mesh.userData.radius_display + 1.5, p.mesh.position.z);
      }
    });
  }
  renderer.render(scene, camera);
}

init();
animate();
</script>
</body>
</html>"""
