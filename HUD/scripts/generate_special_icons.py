#!/usr/bin/env python3
"""
generate_special_icons.py
Procedurally renders 3D low-poly faceted icons adhering strictly to Homesteader standards:
- 128x128 canvas
- 12px safe margin (bounding box max <= 104px centered)
- 32-bit transparent RGBA, 100% border alpha = 0
- 3D low-poly faceted aesthetic with visible polygon planes, top-left key lighting, ambient occlusion, and subtle highlights.
"""

import math
import os
import shutil
from PIL import Image, ImageDraw, ImageFilter

HUD_ITEMS_DIR = r"c:\Users\casey\Desktop\Homesteader\HUD\assets\items"
UE5_ICONS_DIR = r"c:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader\UI\Icons"

os.makedirs(HUD_ITEMS_DIR, exist_ok=True)
os.makedirs(UE5_ICONS_DIR, exist_ok=True)

SUPERSAMPLE = 4
CANVAS_SIZE = 128 * SUPERSAMPLE
MARGIN = 14 * SUPERSAMPLE
MAX_DIM = 100 * SUPERSAMPLE

def create_base_canvas():
    return Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))

def finalize_and_save(img, filename):
    # Downsample with Lanczos for smooth anti-aliased facet edges
    final = img.resize((128, 128), Image.Resampling.LANCZOS)
    
    # Strictly enforce 12px perimeter alpha = 0
    pix = final.load()
    w, h = final.size
    
    # Calculate bounding box of non-zero alpha
    min_x, max_x = w, 0
    min_y, max_y = h, 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = pix[x, y]
            if a > 0:
                if x < min_x: min_x = x
                if x > max_x: max_x = x
                if y < min_y: min_y = y
                if y > max_y: max_y = y
                
    # Ensure 100% outer perimeter is completely alpha 0
    for x in range(w):
        pix[x, 0] = (0, 0, 0, 0)
        pix[x, h - 1] = (0, 0, 0, 0)
    for y in range(h):
        pix[0, y] = (0, 0, 0, 0)
        pix[w - 1, y] = (0, 0, 0, 0)

    # Save to HUD and UE5
    hud_path = os.path.join(HUD_ITEMS_DIR, filename)
    ue5_path = os.path.join(UE5_ICONS_DIR, filename)
    final.save(hud_path, "PNG")
    final.save(ue5_path, "PNG")
    print(f"Saved {filename} -> HUD & UE5 (bounds: [{min_x}, {min_y}] to [{max_x}, {max_y}], span: {max_x-min_x+1}x{max_y-min_y+1})")

def shade(color, factor):
    """Adjust color brightness for 3D faceting (0.5 = shadow, 1.0 = base, 1.3 = highlight)."""
    r, g, b = color[:3]
    a = color[3] if len(color) > 3 else 255
    r = min(255, max(0, int(r * factor)))
    g = min(255, max(0, int(g * factor)))
    b = min(255, max(0, int(b * factor)))
    return (r, g, b, a)

def draw_poly(draw, pts, color, outline=None):
    draw.polygon(pts, fill=color, outline=outline)

# ==============================================================================
# 1. UI ICONS (Rule 5 Compliant: 3D Low-Poly Faceted)
# ==============================================================================

def render_icon_coin():
    img = create_base_canvas()
    draw = ImageDraw.Draw(img)
    cx, cy = 64 * SUPERSAMPLE, 64 * SUPERSAMPLE
    
    # 3D thick gold coin tilted in isometric view
    rx, ry = 42 * SUPERSAMPLE, 34 * SUPERSAMPLE
    depth = 12 * SUPERSAMPLE
    
    gold_base = (245, 185, 35, 255)
    gold_dark = (175, 115, 15, 255)
    gold_mid = (215, 155, 25, 255)
    gold_light = (255, 225, 110, 255)
    gold_rim = (150, 95, 10, 255)
    
    # 1. Extruded Rim / Thickness Facets (Bottom half)
    segments = 16
    rim_pts_top = []
    rim_pts_bot = []
    for i in range(segments + 1):
        angle = math.pi * 0.9 * (i / segments) + math.pi * 0.05
        x = cx + rx * math.cos(angle)
        y = cy + ry * math.sin(angle)
        rim_pts_top.append((x, y))
        rim_pts_bot.append((x, y + depth))
        
    for i in range(segments):
        p1 = rim_pts_top[i]
        p2 = rim_pts_top[i+1]
        p3 = rim_pts_bot[i+1]
        p4 = rim_pts_bot[i]
        light = 0.55 + 0.35 * math.sin(i / segments * math.pi)
        c = shade(gold_dark, light)
        draw.polygon([p1, p2, p3, p4], fill=c, outline=gold_rim)
        
    # 2. Coin Top Face (Faceted Hexadecagon)
    top_poly = []
    num_top = 16
    for i in range(num_top):
        a = 2 * math.pi * (i / num_top)
        top_poly.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
    
    for i in range(num_top):
        p1 = top_poly[i]
        p2 = top_poly[(i+1) % num_top]
        a_mid = 2 * math.pi * ((i + 0.5) / num_top)
        nx = math.cos(a_mid)
        ny = math.sin(a_mid)
        dot = -0.707 * nx - 0.707 * ny
        fac = 0.85 + 0.35 * dot
        draw.polygon([p1, p2, (cx, cy)], fill=shade(gold_base, fac), outline=gold_rim)
        
    # 3. Inner Embossed Bevel Ring
    inner_poly = []
    irx, iry = rx * 0.76, ry * 0.76
    for i in range(num_top):
        a = 2 * math.pi * (i / num_top)
        inner_poly.append((cx + irx * math.cos(a), cy + iry * math.sin(a)))
    for i in range(num_top):
        p1 = inner_poly[i]
        p2 = inner_poly[(i+1) % num_top]
        a_mid = 2 * math.pi * ((i + 0.5) / num_top)
        dot = -0.707 * math.cos(a_mid) - 0.707 * math.sin(a_mid)
        fac = 0.78 + 0.30 * dot
        draw.polygon([p1, p2, (cx, cy)], fill=shade(gold_mid, fac))
    draw.polygon(inner_poly, outline=gold_dark)
        
    # 4. Embossed 3D "$" Symbol (Faceted)
    s_dark = (140, 80, 5, 255)
    s_light = (255, 240, 140, 255)
    s_base = (235, 175, 20, 255)
    
    # Vertical bar
    bw = 3 * SUPERSAMPLE
    bh = 25 * SUPERSAMPLE
    draw.rectangle([cx - bw, cy - bh, cx + bw, cy + bh], fill=s_base, outline=s_dark)
    draw.line([(cx - bw, cy - bh), (cx - bw, cy + bh)], fill=s_light, width=2)
    
    # S curve upper loop, spine, lower loop
    sw = 15 * SUPERSAMPLE
    sh = 18 * SUPERSAMPLE
    draw.rectangle([cx - sw, cy - sh, cx + sw, cy - sh + 5*SUPERSAMPLE], fill=s_base, outline=s_dark)
    draw.rectangle([cx - sw, cy - sh, cx - sw + 5*SUPERSAMPLE, cy - 2*SUPERSAMPLE], fill=s_light, outline=s_dark)
    draw.rectangle([cx - sw, cy - 2*SUPERSAMPLE, cx + sw, cy + 3*SUPERSAMPLE], fill=s_base, outline=s_dark)
    draw.rectangle([cx + sw - 5*SUPERSAMPLE, cy + 2*SUPERSAMPLE, cx + sw, cy + sh], fill=s_dark, outline=s_dark)
    draw.rectangle([cx - sw, cy + sh - 5*SUPERSAMPLE, cx + sw, cy + sh], fill=s_base, outline=s_dark)
    draw.line([(cx - sw, cy - sh), (cx + sw, cy - sh)], fill=s_light, width=2)
    draw.line([(cx - sw, cy - 2*SUPERSAMPLE), (cx + sw, cy - 2*SUPERSAMPLE)], fill=s_light, width=2)

    finalize_and_save(img, "icon_coin.png")

