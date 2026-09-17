"""
Homesteader - Seamless PBR Ground Texture Generator (v3 - Noise & Compacted Aggregate)
Generates 20 high-fidelity seamless PBR texture sets (BaseColor, Normal, ORM) for Unreal Engine 5 & Web HUD:
- Flat cohesive base colors with multi-octave procedural noise for natural, organic tactile texture.
- NO repeating geometric triangles, giant diagonal seams, or artificial scatter shapes.
- Compacted Gravel: thousands of tightly packed, small interlocking stone pebbles with realistic 3D dome relief and compacted fines.
- Tangent-space Direct-X Normal maps (+Y inverted for Unreal Engine) and packed ORM (AO, Roughness, Metallic).
"""

import os
import math
import numpy as np
from PIL import Image

_this_dir = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(_this_dir)  # tools/ sits at the repo root (one level up)

HUD_GROUND_TEX = os.path.join(BASE_DIR, "assets", "ground", "textures")
UNREAL_GROUND_TEX = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader\Assets\Ground\Textures"

SIZE = 512

# ==============================================================================
# NOISE CORE (100% Mathematically Seamless Periodic Noise)
# ==============================================================================

def quintic_smooth(t):
    """C2-continuous smoothstep: 6t^5 - 15t^4 + 10t^3."""
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)

def generate_seamless_noise(size, grid_k, seed=0):
    """
    Generates a seamlessly tileable 2D value noise field of size x size
    interpolating a periodic grid_k x grid_k control lattice.
    """
    rng = np.random.RandomState(seed)
    grid = rng.uniform(-1.0, 1.0, (grid_k, grid_k)).astype(np.float32)
    step = size / grid_k
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)
    
    gx0 = (xs / step).astype(int) % grid_k
    gy0 = (ys / step).astype(int) % grid_k
    gx1 = (gx0 + 1) % grid_k
    gy1 = (gy0 + 1) % grid_k
    
    fx = (xs / step) - np.floor(xs / step)
    fy = (ys / step) - np.floor(ys / step)
    
    wx = quintic_smooth(fx)
    wy = quintic_smooth(fy)
    
    top = grid[gy0, gx0] * (1.0 - wx) + grid[gy0, gx1] * wx
    bot = grid[gy1, gx0] * (1.0 - wx) + grid[gy1, gx1] * wx
    return top * (1.0 - wy) + bot * wy

def generate_fbm(size, octaves=[(8, 0.4), (16, 0.3), (32, 0.2), (64, 0.1)], seed=100):
    """Multi-octave seamless fractal brownian motion noise."""
    res = np.zeros((size, size), dtype=np.float32)
    w_sum = 0.0
    for i, (k, w) in enumerate(octaves):
        res += generate_seamless_noise(size, k, seed=seed + i * 47) * w
        w_sum += w
    return res / w_sum

