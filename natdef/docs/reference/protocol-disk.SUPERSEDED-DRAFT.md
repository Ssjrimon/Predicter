# Briefing Protocol

**Put this file in the project. It is the instruction set for producing every daily brief.**
Any Claude session inside this project reads it and produces the same product the same way.

---

## Cadence and triggering

**The brief runs on a morning-sweep, midday-delivery cycle.** The scan starts at 07:00 local
time and checks the watchlist and every linked source for anything new. Target delivery —
brief written, ledger updated, dashboard and archive re-rendered — is by 13:00 local time. In
practice a single agentic run completes in minutes, so 13:00 is a stated SLA, not a literal
multi-hour job; the 07:00 fire time is what matters operationally.

### What Claude can and cannot do

Claude has no background process. It does not run between conversations, cannot wake itself,
and cannot scan anything on a timer of its own. **Every brief requires an external trigger.**
There is no version of this where scanning happens silently in the background on Claude's side.

If a brief has not been triggered, no scanning has occurred — regardless of how long it has
been. Never assume a brief reflects the current hour unless its stated cutoff says so.

### The only mechanism that works unattended

Scheduled tasks in **Claude Cowork**, created with `create_scheduled_task`.

**Correction — 10 Aug 2026.** This section previously stated, "verified against Anthropic's
help centre, 9 Aug 2026," that Cowork scheduled tasks run in the cloud and do not require the
desktop app open. That claim did not clear the Step 3 gate properly: it was checked against
general Cowork documentation, not the scheduling tool actually used to create this project's
task. The tool's own description states plainly: **scheduled tasks run while the app is open;
if the app is closed when a task is due, it runs on next launch.** That is the authoritative,
in-product constraint and it supersedes the earlier note. Practical effect: the desktop or
mobile app needs to be open (or opened at least once during the day) for the 07:00 sweep to
fire — it will not run against a fully closed app the way a cloud cron job would. See
`verification_log[]` for the correction entry. The 9 Aug entry distinguishing this from Claude
Code Desktop's locally-run tasks still stands; both products' tasks depend on the app being
reachable, they just differ in retry behavior (next-launch catch-up vs. skip entirely).

**Notification.** `create_scheduled_task`'s `notifyOnCompletion` (default `true`) pushes a
notification — including to the phone, if the Claude app has notifications enabled there — each
time the run finishes. No extra step is needed inside the brief's own prompt to get this; it is
a property of the scheduled task itself, set once at creation.

**Configuration — daily brief, 07:00 sweep / 13:00 delivery target:**

```
Produce today's Strategic Threat & Posture brief.

FIRST: locate BRIEFING-PROTOCOL.md and intel-ledger.json in
C:\Users\User\OneDrive\Documents\New folder\strategic-threat-briefing\.
If you don't yet have access to that folder, request it via request_cowork_directory
with that exact path before doing anything else.
If you cannot find BOTH files once you have access, stop and say which is missing.
Do not proceed without them. Do not reconstruct them from memory.

Then follow BRIEFING-PROTOCOL.md exactly:
- Sweep the watchlist from ledger_meta.last_cutoff to now
- Clear every claim through the Step 3 verification gate before writing
- Update intel-ledger.json first (including a new archive[] entry, Step 4.8, and any
  node_edges[]/node_history[] additions if today's sweep found a new connection or
  archival background, Step 4.7), then write daily-brief-YYYY-MM-DD.html using
  today's actual date
- Stamp the information cutoff on the masthead
- Late-file anything that broke since the last cutoff
- Run render.py, then validate.py; do not deliver if validate.py fails — fix the
  ledger and re-render instead
- Write all outputs back to the same folder

Unattended run: no clarifying questions. Produce the files and stop.
```

The refusal-to-proceed clause is mandatory. Without it a run that cannot reach the ledger will
fabricate one and produce a confident, sourceless brief. Visible failure beats silent invention.

**Run it manually once before scheduling.** The single thing being tested is whether the task
can reach the ledger.

**Cost.** Cowork consumes more usage allocation than chat. A ten-thread sweep with verification
is a heavy recurring job. Monitor Settings → Usage for the first week before adding a second
scheduled run.

### On hourly scanning

