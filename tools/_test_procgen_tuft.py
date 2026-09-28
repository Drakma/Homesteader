"""Best-case procedural grass tuft: many thin blades + alpha-cut cards, rendered.

This is the BEST-CASE TEST RIG. The question it answers is "how good can a
pure-Python procedural tuft actually look at a game-viable triangle count?",
not "does a minimal version work". The previous minimal attempt (7 wide ribbons,
49 tris) proved the pipeline; this one aims at the asset.

How real foliage is actually built, and what this reproduces:
  1. MANY THIN BLADE RIBBONS - 20+ narrow strips, each a few segments, tapering
     to a point. Thin is the whole game: a 0.5-0.9 cm blade at 22 cm tall reads
     as a flat plane, where a 0.1-0.24 cm one reads as a blade.
  2. ROOT SPREAD - bases scattered across the tuft footprint. Blades sharing one
     origin make a starburst, not a clump.
  3. OUTWARD FAN - the lean CURVES: nearly upright at the base, opening up
     toward the tip. Straight blades in any direction read as a spiky ball.
  4. HEIGHT VARIANCE - a ragged silhouette, with outer blades shorter so the
     clump has a dome. A uniform top is the giveaway of a generated asset.
  5. ALPHA-CUT CROSS CARDS - vertical quads at intervals of 90 degrees. This is
     the trick that makes cheap foliage look dense: a few cards read as far more
     mass than the geometry contains, because a texture can hold hundreds of
     painted blades for 2 triangles each. Foliage without them looks sparse.

Run:
    python tools/_test_procgen_tuft.py
"""
import math
import os

import numpy as np
from PIL import Image

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_procgen_test")
OUT_DIR = os.path.normpath(OUT_DIR)

# Authored in CENTIMETRES to match every other asset in this project, scaled to
# metres (1 unit = 1 m) on export. Not a second convention - the existing one.
CM = 0.01


class Mesh:
    """Minimal indexed mesh: positions, per-triangle colour, computed normals."""

    def __init__(self, name):
        self.name = name
        self.verts = []
        self.tris = []      # (i0, i1, i2, rgb)
        self.normals = []

    def add_vert(self, x, y, z):
        self.verts.append((float(x), float(y), float(z)))
        return len(self.verts) - 1

    def add_tri(self, a, b, c, rgb):
        self.tris.append((a, b, c, rgb))

    def add_quad(self, a, b, c, d, rgb):
        self.add_tri(a, b, c, rgb)
        self.add_tri(a, c, d, rgb)

    def ground_align(self):
        """Drop the mesh so its lowest point sits on z=0.

        Every world asset needs this. A pivot that is not at the ground makes the
        thing float or sink, and fixing it per-asset in Unity is exactly the
        manual step procedural generation exists to remove.
        """
        min_z = min(v[2] for v in self.verts)
        self.verts = [(x, y, z - min_z) for (x, y, z) in self.verts]

    def compute_normals(self):
        self.normals = []
        for (a, b, c, _rgb) in self.tris:
            p0 = np.array(self.verts[a])
            p1 = np.array(self.verts[b])
            p2 = np.array(self.verts[c])
            n = np.cross(p1 - p0, p2 - p0)
            ln = np.linalg.norm(n)
            self.normals.append(n / ln if ln > 1e-12 else np.array([0.0, 0.0, 1.0]))

    def bounds(self):
        a = np.array(self.verts)
        return a.min(axis=0), a.max(axis=0)

    def stats(self):
        mn, mx = self.bounds()
        return {
            "verts": len(self.verts),
            "tris": len(self.tris),
            "width_cm": max(mx[0] - mn[0], mx[1] - mn[1]),
            "height_cm": mx[2] - mn[2],
        }


def _blade(m, rng, base_x, base_y, angle, height, width, segs=3):
    """One curved, tapering grass blade standing up from (base_x, base_y).

    The lean is split into two terms on purpose: a small LINEAR component so the
    blade leaves vertical immediately, plus a QUADRATIC one that dominates near
    the tip. That produces the arc real grass has - straight up at the base,
    bending over at the top - rather than a straight diagonal.
    """
    ca, sa = math.cos(angle), math.sin(angle)
    px, py = -sa, ca                      # ribbon width direction, in-plane

    # Curvature and final lean are per-blade so no two blades follow one arc.
    curve = rng.uniform(0.25, 0.75)
    tip_lean = rng.uniform(0.30, 0.75) * height

    prev_l = prev_r = None
    for s in range(segs + 1):
        t = s / float(segs)
        reach = tip_lean * (t * t) + curve * height * 0.12 * t
        z = height * t
        cx = base_x + ca * reach
        cy = base_y + sa * reach
        # Taper to a point but keep a sliver at the tip: a zero-width top
        # collapses to a line and vanishes under rasterisation.
        w = width * (1.0 - 0.88 * t) + 0.02
        l = m.add_vert(cx - px * w, cy - py * w, z)
        r = m.add_vert(cx + px * w, cy + py * w, z)
        if prev_l is not None:
            # Vertical gradient (dark at the root, lighter at the tip) gives
            # depth without a texture. Alternating per-segment shades banded
            # badly on wide blades; a per-blade gradient does not.
            k = 0.42 + 0.58 * t
            rgb = (0.23 * k + 0.05, 0.52 * k + 0.07, 0.16 * k + 0.04)
            m.add_quad(prev_l, prev_r, r, l, rgb)
        prev_l, prev_r = l, r


