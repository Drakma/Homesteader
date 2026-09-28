import cv2
import numpy as np

# We want to create weather_blizzard.png matching the prompt's provided image:
# Low-poly faceted volumetric cumulus storm cloud in icy cyan-blue shades (#7EA8C9, #A4C6DE, #D0E4F2),
# with swirling wind ribbon curls sweeping to the right, faceted crystalline snowflakes floating around it,
# snow drifts accumulating at the base with small icy geometric facets,
# and rendered with clean transparent alpha on 128x128 RGBA (standard Homesteader icon spec).

w, h = 128, 128
img = np.zeros((h, w, 4), dtype=np.uint8)

# Let's create an artistic faceted low-poly render of the blizzard cloud and snow gusts
# 1. Base cloud low-poly facets
facets = [
    # Top central dome
    ([(56, 16), (72, 14), (64, 28)], (225, 240, 252, 255)),
    ([(56, 16), (64, 28), (48, 30)], (190, 218, 242, 255)),
    ([(72, 14), (82, 22), (64, 28)], (210, 230, 248, 255)),
    ([(82, 22), (86, 36), (64, 28)], (175, 208, 238, 255)),
    ([(64, 28), (86, 36), (76, 48)], (150, 190, 228, 255)),
    ([(48, 30), (64, 28), (52, 46)], (165, 200, 232, 255)),
    ([(52, 46), (64, 28), (76, 48)], (180, 212, 240, 255)),

    # Right cloud dome
    ([(82, 22), (96, 20), (86, 36)], (215, 232, 250, 255)),
    ([(96, 20), (108, 32), (98, 42)], (195, 220, 245, 255)),
    ([(96, 20), (98, 42), (86, 36)], (180, 210, 240, 255)),
    ([(98, 42), (114, 48), (102, 60)], (160, 195, 232, 255)),
    ([(86, 36), (98, 42), (88, 56)], (145, 185, 225, 255)),
    ([(98, 42), (102, 60), (88, 56)], (130, 172, 215, 255)),
    ([(102, 60), (112, 68), (96, 76)], (150, 185, 222, 255)),
    ([(88, 56), (102, 60), (96, 76)], (135, 175, 216, 255)),

    # Left cloud dome
    ([(48, 30), (36, 34), (40, 48)], (195, 220, 245, 255)),
    ([(36, 34), (26, 46), (38, 58)], (175, 205, 235, 255)),
    ([(36, 34), (48, 30), (52, 46)], (185, 212, 240, 255)),
    ([(36, 34), (38, 58), (48, 62)], (160, 195, 230, 255)),
    ([(40, 48), (52, 46), (48, 62)], (145, 185, 222, 255)),
    ([(26, 46), (22, 62), (34, 72)], (140, 180, 220, 255)),
    ([(26, 46), (34, 72), (38, 58)], (155, 190, 228, 255)),
    ([(22, 62), (24, 78), (34, 72)], (120, 165, 210, 255)),

    # Central mid & lower body
    ([(48, 62), (52, 46), (76, 48)], (150, 190, 228, 255)),
    ([(48, 62), (76, 48), (68, 66)], (130, 175, 218, 255)),
    ([(76, 48), (88, 56), (82, 70)], (120, 165, 210, 255)),
    ([(76, 48), (82, 70), (68, 66)], (140, 182, 222, 255)),
    ([(38, 58), (48, 62), (44, 76)], (135, 175, 215, 255)),
    ([(34, 72), (38, 58), (44, 76)], (125, 168, 210, 255)),
    ([(48, 62), (68, 66), (56, 80)], (115, 160, 205, 255)),
    ([(44, 76), (48, 62), (56, 80)], (125, 170, 212, 255)),
    ([(68, 66), (82, 70), (74, 82)], (110, 155, 202, 255)),
    ([(56, 80), (68, 66), (74, 82)], (120, 165, 210, 255)),
    ([(82, 70), (96, 76), (86, 84)], (125, 170, 214, 255)),
    ([(74, 82), (82, 70), (86, 84)], (115, 160, 205, 255)),
    ([(34, 72), (44, 76), (36, 86)], (110, 155, 200, 255)),
    ([(44, 76), (56, 80), (48, 88)], (115, 160, 205, 255)),

    # Bottom snow drift base
    ([(18, 88), (36, 84), (28, 96)], (210, 228, 245, 255)),
    ([(36, 84), (54, 86), (46, 98)], (225, 240, 252, 255)),
    ([(54, 86), (74, 86), (66, 100)], (235, 245, 255, 255)),
    ([(74, 86), (94, 84), (86, 98)], (220, 236, 250, 255)),
    ([(94, 84), (112, 88), (104, 96)], (205, 225, 242, 255)),
    ([(28, 96), (46, 98), (38, 104)], (195, 218, 240, 255)),
    ([(46, 98), (66, 100), (58, 106)], (215, 232, 250, 255)),
    ([(66, 100), (86, 98), (76, 106)], (210, 230, 248, 255)),
    ([(86, 98), (104, 96), (94, 104)], (190, 215, 238, 255)),
]

