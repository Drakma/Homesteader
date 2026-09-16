import numpy as np
from PIL import Image
import math

SIZE = 512

def quintic_smooth(t):
    """6t^5 - 15t^4 + 10t^3 smoothstep with zero 1st and 2nd derivatives at 0 and 1."""
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)

def generate_seamless_noise_2d(size, grid_k, seed=0):
    """
    Generates a 100% mathematically seamless 2D value noise field of size x size
    using a periodic grid of grid_k x grid_k control points with quintic Hermite interpolation.
    """
    rng = np.random.RandomState(seed)
    grid = rng.uniform(-1.0, 1.0, (grid_k, grid_k)).astype(np.float32)
    
    # Pixel coordinates
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
    
    v00 = grid[gy0, gx0]
    v10 = grid[gy0, gx1]
    v01 = grid[gy1, gx0]
    v11 = grid[gy1, gx1]
    
    top = v00 * (1.0 - wx) + v10 * wx
    bot = v01 * (1.0 - wx) + v11 * wx
    val = top * (1.0 - wy) + bot * wy
    return val

def generate_fbm_seamless(size, octaves=[(4, 0.45), (8, 0.28), (16, 0.16), (32, 0.08), (64, 0.04)], seed=100):
    """Multi-octave seamless fractional brownian motion noise."""
    res = np.zeros((size, size), dtype=np.float32)
    weight_sum = 0.0
    for i, (k, w) in enumerate(octaves):
        res += generate_seamless_noise_2d(size, k, seed=seed + i * 37) * w
        weight_sum += w
    return res / weight_sum

def test_flat_noise_terrain():
    # 1. GRASS
    # Clean pasture green base, subtle organic turf stipple
    base_grass = np.array([48, 168, 88], dtype=np.float32)
    macro_grass = generate_fbm_seamless(SIZE, [(4, 0.5), (8, 0.3), (16, 0.2)], seed=201)
    micro_grass = generate_fbm_seamless(SIZE, [(32, 0.4), (64, 0.35), (128, 0.25)], seed=301)
    # High frequency grit
    rng = np.random.RandomState(401)
    grit = rng.uniform(-1.0, 1.0, (SIZE, SIZE))
    
    # Blend:
    # Macro gives gentle warmth/coolness (+- 14 rgb)
    # Micro gives turf texture (+- 18 rgb)
    # Grit gives fine stipple (+- 6 rgb)
    grass_rgb = base_grass + macro_grass[:, :, None] * np.array([12, 18, -10]) + micro_grass[:, :, None] * np.array([15, 25, 10]) + grit[:, :, None] * 6.0
    grass_img = Image.fromarray(np.clip(grass_rgb, 0, 255).astype(np.uint8), 'RGB')
    grass_img.save('scratch/test_noise_grass.png')
    
    # 2. DIRT
    base_dirt = np.array([124, 82, 52], dtype=np.float32)
    macro_dirt = generate_fbm_seamless(SIZE, [(4, 0.5), (8, 0.3), (16, 0.2)], seed=202)
    micro_dirt = generate_fbm_seamless(SIZE, [(32, 0.4), (64, 0.35), (128, 0.25)], seed=302)
    grit_dirt = rng.uniform(-1.0, 1.0, (SIZE, SIZE))
    
    dirt_rgb = base_dirt + macro_dirt[:, :, None] * np.array([16, 12, 8]) + micro_dirt[:, :, None] * np.array([22, 16, 10]) + grit_dirt[:, :, None] * 8.0
    dirt_img = Image.fromarray(np.clip(dirt_rgb, 0, 255).astype(np.uint8), 'RGB')
    dirt_img.save('scratch/test_noise_dirt.png')

    # 3. SAND
    base_sand = np.array([232, 184, 120], dtype=np.float32)
    macro_sand = generate_fbm_seamless(SIZE, [(4, 0.55), (8, 0.3), (16, 0.15)], seed=203)
    micro_sand = generate_fbm_seamless(SIZE, [(64, 0.4), (128, 0.35), (256, 0.25)], seed=303)
    sand_rgb = base_sand + macro_sand[:, :, None] * np.array([18, 14, 8]) + micro_sand[:, :, None] * np.array([10, 8, 6]) + grit[:, :, None] * 4.0
    sand_img = Image.fromarray(np.clip(sand_rgb, 0, 255).astype(np.uint8), 'RGB')
    sand_img.save('scratch/test_noise_sand.png')
    
    print("Saved test_noise_grass.png, test_noise_dirt.png, test_noise_sand.png")

if __name__ == '__main__':
    test_flat_noise_terrain()

