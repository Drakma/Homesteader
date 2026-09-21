# The Item Modal

Click any card in the grid to open it. The modal is the single place where you
can inspect and act on one asset.

## What it shows

<dl>
<dt>Header</dt>
<dd>The icon, name, item ID, category, and quick-action buttons.</dd>

<dt>3D viewer</dt>
<dd>An interactive preview of the asset's primary model. Drag to rotate, right-drag
to pan, scroll to zoom. If the model contains animation, it plays back.</dd>

<dt>Properties</dt>
<dd>Weight, stack size, value, footprint, and the various restore/modifier
stats, read straight from the manifest.</dd>

<dt>Utilities</dt>
<dd>Water, electricity, sewage, battery, and internet metrics — for buildings
and machines that consume or produce them.</dd>

<dt>Growth</dt>
<dd>For growable assets: species, stage count, the current stage, and the full
stage list with age ranges.</dd>

<dt>Manifest JSON</dt>
<dd>The raw JSON, collapsible. What's on disk is what you see.</dd>

<dt>Files</dt>
<dd>Every file physically present in the asset's folder, with sizes — icons,
models, textures, README, anything else.</dd>
</dl>

## Quick actions

| Button | Effect |
| --- | --- |
| 🔄 | Regenerate the icon following the HUD style rules |
| ✏️ | Rename the asset (name and/or ID) |
| 🗑️ | Move the asset to the trash |
| 📂 | Open the asset's folder in Windows Explorer |

<blockquote>

**Renaming is not cosmetic.** Renaming an item rewrites its manifest, renames
the icon and model files to match, updates growth-stage references pointing at
the old ID, updates the README, and fixes OBJ-internal material references. The
folder is renamed to match the new ID.

</blockquote>

## The primary model

An asset can hold several model files. The modal picks one to display as
*primary*, preferring in this order:

1. An animated file (`_walk` / `_run` in the filename)
2. A rigged file (`_rigged`)
3. Any plain mesh

This is why a rigged-and-animated asset shows the animation rather than a
static mesh — the most complete available version wins.

## Deleting from here

The 🗑️ button moves the asset to the **trash** rather than erasing it. A
confirmation dialog appears unless you've ticked *Don't ask again* (or held
<kbd>Shift</kbd> while clicking). Restore it any time from the Trash indicator
in the status bar — see **Trash & Restore**.
