# Our Guides

The project's authoritative rule and spec documents. These are the same guides
exposed to AI agents through the MCP server's **`list_guides`** and
**`get_guide`** tools, so an agent and a person read the same source.

<blockquote>

**Read these before creating, generating, editing, or organizing assets.** The
icon and asset-creation guides define hard rules — icon dimensions, borders,
taxonomy, manifest shape — and an asset that violates them will fail validation
or look wrong in the grid.

</blockquote>

All 17 guides currently resolve on disk. Paths are relative to the project root.

## docs/ — rules and specs

### Agent instructions

<dl>
<dt>AGENTS.md</dt>
<dd>Operating instructions for AI agents working on this repo.</dd>

<dt>CLAUDE.md</dt>
<dd>Claude-specific project directives and conventions.</dd>
</dl>

### Asset creation and organization

<dl>
<dt>ASSET_CREATION_GUIDE.md</dt>
<dd>The end-to-end process for creating a new asset, from request to catalog entry.</dd>

<dt>ITEM_ICON_STYLE_GUIDE.md</dt>
<dd><b>The icon rules.</b> 128×128 RGBA, ≤104px content, 12px margin, zero
perimeter alpha, no borders, 3D-faceted style. This is the guide the icon
validator enforces.</dd>

<dt>ITEM_ORGANIZATION_GUIDE.md</dt>
<dd>How items and categories are organized — taxonomy and ID conventions.</dd>
</dl>

### Ground, grid and foliage

<dl>
<dt>GRID_AND_GROUND_STANDARDS.md</dt>
<dd>Grid alignment and ground-layer standards.</dd>

<dt>GROUND_TILES_GUIDE.md</dt>
<dd>Ground tile authoring — tiling, seams, and material setup.</dd>

<dt>GROUND_BLENDING_SETUP.md</dt>
<dd>Blend-layer configuration for ground materials.</dd>

<dt>FOLIAGE_GUIDE.md</dt>
<dd>Foliage generation and setup.</dd>
</dl>

### Pipeline and integration

<dl>
<dt>FREE_PIPELINE_GUIDE.md</dt>
<dd><b>The generation pipeline, step by step</b> — the free stack (FLUX.1
schnell for icons, Hunyuan3D-2.0 for models), including the exact calls. The
canonical reference for how assets actually get made.</dd>

<dt>UNITY_INTEGRATION_GUIDE.md</dt>
<dd>Importing into Unity 6: import settings, Mecanim rigging setup, materials
and sprite configuration.</dd>
</dl>

## assets/ — catalog references

<dl>
<dt>assets/GUIDE.md</dt>
<dd>Guide to the assets folder itself — layout and conventions.</dd>

<dt>assets/API_REFERENCE.md</dt>
<dd><b>Complete REST API specification</b> for the local server — every
endpoint, parameter, and response shape. The reference for anything
programmatic.</dd>

<dt>assets/README.md</dt>
<dd>The generated master catalog index across all categories. Produced by
<code>update_catalog_readme.py</code> — don't hand-edit it.</dd>
</dl>

### Sub-folder READMEs

<dl>
<dt>assets/_schemas/README.md</dt>
<dd>The schema and material-tag system.</dd>

<dt>assets/ground/README.md</dt>
<dd>Ground asset conventions.</dd>

<dt>assets/textures/README.md</dt>
<dd>Texture organization and naming.</dd>
</dl>

## Reading a guide as an agent

Through MCP, each guide has a `homesteader://guides/<name>` URI:

```
list_guides()                                    # every guide, with its URI
get_guide("docs/ITEM_ICON_STYLE_GUIDE.md")       # read one in full
get_guide("ITEM_ICON_STYLE_GUIDE.md")            # bare basename also resolves
```

Names are case-insensitive. A bare basename that matches more than one file —
several folders contain a `README.md` — is **refused rather than guessed**, and
the error lists the candidates so you can pick a full path.

<blockquote>

**Legacy docs are excluded on purpose.** The <code>UNREAL_*</code> guides and
session-state notes are not exposed over MCP, so "read the guides" can't return
superseded documentation. If a legacy guide still matters for your task, read it
directly from <code>docs/</code>.

</blockquote>