def render_icon_heart():
    img = create_base_canvas()
    draw = ImageDraw.Draw(img)
    cx, cy = 64 * SUPERSAMPLE, 62 * SUPERSAMPLE
    s = SUPERSAMPLE
    
    v_top_center = (cx, cy - 16*s)
    v_left_lobe_top = (cx - 24*s, cy - 32*s)
    v_left_lobe_mid = (cx - 36*s, cy - 18*s)
    v_left_lobe_bot = (cx - 34*s, cy + 4*s)
    v_tip = (cx, cy + 36*s)
    v_right_lobe_bot = (cx + 34*s, cy + 4*s)
    v_right_lobe_mid = (cx + 36*s, cy - 18*s)
    v_right_lobe_top = (cx + 24*s, cy - 32*s)
    
    v_center_crest = (cx, cy + 2*s)
    v_left_crest = (cx - 18*s, cy - 10*s)
    v_right_crest = (cx + 18*s, cy - 10*s)
    
    red_dark = (130, 15, 25, 255)
    red_mid = (195, 28, 42, 255)
    red_light = (245, 65, 80, 255)
    red_spec = (255, 140, 150, 255)
    dark_rim = (85, 10, 18, 255)
    
    draw_poly(draw, [v_top_center, v_left_lobe_top, v_left_crest], red_light, dark_rim)
    draw_poly(draw, [v_left_lobe_top, v_left_lobe_mid, v_left_crest], red_spec, dark_rim)
    draw_poly(draw, [v_left_lobe_mid, v_left_lobe_bot, v_left_crest], red_light, dark_rim)
    draw_poly(draw, [v_left_crest, v_left_lobe_bot, v_center_crest], red_mid, dark_rim)
    draw_poly(draw, [v_left_lobe_bot, v_tip, v_center_crest], red_mid, dark_rim)
    draw_poly(draw, [v_top_center, v_left_crest, v_center_crest], red_light, dark_rim)
    
    draw_poly(draw, [v_top_center, v_center_crest, v_right_crest], red_mid, dark_rim)
    draw_poly(draw, [v_top_center, v_right_crest, v_right_lobe_top], red_mid, dark_rim)
    draw_poly(draw, [v_right_crest, v_right_lobe_top, v_right_lobe_mid], red_dark, dark_rim)
    draw_poly(draw, [v_right_crest, v_right_lobe_mid, v_right_lobe_bot], red_dark, dark_rim)
    draw_poly(draw, [v_center_crest, v_right_crest, v_right_lobe_bot], red_dark, dark_rim)
    draw_poly(draw, [v_center_crest, v_right_lobe_bot, v_tip], shade(red_dark, 0.85), dark_rim)
    
    finalize_and_save(img, "icon_heart.png")

def render_icon_stamina():
    img = create_base_canvas()
    draw = ImageDraw.Draw(img)
    cx, cy = 64 * SUPERSAMPLE, 64 * SUPERSAMPLE
    s = SUPERSAMPLE
    
    green_light = (90, 240, 110, 255)
    green_mid = (40, 190, 65, 255)
    green_dark = (20, 120, 40, 255)
    green_shadow = (10, 75, 25, 255)
    edge = (15, 60, 20, 255)
    
    p_top = (cx + 8*s, cy - 38*s)
    p_left1 = (cx - 24*s, cy - 4*s)
    p_inner1 = (cx - 4*s, cy - 2*s)
    p_left2 = (cx - 20*s, cy + 24*s)
    p_tip = (cx + 6*s, cy + 38*s)
    p_right1 = (cx + 12*s, cy + 6*s)
    p_inner2 = (cx - 4*s, cy + 8*s)
    p_right2 = (cx + 26*s, cy - 16*s)
    
    dx, dy = 6*s, 6*s
    
    draw_poly(draw, [p_top, (p_top[0]+dx, p_top[1]+dy), (p_right2[0]+dx, p_right2[1]+dy), p_right2], green_shadow, edge)
    draw_poly(draw, [p_right2, (p_right2[0]+dx, p_right2[1]+dy), (p_inner2[0]+dx, p_inner2[1]+dy), p_inner2], green_dark, edge)
    draw_poly(draw, [p_inner2, (p_inner2[0]+dx, p_inner2[1]+dy), (p_right1[0]+dx, p_right1[1]+dy), p_right1], green_shadow, edge)
    draw_poly(draw, [p_right1, (p_right1[0]+dx, p_right1[1]+dy), (p_tip[0]+dx, p_tip[1]+dy), p_tip], green_shadow, edge)
    
    draw_poly(draw, [p_top, p_left1, p_inner1], green_light, edge)
    draw_poly(draw, [p_top, p_inner1, p_right2], green_mid, edge)
    draw_poly(draw, [p_inner1, p_left2, p_inner2], green_light, edge)
    draw_poly(draw, [p_inner1, p_inner2, p_right2], green_mid, edge)
    draw_poly(draw, [p_inner2, p_right1, p_tip], green_mid, edge)
    draw_poly(draw, [p_inner2, p_left2, p_tip], green_light, edge)
    
    finalize_and_save(img, "icon_stamina.png")

