import os
from PIL import Image, ImageDraw, ImageFont

_this_dir = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(_this_dir) if os.path.basename(_this_dir) == chr(115)+chr(99)+chr(114)+chr(105)+chr(112)+chr(116)+chr(115) else _this_dir
PNG_DIR = os.path.join(BASE_DIR, "assets", "png")
os.makedirs(PNG_DIR, exist_ok=True)

SCALE = 4  # 4x supersampling for ultra-crisp anti-aliased low-poly rendering

def draw_supersampled(size, draw_fn):
    w, h = size
    big_img = Image.new("RGBA", (w * SCALE, h * SCALE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(big_img)
    draw_fn(draw, SCALE)
    return big_img.resize((w, h), Image.Resampling.LANCZOS)

# 1. Heart Icon (64x64)
def draw_heart(draw, S):
    # Base low-poly ruby heart facets
    def P(pts): return [(x * S, y * S) for x, y in pts]
    draw.polygon(P([(32,18), (20,8), (32,9)]), fill="#ff4d6d")
    draw.polygon(P([(32,18), (32,9), (44,8)]), fill="#ff758f")
    draw.polygon(P([(20,8), (10,18), (20,24)]), fill="#e01a4f")
    draw.polygon(P([(20,8), (20,24), (32,18)]), fill="#ff4d6d")
    draw.polygon(P([(44,8), (32,18), (44,24)]), fill="#ff597b")
    draw.polygon(P([(44,8), (44,24), (54,18)]), fill="#e01a4f")
    draw.polygon(P([(10,18), (10,34), (20,24)]), fill="#c9184a")
    draw.polygon(P([(20,24), (10,34), (22,38)]), fill="#a8132e")
    draw.polygon(P([(20,24), (22,38), (32,32)]), fill="#d90429")
    draw.polygon(P([(20,24), (32,32), (32,18)]), fill="#ef233c")
    draw.polygon(P([(32,18), (32,32), (42,38)]), fill="#ff4d6d")
    draw.polygon(P([(32,18), (42,38), (44,24)]), fill="#ff758f")
    draw.polygon(P([(44,24), (42,38), (54,34)]), fill="#a8132e")
    draw.polygon(P([(44,24), (54,34), (54,18)]), fill="#c9184a")
    draw.polygon(P([(10,34), (32,58), (22,38)]), fill="#800f2f")
    draw.polygon(P([(22,38), (32,58), (32,44)]), fill="#a8132e")
    draw.polygon(P([(22,38), (32,44), (32,32)]), fill="#c9184a")
    draw.polygon(P([(32,32), (32,44), (42,38)]), fill="#c9184a")
    draw.polygon(P([(42,38), (32,44), (32,58)]), fill="#a8132e")
    draw.polygon(P([(42,38), (32,58), (54,34)]), fill="#590d22")
    draw.polygon(P([(18,14), (24,12), (20,20)]), fill="#ffffff")

draw_supersampled((64, 64), draw_heart).save(os.path.join(PNG_DIR, "icon_heart.png"))

# 2. Stamina Bolt Icon (64x64)
def draw_stamina(draw, S):
    def P(pts): return [(x * S, y * S) for x, y in pts]
    draw.polygon(P([(38,4), (27,19), (33,26)]), fill="#9bf6ff")
    draw.polygon(P([(38,4), (33,26), (48,26)]), fill="#00f5d4")
    draw.polygon(P([(38,4), (16,34), (27,19)]), fill="#cbf3f0")
    draw.polygon(P([(27,19), (16,34), (31,34)]), fill="#00bbf9")
    draw.polygon(P([(31,34), (22,60), (35,43)]), fill="#00f5d4")
    draw.polygon(P([(31,34), (35,43), (48,26)]), fill="#00bbf9")
    draw.polygon(P([(35,43), (22,60), (42,36)]), fill="#007f7a")
    draw.polygon(P([(35,8), (30,19), (36,18)]), fill="#ffffff")

draw_supersampled((64, 64), draw_stamina).save(os.path.join(PNG_DIR, "icon_stamina.png"))

# 3. Gold Coin Icon (64x64)
def draw_coin(draw, S):
    def P(pts): return [(x * S, y * S) for x, y in pts]
    draw.polygon(P([(20,4), (44,4), (40,11), (24,11)]), fill="#ffe066")
    draw.polygon(P([(44,4), (60,20), (53,24), (40,11)]), fill="#ffd13b")
    draw.polygon(P([(60,20), (60,44), (53,40), (53,24)]), fill="#ffb703")
    draw.polygon(P([(60,44), (44,60), (40,53), (53,40)]), fill="#e09200")
    draw.polygon(P([(44,60), (20,60), (24,53), (40,53)]), fill="#b87200")
    draw.polygon(P([(20,60), (4,44), (11,40), (24,53)]), fill="#e09200")
    draw.polygon(P([(4,44), (4,20), (11,24), (11,40)]), fill="#ffb703")
    draw.polygon(P([(4,20), (20,4), (24,11), (11,24)]), fill="#ffe066")
    draw.polygon(P([(24,11), (32,32), (40,11)]), fill="#ffc83b")
    draw.polygon(P([(40,11), (32,32), (53,24)]), fill="#ffa200")
    draw.polygon(P([(53,24), (32,32), (53,40)]), fill="#eb8f00")
    draw.polygon(P([(53,40), (32,32), (40,53)]), fill="#d47a00")
    draw.polygon(P([(40,53), (32,32), (24,53)]), fill="#bd6800")
    draw.polygon(P([(24,53), (32,32), (11,40)]), fill="#d47a00")
    draw.polygon(P([(11,40), (32,32), (11,24)]), fill="#ffa200")
    draw.polygon(P([(11,24), (32,32), (24,11)]), fill="#ffc83b")
    draw.ellipse([(22*S, 22*S), (42*S, 42*S)], fill=(255, 255, 255, 70))

draw_supersampled((64, 64), draw_coin).save(os.path.join(PNG_DIR, "icon_coin.png"))

# 4. Water Droplet Icon (64x64)
def draw_water(draw, S):
    def P(pts): return [(x * S, y * S) for x, y in pts]
    draw.polygon(P([(32,4), (21,24), (32,28)]), fill="#90e0ef")
    draw.polygon(P([(32,4), (32,28), (43,24)]), fill="#48cae4")
    draw.polygon(P([(32,4), (12,34), (21,24)]), fill="#caf0f8")
    draw.polygon(P([(32,4), (43,24), (52,34)]), fill="#0096c7")
    draw.polygon(P([(21,24), (12,34), (24,39)]), fill="#00b4d8")
    draw.polygon(P([(21,24), (24,39), (32,28)]), fill="#48cae4")
    draw.polygon(P([(32,28), (24,39), (32,45)]), fill="#0077b6")
    draw.polygon(P([(32,28), (32,45), (40,39)]), fill="#0096c7")
    draw.polygon(P([(32,28), (40,39), (43,24)]), fill="#0077b6")
    draw.polygon(P([(43,24), (40,39), (52,34)]), fill="#023e8a")
    draw.polygon(P([(12,34), (12,44), (24,39)]), fill="#0077b6")
    draw.polygon(P([(12,44), (22,58), (26,47)]), fill="#023e8a")
    draw.polygon(P([(12,44), (26,47), (24,39)]), fill="#0077b6")
    draw.polygon(P([(24,39), (26,47), (32,45)]), fill="#03045e")
    draw.polygon(P([(32,45), (26,47), (32,58)]), fill="#023e8a")
    draw.polygon(P([(32,45), (32,58), (38,47)]), fill="#023e8a")
    draw.polygon(P([(32,45), (38,47), (40,39)]), fill="#03045e")
    draw.polygon(P([(40,39), (38,47), (52,44)]), fill="#0077b6")
    draw.polygon(P([(38,47), (32,58), (42,58)]), fill="#03045e")
    draw.polygon(P([(38,47), (42,58), (52,44)]), fill="#03045e")
    draw.polygon(P([(22,14), (27,21), (21,23)]), fill="#ffffff")

draw_supersampled((64, 64), draw_water).save(os.path.join(PNG_DIR, "icon_water.png"))

# 5. Battery Power Icon (64x64)
def draw_battery(draw, S):
    def P(pts): return [(x * S, y * S) for x, y in pts]
    draw.polygon(P([(26,6), (38,6), (38,10), (26,10)]), fill="#9ef01a")
    draw.rounded_rectangle([(12*S, 10*S), (52*S, 58*S)], radius=4*S, fill="#122014", outline="#283618", width=2*S)
    draw.rounded_rectangle([(16*S, 46*S), (48*S, 54*S)], radius=2*S, fill="#38b000")
    draw.rounded_rectangle([(16*S, 33*S), (48*S, 41*S)], radius=2*S, fill="#70e000")
    draw.rounded_rectangle([(16*S, 20*S), (48*S, 28*S)], radius=2*S, fill="#9ef01a")

draw_supersampled((64, 64), draw_battery).save(os.path.join(PNG_DIR, "icon_battery.png"))

# 6. Axe Icon (64x64)
def draw_axe(draw, S):
    def P(pts): return [(x * S, y * S) for x, y in pts]
    draw.polygon(P([(14,58), (10,54), (46,10), (50,14)]), fill="#7f4f24")
    draw.polygon(P([(14,58), (12,56), (48,12), (50,14)]), fill="#a66a38")
    draw.polygon(P([(38,8), (50,14), (36,16)]), fill="#92a8d1")
    draw.polygon(P([(50,14), (58,6), (38,8)]), fill="#c3d2e6")
    draw.polygon(P([(50,14), (60,26), (58,6)]), fill="#e0ebf5")
    draw.polygon(P([(50,14), (44,24), (60,26)]), fill="#6c7a89")
    draw.line(P([(58,6), (60,26)]), fill="#ffffff", width=2*S)

draw_supersampled((64, 64), draw_axe).save(os.path.join(PNG_DIR, "icon_axe.png"))

# 7. Hotbar Slot Single (50x50)
def draw_slot(draw, S):
    draw.rounded_rectangle([(1*S, 1*S), (49*S, 49*S)], radius=8*S, fill="#1c2533", outline="#2c3b4f", width=2*S)
    draw.rounded_rectangle([(3*S, 3*S), (47*S, 10*S)], radius=3*S, fill=(16, 21, 29, 160))

draw_supersampled((50, 50), draw_slot).save(os.path.join(PNG_DIR, "compact_hotbar_slot.png"))

# 8. Active Selector Frame (54x50)
def draw_selector(draw, S):
    draw.rounded_rectangle([(2*S, 2*S), (52*S, 48*S)], radius=9*S, outline="#ffe066", width=3*S)
    draw.rounded_rectangle([(3*S, 3*S), (51*S, 47*S)], radius=8*S, outline=(255, 255, 255, 150), width=1*S)

draw_supersampled((54, 50), draw_selector).save(os.path.join(PNG_DIR, "compact_selector_active.png"))

# 9. Full 10-slot Hotbar Strip (570x56)
def draw_hotbar_full(draw, S):
    # Main tray
    draw.rounded_rectangle([(2*S, 2*S), (568*S, 54*S)], radius=12*S, fill="#131922", outline="#283445", width=2*S)
    # 10 slot wells
    for i in range(10):
        x = 12 + i * 54
        draw.rounded_rectangle([(x*S, 6*S), ((x+48)*S, 50*S)], radius=8*S, fill="#1c2533", outline="#222d3d", width=1*S)
        draw.rounded_rectangle([((x+2)*S, 8*S), ((x+46)*S, 14*S)], radius=3*S, fill=(16, 21, 29, 150))

draw_supersampled((570, 56), draw_hotbar_full).save(os.path.join(PNG_DIR, "compact_hotbar_10slots.png"))

# 10. Player Status Pill (240x52)
def draw_player_status(draw, S):
    draw.rounded_rectangle([(2*S, 2*S), (238*S, 50*S)], radius=10*S, fill="#151b24", outline="#2a3545", width=2*S)
    # Health track & fill
    draw.rounded_rectangle([(32*S, 11*S), (182*S, 21*S)], radius=5*S, fill="#201519", outline="#421a22", width=1*S)
    draw.rounded_rectangle([(34*S, 13*S), (158*S, 19*S)], radius=3*S, fill="#ff385c")
    # Stamina track & fill
    draw.rounded_rectangle([(32*S, 30*S), (182*S, 40*S)], radius=5*S, fill="#0f2224", outline="#163f42", width=1*S)
    draw.rounded_rectangle([(34*S, 32*S), (170*S, 38*S)], radius=3*S, fill="#00f5d4")

draw_supersampled((240, 52), draw_player_status).save(os.path.join(PNG_DIR, "compact_player_status.png"))

# 11. Time & Season Capsule (190x44)
def draw_time_season(draw, S):
    draw.rounded_rectangle([(2*S, 2*S), (188*S, 42*S)], radius=20*S, fill="#151b24", outline="#2a3545", width=2*S)
    draw.ellipse([(8*S, 8*S), (36*S, 36*S)], fill="#202937", outline="#37455a", width=1*S)

draw_supersampled((190, 44), draw_time_season).save(os.path.join(PNG_DIR, "compact_time_season.png"))

# 12. Resources Capsule (230x44)
def draw_resources(draw, S):
    draw.rounded_rectangle([(2*S, 2*S), (228*S, 42*S)], radius=20*S, fill="#151b24", outline="#2a3545", width=2*S)
    draw.line([(68*S, 10*S), (68*S, 34*S)], fill="#2a3545", width=1*S)
    draw.line([(138*S, 10*S), (138*S, 34*S)], fill="#2a3545", width=1*S)

draw_supersampled((230, 44), draw_resources).save(os.path.join(PNG_DIR, "compact_resources.png"))

# 13. Window Dialog Frame (460x320)
def draw_window_frame(draw, S):
    draw.rounded_rectangle([(2*S, 2*S), (458*S, 318*S)], radius=14*S, fill="#131922", outline="#b08968", width=2*S)
    draw.rounded_rectangle([(14*S, 56*S), (446*S, 306*S)], radius=8*S, fill="#18202c", outline="#253244", width=1*S)

draw_supersampled((460, 320), draw_window_frame).save(os.path.join(PNG_DIR, "compact_window_dialog.png"))

# 14. Modern Buttons (110x36)
def draw_btn_slate(draw, S):
    draw.rounded_rectangle([(2*S, 2*S), (108*S, 34*S)], radius=8*S, fill="#253142", outline="#3b4d66", width=2*S)
draw_supersampled((110, 36), draw_btn_slate).save(os.path.join(PNG_DIR, "compact_btn_slate_normal.png"))

def draw_btn_slate_hover(draw, S):
    draw.rounded_rectangle([(2*S, 2*S), (108*S, 34*S)], radius=8*S, fill="#253142", outline="#38bdf8", width=3*S)
draw_supersampled((110, 36), draw_btn_slate_hover).save(os.path.join(PNG_DIR, "compact_btn_slate_hover.png"))

def draw_btn_green(draw, S):
    draw.rounded_rectangle([(2*S, 2*S), (108*S, 34*S)], radius=8*S, fill="#1e4620", outline="#2d6a30", width=2*S)
draw_supersampled((110, 36), draw_btn_green).save(os.path.join(PNG_DIR, "compact_btn_green_normal.png"))

def draw_btn_amber(draw, S):
    draw.rounded_rectangle([(2*S, 2*S), (108*S, 34*S)], radius=8*S, fill="#784b06", outline="#a3680d", width=2*S)
draw_supersampled((110, 36), draw_btn_amber).save(os.path.join(PNG_DIR, "compact_btn_amber_normal.png"))

print("Rendered crisp PNG assets with 4x supersampling successfully.")