def height_to_normal_and_orm(h, base_roughness=0.8, metallic_val=0.0, strength=3.2, is_water=False):
    """
    Derives tangent-space Direct-X Normal map and packed ORM (AO=Red, Roughness=Green, Metallic=Blue).
    Uses periodic finite difference for 100% seamless tileability.
    """
    size = h.shape[0]
    h_r = np.roll(h, -1, axis=1)
    h_l = np.roll(h, 1, axis=1)
    h_d = np.roll(h, -1, axis=0)
    h_u = np.roll(h, 1, axis=0)
    
    dx = (h_r - h_l) * strength
    dy = (h_d - h_u) * strength
    dz = np.ones_like(h)
    
    length = np.sqrt(dx * dx + dy * dy + dz * dz)
    nx = -dx / length
    ny = -dy / length
    nz = dz / length
    
    # Normal Map (Direct-X: Red=+X, Green=-Y, Blue=+Z)
    norm_r = np.clip((nx * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)
    norm_g = np.clip((-ny * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)
    norm_b = np.clip((nz * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)
    normal_img = Image.fromarray(np.stack([norm_r, norm_g, norm_b], axis=-1), 'RGB')
    
    # Ambient Occlusion from local curvature / height
    ao_val = np.clip(180 + 75 * (h - h.mean()), 110, 255).astype(np.uint8)
    
    # Roughness modulation
    if is_water:
        rough_arr = np.full((size, size), int(base_roughness * 255), dtype=np.uint8)
    else:
        rough_arr = np.clip((base_roughness + 0.08 * (h - h.mean())) * 255, 40, 255).astype(np.uint8)
        
    met_arr = np.full((size, size), int(metallic_val * 255), dtype=np.uint8)
    orm_img = Image.fromarray(np.stack([ao_val, rough_arr, met_arr], axis=-1), 'RGB')
    
    return normal_img, orm_img

# ==============================================================================
# 20 TERRAIN GENERATORS
# ==============================================================================

# 1. GRASS
def gen_grass(size=SIZE):
    base_color = np.array([52, 168, 82], dtype=np.float32)
    macro = generate_fbm(size, [(8, 0.45), (16, 0.35), (32, 0.20)], seed=101)
    micro = generate_fbm(size, [(32, 0.4), (64, 0.35), (128, 0.25)], seed=201)
    rng = np.random.RandomState(301)
    grit = rng.uniform(-1.0, 1.0, (size, size))
    
    rgb = base_color + macro[:, :, None] * np.array([14, 18, -10]) + micro[:, :, None] * np.array([12, 22, 8]) + grit[:, :, None] * 6.0
    h = macro * 0.4 + micro * 0.6
    normal_img, orm_img = height_to_normal_and_orm(h, base_roughness=0.76, strength=2.2)
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), 'RGB'), normal_img, orm_img

# 2. DIRT
def gen_dirt(size=SIZE):
    base_color = np.array([126, 84, 52], dtype=np.float32)
    macro = generate_fbm(size, [(8, 0.45), (16, 0.35), (32, 0.20)], seed=102)
    micro = generate_fbm(size, [(32, 0.45), (64, 0.35), (128, 0.20)], seed=202)
    rng = np.random.RandomState(302)
    grit = rng.uniform(-1.0, 1.0, (size, size))
    
    rgb = base_color + macro[:, :, None] * np.array([16, 12, 8]) + micro[:, :, None] * np.array([20, 16, 10]) + grit[:, :, None] * 7.5
    h = macro * 0.45 + micro * 0.55
    normal_img, orm_img = height_to_normal_and_orm(h, base_roughness=0.88, strength=2.8)
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), 'RGB'), normal_img, orm_img