def render_icon_water():
    img = create_base_canvas()
    draw = ImageDraw.Draw(img)
    cx, cy = 64 * SUPERSAMPLE, 64 * SUPERSAMPLE
    s = SUPERSAMPLE
    
    v_tip = (cx, cy - 36*s)
    v_mid_left = (cx - 28*s, cy + 6*s)
    v_bot_left = (cx - 20*s, cy + 30*s)
    v_bot_mid = (cx, cy + 38*s)
    v_bot_right = (cx + 20*s, cy + 30*s)
    v_mid_right = (cx + 28*s, cy + 6*s)
    v_center = (cx - 4*s, cy + 10*s)
    
    cyan_spec = (180, 245, 255, 255)
    cyan_light = (85, 215, 245, 255)
    cyan_mid = (35, 160, 215, 255)
    cyan_dark = (15, 95, 165, 255)
    cyan_deep = (8, 60, 115, 255)
    edge = (10, 50, 95, 255)
    
    draw_poly(draw, [v_tip, v_mid_left, v_center], cyan_spec, edge)
    draw_poly(draw, [v_mid_left, v_bot_left, v_center], cyan_light, edge)
    draw_poly(draw, [v_bot_left, v_bot_mid, v_center], cyan_mid, edge)
    draw_poly(draw, [v_bot_mid, v_bot_right, v_center], cyan_dark, edge)
    draw_poly(draw, [v_bot_right, v_mid_right, v_center], cyan_deep, edge)
    draw_poly(draw, [v_mid_right, v_tip, v_center], cyan_dark, edge)
    
    finalize_and_save(img, "icon_water.png")

def render_icon_battery():
    img = create_base_canvas()
    draw = ImageDraw.Draw(img)
    cx, cy = 64 * SUPERSAMPLE, 64 * SUPERSAMPLE
    s = SUPERSAMPLE
    
    cap_cx, cap_cy = cx, cy - 26*s
    cap_w, cap_h = 12*s, 6*s
    cap_gold = (245, 195, 45, 255)
    cap_dark = (165, 115, 20, 255)
    draw_poly(draw, [
        (cap_cx - cap_w, cap_cy), (cap_cx, cap_cy - 4*s),
        (cap_cx + cap_w, cap_cy), (cap_cx + cap_w, cap_cy + cap_h),
        (cap_cx, cap_cy + cap_h + 4*s), (cap_cx - cap_w, cap_cy + cap_h)
    ], cap_gold, cap_dark)
    
    bw = 24*s
    top_y = cy - 20*s
    bot_y = cy + 28*s
    
    p_tl = (cx - bw, top_y + 4*s)
    p_tc = (cx, top_y + 10*s)
    p_tr = (cx + bw, top_y + 4*s)
    p_tback = (cx, top_y - 2*s)
    
    p_bl = (cx - bw, bot_y + 4*s)
    p_bc = (cx, bot_y + 10*s)
    p_br = (cx + bw, bot_y + 4*s)
    
    lid_color = (75, 85, 95, 255)
    draw_poly(draw, [p_tback, (cx - bw*0.6, top_y), p_tl, p_tc, p_tr, (cx + bw*0.6, top_y)], lid_color, (45, 50, 60, 255))
    
    green_light = (55, 205, 145, 255)
    green_dark = (15, 100, 65, 255)
    edge = (20, 45, 35, 255)
    
    draw_poly(draw, [p_tl, p_tc, p_bc, p_bl], green_light, edge)
    draw_poly(draw, [p_tc, p_tr, p_br, p_bc], green_dark, edge)
    
    pw, ph = 4*s, 12*s
    p_cy = cy + 5*s
    draw_poly(draw, [
        (cx - pw, p_cy - ph), (cx + pw, p_cy - ph),
        (cx + pw, p_cy + ph), (cx - pw, p_cy + ph)
    ], (255, 255, 255, 230))
    draw_poly(draw, [
        (cx - ph, p_cy - pw), (cx + ph, p_cy - pw),
        (cx + ph, p_cy + pw), (cx - ph, p_cy + pw)
    ], (255, 255, 255, 230))
    
    finalize_and_save(img, "icon_battery.png")

def render_icon_solar():
    img = create_base_canvas()
    draw = ImageDraw.Draw(img)
    cx, cy = 64 * SUPERSAMPLE, 64 * SUPERSAMPLE
    s = SUPERSAMPLE
    
    r_outer = 38 * s
    r_inner = 20 * s
    num_rays = 8
    
    amber_light = (255, 215, 75, 255)
    amber_mid = (245, 160, 30, 255)
    amber_dark = (190, 95, 15, 255)
    edge = (130, 60, 10, 255)
    
    for i in range(num_rays):
        a_center = i * (2 * math.pi / num_rays)
        a_left = a_center - 0.22
        a_right = a_center + 0.22
        
        tip = (cx + r_outer * math.cos(a_center), cy + r_outer * math.sin(a_center))
        base_l = (cx + r_inner * math.cos(a_left), cy + r_inner * math.sin(a_left))
        base_r = (cx + r_inner * math.cos(a_right), cy + r_inner * math.sin(a_right))
        
        draw_poly(draw, [tip, base_l, (cx, cy)], amber_light if math.cos(a_center) < 0.2 else amber_mid, edge)
        draw_poly(draw, [tip, base_r, (cx, cy)], amber_dark if math.cos(a_center) > -0.2 else amber_mid, edge)
        
    oct_pts = []
    for i in range(8):
        a = i * (2 * math.pi / 8) + 0.392
        oct_pts.append((cx + r_inner * math.cos(a), cy + r_inner * math.sin(a)))
        
    for i in range(8):
        p1 = oct_pts[i]
        p2 = oct_pts[(i+1)%8]
        dot = -0.707 * math.cos(i * 0.785) - 0.707 * math.sin(i * 0.785)
        c = shade(amber_mid, 0.85 + 0.35 * dot)
        draw_poly(draw, [p1, p2, (cx, cy)], c, edge)
        
    finalize_and_save(img, "icon_solar.png")

# ==============================================================================
# 2. REPAIRED CLUTTER ICONS (Genuine 3D low-poly branch, dirt clump, grass tuft)
# ==============================================================================