def _cross_cards(m, radius, height, cards=3, rgb=(0.26, 0.54, 0.20)):
    """Alpha-cut cross cards: vertical quads meeting at the vertical axis.

    In the shipped asset these carry a leaf texture. Here they are tinted only,
    but they are the single highest-value trick in foliage authoring: 2 triangles
    each, and they fill the interior of the clump so it reads as dense mass
    rather than a few visible sticks.
    """
    for i in range(cards):
        # 90-degree steps: a quad is double-sided, so 4 cards cover all angles
        # (2 would leave visible bare gaps once the player walks around it).
        a = (i / float(cards)) * math.pi
        ca, sa = math.cos(a), math.sin(a)
        h = height
        v0 = m.add_vert(-ca * radius, -sa * radius, 0.0)
        v1 = m.add_vert(ca * radius, sa * radius, 0.0)
        v2 = m.add_vert(ca * radius, sa * radius, h)
        v3 = m.add_vert(-ca * radius, -sa * radius, h)
        m.add_quad(v0, v1, v2, v3, rgb)


def build_grass_tuft(num_blades=22, seed=7, cards=3):
    """A dense, ragged tuft of thin curved blades plus alpha-cut cross cards."""
    m = Mesh("clutter_grass_tuft")
    rng = np.random.default_rng(seed)

    footprint = 3.4          # cm radius the clump emerges from
    for i in range(num_blades):
        # Golden-angle distribution: even coverage without the visible pinwheel
        # a fixed i/N sweep produces once there are more than about 8 blades.
        angle = i * 2.39996 + rng.uniform(-0.18, 0.18)
        # Bias roots toward the centre so the clump has a dense core, then vary
        # height so the silhouette is ragged rather than a flat top.
        root_r = footprint * math.sqrt(rng.uniform(0.0, 1.0))
        root_a = rng.uniform(0.0, 2 * math.pi)
        bx = math.cos(root_a) * root_r
        by = math.sin(root_a) * root_r
        # Outer blades shorter: reproduces the dome a real tuft has.
        falloff = 1.0 - 0.35 * (root_r / footprint)
        height = rng.uniform(11.0, 21.0) * falloff
        width = rng.uniform(0.11, 0.24)
        _blade(m, rng, bx, by, angle, height, width)

    _cross_cards(m, footprint * 1.25, 16.0, cards=cards)

    m.ground_align()
    m.compute_normals()
    return m


