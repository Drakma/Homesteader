# Status Bar

The footer along the bottom of the window carries the live health of the whole
system. Everything here updates on its own — nothing needs a manual refresh.

## Left side — the services

| Item | Meaning |
| --- | --- |
| **Server** | Round-trip time to the local app server. Green means it's responding; red means it isn't. |
| **Monitor** | Whether the asset-request watcher is running, and how many seconds ago it last polled. |
| 🧊 **Meshy** | Live credit balance, queried directly from Meshy's API. Click to refresh now. |
| 🤖 **Claude** | Your Claude usage quota, read from the Claude Status VSCode extension's cache. Shows 5-hour and 7-day windows. |
| ✨ **Gemini** | Gemini and Antigravity quotas, read from the local Antigravity daemon. |

<blockquote>

**Why some of these are "last known" rather than live:** a service with no
local API key the server can use can't be polled on its own. Creative Claw is
the clearest example — it's reached only through an MCP connector inside a
Claude session, so the app shows the last balance a session reported rather than
a genuinely live figure. Meshy *does* have a usable API, so its balance is real.

</blockquote>

## Right side — the work indicators

<dl>
<dt>⚠️ Ghost alert</dt>
<dd>Appears only when the catalog references assets whose folders no longer
exist on disk. Click to review and remove those stale entries.</dd>

<dt>Requests</dt>
<dd>The asset request queue. Shows a live summary while work is in flight —
<i>2 asset requests (1 pending, 1 in progress)</i> — and a plain count when
idle. Click to open the full list.</dd>

<dt>🗑️ Trash</dt>
<dd>How many assets are currently deleted. Hidden entirely while empty. Click to
open the restore panel.</dd>

<dt>↻ Refresh</dt>
<dd>Re-reads the catalog and all status readouts without reloading the page.
<b>Shift+click</b> does a full page reload instead, which also picks up any
edits to the app's own HTML/CSS/JS.</dd>
</dl>

## Reading the dots

The small coloured dots next to Server and Monitor are the fastest health check:

- **green** — healthy and current
- **red** — down, or a service that was expected but isn't responding

If **Monitor** goes red while you have requests queued, nothing will happen to
them until a watching session picks the queue back up. That's the first thing to
check when a request seems stuck.

## Ghost entries

A ghost entry is a catalog reference with no matching folder — the catalog
*thinks* an asset exists but its files are gone. This usually happens when
something deleted a folder outside the app.

The ghost alert lists them so you can clear the stale references. It's a
cleanup tool, not a data-recovery one: the files are already absent, and the
dialog only removes the dangling catalog entry.