def render_clutter_branch():
    img = create_base_canvas()
    draw = ImageDraw.Draw(img)
    cx, cy = 64 * SUPERSAMPLE, 64 * SUPERSAMPLE
    s = SUPERSAMPLE
    
    wood_light = (165, 125, 80, 255)
    wood_mid = (130, 90, 50, 255)
    wood_dark = (90, 60, 32, 255)
    bark_edge = (60, 38, 20, 255)
    leaf_green = (80, 140, 50, 255)
    
    p1 = (cx - 36*s, cy + 24*s)
    p2 = (cx + 34*s, cy - 22*s)
    
    w_base = 8 * s
    w_tip = 4 * s
    
    trunk_top = [
        (p1[0] - w_base*0.5, p1[1] - w_base),
        (cx - 2*s, cy - 2*s - 6*s),
        (p2[0], p2[1] - w_tip),
        (p2[0], p2[1]),
        (cx - 2*s, cy - 2*s),
        (p1[0], p1[1])
    ]
    draw_poly(draw, trunk_top, wood_light, bark_edge)
    
    trunk_bot = [
        (p1[0], p1[1]),
        (cx - 2*s, cy - 2*s),
        (p2[0], p2[1]),
        (p2[0] + w_tip*0.7, p2[1] + w_tip*0.7),
        (cx - 2*s + 4*s, cy - 2*s + 6*s),
        (p1[0] + w_base*0.7, p1[1] + w_base*0.7)
    ]
    draw_poly(draw, trunk_bot, wood_dark, bark_edge)
    
    tw1_base = (cx - 12*s, cy + 6*s)
    tw1_tip = (cx - 24*s, cy - 16*s)
    draw_poly(draw, [tw1_base, (tw1_base[0]-3*s, tw1_base[1]-2*s), tw1_tip], wood_light, bark_edge)
    draw_poly(draw, [tw1_base, (tw1_base[0]+3*s, tw1_base[1]+2*s), tw1_tip], wood_mid, bark_edge)
    
    tw2_base = (cx + 14*s, cy - 10*s)
    tw2_tip = (cx + 30*s, cy + 6*s)
    draw_poly(draw, [tw2_base, (tw2_base[0]-2*s, tw2_base[1]+2*s), tw2_tip], wood_mid, bark_edge)
    draw_poly(draw, [tw2_base, (tw2_base[0]+2*s, tw2_base[1]-2*s), tw2_tip], wood_dark, bark_edge)
    
    draw_poly(draw, [(tw1_tip[0]-6*s, tw1_tip[1]-4*s), (tw1_tip[0]-2*s, tw1_tip[1]-8*s), tw1_tip], leaf_green, (40, 80, 25, 255))
    draw_poly(draw, [(p2[0]+4*s, p2[1]-6*s), (p2[0]+8*s, p2[1]-2*s), p2], leaf_green, (40, 80, 25, 255))

    finalize_and_save(img, "clutter_branch.png")

def render_clutter_dirt_clump():
    img = create_base_canvas()
    draw = ImageDraw.Draw(img)
    cx, cy = 64 * SUPERSAMPLE, 64 * SUPERSAMPLE
    s = SUPERSAMPLE
    
    dirt_light = (145, 105, 65, 255)
    dirt_mid = (115, 78, 48, 255)
    dirt_dark = (85, 54, 32, 255)
    dirt_shadow = (55, 34, 20, 255)
    edge = (45, 28, 15, 255)
    stone_gray = (155, 160, 165, 255)
    stone_dark = (105, 110, 115, 255)
    
    mound_pts = [
        (cx - 38*s, cy + 4*s), (cx - 24*s, cy - 16*s),
        (cx - 4*s, cy - 24*s), (cx + 20*s, cy - 20*s),
        (cx + 36*s, cy - 2*s), (cx + 32*s, cy + 18*s),
        (cx + 12*s, cy + 28*s), (cx - 18*s, cy + 26*s),
        (cx - 34*s, cy + 16*s)
    ]
    
    c1 = (cx - 8*s, cy - 4*s)
    c2 = (cx + 10*s, cy + 2*s)
    
    draw_poly(draw, [mound_pts[0], mound_pts[1], c1], dirt_light, edge)
    draw_poly(draw, [mound_pts[1], mound_pts[2], c1], dirt_light, edge)
    draw_poly(draw, [mound_pts[2], mound_pts[3], c1], dirt_light, edge)
    draw_poly(draw, [mound_pts[3], c2, c1], dirt_mid, edge)
    draw_poly(draw, [mound_pts[3], mound_pts[4], c2], dirt_mid, edge)
    draw_poly(draw, [mound_pts[4], mound_pts[5], c2], dirt_dark, edge)
    draw_poly(draw, [mound_pts[5], mound_pts[6], c2], dirt_shadow, edge)
    draw_poly(draw, [mound_pts[6], c1, c2], dirt_mid, edge)
    draw_poly(draw, [mound_pts[6], mound_pts[7], c1], dirt_mid, edge)
    draw_poly(draw, [mound_pts[7], mound_pts[8], c1], dirt_mid, edge)
    draw_poly(draw, [mound_pts[8], mound_pts[0], c1], dirt_light, edge)
    
    draw_poly(draw, [(cx-18*s, cy-2*s), (cx-12*s, cy-6*s), (cx-10*s, cy-1*s), (cx-16*s, cy+2*s)], stone_gray, edge)
    draw_poly(draw, [(cx+16*s, cy-8*s), (cx+22*s, cy-12*s), (cx+26*s, cy-6*s), (cx+20*s, cy-3*s)], stone_dark, edge)
    draw_poly(draw, [(cx+4*s, cy+14*s), (cx+10*s, cy+12*s), (cx+12*s, cy+16*s), (cx+6*s, cy+18*s)], stone_gray, edge)

    finalize_and_save(img, "clutter_dirt_clump.png")

def render_clutter_grass_tuft():
    img = create_base_canvas()
    draw = ImageDraw.Draw(img)
    cx, cy = 64 * SUPERSAMPLE, 64 * SUPERSAMPLE
    s = SUPERSAMPLE
    
    g_bright = (120, 215, 60, 255)
    g_mid = (85, 175, 45, 255)
    g_dark = (50, 125, 30, 255)
    edge = (25, 65, 15, 255)
    base = (cx, cy + 26*s)
    
    blades = [
        (cx - 30*s, cy - 14*s, 6*s, True),
        (cx - 18*s, cy - 32*s, 7*s, True),
        (cx - 4*s,  cy - 38*s, 8*s, True),
        (cx + 12*s, cy - 34*s, 7*s, False),
        (cx + 26*s, cy - 18*s, 6*s, False),
        (cx + 34*s, cy + 4*s,  5*s, False),
    ]
    
    for tip_x, tip_y, w, is_left in blades:
        tip = (tip_x, tip_y)
        b_left = (base[0] - w, base[1])
        b_right = (base[0] + w, base[1])
        mid_spine = ((tip_x + base[0])*0.5, (tip_y + base[1])*0.5)
        c_left = g_bright if is_left else g_mid
        c_right = g_mid if is_left else g_dark
        draw_poly(draw, [tip, b_left, mid_spine], c_left, edge)
        draw_poly(draw, [tip, mid_spine, b_right], c_right, edge)
        
    finalize_and_save(img, "clutter_grass_tuft.png")

# ==============================================================================
# 3. FISH SUITE (6 Species with Distinct Markings & Anatomy)
# ==============================================================================