# 3. GRAVEL (Compacted small stones)
def gen_gravel(size=SIZE):
    rng = np.random.RandomState(103)
    grid_size = 44
    cell_w = size / grid_size
    
    pts = np.zeros((grid_size, grid_size, 2), dtype=np.float32)
    for gy in range(grid_size):
        for gx in range(grid_size):
            jx = (gx + 0.5 + rng.uniform(-0.35, 0.35)) * cell_w
            jy = (gy + 0.5 + rng.uniform(-0.35, 0.35)) * cell_w
            pts[gy, gx] = [jx % size, jy % size]
            
    palette = [
        np.array([160, 164, 172], dtype=np.float32),
        np.array([145, 149, 158], dtype=np.float32),
        np.array([178, 180, 186], dtype=np.float32),
        np.array([130, 134, 142], dtype=np.float32),
        np.array([165, 158, 150], dtype=np.float32),
        np.array([175, 168, 158], dtype=np.float32),
        np.array([115, 120, 128], dtype=np.float32),
        np.array([188, 185, 180], dtype=np.float32),
    ]
    
    pebble_colors = np.zeros((grid_size, grid_size, 3), dtype=np.float32)
    pebble_tilts = np.zeros((grid_size, grid_size, 2), dtype=np.float32)
    for gy in range(grid_size):
        for gx in range(grid_size):
            base_c = palette[rng.randint(len(palette))]
            pebble_colors[gy, gx] = np.clip(base_c + rng.uniform(-8, 8, 3), 0, 255)
            pebble_tilts[gy, gx] = rng.uniform(-0.35, 0.35, 2)
            
    y_coords, x_coords = np.mgrid[0:size, 0:size].astype(np.float32)
    gx_idx = (x_coords / cell_w).astype(int) % grid_size
    gy_idx = (y_coords / cell_w).astype(int) % grid_size
    
    min_d1 = np.full((size, size), 1e9, dtype=np.float32)
    min_d2 = np.full((size, size), 1e9, dtype=np.float32)
    closest_gx = np.zeros((size, size), dtype=int)
    closest_gy = np.zeros((size, size), dtype=int)
    closest_dx = np.zeros((size, size), dtype=np.float32)
    closest_dy = np.zeros((size, size), dtype=np.float32)
    
    for dy in [-1, 0, 1]:
        for dx in [-1, 0, 1]:
            cur_gy = (gy_idx + dy) % grid_size
            cur_gx = (gx_idx + dx) % grid_size
            px = pts[cur_gy, cur_gx, 0]
            py = pts[cur_gy, cur_gx, 1]
            diff_x = (x_coords - px + size * 0.5) % size - size * 0.5
            diff_y = (y_coords - py + size * 0.5) % size - size * 0.5
            d2 = diff_x * diff_x + diff_y * diff_y
            
            mask1 = d2 < min_d1
            min_d2[mask1] = min_d1[mask1]
            min_d1[mask1] = d2[mask1]
            closest_gx[mask1] = cur_gx[mask1]
            closest_gy[mask1] = cur_gy[mask1]
            closest_dx[mask1] = diff_x[mask1]
            closest_dy[mask1] = diff_y[mask1]
            
            mask2 = (~mask1) & (d2 < min_d2)
            min_d2[mask2] = d2[mask2]
            
    d1 = np.sqrt(min_d1)
    d2 = np.sqrt(min_d2)
    edge_dist = d2 - d1
    
    rad = cell_w * 0.55
    nx = -(closest_dx / rad) + pebble_tilts[closest_gy, closest_gx, 0]
    ny = -(closest_dy / rad) + pebble_tilts[closest_gy, closest_gx, 1]
    nz = np.sqrt(np.clip(1.0 - (nx*nx + ny*ny)*0.5, 0.1, 1.0))
    norm_len = np.sqrt(nx*nx + ny*ny + nz*nz)
    nx /= norm_len
    ny /= norm_len
    nz /= norm_len
    
    lx, ly, lz = -0.577, -0.577, 0.577
    diffuse = np.clip(nx * lx + ny * ly + nz * lz, 0.0, 1.0)
    lighting = 0.65 + 0.35 * diffuse
    
    base_color = pebble_colors[closest_gy, closest_gx]
    lit_color = base_color * lighting[:, :, None]
    
    crevice_width = cell_w * 0.14
    crevice_t = np.clip(edge_dist / crevice_width, 0.0, 1.0)[:, :, None]
    dust_color = np.array([88, 90, 96], dtype=np.float32)
    
    gravel_rgb = dust_color * (1.0 - crevice_t) + lit_color * crevice_t
    micro_grit = rng.uniform(-8, 8, (size, size, 1))
    gravel_rgb = np.clip(gravel_rgb + micro_grit, 0, 255).astype(np.uint8)
    
    norm_r = np.clip((nx * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)
    norm_g = np.clip((-ny * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)
    norm_b = np.clip((nz * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)
    normal_img = Image.fromarray(np.stack([norm_r, norm_g, norm_b], axis=-1), 'RGB')
    
    ao = np.clip(160 + 95 * crevice_t[:, :, 0], 0, 255).astype(np.uint8)
    roughness = np.full((size, size), int(0.85 * 255), dtype=np.uint8)
    metallic = np.zeros((size, size), dtype=np.uint8)
    orm_img = Image.fromarray(np.stack([ao, roughness, metallic], axis=-1), 'RGB')
    
    return Image.fromarray(gravel_rgb, 'RGB'), normal_img, orm_img

# 4. SAND
def gen_sand(size=SIZE):
    base_color = np.array([232, 185, 122], dtype=np.float32)
    macro = generate_fbm(size, [(8, 0.50), (16, 0.35), (32, 0.15)], seed=104)
    micro = generate_fbm(size, [(64, 0.50), (128, 0.35), (256, 0.15)], seed=204)
    rng = np.random.RandomState(304)
    grit = rng.uniform(-1.0, 1.0, (size, size))
    
    rgb = base_color + macro[:, :, None] * np.array([16, 12, 6]) + micro[:, :, None] * np.array([10, 8, 5]) + grit[:, :, None] * 5.0
    h = macro * 0.4 + micro * 0.6
    normal_img, orm_img = height_to_normal_and_orm(h, base_roughness=0.85, strength=2.0)
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), 'RGB'), normal_img, orm_img

# 5. SNOW
def gen_snow(size=SIZE):
    base_color = np.array([242, 246, 252], dtype=np.float32)
    macro = generate_fbm(size, [(8, 0.50), (16, 0.35), (32, 0.15)], seed=105)
    micro = generate_fbm(size, [(64, 0.50), (128, 0.35), (256, 0.15)], seed=205)
    rng = np.random.RandomState(305)
    grit = rng.uniform(-1.0, 1.0, (size, size))
    
    # Soft sky-blue shadow modulation
    rgb = base_color + macro[:, :, None] * np.array([-10, -6, 2]) + micro[:, :, None] * np.array([4, 4, 6]) + grit[:, :, None] * 3.5
    h = macro * 0.5 + micro * 0.5
    normal_img, orm_img = height_to_normal_and_orm(h, base_roughness=0.45, strength=2.2)
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), 'RGB'), normal_img, orm_img

