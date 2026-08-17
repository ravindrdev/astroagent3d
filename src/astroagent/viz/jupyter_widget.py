"""Jupyter notebook integration for AstroAgent 3D visualizations."""

from __future__ import annotations

import json
from typing import Any

from IPython.display import HTML, display


def display_orbit_viewer(
    planets: list[dict[str, Any]],
    hz_inner_au: float | None = None,
    hz_outer_au: float | None = None,
    height: int = 550,
    title: str | None = None,
) -> None:
    """Render an interactive 3D orbit viewer inline in a Jupyter notebook."""
    system_name = _detect_system(planets)
    if title is None:
        title = f"{system_name} — 3D Orbital View"

    prepared = _prepare_planets(planets)
    if not prepared:
        display(HTML("<p>No planets with orbital data to visualize.</p>"))
        return

    planets_json = json.dumps(prepared, default=str)
    star_json = json.dumps(_infer_star(planets), default=str)

    max_sma = max(p["semi_major_axis_au"] for p in prepared)
    scale = 40.0 / max_sma if max_sma > 0 else 100.0

    hz_inner_scaled = hz_inner_au * scale if hz_inner_au else 0
    hz_outer_scaled = hz_outer_au * scale if hz_outer_au else 0
    has_hz = "true" if hz_inner_au and hz_outer_au else "false"

    uid = f"astro3d_{id(planets) % 100000}"

    html = f"""
    <div id="{uid}" style="width:100%;height:{height}px;position:relative;
         background:#000;border-radius:10px;overflow:hidden;border:1px solid rgba(255,255,255,0.08)">
      <div style="position:absolute;top:14px;left:18px;z-index:10;color:#fff;font-family:system-ui;pointer-events:none">
        <div style="font-size:16px;font-weight:600;letter-spacing:-0.3px;
             text-shadow:0 0 20px rgba(100,160,255,0.3)">{title}</div>
        <div style="font-size:10px;color:rgba(255,255,255,0.35);margin-top:4px;
             text-transform:uppercase;letter-spacing:1.2px">Interactive 3D Visualization &middot; NASA Data</div>
      </div>
      <div id="{uid}-card" style="position:absolute;top:14px;right:14px;
           background:rgba(8,12,30,0.88);border:1px solid rgba(255,255,255,0.08);
           border-radius:12px;padding:14px 18px;min-width:200px;display:none;
           z-index:10;color:#fff;font-family:system-ui;font-size:13px;
           backdrop-filter:blur(16px);box-shadow:0 8px 24px rgba(0,0,0,0.4)">
      </div>
      <div style="position:absolute;bottom:12px;left:50%;transform:translateX(-50%);
           display:flex;gap:5px;z-index:10">
        <button onclick="{uid}_toggleOrbits()" class="{uid}-btn" id="{uid}-orb">Orbits</button>
        <button onclick="{uid}_toggleHZ()" class="{uid}-btn" id="{uid}-hz">HZ</button>
        <button onclick="{uid}_toggleTrails()" class="{uid}-btn" id="{uid}-trails">Trails</button>
        <button onclick="{uid}_togglePause()" class="{uid}-btn" id="{uid}-pause">Pause</button>
      </div>
    </div>
    <style>
    .{uid}-btn{{padding:5px 13px;border-radius:16px;border:1px solid rgba(255,255,255,0.1);
    background:rgba(255,255,255,0.04);color:rgba(255,255,255,0.7);cursor:pointer;
    font-size:10px;font-weight:500;letter-spacing:0.3px;text-transform:uppercase;
    font-family:system-ui;transition:all .2s}}
    .{uid}-btn:hover{{border-color:rgba(100,160,255,0.4);color:#fff;background:rgba(100,160,255,0.1)}}
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script>
    (function() {{
      const container = document.getElementById('{uid}');
      const P = {planets_json};
      const star = {star_json};
      const SCALE = {scale};
      const hasHZ = {has_hz};
      const hzInner = {hz_inner_scaled};
      const hzOuter = {hz_outer_scaled};
      let paused = false, showOrb = true, showHz = true, showTrails = true;
      const H = {height};

      const scene = new THREE.Scene();
      scene.fog = new THREE.FogExp2(0x000000, 0.004);
      const camera = new THREE.PerspectiveCamera(50, container.clientWidth / H, 0.1, 1000);
      const renderer = new THREE.WebGLRenderer({{ antialias: true }});
      renderer.setSize(container.clientWidth, H);
      renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.2;
      container.appendChild(renderer.domElement);

      scene.add(new THREE.AmbientLight(0x1a1a3a, 0.6));
      scene.add(new THREE.PointLight(new THREE.Color(star.color || '#fff5e0'), 3, 200));

      // Starfield
      const sfGeo = new THREE.BufferGeometry();
      const sfPos = new Float32Array(4000 * 3);
      const sfSizes = new Float32Array(4000);
      for (let i = 0; i < 4000; i++) {{
        const th = Math.random() * Math.PI * 2;
        const ph = Math.acos(2 * Math.random() - 1);
        const r = 200 + Math.random() * 300;
        sfPos[i*3] = r * Math.sin(ph) * Math.cos(th);
        sfPos[i*3+1] = r * Math.sin(ph) * Math.sin(th);
        sfPos[i*3+2] = r * Math.cos(ph);
        sfSizes[i] = 0.4 + Math.random() * 1.5;
      }}
      sfGeo.setAttribute('position', new THREE.Float32BufferAttribute(sfPos, 3));
      scene.add(new THREE.Points(sfGeo, new THREE.PointsMaterial({{
        color: 0xffffff, size: 0.4, transparent: true, opacity: 0.7,
        blending: THREE.AdditiveBlending, depthWrite: false
      }})));

      // Star with glow layers
      const sR = star.display_radius || 2;
      const sColor = new THREE.Color(star.color || '#fff5e0');
      scene.add(new THREE.Mesh(
        new THREE.SphereGeometry(sR, 48, 48),
        new THREE.MeshBasicMaterial({{ color: '#ffffff' }})
      ));
      for (let i = 1; i <= 3; i++) {{
        scene.add(new THREE.Mesh(
          new THREE.SphereGeometry(sR * (1 + i * 0.5), 32, 32),
          new THREE.MeshBasicMaterial({{
            color: sColor, transparent: true, opacity: 0.15 / i,
            blending: THREE.AdditiveBlending, depthWrite: false
          }})
        ));
      }}

      // Habitable zone
      let hzMesh = null;
      if (hasHZ) {{
        const hzGeo = new THREE.RingGeometry(hzInner, hzOuter, 96, 1);
        hzMesh = new THREE.Mesh(hzGeo, new THREE.MeshBasicMaterial({{
          color: 0x22c55e, transparent: true, opacity: 0.1,
          side: THREE.DoubleSide, depthWrite: false, blending: THREE.AdditiveBlending
        }}));
        hzMesh.rotation.x = -Math.PI / 2;
        scene.add(hzMesh);
      }}

      // Planets, orbits, trails
      const pMeshes = [], oLines = [], trailObjs = [];
      P.forEach((p, idx) => {{
        const r = p.semi_major_axis_au * SCALE;
        const ecc = p.eccentricity || 0;
        const b = r * Math.sqrt(1 - ecc * ecc);
        const pColor = new THREE.Color(p.color || '#85B7EB');

        // Orbit
        const curve = new THREE.EllipseCurve(-r * ecc, 0, r, b, 0, Math.PI * 2, false, 0);
        const pts = curve.getPoints(192);
        const oGeo = new THREE.BufferGeometry().setFromPoints(
          pts.map(pt => new THREE.Vector3(pt.x, 0, pt.y))
        );
        const oLine = new THREE.Line(oGeo, new THREE.LineBasicMaterial({{
          color: pColor, transparent: true, opacity: 0.15
        }}));
        scene.add(oLine);
        oLines.push(oLine);

        // Planet
        const pRad = Math.max(0.35, (p.radius_earth || 1) * 0.45);
        const mesh = new THREE.Mesh(
          new THREE.SphereGeometry(pRad, 24, 24),
          new THREE.MeshStandardMaterial({{
            color: pColor, roughness: 0.6, metalness: 0.15,
            emissive: pColor, emissiveIntensity: 0.05
          }})
        );
        mesh.userData = {{ ...p, radius_display: pRad }};
        scene.add(mesh);

        // Atmosphere glow
        const atmosMesh = new THREE.Mesh(
          new THREE.SphereGeometry(pRad * 1.3, 16, 16),
          new THREE.MeshBasicMaterial({{
            color: pColor, transparent: true, opacity: 0.08,
            side: THREE.BackSide, depthWrite: false, blending: THREE.AdditiveBlending
          }})
        );
        mesh.add(atmosMesh);

        pMeshes.push({{
          mesh, radius: r, angle: (Math.PI * 2 / P.length) * idx,
          speed: p.orbital_period_days ? (0.02 / p.orbital_period_days) : 0.01,
          ecc, centerOffset: -r * ecc, pRad
        }});

        // Trail
        const tLen = 60;
        const tGeo = new THREE.BufferGeometry();
        const tPos = new Float32Array(tLen * 3);
        const tAlpha = new Float32Array(tLen);
        for (let t = 0; t < tLen; t++) tAlpha[t] = 1.0 - t / tLen;
        tGeo.setAttribute('position', new THREE.Float32BufferAttribute(tPos, 3));
        tGeo.setAttribute('alpha', new THREE.Float32BufferAttribute(tAlpha, 1));
        const trail = new THREE.Points(tGeo, new THREE.PointsMaterial({{
          color: pColor, size: 2, transparent: true, opacity: 0.4,
          blending: THREE.AdditiveBlending, depthWrite: false
        }}));
        scene.add(trail);
        trailObjs.push({{ points: trail, positions: tPos, len: tLen }});
      }});

      // Camera controls
      let dragging = false, px = 0, py = 0;
      let theta = Math.PI / 4, phi = Math.PI / 5, dist = 60;
      const cv = renderer.domElement;
      cv.style.cursor = 'grab';
      cv.addEventListener('mousedown', e => {{ dragging = true; px = e.clientX; py = e.clientY; cv.style.cursor = 'grabbing'; }});
      cv.addEventListener('mousemove', e => {{
        if (!dragging) return;
        theta -= (e.clientX - px) * 0.005;
        phi = Math.max(0.05, Math.min(1.45, phi - (e.clientY - py) * 0.005));
        px = e.clientX; py = e.clientY; updCam();
      }});
      window.addEventListener('mouseup', () => {{ dragging = false; cv.style.cursor = 'grab'; }});
      cv.addEventListener('wheel', e => {{
        e.preventDefault();
        dist = Math.max(12, Math.min(150, dist + e.deltaY * 0.06));
        updCam();
      }}, {{ passive: false }});
      function updCam() {{
        camera.position.set(
          dist*Math.sin(theta)*Math.cos(phi),
          dist*Math.sin(phi),
          dist*Math.cos(theta)*Math.cos(phi)
        );
        camera.lookAt(0, 0, 0);
      }}
      updCam();

      // Click to select planet
      const raycaster = new THREE.Raycaster();
      const mouse = new THREE.Vector2();
      cv.addEventListener('click', e => {{
        const rect = cv.getBoundingClientRect();
        mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
        raycaster.setFromCamera(mouse, camera);
        const hits = raycaster.intersectObjects(pMeshes.map(p => p.mesh));
        const card = document.getElementById('{uid}-card');
        if (hits.length > 0) {{
          const d = hits[0].object.userData;
          let hzBadge = '';
          if (hasHZ) {{
            const sma = d.semi_major_axis_au;
            const hzInAU = hzInner / SCALE, hzOutAU = hzOuter / SCALE;
            if (sma >= hzInAU && sma <= hzOutAU) hzBadge = '<div style="margin-top:8px;padding:2px 8px;border-radius:10px;display:inline-block;font-size:10px;background:rgba(34,197,94,0.15);color:#4ade80;border:1px solid rgba(34,197,94,0.3)">In Habitable Zone</div>';
            else if (sma < hzInAU) hzBadge = '<div style="margin-top:8px;padding:2px 8px;border-radius:10px;display:inline-block;font-size:10px;background:rgba(239,68,68,0.15);color:#f87171;border:1px solid rgba(239,68,68,0.3)">Too Hot</div>';
            else hzBadge = '<div style="margin-top:8px;padding:2px 8px;border-radius:10px;display:inline-block;font-size:10px;background:rgba(96,165,250,0.15);color:#93c5fd;border:1px solid rgba(96,165,250,0.3)">Too Cold</div>';
          }}
          card.innerHTML = '<div style="font-weight:600;font-size:15px;margin-bottom:3px">' + d.name + '</div>' +
            '<div style="font-size:10px;color:rgba(255,255,255,0.35);text-transform:uppercase;letter-spacing:1px;margin-bottom:10px">' + (d.discovery_method || 'Transit') + '</div>' +
            [['Mass', d.mass_earth ? d.mass_earth.toFixed(3)+' M\\u2295' : '\\u2014'],
             ['Radius', d.radius_earth ? d.radius_earth.toFixed(3)+' R\\u2295' : '\\u2014'],
             ['Period', d.orbital_period_days ? d.orbital_period_days.toFixed(3)+' d' : '\\u2014'],
             ['Orbit', d.semi_major_axis_au.toFixed(5)+' AU'],
             ['Temp', d.equilibrium_temp_k ? Math.round(d.equilibrium_temp_k)+' K' : '\\u2014']
            ].map(([l,v]) => '<div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.04)"><span style="color:rgba(255,255,255,0.4)">'+l+'</span><span style="color:#a5d6ff;font-family:monospace;font-weight:500">'+v+'</span></div>').join('') + hzBadge;
          card.style.display = 'block';
        }} else card.style.display = 'none';
      }});

      // Controls
      window['{uid}_togglePause'] = function() {{ paused = !paused; document.getElementById('{uid}-pause').textContent = paused ? 'Play' : 'Pause'; }};
      window['{uid}_toggleOrbits'] = function() {{ showOrb = !showOrb; oLines.forEach(l => l.visible = showOrb); }};
      window['{uid}_toggleHZ'] = function() {{ showHz = !showHz; if (hzMesh) hzMesh.visible = showHz; }};
      window['{uid}_toggleTrails'] = function() {{ showTrails = !showTrails; trailObjs.forEach(t => t.points.visible = showTrails); }};

      function anim() {{
        requestAnimationFrame(anim);
        if (!paused) {{
          pMeshes.forEach((p, i) => {{
            p.angle += p.speed;
            const a = p.radius;
            const bAxis = a * Math.sqrt(1 - p.ecc * p.ecc);
            const x = Math.cos(p.angle) * a + p.centerOffset;
            const z = Math.sin(p.angle) * bAxis;
            p.mesh.position.set(x, 0, z);

            // Update trail
            const tr = trailObjs[i];
            const tp = tr.positions;
            for (let t = tr.len - 1; t > 0; t--) {{
              tp[t*3] = tp[(t-1)*3];
              tp[t*3+1] = tp[(t-1)*3+1];
              tp[t*3+2] = tp[(t-1)*3+2];
            }}
            tp[0] = x; tp[1] = 0; tp[2] = z;
            tr.points.geometry.attributes.position.needsUpdate = true;
          }});
        }}
        renderer.render(scene, camera);
      }}
      anim();
    }})();
    </script>
    """
    display(HTML(html))