def render_fish_mesh(filename, dorsal_color, flank_color, belly_color, fin_color, markings_func=None, barbels=False):
    img = create_base_canvas()
    draw = ImageDraw.Draw(img)
    cx, cy = 64 * SUPERSAMPLE, 64 * SUPERSAMPLE
    s = SUPERSAMPLE
    
    snout = (cx - 38*s, cy + 2*s)
    forehead = (cx - 24*s, cy - 12*s)
    dorsal_ridge = (cx - 4*s, cy - 18*s)
    dorsal_back = (cx + 16*s, cy - 12*s)
    caudal_peduncle_top = (cx + 28*s, cy - 4*s)
    caudal_peduncle_bot = (cx + 28*s, cy + 8*s)
    belly_curve = (cx - 2*s, cy + 18*s)
    throat = (cx - 20*s, cy + 14*s)
    
    lat_front = (cx - 16*s, cy + 2*s)
    lat_mid = (cx + 4*s, cy + 1*s)
    lat_back = (cx + 24*s, cy + 2*s)
    
    edge = shade(dorsal_color, 0.45)
    
    tail_top = (cx + 42*s, cy - 18*s)
    tail_fork = (cx + 36*s, cy + 2*s)
    tail_bot = (cx + 42*s, cy + 22*s)
    draw_poly(draw, [caudal_peduncle_top, tail_top, tail_fork], fin_color, edge)
    draw_poly(draw, [caudal_peduncle_bot, tail_fork, tail_bot], shade(fin_color, 0.85), edge)
    
    d_fin_peak = (cx + 6*s, cy - 30*s)
    draw_poly(draw, [dorsal_ridge, d_fin_peak, dorsal_back], fin_color, edge)
    
    a_fin_tip = (cx + 18*s, cy + 22*s)
    draw_poly(draw, [caudal_peduncle_bot, a_fin_tip, (cx + 14*s, cy + 14*s)], shade(fin_color, 0.85), edge)
    
    draw_poly(draw, [snout, forehead, lat_front], shade(dorsal_color, 1.15), edge)
    draw_poly(draw, [forehead, dorsal_ridge, lat_front], shade(dorsal_color, 1.1), edge)
    draw_poly(draw, [dorsal_ridge, dorsal_back, lat_mid], dorsal_color, edge)
    draw_poly(draw, [dorsal_ridge, lat_front, lat_mid], flank_color, edge)
    draw_poly(draw, [dorsal_back, caudal_peduncle_top, lat_back], dorsal_color, edge)
    draw_poly(draw, [dorsal_back, lat_mid, lat_back], flank_color, edge)
    
    draw_poly(draw, [snout, lat_front, throat], flank_color, edge)
    draw_poly(draw, [throat, lat_front, belly_curve], belly_color, edge)
    draw_poly(draw, [lat_front, lat_mid, belly_curve], belly_color, edge)
    draw_poly(draw, [lat_mid, lat_back, belly_curve], shade(belly_color, 0.9), edge)
    draw_poly(draw, [lat_back, caudal_peduncle_bot, belly_curve], shade(belly_color, 0.8), edge)
    
    pec_base = (cx - 10*s, cy + 8*s)
    pec_tip = (cx - 2*s, cy + 22*s)
    pec_rear = (cx + 2*s, cy + 10*s)
    draw_poly(draw, [pec_base, pec_tip, pec_rear], shade(fin_color, 1.1), edge)
    
    eye_pos = (cx - 22*s, cy - 2*s)
    draw.ellipse([eye_pos[0]-3*s, eye_pos[1]-3*s, eye_pos[0]+3*s, eye_pos[1]+3*s], fill=(255, 235, 120, 255), outline=edge)
    draw.ellipse([eye_pos[0]-1.5*s, eye_pos[1]-1.5*s, eye_pos[0]+1.5*s, eye_pos[1]+1.5*s], fill=(20, 20, 20, 255))
    draw.line([(cx - 14*s, cy - 8*s), (cx - 10*s, cy + 2*s), (cx - 12*s, cy + 12*s)], fill=edge, width=2*s)
    
    if markings_func:
        markings_func(draw, cx, cy, s)
        
    if barbels:
        barb_col = shade(dorsal_color, 0.6)
        draw.line([snout, (snout[0] - 10*s, snout[1] + 12*s)], fill=barb_col, width=2*s)
        draw.line([(snout[0]+4*s, snout[1]+4*s), (snout[0] - 6*s, snout[1] + 18*s)], fill=barb_col, width=2*s)
        draw.line([(snout[0]+6*s, snout[1]-4*s), (snout[0] - 2*s, snout[1] - 14*s)], fill=barb_col, width=2*s)
        
    finalize_and_save(img, filename)

def render_fish_suite():
    def bass_markings(draw, cx, cy, s):
        band_col = (45, 65, 30, 240)
        draw_poly(draw, [(cx-14*s, cy+2*s), (cx+4*s, cy+1*s), (cx+22*s, cy+2*s), (cx+4*s, cy+5*s)], band_col)
    render_fish_mesh("fish_bass.png", (75, 115, 55, 255), (120, 155, 80, 255), (230, 235, 185, 255), (145, 160, 95, 255), bass_markings)
    
    def salmon_markings(draw, cx, cy, s):
        spot_col = (40, 50, 65, 255)
        for dx, dy in [(-8, -10), (0, -12), (10, -8), (-2, -6), (6, -4), (16, -6)]:
            draw.ellipse([cx+dx*s-1.5*s, cy+dy*s-1.5*s, cx+dx*s+1.5*s, cy+dy*s+1.5*s], fill=spot_col)
    render_fish_mesh("fish_salmon.png", (65, 95, 125, 255), (225, 120, 110, 255), (225, 230, 235, 255), (110, 135, 160, 255), salmon_markings)
    
    def trout_markings(draw, cx, cy, s):
        stripe_col = (235, 80, 140, 240)
        draw_poly(draw, [(cx-14*s, cy+2*s), (cx+4*s, cy+1*s), (cx+24*s, cy+2*s), (cx+4*s, cy+6*s)], stripe_col)
        spot_col = (35, 45, 30, 255)
        for dx, dy in [(-12, -8), (-4, -12), (4, -10), (12, -7), (-6, -4), (2, -3), (14, -2)]:
            draw.ellipse([cx+dx*s-1.5*s, cy+dy*s-1.5*s, cx+dx*s+1.5*s, cy+dy*s+1.5*s], fill=spot_col)
    render_fish_mesh("fish_trout.png", (95, 115, 65, 255), (155, 165, 110, 255), (230, 235, 220, 255), (165, 140, 115, 255), trout_markings)
    
    render_fish_mesh("fish_catfish.png", (60, 75, 90, 255), (105, 120, 135, 255), (220, 225, 230, 255), (85, 95, 110, 255), barbels=True)
    
    def walleye_markings(draw, cx, cy, s):
        bar_col = (55, 65, 30, 200)
        for bx in [-6, 6, 16]:
            draw_poly(draw, [(cx+bx*s-2*s, cy-14*s), (cx+bx*s+3*s, cy-12*s), (cx+bx*s+1*s, cy+6*s), (cx+bx*s-3*s, cy+4*s)], bar_col)
    render_fish_mesh("fish_walleye.png", (110, 115, 45, 255), (185, 175, 75, 255), (240, 240, 210, 255), (145, 135, 65, 255), walleye_markings)
    
    def crappie_markings(draw, cx, cy, s):
        speck = (30, 45, 35, 230)
        for dx, dy in [(-10, -6), (-4, -10), (2, -14), (8, -8), (-6, 0), (0, 2), (8, -2), (14, 0), (-2, 8), (4, 10)]:
            draw.ellipse([cx+dx*s-2*s, cy+dy*s-2*s, cx+dx*s+2*s, cy+dy*s+2*s], fill=speck)
    render_fish_mesh("fish_crappie.png", (70, 95, 80, 255), (150, 175, 160, 255), (230, 238, 235, 255), (120, 145, 130, 255), crappie_markings)

