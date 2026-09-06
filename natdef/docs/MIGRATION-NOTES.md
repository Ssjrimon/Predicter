# Migration notes — claude.ai Project → Claude Code, 6 September 2026

> **Correction, 6 September 2026 (toolchain rebuild).** One claim in this document is
> wrong and was acted on: the "schema style split" note below states that a free-text
> citation "carries a working `<a href>` in the delivered brief's own Sources table."
> Brief 012's Sources table contains no hyperlinks at all — zero `http` hrefs in the whole
> file — so those URLs were not recoverable from this repository by any route. They were
> recovered by search and backfilled into `sources[]` instead. See
> `REBUILD-NOTES.md`, "The citation backfill". The rest of this document stands as written;
> it is the record of what the migration knew at the time, and is not edited retroactively.

This document is the full account of how this repository came to exist. Read it once before
treating the repository as a clean, fully-understood starting point — several things in here
are load-bearing, not just historical color.

## Why this happened, and why now specifically

The user asked to move the whole Nat Def operation into Claude Code. Before building anything,
this migration re-checked the claude.ai Project's actual live state rather than trusting an
earlier summary of it from within the same conversation — and found the project already at
**Brief 12** (29 August 2026, cutoff `2026-08-29T2200Z`), produced by a separate session with no
visibility into this one, while a stale local cloud sandbox from earlier in the same
conversation was still sitting at Brief 11 (25 August). Building the export from that stale
sandbox instead of the live project would have silently regressed two real fixes Brief 12 had
already made — see "What Brief 12 already fixed, and what this migration additionally found"
below.

Separately, as of the migration date (6 September 2026), **the project had gone another eight
days without a new brief** — the 15:00-local Cowork scheduled task had lapsed again, the same
failure mode `BRIEFING-PROTOCOL.md` Rule 0 and `briefs/INDEX.md` already document twice (the 16
August fork, and the five-consecutive-cloud-only stretch that produced Briefs 008-012). That gap
is the concrete argument for what the user chose when asked directly: Claude Code, scheduled
through the operating system rather than a chat app's own scheduler, removes the specific
mechanism that produced both prior incidents — a scheduled task that silently does nothing
while the app that hosts it is closed.

**Two decisions were confirmed with the user directly before building this repository**, because
both are the kind of thing `BRIEFING-PROTOCOL.md`'s own Rule 0 says should never be assumed
silently:

1. **This repository is now the one home Rule 0 requires.** The claude.ai Project is retired,
   not kept as a parallel or backup system of record — see "Retiring the claude.ai Project"
   below for exactly what that means and what's still manual.
2. **A Windows Task Scheduler launcher was built** (`scheduler/`) to replace the Cowork
   scheduled task, running `claude` headlessly at the same 15:00-local cadence. Its one real
   caveat — the unattended-permission flag was not independently verified against the user's
   specific installed Claude Code version — is documented in `scheduler/README.md` and repeated
   here because it's the single most likely thing to silently fail: a wrong flag doesn't error,
   it hangs.

## What Brief 12 already fixed, and what this migration additionally found

Brief 12 (produced 29 Aug, by a session this migration had no visibility into until it read the
project fresh) found and handled two things on its own, before this migration ever started:

1. **Fixed.** Brief 11's `apply_brief11.py` script updated the archive snapshot and the brief's
   own prose to say KP had moved to 6/volatile and HL to 5/escalating, but never wrote those
   values into the live `threads[]` array — Step 4.2 was skipped while Step 4.8 wasn't. Anything
   reading `threads[]` served pre-Brief-11 values for four days. Brief 12 corrected `threads[]`
   directly and recommended a new validator check for this specific failure mode. **This
   migration's `intel-ledger.json` carries Brief 12's fix as-is** — verified directly by diffing
   live `threads[]` against `archive[-1].threads` for every code, which is now also
   `validate.py`'s `check_threads_vs_latest_archive` function, running on every future commit.

