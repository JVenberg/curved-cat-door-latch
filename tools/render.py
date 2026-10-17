"""Render the README images in images/ with PyVista (VTK).

Run from the repo root:
  uv run --with build123d --with pyvista python tools/render.py
"""

import sys
import tempfile
from math import degrees
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pyvista as pv
from build123d import export_stl

from cat_door_latch import P, make_arm, make_casing, make_door, make_jamb, make_plate

COLORS = {"plate": "#e8892c", "arm": "#2f7fc1", "door": "#d9d9d9", "jamb": "#c9a57a", "casing": "#e3cfa6"}

p = P()
solids = {
    "plate": make_plate(p),
    "arm": make_arm(p),
    "door": make_door(p, degrees(p.slot_s / p.r_in), view_h=110),
    "jamb": make_jamb(p, 110),
    "casing": make_casing(p, 110),
}
meshes = {}
with tempfile.TemporaryDirectory() as tmp:
    for k, s in solids.items():
        export_stl(s, f"{tmp}/{k}.stl", tolerance=0.02, angular_tolerance=0.1)
        meshes[k] = pv.read(f"{tmp}/{k}.stl")

# Trim the reference parts to the area around the latch.
clip = pv.Box(bounds=(560, 800, -120, 260, -60, 60))
for k in ("door", "jamb", "casing"):
    meshes[k] = meshes[k].clip_box(clip.bounds, invert=False)


def render(keys, name, camera, size=(1600, 1000), zoom=1.0):
    pl = pv.Plotter(off_screen=True, window_size=size)
    pl.set_background("white")
    for k in keys:
        pl.add_mesh(meshes[k], color=COLORS[k], smooth_shading=False, specular=0.2, ambient=0.25)
        edges = meshes[k].extract_feature_edges(feature_angle=35, boundary_edges=False, manifold_edges=False)
        pl.add_mesh(edges, color="#333333", line_width=1.2)
    pl.enable_anti_aliasing("ssaa")
    pl.camera_position = camera
    pl.reset_camera()
    pl.camera.zoom(zoom)
    (ROOT / "images").mkdir(exist_ok=True)
    pl.screenshot(ROOT / "images" / name)
    pl.close()


everything = ["door", "jamb", "casing", "plate", "arm"]
up = (0, 0, 1)
render(everything, "assembly.png", [(860, 430, 230), (700, 70, 0), up], zoom=1.3)
render(everything, "plan.png", [(690, 70, 900), (690, 70, 0), (0, 1, 0)], zoom=1.2)
render(["plate", "arm"], "parts_door_side.png", [(450, 150, 120), (705, 90, 0), up], (1600, 900), 1.4)
render(["plate", "arm"], "parts_outside.png", [(950, 0, 120), (705, 90, 0), up], (1600, 900), 1.4)
render(["plate"], "face_plate.png", [(450, -60, 150), (712, 20, 0), up], (1200, 900), 1.2)
render(["arm"], "latch_arm.png", [(950, 40, 120), (705, 110, 0), up], (1600, 900), 1.3)