# ==============================================================================
# 4. FISH FILLETS & STEAKS (Food Category - 6 Varieties)
# ==============================================================================

def render_fillet(filename, meat_color, skin_color, fat_lines=False):
    img = create_base_canvas()
    draw = ImageDraw.Draw(img)
    cx, cy = 64 * SUPERSAMPLE, 64 * SUPERSAMPLE
    s = SUPERSAMPLE
    
    thickness = 8 * s
    edge = shade(meat_color, 0.45)
    
    p_front = (cx - 36*s, cy + 8*s)
    p_top_l = (cx - 18*s, cy - 18*s)
    p_top_r = (cx + 20*s, cy - 20*s)
    p_tail = (cx + 38*s, cy - 2*s)
    p_bot_r = (cx + 24*s, cy + 18*s)
    p_bot_l = (cx - 14*s, cy + 22*s)
    
    skin_pts = [
        p_front, (p_front[0], p_front[1] + thickness),
        (p_bot_l[0], p_bot_l[1] + thickness), p_bot_l
    ]
    draw_poly(draw, skin_pts, skin_color, (30, 35, 40, 255))
    skin_pts2 = [
        p_bot_l, (p_bot_l[0], p_bot_l[1] + thickness),
        (p_bot_r[0], p_bot_r[1] + thickness), p_bot_r
    ]
    draw_poly(draw, skin_pts2, shade(skin_color, 0.85), (30, 35, 40, 255))
    skin_pts3 = [
        p_bot_r, (p_bot_r[0], p_bot_r[1] + thickness),
        (p_tail[0], p_tail[1] + thickness), p_tail
    ]
    draw_poly(draw, skin_pts3, shade(skin_color, 0.7), (30, 35, 40, 255))
    
    c_mid = (cx + 2*s, cy)
    draw_poly(draw, [p_front, p_top_l, c_mid], shade(meat_color, 1.15), edge)
    draw_poly(draw, [p_top_l, p_top_r, c_mid], shade(meat_color, 1.05), edge)
    draw_poly(draw, [p_top_r, p_tail, c_mid], meat_color, edge)
    draw_poly(draw, [p_tail, p_bot_r, c_mid], shade(meat_color, 0.9), edge)
    draw_poly(draw, [p_bot_r, p_bot_l, c_mid], shade(meat_color, 0.85), edge)
    draw_poly(draw, [p_bot_l, p_front, c_mid], shade(meat_color, 0.95), edge)
    
    if fat_lines:
        fat_col = (255, 240, 235, 230)
        for offset in [-12, -2, 8, 18]:
            lx = cx + offset * s
            draw.line([(lx - 12*s, cy + 12*s), (lx + 8*s, cy - 14*s)], fill=fat_col, width=2*s)
            
    finalize_and_save(img, filename)

def render_fillet_suite():
    render_fillet("fillet_bass.png", (238, 235, 225, 255), (105, 115, 110, 255))
    render_fillet("fillet_salmon.png", (250, 115, 80, 255), (65, 80, 95, 255), fat_lines=True)
    render_fillet("fillet_trout.png", (245, 155, 140, 255), (95, 105, 90, 255))
    render_fillet("fillet_catfish.png", (245, 245, 240, 255), (75, 85, 100, 255))
    render_fillet("fillet_walleye.png", (242, 238, 228, 255), (135, 125, 70, 255))
    render_fillet("fillet_crappie.png", (240, 242, 238, 255), (85, 105, 95, 255))

# ==============================================================================
# 5. MEATS, PELTS, FEATHERS & FISHING GEAR
# ==============================================================================

def render_meat_beef():
    img = create_base_canvas()
    draw = ImageDraw.Draw(img)
    cx, cy = 64 * SUPERSAMPLE, 64 * SUPERSAMPLE
    s = SUPERSAMPLE
    
    meat_red = (185, 38, 48, 255)
    fat_cream = (245, 240, 220, 255)
    bone_white = (250, 250, 245, 255)
    edge = (90, 18, 25, 255)
    
    draw_poly(draw, [
        (cx - 32*s, cy - 20*s), (cx - 10*s, cy - 28*s),
        (cx + 24*s, cy - 22*s), (cx + 34*s, cy - 6*s),
        (cx + 28*s, cy + 18*s), (cx + 4*s, cy + 26*s),
        (cx - 24*s, cy + 20*s), (cx - 36*s, cy + 2*s)
    ], fat_cream, (150, 140, 120, 255))
    
    draw_poly(draw, [
        (cx - 28*s, cy - 16*s), (cx - 8*s, cy - 22*s),
        (cx + 20*s, cy - 16*s), (cx + 28*s, cy - 4*s),
        (cx + 22*s, cy + 14*s), (cx + 2*s, cy + 20*s),
        (cx - 20*s, cy + 14*s), (cx - 30*s, cy)
    ], meat_red, edge)
    
    draw_poly(draw, [
        (cx - 4*s, cy - 18*s), (cx + 4*s, cy - 18*s),
        (cx + 2*s, cy + 16*s), (cx - 2*s, cy + 16*s)
    ], bone_white, (180, 175, 160, 255))
    
    finalize_and_save(img, "meat_beef.png")

