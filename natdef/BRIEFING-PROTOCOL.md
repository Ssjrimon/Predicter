# Briefing Protocol

**Put this file in the project. It is the instruction set for producing every daily brief.**
Any Claude session inside this project reads it and produces the same product the same way.

---

## Rule 0 — One project, one schedule, one home

This protocol lives in the Claude Project named **Nat Def**. That project is the only
home for this product. Everything the briefing operation owns — the ledger, the source
documents, this protocol, and every brief ever produced — lives there and nowhere else.

**Three things follow from that, and a run that violates any of them is a bad run:**

1. **One project.** If a second project exists that also produces briefs, it is a fork, and
   forks silently diverge — two ledgers, two `last_cutoff` values, two brief numbering
   sequences. Merge it into Nat Def and delete it. Never start a briefing conversation
   outside this project.

2. **One schedule.** Exactly one recurring scheduled task drives the daily brief. Two
   schedules pointed at the same project is not redundancy — it is two runs racing to
   increment `brief_number` and write `last_cutoff`, and the loser's sweep interval is
   destroyed. If a tighter cadence is genuinely needed for a fast-moving situation, add a
   *sweep-only* task that writes nothing to the ledger (see below), and retire it afterward.

3. **One home for output.** Every brief is written back into this project (Step 7). A brief
   that exists only as a chat attachment, only in a session workspace, or only on the user's
   disk is lost the moment that conversation scrolls away.

4. **One ledger.** `intel-ledger.json` exists in two copies for the same operational reason
   this protocol document does — one in the project, one in the working folder — and the same
   discipline applies: they are the same file, and a divergence between them is a correctness
   bug. Unlike this document, the ledger changes on every single run, so the risk is not a
   one-time fork but routine drift. **The working-folder copy is authoritative whenever both
   are reachable in the same session**, because it is the one `render.py` and `validate.py`
   actually check. After any run that updates the working-folder ledger, Step 7 must write the
   same content back to the project copy in the same pass — a working-folder update that never
   reaches the project is exactly as bad as a project update that never reaches the working
   folder. If a session cannot reach the project (no route to it, or a write is refused), or
   cannot reach the working folder (no device bridge), it must say so in `verification_log[]`,
   and a later session with access to both copies must complete the sync before the next
   scheduled run is trusted to treat either copy as ground truth. **Never produce a full
   numbered brief from a ledger copy you cannot confirm is current.** If you can reach one copy
   but not the other, that is itself the fork condition Step 1's continuity check exists to
   catch — treat an unreachable cross-check as a reason to stop and disclose in a short
   situational note that does not touch `brief_number`, not as permission to proceed on the
   copy you happen to have as if it were the full ledger.

   This failed once, on 16 Aug 2026: a cloud-based scheduled task was created without first
   confirming whether a desktop-bound one already existed for this project — the exact check
   point 2 above requires. One did. The cloud task fired against the project's copy of the
   ledger, which had gone stale since roughly Brief 002 because no prior run had synced a
   Step 7 write back through it after the working-folder ledger diverged ahead. Reading only
   the stale copy, it produced a genuine, individually well-verified brief, numbered it
   "Brief 003," and described the interval as a 173-hour, six-missed-run gap — both the
   numbering and the gap were artifacts of the stale copy, not of reality; the working-folder
   ledger was at Brief 006, one normal cycle behind. Separately, within the same hour, the
   pre-existing desktop-bound task produced the real Brief 007, caught the fork by reading the
   project's copies directly, and disclosed it in full rather than renumbering over it — but
   could not write its own output back into the project, leaving Step 7 incomplete on that side
   too. See `verification_log[]`, 16 Aug 2026, for the full account and the reconciliation, and
   `briefs/INDEX.md` for where the retracted brief is preserved.

**This protocol is itself covered by Rule 0.** Two copies exist by necessity — one in the
project, one in the working folder next to `render.py` — and they are the same file. When this
document changes, write **both** copies in the same pass. They forked once, on 15 Aug 2026:
the project copy had drifted to nine threads and had never heard of `render.py` or
`validate.py`, while the folder copy lacked this rule and the Step 7 filing discipline. They
were merged back into this text. A divergence between them is a correctness bug, not a
housekeeping detail, because the scheduled run reads the project copy.

