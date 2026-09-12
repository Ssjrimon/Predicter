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

Everything **added** to the ledger is logged in `verification_log[]` under `2026-09-06` as
infrastructure. `brief_number`, `last_cutoff` and `archive[]` were not touched — this is not
a thirteenth brief:

1. `retired_claims[]`, the registry described below, plus a `schema_notes[]` entry
   documenting its shape and rules.
2. 22 `sources[]` entries backfilling the historical free-text citations, plus the `src[]`
   rewrites that point at them and a `schema_notes[]` entry for the `status: "cited"`
   convention. See "The citation backfill".
3. `verification_log[]` entries recording that the four skipped checks are now implemented,
   that the backfill ran, and how the one unfetchable citation was identified.

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

**Result:** `validate.py` reports **0 failures and 0 skips** against the real ledger, under
`--strict` as well as by default. The 13 remaining warnings are all disclosed, accepted
conventions rather than defects: 3 uses of the `PRESS` sentinel (no single URL by design),
11 archive entries using the older bare-filename convention (both are accepted), and 1 stale
cutoff (the operation has not run since 29 August, which is the point of the warning).

## Open decisions this rebuild closed

`MIGRATION-NOTES.md` left three decisions genuinely open rather than defaulting them
silently. Two are now settled; the third is narrowed.

**1. Brief template — settled: dark.** Briefs 001–011 used a light-paper theme; Brief 012
used an unrelated dark theme; the dashboard was dark. `natdef/theme.py` is one design system
shared by every generated page and by the brief template, using the palette already in the
frozen dashboard. The daily brief and the standing picture are now visibly one product. The
twelve delivered briefs are **not** re-rendered into it — they are preserved exactly as
delivered, which is what the protocol requires, so the archive still holds two visual eras.

**2. Citation style — settled: registry codes, and the history is backfilled.** See
"The citation backfill" below. `resolve_citation` classifies every `src[]` value as
registry, legacy, sentinel, registered-without-url, free-text or dead. Free-text and dead
both fail; registered-without-url warns, and fails under `--strict`. All 23 historical
free-text citations were backfilled, so the strict policy costs nothing to enforce and is
on by default.

**3. Retired claims — implemented, and the registry starts small.** Two entries is not a
complete history of everything this operation has ever corrected. The mechanism is real and
tested; populating it further is ordinary work, and `CLAUDE.md` now says registering a
retired claim is part of issuing a correction rather than a separate task.

## The citation backfill

From Brief 011 onward, citations were increasingly written as inline free text —
`"Reuters via AOL, 28 Aug 2026"`, `"UKMTO warning 121-26"` — rather than as codes resolving
against `sources[]`. 25 `src[]` values across 23 distinct strings. Their URLs could not be
reconstructed from the ledger at all.

`MIGRATION-NOTES.md` assumed that was survivable because "the same citation carries a
working `<a href>` in the delivered brief's own Sources table." **That assumption is wrong.**
Brief 012's Sources table lists every citation with its outlet, headline, date, tier and
attribution class — and contains no hyperlinks whatsoever, zero `http` hrefs in the whole
file. The URLs were not recoverable from the repository by any route.

They were recovered by search instead, each one matched on outlet, date and headline
against both Brief 012's Sources table and the ledger entry's own claim before being
registered. All 23 resolved to real documents. Worth noting in particular:

- **Both UKMTO items resolved to the primary PDFs**, not to reporting about them: warning
  121-26 and JMIC Advisory Note Update 090, both on ukmto.org.
- **The ISW citation was re-pointed to ISW's own publication.** Brief 012 cited the
  28 August Russian Offensive Campaign Assessment through Kyiv Post's republication;
  it is now registered against criticalthreats.org, per Step 2's rule against summarising
  a document from an article about the document.
- **`"Al Jazeera 27 Aug 2026"` denoted two different articles** in two different entries —
  the Qatar Hormuz talks, and the Haiti Kenscoff attack. They are now `AJ-HORMUZ-0827` and
  `AJ-HAITI-0827`. This is the single clearest argument for registry codes over inline
  citations, and it was invisible until the backfill.
- **Two entries keep Brief 012's own access disclosures**: CNN was never fetched (blocked
  by robots.txt) and CNBC returned HTTP 403 to a full fetch. The URLs are registered so the
  citations resolve; the disclosures stand for what Brief 012 knew.
