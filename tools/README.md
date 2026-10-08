# tools/

Asset generation, validation, and deployment scripts. Moved here from
`HUD/scripts/` during the HUD teardown (2026-09-17).

**These scripts write into `assets/` and into the Unity project's
`Assets/Homesteader/` tree.** They must be run from the repo root so their
`dirname(__file__)`-relative paths resolve correctly:

```powershell
cd C:\Users\casey\Desktop\Homesteader
python tools\validate_schema.py appliances
```

## What's here

| Group                 | Scripts                                                                                              | Purpose                                                                                            |
| --------------------- | ---------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| **Asset Kit Runtime** | `server.py`, `app.py`, `asset_kit_mcp.py`, `watch_asset_requests.py`, `build_exe.py` | Local API server, desktop WebView2 wrapper, MCP server, request queue watcher. (The catalog builder `build_kit.py` lives in `assets/`, beside the `index.html` it generates.) |
| **Pipelines**         | `meshy_client.py`, `render_icon_from_model.py`                                                        | Meshy text-to-3D pipeline (model + texture), and 3D model icon renderer (Blender headless)          |
| **Generators**        | `generate_*.py` (24)                                                                                 | Build `.obj`/`.mtl` meshes + 128×128 icons per category batch                                      |
| **Validators**        | `validate_*.py` (11)                                                                                 | Enforce icon rules, mesh bounds, schema conformance, material tags                                 |
| **Extractors**        | `extract_*.py` (6)                                                                                   | Slice icon sheets / sprite sheets into individual transparent PNGs                                 |
| **Catalog**           | `build_*catalog*.py`, `update_*html.py`, `generate_gallery_data.py`, `update_catalog_readme.py`      | Regenerate `assets/README.md` and `gallery/index.html`                                             |
| **Guardrails**        | `check_syntax.py`, `python.cmd`                                                                      | Catch broken Python before it reaches a commit; make `python` resolve in any shell               |
| **Deploy**            | `deploy_icons.py`, `organize_item_assets.py`                                                         | Distribute icons to all required locations                                                         |
| **Item data**         | `items_*.py` (8), `item_catalog_data*.py` (4)                                                        | Category item definitions consumed by the generators                                               |

## Path conventions

Scripts derive their roots from their own location:

```python
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
```

so `tools/generate_homestead_buildings.py` writes to
`<root>/assets/building/structures/` and
`<root>/Homesteader/Assets/Homesteader/Assets/Building/Meshes/`.

A few older scripts still hardcode absolute `C:\Users\casey\Desktop\Homesteader\...`
paths. Those work but should be migrated to the `__file__`-relative form when touched.

## The one pipeline (Meshy text-to-3D - everything costs money)

There is no free pipeline any more. `free_generator.py`, FLUX.1 [schnell],
Hunyuan3D-2.0 and CreativeClaw concept images are **retired** — do not call them.

The only generation route is **Meshy text-to-3D** via `tools/meshy_client.py`
(`create_text_to_3d()`), which returns the model **and its texture** in one task.
Always `model_type='lowpoly'`. Pass the user's `PROMPT='...'` through as-is and
append the standing technical rules. The icon is then rendered from the model.

Confirm the credit cost against `GET /api/meshy-balance` before spending - see
`PAID_ITEM_PIPELINE` in `tools/watch_asset_requests.py`.

| Script                                                                                                                                         | Role                                        |
| ---------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| `meshy_client.py`                                                                                                                              | Meshy API wrapper (text-to-3D, image-to-3D) |
| `meshy_tree_clutter_pipeline.py`                                                                                                               | Tree/clutter generation batch               |
| `deploy_batch.py`, `deploy_saplings.py`, `deploy_trees_and_stumps.py`, `deploy_planted_saplings_and_lifecycle.py`, `deploy_new_fuel_assets.py` | Deploy Meshy output into `assets/`          |
| `monitor_and_deploy_refined.py`, `refine_all_trees.py`                                                                                         | Monitor refine tasks and deploy results     |
| `test_api_key.py`, `test_imagen.py`, `test_image_gen.py`                                                                                       | API connectivity probes                     |

Meshy output lands in `scratch/meshy_output/` (gitignored).

See `docs/MESHY_PIPELINE_GUIDE.md` for the full step-by-step pipeline.


## cpu3d (free rigged creature models)

`cpu3d_client.py` calls the cpu3d MCP server (image -> low-poly rigged, animated GLB, free). Connection lives in `cpu3d_connection.json` (gitignored; holds the token). The asset kit exposes it as `POST /api/cpu3d-generate` and `GET /api/cpu3d-status`, driven by the Model (CPU) button in the asset popup.
