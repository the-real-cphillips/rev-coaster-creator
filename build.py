#!/usr/bin/env python3
"""
build.py — Reverie Coaster Club
Assembles index.html from the template and raw assets.

Usage:
    python build.py                   # builds to dist/index.html
    python build.py --watch           # rebuilds on file change (requires watchdog)
    python build.py --serve           # builds and serves locally on http://localhost:8080

Assets read from:
    assets/rbco-logo.jpg              — RBco. circular logo
    assets/Rev-Coaster-Club_v11.stl   — coaster STL (used to render coaster PNG)

Template read from:
    src/index.template.html

Output written to:
    dist/index.html                   — final self-contained HTML (ready to deploy)
    dist/coaster_preview.png          — standalone coaster top-down render
"""

import base64
import os
import sys
import struct
import argparse
import shutil
import http.server
import threading

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

# ── Paths ────────────────────────────────────────────────────
ROOT     = os.path.dirname(os.path.abspath(__file__))
ASSETS   = os.path.join(ROOT, 'assets')
SRC      = os.path.join(ROOT, 'src')
DIST     = os.path.join(ROOT, 'dist')
TEMPLATE = os.path.join(SRC,    'index.template.html')
STL_PATH = os.path.join(ASSETS, 'Rev-Coaster-Club_v11.stl')
LOGO_PATH= os.path.join(ASSETS, 'rbco-logo.jpg')
OUT_HTML = os.path.join(DIST,   'index.html')
OUT_PNG  = os.path.join(DIST,   'coaster_preview.png')


# ── STL → PNG renderer ──────────────────────────────────────
def render_coaster_png(stl_path: str, size: int = 512) -> Image.Image:
    """Render the coaster STL top-down as a PNG with engraving depth shading."""
    with open(stl_path, 'rb') as f:
        data = f.read()

    tri_count = struct.unpack('<I', data[80:84])[0]
    verts   = np.zeros((tri_count, 3, 3), dtype=np.float32)
    normals = np.zeros((tri_count, 3),    dtype=np.float32)
    offset  = 84
    for i in range(tri_count):
        chunk = data[offset:offset+50]
        normals[i] = struct.unpack('<fff', chunk[0:12])
        for v in range(3):
            verts[i, v] = struct.unpack('<fff', chunk[12+v*12:12+v*12+12])
        offset += 50

    all_v  = verts.reshape(-1, 3)
    mn, mx = all_v.min(0), all_v.max(0)
    center = (mn + mx) / 2
    xySpan = max(mx[0]-mn[0], mx[1]-mn[1])
    verts_c = (verts - center) / xySpan  # normalise

    S = size
    depth_buf  = np.full((S, S), -np.inf, dtype=np.float32)
    normal_buf = np.zeros((S, S, 3), dtype=np.float32)

    for i in range(tri_count):
        n = normals[i]
        if n[2] < 0.05:
            continue
        v  = verts_c[i]
        sx = (v[:, 0] + 0.5) * (S - 1)
        sy = (0.5 - v[:, 1]) * (S - 1)
        depths = v[:, 2]

        x0, x1 = int(max(0, sx.min()-1)), int(min(S-1, sx.max()+1))
        y0, y1 = int(max(0, sy.min()-1)), int(min(S-1, sy.max()+1))
        if x1 <= x0 or y1 <= y0:
            continue

        px2d, py2d = np.meshgrid(np.arange(x0, x1+1), np.arange(y0, y1+1))
        d = (sy[1]-sy[2])*(sx[0]-sx[2]) + (sx[2]-sx[1])*(sy[0]-sy[2])
        if abs(d) < 0.5:
            continue

        w0 = ((sy[1]-sy[2])*(px2d-sx[2]) + (sx[2]-sx[1])*(py2d-sy[2])) / d
        w1 = ((sy[2]-sy[0])*(px2d-sx[2]) + (sx[0]-sx[2])*(py2d-sy[2])) / d
        w2 = 1.0 - w0 - w1
        inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        if not inside.any():
            continue

        depth = w0*depths[0] + w1*depths[1] + w2*depths[2]
        fy, fx = py2d[inside], px2d[inside]
        closer = depth[inside] > depth_buf[fy, fx]
        depth_buf[fy[closer], fx[closer]] = depth[inside][closer]
        normal_buf[fy[closer], fx[closer]] = n

    hit    = depth_buf > -np.inf
    d_vals = depth_buf[hit]
    depth_norm = np.zeros((S, S), dtype=np.float32)
    rng = d_vals.max() - d_vals.min()
    if rng > 0:
        depth_norm[hit] = (depth_buf[hit] - d_vals.min()) / rng

    light   = np.array([0.15, 0.25, 1.0]); light /= np.linalg.norm(light)
    diffuse = np.clip((normal_buf * light).sum(-1), 0, 1)
    base    = np.array([200, 168, 122], dtype=np.float32)
    dark    = np.array([138, 108,  72], dtype=np.float32)
    color   = base * depth_norm[..., None] + dark * (1 - depth_norm[..., None])
    color   = np.clip(color * (0.6 + 0.4*diffuse)[..., None], 0, 255)

    rgb = np.zeros((S, S, 4), dtype=np.uint8)
    rgb[hit, :3] = color[hit].astype(np.uint8)
    rgb[hit,  3] = 255

    img  = Image.fromarray(rgb, 'RGBA')
    mask = Image.new('L', (S, S), 0)
    ImageDraw.Draw(mask).ellipse([4, 4, S-4, S-4], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(2))
    img.putalpha(mask)
    return img


