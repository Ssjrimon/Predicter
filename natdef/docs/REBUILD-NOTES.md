# Rebuild notes — 6 September 2026

The toolchain was rebuilt from scratch. The data was not.

This document records what changed, what deliberately did not, and which previously-open
decisions this rebuild closed. `MIGRATION-NOTES.md`, in this same directory, is the earlier
account of how the operation left the claude.ai Project; it is history now, but it still
holds one open item that needs a human (see the end of this file).

## What was carried over verbatim

Nothing in this list was rewritten, reformatted or re-derived:

| What | Note |
|---|---|
| `intel-ledger.json` | Content unchanged except the three additions below. |
| `briefs/*.html` | All twelve delivered briefs plus `RETRACTED-brief-003-2026-08-16.html`. Delivered briefs are never rewritten. |
| `briefs/INDEX.md` | Unchanged. |
| `BRIEFING-PROTOCOL.md` | Unchanged. It is the specification; the code follows it, not the other way round. |
| `sources/SOURCES.md` | Unchanged. |
| `docs/MIGRATION-NOTES.md` | Moved into `docs/`, otherwise unchanged. |

Three things were **added** to the ledger, all logged in `verification_log[]` under
`2026-09-06` as infrastructure. `brief_number`, `last_cutoff` and `archive[]` were not
touched — this is not a thirteenth brief:

1. `retired_claims[]`, the registry described below.
2. A `schema_notes[]` entry documenting that registry's shape and rules.
3. A `verification_log[]` entry recording that the four skipped checks are now implemented.

## What was rebuilt

Every script. The old `validate.py` and `build_app.py` were replaced rather than extended,
and `render.py` was written for the first time.

```
natdef/
  errors.py       The exception hierarchy. Every failure mode is a distinct, catchable type.
  ledger.py       The one place intel-ledger.json is parsed.
  template.py     Strict token templating. An unresolved token is an exception.
  theme.py        The design system all pages share.
  components.py   HTML fragments used by more than one page.
  pages.py        The four page bodies.
  render.py       The orchestrator. Was missing entirely.
  brief.py        Archive entry -> daily brief.
  build_app.py    Ledger -> the one-file offline console.
  server.py       Serves the live ledger.
  validate.py     The Step 6 gate, all fifteen checks.
  cli.py          python3 -m natdef <command>
```