# 6. FARMLAND (Rich tilled loam with subtle plow furrow lines)
def gen_farmland(size=SIZE):
    base_color = np.array([92, 58, 38], dtype=np.float32)
    macro = generate_fbm(size, [(8, 0.45), (16, 0.35), (32, 0.20)], seed=106)
    micro = generate_fbm(size, [(32, 0.45), (64, 0.35), (128, 0.20)], seed=206)
    rng = np.random.RandomState(306)
    grit = rng.uniform(-1.0, 1.0, (size, size))
    
    # Soft periodic furrows (8 horizontal tilled rows across 512px)
    ys = np.linspace(0, 8 * 2 * math.pi, size, endpoint=False)
    furrows = np.sin(ys)[:, None]
    
    rgb = base_color + furrows * np.array([12, 8, 5]) + macro[:, :, None] * np.array([14, 10, 6]) + micro[:, :, None] * np.array([16, 12, 8]) + grit[:, :, None] * 6.0
    h = furrows * 0.4 + macro * 0.3 + micro * 0.3
    normal_img, orm_img = height_to_normal_and_orm(h, base_roughness=0.88, strength=3.0)
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), 'RGB'), normal_img, orm_img

# 7. FOREST FLOOR (Deep woodland humus & needle duff)
def gen_forest_floor(size=SIZE):
    base_color = np.array([76, 50, 32], dtype=np.float32)
    macro = generate_fbm(size, [(8, 0.45), (16, 0.35), (32, 0.20)], seed=107)
    micro = generate_fbm(size, [(32, 0.40), (64, 0.35), (128, 0.25)], seed=207)
    rng = np.random.RandomState(307)
    grit = rng.uniform(-1.0, 1.0, (size, size))
    
    # Warm autumn duff flecks
    flecks = rng.uniform(0.0, 1.0, (size, size))
    fleck_mask = (flecks > 0.96)[:, :, None]
    fleck_color = np.array([180, 85, 25], dtype=np.float32)
    
    rgb = base_color + macro[:, :, None] * np.array([15, 10, 6]) + micro[:, :, None] * np.array([18, 12, 8]) + grit[:, :, None] * 7.0
    rgb = np.where(fleck_mask, fleck_color, rgb)
    h = macro * 0.4 + micro * 0.6
    normal_img, orm_img = height_to_normal_and_orm(h, base_roughness=0.85, strength=2.8)
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), 'RGB'), normal_img, orm_img

# 8. MUD (Wet alluvial mud, glossy specular)
def gen_mud(size=SIZE):
    base_color = np.array([82, 54, 36], dtype=np.float32)
    macro = generate_fbm(size, [(8, 0.55), (16, 0.30), (32, 0.15)], seed=108)
    micro = generate_fbm(size, [(32, 0.60), (64, 0.30), (128, 0.10)], seed=208)
    
    rgb = base_color + macro[:, :, None] * np.array([14, 10, 6]) + micro[:, :, None] * np.array([10, 8, 4])
    h = macro * 0.6 + micro * 0.4
    normal_img, orm_img = height_to_normal_and_orm(h, base_roughness=0.32, strength=2.0)
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), 'RGB'), normal_img, orm_img

