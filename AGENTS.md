# Homesteader - Multi-Agent Operating Guidelines

This file is automatically indexed by AI agents (Claude, Gemini, Antigravity, Cursor, Codex) working on the Homesteader project.

## Critical Project Directives

1. **Target Game Engine**:
   - **Unity 6 (`6000.6.0f1`)**.
   - World units: **1 Unit = 1 Meter** ($Y$-Up, $+Z$-Forward).
   - Character rigging: Unity Mecanim Humanoid (Mixamo) and Generic (Animal Animator/Blender quadruped).

2. **Generation Pipeline Policy (Meshy only, everything costs money)**:
   - **There is no free pipeline any more.** The 100% Free Stack (FLUX.1 [schnell] + Tencent Hunyuan3D-2.0) and `tools/free_generator.py` are **RETIRED**. Do not call them, do not offer them.
   - **The one and only pipeline is Meshy text-to-3D** (`tools/meshy_client.py` -> `create_text_to_3d()`), which returns the **model AND its texture** in a single task.
   - **The user's prompt is the input.** A request carries a `PROMPT='...'` marker written by the user. Pass that prompt to Meshy **as-is** and **append** the standing technical rules so it generates properly. Never rewrite or replace the user's intent.
   - **LOW POLY IS MANDATORY, ALWAYS, NO EXCEPTIONS**: `model_type='lowpoly'` on every generation. Never `standard` or `smart-topology`.
   - **The icon is rendered FROM the model**, never generated separately: `tools/render_icon_from_model.py <model_path> assets/<category>/<item_id>/<item_id>.png` poses the textured model in Blender (isometric 3/4 front view, top-left key lighting).
   - **Cost confirmation is mandatory before spending**: check `GET /api/meshy-balance`, present the estimated cost and resulting balance, and wait for explicit approval. A user passing a prompt is not approval of a specific spend.
   - Standardize icons to 128×128 RGBA (max 104px, 12px margin, perimeter alpha=0, no borders).
   - **External View Mandatory**: 100% of generations for buildings and objects must be an **EXTERNAL VIEW** from the outside showing the complete outer facade/walls/roof, with **NO internal structure, no cutaways, and no indoor camera perspective** (unless an exterior view can naturally see inside through open doors/windows).

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
   - **Always use absolute paths in every command you run or suggest** - file arguments, `read`/`edit` targets, and script invocations alike. Do not rely on an inherited working directory; a tool may start in a different directory than the last one, and a relative path then silently reads or writes the wrong file. Anchor to `C:\Users\casey\Desktop\Homesteader\...` explicitly.
   - **Never inline a multi-line PowerShell script into a single command line.** PowerShell collapses nested `{ }` blocks and the command fails with `Missing closing '}' in statement block or type definition`. Write the script to a `.ps1` file and invoke that file instead (see the shell-quoting rule below).

   **Shell resolution (Windows PowerShell 5.1)**:
   - `python` and `git` are **NOT** on `PATH` in a bare shell - running them as bare names fails with `CommandNotFoundException`. Use the absolute interpreter `C:\Python313\python.exe` for Python and `tools\python.cmd` for git-backed tooling.
   - `pwsh` and `powershell` are **NOT** resolvable as bare command names either, even though PowerShell 5.1 may be the running shell. Invoke PowerShell by its absolute path: `& "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File <script.ps1>`.
   - **Run PowerShell scripts from a file, never as an inline one-liner.** Passing a multi-line block as a single `-Command` argument collapses its structure. This is the same class of failure as the docstring collapse above: fix the invocation (write a file), not the symptom (re-quote and retry).

5. **Growth / structure groups: `stages/` folders are RESOURCES, not catalog assets.**
   - A migrated group owns its scheme exactly once, in its own manifest at `assets/<category>/<group>/<group>.json`, with each stage's files under `stages/<stage_folder>/`.
   - `build_full_catalog()` in `tools/server.py` **skips the `stages` directory outright** (`GROWTH_STAGES_DIRNAME`), so **stage items are never in `ALL_ITEMS`**. Never resolve a stage by looking it up in `ALL_ITEMS` - it will always return nothing.
   - Read a stage's `icon` / `model` straight from the group manifest's `stages[]` entries, and build asset paths as `assets/<category>/<group>/<resource>/<icon>`. The `stages[]` entry already declares both, so no lookup is needed.
   - `save_growth_group` (`/api/growth-groups`) expects each stage to be its own catalog asset folder and rewrites every member's manifest. It is the **wrong** endpoint for a migrated group - it cannot resolve the stage items and will destroy the group. Edit a migrated group's scheme via `/api/save-group-scheme` instead.
   - Structure groups (`assets/structures/*`) are 4-stage building lifecycles: `struct_foundation` -> `struct_framing` -> `struct_walls` -> `struct_complete`.

6. **`assets/index.html` is a hand-edited SOURCE file, not a build artifact.**
   - The app reads it. Its git history contains real UI commits ("smart presets", "autofill", "stage 4 min age"). Never describe it as generated, and never run a script that rewrites it without asking first.
   - `assets/build_kit.py` is its generator and **refuses to overwrite a file with local edits** (tracked via a `.generated.sha256` sidecar). A refusal exits 1 and changes nothing. Use `--out <path>` to write elsewhere, or `--force` to override deliberately.
   - If you need generated HTML, write it to a different filename. Do not "sync" it into `index.html`.

7. **Key Reference Documents**:
   - [API_REFERENCE.md](file:///C:/Users/casey/Desktop/Homesteader/assets/API_REFERENCE.md) - Complete REST API specification for `server.py` backend.
   - [MODDING_GUIDE.md](file:///C:/Users/casey/Desktop/Homesteader/docs/MODDING_GUIDE.md) - Mod format, manifest fields, content types, load order, scripting interface.
   - [MESHY_PIPELINE_GUIDE.md](file:///C:/Users/casey/Desktop/Homesteader/docs/MESHY_PIPELINE_GUIDE.md) - Complete step-by-step code and instructions.
   - [UNITY_INTEGRATION_GUIDE.md](file:///C:/Users/casey/Desktop/Homesteader/docs/UNITY_INTEGRATION_GUIDE.md) - Import settings, Mecanim setup, material & sprite configuration.
   - [ITEM_ICON_STYLE_GUIDE.md](file:///C:/Users/casey/Desktop/Homesteader/docs/ITEM_ICON_STYLE_GUIDE.md) - Visual rules (3D faceted, left-facing, clean alpha).
   - Master Catalog: `assets/README.md` (600 indexed assets across 16 categories).
