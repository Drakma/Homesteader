"""Procedural asset generator - container / cube / cabin shapes.

INVARIANTS (canonical ruleset, see docs/ITEM_ICON_STYLE_GUIDE.md):
 1. Camera fixed: yaw and pitch rotate the OBJECT, never the camera basis.
 2. Per-tri explicit outward normals.
 3. Z-buffer init at +inf; smaller depth wins so front triangles occlude.
 4. Identical spec -> byte-identical PNG.
 5. Output passes tools/validate_item_icon.py.
 6. NEAREST downsample only (no Lanczos).
"""
import argparse
import hashlib
import json
import math
import os
import sys

import numpy as np
from PIL import Image


class Mesh:
    def __init__(self, name):
        self.name = name
        self.verts = []
        self.tris = []
        self.normals = []
        self.materials = []

    def add_vert(self, x, y, z):
        self.verts.append((float(x), float(y), float(z)))
        return len(self.verts) - 1

    def add_tri(self, a, b, c, mat="wood"):
        self.tris.append((a, b, c))
        self.materials.append(mat)

    def add_quad(self, a, b, c, d, mat="wood"):
        self.add_tri(a, b, c, mat)
        self.add_tri(a, c, d, mat)

    def ground_align(self):
        z_min = min(v[2] for v in self.verts)
        if z_min < 0:
            self.verts = [(x, y, z - z_min) for (x, y, z) in self.verts]

    def compute_normals(self):
        self.normals = []
        for (a, b, c) in self.tris:
            p0 = np.array(self.verts[a])
            p1 = np.array(self.verts[b])
            p2 = np.array(self.verts[c])
            n = np.cross(p1 - p0, p2 - p0)
            ln = np.linalg.norm(n)
            self.normals.append(n / ln if ln > 1e-12 else np.array([0.0, 0.0, 1.0]))


