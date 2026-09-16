# Homesteader - Item Icon Creation Ruleset & Style Guide

This document establishes the official ruleset, aesthetic principles, technical specifications, generation prompts, and extraction pipeline for all item icons in **Homesteader**.

All future item icons—whether generated via 3D rendering (Blender/Maya) or AI concept generation (Imagen/Gemini/Midjourney)—**must** adhere strictly to this ruleset to guarantee visual consistency across the entire game.

> **THESE RULES ARE IMMUTABLE. THERE IS NO ACCEPTABLE DRIFT.** Every rule below (the 5 Core Commandments, the camera pitch/yaw range, the left-facing convention, the low-poly/no-photorealism requirement) is a hard requirement, not a stylistic suggestion the model can interpret loosely. A generated image that is "close" but softer/smoother/more detailed than true low-poly, or that faces the wrong direction, or that drifts outside the pitch/yaw range, **fails** and must be regenerated with the violated rule spelled out more explicitly in the prompt - it does not get shipped as "good enough." Before saving any icon, re-read this document, not just your memory of a prompt template you've used before; wording that worked on one generation call is not guaranteed to keep working, and must be re-verified against the actual rendered pixels every time, not assumed.

---

## 1. The 5 Core Commandments

| Rule                                             | Requirement                                                                                                                                                                  | Violation Consequence                            |
| :----------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :----------------------------------------------- |
| **1. NO BORDERS**                                | Zero border boxes, card outlines, background squares, slot frames, or pedestals.                                                                                             | Immediate rejection.                             |
| **2. FULL VIEW (NO CLIPPING)**                   | 100% of the item geometry must be fully visible. Tool handles, antenna tips, fishing rods, spigots, cables must never touch or cross the border.                             | Immediate rejection.                             |
| **3. 128 × 128 px Canvas with 12px Safe Margin** | Canvas is exactly 128×128 px. Item bounding box must fit inside `MAX_DIM = 104 px` centered, leaving $\ge 12\text{ px}$ clean margin on all 4 edges.                         | Visual inconsistency / HUD clipping.             |
| **4. Pure Transparent Background**               | 32-bit RGBA PNG with `alpha = 0` across all perimeter pixels. Clean anti-aliased edge with zero background color halos.                                                      | Ugly gray/black square halos in UI.              |
| **5. 3D Faceted Low-Poly Style**                 | 3D polygonal model look with visible geometric facets, directional key lighting, ambient occlusion in crevices, and subtle specular sheen. Flat 2D vector art is prohibited. | Mismatched art style against existing 70+ icons. |

---

## 2. Visual & Art Style Guide

### 2.1 Camera & Perspective

- **Projection**: Orthographic or very mild telephoto perspective ($\approx 85\text{mm}$ equivalent) to avoid extreme wide-angle fish-eye distortion.
- **Viewing Angle**: Standard **Isometric 3/4 Front View**:
  - **Pitch**: $30^\circ$ to $35^\circ$ downward angle.
  - **Yaw**: $40^\circ$ to $45^\circ$ rotation to show both the top and side facets simultaneously.
  - **Item Tilt**: Elongated tools (axes, fishing rods, chainsaws, pipes) should be oriented diagonally ($\approx 35^\circ\text{–}45^\circ$) across the canvas to maximize silhouette size and readability inside the square frame.

### 2.2 Lighting & Shading

- **Primary Key Light**: Top-left, warm white ($5500\text{K}\text{–}6000\text{K}$), cast at $45^\circ$ elevation. Produces crisp, faceted highlights on upper faces.
- **Secondary Fill Light**: Bottom-right, cool neutral white ($6500\text{K}$), low intensity ($25\%\text{–}30\%$) to keep shadowed facets readable without pitch black crush.
- **Crevice Ambient Occlusion (AO)**: Subtle darkening in recessed grooves (e.g., ribbing on septic tank, between birch logs in stack, spigot joints) to convey depth.
- **No Ground Shadows**: Never render cast floor shadows or shadow puddles underneath the object; icons float in pure empty space.

### 2.3 Geometry & Facet Density

