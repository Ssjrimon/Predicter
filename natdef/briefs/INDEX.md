# Brief archive — index

Newest first. One line per filed brief. Written by Step 7 of `BRIEFING-PROTOCOL.md`.

Format:
`YYYY-MM-DD · Brief NNN · cutoff YYYY-MM-DDTHHMMZ · <bottom line, one clause>`

The archive files themselves live at `briefs/daily-brief-YYYY-MM-DD.html` in this project.
Any run that finds a gap between this index and `ledger_meta.brief_number` /
`ledger_meta.last_cutoff` has detected a duplicate or forked run — reconcile it and log it in
`verification_log[]` rather than renumbering over it.

---

## Filed

- 2026-08-29 · Brief 012 · cutoff 2026-08-29T2200Z · a 114-hour catch-up (25-29 Aug): CIA Director
  Ratcliffe made an unannounced 25 Aug Moscow visit that Peskov denied the same day and the Kremlin
  later confirmed, saying Putin had been briefed; Qatar's PM ran the first structured Hormuz
  mediation since the Islamabad memorandum lapsed, with Iran's price unmoved and Trump "not in a
  hurry"; both channels opened alongside escalation — a tanker struck in the strait (UKMTO 121-26,
  Hormuz held at SEVERE), a second Tu-95MS destroyed at Engels-2, and a Russian mobile ICBM test
  three days after Ratcliffe left — while Brent fell more than 5% in the week the war's largest
  sanctions package took effect; IR moves escalating → volatile; two corrections run (Haiti: 47
  dead on 23 Aug at Kenscoff, not ~30 on 24 Aug; and Brief 011's KP/HL thread moves were never
  written into the live ledger)
- 2026-08-25 · Brief 011 · cutoff 2026-08-25T0400Z · a 6-day catch-up (19-25 Aug, same pattern as
  Brief 006): Bessent finally unveiled "Operation Economic Outcast" sanctions on Iran and Iran
  vowed "seismic" retaliation; Trump announced plans to meet Kim Jong Un and North Korea answered
  with a ~10-missile barrage, moving KP off its long hold; Russia's largest strike of the window
  killed at least 18 near Kyiv; a Haiti gang attack killed at least 30, moving HL off "easing" —
  WebFetch was rate-limited for nearly this entire sweep, disclosed throughout
- 2026-08-19 · Brief 010 · cutoff 2026-08-19T2100Z · the UAE suspended all trade with Iran over
  the 18 Aug missile alert, the war's first Gulf-state economic break with Iran — Iran's Foreign
  Ministry called the underlying missile claim a false flag; Kherson and Zaporizhzhia strikes
  killed at least six, and a late-filed item shows Ukraine's own dismissed defence minister
  publicly demanding wartime elections; closes the 17-19 Aug cloud-only backfill
- 2026-08-18 · Brief 009 · cutoff 2026-08-18T2100Z · Iran-launched missiles reached Emirati
  waters for the first time since the 12 July blockade — neither intercepted, both fell into the
  sea — the same day Trump repeated his Oman threat for a second straight day; nearly 800 drones
  hit the Moscow region and a Russian strike killed 10 in Kharkiv region's Pechenihy, while Trump
  ordered the Pentagon to reduce, not cancel, the Ulchi Freedom Shield exercises with South Korea
- 2026-08-17 · Brief 008 · cutoff 2026-08-17T2100Z · Trump told Iran to "put up the white flag of
  surrender" and warned Oman he'd "bomb the s*** out of them" if it "gets in the way" of
  reopening Hormuz, while the IRGC denied his claimed backchannel; Hormuz tanker tracking showed
  zero Iranian crude clearing the Gulf since 12 July even as overall transits kept recovering
- 2026-08-16 · Brief 007 · cutoff 2026-08-16T1930Z · the Islamabad memorandum's 60-day window
  lapsed with no extension and no successor channel, so IR turns escalating; Russia and Ukraine
  set reciprocal deep-strike records overnight and RU moves to 8; corrects Brief 006 — the White
  House says Trump was joking about declaring Hormuz US territory
