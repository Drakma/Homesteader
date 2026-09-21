# Technical: How the Interface Retrieves Data

This documents how the browser UI gets its data from the local server: the
request flow, the caching layers, the polling cadences, and what happens when
things fail.

## Architecture

```
┌─────────────────────┐      HTTP (localhost)      ┌──────────────────────┐
│  index.html         │ ─────────────────────────► │  server.py           │
│  (WebView window)   │ ◄───────────────────────── │  SimpleHTTPRequest-  │
│                     │        JSON                │  Handler             │
│  ALL_ITEMS in RAM   │                            │  _catalog_cache      │
└─────────────────────┘                            └──────────┬───────────┘
                                                              │ reads
                                                              ▼
                                                     assets/ (folder tree)
```

There is **no database and no websocket**. The server is a
`SimpleHTTPRequestHandler` subclass that answers `/api/*` with JSON and
everything else from disk. The app is a self-contained HTML file with a large
inline script — no build step, no bundler, no framework.

The server binds port **8088** with `allow_reuse_address = True`, so a restart
doesn't trip over leftover sockets in `TIME_WAIT`.

## The central read: /api/catalog

This is the one request that matters most. On page load:

```
loadCatalog()  →  GET /api/catalog  →  ALL_ITEMS = data.items
```

Everything in the UI is derived from that one in-memory `ALL_ITEMS` array — the
grid, the sidebar counts, search, duplicate detection. There is no per-item
fetch during normal browsing.

### The three-layer cache

| Layer | Scope | Invalidated by |
| --- | --- | --- |
| **`_catalog_cache` (server)** | In-process dict of the built catalog | Explicit invalidation, or the **10-second TTL** |
| **`ALL_ITEMS` (client)** | The page's working set | A reload, or an explicit refresh action |
| **Disk** | The actual truth | — |

The server's cache exists because a full walk — every category, every item,
every manifest — takes a few seconds at this catalog size. Rebuilding on every
page load would be too slow.

### Why there's a TTL *and* explicit invalidation

Both are needed, because they cover different writers:

- **Explicit invalidation** (`invalidate_catalog_cache()`) is called by every
  code path *inside* the server that changes an item — create, delete, move,
  rename, growth edits. It's immediate.
- **The 10-second TTL** covers writes from *outside* the process — a Claude
  session running its own script, or the request watcher finishing a batch.
  Those can't reach into the server's memory, so the TTL bounds how stale the
  cache can get.

Without the TTL, an external write would stay invisible until someone happened
to invalidate. Without explicit invalidation, the app's own edits would lag up
to 10 seconds.

## The endpoint surface

All endpoints return `{"success": true|false, ...}`. Failures carry an `error`
string and a meaningful HTTP status.

### Reads

| Endpoint | Returns |
| --- | --- |
| `GET /api/catalog` | Every item, built live from manifests |
| `GET /api/catalog-entry?category=&id=` | One freshly-built item — used to live-patch a new asset in without a reload |
| `GET /api/item-files?category=&item_id=` | The files physically in one item's folder |
| `GET /api/asset-requests` | The generation queue |
| `GET /api/trash` | Soft-deleted assets, with total size |
| `GET /api/docs` / `GET /api/docs?slug=` | The docs section list / one doc's markdown |
| `GET /api/ping` | Liveness, used for the server latency readout |
| `GET /api/watcher-status` | Is the request watcher running, and how long ago it polled |
| `GET /api/claude-usage`, `GET /api/meshy-balance` | Quota / credit readouts |

### Writes

Everything that changes data is `POST` with a JSON body:

`/api/delete-asset`, `/api/delete-batch`, `/api/rename-asset`,
`/api/trash/restore`, `/api/trash/purge`, `/api/trash/purge-all`,
`/api/asset-requests`, `/api/finalize-asset-requests`, `/api/move-asset`,
plus the schema/biome/tag/growth-group mutation endpoints.

### Cache control

Reads are issued with `cache: "no-store"` — and the server sends no-store
headers anyway. There is deliberately **no HTTP caching layer**; query-string
busting was a recurring source of "why am I seeing the old value" bugs.

## Live-patching instead of reloading

Rather than refetching the whole catalog after a change, the app patches
`ALL_ITEMS` in place:

| Action | Client-side effect |
| --- | --- |
| Delete | Splice out of `ALL_ITEMS`, re-render |
| Rename / move | Refetch that one entry via `/api/catalog-entry` |
| Batch completes | Fetch each new item and push it in |

