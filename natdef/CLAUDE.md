# Nat Def — operating instructions

This repository **is** the operation. It is the one home `BRIEFING-PROTOCOL.md`'s Rule 0
requires: there is no separate claude.ai Project and no separate working folder. Read
`docs/REBUILD-NOTES.md` once, the first time you work here, for what the toolchain does and
which past decisions are settled.

## Producing a brief

Read `BRIEFING-PROTOCOL.md` in full and follow it from Step 1. Do not skip to writing HTML.

1. **Continuity check first.** Read `intel-ledger.json`. Check `ledger_meta.brief_number`
   and `ledger_meta.last_cutoff` against the newest entry in `briefs/INDEX.md`. A mismatch
   means a fork or a skipped write — stop and reconcile it, do not renumber over it
   (Rule 0, Step 1). `python3 -m natdef status` prints both side by side.
2. **Sweep** `standing_watchlist[]` plus each thread's `watch[]`, over the *actual* interval
   since `last_cutoff` — however long that has been, not a fixed 24 hours.
3. **Verify.** Every candidate claim goes through the Step 3 gate before it touches the
   ledger. Claims about Claude's or Claude Code's own capabilities are not exempt.
4. **Update the ledger** — Step 4, all eight sub-steps. **4.2 (revise `threads[]`) and 4.8
   (append the archive entry) are separate writes.** Brief 011 did 4.8 without 4.2 and
   served stale values for four days. `validate.py` catches that now, but do not rely on
   the gate to cover for skipping a step.
5. **Generate the brief:** `python3 -m natdef brief`. It renders from the archive entry you
   just wrote, so the brief and the ledger cannot disagree. Give each item a `body` array
   of paragraph strings in its archive entry — an item without one renders a visible
   "body not written" marker, on purpose.
6. **Gate:** `python3 -m natdef check`. This runs render-freshness, console-freshness and
   the validator. **Do not deliver or commit if it exits non-zero.** Fix the ledger and
   re-run; do not deliver around it.
7. **Index:** prepend one line to `briefs/INDEX.md`, in the established format.
8. **Commit**, naming the brief number and the one-clause bottom line. The commit *is*
   Step 7 — there is no separate filing step now that there is only one home.

## Standing rules that matter every time

- **Never fabricate a claim to fill a quiet day.** A short brief is correct; a padded one
  is not.
- **Never rewrite a delivered brief.** Corrections run in the next brief's verification
  log, never as edits to a committed `briefs/daily-brief-*.html`. `natdef brief` refuses to
  overwrite an existing file without `--force` for this reason.
- **Never hand-edit a generated file** — the four pages, or the console. The next render
  discards the edit silently.
- **Never bump `brief_number` or touch `last_cutoff`/`archive[]` for housekeeping.** A
  ledger patch that is not a new brief gets its own `verification_log[]` entry and, if
  warranted, a `ledger_meta.last_updated` bump. Nothing else. See the `2026-09-06` entries
  for the pattern.
- **The em dash (`—`) is a real, allow-listed archive thread code**, not a data error. See
  "Cross-thread archive items" in `BRIEFING-PROTOCOL.md`. Do not "fix" it.
- **Every citation must resolve to a registered source.** `src[]` values are registry
  codes, resolved against `sources[]` or the older `source_urls{}` shorthand. An inline
  free-text citation (`"Reuters via AOL, 28 Aug 2026"`) **fails the gate** — the 23
  historical ones were backfilled on 6 Sep 2026, so a new one is a defect, not a
  convention. When you cite something new, add a `sources[]` entry with
  `status: "cited"`, a real URL, `tier`, `attribution_class` and a `note` naming the
  origin and hop count; see the 2026-09-06 entries for the pattern. `PRESS` remains a
  documented sentinel with no single URL by design.
- **When you retire a claim, register it.** Add an entry to `retired_claims[]` in the same
  pass as the correction. That is what makes the "retired claims cannot reappear" check
  mean anything; a correction that skips it is half-done.

## The toolchain

| Command | What it does |
|---|---|
| `python3 -m natdef status` | Brief number, cutoff, counts, what is rendered, whether the console is current. |
| `python3 -m natdef render` | Ledger → `index.html`, the dashboard, the node map, the archive. `--check` exits 3 if any is stale. |
| `python3 -m natdef brief` | Archive entry → `briefs/daily-brief-YYYY-MM-DD.html`. |
| `python3 -m natdef build-app` | Ledger → `natdef-console.html`. `--check` exits 3 if stale. |
| `python3 -m natdef validate` | The Step 6 gate. `--strict` also fails on a source registered without a URL. |
| `python3 -m natdef check` | All of the above as one gate. **This is the pre-commit command.** |
| `python3 -m natdef serve` | Localhost server rendering from the live ledger. |
| `python3 -m unittest discover -s tests -t .` | 114 tests. |

Standard library only. If you find yourself adding a dependency to this toolchain, stop:
it runs unattended, and every import is one more way a scheduled run fails silently.

## The daily schedule

One Routine drives this operation, firing at 15:00 US Central: `trig_01H1Wd2FeZ1LiWYpUwUDTVka`.
**Read [`docs/SCHEDULE.md`](docs/SCHEDULE.md) before creating, changing or duplicating any
scheduled task** — Rule 0 allows exactly one, and two schedules pointed at this ledger is not
redundancy, it is two runs racing to increment `brief_number`.

The scheduled run commits straight to `main` and deliberately does not open a pull request;
`docs/SCHEDULE.md` explains why filing behind a review queue would fork the ledger rather
than protect it.

**The daily run is currently not filing.** Its first firing, 7 September 2026, did a full
sweep and lost it: a Routine's fired sessions declare no repository source, so they can read
this public repo but cannot push, and `update_trigger` cannot add one. `docs/SCHEDULE.md`
records the evidence and the two ways out. Until it is fixed, briefs must be produced from an
interactive session. Nothing is corrupted meanwhile — `last_cutoff` does not advance, so the
next brief covers the whole gap.

Two other things there need a human rather than a session: the cron does not follow daylight
saving and must move to `0 21 * * *` on 1 November 2026, and only the user's own machine can
confirm that no Cowork desktop task still points at the retired claude.ai project.


## What is still genuinely open

- **The OneDrive working folder.** `docs/MIGRATION-NOTES.md` records that
  `C:\Users\User\OneDrive\Documents\New folder\strategic-threat-briefing\` may hold state no
  cloud session has ever reached — possibly briefs this repository does not have. If you
  ever get device access, check it, and reconcile any divergence the deliberate way the
  16 Aug 2026 fork was reconciled: log it in `verification_log[]`, discard neither side,
  renumber over nothing.
- **Item bodies for Briefs 001–012.** Their archive entries carry headlines and So-whats but
  not body prose, because `archive[]` was never designed to hold it. Re-rendering those
  briefs is *not* the fix — delivered briefs are never rewritten. New briefs should carry
  `body` from the start.
