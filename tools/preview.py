"""Render out/preview.png: plan and 3D views of the parts installed with the door held at the slot.

Run from the repo root:
  uv run --with build123d --with trimesh --with matplotlib --with scipy --with networkx python tools/preview.py
"""

import sys
import tempfile
from math import degrees
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import matplotlib
import numpy as np
import trimesh
from build123d import export_stl
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from cat_door_latch import P, make_arm, make_casing, make_door, make_jamb, make_plate

matplotlib.use("Agg")
import matplotlib.pyplot as plt

p = P()
objs = {
    "plate": (make_plate(p), "tab:orange"),
    "arm": (make_arm(p), "tab:blue"),
    "door": (make_door(p, degrees(p.slot_s / p.r_in), view_h=120), "lightgray"),
    "jamb": (make_jamb(p, 120), "burlywood"),
    "casing": (make_casing(p, 120), "wheat"),
}
meshes = {}
with tempfile.TemporaryDirectory() as tmp:
    for k, (o, c) in objs.items():
        export_stl(o, f"{tmp}/{k}.stl", tolerance=0.05)
        meshes[k] = (trimesh.load(f"{tmp}/{k}.stl"), c)


def draw(ax, keys, el, az, lim):
    # One collection for all parts, otherwise matplotlib depth-sorts whole parts and draws them wrong.
    tris, fcs = [], []
    for k in keys:
        m, c = meshes[k]
        light = np.clip(m.face_normals @ np.array([0.4, -0.3, 0.85]), 0.25, 1)
        rgb = np.array(matplotlib.colors.to_rgb(c))
        tris.append(m.triangles)
        fcs.append(np.clip(rgb[None] * light[:, None], 0, 1))
    ax.add_collection3d(Poly3DCollection(np.concatenate(tris), facecolors=np.concatenate(fcs), edgecolor="none"))
    (x0, x1), (y0, y1), (z0, z1) = lim
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_zlim(z0, z1)
    ax.set_box_aspect((x1 - x0, y1 - y0, z1 - z0))
    ax.view_init(el, az)
    ax.set_axis_off()


everything = ["door", "jamb", "casing", "plate", "arm"]
fig = plt.figure(figsize=(18, 12))
views = [
    (everything, 90, -90, ((560, 780), (-110, 220), (-60, 60)), "plan, door held at slot"),
    (everything, 25, -130, ((560, 780), (-110, 220), (-60, 60)), "assembly"),
    (["plate", "arm"], 15, 170, ((650, 750), (-60, 220), (-40, 40)), "parts, door side"),
    (["plate", "arm"], 15, -10, ((650, 750), (-60, 220), (-40, 40)), "parts, outside"),
]
for i, (keys, el, az, lim, title) in enumerate(views, 1):
    ax = fig.add_subplot(2, 2, i, projection="3d")
    draw(ax, keys, el, az, lim)
    ax.set_title(title)
plt.tight_layout()
plt.savefig(ROOT / "out" / "preview.png", dpi=70)
