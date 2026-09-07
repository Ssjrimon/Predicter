# The daily schedule

The brief is an afternoon product. **One** scheduled task drives it, firing at **15:00 US
Central**, and the run covers everything since the previous brief's information cutoff.

This document is the record BRIEFING-PROTOCOL.md Rule 0 point 2 requires: *"Before creating
any scheduled task for this project, check whether one already exists and retire the
duplicate rather than adding to it."* If you are about to create a schedule, read this
first — there is already one.

## What is configured

| | |
|---|---|
| **Routine ID** | `trig_01H1Wd2FeZ1LiWYpUwUDTVka` |
| **Name** | Nat Def — daily Strategic Threat & Posture brief (15:00 CT) |
| **Cron** | `0 20 * * *` — **evaluated in UTC** |
| **Local time** | 15:00 US Central while CDT (UTC−5) is in effect |
| **Session model** | A fresh session per firing (`create_new_session_on_fire`) |
| **Environment** | `env_01RvyxQUGov1snpzySEwbmtn` ("node briefs") |
| **Model** | `claude-opus-5` |
| **Notifications** | Push on completion; email off |
| **Created** | 2026-09-07, at the user's request, after confirming no other Routine existed |

It is managed with the `claude-code-remote` MCP tools — `list_triggers`, `update_trigger`,
`delete_trigger`, `fire_trigger` — or from the Routines UI on claude.ai.

## Why the model is pinned

The Routine was created without an explicit model and defaulted to Sonnet 5 — confirmed from
the pre-flight run's own record (`last_served_model`). It was changed to `claude-opus-5` on
7 September 2026 at the user's request.

This is a real setting, not a preference: the daily run is a ten-thread sweep whose output has
to clear the Step 3 verification gate — walking each claim back to origin, counting hops,
checking the date of the assertion rather than the date it was found, and running a
contradiction sweep before anything reaches the ledger. Judgement about what *fails* that gate
is the expensive part of the job, and a run that quietly lowers its bar produces a brief that
looks exactly like a good one.

Because this Routine creates a fresh session per firing, a model change applies from the next
fire. A Routine bound to a persistent session would keep that session's model until the
binding cleared.

## Why a fresh session per firing

Because that is what the protocol already assumes. From Rule 0:

> Each scheduled run starts a fresh session with no memory of the previous one — that is how
> scheduled tasks work and it cannot be changed. This is not a problem to solve; it is the
> reason the ledger exists. Continuity lives in `intel-ledger.json`, not in conversation
> history.

A Routine bound to one long-lived session would accumulate context that the next run must
not rely on, and would quietly diverge from the ledger as the source of truth.

## Why the run commits straight to `main`, and does not open a pull request

This looks like the less careful option and is in fact the only correct one.

The scheduled run reads `main`. If each day's brief landed in an unmerged pull request,
`main` would still hold yesterday's `brief_number` and `last_cutoff` — **and so would
`briefs/INDEX.md`, consistently**. The next run's Step 1 continuity check would therefore
*pass*, because both halves of the check are stale together. It would then re-sweep the same
interval and mint a second brief carrying the same number.

That is precisely the fork condition Rule 0 exists to prevent, arrived at through a
mechanism the 16 August incident did not involve. A daily automation that files behind a
review queue is not a safer version of this operation; it is a slower way to fork it.

The risk this trades away is real but bounded: a bad brief lands unreviewed. The protocol
already answers that — delivered briefs are never rewritten, and corrections run in the next
brief's verification log. Nothing about a bad brief is unrecoverable, and the record of the
correction is itself part of the product.

## Daylight saving — this needs a human twice a year

**Cron is evaluated in UTC. It does not follow US Central through the DST transition.**

| Period | US Central offset | Cron for 15:00 local |
|---|---|---|
| Now → **1 November 2026** | CDT, UTC−5 | `0 20 * * *` ← currently set |
| **1 November 2026** → March 2027 | CST, UTC−6 | `0 21 * * *` |

Left alone, the brief will start firing at **14:00 Central** on 1 November 2026. Update it
with `update_trigger` (schedule-only changes take effect immediately; send them in a call
without a `prompt`):

```
update_trigger(trigger_id="trig_01H1Wd2FeZ1LiWYpUwUDTVka", cron_expression="0 21 * * *")
```

## The one thing this repository cannot verify