# 9. TALL GRASS (Meadow green with vertical blade striae)
def gen_tall_grass(size=SIZE):
    base_color = np.array([36, 128, 58], dtype=np.float32)
    macro = generate_fbm(size, [(8, 0.45), (16, 0.35), (32, 0.20)], seed=109)
    micro = generate_fbm(size, [(32, 0.40), (64, 0.35), (128, 0.25)], seed=209)
    rng = np.random.RandomState(309)
    grit = rng.uniform(-1.0, 1.0, (size, size))
    
    # Vertical grass blade noise (stretched vertically)
    blade_noise = generate_seamless_noise(size, 64, seed=409)
    
    rgb = base_color + macro[:, :, None] * np.array([12, 18, 6]) + micro[:, :, None] * np.array([16, 24, 8]) + blade_noise[:, :, None] * np.array([10, 15, 5]) + grit[:, :, None] * 5.0
    h = macro * 0.3 + micro * 0.4 + blade_noise * 0.3
    normal_img, orm_img = height_to_normal_and_orm(h, base_roughness=0.72, strength=2.5)
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), 'RGB'), normal_img, orm_img

# 10. TRAMPLED GRASS (Soil mottled with worn grass)
def gen_trampled_grass(size=SIZE):
    base_soil = np.array([118, 86, 56], dtype=np.float32)
    base_grass = np.array([102, 142, 54], dtype=np.float32)
    
    blend = generate_fbm(size, [(8, 0.50), (16, 0.35), (32, 0.15)], seed=110)
    blend_t = np.clip((blend + 0.5) * 0.5, 0.0, 1.0)[:, :, None]
    
    micro = generate_fbm(size, [(32, 0.45), (64, 0.35), (128, 0.20)], seed=210)
    rng = np.random.RandomState(310)
    grit = rng.uniform(-1.0, 1.0, (size, size))
    
    base_color = base_soil * (1.0 - blend_t) + base_grass * blend_t
    rgb = base_color + micro[:, :, None] * np.array([15, 15, 8]) + grit[:, :, None] * 6.0
    h = blend * 0.4 + micro * 0.6
    normal_img, orm_img = height_to_normal_and_orm(h, base_roughness=0.82, strength=2.6)
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), 'RGB'), normal_img, orm_img

# 11. PATH (Compacted footpath dirt)
def gen_path(size=SIZE):
    base_color = np.array([138, 102, 72], dtype=np.float32)
    macro = generate_fbm(size, [(8, 0.45), (16, 0.35), (32, 0.20)], seed=111)
    micro = generate_fbm(size, [(32, 0.45), (64, 0.35), (128, 0.20)], seed=211)
    rng = np.random.RandomState(311)
    grit = rng.uniform(-1.0, 1.0, (size, size))
    
    rgb = base_color + macro[:, :, None] * np.array([14, 10, 6]) + micro[:, :, None] * np.array([18, 14, 8]) + grit[:, :, None] * 7.0
    h = macro * 0.35 + micro * 0.65
    normal_img, orm_img = height_to_normal_and_orm(h, base_roughness=0.82, strength=2.6)
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), 'RGB'), normal_img, orm_img

# 12. ROAD (Graded country road aggregate)
def gen_road(size=SIZE):
    base_color = np.array([142, 136, 126], dtype=np.float32)
    macro = generate_fbm(size, [(8, 0.45), (16, 0.35), (32, 0.20)], seed=112)
    micro = generate_fbm(size, [(32, 0.40), (64, 0.35), (128, 0.25)], seed=212)
    rng = np.random.RandomState(312)
    grit = rng.uniform(-1.0, 1.0, (size, size))
    
    rgb = base_color + macro[:, :, None] * np.array([12, 10, 8]) + micro[:, :, None] * np.array([16, 14, 12]) + grit[:, :, None] * 8.0
    h = macro * 0.3 + micro * 0.7
    normal_img, orm_img = height_to_normal_and_orm(h, base_roughness=0.80, strength=2.8)
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), 'RGB'), normal_img, orm_img