- 2026-08-15 · Brief 006 · cutoff 2026-08-15T1500Z · a 72-hour catch-up brief: Trump said he'll
  declare Hormuz US territory, Hegseth called the blockade indefinitely sustainable, and ISW's
  reversal of its Russia battlefield-momentum judgment overshadowed the Gulf news entirely
- 2026-08-12 · Brief 005 · cutoff 2026-08-12T1500Z · Yemen revised the Bab el-Mandeb toll from
  three to six dead, the deadliest single strike on shipping in the war, as Iran's SNSC secretary
  said Hormuz stays closed until Washington changes course
- 2026-08-11 · Brief 004 · cutoff 2026-08-11T1500Z · a suspected Houthi strike killed three
  crewmembers in the Bab el-Mandeb, the war's first shipping deaths, as Hormuz transit volume hit
  a five-week low
- 2026-08-10 · Brief 003 · cutoff 2026-08-10T2359Z · Iran raised the price of reopening Hormuz —
  sanctions relief and war reparations on top of the already-agreed route — and Brent closed a
  fourth straight winning session near 16% above its pre-war baseline
- 2026-08-09 · Brief 002 · cutoff 2026-08-09T1200Z · the Gulf's security architecture changed
  without the US in it — Saudi Arabia, Turkey and Pakistan signed the Mecca Joint Defence
  Agreement; the Hormuz route was agreed but stayed detached from reopening
- 2026-08-08 · Brief 001 · cutoff 2026-08-08T1800Z · the Iran war was the whole board and the
  Intelligence Community had just changed hands — Jay Clayton sworn in as ninth DNI five days
  earlier; Epic Fury status and water-sector attribution both corrected post-publication

**Note the numbering.** The real Brief 003 above is dated 10 Aug. It is unrelated to the
retracted item below, which also called itself "Brief 003" but is dated 16 Aug — a coincidence
of two different numbering schemes, not a duplicate. Do not confuse them — see **Retracted**.

---

## Retracted

- **`briefs/RETRACTED-brief-003-2026-08-16.html`** — a cloud-scheduled task fired on 16 Aug 2026
  against a stale, thin copy of `intel-ledger.json` that had lived in this project since roughly
  Brief 002 and had never been resynced with the working-folder ledger. Self-numbered "Brief 003"
  and dated the same day as the real Brief 007 above. Its interval claim (173 hours, six missed
  runs) and its numbering were both artifacts of the stale copy, not of reality: the
  working-folder ledger was at Brief 006 with a 15 Aug cutoff at the time, one normal cycle
  behind. The file is preserved, not deleted, and carries its own retraction notice at the top.
  Two genuinely new findings it surfaced — EIA/IEA quantification of the Hormuz closure and the
  FBI's federal floor on the water-sector campaign — were independently confirmed and merged into
  the canonical ledger as gap-fills. Full account: `intel-ledger.json` → `verification_log[]`,
  entry dated 2026-08-16, claim "CONTINUITY — reconciliation of a second forked briefing run."

---

## Notes for future runs

**The root cause was two schedules, not one bad run.** A cloud-based scheduled task
(`mcp__claude-code-remote__create_trigger`) was created on 16 Aug without first confirming
whether a desktop-bound one already existed for this project — the exact check
`BRIEFING-PROTOCOL.md` Rule 0 already required. One did: a Cowork scheduled task
(`create_scheduled_task`) with working-folder access, firing daily at 15:00 local, has been
producing the real numbered sequence (Briefs 001–007) the whole time. The cloud task could only
see the project's copy of the ledger, which had gone stale because nothing had synced a Step 7
write back through it since about Brief 002. Both ran within the same hour on 16 Aug and produced
two different "today" briefs. The desktop-bound run caught the fork and disclosed it in full; the
cloud run had no way to. **The cloud trigger has been deleted, not merely disabled**, and replaced
with a separate, strictly read-only status-check trigger that reports whether today's sync is
outstanding — it is not authorized to write to the ledger or produce brief content.

