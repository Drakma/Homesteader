import numpy as np
from PIL import Image
import math

SIZE = 512

def generate_compacted_gravel(size=SIZE, seed=77):
    rng = np.random.RandomState(seed)
    
    # 44x44 grid of small pebbles -> ~11.6px per stone (thousands of tightly packed rocks)
    grid_size = 44
    cell_w = size / grid_size
    
    pts = np.zeros((grid_size, grid_size, 2), dtype=np.float32)
    for gy in range(grid_size):
        for gx in range(grid_size):
            jx = (gx + 0.5 + rng.uniform(-0.35, 0.35)) * cell_w
            jy = (gy + 0.5 + rng.uniform(-0.35, 0.35)) * cell_w
            pts[gy, gx] = [jx % size, jy % size]
            
    # Natural compacted stone palette
    palette = [
        np.array([160, 164, 172], dtype=np.float32), # classic gray stone
        np.array([145, 149, 158], dtype=np.float32), # mid cool slate
        np.array([178, 180, 186], dtype=np.float32), # light limestone
        np.array([130, 134, 142], dtype=np.float32), # darker slate
        np.array([165, 158, 150], dtype=np.float32), # warm tan river rock
        np.array([175, 168, 158], dtype=np.float32), # warm beige pebble
        np.array([115, 120, 128], dtype=np.float32), # dark basalt fragment
        np.array([188, 185, 180], dtype=np.float32), # pale chalk speck
    ]
    
    pebble_colors = np.zeros((grid_size, grid_size, 3), dtype=np.float32)
    pebble_tilts = np.zeros((grid_size, grid_size, 2), dtype=np.float32)
    for gy in range(grid_size):
        for gx in range(grid_size):
            base_c = palette[rng.randint(len(palette))]
            pebble_colors[gy, gx] = np.clip(base_c + rng.uniform(-8, 8, 3), 0, 255)
            # Random facet tilt for low-poly faceted look
            pebble_tilts[gy, gx] = rng.uniform(-0.4, 0.4, 2)
            
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
    edge_dist = d2 - d1  # distance to pebble border
    
    # Pebble normal computation:
    # dome curvature + random facet tilt
    rad = cell_w * 0.55
    nx = -(closest_dx / rad) + pebble_tilts[closest_gy, closest_gx, 0]
    ny = -(closest_dy / rad) + pebble_tilts[closest_gy, closest_gx, 1]
    nz = np.sqrt(np.clip(1.0 - (nx*nx + ny*ny)*0.5, 0.1, 1.0))
    
    norm_len = np.sqrt(nx*nx + ny*ny + nz*nz)
    nx /= norm_len
    ny /= norm_len
    nz /= norm_len
    
    # Directional Key light (Top-Left key light: lx = -0.577, ly = -0.577, lz = 0.577)
    lx, ly, lz = -0.577, -0.577, 0.577
    diffuse = np.clip(nx * lx + ny * ly + nz * lz, 0.0, 1.0)
    lighting = 0.65 + 0.35 * diffuse  # Soft ambient fill, clean key highlight
    
    base_color = pebble_colors[closest_gy, closest_gx]
    lit_color = base_color * lighting[:, :, None]
    
    # Compacted dust / crevice grit filling gaps between stones
    crevice_width = cell_w * 0.14
    crevice_t = np.clip(edge_dist / crevice_width, 0.0, 1.0)[:, :, None]
    dust_color = np.array([88, 90, 96], dtype=np.float32)
    
    # Blend pebble with compacted dust
    gravel_rgb = dust_color * (1.0 - crevice_t) + lit_color * crevice_t
    
    # Fine tactile mineral noise
    micro_grit = rng.uniform(-9, 9, (size, size, 1))
    gravel_rgb = np.clip(gravel_rgb + micro_grit, 0, 255).astype(np.uint8)
    
    # Derive normal map:
    # Direct-X tangent space normal: R=nx, G=-ny, B=nz
    norm_r = np.clip((nx * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)
    norm_g = np.clip((-ny * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8) # Inverted Y for Unreal
    norm_b = np.clip((nz * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)
    normal_img = Image.fromarray(np.stack([norm_r, norm_g, norm_b], axis=-1), 'RGB')
    
    # ORM map: R=AO (crevice shadow), G=Roughness, B=Metallic
    ao = np.clip(160 + 95 * crevice_t[:, :, 0], 0, 255).astype(np.uint8)
    roughness = np.full((size, size), int(0.85 * 255), dtype=np.uint8)
    metallic = np.zeros((size, size), dtype=np.uint8)
    orm_img = Image.fromarray(np.stack([ao, roughness, metallic], axis=-1), 'RGB')
    
    return Image.fromarray(gravel_rgb, 'RGB'), normal_img, orm_img

if __name__ == '__main__':
    base, norm, orm = generate_compacted_gravel()
    base.save('scratch/test_perfect_gravel.png')
    norm.save('scratch/test_perfect_gravel_norm.png')
    orm.save('scratch/test_perfect_gravel_orm.png')
    print("Saved test_perfect_gravel textures!")