# 13. BLACK TOP (Asphalt road surface)
def gen_black_top(size=SIZE):
    base_color = np.array([46, 50, 56], dtype=np.float32)
    macro = generate_fbm(size, [(8, 0.45), (16, 0.35), (32, 0.20)], seed=113)
    micro = generate_fbm(size, [(32, 0.40), (64, 0.35), (128, 0.25)], seed=213)
    rng = np.random.RandomState(313)
    grit = rng.uniform(-1.0, 1.0, (size, size))
    
    rgb = base_color + macro[:, :, None] * np.array([6, 6, 8]) + micro[:, :, None] * np.array([12, 12, 14]) + grit[:, :, None] * 7.0
    h = macro * 0.25 + micro * 0.75
    normal_img, orm_img = height_to_normal_and_orm(h, base_roughness=0.76, metallic_val=0.04, strength=3.0)
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), 'RGB'), normal_img, orm_img

# 14. CONCRETE (Architectural concrete slab)
def gen_concrete(size=SIZE):
    base_color = np.array([198, 202, 210], dtype=np.float32)
    macro = generate_fbm(size, [(8, 0.50), (16, 0.35), (32, 0.15)], seed=114)
    micro = generate_fbm(size, [(32, 0.40), (64, 0.35), (128, 0.25)], seed=214)
    rng = np.random.RandomState(314)
    grit = rng.uniform(-1.0, 1.0, (size, size))
    
    rgb = base_color + macro[:, :, None] * np.array([8, 8, 10]) + micro[:, :, None] * np.array([10, 10, 12]) + grit[:, :, None] * 5.0
    h = macro * 0.3 + micro * 0.7
    normal_img, orm_img = height_to_normal_and_orm(h, base_roughness=0.68, strength=2.2)
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), 'RGB'), normal_img, orm_img

# 15. BRICKS (Clay brick paver surface)
def gen_bricks(size=SIZE):
    brick_color = np.array([178, 72, 52], dtype=np.float32)
    mortar_color = np.array([168, 162, 155], dtype=np.float32)
    
    # Seamless running bond bricks: 8 rows of 64px height, 4 bricks per row (128px width)
    row_h = 64
    brick_w = 128
    mortar_t = 4
    
    ys, xs = np.mgrid[0:size, 0:size]
    row_idx = ys // row_h
    offset = np.where(row_idx % 2 == 1, brick_w // 2, 0)
    col_x = (xs + offset) % brick_w
    row_y = ys % row_h
    
    is_mortar = (row_y < mortar_t) | (col_x < mortar_t)
    mortar_mask = is_mortar[:, :, None]
    
    macro = generate_fbm(size, [(8, 0.45), (16, 0.35), (32, 0.20)], seed=115)
    micro = generate_fbm(size, [(32, 0.45), (64, 0.35), (128, 0.20)], seed=215)
    rng = np.random.RandomState(315)
    grit = rng.uniform(-1.0, 1.0, (size, size))
    
    brick_rgb = brick_color + macro[:, :, None] * np.array([18, 10, 8]) + micro[:, :, None] * np.array([14, 8, 6]) + grit[:, :, None] * 6.0
    mortar_rgb = mortar_color + grit[:, :, None] * 5.0
    
    rgb = np.where(mortar_mask, mortar_rgb, brick_rgb)
    h = np.where(is_mortar, -0.6, 0.4) + micro * 0.3
    normal_img, orm_img = height_to_normal_and_orm(h, base_roughness=0.78, strength=3.5)
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), 'RGB'), normal_img, orm_img