# ===========================================================================
# Builds
# ===========================================================================
def build_container(spec):
    """Round bucket: discrete staves + hoop bands. Object-local coords."""
    s = spec["shape"]
    r_top = float(s["top_radius_cm"])
    r_bot = float(s["bottom_radius_cm"])
    h = float(s["height_cm"])
    n = int(s.get("stave_count", 14))
    chamfer_top_cm = float(s.get("chamfer_top_cm", 0.0))
    m = Mesh(spec["name"])
    for i in range(n):
        a0 = i / n * 2.0 * math.pi
        a1 = (i + 1) / n * 2.0 * math.pi
        center_a = (a0 + a1) * 0.5
        outward = (math.cos(center_a), math.sin(center_a), 0.0)
        ca0, sa0 = math.cos(a0), math.sin(a0)
        ca1, sa1 = math.cos(a1), math.sin(a1)
        i_tl = m.add_vert(ca0 * r_top, sa0 * r_top, h)
        i_tr = m.add_vert(ca1 * r_top, sa1 * r_top, h)
        i_br = m.add_vert(ca1 * r_bot, sa1 * r_bot, 0.0)
        i_bl = m.add_vert(ca0 * r_bot, sa0 * r_bot, 0.0)
        m.add_tri(i_tl, i_tr, i_br, "wood")
        m.normals.append(np.array(outward))
        m.add_tri(i_tl, i_br, i_bl, "wood")
        m.normals.append(np.array(outward))
        if chamfer_top_cm > 0:
            r_ch_top = r_top + 0.20
            r_ch_bot = r_top * (1.0 - chamfer_top_cm / h) + 0.20
            z_top = h
            z_bot = h - chamfer_top_cm
            i_ct_l = m.add_vert(ca0 * r_ch_top, sa0 * r_ch_top, z_top)
            i_ct_r = m.add_vert(ca1 * r_ch_top, sa1 * r_ch_top, z_top)
            i_cb_r = m.add_vert(ca1 * r_ch_bot, sa1 * r_ch_bot, z_bot)
            i_cb_l = m.add_vert(ca0 * r_ch_bot, sa0 * r_ch_bot, z_bot)
            m.add_tri(i_ct_l, i_ct_r, i_cb_r, "wood")
            m.normals.append(np.array(outward))
            m.add_tri(i_ct_l, i_cb_r, i_cb_l, "wood")
            m.normals.append(np.array(outward))
    for hoop in spec.get("hoops", []):
        y_cm = float(hoop["y_cm"])
        t_cm = float(hoop["thickness_cm"])
        t_frac = max(0.0, min(1.0, y_cm / h))
        r_side = r_top + (r_bot - r_top) * t_frac
        r_outer = r_side + t_cm * 0.5
        r_inner = r_side - t_cm * 0.5
        z_top = y_cm + t_cm * 0.5
        z_bot = y_cm - t_cm * 0.5
        for i in range(n):
            a0 = i / n * 2.0 * math.pi
            a1 = (i + 1) / n * 2.0 * math.pi
            center_a = (a0 + a1) * 0.5
            outward = (math.cos(center_a), math.sin(center_a), 0.0)
            ca0, sa0 = math.cos(a0), math.sin(a0)
            ca1, sa1 = math.cos(a1), math.sin(a1)
            i1 = m.add_vert(ca0 * r_outer, sa0 * r_outer, z_top)
            i2 = m.add_vert(ca1 * r_outer, sa1 * r_outer, z_top)
            i3 = m.add_vert(ca1 * r_outer, sa1 * r_outer, z_bot)
            i4 = m.add_vert(ca0 * r_outer, sa0 * r_outer, z_bot)
            m.add_tri(i1, i2, i3, "hoop")
            m.normals.append(np.array(outward))
            m.add_tri(i1, i3, i4, "hoop")
            m.normals.append(np.array(outward))
            j1 = m.add_vert(ca0 * r_inner, sa0 * r_inner, z_top)
            j2 = m.add_vert(ca1 * r_inner, sa1 * r_inner, z_top)
            j3 = m.add_vert(ca1 * r_outer, sa1 * r_outer, z_top)
            j4 = m.add_vert(ca0 * r_outer, sa0 * r_outer, z_top)
            m.add_tri(j1, j2, j3, "hoop_top")
            m.normals.append(np.array([0.0, 0.0, 1.0]))
            m.add_tri(j1, j3, j4, "hoop_top")
            m.normals.append(np.array([0.0, 0.0, 1.0]))
    m.ground_align()
    m.compute_normals()
    return m