Scheduled tasks run on a fixed cadence, not continuously, and an hourly sweep across nine
threads would consume a large amount of quota to return nothing on most passes — geopolitical
threads do not move hourly, and the sources themselves (federal advisories, ministry
statements, IC assessments) publish on a slower clock than that.

The gap-closing problem is real, though, and it is solved by **lookback discipline** rather
than frequency. See below. Nothing falls through the space between briefs because each brief
covers the entire interval since the last one's cutoff, however long that interval was.

If a genuinely fast-moving situation warrants tighter coverage, add a second or third
scheduled run for that period and retire it afterward. Say so in the ledger when you do.

---

## Lookback discipline — how gaps are prevented

Every brief carries an **information cutoff** on its masthead, the way an ODNI assessment
does. That timestamp is the contract with the reader: everything before it was swept,
nothing after it was.

1. Read the previous brief's cutoff from `ledger_meta.last_cutoff`.
2. Sweep the full interval from that cutoff to now — not "the last 24 hours," the actual
   interval. If four days have passed, sweep four days.
3. Stamp the new cutoff on the masthead and write it back to `ledger_meta.last_cutoff`.
4. If the interval exceeds 48 hours, say so on the masthead: the reader needs to know they
   are getting a multi-day catch-up rather than a daily.

### The late file

Anything that broke **after** the previous brief's cutoff but **before** this one's leads the
items section under a `LATE FILE` tag, dated to when it actually happened rather than when it
was caught. This makes catch-up visible instead of laundering old news as today's.

If a scheduled run was missed entirely, the next brief says so on the masthead and runs the
late file to cover the gap. Missed runs are disclosed, never papered over.

---

## The standing job

Maintain a live picture of the global threat and posture environment, anchored to the primary
strategy and intelligence documents in `intel-ledger.json`, and deliver it each morning in a
form that can be absorbed in about ninety seconds.

The dashboard (`strategic-threat-briefing.html`) is the **standing picture**.
The daily brief is **what moved**.
The archive (`brief-archive.html`) is **every brief, browsable by date**, with a
built-in catch-up digest — pick a window (yesterday, 3 days, 7 days, a custom date,
all of it) and get the net thread movement and every item across that window, rather
than a stack of individual briefs to open. It exists because reading one brief a day
does not scale to someone who misses four.

The command center (`index.html`) is the **front door** — the one link worth bookmarking.
Today's bottom line, the ten-thread movement strip, and three cards into the other
pages, each carrying a live stat pulled from the ledger at render time. Open this one
first; it tells you in five seconds whether you need to go deeper anywhere else.

The node map (`node-map.html`) is **every region/actor as a force-directed graph**,
edges showing how they're connected (alliance, adversarial cooperation, conflict,
contested, hemisphere), sized and colored by severity. Click any node for its full
deep dive: history as far back as the ledger's archival research goes, recent items
since the founding documents, and dated horizon/forecast items — each with a date,
a source, and a "how long ago" readout. It exists so a region's *present* posture is
never read apart from *how it got there* and *where it's headed*.

---

## Step 1 — Read the ledger

Open `intel-ledger.json`. It carries:

| Key | What it holds |
|---|---|
| `sources[]` | Every primary document, with status `current` / `superseded` / `tracking` |
| `threads[]` | The nine tracked threads, each with intensity 1–10 and a direction |
| `revisions[]` | Places where a newer document changed an older judgment |
| `timeline_additions_2026[]` | Events added since the founding three documents |
| `horizon[]` | Dated things ahead, with a confidence label |
| `standing_watchlist[]` | The recurring search targets |
| `ledger_meta.brief_number` | Increment this each brief |
| `ledger_meta.last_cutoff` | Information cutoff of the previous brief — the sweep starts here |
| `archive[]` | One entry per brief, written in Step 4 — feeds `brief-archive.html` |
| `map_nodes[].severity` | 1-10, drives node size/color on `node-map.html` |
| `node_topics` | Maps a `map_nodes` id to the timeline/horizon category codes that populate its deep dive |
| `node_history` | Deep archival background per node (declassified/historical, pre-dates the founding docs) — hand-curated, sourced, never auto-generated |
| `node_edges[]` | The graph's connections: `{from, to, type, label}` — `type` is one of `alliance` / `adversarial-cooperation` / `conflict` / `contested` / `hemisphere` |