**The desktop-bound task cannot currently write to this project.** It self-reported (in Brief
007's "Changed on the board" section) that a project write was attempted and refused. Until that
changes, Step 7's project-filing is a manual/interactive step: after each local run, a session
with both project and working-folder access needs to copy the outputs across, the way this
reconciliation did — and the way Briefs 001–006 above were filed today, well after the fact.
`BRIEFING-PROTOCOL.md` Rule 0, point 4, covers this in full.

**The "archive stubs" and "missing node data" defects were never real.** The retracted brief's
`ledger_meta.open_defects` claimed Briefs 001–002 were unrecoverable stub entries and that
`map_nodes`/`node_topics`/`node_history`/`node_edges` were entirely absent from "the ledger."
Both claims were true only of the stale project copy it was reading. The working-folder canonical
ledger has always carried full, non-stub entries for every brief and all four node-map keys —
confirmed while reconciling this index. There is no outstanding defect of either kind.

**Briefs 008–010 (17–19 Aug 2026) were produced cloud-only, with the user's explicit, informed
sign-off — this backfill is now closed.** The device bridge to the user's own computer was
unreachable for the entire session that produced them (degraded relay state, then an explicit
"not connected" error, retried once per the tool's own guidance). The user, primarily on mobile
that cycle, was told plainly and chose a full independent cloud sweep over waiting for
reconnection. Each of the three starts from the project's own ledger — current as of Brief 007's
16 Aug reconciliation — runs every claim through the same Step 3 gate, and discloses on its own
masthead and verification log that the working-folder ledger was not reachable and was not
updated. `render.py`/`validate.py` do not exist in that cloud session's own sandbox; a narrower
manual structural check stood in for them and is disclosed as such in each brief, not represented
as a full Step 6 pass. **The working-folder ledger on the user's device stayed at Brief 007
throughout all three** — it is now three briefs behind. The next session with both project and
device access must sync it forward to Brief 010's state, and check whether the desktop-bound
scheduler independently produced its own content for 17–19 Aug while this cloud run was in
progress. If it did, reconcile the two the same deliberate way Brief 003 was: don't discard
either side silently, and don't renumber over a divergence. This question was in fact re-opened
before Brief 011: that session checked device access (still unreachable, retried once) and asked
the user directly via AskUserQuestion before proceeding cloud-only a fourth time. See the Brief
011 note below.

**A minor self-caught error during Brief 010's ledger update, for transparency.** The script that
applied Brief 010's delta appended a second, duplicate `horizon[]` entry about Bessent's promised
Iran sanctions instead of updating the existing one in place, because its text-matching logic
didn't recognize the older entry's exact wording. Caught on review before the brief was filed —
merged into one entry, and the archive's verification tally and "changed" bullets were corrected
to match. Full account in `intel-ledger.json` → `verification_log[]`, entry dated 2026-08-19,
claim "Internal QA -- draft ledger script appended a duplicate Bessent-sanctions horizon item."
Worth knowing for future runs: when re-noting an existing horizon item programmatically, matching
on the item's exact current text is fragile once earlier briefs have already reworded it —
matching on a stable identifier (or reviewing the full horizon list by eye before filing, as was
done here) is safer than trusting a text-prefix match alone.

**Brief 011 (25 Aug 2026) is a 6-day catch-up, produced cloud-only for the fourth consecutive
time, with the user asked and re-confirming before it ran.** The gap since Brief 010 turned out to
be six days (20-25 Aug), not the three initially estimated when the user was first asked — the
session flagged that correction to the user before starting research rather than quietly
absorbing the difference. Device access was checked and retried once at session start; both
attempts failed "not connected." The user chose to proceed cloud-only via AskUserQuestion rather
than wait. Following Brief 006's precedent, the whole 19-25 Aug gap is covered as one catch-up
window rather than reconstructed day-by-day or forced into a false 24-hour frame. **New this
brief: WebFetch itself hit a session rate limit (stated reset 8am UTC) partway through research**,
after only two calls succeeded. Nearly every claim in Brief 011 rests on convergence across
multiple independent WebSearch results rather than a full-page fetch — a real, disclosed
reduction in verification depth versus Briefs 001-010, flagged on the brief's own masthead, in
every affected item's sourcing line, and in `verification_log[]`. The one exception is the 20 Aug
Russia/Ukraine strike, fetched in full during Brief 010's own research before the limit hit.
KP moved off a long hold to 6/volatile and HL moved off "easing" to 5/escalating in this brief —
both logged as deliberate, reasoned moves (KP as a `revisions[]` entry, since it explicitly
supersedes prior briefs' stated reasoning), not silent drift. **The working-folder ledger on the
user's device stayed at Brief 007 across all four cloud-only briefs** — it is now four behind.
The next session should re-check device access before a fifth consecutive cloud-only brief, and
should re-attempt WebFetch rather than assume Brief 011's rate limit still applies.

**Brief 012 (29 Aug 2026) is a 114-hour catch-up, cloud-only for the fifth consecutive time, run
interactively at the user's explicit request rather than by the scheduler.** The 15:00 local task
did not fire on 26, 27 or 28 Aug. A read-only status-check run earlier on 29 Aug confirmed the gap
and, correctly, wrote nothing; the user then asked for the brief directly in that same session.
Device access was not merely failing but absent — no `mcp__remote-devices__*` tool existed in the
session at all — so no retry was possible or attempted, and this is disclosed on the masthead.
**The continuity check passed cleanly:** `ledger_meta` (Brief 011, cutoff 2026-08-25T0400Z) agreed
exactly with this index's newest filed entry, so Rule 0 point 4's stop condition was read as not
triggered — that rule's stop applies where the reachable copy *cannot be confirmed current*, and
here the index independently confirmed it. That reading is recorded in `verification_log[]` so a
later run can disagree with it. **The working-folder ledger is now five briefs behind (still at
Brief 007).**

**WebFetch availability recovered fully.** Per Brief 011's note above, the rate limit was re-tested
rather than assumed. It was gone: roughly seventeen full-page fetches succeeded, including both
UKMTO primary PDFs and the ODNI newsroom index. Brief 012 therefore does not carry Brief 011's
blanket convergence-only caveat. Four fetches failed for site-specific reasons — CNN and Taiwan MND
on robots.txt, CNBC and CISA.gov on 403 — and each is disclosed at its point of use. The Taiwan MND
block is a real reduction in CN coverage and is stated as such rather than papered over.

**Two ledger defects were found this run, one fixed and one deliberately left alone.**

1. *Fixed.* Brief 011's thread moves were never applied to `threads[]`. Its archive snapshot, its
   `bottom_line` and the threads' own `one_line` text all record KP at 6/volatile and HL at
   5/escalating, but live `threads[]` still held KP 5/holding and HL 4/easing — Step 4.2 was skipped
   while Step 4.8 was not. Anything reading `threads[]` (dashboard, node map, console) served
   pre-Brief-011 values for four days. Corrected in Brief 012. **`validate.py` does not catch this**
   — it range-checks intensities and direction vocabulary but never diffs `threads[]` against the
   newest archive snapshot. **Recommended new check: assert every thread's live intensity and
   direction equal the newest archive entry's snapshot for that code.** This is the second time a
   Step 4 sub-step has been silently skipped (cf. Brief 010's duplicate horizon entry), which
   suggests the Step 4 sub-steps want a checklist in the validator rather than in the operator's
   head.

2. *Found, logged, NOT modified.* Brief 002's archive entry contains an item whose `thread` is an
   em dash — a deliberate cross-thread "nothing moved" note, not corrupted data, but not a declared
   thread code either. It will fail `validate.py`'s stated check that every archive item's thread
   code is a declared thread. Briefs 001-002 were filed retroactively during the 16 Aug
   reconciliation, which is the likeliest reason this has never surfaced: the validator has probably
   not been run against the archive since. It was left unmodified because rewriting a delivered
   brief's archive record alters the evidence of what that brief said. **The next session with
   folder access should expect this failure on the first `validate.py` run and treat it as
   anticipated, not as a fresh regression** — then decide explicitly between declaring a reserved
   cross-thread code (e.g. `XX`) and amending the Brief 002 entry with the change logged.

**Step 6 was not run as specified and Step 7 is only partly complete.** `render.py`, `build_app.py`
and `validate.py` live in the working folder and were unreachable; a narrower manual structural
check stood in (archive numbering sequential and gap-free, no duplicate dates, archive thread codes
checked against `threads[]`, live threads reconciled against the newest snapshot, every new timeline
entry carrying a date and a source, JSON well-formed with every list key still a list). This is
disclosed in the brief as a partial Step 6, not represented as a validate.py pass. **The dashboard,
brief archive, node map and console are now stale against the ledger** and stay that way until a
session with folder access re-runs all three scripts. Step 7 items 1 and 2 (brief filed, this index
updated) are done; items 3 and 4 (re-file the rendered dashboard, write outputs back to the working
folder) are outstanding.

**A correction carried forward, for the record.** Brief 011 logged the Haiti attack as "at least 30
killed, 24 Aug, farming community" from AP-wire convergence read without a full fetch, under that
brief's disclosed rate-limit caveat. Three independent full fetches this sweep (Al Jazeera 27 Aug,
UPI 26 Aug, UN News 28 Aug, all tracing to the UN Integrated Office in Haiti) establish 23 Aug, at
Kenscoff outside Port-au-Prince, at least 47 killed including five children, 22 injured and more
than 52 abducted. Both the date and the toll were wrong, in exactly the direction Brief 011's own
caveat warned about — which is the caveat working as intended, and an argument for re-testing a
degraded tool at the start of every run rather than inheriting the previous run's constraint.

---

## 2026-09-06 — Migrated to Claude Code. This project ("Nat Def") is retired.

**This claude.ai Project is no longer the home of this operation and must not be written to
again.** Per `BRIEFING-PROTOCOL.md` Rule 0, there is exactly one home; as of 6 September 2026
that home is a git repository run under Claude Code, not this project. If you are a Claude
session reading this inside the Nat Def project — scheduled, interactive, or otherwise — **stop
before producing a brief here.** Producing one would recreate the exact fork condition Rule 0
exists to prevent, this time between this project and the Claude Code repository rather than
between a project and a working folder. Tell whoever is present that this project is retired
and point them at the migration this note describes.

**Why now.** The user asked to move the whole operation into Claude Code. Before building the
export, the session doing the migration re-checked this project's actual state rather than
trusting an earlier summary of it, and found it already at Brief 012 (29 Aug) — a brief produced
by a separate session with no visibility into it — while a stale local cloud sandbox from an
earlier part of the same conversation was still sitting at Brief 011 (25 Aug). That gap, plus the
discovery that Brief 012 itself had already found and fixed a real defect in Brief 011's own
ledger update (see the note above), is the direct reason the migration reads the canonical
project state fresh rather than exporting from whichever copy happened to be sitting in a
sandbox. **As of the migration, this project had gone another 8 days without a new brief**
(last cutoff 2026-08-29T2200Z; migration performed 2026-09-06) — the daily 15:00-local Cowork
schedule had lapsed again, the same failure mode Rule 0 and this index have already documented
twice. That gap is exactly the kind of drift Rule 0 point 4 exists to catch, and it is a concrete
argument for the answer the user gave when asked: Claude Code, run under a scheduler that does
not depend on a chat app being open, removes the specific failure mode that produced this gap
and the 16 Aug fork before it.

**What the export contains.** Everything in this project as of the read above — `intel-ledger.json`
at Brief 12, every `daily-brief-*.html` including the retracted one, `BRIEFING-PROTOCOL.md`,
this index, and the two `claude/*` docs — carried over verbatim, byte-for-byte where the file
was re-fetched from the project directly (the ledger, this index, `BRIEFING-PROTOCOL.md`, and
Brief 012's HTML), or from a local cloud-sandbox copy whose project timestamp showed no changes
since it was written (the other brief HTMLs, the dashboard, the console readme). The export also
carries a set of tools that were **built in a cloud sandbox across Briefs 008–012 and never lived
in this project at all**: `build_app.py` (real, complete, matches the Step 6 spec exactly),
`app-template.html`, `natdef-console.html`, `parts/*`, `server.py`, `smoke.py`, the historical
`apply_brief8.py`–`apply_brief11.py` ledger-delta scripts, and the `shot_brief*.py` Playwright
verification scripts. A new `validate.py` was authored during the migration directly from this
document's Step 6 checklist, since no working `validate.py` had ever been reachable from any
cloud session in this project's history — full account in `MIGRATION-NOTES.md` at the repository
root. `render.py` was **not** reconstructed: no template for it (the dashboard/archive/node-map
HTML structure `render.py` is supposed to emit) was recoverable from any cloud sandbox, and
guessing one from `strategic-threat-briefing.html`'s rendered output alone risked exactly the
kind of silent invention this protocol exists to prevent. It is an open item, not a fabricated one.

**The two Brief 012 postmortem items are both closed as of this migration.** The `threads[]` fix
Brief 012 already made is carried forward as-is. The Brief 002 `—` thread-code question is
resolved by declaring the em dash a formally allow-listed cross-thread sentinel in
`BRIEFING-PROTOCOL.md` and in `validate.py` — see the new "Cross-thread archive items" section
added to the protocol — rather than amending Brief 002's record. Brief 002's file itself is
untouched. The new `validate.py` also carries forward Brief 012's recommended check (thread
snapshot vs. live `threads[]`) and accepts both cutoff-timestamp forms actually seen across this
ledger's history (`HH:MM` and `HHMM`, both meaning the same instant) rather than failing on the
inconsistency — flagged for standardizing on `HH:MM` going forward, not silently rewritten in
place. Full detail on all three in `verification_log[]` under the 2026-09-06 entries.

**What this migration could not see, and the one thing that must happen before this repository
is trusted as complete.** The device bridge to the user's own computer was unreachable throughout
(checked, retried once, per this project's own standing practice). `BRIEFING-PROTOCOL.md`'s own
configuration block names a working folder on the user's machine —
`C:\Users\User\OneDrive\Documents\New folder\strategic-threat-briefing\` — as the place
`render.py`, `build_app.py` and `validate.py` were meant to live and where the desktop-bound
Cowork scheduled task was, as of Brief 007, still writing successfully even though it could not
write back to this project. **This migration has no way to know whether that folder kept
advancing past Brief 007, or past Brief 012, while this project sat still.** If it did, that
folder — not this export — may hold the true most-current state of this operation, including a
real, working `render.py` this migration was never able to recover. The first session that runs
this Claude Code repository with access to that machine must check that folder before treating
this repository alone as the complete history, and reconcile the two the same deliberate way the
16 Aug fork was reconciled if they've diverged: don't discard either side silently, don't
renumber over it. See `MIGRATION-NOTES.md` for the full reasoning.

---

**Toolchain rebuilt, 6 September 2026.** No brief was produced and nothing in this index
changed. The scripts were rebuilt from scratch on the same data: `render.py` now exists,
all fifteen of `BRIEFING-PROTOCOL.md` Step 6's checks are implemented (the four that had
been standing down as `SKIPPED`, plus "retired claims cannot reappear" against a new
`retired_claims[]` registry), and briefs are now generated from their `archive[]` entry so
a brief and the ledger cannot disagree. `brief_number`, `last_cutoff` and `archive[]` were
untouched — this was infrastructure, logged in `verification_log[]` under `2026-09-06`, not
a thirteenth brief. Full account: `docs/REBUILD-NOTES.md`.

The paragraph above this one still stands: the OneDrive working folder has still never been
reached, and must be checked before this repository is treated as the complete history.
