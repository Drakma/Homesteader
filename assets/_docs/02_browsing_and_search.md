# Browsing & Search

## The sidebar

The left sidebar has four tabs, each switching what the grid shows:

<dl>
<dt>🗂️ Categories</dt>
<dd>The main view. Lists every asset category with a live item count, and
expands to show species subfolders inside a category.</dd>

<dt>🏷️ Tags</dt>
<dd>Virtual groupings. A tag stands in for a set of interchangeable real items —
for example, any of several wood types that satisfy the same recipe slot.</dd>

<dt>🌍 Biomes</dt>
<dd>Spawn/environment definitions. Each biome can list which assets belong to
it.</dd>

<dt>🧬 Schemas</dt>
<dd>Per-category field definitions — the contract every manifest in that
category is validated against.</dd>
</dl>

## Searching

The search bar at the top filters whatever the active tab is showing:

- **Assets** — matches by name, item ID, or tag
- **Biomes** — matches by biome name or ID
- **Schemas** — matches by schema name
- **Tags** — matches by tag name

Press <kbd>/</kbd> from anywhere to focus the box. The <kbd>✕</kbd> button
clears it. The placeholder always tells you what's currently being searched, so
you can tell at a glance which mode you're in.

## Selecting assets

Each card has a **✓ checkbox**. Checked assets collect into a selection, and a
floating action bar appears at the bottom of the screen with batch operations:

| Action | What it does |
| --- | --- |
| **Move All** | Drag this button onto any sidebar category to move every checked asset there |
| **🧊 Request Models** | Queue 3D model generation for all checked assets |
| **Make Group** | Build a growth group from the checked assets |
| **Request Rigging** | Queue rigging (Blender skeleton/animation) for all checked |
| **Bulk Request New** | Create new assets modelled on the checked ones |
| **Delete All** | Move every checked asset to the trash |

**Select All Shown** in the banner checks everything currently visible — handy
after filtering down to a subset.

## Filters and badges

Cards carry badges that flag things worth knowing:

- **3D** — the asset has at least one model file
- **4-Stage Growable** — it participates in a growth lifecycle
- **Duplicates** — another asset looks near-identical (same name or model)
- **Combine** — two models scored as likely parts of one whole

<blockquote>

**Note:** duplicate and combine detection compares model *signatures*, not just
names. Two assets can share a name and still not be flagged, and two
differently-named assets can be — the model files are what decide it.

</blockquote>

## Duplicates view

Selecting the **duplicates** filter shows only assets flagged as near-identical,
grouped by cluster. This is the fastest way to audit the catalog for
accidental redundancy introduced by repeated generation requests.