The ledger is the source of truth. Both the dashboard and the briefs are generated from it.

## Step 2 — Search against the watchlist

Work `standing_watchlist[]` plus anything the threads flag in their `watch` arrays.
Scale effort to how much is moving: a quiet day needs six or eight searches, an active one
needs fifteen to twenty.

**Always check for new primary documents.** A new ODNI assessment, National Defense Strategy,
National Security Strategy, posture statement, or equivalent from an allied government is the
highest-value find there is — it resets the baseline rather than adding to it.

Source discipline:

- **Primary** — the document itself. Fetch the PDF and read it. Never summarize a government
  document from a news article about the document.
- **Secondary-analytic** — ISW/AEI, CSIS, IISS and similar. Useful, attributed as analysis.
- **Secondary-aggregator** — daily trackers. Useful for tempo, but figures in an active conflict
  are contested. Attribute them and say who is claiming what.
- Government self-assessment is a **claim**, not a finding. "The White House states…" not
  "the operation achieved…". This holds regardless of which administration is speaking.

## Step 3 — Verification gate

**Nothing reaches the reader before it clears this.** Every candidate claim is walked back to
its origin before it is written, not after.

For each claim, establish:

1. **Origin.** Who first asserted this — an agency, a belligerent, a reporter, an aggregator?
   Find that source and open it. If the origin cannot be reached, the claim does not run.
2. **Hop count.** How many intermediaries sit between the origin and me? Two or more hops
   means the claim runs only with the chain named in the text.
3. **Date of the assertion, not the date I found it.** Aggregators re-date old material. A
   federal advisory published in April does not become an August event because press coverage
   peaked in August.
4. **Tense and status.** Is an operation ongoing or concluded? Check the issuing organization's
   own current page, not a reference work's summary of it. Live government pages carry the
   authoritative present tense.
5. **Contradiction sweep.** Actively look for a source that disagrees. Where two credible
   sources conflict, both run, named. Never harmonize silently.
6. **Attribution class.** Tag every claim: `verified-primary` · `attributed-claim` ·
   `contested` · `single-source` · `analyst-judgment`. The last one covers anything I assign
   myself, including thread intensities and directions.

**Hard rules:**

- A government summary of its own operation is `attributed-claim`, never `verified-primary`.
- A reference-work entry (encyclopedia, wiki) is a pointer to a source, never the source.
- If a claim cannot clear the gate, it is cut. A shorter brief is the correct outcome; a
  padded one is not.
- Log every check in `verification_log[]` in the ledger — including the ones that passed, and
  including corrections to earlier briefs. The log is part of the product.

**Always re-verify before each brief:** who currently holds the relevant offices, whether
named operations are still running, and whether any strategy document has been superseded.
These change without announcement and are the most common source of a stale brief.

### The gate also covers tooling

Claims about platforms, products and capabilities — Claude's own included — run through the
same gate as claims about the world. They fail in the same ways and are not exempt.

- **Fetch the page, do not reason from a search snippet.** Snippets are lossy. A snippet that
  omits a capability is not evidence the capability is absent.
- **Name the product before applying its constraint.** Claude Code, Cowork, Desktop, web and
  the API have materially different limits. A constraint verified for one is unverified for
  the others. This is the specific error made on 9 Aug 2026.
- **Treat rollout language as expiring.** "Rolling out over the coming weeks" is a claim with
  a short shelf life, not a standing fact. Re-check it, don't cite it.
- **Assume no prior.** Anything launched after the training cutoff is invisible without a
  fetch. Absence of recall is not evidence of absence.

## Step 4 — Update the ledger

Before writing anything the reader sees:

1. Append genuinely new events to `timeline_additions_2026[]`.
2. Revise `threads[].intensity`, `.direction`, `.status`, `.one_line` where they moved.
3. Add any new document to `sources[]`. If it supersedes one, mark the old entry
   `"status": "superseded"` and set `superseded_by`. **Never delete it** — the diff between
   an old and new assessment is often the most valuable thing on the page.