def render(mesh, path, size=640, yaw_deg=30.0, pitch_deg=14.0, ss=2,
           bg=(18, 22, 30)):
    """Flat-shaded software render with supersampling.

    Viewer only - no texturing, no shadows. It reveals silhouette and facet
    structure, which is what a low-poly asset is judged on.

    Rotation is yaw about the Z (UP) axis FIRST, then pitch tilting the camera
    down. An earlier version applied pitch before yaw, which tips the vertical
    axis over and renders upright grass lying on its side - a bug that looked
    exactly like a broken mesh.
    """
    verts = np.array(mesh.verts, dtype=float)
    verts = verts - verts.mean(axis=0)

    yaw = math.radians(yaw_deg)
    pitch = math.radians(pitch_deg)
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)
    rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])     # turn about up
    rx = np.array([[1, 0, 0], [0, cp, sp], [0, -sp, cp]])     # tilt camera down
    v = verts @ (rx @ rz).T

    W = size * ss
    xy = v[:, :2]
    scale = (W * 0.42) / (np.abs(xy).max() + 1e-9)
    px = xy[:, 0] * scale + W / 2
    py = -xy[:, 1] * scale + W / 2

    img = np.zeros((W, W, 4), dtype=np.uint8)
    img[:, :, 0], img[:, :, 1], img[:, :, 2] = bg
    img[:, :, 3] = 255
    zbuf = np.full((W, W), -1e18)

    light = np.array([0.40, 0.34, 0.85])
    light = light / np.linalg.norm(light)

    for idx, (a, b, c, rgb) in enumerate(mesh.tris):
        xs = [px[a], px[b], px[c]]
        ys = [py[a], py[b], py[c]]
        zs = [v[a, 2], v[b, 2], v[c, 2]]

        x0, x1 = max(int(min(xs)), 0), min(int(max(xs)) + 1, W - 1)
        y0, y1 = max(int(min(ys)), 0), min(int(max(ys)) + 1, W - 1)
        if x1 < x0 or y1 < y0:
            continue

        ax, ay = xs[0], ys[0]
        bx, by = xs[1], ys[1]
        cx_, cy_ = xs[2], ys[2]
        denom = (by - cy_) * (ax - cx_) + (cx_ - bx) * (ay - cy_)
        if abs(denom) < 1e-12:
            continue

        n = mesh.normals[idx]
        # Two-sided: a ribbon has no back face, and a blade seen from behind
        # should still be lit rather than going black.
        lam = abs(float(np.dot(n, light)))
        shade = 0.55 + 0.45 * lam
        col = np.array([min(255, int(rgb[0] * shade * 255)),
                        min(255, int(rgb[1] * shade * 255)),
                        min(255, int(rgb[2] * shade * 255))], dtype=np.uint8)

        gx, gy = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        w0 = ((by - cy_) * (gx - cx_) + (cx_ - bx) * (gy - cy_)) / denom
        w1 = ((cy_ - ay) * (gx - cx_) + (ax - cx_) * (gy - cy_)) / denom
        w2 = 1.0 - w0 - w1
        inside = (w0 >= -1e-9) & (w1 >= -1e-9) & (w2 >= -1e-9)
        if not inside.any():
            continue
        z = w0 * zs[0] + w1 * zs[1] + w2 * zs[2]
        sub = zbuf[y0:y1 + 1, x0:x1 + 1]
        win = inside & (z > sub)
        if not win.any():
            continue
        sub[win] = z[win]
        # Write through a view of the SAME window: `img[a:b][win] = col` would
        # assign to a temporary copy and silently discard the result, and the
        # window is RGBA while `col` is RGB, so the channel extent has to match
        # explicitly rather than relying on broadcasting.
        img_win = img[y0:y1 + 1, x0:x1 + 1, :3]
        img_win[win] = col

    out = Image.fromarray(img, "RGBA")
    if ss > 1:
        out = out.resize((size, size), Image.LANCZOS)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    out.save(path)
    return path


def contact_sheet(mesh, path, size=420, views=(0, 45, 90, 135)):
    """The same tuft at four yaw angles, side by side.

    A single view can flatter or hide a mesh; four views make a geometry problem
    (blades facing the wrong way, a collapsed silhouette) impossible to miss.
    """
    tiles = []
    tmp = os.path.join(OUT_DIR, "_tmp_view.png")
    for yaw in views:
        render(mesh, tmp, size=size, yaw_deg=yaw, pitch_deg=14.0)
        tiles.append(Image.open(tmp).convert("RGBA"))
    sheet = Image.new("RGBA", (size * len(tiles), size), (18, 22, 30, 255))
    for i, t in enumerate(tiles):
        sheet.paste(t, (i * size, 0))
    sheet.save(path)
    try:
        os.remove(tmp)
    except OSError:
        pass
    return path


def write_obj(mesh, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Procedural grass tuft\n")
        f.write("mtllib clutter_grass_tuft.mtl\n")
        f.write("o clutter_grass_tuft\n")
        for (x, y, z) in mesh.verts:
            f.write("v %.4f %.4f %.4f\n" % (x * CM, y * CM, z * CM))
        f.write("usemtl M_Foliage_Grass\n")
        for (a, b, c, _rgb) in mesh.tris:
            f.write("f %d %d %d\n" % (a + 1, b + 1, c + 1))
    return path


def main():
    print("=== BEST-CASE procedural grass tuft ===")
    for blades, cards in ((16, 2), (22, 3), (30, 4)):
        mesh = build_grass_tuft(num_blades=blades, cards=cards)
        s = mesh.stats()
        print("blades=%-3d cards=%d -> %4d tris, %4d verts, %.1f cm wide, %.1f cm tall"
              % (blades, cards, s["tris"], s["verts"], s["width_cm"], s["height_cm"]))

    mesh = build_grass_tuft(num_blades=22, cards=3)
    s = mesh.stats()
    print()
    print("--- chosen variant ---")
    for k in ("verts", "tris", "width_cm", "height_cm"):
        print("%-11s: %s" % (k, round(s[k], 2)))

    os.makedirs(OUT_DIR, exist_ok=True)
    obj = write_obj(mesh, os.path.join(OUT_DIR, "clutter_grass_tuft.obj"))
    print("wrote: %s (%.1f KB)" % (obj, os.path.getsize(obj) / 1024))

    png = render(mesh, os.path.join(OUT_DIR, "clutter_grass_tuft.png"),
                 yaw_deg=30, pitch_deg=14)
    print("wrote: %s" % png)

    sheet = contact_sheet(mesh, os.path.join(OUT_DIR, "clutter_grass_tuft_views.png"))
    print("wrote: %s" % sheet)


if __name__ == "__main__":
    main()