def display_light_curve(
    data_points: list[dict[str, float]],
    title: str = "Light Curve",
    height: int = 300,
) -> None:
    """Render a light curve plot inline in a Jupyter notebook."""
    if not data_points:
        display(HTML("<p>No light curve data to display.</p>"))
        return

    times = [dp["time_bjd"] for dp in data_points]
    fluxes = [dp["flux"] for dp in data_points]

    points_json = json.dumps([{"x": t, "y": f} for t, f in zip(times, fluxes, strict=False)])
    t_min, t_max = min(times), max(times)
    f_min, f_max = min(fluxes), max(fluxes)
    f_range = f_max - f_min if f_max != f_min else 0.001
    f_pad = f_range * 0.1

    uid = f"lc_{id(data_points) % 100000}"

    html = f"""
    <div style="border:1px solid rgba(128,128,128,0.15);border-radius:10px;overflow:hidden;
         background:#0a0e1a;padding:16px">
      <canvas id="{uid}" width="700" height="{height}" style="width:100%;background:#0a0e1a"></canvas>
    </div>
    <script>
    (function() {{
      const c = document.getElementById('{uid}');
      const ctx = c.getContext('2d');
      const pts = {points_json};
      const W = c.width, H = c.height;
      const pad = {{ t: 35, r: 20, b: 45, l: 75 }};
      const pW = W - pad.l - pad.r, pH = H - pad.t - pad.b;
      const tMin = {t_min}, tMax = {t_max};
      const fMin = {f_min - f_pad}, fMax = {f_max + f_pad};

      function tx(v) {{ return pad.l + ((v - tMin) / (tMax - tMin)) * pW; }}
      function ty(v) {{ return pad.t + pH - ((v - fMin) / (fMax - fMin)) * pH; }}

      // Grid
      ctx.strokeStyle = 'rgba(255,255,255,0.06)';
      ctx.lineWidth = 0.5;
      ctx.fillStyle = 'rgba(255,255,255,0.35)';
      ctx.font = '11px system-ui';
      for (let i = 0; i <= 4; i++) {{
        const f = fMin + (fMax - fMin) * i / 4;
        ctx.beginPath(); ctx.moveTo(pad.l, ty(f)); ctx.lineTo(W-pad.r, ty(f)); ctx.stroke();
        ctx.textAlign = 'right';
        ctx.fillText(f.toFixed(4), pad.l - 8, ty(f) + 4);
      }}

      // Axis labels
      ctx.fillStyle = 'rgba(255,255,255,0.4)';
      ctx.font = '11px system-ui';
      ctx.textAlign = 'center';
      ctx.fillText('Time (BJD)', W/2, H - 6);
      ctx.save();
      ctx.translate(14, H/2);
      ctx.rotate(-Math.PI/2);
      ctx.fillText('Relative Flux', 0, 0);
      ctx.restore();

      // Data points
      ctx.fillStyle = 'rgba(74, 144, 217, 0.35)';
      pts.forEach(p => {{
        ctx.beginPath();
        ctx.arc(tx(p.x), ty(p.y), 2, 0, Math.PI*2);
        ctx.fill();
      }});

      // Line
      ctx.strokeStyle = '#4a90d9';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      const sorted = [...pts].sort((a,b) => a.x - b.x);
      sorted.forEach((p, i) => {{ i === 0 ? ctx.moveTo(tx(p.x), ty(p.y)) : ctx.lineTo(tx(p.x), ty(p.y)); }});
      ctx.stroke();

      // Title
      ctx.fillStyle = '#ffffff';
      ctx.font = '600 14px system-ui';
      ctx.textAlign = 'left';
      ctx.fillText('{title}', pad.l, 22);
    }})();
    </script>
    """
    display(HTML(html))


