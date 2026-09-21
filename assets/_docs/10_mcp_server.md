# MCP Server & Endpoints

The **Homesteader Asset Kit MCP server** exposes this project's asset tooling to
AI agents over the Model Context Protocol. Instead of an agent reading and
writing files by hand — guessing at paths and manifest shapes — it calls typed
tools that know the real layout and validate what they write.

<blockquote>

**Why this exists:** an agent editing `assets/building/foo/foo.json` directly can
get the folder wrong, forget the `id`/`category` fields, or write an icon the
engine can't use. Every tool on this page closes one of those gaps, and several
add hard validation on the way through.

</blockquote>

## Configuration

The server is registered in `.mcp.json` at the project root:

```json
{
	"mcpServers": {
		"homesteader-asset-kit": {
			"command": "C:/Python313/python.exe",
			"args": ["tools/asset_kit_mcp.py"],
			"env": { "PYTHONPATH": "tools" }
		}
	}
}
```

It runs over **stdio** — it has no network port and no HTTP surface, so there's
nothing to secure beyond local process access.

## The instruction contract

The server ships with a mandatory instruction for connecting agents:

<blockquote>

Homesteader project guides are MANDATORY. Before generating, editing, or
organizing any asset, list the guides via `list_guides` and read the relevant
ones. The icon and asset-creation guides define hard rules (128×128 RGBA
icons, no borders, taxonomy, manifests).

</blockquote>

So the expected flow for any asset work is: **list the guides, read the relevant
ones, then act.** The tools below assume that order.

## Tools

### Asset requests

<dl>
<dt>list_asset_requests(status)</dt>
<dd>Lists generation requests from the queue. <code>status</code> filters by
<code>all</code> (default), <code>pending</code>, <code>in_progress</code>, or
<code>done</code>. Returns every request dict plus a count.</dd>

<dt>update_asset_request(request_id, status, step, item_id, meshy_credits, creative_claw_credits)</dt>
<dd>Updates a request and <b>moves its file between the status folders
automatically</b>. Setting <code>status="done"</code> also stamps
<code>completed_at</code>, and updates the matching entry inside its batch file
if the request has a <code>batch_id</code>. Credit arguments <i>accumulate</i> —
passing <code>meshy_credits=5</code> twice records 10, not 5.</dd>

<dt>finalize_asset_requests()</dt>
<dd>Groups every pending request into one batch file in
<code>_asset_requests/batches/</code> and notifies watchers. Returns the new
<code>batch_id</code> and item count. Fails if nothing is pending.</dd>
</dl>

### Catalog and manifests

<dl>
<dt>get_catalog_item(category, item_id)</dt>
<dd>Reads an item's manifest <i>and</i> lists its real files on disk with sizes
and extensions. This is the tool to call before editing anything — it shows what
actually exists rather than what a manifest claims.</dd>

<dt>save_item_manifest(category, item_id, manifest)</dt>
<dd>Writes a manifest, creating the folder if needed. It <b>overwrites three
fields regardless of what you pass</b>: <code>id</code> and <code>category</code>
are forced to match the directory, and <code>icon</code> is forced to
<code>&lt;item_id&gt;.png</code>. This makes it impossible to write a manifest
whose identity disagrees with its location.</dd>
</dl>

### Material tags

<dl>
<dt>list_material_tags()</dt>
<dd>Returns every recipe material tag from <code>_schemas/material_tags.json</code>.</dd>

<dt>save_material_tag(tag_name, members)</dt>
<dd>Creates or updates a tag. The name is normalized (leading <code>#</code>
stripped, lowercased). Members are catalog item IDs.</dd>
</dl>

### Validation and synchronization

<dl>
<dt>validate_item_icon(category, item_id)</dt>
<dd>Checks an icon against the Homesteader icon standards and returns a list of
specific violations. See <b>What the icon validator enforces</b> below.</dd>

<dt>sync_catalog_index()</dt>
<dd>Runs <code>update_catalog_readme.py</code> to rebuild
<code>assets/README.md</code> from what's on disk. Run this after any change that
adds, removes, or renames assets.</dd>
</dl>

### Project guides

<dl>
<dt>list_guides()</dt>
<dd>Lists every active guide, grouped into <code>docs</code> and
<code>assets</code>, each with its <code>homesteader://guides/&lt;name&gt;</code>
URI and whether the file actually exists on disk.</dd>

<dt>get_guide(name)</dt>
<dd>Reads a guide in full. Accepts a full display name
(<code>docs/ITEM_ICON_STYLE_GUIDE.md</code>) or a bare basename
(<code>ITEM_ICON_STYLE_GUIDE.md</code>); case-insensitive.
<b>Ambiguous basenames are refused rather than guessed</b> — several folders
contain a <code>README.md</code>, so asking for "README.md" returns the list of
candidates instead of picking one.</dd>
</dl>

## Resources

Two URI schemes expose the same guides as MCP resources, for clients that
subscribe to resources rather than calling tools:

| URI                           | Serves                                                               |
| ----------------------------- | -------------------------------------------------------------------- |
| `homesteader://guides/{name}` | A `docs/` guide, falling back to any unambiguous basename            |
| `homesteader://assets/{name}` | An `assets/` guide (slash-safe, for paths like `_schemas/README.md`) |

Both return markdown. A missing guide returns a readable
`# Guide not found` block rather than an error, so an agent can tell "absent"
from "failed".

## What the icon validator enforces

`validate_item_icon` is the strictest tool here, and the one worth running
before shipping any generated icon. It checks:

- **Format is PNG**, not just a `.png` filename
- **Mode is RGBA** (32-bit) — an RGB icon fails
- **Size is exactly 128×128**
- **The image isn't fully transparent**
- **Max content dimension ≤ 106px** — the 104px rule with 2px tolerance
- **Every pixel on all four edges has alpha 0** — no borders, no frames

It returns `valid: true` plus an empty `errors` list, or the specific
violations. Each failure message names the actual value it found, so a failure
tells you what to fix rather than just that something is wrong.

## Excluded guides

`list_guides` deliberately omits legacy and session-state documents — the
`UNREAL_*` guides and working notes. Only rules and specs that are still
authoritative are exposed, so an agent reading "the guides" can't be misled by
superseded documentation.

## Self-test

The server has a built-in smoke test covering five tools end to end:

```
python tools/asset_kit_mcp.py --test
```

It exercises `list_asset_requests`, `get_catalog_item`, `validate_item_icon`,
`list_material_tags`, and `sync_catalog_index`, asserting on each. Run it after
changing the MCP server or moving the catalog layout.

<blockquote>

**Note:** the self-test asserts against real assets — it expects
<code>building/mat_steel_stud_framing</code> to exist and the
<code>steel_framing</code> tag to be defined. If those are renamed or deleted,
the test fails for a legitimate reason rather than a code fault.

</blockquote>