- **Low-to-Mid Poly Aesthetic**: Visible polygonal facets on curved surfaces (e.g., faceted fruit contours, angular log ends, polygonal fish bodies).
- **Beveled Edges**: Hard mechanical edges should have tiny chamfers/bevels to catch specular light glints.
- **Readability at Small Scales**: Homesteader hotbar slots display icons at $32\times32\text{ px}$ to $50\times50\text{ px}$. Silhouettes must be **bold, chunky, and instantly recognizable** without relying on microscopic micro-details.

### 2.4 Material & Color Palette

- **Metals**: Cool slate gray (`#64748b`), dark gunmetal (`#334155`), warm brass/bronze (`#d97706`), galvanized silver (`#cbd5e1`). Soft satin reflection, not mirror-reflective.
- **Wood**: Warm honey timber (`#b08968`), weathered birch (`#e2e8f0` with dark bark flecks `#2d3748`), rich cedar (`#7f4f24`).
- **Organics / Crops**: Saturated, appetizing hues—vibrant carrot orange (`#ea580c`), sweet corn gold (`#eab308`), leaf greens (`#16a34a` to `#4ade80`), strawberry ruby (`#e11d48`).
- **Plastics / Electronics**: Matte industrial dark charcoal (`#1e293b`), tech accent cyan/blue (`#0284c7`), hi-vis emergency orange/red (`#ea580c` / `#dc2626`).

---

## 3. AI Generation & Prompting Standard

When generating new sheets or single assets using Gemini / Imagen / Midjourney / DALL-E, use the standardized prompt formula below.

### 3.1 Master Prompt Formula

```
A 3D low-poly faceted render of [ITEM_NAME], [DETAILED_ITEM_DESCRIPTION].
Style: clean video game asset icon, low-poly 3D model with CHUNKY SIMPLIFIED GEOMETRY and clearly VISIBLE FLAT POLYGON FACETS on every surface - each panel/plank/shingle should read as a distinct flat-shaded low-poly facet, NOT a smooth gradient and NOT fine photorealistic surface texture (no wood-grain micro-texture, no fine material texture of any kind). Ambient occlusion in crevices, smooth matte and satin materials, faceted specular highlights. This must look like a simple low-poly mobile-game asset, never a realistic/high-detail render - if the result reads as smoother or more detailed than a blocky low-poly model, it has failed this rule and must be redone with this paragraph repeated more forcefully, not shipped as "close enough."
View: isometric 3/4 front view, floating centered in empty space. STRICT CAMERA ANGLE: pitch 30-35 degrees downward from horizontal, yaw 40-45 degrees around the subject (showing both a top facet and a side facet at once) - this range is not optional and is not "roughly isometric," it is the exact angle window every existing icon in the catalog was shot at. If the subject has a clear front/back (animals, vehicles, tools with a handle or blade, buildings with a front door, anything with a "face" or direction of travel), it must be facing/oriented toward the LEFT of the frame - this matches the existing catalog convention and is not optional.
Lighting: soft studio key lighting from top-left, clean edge lighting, no cast shadows on floor, no pedestal, no table.
Background: solid uniform DARK SLATE background (hex #2b3442), completely plain and flat, no gradient, no patterns, no borders, no cards, no square frames, no UI elements.
```

