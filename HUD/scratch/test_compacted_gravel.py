import numpy as np
from PIL import Image
import math

SIZE = 512

def generate_compacted_gravel(size=SIZE, seed=42):
    np.random.seed(seed)
    
    # Grid of small pebbles: 36x36 across 512 = ~14px per pebble
    grid_size = 36
    cell_w = size / grid_size
    
    pts = np.zeros((grid_size, grid_size, 2), dtype=np.float32)
    for gy in range(grid_size):
        for gx in range(grid_size):
            jx = (gx + 0.5 + np.random.uniform(-0.35, 0.35)) * cell_w
            jy = (gy + 0.5 + np.random.uniform(-0.35, 0.35)) * cell_w
            pts[gy, gx] = [jx % size, jy % size]
            
    palette = [
        np.array([172, 176, 184], dtype=np.float32), # light blue-gray
        np.array([150, 155, 163], dtype=np.float32), # mid gray
        np.array([195, 198, 204], dtype=np.float32), # bright chalk/limestone
        np.array([135, 138, 146], dtype=np.float32), # darker slate
        np.array([168, 162, 155], dtype=np.float32), # warm tan-gray
        np.array([182, 175, 165], dtype=np.float32), # warm beige pebble
        np.array([120, 125, 132], dtype=np.float32), # deep slate
    ]
    
    pebble_colors = np.zeros((grid_size, grid_size, 3), dtype=np.float32)
    for gy in range(grid_size):
        for gx in range(grid_size):
            base_c = palette[np.random.randint(len(palette))]
            pebble_colors[gy, gx] = np.clip(base_c + np.random.uniform(-10, 10, 3), 0, 255)
            
    y_coords, x_coords = np.mgrid[0:size, 0:size].astype(np.float32)
    gx_idx = (x_coords / cell_w).astype(int) % grid_size
    gy_idx = (y_coords / cell_w).astype(int) % grid_size
    
    min_dist1 = np.full((size, size), 1e9, dtype=np.float32)
    min_dist2 = np.full((size, size), 1e9, dtype=np.float32)
    closest_gx = np.zeros((size, size), dtype=int)
    closest_gy = np.zeros((size, size), dtype=int)
    
    for dy in [-1, 0, 1]:
        for dx in [-1, 0, 1]:
            cur_gy = (gy_idx + dy) % grid_size
            cur_gx = (gx_idx + dx) % grid_size
            
            px = pts[cur_gy, cur_gx, 0]
            py = pts[cur_gy, cur_gx, 1]
            
            diff_x = (x_coords - px + size * 0.5) % size - size * 0.5
            diff_y = (y_coords - py + size * 0.5) % size - size * 0.5
            d2 = diff_x * diff_x + diff_y * diff_y
            
            mask1 = d2 < min_dist1
            min_dist2[mask1] = min_dist1[mask1]
            min_dist1[mask1] = d2[mask1]
            closest_gx[mask1] = cur_gx[mask1]
            closest_gy[mask1] = cur_gy[mask1]
            
            mask2 = (~mask1) & (d2 < min_dist2)
            min_dist2[mask2] = d2[mask2]
            
    d1 = np.sqrt(min_dist1)
    d2 = np.sqrt(min_dist2)
    
    edge_dist = d2 - d1
    
    base_color = pebble_colors[closest_gy, closest_gx]
    
    # Pebble dome shape
    pebble_dome = np.clip(edge_dist / (cell_w * 0.4), 0.0, 1.0)
    pebble_dome = np.sin(pebble_dome * (math.pi * 0.5))
    
    # Compacted dust / crevice color
    dust_color = np.array([85, 88, 95], dtype=np.float32)
    
    crevice_mask = np.clip(edge_dist / (cell_w * 0.18), 0.0, 1.0)[:, :, None]
    color = dust_color * (1.0 - crevice_mask) + base_color * crevice_mask
    
    # Fine stone grit noise (seamless)
    noise_fine = np.random.uniform(-10, 10, (size, size, 1))
    
    color = color * (0.80 + 0.28 * pebble_dome[:, :, None]) + noise_fine
    color = np.clip(color, 0, 255).astype(np.uint8)
    return Image.fromarray(color, 'RGB')

if __name__ == '__main__':
    im = generate_compacted_gravel(512)
    im.save('scratch/test_compacted_gravel.png')
    print('Saved scratch/test_compacted_gravel.png')