for pts, col in facets:
    poly = np.array(pts, dtype=np.int32)
    cv2.fillPoly(img, [poly], col)

# Draw elegant swirling wind gusts (ribbon curves) sweeping rightward
# Upper swirl
pts_upper_swirl = [
    (58, 44), (66, 42), (76, 42), (86, 44), (94, 40), (100, 34), (98, 28), (92, 30), (96, 36), (88, 48), (78, 48), (64, 48)
]
cv2.fillPoly(img, [np.array(pts_upper_swirl, dtype=np.int32)], (240, 248, 255, 255))

# Mid sweeping swirl
pts_mid_swirl = [
    (50, 54), (62, 50), (74, 48), (88, 52), (102, 50), (110, 44), (108, 38), (104, 42), (98, 54), (84, 56), (70, 56), (56, 58)
]
cv2.fillPoly(img, [np.array(pts_mid_swirl, dtype=np.int32)], (245, 250, 255, 255))

# Lower big spiral curl
pts_lower_curl = [
    (42, 66), (54, 62), (70, 60), (84, 62), (96, 68), (104, 64), (106, 56), (98, 58), (92, 66), (80, 68), (64, 68), (48, 72)
]
cv2.fillPoly(img, [np.array(pts_lower_curl, dtype=np.int32)], (245, 250, 255, 255))

# Bottom ground gust
pts_ground_gust = [
    (38, 78), (52, 74), (68, 72), (82, 76), (92, 74), (90, 70), (80, 72), (64, 76), (46, 80)
]
cv2.fillPoly(img, [np.array(pts_ground_gust, dtype=np.int32)], (235, 245, 255, 255))

# Add faceted 6-pointed snowflakes
def draw_faceted_snowflake(cx, cy, r, col):
    for i in range(6):
        ang = i * np.pi / 3.0
        x1 = int(cx + r * np.cos(ang))
        y1 = int(cy + r * np.sin(ang))
        cv2.line(img, (cx, cy), (x1, y1), col, 2, cv2.LINE_AA)
        # Small facet diamond at tip
        p_tip = np.array([
            (x1, y1),
            (int(x1 - 1.5 * np.cos(ang + 0.8)), int(y1 - 1.5 * np.sin(ang + 0.8))),
            (int(x1 + 2.5 * np.cos(ang)), int(y1 + 2.5 * np.sin(ang))),
            (int(x1 - 1.5 * np.cos(ang - 0.8)), int(y1 - 1.5 * np.sin(ang - 0.8)))
        ], dtype=np.int32)
        cv2.fillPoly(img, [p_tip], col)

draw_faceted_snowflake(30, 48, 6.5, (245, 250, 255, 255))
draw_faceted_snowflake(40, 32, 5.0, (230, 242, 255, 255))
draw_faceted_snowflake(62, 34, 6.0, (245, 250, 255, 255))
draw_faceted_snowflake(46, 68, 7.5, (255, 255, 255, 255))
draw_faceted_snowflake(32, 76, 5.5, (235, 245, 255, 255))
draw_faceted_snowflake(80, 30, 5.0, (230, 242, 255, 255))
draw_faceted_snowflake(106, 72, 4.5, (245, 250, 255, 255))

# Soft crisp anti-aliasing / smoothing
# Save as 128x128 RGBA icon
out_icon = r"Homesteader\Assets\Resources\HUDTree\KitSprites\weather\weather_blizzard.png"
cv2.imwrite(out_icon, img)
print("Saved weather_blizzard.png successfully!")
