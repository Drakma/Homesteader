# Requests & Generation

Assets aren't generated inside this app. It **queues requests**; a Claude
session watching that queue picks them up and does the actual generation. This
page explains the whole loop.

## The queue model

A request moves through these states:

| State | Meaning |
| --- | --- |
| `pending` | Submitted, not yet batched. Nothing has been generated. |
| `queued` | Finalized into a batch and waiting for the watcher. |
| `in_progress` | A Claude session is actively working on it. |
| `done` | Finished. |

Nothing is generated until you **finalize** — this is deliberate, so icon
generation can be batched into a single image sheet instead of one paid call
per item.

## Requesting a new asset

**Request New Asset** in the banner opens a dialog asking for:

- **Name** and **item ID** (the ID auto-fills from the name but is editable)
- **Category**
- **Description** — the prompt that drives generation
- **Reference Asset** — optionally, an existing item to match the style of
- **Also request rigging** — queues a follow-up rigging pass once the model exists

## Requesting a growth group

**Request Growth Group** queues a *full lifecycle* — several linked stages
(sprout → growing → mature, for example) — as one request. You define the
group's metadata and give each stage its own reference up front, and the stages
arrive already linked rather than needing to be joined afterwards.

## The batch operations

With assets checked, the floating batch bar can queue work across many items at
once:

<dl>
<dt>🧊 Request Models</dt>
<dd>Queues 3D model generation for every checked asset.</dd>

<dt>Request Rigging</dt>
<dd>Queues Blender rigging. A picker lets you choose the rig type, since a
quadruped and a humanoid need different skeletons.</dd>

<dt>Bulk Request New</dt>
<dd>Takes the checked assets and one shared prompt, then queues one new-asset
request per item — each modelled on its source.</dd>

<dt>Make Group</dt>
<dd>Assembles the checked assets into a growth group, seeding the stage rows in
order.</dd>
</dl>

## The Requests indicator

The **Requests** item in the status bar is the entry point to the queue. It
shows a live summary while work is in flight:

```
2 asset requests (1 pending, 1 in progress)
```

When idle it falls back to a plain count of past requests. Click it to open the
full list.

## The request list

Each row shows the item, its status, when it was requested, and — where
applicable — the current step, any error, credit spend, and a stage badge for
linked growth stages.

Buttons at the top of the panel:

| Button | Effect |
| --- | --- |
| **Finalize & Queue for Generation** | Batches everything pending and notifies the watcher |
| ✅🗑️ | Clear completed requests only |
| 🗑️ | Delete all requests |

<blockquote>

**Deleting a request only clears the queue row.** It does not undo anything
already generated — if the asset was created, it's still on disk. To remove a
generated asset, delete it from the grid (which sends it to the trash).

</blockquote>

## Watching it happen

A batch completing raises a **batch complete** dialog listing what arrived.
Newly generated items are live-patched straight into the grid — no page reload
needed. The **Monitor** item in the status bar reports whether the watcher is
actually running and how recently it polled; if it says *not watching*, queued
requests will sit untouched until a session picks them up.