def render_meat_chicken():
    img = create_base_canvas()
    draw = ImageDraw.Draw(img)
    cx, cy = 64 * SUPERSAMPLE, 64 * SUPERSAMPLE
    s = SUPERSAMPLE
    
    pink_light = (245, 175, 165, 255)
    pink_mid = (225, 145, 135, 255)
    pink_dark = (195, 115, 105, 255)
    bone_col = (245, 245, 235, 255)
    edge = (140, 65, 55, 255)
    
    draw_poly(draw, [
        (cx - 28*s, cy - 22*s), (cx - 8*s, cy - 28*s),
        (cx + 10*s, cy - 16*s), (cx + 6*s, cy + 6*s),
        (cx - 14*s, cy + 10*s), (cx - 30*s, cy - 6*s)
    ], pink_light, edge)
    draw_poly(draw, [
        (cx - 30*s, cy - 6*s), (cx - 14*s, cy + 10*s),
        (cx - 2*s, cy + 14*s), (cx - 18*s, cy + 18*s)
    ], pink_dark, edge)
    
    draw_poly(draw, [
        (cx + 2*s, cy + 4*s), (cx + 26*s, cy + 22*s),
        (cx + 22*s, cy + 28*s), (cx - 4*s, cy + 12*s)
    ], bone_col, (160, 155, 145, 255))
    draw.ellipse([(cx+22*s), (cy+16*s), (cx+34*s), (cy+28*s)], fill=bone_col, outline=(160, 155, 145, 255))
    draw.ellipse([(cx+18*s), (cy+24*s), (cx+30*s), (cy+36*s)], fill=bone_col, outline=(160, 155, 145, 255))
    
    finalize_and_save(img, "meat_chicken.png")

def render_meat_pork():
    img = create_base_canvas()
    draw = ImageDraw.Draw(img)
    cx, cy = 64 * SUPERSAMPLE, 64 * SUPERSAMPLE
    s = SUPERSAMPLE
    
    pork_pink = (245, 145, 145, 255)
    fat_white = (250, 245, 235, 255)
    bone_col = (240, 240, 230, 255)
    edge = (160, 75, 75, 255)
    
    draw_poly(draw, [
        (cx - 30*s, cy - 22*s), (cx + 8*s, cy - 26*s),
        (cx + 32*s, cy - 10*s), (cx + 22*s, cy + 18*s),
        (cx - 12*s, cy + 24*s), (cx - 32*s, cy + 4*s)
    ], fat_white, (160, 150, 135, 255))
    draw_poly(draw, [
        (cx - 24*s, cy - 16*s), (cx + 4*s, cy - 20*s),
        (cx + 24*s, cy - 6*s), (cx + 16*s, cy + 14*s),
        (cx - 8*s, cy + 18*s), (cx - 26*s, cy)
    ], pork_pink, edge)
    draw_poly(draw, [
        (cx - 32*s, cy - 2*s), (cx - 34*s, cy + 16*s),
        (cx - 26*s, cy + 18*s), (cx - 24*s, cy)
    ], bone_col, (150, 140, 130, 255))
    
    finalize_and_save(img, "meat_pork.png")

def render_meat_mutton():
    img = create_base_canvas()
    draw = ImageDraw.Draw(img)
    cx, cy = 64 * SUPERSAMPLE, 64 * SUPERSAMPLE
    s = SUPERSAMPLE
    
    meat_col = (160, 25, 40, 255)
    fat_col = (245, 240, 220, 255)
    bone_col = (240, 240, 235, 255)
    edge = (80, 15, 20, 255)
    
    draw_poly(draw, [(cx-26*s, cy-22*s), (cx+16*s, cy-24*s), (cx+30*s, cy-4*s), (cx+18*s, cy+20*s), (cx-18*s, cy+22*s)], fat_col, (140, 130, 115, 255))
    draw_poly(draw, [(cx-20*s, cy-16*s), (cx+10*s, cy-18*s), (cx+22*s, cy-2*s), (cx+12*s, cy+14*s), (cx-12*s, cy+16*s)], meat_col, edge)
    draw_poly(draw, [(cx-26*s, cy+6*s), (cx-34*s, cy+26*s), (cx-26*s, cy+28*s), (cx-18*s, cy+10*s)], bone_col, (150, 140, 130, 255))
    
    finalize_and_save(img, "meat_mutton.png")

def render_meat_goat():
    img = create_base_canvas()
    draw = ImageDraw.Draw(img)
    cx, cy = 64 * SUPERSAMPLE, 64 * SUPERSAMPLE
    s = SUPERSAMPLE
    
    meat_col = (145, 30, 35, 255)
    fat_col = (240, 235, 215, 255)
    edge = (75, 12, 18, 255)
    
    draw_poly(draw, [(cx-28*s, cy-18*s), (cx+12*s, cy-26*s), (cx+32*s, cy-8*s), (cx+20*s, cy+18*s), (cx-16*s, cy+24*s)], fat_col, (130, 120, 105, 255))
    draw_poly(draw, [(cx-22*s, cy-12*s), (cx+6*s, cy-18*s), (cx+24*s, cy-4*s), (cx+14*s, cy+12*s), (cx-10*s, cy+16*s)], meat_col, edge)
    
    finalize_and_save(img, "meat_goat.png")