- **One item needed a second pass, and it mattered.** militarnyi.com is blocked by the
  network egress proxy (the gateway answers 403 to CONNECT), so that article could not be
  opened. The site carries **two** similarly titled Engels Tu-95MS articles, and the wrong
  one is a credible decoy: it is headlined "Satellite Images Confirm *Destruction*…" and
  this ledger entry's own title uses the word "destroy". It is about the *first* bomber,
  struck 16 July 2026, tail section, corroborated by Ukrainska Pravda dated 19 July. The
  registered URL is the *second* bomber: night of Friday 28 August 2026, right wing
  partially broken off, AviVector imagery, SSU Special Operations Center «А» drones, and
  the article itself contrasts this aircraft with the one destroyed on 16 July.
  28 August 2026 was in fact a Friday, and Ukrainska Pravda's same-day 28 August report
  carries the same right-wing damage and AviVector attribution.

  Seven converging factors, then — but the page still has not been opened, and every
  corroborating outlet (pravda.com.ua, english.nv.ua, defencematters.eu, united24media.com)
  is blocked from this environment too. That is a strong identification, not the primary
  fetch Step 3 asks for, and the source's `note` and a `verification_log[]` entry both say
  so. The exact publication date (28 or 29 August) is unconfirmed and immaterial to
  identity. A session on a network that can reach the domain should open it and close this
  out. **A backfill that had matched on headline alone would have picked the wrong
  article** — worth remembering the next time this looks like clerical work.

The 22 new `sources[]` entries carry `status: "cited"` — a dated item a brief cited, as
distinct from a standing document (`current`) or a recurring tracker (`tracking`) — so they
do not inflate the "current primary documents" count the dashboard displays, which stays at
10. Each carries `cited_as[]`, the original inline strings, so the pre-backfill form of
every citation is preserved rather than erased.

With no free-text citations left, an unregistered citation is now a **failure** by default
rather than a warning. Leaving it a warning would have meant the one thing the backfill was
for — stopping new ones appearing — never actually took effect.

Result: 199 citations resolve to a URL, 3 uses of the documented `PRESS` sentinel, 0
free-text, 0 dead. `validate.py` and `validate.py --strict` both pass. Warnings against the
real ledger fell from 38 to 13.

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
- **Opening the Militarnyi page** from a network that can reach militarnyi.com. Its
  identity is confirmed on seven converging factors (see "The citation backfill"), but it
  is the one citation in the ledger that has never been fetched directly, and its exact
  publication date is unconfirmed.
- **Item bodies.** `archive[]` entries for Briefs 001–012 carry headlines and So-whats but
  not body prose, so `natdef brief` renders those items with a visible placeholder. That is
  correct behaviour for a historical entry and is not a reason to re-render a delivered
  brief. New briefs should write `body` from the start.

## Testing performed

- 124 tests, stdlib `unittest`, no third-party dependencies. Each validator check is
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

## Code review, 12 September 2026

A read-through of the toolchain plus an exercise of every CLI path, the server and the
gate. Four defects were found and fixed. None of them could corrupt the ledger or a
delivered brief; all four shared the same shape, which is why they are recorded together:
**a failure that does not announce itself.** That is the one property this toolchain is
built around, so a quiet failure in the tooling is worth more attention than its blast
radius suggests.

- **`natdef check --strict` ran the loose gate and printed PASS.** `--strict` is declared on
  the `check` subparser, so `argparse` put it in the parsed namespace; `cli._check` read it
  out of the *leftover* argv, where it never appears, and therefore always saw `False`.
  Anyone tightening the gate got no error and no behaviour change — only a pass. Fixed in
  `cli.py`; `tests/test_cli.py` asserts the flag reaches `_check` in both directions.
- **`natdef render --page X --out <new dir>` died with a bare traceback.** `render_all()`
  creates its output directory; the single-page branch of `render.main` never got the same
  `mkdir`, so it raised `FileNotFoundError` instead of writing. Fixed, with the `--check`
  case asserted too: inspecting a page must not create the directory it was only asked to
  look at.
- **`check_sources` and `check_nodes` printed their PASS line unconditionally.** A run could
  report "every superseded_by resolves" directly above the failure saying one did not, and
  "edges all resolvable and typed" above an unresolvable edge. The exit code was always
  right; the report contradicted itself.
- **`check_archive` tested the whole run's failure list rather than its own findings.** An
  unrelated earlier failure — a bad thread direction, say — silently withheld a PASS the
  archive had earned, and undercounted the "N check group(s) passed" summary with it.

The last two are fixed with `Report.mark()` / `Report.clean_since()`, so each check decides
its own PASS line from its own findings and neither failure mode can return.

Verified, not assumed: the gate was re-run against mutated copies of the real ledger to
confirm each check still catches what it is for — a live `threads[]` moved without its
archive snapshot (the Brief 011 defect class), a new free-text citation, an out-of-range
intensity, an invalid direction, an unresolvable edge, a stale rendered page and a stale
console. All were caught. `natdef check` and `natdef check --strict` now give different
answers on a ledger with a disclosed URL gap, which is the whole point of the flag.

Also checked and found sound, recorded so the next reviewer need not redo it: `server.py`
rejects `..` traversal, encoded traversal and absolute paths, and serves only the four
generated pages plus `briefs/`, `sources/` and `docs/`; every ledger value reaching HTML
goes through `esc()`, `attr()` or `json_literal()`, and the two interpolations that look
raw are not (a `float`-coerced SVG coordinate and an `href` escaped at its use site);
rendering is deterministic apart from the generated-at stamp, which `--check` already
neutralises; and every failure path — missing ledger, malformed JSON, wrong root type,
missing required keys, an unknown brief number, an existing brief without `--force` —
exits non-zero with a message that names the fix.
