# Homesteader - Multi-Agent Operating Guidelines

This file is automatically indexed by AI agents (Claude, Gemini, Antigravity, Cursor, Codex) working on the Homesteader project.

## Critical Project Directives

1. **Target Game Engine**:
   - **Unity 6 (`6000.6.0f1`)**.
   - World units: **1 Unit = 1 Meter** ($Y$-Up, $+Z$-Forward).
   - Character rigging: Unity Mecanim Humanoid (Mixamo) and Generic (Animal Animator/Blender quadruped).

2. **Generation Pipeline Policy (default-free, paid opt-in)**:
   - The **100% Free Stack** is the **DEFAULT** for all generation, via `assets/free_generator.py`.
   - 2D Icons: FLUX.1 [schnell] on Hugging Face Spaces (`black-forest-labs/FLUX.1-schnell`) / Google AI Studio / Pollinations.
   - 3D Models: Tencent Hunyuan3D-2.0 on Hugging Face Spaces (`tencent/Hunyuan3D-2`).
   - Paid services (**Meshy.ai**, **CreativeClaw.co**) are available as an explicit **opt-in per request** via the Request Asset / Request Growth Group dialog's "Generation Pipeline" dropdown. Only use them when a request is marked `PIPELINE=paid`, and always confirm the credit cost with the user before spending (see `PAID_ITEM_PIPELINE` in `assets/watch_asset_requests.py`).
   - Standardize icons to 128×128 RGBA (max 104px, 12px margin, perimeter alpha=0, no borders).

3. **Key Reference Documents**:
   - [API_REFERENCE.md](file:///C:/Users/casey/Desktop/Homesteader/assets/API_REFERENCE.md) - Complete REST API specification for `server.py` backend.
   - [FREE_PIPELINE_GUIDE.md](file:///C:/Users/casey/Desktop/Homesteader/docs/FREE_PIPELINE_GUIDE.md) - Complete step-by-step code and instructions.
   - [UNITY_INTEGRATION_GUIDE.md](file:///C:/Users/casey/Desktop/Homesteader/docs/UNITY_INTEGRATION_GUIDE.md) - Import settings, Mecanim setup, material & sprite configuration.
   - [ITEM_ICON_STYLE_GUIDE.md](file:///C:/Users/casey/Desktop/Homesteader/docs/ITEM_ICON_STYLE_GUIDE.md) - Visual rules (3D faceted, left-facing, clean alpha).
   - Master Catalog: `assets/README.md` (600 indexed assets across 16 categories).