def build_cube(spec):
    """Square box, optional plank seams per face, optional open top."""
    s = spec["shape"]
    size = float(s["size_cm"])
    half = size / 2.0
    top_open = bool(s.get("top_open", False))
    planks_per_face = int(s.get("planks_per_face", 3))
    rim_thickness_cm = float(s.get("rim_thickness_cm", 0.0))
    rim_outset_cm = 0.0
    m = Mesh(spec["name"])

    def add_face(axis, sign):
        normal_vec = (sign if axis == "x" else 0.0,
                      sign if axis == "y" else 0.0,
                      sign if axis == "z" else 0.0)
        if planks_per_face < 2:
            if axis == "x":
                pts = [(half * sign, -half, -half), (half * sign, half, -half),
                       (half * sign, half, half), (half * sign, -half, half)]
            elif axis == "y":
                pts = [(-half, half * sign, -half), (half, half * sign, -half),
                       (half, half * sign, half), (-half, half * sign, half)]
            else:
                pts = [(-half, -half, half * sign), (half, -half, half * sign),
                       (half, half, half * sign), (-half, half, half * sign)]
            mat = "face_{}{}".format(axis, "+" if sign > 0 else "-")
            m.add_tri(m.add_vert(*pts[0]), m.add_vert(*pts[1]),
                      m.add_vert(*pts[2]), mat)
            m.normals.append(np.array(normal_vec))
            m.add_tri(m.add_vert(*pts[0]), m.add_vert(*pts[2]),
                      m.add_vert(*pts[3]), mat)
            m.normals.append(np.array(normal_vec))
            return
        n_strips = planks_per_face
        if axis == "x":
            for k in range(n_strips):
                lo = -half + (k / float(n_strips)) * (2 * half)
                hi = -half + ((k + 1) / float(n_strips)) * (2 * half)
                pts = [(half * sign, lo, -half), (half * sign, hi, -half),
                       (half * sign, hi, half), (half * sign, lo, half)]
                mat = "plank_a" if k % 2 == 0 else "plank_b"
                m.add_tri(m.add_vert(*pts[0]), m.add_vert(*pts[1]),
                          m.add_vert(*pts[2]), mat)
                m.normals.append(np.array(normal_vec))
                m.add_tri(m.add_vert(*pts[0]), m.add_vert(*pts[2]),
                          m.add_vert(*pts[3]), mat)
                m.normals.append(np.array(normal_vec))
        elif axis == "y":
            for k in range(n_strips):
                lo = -half + (k / float(n_strips)) * (2 * half)
                hi = -half + ((k + 1) / float(n_strips)) * (2 * half)
                pts = [(lo, half * sign, -half), (hi, half * sign, -half),
                       (hi, half * sign, half), (lo, half * sign, half)]
                mat = "plank_a" if k % 2 == 0 else "plank_b"
                m.add_tri(m.add_vert(*pts[0]), m.add_vert(*pts[1]),
                          m.add_vert(*pts[2]), mat)
                m.normals.append(np.array(normal_vec))
                m.add_tri(m.add_vert(*pts[0]), m.add_vert(*pts[2]),
                          m.add_vert(*pts[3]), mat)
                m.normals.append(np.array(normal_vec))
        else:
            for k in range(n_strips):
                lo = -half + (k / float(n_strips)) * (2 * half)
                hi = -half + ((k + 1) / float(n_strips)) * (2 * half)
                pts = [(lo, -half, half * sign), (hi, -half, half * sign),
                       (hi, half, half * sign), (lo, half, half * sign)]
                mat = "plank_a" if k % 2 == 0 else "plank_b"
                m.add_tri(m.add_vert(*pts[0]), m.add_vert(*pts[1]),
                          m.add_vert(*pts[2]), mat)
                m.normals.append(np.array(normal_vec))
                m.add_tri(m.add_vert(*pts[0]), m.add_vert(*pts[2]),
                          m.add_vert(*pts[3]), mat)
                m.normals.append(np.array(normal_vec))

    add_face("x", +1)
    add_face("x", -1)
    add_face("y", +1)
    add_face("y", -1)
    if not top_open:
        add_face("z", +1)
    add_face("z", -1)
    if rim_thickness_cm > 0:
        t = rim_thickness_cm
        z_top = half
        z_bot = half - t
        o = rim_outset_cm
        out = o
        m.add_tri(m.add_vert(half + out, -half, z_bot),
                  m.add_vert(half + out,  half, z_bot),
                  m.add_vert(half + out,  half, z_top),
                  "wood")
        m.normals.append(np.array([1.0, 0.0, 0.0]))
        m.add_tri(m.add_vert(half + out, -half, z_bot),
                  m.add_vert(half + out,  half, z_top),
                  m.add_vert(half + out, -half, z_top),
                  "wood")
        m.normals.append(np.array([1.0, 0.0, 0.0]))
        m.add_tri(m.add_vert(-half - out,  half, z_bot),
                  m.add_vert(-half - out, -half, z_bot),
                  m.add_vert(-half - out, -half, z_top),
                  "wood")
        m.normals.append(np.array([-1.0, 0.0, 0.0]))
        m.add_tri(m.add_vert(-half - out,  half, z_bot),
                  m.add_vert(-half - out, -half, z_top),
                  m.add_vert(-half - out,  half, z_top),
                  "wood")
        m.normals.append(np.array([-1.0, 0.0, 0.0]))
        m.add_tri(m.add_vert( half, half + out, z_bot),
                  m.add_vert(-half, half + out, z_bot),
                  m.add_vert(-half, half + out, z_top),
                  "wood")
        m.normals.append(np.array([0.0, 1.0, 0.0]))
        m.add_tri(m.add_vert( half, half + out, z_bot),
                  m.add_vert(-half, half + out, z_top),
                  m.add_vert( half, half + out, z_top),
                  "wood")
        m.normals.append(np.array([0.0, 1.0, 0.0]))
        m.add_tri(m.add_vert(-half, -half - out, z_bot),
                  m.add_vert( half, -half - out, z_bot),
                  m.add_vert( half, -half - out, z_top),
                  "wood")
        m.normals.append(np.array([0.0, -1.0, 0.0]))
        m.add_tri(m.add_vert(-half, -half - out, z_bot),
                  m.add_vert( half, -half - out, z_top),
                  m.add_vert(-half, -half - out, z_top),
                  "wood")
        m.normals.append(np.array([0.0, -1.0, 0.0]))
    m.ground_align()
    m.compute_normals()
    return m