# 16. FLAGSTONE (Natural slate paving)
def gen_flagstone(size=SIZE):
    base_slate = np.array([136, 144, 154], dtype=np.float32)
    mortar_color = np.array([80, 75, 72], dtype=np.float32)
    
    # 8x8 Voronoi stones
    rng = np.random.RandomState(116)
    grid_size = 8
    cell_w = size / grid_size
    pts = np.zeros((grid_size, grid_size, 2), dtype=np.float32)
    for gy in range(grid_size):
        for gx in range(grid_size):
            jx = (gx + 0.5 + rng.uniform(-0.3, 0.3)) * cell_w
            jy = (gy + 0.5 + rng.uniform(-0.3, 0.3)) * cell_w
            pts[gy, gx] = [jx % size, jy % size]
            
    stone_tones = [
        np.array([145, 153, 163], dtype=np.float32),
        np.array([125, 134, 145], dtype=np.float32),
        np.array([150, 156, 162], dtype=np.float32),
        np.array([130, 138, 148], dtype=np.float32),
    ]
    stone_colors = np.zeros((grid_size, grid_size, 3), dtype=np.float32)
    for gy in range(grid_size):
        for gx in range(grid_size):
            stone_colors[gy, gx] = stone_tones[rng.randint(len(stone_tones))]
            
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)
    gx_idx = (xs / cell_w).astype(int) % grid_size
    gy_idx = (ys / cell_w).astype(int) % grid_size
    
    min_d1 = np.full((size, size), 1e9, dtype=np.float32)
    min_d2 = np.full((size, size), 1e9, dtype=np.float32)
    closest_gx = np.zeros((size, size), dtype=int)
    closest_gy = np.zeros((size, size), dtype=int)
    
    for dy in [-1, 0, 1]:
        for dx in [-1, 0, 1]:
            cur_gy = (gy_idx + dy) % grid_size
            cur_gx = (gx_idx + dx) % grid_size
            px = pts[cur_gy, cur_gx, 0]
            py = pts[cur_gy, cur_gx, 1]
            diff_x = (xs - px + size * 0.5) % size - size * 0.5
            diff_y = (ys - py + size * 0.5) % size - size * 0.5
            d2 = diff_x * diff_x + diff_y * diff_y
            mask1 = d2 < min_d1
            min_d2[mask1] = min_d1[mask1]
            min_d1[mask1] = d2[mask1]
            closest_gx[mask1] = cur_gx[mask1]
            closest_gy[mask1] = cur_gy[mask1]
            mask2 = (~mask1) & (d2 < min_d2)
            min_d2[mask2] = d2[mask2]
            
    d1 = np.sqrt(min_d1)
    d2 = np.sqrt(min_d2)
    edge_dist = d2 - d1
    
    stone_c = stone_colors[closest_gy, closest_gx]
    micro = generate_fbm(size, [(32, 0.5), (64, 0.35), (128, 0.15)], seed=216)
    grit = rng.uniform(-1.0, 1.0, (size, size))
    
    mortar_t = np.clip(edge_dist / 6.0, 0.0, 1.0)[:, :, None]
    rgb = mortar_color * (1.0 - mortar_t) + (stone_c + micro[:, :, None] * 12.0 + grit[:, :, None] * 5.0) * mortar_t
    h = np.clip(edge_dist / 6.0, 0.0, 1.0) * 0.7 + micro * 0.3
    normal_img, orm_img = height_to_normal_and_orm(h, base_roughness=0.75, strength=3.0)
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), 'RGB'), normal_img, orm_img

# 17. WOOD PLANKS (Timber deck boards)
def gen_wood_planks(size=SIZE):
    base_wood = np.array([168, 122, 82], dtype=np.float32)
    gap_color = np.array([48, 32, 20], dtype=np.float32)
    
    # 8 planks of 64px width running vertically
    plank_w = 64
    gap_w = 3
    
    ys, xs = np.mgrid[0:size, 0:size]
    plank_x = xs % plank_w
    is_gap = plank_x < gap_w
    gap_mask = is_gap[:, :, None]
    
    macro = generate_fbm(size, [(8, 0.50), (16, 0.35), (32, 0.15)], seed=117)
    # Stretched grain noise
    grain = generate_seamless_noise(size, 64, seed=217)
    rng = np.random.RandomState(317)
    grit = rng.uniform(-1.0, 1.0, (size, size))
    
    wood_rgb = base_wood + macro[:, :, None] * np.array([14, 10, 6]) + grain[:, :, None] * np.array([12, 8, 5]) + grit[:, :, None] * 5.0
    rgb = np.where(gap_mask, gap_color, wood_rgb)
    h = np.where(is_gap, -0.6, 0.4) + grain * 0.25
    normal_img, orm_img = height_to_normal_and_orm(h, base_roughness=0.70, strength=3.2)
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), 'RGB'), normal_img, orm_img