# ── Build ────────────────────────────────────────────────────
def build():
    os.makedirs(DIST, exist_ok=True)

    print("▸ Rendering coaster PNG...")
    coaster_img = render_coaster_png(STL_PATH)
    coaster_img.save(OUT_PNG)
    print(f"  Saved {OUT_PNG}")

    print("▸ Encoding assets...")
    with open(LOGO_PATH, 'rb') as f:
        logo_b64 = base64.b64encode(f.read()).decode()
    with open(OUT_PNG, 'rb') as f:
        png_b64  = base64.b64encode(f.read()).decode()

    print("▸ Assembling index.html...")
    with open(TEMPLATE, 'r') as f:
        template = f.read()

    html = template
    html = html.replace('{{LOGO_B64}}', logo_b64)
    html = html.replace('{{PNG_B64}}',  png_b64)

    with open(OUT_HTML, 'w') as f:
        f.write(html)

    size_kb = len(html) // 1024
    print(f"  Saved {OUT_HTML} ({size_kb} KB)")
    print("✓ Build complete")


# ── CLI ──────────────────────────────────────────────────────
def serve():
    os.chdir(DIST)
    port = 8080
    handler = http.server.SimpleHTTPRequestHandler
    server  = http.server.HTTPServer(('', port), handler)
    print(f"▸ Serving at http://localhost:{port} (Ctrl+C to stop)")
    server.serve_forever()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build Reverie Coaster Club site')
    parser.add_argument('--serve', action='store_true', help='Serve dist/ after building')
    parser.add_argument('--watch', action='store_true', help='Watch for changes and rebuild')
    args = parser.parse_args()

    build()

    if args.serve:
        serve()

    if args.watch:
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler

            class RebuildHandler(FileSystemEventHandler):
                def on_modified(self, event):
                    if not event.is_directory and not event.src_path.startswith(DIST):
                        print(f"\n▸ Change detected: {event.src_path}")
                        build()

            observer = Observer()
            observer.schedule(RebuildHandler(), ROOT, recursive=True)
            observer.start()
            print("▸ Watching for changes (Ctrl+C to stop)...")
            import time
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                observer.stop()
            observer.join()
        except ImportError:
            print("watchdog not installed. Run: pip install watchdog")