2. **Found, logged, deliberately left unmodified.** Brief 2's archive entry uses an em dash as
   a cross-thread "nothing moved" marker in one item, which isn't a declared thread code and
   would fail a strict validator. Brief 12 named two options (reserve an allow-listed code, or
   amend Brief 2's record) and left the decision open. **This migration resolved it**: added a
   "Cross-thread archive items" section to `BRIEFING-PROTOCOL.md` formally allow-listing the em
   dash, and `validate.py` recognizes it explicitly. Brief 2's file is untouched — rewriting a
   delivered brief's record was the one option Brief 12 itself ruled out, correctly.

This migration's own pass — writing `validate.py` from `BRIEFING-PROTOCOL.md`'s Step 6 checklist
and running it against the full ledger for the first time in this operation's recorded
history — found four more things, all logged in `verification_log[]` under `2026-09-06` and all
non-destructive:

- **A real dead reference, fixed.** `timeline_additions_2026[74]`'s citation used the short code
  `UKMTO`, which had never been added to the legacy `source_urls{}` registry. UKMTO's canonical
  URL (`https://www.ukmto.org/`) already appears correctly elsewhere in this same ledger's
  delivered output (Brief 12's own Sources table), so this was registered rather than guessed.
- **A documented sentinel, not a defect.** `PRESS` is used as a citation code in three pre-2026
  entries, meaning "general contemporaneous press reporting, no single primary document." It was
  never in `source_urls{}` because there's no single URL to put there, not because it was
  missed. `validate.py` now recognizes it explicitly (`KNOWN_GENERIC_SENTINELS`) instead of
  failing on it or inventing a fake URL.
- **A schema style split, accepted rather than forced.** From Brief 11 onward, citations
  increasingly appear as inline free text (`"Al Jazeera 24 Aug 2026"`, `"Reuters via AOL, 28 Aug
  2026"`) rather than as short codes resolved against `sources[]`/`source_urls{}`. Both styles
  coexist in the same ledger. `validate.py` treats the free-text style as a disclosed schema gap
  (a warning, not a failure) rather than picking a winner unilaterally — **this is an open
  product decision, not a bug**; see "Open decisions" below.
- **A timestamp and a file-path format, both tolerated rather than rewritten.**
  `ledger_meta.last_cutoff` and `archive[].cutoff` use `HH:MM` for every brief except Brief 12,
  which used `HHMM` with no colon (same instant, different string). `archive[].file` is a bare
  filename for Briefs 1-11 and carries a `briefs/` prefix for Brief 12. `validate.py` accepts
  both forms of each rather than rewriting eleven historical archive entries to match one
  convention. Recommended going forward: `HH:MM` and the `briefs/<file>` form, since both are
  what `BRIEFING-PROTOCOL.md` and `briefs/INDEX.md` already document as correct.

None of the above touched `brief_number`, `last_cutoff`, or any `archive[]` entry — this was
infrastructure housekeeping, logged as such, not a thirteenth brief.

## What was carried over, and how each piece was sourced

"Without losing anything" required treating the claude.ai Project as the canonical source for
data and the cloud sandbox (from earlier in the same conversation, which had been producing
Briefs 008-012's *tooling*) as the source for everything that never made it into the project.
Nothing was reconstructed from memory or paraphrase.

| What | Source | How it was verified |
|---|---|---|
| `intel-ledger.json` | claude.ai Project, fetched fresh | Read directly this session, not from an earlier cached copy — confirmed Brief 12, 113 verification_log entries pre-migration |
| `BRIEFING-PROTOCOL.md` | claude.ai Project, fetched fresh | Read directly this session (previously only assumed unchanged by timestamp) |
| `briefs/INDEX.md` | claude.ai Project, fetched fresh | Read directly this session; the Brief 12 entry and its extensive "Notes for future runs" section were previously known only from a paraphrased summary, not verbatim, until this fetch |
| `briefs/daily-brief-2026-08-29.html` (Brief 12) | claude.ai Project, fetched fresh | Read directly this session; previously not seen in full — only described secondhand |
| `briefs/daily-brief-2026-08-{08,09,10,11,12,15,16,17,18,19,25}.html`, `RETRACTED-brief-003-2026-08-16.html` | Local cloud sandbox (same conversation, authored earlier) | Project's own doc timestamps for each showed no change since the sandbox copy was written and filed — not re-fetched byte-for-byte; flagged here so a future audit knows this was a timestamp-based inference, not a re-read |
| `claude/strategic-threat-briefing.html`, `claude/CONSOLE-README.md` | Local cloud sandbox | Same timestamp-based reasoning as above |
| `sources/SOURCES.md` (the three founding URLs) | claude.ai Project docs "Nat sec strt", "Nat def strt", "Odni" | Fetched fresh this session — each was a single bare URL, nothing else, reproduced verbatim |
| `build_app.py`, `app-template.html`, `natdef-console.html`, `server.py`, `tools/smoke.py`, `tools/parts/*` | Local cloud sandbox only — **never lived in the claude.ai Project at all** | `build_app.py` re-run against the migrated ledger during this migration; produced a valid 435KB console with no errors. Not otherwise modified. |
| `tools/verify/shot_brief{18,19,25}.py` | Local cloud sandbox only | Playwright verification scripts written for Briefs 009/010/011; carried as historical record |
| `tools/legacy/apply_brief{8,9,10,11}.py`, `intel-ledger.pristine.json`, `intel-ledger.json.presprint8.bak`, `intel-ledger.merged.json`, `protocol-disk.SUPERSEDED-DRAFT.md`, `start-console.cmd`, `manual_checks.py`, `screenshots/*.png` | Local cloud sandbox only | Kept verbatim as historical record, not because any are live tooling — see `tools/legacy/` below |
| `validate.py` | **Newly authored during this migration** | Written directly from `BRIEFING-PROTOCOL.md`'s Step 6 checklist text, since no working `validate.py` had ever been reachable from any cloud session across this operation's history. Run repeatedly against the real ledger during authoring — see "Testing performed" below. |
| `CLAUDE.md`, `README.md`, this file, `scheduler/*`, `sources/SOURCES.md` | **Newly authored during this migration** | — |

`protocol-disk.md` is worth a specific note: it is an **earlier, superseded draft** of
`BRIEFING-PROTOCOL.md` (a 07:00-sweep/13:00-delivery cadence design, later corrected to the
15:00 cadence actually used from 15 Aug onward) that was left behind in the cloud sandbox and
never reconciled. It is kept at `tools/legacy/protocol-disk.SUPERSEDED-DRAFT.md` for the
historical record and because it independently confirms the working-folder path referenced
throughout this document — but the live `BRIEFING-PROTOCOL.md` at the repository root is the one
to follow. Do not merge them.

## render.py was not reconstructed

`BRIEFING-PROTOCOL.md` describes `render.py` in detail — it generates
`strategic-threat-briefing.html`, `brief-archive.html`, `node-map.html` and `index.html` from
the ledger, refuses to run on a ledger missing required keys, and fails loudly on an unresolved
template token. No copy of it, and no copy of whatever HTML templates it reads (distinct from
`app-template.html`, which is `build_app.py`'s template, not `render.py`'s), was recoverable
from the local cloud sandbox or the claude.ai Project. The only surviving artifact of its output
is `claude/strategic-threat-briefing.html` itself — a rendered result, not a template.

This migration chose not to guess at `render.py`'s implementation from that one rendered output.
`BRIEFING-PROTOCOL.md`'s own standing constraints exist specifically to prevent this class of
mistake elsewhere in the operation ("a run that cannot reach the ledger will fabricate one and
produce a confident, sourceless brief. Visible failure beats silent invention.") — the same
principle applies to fabricating a whole script's template design from a single sample and
presenting it as the recovered original. `validate.py`'s four render-dependent checks are
implemented to activate automatically the moment the relevant rendered file exists, and until
then print an explicit `SKIPPED` line rather than silently passing.

## Retiring the claude.ai Project

Per the user's decision, the claude.ai Project is retired as of this migration. What was
actually done, and what is still manual:

- **Done:** `briefs/INDEX.md` inside the claude.ai Project was updated (via `project_write`,
  from this same migration session) with a prominent retirement notice at the very end, telling
  any future Claude session that opens that project to stop before producing a brief there.
- **Done:** the one active cloud-side scheduled task associated with this project —
  `trig_01TNWnFTKvs88qcCtnYusLTp`, "Nat Def — Step 7 sync check (read-only)," firing daily at
  21:00 UTC — was deleted as part of this migration. It was already harmless by design (strictly
  read-only, per its own prompt text, added after the 16 Aug fork specifically so a cloud
  trigger could never again produce competing brief content), but there is no reason to keep a
  Cowork-side automation running against a retired project.
- **Not done, and not possible from here:** the claude.ai Project's own configured
  **instructions** field (visible in Project settings — "Set it daily, 3:00 PM. Produce today's
  Strategic Threat & Posture brief...") is a project-level setting, not a document, and this
  migration's tools can write project *documents* but not that field. **If a Cowork scheduled
  task pointed at this project still exists on the user's account or desktop app, it will keep
  trying to fire against a project that now says, in its own index, to stop.** The user should
  check Cowork's scheduled-task list directly and delete or disable any task still targeting the
  "Nat Def" project, the same way this migration deleted the one cloud-side trigger it could see
  and act on.

## Open decisions — genuinely undecided, not defaulted silently

Three things were deliberately left open rather than resolved unilaterally, because each is a
real trade-off this migration had no clear mandate to pick a side on:

1. **Template going forward.** Briefs 001-011 use a light-paper theme with an interactive
   JS-driven movement board. Brief 012 uses an unrelated dark theme with a static board and a
   serif ("Iowan Old Style") body font. Both are preserved exactly as delivered — per
   `BRIEFING-PROTOCOL.md`, briefs are never rewritten retroactively — but the next brief produced
   in this repository needs one or the other as its starting point, and nothing in either
   template or in the protocol document says which. Pick one (or design a third) before the next
   `daily-brief-*.html` is written, rather than drifting into whichever one whoever's prompting
   that day happens to reach for.

2. **Citation style.** See "inline free text vs. registry codes" above. `validate.py` accepts
   both permanently, but that's a tooling accommodation, not a style recommendation. Decide
   whether future entries should register a `sources[]`/`source_urls{}` entry for every citation
   (more consistent, more work) or continue writing citations inline (what's actually happened
   since Brief 11, lower friction, and it does mean the ledger's `src[]` field can't be trusted
   alone to reconstruct a citation's URL for those entries without opening the rendered brief).

3. **The "retired claims cannot reappear" check.** `BRIEFING-PROTOCOL.md` lists this as one of
   `validate.py`'s required checks. It is not implemented, because it requires a defined registry
   of what counts as "retired" that does not currently exist anywhere in the ledger schema
   (`sources[].status: superseded` is the closest thing, and `check_sources`/`check_citations`
   already enforce that those stay resolvable — but a *claim* being retired, as opposed to a
   *source document*, isn't tracked anywhere as data). This is flagged in `validate.py`'s own
   docstring as a real gap, not silently absent.

## The one thing this migration could not verify, and must be checked before this repository is fully trusted

`BRIEFING-PROTOCOL.md`'s own scheduled-task configuration names a working folder on the user's
machine — `C:\Users\User\OneDrive\Documents\New folder\strategic-threat-briefing\` — as where
`render.py`, `build_app.py` and `validate.py` were meant to live, and where, as of Brief 007's
16 August reconciliation, a desktop-bound Cowork scheduled task was still writing successfully
even though it could not write back to the claude.ai Project. This migration's device bridge to
the user's computer was unreachable throughout (`get_device_info` failed "not connected," on
both this attempt and the standing one-retry policy).

**This means there is a real, live possibility that folder kept advancing — past Brief 7, past
Brief 12, possibly with a working `render.py` this migration was never able to recover — while
the claude.ai Project sat still.** If so, that folder may be more current than this repository,
not less. The first time this repository is opened on the machine where that folder lives:

1. Check whether `C:\Users\User\OneDrive\Documents\New folder\strategic-threat-briefing\`
   exists and what `intel-ledger.json` inside it says for `brief_number` and `last_cutoff`.
2. If it's behind or matches this repository, nothing to do — this repository is current.
3. If it's ahead, or has briefs this repository doesn't, **reconcile it the same deliberate way
   the 16 August 2026 fork was reconciled** (`intel-ledger.json` → `verification_log[]`, entry
   dated 2026-08-16, and `briefs/INDEX.md`'s "Retracted" section): don't discard either side
   silently, don't renumber over the divergence, and log exactly how the two were merged.
4. If that folder has a real `render.py`, copy it into this repository and delete this
   repository's `SKIPPED` disclosures in `validate.py` in favor of the real checks — don't keep
   both a working and a fictional render step side by side.

## Testing performed during this migration

- `python3 validate.py` run repeatedly while `validate.py` was being written, against the real
  migrated ledger — not a synthetic fixture — specifically so its checks would be calibrated
  against this ledger's actual, sometimes messy history (the `source_urls{}` legacy registry,
  the free-text citation style, the two cutoff formats) rather than an idealized schema. Final
  state: **0 failures**, 56 warnings (all individually explained above or in `validate.py`'s own
  output), 4 skips (all `render.py`-dependent, all explicit).
- `python3 build_app.py` run against the migrated ledger: succeeded, produced a 435KB
  `natdef-console.html` reporting brief #12, cutoff `2026-08-29T2200Z`, 93 timeline entries, 10
  threads, 28 horizon items, 12 archive entries. `python3 build_app.py --check` confirmed the
  output matches the ledger with no drift.
- Every file in the provenance table above was either fetched fresh this session or matched
  against the claude.ai Project's own last-modified timestamp before being trusted as unchanged.
