"""
Generates the 16 autotile blend-mask textures used by UGroundTileSubsystem
(Source/Homesteader/Public/World/GroundTileSubsystem.h) to soften the seam
between two adjacent ground tiles of different types.

Bit convention (must match GroundTileSubsystem.cpp):
    bit 0 (1)  = North (image top,    y=0)
    bit 1 (2)  = East  (image right,  x=SIZE-1)
    bit 2 (4)  = South (image bottom, y=SIZE-1)
    bit 3 (8)  = West  (image left,   x=0)

Each mask is a 512x512 grayscale PNG. White (255) = fully show the overlay
("B") ground type's texture; black (0) = fully show this tile's own ("A")
texture. Falloff is smoothstepped and perturbed with soft blotchy noise so
the transition reads as an organic edge rather than a straight ruled line
(this is the actual fix for "no hard line" when tiling ground types).

Output:
    assets/ground/blend_masks/T_GroundBlendMask_<00-15>.png
    Homesteader/Content/Homesteader/Assets/Ground/BlendMasks/T_GroundBlendMask_<00-15>.png
"""
import os
import math
import random
from PIL import Image, ImageFilter

_this_dir = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(_this_dir)  # tools/ sits at the repo root (one level up)

HUD_MASK_DIR = os.path.join(BASE_DIR, "assets", "ground", "blend_masks")
UNREAL_MASK_DIR = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader\Assets\Ground\BlendMasks"

SIZE = 512
INSET = 0.42  # fraction of half-tile the blend reaches in from each active edge
MAX_ALPHA = 235  # never fully 255 so a sliver of the base texture's own detail still shows through


def edge_falloff(dist_from_edge_norm):
    """dist_from_edge_norm: 0 at the edge, 1 at INSET (or beyond). Smoothstep down to 0."""
    t = max(0.0, min(1.0, dist_from_edge_norm / INSET))
    smooth = 1.0 - (t * t * (3 - 2 * t))
    return smooth


def make_mask(bitmask, seed):
    random.seed(seed)
    im = Image.new("L", (SIZE, SIZE), 0)
    px = im.load()

    north = bool(bitmask & 1)
    east = bool(bitmask & 2)
    south = bool(bitmask & 4)
    west = bool(bitmask & 8)

    # Coarse random "wobble" field so the blend edge isn't a straight line -
    # a handful of large soft blotches sampled per-pixel via cheap value noise.
    blotches = [(random.uniform(0, SIZE), random.uniform(0, SIZE), random.uniform(60, 140))
                for _ in range(10)]

    def wobble(x, y):
        # Signed offset in pixels, built from a few overlapping radial bumps.
        v = 0.0
        for bx, by, br in blotches:
            d = math.hypot(x - bx, y - by)
            v += math.cos(d / br * math.pi) * (br * 0.12)
        return v / len(blotches)

    for y in range(SIZE):
        for x in range(SIZE):
            w = wobble(x, y)
            a = 0.0
            if north:
                a = max(a, edge_falloff((y + w) / SIZE))
            if south:
                a = max(a, edge_falloff((SIZE - 1 - y + w) / SIZE))
            if west:
                a = max(a, edge_falloff((x + w) / SIZE))
            if east:
                a = max(a, edge_falloff((SIZE - 1 - x + w) / SIZE))
            px[x, y] = int(a * MAX_ALPHA)

    # Light blur to smooth the blotch-perturbed falloff into a clean gradient.
    im = im.filter(ImageFilter.GaussianBlur(radius=6))
    return im


def main():
    os.makedirs(HUD_MASK_DIR, exist_ok=True)
    os.makedirs(UNREAL_MASK_DIR, exist_ok=True)

    print("=== HOMESTEADER GROUND BLEND MASK GENERATOR ===")
    print("Generating 16 autotile blend masks (512x512 grayscale)...\n")

    for bitmask in range(16):
        im = make_mask(bitmask, seed=1000 + bitmask)
        fname = f"T_GroundBlendMask_{bitmask:02d}.png"
        im.save(os.path.join(HUD_MASK_DIR, fname), "PNG")
        im.save(os.path.join(UNREAL_MASK_DIR, fname), "PNG")
        flags = "".join([
            "N" if bitmask & 1 else "-",
            "E" if bitmask & 2 else "-",
            "S" if bitmask & 4 else "-",
            "W" if bitmask & 8 else "-",
        ])
        print(f"  [OK] {fname}  (edges: {flags})")

    print(f"\nSUCCESS: 16 blend masks generated across HUD and Unreal directories.")


if __name__ == "__main__":
    main()