`list_triggers` shows only Routines on this account **in the cloud**. Its own documentation
is explicit: *"Scheduled tasks stored locally by the Cowork desktop app do not appear in this
list."* BRIEFING-PROTOCOL.md says the same thing about the two lists and requires confirming
both.

That list was empty when this Routine was created, so nothing on the cloud side competes with
it. **Whether a Cowork desktop scheduled task still points at the retired claude.ai "Nat Def"
project can only be checked on the user's own machine.** `docs/MIGRATION-NOTES.md` flags this
too: the migration deleted the one cloud-side trigger it could see, but could not reach the
desktop list, and the project's own instructions field could not be cleared.

If such a task exists, it is firing against a project whose `briefs/INDEX.md` now carries a
retirement notice telling any session that opens it to stop. Delete or disable it.

## Testing it

The protocol requires this and it is not a formality: *"Run it manually once before
scheduling. The single thing being tested is whether the task can reach the ledger."*

Use `fire_trigger` with a `text` override that turns the run into a read-only pre-flight —
it is appended after the Routine's own prompt, so it can countermand it:

```
fire_trigger(
  trigger_id="trig_01H1Wd2FeZ1LiWYpUwUDTVka",
  text="OVERRIDE FOR THIS ONE RUN ONLY — PRE-FLIGHT TEST, NOT A BRIEF. Do not produce a
        brief, do not write to intel-ledger.json, do not commit or push. Only: confirm the
        repo is reachable; confirm BRIEFING-PROTOCOL.md and intel-ledger.json are readable;
        run `python3 -m natdef status` and `python3 -m natdef check`; run the tests; run
        `git push --dry-run origin main`; report whether web search is available. Then stop."
)
```

### What the first pre-flight established (7 September 2026)

The pre-flight was run before the schedule was trusted, and the honest reading of it is
narrower than "it passed".

**Established.** The run reports `ROUTINE_RUN_STATUS_SUCCEEDED`, fired 05:13:45Z and finished
05:25:50Z — twelve minutes and roughly 218,000 context tokens of work. `origin/main` was
unchanged at `928d152` afterwards, with zero commits added, so the run honoured the read-only
override and wrote nothing. The whole unattended path therefore works: the Routine fires, a
session spawns in the environment, it does substantial work, and it exits cleanly.

**Not established.** The outcome of each of the seven individual checks. The fired session is
a separate session and its transcript is not readable from the session that fired it — only
the run record and the repository's own state are available as evidence. Do not record the
individual checks as having passed on the strength of `SUCCEEDED`, which only means the
session ran to completion without erroring.

**The strongest available inference**, stated as an inference rather than a finding: a session
that could not reach the repository would have stopped within seconds on its own mandatory
refusal clause, not worked for twelve minutes.

**The real test is the first scheduled run.** Watch for two signals: the push notification,
and a commit on `main`. If the run produces no commit, treat the refusal clause as having
fired and read that session's report before changing any configuration.

A failure is the useful outcome. The four things that would silently break the daily run,
in rough order of likelihood:

1. **No repository access** in the fired session — it cannot clone, or has no push
   credentials. The run would stop at its own refusal clause, which is correct behaviour but
   produces nothing.
2. **No web search** — the sweep cannot happen. A run without it must stop, not guess.
3. **Push rejected** on `main` — branch protection, or a credential the fired session does
   not carry.
4. **The Routine's connector grant is empty.** Fired sessions get no `mcp__*` tools. The run
   does not need them — git over HTTPS and the CLI are enough — but anything that assumed a
   GitHub MCP tool would fail.

## Changing the cadence

Rule 0: exactly one recurring task. Two schedules pointed at this operation is not
redundancy, it is two runs racing to increment `brief_number`.

If a fast-moving situation needs tighter coverage, add a **sweep-only** task that writes
nothing, and retire it afterward. It is safe to run alongside the daily because it touches
no state:

```
Run a sweep only, per BRIEFING-PROTOCOL.md. Do not produce a brief.
Do not write to intel-ledger.json and do not advance last_cutoff.
Check the watchlist for anything that would change a thread's direction or
intensity. If nothing qualifies, say so in one line and stop.
```

Say so in the ledger's `verification_log[]` when you add or retire one.

## If a run is missed

Nothing is lost and nothing needs backfilling. Every brief covers the entire interval since
the last one's cutoff, however long that was — that is what lookback discipline is for. The
next brief states the interval on its masthead, and `natdef brief` computes and prints it
automatically, including whether it exceeds 48 hours. Brief 013 covered 190 hours this way.