def _detect_system(planets: list[dict[str, Any]]) -> str:
    if planets:
        host = planets[0].get("host_star", "")
        if host:
            return str(host)
    return "Unknown System"


def _prepare_planets(planets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for p in planets:
        sma = p.get("semi_major_axis_au")
        if sma is None:
            continue
        result.append(
            {
                "name": p.get("name", "Unknown"),
                "semi_major_axis_au": float(sma),
                "eccentricity": float(p.get("eccentricity") or 0),
                "orbital_period_days": p.get("orbital_period_days"),
                "mass_earth": p.get("mass_earth"),
                "radius_earth": p.get("radius_earth"),
                "equilibrium_temp_k": p.get("equilibrium_temp_k"),
                "discovery_method": p.get("discovery_method"),
                "color": _planet_color(p.get("equilibrium_temp_k"), p.get("mass_earth")),
            }
        )
    return result


def _planet_color(temp: float | None, mass: float | None) -> str:
    if mass and mass > 50:
        return "#c4956a"
    if temp is None:
        return "#85B7EB"
    if temp > 1000:
        return "#e24b4a"
    if temp > 400:
        return "#d85a30"
    if temp > 200:
        return "#4a90d9"
    if temp > 100:
        return "#7ec8e3"
    return "#9fd5d1"


def _infer_star(planets: list[dict[str, Any]]) -> dict[str, Any]:
    if not planets:
        return {"temp_k": 5778, "color": "#fff5e0", "display_radius": 2.0}
    temp = planets[0].get("star_temp_k", 5778)
    radius = planets[0].get("star_radius_solar", 1.0)
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
    return {"temp_k": temp, "color": color, "display_radius": max(1.0, min(4.0, radius * 2.0))}