4. When a new document contradicts an older judgment, add a `revisions[]` entry.
5. Move `horizon[]` items that have happened into the timeline; add newly dated ones.
6. Bump `brief_number` and `last_updated`.
7. If today's sweep surfaced a new relationship between two nodes (a new pact, a
   new proxy tie, a severed partnership) or a genuinely new piece of archival
   background for a node's history, add it to `node_edges[]` / `node_history[]`
   now. This is occasional, not daily — most sweeps touch neither. Every
   `node_history` entry needs a real date, a source (`source_title` and, where one
   exists, `source_url`), and a `tier` (`verified-primary` for a fetched primary
   document, `attributed-claim` for reporting on one, `reference` for general
   historical record not re-verified this sweep — be honest about which).
8. Append an `archive[]` entry for this brief — same step, not an afterthought. It
   carries: `number` (sequential, no gaps), `date`, `weekday`, `file`, `cutoff`,
   `revision`, `bottom_line`, a full `threads` snapshot (every thread's intensity and
   direction as of this brief), `items` (headline + `sowhat` per item, mirroring
   Step 5), `changed`, `verification` (the tally by outcome), and
   `headline_correction` if one applies. An entry is written even on a quiet day —
   a gap in the numbering is a defect, not a quiet day (`ledger_meta.archive_rule`).

## Step 5 — Write the brief

One self-contained HTML file: `daily-brief-YYYY-MM-DD.html`.

**Structure, in order:**

1. **Masthead** — date, brief number, **information cutoff**, and the interval covered.
   If the interval exceeds 48 hours or a scheduled run was missed, state it here. Link to
   `brief-archive.html` so a reader can always reach the full run of briefs from today's.
2. **The bottom line** — three or four sentences, largest type on the page. The single
   assessment that matters. If someone reads nothing else, this is what they get.
3. **Movement board** — all nine threads as gauge columns, intensity as bar height, direction
   as an arrow, colored by direction. This is the five-second read and the signature element
   of the product. It never gets dropped, even on a quiet day.
4. **Items** — numbered, three to six of them, ordered by consequence. **Late file items
   run first**, tagged and dated to when they occurred. Each: a headline,
   two short paragraphs, and a **So what** line naming the implication. An item earns its
   place by changing something, not by being interesting.
5. **Changed on the board** — what this brief altered in the standing picture: threads that
   moved, judgments that were revised, documents that were added.
6. **Horizon** — dated things ahead, nearest first, each tagged with its confidence.
7. **Verification log** — what was checked against origin, what changed, what was cut, and any
   correction to a prior brief. Corrections are never quiet.
8. **Sources** — every document touched, linked, tiered, with attribution class.

**Voice:**

- Observe and hand over. State what is true; don't tell the reader what to feel about it.
- No padding, no cheerleading, no apologizing for a quiet day. A quiet day is a quiet day.
- Attribute contested figures. In an active war, casualty and damage numbers are claims.
- Distinguish *happened* from *stated goal* from *forecast*, visibly, every time.
- Where sources conflict, say so and give both. Don't resolve it silently.

## Step 6 — Render and validate

Every artifact in this folder is **generated**, not maintained. `strategic-threat-briefing.html`,
`brief-archive.html` and `node-map.html` are all output of `render.py`. Editing any of
them by hand is a defect: the next render discards the edit silently, which is precisely
the drift this replaced. `node-map.html`'s history/recent/future timelines are themselves
computed from `timeline[]`, `timeline_additions_2026[]` and `horizon[]` via `node_topics` —
only `node_edges[]` and `node_history[]` are hand-curated inputs; everything else on that
page is derived, never duplicated.

```
python3 render.py       # ledger -> dashboard + archive + node-map + index.html
python3 build_app.py    # ledger -> natdef-console.html (the offline console)
python3 validate.py     # gate; must pass before anything is delivered
```

`render.py` refuses to run on a ledger missing required keys (including `archive`), and fails
loudly on an unresolved template token in either template rather than shipping `{{CUTOFF}}` or
`{{ARCHIVE_COUNT}}` to the reader.

`build_app.py` bakes a full copy of the ledger into `natdef-console.html`, so unlike the
dashboard it goes stale on **every** ledger write, not only when the picture shifts — rebuild
it each brief. It refuses to build on a malformed ledger (wrong root type, a list key holding
an object, a missing `ledger_meta`), so a bad write fails at the command line rather than
silently in the browser, and `python3 build_app.py --check` exits 3 when the built file is
behind the ledger — the console's equivalent of the freshness checks below. If a run cannot
reach the folder, note it in `verification_log[]` and move on: the console is derived, the
next rebuild heals it, and server mode (`server.py`) reads the live ledger and never goes
stale at all.