def build_cabin(spec):
    """Small log cabin: cube body with log planks + pyramid roof +
    rectangular stone chimney + thin slab porch. No trees, no ground.
    """
    s = spec["shape"]
    body_w = float(s.get("body_w_cm", 26.0))
    body_d = float(s.get("body_d_cm", 22.0))
    body_h = float(s.get("body_h_cm", 18.0))
    porch_d = float(s.get("porch_d_cm", 6.0))
    roof_h = float(s.get("roof_h_cm", 8.0))
    chimney_w = float(s.get("chimney_w_cm", 3.0))
    chimney_h = float(s.get("chimney_h_cm", 8.0))
    planks = int(s.get("planks_per_face", 4))
    m = Mesh(spec["name"])

    bw2 = body_w / 2.0
    bd2 = body_d / 2.0
    bh = body_h
    porch_z_top = 1.5
    porch_y = bd2 + porch_d / 2.0

    # Slab porch (slab only; no posts, no clutter).
    m.add_tri(m.add_vert(-bw2 - 1.0, porch_y - porch_d / 2.0, porch_z_top),
              m.add_vert( bw2 + 1.0, porch_y - porch_d / 2.0, porch_z_top),
              m.add_vert( bw2 + 1.0, porch_y + porch_d / 2.0, porch_z_top),
              "wood_inside")
    m.normals.append(np.array([0.0, 1.0, 0.0]))
    m.add_tri(m.add_vert(-bw2 - 1.0, porch_y - porch_d / 2.0, porch_z_top),
              m.add_vert( bw2 + 1.0, porch_y + porch_d / 2.0, porch_z_top),
              m.add_vert(-bw2 - 1.0, porch_y + porch_d / 2.0, porch_z_top),
              "wood_inside")
    m.normals.append(np.array([0.0, 1.0, 0.0]))

    def plank_face(axis, sign, normal_vec):
        if axis == "x":
            xs = bw2 * sign
            for k in range(planks):
                lo = -bd2 + (k / planks) * body_d
                hi = -bd2 + ((k + 1) / planks) * body_d
                pts = [(xs, lo, 0.0), (xs, hi, 0.0),
                       (xs, hi, bh), (xs, lo, bh)]
                mat = "log_a" if (k + (1 if sign < 0 else 0)) % 2 == 0 else "log_b"
                m.add_tri(m.add_vert(*pts[0]), m.add_vert(*pts[1]),
                          m.add_vert(*pts[2]), mat)
                m.normals.append(np.array(normal_vec))
                m.add_tri(m.add_vert(*pts[0]), m.add_vert(*pts[2]),
                          m.add_vert(*pts[3]), mat)
                m.normals.append(np.array(normal_vec))
        elif axis == "y":
            ys = bd2 * sign
            for k in range(planks):
                lo = -bw2 + (k / planks) * body_w
                hi = -bw2 + ((k + 1) / planks) * body_w
                pts = [(lo, ys, 0.0), (hi, ys, 0.0),
                       (hi, ys, bh), (lo, ys, bh)]
                mat = "log_a" if (k + (1 if sign < 0 else 0)) % 2 == 0 else "log_b"
                m.add_tri(m.add_vert(*pts[0]), m.add_vert(*pts[1]),
                          m.add_vert(*pts[2]), mat)
                m.normals.append(np.array(normal_vec))
                m.add_tri(m.add_vert(*pts[0]), m.add_vert(*pts[2]),
                          m.add_vert(*pts[3]), mat)
                m.normals.append(np.array(normal_vec))
        else:
            pts = [(-bw2, -bd2, 0.0), ( bw2, -bd2, 0.0),
                   ( bw2,  bd2, 0.0), (-bw2,  bd2, 0.0)]
            m.add_tri(m.add_vert(*pts[0]), m.add_vert(*pts[1]),
                      m.add_vert(*pts[2]), "wood_inside")
            m.normals.append(np.array([0.0, 0.0, -1.0]))
            m.add_tri(m.add_vert(*pts[0]), m.add_vert(*pts[2]),
                      m.add_vert(*pts[3]), "wood_inside")
            m.normals.append(np.array([0.0, 0.0, -1.0]))

    plank_face("x", +1, (1.0, 0.0, 0.0))
    plank_face("x", -1, (-1.0, 0.0, 0.0))
    plank_face("y", +1, (0.0, 1.0, 0.0))
    plank_face("y", -1, (0.0, -1.0, 0.0))
    plank_face("z", -1, None)

    # Pyramid roof - 4 triangular faces meeting at apex.
    apex = m.add_vert(0.0, 0.0, bh + roof_h)
    cnt = 4
    rim = []
    for i in range(cnt):
        a = i / cnt * 2.0 * math.pi + math.pi / 4.0
        rim.append(m.add_vert(math.cos(a) * bw2 * 1.15,
                              math.sin(a) * bd2 * 1.15, bh))
    for i in range(cnt):
        j = (i + 1) % cnt
        pa = np.array(m.verts[rim[i]])
        pb = np.array(m.verts[rim[j]])
        pc = np.array(m.verts[apex])
        nn = np.cross(pb - pa, pc - pa)
        ln = np.linalg.norm(nn)
        nn = nn / ln if ln > 1e-9 else np.array([0.0, 0.0, 1.0])
        m.add_tri(rim[i], rim[j], apex, "roof")
        m.normals.append(nn)

    # Stone chimney (square column, no smoke, no decoration).
    cx_off = bw2 - chimney_w - 1.0
    cy_off = bd2 - chimney_w - 1.0
    cz_bot = bh + 2.0
    cz_top = cz_bot + chimney_h
    ch_verts = [
        m.add_vert(cx_off - chimney_w / 2.0, cy_off - chimney_w / 2.0, cz_bot),
        m.add_vert(cx_off + chimney_w / 2.0, cy_off - chimney_w / 2.0, cz_bot),
        m.add_vert(cx_off + chimney_w / 2.0, cy_off + chimney_w / 2.0, cz_bot),
        m.add_vert(cx_off - chimney_w / 2.0, cy_off + chimney_w / 2.0, cz_bot),
        m.add_vert(cx_off - chimney_w / 2.0, cy_off - chimney_w / 2.0, cz_top),
        m.add_vert(cx_off + chimney_w / 2.0, cy_off - chimney_w / 2.0, cz_top),
        m.add_vert(cx_off + chimney_w / 2.0, cy_off + chimney_w / 2.0, cz_top),
        m.add_vert(cx_off - chimney_w / 2.0, cy_off + chimney_w / 2.0, cz_top),
    ]
    b0, b1, b2, b3, t0, t1, t2, t3 = ch_verts
    m.add_tri(b0, b1, t1, "stone"); m.normals.append(np.array([-1.0, 0.0, 0.0]))
    m.add_tri(b0, t1, t0, "stone"); m.normals.append(np.array([-1.0, 0.0, 0.0]))
    m.add_tri(b1, b2, t2, "stone"); m.normals.append(np.array([0.0, 1.0, 0.0]))
    m.add_tri(b1, t2, t1, "stone"); m.normals.append(np.array([0.0, 1.0, 0.0]))
    m.add_tri(b2, b3, t3, "stone"); m.normals.append(np.array([1.0, 0.0, 0.0]))
    m.add_tri(b2, t3, t2, "stone"); m.normals.append(np.array([1.0, 0.0, 0.0]))
    m.add_tri(b3, b0, t0, "stone"); m.normals.append(np.array([0.0, -1.0, 0.0]))
    m.add_tri(b3, t0, t3, "stone"); m.normals.append(np.array([0.0, -1.0, 0.0]))
    m.add_tri(t0, t1, t2, "stone_top"); m.normals.append(np.array([0.0, 0.0, 1.0]))
    m.add_tri(t0, t2, t3, "stone_top"); m.normals.append(np.array([0.0, 0.0, 1.0]))

    m.ground_align()
    m.compute_normals()
    return m


