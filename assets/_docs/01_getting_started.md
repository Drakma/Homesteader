# Getting Started

The **Homesteader Asset Kit** is the browser UI for browsing, editing, and
generating every asset in the game's catalog. This documentation covers each
part of the application in turn — what it does and how to use it.

## Launching

Run `HomesteaderAssetKit.bat` from the project root. It starts a local Python
server and opens a native desktop window pointing at it.

<blockquote>

**The app owns its own server.** It binds port `8088`. If something else is
already using that port, the app picks a free port instead — so you don't need
to start a server yourself.

</blockquote>

## The layout

The window is split into four regions:

| Region | What lives there |
| --- | --- |
| **Header** | Search bar, and the **Docs** button on its right |
| **Left sidebar** | Categories, Tags, Biomes, and Schemas tabs |
| **Center** | The asset grid (or the editor for the active sidebar tab) |
| **Footer** | Live status + the Requests and Trash indicators |

## What "disk is the source of truth" means

Every asset is a folder on disk:

```
assets/<category>/<item_id>/
├── <item_id>.json     ← the manifest: name, icon, models, properties
├── <item_id>.png      ← the 128×128 icon
├── SM_<...>.fbx       ← one or more 3D models
└── README.md
```

The app **reads this layout live** — it does not keep its own separate copy of
the catalog that could drift out of sync. When you rename, move, edit, or
delete an asset, the folder on disk changes and the app re-reads it. This is
why changes made outside the app (for example by a Claude session running its
own script) show up on their own within a few seconds.

## First steps

1. **Browse** — click a category in the left sidebar to filter the grid.
2. **Inspect** — click any card to open the full item modal: properties, 3D
   model, manifest JSON, and every file in the folder.
3. **Search** — press <kbd>/</kbd> anywhere to jump to the search bar.
4. **Request something new** — use **Request New Asset** in the banner to queue
   an asset for generation.

<blockquote>

**Tip:** the ⚠️ ghost-alert item in the status bar appears when the catalog
references an asset whose folder no longer exists on disk. Click it to review
and clean up those stale entries.

</blockquote>

## Where to go next

- **Browsing & Search** — the sidebar, filters, and finding things fast
- **The Item Modal** — everything you can do to a single asset
- **Requests & Generation** — how new assets get made
- **Trash & Restore** — deleting things without losing them
- **Schemas, Biomes & Tags** — the taxonomy layer
- **Status Bar** — reading the live health indicators
