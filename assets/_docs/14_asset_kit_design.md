# Asset Kit Design Document

## Purpose
This document outlines the design principles, architecture, and workflow for the Homesteader Asset Kit. It serves as a reference for developers, artists, and contributors who build, maintain, or extend the asset catalog.

## Scope
- Asset types: 3D models, textures, icons, prefabs, and scripts.
- Catalog structure: folder layout, naming conventions, and tagging.
- Build pipeline: import, validation, and export steps.
- Integration: Unity, Meshy, and API usage.
- Governance: contribution guidelines, versioning, and documentation.

## Design Principles
1. **Modularity** – Assets are self‑contained and can be reused across projects.
2. **Consistency** – Naming, folder layout, and metadata follow a single, documented standard.
3. **Scalability** – The system can grow to thousands of assets without performance loss.
4. **Transparency** – All steps are logged and auditable.
5. **Extensibility** – New asset types or pipelines can be added with minimal friction.

## Asset Catalog Structure
```
assets/
├── building/
│   ├── house/
│   │   ├── house_01.json
│   │   ├── house_01.obj
│   │   └── house_01.png
│   └── barn/
│       ├── barn_01.json
│       ├── barn_01.obj
│       └── barn_01.png
├── textures/
│   ├── wood/
│   │   └── oak.png
│   └── metal/
│       └── steel.png
└── ground/
    └── tiles/
        └── grass_tile.png
```
- Each asset folder contains a JSON manifest (`<asset_id>.json`) describing metadata.
- The manifest references the model, textures, and icon.
- Icons are 128×128 PNGs with 32‑bit RGBA.

## Naming Conventions
- **Asset ID**: `mat_<category>_<name>_<index>` e.g., `mat_steel_stud_framing_01`.
- **File names**: Use snake_case, match the asset ID.
- **Folders**: Lowercase, singular nouns.

## Metadata Schema
```json
{
  "id": "mat_steel_stud_framing_01",
  "category": "building",
  "name": "Steel Stud Framing",
  "description": "A modular steel framing component.",
  "tags": ["steel", "framing", "construction"],
  "files": {
    "model": "steel_stud_framing.obj",
    "icon": "steel_stud_framing.png",
    "textures": ["steel_texture.png"]
  }
}
```

## Build Pipeline
1. **Import** – Artists export models/textures to the asset folder.
2. **Validation** – Run `homesteader-asset-kit__validate_item_icon` and `homesteader-asset-kit__save_item_manifest`.
3. **Tagging** – Use `homesteader-asset-kit__save_material_tag` for recipe tags.
4. **Indexing** – Execute `homesteader-asset-kit__sync_catalog_index` to regenerate `assets/README.md`.
5. **Deployment** – Assets are packaged for Unity via the `unity-mcp` tools.

## Integration with Unity
- Use the `unity-mcp` server to import assets.
- Run `unity-mcp` commands to generate prefabs and assign materials.
- Unity console logs are captured via the MCP server.

## Contribution Workflow
1. Fork the repository.
2. Create a new branch for the asset.
3. Add files following the structure and naming conventions.
4. Commit and push.
5. Open a pull request.
6. CI will run validation and build tests.

## Documentation & Guides
- See `docs/ASSET_CREATION_GUIDE.md` for detailed asset creation steps.
- `docs/ITEM_ICON_STYLE_GUIDE.md` covers icon requirements.
- `docs/ITEM_ORGANIZATION_GUIDE.md` explains folder layout.
- `assets/API_REFERENCE.md` documents the public API.

## Future Work
- Automate icon generation from 3D models.
- Expand tagging system to support recipe dependencies.
- Add a web UI for browsing the catalog.

---

*Prepared by the Homesteader Asset Kit Team*