# ===========================================================================
# Colour helpers
# ===========================================================================
def _hex_to_rgb(h, default):
    h = h.lstrip("#")
    if len(h) != 6:
        return default
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# ===========================================================================
# Object rotation (camera is fixed).
# ===========================================================================
def object_rotation(yaw_deg=45.0, pitch_deg=30.0):
    yaw = math.radians(yaw_deg)
    pitch = math.radians(pitch_deg)
    # CW from above = -right-hand-rule about +Z.
    R_yaw = np.array([
        [math.cos(-yaw), -math.sin(-yaw), 0.0],
        [math.sin(-yaw),  math.cos(-yaw), 0.0],
        [0.0,             0.0,             1.0],
    ])
    # +X rotation tips +Y toward +Z (object's top tips toward viewer).
    R_pitch = np.array([
        [1.0, 0.0,             0.0],
        [0.0,  math.cos(pitch),  math.sin(pitch)],
        [0.0, -math.sin(pitch),  math.cos(pitch)],
    ])
    return R_pitch @ R_yaw


# ===========================================================================
# Renderer
# ===========================================================================
def render(mesh, colors, size=128, yaw_deg=45.0, pitch_deg=30.0, ss=4,
           anchor=(0.0, 0.0, 0.0)):
    """Camera-fixed orthographic render. Object rotates by (yaw,pitch)."""
    if len(mesh.tris) == 0:
        raise RuntimeError("mesh has no triangles")
    verts = np.array(mesh.verts, dtype=float)
    verts = verts - np.array(anchor, dtype=float)
    R_obj = object_rotation(yaw_deg, pitch_deg)
    world = verts @ R_obj.T
    W = H = size * ss
    xy = world[:, :2]
    denom = np.abs(xy).max() + 1e-9
    scale = (W * 0.45) / denom
    px = xy[:, 0] * scale + W / 2.0
    py = -xy[:, 1] * scale + H / 2.0

    img = np.zeros((H, W, 4), dtype=np.uint8)
    img[:, :, 3] = 0
    zbuf = np.full((H, W), 1e18, dtype=np.float64)
    key = np.array([0.55, -0.50, 0.80], dtype=float)
    key /= np.linalg.norm(key)
    fill = np.array([-0.45, 0.45, 0.40], dtype=float)
    fill /= np.linalg.norm(fill)
    base_rgb = {
        "wood":        np.array(colors.get("wood", (176, 137, 104)), dtype=float),
        "wood_inside": np.array(colors.get("wood", (176, 137, 104)), dtype=float) * 0.35,
        "hoop":        np.array(colors.get("hoop", (203, 213, 225)), dtype=float),
        "hoop_top":    np.array(colors.get("hoop", (203, 213, 225)), dtype=float) * 1.10,
        "stone":       np.array(colors.get("stone", (160, 152, 138)), dtype=float),
        "stone_top":   np.array(colors.get("stone", (160, 152, 138)), dtype=float) * 1.10,
        "roof":        np.array(colors.get("roof", (90, 60, 35)), dtype=float),
        "log_a":       np.array(colors.get("wood", (176, 137, 104)), dtype=float),
        "log_b":       np.array(colors.get("wood_dark", (130, 95, 65)), dtype=float),
        "plank_a":     np.array(colors.get("wood", (176, 137, 104)), dtype=float),
        "plank_b":     np.array(colors.get("wood_dark", (130, 95, 65)), dtype=float),
        "face_x+":     np.array(colors.get("wood", (176, 137, 104)), dtype=float),
        "face_x-":     np.array(colors.get("wood", (176, 137, 104)), dtype=float),
        "face_y+":     np.array(colors.get("wood", (176, 137, 104)), dtype=float),
        "face_y-":     np.array(colors.get("wood", (176, 137, 104)), dtype=float),
        "face_z+":     np.array(colors.get("wood", (176, 137, 104)), dtype=float),
        "face_z-":     np.array(colors.get("wood", (176, 137, 104)), dtype=float),
    }

    world_norms = []
    for n in mesh.normals:
        world_norms.append(R_obj.T @ np.array(n))

    for idx, (a, b, c) in enumerate(mesh.tris):
        xs = (px[a], px[b], px[c])
        ys = (py[a], py[b], py[c])
        zs = (world[a, 2], world[b, 2], world[c, 2])
        x0 = max(int(min(xs)), 0)
        x1 = min(int(max(xs)) + 1, W - 1)
        y0 = max(int(min(ys)), 0)
        y1 = min(int(max(ys)) + 1, H - 1)
        if x1 < x0 or y1 < y0:
            continue
        denom_a = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(denom_a) < 1e-12:
            continue
        n = world_norms[idx]
        lam_key = max(0.0, float(np.dot(n, key)))
        lam_fill = max(0.0, float(np.dot(n, fill)))
        mat = mesh.materials[idx] if idx < len(mesh.materials) else "wood"
        base = base_rgb.get(mat, base_rgb["wood"])
        col = np.clip(base * (0.40 + lam_key + 0.30 * lam_fill), 0, 255).astype(np.uint8)

        gx, gy = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        w0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / denom_a
        w1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / denom_a
        w2 = 1.0 - w0 - w1
        inside = (w0 >= -1e-9) & (w1 >= -1e-9) & (w2 >= -1e-9)
        if not inside.any():
            continue
        d = w0 * zs[0] + w1 * zs[1] + w2 * zs[2]
        zb_sub = zbuf[y0:y1 + 1, x0:x1 + 1]
        win = inside & (d < zb_sub)
        if not win.any():
            continue
        zb_sub[win] = d[win]
        sub_rgb = img[y0:y1 + 1, x0:x1 + 1, :3]
        sub_a = img[y0:y1 + 1, x0:x1 + 1, 3]
        sub_rgb[win] = col
        sub_a[win] = 255

    out = Image.fromarray(img, "RGBA")
    if ss > 1:
        out = out.resize((size, size), Image.NEAREST)
    return out