**Chroma-key background: use dark slate (#2b3442), not magenta.** This reverses an earlier change made the same day (2026-09-15) - the history is worth keeping so a future session doesn't flip-flop again without cause. Dark slate was the original background, then briefly replaced with magenta (#FF00FF) after an empirical scan showed magenta had the largest safety margin against real catalog colors (130.9 vs 113 for green/blue, and cyan was actively dangerous). Magenta did fix the specific problem it was chosen for (a stovepipe shadow and an oven window both got eaten by dark-slate flood-fill extraction). But magenta introduced a WORSE problem in practice: a saturated magenta backdrop bleeds color into the rendered scene's shading and reflections themselves (not just the extraction edge) - shipped icons showed a visible purple/magenta cast baked into shadowed and reflective areas (gray metal pumps, glass shower panels, a fabric coat), which is contamination of the actual asset content, not just a background/extraction artifact. Reverted to dark slate by explicit user decision (2026-09-15) after seeing this in real shipped output. If dark slate's shadow-collision problem recurs, fix it with tolerance tuning or an explicit "no cast shadow" prompt instruction (already standing practice) rather than switching the background color again - both colors have a real failure mode, and color-switching alone doesn't eliminate the underlying flood-fill fragility.

**Directional subjects ALWAYS face LEFT. No exceptions, ever - this includes every stage of a growth-group set (foundation/framing/walls/complete all face left, not just some of them).** Before shipping any icon (single item or a batch sheet), check the render: does the subject visibly face/point right instead of left? If so, either regenerate with the direction called out more explicitly in the prompt, or horizontally flip the *standardized* icon (after `standardize_icon_image()`, not before - flipping the raw render first can shift lighting/shading in ways the flood-fill crop doesn't expect). Never ship a right-facing directional icon, and never treat an existing right-facing icon (a past mistake) as the "established convention" to match - flip it to left too rather than propagating the error.

**Verify against actual pixels, not the prompt you sent.** A prompt asking for low-poly does not guarantee a low-poly result - the model can and does drift toward smoother/more photorealistic renders even when explicitly told not to. Look at the returned image before extracting/shipping it: does it show visible flat facets, or does it read as a smooth detailed render? Does the camera angle look like the 30-35°/40-45° window, or does it look flatter/steeper? Does the directional facing actually match left (or the sibling convention)? Catching drift here, before extraction, is cheaper than a user catching it after it's live in the catalog.

### 3.2 Key Negative Constraints to Enforce

- ❌ **Do NOT include**: `frame, border, card, card slot, rounded rectangle, box, pedestal, ground plane, floor shadow, HUD elements, text, watermark, vignette, photorealistic microtexture, 2D vector flat icon`.
- ✅ **Must have**: `solid flat dark slate chroma-key background (#2b3442)`, `floating centered object`, `3D low-poly faceted`.

### 3.3 Batching Sheets vs. Single Icons

- **Standing rule: batch as much as possible into as few sheets as possible, including single-item and reference-matched requests.** A generation call costs the same flat credit amount whether it produces 1 item or 9, so any request processed as an individual call (rather than folded into a shared sheet) is a real, avoidable credit cost - group everything from a batch together by default, and only fall back to an individual call when a request genuinely needs true per-item image conditioning (see below) that batching can't provide.
- Target **9 items per sheet** as the reliable default ceiling; 12 is the outer edge, not a safe target - confirmed empirically: an 8-item request once came back with 12 items instead (the model added 4 unrequested extras), which broke the row-based extraction mapping and needed a manual fix. Prefer several 9-item sheets over one 12+-item sheet.
- When generating multiple items together on a concept sheet:
  - Keep a minimum of **$80\text{ px}$ spacing** between adjacent items on the sheet.
  - Arrange in a tidy grid (e.g., $2\times5$ or $3\times4$ on a $1376\times768$ canvas, or $3\times3$ for exactly 9).
  - Ensure uniform background color across the entire image (e.g. RGB `(45, 54, 69)` or `(58, 70, 84)`).
  - State the left-facing direction explicitly for **every** directional item in the prompt, not just once for the sheet as a whole - a per-item instruction gets followed far more reliably than one blanket line at the end covering N items.
  - After generating, count the actual items rendered against the count requested before running extraction - if they don't match, re-map the extraction script's row/column assignment by hand rather than assuming the requested order held.
- **Reference-matched items in a shared sheet lose true per-item image conditioning** (a single generation call only accepts one source image, and a shared sheet has no single source). Fold each reference-matched item's style into the sheet's text prompt instead (describe the reference's color/material/proportions in words per item, same as the REFERENCE_ITEM_PIPELINE fallback already allows) - this is the right tradeoff for simple, describable changes (a recolor, a different wood species, a size variant). Reserve genuine individual per-item image-conditioned edits for cases where wording alone is unlikely to nail the look (an unusual creature, a specific proportions match) - don't default to individual calls just because a request happens to have a reference asset attached.

### 3.4 Exact-Match Reference Requests: Use Image-Edit Mode, Not a Text Re-Description

When a request says match the reference **exactly / identically / precisely** (as opposed to "in a similar style" or "recolor this"), do not describe the reference from scratch in text, even carefully - word-only descriptions reliably drift details the user never asked to change. Confirmed directly (2026-09-15): asked to regenerate a building "exactly as the reference except add a roof," a text-only re-description silently changed the reference's white porch trim to brown. The fix was to actually edit the reference image instead of re-describing it:

1. Upload the reference PNG to get a usable image URL (Creative Claw's `get_upload_url` → `curl -X PUT` the local file bytes → `confirm_upload`).
2. Call `generate_image` with `image_url` set to that URL, and a prompt structured as: "Keep EVERYTHING else identical: [camera angle, facing direction, colors, proportions, materials]" followed by **only** the specific deltas being requested.
3. This item cannot be folded into a shared sheet (one generation call takes one source image) - it gets its own individual call, same as any other case where wording alone can't be trusted to nail the look.
4. Compare the result against the reference side-by-side before shipping - specifically check colors and material/trim choices, not just silhouette, since those are exactly what word-only drift breaks silently.

This applies to every new asset creation and every regeneration, not just corrections - if a request's own wording implies an exact match, treat it as one from the first attempt rather than waiting for the user to catch the drift.

---

## 4. Technical Asset Specifications

| Property                     | Value                                                            | Notes                                                  |
| :--------------------------- | :--------------------------------------------------------------- | :----------------------------------------------------- |
| **File Format**              | `PNG` (Portable Network Graphics)                                | Must support 8-bit alpha channel.                      |
| **Color Mode**               | `RGBA` (32-bit: 8-bit Red, 8-bit Green, 8-bit Blue, 8-bit Alpha) | No Indexed / Palette color modes.                      |
| **Dimensions**               | Exactly **$128 \times 128\text{ pixels}$**                       | Strictly square.                                       |
| **Max Item Dimension**       | **$104\text{ pixels}$**                                          | $\max(\text{width}, \text{height}) \le 104\text{ px}$. |
| **Padding Margin**           | Minimum **$12\text{ pixels}$**                                   | $(128 - 104) / 2 = 12\text{ px}$ on both axes.         |
| **Canvas Edge Transparency** | $\text{Alpha} = 0$ for $100\%$ of pixels on border               | `x=0, x=127, y=0, y=127` must have 0 alpha.            |
| **Resampling Filter**        | **Lanczos** (`Image.Resampling.LANCZOS`)                         | Prevents pixel blurring or aliasing shimmer.           |

---

## 5. Automated Extraction Pipeline

To extract items from concept sheets while **preserving internal dark grooves and shadows** (such as ribbed tanks, dark gunmetal tools, or hollow pipe fittings), **never** use simple naive color thresholding. Always use **Outside-In Perimeter Flood Fill**.

### 5.1 Python Extraction Algorithm

```python
import math
from PIL import Image

def extract_item_outside_in(sheet_img, cx, cy, radius, tol=20.0, max_dim=104, target_size=128):
    """
    Extracts an isolated 3D model with 100% pure transparent background,
    zero borders, zero clipping, and fully preserved internal shadows.
    """
    x0 = max(0, cx - radius)
    y0 = max(0, cy - radius)
    x1 = min(sheet_img.width, cx + radius)
    y1 = min(sheet_img.height, cy + radius)
    crop = sheet_img.crop((x0, y0, x1, y1)).convert("RGB")
    cw, ch = crop.size

    # 1. Sample background color from perimeter
    perim = []
    for x in range(cw):
        perim.append(crop.getpixel((x, 0)))
        perim.append(crop.getpixel((x, ch - 1)))
    for y in range(ch):
        perim.append(crop.getpixel((0, y)))
        perim.append(crop.getpixel((cw - 1, y)))
    bg_r = sum(p[0] for p in perim) / len(perim)
    bg_g = sum(p[1] for p in perim) / len(perim)
    bg_b = sum(p[2] for p in perim) / len(perim)
    bg = (bg_r, bg_g, bg_b)

    def is_bg(p):
        return math.sqrt((p[0]-bg[0])**2 + (p[1]-bg[1])**2 + (p[2]-bg[2])**2) < tol

    # 2. Outside-in Flood Fill starting from outer perimeter
    visited = [[False] * cw for _ in range(ch)]
    queue = []
    for x in range(cw):
        if is_bg(crop.getpixel((x, 0))):
            visited[0][x] = True; queue.append((x, 0))
        if is_bg(crop.getpixel((x, ch - 1))):
            visited[ch - 1][x] = True; queue.append((x, ch - 1))
    for y in range(ch):
        if not visited[y][0] and is_bg(crop.getpixel((0, y))):
            visited[y][0] = True; queue.append((0, y))
        if not visited[y][cw - 1] and is_bg(crop.getpixel((cw - 1, y))):
            visited[y][cw - 1] = True; queue.append((cw - 1, y))

    while queue:
        qx, qy = queue.pop(0)
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = qx + dx, qy + dy
            if 0 <= nx < cw and 0 <= ny < ch and not visited[ny][nx] and is_bg(crop.getpixel((nx, ny))):
                visited[ny][nx] = True
                queue.append((nx, ny))

    # 3. Foreground = unvisited pixels (with anti-aliased edge feathering)
    rgba = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    for y in range(ch):
        for x in range(cw):
            if not visited[y][x]:
                px = crop.getpixel((x, y))
                d = math.sqrt((px[0]-bg[0])**2 + (px[1]-bg[1])**2 + (px[2]-bg[2])**2)
                alpha = min(255, max(0, int(255 * (d - tol + 8) / 8.0))) if d < tol + 8 else 255
                rgba.putpixel((x, y), (px[0], px[1], px[2], alpha))

    # 4. Crop tightly to item bounds
    bbox = rgba.split()[3].getbbox()
    if not bbox:
        return None
    item_only = rgba.crop(bbox)

    # 5. Aspect-ratio preserving scale down to max_dim (104px)
    scale = min(float(max_dim) / item_only.width, float(max_dim) / item_only.height)
    nw = max(1, int(round(item_only.width * scale)))
    nh = max(1, int(round(item_only.height * scale)))
    resized = item_only.resize((nw, nh), Image.Resampling.LANCZOS)

    # 6. Center onto target square canvas (128x128)
    canvas = Image.new("RGBA", (target_size, target_size), (0, 0, 0, 0))
    canvas.paste(resized, ((target_size - nw) // 2, (target_size - nh) // 2), resized)
    return canvas
```

---

## 6. Naming Conventions & Folder Hierarchy

### 6.1 Standard Prefixes

All item filenames must be all-lowercase with underscore separators:

- `seed_<crop>.png`: Plantable seed packets or grain clusters (e.g., `seed_corn.png`).
- `crop_<name>.png`: Freshly harvested farm produce (e.g., `crop_tomato.png`).
- `food_<name>.png`: Cooked meals and processed foodstuffs (e.g., `food_bread.png`).
- `meat_<animal>.png`: Butchered cuts of livestock or wild game (e.g., `meat_beef.png`).
- `pelt_<animal>.png`: Raw skins and cured pelts (e.g., `pelt_cow.png`).
- `tool_<name>.png`: Usable hand tools and motorized equipment (e.g., `tool_axe.png`, `tool_chainsaw.png`).
- `mat_<material>.png`: Base construction & crafting materials (e.g., `mat_lumber.png`, `mat_stone.png`).
- `fuel_<type>.png`: Consumable fuels (e.g., `fuel_firewood.png`, `fuel_gasoline.png`).
- `fish_<species>.png`: Caught aquatic fish (e.g., `fish_trout.png`, `fish_bass.png`).
- `item_<name>.png`: General utility objects and machinery (e.g., `item_solar_panel.png`, `item_generator.png`).
- `icon_<name>.png`: HUD meters, resources, and status tokens (e.g., `icon_heart.png`, `icon_coin.png`).

### 6.2 The 11 System Categories & Target Folders

When adding a new icon, place it into the root directories:

- `c:\Users\casey\Desktop\Homesteader\HUD\assets\items\`
- `C:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader\UI\Icons\`

And distribute a copy into its specific subfolder:

```
assets/
├── farming/
│   ├── seeds/
│   ├── crops/
│   ├── produce/
│   ├── fertilizer/
│   └── irrigation/
├── ranching/
│   ├── animals/
│   ├── meats/
│   ├── pelts/
│   ├── byproducts/
│   └── feed/
├── logging/
│   ├── wood/
│   ├── fuel/
│   ├── saplings/
│   └── byproducts/
├── fishing/
│   ├── fish/
│   ├── tackle/
│   ├── bait/
│   └── equipment/
├── building/
│   ├── materials/
│   ├── structures/
│   ├── fencing/
│   ├── hardware/
│   └── roads/
├── tools/
│   ├── hand_tools/
│   ├── equipment/
│   └── measuring/
├── electricity/
│   ├── generation/
│   ├── storage/
│   ├── fuel/
│   └── wiring/
├── water/
│   ├── sources/
│   ├── storage/
│   ├── piping/
│   └── treatment/
├── sewage/
│   ├── waste/
│   ├── treatment/
│   └── drainage/
├── internet/
│   ├── satellite_antennas/
│   ├── routers_networking/
│   └── cabling/
└── hud/
    ├── status/
    ├── resources/
    ├── hotbar/
    ├── bars/
    ├── buttons/
    └── windows/
```

---

## 7. Automated Quality Assurance Linter

Run this check on any newly produced icon before adding it to the repository or importing into Unreal Engine.

```python
import sys
from PIL import Image

def validate_icon(path):
    errors = []
    try:
        im = Image.open(path)
    except Exception as e:
        return [f"Unable to open image: {e}"]

    # 1. Format check
    if im.format != "PNG":
        errors.append(f"Format is {im.format}; must be PNG")
    if im.mode != "RGBA":
        errors.append(f"Color mode is {im.mode}; must be RGBA")

    # 2. Dimension check
    if im.size != (128, 128):
        errors.append(f"Dimensions are {im.size}; must be exactly 128x128")

    # 3. Alpha bounds check
    alpha = im.split()[3]
    bbox = alpha.getbbox()
    if not bbox:
        errors.append("Image is completely transparent / empty")
        return errors

    x0, y0, x1, y1 = bbox
    item_w, item_h = x1 - x0, y1 - y0
    max_dim = max(item_w, item_h)
    if max_dim > 106:
        errors.append(f"Max item dimension is {max_dim}px; exceeds 104px (+2px tol)")

    # 4. Canvas edge transparency check (NO CLIPPING & NO BORDERS)
    w, h = im.size
    for x in range(w):
        if im.getpixel((x, 0))[3] != 0 or im.getpixel((x, h - 1))[3] != 0:
            errors.append("Non-zero alpha detected on top/bottom canvas edge")
            break
    for y in range(h):
        if im.getpixel((0, y))[3] != 0 or im.getpixel((w - 1, y))[3] != 0:
            errors.append("Non-zero alpha detected on left/right canvas edge")
            break

    return errors

if __name__ == "__main__":
    if len(sys.argv) > 1:
        errs = validate_icon(sys.argv[1])
        if errs:
            print("FAILED QA:")
            for err in errs: print(" -", err)
            sys.exit(1)
        else:
            print("PASSED QA: 128x128 RGBA, zero borders, pure transparent, perfectly padded.")
```

---

## 8. Unreal Engine 5 Import Presets

When importing `.png` files into Unreal Engine 5 (`Content/Homesteader/UI/Icons/`):

1. **Texture Group**: `UI`
2. **Compression Settings**: `UserInterface2D (RGBA)`
3. **Mip Gen Settings**: `NoMipmaps` (critical to keep icons razor-sharp at all resolutions)
4. **Filter**: `Default` or `Bilinear`
5. **sRGB**: `Enabled` (Checked)
6. **Max Texture Size**: `128` (or `0` for default unconstrained)

---

## 9. Summary Checklist for New Icons

When creating a new item icon:

- [ ] 3D low-poly faceted render with visible polygon planes and isometric 3/4 lighting.
- [ ] No borders, no slot boxes, no cards, no drop shadows.
- [ ] Rendered on solid dark slate chroma-key background `#2b3442` with $\ge 80\text{ px}$ spacing.
- [ ] Extracted using outside-in flood fill (preserving all internal dark grooves).
- [ ] Scaled with Lanczos to $\le 104\text{ px}$ and centered on a $128 \times 128\text{ px}$ canvas.
- [ ] 100% transparent edge boundary (`alpha = 0` on all outer pixels).
- [ ] Saved as 32-bit RGBA `.png` with correct prefix (`seed_`, `crop_`, `tool_`, etc.).
- [ ] Placed in `HUD/assets/items/`, `HUD/assets/<category>/<subcategory>/`, and `Homesteader/Content/Homesteader/UI/Icons/<category>/<subcategory>/`.
- [ ] Added to `DT_Items.csv` and verified in [index.html](file:///c:/Users/casey/Desktop/Homesteader/HUD/index.html).