# 18. SWAMP (Murky stagnant water & bog)
def gen_swamp(size=SIZE):
    base_color = np.array([42, 56, 36], dtype=np.float32)
    macro = generate_fbm(size, [(8, 0.50), (16, 0.35), (32, 0.15)], seed=118)
    micro = generate_fbm(size, [(32, 0.55), (64, 0.30), (128, 0.15)], seed=218)
    
    rgb = base_color + macro[:, :, None] * np.array([8, 12, 6]) + micro[:, :, None] * np.array([12, 16, 8])
    h = macro * 0.5 + micro * 0.5
    normal_img, orm_img = height_to_normal_and_orm(h, base_roughness=0.28, strength=1.8, is_water=True)
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), 'RGB'), normal_img, orm_img

# 19. POND (Clear turquoise freshwater)
def gen_pond(size=SIZE):
    base_color = np.array([30, 158, 182], dtype=np.float32)
    macro = generate_fbm(size, [(8, 0.55), (16, 0.30), (32, 0.15)], seed=119)
    micro = generate_fbm(size, [(32, 0.50), (64, 0.35), (128, 0.15)], seed=219)
    
    rgb = base_color + macro[:, :, None] * np.array([6, 14, 18]) + micro[:, :, None] * np.array([8, 18, 22])
    h = macro * 0.6 + micro * 0.4
    normal_img, orm_img = height_to_normal_and_orm(h, base_roughness=0.10, strength=1.5, is_water=True)
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), 'RGB'), normal_img, orm_img

# 20. DEEP WATER (Deep cobalt ocean water)
def gen_deep_water(size=SIZE):
    base_color = np.array([24, 62, 132], dtype=np.float32)
    macro = generate_fbm(size, [(8, 0.60), (16, 0.30), (32, 0.10)], seed=120)
    micro = generate_fbm(size, [(32, 0.55), (64, 0.30), (128, 0.15)], seed=220)
    
    rgb = base_color + macro[:, :, None] * np.array([6, 12, 22]) + micro[:, :, None] * np.array([8, 16, 26])
    h = macro * 0.7 + micro * 0.3
    normal_img, orm_img = height_to_normal_and_orm(h, base_roughness=0.08, strength=1.6, is_water=True)
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), 'RGB'), normal_img, orm_img

# ==============================================================================
# DISPATCHER
# ==============================================================================
GROUND_GENERATORS = {
    "grass": gen_grass,
    "dirt": gen_dirt,
    "gravel": gen_gravel,
    "sand": gen_sand,
    "snow": gen_snow,
    "farmland": gen_farmland,
    "forest_floor": gen_forest_floor,
    "mud": gen_mud,
    "tall_grass": gen_tall_grass,
    "trampled_grass": gen_trampled_grass,
    "path": gen_path,
    "road": gen_road,
    "black_top": gen_black_top,
    "concrete": gen_concrete,
    "bricks": gen_bricks,
    "flagstone": gen_flagstone,
    "wood_planks": gen_wood_planks,
    "swamp": gen_swamp,
    "pond": gen_pond,
    "deep_water": gen_deep_water,
}

def main():
    print("=== GENERATING 20 SEAMLESS PBR GROUND TEXTURE SETS (v3 - Noise & Compacted Aggregate) ===")
    targets = [HUD_GROUND_TEX, UNREAL_GROUND_TEX]
    
    for name, func in GROUND_GENERATORS.items():
        base_img, norm_img, orm_img = func(SIZE)
        
        for t_root in targets:
            g_dir = os.path.join(t_root, name)
            os.makedirs(g_dir, exist_ok=True)
            
            base_img.save(os.path.join(g_dir, f"T_Ground_{name}_BaseColor.png"), "PNG")
            norm_img.save(os.path.join(g_dir, f"T_Ground_{name}_Normal.png"), "PNG")
            orm_img.save(os.path.join(g_dir, f"T_Ground_{name}_ORM.png"), "PNG")
            
        print(f"  [OK] {name:16} -> BaseColor, Normal, ORM generated and deployed.")
        
    print("\nSUCCESS: All 20 seamless terrain textures regenerated and synchronized.")

if __name__ == '__main__':
    main()