# ===========================================================================
# Icon standardization
# ===========================================================================
CANVAS = 128
MAX_DIM = 104


def make_icon(src_png):
    """Crop to alpha bbox, fill the safe zone (NEAREST so longer side =
    MAX_DIM), centre on 128x128 canvas, force alpha=0 on perimeter.
    """
    im = src_png.convert("RGBA")
    bbox = im.split()[3].getbbox()
    if not bbox:
        raise RuntimeError("render produced empty image")
    cropped = im.crop(bbox)
    cw, ch = cropped.size
    longer = max(cw, ch)
    if longer > 0:
        scale = float(MAX_DIM) / float(longer)
        nw = max(1, int(round(cw * scale)))
        nh = max(1, int(round(ch * scale)))
        resized = cropped.resize((nw, nh), Image.NEAREST)
    else:
        resized = cropped
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    canvas.paste(resized, ((CANVAS - resized.width) // 2,
                           (CANVAS - resized.height) // 2), resized)
    px = canvas.load()
    w, h = canvas.size
    for x in range(w):
        px[x, 0] = (0, 0, 0, 0)
        px[x, h - 1] = (0, 0, 0, 0)
    for y in range(h):
        px[0, y] = (0, 0, 0, 0)
        px[w - 1, y] = (0, 0, 0, 0)
    return canvas


def write_obj(mesh, obj_path, mtl_path, materials):
    full_mats = dict(materials)
    with open(obj_path, "w", encoding="utf-8") as f:
        f.write("# Procedural: %s\n" % mesh.name)
        f.write("mtllib %s\n" % os.path.basename(mtl_path))
        f.write("o %s\n" % mesh.name)
        for (x, y, z) in mesh.verts:
            f.write("v %.4f %.4f %.4f\n" % (x * 0.01, y * 0.01, z * 0.01))
        for idx, (a, b, c) in enumerate(mesh.tris):
            mat = mesh.materials[idx] if idx < len(mesh.materials) else "wood"
            if mat not in full_mats:
                mat = "wood"
            f.write("usemtl %s\n" % mat)
            f.write("f %d %d %d\n" % (a + 1, b + 1, c + 1))
    with open(mtl_path, "w", encoding="utf-8") as f:
        for mat_name, rgb in full_mats.items():
            r, g, b = rgb
            f.write("newmtl %s\n" % mat_name)
            f.write("Kd %.4f %.4f %.4f\n" % (r / 255.0, g / 255.0, b / 255.0))


def _spec_hash(spec):
    canonical = json.dumps(spec, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def generate(spec, out_dir):
    name = spec["name"]
    category = spec.get("category", "container")
    if category == "container":
        mesh = build_container(spec)
    elif category == "cube":
        mesh = build_cube(spec)
    elif category == "cabin":
        mesh = build_cabin(spec)
    else:
        raise ValueError("unsupported category: %s" % category)
    wood = _hex_to_rgb(spec.get("wood_color", "#b08968"), (176, 137, 104))
    stone = _hex_to_rgb(spec.get("stone_color", "#a0988a"), (160, 152, 138))
    roof = _hex_to_rgb(spec.get("roof_color", "#5a3c23"), (90, 60, 35))
    hoop = _hex_to_rgb("#cbd5e1", (203, 213, 225))
    materials = {"wood": wood, "hoop": hoop, "stone": stone, "roof": roof}
    colors = materials
    r = spec.get("render", {})
    target = int(r.get("size", 128))
    src = render(mesh, colors,
                 size=target,
                 yaw_deg=float(r.get("yaw_deg", 30)),
                 pitch_deg=float(r.get("pitch_deg", 28)),
                 ss=int(r.get("ss", 1)))
    icon = make_icon(src)
    os.makedirs(out_dir, exist_ok=True)
    icon_path = os.path.join(out_dir, name + "_icon.png")
    src_path = os.path.join(out_dir, name + "_render.png")
    obj_path = os.path.join(out_dir, name + ".obj")
    mtl_path = os.path.join(out_dir, name + ".mtl")
    icon.save(icon_path, "PNG")
    src.save(src_path, "PNG")
    write_obj(mesh, obj_path, mtl_path, materials)
    return {
        "name": name,
        "category": category,
        "spec_hash": _spec_hash(spec),
        "verts": len(mesh.verts),
        "tris": len(mesh.tris),
        "icon_path": icon_path,
        "render_path": src_path,
        "obj": obj_path,
        "mtl": mtl_path,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    with open(args.spec, "r", encoding="utf-8") as f:
        spec = json.load(f)
    info = generate(spec, args.out)
    print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