**On the many separate task threads.** Each scheduled run starts a fresh session with no
memory of the previous one — that is how scheduled tasks work and it cannot be changed. This
is not a problem to solve; it is the reason the ledger exists. Continuity lives in
`intel-ledger.json`, not in conversation history. As long as every run reads the ledger first
and writes the ledger and the brief back, the scattered threads are just disposable
workspaces and nothing is lost between them.

---

## Cadence and triggering

**The brief is an afternoon product.** The live schedule fires at **15:00 local**, and the
run covers everything since the previous brief's information cutoff — sweep, ledger, render,
validate and delivery in one pass. In practice a single agentic run completes in minutes, so
the fire time is what matters operationally, not a delivery window.

**Corrected 15 Aug 2026.** This section previously described a 07:00 sweep with a 13:00
delivery target, which no longer matched the scheduled task actually running. Where a stated
cadence and the live task disagree, the live task is the fact; fix the document.

### What Claude can and cannot do

Claude has no background process. It does not run between conversations, cannot wake itself,
and cannot scan anything on a timer of its own. **Every brief requires an external trigger.**
There is no version of this where scanning happens silently in the background on Claude's side.

If a brief has not been triggered, no scanning has occurred — regardless of how long it has
been. Never assume a brief reflects the current hour unless its stated cutoff says so.

### The only mechanism that works unattended

**One** scheduled task in the Claude app, pointed at this project. That is the external
trigger, and per Rule 0 there should be exactly one of them.

Before creating any scheduled task for this project, **check whether one already exists** and
retire the duplicate rather than adding to it. Scheduled tasks created on the desktop app and
scheduled tasks created in the cloud are two separate lists — a session can only see the
cloud list, so an apparently-empty list does not prove there are no desktop schedules running.
Confirm both.

**Correction — 10 Aug 2026.** This section previously stated, "verified against Anthropic's
help centre, 9 Aug 2026," that Cowork scheduled tasks run in the cloud and do not require the
desktop app open. That claim did not clear the Step 3 gate properly: it was checked against
general Cowork documentation, not the scheduling tool actually used to create this project's
task. The tool's own description states plainly: **scheduled tasks run while the app is open;
if the app is closed when a task is due, it runs on next launch.** That is the authoritative,
in-product constraint and it supersedes the earlier note. Practical effect: the desktop or
mobile app needs to be open (or opened at least once during the day) for the scheduled sweep to
fire — it will not run against a fully closed app the way a cloud cron job would. See
`verification_log[]` for the correction entry. The 9 Aug entry distinguishing this from Claude
Code Desktop's locally-run tasks still stands; both products' tasks depend on the app being
reachable, they just differ in retry behavior (next-launch catch-up vs. skip entirely).

**Notification.** `create_scheduled_task`'s `notifyOnCompletion` (default `true`) pushes a
notification — including to the phone, if the Claude app has notifications enabled there — each
time the run finishes. No extra step is needed inside the brief's own prompt to get this; it is
a property of the scheduled task itself, set once at creation.

**Configuration — daily brief, 15:00 local:**

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
- Run render.py, then build_app.py, then validate.py; do not deliver if validate.py
  fails — fix the ledger and re-render instead
- File the brief and INDEX.md line back into the project (Step 7) before delivering
- Write all outputs back to the same folder
- If writing to the project is refused or the project cannot be reached at all, do not
  treat that as permission to skip Step 7 silently: write every output to the working
  folder in full exactly as normal, state the gap plainly in verification_log[], and stop.
  A later interactive session — one with both project and working-folder access —
  completes the sync. This happened on 16 Aug 2026; see Rule 0, point 4.

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

Scheduled tasks run on a fixed cadence, not continuously, and an hourly sweep across ten
threads would consume a large amount of quota to return nothing on most passes — geopolitical
threads do not move hourly, and the sources themselves (federal advisories, ministry
statements, IC assessments) publish on a slower clock than that.