def render_materials_pelts():
    # 1. Bird Down Feather
    img = create_base_canvas()
    draw = ImageDraw.Draw(img)
    cx, cy = 64 * SUPERSAMPLE, 64 * SUPERSAMPLE
    s = SUPERSAMPLE
    
    quill_col = (250, 250, 240, 255)
    vane_light = (240, 245, 250, 255)
    vane_dark = (195, 205, 215, 255)
    edge = (140, 150, 160, 255)
    
    draw.line([(cx - 26*s, cy + 32*s), (cx + 26*s, cy - 32*s)], fill=quill_col, width=3*s)
    draw_poly(draw, [
        (cx + 26*s, cy - 32*s), (cx + 10*s, cy - 34*s),
        (cx - 8*s, cy - 20*s), (cx - 20*s, cy + 4*s),
        (cx - 16*s, cy + 20*s), (cx - 14*s, cy + 18*s)
    ], vane_light, edge)
    draw_poly(draw, [
        (cx + 26*s, cy - 32*s), (cx + 28*s, cy - 18*s),
        (cx + 22*s, cy + 4*s), (cx + 8*s, cy + 22*s),
        (cx - 4*s, cy + 24*s), (cx + 6*s, cy - 4*s)
    ], vane_dark, edge)
    finalize_and_save(img, "mat_feather.png")
    
    # 2. Cow Pelt
    img = create_base_canvas()
    draw = ImageDraw.Draw(img)
    p_white = (245, 245, 240, 255)
    p_black = (40, 40, 42, 255)
    p_suede = (165, 125, 85, 255)
    edge = (60, 45, 30, 255)
    draw_poly(draw, [(cx-28*s, cy-12*s), (cx+16*s, cy-24*s), (cx+32*s, cy+6*s), (cx-12*s, cy+20*s)], p_white, edge)
    draw_poly(draw, [(cx-28*s, cy-12*s), (cx-12*s, cy+20*s), (cx-12*s, cy+28*s), (cx-28*s, cy-4*s)], p_suede, edge)
    draw_poly(draw, [(cx-12*s, cy+20*s), (cx+32*s, cy+6*s), (cx+32*s, cy+14*s), (cx-12*s, cy+28*s)], shade(p_suede, 0.8), edge)
    draw_poly(draw, [(cx-18*s, cy-8*s), (cx-2*s, cy-14*s), (cx+2*s, cy-4*s), (cx-12*s, cy+4*s)], p_black)
    draw_poly(draw, [(cx+12*s, cy-16*s), (cx+24*s, cy-18*s), (cx+26*s, cy-8*s), (cx+16*s, cy-6*s)], p_black)
    finalize_and_save(img, "pelt_cow.png")
    
    # 3. Sheep Pelt
    img = create_base_canvas()
    draw = ImageDraw.Draw(img)
    w_light = (250, 248, 240, 255)
    w_mid = (225, 220, 205, 255)
    w_dark = (185, 178, 160, 255)
    draw_poly(draw, [(cx-30*s, cy-10*s), (cx+12*s, cy-22*s), (cx+30*s, cy+8*s), (cx-12*s, cy+22*s)], w_light, (120, 115, 100, 255))
    draw_poly(draw, [(cx-30*s, cy-10*s), (cx-12*s, cy+22*s), (cx-12*s, cy+30*s), (cx-30*s, cy-2*s)], w_mid, (120, 115, 100, 255))
    draw_poly(draw, [(cx-12*s, cy+22*s), (cx+30*s, cy+8*s), (cx+30*s, cy+16*s), (cx-12*s, cy+30*s)], w_dark, (120, 115, 100, 255))
    finalize_and_save(img, "pelt_sheep.png")
    
    # 4. Goat Pelt
    img = create_base_canvas()
    draw = ImageDraw.Draw(img)
    g_fur = (145, 95, 55, 255)
    g_suede = (195, 155, 110, 255)
    draw_poly(draw, [(cx-28*s, cy-12*s), (cx+16*s, cy-24*s), (cx+32*s, cy+6*s), (cx-12*s, cy+20*s)], g_fur, (70, 45, 25, 255))
    draw_poly(draw, [(cx-28*s, cy-12*s), (cx-12*s, cy+20*s), (cx-12*s, cy+28*s), (cx-28*s, cy-4*s)], g_suede, (70, 45, 25, 255))
    draw_poly(draw, [(cx-12*s, cy+20*s), (cx+32*s, cy+6*s), (cx+32*s, cy+14*s), (cx-12*s, cy+28*s)], shade(g_suede, 0.8), (70, 45, 25, 255))
    finalize_and_save(img, "pelt_goat.png")

def render_fishing_gear():
    # 1. Fishing Bait
    img = create_base_canvas()
    draw = ImageDraw.Draw(img)
    cx, cy = 64 * SUPERSAMPLE, 64 * SUPERSAMPLE
    s = SUPERSAMPLE
    
    tin_silver = (185, 195, 205, 255)
    tin_dark = (115, 125, 135, 255)
    worm_pink = (235, 125, 115, 255)
    dirt_brown = (95, 65, 40, 255)
    edge = (60, 65, 75, 255)
    
    draw_poly(draw, [
        (cx - 28*s, cy - 8*s), (cx, cy - 18*s),
        (cx + 28*s, cy - 8*s), (cx + 28*s, cy + 16*s),
        (cx, cy + 26*s), (cx - 28*s, cy + 16*s)
    ], tin_silver, edge)
    draw_poly(draw, [
        (cx, cy - 18*s), (cx + 28*s, cy - 8*s),
        (cx + 28*s, cy + 16*s), (cx, cy + 26*s)
    ], tin_dark, edge)
    draw.ellipse([(cx-24*s), (cy-16*s), (cx+24*s), (cy-2*s)], fill=dirt_brown, outline=edge)
    draw.line([(cx-12*s, cy-8*s), (cx-4*s, cy-12*s), (cx+8*s, cy-6*s), (cx+16*s, cy-10*s)], fill=worm_pink, width=3*s)
    draw.line([(cx-16*s, cy-12*s), (cx-6*s, cy-6*s), (cx+4*s, cy-10*s)], fill=shade(worm_pink, 0.9), width=3*s)
    finalize_and_save(img, "fishing_bait.png")
    
    # 2. Fishing Lure
    img = create_base_canvas()
    draw = ImageDraw.Draw(img)
    gold_spoon = (245, 210, 50, 255)
    gold_dark = (165, 130, 20, 255)
    red_feather = (235, 40, 45, 255)
    steel_hook = (170, 175, 180, 255)
    
    draw_poly(draw, [(cx-26*s, cy-22*s), (cx-6*s, cy-28*s), (cx+8*s, cy-12*s), (cx-10*s, cy-4*s)], gold_spoon, gold_dark)
    draw_poly(draw, [(cx-10*s, cy-4*s), (cx+8*s, cy-12*s), (cx+4*s, cy-6*s), (cx-8*s, cy+2*s)], gold_dark, gold_dark)
    draw.line([(cx-26*s, cy-22*s), (cx-32*s, cy-28*s)], fill=steel_hook, width=2*s)
    draw_poly(draw, [(cx, cy), (cx+28*s, cy+22*s), (cx+22*s, cy+28*s), (cx-4*s, cy+6*s)], red_feather, (120, 20, 25, 255))
    draw.line([(cx+22*s, cy+28*s), (cx+32*s, cy+32*s), (cx+28*s, cy+38*s)], fill=steel_hook, width=2*s)
    finalize_and_save(img, "fishing_lure.png")

if __name__ == "__main__":
    print("=== Generating 3D Low-Poly Faceted UI Icons ===")
    render_icon_coin()
    render_icon_heart()
    render_icon_stamina()
    render_icon_water()
    render_icon_battery()
    render_icon_solar()

    print("\n=== Generating Repaired Clutter Icons ===")
    render_clutter_branch()
    render_clutter_dirt_clump()
    render_clutter_grass_tuft()

    print("\n=== Generating 6-Species Fish Suite ===")
    render_fish_suite()

    print("\n=== Generating 6-Species Fish Fillet Suite ===")
    render_fillet_suite()

    print("\n=== Generating Meats, Pelts, Feather & Fishing Gear ===")
    render_meat_beef()
    render_meat_chicken()
    render_meat_pork()
    render_meat_mutton()
    render_meat_goat()
    render_materials_pelts()
    render_fishing_gear()

    print("\nALL SPECIAL ICONS SUCCESSFULLY GENERATED & DEPLOYED!")

