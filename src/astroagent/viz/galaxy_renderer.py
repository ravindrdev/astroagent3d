"""Generate Three.js 3D galaxy map visualization of all known exoplanets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jinja2 import Template


class GalaxyMapRenderer:
    """Renders a 3D map of all known exoplanets positioned in the Milky Way."""

    METHOD_COLORS = {
        "Transit": "#4a90d9",
        "Radial Velocity": "#e24b4a",
        "Imaging": "#22c55e",
        "Microlensing": "#f59e0b",
        "Transit Timing Variations": "#8b5cf6",
        "Eclipse Timing Variations": "#ec4899",
        "Pulsar Timing": "#06b6d4",
        "Orbital Brightness Modulation": "#f97316",
        "Astrometry": "#14b8a6",
        "Disk Kinematics": "#a855f7",
    }
    DEFAULT_COLOR = "#85B7EB"

    def render(
        self,
        planets: list[dict[str, Any]],
        stats: dict[str, Any] | None = None,
        title: str | None = None,
    ) -> str:
        if title is None:
            title = f"Every Known Exoplanet — 3D Galaxy Map ({len(planets)} planets)"

        max_dist = max((p.get("distance_pc") or 1) for p in planets) if planets else 1000
        scale = 80.0 / max_dist

        processed = []
        for p in planets:
            x = p.get("x")
            y = p.get("y")
            z = p.get("z")
            if x is None or y is None or z is None:
                continue
            method = p.get("discovery_method") or "Unknown"
            color = self.METHOD_COLORS.get(method, self.DEFAULT_COLOR)
            processed.append(
                {
                    "name": p.get("name", "Unknown"),
                    "host_star": p.get("host_star", "Unknown"),
                    "x": float(x) * scale,
                    "y": float(y) * scale,
                    "z": float(z) * scale,
                    "distance_pc": p.get("distance_pc"),
                    "distance_ly": p.get("distance_ly"),
                    "ra": p.get("ra"),
                    "dec": p.get("dec"),
                    "discovery_method": method,
                    "discovery_year": p.get("discovery_year"),
                    "radius_earth": p.get("radius_earth"),
                    "mass_earth": p.get("mass_earth"),
                    "equilibrium_temp_k": p.get("equilibrium_temp_k"),
                    "orbital_period_days": p.get("orbital_period_days"),
                    "color": color,
                }
            )

        method_colors_json = json.dumps(self.METHOD_COLORS)

        template = Template(_GALAXY_TEMPLATE)
        return template.render(
            title=title,
            planets_json=json.dumps(processed, default=str),
            stats_json=json.dumps(stats or {}, default=str),
            method_colors_json=method_colors_json,
            planet_count=len(processed),
        )

    def render_to_file(
        self,
        planets: list[dict[str, Any]],
        output_path: str | Path,
        **kwargs: Any,
    ) -> Path:
        html = self.render(planets, **kwargs)
        path = Path(output_path)
        path.write_text(html, encoding="utf-8")
        return path


_GALAXY_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{{ title }}</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;color:#fff;font-family:'Inter',system-ui,-apple-system,sans-serif;overflow:hidden;cursor:grab}
body.dragging{cursor:grabbing}
#canvas-container{width:100vw;height:100vh;position:relative}
canvas{display:block}

#title-bar{position:absolute;top:24px;left:28px;z-index:10;pointer-events:none}
#title-bar h1{font-size:20px;font-weight:600;letter-spacing:-0.3px;
  text-shadow:0 0 30px rgba(100,160,255,0.4)}
#title-bar .subtitle{font-size:11px;color:rgba(255,255,255,0.35);margin-top:5px;
  text-transform:uppercase;letter-spacing:1.5px}
#title-bar .count{font-size:32px;font-weight:700;margin-top:10px;
  background:linear-gradient(135deg,#4a90d9,#22c55e);-webkit-background-clip:text;
  -webkit-text-fill-color:transparent;letter-spacing:-1px}
#title-bar .count-label{font-size:10px;color:rgba(255,255,255,0.3);
  text-transform:uppercase;letter-spacing:2px;margin-top:2px}

#legend{position:absolute;bottom:24px;left:28px;z-index:10;
  background:rgba(8,12,30,0.8);border:1px solid rgba(255,255,255,0.06);
  border-radius:12px;padding:14px 18px;backdrop-filter:blur(16px)}
#legend h4{font-size:10px;text-transform:uppercase;letter-spacing:1.5px;
  color:rgba(255,255,255,0.35);margin-bottom:10px;font-weight:500}
.legend-item{display:flex;align-items:center;gap:8px;padding:3px 0;
  font-size:11px;color:rgba(255,255,255,0.6);cursor:pointer;transition:opacity .2s}
.legend-item:hover{color:#fff}
.legend-item.dimmed{opacity:0.25}
.legend-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}

#info-card{position:absolute;top:24px;right:24px;
  background:rgba(8,12,30,0.88);border:1px solid rgba(255,255,255,0.08);
  border-radius:14px;padding:18px 22px;min-width:220px;max-width:280px;
  display:none;backdrop-filter:blur(20px);z-index:10;
  box-shadow:0 8px 32px rgba(0,0,0,0.5)}
#info-card.show{display:block;animation:cardIn 0.25s ease}
@keyframes cardIn{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:translateY(0)}}
#info-card h3{font-size:16px;font-weight:600;margin-bottom:2px}
#info-card .card-host{font-size:11px;color:rgba(255,255,255,0.35);margin-bottom:12px}
.info-row{display:flex;justify-content:space-between;padding:4px 0;font-size:12px;
  border-bottom:1px solid rgba(255,255,255,0.04)}
.info-row:last-child{border-bottom:none}
.info-label{color:rgba(255,255,255,0.4)}
.info-value{color:#a5d6ff;font-family:'SF Mono',monospace;font-weight:500}

#stats-bar{position:absolute;top:24px;left:50%;transform:translateX(-50%);
  display:flex;gap:24px;z-index:10;pointer-events:none}
.stat-item{text-align:center}
.stat-value{font-size:18px;font-weight:700;color:#fff}
.stat-label{font-size:9px;text-transform:uppercase;letter-spacing:1.5px;
  color:rgba(255,255,255,0.3);margin-top:2px}

#controls{position:absolute;bottom:24px;right:28px;display:flex;gap:6px;z-index:10}
.btn{padding:7px 16px;border-radius:20px;border:1px solid rgba(255,255,255,0.1);
  background:rgba(255,255,255,0.04);color:rgba(255,255,255,0.6);cursor:pointer;
  font-size:10px;font-weight:500;letter-spacing:0.3px;text-transform:uppercase;
  transition:all 0.2s}
.btn:hover{border-color:rgba(100,160,255,0.4);color:#fff;background:rgba(100,160,255,0.1)}
.btn.active{border-color:rgba(100,160,255,0.5);color:#fff;background:rgba(100,160,255,0.12)}

#search-box{position:absolute;top:24px;right:24px;z-index:11;display:none}
#search-input{width:250px;padding:8px 14px;border-radius:20px;
  border:1px solid rgba(255,255,255,0.1);background:rgba(8,12,30,0.9);
  color:#fff;font-size:12px;outline:none;backdrop-filter:blur(16px)}
#search-input:focus{border-color:rgba(100,160,255,0.5)}
#search-input::placeholder{color:rgba(255,255,255,0.25)}

.tooltip{position:absolute;padding:4px 10px;border-radius:8px;
  background:rgba(8,12,30,0.92);border:1px solid rgba(255,255,255,0.1);
  font-size:11px;color:rgba(255,255,255,0.8);pointer-events:none;display:none;
  white-space:nowrap;z-index:20;backdrop-filter:blur(10px)}
</style>
</head>
<body>
<div id="canvas-container">
  <div id="title-bar">
    <h1>Exoplanet Galaxy Map</h1>
    <div class="subtitle">Every Confirmed Planet in the Milky Way</div>
    <div class="count">{{ planet_count }}</div>
    <div class="count-label">Confirmed Exoplanets</div>
  </div>

  <div id="stats-bar"></div>

  <div id="legend"></div>

  <div id="info-card">
    <h3 id="card-name"></h3>
    <div class="card-host" id="card-host"></div>
    <div id="card-body"></div>
  </div>

  <div id="controls">
    <button class="btn active" id="btn-grid">Grid</button>
    <button class="btn active" id="btn-sun">Sun</button>
    <button class="btn" id="btn-search">Search</button>
    <button class="btn" id="btn-spin">Auto-Rotate</button>
  </div>

  <div id="search-box">
    <input type="text" id="search-input" placeholder="Search planet or star name..."/>
  </div>

  <div class="tooltip" id="tooltip"></div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
const PLANETS = {{ planets_json }};
const STATS = {{ stats_json }};
const METHOD_COLORS = {{ method_colors_json }};

let scene, camera, renderer;
let pointCloud, pointPositions, pointColors, pointSizes;
let gridHelper, sunMarker;
let autoRotate = false, showGrid = true;
let highlightedIndex = -1;
let activeFilters = new Set();

function init() {
  scene = new THREE.Scene();

  camera = new THREE.PerspectiveCamera(55, innerWidth / innerHeight, 0.1, 2000);
  camera.position.set(60, 45, 80);
  camera.lookAt(0, 0, 0);

  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(innerWidth, innerHeight);
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.0;
  document.getElementById('canvas-container').appendChild(renderer.domElement);

  // Background starfield
  const bgGeo = new THREE.BufferGeometry();
  const bgPos = new Float32Array(8000 * 3);
  for (let i = 0; i < 8000; i++) {
    const th = Math.random() * Math.PI * 2;
    const ph = Math.acos(2 * Math.random() - 1);
    const r = 400 + Math.random() * 600;
    bgPos[i*3] = r * Math.sin(ph) * Math.cos(th);
    bgPos[i*3+1] = r * Math.sin(ph) * Math.sin(th);
    bgPos[i*3+2] = r * Math.cos(ph);
  }
  bgGeo.setAttribute('position', new THREE.Float32BufferAttribute(bgPos, 3));
  scene.add(new THREE.Points(bgGeo, new THREE.PointsMaterial({
    color: 0xffffff, size: 0.3, transparent: true, opacity: 0.5,
    blending: THREE.AdditiveBlending, depthWrite: false
  })));

  // Sun marker (origin)
  const sunGeo = new THREE.SphereGeometry(0.5, 24, 24);
  const sunMat = new THREE.MeshBasicMaterial({ color: '#ffdd44' });
  sunMarker = new THREE.Mesh(sunGeo, sunMat);
  scene.add(sunMarker);
  // Sun glow
  for (let i = 1; i <= 3; i++) {
    scene.add(new THREE.Mesh(
      new THREE.SphereGeometry(0.5 + i * 0.4, 16, 16),
      new THREE.MeshBasicMaterial({
        color: '#ffdd44', transparent: true, opacity: 0.12 / i,
        blending: THREE.AdditiveBlending, depthWrite: false
      })
    ));
  }
  // Sun label
  const sunCanvas = document.createElement('canvas');
  sunCanvas.width = 128; sunCanvas.height = 48;
  const sCtx = sunCanvas.getContext('2d');
  sCtx.font = '600 20px system-ui'; sCtx.fillStyle = '#ffdd44';
  sCtx.textAlign = 'center'; sCtx.fillText('Sun', 64, 30);
  const sunTex = new THREE.CanvasTexture(sunCanvas);
  const sunSprite = new THREE.Sprite(new THREE.SpriteMaterial({
    map: sunTex, transparent: true, opacity: 0.9, depthWrite: false
  }));
  sunSprite.position.set(0, 2, 0);
  sunSprite.scale.set(4, 1.5, 1);
  sunMarker.add(sunSprite);

  // Grid
  gridHelper = new THREE.GridHelper(200, 20, 0x1a2744, 0x0d1a2d);
  gridHelper.position.y = -0.5;
  scene.add(gridHelper);

  // Exoplanet point cloud
  const count = PLANETS.length;
  const positions = new Float32Array(count * 3);
  const colors = new Float32Array(count * 3);
  const sizes = new Float32Array(count);

  PLANETS.forEach((p, i) => {
    positions[i*3] = p.x;
    positions[i*3+1] = p.z;  // map z -> y for vertical
    positions[i*3+2] = p.y;
    const c = new THREE.Color(p.color);
    colors[i*3] = c.r;
    colors[i*3+1] = c.g;
    colors[i*3+2] = c.b;
    sizes[i] = 3.5;
  });

  pointPositions = positions;
  pointColors = colors;
  pointSizes = sizes;

  const geom = new THREE.BufferGeometry();
  geom.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geom.setAttribute('customColor', new THREE.Float32BufferAttribute(colors, 3));
  geom.setAttribute('size', new THREE.Float32BufferAttribute(sizes, 1));

  const mat = new THREE.ShaderMaterial({
    uniforms: { time: { value: 0 } },
    vertexShader: `
      attribute float size;
      attribute vec3 customColor;
      varying vec3 vColor;
      void main() {
        vColor = customColor;
        vec4 mvPos = modelViewMatrix * vec4(position, 1.0);
        gl_PointSize = size * (200.0 / -mvPos.z);
        gl_PointSize = clamp(gl_PointSize, 2.0, 24.0);
        gl_Position = projectionMatrix * mvPos;
      }
    `,
    fragmentShader: `
      varying vec3 vColor;
      void main() {
        float d = length(gl_PointCoord - 0.5) * 2.0;
        float core = 1.0 - smoothstep(0.0, 0.5, d);
        float glow = exp(-d * 1.8) * 0.7;
        float alpha = core + glow;
        vec3 col = mix(vColor, vec3(1.0), core * 0.3);
        gl_FragColor = vec4(col, alpha);
      }
    `,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  });

  pointCloud = new THREE.Points(geom, mat);
  scene.add(pointCloud);

  // Distance rings
  [10, 25, 50, 100].forEach(r => {
    const scaled = r * (80.0 / (STATS.farthest_pc || 1000));
    const ringGeo = new THREE.TorusGeometry(scaled, 0.02, 8, 128);
    const ringMat = new THREE.MeshBasicMaterial({
      color: 0x1a3050, transparent: true, opacity: 0.2
    });
    const ring = new THREE.Mesh(ringGeo, ringMat);
    ring.rotation.x = Math.PI / 2;
    ring.position.y = -0.4;
    scene.add(ring);
  });

  // Build legend
  buildLegend();
  buildStats();

  // Camera controls
  let dragging = false, px = 0, py = 0;
  let theta = Math.PI / 4, phi = Math.PI / 5, dist = 110;
  let targetTheta = theta, targetPhi = phi, targetDist = dist;
  const cv = renderer.domElement;

  const raycaster = new THREE.Raycaster();

  cv.addEventListener('mousedown', e => {
    dragging = true; px = e.clientX; py = e.clientY;
    document.body.classList.add('dragging');
  });
  cv.addEventListener('mousemove', e => {
    if (dragging) {
      targetTheta -= (e.clientX - px) * 0.004;
      targetPhi = Math.max(0.05, Math.min(1.5, targetPhi - (e.clientY - py) * 0.004));
      px = e.clientX; py = e.clientY;
    }
    // Hover tooltip
    const mouse = new THREE.Vector2(
      (e.clientX / innerWidth) * 2 - 1,
      -(e.clientY / innerHeight) * 2 + 1
    );
    raycaster.setFromCamera(mouse, camera);
    raycaster.params.Points.threshold = 1.2;
    const hits = raycaster.intersectObject(pointCloud);
    const tip = document.getElementById('tooltip');
    if (hits.length > 0) {
      const idx = hits[0].index;
      const p = PLANETS[idx];
      tip.textContent = p.name + ' (' + (p.distance_ly || '?') + ' ly)';
      tip.style.display = 'block';
      tip.style.left = (e.clientX + 14) + 'px';
      tip.style.top = (e.clientY - 10) + 'px';
      cv.style.cursor = 'pointer';
    } else {
      tip.style.display = 'none';
      cv.style.cursor = dragging ? 'grabbing' : 'grab';
    }
  });
  window.addEventListener('mouseup', () => {
    dragging = false;
    document.body.classList.remove('dragging');
  });
  cv.addEventListener('wheel', e => {
    e.preventDefault();
    targetDist = Math.max(8, Math.min(400, targetDist + e.deltaY * 0.12));
  }, { passive: false });

  // Touch
  let lastTD = 0;
  cv.addEventListener('touchstart', e => {
    if (e.touches.length === 1) { dragging = true; px = e.touches[0].clientX; py = e.touches[0].clientY; }
    else if (e.touches.length === 2) lastTD = Math.hypot(e.touches[0].clientX-e.touches[1].clientX, e.touches[0].clientY-e.touches[1].clientY);
  });
  cv.addEventListener('touchmove', e => {
    e.preventDefault();
    if (e.touches.length === 1 && dragging) {
      targetTheta -= (e.touches[0].clientX - px) * 0.004;
      targetPhi = Math.max(0.05, Math.min(1.5, targetPhi - (e.touches[0].clientY - py) * 0.004));
      px = e.touches[0].clientX; py = e.touches[0].clientY;
    } else if (e.touches.length === 2) {
      const d = Math.hypot(e.touches[0].clientX-e.touches[1].clientX, e.touches[0].clientY-e.touches[1].clientY);
      targetDist = Math.max(8, Math.min(400, targetDist - (d - lastTD) * 0.15));
      lastTD = d;
    }
  }, { passive: false });
  cv.addEventListener('touchend', () => dragging = false);

  // Click to select
  cv.addEventListener('click', e => {
    const mouse = new THREE.Vector2(
      (e.clientX / innerWidth) * 2 - 1,
      -(e.clientY / innerHeight) * 2 + 1
    );
    raycaster.setFromCamera(mouse, camera);
    raycaster.params.Points.threshold = 1.2;
    const hits = raycaster.intersectObject(pointCloud);
    if (hits.length > 0) {
      showInfoCard(PLANETS[hits[0].index]);
    } else {
      document.getElementById('info-card').classList.remove('show');
    }
  });

  // Button handlers
  document.getElementById('btn-grid').addEventListener('click', function() {
    showGrid = !showGrid;
    gridHelper.visible = showGrid;
    this.classList.toggle('active');
  });
  document.getElementById('btn-sun').addEventListener('click', function() {
    sunMarker.visible = !sunMarker.visible;
    this.classList.toggle('active');
  });
  document.getElementById('btn-spin').addEventListener('click', function() {
    autoRotate = !autoRotate;
    this.classList.toggle('active');
  });
  document.getElementById('btn-search').addEventListener('click', function() {
    const box = document.getElementById('search-box');
    const card = document.getElementById('info-card');
    if (box.style.display === 'block') {
      box.style.display = 'none';
      card.classList.remove('show');
    } else {
      box.style.display = 'block';
      card.style.display = 'none';
      document.getElementById('search-input').focus();
    }
    this.classList.toggle('active');
  });

  document.getElementById('search-input').addEventListener('input', function() {
    const q = this.value.toLowerCase().trim();
    if (q.length < 2) return;
    const match = PLANETS.findIndex(p =>
      (p.name && p.name.toLowerCase().includes(q)) ||
      (p.host_star && p.host_star.toLowerCase().includes(q))
    );
    if (match >= 0) showInfoCard(PLANETS[match]);
  });

  window.addEventListener('resize', () => {
    camera.aspect = innerWidth / innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(innerWidth, innerHeight);
  });

  // Store camera state
  window._cam = { theta, phi, dist, targetTheta, targetPhi, targetDist };
  window._updateCam = function() {
    const c = window._cam;
    theta += (targetTheta - theta) * 0.06;
    phi += (targetPhi - phi) * 0.06;
    dist += (targetDist - dist) * 0.06;
    if (autoRotate && !dragging) targetTheta += 0.002;
    camera.position.set(
      dist * Math.sin(theta) * Math.cos(phi),
      dist * Math.sin(phi),
      dist * Math.cos(theta) * Math.cos(phi)
    );
    camera.lookAt(0, 0, 0);
  };
}

function buildLegend() {
  const container = document.getElementById('legend');
  let html = '<h4>Discovery Method</h4>';
  const methods = STATS.discovery_methods || {};
  Object.entries(methods).slice(0, 8).forEach(([method, count]) => {
    const color = METHOD_COLORS[method] || '#85B7EB';
    html += `<div class="legend-item" data-method="${method}" onclick="toggleMethod('${method}', this)">
      <span class="legend-dot" style="background:${color}"></span>
      ${method} <span style="color:rgba(255,255,255,0.25);margin-left:auto;font-size:10px">${count}</span>
    </div>`;
  });
  container.innerHTML = html;
}

function buildStats() {
  const bar = document.getElementById('stats-bar');
  if (!STATS.total_planets) return;
  const items = [
    [STATS.nearest_pc ? (STATS.nearest_pc * 3.26).toFixed(1) + ' ly' : '—', 'Nearest'],
    [STATS.farthest_pc ? Math.round(STATS.farthest_pc * 3.26).toLocaleString() + ' ly' : '—', 'Farthest'],
    [STATS.median_distance_pc ? Math.round(STATS.median_distance_pc * 3.26).toLocaleString() + ' ly' : '—', 'Median Distance'],
  ];
  bar.innerHTML = items.map(([v, l]) =>
    `<div class="stat-item"><div class="stat-value">${v}</div><div class="stat-label">${l}</div></div>`
  ).join('');
}

function toggleMethod(method, el) {
  if (activeFilters.has(method)) {
    activeFilters.delete(method);
    el.classList.remove('dimmed');
  } else {
    activeFilters.add(method);
    el.classList.add('dimmed');
  }
  updateVisibility();
}

function updateVisibility() {
  if (activeFilters.size === 0) {
    for (let i = 0; i < PLANETS.length; i++) pointSizes[i] = 3.5;
  } else {
    for (let i = 0; i < PLANETS.length; i++) {
      pointSizes[i] = activeFilters.has(PLANETS[i].discovery_method) ? 0.0 : 2.0;
    }
  }
  pointCloud.geometry.attributes.size.needsUpdate = true;
}

function showInfoCard(data) {
  document.getElementById('card-name').textContent = data.name;
  document.getElementById('card-host').textContent =
    (data.host_star || 'Unknown') + ' · ' + (data.discovery_method || '');

  const rows = [
    ['Distance', data.distance_ly ? data.distance_ly.toLocaleString() + ' ly' : '—'],
    ['RA / Dec', data.ra != null ? data.ra.toFixed(3) + '° / ' + data.dec.toFixed(3) + '°' : '—'],
    ['Discovered', data.discovery_year || '—'],
    ['Radius', data.radius_earth ? data.radius_earth.toFixed(2) + ' R⊕' : '—'],
    ['Mass', data.mass_earth ? data.mass_earth.toFixed(2) + ' M⊕' : '—'],
    ['Period', data.orbital_period_days ? data.orbital_period_days.toFixed(2) + ' d' : '—'],
    ['Temp', data.equilibrium_temp_k ? Math.round(data.equilibrium_temp_k) + ' K' : '—'],
  ];

  document.getElementById('card-body').innerHTML = rows.map(
    ([l, v]) => `<div class="info-row"><span class="info-label">${l}</span><span class="info-value">${v}</span></div>`
  ).join('');
  document.getElementById('info-card').classList.add('show');
}

let time = 0;
function animate() {
  requestAnimationFrame(animate);
  time += 0.016;
  window._updateCam();
  if (pointCloud && pointCloud.material.uniforms) {
    pointCloud.material.uniforms.time.value = time;
  }
  renderer.render(scene, camera);
}

init();
animate();
</script>
</body>
</html>"""