The gap-closing problem is real, though, and it is solved by **lookback discipline** rather
than frequency. See below. Nothing falls through the space between briefs because each brief
covers the entire interval since the last one's cutoff, however long that interval was.

If a genuinely fast-moving situation warrants tighter coverage, add a **sweep-only** task for
that period and retire it afterward. It is safe to run alongside the daily because it touches
nothing:

```
Run a sweep only, per BRIEFING-PROTOCOL.md. Do not produce a brief.
Do not write to intel-ledger.json and do not advance last_cutoff.
Check the watchlist for anything that would change a thread's direction or
intensity. If nothing qualifies, say so in one line and stop.
```

Say so in the ledger when you add or retire one.

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
| `threads[]` | The ten tracked threads, each with intensity 1–10 and a direction |
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

**Continuity check, before anything else.** Read `ledger_meta.last_cutoff` and
`ledger_meta.brief_number`. If either is inconsistent with the most recent brief listed in
`briefs/INDEX.md` — a gap in numbering, a cutoff later than the last filed brief, two briefs
carrying the same number — a duplicate or forked run has occurred. Reconcile it, note it in
`verification_log[]`, and say so on the masthead. Do not quietly renumber over it.

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

**Reminder added during the 6 Sep 2026 Claude Code migration, per the Brief 012 postmortem:**
Step 4.2 (revise `threads[]`) and Step 4.8 (append the archive entry) are two separate writes.
Brief 011 did 4.8 and skipped 4.2 — the archive snapshot and the brief's own prose said KP and
HL had moved, but the live `threads[]` object never changed, and nothing caught it for four
days. `validate.py` (below) now asserts every thread's live intensity/direction equals the
newest archive entry's snapshot for that code specifically so this class of error fails loudly
instead of silently. Treat Step 4 as a checklist to run in full, not a single mental motion.

## Step 5 — Write the brief

One self-contained HTML file: `daily-brief-YYYY-MM-DD.html`.

**Structure, in order:**

1. **Masthead** — date, brief number, **information cutoff**, and the interval covered.
   If the interval exceeds 48 hours or a scheduled run was missed, state it here. Link to
   `brief-archive.html` so a reader can always reach the full run of briefs from today's.
2. **The bottom line** — three or four sentences, largest type on the page. The single
   assessment that matters. If someone reads nothing else, this is what they get.
3. **Movement board** — all ten threads as gauge columns, intensity as bar height, direction
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
- **every thread's live intensity/direction equals the newest archive entry's snapshot for
  that code** — added 6 Sep 2026 per the Brief 012 postmortem (see Step 4 note above); this
  is the check that would have caught Brief 011's skipped Step 4.2

Run `validate.py` before every delivery, not only on render days. Two dashboard-drift incidents
were caught by luck before this existed — the archive gets the same check for the same reason.

## Step 7 — File the brief in the project, then deliver it

**Filing comes before delivery. A brief that was only shown to the reader was not filed.**

Run `python3 validate.py` first. If it fails, fix the ledger and re-render — do not deliver
around it, and do not file a brief that failed the gate.

Then, in order:

1. **File the brief in the project** at `briefs/daily-brief-YYYY-MM-DD.html`. This is the
   permanent copy and the reason the archive survives the session that produced it.
2. **Update `briefs/INDEX.md`** — one line prepended per brief:
   `YYYY-MM-DD · Brief NNN · cutoff YYYY-MM-DDTHHMMZ · <the bottom line, one clause>`.
   The index is how any future run finds the archive without opening every file, and how the
   Step 1 continuity check detects a duplicate or forked run.
3. **File the dashboard too**, at `strategic-threat-briefing.html` in the project, whenever
   Step 6 re-rendered it. The project's doc-write tool namespaces a brand-new bare filename
   under `claude/` automatically (confirmed 16 Aug 2026, matching `claude/CONSOLE-README.md`);
   once the doc exists at whatever path it first lands on, writing that same path again
   updates it in place. Either location is fine as long as later runs check for the existing
   doc first rather than creating a second copy at a different path.
4. **Write every output back to the working folder** as well — the rendered dashboard,
   archive, node map, index and the rebuilt console all belong beside the ledger.