`validate.py` enforces what used to depend on remembering to grep:

- thread intensity 1–10, direction from the valid set, no duplicate codes
- every `superseded` source carries a resolvable `superseded_by`
- every timeline citation resolves to a URL — a dead link fails the build
- `last_cutoff` present and correctly formatted; warns past 48 hours
- **retired claims cannot reappear** — swept across the dashboard, the archive, and every
  `daily-brief-*.html` on disk, not just the dashboard
- **event counts must match** between ledger and rendered dashboard
- **archive numbering has no gaps** — sequential from 1, one entry per brief, no duplicate dates
- every archive item's `thread` code is a declared thread; every entry's `file` exists on disk
- **archive entry counts must match** between `ledger.archive` and rendered `brief-archive.html`
- **every delivered brief has an archive entry** — checked in both directions: an archive
  entry pointing at a missing file fails, and a `daily-brief-*.html` on disk with no
  matching archive entry fails too, which is what would catch a skipped Step 4.8
- **every `node_edges[]` entry resolves to two real `map_nodes` ids**, isn't
  self-referential, and carries a `type`; every `node_history[]` entry has a date, a
  title, body text and is keyed to a real node id
- **node and edge counts must match** between the ledger and rendered `node-map.html`
- **`index.html`'s displayed brief number must match `ledger_meta.brief_number`** — the
  narrowest of the freshness checks, since the landing page has no single JS array to
  diff the way the other three do

Run `validate.py` before every delivery, not only on render days. Two dashboard-drift incidents
were caught by luck before this existed — the archive gets the same check for the same reason.

## Step 7 — Deliver

Run `python3 validate.py`. If it fails, fix the ledger and re-render — do not deliver around it.
Then write files to the outputs directory and present them. The brief always comes first.

Briefs already delivered are **never edited retroactively**. A brief revised after the fact stops
being evidence of what was known when. Corrections go in the next brief's verification log.

---

## The ten threads

| Code | Thread |
|---|---|
| `IR` | Iran / Hormuz |
| `RU` | Russia / Ukraine |
| `CN` | China / Taiwan |
| `KP` | North Korea |
| `HL` | Homeland / Hemisphere |
| `TR` | Terrorism |
| `EU` | Europe / NATO |
| `CY` | Cyber / Tech |
| `EN` | Energy / Markets |
| `AL` | Alliance architecture |

Add a thread only if something genuinely doesn't fit an existing one, and add it to the ledger
schema at the same time. Retire a thread by dropping its intensity, not by deleting it.

**`AL` filing rule.** An event *in* a theatre goes to that theatre's thread. An event that
*changes who is obligated to defend whom* goes to `AL`. The Mecca pact changes obligations —
`AL`. A Houthi strike on Najran is an event in a theatre — `TR`. `AL` was opened 9 Aug 2026 at
the two-item threshold, and the two pacts were reclassified out of `IR` at that point.

**`AL` direction semantics.** The direction vocabulary was built for threat threads, where
`escalating` means worsening. On `AL` it means *rate of structural change*: `escalating` =
rapid realignment, `holding` = stable architecture, `easing` = consolidation toward existing
structures. The redefinition is carried on the thread object in the ledger, not just here.

**Direction values:** `escalating` · `holding` · `easing` · `volatile`
(`volatile` means large movement without a consistent direction — reserve it for that, don't
use it as a hedge.)

---

## Standing constraints

- **Attribution over assertion.** Anything from a government, a belligerent, or an aggregator
  is attributed. The brief has no independent knowledge of a battlefield.
- **Politically even.** These documents are written by an administration about its own record.
  Report what they say and who said it; don't adopt their framing as the brief's voice, and
  don't editorialize against it either.
- **Forecasts stay labeled.** Every forward-looking item carries a confidence tag. A stated
  goal is not a prediction and a projection is not a plan.
- **Superseded material is kept.** The ledger is a record of how the assessment changed, which
  is frequently more informative than the current snapshot.
- **Gaps are stated.** If a thread had nothing worth reporting, say that. Don't manufacture
  an item to fill a slot.
