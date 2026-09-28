import math
import os
from PIL import Image

out_dir = r"Homesteader\Assets\Resources\WeatherFX"
os.makedirs(out_dir, exist_ok=True)

def make_raindrop():
    w, h = 32, 128
    # Start with pure light blue RGB across ALL pixels, alpha = 0
    img = Image.new("RGBA", (w, h), (225, 240, 255, 0))
    for y in range(h):
        progress = y / float(h)
        current_w = 0.8 + 7.2 * (progress ** 1.6)
        alpha_mult = min(1.0, progress * 1.8) * (1.0 - max(0.0, (progress - 0.88) / 0.12))
        for x in range(w):
            dx = abs(x - (w - 1) / 2.0)
            if dx <= current_w:
                t = dx / current_w
                falloff = math.cos(t * math.pi * 0.5) ** 1.2
                a = int(255 * falloff * alpha_mult * 0.85)
                # Keep bright RGB, only vary alpha
                img.putpixel((x, y), (225, 240, 255, max(0, min(255, a))))
            else:
                img.putpixel((x, y), (225, 240, 255, 0))
    p = os.path.join(out_dir, "tex_raindrop.png")
    img.save(p)
    print("Regenerated clean", p)

def make_snowflake():
    w, h = 64, 64
    # Pure white RGB across ALL pixels, alpha = 0
    img = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    cx, cy = (w - 1) / 2.0, (h - 1) / 2.0
    max_radius = 26.0
    for y in range(h):
        for x in range(w):
            dx = x - cx
            dy = y - cy
            dist = math.sqrt(dx*dx + dy*dy)
            if dist <= max_radius:
                angle = math.atan2(dy, dx)
                shimmer = 0.85 + 0.15 * math.cos(angle * 6.0)
                r_norm = dist / max_radius
                falloff = math.cos(r_norm * math.pi * 0.5) ** 1.8
                a = int(255 * falloff * shimmer * 0.95)
                img.putpixel((x, y), (255, 255, 255, max(0, min(255, a))))
            else:
                img.putpixel((x, y), (255, 255, 255, 0))
    p = os.path.join(out_dir, "tex_snowflake.png")
    img.save(p)
    print("Regenerated clean", p)

def make_splash():
    w, h = 64, 64
    img = Image.new("RGBA", (w, h), (225, 240, 255, 0))
    cx, cy = (w - 1) / 2.0, (h - 1) / 2.0
    for y in range(h):
        for x in range(w):
            dx = x - cx
            dy = y - cy
            dist = math.sqrt(dx*dx + dy*dy)
            if 6.0 <= dist <= 28.0:
                ring_center = 17.0
                ring_width = 9.0
                d_ring = abs(dist - ring_center) / ring_width
                if d_ring <= 1.0:
                    falloff = math.cos(d_ring * math.pi * 0.5)
                    a = int(255 * falloff * 0.75)
                    img.putpixel((x, y), (225, 240, 255, max(0, min(255, a))))
                else:
                    img.putpixel((x, y), (225, 240, 255, 0))
            else:
                img.putpixel((x, y), (225, 240, 255, 0))
    p = os.path.join(out_dir, "tex_splash.png")
    img.save(p)
    print("Regenerated clean", p)

make_raindrop()
make_snowflake()
make_splash()
