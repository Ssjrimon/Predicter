# NAT DEF CONSOLE

A workbench for the Strategic Threat & Posture ledger. Everything in
`intel-ledger.json` — timeline, threads, horizon, briefs, node map, verification
log, sources — is readable in one place, and everything is writable from the same
place.

The ledger stays the only source of truth. The console reads it and writes it;
it never becomes a second copy of the truth.

---

## Two ways to run it

**File mode — zero setup.** Double-click `natdef-console.html`. The ledger is
baked into the file at build time. You can browse, search, and add entries; the
Save button downloads a fresh `intel-ledger.json` that you drop back into this
folder, replacing the old one.

**Server mode — writes persist.** Double-click `start-console.cmd` (or run
`python server.py`). Your browser opens the console, Save writes
`intel-ledger.json` in place, and a timestamped backup is taken first. Archive
links to the generated `daily-brief-*.html` files work in this mode too.

Server mode binds to `127.0.0.1` only. It has no authentication because it is a
single-user local workbench — don't expose the port.

---

## The files

| File | What it is |
|---|---|
| `natdef-console.html` | The built, standalone console. Regenerate after every brief. |
| `app-template.html` | Source template. Edit this, not the built file. |
| `build_app.py` | `ledger + template → natdef-console.html`. |
| `server.py` | Local server with the read/write API. |
| `start-console.cmd` | Windows launcher for server mode. |
| `smoke.py` | Headless test: every view renders, writes land, saves persist. |

Rebuild after each daily brief:

```
python build_app.py          # writes natdef-console.html
python build_app.py --check  # exit 3 if the built file is stale
```

`build_app.py` refuses to build if the ledger is malformed — wrong root type,
a list key holding an object, a missing `ledger_meta` — so a bad ledger fails at
the command line rather than silently in the browser.

---

## The write model

The console does not let raw material walk straight into the ledger, because
BRIEFING-PROTOCOL.md's Step 3 gate exists for a reason.

1. **Capture** (`+ Capture`, or the Intake queue) drops anything — a headline, a
   link, a rumour — into a new `inbox[]` collection with status `pending`. It is
   parked, not published.
2. **Promote** turns a pending capture into a real `timeline[]` or `horizon[]`
   entry, opening the normal form pre-filled so you can correct it, and writing a
   matching `verification_log[]` record at the same moment.
3. **Cut** marks a capture as rejected without deleting the trail.

Direct forms exist for every collection when you already know what you're
adding: timeline events, horizon items, threads, sources, verification checks,
judgment revisions, watchlist items, node history.

Nothing is written to disk until you press **Save**. The bar at the bottom tells
you when there are unsaved changes, and closing the tab with unsaved work warns
you first.

### New keys added to the ledger

Both are additive and ignored by `render.py`:

- `inbox[]` — the capture queue described above.
- `app_log[]` — a rolling audit of console writes (last 500), so you can see what
  the console changed and when.

---

## Notes

- Every string you type is HTML-escaped on the way into the ledger, matching the
  existing convention (`Homeland &amp; Hemisphere`). URLs that aren't `http(s)`
  are dropped rather than stored.
- No browser storage is used. The in-memory ledger is the working copy; Save is
  the only thing that makes a change durable.
- Keyboard: `/` focuses search, `1`–`9`/`0` jump between views, `Ctrl+S` saves,
  `Esc` closes a dialog.
- The webfonts load from Google Fonts. Offline, the console falls back to
  Georgia and a system monospace — it stays fully usable.

Run `python smoke.py` any time you change the template; it drives a headless
browser through all eleven views, both modes, the validation path, the escaping
path, and a real save round-trip.
