# Trash & Restore

**Deleting an asset does not erase it.** Deleted assets move to a trash store
and stay there until you explicitly remove them for good. This page explains
that model and how to work with it.

## How it works

When you delete an asset, its **entire folder is moved** — not copied and
deleted — from:

```
assets/<category>/<item_id>/     →     assets/_trash/<category>__<item_id>/
```

The manifest, icon, models, and README all travel together, byte for byte, so a
restore brings the asset back exactly as it was.

Because the catalog only walks the real category folders, anything sitting in
`_trash/` is **invisible to the app** while it's there. A trashed asset is gone
from the grid, from search, and from the catalog — but not from disk.

## The Trash indicator

The 🗑️ trash can in the status bar shows how many assets are currently deleted.
It **hides itself entirely when the trash is empty**, so there's no permanent
`0` cluttering the bar.

Click it to open the Trash panel.

## The Trash panel

The panel lists every deleted asset, newest first. Each row shows:

- the asset's icon and name
- its original location (`category/item_id`)
- when it was deleted, and how much space it occupies

Rows also have a per-row **♻️ Restore** button for one-off recovery.

## The three actions

<dl>
<dt>♻️ Restore Selected</dt>
<dd>Moves the checked items back to their original category folders, exactly
where they came from. The grid refreshes immediately so they reappear without a
reload.</dd>

<dt>✖ Permanently Delete</dt>
<dd>The only action in the entire app that actually erases asset data. Shows a
confirmation listing the affected names before doing anything.</dd>

<dt>🗑️ Delete All</dt>
<dd>Empties the trash completely. Also confirmed before running.</dd>
</dl>

Use **Select all** to work on the whole bin at once, and the readout beside it
tells you how many rows are checked.

<blockquote>

**Restore refuses to overwrite.** If an asset now exists at the destination —
say you deleted `crop_corn`, then created a new asset with the same ID — the
restore fails with an explanation rather than destroying the newer asset. That
newer asset is *not* in the trash, so overwriting it would lose data
irrecoverably. Rename or delete the existing item first, then restore.

</blockquote>

## What "permanent" means

Permanent deletion is a real, unrecoverable filesystem removal. Once you confirm
it, the folder is gone — there is no second-level bin and no undo.

For this reason the safe habit is: **deleting is routine, emptying the trash is
deliberate.** Leave things in the trash while you're unsure; empty it when
you're certain.

## Rows that can't be restored

If a folder in the trash store doesn't match the expected layout — for example
something placed there by hand rather than by the app — it still shows up in the
list, marked with a warning and a disabled checkbox. It's surfaced rather than
hidden so it isn't silently stranded, but it can't be restored automatically
because the app can't tell where it came from. It can still be permanently
deleted.
