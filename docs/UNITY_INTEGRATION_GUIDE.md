# Homesteader - Unity 6 Asset Integration & Pipeline Guide

Comprehensive guide for integrating Homesteader's 3D models, animations, and 128×128 transparent UI icons into **Unity 6 (`6000.6.0f1`)**.

---

## 1. Engine Standards & Conventions

| Property              | Standard                                           | Notes                                                                                           |
| :-------------------- | :------------------------------------------------- | :---------------------------------------------------------------------------------------------- |
| **Engine**            | **Unity 6 (`6000.6.0f1`)**                         | Universal Render Pipeline (URP) or Built-in.                                                    |
| **World Scale**       | **1 Unit = 1 Meter**                               | Unreal was 1 unit = 1 cm. In Unity, 1 unit = 1 meter.                                           |
| **Coordinate System** | **Left-handed ($Y$-Up, $+Z$-Forward, $+X$-Right)** | Blender export handles this using `-Z Forward, Y Up`.                                           |
| **Pivots**            | **Base / Ground level ($Y_{min} = 0$)**            | Placed structures, foliage, and crops anchor cleanly to terrain. Handheld tools center on grip. |
| **UI Canvas**         | **Canvas Scaler (Scale With Screen Size)**         | Reference resolution: `1920 × 1080`.                                                            |

---

## 2. 2D UI Icons (`.png`) Import Settings

All icons in `assets/<category>/<item_id>/<item_id>.png` are 128×128 32-bit transparent RGBA PNGs.

### Recommended Unity Texture Import Settings:

1. Drag or copy icons into `Assets/UI/Icons/` or `Assets/AddressableAssets/Icons/`.
2. Select all icons in the Project window and set Inspector properties:
   - **Texture Type**: `Sprite (2D and UI)`
   - **Sprite Mode**: `Single`
   - **Pixels Per Unit**: `128` (or `100`)
   - **Mesh Type**: `Full Rect` (prevents tight polygon clipping)
   - **Extrude Edges**: `1`
   - **Generate Mip Maps**: `False` (Unchecked - ensures pixel-sharp icons at all resolutions)
   - **Filter Mode**: `Bilinear`
   - **Format**: `RGBA 32 bit` (or `Automatic` / `Truecolor`)
3. Click **Apply**.

---

## 3. 3D Models: GLB is the standard

**Models are `.glb` (textures embedded).** Mods load them at RUNTIME through glTFast (`GlbAssetResolver`): the game reads the file straight from the mod folder, lazily on first use, so no Unity import or prefab-generation step is needed and a runtime-installed mod brings its own models. Keep `.fbx` only for rigged/animated models (Humanoid/Generic). The FBX import settings below apply to those.

## 3b. FBX Import Settings (rigged/animated models only)

Rigged/animated models are exported from Blender as metric FBX files with embedded diffuse textures.

### Unity Model Inspector Settings:

- **Model Tab**:
  - **Scale Factor**: `1.0`
  - **Convert Units**: `Checked` (Unity maps 1 meter to 1 unit)
  - **Bake Axis Conversion**: `Checked` (preserves proper $Y$-Up orientation)
  - **Read/Write**: `Checked` if procedural terrain deformation or mesh colliders are used.
  - **Generate Colliders**: `Checked` for static structures/rocks; `Unchecked` for pickups and animated characters.
- **Rig Tab**:
  - **Humanoid Models** (Farmer, NPCs):
    - **Animation Type**: `Humanoid`
    - **Avatar Definition**: `Create From This Model`
    - Click **Configure...** to verify bones (Mixamo rigs auto-map 100% cleanly).
  - **Animals & Creatures** (Highland Calf, Sheep, Fish):
    - **Animation Type**: `Generic`
    - **Root Node**: `root` or `pelvis`
- **Animation Tab**:
  - For walk/run clips (`_Walk.fbx`, `_Run.fbx`):
    - Check **Loop Time** and **Loop Pose**.
    - Set **Root Transform Rotation** $\rightarrow$ **Bake Into Pose** (Based Upon: `Original`).
    - Set **Root Transform Position (Y)** $\rightarrow$ **Bake Into Pose** (Based Upon: `Original`).
    - Set **Root Transform Position (XZ)** $\rightarrow$ **Bake Into Pose** for in-place animations, or leave unchecked for root-motion.

---

## 4. ScriptableObject Item Definition (`ItemDefinition.cs`)

To mirror Homesteader's machine-readable `<item_id>.json` plugin manifests:

```csharp
using UnityEngine;

[CreateAssetMenu(fileName = "NewItem", menuName = "Homesteader/Item Definition")]
public class ItemDefinition : ScriptableObject
{
    [Header("Identity")]
    public string itemId;
    public string displayName;
    public string category;
    [TextArea(2, 4)]
    public string description;
    public Sprite icon;

    [Header("Physical Properties")]
    public float weightKg = 1.0f;
    public int maxStackSize = 99;
    public float baseValue = 10.0f;
    public bool isConsumable = false;
    public GameObject prefab3D;

    [Header("Growth Lifecycle")]
    public bool isGrowable = false;
    public string species;
    public int currentStage = 1;
    public int totalStages = 4;
}
```

---

## 5. Summary Checklist for Other Agents

When creating or importing any asset:

- [ ] 3D Model + texture is generated via **Meshy text-to-3D** (`tools/meshy_client.py`, `model_type='lowpoly'` — always).
- [ ] The user's `PROMPT='...'` was passed through as-is (not rewritten), with the standing rules appended.
- [ ] Credit cost was confirmed against `GET /api/meshy-balance` and approved by the user before spending.
- [ ] Icon is **rendered from the model** (`tools/render_icon_from_model.py`) and standardized to 128×128 RGBA.
- [ ] Model is scaled to metric (1 unit = 1 meter) and exported as GLB (FBX only if rigged/animated).
- [ ] `credits_used` was reported in the `done` payload so the cost summary stays accurate.
- [ ] No retired tools were invoked (`free_generator.py`, FLUX.1 [schnell], Hunyuan3D-2.0, Creative Claw).
