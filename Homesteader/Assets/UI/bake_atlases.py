"""bake_atlases.py - emit PNG atlases for the Unity UI Toolkit HUD.

This script runs once (manually or as a build pre-step). Output goes to
Assets/UI/Atlases so Unity's default importer picks them up.

The formats chosen here mirror the procedural look the Python
``runtime/render.py`` produces so the in-game HUD stays visually
consistent.
"""
from PIL import Image, ImageDraw, ImageFont
import os

OUT = os.path.join(os.path.dirname(__file__), "Atlases")
os.makedirs(OUT, exist_ok=True)


def _hex(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def _lerp(c0, c1, t):
    t = max(0.0, min(1.0, float(t)))
    return tuple(int(round(c0[i] + (c1[i] - c0[i]) * t)) for i in range(3))


def _save(img, name):
    path = os.path.join(OUT, name)
    img.save(path, "PNG")
    print("wrote", path)


# ---------------------------------------------------------------------
# 1. Header band: full-canvas-wide 32-px-tall procedural strip. The
#    metallic+noise look is created by per-pixel `body + drift + noise`
#    math, then sampled to 1920x64 so Unity treats it as a repeating
#    background-image with nine-slice potential.
# ---------------------------------------------------------------------

def bake_header_strip(width=1920, height=64):
    body = _hex("#222b3a")
    drift_lo = (1, -2, 0)
    drift_hi = (-1, 2, 0)
    drift_span = (-18, 18)
    diag_max = max(1, width + height)
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    px = img.load()
    for y in range(height):
        for x in range(width):
            t = (x + y) / diag_max
            drift_t = drift_span[0] + (drift_span[1] - drift_span[0]) * t
            r = body[0] + drift_t + drift_lo[0] if t < 0.5 else \
                body[0] + drift_t + drift_hi[0]
            g = body[1] + drift_t + drift_lo[1] if t < 0.5 else \
                body[1] + drift_t + drift_hi[1]
            b = body[2] + drift_t + drift_lo[2] if t < 0.5 else \
                body[2] + drift_t + drift_hi[2]
            px[x, y] = (max(0, min(255, int(r))),
                         max(0, min(255, int(g))),
                         max(0, min(255, int(b))),
                         255)
    # Bottom inner highlight + top inner contour.
    d = ImageDraw.Draw(img)
    d.line([(0, height - 2), (width, height - 2)],
           fill=_hex("#c19a3c"), width=2)
    d.line([(0, 0), (width, 0)],
           fill=_hex("#0a0e15"), width=2)
    _save(img, "header_strip.png")


# ---------------------------------------------------------------------
# 2. Well texture: 320x32 procedural square-corner slab with the 3D
#    border treatment used by the header wells.
# ---------------------------------------------------------------------

def bake_well(width=320, height=32):
    body = _hex("#29344a")
    shadow = _hex("#0a0e15")
    highlight = _hex("#8b9cba")
    img = Image.new("RGBA", (width, height), body + (255,))
    d = ImageDraw.Draw(img)
    d.line([(0, 0), (width, 0)], fill=shadow, width=1)
    d.line([(0, 0), (0, height)], fill=shadow, width=1)
    d.line([(0, height - 1), (width, height - 1)],
           fill=highlight, width=1)
    d.line([(width - 1, 0), (width - 1, height)],
           fill=highlight, width=1)
    _save(img, "well.png")


# ---------------------------------------------------------------------
# 3. Window body + header band atlas. 32 px header on top of dark body.
# ---------------------------------------------------------------------

def _clamped_pixel(channel):
    return max(0, min(255, int(round(channel))))


def bake_window(width=380, height=180):
    body_color = _hex("#1a2230")
    img = Image.new("RGBA", (width, height), body_color + (255,))
    # Header band (32 px tall) shares visual style with header_strip.
    bw = Image.new("RGBA", (width, 32), (0, 0, 0, 0))
    px = bw.load()
    band = _hex("#222b3a")
    hi = _hex("#8b9cba")
    shadow = _hex("#0a0e15")
    diag_max = max(1, width + 32)
    for y in range(32):
        for x in range(width):
            t = (x + y) / diag_max
            drift_t = -18 + 36 * t
            px[x, y] = (_clamped_pixel(band[0] + drift_t),
                        _clamped_pixel(band[1] + drift_t),
                        _clamped_pixel(band[2] + drift_t),
                        255)
    bd = ImageDraw.Draw(bw)
    bd.line([(0, 0), (width, 0)], fill=shadow, width=1)
    bd.line([(0, 31), (width, 31)], fill=hi, width=1)

    img.paste(bw, (0, 0))
    _save(img, "window_frame.png")


def bake_modal(width=800, height=480, header_h=32):
    body_color = _hex("#1a2230")
    img = Image.new("RGBA", (width, height), body_color + (255,))
    # Header strip.
    bw = Image.new("RGBA", (width, header_h), (0, 0, 0, 0))
    px = bw.load()
    band = _hex("#222b3a")
    diag_max = max(1, width + header_h)
    for y in range(header_h):
        for x in range(width):
            t = (x + y) / diag_max
            drift_t = -18 + 36 * t
            px[x, y] = (_clamped_pixel(band[0] + drift_t),
                        _clamped_pixel(band[1] + drift_t),
                        _clamped_pixel(band[2] + drift_t),
                        255)
    bd = ImageDraw.Draw(bw)
    bd.line([(0, 0), (width, 0)], fill=_hex("#0a0e15"), width=1)
    bd.line([(0, header_h - 1), (width, header_h - 1)],
           fill=_hex("#c19a3c"), width=1)
    img.paste(bw, (0, 0))
    # Body content area (lighter fabric background).
    d = ImageDraw.Draw(img)
    d.rectangle(
        [0, header_h, width, height],
        fill=_hex("#29344a") + (255,),
    )
    _save(img, "modal_frame.png")


# ---------------------------------------------------------------------
# 4. Tile atlas for the slider track. Three kinds x two heights.
# ---------------------------------------------------------------------

def bake_slider_track(width=480, height=20, kind="lightslate"):
    cols = {
        "lightslate": _hex("#778899"),
        "slate":      _hex("#708090"),
        "disabled":   _hex("#2a2f38"),
    }
    h = height
    img = Image.new("RGBA", (width, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    body = cols[kind]
    track_h = max(6, h // 2)
    track_y = (h - track_h) // 2
    d.rectangle(
        [0, track_y, width, track_y + track_h],
        fill=body + (255,),
        outline=_hex("#0a0e15") + (255,),
        width=1,
    )
    _save(img, f"slider_track_{kind}.png")


# ---------------------------------------------------------------------
# 5. Button atlas: 4 colors x 4 states, all 28 px tall, 200 px wide.
# ---------------------------------------------------------------------

BUTTON_PAL = {
    "red":    {"unclicked": "#a82f2f", "hover": "#c44f4f",
               "clicked": "#8a2424", "disabled": "#5a1818",
               "label": (255, 230, 230)},
    "green":  {"unclicked": "#3b7a4b", "hover": "#5fa070",
               "clicked": "#2d5b3a", "disabled": "#1f3d28",
               "label": (235, 245, 235)},
    "amber":  {"unclicked": "#c19a3c", "hover": "#d8b25a",
               "clicked": "#a07c2e", "disabled": "#5e4721",
               "label": (20, 24, 32)},
    "slate":  {"unclicked": "#778899", "hover": "#92a3b6",
               "clicked": "#5d6e7f", "disabled": "#3e4754",
               "label": (240, 244, 248)},
}


def bake_buttons(bw=200, bh=56):
    """Atlas each color x state on a single PNG column so Unity
    nine-slice can sample each cell. Atlas is bw x (bh * 4 colors * 4
    states) - one row per (color, state)."""
    rows = []
    for color in ("red", "green", "amber", "slate"):
        for state in ("unclicked", "hover", "clicked", "disabled"):
            rows.append((color, state))
    n = len(rows)
    atlas = Image.new("RGBA", (bw, bh * n), (0, 0, 0, 255))
    d = ImageDraw.Draw(atlas)
    font = _load_font(max(10, int(bh * 0.55)))
    for i, (color, state) in enumerate(rows):
        body = _hex(BUTTON_PAL[color][state])
        y0 = i * bh
        d.rectangle([0, y0, bw, y0 + bh], fill=body)
        # Label color is muted in disabled.
        label = BUTTON_PAL[color]["label"]
        if state == "disabled":
            label = _lerp(label, (90, 90, 90), 0.55)
        bb = font.getbbox("OK")
        tw = bb[2] - bb[0]
        ascent, descent = font.getmetrics()
        cy = y0 + bh // 2
        dy = cy - (ascent - descent) // 2 - bb[1]
        d.text(((bw - tw) // 2 - bb[0], dy), "OK",
               fill=label, font=font)
    _save(atlas, "button_atlas.png")


# ---------------------------------------------------------------------
# 6. Checkbox / radio atlas. Tile 28 px.
# ---------------------------------------------------------------------

def bake_checkboxes(size=28):
    kinds = [
        ("unchecked",          False, "unclicked"),
        ("checked",            True,  "unclicked"),
        ("unchecked_disabled", False, "disabled"),
        ("checked_disabled",   True,  "disabled"),
    ]
    atlas = Image.new("RGBA", (size * len(kinds), size), (0, 0, 0, 255))
    d = ImageDraw.Draw(atlas)
    for i, (name, checked, state) in enumerate(kinds):
        x0 = i * size
        x1 = x0 + size - 1
        if state == "disabled":
            bg, edge = _hex("#2a2f38"), _hex("#1b1f27")
        else:
            bg, edge = _hex("#3e4754"), _hex("#0a0e15")
        d.rectangle([x0, 0, x1, size - 1], fill=bg, outline=edge, width=1)
        if checked and state != "disabled":
            stroke = _hex("#c19a3c")
            pad = max(3, size // 5)
            ax = x0 + pad
            ay = size // 2
            bx = x0 + size // 3
            by_ = size - pad
            cx = x1 - pad
            cy = pad
            d.line([(ax, ay), (bx, by_)], fill=stroke, width=2)
            d.line([(bx, by_), (cx, cy)], fill=stroke, width=2)
    _save(atlas, "checkbox_atlas.png")


def bake_radios(size=28):
    kinds = [
        ("unselected",          False, "unclicked"),
        ("selected",            True,  "unclicked"),
        ("unselected_disabled", False, "disabled"),
        ("selected_disabled",   True,  "disabled"),
    ]
    atlas = Image.new("RGBA", (size * len(kinds), size), (0, 0, 0, 255))
    d = ImageDraw.Draw(atlas)
    for i, (name, selected, state) in enumerate(kinds):
        cx = i * size + size // 2
        cy = size // 2
        if state == "disabled":
            bg, edge = _hex("#2a2f38"), _hex("#1b1f27")
        else:
            bg, edge = _hex("#3e4754"), _hex("#0a0e15")
        r_out = size // 2
        d.ellipse([cx - r_out, cy - r_out, cx + r_out, cy + r_out],
                 fill=bg, outline=edge, width=1)
        if selected and state != "disabled":
            r_in = max(2, size // 3)
            d.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in],
                     fill=_hex("#c19a3c"))
    _save(atlas, "radio_atlas.png")


# ---------------------------------------------------------------------
# 7. Slider knob atlas: 18-px-wide, 28-px-tall. Flat color (no inner
#    notch in the atlas -- Unity applies USS shadow for depth).
# ---------------------------------------------------------------------

def bake_slider_knob(width=18, height=28):
    img = Image.new("RGBA", (width, height), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, width - 1, height - 1],
                fill=_hex("#778899"), outline=_hex("#0a0e15"), width=1)
    # Subtle vertical grip notch.
    notch_w = max(2, width // 6)
    notch_h = max(6, height // 2)
    nx = (width - notch_w) // 2
    ny = (height - notch_h) // 2
    d.rectangle([nx, ny, nx + notch_w - 1, ny + notch_h - 1],
                fill=_hex("#3e4754"))
    _save(img, "slider_knob.png")


# ---------------------------------------------------------------------
# font helper
# ---------------------------------------------------------------------

def _load_font(size):
    candidates = [
        r"C:\Windows\Fonts\segoeuib.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\arial.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


# ---------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------

def main():
    bake_header_strip()
    bake_well()
    bake_window()
    bake_modal()
    bake_slider_track(kind="lightslate")
    bake_slider_track(kind="slate")
    bake_slider_track(kind="disabled")
    bake_buttons()
    bake_checkboxes()
    bake_radios()
    bake_slider_knob()


if __name__ == "__main__":
    main()
