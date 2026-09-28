import math
from PIL import Image, ImageDraw

def make_raindrop():
    # 32x128 soft capsule/streak
    w, h = 32, 128
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for y in range(h):
        # taper at top, rounded teardrop at bottom
        progress = y / float(h)
        # width varies from narrow at top to wider near bottom
        current_w = 1.0 + 8.0 * (progress ** 1.5)
        alpha_mult = min(1.0, progress * 1.5) * (1.0 - max(0.0, (progress - 0.85) / 0.15))
        for x in range(w):
            dx = abs(x - w / 2.0)
            if dx <= current_w:
                t = dx / current_w
                # smooth falloff
                falloff = math.cos(t * math.pi * 0.5)
                a = int(255 * falloff * alpha_mult * 0.85)
                # gentle blue-white
                img.putpixel((x, y), (220, 235, 255, max(0, min(255, a))))
    img.save(r"Homesteader\Assets\Resources\WeatherFX\tex_raindrop.png")
    print("Saved tex_raindrop.png")

def make_snowflake():
    # 64x64 soft circular glowing flake with subtle crystallization
    w, h = 64, 64
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    cx, cy = w / 2.0, h / 2.0
    for y in range(h):
        for x in range(w):
            dx = x - cx
            dy = y - cy
            dist = math.sqrt(dx*dx + dy*dy)
            if dist <= 28.0:
                angle = math.atan2(dy, dx)
                # 6-fold radial shimmer
                shimmer = 0.8 + 0.2 * math.cos(angle * 6.0)
                r_norm = dist / 28.0
                falloff = math.cos(r_norm * math.pi * 0.5) ** 1.8
                a = int(255 * falloff * shimmer * 0.95)
                img.putpixel((x, y), (245, 250, 255, max(0, min(255, a))))
    img.save(r"Homesteader\Assets\Resources\WeatherFX\tex_snowflake.png")
    print("Saved tex_snowflake.png")

def make_splash():
    # 64x64 expanding ripple / droplet ring
    w, h = 64, 64
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    cx, cy = w / 2.0, h / 2.0
    for y in range(h):
        for x in range(w):
            dx = x - cx
            dy = y - cy
            dist = math.sqrt(dx*dx + dy*dy)
            # ring at dist around 16 to 26
            if 8.0 <= dist <= 28.0:
                ring_center = 18.0
                ring_width = 8.0
                d_ring = abs(dist - ring_center) / ring_width
                if d_ring <= 1.0:
                    falloff = math.cos(d_ring * math.pi * 0.5)
                    a = int(255 * falloff * 0.75)
                    img.putpixel((x, y), (210, 230, 255, max(0, min(255, a))))
    img.save(r"Homesteader\Assets\Resources\WeatherFX\tex_splash.png")
    print("Saved tex_splash.png")

import os
os.makedirs(r"Homesteader\Assets\Resources\WeatherFX", exist_ok=True)
make_raindrop()
make_snowflake()
make_splash()