This is why a newly generated asset appears in the grid without a reload — see
`checkForCompletedBatches`.

The trade-off: the client's `ALL_ITEMS` is a **snapshot**, so it can drift from
disk if something changes outside the app. The **↻ Refresh** button forces
`loadCatalog()` to re-read everything, which is the manual escape hatch.
**Shift+click** on it does a hard page reload instead, picking up HTML/CSS/JS
edits too.

## Polling cadences

Nothing uses a websocket; the UI polls on fixed intervals, chosen so idle
traffic stays near zero while active work stays responsive.

| What | Interval | Why |
| --- | --- | --- |
| **Asset requests** | **2s while work is in flight, else 10s** | Adaptive: tight while a job is running, relaxed when idle |
| **Trash count** | 20s | Deletions refresh it immediately, so this only catches changes from elsewhere |
| **Status bar** | 30s | Server ping, watcher heartbeat, quotas |
| **Ghost alert** | 30s | Catalog references with no folder on disk |

The adaptive request poll is the interesting one — `refreshAssetRequestsIndicator()`
returns whether anything is active, and the next timeout is scheduled from that:

```js
function scheduleAssetRequestsPoll() {
  clearTimeout(ariPollTimer);
  refreshAssetRequestsIndicator().then(inProgress => {
    ariPollTimer = setTimeout(scheduleAssetRequestsPoll, inProgress ? 2000 : 10000);
  });
}
```

It's a **self-rescheduling `setTimeout`, not `setInterval`**, so a slow response
can't stack up overlapping requests.

## Failure handling

The design principle throughout: **a failed read degrades one indicator, it
never blanks the page.**

<dl>
<dt>Catalog load retries</dt>
<dd><code>loadCatalog()</code> retries up to <b>3 times</b> with backoff
(400ms × attempt). It's the only fetch that retries, because it's the only one
whose failure leaves the UI unusable.</dd>

<dt>Per-indicator isolation</dt>
<dd>Every poll runs in its own <code>try/catch</code>. A dead Meshy API shows
"unavailable" in the status bar and changes nothing else.</dd>

<dt>Failure is visible, not silent</dt>
<dd>The trash panel shows the actual error text rather than an empty list, so
"nothing here" and "couldn't load" are distinguishable.</dd>

<dt>Stale-response guard</dt>
<dd>The docs panel checks <code>docsActiveSlug</code> after awaiting a fetch, so
a slow response can't overwrite a section the user already navigated away
from.</dd>
</dl>

## Client error reporting

The page installs a global `window.onerror` that POSTs to
`/api/client-error`, which prints to the server console with a stack trace.
A JS error in the running app therefore shows up in the server's terminal, not
just the WebView's devtools.

## Reading the request queue

Request state comes from the filesystem, not a field:

```
pending/ → in_progress/ → done/     (in _asset_requests/)
```

`/api/asset-requests` lists those folders. A request only advances when a
Claude session actually moves the file, so **the UI reflects real progress
rather than "was submitted"** — which is why a queue that never moves is a
watcher problem, not a UI problem. The **Monitor** status item is the check:
it reads `watcher_heartbeat.json` and reports the watcher offline if the
heartbeat is older than **15 seconds**.

## Notable implementation details

<dl>
<dt>BOM sensitivity</dt>
<dd>A manifest saved with a UTF-8 BOM fails <code>json.load</code> and the item
silently vanishes from the catalog. Worth knowing when a file looks fine in an
editor but the app can't see it.</dd>

<dt>Icon URLs are folder-relative</dt>
<dd>Manifests store <code>icon</code> as a bare filename. The server prefixes
<code>category/item_id/</code> when building entries, and the grid builds
<code>assets/&lt;category&gt;/&lt;item_id&gt;/&lt;icon&gt;</code> to display it. A
renamed item therefore needs its icon file renamed too — which the rename
handler does.</dd>

<dt>Fallback rendering</dt>
<dd>The docs panel uses <code>marked</code> from a CDN when available and falls
back to a built-in renderer otherwise, so a CDN failure degrades to plain-but-
readable text instead of a blank panel.</dd>

<dt>Ghost entries</dt>
<dd>A catalog item whose folder no longer exists is a "ghost". The app doesn't
hide this — it surfaces it as a clickable ⚠️ alert, since silently dropping the
reference would make the problem invisible.</dd>
</dl>
