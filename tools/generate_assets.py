import os

_this_dir = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(_this_dir)  # tools/ sits at the repo root (one level up)
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
SVG_DIR = os.path.join(ASSETS_DIR, "svg")
PNG_DIR = os.path.join(ASSETS_DIR, "png")
ICONS_DIR = os.path.join(ASSETS_DIR, "icons")
HOTBAR_DIR = os.path.join(ASSETS_DIR, "hotbar")
WINDOWS_DIR = os.path.join(ASSETS_DIR, "windows")
BUTTONS_DIR = os.path.join(ASSETS_DIR, "buttons")
BARS_DIR = os.path.join(ASSETS_DIR, "bars")

for d in [SVG_DIR, PNG_DIR, ICONS_DIR, HOTBAR_DIR, WINDOWS_DIR, BUTTONS_DIR, BARS_DIR]:
    os.makedirs(d, exist_ok=True)

SVGS = {}

# =========================================================================
# 1. MODERN COMPACT ICONS (64x64 / 128x128)
# =========================================================================

# Modern low-poly ruby heart
SVGS["icons/icon_heart.svg"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
  <defs>
    <filter id="glow_red" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#ff3b5c" flood-opacity="0.6"/>
    </filter>
  </defs>
  <g filter="url(#glow_red)">
    <!-- Facets -->
    <polygon points="32,58 10,34 10,18 20,8 32,18 44,8 54,18 54,34" fill="#a8132e"/>
    <polygon points="32,18 20,8 32,9" fill="#ff4d6d"/>
    <polygon points="32,18 32,9 44,8" fill="#ff758f"/>
    <polygon points="20,8 10,18 20,24" fill="#e01a4f"/>
    <polygon points="20,8 20,24 32,18" fill="#ff4d6d"/>
    <polygon points="44,8 32,18 44,24" fill="#ff597b"/>
    <polygon points="44,8 44,24 54,18" fill="#e01a4f"/>
    <polygon points="10,18 10,34 20,24" fill="#c9184a"/>
    <polygon points="20,24 10,34 22,38" fill="#a8132e"/>
    <polygon points="20,24 22,38 32,32" fill="#d90429"/>
    <polygon points="20,24 32,32 32,18" fill="#ef233c"/>
    <polygon points="32,18 32,32 42,38" fill="#ff4d6d"/>
    <polygon points="32,18 42,38 44,24" fill="#ff758f"/>
    <polygon points="44,24 42,38 54,34" fill="#a8132e"/>
    <polygon points="44,24 54,34 54,18" fill="#c9184a"/>
    <!-- Lower facets -->
    <polygon points="10,34 32,58 22,38" fill="#800f2f"/>
    <polygon points="22,38 32,58 32,44" fill="#a8132e"/>
    <polygon points="22,38 32,44 32,32" fill="#c9184a"/>
    <polygon points="32,32 32,44 42,38" fill="#c9184a"/>
    <polygon points="42,38 32,44 32,58" fill="#a8132e"/>
    <polygon points="42,38 32,58 54,34" fill="#590d22"/>
    <!-- Glint -->
    <polygon points="18,14 24,12 20,20" fill="#ffffff" opacity="0.8"/>
  </g>
</svg>"""

# Modern low-poly cyan stamina bolt
SVGS["icons/icon_stamina.svg"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
  <defs>
    <filter id="glow_cyan" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#00f5d4" flood-opacity="0.8"/>
    </filter>
  </defs>
  <g filter="url(#glow_cyan)">
    <polygon points="38,4 16,34 31,34 22,60 48,26 33,26" fill="#007f7a"/>
    <polygon points="38,4 27,19 33,26" fill="#9bf6ff"/>
    <polygon points="38,4 33,26 48,26" fill="#00f5d4"/>
    <polygon points="38,4 16,34 27,19" fill="#cbf3f0"/>
    <polygon points="27,19 16,34 31,34" fill="#00bbf9"/>
    <polygon points="31,34 22,60 35,43" fill="#00f5d4"/>
    <polygon points="31,34 35,43 48,26" fill="#00bbf9"/>
    <polygon points="35,43 22,60 42,36" fill="#007f7a"/>
    <!-- Glint -->
    <polygon points="35,8 30,19 36,18" fill="#ffffff" opacity="0.9"/>
  </g>
</svg>"""

# Modern low-poly gold coin
SVGS["icons/icon_coin.svg"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
  <defs>
    <filter id="glow_gold" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#ffb703" flood-opacity="0.7"/>
    </filter>
  </defs>
  <g filter="url(#glow_gold)">
    <!-- Octagon rim -->
    <polygon points="20,4 44,4 60,20 60,44 44,60 20,60 4,44 4,20" fill="#c97e00"/>
    <polygon points="20,4 44,4 40,11 24,11" fill="#ffe066"/>
    <polygon points="44,4 60,20 53,24 40,11" fill="#ffd13b"/>
    <polygon points="60,20 60,44 53,40 53,24" fill="#ffb703"/>
    <polygon points="60,44 44,60 40,53 53,40" fill="#e09200"/>
    <polygon points="44,60 20,60 24,53 40,53" fill="#b87200"/>
    <polygon points="20,60 4,44 11,40 24,53" fill="#e09200"/>
    <polygon points="4,44 4,20 11,24 11,40" fill="#ffb703"/>
    <polygon points="4,20 20,4 24,11 11,24" fill="#ffe066"/>
    <!-- Face -->
    <polygon points="24,11 40,11 53,24 53,40 40,53 24,53 11,40 11,24" fill="#f5aa00"/>
    <polygon points="24,11 32,32 40,11" fill="#ffc83b"/>
    <polygon points="40,11 32,32 53,24" fill="#ffa200"/>
    <polygon points="53,24 32,32 53,40" fill="#eb8f00"/>
    <polygon points="53,40 32,32 40,53" fill="#d47a00"/>
    <polygon points="40,53 32,32 24,53" fill="#bd6800"/>
    <polygon points="24,53 32,32 11,40" fill="#d47a00"/>
    <polygon points="11,40 32,32 11,24" fill="#ffa200"/>
    <polygon points="11,24 32,32 24,11" fill="#ffc83b"/>
    <!-- Currency glyph -->
    <circle cx="32" cy="32" r="10" fill="#ffffff" opacity="0.3"/>
    <text x="27" y="38" font-family="'Segoe UI', Arial, sans-serif" font-weight="900" font-size="16" fill="#472600">$</text>
  </g>
</svg>"""

# Modern low-poly water droplet
SVGS["icons/icon_water.svg"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
  <defs>
    <filter id="glow_blue" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#00b4d8" flood-opacity="0.7"/>
    </filter>
  </defs>
  <g filter="url(#glow_blue)">
    <polygon points="32,4 12,34 12,44 22,58 42,58 52,44 52,34" fill="#03045e"/>
    <polygon points="32,4 21,24 32,28" fill="#90e0ef"/>
    <polygon points="32,4 32,28 43,24" fill="#48cae4"/>
    <polygon points="32,4 12,34 21,24" fill="#caf0f8"/>
    <polygon points="32,4 43,24 52,34" fill="#0096c7"/>
    <!-- Mid facets -->
    <polygon points="21,24 12,34 24,39" fill="#00b4d8"/>
    <polygon points="21,24 24,39 32,28" fill="#48cae4"/>
    <polygon points="32,28 24,39 32,45" fill="#0077b6"/>
    <polygon points="32,28 32,45 40,39" fill="#0096c7"/>
    <polygon points="32,28 40,39 43,24" fill="#0077b6"/>
    <polygon points="43,24 40,39 52,34" fill="#023e8a"/>
    <!-- Bottom facets -->
    <polygon points="12,34 12,44 24,39" fill="#0077b6"/>
    <polygon points="12,44 22,58 26,47" fill="#023e8a"/>
    <polygon points="12,44 26,47 24,39" fill="#0077b6"/>
    <polygon points="24,39 26,47 32,45" fill="#03045e"/>
    <polygon points="32,45 26,47 32,58" fill="#023e8a"/>
    <polygon points="32,45 32,58 38,47" fill="#023e8a"/>
    <polygon points="32,45 38,47 40,39" fill="#03045e"/>
    <polygon points="40,39 38,47 52,44" fill="#0077b6"/>
    <polygon points="38,47 32,58 42,58" fill="#03045e"/>
    <polygon points="38,47 42,58 52,44" fill="#03045e"/>
    <polygon points="40,39 52,44 52,34" fill="#023e8a"/>
    <!-- Glint -->
    <polygon points="22,14 27,21 21,23" fill="#ffffff" opacity="0.9"/>
  </g>
</svg>"""

# Modern low-poly battery / power cell
SVGS["icons/icon_battery.svg"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
  <defs>
    <filter id="glow_green" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#38b000" flood-opacity="0.8"/>
    </filter>
  </defs>
  <g filter="url(#glow_green)">
    <!-- Battery terminal -->
    <polygon points="26,6 38,6 38,10 26,10" fill="#9ef01a"/>
    <!-- Battery case -->
    <polygon points="14,10 50,10 52,14 52,56 50,60 14,60 12,56 12,14" fill="#122014" stroke="#283618" stroke-width="2"/>
    <!-- Glowing green energy bars -->
    <rect x="16" y="46" width="32" height="10" rx="2" fill="#38b000"/>
    <rect x="16" y="33" width="32" height="10" rx="2" fill="#70e000"/>
    <rect x="16" y="20" width="32" height="10" rx="2" fill="#9ef01a"/>
    <!-- Glass reflection -->
    <polygon points="14,12 28,12 18,58 14,58" fill="#ffffff" opacity="0.25"/>
  </g>
</svg>"""

# Modern Sundial / Compass Icon
SVGS["icons/icon_sundial.svg"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
  <defs>
    <filter id="glow_sun" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#e9c46a" flood-opacity="0.7"/>
    </filter>
  </defs>
  <g filter="url(#glow_sun)">
    <!-- Sundial base plate -->
    <polygon points="32,6 54,16 60,38 48,56 16,56 4,38 10,16" fill="#3d5a80" stroke="#1d2d44" stroke-width="2"/>
    <polygon points="32,6 54,16 48,22 32,14" fill="#5b84b1"/>
    <polygon points="54,16 60,38 52,36 48,22" fill="#466d98"/>
    <polygon points="60,38 48,56 42,50 52,36" fill="#32527b"/>
    <polygon points="48,56 16,56 22,50 42,50" fill="#243e63"/>
    <polygon points="16,56 4,38 12,36 22,50" fill="#1b2f4d"/>
    <polygon points="4,38 10,16 16,22 12,36" fill="#32527b"/>
    <polygon points="10,16 32,6 32,14 16,22" fill="#5b84b1"/>
    <!-- Center plate -->
    <polygon points="32,14 48,22 52,36 42,50 22,50 12,36 16,22" fill="#e0e1dd"/>
    <!-- Sundial Gnomon (Stylized golden low-poly pointer shadow) -->
    <polygon points="32,18 36,36 32,38 28,36" fill="#f4a261"/>
    <polygon points="32,18 36,36 32,38" fill="#e76f51"/>
    <polygon points="32,38 48,46 36,36" fill="#2b2d42" opacity="0.6"/>
  </g>
</svg>"""

# Modern low-poly axe
SVGS["icons/icon_axe.svg"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
  <defs>
    <filter id="tool_sh" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#000" flood-opacity="0.6"/>
    </filter>
  </defs>
  <g filter="url(#tool_sh)">
    <!-- Wooden haft -->
    <polygon points="14,58 10,54 46,10 50,14" fill="#7f4f24"/>
    <polygon points="14,58 12,56 48,12 50,14" fill="#a66a38"/>
    <!-- Blade head -->
    <polygon points="38,8 58,6 60,26 44,24 36,16" fill="#4a5759"/>
    <polygon points="38,8 50,14 36,16" fill="#92a8d1"/>
    <polygon points="50,14 58,6 38,8" fill="#c3d2e6"/>
    <polygon points="50,14 60,26 58,6" fill="#e0ebf5"/>
    <polygon points="50,14 44,24 60,26" fill="#6c7a89"/>
    <polygon points="58,6 60,26 59,25 57,7" fill="#ffffff" opacity="0.9"/>
  </g>
</svg>"""

# Modern low-poly wheat
SVGS["icons/icon_wheat.svg"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
  <g filter="drop-shadow(0 2px 2px rgba(0,0,0,0.6))">
    <line x1="18" y1="58" x2="44" y2="12" stroke="#d4a373" stroke-width="2.5" stroke-linecap="round"/>
    <polygon points="44,10 52,6 48,14" fill="#ffb703"/>
    <polygon points="40,16 50,14 45,21" fill="#ffb703"/>
    <polygon points="39,18 31,13 35,21" fill="#ffe066"/>
    <polygon points="35,24 45,23 40,30" fill="#fa8c16"/>
    <polygon points="33,26 24,22 28,30" fill="#ffd13b"/>
    <polygon points="29,32 38,32 33,39" fill="#fa8c16"/>
    <polygon points="27,34 19,30 23,38" fill="#ffd13b"/>
  </g>
</svg>"""

# Modern low-poly timber log
SVGS["icons/icon_wood_log.svg"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
  <g filter="drop-shadow(0 2px 2px rgba(0,0,0,0.6))">
    <polygon points="18,22 52,10 58,26 24,38" fill="#583110"/>
    <polygon points="18,22 52,10 54,17 20,29" fill="#7f4f24"/>
    <!-- Cut end face -->
    <polygon points="8,30 18,22 24,38 14,46" fill="#ddb892"/>
    <polygon points="8,30 18,22 16,34" fill="#ede0d4"/>
    <polygon points="18,22 24,38 16,34" fill="#b08968"/>
    <polygon points="24,38 14,46 16,34" fill="#9c6644"/>
    <polygon points="14,46 8,30 16,34" fill="#b08968"/>
    <circle cx="16" cy="34" r="3" fill="#7f4f24"/>
  </g>
</svg>"""

# Modern low-poly watering can
SVGS["icons/icon_watering_can.svg"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
  <g filter="drop-shadow(0 2px 2px rgba(0,0,0,0.6))">
    <!-- Body -->
    <polygon points="22,24 44,24 48,50 20,50" fill="#52796f"/>
    <polygon points="22,24 44,24 42,34 24,34" fill="#84a98c"/>
    <polygon points="24,34 42,34 40,48 22,48" fill="#354f52"/>
    <!-- Spout -->
    <polygon points="44,38 58,16 60,20 46,44" fill="#84a98c"/>
    <polygon points="56,14 62,18 58,22 52,18" fill="#cad2c5"/>
    <!-- Handle -->
    <path d="M 22,28 C 12,28 12,46 20,46" fill="none" stroke="#84a98c" stroke-width="4" stroke-linecap="round"/>
  </g>
</svg>"""

# Modern low-poly pickaxe
SVGS["icons/icon_pickaxe.svg"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
  <g filter="drop-shadow(0 2px 2px rgba(0,0,0,0.6))">
    <polygon points="14,56 10,52 48,14 52,18" fill="#7f4f24"/>
    <polygon points="14,56 12,54 50,16 52,18" fill="#a66a38"/>
    <!-- Pick head arch -->
    <path d="M 28,10 Q 48,18 60,34 L 56,36 Q 44,24 26,14 Z" fill="#6c7a89"/>
    <path d="M 32,8 Q 48,14 60,34 L 58,32 Q 46,14 30,6 Z" fill="#c3d2e6"/>
  </g>
</svg>"""

# Modern low-poly hoe
SVGS["icons/icon_hoe.svg"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
  <g filter="drop-shadow(0 2px 2px rgba(0,0,0,0.6))">
    <polygon points="14,56 10,52 48,14 52,18" fill="#7f4f24"/>
    <!-- Hoe blade -->
    <polygon points="46,12 56,16 48,32 42,30" fill="#4a5759"/>
    <polygon points="46,12 56,16 52,24 44,20" fill="#c3d2e6"/>
  </g>
</svg>"""

# Modern low-poly bread
SVGS["icons/icon_bread.svg"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
  <g filter="drop-shadow(0 2px 2px rgba(0,0,0,0.6))">
    <polygon points="12,38 20,20 44,20 52,38 44,48 20,48" fill="#bc6c25"/>
    <polygon points="20,20 44,20 40,28 24,28" fill="#dda15e"/>
    <polygon points="12,38 20,20 24,28 18,42" fill="#c57b32"/>
    <polygon points="44,20 52,38 46,42 40,28" fill="#99582a"/>
    <!-- Slash marks -->
    <line x1="26" y1="22" x2="30" y2="30" stroke="#fefae0" stroke-width="2"/>
    <line x1="36" y1="22" x2="40" y2="30" stroke="#fefae0" stroke-width="2"/>
  </g>
</svg>"""

# Modern low-poly seeds
SVGS["icons/icon_seeds.svg"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
  <g filter="drop-shadow(0 2px 2px rgba(0,0,0,0.6))">
    <!-- Seed 1 -->
    <polygon points="24,18 32,28 24,36 18,28" fill="#cda882"/>
    <polygon points="24,18 32,28 24,27" fill="#edd6be"/>
    <polygon points="24,27 32,28 24,36" fill="#a47850"/>
    <!-- Seed 2 -->
    <polygon points="42,24 50,34 42,42 36,34" fill="#cda882"/>
    <polygon points="42,24 50,34 42,33" fill="#edd6be"/>
    <!-- Seed 3 -->
    <polygon points="30,36 38,46 30,52 24,44" fill="#cda882"/>
  </g>
</svg>"""


# =========================================================================
# 2. ULTRA-COMPACT MODERN TOP BAR MODULES
# =========================================================================

# Top-Left: Slim Dual Status Card (240x52)
SVGS["bars/compact_player_status.svg"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 52" width="240" height="52">
  <defs>
    <filter id="m_card_sh" x="-10%" y="-15%" width="120%" height="135%">
      <feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#050a10" flood-opacity="0.75"/>
    </filter>
  </defs>
  <g filter="url(#m_card_sh)">
    <!-- Compact frosted slate pill card -->
    <rect x="2" y="2" width="236" height="48" rx="10" fill="#151b24" stroke="#2a3545" stroke-width="1.5" opacity="0.94"/>
    
    <!-- Health Row (Top) -->
    <g transform="translate(10, 8)">
      <!-- Mini Heart Icon -->
      <polygon points="10,14 4,8 4,4 7,1 10,4 13,1 16,4 16,8" fill="#ff4d6d"/>
      <!-- Track -->
      <rect x="22" y="3" width="150" height="10" rx="5" fill="#201519" stroke="#421a22" stroke-width="1"/>
      <!-- Fill (85%) -->
      <rect x="24" y="5" width="124" height="6" rx="3" fill="#ff385c"/>
      <rect x="24" y="5" width="124" height="2" rx="1" fill="#ff758f" opacity="0.8"/>
      <!-- Number -->
      <text x="180" y="12" font-family="'Segoe UI', Roboto, sans-serif" font-weight="bold" font-size="9.5" fill="#ffffff" letter-spacing="0.5">85/100</text>
    </g>

    <!-- Stamina Row (Bottom) -->
    <g transform="translate(10, 27)">
      <!-- Mini Lightning Icon -->
      <polygon points="12,1 5,9 9,9 7,15 14,7 10,7" fill="#00f5d4"/>
      <!-- Track -->
      <rect x="22" y="3" width="150" height="10" rx="5" fill="#0f2224" stroke="#163f42" stroke-width="1"/>
      <!-- Fill (92%) -->
      <rect x="24" y="5" width="136" height="6" rx="3" fill="#00f5d4"/>
      <rect x="24" y="5" width="136" height="2" rx="1" fill="#cbf3f0" opacity="0.9"/>
      <!-- Number -->
      <text x="180" y="12" font-family="'Segoe UI', Roboto, sans-serif" font-weight="bold" font-size="9.5" fill="#ffffff" letter-spacing="0.5">92/100</text>
    </g>
  </g>
</svg>"""

# Top-Center: Slim Time & Season Capsule (190x44)
SVGS["bars/compact_time_season.svg"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 190 44" width="190" height="44">
  <defs>
    <filter id="m_cap_sh" x="-10%" y="-15%" width="120%" height="135%">
      <feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#050a10" flood-opacity="0.75"/>
    </filter>
  </defs>
  <g filter="url(#m_cap_sh)">
    <!-- Compact Pill Frame -->
    <rect x="2" y="2" width="186" height="40" rx="20" fill="#151b24" stroke="#2a3545" stroke-width="1.5" opacity="0.94"/>
    
    <!-- Mini Sundial icon inside circular pocket -->
    <circle cx="22" cy="22" r="14" fill="#202937" stroke="#37455a" stroke-width="1"/>
    <!-- Sundial graphic -->
    <circle cx="22" cy="22" r="11" fill="#e0e1dd"/>
    <polygon points="22,14 25,24 22,25 19,24" fill="#e76f51"/>
    <polygon points="22,25 29,29 25,24" fill="#2b2d42" opacity="0.5"/>

    <!-- Clock Text -->
    <text x="46" y="21" font-family="'Segoe UI', Roboto, sans-serif" font-weight="bold" font-size="14" fill="#ffffff" letter-spacing="0.5">08:45 AM</text>
    <!-- Season & Day Subtitle -->
    <text x="46" y="33" font-family="'Segoe UI', Roboto, sans-serif" font-weight="600" font-size="9" fill="#94a3b8" letter-spacing="1">SPRING · DAY 4</text>
  </g>
</svg>"""

# Top-Right: Slim Unified Resource Capsule (230x44)
SVGS["bars/compact_resources.svg"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 230 44" width="230" height="44">
  <defs>
    <filter id="m_res_sh" x="-10%" y="-15%" width="120%" height="135%">
      <feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#050a10" flood-opacity="0.75"/>
    </filter>
  </defs>
  <g filter="url(#m_res_sh)">
    <!-- Compact Pill Frame -->
    <rect x="2" y="2" width="226" height="40" rx="20" fill="#151b24" stroke="#2a3545" stroke-width="1.5" opacity="0.94"/>
    
    <!-- Section 1: Gold Coins -->
    <g transform="translate(10, 11)">
      <!-- Mini Coin -->
      <circle cx="11" cy="11" r="9" fill="#ffb703" stroke="#b87200" stroke-width="1"/>
      <text x="8" y="15" font-family="'Segoe UI', sans-serif" font-weight="900" font-size="10" fill="#472600">$</text>
      <!-- Value -->
      <text x="25" y="15" font-family="'Segoe UI', Roboto, sans-serif" font-weight="bold" font-size="12" fill="#ffffff">520</text>
    </g>

    <!-- Divider 1 -->
    <line x1="68" y1="10" x2="68" y2="34" stroke="#2a3545" stroke-width="1"/>

    <!-- Section 2: Water (L) -->
    <g transform="translate(76, 11)">
      <!-- Mini Water Drop -->
      <polygon points="10,2 4,12 4,15 10,20 16,15 16,12" fill="#00b4d8"/>
      <!-- Value -->
      <text x="22" y="15" font-family="'Segoe UI', Roboto, sans-serif" font-weight="bold" font-size="12" fill="#ffffff">85L</text>
    </g>

    <!-- Divider 2 -->
    <line x1="138" y1="10" x2="138" y2="34" stroke="#2a3545" stroke-width="1"/>

    <!-- Section 3: Battery Energy (kW) -->
    <g transform="translate(146, 11)">
      <!-- Mini Battery -->
      <rect x="4" y="4" width="14" height="14" rx="2" fill="#142617" stroke="#38b000" stroke-width="1"/>
      <rect x="6" y="6" width="10" height="10" rx="1" fill="#70e000"/>
      <!-- Value -->
      <text x="23" y="15" font-family="'Segoe UI', Roboto, sans-serif" font-weight="bold" font-size="12" fill="#ffffff">140kW</text>
    </g>
  </g>
</svg>"""


# =========================================================================
# 3. SLIM LOW-PROFILE 10-SLOT HOTBAR
# =========================================================================

# Complete Slim 10-slot Hotbar (570x56)
SVGS["hotbar/compact_hotbar_10slots.svg"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 570 56" width="570" height="56">
  <defs>
    <filter id="m_bar_sh" x="-5%" y="-15%" width="110%" height="135%">
      <feDropShadow dx="0" dy="4" stdDeviation="5" flood-color="#050a10" flood-opacity="0.8"/>
    </filter>
  </defs>
  <g filter="url(#m_bar_sh)">
    <!-- Sleek translucent dark-slate tray -->
    <rect x="2" y="2" width="566" height="52" rx="12" fill="#131922" stroke="#283445" stroke-width="1.5" opacity="0.95"/>

    <!-- 10 Recessed Slot Wells (width 48, height 44, spacing 54, offset 12) -->
"""
for i in range(10):
    x = 12 + i * 54
    num = (i + 1) % 10
    SVGS["hotbar/compact_hotbar_10slots.svg"] += f"""
    <!-- Slot {i+1} -->
    <g transform="translate({x}, 6)">
      <!-- Slot well -->
      <rect x="0" y="0" width="48" height="44" rx="8" fill="#1c2533" stroke="#222d3d" stroke-width="1"/>
      <!-- Subtle top inner shadow -->
      <rect x="2" y="2" width="44" height="6" rx="3" fill="#10151d" opacity="0.6"/>
      <!-- Tiny Slot key label in corner -->
      <text x="6" y="12" font-family="'Segoe UI', Roboto, sans-serif" font-weight="bold" font-size="9" fill="#64748b">{num}</text>
    </g>
"""

SVGS["hotbar/compact_hotbar_10slots.svg"] += """
  </g>
</svg>"""

# Single Modular Compact Slot (50x50)
SVGS["hotbar/compact_hotbar_slot.svg"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 50 50" width="50" height="50">
  <rect x="1" y="1" width="48" height="48" rx="8" fill="#1c2533" stroke="#2c3b4f" stroke-width="1.5"/>
  <rect x="3" y="3" width="44" height="6" rx="3" fill="#10151d" opacity="0.6"/>
</svg>"""

# Glowing Golden Active Selector Bracket (54x50)
SVGS["hotbar/compact_selector_active.svg"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 54 50" width="54" height="50">
  <defs>
    <filter id="sel_glow" x="-30%" y="-30%" width="160%" height="160%">
      <feDropShadow dx="0" dy="0" stdDeviation="4" flood-color="#ffb703" flood-opacity="0.9"/>
      <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#fb8500" flood-opacity="0.7"/>
    </filter>
  </defs>
  <g filter="url(#sel_glow)">
    <rect x="2" y="2" width="50" height="46" rx="9" fill="none" stroke="#ffe066" stroke-width="2.5"/>
    <rect x="3.5" y="3.5" width="47" height="43" rx="7.5" fill="none" stroke="#ffffff" stroke-width="0.8" opacity="0.6"/>
  </g>
</svg>"""

# Floating Item Tooltip Pill (160x28)
SVGS["hotbar/compact_tooltip_pill.svg"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 28" width="160" height="28">
  <defs>
    <filter id="tip_sh" x="-10%" y="-20%" width="120%" height="150%">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#000" flood-opacity="0.7"/>
    </filter>
  </defs>
  <g filter="url(#tip_sh)">
    <rect x="2" y="2" width="156" height="24" rx="12" fill="#151b24" stroke="#334155" stroke-width="1" opacity="0.95"/>
    <text x="80" y="17" font-family="'Segoe UI', Roboto, sans-serif" font-weight="bold" font-size="11" fill="#f8fafc" text-anchor="middle" letter-spacing="0.5">Wood Axe</text>
  </g>
</svg>"""


# =========================================================================
# 4. COMPACT MODERN WINDOW DIALOG & BUTTONS
# =========================================================================

# Compact Window Frame (460x320)
SVGS["windows/compact_window_dialog.svg"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 460 320" width="460" height="320">
  <defs>
    <filter id="win_drop" x="-5%" y="-5%" width="110%" height="115%">
      <feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="#03070d" flood-opacity="0.9"/>
    </filter>
  </defs>
  <g filter="url(#win_drop)">
    <!-- Base card -->
    <rect x="2" y="2" width="456" height="316" rx="14" fill="#131922" stroke="#b08968" stroke-width="1.5" opacity="0.96"/>
    <!-- Header strip -->
    <path d="M 2,16 A 14,14 0 0,1 16,2 L 444,2 A 14,14 0 0,1 458,16 L 458,44 L 2,44 Z" fill="#1b2330"/>
    <line x1="2" y1="44" x2="458" y2="44" stroke="#2e3c50" stroke-width="1"/>
    <!-- Content background area -->
    <rect x="14" y="56" width="432" height="250" rx="8" fill="#18202c" stroke="#253244" stroke-width="1"/>
  </g>
</svg>"""

# Close Button States
SVGS["windows/compact_close_normal.svg"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">
  <rect x="2" y="2" width="28" height="28" rx="7" fill="#253142" stroke="#384961" stroke-width="1"/>
  <line x1="10" y1="10" x2="22" y2="22" stroke="#94a3b8" stroke-width="2.5" stroke-linecap="round"/>
  <line x1="22" y1="10" x2="10" y2="22" stroke="#94a3b8" stroke-width="2.5" stroke-linecap="round"/>
</svg>"""

SVGS["windows/compact_close_hover.svg"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">
  <defs>
    <filter id="cl_glow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="0" stdDeviation="2" flood-color="#ff4d6d" flood-opacity="0.8"/>
    </filter>
  </defs>
  <g filter="url(#cl_glow)">
    <rect x="2" y="2" width="28" height="28" rx="7" fill="#dc2626" stroke="#ef4444" stroke-width="1.5"/>
    <line x1="10" y1="10" x2="22" y2="22" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round"/>
    <line x1="22" y1="10" x2="10" y2="22" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round"/>
  </g>
</svg>"""

# Modern Buttons in 4 States (Normal, Hover with cyan glow, Pressed, Disabled)
MODERN_THEMES = {
    "slate": {"bg": "#253142", "bdr": "#3b4d66", "text": "#f1f5f9", "glow": "#38bdf8"},
    "green": {"bg": "#1e4620", "bdr": "#2d6a30", "text": "#dcfce7", "glow": "#4ade80"},
    "amber": {"bg": "#784b06", "bdr": "#a3680d", "text": "#fef3c7", "glow": "#fbbf24"}
}

for tname, c in MODERN_THEMES.items():
    # Normal (110x36)
    SVGS[f"buttons/compact_btn_{tname}_normal.svg"] = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 110 36" width="110" height="36">
  <rect x="1.5" y="1.5" width="107" height="33" rx="8" fill="{c['bg']}" stroke="{c['bdr']}" stroke-width="1.5"/>
</svg>"""
    # Hover (with sleek glow border)
    SVGS[f"buttons/compact_btn_{tname}_hover.svg"] = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 110 36" width="110" height="36">
  <defs>
    <filter id="btn_glow_{tname}" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="0" stdDeviation="3" flood-color="{c['glow']}" flood-opacity="0.8"/>
    </filter>
  </defs>
  <g filter="url(#btn_glow_{tname})">
    <rect x="1.5" y="1.5" width="107" height="33" rx="8" fill="{c['bg']}" stroke="{c['glow']}" stroke-width="2"/>
  </g>
</svg>"""
    # Pressed
    SVGS[f"buttons/compact_btn_{tname}_pressed.svg"] = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 110 36" width="110" height="36">
  <rect x="1.5" y="2.5" width="107" height="32" rx="8" fill="#131922" stroke="{c['bdr']}" stroke-width="1.5"/>
</svg>"""
    # Disabled
    SVGS[f"buttons/compact_btn_{tname}_disabled.svg"] = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 110 36" width="110" height="36">
  <rect x="1.5" y="1.5" width="107" height="33" rx="8" fill="#18202c" stroke="#253244" stroke-width="1" opacity="0.6"/>
</svg>"""

# Save all SVGs
for rel_path, content in SVGS.items():
    full_path = os.path.join(ASSETS_DIR, rel_path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.strip())
    flat_name = rel_path.replace("/", "_")
    flat_path = os.path.join(SVG_DIR, flat_name)
    with open(flat_path, "w", encoding="utf-8") as f:
        f.write(content.strip())

print(f"Generated {len(SVGS)} compact modern SVG assets successfully.")