Dropped: `tools/legacy/` (old ledger backups, the one-off `apply_brief*.py` scripts, the
superseded protocol draft, screenshots), `tools/verify/` (Playwright scripts written for
Briefs 009–011), `tools/parts/` (the old console's source fragments), `app-template.html`,
and `scheduler/` (Windows Task Scheduler `.cmd` files). The three pieces of that material
with lasting value are kept in `docs/reference/`: the last rendered dashboard frozen at
Brief 12, its README, and the superseded protocol draft.

## The four checks that were standing down

`BRIEFING-PROTOCOL.md` Step 6 has always listed fifteen checks `validate.py` "enforces".
Four of them compare the ledger against `render.py`'s output, and `render.py` did not exist
— no copy survived into any session in this operation's history. The migration of 6
September correctly refused to guess at its implementation from the single rendered sample
it had, and made `validate.py` print an explicit `SKIPPED` line for each rather than pass
silently. A fifteenth, "retired claims cannot reappear", was unimplemented for a different
reason: it needed a registry of what counts as retired, and the schema had nowhere to put
one.

All five are now implemented.

**`render.py` is a fresh implementation, not a recovery.** It was written against the
protocol's own description of the contract — four pages from the ledger, refuses a ledger
missing required keys, fails loudly on an unresolved template token — and it is not
represented as the lost original. `docs/reference/strategic-threat-briefing.frozen.html`
was read as a guide to the *information architecture*, not copied.

**The freshness checks read a declared contract, not scraped markup.** Every generated page
carries `<meta name="natdef:counts">` holding the counts the renderer built it from. The
validator diffs those against the ledger. A page cannot claim a count it did not build
with, and the check does not break the next time a heading is reworded.

**`retired_claims[]`** carries, per entry: `id`, `claim`, `retired_on`, `retired_by_brief`,
`reason`, `patterns[]` (case-insensitive regexes matched against the *visible text* of
rendered output) and `exempt_files[]`. Two exemptions keep the sweep from flagging the
operation's own honest record:

- a brief filed on or before `retired_on` is exempt automatically, because delivered briefs
  are never rewritten and necessarily still contain the claim they made; and
- `RETRACTED-*.html` files are exempt, because they exist to preserve a retracted claim.

It is seeded with the two claims this operation has actually retired: the 9 August 2026
assertion that Cowork scheduled tasks run in the cloud without the app open (corrected 10
August), and the numbering and 173-hour-gap narrative of the forked "Brief 003" (retracted
16 August). The check was verified by injecting a restatement of the first into a
post-retirement brief and confirming the gate failed with the matched text quoted.

**Result:** `validate.py` reports **0 failures, 0 skips** against the real ledger. The
38 remaining warnings are the disclosed schema gaps (25 free-text citations, 3 uses of the
`PRESS` sentinel, 11 archive entries using the older bare-filename convention, 1 stale
cutoff) — each one a thing the protocol or the migration notes already documents as
accepted rather than broken.

## Open decisions this rebuild closed

`MIGRATION-NOTES.md` left three decisions genuinely open rather than defaulting them
silently. Two are now settled; the third is narrowed.

**1. Brief template — settled: dark.** Briefs 001–011 used a light-paper theme; Brief 012
used an unrelated dark theme; the dashboard was dark. `natdef/theme.py` is one design system
shared by every generated page and by the brief template, using the palette already in the
frozen dashboard. The daily brief and the standing picture are now visibly one product. The
twelve delivered briefs are **not** re-rendered into it — they are preserved exactly as
delivered, which is what the protocol requires, so the archive still holds two visual eras.

**2. Citation style — settled: register going forward, tolerate the history.**
`resolve_citation` classifies every `src[]` value as registry, legacy, sentinel, free-text
or dead. Dead always fails. Free-text warns by default and fails under `--strict`. The
recommendation is that new entries register a `sources[]` code; `--strict` is how that
becomes enforced once the 25 historical free-text citations are backfilled. Making it the
default today would fail the gate 25 times a day on entries nobody is going to fix that
morning, which is how a gate gets ignored.

**3. Retired claims — implemented, and the registry starts small.** Two entries is not a
complete history of everything this operation has ever corrected. The mechanism is real and
tested; populating it further is ordinary work, and `CLAUDE.md` now says registering a
retired claim is part of issuing a correction rather than a separate task.

## Defects found and fixed during the rebuild

Two real bugs surfaced from running the new code against the real data:

- **Double-escaped entities.** Parts of the ledger were authored by hand directly into HTML
  and carry entities in fields that are otherwise plain text — `map_nodes[].label` holds
  `"ISRAEL &amp; GULF PARTNERS"`. Escaping those again renders a literal `&amp;` to the
  reader; the frozen dashboard shows `Homeland &amp;amp; Western Hemisphere` in its
  briefings accordion, so this defect shipped. Ledger text is now normalised to plain text
  on the way out of `ledger.py`, and `esc()`/`attr()` are idempotent.
- **Roughly 40% of timeline dates did not sort.** `timeline[].d` holds 37 distinct date
  shapes — `2016`, `Jan 23, 2026`, `Sept 2025`, `Aug 5–6, 2026`, `2023–24`, `Mid-2024`,
  `Through 2028`, `2030s`. A strict ISO parser drops all the prose forms into one
  unsortable bucket that then renders in arbitrary order, which stops a chronology being
  one. `parse_ledger_date` handles every shape in the ledger; a test asserts that none is
  unparseable.

## What is still open

- **The OneDrive working folder.** `MIGRATION-NOTES.md`'s one unresolved item stands
  unchanged: `C:\Users\User\OneDrive\Documents\New folder\strategic-threat-briefing\` was
  never reachable from any cloud session, and may hold briefs or a ledger this repository
  has never seen. It needs a human on that machine. If it turns out to hold its own
  `render.py`, that is a historical curiosity now, not a recovery target — but a divergent
  *ledger* would matter a great deal.
- **Backfilling the 25 free-text citations**, after which `--strict` should become the
  default.
- **Item bodies.** `archive[]` entries for Briefs 001–012 carry headlines and So-whats but
  not body prose, so `natdef brief` renders those items with a visible placeholder. That is
  correct behaviour for a historical entry and is not a reason to re-render a delivered
  brief. New briefs should write `body` from the start.

## Testing performed

- 104 tests, stdlib `unittest`, no third-party dependencies. Each validator check is
  asserted by introducing exactly one defect and confirming that check — and the message it
  produces — catches it.
- `tests/test_real_ledger.py` runs the whole pipeline against the real
  `intel-ledger.json` and asserts what must always hold: it loads, every date parses, it
  validates with no failures **and no skips**, it renders without shipping a template
  token, the console builds, every delivered brief has an archive entry, and the pages on
  disk agree with the ledger. It asserts no specific counts, so filing a brief does not
  break it.
- All four pages, the console (all five tabs) and a generated brief were loaded in a real
  browser and checked for console errors and page errors: none. The map click-through,
  the timeline thread filter and projected-item toggle, the archive catch-up digest, and
  the node-map deep dive were each exercised.
- `python3 -m natdef check` — render freshness, console freshness, validator — passes.
