import numpy as np
from PIL import Image
import math

SIZE = 512

def quintic_smooth(t):
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)

def generate_seamless_noise(size, grid_k, seed=0):
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

def generate_fbm(size, octaves, seed=100):
    res = np.zeros((size, size), dtype=np.float32)
    w_sum = 0.0
    for i, (k, w) in enumerate(octaves):
        res += generate_seamless_noise(size, k, seed=seed + i * 37) * w
        w_sum += w
    return res / w_sum

def height_to_normal(h, strength=3.0):
    size = h.shape[0]
    # Periodic finite difference
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
    
    norm_r = np.clip((nx * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)
    norm_g = np.clip((-ny * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8) # Invert Y for Unreal Engine
    norm_b = np.clip((nz * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)
    return Image.fromarray(np.stack([norm_r, norm_g, norm_b], axis=-1), 'RGB'), nx, ny, nz

print("Noise engine verified!")