5. **Then deliver** — present the brief to the reader. The brief comes first, the dashboard
   second if it moved.

The project is the archive of record; the working folder is where the toolchain runs. Neither
substitutes for the other.

**Do not file `natdef-console.html` in the project.** It bakes a full copy of the ledger into
itself, and the project already holds the ledger — filing it each run would push a large
duplicate into the project's knowledge every day for a file that one command regenerates. It
lives in the working folder only.

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

## Cross-thread archive items

An archive `items[]` entry that genuinely spans multiple threads or reports that nothing moved
across several at once (e.g. Brief 002's "Russia, China, North Korea, Europe and cyber: nothing
verified moved" rollup) may carry the sentinel thread code **`—`** (a single em dash) instead of
one of the ten codes above. This is a deliberate, allow-listed sentinel, not a data error —
`validate.py` recognizes it explicitly (see Step 6). Do not invent additional sentinels without
adding them here and to the validator in the same pass; do not retroactively rewrite an already
delivered archive entry to avoid using it. **Added to this document 6 Sep 2026**, during the
Claude Code migration, resolving a gap Brief 012 (29 Aug 2026) found and deliberately left
unmodified in Brief 002's archive entry — see `verification_log[]`.

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
- **One project, one schedule, one home.** See Rule 0. A fork is a correctness bug, not a
  filing inconvenience — and this document is covered by it too.

---

## Addendum — 6 Sep 2026: migration to Claude Code

**Rule 0's "home" changed on 6 Sep 2026.** This operation moved from the claude.ai Project
named "Nat Def" (Cowork) to a git repository run under Claude Code. The repository is now the
one home Rule 0 requires; the claude.ai Project is retired and must not be written to again.
Everything in Rule 0 still applies verbatim with "the project" read as "this repository" and
"the working folder" read as "this repository's own directory" — there is no longer a
project/working-folder split, which retires the single largest source of drift this protocol
spent its first month fighting (see Rule 0 point 4 and the 16 Aug incident above). Full account
of the migration itself — what was carried over, what was found stale, what remains
unreconstructed — is in `MIGRATION-NOTES.md` at the repository root and in `verification_log[]`
under the 2026-09-06 entries. See `MIGRATION-NOTES.md` for what still needs a human decision
(principally: whether the user's own OneDrive working folder referenced above ever received
briefs this migration could not see, since the device bridge was unreachable throughout).

---

## Addendum — 6 Sep 2026: toolchain rebuild

The toolchain was rebuilt from scratch on the same data, later the same day as the
migration recorded in the addendum above. Nothing in this document's methodology changed;
what changed is that the tooling Step 6 has always specified now exists in full.

- **`render.py` exists.** It was specified here from the beginning and no copy of it ever
  survived into any session of this operation. It is a fresh implementation written against
  this document's own description of its contract — four pages from the ledger, refuses a
  ledger missing required keys, fails loudly on an unresolved template token — and is not
  represented as a recovery of the lost original.
- **All fifteen of Step 6's checks are implemented.** The four that depend on `render.py`'s
  output were standing down with an explicit `SKIPPED`; they are real now. "Retired claims
  cannot reappear" is implemented against a new `retired_claims[]` array in the ledger,
  described in `schema_notes[]`. `validate.py` reports 0 failures and 0 skips.
- **The commands are now subcommands of one entry point.** Step 6's three commands read
  `python3 -m natdef render`, `python3 -m natdef build-app` and `python3 -m natdef validate`;
  `python3 -m natdef check` runs all three as one gate and is what Step 6 means in practice.
  `python3 -m natdef brief` renders the brief from the archive entry Step 4.8 just wrote,
  which is what makes Step 5 unable to disagree with Step 4.
- **Paths.** `MIGRATION-NOTES.md` is now at `docs/MIGRATION-NOTES.md`; the account of this
  rebuild is at `docs/REBUILD-NOTES.md`. Both references in the addendum above should be
  read accordingly. The open item that addendum flags — the user's OneDrive working folder,
  never reachable from any cloud session — stands unresolved and still needs a human on that
  machine.
