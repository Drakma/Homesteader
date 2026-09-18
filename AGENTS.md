# Homesteader - Multi-Agent Operating Guidelines

This file is automatically indexed by AI agents (Claude, Gemini, Antigravity, Cursor, Codex) working on the Homesteader project.

## Critical Project Directives

1. **Target Game Engine**:
   - **Unity 6 (`6000.6.0f1`)**.
   - World units: **1 Unit = 1 Meter** ($Y$-Up, $+Z$-Forward).
   - Character rigging: Unity Mecanim Humanoid (Mixamo) and Generic (Animal Animator/Blender quadruped).

2. **Generation Pipeline Policy (default-free, paid opt-in)**:
   - The **100% Free Stack** is the **DEFAULT** for all generation, via `tools/free_generator.py`.
   - 2D Icons: FLUX.1 [schnell] on Hugging Face Spaces (`black-forest-labs/FLUX.1-schnell`) / Google AI Studio / Pollinations.
   - 3D Models: Tencent Hunyuan3D-2.0 on Hugging Face Spaces (`tencent/Hunyuan3D-2`).
   - Paid services (**Meshy.ai**, **CreativeClaw.co**) are available as an explicit **opt-in per request** via the Request Asset / Request Growth Group dialog's "Generation Pipeline" dropdown. Only use them when a request is marked `PIPELINE=paid`, and always confirm the credit cost with the user before spending (see `PAID_ITEM_PIPELINE` in `tools/watch_asset_requests.py`).
   - Standardize icons to 128×128 RGBA (max 104px, 12px margin, perimeter alpha=0, no borders).
   - **External View Mandatory**: 100% of concept generations for buildings and objects must be an **EXTERNAL VIEW** from the outside showing the complete outer facade/walls/roof, with **NO internal structure, no cutaways, and no indoor camera perspective** (unless an exterior view can naturally see inside through open doors/windows). Never pass an interior concept to 3D reconstruction.

3. **Mod System** (runtime content loading):
   - Mods live in `<persistentDataPath>/Mods` and `<StreamingAssets>/Mods`, as **folders or `.zip` archives**.
   - Every mod has a `mod.json` manifest at its root (id/name/version/author/date/description + a `contents[]` list).
   - At startup `ModManager` discovers, validates, orders (dependencies first), and applies mods **before terrain generation**, so modded biomes are baked into the world.
   - Code lives in `Homesteader/Assets/Scripts/Modding/`. Merge rules are centralized in `ModLoader.cs`; core content always wins over a colliding mod id.
   - Example mod: `mods/example_lavender_homestead/`.

4. **Editing Rules (tooling-enforced, read before editing Python)**
   - **Run the syntax gate after any edit to a `.py` file**: `python tools\check_syntax.py <path>`. It names the file, line, and cause, and flags collapsed triple-quote delimiters explicitly. `git commit` runs it automatically over staged files and blocks on a real parse error; `git commit --no-verify` bypasses it.
   - **Never emit a triple-quoted block inside a string literal.** That is what collapses `"` to `"` in transit. To change a docstring, anchor an edit on the lines *around* it, or rewrite the block as `#` comments. Do not build quote characters dynamically (`chr(34) * 3`) to work around this - fix the edit, not the symptom.
   - **`python` and `git` resolve in any shell** via `tools/python.cmd` and the PowerShell profile. Use `python`, not a hardcoded absolute path, in commands you suggest to the user. The absolute interpreter is `C:\Python313\python.exe` (as configured in `.mcp.json`).
   - **Do not save Python files with a UTF-8 BOM.** Python 3 will not run them (`invalid non-printable character U+FEFF`). The gate reports these as warnings.

5. **`assets/index.html` is a hand-edited SOURCE file, not a build artifact.**
   - The app reads it. Its git history contains real UI commits ("smart presets", "autofill", "stage 4 min age"). Never describe it as generated, and never run a script that rewrites it without asking first.
   - `assets/build_kit.py` is its generator and **refuses to overwrite a file with local edits** (tracked via a `.generated.sha256` sidecar). A refusal exits 1 and changes nothing. Use `--out <path>` to write elsewhere, or `--force` to override deliberately.
   - If you need generated HTML, write it to a different filename. Do not "sync" it into `index.html`.

6. **Key Reference Documents**:
   - [API_REFERENCE.md](file:///C:/Users/casey/Desktop/Homesteader/assets/API_REFERENCE.md) - Complete REST API specification for `server.py` backend.
   - [MODDING_GUIDE.md](file:///C:/Users/casey/Desktop/Homesteader/docs/MODDING_GUIDE.md) - Mod format, manifest fields, content types, load order, scripting interface.
   - [FREE_PIPELINE_GUIDE.md](file:///C:/Users/casey/Desktop/Homesteader/docs/FREE_PIPELINE_GUIDE.md) - Complete step-by-step code and instructions.
   - [UNITY_INTEGRATION_GUIDE.md](file:///C:/Users/casey/Desktop/Homesteader/docs/UNITY_INTEGRATION_GUIDE.md) - Import settings, Mecanim setup, material & sprite configuration.
   - [ITEM_ICON_STYLE_GUIDE.md](file:///C:/Users/casey/Desktop/Homesteader/docs/ITEM_ICON_STYLE_GUIDE.md) - Visual rules (3D faceted, left-facing, clean alpha).
   - Master Catalog: `assets/README.md` (600 indexed assets across 16 categories).
